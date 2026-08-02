//! Auditable hard-partition pilot over the frozen TEv4.1 idea vectors.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufWriter, Read, Write};
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::{hash_bytes, hash_file};
use crate::fine_region_partition::{
    CosineMatrix, RegionPartition, ResolutionLevel, complete_linkage_partition, dp_vmf_partition,
    resolution_levels,
};

const CONFIG_SCHEMA_VERSION: u32 = 1;
const REPORT_SCHEMA_VERSION: u32 = 1;
const MANIFEST_SCHEMA_VERSION: u32 = 1;
const ANALYSIS_FILE: &str = "analysis.json";
const AUDIT_FILE: &str = "audit.md";
const MANIFEST_FILE: &str = "manifest.json";
const COSINE_TOLERANCE: f64 = 1.0e-6;
const PARTITION_SOURCE: &[u8] = include_bytes!("fine_region_partition.rs");
const PILOT_SOURCE: &[u8] = include_bytes!("fine_region_pilot.rs");

pub type Result<T> = std::result::Result<T, FineRegionPilotError>;

#[derive(Debug, Error)]
pub enum FineRegionPilotError {
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: io::Error,
    },
    #[error("failed to {operation} JSON `{path}`: {source}")]
    Json {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: serde_json::Error,
    },
    #[error("fine-region pilot artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("fine-region pilot artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),
    #[error("fine-region pilot invariant failed: {0}")]
    Invariant(String),
    #[error(
        "fine-region pilot input hash mismatch for `{path}`: expected {expected}, got {actual}"
    )]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("fine-region pilot replay differs from `{0}`")]
    ReplayMismatch(PathBuf),
    #[error(transparent)]
    Partition(#[from] crate::fine_region_partition::FineRegionPartitionError),
    #[error(transparent)]
    Source(#[from] crate::snapshot::Error),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FineRegionPilotConfig {
    schema_version: u32,
    pilot_id: String,
    baseline_archive_sha256: String,
    generation_manifest: BoundFile,
    analysis_manifest: BoundFile,
    resolution_percentiles: Vec<u8>,
    audit_percentiles: Vec<u8>,
    dp_vmf_order_count: usize,
    shuffle_seed: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BoundFile {
    path: String,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FileIdentity {
    bytes: u64,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
struct ExternalManifest {
    #[allow(dead_code)]
    schema_version: u32,
    #[serde(default)]
    note_count: Option<usize>,
    #[serde(default)]
    subject_count: Option<usize>,
    #[serde(default)]
    dimensions: Option<usize>,
    files: BTreeMap<String, FileIdentity>,
}

#[derive(Clone, Debug, Deserialize)]
struct NoteInput {
    notes: Vec<SourceNote>,
}

#[derive(Clone, Debug, Deserialize)]
struct SourceNote {
    note_id: String,
    text: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Proposal {
    notes: Vec<ProposalNote>,
}

#[derive(Clone, Debug, Deserialize)]
struct ProposalNote {
    note_id: String,
    subjects: Vec<ProposalSubject>,
}

#[derive(Clone, Debug, Deserialize)]
struct ProposalSubject {
    subject_id: String,
    label: String,
    status: String,
    fragments: Vec<ProposalFragment>,
}

#[derive(Clone, Debug, Deserialize)]
struct ProposalFragment {
    text: String,
    occurrence: usize,
}

#[derive(Clone, Debug, Deserialize)]
struct WorkerReceipt {
    dimensions: usize,
    row_count: usize,
    rows: Vec<WorkerRow>,
}

#[derive(Clone, Debug, Deserialize)]
struct WorkerRow {
    ordinal: usize,
    note_id: String,
    subject_id: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionPilotReport {
    pub schema_version: u32,
    pub pilot_id: String,
    pub config_sha256: String,
    pub baseline_archive_sha256: String,
    pub generation_manifest_sha256: String,
    pub analysis_manifest_sha256: String,
    pub partition_source_sha256: String,
    pub pilot_source_sha256: String,
    pub note_count: usize,
    pub vector_count: usize,
    pub dimensions: usize,
    pub rules: PilotRules,
    pub pairwise_cosines: DistributionSummary,
    pub cross_note_nearest_cosines: DistributionSummary,
    pub vectors: Vec<VectorEvidence>,
    pub resolutions: Vec<ResolutionReport>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PilotRules {
    pub resolution_source: String,
    pub complete_linkage: String,
    pub dp_vmf: String,
    pub dp_vmf_orders: String,
    pub coassignment_order: String,
    pub labels_used_for_membership: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DistributionSummary {
    pub count: usize,
    pub minimum: f64,
    pub p05: f64,
    pub p25: f64,
    pub median: f64,
    pub p75: f64,
    pub p95: f64,
    pub maximum: f64,
    pub mean: f64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct VectorEvidence {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub takeaway: String,
    pub selected_source_fragments: Vec<SelectedSourceFragment>,
    pub source_note: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SelectedSourceFragment {
    pub text: String,
    pub occurrence: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ResolutionReport {
    pub level: ResolutionLevel,
    pub audited: bool,
    pub complete_linkage: PartitionReport,
    pub dp_vmf: DpVmfReport,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PartitionReport {
    pub region_count: usize,
    pub singleton_count: usize,
    pub cross_note_region_count: usize,
    pub regions: Vec<RegionReport>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RegionReport {
    pub region_index: usize,
    pub members: Vec<usize>,
    pub distinct_note_count: usize,
    pub medoid: usize,
    pub minimum_within_cosine: Option<f64>,
    pub median_within_cosine: Option<f64>,
    pub nearest_external_cosine: Option<f64>,
    pub minimum_silhouette: f64,
    pub median_silhouette: f64,
    pub member_geometry: Vec<MemberGeometry>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MemberGeometry {
    pub ordinal: usize,
    pub nearest_within: Option<Neighbor>,
    pub nearest_outside: Option<Neighbor>,
    pub silhouette: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Neighbor {
    pub ordinal: usize,
    pub cosine: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DpVmfReport {
    pub order_count: usize,
    pub region_count_minimum: usize,
    pub region_count_median: f64,
    pub region_count_maximum: usize,
    pub uncertain_pair_count: usize,
    pub coassignment_certainty_mean: f64,
    pub complete_within_pair_coassignment_mean: Option<f64>,
    pub complete_between_pair_separation_mean: Option<f64>,
    pub complete_region_minimum_coassignment: Vec<Option<f64>>,
    pub coassignment_lower_triangle: Vec<f64>,
    pub partitions: Vec<Vec<Vec<usize>>>,
    pub identity_order_partition: PartitionReport,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PilotManifest {
    schema_version: u32,
    pilot_id: String,
    config_sha256: String,
    baseline_archive_sha256: String,
    generation_manifest_sha256: String,
    analysis_manifest_sha256: String,
    partition_source_sha256: String,
    pilot_source_sha256: String,
    files: BTreeMap<String, FileIdentity>,
}

struct LoadedPilot {
    config_sha256: String,
    config: FineRegionPilotConfig,
    generation_manifest_sha256: String,
    analysis_manifest_sha256: String,
    dimensions: usize,
    vectors: Vec<Vec<f64>>,
    evidence: Vec<VectorEvidence>,
}

pub fn run_fine_region_pilot(
    config_path: impl AsRef<Path>,
    baseline_root: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<FineRegionPilotReport> {
    let config_path = config_path.as_ref();
    let baseline_root = baseline_root.as_ref();
    let output_path = output_path.as_ref();
    if output_path.exists() {
        return Err(FineRegionPilotError::ArtifactExists(
            output_path.to_path_buf(),
        ));
    }
    let loaded = load_pilot(config_path, baseline_root)?;
    let report = build_report(&loaded)?;
    let audit = render_audit(&report);
    publish_artifact(output_path, &loaded, &report, &audit)?;
    Ok(report)
}

pub fn verify_fine_region_pilot(
    config_path: impl AsRef<Path>,
    baseline_root: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<FineRegionPilotReport> {
    let config_path = config_path.as_ref();
    let baseline_root = baseline_root.as_ref();
    let output_path = output_path.as_ref();
    if !output_path.is_dir() {
        return Err(FineRegionPilotError::ArtifactMissing(
            output_path.to_path_buf(),
        ));
    }
    let loaded = load_pilot(config_path, baseline_root)?;
    let manifest: PilotManifest = load_json(&output_path.join(MANIFEST_FILE))?;
    validate_manifest(&manifest, &loaded, output_path)?;

    let recorded_report: FineRegionPilotReport = load_json(&output_path.join(ANALYSIS_FILE))?;
    let expected_report = build_report(&loaded)?;
    if recorded_report != expected_report {
        return Err(FineRegionPilotError::ReplayMismatch(
            output_path.join(ANALYSIS_FILE),
        ));
    }
    let recorded_audit = read_string(&output_path.join(AUDIT_FILE))?;
    if recorded_audit != render_audit(&expected_report) {
        return Err(FineRegionPilotError::ReplayMismatch(
            output_path.join(AUDIT_FILE),
        ));
    }
    Ok(recorded_report)
}

fn load_pilot(config_path: &Path, baseline_root: &Path) -> Result<LoadedPilot> {
    let config_sha256 = hash_file(config_path)?;
    let config: FineRegionPilotConfig = load_json(config_path)?;
    validate_config(&config)?;

    let generation_manifest_path =
        resolve_baseline_path(baseline_root, &config.generation_manifest.path)?;
    verify_hash(
        &generation_manifest_path,
        &config.generation_manifest.sha256,
    )?;
    let generation_manifest: ExternalManifest = load_json(&generation_manifest_path)?;
    let generation_manifest_sha256 = hash_file(&generation_manifest_path)?;
    let input_path = verify_manifest_file(baseline_root, &generation_manifest, "input.json")?;
    let proposal_path = verify_manifest_file(baseline_root, &generation_manifest, "proposal.json")?;

    let analysis_manifest_path =
        resolve_baseline_path(baseline_root, &config.analysis_manifest.path)?;
    verify_hash(&analysis_manifest_path, &config.analysis_manifest.sha256)?;
    let analysis_manifest: ExternalManifest = load_json(&analysis_manifest_path)?;
    let analysis_manifest_sha256 = hash_file(&analysis_manifest_path)?;
    let vector_path = verify_manifest_file(
        &analysis_manifest_path
            .parent()
            .ok_or_else(|| invalid("analysis manifest has no parent"))?,
        &analysis_manifest,
        "normalized-vectors.f32le",
    )?;
    let receipt_path = verify_manifest_file(
        &analysis_manifest_path
            .parent()
            .ok_or_else(|| invalid("analysis manifest has no parent"))?,
        &analysis_manifest,
        "worker-receipt.json",
    )?;

    let input: NoteInput = load_json(&input_path)?;
    let proposal: Proposal = load_json(&proposal_path)?;
    let receipt: WorkerReceipt = load_json(&receipt_path)?;
    let note_count = analysis_manifest
        .note_count
        .ok_or_else(|| invalid("analysis manifest omits note_count"))?;
    let subject_count = analysis_manifest
        .subject_count
        .ok_or_else(|| invalid("analysis manifest omits subject_count"))?;
    let dimensions = analysis_manifest
        .dimensions
        .ok_or_else(|| invalid("analysis manifest omits dimensions"))?;
    if input.notes.len() != note_count
        || proposal.notes.len() != note_count
        || receipt.row_count != subject_count
        || receipt.rows.len() != subject_count
        || receipt.dimensions != dimensions
    {
        return Err(invalid(
            "baseline note, vector, dimension, or receipt counts disagree",
        ));
    }

    let evidence = bind_evidence(&input, &proposal, &receipt)?;
    if evidence.len() != subject_count {
        return Err(invalid(
            "proposal subject count does not match the vector count",
        ));
    }
    let vectors = read_vectors(&vector_path, subject_count, dimensions)?;
    CosineMatrix::from_normalized_vectors(&vectors)?;

    Ok(LoadedPilot {
        config_sha256,
        config,
        generation_manifest_sha256,
        analysis_manifest_sha256,
        dimensions,
        vectors,
        evidence,
    })
}

fn validate_config(config: &FineRegionPilotConfig) -> Result<()> {
    if config.schema_version != CONFIG_SCHEMA_VERSION
        || config.pilot_id.trim().is_empty()
        || !is_lower_hex(&config.baseline_archive_sha256, 64)
        || !is_lower_hex(&config.generation_manifest.sha256, 64)
        || !is_lower_hex(&config.analysis_manifest.sha256, 64)
        || config.dp_vmf_order_count == 0
        || config.dp_vmf_order_count > 256
    {
        return Err(invalid(
            "pilot config schema, identity, or order count is invalid",
        ));
    }
    validate_relative_path(&config.generation_manifest.path)?;
    validate_relative_path(&config.analysis_manifest.path)?;
    if config.resolution_percentiles.is_empty()
        || config
            .resolution_percentiles
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
        || config
            .resolution_percentiles
            .iter()
            .any(|value| *value == 0 || *value >= 100)
        || config.audit_percentiles.is_empty()
        || config
            .audit_percentiles
            .iter()
            .any(|value| !config.resolution_percentiles.contains(value))
    {
        return Err(invalid("pilot resolution or audit percentiles are invalid"));
    }
    Ok(())
}

fn bind_evidence(
    input: &NoteInput,
    proposal: &Proposal,
    receipt: &WorkerReceipt,
) -> Result<Vec<VectorEvidence>> {
    let mut source_notes = BTreeMap::new();
    for note in &input.notes {
        if note.note_id.trim().is_empty()
            || note.text.trim().is_empty()
            || source_notes
                .insert(note.note_id.as_str(), note.text.as_str())
                .is_some()
        {
            return Err(invalid("input contains an invalid or duplicate note"));
        }
    }

    let mut subjects = BTreeMap::new();
    for note in &proposal.notes {
        let source = source_notes
            .get(note.note_id.as_str())
            .ok_or_else(|| invalid("proposal names a note absent from input"))?;
        for subject in &note.subjects {
            if subject.subject_id.trim().is_empty()
                || subject.label.trim().is_empty()
                || subject.status != "masked"
                || subject.fragments.is_empty()
                || subjects.contains_key(subject.subject_id.as_str())
            {
                return Err(invalid("proposal contains an invalid or duplicate subject"));
            }
            for fragment in &subject.fragments {
                if fragment.text.is_empty()
                    || fragment.occurrence == 0
                    || source.match_indices(fragment.text.as_str()).count() < fragment.occurrence
                {
                    return Err(invalid(format!(
                        "subject {} contains an unbound source fragment",
                        subject.subject_id
                    )));
                }
            }
            subjects.insert(
                subject.subject_id.as_str(),
                (note.note_id.as_str(), subject, *source),
            );
        }
    }

    let mut rows = receipt.rows.iter().collect::<Vec<_>>();
    rows.sort_by_key(|row| row.ordinal);
    if rows
        .iter()
        .enumerate()
        .any(|(ordinal, row)| row.ordinal != ordinal)
    {
        return Err(invalid("worker receipt row ordinals are not contiguous"));
    }
    let mut used_subjects = BTreeSet::new();
    rows.into_iter()
        .map(|row| {
            let (note_id, subject, source_note) = subjects
                .get(row.subject_id.as_str())
                .ok_or_else(|| invalid("worker receipt names an unknown subject"))?;
            if row.note_id != *note_id || !used_subjects.insert(row.subject_id.as_str()) {
                return Err(invalid(
                    "worker receipt note binding is wrong or repeats a subject",
                ));
            }
            Ok(VectorEvidence {
                ordinal: row.ordinal,
                note_id: row.note_id.clone(),
                subject_id: row.subject_id.clone(),
                takeaway: subject.label.clone(),
                selected_source_fragments: subject
                    .fragments
                    .iter()
                    .map(|fragment| SelectedSourceFragment {
                        text: fragment.text.clone(),
                        occurrence: fragment.occurrence,
                    })
                    .collect(),
                source_note: (*source_note).to_owned(),
            })
        })
        .collect()
}

fn read_vectors(path: &Path, count: usize, dimensions: usize) -> Result<Vec<Vec<f64>>> {
    let bytes = read_bytes(path)?;
    let expected = count
        .checked_mul(dimensions)
        .and_then(|values| values.checked_mul(4))
        .ok_or_else(|| invalid("vector byte count overflowed"))?;
    if bytes.len() != expected {
        return Err(invalid(format!(
            "normalized vector file has {} bytes, expected {expected}",
            bytes.len()
        )));
    }
    let mut vectors = Vec::with_capacity(count);
    for row in bytes.chunks_exact(dimensions * 4) {
        let mut vector = Vec::with_capacity(dimensions);
        for coordinate in row.chunks_exact(4) {
            let value = f32::from_le_bytes(coordinate.try_into().expect("four-byte chunk"));
            if !value.is_finite() {
                return Err(invalid(
                    "normalized vector file contains a non-finite value",
                ));
            }
            vector.push(f64::from(value));
        }
        vectors.push(vector);
    }
    Ok(vectors)
}

fn build_report(loaded: &LoadedPilot) -> Result<FineRegionPilotReport> {
    let cosines = CosineMatrix::from_normalized_vectors(&loaded.vectors)?;
    let note_ids = loaded
        .evidence
        .iter()
        .map(|evidence| evidence.note_id.clone())
        .collect::<Vec<_>>();
    let levels = resolution_levels(&cosines, &note_ids, &loaded.config.resolution_percentiles)?;
    let pairwise = unordered_pair_values(&cosines)?;
    let cross_note_nearest = cross_note_nearest_values(&cosines, &note_ids)?;
    let orders = deterministic_orders(
        loaded.vectors.len(),
        loaded.config.dp_vmf_order_count,
        loaded.config.shuffle_seed,
    );

    let mut resolutions = Vec::with_capacity(levels.len());
    for level in levels {
        let complete = complete_linkage_partition(&cosines, level.pairwise_min_cosine)?;
        let complete_report = analyze_partition(&complete, &cosines, &note_ids)?;
        let dp_vmf = analyze_dp_vmf(
            &loaded.vectors,
            &cosines,
            &note_ids,
            level.centroid_min_cosine,
            &orders,
            &complete,
        )?;
        resolutions.push(ResolutionReport {
            audited: loaded.config.audit_percentiles.contains(&level.percentile),
            level,
            complete_linkage: complete_report,
            dp_vmf,
        });
    }

    Ok(FineRegionPilotReport {
        schema_version: REPORT_SCHEMA_VERSION,
        pilot_id: loaded.config.pilot_id.clone(),
        config_sha256: loaded.config_sha256.clone(),
        baseline_archive_sha256: loaded.config.baseline_archive_sha256.clone(),
        generation_manifest_sha256: loaded.generation_manifest_sha256.clone(),
        analysis_manifest_sha256: loaded.analysis_manifest_sha256.clone(),
        partition_source_sha256: hash_bytes(PARTITION_SOURCE),
        pilot_source_sha256: hash_bytes(PILOT_SOURCE),
        note_count: note_ids.iter().collect::<BTreeSet<_>>().len(),
        vector_count: loaded.vectors.len(),
        dimensions: loaded.dimensions,
        rules: PilotRules {
            resolution_source: "linear p10..p90 percentiles of each vector's nearest cross-note cosine"
                .to_owned(),
            complete_linkage: "merge maximum complete-link cosine; cut inclusively at pairwise threshold"
                .to_owned(),
            dp_vmf: "sequential DP-vMF assignment; native centroid threshold uses the same observed cosine level as complete linkage"
                .to_owned(),
            dp_vmf_orders: format!(
                "identity order followed by {} deterministic SplitMix64 Fisher-Yates shuffles from seed {}",
                loaded.config.dp_vmf_order_count - 1,
                loaded.config.shuffle_seed
            ),
            coassignment_order: "lower triangle: (1,0),(2,0),(2,1),...".to_owned(),
            labels_used_for_membership: false,
        },
        pairwise_cosines: summarize(&pairwise)?,
        cross_note_nearest_cosines: summarize(&cross_note_nearest)?,
        vectors: loaded.evidence.clone(),
        resolutions,
    })
}

fn analyze_partition(
    partition: &RegionPartition,
    cosines: &CosineMatrix,
    note_ids: &[String],
) -> Result<PartitionReport> {
    let mut ordinal_to_region = vec![usize::MAX; cosines.count()];
    for (region_index, members) in partition.regions().iter().enumerate() {
        for member in members {
            ordinal_to_region[*member] = region_index;
        }
    }
    if ordinal_to_region.contains(&usize::MAX) {
        return Err(invalid("partition analysis found an unassigned vector"));
    }

    let mut regions = Vec::with_capacity(partition.regions().len());
    for (region_index, members) in partition.regions().iter().enumerate() {
        let within_values = pair_values(cosines, members)?;
        let medoid = members
            .iter()
            .copied()
            .max_by(|left, right| {
                mean_similarity_to(cosines, *left, members)
                    .total_cmp(&mean_similarity_to(cosines, *right, members))
                    .then_with(|| right.cmp(left))
            })
            .expect("partition regions are nonempty");
        let mut member_geometry = Vec::with_capacity(members.len());
        for member in members {
            let nearest_within = best_neighbor(
                cosines,
                *member,
                members
                    .iter()
                    .copied()
                    .filter(|candidate| candidate != member),
            )?;
            let nearest_outside = best_neighbor(
                cosines,
                *member,
                (0..cosines.count()).filter(|candidate| {
                    ordinal_to_region[*candidate] != ordinal_to_region[*member]
                }),
            )?;
            let silhouette = silhouette(cosines, *member, region_index, partition.regions())?;
            member_geometry.push(MemberGeometry {
                ordinal: *member,
                nearest_within,
                nearest_outside,
                silhouette,
            });
        }
        let mut silhouettes = member_geometry
            .iter()
            .map(|member| member.silhouette)
            .collect::<Vec<_>>();
        silhouettes.sort_by(f64::total_cmp);
        let distinct_note_count = members
            .iter()
            .map(|member| note_ids[*member].as_str())
            .collect::<BTreeSet<_>>()
            .len();
        let nearest_external_cosine = member_geometry
            .iter()
            .filter_map(|member| {
                member
                    .nearest_outside
                    .as_ref()
                    .map(|neighbor| neighbor.cosine)
            })
            .max_by(f64::total_cmp);
        regions.push(RegionReport {
            region_index,
            members: members.clone(),
            distinct_note_count,
            medoid,
            minimum_within_cosine: within_values.first().copied(),
            median_within_cosine: (!within_values.is_empty())
                .then(|| linear_percentile(&within_values, 0.5)),
            nearest_external_cosine,
            minimum_silhouette: silhouettes[0],
            median_silhouette: linear_percentile(&silhouettes, 0.5),
            member_geometry,
        });
    }

    Ok(PartitionReport {
        region_count: regions.len(),
        singleton_count: regions
            .iter()
            .filter(|region| region.members.len() == 1)
            .count(),
        cross_note_region_count: regions
            .iter()
            .filter(|region| region.distinct_note_count > 1)
            .count(),
        regions,
    })
}

fn analyze_dp_vmf(
    vectors: &[Vec<f64>],
    cosines: &CosineMatrix,
    note_ids: &[String],
    centroid_min_cosine: f64,
    orders: &[Vec<usize>],
    complete: &RegionPartition,
) -> Result<DpVmfReport> {
    let mut partitions = Vec::with_capacity(orders.len());
    for order in orders {
        partitions.push(dp_vmf_partition(vectors, centroid_min_cosine, order)?);
    }
    let pair_count = vectors.len() * (vectors.len() - 1) / 2;
    let mut coassignments = vec![0_usize; pair_count];
    for partition in &partitions {
        let labels = partition_labels(partition, vectors.len())?;
        let mut pair = 0;
        for left in 1..vectors.len() {
            for right in 0..left {
                if labels[left] == labels[right] {
                    coassignments[pair] += 1;
                }
                pair += 1;
            }
        }
    }
    let probabilities = coassignments
        .iter()
        .map(|count| *count as f64 / orders.len() as f64)
        .collect::<Vec<_>>();
    let uncertain_pair_count = probabilities
        .iter()
        .filter(|probability| **probability > 0.1 && **probability < 0.9)
        .count();
    let coassignment_certainty_mean = probabilities
        .iter()
        .map(|probability| probability.max(1.0 - probability))
        .sum::<f64>()
        / probabilities.len() as f64;
    let complete_labels = partition_labels(complete, vectors.len())?;
    let mut within = Vec::new();
    let mut between_separation = Vec::new();
    let mut pair = 0;
    for left in 1..vectors.len() {
        for right in 0..left {
            if complete_labels[left] == complete_labels[right] {
                within.push(probabilities[pair]);
            } else {
                between_separation.push(1.0 - probabilities[pair]);
            }
            pair += 1;
        }
    }
    let complete_region_minimum_coassignment = complete
        .regions()
        .iter()
        .map(|region| {
            if region.len() == 1 {
                return None;
            }
            let mut minimum = 1.0_f64;
            for (position, left) in region.iter().enumerate() {
                for right in &region[(position + 1)..] {
                    minimum = minimum.min(probabilities[lower_triangle_index(*left, *right)]);
                }
            }
            Some(minimum)
        })
        .collect();
    let mut region_counts = partitions
        .iter()
        .map(|partition| partition.regions().len())
        .collect::<Vec<_>>();
    region_counts.sort_unstable();
    let serialized_partitions = partitions
        .iter()
        .map(|partition| partition.regions().to_vec())
        .collect::<Vec<_>>();
    let identity_order_partition = analyze_partition(&partitions[0], cosines, note_ids)?;

    Ok(DpVmfReport {
        order_count: orders.len(),
        region_count_minimum: region_counts[0],
        region_count_median: linear_percentile_usize(&region_counts, 0.5),
        region_count_maximum: *region_counts.last().expect("orders are nonempty"),
        uncertain_pair_count,
        coassignment_certainty_mean,
        complete_within_pair_coassignment_mean: mean_or_none(&within),
        complete_between_pair_separation_mean: mean_or_none(&between_separation),
        complete_region_minimum_coassignment,
        coassignment_lower_triangle: probabilities,
        partitions: serialized_partitions,
        identity_order_partition,
    })
}

fn render_audit(report: &FineRegionPilotReport) -> String {
    let mut output = String::new();
    output.push_str("# Fine-region membership audit\n\n");
    output.push_str(
        "This report shows raw membership evidence only. Region numbers are stable identifiers, not generated subject labels. No language influenced the partitions.\n\n",
    );
    output.push_str(&format!(
        "Input: {} vectors from {} notes. The three sections below are the frozen 40th, 50th, and 60th-percentile audit levels.\n\n",
        report.vector_count, report.note_count
    ));

    for resolution in report
        .resolutions
        .iter()
        .filter(|resolution| resolution.audited)
    {
        output.push_str(&format!(
            "## P{} · pairwise cosine {:.6} · maximum pair angle {:.2}°\n\n",
            resolution.level.percentile,
            resolution.level.pairwise_min_cosine,
            resolution.level.pairwise_max_angle_degrees
        ));
        output.push_str(&format!(
            "Complete linkage: {} regions; {} cross-note regions. DP-vMF identity order: {} regions; {} cross-note regions.\n\n",
            resolution.complete_linkage.region_count,
            resolution.complete_linkage.cross_note_region_count,
            resolution.dp_vmf.identity_order_partition.region_count,
            resolution
                .dp_vmf
                .identity_order_partition
                .cross_note_region_count,
        ));
        render_partition_audit(
            &mut output,
            "Complete linkage",
            "CL",
            resolution.level.percentile,
            &resolution.complete_linkage,
            &report.vectors,
        );
        render_partition_audit(
            &mut output,
            "DP-vMF identity order",
            "DP",
            resolution.level.percentile,
            &resolution.dp_vmf.identity_order_partition,
            &report.vectors,
        );
    }
    output
}

fn render_partition_audit(
    output: &mut String,
    heading: &str,
    prefix: &str,
    percentile: u8,
    partition: &PartitionReport,
    evidence: &[VectorEvidence],
) {
    output.push_str(&format!("### {heading}\n\n"));
    for region in partition
        .regions
        .iter()
        .filter(|region| region.distinct_note_count > 1)
    {
        output.push_str(&format!(
            "#### {prefix}-P{percentile}-R{:03} · {} vectors · {} notes\n\n",
            region.region_index + 1,
            region.members.len(),
            region.distinct_note_count,
        ));
        if let Some(minimum) = region.minimum_within_cosine {
            output.push_str(&format!(
                "Minimum member-pair cosine: `{minimum:.6}`. Nearest external cosine: `{:.6}`.\n\n",
                region.nearest_external_cosine.unwrap_or(f64::NAN)
            ));
        }
        for ordinal in &region.members {
            let item = &evidence[*ordinal];
            output.push_str(&format!(
                "- `V{:03}` · note `{}`\n  - Takeaway: {}\n  - Selected source: {}\n",
                item.ordinal,
                &item.note_id[..item.note_id.len().min(12)],
                single_line(&item.takeaway),
                item.selected_source_fragments
                    .iter()
                    .map(|fragment| {
                        let occurrence = (fragment.occurrence > 1)
                            .then(|| format!(" (occurrence {})", fragment.occurrence))
                            .unwrap_or_default();
                        format!("`{}`{occurrence}", escape_inline_code(&fragment.text))
                    })
                    .collect::<Vec<_>>()
                    .join(" + ")
            ));
        }
        output.push('\n');
    }
}

fn publish_artifact(
    output_path: &Path,
    loaded: &LoadedPilot,
    report: &FineRegionPilotReport,
    audit: &str,
) -> Result<()> {
    let parent = output_path
        .parent()
        .ok_or_else(|| invalid("output path has no parent"))?;
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let name = output_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| invalid("output path has no UTF-8 file name"))?;
    let stage = parent.join(format!(".{name}.stage-{}", std::process::id()));
    if stage.exists() {
        return Err(FineRegionPilotError::ArtifactExists(stage));
    }
    fs::create_dir(&stage).map_err(|source| io_error("create", &stage, source))?;

    write_json_new(&stage.join(ANALYSIS_FILE), report)?;
    write_bytes_new(&stage.join(AUDIT_FILE), audit.as_bytes())?;
    let files = [ANALYSIS_FILE, AUDIT_FILE]
        .into_iter()
        .map(|name| Ok((name.to_owned(), describe_file(&stage.join(name))?)))
        .collect::<Result<BTreeMap<_, _>>>()?;
    let manifest = PilotManifest {
        schema_version: MANIFEST_SCHEMA_VERSION,
        pilot_id: loaded.config.pilot_id.clone(),
        config_sha256: loaded.config_sha256.clone(),
        baseline_archive_sha256: loaded.config.baseline_archive_sha256.clone(),
        generation_manifest_sha256: loaded.generation_manifest_sha256.clone(),
        analysis_manifest_sha256: loaded.analysis_manifest_sha256.clone(),
        partition_source_sha256: hash_bytes(PARTITION_SOURCE),
        pilot_source_sha256: hash_bytes(PILOT_SOURCE),
        files,
    };
    write_json_new(&stage.join(MANIFEST_FILE), &manifest)?;
    fs::rename(&stage, output_path).map_err(|source| io_error("publish", output_path, source))?;
    Ok(())
}

fn validate_manifest(
    manifest: &PilotManifest,
    loaded: &LoadedPilot,
    output_path: &Path,
) -> Result<()> {
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION
        || manifest.pilot_id != loaded.config.pilot_id
        || manifest.config_sha256 != loaded.config_sha256
        || manifest.baseline_archive_sha256 != loaded.config.baseline_archive_sha256
        || manifest.generation_manifest_sha256 != loaded.generation_manifest_sha256
        || manifest.analysis_manifest_sha256 != loaded.analysis_manifest_sha256
        || manifest.partition_source_sha256 != hash_bytes(PARTITION_SOURCE)
        || manifest.pilot_source_sha256 != hash_bytes(PILOT_SOURCE)
        || manifest.files.len() != 2
    {
        return Err(invalid("result manifest identity is invalid"));
    }
    for name in [ANALYSIS_FILE, AUDIT_FILE] {
        let expected = manifest
            .files
            .get(name)
            .ok_or_else(|| invalid("result manifest omits an output file"))?;
        let actual = describe_file(&output_path.join(name))?;
        if expected != &actual {
            return Err(invalid(format!("result file identity changed for {name}")));
        }
    }
    Ok(())
}

fn unordered_pair_values(cosines: &CosineMatrix) -> Result<Vec<f64>> {
    let mut values = Vec::with_capacity(cosines.count() * (cosines.count() - 1) / 2);
    for left in 1..cosines.count() {
        for right in 0..left {
            values.push(cosines.get(left, right)?);
        }
    }
    Ok(values)
}

fn cross_note_nearest_values(cosines: &CosineMatrix, note_ids: &[String]) -> Result<Vec<f64>> {
    (0..cosines.count())
        .map(|left| {
            (0..cosines.count())
                .filter(|right| note_ids[*right] != note_ids[left])
                .map(|right| Ok(cosines.get(left, right)?))
                .collect::<Result<Vec<_>>>()?
                .into_iter()
                .max_by(f64::total_cmp)
                .ok_or_else(|| invalid("a vector has no cross-note neighbor"))
        })
        .collect()
}

fn pair_values(cosines: &CosineMatrix, members: &[usize]) -> Result<Vec<f64>> {
    let mut values = Vec::new();
    for (position, left) in members.iter().enumerate() {
        for right in &members[(position + 1)..] {
            values.push(cosines.get(*left, *right)?);
        }
    }
    values.sort_by(f64::total_cmp);
    Ok(values)
}

fn mean_similarity_to(cosines: &CosineMatrix, member: usize, region: &[usize]) -> f64 {
    if region.len() == 1 {
        return 1.0;
    }
    region
        .iter()
        .filter(|candidate| **candidate != member)
        .map(|candidate| cosines.get(member, *candidate).expect("validated member"))
        .sum::<f64>()
        / (region.len() - 1) as f64
}

fn best_neighbor(
    cosines: &CosineMatrix,
    ordinal: usize,
    candidates: impl Iterator<Item = usize>,
) -> Result<Option<Neighbor>> {
    let mut best: Option<Neighbor> = None;
    for candidate in candidates {
        let cosine = cosines.get(ordinal, candidate)?;
        if best.as_ref().is_none_or(|current| {
            cosine > current.cosine + COSINE_TOLERANCE
                || ((cosine - current.cosine).abs() <= COSINE_TOLERANCE
                    && candidate < current.ordinal)
        }) {
            best = Some(Neighbor {
                ordinal: candidate,
                cosine,
            });
        }
    }
    Ok(best)
}

fn silhouette(
    cosines: &CosineMatrix,
    ordinal: usize,
    own_region: usize,
    regions: &[Vec<usize>],
) -> Result<f64> {
    if regions[own_region].len() == 1 || regions.len() == 1 {
        return Ok(0.0);
    }
    let own = &regions[own_region];
    let a = own
        .iter()
        .filter(|candidate| **candidate != ordinal)
        .map(|candidate| Ok(1.0 - cosines.get(ordinal, *candidate)?))
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .sum::<f64>()
        / (own.len() - 1) as f64;
    let mut b = f64::INFINITY;
    for (region_index, region) in regions.iter().enumerate() {
        if region_index == own_region {
            continue;
        }
        let mean = region
            .iter()
            .map(|candidate| Ok(1.0 - cosines.get(ordinal, *candidate)?))
            .collect::<Result<Vec<_>>>()?
            .into_iter()
            .sum::<f64>()
            / region.len() as f64;
        b = b.min(mean);
    }
    let denominator = a.max(b);
    Ok(if denominator <= 0.0 {
        0.0
    } else {
        (b - a) / denominator
    })
}

fn summarize(values: &[f64]) -> Result<DistributionSummary> {
    if values.is_empty() || values.iter().any(|value| !value.is_finite()) {
        return Err(invalid(
            "cannot summarize an empty or non-finite distribution",
        ));
    }
    let mut sorted = values.to_vec();
    sorted.sort_by(f64::total_cmp);
    Ok(DistributionSummary {
        count: sorted.len(),
        minimum: sorted[0],
        p05: linear_percentile(&sorted, 0.05),
        p25: linear_percentile(&sorted, 0.25),
        median: linear_percentile(&sorted, 0.50),
        p75: linear_percentile(&sorted, 0.75),
        p95: linear_percentile(&sorted, 0.95),
        maximum: *sorted.last().expect("nonempty distribution"),
        mean: sorted.iter().sum::<f64>() / sorted.len() as f64,
    })
}

fn deterministic_orders(count: usize, order_count: usize, seed: u64) -> Vec<Vec<usize>> {
    let identity = (0..count).collect::<Vec<_>>();
    let mut orders = Vec::with_capacity(order_count);
    orders.push(identity.clone());
    let mut state = seed;
    for _ in 1..order_count {
        let mut order = identity.clone();
        for position in (1..count).rev() {
            let swap = (splitmix64(&mut state) % (position as u64 + 1)) as usize;
            order.swap(position, swap);
        }
        orders.push(order);
    }
    orders
}

fn splitmix64(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9e37_79b9_7f4a_7c15);
    let mut value = *state;
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

fn partition_labels(partition: &RegionPartition, count: usize) -> Result<Vec<usize>> {
    let mut labels = vec![usize::MAX; count];
    for (region_index, region) in partition.regions().iter().enumerate() {
        for ordinal in region {
            if *ordinal >= count || labels[*ordinal] != usize::MAX {
                return Err(invalid("partition repeats or exceeds a vector ordinal"));
            }
            labels[*ordinal] = region_index;
        }
    }
    if labels.contains(&usize::MAX) {
        return Err(invalid("partition omits a vector ordinal"));
    }
    Ok(labels)
}

fn lower_triangle_index(left: usize, right: usize) -> usize {
    let (high, low) = if left > right {
        (left, right)
    } else {
        (right, left)
    };
    high * (high - 1) / 2 + low
}

fn mean_or_none(values: &[f64]) -> Option<f64> {
    (!values.is_empty()).then(|| values.iter().sum::<f64>() / values.len() as f64)
}

fn linear_percentile(sorted: &[f64], quantile: f64) -> f64 {
    let position = (sorted.len() - 1) as f64 * quantile;
    let lower = position.floor() as usize;
    let upper = position.ceil() as usize;
    sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower as f64)
}

fn linear_percentile_usize(sorted: &[usize], quantile: f64) -> f64 {
    let position = (sorted.len() - 1) as f64 * quantile;
    let lower = position.floor() as usize;
    let upper = position.ceil() as usize;
    sorted[lower] as f64 + (sorted[upper] as f64 - sorted[lower] as f64) * (position - lower as f64)
}

fn single_line(value: &str) -> String {
    value.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn escape_inline_code(value: &str) -> String {
    single_line(value).replace('`', "\\`")
}

fn load_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let bytes = read_bytes(path)?;
    serde_json::from_slice(&bytes).map_err(|source| FineRegionPilotError::Json {
        operation: "parse",
        path: path.to_path_buf(),
        source,
    })
}

fn read_bytes(path: &Path) -> Result<Vec<u8>> {
    let mut file = File::open(path).map_err(|source| io_error("open", path, source))?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| io_error("read", path, source))?;
    Ok(bytes)
}

fn read_string(path: &Path) -> Result<String> {
    let bytes = read_bytes(path)?;
    String::from_utf8(bytes)
        .map_err(|source| invalid(format!("{} is not valid UTF-8: {source}", path.display())))
}

fn write_json_new<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let mut bytes =
        serde_json::to_vec_pretty(value).map_err(|source| FineRegionPilotError::Json {
            operation: "serialize",
            path: path.to_path_buf(),
            source,
        })?;
    bytes.push(b'\n');
    write_bytes_new(path, &bytes)
}

fn write_bytes_new(path: &Path, bytes: &[u8]) -> Result<()> {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    writer
        .write_all(bytes)
        .map_err(|source| io_error("write", path, source))?;
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    Ok(())
}

fn describe_file(path: &Path) -> Result<FileIdentity> {
    let metadata = fs::metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if !metadata.is_file() {
        return Err(invalid(format!("{} is not a regular file", path.display())));
    }
    Ok(FileIdentity {
        bytes: metadata.len(),
        sha256: hash_file(path)?,
    })
}

fn verify_manifest_file(root: &Path, manifest: &ExternalManifest, name: &str) -> Result<PathBuf> {
    let expected = manifest
        .files
        .get(name)
        .ok_or_else(|| invalid(format!("external manifest omits {name}")))?;
    let path = resolve_baseline_path(root, name)?;
    let actual = describe_file(&path)?;
    if &actual != expected {
        return Err(invalid(format!(
            "external manifest identity changed for {name}"
        )));
    }
    Ok(path)
}

fn verify_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_file(path)?;
    if actual != expected {
        return Err(FineRegionPilotError::HashMismatch {
            path: path.to_path_buf(),
            expected: expected.to_owned(),
            actual,
        });
    }
    Ok(())
}

fn resolve_baseline_path(root: &Path, relative: &str) -> Result<PathBuf> {
    validate_relative_path(relative)?;
    let canonical_root =
        fs::canonicalize(root).map_err(|source| io_error("canonicalize", root, source))?;
    let joined = canonical_root.join(relative);
    let canonical_path =
        fs::canonicalize(&joined).map_err(|source| io_error("canonicalize", &joined, source))?;
    if !canonical_path.starts_with(&canonical_root) {
        return Err(invalid("baseline path escapes the baseline root"));
    }
    Ok(canonical_path)
}

fn validate_relative_path(path: &str) -> Result<()> {
    let path = Path::new(path);
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(invalid("artifact path is not a plain relative path"));
    }
    Ok(())
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn invalid(message: impl Into<String>) -> FineRegionPilotError {
    FineRegionPilotError::Invariant(message.into())
}

fn io_error(operation: &'static str, path: &Path, source: io::Error) -> FineRegionPilotError {
    FineRegionPilotError::Io {
        operation,
        path: path.to_path_buf(),
        source,
    }
}
