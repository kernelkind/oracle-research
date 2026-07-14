//! Versioned nested corpus stages over the canonical stable row order.

use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};

use serde::{Deserialize, Serialize};

use crate::artifact::{
    ArtifactFile, describe_fixed_artifact, hash_file, is_safe_artifact_name, verify_fixed_artifact,
};
use crate::canonical::{CanonicalManifest, verify_canonical_rows};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, EligibilityRules, Error, Result, create_directory, io_error,
    read_manifest, require_file, verify_corpus_manifest, write_manifest,
};

const EVENT_ID_BYTES: usize = 32;
const CORPUS_STAGE_MANIFEST_SCHEMA_VERSION: u32 = 2;
const SELECTION_RULE: &str = "first-stable-canonical-rows-v1";

/// Requested nested corpus stage.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CorpusStageConfig {
    /// Filesystem-safe immutable stage name.
    pub name: String,
    /// Exact number of canonical rows to select.
    pub rows: u64,
}

/// Durable identity of an exact prefix of the stable canonical row order.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CorpusStageManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// Immutable stage name.
    pub name: String,
    /// SHA-256 inherited from source ingestion.
    pub source_snapshot_sha256: String,
    /// Eligibility contract inherited from corpus derivation.
    pub eligibility: EligibilityRules,
    /// SHA-256 of the complete backing canonical manifest.
    pub canonical_manifest_sha256: String,
    /// SHA-256 of the complete backing canonical row file.
    pub canonical_rows_sha256: String,
    /// Deterministic rule used to select nested rows.
    pub selection_rule: String,
    /// Canonical rows available in the backing reservoir.
    pub available_canonical_rows: u64,
    /// Canonical rows selected for this stage.
    pub selected_rows: u64,
    /// Selected canonical event IDs in stable row order.
    pub rows: ArtifactFile,
}

impl DamusSnapshot {
    /// Materialize an immutable exact prefix of the canonical stable row order.
    pub fn materialize_corpus_stage(
        &self,
        config: &CorpusStageConfig,
    ) -> Result<CorpusStageManifest> {
        validate_stage_name(&config.name)?;
        if config.rows == 0 {
            return Err(Error::Invariant(
                "corpus stage must contain at least one row".to_owned(),
            ));
        }
        let canonical = self.verified_canonical_source()?;
        if config.rows > canonical.manifest.counts.canonical_rows {
            return Err(Error::Invariant(format!(
                "corpus stage requests {} rows but the canonical reservoir has only {}",
                config.rows, canonical.manifest.counts.canonical_rows
            )));
        }
        let artifact = self.layout().corpus_stage_dir(&config.name);
        if artifact.exists() {
            let manifest = self.open_corpus_stage(&config.name)?;
            if manifest.selected_rows != config.rows {
                return Err(Error::Invariant(format!(
                    "existing corpus stage `{}` contains {} rows instead of {}",
                    config.name, manifest.selected_rows, config.rows
                )));
            }
            return Ok(manifest);
        }

        create_directory(&self.layout().corpus_stage_root())?;
        let stage =
            self.prepare_stage(&artifact, &self.layout().corpus_stage_work(&config.name))?;
        let rows_path = stage.join("rows.bin");
        copy_rows(
            &canonical.rows_path,
            &rows_path,
            config.rows,
            EVENT_ID_BYTES,
        )?;
        let rows = describe_fixed_artifact(&rows_path, "rows.bin", EVENT_ID_BYTES, config.rows)?;
        let manifest = CorpusStageManifest {
            schema_version: CORPUS_STAGE_MANIFEST_SCHEMA_VERSION,
            name: config.name.clone(),
            source_snapshot_sha256: canonical.manifest.source_snapshot_sha256,
            eligibility: canonical.manifest.eligibility,
            canonical_manifest_sha256: canonical.manifest_sha256,
            canonical_rows_sha256: canonical.rows_sha256,
            selection_rule: SELECTION_RULE.to_owned(),
            available_canonical_rows: canonical.manifest.counts.canonical_rows,
            selected_rows: config.rows,
            rows,
        };
        write_manifest(&stage.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage, &artifact)?;
        Ok(manifest)
    }

    /// Open and fully verify one immutable corpus stage.
    pub fn open_corpus_stage(&self, name: &str) -> Result<CorpusStageManifest> {
        validate_stage_name(name)?;
        let canonical = self.verified_canonical_source()?;
        let root = self.layout().corpus_stage_dir(name);
        let manifest_path = root.join("manifest.json");
        require_file(&manifest_path)?;
        let manifest: CorpusStageManifest = read_manifest(&manifest_path)?;
        if manifest.schema_version != CORPUS_STAGE_MANIFEST_SCHEMA_VERSION {
            return Err(Error::Invariant(format!(
                "corpus stage manifest schema {} is not supported",
                manifest.schema_version
            )));
        }
        if manifest.name != name || manifest.selection_rule != SELECTION_RULE {
            return Err(Error::Invariant(format!(
                "corpus stage `{name}` has an incompatible identity"
            )));
        }
        if manifest.source_snapshot_sha256 != canonical.manifest.source_snapshot_sha256
            || manifest.eligibility != canonical.manifest.eligibility
            || manifest.canonical_manifest_sha256 != canonical.manifest_sha256
            || manifest.canonical_rows_sha256 != canonical.rows_sha256
            || manifest.available_canonical_rows != canonical.manifest.counts.canonical_rows
        {
            return Err(Error::Invariant(format!(
                "corpus stage `{name}` was selected from a different canonical reservoir"
            )));
        }
        if manifest.selected_rows == 0 || manifest.selected_rows > manifest.available_canonical_rows
        {
            return Err(Error::Invariant(format!(
                "corpus stage `{name}` has invalid selected row count {}",
                manifest.selected_rows
            )));
        }
        verify_fixed_artifact(
            &root,
            &manifest.rows,
            "rows.bin",
            EVENT_ID_BYTES,
            manifest.selected_rows,
        )?;
        verify_canonical_prefix(
            &canonical.rows_path,
            &self.layout().corpus_stage_rows(name),
            manifest.selected_rows,
        )?;
        Ok(manifest)
    }

    fn verified_canonical_source(&self) -> Result<VerifiedCanonical> {
        let manifest_path = self.layout().canonical_manifest();
        let rows_path = self.layout().canonical_rows();
        let corpus_manifest_path = self.layout().corpus_manifest();
        require_file(&manifest_path)?;
        require_file(&rows_path)?;
        require_file(&corpus_manifest_path)?;
        let corpus: CorpusManifest = read_manifest(&corpus_manifest_path)?;
        verify_corpus_manifest(&corpus)?;
        let manifest: CanonicalManifest = read_manifest(&manifest_path)?;
        verify_canonical_rows(&self.layout().canonical_dir(), &manifest)?;
        if manifest.source_snapshot_sha256 != corpus.source_snapshot_sha256
            || manifest.eligibility != corpus.eligibility
            || manifest.counts.eligible_events != corpus.eligible_events
        {
            return Err(Error::Invariant(
                "canonical manifest was derived from a different corpus contract".to_owned(),
            ));
        }
        let manifest_sha256 = hash_file(&manifest_path)?;
        let rows_sha256 = manifest.rows.sha256.clone();
        Ok(VerifiedCanonical {
            manifest,
            manifest_sha256,
            rows_sha256,
            rows_path,
        })
    }
}

fn verify_canonical_prefix(
    canonical: &std::path::Path,
    selected: &std::path::Path,
    rows: u64,
) -> Result<()> {
    let expected_bytes = rows
        .checked_mul(u64::try_from(EVENT_ID_BYTES).expect("event ID width fits u64"))
        .ok_or_else(|| Error::Invariant("corpus stage byte count overflowed u64".to_owned()))?;
    let mut canonical_reader = BufReader::new(
        File::open(canonical).map_err(|source| io_error("open", canonical, source))?,
    );
    let mut selected_reader =
        BufReader::new(File::open(selected).map_err(|source| io_error("open", selected, source))?);
    let mut remaining = expected_bytes;
    let mut canonical_buffer = [0_u8; 64 * 1024];
    let mut selected_buffer = [0_u8; 64 * 1024];
    while remaining > 0 {
        let bytes = usize::try_from(remaining.min(canonical_buffer.len() as u64))
            .expect("bounded comparison size fits usize");
        canonical_reader
            .read_exact(&mut canonical_buffer[..bytes])
            .map_err(|source| io_error("read", canonical, source))?;
        selected_reader
            .read_exact(&mut selected_buffer[..bytes])
            .map_err(|source| io_error("read", selected, source))?;
        if canonical_buffer[..bytes] != selected_buffer[..bytes] {
            return Err(Error::Invariant(format!(
                "corpus stage rows are not the exact canonical prefix of {rows} rows"
            )));
        }
        remaining -= u64::try_from(bytes).expect("comparison size fits u64");
    }
    Ok(())
}

struct VerifiedCanonical {
    manifest: CanonicalManifest,
    manifest_sha256: String,
    rows_sha256: String,
    rows_path: std::path::PathBuf,
}

fn copy_rows(
    input: &std::path::Path,
    output: &std::path::Path,
    rows: u64,
    record_bytes: usize,
) -> Result<()> {
    let expected_bytes = rows
        .checked_mul(u64::try_from(record_bytes).expect("record width fits u64"))
        .ok_or_else(|| Error::Invariant("corpus stage byte count overflowed u64".to_owned()))?;
    let source = File::open(input).map_err(|source| io_error("open", input, source))?;
    let mut reader = BufReader::new(source).take(expected_bytes);
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(output)
        .map_err(|source| io_error("create", output, source))?;
    let mut writer = BufWriter::new(file);
    let copied = std::io::copy(&mut reader, &mut writer)
        .map_err(|source| io_error("copy rows into", output, source))?;
    if copied != expected_bytes {
        return Err(Error::Invariant(format!(
            "canonical row file supplied {copied} bytes but stage requires {expected_bytes}"
        )));
    }
    writer
        .flush()
        .map_err(|source| io_error("flush", output, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", output, source))
}

fn validate_stage_name(name: &str) -> Result<()> {
    if !is_safe_artifact_name(name) {
        return Err(Error::Invariant(format!(
            "corpus stage name `{name}` is not filesystem-safe"
        )));
    }
    Ok(())
}
