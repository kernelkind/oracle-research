//! Versioned native-INT8 embedding artifacts over canonical corpus rows.

use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::artifact::{
    ArtifactFile, describe_fixed_artifact, hash_file, is_safe_artifact_name, verify_fixed_artifact,
};
use crate::canonical::CanonicalManifest;
use crate::snapshot::{
    DamusSnapshot, Error, Result, Validation, create_directory, io_error, ndb_error, open_ndb,
    read_manifest, require_directory, require_file, write_manifest,
};
use crate::stage::CorpusStageManifest;

const EVENT_ID_BYTES: usize = 32;
const NORM_BYTES: usize = size_of::<f32>();

type EventId = [u8; EVENT_ID_BYTES];

/// Reproducibility metadata for an embedding encoder.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EncoderDescriptor {
    /// Stable upstream model identifier.
    pub model_id: String,
    /// Immutable upstream model revision.
    pub model_revision: String,
    /// SHA-256 of the checked-in model-file lock.
    pub model_lock_sha256: String,
    /// Inference runtime family.
    pub runtime: String,
    /// Inference runtime version or compatibility level.
    pub runtime_version: String,
    /// SHA-256 of the inference runtime library.
    pub runtime_sha256: String,
    /// Runtime execution provider used for inference.
    pub execution_provider: String,
    /// Model output used for the stored vectors.
    pub output_name: String,
    /// Elements in each vector.
    pub dimensions: u32,
    /// Preflight token ceiling.
    pub max_tokens: u32,
    /// Exact experiment-only text preprocessing rule.
    pub input_rule: String,
    /// Pooling performed by the model.
    pub pooling: String,
    /// Quantization performed by the model.
    pub quantization: String,
    /// Optional text prepended before tokenization.
    pub instruction: Option<String>,
}

/// A batch encoder that returns row-major native-INT8 vectors.
pub trait EmbeddingEncoder {
    /// Return the exact model, runtime, and preprocessing identity.
    fn descriptor(&self) -> &EncoderDescriptor;

    /// Encode raw kind `1` content in input order.
    fn encode(&mut self, texts: &[&str]) -> Result<Vec<i8>>;
}

/// Controls artifact partitioning without changing encoder semantics.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EmbeddingBuildConfig {
    /// Filesystem-safe artifact name beneath `embeddings/`.
    pub artifact_name: String,
    /// Maximum rows submitted to the encoder at once.
    pub batch_size: usize,
    /// Maximum rows in one immutable output shard.
    pub shard_rows: u64,
}

/// Metadata for one immutable embedding shard.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingShardManifest {
    /// Zero-based shard ordinal.
    pub ordinal: u32,
    /// Global canonical row at which this shard begins.
    pub start_row: u64,
    /// Rows stored in the shard.
    pub rows: u64,
    /// Row-major native-INT8 vectors.
    pub vectors: ArtifactFile,
    /// Little-endian float32 cosine norms.
    pub norms: ArtifactFile,
    /// Canonical event IDs corresponding one-to-one with vector rows.
    pub row_ids: ArtifactFile,
}

/// Identity of a selected corpus stage represented by an embedding artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingCorpusStage {
    /// Immutable stage name beneath `stages/`.
    pub name: String,
    /// SHA-256 of the stage manifest.
    pub manifest_sha256: String,
    /// SHA-256 of the exact selected row file.
    pub rows_sha256: String,
    /// Deterministic rule used to select the rows.
    pub selection_rule: String,
}

/// Durable description of a complete embedding artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 inherited from the source snapshot import.
    pub source_snapshot_sha256: String,
    /// SHA-256 of the canonical manifest consumed by this build.
    pub canonical_manifest_sha256: String,
    /// SHA-256 of the complete canonical row-ID file.
    pub canonical_rows_sha256: String,
    /// Selected corpus stage, absent when every canonical row was embedded.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub corpus_stage: Option<EmbeddingCorpusStage>,
    /// Exact encoder identity and preprocessing contract.
    pub encoder: EncoderDescriptor,
    /// Configured build batch size.
    pub batch_size: u32,
    /// Configured maximum rows per shard.
    pub shard_rows: u64,
    /// Total canonical rows embedded.
    pub total_rows: u64,
    /// Ordered immutable shard metadata.
    pub shards: Vec<EmbeddingShardManifest>,
}

impl DamusSnapshot {
    /// Encode every canonical row once and publish immutable INT8 shards.
    pub fn embed_canonical_corpus(
        &self,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        validate_config(config, encoder.descriptor())?;
        let source = self.canonical_embedding_source()?;
        self.embed_rows(config, encoder, source)
    }

    /// Encode every row in one verified nested corpus stage.
    pub fn embed_corpus_stage(
        &self,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        validate_config(config, encoder.descriptor())?;
        let source = self.staged_embedding_source(stage_name)?;
        self.embed_rows(config, encoder, source)
    }

    fn embed_rows(
        &self,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
        source: EmbeddingSource,
    ) -> Result<EmbeddingManifest> {
        let layout = self.layout();
        let corpus_path = layout.corpus_db();
        require_directory(&corpus_path)?;

        let artifact = layout.embedding_dir(&config.artifact_name);
        if artifact.exists() {
            let manifest = self.open_embedding_artifact(&config.artifact_name)?;
            if manifest.encoder != *encoder.descriptor() {
                return Err(Error::Invariant(
                    "existing embedding artifact has a different encoder identity".to_owned(),
                ));
            }
            let batch_size = u32::try_from(config.batch_size)
                .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?;
            if manifest.batch_size != batch_size || manifest.shard_rows != config.shard_rows {
                return Err(Error::Invariant(
                    "existing embedding artifact has different build settings".to_owned(),
                ));
            }
            if manifest.source_snapshot_sha256 != source.source_snapshot_sha256
                || manifest.canonical_manifest_sha256 != source.canonical_manifest_sha256
                || manifest.canonical_rows_sha256 != source.canonical_rows_sha256
                || manifest.corpus_stage != source.corpus_stage
                || manifest.total_rows != source.rows
            {
                return Err(Error::Invariant(
                    "existing embedding artifact represents a different corpus selection"
                        .to_owned(),
                ));
            }
            return Ok(manifest);
        }

        create_directory(&layout.embedding_root())?;
        let stage =
            self.prepare_stage(&artifact, &layout.embedding_stage(&config.artifact_name))?;
        create_directory(&stage.join("shards"))?;

        let corpus = open_ndb(&corpus_path, Validation::TrustedSource)?;
        let txn = Transaction::new(&corpus)
            .map_err(|source| ndb_error("open transaction on", &corpus_path, source))?;
        let mut rows = BufReader::new(
            File::open(&source.rows_path)
                .map_err(|error| io_error("open", &source.rows_path, error))?,
        );
        let mut next_row = 0_u64;
        let mut shards = Vec::new();
        {
            let mut build = ShardBuild {
                stage: &stage,
                batch_size: config.batch_size,
                encoder,
                corpus: &corpus,
                txn: &txn,
                corpus_path: &corpus_path,
                canonical_rows: &mut rows,
                canonical_rows_path: &source.rows_path,
            };

            while next_row < source.rows {
                let ordinal = u32::try_from(shards.len())
                    .map_err(|_| Error::Invariant("shard ordinal does not fit u32".to_owned()))?;
                let rows_in_shard = config.shard_rows.min(source.rows - next_row);
                let shard = build.encode_shard(ordinal, next_row, rows_in_shard)?;
                next_row = next_row.checked_add(rows_in_shard).ok_or_else(|| {
                    Error::Invariant("embedded row count overflowed u64".to_owned())
                })?;
                shards.push(shard);
            }
        }
        if read_event_id(&mut rows, &source.rows_path)?.is_some() {
            return Err(Error::Invariant(format!(
                "embedding row file contains more than {} records",
                source.rows
            )));
        }

        let manifest = EmbeddingManifest {
            schema_version: if source.corpus_stage.is_some() { 2 } else { 1 },
            source_snapshot_sha256: source.source_snapshot_sha256,
            canonical_manifest_sha256: source.canonical_manifest_sha256,
            canonical_rows_sha256: source.canonical_rows_sha256,
            corpus_stage: source.corpus_stage,
            encoder: encoder.descriptor().clone(),
            batch_size: u32::try_from(config.batch_size)
                .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?,
            shard_rows: config.shard_rows,
            total_rows: next_row,
            shards,
        };
        write_manifest(&stage.join("manifest.json"), &manifest)?;
        drop(txn);
        drop(corpus);
        self.publish_stage(&stage, &artifact)?;
        Ok(manifest)
    }

    /// Open and fully verify an immutable embedding artifact without inference.
    pub fn open_embedding_artifact(&self, artifact_name: &str) -> Result<EmbeddingManifest> {
        validate_artifact_name(artifact_name)?;
        let layout = self.layout();
        let artifact = layout.embedding_dir(artifact_name);
        require_directory(&artifact)?;
        let manifest_path = artifact.join("manifest.json");
        require_file(&manifest_path)?;
        let manifest: EmbeddingManifest = read_manifest(&manifest_path)?;
        let source = match &manifest.corpus_stage {
            Some(stage) => self.staged_embedding_source(&stage.name)?,
            None => self.canonical_embedding_source()?,
        };
        verify_embedding(&artifact, manifest, &source)
    }

    fn canonical_embedding_source(&self) -> Result<EmbeddingSource> {
        let manifest_path = self.layout().canonical_manifest();
        let rows_path = self.layout().canonical_rows();
        require_file(&manifest_path)?;
        require_file(&rows_path)?;
        let canonical: CanonicalManifest = read_manifest(&manifest_path)?;
        let manifest_sha256 = hash_file(&manifest_path)?;
        let rows_sha256 = hash_file(&rows_path)?;
        if rows_sha256 != canonical.rows.sha256 {
            return Err(Error::Invariant(format!(
                "canonical rows checksum {rows_sha256} does not match manifest {}",
                canonical.rows.sha256
            )));
        }
        Ok(EmbeddingSource {
            source_snapshot_sha256: canonical.source_snapshot_sha256,
            canonical_manifest_sha256: manifest_sha256,
            canonical_rows_sha256: rows_sha256,
            selected_rows_sha256: canonical.rows.sha256,
            rows_path,
            rows: canonical.counts.canonical_rows,
            corpus_stage: None,
        })
    }

    fn staged_embedding_source(&self, stage_name: &str) -> Result<EmbeddingSource> {
        let stage: CorpusStageManifest = self.open_corpus_stage(stage_name)?;
        let stage_manifest_path = self.layout().corpus_stage_manifest(stage_name);
        let stage_manifest_sha256 = hash_file(&stage_manifest_path)?;
        Ok(EmbeddingSource {
            source_snapshot_sha256: stage.source_snapshot_sha256,
            canonical_manifest_sha256: stage.canonical_manifest_sha256,
            canonical_rows_sha256: stage.canonical_rows_sha256,
            selected_rows_sha256: stage.rows.sha256.clone(),
            rows_path: self.layout().corpus_stage_rows(stage_name),
            rows: stage.selected_rows,
            corpus_stage: Some(EmbeddingCorpusStage {
                name: stage.name,
                manifest_sha256: stage_manifest_sha256,
                rows_sha256: stage.rows.sha256,
                selection_rule: stage.selection_rule,
            }),
        })
    }
}

struct EmbeddingSource {
    source_snapshot_sha256: String,
    canonical_manifest_sha256: String,
    canonical_rows_sha256: String,
    selected_rows_sha256: String,
    rows_path: PathBuf,
    rows: u64,
    corpus_stage: Option<EmbeddingCorpusStage>,
}

struct ShardBuild<'a> {
    stage: &'a Path,
    batch_size: usize,
    encoder: &'a mut dyn EmbeddingEncoder,
    corpus: &'a nostrdb::Ndb,
    txn: &'a Transaction,
    corpus_path: &'a Path,
    canonical_rows: &'a mut BufReader<File>,
    canonical_rows_path: &'a Path,
}

impl ShardBuild<'_> {
    fn encode_shard(
        &mut self,
        ordinal: u32,
        start_row: u64,
        row_count: u64,
    ) -> Result<EmbeddingShardManifest> {
        let relative_dir = format!("shards/{ordinal:06}");
        let shard_dir = self.stage.join(&relative_dir);
        create_directory(&shard_dir)?;
        let vectors_path = shard_dir.join("vectors.i8");
        let norms_path = shard_dir.join("norms.f32le");
        let row_ids_path = shard_dir.join("row_ids.bin");
        let mut vectors = create_writer(&vectors_path)?;
        let mut norms = create_writer(&norms_path)?;
        let mut row_ids = create_writer(&row_ids_path)?;
        let dimensions = usize::try_from(self.encoder.descriptor().dimensions)
            .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
        let mut written = 0_u64;

        while written < row_count {
            let batch_rows = usize::try_from(
                (row_count - written).min(
                    u64::try_from(self.batch_size)
                        .map_err(|_| Error::Invariant("batch size does not fit u64".to_owned()))?,
                ),
            )
            .map_err(|_| Error::Invariant("batch row count does not fit usize".to_owned()))?;
            let mut ids = Vec::with_capacity(batch_rows);
            let mut texts = Vec::with_capacity(batch_rows);
            for _ in 0..batch_rows {
                let id = read_event_id(self.canonical_rows, self.canonical_rows_path)?.ok_or_else(
                    || {
                        Error::Invariant(format!(
                            "canonical row file ended after {} rows",
                            start_row + written
                        ))
                    },
                )?;
                let note = self
                    .corpus
                    .get_note_by_id(self.txn, &id)
                    .map_err(|source| {
                        ndb_error("load canonical note from", self.corpus_path, source)
                    })?;
                ids.push(id);
                texts.push(note.content().to_owned());
            }
            let text_refs = texts.iter().map(String::as_str).collect::<Vec<_>>();
            let encoded = self.encoder.encode(&text_refs)?;
            let expected = batch_rows.checked_mul(dimensions).ok_or_else(|| {
                Error::Invariant("encoded batch element count overflowed usize".to_owned())
            })?;
            if encoded.len() != expected {
                return Err(Error::Invariant(format!(
                    "encoder returned {} elements for {batch_rows} rows at {dimensions} dimensions",
                    encoded.len()
                )));
            }
            let encoded_bytes = encoded.iter().map(|value| *value as u8).collect::<Vec<_>>();

            for ((id, vector), vector_bytes) in ids
                .iter()
                .zip(encoded.chunks_exact(dimensions))
                .zip(encoded_bytes.chunks_exact(dimensions))
            {
                vectors
                    .write_all(vector_bytes)
                    .map_err(|source| io_error("write", &vectors_path, source))?;
                let squared = vector.iter().try_fold(0_u64, |sum, value| {
                    let value = i64::from(*value);
                    sum.checked_add(u64::try_from(value * value).expect("square is nonnegative"))
                });
                let squared = squared.ok_or_else(|| {
                    Error::Invariant("vector squared norm overflowed u64".to_owned())
                })?;
                let norm = (squared as f32).sqrt();
                if norm == 0.0 {
                    return Err(Error::Invariant(format!(
                        "encoder returned a zero vector at row {}",
                        start_row + written
                    )));
                }
                norms
                    .write_all(&norm.to_le_bytes())
                    .map_err(|source| io_error("write", &norms_path, source))?;
                row_ids
                    .write_all(id)
                    .map_err(|source| io_error("write", &row_ids_path, source))?;
                written = written
                    .checked_add(1)
                    .ok_or_else(|| Error::Invariant("shard row count overflowed u64".to_owned()))?;
            }
        }

        finish_writer(&mut vectors, &vectors_path)?;
        finish_writer(&mut norms, &norms_path)?;
        finish_writer(&mut row_ids, &row_ids_path)?;
        Ok(EmbeddingShardManifest {
            ordinal,
            start_row,
            rows: written,
            vectors: describe_fixed_artifact(
                &vectors_path,
                &format!("{relative_dir}/vectors.i8"),
                dimensions,
                written,
            )?,
            norms: describe_fixed_artifact(
                &norms_path,
                &format!("{relative_dir}/norms.f32le"),
                NORM_BYTES,
                written,
            )?,
            row_ids: describe_fixed_artifact(
                &row_ids_path,
                &format!("{relative_dir}/row_ids.bin"),
                EVENT_ID_BYTES,
                written,
            )?,
        })
    }
}

fn verify_embedding(
    artifact: &Path,
    manifest: EmbeddingManifest,
    source: &EmbeddingSource,
) -> Result<EmbeddingManifest> {
    require_directory(artifact)?;
    let expected_schema = if source.corpus_stage.is_some() { 2 } else { 1 };
    if manifest.schema_version != expected_schema {
        return Err(Error::Invariant(format!(
            "embedding manifest schema {} does not match corpus selection schema {expected_schema}",
            manifest.schema_version,
        )));
    }
    if manifest.batch_size == 0 || manifest.shard_rows == 0 {
        return Err(Error::Invariant(
            "embedding manifest contains zero-sized build settings".to_owned(),
        ));
    }
    validate_descriptor(&manifest.encoder)?;
    if manifest.source_snapshot_sha256 != source.source_snapshot_sha256
        || manifest.canonical_manifest_sha256 != source.canonical_manifest_sha256
        || manifest.canonical_rows_sha256 != source.canonical_rows_sha256
        || manifest.corpus_stage != source.corpus_stage
        || manifest.total_rows != source.rows
    {
        return Err(Error::Invariant(
            "embedding artifact was built from a different corpus selection".to_owned(),
        ));
    }
    let selected_rows_sha256 = manifest
        .corpus_stage
        .as_ref()
        .map_or(&manifest.canonical_rows_sha256, |stage| &stage.rows_sha256);
    if selected_rows_sha256 != &source.selected_rows_sha256 {
        return Err(Error::Invariant(
            "embedding artifact names a different selected row file".to_owned(),
        ));
    }

    let dimensions = usize::try_from(manifest.encoder.dimensions)
        .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
    let mut canonical_rows = BufReader::new(
        File::open(&source.rows_path)
            .map_err(|error| io_error("open", &source.rows_path, error))?,
    );
    let mut expected_start = 0_u64;
    for (index, shard) in manifest.shards.iter().enumerate() {
        let ordinal = u32::try_from(index)
            .map_err(|_| Error::Invariant("shard ordinal does not fit u32".to_owned()))?;
        let remaining = manifest
            .total_rows
            .checked_sub(expected_start)
            .ok_or_else(|| {
                Error::Invariant("embedding shards exceed the manifest row count".to_owned())
            })?;
        let expected_rows = manifest.shard_rows.min(remaining);
        if expected_rows == 0 {
            return Err(Error::Invariant(
                "embedding manifest contains an empty trailing shard".to_owned(),
            ));
        }
        if shard.ordinal != ordinal
            || shard.start_row != expected_start
            || shard.rows != expected_rows
        {
            return Err(Error::Invariant(format!(
                "embedding shard {index} does not match the configured row partition"
            )));
        }
        let relative_dir = format!("shards/{ordinal:06}");
        verify_fixed_artifact(
            artifact,
            &shard.vectors,
            &format!("{relative_dir}/vectors.i8"),
            dimensions,
            shard.rows,
        )?;
        verify_fixed_artifact(
            artifact,
            &shard.norms,
            &format!("{relative_dir}/norms.f32le"),
            NORM_BYTES,
            shard.rows,
        )?;
        verify_fixed_artifact(
            artifact,
            &shard.row_ids,
            &format!("{relative_dir}/row_ids.bin"),
            EVENT_ID_BYTES,
            shard.rows,
        )?;
        verify_row_ids(
            &artifact.join(&shard.row_ids.file),
            shard.rows,
            &mut canonical_rows,
            &source.rows_path,
            expected_start,
        )?;
        expected_start = expected_start
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("embedded row count overflowed u64".to_owned()))?;
    }
    if expected_start != manifest.total_rows {
        return Err(Error::Invariant(format!(
            "embedding shards contain {expected_start} rows but manifest records {}",
            manifest.total_rows
        )));
    }
    if read_event_id(&mut canonical_rows, &source.rows_path)?.is_some() {
        return Err(Error::Invariant(
            "embedding shards do not cover every selected row".to_owned(),
        ));
    }
    Ok(manifest)
}

fn verify_row_ids(
    row_ids_path: &Path,
    rows: u64,
    canonical_rows: &mut impl Read,
    canonical_rows_path: &Path,
    start_row: u64,
) -> Result<()> {
    let mut row_ids = BufReader::new(
        File::open(row_ids_path).map_err(|source| io_error("open", row_ids_path, source))?,
    );
    for offset in 0..rows {
        let embedded = read_event_id(&mut row_ids, row_ids_path)?.ok_or_else(|| {
            Error::Invariant(format!("embedding row-ID file ended after {offset} rows"))
        })?;
        let canonical = read_event_id(canonical_rows, canonical_rows_path)?.ok_or_else(|| {
            Error::Invariant(format!(
                "canonical row file ended before row {}",
                start_row + offset
            ))
        })?;
        if embedded != canonical {
            return Err(Error::Invariant(format!(
                "embedding row ID differs from canonical row {}",
                start_row + offset
            )));
        }
    }
    if read_event_id(&mut row_ids, row_ids_path)?.is_some() {
        return Err(Error::Invariant(format!(
            "embedding row-ID file `{}` contains too many rows",
            row_ids_path.display()
        )));
    }
    Ok(())
}

fn validate_config(config: &EmbeddingBuildConfig, descriptor: &EncoderDescriptor) -> Result<()> {
    validate_artifact_name(&config.artifact_name)?;
    if config.batch_size == 0 {
        return Err(Error::Invariant(
            "embedding batch size must be positive".to_owned(),
        ));
    }
    if config.shard_rows == 0 {
        return Err(Error::Invariant(
            "embedding shard size must be positive".to_owned(),
        ));
    }
    validate_descriptor(descriptor)
}

fn validate_artifact_name(artifact_name: &str) -> Result<()> {
    if !is_safe_artifact_name(artifact_name) {
        return Err(Error::Invariant(format!(
            "embedding artifact name `{artifact_name}` is not filesystem-safe"
        )));
    }
    Ok(())
}

fn validate_descriptor(descriptor: &EncoderDescriptor) -> Result<()> {
    if descriptor.dimensions == 0 {
        return Err(Error::Invariant(
            "encoder dimensions must be positive".to_owned(),
        ));
    }
    if descriptor.quantization != "native-int8" {
        return Err(Error::Invariant(format!(
            "encoder quantization `{}` is not native-int8",
            descriptor.quantization
        )));
    }
    Ok(())
}

fn read_event_id(reader: &mut impl Read, path: &Path) -> Result<Option<EventId>> {
    let mut id = [0_u8; EVENT_ID_BYTES];
    let mut offset = 0;
    while offset < id.len() {
        let bytes = reader
            .read(&mut id[offset..])
            .map_err(|source| io_error("read", path, source))?;
        if bytes == 0 {
            if offset == 0 {
                return Ok(None);
            }
            return Err(Error::Invariant(format!(
                "canonical row file `{}` ends with a partial event ID",
                path.display()
            )));
        }
        offset += bytes;
    }
    Ok(Some(id))
}

fn create_writer(path: &Path) -> Result<BufWriter<File>> {
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    Ok(BufWriter::new(file))
}

fn finish_writer(writer: &mut BufWriter<File>, path: &Path) -> Result<()> {
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}
