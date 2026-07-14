//! Complete raw-token-length audits for exact canonical corpus selections.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};

use crate::artifact::{
    ArtifactFile, describe_fixed_artifact, hash_file, is_safe_artifact_name, verify_fixed_artifact,
};
use crate::canonical::{CanonicalManifest, verify_canonical_rows};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, EligibilityRules, Error, Result, Validation, create_directory,
    io_error, ndb_error, open_ndb, read_manifest, require_directory, require_file,
    verify_corpus_manifest, write_manifest,
};

const MANIFEST_SCHEMA_VERSION: u32 = 1;
const ROW_ID_BYTES: usize = 32;
const LENGTH_RECORD_BYTES: usize = 4;
const BUCKET_RECORD_BYTES: usize = 12;
const TOKENIZE_BATCH_ROWS: usize = 1_024;
const ROW_LENGTH_FILE: &str = "row_lengths.u32le";
const BUCKET_FILE: &str = "length_buckets.bin";

/// Stable identity of the tokenizer rules used by an audit.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenizerDescriptor {
    /// Model repository identity.
    pub model_id: String,
    /// Immutable model revision.
    pub model_revision: String,
    /// SHA-256 of the frozen model lock.
    pub model_lock_sha256: String,
    /// SHA-256 of the tokenizer file actually loaded.
    pub tokenizer_file_sha256: String,
    /// Tokenizer library and version.
    pub tokenizer_runtime: String,
    /// Token length accepted by the model before truncation is required.
    pub model_token_ceiling: u32,
    /// Exact input transformation applied before tokenization.
    pub input_rule: String,
    /// Exact rule represented by each recorded length.
    pub token_length_rule: String,
}

/// Tokenizer-only production seam used by the complete audit.
pub trait TokenLengthCounter {
    /// Return the immutable tokenizer identity.
    fn descriptor(&self) -> &TokenizerDescriptor;

    /// Count tokens after input preparation and before model truncation or padding.
    fn raw_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>>;
}

/// Filesystem identity for one immutable token audit.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TokenAuditConfig {
    /// Safe directory name beneath `token-audits/`.
    pub artifact_name: String,
    /// Maximum rows per durable, independently verified checkpoint shard.
    pub shard_rows: u64,
}

/// Exact nested corpus-stage provenance, when the audit is stage-scoped.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenAuditCorpusStage {
    /// Immutable corpus-stage name.
    pub name: String,
    /// SHA-256 of its complete manifest.
    pub manifest_sha256: String,
    /// SHA-256 of its selected stable row IDs.
    pub rows_sha256: String,
    /// Selection rule inherited from the corpus stage.
    pub selection_rule: String,
    /// Rows available in the canonical reservoir when selected.
    pub available_canonical_rows: u64,
    /// Rows audited from this stage.
    pub selected_rows: u64,
}

/// Durable, complete raw-token-length distribution for one exact corpus selection.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenAuditManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 inherited from snapshot ingestion.
    pub source_snapshot_sha256: String,
    /// Eligibility rules inherited from the canonical corpus.
    pub eligibility: EligibilityRules,
    /// SHA-256 of the complete canonical manifest.
    pub canonical_manifest_sha256: String,
    /// SHA-256 of the complete canonical row reservoir.
    pub canonical_rows_sha256: String,
    /// Optional exact nested-stage identity.
    pub corpus_stage: Option<TokenAuditCorpusStage>,
    /// Frozen model and tokenizer identity.
    pub tokenizer: TokenizerDescriptor,
    /// Maximum rows in each independently durable checkpoint shard.
    pub shard_rows: u64,
    /// Number of audited canonical rows.
    pub total_rows: u64,
    /// Sum of raw, pre-truncation token lengths.
    pub total_tokens: u64,
    /// Smallest raw token length observed.
    pub minimum_tokens: u32,
    /// Largest raw token length observed.
    pub maximum_tokens: u32,
    /// Rows whose raw length exceeds the model's token ceiling.
    pub rows_over_model_ceiling: u64,
    /// Sorted `(token length, row count)` records covering every row.
    pub length_buckets: ArtifactFile,
    /// Complete, contiguous raw-token-length shards in stable corpus row order.
    pub shards: Vec<TokenAuditShardManifest>,
}

/// One immutable checkpoint of raw token lengths and its exact distribution.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenAuditShardManifest {
    /// Zero-based shard ordinal.
    pub ordinal: u32,
    /// First stable corpus row represented by this shard.
    pub start_row: u64,
    /// Number of contiguous rows represented by this shard.
    pub rows: u64,
    /// Sum of raw token lengths in this shard.
    pub total_tokens: u64,
    /// Smallest raw token length in this shard.
    pub minimum_tokens: u32,
    /// Largest raw token length in this shard.
    pub maximum_tokens: u32,
    /// Shard rows exceeding the frozen model ceiling.
    pub rows_over_model_ceiling: u64,
    /// One raw u32 token length for every stable row in this shard.
    pub row_lengths: ArtifactFile,
    /// Sorted `(token length, row count)` records for this shard.
    pub length_buckets: ArtifactFile,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct TokenAuditWorkManifest {
    schema_version: u32,
    source_snapshot_sha256: String,
    eligibility: EligibilityRules,
    canonical_manifest_sha256: String,
    canonical_rows_sha256: String,
    selected_rows_sha256: String,
    corpus_stage: Option<TokenAuditCorpusStage>,
    tokenizer: TokenizerDescriptor,
    shard_rows: u64,
    total_rows: u64,
}

impl DamusSnapshot {
    /// Audit every row of the verified canonical corpus.
    pub fn audit_canonical_token_lengths(
        &self,
        config: &TokenAuditConfig,
        counter: &mut dyn TokenLengthCounter,
    ) -> Result<TokenAuditManifest> {
        self.audit_token_lengths(config, None, counter)
    }

    /// Audit every row of one verified nested canonical corpus stage.
    pub fn audit_corpus_stage_token_lengths(
        &self,
        stage_name: &str,
        config: &TokenAuditConfig,
        counter: &mut dyn TokenLengthCounter,
    ) -> Result<TokenAuditManifest> {
        self.audit_token_lengths(config, Some(stage_name), counter)
    }

    /// Reopen and fully verify an immutable audit against its corpus and tokenizer.
    pub fn open_token_length_audit(
        &self,
        artifact_name: &str,
        expected_tokenizer: &TokenizerDescriptor,
    ) -> Result<TokenAuditManifest> {
        validate_artifact_name(artifact_name)?;
        validate_tokenizer(expected_tokenizer)?;
        let root = audit_dir(self, artifact_name);
        let manifest_path = root.join("manifest.json");
        require_file(&manifest_path)?;
        let manifest: TokenAuditManifest = read_manifest(&manifest_path)?;
        if manifest.schema_version != MANIFEST_SCHEMA_VERSION {
            return Err(Error::Invariant(format!(
                "token-audit manifest schema {} is not supported",
                manifest.schema_version
            )));
        }
        if &manifest.tokenizer != expected_tokenizer {
            return Err(Error::Invariant(
                "token-audit tokenizer identity does not match the requested tokenizer".to_owned(),
            ));
        }
        let source = audit_source(
            self,
            manifest
                .corpus_stage
                .as_ref()
                .map(|stage| stage.name.as_str()),
        )?;
        if manifest.source_snapshot_sha256 != source.source_snapshot_sha256
            || manifest.eligibility != source.eligibility
            || manifest.canonical_manifest_sha256 != source.canonical_manifest_sha256
            || manifest.canonical_rows_sha256 != source.canonical_rows_sha256
            || manifest.corpus_stage != source.corpus_stage
            || manifest.total_rows != source.rows
            || manifest.shard_rows == 0
        {
            return Err(Error::Invariant(
                "token-audit corpus provenance does not match the current verified corpus selection"
                    .to_owned(),
            ));
        }
        let aggregates = verify_shards(
            &root,
            &manifest.shards,
            manifest.shard_rows,
            manifest.total_rows,
            &manifest.tokenizer,
        )?;
        verify_fixed_artifact(
            &root,
            &manifest.length_buckets,
            BUCKET_FILE,
            BUCKET_RECORD_BYTES,
            u64::try_from(aggregates.buckets.len())
                .map_err(|_| Error::Invariant("token bucket count does not fit u64".to_owned()))?,
        )?;
        verify_bucket_file(&root.join(BUCKET_FILE), &aggregates.buckets)?;
        if manifest.total_tokens != aggregates.total_tokens
            || manifest.minimum_tokens != aggregates.minimum_tokens
            || manifest.maximum_tokens != aggregates.maximum_tokens
            || manifest.rows_over_model_ceiling != aggregates.rows_over_model_ceiling
        {
            return Err(Error::Invariant(
                "token-audit aggregates do not match its complete row-length artifact".to_owned(),
            ));
        }
        Ok(manifest)
    }

    fn audit_token_lengths(
        &self,
        config: &TokenAuditConfig,
        stage_name: Option<&str>,
        counter: &mut dyn TokenLengthCounter,
    ) -> Result<TokenAuditManifest> {
        validate_artifact_name(&config.artifact_name)?;
        if config.shard_rows == 0 {
            return Err(Error::Invariant(
                "token-audit shard size must be positive".to_owned(),
            ));
        }
        let tokenizer = counter.descriptor().clone();
        validate_tokenizer(&tokenizer)?;
        let source = audit_source(self, stage_name)?;
        if source.rows == 0 {
            return Err(Error::Invariant(
                "cannot audit an empty canonical corpus selection".to_owned(),
            ));
        }
        let artifact = audit_dir(self, &config.artifact_name);
        if artifact.exists() {
            let manifest = self.open_token_length_audit(&config.artifact_name, &tokenizer)?;
            if manifest.shard_rows != config.shard_rows {
                return Err(Error::Invariant(format!(
                    "existing token audit uses {} rows per shard instead of {}",
                    manifest.shard_rows, config.shard_rows
                )));
            }
            return Ok(manifest);
        }

        create_directory(&self.layout().root().join("token-audits"))?;
        let work_manifest = TokenAuditWorkManifest {
            schema_version: MANIFEST_SCHEMA_VERSION,
            source_snapshot_sha256: source.source_snapshot_sha256.clone(),
            eligibility: source.eligibility.clone(),
            canonical_manifest_sha256: source.canonical_manifest_sha256.clone(),
            canonical_rows_sha256: source.canonical_rows_sha256.clone(),
            selected_rows_sha256: source.selected_rows_sha256.clone(),
            corpus_stage: source.corpus_stage.clone(),
            tokenizer: tokenizer.clone(),
            shard_rows: config.shard_rows,
            total_rows: source.rows,
        };
        let stage = prepare_audit_stage(
            self,
            &audit_work_dir(self, &config.artifact_name),
            &work_manifest,
        )?;
        let mut shards = load_completed_shards(&stage, config.shard_rows, source.rows, &tokenizer)?;
        let mut next_row = shards
            .last()
            .map_or(0, |shard| shard.start_row + shard.rows);
        let corpus_path = self.layout().corpus_db();
        require_directory(&corpus_path)?;
        let corpus = open_ndb(&corpus_path, Validation::TrustedSource)?;
        let txn = Transaction::new(&corpus)
            .map_err(|error| ndb_error("open transaction on", &corpus_path, error))?;
        let mut rows = BufReader::new(
            File::open(&source.rows_path)
                .map_err(|error| io_error("open", &source.rows_path, error))?,
        );
        rows.seek(SeekFrom::Start(
            next_row
                .checked_mul(ROW_ID_BYTES as u64)
                .ok_or_else(|| Error::Invariant("token-audit row offset overflowed".to_owned()))?,
        ))
        .map_err(|error| io_error("seek", &source.rows_path, error))?;
        {
            let mut build = ShardBuild {
                stage: &stage,
                rows_reader: &mut rows,
                rows_path: &source.rows_path,
                corpus: &corpus,
                txn: &txn,
                corpus_path: &corpus_path,
                tokenizer: &tokenizer,
                counter,
            };
            while next_row < source.rows {
                let ordinal = u32::try_from(shards.len()).map_err(|_| {
                    Error::Invariant("token-audit shard ordinal does not fit u32".to_owned())
                })?;
                let rows_in_shard = config.shard_rows.min(source.rows - next_row);
                let shard = build.measure(ordinal, next_row, rows_in_shard)?;
                next_row = next_row.checked_add(rows_in_shard).ok_or_else(|| {
                    Error::Invariant("audited row count overflowed u64".to_owned())
                })?;
                shards.push(shard);
            }
        }
        if read_event_id(&mut rows, &source.rows_path)?.is_some() {
            return Err(Error::Invariant(format!(
                "token-audit row file contains more than {} records",
                source.rows
            )));
        }
        if counter.descriptor() != &tokenizer {
            return Err(Error::Invariant(
                "tokenizer identity changed while producing the token audit".to_owned(),
            ));
        }
        let aggregates =
            verify_shards(&stage, &shards, config.shard_rows, source.rows, &tokenizer)?;
        let buckets_path = stage.join(BUCKET_FILE);
        remove_if_file(&buckets_path)?;
        write_buckets(&buckets_path, &aggregates.buckets)?;

        let manifest = TokenAuditManifest {
            schema_version: MANIFEST_SCHEMA_VERSION,
            source_snapshot_sha256: source.source_snapshot_sha256,
            eligibility: source.eligibility,
            canonical_manifest_sha256: source.canonical_manifest_sha256,
            canonical_rows_sha256: source.canonical_rows_sha256,
            corpus_stage: source.corpus_stage,
            tokenizer: tokenizer.clone(),
            shard_rows: config.shard_rows,
            total_rows: source.rows,
            total_tokens: aggregates.total_tokens,
            minimum_tokens: aggregates.minimum_tokens,
            maximum_tokens: aggregates.maximum_tokens,
            rows_over_model_ceiling: aggregates.rows_over_model_ceiling,
            length_buckets: describe_fixed_artifact(
                &buckets_path,
                BUCKET_FILE,
                BUCKET_RECORD_BYTES,
                u64::try_from(aggregates.buckets.len()).map_err(|_| {
                    Error::Invariant("token bucket count does not fit u64".to_owned())
                })?,
            )?,
            shards,
        };
        remove_if_file(&stage.join("manifest.json"))?;
        write_manifest(&stage.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage, &artifact)?;
        self.open_token_length_audit(&config.artifact_name, &tokenizer)
    }
}

struct AuditSource {
    source_snapshot_sha256: String,
    eligibility: EligibilityRules,
    canonical_manifest_sha256: String,
    canonical_rows_sha256: String,
    selected_rows_sha256: String,
    corpus_stage: Option<TokenAuditCorpusStage>,
    rows_path: PathBuf,
    rows: u64,
}

fn audit_source(pipeline: &DamusSnapshot, stage_name: Option<&str>) -> Result<AuditSource> {
    let canonical_path = pipeline.layout().canonical_manifest();
    let corpus_path = pipeline.layout().corpus_manifest();
    require_file(&canonical_path)?;
    require_file(&corpus_path)?;
    let canonical: CanonicalManifest = read_manifest(&canonical_path)?;
    verify_canonical_rows(&pipeline.layout().root().join("canonical"), &canonical)?;
    let corpus: CorpusManifest = read_manifest(&corpus_path)?;
    verify_corpus_manifest(&corpus)?;
    if canonical.source_snapshot_sha256 != corpus.source_snapshot_sha256
        || canonical.eligibility != corpus.eligibility
        || canonical.counts.eligible_events != corpus.eligible_events
    {
        return Err(Error::Invariant(
            "canonical corpus does not match its eligible-corpus provenance".to_owned(),
        ));
    }
    let canonical_manifest_sha256 = hash_file(&canonical_path)?;
    let canonical_rows_sha256 = canonical.rows.sha256.clone();

    let (corpus_stage, rows_path, selected_rows_sha256, rows) = match stage_name {
        Some(name) => {
            let stage = pipeline.open_corpus_stage(name)?;
            let stage_manifest_path = pipeline.layout().corpus_stage_manifest(name);
            let selected_rows_sha256 = stage.rows.sha256.clone();
            (
                Some(TokenAuditCorpusStage {
                    name: stage.name,
                    manifest_sha256: hash_file(&stage_manifest_path)?,
                    rows_sha256: selected_rows_sha256.clone(),
                    selection_rule: stage.selection_rule,
                    available_canonical_rows: stage.available_canonical_rows,
                    selected_rows: stage.selected_rows,
                }),
                pipeline.layout().corpus_stage_rows(name),
                selected_rows_sha256,
                stage.selected_rows,
            )
        }
        None => (
            None,
            pipeline.layout().canonical_rows(),
            canonical_rows_sha256.clone(),
            canonical.counts.canonical_rows,
        ),
    };
    Ok(AuditSource {
        source_snapshot_sha256: canonical.source_snapshot_sha256,
        eligibility: canonical.eligibility,
        canonical_manifest_sha256,
        canonical_rows_sha256,
        selected_rows_sha256,
        corpus_stage,
        rows_path,
        rows,
    })
}

fn prepare_audit_stage(
    pipeline: &DamusSnapshot,
    stage: &Path,
    expected: &TokenAuditWorkManifest,
) -> Result<PathBuf> {
    if stage.exists() {
        require_directory(stage)?;
        let build_path = stage.join("build.json");
        require_file(&build_path)?;
        let actual: TokenAuditWorkManifest = read_manifest(&build_path)?;
        if &actual != expected {
            return Err(Error::Invariant(
                "incomplete token audit was built from different corpus, tokenizer, or shard settings"
                    .to_owned(),
            ));
        }
        cleanup_temporary_shards(&stage.join("shards"))?;
        return Ok(stage.to_owned());
    }
    create_directory(&pipeline.layout().root().join("work"))?;
    fs::create_dir(stage).map_err(|error| io_error("create", stage, error))?;
    create_directory(&stage.join("shards"))?;
    write_manifest(&stage.join("build.json"), expected)?;
    Ok(stage.to_owned())
}

fn cleanup_temporary_shards(shards: &Path) -> Result<()> {
    require_directory(shards)?;
    for entry in fs::read_dir(shards).map_err(|error| io_error("read", shards, error))? {
        let entry = entry.map_err(|error| io_error("read", shards, error))?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if name.starts_with('.') && name.ends_with(".tmp") {
            let path = entry.path();
            if !path.is_dir() {
                return Err(Error::Invariant(format!(
                    "token-audit temporary shard `{}` is not a directory",
                    path.display()
                )));
            }
            fs::remove_dir_all(&path).map_err(|error| io_error("remove", &path, error))?;
        }
    }
    Ok(())
}

fn load_completed_shards(
    stage: &Path,
    shard_rows: u64,
    total_rows: u64,
    tokenizer: &TokenizerDescriptor,
) -> Result<Vec<TokenAuditShardManifest>> {
    let shards_root = stage.join("shards");
    require_directory(&shards_root)?;
    let mut entries = Vec::new();
    for entry in
        fs::read_dir(&shards_root).map_err(|error| io_error("read", &shards_root, error))?
    {
        let entry = entry.map_err(|error| io_error("read", &shards_root, error))?;
        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| Error::Invariant("token-audit shard name is not UTF-8".to_owned()))?;
        if name.len() != 6 || !name.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err(Error::Invariant(format!(
                "unexpected token-audit shard entry `{name}`"
            )));
        }
        let ordinal = name
            .parse::<u32>()
            .map_err(|_| Error::Invariant(format!("invalid token-audit shard `{name}`")))?;
        entries.push((ordinal, entry.path()));
    }
    entries.sort_unstable_by_key(|(ordinal, _)| *ordinal);
    let mut manifests = Vec::with_capacity(entries.len());
    let mut next_row = 0_u64;
    for (index, (ordinal, path)) in entries.into_iter().enumerate() {
        let expected_ordinal = u32::try_from(index).map_err(|_| {
            Error::Invariant("token-audit shard ordinal does not fit u32".to_owned())
        })?;
        if ordinal != expected_ordinal {
            return Err(Error::Invariant(format!(
                "token-audit shard sequence skips ordinal {expected_ordinal}"
            )));
        }
        let manifest: TokenAuditShardManifest = read_manifest(&path.join("manifest.json"))?;
        let expected_rows = shard_rows.min(total_rows.saturating_sub(next_row));
        verify_one_shard(
            stage,
            &manifest,
            expected_ordinal,
            next_row,
            expected_rows,
            tokenizer,
        )?;
        next_row = next_row
            .checked_add(manifest.rows)
            .ok_or_else(|| Error::Invariant("audited row count overflowed u64".to_owned()))?;
        if next_row > total_rows {
            return Err(Error::Invariant(
                "completed token-audit shards exceed the selected corpus".to_owned(),
            ));
        }
        manifests.push(manifest);
    }
    Ok(manifests)
}

struct ShardBuild<'a> {
    stage: &'a Path,
    rows_reader: &'a mut BufReader<File>,
    rows_path: &'a Path,
    corpus: &'a Ndb,
    txn: &'a Transaction,
    corpus_path: &'a Path,
    tokenizer: &'a TokenizerDescriptor,
    counter: &'a mut dyn TokenLengthCounter,
}

impl ShardBuild<'_> {
    fn measure(
        &mut self,
        ordinal: u32,
        start_row: u64,
        shard_rows: u64,
    ) -> Result<TokenAuditShardManifest> {
        let final_name = format!("{ordinal:06}");
        let relative_dir = format!("shards/{final_name}");
        let shard_dir = self.stage.join(&relative_dir);
        let temporary_dir = self.stage.join("shards").join(format!(".{final_name}.tmp"));
        fs::create_dir(&temporary_dir)
            .map_err(|error| io_error("create", &temporary_dir, error))?;
        let lengths_path = temporary_dir.join(ROW_LENGTH_FILE);
        let mut writer = BufWriter::new(create_new_file(&lengths_path)?);
        let mut measured = 0_u64;
        let mut aggregates = LengthAggregates::new(self.tokenizer.model_token_ceiling);
        while measured < shard_rows {
            let batch_rows =
                usize::try_from((shard_rows - measured).min(TOKENIZE_BATCH_ROWS as u64))
                    .expect("bounded token-audit batch fits usize");
            let mut contents = Vec::with_capacity(batch_rows);
            for _ in 0..batch_rows {
                let id = read_event_id(self.rows_reader, self.rows_path)?.ok_or_else(|| {
                    Error::Invariant(format!(
                        "token-audit row file ended within shard {ordinal} after {measured} rows"
                    ))
                })?;
                let note = self.corpus.get_note_by_id(self.txn, &id).map_err(|error| {
                    ndb_error("load canonical note from", self.corpus_path, error)
                })?;
                contents.push(note.content().to_owned());
            }
            let text_refs = contents.iter().map(String::as_str).collect::<Vec<_>>();
            let lengths = self.counter.raw_token_lengths(&text_refs)?;
            if lengths.len() != batch_rows {
                return Err(Error::Invariant(format!(
                    "tokenizer returned {} lengths for {batch_rows} corpus rows",
                    lengths.len()
                )));
            }
            for length in lengths {
                if length == 0 {
                    return Err(Error::Invariant(
                        "tokenizer returned an empty raw token sequence".to_owned(),
                    ));
                }
                writer
                    .write_all(&length.to_le_bytes())
                    .map_err(|error| io_error("write", &lengths_path, error))?;
                aggregates.push(length)?;
            }
            measured = measured
                .checked_add(u64::try_from(batch_rows).expect("batch size fits u64"))
                .ok_or_else(|| Error::Invariant("audited row count overflowed u64".to_owned()))?;
        }
        finish_writer(&mut writer, &lengths_path)?;
        let buckets_path = temporary_dir.join(BUCKET_FILE);
        write_buckets(&buckets_path, &aggregates.buckets)?;
        let manifest = TokenAuditShardManifest {
            ordinal,
            start_row,
            rows: shard_rows,
            total_tokens: aggregates.total_tokens,
            minimum_tokens: aggregates.minimum_tokens,
            maximum_tokens: aggregates.maximum_tokens,
            rows_over_model_ceiling: aggregates.rows_over_model_ceiling,
            row_lengths: describe_fixed_artifact(
                &lengths_path,
                &format!("{relative_dir}/{ROW_LENGTH_FILE}"),
                LENGTH_RECORD_BYTES,
                shard_rows,
            )?,
            length_buckets: describe_fixed_artifact(
                &buckets_path,
                &format!("{relative_dir}/{BUCKET_FILE}"),
                BUCKET_RECORD_BYTES,
                u64::try_from(aggregates.buckets.len()).map_err(|_| {
                    Error::Invariant("token bucket count does not fit u64".to_owned())
                })?,
            )?,
        };
        write_manifest(&temporary_dir.join("manifest.json"), &manifest)?;
        fs::rename(&temporary_dir, &shard_dir)
            .map_err(|error| io_error("publish", &shard_dir, error))?;
        Ok(manifest)
    }
}

fn verify_shards(
    root: &Path,
    shards: &[TokenAuditShardManifest],
    shard_rows: u64,
    total_rows: u64,
    tokenizer: &TokenizerDescriptor,
) -> Result<LengthAggregates> {
    if shard_rows == 0 || total_rows == 0 || shards.is_empty() {
        return Err(Error::Invariant(
            "token-audit shard coverage must be nonempty".to_owned(),
        ));
    }
    let mut combined = LengthAggregates::new(tokenizer.model_token_ceiling);
    let mut next_row = 0_u64;
    for (index, shard) in shards.iter().enumerate() {
        let ordinal = u32::try_from(index).map_err(|_| {
            Error::Invariant("token-audit shard ordinal does not fit u32".to_owned())
        })?;
        let expected_rows = shard_rows.min(total_rows - next_row);
        let aggregate = verify_one_shard(root, shard, ordinal, next_row, expected_rows, tokenizer)?;
        combined.merge(&aggregate)?;
        next_row = next_row
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("audited row count overflowed u64".to_owned()))?;
    }
    if next_row != total_rows || combined.rows != total_rows {
        return Err(Error::Invariant(format!(
            "token-audit shards cover {next_row} rows instead of {total_rows}"
        )));
    }
    Ok(combined)
}

fn verify_one_shard(
    root: &Path,
    shard: &TokenAuditShardManifest,
    ordinal: u32,
    start_row: u64,
    rows: u64,
    tokenizer: &TokenizerDescriptor,
) -> Result<LengthAggregates> {
    if rows == 0 || shard.ordinal != ordinal || shard.start_row != start_row || shard.rows != rows {
        return Err(Error::Invariant(format!(
            "token-audit shard {ordinal} has incompatible row coverage"
        )));
    }
    let relative_dir = format!("shards/{ordinal:06}");
    let lengths_file = format!("{relative_dir}/{ROW_LENGTH_FILE}");
    let bucket_file = format!("{relative_dir}/{BUCKET_FILE}");
    verify_fixed_artifact(
        root,
        &shard.row_lengths,
        &lengths_file,
        LENGTH_RECORD_BYTES,
        rows,
    )?;
    let aggregate = read_length_aggregates(&root.join(&lengths_file), tokenizer)?;
    if aggregate.rows != rows {
        return Err(Error::Invariant(format!(
            "token-audit shard {ordinal} contains {} lengths instead of {rows}",
            aggregate.rows
        )));
    }
    verify_fixed_artifact(
        root,
        &shard.length_buckets,
        &bucket_file,
        BUCKET_RECORD_BYTES,
        u64::try_from(aggregate.buckets.len())
            .map_err(|_| Error::Invariant("token bucket count does not fit u64".to_owned()))?,
    )?;
    verify_bucket_file(&root.join(bucket_file), &aggregate.buckets)?;
    if shard.total_tokens != aggregate.total_tokens
        || shard.minimum_tokens != aggregate.minimum_tokens
        || shard.maximum_tokens != aggregate.maximum_tokens
        || shard.rows_over_model_ceiling != aggregate.rows_over_model_ceiling
    {
        return Err(Error::Invariant(format!(
            "token-audit shard {ordinal} aggregates do not match its row lengths"
        )));
    }
    Ok(aggregate)
}

#[derive(Default)]
struct LengthAggregates {
    model_token_ceiling: u32,
    rows: u64,
    total_tokens: u64,
    minimum_tokens: u32,
    maximum_tokens: u32,
    rows_over_model_ceiling: u64,
    buckets: BTreeMap<u32, u64>,
}

impl LengthAggregates {
    fn new(model_token_ceiling: u32) -> Self {
        Self {
            model_token_ceiling,
            minimum_tokens: u32::MAX,
            ..Self::default()
        }
    }

    fn push(&mut self, length: u32) -> Result<()> {
        self.rows = self
            .rows
            .checked_add(1)
            .ok_or_else(|| Error::Invariant("raw-token row count overflowed u64".to_owned()))?;
        self.total_tokens = self
            .total_tokens
            .checked_add(u64::from(length))
            .ok_or_else(|| Error::Invariant("raw token count overflowed u64".to_owned()))?;
        self.minimum_tokens = self.minimum_tokens.min(length);
        self.maximum_tokens = self.maximum_tokens.max(length);
        if length > self.model_token_ceiling {
            self.rows_over_model_ceiling =
                self.rows_over_model_ceiling.checked_add(1).ok_or_else(|| {
                    Error::Invariant("over-ceiling row count overflowed u64".to_owned())
                })?;
        }
        let count = self.buckets.entry(length).or_default();
        *count = count
            .checked_add(1)
            .ok_or_else(|| Error::Invariant("token bucket count overflowed u64".to_owned()))?;
        Ok(())
    }

    fn merge(&mut self, other: &Self) -> Result<()> {
        if self.model_token_ceiling != other.model_token_ceiling {
            return Err(Error::Invariant(
                "cannot merge token audits with different model ceilings".to_owned(),
            ));
        }
        self.rows = self
            .rows
            .checked_add(other.rows)
            .ok_or_else(|| Error::Invariant("raw-token row count overflowed u64".to_owned()))?;
        self.total_tokens = self
            .total_tokens
            .checked_add(other.total_tokens)
            .ok_or_else(|| Error::Invariant("raw token count overflowed u64".to_owned()))?;
        self.minimum_tokens = self.minimum_tokens.min(other.minimum_tokens);
        self.maximum_tokens = self.maximum_tokens.max(other.maximum_tokens);
        self.rows_over_model_ceiling = self
            .rows_over_model_ceiling
            .checked_add(other.rows_over_model_ceiling)
            .ok_or_else(|| Error::Invariant("over-ceiling row count overflowed u64".to_owned()))?;
        for (length, rows) in &other.buckets {
            let count = self.buckets.entry(*length).or_default();
            *count = count
                .checked_add(*rows)
                .ok_or_else(|| Error::Invariant("token bucket count overflowed u64".to_owned()))?;
        }
        Ok(())
    }
}

fn read_length_aggregates(
    path: &Path,
    tokenizer: &TokenizerDescriptor,
) -> Result<LengthAggregates> {
    let mut reader =
        BufReader::new(File::open(path).map_err(|error| io_error("open", path, error))?);
    let mut aggregates = LengthAggregates::new(tokenizer.model_token_ceiling);
    let mut record = [0_u8; LENGTH_RECORD_BYTES];
    loop {
        match reader.read_exact(&mut record) {
            Ok(()) => {
                let length = u32::from_le_bytes(record);
                if length == 0 {
                    return Err(Error::Invariant(
                        "token-audit contains an empty raw token sequence".to_owned(),
                    ));
                }
                aggregates.push(length)?;
            }
            Err(error) if error.kind() == std::io::ErrorKind::UnexpectedEof => break,
            Err(error) => return Err(io_error("read", path, error)),
        }
    }
    Ok(aggregates)
}

fn write_buckets(path: &Path, buckets: &BTreeMap<u32, u64>) -> Result<()> {
    let mut writer = BufWriter::new(create_new_file(path)?);
    for (length, rows) in buckets {
        writer
            .write_all(&length.to_le_bytes())
            .and_then(|()| writer.write_all(&rows.to_le_bytes()))
            .map_err(|error| io_error("write", path, error))?;
    }
    finish_writer(&mut writer, path)
}

fn verify_bucket_file(path: &Path, expected: &BTreeMap<u32, u64>) -> Result<()> {
    let mut reader =
        BufReader::new(File::open(path).map_err(|error| io_error("open", path, error))?);
    let mut actual = BTreeMap::new();
    let mut record = [0_u8; BUCKET_RECORD_BYTES];
    loop {
        match reader.read_exact(&mut record) {
            Ok(()) => {
                let length = u32::from_le_bytes(record[..4].try_into().expect("length width"));
                let rows = u64::from_le_bytes(record[4..].try_into().expect("row-count width"));
                if length == 0 || rows == 0 || actual.insert(length, rows).is_some() {
                    return Err(Error::Invariant(
                        "token-audit length buckets are not unique positive records".to_owned(),
                    ));
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::UnexpectedEof => break,
            Err(error) => return Err(io_error("read", path, error)),
        }
    }
    if &actual != expected {
        return Err(Error::Invariant(
            "token-audit buckets do not match its complete row lengths".to_owned(),
        ));
    }
    Ok(())
}

fn read_event_id(reader: &mut BufReader<File>, path: &Path) -> Result<Option<[u8; ROW_ID_BYTES]>> {
    let mut event_id = [0_u8; ROW_ID_BYTES];
    match reader.read_exact(&mut event_id) {
        Ok(()) => Ok(Some(event_id)),
        Err(error) if error.kind() == std::io::ErrorKind::UnexpectedEof => Ok(None),
        Err(error) => Err(io_error("read", path, error)),
    }
}

fn validate_artifact_name(name: &str) -> Result<()> {
    if !is_safe_artifact_name(name) {
        return Err(Error::Invariant(format!(
            "token-audit artifact name `{name}` must be one filesystem-safe component"
        )));
    }
    Ok(())
}

fn validate_tokenizer(descriptor: &TokenizerDescriptor) -> Result<()> {
    if descriptor.model_id.is_empty()
        || descriptor.model_revision.is_empty()
        || !is_sha256(&descriptor.model_lock_sha256)
        || !is_sha256(&descriptor.tokenizer_file_sha256)
        || descriptor.tokenizer_runtime.is_empty()
        || descriptor.model_token_ceiling == 0
        || descriptor.input_rule.is_empty()
        || descriptor.token_length_rule.is_empty()
    {
        return Err(Error::Invariant(
            "token-audit tokenizer identity is incomplete".to_owned(),
        ));
    }
    Ok(())
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn audit_dir(pipeline: &DamusSnapshot, name: &str) -> PathBuf {
    pipeline.layout().root().join("token-audits").join(name)
}

fn audit_work_dir(pipeline: &DamusSnapshot, name: &str) -> PathBuf {
    pipeline
        .layout()
        .root()
        .join("work")
        .join(format!("token-audit-{name}"))
}

fn create_new_file(path: &Path) -> Result<File> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|error| io_error("create", path, error))
}

fn remove_if_file(path: &Path) -> Result<()> {
    if path.exists() {
        if !path.is_file() {
            return Err(Error::Invariant(format!(
                "token-audit finalization path `{}` is not a file",
                path.display()
            )));
        }
        fs::remove_file(path).map_err(|error| io_error("remove", path, error))?;
    }
    Ok(())
}

fn finish_writer(writer: &mut BufWriter<File>, path: &Path) -> Result<()> {
    writer
        .flush()
        .map_err(|error| io_error("flush", path, error))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|error| io_error("sync", path, error))
}
