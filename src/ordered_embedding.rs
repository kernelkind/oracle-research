//! Native-INT8 embeddings over a deterministic prefix of the final corpus.

use std::fs::{self, File};
use std::io::{BufReader, Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::time::Instant;

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::artifact::hash_file;
use crate::embedding::{
    BATCHING_RULE, EVENT_ID_BYTES, EmbeddingEncoder, EmbeddingShardBuilder, EmbeddingShardManifest,
    EncoderDescriptor, MATRIX_FORMAT, read_event_id, reject_unadmitted_cuda, validate_descriptor,
    verify_effective_token_metadata, verify_shard_files,
};
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_ndb, read_manifest, require_directory,
    require_file, write_manifest,
};

const SCHEMA_VERSION: u32 = 1;
const SELECTION_RULE: &str = "first-ordered-event-ids-v1";

/// Fixed inputs for one deterministic final-corpus embedding prefix.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrderedEmbeddingBuildConfig {
    /// Number of ordered corpus rows to embed.
    pub rows: u64,
    /// Maximum rows in one model call.
    pub batch_size: usize,
    /// Maximum rows in one immutable artifact shard.
    pub shard_rows: u64,
}

/// Earlier immutable rows copied into a self-contained extension artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OrderedEmbeddingBaseArtifact {
    /// SHA-256 of the base artifact manifest.
    pub manifest_sha256: String,
    /// Ordered rows supplied by the base artifact.
    pub rows: u64,
}

/// Durable identity and files for one final-corpus embedding prefix.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OrderedEmbeddingManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 of the complete deterministic event-ID order.
    pub ordered_event_ids_sha256: String,
    /// Complete event-ID records available in the ordered source.
    pub available_rows: u64,
    /// Rule selecting this artifact's rows from the ordered source.
    pub selection_rule: String,
    /// Exact model, runtime, and preprocessing identity.
    pub encoder: EncoderDescriptor,
    /// Maximum rows submitted to the encoder at once.
    pub batch_size: u32,
    /// Deterministic batching rule shared with the existing embedding builder.
    pub batching_rule: String,
    /// Shared vector, norm, and row-ID representation.
    pub matrix_format: String,
    /// Maximum rows in each immutable shard.
    pub shard_rows: u64,
    /// Ordered prefix rows represented by this artifact.
    pub total_rows: u64,
    /// Optional earlier artifact reused without inference.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub base_artifact: Option<OrderedEmbeddingBaseArtifact>,
    /// Complete ordered shard list.
    pub shards: Vec<EmbeddingShardManifest>,
}

/// Result of one build or extension invocation.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct OrderedEmbeddingBuildResult {
    /// Fully verified completed manifest.
    pub manifest: OrderedEmbeddingManifest,
    /// Rows encoded during this invocation rather than reused.
    pub encoded_rows: u64,
    /// Complete invocation wall time, including verification and publication.
    pub elapsed_milliseconds: u64,
}

/// Embed a prefix without an earlier embedding artifact.
pub fn build_ordered_embeddings(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &OrderedEmbeddingBuildConfig,
    encoder: &mut dyn EmbeddingEncoder,
) -> Result<OrderedEmbeddingBuildResult> {
    build(
        corpus_path.as_ref(),
        ordered_event_ids_path.as_ref(),
        None,
        output_path.as_ref(),
        config,
        encoder,
    )
}

/// Extend an earlier aligned prefix without re-encoding its rows.
pub fn extend_ordered_embeddings(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    base_artifact_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &OrderedEmbeddingBuildConfig,
    encoder: &mut dyn EmbeddingEncoder,
) -> Result<OrderedEmbeddingBuildResult> {
    build(
        corpus_path.as_ref(),
        ordered_event_ids_path.as_ref(),
        Some(base_artifact_path.as_ref()),
        output_path.as_ref(),
        config,
        encoder,
    )
}

/// Reopen and fully verify an artifact without loading the encoder.
pub fn open_ordered_embedding_artifact(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    artifact_path: impl AsRef<Path>,
) -> Result<OrderedEmbeddingManifest> {
    let artifact_path = artifact_path.as_ref();
    require_directory(artifact_path)?;
    let manifest_path = artifact_path.join("manifest.json");
    require_file(&manifest_path)?;
    let manifest: OrderedEmbeddingManifest = read_manifest(&manifest_path)?;
    verify_artifact(
        corpus_path.as_ref(),
        ordered_event_ids_path.as_ref(),
        artifact_path,
        manifest,
    )
}

fn build(
    corpus_path: &Path,
    ordered_event_ids_path: &Path,
    base_artifact_path: Option<&Path>,
    output_path: &Path,
    config: &OrderedEmbeddingBuildConfig,
    encoder: &mut dyn EmbeddingEncoder,
) -> Result<OrderedEmbeddingBuildResult> {
    let started = Instant::now();
    require_directory(corpus_path)?;
    require_file(ordered_event_ids_path)?;
    validate_build_config(config, encoder.descriptor())?;
    reject_unadmitted_cuda(encoder.descriptor())?;
    let source = source_identity(ordered_event_ids_path)?;
    if config.rows > source.available_rows {
        return Err(Error::Invariant(format!(
            "requested {} embedding rows but the ordered corpus contains {}",
            config.rows, source.available_rows
        )));
    }

    let base = match base_artifact_path {
        Some(path) => {
            let manifest =
                open_ordered_embedding_artifact(corpus_path, ordered_event_ids_path, path)?;
            validate_base(path, &manifest, &source, config, encoder.descriptor())?;
            Some(BaseBuild {
                identity: OrderedEmbeddingBaseArtifact {
                    manifest_sha256: hash_file(&path.join("manifest.json"))?,
                    rows: manifest.total_rows,
                },
                path: path.to_owned(),
                manifest,
            })
        }
        None => None,
    };
    let expected_base = base.as_ref().map(|base| base.identity.clone());

    if output_path.exists() {
        let manifest =
            open_ordered_embedding_artifact(corpus_path, ordered_event_ids_path, output_path)?;
        validate_completed(
            &manifest,
            &source,
            config,
            encoder.descriptor(),
            expected_base.as_ref(),
        )?;
        return Ok(OrderedEmbeddingBuildResult {
            manifest,
            encoded_rows: 0,
            elapsed_milliseconds: elapsed_milliseconds(started),
        });
    }

    let stage = create_stage_directory(output_path)?;
    let result = build_in_stage(
        corpus_path,
        ordered_event_ids_path,
        &stage,
        &source,
        base.as_ref(),
        config,
        encoder,
    );
    let (manifest, encoded_rows) = match result {
        Ok(result) => result,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage);
            return Err(error);
        }
    };
    if output_path.exists() {
        let _ = fs::remove_dir_all(&stage);
        return Err(Error::ArtifactExists(output_path.to_owned()));
    }
    fs::rename(&stage, output_path).map_err(|source| io_error("publish", output_path, source))?;
    if let Some(parent) = output_path.parent() {
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", parent, source))?;
    }
    Ok(OrderedEmbeddingBuildResult {
        manifest,
        encoded_rows,
        elapsed_milliseconds: elapsed_milliseconds(started),
    })
}

#[allow(clippy::too_many_arguments)]
fn build_in_stage(
    corpus_path: &Path,
    ordered_event_ids_path: &Path,
    stage: &Path,
    source: &OrderedSourceIdentity,
    base: Option<&BaseBuild>,
    config: &OrderedEmbeddingBuildConfig,
    encoder: &mut dyn EmbeddingEncoder,
) -> Result<(OrderedEmbeddingManifest, u64)> {
    fs::create_dir(stage.join("shards"))
        .map_err(|source| io_error("create", stage.join("shards"), source))?;
    let mut shards = match base {
        Some(base) => {
            copy_base_shards(&base.path, stage, &base.manifest.shards)?;
            base.manifest.shards.clone()
        }
        None => Vec::new(),
    };
    let start_row = base.map_or(0, |base| base.manifest.total_rows);
    let corpus = open_ndb(corpus_path, Validation::TrustedSource)?;
    let txn = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut rows = BufReader::new(
        File::open(ordered_event_ids_path)
            .map_err(|source| io_error("open", ordered_event_ids_path, source))?,
    );
    rows.seek(SeekFrom::Start(
        start_row
            .checked_mul(EVENT_ID_BYTES as u64)
            .ok_or_else(|| Error::Invariant("embedding row offset overflowed".to_owned()))?,
    ))
    .map_err(|source| io_error("seek", ordered_event_ids_path, source))?;
    let mut next_row = start_row;
    let mut observer = ();
    {
        let mut builder = EmbeddingShardBuilder::new(
            stage,
            config.batch_size,
            encoder,
            &corpus,
            &txn,
            corpus_path,
            &mut rows,
            ordered_event_ids_path,
            &mut observer,
        );
        while next_row < config.rows {
            let ordinal = u32::try_from(shards.len())
                .map_err(|_| Error::Invariant("shard ordinal does not fit u32".to_owned()))?;
            let rows_in_shard = config.shard_rows.min(config.rows - next_row);
            let shard = builder.encode_shard(ordinal, next_row, rows_in_shard)?;
            next_row = next_row
                .checked_add(rows_in_shard)
                .ok_or_else(|| Error::Invariant("embedded row count overflowed".to_owned()))?;
            shards.push(shard);
        }
    }
    drop(txn);
    drop(corpus);

    let manifest = OrderedEmbeddingManifest {
        schema_version: SCHEMA_VERSION,
        ordered_event_ids_sha256: source.sha256.clone(),
        available_rows: source.available_rows,
        selection_rule: SELECTION_RULE.to_owned(),
        encoder: encoder.descriptor().clone(),
        batch_size: u32::try_from(config.batch_size)
            .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?,
        batching_rule: BATCHING_RULE.to_owned(),
        matrix_format: MATRIX_FORMAT.to_owned(),
        shard_rows: config.shard_rows,
        total_rows: config.rows,
        base_artifact: base.map(|base| base.identity.clone()),
        shards,
    };
    write_manifest(&stage.join("manifest.json"), &manifest)?;
    let verified = verify_artifact(corpus_path, ordered_event_ids_path, stage, manifest)?;
    Ok((verified, config.rows - start_row))
}

fn verify_artifact(
    corpus_path: &Path,
    ordered_event_ids_path: &Path,
    artifact_path: &Path,
    manifest: OrderedEmbeddingManifest,
) -> Result<OrderedEmbeddingManifest> {
    let source = source_identity(ordered_event_ids_path)?;
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.ordered_event_ids_sha256 != source.sha256
        || manifest.available_rows != source.available_rows
        || manifest.selection_rule != SELECTION_RULE
        || manifest.batching_rule != BATCHING_RULE
        || manifest.matrix_format != MATRIX_FORMAT
        || manifest.batch_size == 0
        || manifest.shard_rows == 0
        || manifest.total_rows == 0
        || manifest.total_rows > manifest.available_rows
    {
        return Err(Error::Invariant(
            "ordered embedding manifest has incompatible source or build rules".to_owned(),
        ));
    }
    validate_descriptor(&manifest.encoder)?;
    verify_base_identity(&manifest)?;

    let dimensions = usize::try_from(manifest.encoder.dimensions)
        .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
    let corpus = open_ndb(corpus_path, Validation::TrustedSource)?;
    let txn = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut ordered = BufReader::new(
        File::open(ordered_event_ids_path)
            .map_err(|source| io_error("open", ordered_event_ids_path, source))?,
    );
    let mut expected_start = 0_u64;
    for (index, shard) in manifest.shards.iter().enumerate() {
        let ordinal = u32::try_from(index)
            .map_err(|_| Error::Invariant("shard ordinal does not fit u32".to_owned()))?;
        let remaining = manifest
            .total_rows
            .checked_sub(expected_start)
            .ok_or_else(|| Error::Invariant("embedding shards exceed total rows".to_owned()))?;
        let expected_rows = manifest.shard_rows.min(remaining);
        if expected_rows == 0
            || shard.ordinal != ordinal
            || shard.start_row != expected_start
            || shard.rows != expected_rows
        {
            return Err(Error::Invariant(format!(
                "ordered embedding shard {index} does not match its row partition"
            )));
        }
        verify_shard_files(artifact_path, shard, dimensions)?;
        verify_effective_token_metadata(shard, manifest.encoder.max_tokens)?;
        verify_shard_rows(
            &corpus,
            &txn,
            corpus_path,
            &artifact_path.join(&shard.row_ids.file),
            shard.rows,
            &mut ordered,
            ordered_event_ids_path,
            expected_start,
        )?;
        expected_start = expected_start
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("verified row count overflowed".to_owned()))?;
    }
    if expected_start != manifest.total_rows {
        return Err(Error::Invariant(format!(
            "embedding shards contain {expected_start} rows but manifest records {}",
            manifest.total_rows
        )));
    }
    Ok(manifest)
}

#[allow(clippy::too_many_arguments)]
fn verify_shard_rows(
    corpus: &nostrdb::Ndb,
    txn: &Transaction,
    corpus_path: &Path,
    row_ids_path: &Path,
    rows: u64,
    ordered: &mut impl Read,
    ordered_path: &Path,
    start_row: u64,
) -> Result<()> {
    let mut row_ids = BufReader::new(
        File::open(row_ids_path).map_err(|source| io_error("open", row_ids_path, source))?,
    );
    for offset in 0..rows {
        let actual = read_event_id(&mut row_ids, row_ids_path)?.ok_or_else(|| {
            Error::Invariant(format!("embedding row-ID file ended after {offset} rows"))
        })?;
        let expected = read_event_id(ordered, ordered_path)?.ok_or_else(|| {
            Error::Invariant(format!(
                "ordered event-ID file ended before row {}",
                start_row + offset
            ))
        })?;
        if actual != expected {
            return Err(Error::Invariant(format!(
                "embedding row ID differs from ordered corpus row {}",
                start_row + offset
            )));
        }
        corpus
            .get_note_by_id(txn, &actual)
            .map_err(|source| ndb_error("load ordered note from", corpus_path, source))?;
    }
    if read_event_id(&mut row_ids, row_ids_path)?.is_some() {
        return Err(Error::Invariant(format!(
            "embedding row-ID file `{}` contains too many rows",
            row_ids_path.display()
        )));
    }
    Ok(())
}

fn validate_build_config(
    config: &OrderedEmbeddingBuildConfig,
    descriptor: &EncoderDescriptor,
) -> Result<()> {
    if config.rows == 0 || config.batch_size == 0 || config.shard_rows == 0 {
        return Err(Error::Invariant(
            "embedding rows, batch size, and shard size must be positive".to_owned(),
        ));
    }
    validate_descriptor(descriptor)
}

fn validate_base(
    path: &Path,
    base: &OrderedEmbeddingManifest,
    source: &OrderedSourceIdentity,
    config: &OrderedEmbeddingBuildConfig,
    descriptor: &EncoderDescriptor,
) -> Result<()> {
    if base.ordered_event_ids_sha256 != source.sha256
        || base.available_rows != source.available_rows
        || base.encoder != *descriptor
        || base.batch_size
            != u32::try_from(config.batch_size)
                .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?
        || base.shard_rows != config.shard_rows
        || base.total_rows >= config.rows
        || !base.total_rows.is_multiple_of(config.shard_rows)
    {
        return Err(Error::Invariant(format!(
            "base embedding artifact `{}` cannot extend to the requested prefix",
            path.display()
        )));
    }
    Ok(())
}

fn validate_completed(
    manifest: &OrderedEmbeddingManifest,
    source: &OrderedSourceIdentity,
    config: &OrderedEmbeddingBuildConfig,
    descriptor: &EncoderDescriptor,
    expected_base: Option<&OrderedEmbeddingBaseArtifact>,
) -> Result<()> {
    let batch_size = u32::try_from(config.batch_size)
        .map_err(|_| Error::Invariant("batch size does not fit u32".to_owned()))?;
    if manifest.ordered_event_ids_sha256 != source.sha256
        || manifest.available_rows != source.available_rows
        || manifest.encoder != *descriptor
        || manifest.batch_size != batch_size
        || manifest.shard_rows != config.shard_rows
        || manifest.total_rows != config.rows
        || manifest.base_artifact.as_ref() != expected_base
    {
        return Err(Error::Invariant(
            "existing ordered embedding artifact represents different work".to_owned(),
        ));
    }
    Ok(())
}

fn verify_base_identity(manifest: &OrderedEmbeddingManifest) -> Result<()> {
    let Some(base) = &manifest.base_artifact else {
        return Ok(());
    };
    if base.rows == 0
        || base.rows >= manifest.total_rows
        || !base.rows.is_multiple_of(manifest.shard_rows)
        || base.manifest_sha256.len() != 64
        || !base
            .manifest_sha256
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(Error::Invariant(
            "ordered embedding base identity is invalid".to_owned(),
        ));
    }
    Ok(())
}

struct OrderedSourceIdentity {
    sha256: String,
    available_rows: u64,
}

fn source_identity(path: &Path) -> Result<OrderedSourceIdentity> {
    require_file(path)?;
    let bytes = fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    if !bytes.is_multiple_of(EVENT_ID_BYTES as u64) {
        return Err(Error::Invariant(format!(
            "ordered event-ID file `{}` ends with a partial event ID",
            path.display()
        )));
    }
    Ok(OrderedSourceIdentity {
        sha256: hash_file(path)?,
        available_rows: bytes / EVENT_ID_BYTES as u64,
    })
}

struct BaseBuild {
    identity: OrderedEmbeddingBaseArtifact,
    path: PathBuf,
    manifest: OrderedEmbeddingManifest,
}

fn copy_base_shards(
    base_path: &Path,
    stage: &Path,
    shards: &[EmbeddingShardManifest],
) -> Result<()> {
    for shard in shards {
        let relative = format!("shards/{:06}", shard.ordinal);
        let source = base_path.join(&relative);
        let target = stage.join(&relative);
        fs::create_dir(&target).map_err(|error| io_error("create", &target, error))?;
        for file in ["vectors.i8", "norms.f32le", "row_ids.bin"] {
            link_or_copy(&source.join(file), &target.join(file))?;
        }
        write_manifest(&target.join("manifest.json"), shard)?;
    }
    Ok(())
}

fn link_or_copy(source: &Path, target: &Path) -> Result<()> {
    match fs::hard_link(source, target) {
        Ok(()) => Ok(()),
        Err(link_error) => {
            fs::copy(source, target).map_err(|copy_error| {
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

fn create_stage_directory(output: &Path) -> Result<PathBuf> {
    let parent = output.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let name = output
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            Error::Invariant(format!(
                "invalid embedding output path: {}",
                output.display()
            ))
        })?;
    for attempt in 0..100_u8 {
        let stage = parent.join(format!(
            ".{name}.ordered-embedding-{}-{attempt}",
            std::process::id()
        ));
        match fs::create_dir(&stage) {
            Ok(()) => return Ok(stage),
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(source) => return Err(io_error("create", &stage, source)),
        }
    }
    Err(Error::Invariant(format!(
        "could not reserve a staging directory beside {}",
        output.display()
    )))
}

fn elapsed_milliseconds(started: Instant) -> u64 {
    u64::try_from(started.elapsed().as_millis()).unwrap_or(u64::MAX)
}
