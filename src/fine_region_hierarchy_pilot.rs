//! Frozen pilot that turns the reviewed fine-region boundary into a complete hierarchy.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufWriter, Read, Write};
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::{hash_bytes, hash_file};
use crate::fine_region_hierarchy::{
    FineRegionHierarchy, FineSegment, HierarchyNode, average_linkage_hierarchy,
    average_linkage_hierarchy_over_selected_segments,
};
use crate::fine_region_partition::{CosineMatrix, complete_linkage_partition};

const CONFIG_SCHEMA_VERSION: u32 = 2;
const REPORT_SCHEMA_VERSION: u32 = 2;
const MANIFEST_SCHEMA_VERSION: u32 = 1;
const ANALYSIS_FILE: &str = "analysis.json";
const AUDIT_FILE: &str = "audit.md";
const MANIFEST_FILE: &str = "manifest.json";
const HIERARCHY_SOURCE: &[u8] = include_bytes!("fine_region_hierarchy.rs");
const PILOT_SOURCE: &[u8] = include_bytes!("fine_region_hierarchy_pilot.rs");
const PARTITION_SOURCE: &[u8] = include_bytes!("fine_region_partition.rs");
const CARGO_LOCK: &[u8] = include_bytes!("../Cargo.lock");

pub type Result<T> = std::result::Result<T, FineRegionHierarchyPilotError>;

#[derive(Debug, Error)]
pub enum FineRegionHierarchyPilotError {
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
    #[error("fine-region hierarchy pilot artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("fine-region hierarchy pilot artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),
    #[error("fine-region hierarchy pilot invariant failed: {0}")]
    Invariant(String),
    #[error(
        "fine-region hierarchy pilot input hash mismatch for `{path}`: expected {expected}, got {actual}"
    )]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("fine-region hierarchy pilot replay differs from `{0}`")]
    ReplayMismatch(PathBuf),
    #[error(transparent)]
    Hierarchy(#[from] crate::fine_region_hierarchy::FineRegionHierarchyError),
    #[error(transparent)]
    Partition(#[from] crate::fine_region_partition::FineRegionPartitionError),
    #[error(transparent)]
    Source(#[from] crate::snapshot::Error),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PilotConfig {
    schema_version: u32,
    pilot_id: String,
    #[serde(default)]
    fine_segment_selection: FineSegmentSelection,
    baseline_archive_sha256: String,
    analysis_manifest_sha256: String,
    normalized_vectors: BoundFile,
    partition_analysis_sha256: String,
    review_decisions_sha256: String,
    vector_count: usize,
    dimensions: usize,
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FineSegmentSelection {
    #[default]
    CompleteReviewedCut,
    MaximalCrossNoteSets,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BoundFile {
    path: String,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
struct PartitionAnalysisIdentity {
    baseline_archive_sha256: String,
    analysis_manifest_sha256: String,
    vector_count: usize,
    dimensions: usize,
    vectors: Vec<PartitionVectorIdentity>,
}

#[derive(Clone, Debug, Deserialize)]
struct PartitionVectorIdentity {
    ordinal: usize,
    note_id: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReviewRecord {
    schema_version: u32,
    criterion: String,
    decision_owner: String,
    decisions: Vec<ReviewDecision>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReviewDecision {
    segment_id: String,
    minimum_cosine: f64,
    title_reviewed: String,
    decision: String,
    #[serde(default)]
    note: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FileIdentity {
    bytes: u64,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionHierarchyPilotReport {
    pub schema_version: u32,
    pub pilot_id: String,
    pub config_sha256: String,
    pub baseline_archive_sha256: String,
    pub analysis_manifest_sha256: String,
    pub normalized_vectors_sha256: String,
    pub partition_analysis_sha256: String,
    pub review_decisions_sha256: String,
    pub hierarchy_source_sha256: String,
    pub pilot_source_sha256: String,
    pub partition_source_sha256: String,
    pub cargo_lock_sha256: String,
    pub vector_count: usize,
    pub dimensions: usize,
    pub accepted_review_count: usize,
    pub accepted_minimum_cosine: f64,
    pub first_rejected_minimum_cosine: f64,
    pub partition_cutoff_cosine: f64,
    pub fine_segment_selection: FineSegmentSelection,
    pub cross_note_candidate_segment_count: usize,
    pub cross_note_fine_segment_count: usize,
    pub excluded_strict_subset_segment_count: usize,
    pub singleton_fine_segment_count: usize,
    pub unreviewed_same_note_group_count: usize,
    pub unreviewed_same_note_vector_count: usize,
    pub hierarchy_vector_count: usize,
    pub hierarchy_note_count: usize,
    pub rules: HierarchyPilotRules,
    pub hierarchy: FineRegionHierarchy,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyPilotRules {
    pub fine_segments: String,
    pub higher_groups: String,
    pub fine_segment_weighting: String,
    pub labels_used_for_geometry: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PilotManifest {
    schema_version: u32,
    pilot_id: String,
    config_sha256: String,
    baseline_archive_sha256: String,
    analysis_manifest_sha256: String,
    normalized_vectors_sha256: String,
    partition_analysis_sha256: String,
    review_decisions_sha256: String,
    hierarchy_source_sha256: String,
    pilot_source_sha256: String,
    partition_source_sha256: String,
    cargo_lock_sha256: String,
    files: BTreeMap<String, FileIdentity>,
}

struct LoadedPilot {
    config: PilotConfig,
    config_sha256: String,
    vectors: Vec<Vec<f64>>,
    note_ids: Vec<String>,
    accepted_review_count: usize,
    accepted_minimum_cosine: f64,
    first_rejected_minimum_cosine: f64,
}

pub fn run_fine_region_hierarchy_pilot(
    config_path: impl AsRef<Path>,
    baseline_root: impl AsRef<Path>,
    partition_analysis_path: impl AsRef<Path>,
    review_decisions_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<FineRegionHierarchyPilotReport> {
    let output_path = output_path.as_ref();
    if output_path.exists() {
        return Err(FineRegionHierarchyPilotError::ArtifactExists(
            output_path.to_path_buf(),
        ));
    }
    let loaded = load_pilot(
        config_path.as_ref(),
        baseline_root.as_ref(),
        partition_analysis_path.as_ref(),
        review_decisions_path.as_ref(),
    )?;
    let report = build_report(&loaded)?;
    let audit = render_audit(&report);
    publish_artifact(output_path, &loaded, &report, &audit)?;
    Ok(report)
}

pub fn ensure_fine_region_hierarchy_pilot(
    config_path: impl AsRef<Path>,
    baseline_root: impl AsRef<Path>,
    partition_analysis_path: impl AsRef<Path>,
    review_decisions_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<FineRegionHierarchyPilotReport> {
    let config_path = config_path.as_ref();
    let baseline_root = baseline_root.as_ref();
    let partition_analysis_path = partition_analysis_path.as_ref();
    let review_decisions_path = review_decisions_path.as_ref();
    let output_path = output_path.as_ref();
    if output_path.exists() {
        verify_fine_region_hierarchy_pilot(
            config_path,
            baseline_root,
            partition_analysis_path,
            review_decisions_path,
            output_path,
        )
    } else {
        run_fine_region_hierarchy_pilot(
            config_path,
            baseline_root,
            partition_analysis_path,
            review_decisions_path,
            output_path,
        )?;
        verify_fine_region_hierarchy_pilot(
            config_path,
            baseline_root,
            partition_analysis_path,
            review_decisions_path,
            output_path,
        )
    }
}

pub fn verify_fine_region_hierarchy_pilot(
    config_path: impl AsRef<Path>,
    baseline_root: impl AsRef<Path>,
    partition_analysis_path: impl AsRef<Path>,
    review_decisions_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<FineRegionHierarchyPilotReport> {
    let output_path = output_path.as_ref();
    if !output_path.is_dir() {
        return Err(FineRegionHierarchyPilotError::ArtifactMissing(
            output_path.to_path_buf(),
        ));
    }
    let loaded = load_pilot(
        config_path.as_ref(),
        baseline_root.as_ref(),
        partition_analysis_path.as_ref(),
        review_decisions_path.as_ref(),
    )?;
    let manifest: PilotManifest = load_json(&output_path.join(MANIFEST_FILE))?;
    validate_manifest(&manifest, &loaded, output_path)?;

    let recorded: FineRegionHierarchyPilotReport = load_json(&output_path.join(ANALYSIS_FILE))?;
    let expected = build_report(&loaded)?;
    if recorded != expected {
        return Err(FineRegionHierarchyPilotError::ReplayMismatch(
            output_path.join(ANALYSIS_FILE),
        ));
    }
    if read_string(&output_path.join(AUDIT_FILE))? != render_audit(&expected) {
        return Err(FineRegionHierarchyPilotError::ReplayMismatch(
            output_path.join(AUDIT_FILE),
        ));
    }
    Ok(recorded)
}

fn load_pilot(
    config_path: &Path,
    baseline_root: &Path,
    partition_analysis_path: &Path,
    review_decisions_path: &Path,
) -> Result<LoadedPilot> {
    let config_sha256 = hash_file(config_path)?;
    let config: PilotConfig = load_json(config_path)?;
    validate_config(&config)?;

    verify_hash(partition_analysis_path, &config.partition_analysis_sha256)?;
    let partition: PartitionAnalysisIdentity = load_json(partition_analysis_path)?;
    if partition.baseline_archive_sha256 != config.baseline_archive_sha256
        || partition.analysis_manifest_sha256 != config.analysis_manifest_sha256
        || partition.vector_count != config.vector_count
        || partition.dimensions != config.dimensions
    {
        return Err(invalid(
            "the partition analysis does not match the configured vector baseline",
        ));
    }
    let note_ids = ordered_note_ids(partition.vectors, config.vector_count)?;

    verify_hash(review_decisions_path, &config.review_decisions_sha256)?;
    let review: ReviewRecord = load_json(review_decisions_path)?;
    let (accepted_review_count, accepted_minimum_cosine, first_rejected_minimum_cosine) =
        validate_review(&review)?;

    let vector_path = resolve_baseline_path(baseline_root, &config.normalized_vectors.path)?;
    verify_hash(&vector_path, &config.normalized_vectors.sha256)?;
    let vectors = read_vectors(&vector_path, config.vector_count, config.dimensions)?;
    CosineMatrix::from_normalized_vectors(&vectors)?;

    Ok(LoadedPilot {
        config,
        config_sha256,
        vectors,
        note_ids,
        accepted_review_count,
        accepted_minimum_cosine,
        first_rejected_minimum_cosine,
    })
}

fn ordered_note_ids(
    mut vectors: Vec<PartitionVectorIdentity>,
    vector_count: usize,
) -> Result<Vec<String>> {
    vectors.sort_by_key(|vector| vector.ordinal);
    if vectors.len() != vector_count
        || vectors
            .iter()
            .enumerate()
            .any(|(ordinal, vector)| vector.ordinal != ordinal || vector.note_id.trim().is_empty())
    {
        return Err(invalid(
            "partition vector identities must cover every configured ordinal exactly once",
        ));
    }
    Ok(vectors.into_iter().map(|vector| vector.note_id).collect())
}

fn validate_config(config: &PilotConfig) -> Result<()> {
    let schema_and_selection_are_valid = matches!(
        (config.schema_version, config.fine_segment_selection),
        (1, FineSegmentSelection::CompleteReviewedCut)
            | (
                CONFIG_SCHEMA_VERSION,
                FineSegmentSelection::MaximalCrossNoteSets
            )
    );
    if !schema_and_selection_are_valid
        || config.pilot_id.trim().is_empty()
        || config.vector_count < 2
        || config.dimensions == 0
        || !is_lower_hex(&config.baseline_archive_sha256, 64)
        || !is_lower_hex(&config.analysis_manifest_sha256, 64)
        || !is_lower_hex(&config.normalized_vectors.sha256, 64)
        || !is_lower_hex(&config.partition_analysis_sha256, 64)
        || !is_lower_hex(&config.review_decisions_sha256, 64)
    {
        return Err(invalid("pilot config identity or dimensions are invalid"));
    }
    validate_relative_path(&config.normalized_vectors.path)
}

fn validate_review(review: &ReviewRecord) -> Result<(usize, f64, f64)> {
    if review.schema_version != 1
        || review.criterion.trim().is_empty()
        || review.decision_owner != "user"
        || review.decisions.len() < 2
    {
        return Err(invalid("fine-segment review identity is invalid"));
    }
    let accepted = review
        .decisions
        .iter()
        .filter(|decision| decision.decision == "pass")
        .collect::<Vec<_>>();
    let rejected = review
        .decisions
        .iter()
        .filter(|decision| decision.decision == "fail")
        .collect::<Vec<_>>();
    if accepted.is_empty()
        || rejected.len() != 1
        || review
            .decisions
            .last()
            .map(|decision| decision.decision.as_str())
            != Some("fail")
        || review.decisions.iter().any(|decision| {
            decision.segment_id.trim().is_empty()
                || decision.title_reviewed.trim().is_empty()
                || !decision.minimum_cosine.is_finite()
                || !matches!(decision.decision.as_str(), "pass" | "fail")
                || decision
                    .note
                    .as_ref()
                    .is_some_and(|note| note.trim().is_empty())
        })
    {
        return Err(invalid(
            "review must end at exactly one explicit failure after accepted segments",
        ));
    }

    let accepted_minimum = accepted
        .iter()
        .map(|decision| decision.minimum_cosine)
        .min_by(f64::total_cmp)
        .expect("accepted review is not empty");
    let rejected_minimum = rejected[0].minimum_cosine;
    if accepted_minimum <= rejected_minimum {
        return Err(invalid(
            "the accepted review scores do not define a boundary above the first failure",
        ));
    }
    Ok((accepted.len(), accepted_minimum, rejected_minimum))
}

fn build_report(loaded: &LoadedPilot) -> Result<FineRegionHierarchyPilotReport> {
    let cosines = CosineMatrix::from_normalized_vectors(&loaded.vectors)?;
    let partition_cutoff_cosine = loaded.first_rejected_minimum_cosine
        + (loaded.accepted_minimum_cosine - loaded.first_rejected_minimum_cosine) / 2.0;
    if !partition_cutoff_cosine.is_finite()
        || partition_cutoff_cosine <= loaded.first_rejected_minimum_cosine
        || partition_cutoff_cosine >= loaded.accepted_minimum_cosine
    {
        return Err(invalid(
            "the reviewed pass and failure do not define a representable partition cutoff",
        ));
    }
    let partition = complete_linkage_partition(&cosines, partition_cutoff_cosine)?;
    let mut cross_note_candidates = Vec::new();
    let mut unreviewed_same_note_group_count = 0;
    let mut unreviewed_same_note_vector_count = 0;
    for members in partition.regions() {
        let distinct_notes = members
            .iter()
            .map(|member| loaded.note_ids[*member].as_str())
            .collect::<BTreeSet<_>>();
        if distinct_notes.len() > 1 {
            cross_note_candidates.push((members.clone(), distinct_notes));
        } else if members.len() > 1 {
            unreviewed_same_note_group_count += 1;
            unreviewed_same_note_vector_count += members.len();
        }
    }

    let cross_note_candidate_segment_count = cross_note_candidates.len();
    let (mut groups, excluded_strict_subset_segment_count) =
        match loaded.config.fine_segment_selection {
            FineSegmentSelection::CompleteReviewedCut => {
                let mut groups = Vec::new();
                for members in partition.regions() {
                    let distinct_note_count = members
                        .iter()
                        .map(|member| loaded.note_ids[*member].as_str())
                        .collect::<BTreeSet<_>>()
                        .len();
                    if distinct_note_count > 1 {
                        groups.push(members.clone());
                    } else {
                        groups.extend(members.iter().map(|member| vec![*member]));
                    }
                }
                (groups, 0)
            }
            FineSegmentSelection::MaximalCrossNoteSets => {
                if cross_note_candidates
                    .iter()
                    .enumerate()
                    .any(|(index, left)| {
                        cross_note_candidates
                            .iter()
                            .skip(index + 1)
                            .any(|right| left.1 == right.1)
                    })
                {
                    return Err(invalid(
                        "multiple cross-note candidate segments resolve to the same note set",
                    ));
                }
                let groups = cross_note_candidates
                    .iter()
                    .filter(|candidate| {
                        !cross_note_candidates.iter().any(|other| {
                            candidate.1.len() < other.1.len() && candidate.1.is_subset(&other.1)
                        })
                    })
                    .map(|candidate| candidate.0.clone())
                    .collect::<Vec<_>>();
                let excluded = cross_note_candidate_segment_count - groups.len();
                (groups, excluded)
            }
        };
    groups.sort_by_key(|members| members[0]);
    let fine_segments = groups
        .into_iter()
        .enumerate()
        .map(|(index, members)| FineSegment {
            segment_id: format!("F{index:06}"),
            members,
        })
        .collect::<Vec<_>>();
    let singleton_fine_segment_count = fine_segments
        .iter()
        .filter(|segment| segment.members.len() == 1)
        .count();
    let hierarchy_vector_count = fine_segments
        .iter()
        .map(|segment| segment.members.len())
        .sum();
    let hierarchy_note_count = fine_segments
        .iter()
        .flat_map(|segment| segment.members.iter())
        .map(|member| loaded.note_ids[*member].as_str())
        .collect::<BTreeSet<_>>()
        .len();
    let hierarchy = match loaded.config.fine_segment_selection {
        FineSegmentSelection::CompleteReviewedCut => {
            average_linkage_hierarchy(&loaded.vectors, &fine_segments)?
        }
        FineSegmentSelection::MaximalCrossNoteSets => {
            average_linkage_hierarchy_over_selected_segments(&loaded.vectors, &fine_segments)?
        }
    };
    let cross_note_fine_segment_count = fine_segments
        .iter()
        .filter(|segment| {
            segment
                .members
                .iter()
                .map(|member| loaded.note_ids[*member].as_str())
                .collect::<BTreeSet<_>>()
                .len()
                > 1
        })
        .count();

    Ok(FineRegionHierarchyPilotReport {
        schema_version: REPORT_SCHEMA_VERSION,
        pilot_id: loaded.config.pilot_id.clone(),
        config_sha256: loaded.config_sha256.clone(),
        baseline_archive_sha256: loaded.config.baseline_archive_sha256.clone(),
        analysis_manifest_sha256: loaded.config.analysis_manifest_sha256.clone(),
        normalized_vectors_sha256: loaded.config.normalized_vectors.sha256.clone(),
        partition_analysis_sha256: loaded.config.partition_analysis_sha256.clone(),
        review_decisions_sha256: loaded.config.review_decisions_sha256.clone(),
        hierarchy_source_sha256: hash_bytes(HIERARCHY_SOURCE),
        pilot_source_sha256: hash_bytes(PILOT_SOURCE),
        partition_source_sha256: hash_bytes(PARTITION_SOURCE),
        cargo_lock_sha256: hash_bytes(CARGO_LOCK),
        vector_count: loaded.config.vector_count,
        dimensions: loaded.config.dimensions,
        accepted_review_count: loaded.accepted_review_count,
        accepted_minimum_cosine: loaded.accepted_minimum_cosine,
        first_rejected_minimum_cosine: loaded.first_rejected_minimum_cosine,
        partition_cutoff_cosine,
        fine_segment_selection: loaded.config.fine_segment_selection,
        cross_note_candidate_segment_count,
        cross_note_fine_segment_count,
        excluded_strict_subset_segment_count,
        singleton_fine_segment_count,
        unreviewed_same_note_group_count,
        unreviewed_same_note_vector_count,
        hierarchy_vector_count,
        hierarchy_note_count,
        rules: HierarchyPilotRules {
            fine_segments: match loaded.config.fine_segment_selection {
                FineSegmentSelection::CompleteReviewedCut => "retain cross-note complete-linkage groups at the lowest reviewed pass before the first explicit failure; leave every other vector singleton".to_owned(),
                FineSegmentSelection::MaximalCrossNoteSets => "from the complete-linkage cut, retain only groups spanning at least two distinct notes whose note set is not a strict subset of another eligible group".to_owned(),
            },
            higher_groups: "exact average linkage over the selected fine segments; preserve all binary merges".to_owned(),
            fine_segment_weighting: "each fine segment is one equally weighted observation, regardless of vector-member count".to_owned(),
            labels_used_for_geometry: false,
        },
        hierarchy,
    })
}

fn render_audit(report: &FineRegionHierarchyPilotReport) -> String {
    let mut output = String::new();
    output.push_str("# Fine-segment hierarchy pilot\n\n");
    output.push_str("This artifact preserves geometry only. No generated title influenced a segment or hierarchy merge.\n\n");
    output.push_str(&format!(
        "- Input: {} vectors in {} dimensions\n- Reviewed boundary: {} passes through `{:.6}`, then first failure at `{:.6}`\n- Partition cutoff between those decisions: `{:.6}`\n- Fine-segment selection: `{:?}`\n- Cross-note candidates before maximal filtering: {}\n- Strict-subset candidates excluded: {}\n- Fine segments selected: {}\n- Source notes represented: {}\n- Vectors represented: {}\n- Singleton fine segments selected: {}\n- Unreviewed same-note groups retained only in the source artifact: {} groups containing {} vectors\n- Higher merges: {}\n\n",
        report.vector_count,
        report.dimensions,
        report.accepted_review_count,
        report.accepted_minimum_cosine,
        report.first_rejected_minimum_cosine,
        report.partition_cutoff_cosine,
        report.fine_segment_selection,
        report.cross_note_candidate_segment_count,
        report.excluded_strict_subset_segment_count,
        report.cross_note_fine_segment_count,
        report.hierarchy_note_count,
        report.hierarchy_vector_count,
        report.singleton_fine_segment_count,
        report.unreviewed_same_note_group_count,
        report.unreviewed_same_note_vector_count,
        report.hierarchy.merges.len(),
    ));

    output.push_str("## Fine segments\n\n");
    for segment in &report.hierarchy.fine_segments {
        output.push_str(&format!(
            "- `{}`: {}\n",
            segment.segment_id,
            segment
                .members
                .iter()
                .map(|member| format!("V{member:03}"))
                .collect::<Vec<_>>()
                .join(" ")
        ));
    }

    output.push_str("\n## Complete higher-level merge tree\n\n");
    for merge in &report.hierarchy.merges {
        output.push_str(&format!(
            "- `H{:06}` · cosine `{:.6}` · {} fine segments: {} + {}\n",
            merge.merge_index,
            merge.similarity,
            merge.fine_segment_count,
            node_name(&merge.children[0]),
            node_name(&merge.children[1]),
        ));
    }
    output
}

fn node_name(node: &HierarchyNode) -> String {
    match node {
        HierarchyNode::FineSegment(segment_id) => format!("`{segment_id}`"),
        HierarchyNode::Merge(index) => format!("`H{index:06}`"),
    }
}

fn publish_artifact(
    output_path: &Path,
    loaded: &LoadedPilot,
    report: &FineRegionHierarchyPilotReport,
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
        return Err(FineRegionHierarchyPilotError::ArtifactExists(stage));
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
        analysis_manifest_sha256: loaded.config.analysis_manifest_sha256.clone(),
        normalized_vectors_sha256: loaded.config.normalized_vectors.sha256.clone(),
        partition_analysis_sha256: loaded.config.partition_analysis_sha256.clone(),
        review_decisions_sha256: loaded.config.review_decisions_sha256.clone(),
        hierarchy_source_sha256: hash_bytes(HIERARCHY_SOURCE),
        pilot_source_sha256: hash_bytes(PILOT_SOURCE),
        partition_source_sha256: hash_bytes(PARTITION_SOURCE),
        cargo_lock_sha256: hash_bytes(CARGO_LOCK),
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
        || manifest.analysis_manifest_sha256 != loaded.config.analysis_manifest_sha256
        || manifest.normalized_vectors_sha256 != loaded.config.normalized_vectors.sha256
        || manifest.partition_analysis_sha256 != loaded.config.partition_analysis_sha256
        || manifest.review_decisions_sha256 != loaded.config.review_decisions_sha256
        || manifest.hierarchy_source_sha256 != hash_bytes(HIERARCHY_SOURCE)
        || manifest.pilot_source_sha256 != hash_bytes(PILOT_SOURCE)
        || manifest.partition_source_sha256 != hash_bytes(PARTITION_SOURCE)
        || manifest.cargo_lock_sha256 != hash_bytes(CARGO_LOCK)
        || manifest.files.len() != 2
    {
        return Err(invalid("result manifest identity is invalid"));
    }
    for name in [ANALYSIS_FILE, AUDIT_FILE] {
        let expected = manifest
            .files
            .get(name)
            .ok_or_else(|| invalid("result manifest omits an output file"))?;
        if expected != &describe_file(&output_path.join(name))? {
            return Err(invalid(format!("result file identity changed for {name}")));
        }
    }
    Ok(())
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
    bytes
        .chunks_exact(dimensions * 4)
        .map(|row| {
            row.chunks_exact(4)
                .map(|coordinate| {
                    let value = f32::from_le_bytes(coordinate.try_into().expect("four bytes"));
                    value
                        .is_finite()
                        .then_some(f64::from(value))
                        .ok_or_else(|| {
                            invalid("normalized vector file contains a non-finite value")
                        })
                })
                .collect()
        })
        .collect()
}

fn resolve_baseline_path(root: &Path, relative: &str) -> Result<PathBuf> {
    validate_relative_path(relative)?;
    Ok(root.join(relative))
}

fn validate_relative_path(path: &str) -> Result<()> {
    let path = Path::new(path);
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(invalid("artifact input path is not a safe relative path"));
    }
    Ok(())
}

fn verify_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_file(path)?;
    if actual != expected {
        return Err(FineRegionHierarchyPilotError::HashMismatch {
            path: path.to_path_buf(),
            expected: expected.to_owned(),
            actual,
        });
    }
    Ok(())
}

fn describe_file(path: &Path) -> Result<FileIdentity> {
    let bytes = fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    Ok(FileIdentity {
        bytes,
        sha256: hash_file(path)?,
    })
}

fn load_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let bytes = read_bytes(path)?;
    serde_json::from_slice(&bytes).map_err(|source| FineRegionHierarchyPilotError::Json {
        operation: "decode",
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
    String::from_utf8(read_bytes(path)?)
        .map_err(|_| invalid(format!("{} is not UTF-8", path.display())))
}

fn write_json_new<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let mut bytes =
        serde_json::to_vec_pretty(value).map_err(|source| FineRegionHierarchyPilotError::Json {
            operation: "encode",
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

fn io_error(
    operation: &'static str,
    path: &Path,
    source: io::Error,
) -> FineRegionHierarchyPilotError {
    FineRegionHierarchyPilotError::Io {
        operation,
        path: path.to_path_buf(),
        source,
    }
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn invalid(message: impl Into<String>) -> FineRegionHierarchyPilotError {
    FineRegionHierarchyPilotError::Invariant(message.into())
}
