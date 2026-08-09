//! Reproducible fixed-floor complete-link segments for the scaled SSE artifact.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::{hash_bytes, hash_file};
use crate::fine_region_partition::{CosineMatrix, complete_linkage_partition};

const SCHEMA_VERSION: u32 = 1;
const SEGMENTS_FILE: &str = "segments.json";
const MANIFEST_FILE: &str = "manifest.json";
const SELECTION_RULE: &str = "fixed-floor-complete-linkage-maximal-cross-note-segments-v1";
const PARTITION_SOURCE: &[u8] = include_bytes!("fine_region_partition.rs");
const SEGMENT_SOURCE: &[u8] = include_bytes!("scaled_fine_segments.rs");

pub type Result<T> = std::result::Result<T, ScaledFineSegmentError>;

#[derive(Debug, Error)]
pub enum ScaledFineSegmentError {
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: io::Error,
    },
    #[error("failed to decode JSON `{path}`: {source}")]
    Json {
        path: PathBuf,
        #[source]
        source: serde_json::Error,
    },
    #[error("scaled fine-segment invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    Partition(#[from] crate::fine_region_partition::FineRegionPartitionError),
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RawConfig {
    schema_version: u32,
    artifact_id: String,
    vector_artifact_path: PathBuf,
    pairwise_min_cosine: f64,
    output_path: PathBuf,
}

#[derive(Clone, Debug)]
struct Config {
    path: PathBuf,
    artifact_id: String,
    vector_artifact_path: PathBuf,
    pairwise_min_cosine: f64,
    output_path: PathBuf,
}

#[derive(Clone, Debug, Deserialize)]
struct VectorManifest {
    schema_version: u32,
    artifact_id: String,
    note_count: usize,
    vector_count: usize,
    dimensions: usize,
    files: BTreeMap<String, FileIdentity>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FileIdentity {
    bytes: u64,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct VectorMap {
    schema_version: u32,
    artifact_id: String,
    note_count: usize,
    vector_count: usize,
    generation_output_sha256: String,
    vectors: Vec<VectorMapping>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct VectorMapping {
    pub ordinal: usize,
    pub subject_id: String,
    pub note_id: String,
    pub takeaway_index: usize,
    pub takeaway: String,
    pub prominence: u8,
    pub fragments: Vec<String>,
    pub byte_spans: Vec<[u64; 2]>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScaledFineSegmentReport {
    pub schema_version: u32,
    pub artifact_id: String,
    pub selection_rule: String,
    pub pairwise_min_cosine: f64,
    pub source_note_count: usize,
    pub source_vector_count: usize,
    pub source_partition_region_count: usize,
    pub excluded_partition_regions: usize,
    pub segment_count: usize,
    pub represented_vector_count: usize,
    pub represented_note_count: usize,
    pub segments: Vec<FineSegment>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineSegment {
    pub segment_id: String,
    pub vector_ordinals: Vec<usize>,
    pub note_ids: Vec<String>,
    pub minimum_within_cosine: f64,
    pub members: Vec<VectorMapping>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct SegmentManifest {
    schema_version: u32,
    artifact_id: String,
    config_sha256: String,
    vector_manifest_sha256: String,
    vector_map_sha256: String,
    normalized_vectors_sha256: String,
    partition_source_sha256: String,
    segment_source_sha256: String,
    selection_rule: String,
    pairwise_min_cosine_bits: u64,
    segment_count: usize,
    represented_vector_count: usize,
    represented_note_count: usize,
    files: BTreeMap<String, FileIdentity>,
}

pub fn ensure_scaled_fine_segments(
    config_path: impl AsRef<Path>,
) -> Result<ScaledFineSegmentReport> {
    let config = load_config(config_path.as_ref())?;
    if config.output_path.exists() {
        verify_with_config(&config)
    } else {
        run_with_config(&config)
    }
}

pub fn run_scaled_fine_segments(config_path: impl AsRef<Path>) -> Result<ScaledFineSegmentReport> {
    let config = load_config(config_path.as_ref())?;
    if config.output_path.exists() {
        return Err(invalid("output artifact already exists"));
    }
    run_with_config(&config)
}

pub fn verify_scaled_fine_segments(
    config_path: impl AsRef<Path>,
) -> Result<ScaledFineSegmentReport> {
    verify_with_config(&load_config(config_path.as_ref())?)
}

fn load_config(path: &Path) -> Result<Config> {
    let path = fs::canonicalize(path).map_err(|source| io_error("resolve", path, source))?;
    let raw: RawConfig = read_json(&path)?;
    if raw.schema_version != SCHEMA_VERSION || raw.artifact_id.trim().is_empty() {
        return Err(invalid("config violates schema version 1"));
    }
    if !raw.pairwise_min_cosine.is_finite() || !(-1.0..=1.0).contains(&raw.pairwise_min_cosine) {
        return Err(invalid(
            "pairwise cosine floor must be finite and between -1 and 1",
        ));
    }
    let parent = path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .to_path_buf();
    Ok(Config {
        path,
        artifact_id: raw.artifact_id,
        vector_artifact_path: resolve(&parent, &raw.vector_artifact_path),
        pairwise_min_cosine: raw.pairwise_min_cosine,
        output_path: resolve(&parent, &raw.output_path),
    })
}

fn resolve(parent: &Path, path: &Path) -> PathBuf {
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        parent.join(path)
    }
}

fn run_with_config(config: &Config) -> Result<ScaledFineSegmentReport> {
    let report = build_report(config)?;
    let report_bytes = json_bytes(&report)?;
    let manifest = build_manifest(config, &report, &report_bytes)?;
    let manifest_bytes = json_bytes(&manifest)?;
    let parent = config
        .output_path
        .parent()
        .unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage = parent.join(format!(
        ".{}.{}.tmp",
        config
            .output_path
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("segments"),
        std::process::id()
    ));
    fs::create_dir(&stage).map_err(|source| io_error("create", &stage, source))?;
    let published: Result<()> = (|| {
        write_file(&stage.join(SEGMENTS_FILE), &report_bytes)?;
        write_file(&stage.join(MANIFEST_FILE), &manifest_bytes)?;
        fs::rename(&stage, &config.output_path)
            .map_err(|source| io_error("publish", &config.output_path, source))?;
        Ok(())
    })();
    if published.is_err() {
        let _ = fs::remove_dir_all(&stage);
    }
    published?;
    verify_with_config(config)
}

fn verify_with_config(config: &Config) -> Result<ScaledFineSegmentReport> {
    let entries = fs::read_dir(&config.output_path)
        .map_err(|source| io_error("read", &config.output_path, source))?
        .map(|entry| {
            let entry = entry.map_err(|source| io_error("read", &config.output_path, source))?;
            if !entry
                .file_type()
                .map_err(|source| io_error("read metadata for", &entry.path(), source))?
                .is_file()
            {
                return Err(invalid("segment artifact entries must be regular files"));
            }
            entry
                .file_name()
                .into_string()
                .map_err(|_| invalid("segment artifact has a non-UTF-8 entry"))
        })
        .collect::<Result<BTreeSet<_>>>()?;
    if entries != BTreeSet::from([SEGMENTS_FILE.to_owned(), MANIFEST_FILE.to_owned()]) {
        return Err(invalid(
            "segment artifact must contain exactly segments.json and manifest.json",
        ));
    }
    let stored_report: ScaledFineSegmentReport =
        read_json(&config.output_path.join(SEGMENTS_FILE))?;
    let expected_report = build_report(config)?;
    if stored_report != expected_report {
        return Err(invalid("stored fine segments differ from a source replay"));
    }
    let report_bytes = fs::read(config.output_path.join(SEGMENTS_FILE))
        .map_err(|source| io_error("read", config.output_path.join(SEGMENTS_FILE), source))?;
    let stored_manifest: SegmentManifest = read_json(&config.output_path.join(MANIFEST_FILE))?;
    let expected_manifest = build_manifest(config, &stored_report, &report_bytes)?;
    if stored_manifest != expected_manifest {
        return Err(invalid("segment manifest differs from its bound sources"));
    }
    Ok(stored_report)
}

fn build_report(config: &Config) -> Result<ScaledFineSegmentReport> {
    let manifest_path = config.vector_artifact_path.join(MANIFEST_FILE);
    let vector_manifest: VectorManifest = read_json(&manifest_path)?;
    if vector_manifest.schema_version != SCHEMA_VERSION
        || vector_manifest.artifact_id.trim().is_empty()
        || vector_manifest.vector_count == 0
        || vector_manifest.dimensions == 0
    {
        return Err(invalid("vector manifest violates schema version 1"));
    }
    let map_path = config.vector_artifact_path.join("vector-map.json");
    let vector_map: VectorMap = read_json(&map_path)?;
    if vector_map.schema_version != SCHEMA_VERSION
        || vector_map.artifact_id != vector_manifest.artifact_id
        || vector_map.note_count != vector_manifest.note_count
        || vector_map.vector_count != vector_manifest.vector_count
        || vector_map.vectors.len() != vector_manifest.vector_count
        || vector_map.generation_output_sha256.len() != 64
    {
        return Err(invalid("vector map differs from its vector manifest"));
    }
    for (ordinal, mapping) in vector_map.vectors.iter().enumerate() {
        if mapping.ordinal != ordinal
            || mapping.note_id.len() != 64
            || mapping.subject_id.len() != 16
            || mapping.takeaway.trim().is_empty()
            || mapping.fragments.is_empty()
            || mapping.fragments.len() != mapping.byte_spans.len()
            || mapping.prominence > 100
        {
            return Err(invalid(format!("vector mapping {ordinal} is invalid")));
        }
    }
    let normalized_path = config.vector_artifact_path.join("normalized-vectors.f32le");
    verify_bound_file(
        &normalized_path,
        vector_manifest.files.get("normalized-vectors.f32le"),
    )?;
    verify_bound_file(&map_path, vector_manifest.files.get("vector-map.json"))?;
    let vectors = read_vectors(
        &normalized_path,
        vector_manifest.vector_count,
        vector_manifest.dimensions,
    )?;
    let cosines = CosineMatrix::from_normalized_vectors(&vectors)?;
    let partition = complete_linkage_partition(&cosines, config.pairwise_min_cosine)?;
    let selected = partition
        .regions()
        .iter()
        .filter(|members| {
            members
                .iter()
                .map(|ordinal| &vector_map.vectors[*ordinal].note_id)
                .collect::<BTreeSet<_>>()
                .len()
                >= 2
        })
        .collect::<Vec<_>>();
    let segments = selected
        .iter()
        .enumerate()
        .map(|(index, members)| {
            let note_ids = members
                .iter()
                .map(|ordinal| vector_map.vectors[*ordinal].note_id.clone())
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();
            FineSegment {
                segment_id: format!("S{:06}", index + 1),
                vector_ordinals: members.to_vec(),
                note_ids,
                minimum_within_cosine: cosines
                    .minimum_within(members)
                    .expect("cross-note segment contains at least two vectors"),
                members: members
                    .iter()
                    .map(|ordinal| vector_map.vectors[*ordinal].clone())
                    .collect(),
            }
        })
        .collect::<Vec<_>>();
    if segments
        .iter()
        .any(|segment| segment.minimum_within_cosine < config.pairwise_min_cosine)
    {
        return Err(invalid(
            "a selected segment violates the frozen cosine floor",
        ));
    }
    let represented_vector_count = segments
        .iter()
        .map(|segment| segment.vector_ordinals.len())
        .sum();
    let represented_note_count = segments
        .iter()
        .flat_map(|segment| segment.note_ids.iter())
        .collect::<BTreeSet<_>>()
        .len();
    Ok(ScaledFineSegmentReport {
        schema_version: SCHEMA_VERSION,
        artifact_id: config.artifact_id.clone(),
        selection_rule: SELECTION_RULE.to_owned(),
        pairwise_min_cosine: config.pairwise_min_cosine,
        source_note_count: vector_manifest.note_count,
        source_vector_count: vector_manifest.vector_count,
        source_partition_region_count: partition.regions().len(),
        excluded_partition_regions: partition.regions().len() - segments.len(),
        segment_count: segments.len(),
        represented_vector_count,
        represented_note_count,
        segments,
    })
}

fn build_manifest(
    config: &Config,
    report: &ScaledFineSegmentReport,
    report_bytes: &[u8],
) -> Result<SegmentManifest> {
    let report_file = FileIdentity {
        bytes: report_bytes.len() as u64,
        sha256: hash_bytes(report_bytes),
    };
    Ok(SegmentManifest {
        schema_version: SCHEMA_VERSION,
        artifact_id: config.artifact_id.clone(),
        config_sha256: hash_file(&config.path).map_err(map_snapshot_error)?,
        vector_manifest_sha256: hash_file(&config.vector_artifact_path.join(MANIFEST_FILE))
            .map_err(map_snapshot_error)?,
        vector_map_sha256: hash_file(&config.vector_artifact_path.join("vector-map.json"))
            .map_err(map_snapshot_error)?,
        normalized_vectors_sha256: hash_file(
            &config.vector_artifact_path.join("normalized-vectors.f32le"),
        )
        .map_err(map_snapshot_error)?,
        partition_source_sha256: hash_bytes(PARTITION_SOURCE),
        segment_source_sha256: hash_bytes(SEGMENT_SOURCE),
        selection_rule: SELECTION_RULE.to_owned(),
        pairwise_min_cosine_bits: config.pairwise_min_cosine.to_bits(),
        segment_count: report.segment_count,
        represented_vector_count: report.represented_vector_count,
        represented_note_count: report.represented_note_count,
        files: BTreeMap::from([(SEGMENTS_FILE.to_owned(), report_file)]),
    })
}

fn read_vectors(path: &Path, rows: usize, dimensions: usize) -> Result<Vec<Vec<f64>>> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let expected = rows
        .checked_mul(dimensions)
        .and_then(|values| values.checked_mul(4))
        .ok_or_else(|| invalid("vector byte length overflowed"))?;
    if bytes.len() != expected {
        return Err(invalid("normalized vector byte length is invalid"));
    }
    Ok(bytes
        .chunks_exact(dimensions * 4)
        .map(|row| {
            row.chunks_exact(4)
                .map(|value| {
                    f64::from(f32::from_le_bytes(value.try_into().expect("four-byte f32")))
                })
                .collect()
        })
        .collect())
}

fn verify_bound_file(path: &Path, expected: Option<&FileIdentity>) -> Result<()> {
    let expected = expected.ok_or_else(|| invalid("vector manifest omits a required file"))?;
    let metadata =
        fs::metadata(path).map_err(|source| io_error("read metadata for", path, source))?;
    let actual_hash = hash_file(path).map_err(map_snapshot_error)?;
    if metadata.len() != expected.bytes || actual_hash != expected.sha256 {
        return Err(invalid(format!(
            "vector artifact file {} differs from its manifest",
            path.display()
        )));
    }
    Ok(())
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    serde_json::from_reader(File::open(path).map_err(|source| io_error("open", path, source))?)
        .map_err(|source| ScaledFineSegmentError::Json {
            path: path.to_path_buf(),
            source,
        })
}

fn json_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    let mut bytes = serde_json::to_vec(value).map_err(|source| ScaledFineSegmentError::Json {
        path: PathBuf::from("<memory>"),
        source,
    })?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn write_file(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = File::create(path).map_err(|source| io_error("create", path, source))?;
    file.write_all(bytes)
        .map_err(|source| io_error("write", path, source))?;
    file.sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> ScaledFineSegmentError {
    ScaledFineSegmentError::Io {
        operation,
        path: path.as_ref().to_path_buf(),
        source,
    }
}

fn map_snapshot_error(error: crate::snapshot::Error) -> ScaledFineSegmentError {
    invalid(error.to_string())
}

fn invalid(message: impl Into<String>) -> ScaledFineSegmentError {
    ScaledFineSegmentError::Invariant(message.into())
}
