//! Non-evaluative capacity execution of the complete Phase 3 learning path.

use std::collections::BTreeSet;
use std::fs;
use std::io::{self, Write};
use std::os::fd::AsRawFd;
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use crate::adaptive_learning::CompletedAdaptiveLearning;
use crate::adaptive_learning_runner::{
    AdaptiveLearningRunnerConfig, AdaptiveLearningRunnerOutcome, run_adaptive_learning,
};
use crate::candidate_order::{CandidateOrderAttempt, CandidateOrderOracle};
use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RestOutcome, RestView,
};
use crate::snapshot::{Error, Result};

/// The kernel-enforced memory boundary shared by the controller and worker.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct CombinedMemoryLimitObservation {
    memory_max_bytes: u64,
    memory_swap_max_bytes: u64,
}

/// Host memory remaining after honoring the run ceiling, existing swap debt,
/// and the operator-approved reserve.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct HostMemoryAdmissionObservation {
    available_bytes: u64,
    swap_used_bytes: u64,
    reserve_bytes: u64,
    run_limit_bytes: u64,
    headroom_bytes: u64,
}

impl HostMemoryAdmissionObservation {
    pub const fn headroom_bytes(self) -> u64 {
        self.headroom_bytes
    }
}

/// Files and bytes explicitly submitted to the kernel's cache-eviction advice.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct FileCacheEvictionObservation {
    files: usize,
    bytes: u64,
}

/// File-backed pages resident in RAM at one admission boundary.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct FileCacheResidencyObservation {
    files: usize,
    bytes: u64,
}

impl FileCacheResidencyObservation {
    pub const fn files(self) -> usize {
        self.files
    }

    pub const fn bytes(self) -> u64 {
        self.bytes
    }
}

impl FileCacheEvictionObservation {
    pub const fn files(self) -> usize {
        self.files
    }

    pub const fn bytes(self) -> u64 {
        self.bytes
    }
}

/// Remove prior page-cache ownership from the exact immutable input files.
/// File contents and metadata are not modified.
pub fn evict_file_cache(paths: &[PathBuf]) -> Result<FileCacheEvictionObservation> {
    let mut unique = BTreeSet::new();
    let mut bytes = 0_u64;
    for path in paths {
        let path = fs::canonicalize(path)
            .map_err(|source| crate::snapshot::io_error("resolve", path, source))?;
        if !unique.insert(path.clone()) {
            continue;
        }
        let file = fs::File::open(&path)
            .map_err(|source| crate::snapshot::io_error("open", &path, source))?;
        let metadata = file
            .metadata()
            .map_err(|source| crate::snapshot::io_error("read metadata for", &path, source))?;
        if !metadata.is_file() {
            return Err(Error::Invariant(format!(
                "cache-eviction input is not a regular file: `{}`",
                path.display()
            )));
        }
        bytes = bytes
            .checked_add(metadata.len())
            .ok_or_else(|| Error::Invariant("cache-eviction byte count overflowed".to_owned()))?;
        // POSIX_FADV_DONTNEED only changes reclaimable kernel cache state. It
        // does not write or truncate the immutable input file.
        let result =
            unsafe { libc::posix_fadvise(file.as_raw_fd(), 0, 0, libc::POSIX_FADV_DONTNEED) };
        if result != 0 {
            return Err(Error::Io {
                operation: "evict page cache for",
                path,
                source: io::Error::from_raw_os_error(result),
            });
        }
    }
    Ok(FileCacheEvictionObservation {
        files: unique.len(),
        bytes,
    })
}

/// Measure resident file-backed pages directly through `mincore(2)` so the
/// guarded image does not depend on a separate host utility.
pub fn resident_file_cache(paths: &[PathBuf]) -> Result<FileCacheResidencyObservation> {
    let page_size = unsafe { libc::sysconf(libc::_SC_PAGESIZE) };
    if page_size <= 0 {
        return Err(Error::Io {
            operation: "read page size for",
            path: PathBuf::from("<host>"),
            source: io::Error::last_os_error(),
        });
    }
    let page_size = u64::try_from(page_size)
        .map_err(|_| Error::Invariant("host page size is invalid".to_owned()))?;
    let mut unique = BTreeSet::new();
    let mut resident_bytes = 0_u64;
    for path in paths {
        let path = fs::canonicalize(path)
            .map_err(|source| crate::snapshot::io_error("resolve", path, source))?;
        if !unique.insert(path.clone()) {
            continue;
        }
        let file = fs::File::open(&path)
            .map_err(|source| crate::snapshot::io_error("open", &path, source))?;
        let length = file
            .metadata()
            .map_err(|source| crate::snapshot::io_error("read metadata for", &path, source))?
            .len();
        if length == 0 {
            continue;
        }
        let map_length = usize::try_from(length).map_err(|_| {
            Error::Invariant(format!(
                "cache-residency input is too large to map: `{}`",
                path.display()
            ))
        })?;
        let mapping = unsafe {
            libc::mmap(
                std::ptr::null_mut(),
                map_length,
                libc::PROT_NONE,
                libc::MAP_SHARED,
                file.as_raw_fd(),
                0,
            )
        };
        if mapping == libc::MAP_FAILED {
            return Err(Error::Io {
                operation: "map for cache-residency measurement",
                path,
                source: io::Error::last_os_error(),
            });
        }
        let page_count = length.div_ceil(page_size);
        let mut residency = vec![
            0_u8;
            usize::try_from(page_count).map_err(|_| {
                Error::Invariant("cache-residency page count exceeds address space".to_owned())
            })?
        ];
        let mincore_result = unsafe { libc::mincore(mapping, map_length, residency.as_mut_ptr()) };
        let mincore_error = (mincore_result != 0).then(io::Error::last_os_error);
        let unmap_result = unsafe { libc::munmap(mapping, map_length) };
        if let Some(source) = mincore_error {
            return Err(Error::Io {
                operation: "measure cache residency for",
                path,
                source,
            });
        }
        if unmap_result != 0 {
            return Err(Error::Io {
                operation: "unmap cache-residency measurement for",
                path,
                source: io::Error::last_os_error(),
            });
        }
        for (index, state) in residency.into_iter().enumerate() {
            if state & 1 == 0 {
                continue;
            }
            let start = u64::try_from(index)
                .ok()
                .and_then(|index| index.checked_mul(page_size))
                .ok_or_else(|| {
                    Error::Invariant("cache-residency byte offset overflowed".to_owned())
                })?;
            resident_bytes = resident_bytes
                .checked_add((length - start).min(page_size))
                .ok_or_else(|| {
                    Error::Invariant("cache-residency byte count overflowed".to_owned())
                })?;
        }
    }
    Ok(FileCacheResidencyObservation {
        files: unique.len(),
        bytes: resident_bytes,
    })
}

impl CombinedMemoryLimitObservation {
    pub const fn memory_max_bytes(self) -> u64 {
        self.memory_max_bytes
    }

    pub const fn memory_swap_max_bytes(self) -> u64 {
        self.memory_swap_max_bytes
    }
}

/// Refuse to begin when admitting the full run ceiling could consume memory
/// already represented by host swap or the operator-approved host reserve.
pub fn require_host_memory_admission(
    available_bytes: u64,
    swap_used_bytes: u64,
    reserve_bytes: u64,
    run_limit_bytes: u64,
) -> Result<HostMemoryAdmissionObservation> {
    if reserve_bytes == 0 || run_limit_bytes == 0 {
        return Err(Error::ExperimentState(
            "host memory reserve and run ceiling must be positive".to_owned(),
        ));
    }
    let required_bytes = run_limit_bytes
        .checked_add(swap_used_bytes)
        .and_then(|required| required.checked_add(reserve_bytes))
        .ok_or_else(|| Error::ExperimentState("host memory requirement overflowed".to_owned()))?;
    let headroom_bytes = available_bytes.checked_sub(required_bytes).ok_or_else(|| {
        Error::ExperimentState(format!(
            "host memory admission failed: {available_bytes} bytes available, {required_bytes} bytes required"
        ))
    })?;
    Ok(HostMemoryAdmissionObservation {
        available_bytes,
        swap_used_bytes,
        reserve_bytes,
        run_limit_bytes,
        headroom_bytes,
    })
}

/// Refuse to begin unless the current cgroup has the exact approved RAM cap
/// and cannot escape it through swap.
pub fn require_combined_memory_limit(
    cgroup_root: impl AsRef<Path>,
    expected_memory_max_bytes: u64,
) -> Result<CombinedMemoryLimitObservation> {
    if expected_memory_max_bytes == 0 {
        return Err(Error::ExperimentState(
            "capacity memory ceiling must be positive".to_owned(),
        ));
    }
    let cgroup_root = cgroup_root.as_ref();
    let read_limit = |name: &str| -> Result<u64> {
        let path = cgroup_root.join(name);
        let value = fs::read_to_string(&path)
            .map_err(|source| crate::snapshot::io_error("read", &path, source))?;
        let value = value.trim();
        if value == "max" {
            return Err(Error::ExperimentState(format!(
                "capacity cgroup `{name}` is unlimited"
            )));
        }
        value.parse::<u64>().map_err(|error| {
            Error::ExperimentState(format!(
                "capacity cgroup `{name}` is not a byte count: {error}"
            ))
        })
    };
    let memory_max_bytes = read_limit("memory.max")?;
    let memory_swap_max_bytes = read_limit("memory.swap.max")?;
    if memory_max_bytes != expected_memory_max_bytes {
        return Err(Error::ExperimentState(format!(
            "capacity cgroup memory limit is {memory_max_bytes} bytes; expected {expected_memory_max_bytes}"
        )));
    }
    if memory_swap_max_bytes != 0 {
        return Err(Error::ExperimentState(format!(
            "capacity cgroup allows {memory_swap_max_bytes} bytes of swap; expected zero"
        )));
    }
    Ok(CombinedMemoryLimitObservation {
        memory_max_bytes,
        memory_swap_max_bytes,
    })
}

/// Resolve this process's cgroup-v2 directory below the mounted hierarchy.
pub fn resolve_unified_cgroup_path(mount: &Path, process_cgroup: &str) -> Result<PathBuf> {
    let relative = process_cgroup
        .lines()
        .find_map(|line| line.strip_prefix("0::"))
        .ok_or_else(|| Error::ExperimentState("process has no unified cgroup entry".to_owned()))?;
    let relative = Path::new(relative);
    if !relative.is_absolute()
        || relative.components().any(|component| {
            !matches!(
                component,
                std::path::Component::RootDir | std::path::Component::Normal(_)
            )
        })
    {
        return Err(Error::ExperimentState(
            "process unified cgroup path is invalid".to_owned(),
        ));
    }
    Ok(mount.join(relative.strip_prefix("/").expect("absolute path has root")))
}

/// Actual production-state growth reached by one completed synthetic run.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct CapacityReachedCounts {
    rounds: usize,
    unique_source_queries: usize,
    encoded_source_queries: u64,
    matrix_passes: u64,
    logical_oracle_calls: usize,
    source_response_deliveries: usize,
    unique_source_candidate_records: usize,
    cached_vectors: usize,
    retained_attributions: usize,
    accepted_candidates: usize,
    eligible_presentations: usize,
    wrong_language_presentations: usize,
    unique_ratings: usize,
    new_rating_routes: usize,
    stored_rating_reuse_routes: usize,
    quota_audit_events: usize,
    shared_round_audit_events: usize,
}

impl CapacityReachedCounts {
    pub fn from_completed(
        completed: &CompletedAdaptiveLearning,
        seed_event_ids: &[crate::representation::EventId],
    ) -> Result<Self> {
        let mut source_candidate_counts = std::collections::BTreeMap::new();
        let mut vector_event_ids = seed_event_ids.iter().copied().collect::<BTreeSet<_>>();
        let mut retained_attributions = 0_usize;
        let mut accepted_candidates = 0_usize;
        let mut encoded_source_queries = 0_u64;
        let mut matrix_passes = 0_u64;
        let mut logical_oracle_calls = 0_usize;
        let mut source_response_deliveries = 0_usize;
        let mut account_attempt = |attempt: &CandidateOrderAttempt| -> Result<()> {
            logical_oracle_calls = logical_oracle_calls.checked_add(1).ok_or_else(|| {
                Error::Invariant("capacity logical-call count overflowed".to_owned())
            })?;
            source_response_deliveries = source_response_deliveries
                .checked_add(attempt.source_responses().len())
                .ok_or_else(|| {
                    Error::Invariant("capacity source-delivery count overflowed".to_owned())
                })?;
            encoded_source_queries = encoded_source_queries
                .checked_add(attempt.discovery_metrics().encoded_queries)
                .ok_or_else(|| {
                    Error::Invariant("capacity encoded-query count overflowed".to_owned())
                })?;
            matrix_passes = matrix_passes
                .checked_add(attempt.discovery_metrics().matrix_passes)
                .ok_or_else(|| {
                    Error::Invariant("capacity matrix-pass count overflowed".to_owned())
                })?;
            for source in attempt.source_responses() {
                match source_candidate_counts
                    .insert(source.source_event_id(), source.candidate_count())
                {
                    Some(previous) if previous != source.candidate_count() => {
                        return Err(Error::Invariant(format!(
                            "source {:?} changed candidate count from {previous} to {}",
                            source.source_event_id(),
                            source.candidate_count()
                        )));
                    }
                    _ => {}
                }
            }
            for candidate in attempt.candidates() {
                retained_attributions = retained_attributions
                    .checked_add(candidate.attributions().len())
                    .ok_or_else(|| {
                        Error::Invariant("capacity attribution count overflowed".to_owned())
                    })?;
                if candidate.exclusion_reasons().is_empty() {
                    vector_event_ids.insert(candidate.event_id());
                }
            }
            accepted_candidates = accepted_candidates
                .checked_add(attempt.accepted().len())
                .ok_or_else(|| {
                    Error::Invariant("capacity accepted-candidate count overflowed".to_owned())
                })?;
            Ok(())
        };
        for attempt in completed.failed_candidate_order_attempts() {
            account_attempt(attempt)?;
        }
        for round in completed.round_records() {
            account_attempt(round.compact_order().attempt())?;
            account_attempt(round.rbf_order().attempt())?;
        }
        if vector_event_ids.len() != completed.cached_vector_count() {
            return Err(Error::Invariant(format!(
                "reconstructed {} cached vectors but production retained {}",
                vector_event_ids.len(),
                completed.cached_vector_count()
            )));
        }

        for wave in completed.source_wave_records() {
            logical_oracle_calls = logical_oracle_calls.checked_add(1).ok_or_else(|| {
                Error::Invariant("capacity logical-call count overflowed".to_owned())
            })?;
            encoded_source_queries = encoded_source_queries
                .checked_add(wave.metrics().encoded_queries)
                .ok_or_else(|| {
                    Error::Invariant("capacity encoded-query count overflowed".to_owned())
                })?;
            matrix_passes = matrix_passes
                .checked_add(wave.metrics().matrix_passes)
                .ok_or_else(|| {
                    Error::Invariant("capacity matrix-pass count overflowed".to_owned())
                })?;
            source_response_deliveries = source_response_deliveries
                .checked_add(wave.source_event_ids().len())
                .ok_or_else(|| {
                    Error::Invariant("capacity source-delivery count overflowed".to_owned())
                })?;
        }
        let unique_sources = source_candidate_counts
            .keys()
            .copied()
            .collect::<BTreeSet<_>>();
        let unique_source_candidate_records = source_candidate_counts
            .values()
            .try_fold(0_usize, |total, count| total.checked_add(*count))
            .ok_or_else(|| {
                Error::Invariant("capacity source-candidate count overflowed".to_owned())
            })?;
        let new_rating_routes = completed
            .round_records()
            .iter()
            .map(|round| round.quota_metadata().new_rating_routes().len())
            .sum();
        let stored_rating_reuse_routes = completed
            .round_records()
            .iter()
            .map(|round| round.quota_metadata().stored_rating_reuse_routes().len())
            .sum();
        let quota_audit_events = completed
            .round_records()
            .iter()
            .map(|round| round.quota_metadata().audit().len())
            .sum();
        let shared_round_audit_events = completed
            .round_records()
            .iter()
            .map(|round| round.audit().len())
            .sum();

        Ok(Self {
            rounds: completed.round_records().len(),
            unique_source_queries: unique_sources.len(),
            encoded_source_queries,
            matrix_passes,
            logical_oracle_calls,
            source_response_deliveries,
            unique_source_candidate_records,
            cached_vectors: completed.cached_vector_count(),
            retained_attributions,
            accepted_candidates,
            eligible_presentations: completed.language_totals().eligible_presentations(),
            wrong_language_presentations: completed
                .language_totals()
                .wrong_language_presentations(),
            unique_ratings: completed.ratings().len(),
            new_rating_routes,
            stored_rating_reuse_routes,
            quota_audit_events,
            shared_round_audit_events,
        })
    }

    pub const fn rounds(self) -> usize {
        self.rounds
    }

    pub const fn unique_source_queries(self) -> usize {
        self.unique_source_queries
    }

    pub const fn encoded_source_queries(self) -> u64 {
        self.encoded_source_queries
    }

    pub const fn matrix_passes(self) -> u64 {
        self.matrix_passes
    }

    pub const fn logical_oracle_calls(self) -> usize {
        self.logical_oracle_calls
    }

    pub const fn source_response_deliveries(self) -> usize {
        self.source_response_deliveries
    }

    pub const fn unique_source_candidate_records(self) -> usize {
        self.unique_source_candidate_records
    }

    pub const fn cached_vectors(self) -> usize {
        self.cached_vectors
    }

    pub const fn retained_attributions(self) -> usize {
        self.retained_attributions
    }

    pub const fn accepted_candidates(self) -> usize {
        self.accepted_candidates
    }

    pub const fn eligible_presentations(self) -> usize {
        self.eligible_presentations
    }

    pub const fn wrong_language_presentations(self) -> usize {
        self.wrong_language_presentations
    }

    pub const fn unique_ratings(self) -> usize {
        self.unique_ratings
    }

    pub const fn new_rating_routes(self) -> usize {
        self.new_rating_routes
    }

    pub const fn stored_rating_reuse_routes(self) -> usize {
        self.stored_rating_reuse_routes
    }

    pub const fn quota_audit_events(self) -> usize {
        self.quota_audit_events
    }

    pub const fn shared_round_audit_events(self) -> usize {
        self.shared_round_audit_events
    }
}

/// CREC-89's audited upper bounds for the unchanged ten-round production path.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct CapacityMaxima {
    unique_source_queries: usize,
    encoded_source_queries: u64,
    matrix_passes: u64,
    logical_oracle_calls: usize,
    source_response_deliveries: usize,
    unique_source_candidate_records: usize,
    cached_vectors: usize,
    retained_attributions: usize,
    source_response_files: u64,
    logical_call_files: u64,
    vector_response_files: u64,
    total_cache_files: u64,
}

pub const fn audited_capacity_maxima() -> CapacityMaxima {
    CapacityMaxima {
        unique_source_queries: 365,
        encoded_source_queries: 365,
        matrix_passes: 10,
        logical_oracle_calls: 31,
        source_response_deliveries: 3_755,
        unique_source_candidate_records: 373_760,
        cached_vectors: 373_765,
        retained_attributions: 1_950_720,
        source_response_files: 365,
        logical_call_files: 31,
        vector_response_files: 20,
        total_cache_files: 416,
    }
}

impl CapacityMaxima {
    pub fn require_not_exceeded(
        self,
        reached: &CapacityReachedCounts,
        total_cache_files: u64,
        source_response_files: u64,
        logical_call_files: u64,
        vector_response_files: u64,
    ) -> Result<()> {
        let checks = [
            (
                "unique source queries",
                reached.unique_source_queries as u64,
                self.unique_source_queries as u64,
            ),
            (
                "encoded source queries",
                reached.encoded_source_queries,
                self.encoded_source_queries,
            ),
            ("matrix passes", reached.matrix_passes, self.matrix_passes),
            (
                "logical Oracle calls",
                reached.logical_oracle_calls as u64,
                self.logical_oracle_calls as u64,
            ),
            (
                "source response deliveries",
                reached.source_response_deliveries as u64,
                self.source_response_deliveries as u64,
            ),
            (
                "unique source candidate records",
                reached.unique_source_candidate_records as u64,
                self.unique_source_candidate_records as u64,
            ),
            (
                "cached vectors",
                reached.cached_vectors as u64,
                self.cached_vectors as u64,
            ),
            (
                "retained attributions",
                reached.retained_attributions as u64,
                self.retained_attributions as u64,
            ),
            (
                "source response files",
                source_response_files,
                self.source_response_files,
            ),
            (
                "logical call files",
                logical_call_files,
                self.logical_call_files,
            ),
            (
                "vector response files",
                vector_response_files,
                self.vector_response_files,
            ),
            (
                "total cache files",
                total_cache_files,
                self.total_cache_files,
            ),
        ];
        if let Some((label, actual, maximum)) = checks
            .into_iter()
            .find(|(_, actual, maximum)| actual > maximum)
        {
            return Err(Error::ExperimentState(format!(
                "capacity {label} reached {actual}; audited maximum is {maximum}"
            )));
        }
        Ok(())
    }
}

/// Counts proving what the synthetic evaluator did at the production boundary.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, serde::Deserialize, serde::Serialize)]
pub struct CapacityBoundaryObservation {
    unix_time_ns: u64,
    monotonic_elapsed_ns: u64,
    session_bytes: u64,
    cache_bytes: u64,
    cache_files: u64,
    process_read_bytes: u64,
    process_write_bytes: u64,
}

impl CapacityBoundaryObservation {
    pub const fn unix_time_ns(self) -> u64 {
        self.unix_time_ns
    }

    pub const fn monotonic_elapsed_ns(self) -> u64 {
        self.monotonic_elapsed_ns
    }

    pub const fn session_bytes(self) -> u64 {
        self.session_bytes
    }

    pub const fn cache_bytes(self) -> u64 {
        self.cache_bytes
    }

    pub const fn cache_files(self) -> u64 {
        self.cache_files
    }

    pub const fn process_read_bytes(self) -> u64 {
        self.process_read_bytes
    }

    pub const fn process_write_bytes(self) -> u64 {
        self.process_write_bytes
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Deserialize, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CapacityBoundaryKind {
    Preparing,
    Complete,
}

/// One append-only boundary record that survives a killed capacity process.
#[derive(Clone, Debug, Eq, PartialEq, serde::Deserialize, serde::Serialize)]
pub struct CapacityBoundaryLogEvent {
    invocation_id: String,
    kind: CapacityBoundaryKind,
    preparing_call: Option<usize>,
    observation: CapacityBoundaryObservation,
}

impl CapacityBoundaryLogEvent {
    pub fn invocation_id(&self) -> &str {
        &self.invocation_id
    }

    pub const fn kind(&self) -> CapacityBoundaryKind {
        self.kind
    }

    pub const fn preparing_call(&self) -> Option<usize> {
        self.preparing_call
    }

    pub const fn observation(&self) -> CapacityBoundaryObservation {
        self.observation
    }
}

pub fn capacity_boundary_log_path(session_path: impl AsRef<Path>) -> Result<PathBuf> {
    let session_path = session_path.as_ref();
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    Ok(session_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!(".{name}.capacity-boundaries.jsonl")))
}

#[derive(Clone, Debug, Default, Eq, PartialEq, serde::Serialize)]
pub struct CapacityStressEvaluatorObservation {
    preparing_calls: usize,
    rating_requests: usize,
    recovery_requests: usize,
    rest_requests: usize,
    completion_presentations: Option<usize>,
    preparing_boundaries: Vec<CapacityBoundaryObservation>,
    completion_boundary: Option<CapacityBoundaryObservation>,
}

impl CapacityStressEvaluatorObservation {
    pub const fn preparing_calls(&self) -> usize {
        self.preparing_calls
    }

    pub const fn rating_requests(&self) -> usize {
        self.rating_requests
    }

    pub const fn recovery_requests(&self) -> usize {
        self.recovery_requests
    }

    pub const fn rest_requests(&self) -> usize {
        self.rest_requests
    }

    pub const fn completion_presentations(&self) -> Option<usize> {
        self.completion_presentations
    }

    pub fn preparing_boundaries(&self) -> &[CapacityBoundaryObservation] {
        &self.preparing_boundaries
    }

    pub const fn completion_boundary(&self) -> Option<&CapacityBoundaryObservation> {
        self.completion_boundary.as_ref()
    }
}

/// A completed production run and the synthetic evaluator's independent counts.
pub struct CapacityStressRun {
    completed: Box<CompletedAdaptiveLearning>,
    observation: CapacityStressEvaluatorObservation,
}

impl CapacityStressRun {
    pub fn completed(&self) -> &CompletedAdaptiveLearning {
        &self.completed
    }

    pub const fn observation(&self) -> &CapacityStressEvaluatorObservation {
        &self.observation
    }

    pub fn into_completed(self) -> Box<CompletedAdaptiveLearning> {
        self.completed
    }
}

/// Run or resume all ten production learning rounds without making a quality claim.
///
/// Every newly presented note is marked language-eligible and receives rating 7.
/// This maximizes later positive-source growth for the candidates the two real
/// personalizers actually select.
pub fn run_capacity_stress<O>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
) -> Result<CapacityStressRun>
where
    O: CandidateOrderOracle,
{
    let mut evaluator = AllSevenCapacityEvaluator::new(&config.session_path)?;
    let outcome = run_adaptive_learning(config, oracle, &mut evaluator)?;
    let AdaptiveLearningRunnerOutcome::Complete(completed) = outcome else {
        return Err(Error::Invariant(
            "capacity evaluator unexpectedly paused the production runner".to_owned(),
        ));
    };
    let seed_event_ids = config
        .seeds
        .iter()
        .map(|seed| seed.event_id())
        .collect::<BTreeSet<_>>();
    let observation = evaluator.finish(&completed, &seed_event_ids)?;
    Ok(CapacityStressRun {
        completed,
        observation,
    })
}

struct AllSevenCapacityEvaluator {
    observation: CapacityStressEvaluatorObservation,
    presentation_numbers: BTreeSet<usize>,
    session_path: PathBuf,
    cache_path: PathBuf,
    boundary_log_path: PathBuf,
    invocation_id: String,
    started: Instant,
}

impl AllSevenCapacityEvaluator {
    fn new(session_path: &Path) -> Result<Self> {
        let name = session_path
            .file_name()
            .and_then(|name| name.to_str())
            .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
        let cache_path = session_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join(format!(".{name}.oracle-responses"));
        let boundary_log_path = capacity_boundary_log_path(session_path)?;
        let invocation_id = format!(
            "{}-{}",
            std::process::id(),
            unix_time_ns().map_err(|source| {
                crate::snapshot::io_error("read clock for", &boundary_log_path, source)
            })?
        );
        Ok(Self {
            observation: CapacityStressEvaluatorObservation::default(),
            presentation_numbers: BTreeSet::new(),
            session_path: session_path.to_owned(),
            cache_path,
            boundary_log_path,
            invocation_id,
            started: Instant::now(),
        })
    }

    fn finish(
        self,
        completed: &CompletedAdaptiveLearning,
        seed_event_ids: &BTreeSet<crate::representation::EventId>,
    ) -> Result<CapacityStressEvaluatorObservation> {
        let eligible = completed.language_totals().eligible_presentations();
        if completed.round_records().len() != 10
            || completed.language_totals().wrong_language_presentations() != 0
            || completed
                .ratings()
                .iter()
                .any(|(event_id, rating)| !seed_event_ids.contains(event_id) && rating.value() != 7)
            || self.observation.completion_presentations != Some(eligible)
            || self.presentation_numbers.len()
                != self.observation.rating_requests + self.observation.recovery_requests
        {
            return Err(Error::Invariant(
                "capacity evaluator did not complete ten rounds using only synthetic rating 7"
                    .to_owned(),
            ));
        }
        Ok(self.observation)
    }

    fn submission() -> EvaluatorSubmission {
        EvaluatorSubmission::new(EvaluatorDecision::Rating(7), false)
    }

    fn record_presentation(&mut self, presentation_number: usize) -> io::Result<()> {
        if !self.presentation_numbers.insert(presentation_number) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!("presentation {presentation_number} was requested twice"),
            ));
        }
        Ok(())
    }

    fn capture_boundary(&self) -> io::Result<CapacityBoundaryObservation> {
        let unix_time_ns = unix_time_ns()?;
        let monotonic_elapsed_ns = self
            .started
            .elapsed()
            .as_nanos()
            .try_into()
            .unwrap_or(u64::MAX);
        let session_bytes = match fs::metadata(&self.session_path) {
            Ok(metadata) => metadata.len(),
            Err(error) if error.kind() == io::ErrorKind::NotFound => 0,
            Err(error) => return Err(error),
        };
        let (cache_bytes, cache_files) = path_usage(&self.cache_path)?;
        let process_io = fs::read_to_string("/proc/self/io")?;
        let process_read_bytes = proc_io_value(&process_io, "read_bytes:")?;
        let process_write_bytes = proc_io_value(&process_io, "write_bytes:")?;
        Ok(CapacityBoundaryObservation {
            unix_time_ns,
            monotonic_elapsed_ns,
            session_bytes,
            cache_bytes,
            cache_files,
            process_read_bytes,
            process_write_bytes,
        })
    }

    fn append_boundary(
        &self,
        kind: CapacityBoundaryKind,
        preparing_call: Option<usize>,
        observation: CapacityBoundaryObservation,
    ) -> io::Result<()> {
        let event = CapacityBoundaryLogEvent {
            invocation_id: self.invocation_id.clone(),
            kind,
            preparing_call,
            observation,
        };
        let mut file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .mode(0o600)
            .open(&self.boundary_log_path)?;
        serde_json::to_writer(&mut file, &event).map_err(io::Error::other)?;
        file.write_all(b"\n")?;
        file.sync_data()
    }
}

impl EvaluatorUi for AllSevenCapacityEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.record_presentation(view.presentation_number())?;
        self.observation.rating_requests += 1;
        Ok(RatingOutcome::Submitted(Self::submission()))
    }

    fn recover(&mut self, view: RecoveryView) -> io::Result<RecoveryOutcome> {
        self.record_presentation(view.presentation_number())?;
        self.observation.recovery_requests += 1;
        Ok(RecoveryOutcome::Submitted(Self::submission()))
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        self.observation.rest_requests += 1;
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        self.observation.preparing_calls += 1;
        let boundary = self.capture_boundary()?;
        self.append_boundary(
            CapacityBoundaryKind::Preparing,
            Some(self.observation.preparing_calls),
            boundary,
        )?;
        self.observation.preparing_boundaries.push(boundary);
        Ok(())
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        if self.observation.completion_presentations.is_some() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "capacity completion was requested twice",
            ));
        }
        self.observation.completion_presentations = Some(view.presentations_stored());
        let boundary = self.capture_boundary()?;
        self.append_boundary(CapacityBoundaryKind::Complete, None, boundary)?;
        self.observation.completion_boundary = Some(boundary);
        Ok(())
    }
}

fn path_usage(path: &Path) -> io::Result<(u64, u64)> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok((0, 0)),
        Err(error) => return Err(error),
    };
    if metadata.file_type().is_symlink() || metadata.is_file() {
        return Ok((metadata.len(), u64::from(metadata.is_file())));
    }
    if !metadata.is_dir() {
        return Ok((0, 0));
    }
    let mut bytes = 0_u64;
    let mut files = 0_u64;
    for entry in fs::read_dir(path)? {
        let (entry_bytes, entry_files) = path_usage(&entry?.path())?;
        bytes = bytes
            .checked_add(entry_bytes)
            .ok_or_else(|| io::Error::other("cache byte count overflowed"))?;
        files = files
            .checked_add(entry_files)
            .ok_or_else(|| io::Error::other("cache file count overflowed"))?;
    }
    Ok((bytes, files))
}

fn proc_io_value(contents: &str, key: &str) -> io::Result<u64> {
    contents
        .lines()
        .find_map(|line| {
            line.strip_prefix(key)
                .map(str::trim)
                .and_then(|value| value.parse().ok())
        })
        .ok_or_else(|| io::Error::other(format!("/proc/self/io has no `{key}` value")))
}

fn unix_time_ns() -> io::Result<u64> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(io::Error::other)?
        .as_nanos()
        .try_into()
        .map_err(|_| io::Error::other("wall-clock nanoseconds exceed u64"))
}
