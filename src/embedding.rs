//! Versioned native-INT8 embedding artifacts over canonical corpus rows.

use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::artifact::{
    ArtifactFile, describe_fixed_artifact, hash_file, is_safe_artifact_name, verify_fixed_artifact,
};
use crate::canonical::{CanonicalManifest, verify_canonical_rows};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, Error, Result, Validation, create_directory, io_error,
    ndb_error, open_ndb, read_manifest, require_directory, require_file, verify_corpus_manifest,
    write_manifest,
};
use crate::stage::CorpusStageManifest;

pub(crate) const EVENT_ID_BYTES: usize = 32;
const NORM_BYTES: usize = size_of::<f32>();
const EMBEDDING_SCHEMA_VERSION: u32 = 3;
const WORK_SCHEMA_VERSION: u32 = 1;
pub(crate) const BATCHING_RULE: &str = "effective-token-length-ascending-within-shard-v1";
pub const MATRIX_FORMAT: &str =
    "sharded-row-major-native-int8-vectors-f32le-norms-32-byte-event-ids-v1";
const LENGTH_MEASUREMENT_BATCH_ROWS: usize = 1_024;

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

    /// Return each input's post-truncation, pre-padding model-token length.
    fn effective_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>>;

    /// Encode raw kind `1` content in input order.
    fn encode(&mut self, texts: &[&str]) -> Result<Vec<i8>>;
}

/// Controls artifact partitioning without changing encoder semantics.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingBuildConfig {
    /// Filesystem-safe artifact name beneath `embeddings/`.
    pub artifact_name: String,
    /// Maximum rows submitted to the encoder at once.
    pub batch_size: usize,
    /// Maximum rows in one immutable output shard.
    pub shard_rows: u64,
}

/// Directly measured phase within the production embedding artifact path.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EmbeddingArtifactPhase {
    /// Creating and writing vector, norm, or row-ID files.
    Write,
    /// Syncing, hashing, manifesting, and atomically publishing completed work.
    Checkpoint,
}

/// Optional observations from the same resumable builder used in production.
///
/// The default methods make ordinary builds pay no storage or serialization
/// cost for benchmark data. A benchmark recorder receives only completed work;
/// a failed encoder call or unpublished shard is not reported as completed.
pub trait EmbeddingBuildObserver {
    /// Refuse to begin more production work after an external safety limit.
    fn check_continue(&mut self) -> Result<()> {
        Ok(())
    }

    /// A durable shard was verified and reused rather than recomputed.
    fn reused_shard(&mut self, _shard: &EmbeddingShardManifest) {}

    /// Effective lengths were produced by the configured production tokenizer.
    fn measured_effective_lengths(&mut self, _lengths: &[u32], _elapsed: Duration) {}

    /// One real length-sorted production batch was encoded successfully.
    fn encoded_batch(&mut self, _lengths: &[u32], _elapsed: Duration) {}

    /// One directly timed artifact-production phase completed successfully.
    fn artifact_phase(&mut self, _phase: EmbeddingArtifactPhase, _elapsed: Duration) {}

    /// A newly encoded shard reached its durable atomic checkpoint.
    fn completed_shard(&mut self, _shard: &EmbeddingShardManifest) {}
}

impl EmbeddingBuildObserver for () {}

/// Metadata for one immutable embedding shard.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingShardManifest {
    /// Zero-based shard ordinal.
    pub ordinal: u32,
    /// Global canonical row at which this shard begins.
    pub start_row: u64,
    /// Rows stored in the shard.
    pub rows: u64,
    /// Sum of post-truncation model tokens represented by this shard.
    pub effective_tokens: u64,
    /// Smallest post-truncation input length in this shard.
    pub minimum_effective_tokens: u32,
    /// Largest post-truncation input length in this shard.
    pub maximum_effective_tokens: u32,
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
    /// Earlier immutable stage artifact reused by an incremental build.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub base_artifact: Option<EmbeddingBaseArtifact>,
    /// Exact encoder identity and preprocessing contract.
    pub encoder: EncoderDescriptor,
    /// Configured build batch size.
    pub batch_size: u32,
    /// Deterministic scheduling rule used to avoid excessive padding.
    pub batching_rule: String,
    /// Versioned on-disk representation of vectors, norms, and row IDs.
    pub matrix_format: String,
    /// Configured maximum rows per shard.
    pub shard_rows: u64,
    /// Total canonical rows embedded.
    pub total_rows: u64,
    /// Ordered immutable shard metadata.
    pub shards: Vec<EmbeddingShardManifest>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct EmbeddingWorkManifest {
    schema_version: u32,
    source_snapshot_sha256: String,
    canonical_manifest_sha256: String,
    canonical_rows_sha256: String,
    selected_rows_sha256: String,
    corpus_stage: Option<EmbeddingCorpusStage>,
    encoder: EncoderDescriptor,
    batch_size: u32,
    batching_rule: String,
    matrix_format: String,
    shard_rows: u64,
    total_rows: u64,
    base_artifact: Option<EmbeddingBaseArtifact>,
}

/// Exact immutable artifact reused by an incremental embedding build.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingBaseArtifact {
    pub name: String,
    pub manifest_sha256: String,
    pub rows: u64,
}

impl DamusSnapshot {
    /// Encode every canonical row once and publish immutable INT8 shards.
    pub fn embed_canonical_corpus(
        &self,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        reject_unadmitted_cuda(encoder.descriptor())?;
        validate_config(config, encoder.descriptor())?;
        let source = self.canonical_embedding_source()?;
        self.embed_rows(config, encoder, source, None, &mut ())
    }

    /// Encode every row in one verified nested corpus stage.
    pub fn embed_corpus_stage(
        &self,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        reject_unadmitted_cuda(encoder.descriptor())?;
        validate_config(config, encoder.descriptor())?;
        let source = self.staged_embedding_source(stage_name)?;
        self.embed_rows(config, encoder, source, None, &mut ())
    }

    /// Encode one verified corpus stage while exposing production-path timings.
    pub(crate) fn embed_corpus_stage_observed(
        &self,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
        observer: &mut dyn EmbeddingBuildObserver,
    ) -> Result<EmbeddingManifest> {
        validate_config(config, encoder.descriptor())?;
        let source = self.staged_embedding_source(stage_name)?;
        self.embed_rows(config, encoder, source, None, observer)
    }

    /// Extend an aligned nested-stage artifact without re-encoding existing rows.
    pub fn extend_corpus_stage(
        &self,
        base_artifact_name: &str,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        reject_unadmitted_cuda(encoder.descriptor())?;
        validate_config(config, encoder.descriptor())?;
        validate_artifact_name(base_artifact_name)?;
        let source = self.staged_embedding_source(stage_name)?;
        let base_manifest = self.open_embedding_artifact(base_artifact_name)?;
        let base_manifest_sha256 =
            hash_file(&self.layout().embedding_manifest(base_artifact_name))?;
        validate_extension(
            base_artifact_name,
            &base_manifest,
            config,
            encoder.descriptor(),
            &source,
        )?;
        self.embed_rows(
            config,
            encoder,
            source,
            Some(BaseBuild {
                identity: EmbeddingBaseArtifact {
                    name: base_artifact_name.to_owned(),
                    manifest_sha256: base_manifest_sha256,
                    rows: base_manifest.total_rows,
                },
                manifest: base_manifest,
            }),
            &mut (),
        )
    }

    /// Execute a CUDA stage only after the budget module verifies admission.
    pub(crate) fn embed_corpus_stage_admitted(
        &self,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        validate_config(config, encoder.descriptor())?;
        let source = self.staged_embedding_source(stage_name)?;
        self.embed_rows(config, encoder, source, None, &mut ())
    }

    /// Execute an admitted CUDA extension through the same resumable builder.
    pub(crate) fn extend_corpus_stage_admitted(
        &self,
        base_artifact_name: &str,
        stage_name: &str,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingManifest> {
        validate_config(config, encoder.descriptor())?;
        validate_artifact_name(base_artifact_name)?;
        let source = self.staged_embedding_source(stage_name)?;
        let base_manifest = self.open_embedding_artifact(base_artifact_name)?;
        let base_manifest_sha256 =
            hash_file(&self.layout().embedding_manifest(base_artifact_name))?;
        validate_extension(
            base_artifact_name,
            &base_manifest,
            config,
            encoder.descriptor(),
            &source,
        )?;
        self.embed_rows(
            config,
            encoder,
            source,
            Some(BaseBuild {
                identity: EmbeddingBaseArtifact {
                    name: base_artifact_name.to_owned(),
                    manifest_sha256: base_manifest_sha256,
                    rows: base_manifest.total_rows,
                },
                manifest: base_manifest,
            }),
            &mut (),
        )
    }

    fn embed_rows(
        &self,
        config: &EmbeddingBuildConfig,
        encoder: &mut dyn EmbeddingEncoder,
        source: EmbeddingSource,
        base: Option<BaseBuild>,
        observer: &mut dyn EmbeddingBuildObserver,
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
            if manifest.batch_size != batch_size
                || manifest.batching_rule != BATCHING_RULE
                || manifest.matrix_format != MATRIX_FORMAT
                || manifest.shard_rows != config.shard_rows
            {
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
            let expected_base = base.as_ref().map(|base| &base.identity);
            if manifest.base_artifact.as_ref() != expected_base {
                return Err(Error::Invariant(
                    "existing embedding artifact has different incremental provenance".to_owned(),
                ));
            }
            for shard in &manifest.shards {
                observer.reused_shard(shard);
            }
            return Ok(manifest);
        }

        create_directory(&layout.embedding_root())?;
        let stage = layout.embedding_stage(&config.artifact_name);
        let work_manifest = EmbeddingWorkManifest {
            schema_version: WORK_SCHEMA_VERSION,
            source_snapshot_sha256: source.source_snapshot_sha256.clone(),
            canonical_manifest_sha256: source.canonical_manifest_sha256.clone(),
            canonical_rows_sha256: source.canonical_rows_sha256.clone(),
            selected_rows_sha256: source.selected_rows_sha256.clone(),
            corpus_stage: source.corpus_stage.clone(),
            encoder: encoder.descriptor().clone(),
            batch_size: u32::try_from(config.batch_size)
                .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?,
            batching_rule: BATCHING_RULE.to_owned(),
            matrix_format: MATRIX_FORMAT.to_owned(),
            shard_rows: config.shard_rows,
            total_rows: source.rows,
            base_artifact: base.as_ref().map(|base| base.identity.clone()),
        };
        prepare_embedding_stage(&stage, &work_manifest)?;
        if let Some(base) = &base {
            seed_base_shards(
                &layout.embedding_dir(&base.identity.name),
                &stage,
                &base.manifest.shards,
            )?;
        }

        let corpus = open_ndb(&corpus_path, Validation::TrustedSource)?;
        let txn = Transaction::new(&corpus)
            .map_err(|source| ndb_error("open transaction on", &corpus_path, source))?;
        let mut rows = BufReader::new(
            File::open(&source.rows_path)
                .map_err(|error| io_error("open", &source.rows_path, error))?,
        );
        let mut shards =
            load_completed_shards(&stage, &source, config.shard_rows, encoder.descriptor())?;
        for shard in &shards {
            observer.reused_shard(shard);
        }
        let mut next_row = shards
            .last()
            .map_or(0, |shard| shard.start_row + shard.rows);
        rows.seek(SeekFrom::Start(
            next_row
                .checked_mul(EVENT_ID_BYTES as u64)
                .ok_or_else(|| Error::Invariant("embedding row offset overflowed".to_owned()))?,
        ))
        .map_err(|error| io_error("seek", &source.rows_path, error))?;
        {
            let mut build = EmbeddingShardBuilder::new(
                &stage,
                config.batch_size,
                encoder,
                &corpus,
                &txn,
                &corpus_path,
                &mut rows,
                &source.rows_path,
                observer,
            );

            while next_row < source.rows {
                build.observer.check_continue()?;
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
            schema_version: EMBEDDING_SCHEMA_VERSION,
            source_snapshot_sha256: source.source_snapshot_sha256,
            canonical_manifest_sha256: source.canonical_manifest_sha256,
            canonical_rows_sha256: source.canonical_rows_sha256,
            corpus_stage: source.corpus_stage,
            base_artifact: base.as_ref().map(|base| base.identity.clone()),
            encoder: encoder.descriptor().clone(),
            batch_size: u32::try_from(config.batch_size)
                .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?,
            batching_rule: BATCHING_RULE.to_owned(),
            matrix_format: MATRIX_FORMAT.to_owned(),
            shard_rows: config.shard_rows,
            total_rows: next_row,
            shards,
        };
        let checkpoint_started = Instant::now();
        write_or_verify_manifest(&stage.join("manifest.json"), &manifest)?;
        drop(txn);
        drop(corpus);
        self.publish_stage(&stage, &artifact)?;
        observer.artifact_phase(
            EmbeddingArtifactPhase::Checkpoint,
            checkpoint_started.elapsed(),
        );
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
        let layout = self.layout();
        let manifest_path = layout.canonical_manifest();
        let rows_path = layout.canonical_rows();
        let corpus_manifest_path = layout.corpus_manifest();
        require_file(&manifest_path)?;
        require_file(&rows_path)?;
        require_file(&corpus_manifest_path)?;
        let corpus: CorpusManifest = read_manifest(&corpus_manifest_path)?;
        verify_corpus_manifest(&corpus)?;
        let canonical: CanonicalManifest = read_manifest(&manifest_path)?;
        verify_canonical_rows(&layout.canonical_dir(), &canonical)?;
        if canonical.source_snapshot_sha256 != corpus.source_snapshot_sha256
            || canonical.eligibility != corpus.eligibility
            || canonical.counts.eligible_events != corpus.eligible_events
        {
            return Err(Error::Invariant(
                "canonical manifest was derived from a different corpus contract".to_owned(),
            ));
        }
        let manifest_sha256 = hash_file(&manifest_path)?;
        let rows_sha256 = canonical.rows.sha256.clone();
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

#[derive(Clone)]
struct EmbeddingSource {
    source_snapshot_sha256: String,
    canonical_manifest_sha256: String,
    canonical_rows_sha256: String,
    selected_rows_sha256: String,
    rows_path: PathBuf,
    rows: u64,
    corpus_stage: Option<EmbeddingCorpusStage>,
}

struct BaseBuild {
    identity: EmbeddingBaseArtifact,
    manifest: EmbeddingManifest,
}

fn validate_extension(
    base_name: &str,
    base: &EmbeddingManifest,
    config: &EmbeddingBuildConfig,
    descriptor: &EncoderDescriptor,
    target: &EmbeddingSource,
) -> Result<()> {
    let target_stage = target.corpus_stage.as_ref().ok_or_else(|| {
        Error::Invariant("embedding extension requires a selected corpus stage".to_owned())
    })?;
    let base_stage = base.corpus_stage.as_ref().ok_or_else(|| {
        Error::Invariant(format!(
            "base embedding artifact `{base_name}` does not represent a corpus stage"
        ))
    })?;
    let batch_size = u32::try_from(config.batch_size)
        .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?;
    if base.encoder != *descriptor
        || base.batch_size != batch_size
        || base.batching_rule != BATCHING_RULE
        || base.matrix_format != MATRIX_FORMAT
        || base.shard_rows != config.shard_rows
    {
        return Err(Error::Invariant(format!(
            "base embedding artifact `{base_name}` has incompatible encoder or build settings"
        )));
    }
    if base.canonical_manifest_sha256 != target.canonical_manifest_sha256
        || base.canonical_rows_sha256 != target.canonical_rows_sha256
        || base.source_snapshot_sha256 != target.source_snapshot_sha256
        || base_stage.selection_rule != target_stage.selection_rule
    {
        return Err(Error::Invariant(format!(
            "base embedding artifact `{base_name}` belongs to a different canonical reservoir"
        )));
    }
    if base.total_rows == 0 || base.total_rows >= target.rows {
        return Err(Error::Invariant(format!(
            "base embedding artifact `{base_name}` must be a smaller nonempty corpus prefix"
        )));
    }
    if !base.total_rows.is_multiple_of(base.shard_rows) {
        return Err(Error::Invariant(format!(
            "base embedding artifact `{base_name}` ends with a partial shard and cannot be extended without mutating it"
        )));
    }
    Ok(())
}

fn prepare_embedding_stage(stage: &Path, expected: &EmbeddingWorkManifest) -> Result<bool> {
    if stage.exists() {
        require_directory(stage)?;
        let manifest_path = stage.join("build.json");
        require_file(&manifest_path)?;
        let actual: EmbeddingWorkManifest = read_manifest(&manifest_path)?;
        if &actual != expected {
            return Err(Error::Invariant(format!(
                "incomplete embedding stage `{}` belongs to different build inputs",
                stage.display()
            )));
        }
        let temporary_shards = stage.join("shards");
        require_directory(&temporary_shards)?;
        for entry in std::fs::read_dir(&temporary_shards)
            .map_err(|source| io_error("read", &temporary_shards, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &temporary_shards, source))?;
            let name = entry.file_name();
            if name.to_string_lossy().starts_with('.') {
                let path = entry.path();
                if path.is_dir() {
                    std::fs::remove_dir_all(&path)
                        .map_err(|source| io_error("remove", &path, source))?;
                } else {
                    std::fs::remove_file(&path)
                        .map_err(|source| io_error("remove", &path, source))?;
                }
            }
        }
        return Ok(false);
    }
    let parent = stage.parent().ok_or_else(|| {
        Error::Invariant(format!(
            "embedding stage `{}` has no parent",
            stage.display()
        ))
    })?;
    create_directory(parent)?;
    std::fs::create_dir(stage).map_err(|source| io_error("create", stage, source))?;
    create_directory(&stage.join("shards"))?;
    write_manifest(&stage.join("build.json"), expected)?;
    Ok(true)
}

fn seed_base_shards(
    base_root: &Path,
    stage: &Path,
    shards: &[EmbeddingShardManifest],
) -> Result<()> {
    for shard in shards {
        let relative_dir = format!("shards/{:06}", shard.ordinal);
        let source_dir = base_root.join(&relative_dir);
        let target_dir = stage.join(&relative_dir);
        require_directory(&source_dir)?;
        let dimensions = usize::try_from(shard.vectors.record_bytes)
            .map_err(|_| Error::Invariant("base vector width does not fit usize".to_owned()))?;
        if target_dir.exists() {
            require_directory(&target_dir)?;
            let existing: EmbeddingShardManifest =
                read_manifest(&target_dir.join("manifest.json"))?;
            if &existing != shard {
                return Err(Error::Invariant(format!(
                    "seeded base shard {} has different provenance",
                    shard.ordinal
                )));
            }
            verify_shard_files(stage, shard, dimensions)?;
            continue;
        }
        let temporary_dir = stage.join(format!("shards/.{:06}.base.tmp", shard.ordinal));
        if temporary_dir.exists() {
            std::fs::remove_dir_all(&temporary_dir)
                .map_err(|source| io_error("remove", &temporary_dir, source))?;
        }
        std::fs::create_dir(&temporary_dir)
            .map_err(|source| io_error("create", &temporary_dir, source))?;
        for file in ["vectors.i8", "norms.f32le", "row_ids.bin"] {
            link_or_copy(&source_dir.join(file), &temporary_dir.join(file))?;
        }
        write_manifest(&temporary_dir.join("manifest.json"), shard)?;
        std::fs::rename(&temporary_dir, &target_dir)
            .map_err(|source| io_error("publish", &target_dir, source))?;
        verify_shard_files(stage, shard, dimensions)?;
    }
    Ok(())
}

fn link_or_copy(source: &Path, target: &Path) -> Result<()> {
    match std::fs::hard_link(source, target) {
        Ok(()) => Ok(()),
        Err(link_error) => {
            std::fs::copy(source, target).map_err(|copy_error| {
                Error::Invariant(format!(
                    "failed to hard-link `{}` to `{}` ({link_error}) and copy fallback failed ({copy_error})",
                    source.display(),
                    target.display()
                ))
            })?;
            Ok(())
        }
    }
}

fn load_completed_shards(
    stage: &Path,
    source: &EmbeddingSource,
    shard_rows: u64,
    descriptor: &EncoderDescriptor,
) -> Result<Vec<EmbeddingShardManifest>> {
    let dimensions = usize::try_from(descriptor.dimensions)
        .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
    let mut shards = Vec::new();
    let mut start_row = 0_u64;
    while start_row < source.rows {
        let ordinal = u32::try_from(shards.len())
            .map_err(|_| Error::Invariant("shard ordinal does not fit u32".to_owned()))?;
        let relative_dir = format!("shards/{ordinal:06}");
        let root = stage.join(&relative_dir);
        if !root.exists() {
            break;
        }
        require_directory(&root)?;
        let manifest_path = root.join("manifest.json");
        require_file(&manifest_path)?;
        let shard: EmbeddingShardManifest = read_manifest(&manifest_path)?;
        let expected_rows = shard_rows.min(source.rows - start_row);
        if shard.ordinal != ordinal || shard.start_row != start_row || shard.rows != expected_rows {
            return Err(Error::Invariant(format!(
                "completed embedding shard {ordinal} does not match the requested partition"
            )));
        }
        verify_shard_files(stage, &shard, dimensions)?;
        let mut canonical_rows = BufReader::new(
            File::open(&source.rows_path)
                .map_err(|error| io_error("open", &source.rows_path, error))?,
        );
        canonical_rows
            .seek(SeekFrom::Start(
                start_row
                    .checked_mul(EVENT_ID_BYTES as u64)
                    .ok_or_else(|| {
                        Error::Invariant("canonical row verification offset overflowed".to_owned())
                    })?,
            ))
            .map_err(|error| io_error("seek", &source.rows_path, error))?;
        verify_row_ids(
            &stage.join(&shard.row_ids.file),
            shard.rows,
            &mut canonical_rows,
            &source.rows_path,
            start_row,
        )?;
        start_row = start_row
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("completed shard rows overflowed".to_owned()))?;
        shards.push(shard);
    }
    let shard_root = stage.join("shards");
    for entry in
        std::fs::read_dir(&shard_root).map_err(|error| io_error("read", &shard_root, error))?
    {
        let entry = entry.map_err(|error| io_error("read", &shard_root, error))?;
        let name = entry.file_name().to_string_lossy().into_owned();
        if name.starts_with('.') {
            continue;
        }
        let parsed = (name.len() == 6 && name.bytes().all(|byte| byte.is_ascii_digit()))
            .then(|| name.parse::<usize>().ok())
            .flatten();
        if !entry.path().is_dir() || parsed.is_none_or(|ordinal| ordinal >= shards.len()) {
            return Err(Error::Invariant(format!(
                "incomplete embedding stage contains unexpected shard `{name}`"
            )));
        }
    }
    Ok(shards)
}

pub(crate) struct EmbeddingShardBuilder<'a> {
    stage: &'a Path,
    batch_size: usize,
    encoder: &'a mut dyn EmbeddingEncoder,
    corpus: &'a nostrdb::Ndb,
    txn: &'a Transaction,
    corpus_path: &'a Path,
    canonical_rows: &'a mut BufReader<File>,
    canonical_rows_path: &'a Path,
    observer: &'a mut dyn EmbeddingBuildObserver,
}

impl<'a> EmbeddingShardBuilder<'a> {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        stage: &'a Path,
        batch_size: usize,
        encoder: &'a mut dyn EmbeddingEncoder,
        corpus: &'a nostrdb::Ndb,
        txn: &'a Transaction,
        corpus_path: &'a Path,
        canonical_rows: &'a mut BufReader<File>,
        canonical_rows_path: &'a Path,
        observer: &'a mut dyn EmbeddingBuildObserver,
    ) -> Self {
        Self {
            stage,
            batch_size,
            encoder,
            corpus,
            txn,
            corpus_path,
            canonical_rows,
            canonical_rows_path,
            observer,
        }
    }

    pub(crate) fn encode_shard(
        &mut self,
        ordinal: u32,
        start_row: u64,
        row_count: u64,
    ) -> Result<EmbeddingShardManifest> {
        let relative_dir = format!("shards/{ordinal:06}");
        let shard_dir = self.stage.join(&relative_dir);
        if shard_dir.exists() {
            return Err(Error::Invariant(format!(
                "embedding shard `{}` already exists",
                shard_dir.display()
            )));
        }
        let temporary_dir = self.stage.join(format!("shards/.{ordinal:06}.tmp"));
        if temporary_dir.exists() {
            std::fs::remove_dir_all(&temporary_dir)
                .map_err(|source| io_error("remove", &temporary_dir, source))?;
        }
        std::fs::create_dir(&temporary_dir)
            .map_err(|source| io_error("create", &temporary_dir, source))?;
        let vectors_path = temporary_dir.join("vectors.i8");
        let norms_path = temporary_dir.join("norms.f32le");
        let row_ids_path = temporary_dir.join("row_ids.bin");
        let dimensions = usize::try_from(self.encoder.descriptor().dimensions)
            .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
        let row_count_usize = usize::try_from(row_count)
            .map_err(|_| Error::Invariant("shard row count does not fit usize".to_owned()))?;
        let mut ids = Vec::with_capacity(row_count_usize);
        for offset in 0..row_count {
            ids.push(
                read_event_id(self.canonical_rows, self.canonical_rows_path)?.ok_or_else(|| {
                    Error::Invariant(format!(
                        "canonical row file ended before row {}",
                        start_row + offset
                    ))
                })?,
            );
        }
        let row_ids_started = Instant::now();
        let mut row_ids = create_writer(&row_ids_path)?;
        for id in &ids {
            row_ids
                .write_all(id)
                .map_err(|source| io_error("write", &row_ids_path, source))?;
        }
        finish_writer(&mut row_ids, &row_ids_path)?;
        self.observer
            .artifact_phase(EmbeddingArtifactPhase::Write, row_ids_started.elapsed());

        let mut schedule = Vec::with_capacity(ids.len());
        for (chunk_index, chunk) in ids.chunks(LENGTH_MEASUREMENT_BATCH_ROWS).enumerate() {
            self.observer.check_continue()?;
            let texts = self.texts_for_ids(chunk)?;
            let text_refs = texts.iter().map(String::as_str).collect::<Vec<_>>();
            let lengths_started = Instant::now();
            let lengths = self.encoder.effective_token_lengths(&text_refs)?;
            let lengths_elapsed = lengths_started.elapsed();
            if lengths.len() != chunk.len() {
                return Err(Error::Invariant(format!(
                    "encoder returned {} effective lengths for {} rows",
                    lengths.len(),
                    chunk.len()
                )));
            }
            for (offset, length) in lengths.iter().copied().enumerate() {
                if length == 0 || length > self.encoder.descriptor().max_tokens {
                    return Err(Error::Invariant(format!(
                        "encoder reported invalid effective token length {length}"
                    )));
                }
                let row_offset = chunk_index
                    .checked_mul(LENGTH_MEASUREMENT_BATCH_ROWS)
                    .and_then(|base| base.checked_add(offset))
                    .ok_or_else(|| {
                        Error::Invariant("shard schedule offset overflowed".to_owned())
                    })?;
                schedule.push(RowSchedule { row_offset, length });
            }
            self.observer
                .measured_effective_lengths(&lengths, lengths_elapsed);
            self.observer.check_continue()?;
        }
        schedule.sort_unstable_by_key(|row| (row.length, row.row_offset));

        let vectors_bytes = row_count
            .checked_mul(u64::try_from(dimensions).expect("dimensions fit u64"))
            .ok_or_else(|| Error::Invariant("vector file size overflowed".to_owned()))?;
        let norms_bytes = row_count
            .checked_mul(NORM_BYTES as u64)
            .ok_or_else(|| Error::Invariant("norm file size overflowed".to_owned()))?;
        let file_create_started = Instant::now();
        let mut vectors = create_random_access_file(&vectors_path, vectors_bytes)?;
        let mut norms = create_random_access_file(&norms_path, norms_bytes)?;
        self.observer
            .artifact_phase(EmbeddingArtifactPhase::Write, file_create_started.elapsed());
        let mut written = 0_u64;
        for batch in schedule.chunks(self.batch_size) {
            self.observer.check_continue()?;
            let batch_ids = batch
                .iter()
                .map(|row| ids[row.row_offset])
                .collect::<Vec<_>>();
            let texts = self.texts_for_ids(&batch_ids)?;
            let text_refs = texts.iter().map(String::as_str).collect::<Vec<_>>();
            let encode_started = Instant::now();
            let encoded = self.encoder.encode(&text_refs)?;
            let encode_elapsed = encode_started.elapsed();
            let expected = batch.len().checked_mul(dimensions).ok_or_else(|| {
                Error::Invariant("encoded batch element count overflowed usize".to_owned())
            })?;
            if encoded.len() != expected {
                return Err(Error::Invariant(format!(
                    "encoder returned {} elements for {} rows at {dimensions} dimensions",
                    encoded.len(),
                    batch.len()
                )));
            }
            let batch_lengths = batch.iter().map(|row| row.length).collect::<Vec<_>>();
            self.observer.encoded_batch(&batch_lengths, encode_elapsed);
            self.observer.check_continue()?;
            let artifact_write_started = Instant::now();
            let encoded_bytes = encoded.iter().map(|value| *value as u8).collect::<Vec<_>>();
            for ((row, vector), vector_bytes) in batch
                .iter()
                .zip(encoded.chunks_exact(dimensions))
                .zip(encoded_bytes.chunks_exact(dimensions))
            {
                let vector_offset = u64::try_from(row.row_offset)
                    .expect("row offset fits u64")
                    .checked_mul(u64::try_from(dimensions).expect("dimensions fit u64"))
                    .ok_or_else(|| Error::Invariant("vector write offset overflowed".to_owned()))?;
                write_at(&mut vectors, &vectors_path, vector_offset, vector_bytes)?;
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
                        start_row + u64::try_from(row.row_offset).expect("row offset fits u64")
                    )));
                }
                let norm_offset = u64::try_from(row.row_offset)
                    .expect("row offset fits u64")
                    .checked_mul(NORM_BYTES as u64)
                    .ok_or_else(|| Error::Invariant("norm write offset overflowed".to_owned()))?;
                write_at(&mut norms, &norms_path, norm_offset, &norm.to_le_bytes())?;
                written = written
                    .checked_add(1)
                    .ok_or_else(|| Error::Invariant("shard row count overflowed u64".to_owned()))?;
            }
            self.observer.artifact_phase(
                EmbeddingArtifactPhase::Write,
                artifact_write_started.elapsed(),
            );
            self.observer.check_continue()?;
        }
        let checkpoint_started = Instant::now();
        vectors
            .sync_all()
            .map_err(|source| io_error("sync", &vectors_path, source))?;
        norms
            .sync_all()
            .map_err(|source| io_error("sync", &norms_path, source))?;
        let effective_tokens = schedule
            .iter()
            .try_fold(0_u64, |sum, row| sum.checked_add(u64::from(row.length)))
            .ok_or_else(|| Error::Invariant("effective token count overflowed".to_owned()))?;
        let manifest = EmbeddingShardManifest {
            ordinal,
            start_row,
            rows: written,
            effective_tokens,
            minimum_effective_tokens: schedule
                .first()
                .map(|row| row.length)
                .ok_or_else(|| Error::Invariant("cannot encode an empty shard".to_owned()))?,
            maximum_effective_tokens: schedule
                .last()
                .map(|row| row.length)
                .ok_or_else(|| Error::Invariant("cannot encode an empty shard".to_owned()))?,
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
        };
        write_manifest(&temporary_dir.join("manifest.json"), &manifest)?;
        std::fs::rename(&temporary_dir, &shard_dir)
            .map_err(|source| io_error("publish", &shard_dir, source))?;
        self.observer.artifact_phase(
            EmbeddingArtifactPhase::Checkpoint,
            checkpoint_started.elapsed(),
        );
        self.observer.completed_shard(&manifest);
        Ok(manifest)
    }

    fn texts_for_ids(&self, ids: &[EventId]) -> Result<Vec<String>> {
        ids.iter()
            .map(|id| {
                self.corpus
                    .get_note_by_id(self.txn, id)
                    .map(|note| note.content().to_owned())
                    .map_err(|source| {
                        ndb_error("load canonical note from", self.corpus_path, source)
                    })
            })
            .collect()
    }
}

#[derive(Clone, Copy)]
struct RowSchedule {
    row_offset: usize,
    length: u32,
}

fn create_random_access_file(path: &Path, bytes: u64) -> Result<File> {
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    file.set_len(bytes)
        .map_err(|source| io_error("resize", path, source))?;
    Ok(file)
}

fn write_at(file: &mut File, path: &Path, offset: u64, bytes: &[u8]) -> Result<()> {
    file.seek(SeekFrom::Start(offset))
        .map_err(|source| io_error("seek", path, source))?;
    file.write_all(bytes)
        .map_err(|source| io_error("write", path, source))
}

fn verify_embedding(
    artifact: &Path,
    manifest: EmbeddingManifest,
    source: &EmbeddingSource,
) -> Result<EmbeddingManifest> {
    require_directory(artifact)?;
    if manifest.schema_version != EMBEDDING_SCHEMA_VERSION {
        return Err(Error::Invariant(format!(
            "embedding manifest schema {} is unsupported; expected {EMBEDDING_SCHEMA_VERSION}",
            manifest.schema_version,
        )));
    }
    if manifest.batch_size == 0 || manifest.shard_rows == 0 {
        return Err(Error::Invariant(
            "embedding manifest contains zero-sized build settings".to_owned(),
        ));
    }
    validate_descriptor(&manifest.encoder)?;
    if manifest.batching_rule != BATCHING_RULE || manifest.matrix_format != MATRIX_FORMAT {
        return Err(Error::Invariant(
            "embedding manifest contains unsupported batching or matrix semantics".to_owned(),
        ));
    }
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
    verify_base_artifact(&manifest)?;

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
        verify_shard_files(artifact, shard, dimensions)?;
        verify_effective_token_metadata(shard, manifest.encoder.max_tokens)?;
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

fn verify_base_artifact(manifest: &EmbeddingManifest) -> Result<()> {
    let Some(identity) = &manifest.base_artifact else {
        return Ok(());
    };
    validate_artifact_name(&identity.name)?;
    if identity.rows == 0
        || identity.rows >= manifest.total_rows
        || !identity.rows.is_multiple_of(manifest.shard_rows)
        || manifest.corpus_stage.is_none()
        || identity.manifest_sha256.len() != 64
        || !identity
            .manifest_sha256
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(Error::Invariant(
            "incremental embedding base has an invalid aligned row range".to_owned(),
        ));
    }
    let base_shards = identity.rows / manifest.shard_rows;
    if u64::try_from(manifest.shards.len()).map_or(true, |shards| shards < base_shards) {
        return Err(Error::Invariant(
            "incremental embedding artifact does not intrinsically cover its recorded base rows"
                .to_owned(),
        ));
    }
    Ok(())
}

pub(crate) fn verify_shard_files(
    artifact: &Path,
    shard: &EmbeddingShardManifest,
    dimensions: usize,
) -> Result<()> {
    let relative_dir = format!("shards/{:06}", shard.ordinal);
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
    Ok(())
}

pub(crate) fn verify_effective_token_metadata(
    shard: &EmbeddingShardManifest,
    max_tokens: u32,
) -> Result<()> {
    let minimum_effective_tokens = shard
        .rows
        .checked_mul(u64::from(shard.minimum_effective_tokens))
        .ok_or_else(|| Error::Invariant("minimum effective-token bound overflowed".to_owned()))?;
    let maximum_effective_tokens = shard
        .rows
        .checked_mul(u64::from(shard.maximum_effective_tokens))
        .ok_or_else(|| Error::Invariant("maximum effective-token bound overflowed".to_owned()))?;
    if shard.minimum_effective_tokens == 0
        || shard.minimum_effective_tokens > shard.maximum_effective_tokens
        || shard.maximum_effective_tokens > max_tokens
        || shard.effective_tokens < minimum_effective_tokens
        || shard.effective_tokens > maximum_effective_tokens
    {
        return Err(Error::Invariant(format!(
            "embedding shard {} contains invalid effective-token metadata",
            shard.ordinal
        )));
    }
    Ok(())
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

pub(crate) fn validate_config(
    config: &EmbeddingBuildConfig,
    descriptor: &EncoderDescriptor,
) -> Result<()> {
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

pub(crate) fn reject_unadmitted_cuda(descriptor: &EncoderDescriptor) -> Result<()> {
    if descriptor.execution_provider == "cuda" {
        return Err(Error::Budget(
            "ordinary embedding APIs refuse CUDA; use the capped benchmark or verified admission path"
                .to_owned(),
        ));
    }
    Ok(())
}

fn validate_artifact_name(artifact_name: &str) -> Result<()> {
    if !is_safe_artifact_name(artifact_name) {
        return Err(Error::Invariant(format!(
            "embedding artifact name `{artifact_name}` is not filesystem-safe"
        )));
    }
    Ok(())
}

pub(crate) fn validate_descriptor(descriptor: &EncoderDescriptor) -> Result<()> {
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

pub(crate) fn read_event_id(reader: &mut impl Read, path: &Path) -> Result<Option<EventId>> {
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

fn write_or_verify_manifest<T>(path: &Path, manifest: &T) -> Result<()>
where
    T: Serialize + serde::de::DeserializeOwned + PartialEq,
{
    if path.exists() {
        let existing: T = read_manifest(path)?;
        if &existing != manifest {
            return Err(Error::Invariant(format!(
                "existing final manifest `{}` belongs to different completed work",
                path.display()
            )));
        }
        return Ok(());
    }
    write_manifest(path, manifest)
}
