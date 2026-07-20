//! Budget gates for the GTE calibration and the one admitted full-corpus build.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::artifact::{hash_bytes, hash_file};
use crate::budget::MicroUsd;
use crate::representation::{
    RepresentationArtifactPhase, RepresentationBatchShape, RepresentationBuildObserver,
    RepresentationShard, open_representation,
};
use crate::representation_batch_plan::{RepresentationBatchPlan, open_representation_batch_plan};
use crate::snapshot::{Error, Result, io_error};

const NANOS_PER_HOUR: u128 = 3_600_000_000_000;
const MICRO_USD_PER_CENT: u64 = 10_000;
const LEDGER_SCHEMA_VERSION: u32 = 2;
const LEDGER_SCOPE: &str = "Entire oracle MVP effort";
const CALIBRATION_EVIDENCE_SCHEMA_VERSION: u32 = 6;
const CALIBRATION_EVIDENCE_KIND: &str = "gte-calibration-evidence";
const CALIBRATION_EXECUTION_IDENTITY_SCHEMA_VERSION: u32 = 2;
const CALIBRATION_EXECUTION_IDENTITY_KIND: &str = "gte-calibration-execution-identity";
const APPROVED_GPU_MODEL: &str = "NVIDIA RTX PRO 6000 Blackwell Workstation Edition";
const APPROVED_PROVIDER: &str = "vast.ai";
const MIN_DRIVER_VERSION: [u32; 3] = [580, 95, 5];
const MIN_HOST_MEMORY_BYTES: u64 = 128 * 1_024 * 1_024 * 1_024;
const MIN_LOCAL_NVME_BYTES: u64 = 200_000_000_000;
const MIN_LOCAL_NVME_BANDWIDTH_BYTES_PER_SECOND: u64 = 1_000_000_000;
const MIN_RELIABILITY_MILLIONTHS: u32 = 995_000;
const REQUIRED_POWER_LIMIT_WATTS: u32 = 600;
const MIN_AVAILABLE_DURATION_SECONDS: u64 = 86_400;

/// Maximum cumulative charge authorized for all GTE calibration attempts.
pub const CALIBRATION_LIFETIME_CAP: MicroUsd = MicroUsd::from_dollars(25);

/// Maximum cumulative charge authorized for the entire oracle MVP effort.
pub const MVP_LIFETIME_CAP: MicroUsd = MicroUsd::from_dollars(500);

/// Budget state read from one exact version of `budget-ledger.json`.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BudgetLedger {
    pub ledger_sha256: String,
    pub lifetime_cap: MicroUsd,
    pub calibration_lifetime_cap: MicroUsd,
    pub actual_spend: MicroUsd,
    pub outstanding_commitments: MicroUsd,
    pub calibration_actual_spend: MicroUsd,
    pub calibration_outstanding_commitments: MicroUsd,
}

/// A decision reserving at most one more calibration charge.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CalibrationAdmission {
    pub reservation_id: String,
    pub previous_ledger_sha256: String,
    pub authorization_sha256: String,
    pub ledger_sha256: String,
    pub maximum_new_charge: MicroUsd,
    pub maximum_runtime_charge: MicroUsd,
    pub non_runtime_charge_reserve: MicroUsd,
    pub projected_calibration_total: MicroUsd,
    pub projected_lifetime_total: MicroUsd,
    pub remaining_calibration_budget: MicroUsd,
    pub remaining_lifetime_budget: MicroUsd,
}

/// One active calibration reservation and the exact runtime allowance derived
/// from its total provider cap.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ActiveCalibrationReservation {
    pub binding: CalibrationReservationBinding,
    pub maximum_total_charge: MicroUsd,
    pub maximum_runtime_charge: MicroUsd,
    pub non_runtime_charge_reserve: MicroUsd,
}

/// The one ledger transition that permits a production calibration command to
/// start its worker.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CalibrationExecutionClaim {
    pub reservation: ActiveCalibrationReservation,
    pub claim_authorization_sha256: String,
    pub ledger_sha256: String,
}

/// Exact ledger decision that one calibration evidence artifact must name.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CalibrationReservationBinding {
    pub reservation_id: String,
    pub previous_ledger_sha256: String,
    pub authorization_sha256: String,
    pub maximum_charge: MicroUsd,
}

impl CalibrationAdmission {
    pub fn evidence_binding(&self) -> CalibrationReservationBinding {
        CalibrationReservationBinding {
            reservation_id: self.reservation_id.clone(),
            previous_ledger_sha256: self.previous_ledger_sha256.clone(),
            authorization_sha256: self.authorization_sha256.clone(),
            maximum_charge: self.maximum_new_charge,
        }
    }
}

/// Costs that must all be reserved before the full-corpus build may begin.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildCostProjection {
    remaining_compute: MicroUsd,
    artifact_storage_and_transfer: MicroUsd,
    paid_lazy_inference: MicroUsd,
    one_cold_restart: MicroUsd,
    one_lost_shard: MicroUsd,
}

impl FullBuildCostProjection {
    pub fn remaining_compute(&self) -> MicroUsd {
        self.remaining_compute
    }

    pub fn artifact_storage_and_transfer(&self) -> MicroUsd {
        self.artifact_storage_and_transfer
    }

    pub fn paid_lazy_inference(&self) -> MicroUsd {
        self.paid_lazy_inference
    }

    pub fn one_cold_restart(&self) -> MicroUsd {
        self.one_cold_restart
    }

    pub fn one_lost_shard(&self) -> MicroUsd {
        self.one_lost_shard
    }
}

/// Additional full-build costs supplied outside the measured calibration path.
/// Restart and lost-shard values may only increase their measured reserves.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildNonComputeCosts {
    pub artifact_storage_and_transfer: MicroUsd,
    pub paid_lazy_inference: MicroUsd,
    pub one_cold_restart: MicroUsd,
    pub one_lost_shard: MicroUsd,
}

/// Artifacts needed to prove that calibration timings describe the exact
/// production plan and immutable calibrated shards. The representation root
/// may later publish additional shards under the same build identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CalibrationEvidencePaths {
    pub ordered_event_ids_path: PathBuf,
    pub token_audit_path: PathBuf,
    pub batch_plan_path: PathBuf,
    pub representation_path: PathBuf,
    pub execution_identity_path: PathBuf,
}

/// Immutable inputs used to verify the completed representation and the exact
/// rental identity before releasing its budget commitment.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildResultPaths {
    pub corpus_path: PathBuf,
    pub ordered_event_ids_path: PathBuf,
    pub representation_path: PathBuf,
    pub execution_identity_path: PathBuf,
}

/// Exact rented hardware, offer, rate, and representation runtime measured by
/// calibration. The representation descriptor hash binds the model, worker,
/// dependency locks, container, numeric format, and CUDA software identity.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CalibrationExecutionIdentity {
    pub schema_version: u32,
    pub artifact_kind: String,
    pub representation_descriptor_sha256: String,
    pub gpu_model: String,
    pub gpu_device_uuid: String,
    pub gpu_count: u32,
    pub gpu_power_limit_watts: u32,
    pub driver_version: String,
    pub machine_verified: bool,
    pub reliability_millionths: u32,
    pub host_cpu: String,
    pub host_memory_bytes: u64,
    pub local_nvme_bytes: u64,
    pub local_nvme_bandwidth_bytes_per_second: u64,
    pub on_demand: bool,
    pub available_duration_seconds: u64,
    pub rental_provider: String,
    pub rental_offer_id: String,
    pub rental_instance_id: String,
    pub rental_rate_per_hour: MicroUsd,
}

pub fn read_calibration_execution_identity(path: &Path) -> Result<CalibrationExecutionIdentity> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let identity = serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })?;
    validate_execution_identity(&identity)?;
    Ok(identity)
}

/// Prove from the immutable production plan that the selected real shards can
/// calibrate every approved token range before a reservation or model start.
pub fn validate_calibration_selection(
    ordered_event_ids_path: &Path,
    token_audit_path: &Path,
    batch_plan_path: &Path,
    shard_ordinals: &[u32],
    token_range_upper_bounds: &[u32],
) -> Result<()> {
    if shard_ordinals.is_empty() {
        return Err(Error::Budget(
            "calibration requires at least one production shard".to_owned(),
        ));
    }
    if token_range_upper_bounds.is_empty()
        || token_range_upper_bounds.contains(&0)
        || token_range_upper_bounds
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
    {
        return Err(Error::Budget(
            "calibration token-range ceilings must be positive and strictly increasing".to_owned(),
        ));
    }

    let plan =
        open_representation_batch_plan(ordered_event_ids_path, token_audit_path, batch_plan_path)?;
    let maximum_planned_tokens = plan
        .manifest()
        .batch_shapes
        .iter()
        .map(|shape| shape.padded_tokens_per_row)
        .max()
        .expect("verified batch plan has at least one shape");
    if token_range_upper_bounds.last().copied() != Some(maximum_planned_tokens) {
        return Err(Error::Budget(format!(
            "calibration token ranges must end at the plan maximum of {maximum_planned_tokens} tokens"
        )));
    }

    let selected = shard_ordinals.iter().copied().collect::<BTreeSet<_>>();
    if selected.len() != shard_ordinals.len() {
        return Err(Error::Budget(
            "calibration selection contains a duplicate shard ordinal".to_owned(),
        ));
    }

    let mut selected_shapes_by_range = vec![BTreeSet::new(); token_range_upper_bounds.len()];
    let mut selected_batches_by_range = vec![0_u64; token_range_upper_bounds.len()];
    let mut maximum_selected_shard_rows = 0_u64;
    for ordinal in selected {
        let batches = plan.shard_batches(ordinal)?;
        let shard_rows = batches.iter().try_fold(0_u64, |rows, batch| {
            rows.checked_add(batch.rows.len() as u64).ok_or_else(|| {
                Error::Budget("calibration selected-row count overflowed".to_owned())
            })
        })?;
        maximum_selected_shard_rows = maximum_selected_shard_rows.max(shard_rows);
        for batch in batches {
            let range = token_range_index(token_range_upper_bounds, batch.padded_tokens_per_row)?;
            let rows = u32::try_from(batch.rows.len()).map_err(|_| {
                Error::Budget("planned calibration batch rows do not fit u32".to_owned())
            })?;
            selected_shapes_by_range[range].insert((rows, batch.padded_tokens_per_row));
            selected_batches_by_range[range] = selected_batches_by_range[range]
                .checked_add(1)
                .ok_or_else(|| {
                    Error::Budget("calibration selected-batch count overflowed".to_owned())
                })?;
        }
    }

    let total_shards = plan
        .identity()
        .total_rows
        .div_ceil(plan.identity().shard_rows);
    let maximum_planned_shard_rows = if total_shards > 1 {
        plan.identity().shard_rows
    } else {
        plan.identity().total_rows
    };
    if maximum_selected_shard_rows < maximum_planned_shard_rows {
        return Err(Error::Budget(
            "calibration must measure a full-sized production shard".to_owned(),
        ));
    }

    let mut planned_batches_by_range = vec![0_u64; token_range_upper_bounds.len()];
    for shape in &plan.manifest().batch_shapes {
        let range = token_range_index(token_range_upper_bounds, shape.padded_tokens_per_row)?;
        planned_batches_by_range[range] = planned_batches_by_range[range]
            .checked_add(shape.batches)
            .ok_or_else(|| {
                Error::Budget("calibration planned-batch count overflowed".to_owned())
            })?;
        if selected_batches_by_range[range] < planned_batches_by_range[range]
            && !selected_shapes_by_range[range]
                .iter()
                .any(|&(rows, padded_tokens)| {
                    rows >= shape.rows_per_batch && padded_tokens >= shape.padded_tokens_per_row
                })
        {
            return Err(Error::Budget(format!(
                "calibration range ending at {} has no selected production batch that upper-bounds planned shape {}x{}",
                token_range_upper_bounds[range], shape.rows_per_batch, shape.padded_tokens_per_row,
            )));
        }
    }
    for (range, (&planned, &selected)) in planned_batches_by_range
        .iter()
        .zip(&selected_batches_by_range)
        .enumerate()
    {
        if planned > selected && selected < 2 {
            return Err(Error::Budget(format!(
                "calibration range ending at {} requires several selected production batches",
                token_range_upper_bounds[range]
            )));
        }
    }
    Ok(())
}

/// Fixed guard settings for one measured calibration process.
#[derive(Clone, Debug)]
pub struct CalibrationRecorderConfig {
    pub rental_started_at: Instant,
    pub rental_rate_per_hour: MicroUsd,
    pub maximum_charge: MicroUsd,
    pub maximum_work_unit: Duration,
    pub reservation: CalibrationReservationBinding,
}

/// Records the exact production build callbacks needed to publish calibration
/// evidence while stopping before another unit can exceed its reservation.
#[derive(Debug)]
pub struct CalibrationRecorder {
    rental_started_at: Instant,
    guard: MonotonicCostGuard,
    maximum_work_unit: Duration,
    reservation: CalibrationReservationBinding,
    cold_start_elapsed: Option<Duration>,
    batches: Vec<CalibrationBatchMeasurement>,
    shard_setups: Vec<CalibrationShardSetupMeasurement>,
    shard_checkpoints: Vec<CalibrationShardCheckpointMeasurement>,
    manifest_publication_elapsed: Option<Duration>,
    verification_elapsed: Option<Duration>,
}

impl CalibrationRecorder {
    pub fn new(config: CalibrationRecorderConfig) -> Result<Self> {
        if config.maximum_work_unit.is_zero() {
            return Err(Error::Budget(
                "calibration recorder requires a nonzero work-unit reserve".to_owned(),
            ));
        }
        validate_reservation_binding(&config.reservation)?;
        if config.maximum_charge > config.reservation.maximum_charge {
            return Err(Error::Budget(
                "calibration runtime cap exceeds the total provider reservation".to_owned(),
            ));
        }
        let guard = MonotonicCostGuard::new(
            config.rental_started_at,
            config.rental_rate_per_hour,
            config.maximum_charge,
        )?;
        Ok(Self {
            rental_started_at: config.rental_started_at,
            guard,
            maximum_work_unit: config.maximum_work_unit,
            reservation: config.reservation,
            cold_start_elapsed: None,
            batches: Vec::new(),
            shard_setups: Vec::new(),
            shard_checkpoints: Vec::new(),
            manifest_publication_elapsed: None,
            verification_elapsed: None,
        })
    }

    pub fn check_startup(&self) -> Result<()> {
        self.guard.check_with_reserve(self.maximum_work_unit)?;
        Ok(())
    }

    /// Atomically publish measurements, then reopen them through the same
    /// fail-closed verifier used by the full-build budget gate.
    pub fn publish(
        self,
        evidence_path: &Path,
        paths: &CalibrationEvidencePaths,
        token_range_upper_bounds: Vec<u32>,
    ) -> Result<VerifiedCalibrationEvidence> {
        self.guard.check_with_reserve(self.maximum_work_unit)?;
        let cold_start_elapsed = self.cold_start_elapsed.ok_or_else(|| {
            Error::Budget("calibration did not start a measured production batch".to_owned())
        })?;
        let manifest_publication_elapsed = self.manifest_publication_elapsed.ok_or_else(|| {
            Error::Budget("calibration did not measure manifest publication".to_owned())
        })?;
        let verification_elapsed = self.verification_elapsed.ok_or_else(|| {
            Error::Budget("calibration did not measure final verification".to_owned())
        })?;
        let finalization_elapsed = manifest_publication_elapsed
            .checked_add(verification_elapsed)
            .ok_or_else(|| Error::Budget("calibration finalization time overflowed".to_owned()))?;
        let reopen_started = Instant::now();
        let representation =
            open_representation(&paths.ordered_event_ids_path, &paths.representation_path)?;
        self.require_bounded_unit(reopen_started.elapsed())?;
        let calibration_shards = self
            .shard_checkpoints
            .iter()
            .map(|checkpoint| {
                representation
                    .manifest()
                    .shards
                    .iter()
                    .find(|shard| shard.ordinal == checkpoint.shard_ordinal)
                    .cloned()
                    .ok_or_else(|| {
                        Error::Budget(format!(
                            "calibration checkpoint belongs to unpublished shard {}",
                            checkpoint.shard_ordinal
                        ))
                    })
            })
            .collect::<Result<Vec<_>>>()?;
        let batch_plan_manifest = paths.batch_plan_path.join("manifest.json");
        let document = CalibrationEvidenceDocument {
            schema_version: CALIBRATION_EVIDENCE_SCHEMA_VERSION,
            artifact_kind: CALIBRATION_EVIDENCE_KIND.to_owned(),
            reservation_id: self.reservation.reservation_id.clone(),
            reservation_previous_ledger_sha256: self.reservation.previous_ledger_sha256.clone(),
            reservation_authorization_sha256: self.reservation.authorization_sha256.clone(),
            reservation_maximum_charge_micro_usd: self.reservation.maximum_charge.0,
            representation_build_identity_sha256: representation
                .manifest()
                .build_identity_sha256
                .clone(),
            calibration_shards,
            batch_plan_manifest_sha256: hash_file(&batch_plan_manifest)?,
            execution_identity_sha256: hash_file(&paths.execution_identity_path)?,
            token_range_upper_bounds,
            cold_start_elapsed_nanoseconds: duration_nanoseconds(cold_start_elapsed)?,
            shard_setups: self.shard_setups.clone(),
            shard_checkpoints: self.shard_checkpoints.clone(),
            finalization_elapsed_nanoseconds: duration_nanoseconds(finalization_elapsed)?,
            batches: self.batches.clone(),
        };
        verify_calibration_evidence(&document)?;
        self.guard.check_with_reserve(self.maximum_work_unit)?;
        let evidence_publication_started = Instant::now();
        publish_calibration_evidence(evidence_path, &document)?;
        self.require_bounded_unit(evidence_publication_started.elapsed())?;
        self.guard.check_with_reserve(self.maximum_work_unit)?;
        let evidence_verification_started = Instant::now();
        let evidence = VerifiedCalibrationEvidence::open(evidence_path, paths)?;
        self.require_bounded_unit(evidence_verification_started.elapsed())?;
        Ok(evidence)
    }
}

impl RepresentationBuildObserver for CalibrationRecorder {
    fn check_continue(
        &mut self,
        _shard_ordinal: u32,
        _batch_ordinal: u32,
        _next: &RepresentationBatchShape,
    ) -> Result<()> {
        self.guard.check_with_reserve(self.maximum_work_unit)?;
        Ok(())
    }

    fn check_artifact_phase(
        &mut self,
        phase: RepresentationArtifactPhase,
        _shard_ordinal: Option<u32>,
    ) -> Result<()> {
        if phase == RepresentationArtifactPhase::ShardSetup && self.cold_start_elapsed.is_none() {
            let elapsed = self.rental_started_at.elapsed();
            self.require_bounded_unit(elapsed)?;
            self.cold_start_elapsed = Some(elapsed);
        }
        if phase != RepresentationArtifactPhase::Write {
            self.guard.check_with_reserve(self.maximum_work_unit)?;
        }
        Ok(())
    }

    fn completed_batch(
        &mut self,
        shard_ordinal: u32,
        batch_ordinal: u32,
        _shape: &RepresentationBatchShape,
        elapsed: Duration,
    ) -> Result<()> {
        self.require_bounded_unit(elapsed)?;
        self.batches.push(CalibrationBatchMeasurement {
            shard_ordinal,
            batch_ordinal,
            end_to_end_elapsed_nanoseconds: duration_nanoseconds(elapsed)?,
        });
        Ok(())
    }

    fn artifact_phase(
        &mut self,
        phase: RepresentationArtifactPhase,
        shard_ordinal: Option<u32>,
        elapsed: Duration,
    ) -> Result<()> {
        if phase == RepresentationArtifactPhase::Write {
            return Ok(());
        }
        self.require_bounded_unit(elapsed)?;
        match phase {
            RepresentationArtifactPhase::Write => unreachable!(),
            RepresentationArtifactPhase::ShardSetup => {
                let shard_ordinal = shard_ordinal.ok_or_else(|| {
                    Error::Budget("shard setup measurement has no shard ordinal".to_owned())
                })?;
                self.shard_setups.push(CalibrationShardSetupMeasurement {
                    shard_ordinal,
                    elapsed_nanoseconds: duration_nanoseconds(elapsed)?,
                });
            }
            RepresentationArtifactPhase::Checkpoint => {
                let shard_ordinal = shard_ordinal.ok_or_else(|| {
                    Error::Budget("checkpoint measurement has no shard ordinal".to_owned())
                })?;
                self.shard_checkpoints
                    .push(CalibrationShardCheckpointMeasurement {
                        shard_ordinal,
                        elapsed_nanoseconds: duration_nanoseconds(elapsed)?,
                    });
            }
            RepresentationArtifactPhase::ManifestPublication => {
                set_once(
                    &mut self.manifest_publication_elapsed,
                    elapsed,
                    "manifest publication",
                )?;
            }
            RepresentationArtifactPhase::Verification => {
                set_once(
                    &mut self.verification_elapsed,
                    elapsed,
                    "final verification",
                )?;
            }
        }
        Ok(())
    }
}

impl CalibrationRecorder {
    fn require_bounded_unit(&self, elapsed: Duration) -> Result<()> {
        if elapsed > self.maximum_work_unit {
            return Err(Error::Budget(format!(
                "calibration work unit took {} ns, exceeding its reserved {} ns",
                elapsed.as_nanos(),
                self.maximum_work_unit.as_nanos(),
            )));
        }
        self.guard.check()?;
        Ok(())
    }
}

/// Verified measurements from the exact calibration build path.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedCalibrationEvidence {
    evidence_path: PathBuf,
    evidence_sha256: String,
    paths: CalibrationEvidencePaths,
    representation_build_identity_sha256: String,
    batch_plan_manifest_sha256: String,
    execution_identity_sha256: String,
    execution_identity: CalibrationExecutionIdentity,
    reservation: CalibrationReservationBinding,
    total_corpus_rows: u64,
    ranges: Vec<VerifiedTokenRangeMeasurement>,
    measured_batches: u64,
    measured_rows: u64,
    elapsed: Duration,
    remaining_elapsed_nanoseconds: u128,
    startup_elapsed_nanoseconds: u128,
    cold_restart_elapsed_nanoseconds: u128,
    lost_shard_elapsed_nanoseconds: u128,
}

impl VerifiedCalibrationEvidence {
    /// Open measurements and derive every shape and corpus count from the
    /// checksum-verified production batch plan. There is intentionally no
    /// constructor from caller-supplied shape or row counters.
    pub fn open(path: &Path, paths: &CalibrationEvidencePaths) -> Result<Self> {
        let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
        let document: CalibrationEvidenceDocument =
            serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: path.to_owned(),
                source,
            })?;
        verify_calibration_evidence(&document)?;

        let plan = open_representation_batch_plan(
            &paths.ordered_event_ids_path,
            &paths.token_audit_path,
            &paths.batch_plan_path,
        )?;
        verify_evidence_reference(
            "batch-plan manifest",
            &paths.batch_plan_path.join("manifest.json"),
            &document.batch_plan_manifest_sha256,
        )?;
        if plan.identity().manifest_sha256 != document.batch_plan_manifest_sha256 {
            return Err(Error::Budget(
                "calibration evidence does not match the verified production batch plan".to_owned(),
            ));
        }

        let representation =
            open_representation(&paths.ordered_event_ids_path, &paths.representation_path)?;
        if representation.manifest().batch_plan != *plan.identity() {
            return Err(Error::Budget(
                "calibration representation does not use the recorded production batch plan"
                    .to_owned(),
            ));
        }
        if representation.manifest().build_identity_sha256
            != document.representation_build_identity_sha256
        {
            return Err(Error::Budget(
                "calibration evidence does not match the immutable representation build identity"
                    .to_owned(),
            ));
        }

        let current_shards = representation
            .manifest()
            .shards
            .iter()
            .map(|shard| (shard.ordinal, shard))
            .collect::<BTreeMap<_, _>>();
        let mut calibration_shards = BTreeMap::new();
        for shard in &document.calibration_shards {
            if calibration_shards.insert(shard.ordinal, shard).is_some() {
                return Err(Error::Budget(
                    "calibration evidence contains a duplicate representation shard".to_owned(),
                ));
            }
            if current_shards.get(&shard.ordinal).copied() != Some(shard) {
                return Err(Error::Budget(format!(
                    "calibration representation shard {} changed or is missing",
                    shard.ordinal
                )));
            }
        }

        let execution_bytes = fs::read(&paths.execution_identity_path)
            .map_err(|source| io_error("read", &paths.execution_identity_path, source))?;
        if hash_bytes(&execution_bytes) != document.execution_identity_sha256 {
            return Err(Error::Budget(
                "calibration evidence execution identity changed or does not match its recorded SHA-256"
                    .to_owned(),
            ));
        }
        let execution_identity: CalibrationExecutionIdentity =
            serde_json::from_slice(&execution_bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: paths.execution_identity_path.clone(),
                source,
            })?;
        validate_execution_identity(&execution_identity)?;
        let reservation = CalibrationReservationBinding {
            reservation_id: document.reservation_id.clone(),
            previous_ledger_sha256: document.reservation_previous_ledger_sha256.clone(),
            authorization_sha256: document.reservation_authorization_sha256.clone(),
            maximum_charge: MicroUsd(document.reservation_maximum_charge_micro_usd),
        };
        validate_reservation_binding(&reservation)?;
        if execution_identity.representation_descriptor_sha256
            != representation.manifest().descriptor_sha256
            || !representation
                .manifest()
                .descriptor
                .execution_device
                .starts_with("cuda")
        {
            return Err(Error::Budget(
                "calibration execution identity does not match the CUDA representation runtime"
                    .to_owned(),
            ));
        }

        let completed_shards = calibration_shards.keys().copied().collect::<BTreeSet<_>>();
        let mut setup_shards = BTreeSet::new();
        let mut maximum_setup_elapsed_nanoseconds = 0_u64;
        let mut setup_elapsed = Duration::ZERO;
        for setup in &document.shard_setups {
            if setup.elapsed_nanoseconds == 0 {
                return Err(Error::Budget(
                    "calibration evidence contains a zero-duration shard setup".to_owned(),
                ));
            }
            if !completed_shards.contains(&setup.shard_ordinal) {
                return Err(Error::Budget(format!(
                    "calibration shard setup belongs to unpublished shard {}",
                    setup.shard_ordinal
                )));
            }
            if !setup_shards.insert(setup.shard_ordinal) {
                return Err(Error::Budget(
                    "calibration evidence contains a duplicate shard setup".to_owned(),
                ));
            }
            maximum_setup_elapsed_nanoseconds =
                maximum_setup_elapsed_nanoseconds.max(setup.elapsed_nanoseconds);
            setup_elapsed = setup_elapsed
                .checked_add(Duration::from_nanos(setup.elapsed_nanoseconds))
                .ok_or_else(|| {
                    Error::Budget("calibration shard setup time overflowed".to_owned())
                })?;
        }
        if setup_shards != completed_shards {
            return Err(Error::Budget(
                "calibration evidence must measure setup for every completed shard".to_owned(),
            ));
        }
        let mut checkpoint_shards = BTreeSet::new();
        let mut maximum_checkpoint_elapsed_nanoseconds = 0_u64;
        let mut checkpoint_elapsed = Duration::ZERO;
        for checkpoint in &document.shard_checkpoints {
            if checkpoint.elapsed_nanoseconds == 0 {
                return Err(Error::Budget(
                    "calibration evidence contains a zero-duration shard checkpoint".to_owned(),
                ));
            }
            if !completed_shards.contains(&checkpoint.shard_ordinal) {
                return Err(Error::Budget(format!(
                    "calibration checkpoint belongs to unpublished shard {}",
                    checkpoint.shard_ordinal
                )));
            }
            if !checkpoint_shards.insert(checkpoint.shard_ordinal) {
                return Err(Error::Budget(
                    "calibration evidence contains a duplicate shard checkpoint".to_owned(),
                ));
            }
            maximum_checkpoint_elapsed_nanoseconds =
                maximum_checkpoint_elapsed_nanoseconds.max(checkpoint.elapsed_nanoseconds);
            checkpoint_elapsed = checkpoint_elapsed
                .checked_add(Duration::from_nanos(checkpoint.elapsed_nanoseconds))
                .ok_or_else(|| {
                    Error::Budget("calibration checkpoint time overflowed".to_owned())
                })?;
        }
        if checkpoint_shards != completed_shards {
            return Err(Error::Budget(
                "calibration evidence must measure the checkpoint for every completed shard"
                    .to_owned(),
            ));
        }
        let mut addresses = BTreeSet::new();
        let mut batches_by_shard = BTreeMap::<u32, BTreeSet<u32>>::new();
        let mut measurements = BTreeMap::<(u32, u32), ShapeMeasurements>::new();
        let mut measured_rows = 0_u64;
        let mut elapsed = Duration::ZERO;
        for measured in &document.batches {
            if !addresses.insert((measured.shard_ordinal, measured.batch_ordinal)) {
                return Err(Error::Budget(
                    "calibration evidence contains a duplicate production batch address".to_owned(),
                ));
            }
            if !completed_shards.contains(&measured.shard_ordinal) {
                return Err(Error::Budget(format!(
                    "calibration batch belongs to unpublished shard {}",
                    measured.shard_ordinal
                )));
            }
            let planned = plan.shard_batches(measured.shard_ordinal)?;
            let batch_index = usize::try_from(measured.batch_ordinal).map_err(|_| {
                Error::Budget("calibration batch ordinal does not fit usize".to_owned())
            })?;
            let batch = planned.get(batch_index).ok_or_else(|| {
                Error::Budget(format!(
                    "calibration batch address ({}, {}) is outside the production plan",
                    measured.shard_ordinal, measured.batch_ordinal
                ))
            })?;
            let rows = u32::try_from(batch.rows.len()).map_err(|_| {
                Error::Budget("planned calibration batch rows do not fit u32".to_owned())
            })?;
            let shape = (rows, batch.padded_tokens_per_row);
            let entry = measurements.entry(shape).or_default();
            entry.measured_batches = entry.measured_batches.checked_add(1).ok_or_else(|| {
                Error::Budget("calibration measured-batch count overflowed".to_owned())
            })?;
            entry.maximum_elapsed_nanoseconds = entry
                .maximum_elapsed_nanoseconds
                .max(measured.end_to_end_elapsed_nanoseconds);
            measured_rows = measured_rows.checked_add(u64::from(rows)).ok_or_else(|| {
                Error::Budget("calibration measured-row count overflowed".to_owned())
            })?;
            elapsed = elapsed
                .checked_add(Duration::from_nanos(
                    measured.end_to_end_elapsed_nanoseconds,
                ))
                .ok_or_else(|| Error::Budget("calibration elapsed time overflowed".to_owned()))?;
            batches_by_shard
                .entry(measured.shard_ordinal)
                .or_default()
                .insert(measured.batch_ordinal);
        }

        for (shard_ordinal, observed) in &batches_by_shard {
            let planned = plan.shard_batches(*shard_ordinal)?;
            if observed.len() != planned.len()
                || !(0..u32::try_from(planned.len()).map_err(|_| {
                    Error::Budget("planned shard batch count does not fit u32".to_owned())
                })?)
                    .all(|batch_ordinal| observed.contains(&batch_ordinal))
            {
                return Err(Error::Budget(format!(
                    "calibration evidence must measure every batch in completed shard {shard_ordinal}"
                )));
            }
        }

        let maximum_planned_tokens = plan
            .manifest()
            .batch_shapes
            .iter()
            .map(|shape| shape.padded_tokens_per_row)
            .max()
            .expect("verified batch plan has at least one shape");
        if document.token_range_upper_bounds.last().copied() != Some(maximum_planned_tokens) {
            return Err(Error::Budget(format!(
                "calibration token ranges must end at the plan maximum of {maximum_planned_tokens} tokens"
            )));
        }

        let mut ranges = document
            .token_range_upper_bounds
            .iter()
            .copied()
            .map(|upper_bound| VerifiedTokenRangeMeasurement {
                upper_bound,
                planned_batches: 0,
                measured_batches: 0,
                maximum_elapsed_nanoseconds: 0,
            })
            .collect::<Vec<_>>();
        let mut measured_shapes_by_range = vec![BTreeSet::new(); ranges.len()];
        for (&(rows, padded_tokens), measured) in &measurements {
            let range = token_range_index(&document.token_range_upper_bounds, padded_tokens)?;
            ranges[range].measured_batches = ranges[range]
                .measured_batches
                .checked_add(measured.measured_batches)
                .ok_or_else(|| {
                    Error::Budget("calibration range measured-batch count overflowed".to_owned())
                })?;
            ranges[range].maximum_elapsed_nanoseconds = ranges[range]
                .maximum_elapsed_nanoseconds
                .max(measured.maximum_elapsed_nanoseconds);
            measured_shapes_by_range[range].insert((rows, padded_tokens));
        }

        for planned in &plan.manifest().batch_shapes {
            let range = token_range_index(
                &document.token_range_upper_bounds,
                planned.padded_tokens_per_row,
            )?;
            ranges[range].planned_batches = ranges[range]
                .planned_batches
                .checked_add(planned.batches)
                .ok_or_else(|| {
                    Error::Budget("calibration range planned-batch count overflowed".to_owned())
                })?;
            let measured_batches = measurements
                .get(&(planned.rows_per_batch, planned.padded_tokens_per_row))
                .map_or(0, |measurement| measurement.measured_batches);
            if measured_batches > planned.batches {
                return Err(Error::Budget(
                    "calibration measured more batches than the immutable plan contains".to_owned(),
                ));
            }
            let remaining_batches = planned.batches - measured_batches;
            if remaining_batches > 0
                && !measured_shapes_by_range[range]
                    .iter()
                    .any(|&(rows, padded_tokens)| {
                        rows >= planned.rows_per_batch
                            && padded_tokens >= planned.padded_tokens_per_row
                    })
            {
                return Err(Error::Budget(format!(
                    "calibration range ending at {} has no measured production batch that upper-bounds planned shape {}x{}",
                    ranges[range].upper_bound,
                    planned.rows_per_batch,
                    planned.padded_tokens_per_row,
                )));
            }
        }
        for range in &ranges {
            if range.planned_batches > range.measured_batches && range.measured_batches < 2 {
                return Err(Error::Budget(format!(
                    "calibration range ending at {} requires several measured production batches",
                    range.upper_bound
                )));
            }
        }

        let measured_batches = u64::try_from(addresses.len()).map_err(|_| {
            Error::Budget("calibration measured-batch count does not fit u64".to_owned())
        })?;

        let total_shards = plan
            .identity()
            .total_rows
            .div_ceil(plan.identity().shard_rows);
        let completed_shard_count = u64::try_from(completed_shards.len())
            .map_err(|_| Error::Budget("completed shard count does not fit u64".to_owned()))?;
        let remaining_shards = total_shards
            .checked_sub(completed_shard_count)
            .ok_or_else(|| Error::Budget("completed shard count exceeds the plan".to_owned()))?;
        let maximum_completed_shard_rows = calibration_shards
            .values()
            .map(|shard| shard.rows)
            .max()
            .expect("verified calibration has at least one completed shard");
        let mut maximum_remaining_shard_rows = 0_u64;
        for ordinal in 0..total_shards {
            let ordinal = u32::try_from(ordinal)
                .map_err(|_| Error::Budget("planned shard ordinal does not fit u32".to_owned()))?;
            if completed_shards.contains(&ordinal) {
                continue;
            }
            let start_row = u64::from(ordinal)
                .checked_mul(plan.identity().shard_rows)
                .ok_or_else(|| Error::Budget("planned shard start overflowed".to_owned()))?;
            maximum_remaining_shard_rows = maximum_remaining_shard_rows.max(
                plan.identity()
                    .shard_rows
                    .min(plan.identity().total_rows - start_row),
            );
        }
        if maximum_completed_shard_rows < maximum_remaining_shard_rows {
            return Err(Error::Budget(
                "calibration checkpoint does not cover a full-sized remaining shard".to_owned(),
            ));
        }
        let remaining_batch_elapsed_nanoseconds =
            projected_remaining_batch_elapsed_nanoseconds(&ranges)?;
        if remaining_batch_elapsed_nanoseconds == 0 {
            return Err(Error::Budget(
                "calibration evidence leaves no remaining corpus build to reserve".to_owned(),
            ));
        }
        let remaining_checkpoint_elapsed_nanoseconds =
            u128::from(maximum_checkpoint_elapsed_nanoseconds)
                .checked_mul(u128::from(remaining_shards))
                .ok_or_else(|| {
                    Error::Budget("full-build checkpoint projection overflowed".to_owned())
                })?;
        let remaining_setup_elapsed_nanoseconds = u128::from(maximum_setup_elapsed_nanoseconds)
            .checked_mul(u128::from(remaining_shards))
            .ok_or_else(|| {
                Error::Budget("full-build shard setup projection overflowed".to_owned())
            })?;
        let projected_finalization_elapsed_nanoseconds = div_ceil(
            u128::from(document.finalization_elapsed_nanoseconds)
                .checked_mul(u128::from(plan.identity().total_rows))
                .ok_or_else(|| {
                    Error::Budget("full-build finalization projection overflowed".to_owned())
                })?,
            u128::from(measured_rows),
        );
        let remaining_elapsed_nanoseconds = remaining_batch_elapsed_nanoseconds
            .checked_add(remaining_setup_elapsed_nanoseconds)
            .and_then(|elapsed| elapsed.checked_add(remaining_checkpoint_elapsed_nanoseconds))
            .and_then(|elapsed| elapsed.checked_add(projected_finalization_elapsed_nanoseconds))
            .ok_or_else(|| {
                Error::Budget("complete full-build elapsed-time projection overflowed".to_owned())
            })?;
        let lost_shard_elapsed_nanoseconds = projected_lost_shard_elapsed_nanoseconds(
            &plan,
            &ranges,
            maximum_setup_elapsed_nanoseconds,
            maximum_checkpoint_elapsed_nanoseconds,
        )?;
        elapsed = elapsed
            .checked_add(Duration::from_nanos(
                document.cold_start_elapsed_nanoseconds,
            ))
            .and_then(|elapsed| elapsed.checked_add(setup_elapsed))
            .and_then(|elapsed| elapsed.checked_add(checkpoint_elapsed))
            .and_then(|elapsed| {
                elapsed.checked_add(Duration::from_nanos(
                    document.finalization_elapsed_nanoseconds,
                ))
            })
            .ok_or_else(|| Error::Budget("calibration pipeline time overflowed".to_owned()))?;

        Ok(Self {
            evidence_path: path.to_owned(),
            evidence_sha256: hash_bytes(&bytes),
            paths: paths.clone(),
            representation_build_identity_sha256: document.representation_build_identity_sha256,
            batch_plan_manifest_sha256: document.batch_plan_manifest_sha256,
            execution_identity_sha256: document.execution_identity_sha256,
            execution_identity,
            reservation,
            total_corpus_rows: plan.identity().total_rows,
            ranges,
            measured_batches,
            measured_rows,
            elapsed,
            remaining_elapsed_nanoseconds,
            startup_elapsed_nanoseconds: u128::from(document.cold_start_elapsed_nanoseconds),
            cold_restart_elapsed_nanoseconds: u128::from(document.cold_start_elapsed_nanoseconds)
                .checked_add(projected_finalization_elapsed_nanoseconds)
                .ok_or_else(|| Error::Budget("cold-restart projection overflowed".to_owned()))?,
            lost_shard_elapsed_nanoseconds,
        })
    }

    pub fn evidence_sha256(&self) -> &str {
        &self.evidence_sha256
    }

    pub fn representation_build_identity_sha256(&self) -> &str {
        &self.representation_build_identity_sha256
    }

    pub fn batch_plan_manifest_sha256(&self) -> &str {
        &self.batch_plan_manifest_sha256
    }

    pub fn execution_identity_sha256(&self) -> &str {
        &self.execution_identity_sha256
    }

    pub fn total_corpus_rows(&self) -> u64 {
        self.total_corpus_rows
    }

    pub fn measured_batches(&self) -> u64 {
        self.measured_batches
    }

    pub fn measured_rows(&self) -> u64 {
        self.measured_rows
    }

    pub fn elapsed(&self) -> Duration {
        self.elapsed
    }

    fn reverify(&self) -> Result<()> {
        if hash_file(&self.evidence_path)? != self.evidence_sha256 {
            return Err(Error::Budget(
                "calibration evidence file changed after verification".to_owned(),
            ));
        }
        verify_evidence_reference(
            "batch-plan manifest",
            &self.paths.batch_plan_path.join("manifest.json"),
            &self.batch_plan_manifest_sha256,
        )?;
        verify_evidence_reference(
            "execution identity",
            &self.paths.execution_identity_path,
            &self.execution_identity_sha256,
        )?;
        let reopened = Self::open(&self.evidence_path, &self.paths)?;
        if reopened != *self {
            return Err(Error::Budget(
                "calibration evidence dependencies changed after verification".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
struct ShapeMeasurements {
    measured_batches: u64,
    maximum_elapsed_nanoseconds: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct VerifiedTokenRangeMeasurement {
    upper_bound: u32,
    planned_batches: u64,
    measured_batches: u64,
    maximum_elapsed_nanoseconds: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CalibrationBatchMeasurement {
    shard_ordinal: u32,
    batch_ordinal: u32,
    end_to_end_elapsed_nanoseconds: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CalibrationShardSetupMeasurement {
    shard_ordinal: u32,
    elapsed_nanoseconds: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CalibrationShardCheckpointMeasurement {
    shard_ordinal: u32,
    elapsed_nanoseconds: u64,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CalibrationEvidenceDocument {
    schema_version: u32,
    artifact_kind: String,
    reservation_id: String,
    reservation_previous_ledger_sha256: String,
    reservation_authorization_sha256: String,
    reservation_maximum_charge_micro_usd: u64,
    representation_build_identity_sha256: String,
    calibration_shards: Vec<RepresentationShard>,
    batch_plan_manifest_sha256: String,
    execution_identity_sha256: String,
    token_range_upper_bounds: Vec<u32>,
    cold_start_elapsed_nanoseconds: u64,
    shard_setups: Vec<CalibrationShardSetupMeasurement>,
    shard_checkpoints: Vec<CalibrationShardCheckpointMeasurement>,
    finalization_elapsed_nanoseconds: u64,
    batches: Vec<CalibrationBatchMeasurement>,
}

/// A decision reserving the complete remaining cost of one full-corpus build.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildAdmission {
    pub reservation_id: String,
    pub previous_ledger_sha256: String,
    pub authorization_sha256: String,
    pub ledger_sha256: String,
    pub calibration_evidence_sha256: String,
    pub projection: FullBuildCostProjection,
    pub projected_lifetime_total: MicroUsd,
    pub remaining_lifetime_budget: MicroUsd,
}

/// Exact ledger decision authorizing the one complete representation build.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildReservationBinding {
    pub reservation_id: String,
    pub previous_ledger_sha256: String,
    pub authorization_sha256: String,
    pub maximum_charge: MicroUsd,
}

/// The active complete-build reservation and its exact projected costs.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ActiveFullBuildReservation {
    pub binding: FullBuildReservationBinding,
    pub calibration_evidence_sha256: String,
    pub representation_build_identity_sha256: String,
    pub batch_plan_manifest_sha256: String,
    pub projection: FullBuildCostProjection,
}

/// The one execution identity allowed to continue the reserved complete build.
/// An exact retry on the same rental returns this claim without another ledger
/// mutation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildExecutionClaim {
    pub reservation: ActiveFullBuildReservation,
    pub execution_identity_sha256: String,
    pub control_binary_sha256: String,
    pub claim_authorization_sha256: String,
    pub ledger_sha256: String,
    pub resumed: bool,
}

/// Verified, read-only answer to whether the projected full build fits the
/// remaining lifetime budget.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullBuildProjectionReview {
    pub ledger_sha256: String,
    pub calibration_evidence_sha256: String,
    pub projection: FullBuildCostProjection,
    pub projected_lifetime_total: MicroUsd,
    pub remaining_lifetime_budget: MicroUsd,
}

/// One monotonic-time observation of a running rental.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CostObservation {
    pub elapsed: Duration,
    pub reserved_additional_elapsed: Duration,
    pub accrued_charge: MicroUsd,
    pub projected_charge: MicroUsd,
    pub remaining_charge: MicroUsd,
}

/// Stops a build observer from starting a measured unit whose worst-case
/// elapsed time would exceed its admitted rental charge.
#[derive(Clone, Debug)]
pub struct MonotonicCostGuard {
    started_at: Instant,
    rental_rate_per_hour: MicroUsd,
    maximum_charge: MicroUsd,
}

impl MonotonicCostGuard {
    pub fn new(
        started_at: Instant,
        rental_rate_per_hour: MicroUsd,
        maximum_charge: MicroUsd,
    ) -> Result<Self> {
        if rental_rate_per_hour.0 == 0 {
            return Err(Error::Budget(
                "elapsed-time cost guard requires a nonzero rental rate".to_owned(),
            ));
        }
        if maximum_charge.0 == 0 {
            return Err(Error::Budget(
                "elapsed-time cost guard requires a nonzero admitted charge".to_owned(),
            ));
        }
        Ok(Self {
            started_at,
            rental_rate_per_hour,
            maximum_charge,
        })
    }

    /// Check the accrued cost at the current monotonic instant.
    pub fn check(&self) -> Result<CostObservation> {
        self.check_at(Instant::now(), Duration::ZERO)
    }

    /// Check that the current rental can afford one more observed work unit.
    pub fn check_with_reserve(
        &self,
        maximum_additional_elapsed: Duration,
    ) -> Result<CostObservation> {
        self.check_at(Instant::now(), maximum_additional_elapsed)
    }

    /// Deterministic form used when an observer already captured its
    /// monotonic timestamp.
    pub fn check_at(
        &self,
        observed_at: Instant,
        maximum_additional_elapsed: Duration,
    ) -> Result<CostObservation> {
        let elapsed = observed_at
            .checked_duration_since(self.started_at)
            .ok_or_else(|| {
                Error::Budget(
                    "elapsed-time cost guard received a timestamp before the rental start"
                        .to_owned(),
                )
            })?;
        let projected_elapsed = elapsed
            .checked_add(maximum_additional_elapsed)
            .ok_or_else(|| Error::Budget("elapsed-time projection overflowed".to_owned()))?;
        let accrued_charge = rental_charge(elapsed, self.rental_rate_per_hour)?;
        let projected_charge = rental_charge(projected_elapsed, self.rental_rate_per_hour)?;
        if projected_charge > self.maximum_charge {
            return Err(Error::Budget(format!(
                "elapsed-time cost cap exceeded: projected {} micro-USD exceeds admitted {} micro-USD",
                projected_charge.0, self.maximum_charge.0
            )));
        }
        Ok(CostObservation {
            elapsed,
            reserved_additional_elapsed: maximum_additional_elapsed,
            accrued_charge,
            projected_charge,
            remaining_charge: MicroUsd(
                self.maximum_charge
                    .0
                    .checked_sub(projected_charge.0)
                    .expect("accepted projected charge is within the cap"),
            ),
        })
    }
}

/// Read and validate the exact ledger bytes used by a budget decision.
pub fn read_budget_ledger(path: &Path) -> Result<BudgetLedger> {
    let (bytes, document) = read_ledger_document(path)?;
    ledger_from_document(&document, hash_bytes(&bytes))
}

/// Atomically reserve one bounded calibration attempt in the ledger before it
/// can be executed. A crash after publication leaves the reservation in place;
/// a concurrent process cannot make another decision from the earlier state.
pub fn reserve_calibration(
    ledger_path: &Path,
    reservation_id: &str,
    maximum_new_charge: MicroUsd,
    recorded_at_utc: &str,
) -> Result<CalibrationAdmission> {
    reserve_calibration_with_non_runtime_reserve(
        ledger_path,
        reservation_id,
        maximum_new_charge,
        MicroUsd(0),
        recorded_at_utc,
    )
}

/// Atomically reserve the complete provider charge before rental creation.
/// Transfer, setup, teardown, and storage consume the non-runtime reserve; the
/// production runtime guard receives only the derived remainder.
pub fn reserve_calibration_with_non_runtime_reserve(
    ledger_path: &Path,
    reservation_id: &str,
    maximum_total_charge: MicroUsd,
    non_runtime_charge_reserve: MicroUsd,
    recorded_at_utc: &str,
) -> Result<CalibrationAdmission> {
    let maximum_runtime_charge =
        calibration_runtime_charge(maximum_total_charge, non_runtime_charge_reserve)?;
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    reject_existing_reservation(&document, reservation_id)?;
    let ledger = ledger_from_document(&document, hash_bytes(&previous_bytes))?;
    let reserved_cents = ceiling_cents(maximum_total_charge)?;
    let reserved_charge = cents(reserved_cents)?;
    let projected_calibration_total = checked_sum(&[
        ledger.calibration_actual_spend,
        ledger.calibration_outstanding_commitments,
        reserved_charge,
    ])?;
    if projected_calibration_total > CALIBRATION_LIFETIME_CAP {
        return Err(Error::Budget(format!(
            "projected calibration total {} micro-USD exceeds the cumulative $25 calibration cap",
            projected_calibration_total.0
        )));
    }

    let projected_lifetime_total = checked_sum(&[
        ledger.actual_spend,
        ledger.outstanding_commitments,
        reserved_charge,
    ])?;
    require_lifetime_cap(projected_lifetime_total)?;

    document.outstanding_commitments_cents = document
        .outstanding_commitments_cents
        .checked_add(reserved_cents)
        .ok_or_else(|| Error::Budget("lifetime commitment cents overflowed".to_owned()))?;
    document.calibration_outstanding_commitments_cents = document
        .calibration_outstanding_commitments_cents
        .checked_add(reserved_cents)
        .ok_or_else(|| Error::Budget("calibration commitment cents overflowed".to_owned()))?;
    let previous_ledger_sha256 = ledger.ledger_sha256.clone();
    let reservation_entry = json!({
        "kind": "calibration_reservation",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "requested_maximum_charge_micro_usd": maximum_total_charge.0,
        "non_runtime_charge_reserve_micro_usd": non_runtime_charge_reserve.0,
        "reserved_maximum_charge_cents": reserved_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    });
    let authorization_sha256 = calibration_authorization_sha256(&reservation_entry)?;
    document.entries.push(reservation_entry);
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;

    Ok(CalibrationAdmission {
        reservation_id: reservation_id.to_owned(),
        previous_ledger_sha256,
        authorization_sha256,
        ledger_sha256,
        maximum_new_charge: reserved_charge,
        maximum_runtime_charge,
        non_runtime_charge_reserve,
        projected_calibration_total,
        projected_lifetime_total,
        remaining_calibration_budget: subtract(
            CALIBRATION_LIFETIME_CAP,
            projected_calibration_total,
        ),
        remaining_lifetime_budget: subtract(MVP_LIFETIME_CAP, projected_lifetime_total),
    })
}

/// Read the reservation that already authorized a calibration command. This
/// never creates, settles, or otherwise changes budget state.
pub fn read_active_calibration_reservation(
    ledger_path: &Path,
    reservation_id: &str,
    expected_maximum_total_charge: MicroUsd,
    expected_non_runtime_charge_reserve: MicroUsd,
) -> Result<ActiveCalibrationReservation> {
    read_expected_calibration_reservation(
        ledger_path,
        reservation_id,
        expected_maximum_total_charge,
        expected_non_runtime_charge_reserve,
        false,
    )
}

/// Read the exact active reservation only when no paid execution has claimed it.
pub fn read_unclaimed_calibration_reservation(
    ledger_path: &Path,
    reservation_id: &str,
    expected_maximum_total_charge: MicroUsd,
    expected_non_runtime_charge_reserve: MicroUsd,
) -> Result<ActiveCalibrationReservation> {
    read_expected_calibration_reservation(
        ledger_path,
        reservation_id,
        expected_maximum_total_charge,
        expected_non_runtime_charge_reserve,
        true,
    )
}

fn read_expected_calibration_reservation(
    ledger_path: &Path,
    reservation_id: &str,
    expected_maximum_total_charge: MicroUsd,
    expected_non_runtime_charge_reserve: MicroUsd,
    reject_claimed: bool,
) -> Result<ActiveCalibrationReservation> {
    validate_reservation_input(reservation_id, "active-reservation")?;
    calibration_runtime_charge(
        expected_maximum_total_charge,
        expected_non_runtime_charge_reserve,
    )?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (bytes, document) = read_ledger_document(ledger_path)?;
    ledger_from_document(&document, hash_bytes(&bytes))?;
    let active = active_calibration_reservation(&document, reservation_id)?;
    if active.maximum_total_charge != expected_maximum_total_charge
        || active.non_runtime_charge_reserve != expected_non_runtime_charge_reserve
    {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` does not match the configured total and non-runtime charges"
        )));
    }
    if reject_claimed
        && document.entries.iter().any(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str)
                == Some("calibration_execution_claim")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
    {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` is already claimed for execution"
        )));
    }
    Ok(active)
}

/// Atomically consume one production reservation before the paid worker can
/// start. Validation may be retried, but the execution claim may not.
pub fn claim_calibration_execution(
    ledger_path: &Path,
    reservation_id: &str,
    expected_maximum_total_charge: MicroUsd,
    expected_non_runtime_charge_reserve: MicroUsd,
) -> Result<CalibrationExecutionClaim> {
    validate_reservation_input(reservation_id, "execution-claim")?;
    calibration_runtime_charge(
        expected_maximum_total_charge,
        expected_non_runtime_charge_reserve,
    )?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    ledger_from_document(&document, hash_bytes(&previous_bytes))?;
    let active = active_calibration_reservation(&document, reservation_id)?;
    if active.maximum_total_charge != expected_maximum_total_charge
        || active.non_runtime_charge_reserve != expected_non_runtime_charge_reserve
    {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` does not match the configured total and non-runtime charges"
        )));
    }
    if document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str) == Some("calibration_execution_claim")
            && entry
                .get("reservation_id")
                .and_then(serde_json::Value::as_str)
                == Some(reservation_id)
    }) {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` is already claimed for execution"
        )));
    }
    let claim_entry = json!({
        "kind": "calibration_execution_claim",
        "reservation_id": reservation_id,
        "reservation_authorization_sha256": active.binding.authorization_sha256.clone(),
        "previous_ledger_sha256": hash_bytes(&previous_bytes),
    });
    let claim_authorization_sha256 = calibration_authorization_sha256(&claim_entry)?;
    document.entries.push(claim_entry);
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    Ok(CalibrationExecutionClaim {
        reservation: active,
        claim_authorization_sha256,
        ledger_sha256,
    })
}

/// Atomically replace one completed calibration reservation with its actual
/// provider charge. The verified evidence is recorded in the same ledger
/// transition so an unmeasured or mutable run cannot unlock full-build review.
pub fn settle_calibration(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    actual_charge: MicroUsd,
    recorded_at_utc: &str,
) -> Result<BudgetLedger> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    calibration_evidence.reverify()?;
    if calibration_evidence.reservation.reservation_id != reservation_id {
        return Err(Error::Budget(format!(
            "calibration evidence is bound to reservation `{}` rather than `{reservation_id}`",
            calibration_evidence.reservation.reservation_id
        )));
    }
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    let active = active_calibration_reservation(&document, reservation_id)?;
    let reserved_cents = ceiling_cents(active.binding.maximum_charge)?;
    if active.binding != calibration_evidence.reservation {
        return Err(Error::Budget(
            "calibration evidence does not match the ledger authorization that paid for it"
                .to_owned(),
        ));
    }
    require_calibration_execution_claim(&document, &active)?;
    if document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str) == Some("calibration_settlement")
            && entry
                .get("calibration_evidence_sha256")
                .and_then(serde_json::Value::as_str)
                == Some(calibration_evidence.evidence_sha256())
    }) {
        return Err(Error::Budget(
            "calibration evidence is already bound to another settlement".to_owned(),
        ));
    }
    let actual_cents = ceiling_cents(actual_charge)?;
    let released_cents = apply_calibration_charge(
        &mut document,
        reserved_cents,
        actual_cents,
        recorded_at_utc,
        false,
    )?;
    let previous_ledger_sha256 = hash_bytes(&previous_bytes);
    document.entries.push(json!({
        "kind": "calibration_settlement",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "calibration_evidence_sha256": calibration_evidence.evidence_sha256,
        "representation_build_identity_sha256": calibration_evidence.representation_build_identity_sha256,
        "batch_plan_manifest_sha256": calibration_evidence.batch_plan_manifest_sha256,
        "execution_identity_sha256": calibration_evidence.execution_identity_sha256,
        "actual_charge_micro_usd": actual_charge.0,
        "recorded_actual_charge_cents": actual_cents,
        "released_commitment_cents": released_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    }));
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    ledger_from_document(&document, ledger_sha256)
}

/// Reconcile one successful calibration settlement against the provider's
/// finalized invoice. The caller pins the exact invoice bytes; the invoice is
/// also bound to the rental instance recorded in the verified calibration
/// evidence. This transition can only add the newly discovered rounded cents.
pub fn reconcile_calibration_finalized_charge(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    provider_invoice_path: &Path,
    expected_provider_invoice_sha256: &str,
    recorded_at_utc: &str,
) -> Result<BudgetLedger> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    calibration_evidence.reverify()?;
    if calibration_evidence.reservation.reservation_id != reservation_id {
        return Err(Error::Budget(format!(
            "calibration evidence is bound to reservation `{}` rather than `{reservation_id}`",
            calibration_evidence.reservation.reservation_id
        )));
    }
    if !is_sha256(expected_provider_invoice_sha256) {
        return Err(Error::Budget(
            "finalized provider invoice requires a lowercase SHA-256".to_owned(),
        ));
    }
    let provider_invoice_bytes = fs::read(provider_invoice_path)
        .map_err(|source| io_error("read", provider_invoice_path, source))?;
    let provider_invoice_sha256 = hash_bytes(&provider_invoice_bytes);
    if provider_invoice_sha256 != expected_provider_invoice_sha256 {
        return Err(Error::Budget(
            "finalized provider invoice does not match its expected SHA-256".to_owned(),
        ));
    }
    let provider_invoice: FinalizedProviderInvoiceDocument =
        serde_json::from_slice(&provider_invoice_bytes).map_err(|source| Error::Manifest {
            operation: "decode",
            path: provider_invoice_path.to_owned(),
            source,
        })?;
    let finalized_charge = provider_invoice
        .finalized_instance_charge(&calibration_evidence.execution_identity.rental_instance_id)?;
    let finalized_cents = ceiling_cents(finalized_charge)?;

    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    let previous_ledger_sha256 = hash_bytes(&previous_bytes);
    if document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str)
            == Some("calibration_finalized_charge_reconciliation")
            && entry
                .get("reservation_id")
                .and_then(serde_json::Value::as_str)
                == Some(reservation_id)
    }) {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` already reconciled its finalized provider charge"
        )));
    }

    let settlements = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str) == Some("calibration_settlement")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
        .collect::<Vec<_>>();
    let [settlement] = settlements.as_slice() else {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` requires exactly one successful settlement before finalized-charge reconciliation"
        )));
    };
    let settlement_bindings = [
        (
            "calibration_evidence_sha256",
            calibration_evidence.evidence_sha256(),
        ),
        (
            "representation_build_identity_sha256",
            calibration_evidence.representation_build_identity_sha256(),
        ),
        (
            "batch_plan_manifest_sha256",
            calibration_evidence.batch_plan_manifest_sha256(),
        ),
        (
            "execution_identity_sha256",
            calibration_evidence.execution_identity_sha256(),
        ),
    ];
    if settlement_bindings.iter().any(|(field, expected)| {
        settlement.get(field).and_then(serde_json::Value::as_str) != Some(*expected)
    }) {
        return Err(Error::Budget(
            "finalized provider invoice does not match the calibration settlement evidence"
                .to_owned(),
        ));
    }
    let previous_actual_charge = settlement
        .get("actual_charge_micro_usd")
        .and_then(serde_json::Value::as_u64)
        .map(MicroUsd)
        .ok_or_else(|| {
            Error::Budget("calibration settlement has no valid actual provider charge".to_owned())
        })?;
    let previous_cents = settlement
        .get("recorded_actual_charge_cents")
        .and_then(serde_json::Value::as_u64)
        .ok_or_else(|| {
            Error::Budget("calibration settlement has no valid rounded provider charge".to_owned())
        })?;
    if ceiling_cents(previous_actual_charge)? != previous_cents {
        return Err(Error::Budget(
            "calibration settlement does not conservatively round its provider charge".to_owned(),
        ));
    }
    if finalized_cents <= previous_cents {
        return Err(Error::Budget(
            "finalized provider charge must increase the previously recorded rounded charge"
                .to_owned(),
        ));
    }
    let added_cents = finalized_cents - previous_cents;
    let projected_calibration_actual_cents = document
        .calibration_actual_spend_cents
        .checked_add(added_cents)
        .ok_or_else(|| Error::Budget("calibration actual-spend cents overflowed".to_owned()))?;
    let projected_actual_cents = document
        .actual_spend_cents
        .checked_add(added_cents)
        .ok_or_else(|| Error::Budget("lifetime actual-spend cents overflowed".to_owned()))?;

    let settlement_sha256 =
        hash_bytes(
            &serde_json::to_vec(settlement).map_err(|source| Error::Manifest {
                operation: "encode",
                path: PathBuf::from("calibration-settlement"),
                source,
            })?,
        );
    document.actual_spend_cents = projected_actual_cents;
    document.calibration_actual_spend_cents = projected_calibration_actual_cents;
    document.reconciled_through_utc = recorded_at_utc.to_owned();
    document.entries.push(json!({
        "kind": "calibration_finalized_charge_reconciliation",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "calibration_evidence_sha256": calibration_evidence.evidence_sha256(),
        "calibration_settlement_sha256": settlement_sha256,
        "provider": APPROVED_PROVIDER,
        "provider_instance_id": calibration_evidence.execution_identity.rental_instance_id,
        "provider_invoice_sha256": provider_invoice_sha256,
        "previous_actual_charge_micro_usd": previous_actual_charge.0,
        "previous_recorded_charge_cents": previous_cents,
        "finalized_actual_charge_micro_usd": finalized_charge.0,
        "finalized_recorded_charge_cents": finalized_cents,
        "added_actual_spend_cents": added_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    }));
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    ledger_from_document(&document, ledger_sha256)
}

/// Reconcile a failed or interrupted calibration attempt against provider
/// evidence without making it eligible to unlock a full-corpus build.
pub fn settle_failed_calibration(
    ledger_path: &Path,
    reservation_id: &str,
    failure_evidence_path: &Path,
    actual_charge: MicroUsd,
    recorded_at_utc: &str,
) -> Result<BudgetLedger> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    let failure_evidence_sha256 = hash_file(failure_evidence_path)?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    let active = active_calibration_reservation(&document, reservation_id)?;
    let reserved_cents = ceiling_cents(active.binding.maximum_charge)?;
    let actual_cents = ceiling_cents(actual_charge)?;
    let released_cents = apply_calibration_charge(
        &mut document,
        reserved_cents,
        actual_cents,
        recorded_at_utc,
        true,
    )?;
    let previous_ledger_sha256 = hash_bytes(&previous_bytes);
    document.entries.push(json!({
        "kind": "failed_calibration_settlement",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "failure_evidence_sha256": failure_evidence_sha256,
        "actual_charge_micro_usd": actual_charge.0,
        "recorded_actual_charge_cents": actual_cents,
        "released_commitment_cents": released_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    }));
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    ledger_from_document(&document, ledger_sha256)
}

/// Derive the conservative full-corpus cost from verified calibration evidence
/// and current ledger state without creating a reservation.
pub fn project_full_build(
    ledger_path: &Path,
    calibration_evidence: &VerifiedCalibrationEvidence,
    non_compute_costs: FullBuildNonComputeCosts,
) -> Result<FullBuildProjectionReview> {
    calibration_evidence.reverify()?;
    let projection = derive_full_build_projection(calibration_evidence, non_compute_costs)?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (ledger_bytes, document) = read_ledger_document(ledger_path)?;
    if has_successful_full_build_settlement(&document) {
        return Err(Error::Budget(
            "the full build is already completed".to_owned(),
        ));
    }
    if has_active_full_build_reservation(&document) {
        return Err(Error::Budget(
            "an active full-build reservation already exists".to_owned(),
        ));
    }
    full_build_projection_review(
        &document,
        hash_bytes(&ledger_bytes),
        calibration_evidence,
        projection,
    )
}

/// Atomically reserve the full-corpus build. A terminal infrastructure failure
/// may be followed by another explicitly reviewed reservation, but a completed
/// representation permanently closes admission. Remaining compute is derived
/// from verified per-range measurements rather than supplied by the caller.
pub fn reserve_full_build(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    non_compute_costs: FullBuildNonComputeCosts,
    recorded_at_utc: &str,
) -> Result<FullBuildAdmission> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    calibration_evidence.reverify()?;
    let projection = derive_full_build_projection(calibration_evidence, non_compute_costs)?;

    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    let existing_full_build_reservation = document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str) == Some("full_build_reservation")
            && entry
                .get("reservation_id")
                .and_then(serde_json::Value::as_str)
                == Some(reservation_id)
    });
    if existing_full_build_reservation {
        let ledger_sha256 = hash_bytes(&previous_bytes);
        let active =
            active_full_build_reservation(&document, reservation_id, calibration_evidence)?;
        if active.projection != projection {
            return Err(Error::Budget(format!(
                "full-build reservation `{reservation_id}` already exists with a different projection"
            )));
        }
        let ledger = ledger_from_document(&document, ledger_sha256.clone())?;
        let projected_lifetime_total =
            checked_sum(&[ledger.actual_spend, ledger.outstanding_commitments])?;
        require_lifetime_cap(projected_lifetime_total)?;
        return Ok(FullBuildAdmission {
            reservation_id: reservation_id.to_owned(),
            previous_ledger_sha256: active.binding.previous_ledger_sha256,
            authorization_sha256: active.binding.authorization_sha256,
            ledger_sha256,
            calibration_evidence_sha256: active.calibration_evidence_sha256,
            projection: active.projection,
            projected_lifetime_total,
            remaining_lifetime_budget: subtract(MVP_LIFETIME_CAP, projected_lifetime_total),
        });
    }
    reject_existing_reservation(&document, reservation_id)?;
    if has_successful_full_build_settlement(&document) {
        return Err(Error::Budget(
            "the full build is already completed".to_owned(),
        ));
    }
    if has_active_full_build_reservation(&document) {
        return Err(Error::Budget(
            "an active full-build reservation already exists".to_owned(),
        ));
    }
    let review = full_build_projection_review(
        &document,
        hash_bytes(&previous_bytes),
        calibration_evidence,
        projection,
    )?;
    let reserved_cents = ceiling_cents(review.projection.total()?)?;

    document.outstanding_commitments_cents = document
        .outstanding_commitments_cents
        .checked_add(reserved_cents)
        .ok_or_else(|| Error::Budget("lifetime commitment cents overflowed".to_owned()))?;
    let previous_ledger_sha256 = review.ledger_sha256.clone();
    let reservation_entry = json!({
        "kind": "full_build_reservation",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "calibration_evidence_sha256": calibration_evidence.evidence_sha256,
        "representation_build_identity_sha256": calibration_evidence.representation_build_identity_sha256,
        "batch_plan_manifest_sha256": calibration_evidence.batch_plan_manifest_sha256,
        "execution_identity_sha256": calibration_evidence.execution_identity_sha256,
        "rental_rate_micro_usd_per_hour": calibration_evidence.execution_identity.rental_rate_per_hour.0,
        "remaining_compute_micro_usd": review.projection.remaining_compute.0,
        "artifact_storage_and_transfer_micro_usd": review.projection.artifact_storage_and_transfer.0,
        "paid_lazy_inference_micro_usd": review.projection.paid_lazy_inference.0,
        "one_cold_restart_micro_usd": review.projection.one_cold_restart.0,
        "one_lost_shard_micro_usd": review.projection.one_lost_shard.0,
        "reserved_maximum_charge_cents": reserved_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    });
    let authorization_sha256 = full_build_authorization_sha256(&reservation_entry)?;
    document.entries.push(reservation_entry);
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;

    Ok(FullBuildAdmission {
        reservation_id: reservation_id.to_owned(),
        previous_ledger_sha256,
        authorization_sha256,
        ledger_sha256,
        calibration_evidence_sha256: calibration_evidence.evidence_sha256.clone(),
        projection: review.projection,
        projected_lifetime_total: review.projected_lifetime_total,
        remaining_lifetime_budget: review.remaining_lifetime_budget,
    })
}

/// Read the exact active complete-build reservation without changing the
/// ledger. This is the local preflight used before a paid launch.
pub fn read_active_full_build_reservation(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
) -> Result<ActiveFullBuildReservation> {
    validate_reservation_input(reservation_id, "active-full-build-reservation")?;
    calibration_evidence.reverify()?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (bytes, document) = read_ledger_document(ledger_path)?;
    ledger_from_document(&document, hash_bytes(&bytes))?;
    active_full_build_reservation(&document, reservation_id, calibration_evidence)
}

/// Atomically bind the reserved complete build to one exact rental and one
/// checksum-pinned controller. Re-entering with the same identities is a
/// read-only resume; another rental or controller is rejected.
pub fn claim_or_resume_full_build_execution(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    expected_non_compute_costs: &FullBuildNonComputeCosts,
    execution_identity_path: &Path,
    control_binary_sha256: &str,
) -> Result<FullBuildExecutionClaim> {
    validate_reservation_input(reservation_id, "full-build-execution-claim")?;
    if !is_sha256(control_binary_sha256) {
        return Err(Error::Budget(
            "full-build control binary has an invalid SHA-256".to_owned(),
        ));
    }
    calibration_evidence.reverify()?;
    let expected_projection =
        derive_full_build_projection(calibration_evidence, expected_non_compute_costs.clone())?;
    let execution_identity = read_calibration_execution_identity(execution_identity_path)?;
    if execution_identity.representation_descriptor_sha256
        != calibration_evidence
            .execution_identity
            .representation_descriptor_sha256
        || execution_identity.rental_rate_per_hour
            > calibration_evidence.execution_identity.rental_rate_per_hour
    {
        return Err(Error::Budget(
            "full-build execution does not match the calibrated representation or maximum rental rate"
                .to_owned(),
        ));
    }
    let required_elapsed_nanoseconds = calibration_evidence
        .remaining_elapsed_nanoseconds
        .checked_add(calibration_evidence.startup_elapsed_nanoseconds)
        .and_then(|elapsed| {
            elapsed.checked_add(calibration_evidence.cold_restart_elapsed_nanoseconds)
        })
        .and_then(|elapsed| {
            elapsed.checked_add(calibration_evidence.lost_shard_elapsed_nanoseconds)
        })
        .ok_or_else(|| Error::Budget("full-build required duration overflowed".to_owned()))?;
    let required_elapsed_seconds = div_ceil(required_elapsed_nanoseconds, 1_000_000_000);
    if u128::from(execution_identity.available_duration_seconds) < required_elapsed_seconds {
        return Err(Error::Budget(
            "full-build offer duration does not cover the build and reserved recovery work"
                .to_owned(),
        ));
    }
    let execution_identity_sha256 = hash_file(execution_identity_path)?;

    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    let current_ledger_sha256 = hash_bytes(&previous_bytes);
    ledger_from_document(&document, current_ledger_sha256.clone())?;
    let active = active_full_build_reservation(&document, reservation_id, calibration_evidence)?;
    if active.projection != expected_projection {
        return Err(Error::Budget(
            "full-build reservation does not match the configured cost projection".to_owned(),
        ));
    }
    let claims = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str)
                == Some("full_build_execution_claim")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
        .collect::<Vec<_>>();
    if let [claim] = claims.as_slice() {
        if claim
            .get("reservation_authorization_sha256")
            .and_then(serde_json::Value::as_str)
            != Some(active.binding.authorization_sha256.as_str())
            || claim
                .get("execution_identity_sha256")
                .and_then(serde_json::Value::as_str)
                != Some(execution_identity_sha256.as_str())
            || claim
                .get("control_binary_sha256")
                .and_then(serde_json::Value::as_str)
                != Some(control_binary_sha256)
        {
            return Err(Error::Budget(
                "full-build reservation is already bound to a different execution".to_owned(),
            ));
        }
        return Ok(FullBuildExecutionClaim {
            reservation: active,
            execution_identity_sha256,
            control_binary_sha256: control_binary_sha256.to_owned(),
            claim_authorization_sha256: full_build_authorization_sha256(claim)?,
            ledger_sha256: current_ledger_sha256,
            resumed: true,
        });
    }
    if !claims.is_empty() {
        return Err(Error::Budget(
            "full-build reservation has duplicate execution claims".to_owned(),
        ));
    }

    let claim_entry = json!({
        "kind": "full_build_execution_claim",
        "reservation_id": reservation_id,
        "reservation_authorization_sha256": active.binding.authorization_sha256.clone(),
        "execution_identity_sha256": execution_identity_sha256,
        "rental_instance_id": execution_identity.rental_instance_id,
        "control_binary_sha256": control_binary_sha256,
        "previous_ledger_sha256": current_ledger_sha256,
    });
    let claim_authorization_sha256 = full_build_authorization_sha256(&claim_entry)?;
    document.entries.push(claim_entry);
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    Ok(FullBuildExecutionClaim {
        reservation: active,
        execution_identity_sha256,
        control_binary_sha256: control_binary_sha256.to_owned(),
        claim_authorization_sha256,
        ledger_sha256,
        resumed: false,
    })
}

/// Reconcile the one successful complete build only after deeply verifying the
/// final representation and the exact execution claim that produced it.
pub fn settle_full_build(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    paths: &FullBuildResultPaths,
    actual_charge: MicroUsd,
    recorded_at_utc: &str,
) -> Result<BudgetLedger> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    calibration_evidence.reverify()?;
    let execution_identity_sha256 = hash_file(&paths.execution_identity_path)?;
    read_calibration_execution_identity(&paths.execution_identity_path)?;
    let completed = crate::representation::verify_representation(
        &paths.corpus_path,
        &paths.ordered_event_ids_path,
        &paths.representation_path,
    )?;
    if !completed.manifest().complete {
        return Err(Error::Budget(
            "full-build representation is not complete".to_owned(),
        ));
    }

    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    ledger_from_document(&document, hash_bytes(&previous_bytes))?;
    let active = active_full_build_reservation(&document, reservation_id, calibration_evidence)?;
    if completed.manifest().build_identity_sha256 != active.representation_build_identity_sha256
        || completed.manifest().batch_plan.manifest_sha256 != active.batch_plan_manifest_sha256
    {
        return Err(Error::Budget(
            "completed representation does not match the reserved full build".to_owned(),
        ));
    }
    let claim = require_full_build_execution_claim(&document, &active)?;
    if claim
        .get("execution_identity_sha256")
        .and_then(serde_json::Value::as_str)
        != Some(execution_identity_sha256.as_str())
    {
        return Err(Error::Budget(
            "full-build execution identity changed after the claim".to_owned(),
        ));
    }
    let control_binary_sha256 = claim
        .get("control_binary_sha256")
        .and_then(serde_json::Value::as_str)
        .filter(|value| is_sha256(value))
        .ok_or_else(|| Error::Budget("full-build claim has no valid controller hash".to_owned()))?
        .to_owned();
    let reserved_cents = ceiling_cents(active.binding.maximum_charge)?;
    let actual_cents = ceiling_cents(actual_charge)?;
    let provider_overrun_cents = actual_cents.saturating_sub(reserved_cents);
    let released_cents = apply_full_build_charge(
        &mut document,
        reserved_cents,
        actual_cents,
        recorded_at_utc,
        true,
    )?;
    let previous_ledger_sha256 = hash_bytes(&previous_bytes);
    document.entries.push(json!({
        "kind": "full_build_settlement",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "calibration_evidence_sha256": calibration_evidence.evidence_sha256(),
        "representation_build_identity_sha256": completed.manifest().build_identity_sha256,
        "batch_plan_manifest_sha256": completed.manifest().batch_plan.manifest_sha256,
        "representation_version": completed.representation_version(),
        "completed_rows": completed.manifest().completed_rows,
        "execution_identity_sha256": execution_identity_sha256,
        "control_binary_sha256": control_binary_sha256,
        "actual_charge_micro_usd": actual_charge.0,
        "recorded_actual_charge_cents": actual_cents,
        "provider_overrun_cents": provider_overrun_cents,
        "released_commitment_cents": released_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    }));
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    ledger_from_document(&document, ledger_sha256)
}

/// Reconcile a failed or interrupted complete-build reservation against the
/// provider's actual charge. This attempt is terminal even when the provider
/// exceeded the reservation; a later attempt requires a new reviewed reservation.
pub fn settle_failed_full_build(
    ledger_path: &Path,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
    failure_evidence_path: &Path,
    actual_charge: MicroUsd,
    recorded_at_utc: &str,
) -> Result<BudgetLedger> {
    validate_reservation_input(reservation_id, recorded_at_utc)?;
    calibration_evidence.reverify()?;
    let failure_evidence_sha256 = hash_file(failure_evidence_path)?;
    let _lock = LedgerLock::acquire(ledger_path)?;
    let (previous_bytes, mut document) = read_ledger_document(ledger_path)?;
    ledger_from_document(&document, hash_bytes(&previous_bytes))?;
    let active = active_full_build_reservation(&document, reservation_id, calibration_evidence)?;
    let execution_claim_sha256 = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str)
                == Some("full_build_execution_claim")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
        .map(full_build_authorization_sha256)
        .collect::<Result<Vec<_>>>()?;
    if execution_claim_sha256.len() > 1 {
        return Err(Error::Budget(
            "full-build reservation has duplicate execution claims".to_owned(),
        ));
    }
    let reserved_cents = ceiling_cents(active.binding.maximum_charge)?;
    let actual_cents = ceiling_cents(actual_charge)?;
    let released_cents = apply_full_build_charge(
        &mut document,
        reserved_cents,
        actual_cents,
        recorded_at_utc,
        true,
    )?;
    let previous_ledger_sha256 = hash_bytes(&previous_bytes);
    document.entries.push(json!({
        "kind": "failed_full_build_settlement",
        "reservation_id": reservation_id,
        "recorded_at_utc": recorded_at_utc,
        "calibration_evidence_sha256": calibration_evidence.evidence_sha256(),
        "failure_evidence_sha256": failure_evidence_sha256,
        "execution_claim_sha256": execution_claim_sha256.first(),
        "actual_charge_micro_usd": actual_charge.0,
        "recorded_actual_charge_cents": actual_cents,
        "released_commitment_cents": released_cents,
        "previous_ledger_sha256": previous_ledger_sha256,
    }));
    let ledger_sha256 = publish_ledger_document(ledger_path, &document)?;
    ledger_from_document(&document, ledger_sha256)
}

impl FullBuildCostProjection {
    pub fn total(&self) -> Result<MicroUsd> {
        checked_sum(&[
            self.remaining_compute,
            self.artifact_storage_and_transfer,
            self.paid_lazy_inference,
            self.one_cold_restart,
            self.one_lost_shard,
        ])
    }
}

fn full_build_projection_review(
    document: &BudgetLedgerDocument,
    ledger_sha256: String,
    calibration_evidence: &VerifiedCalibrationEvidence,
    projection: FullBuildCostProjection,
) -> Result<FullBuildProjectionReview> {
    let calibration_is_settled = document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str) == Some("calibration_settlement")
            && entry
                .get("calibration_evidence_sha256")
                .and_then(serde_json::Value::as_str)
                == Some(calibration_evidence.evidence_sha256())
            && entry
                .get("representation_build_identity_sha256")
                .and_then(serde_json::Value::as_str)
                == Some(calibration_evidence.representation_build_identity_sha256())
            && entry
                .get("batch_plan_manifest_sha256")
                .and_then(serde_json::Value::as_str)
                == Some(calibration_evidence.batch_plan_manifest_sha256())
            && entry
                .get("execution_identity_sha256")
                .and_then(serde_json::Value::as_str)
                == Some(calibration_evidence.execution_identity_sha256())
    });
    if !calibration_is_settled {
        return Err(Error::Budget(
            "full-build projection requires this exact calibration evidence to be settled"
                .to_owned(),
        ));
    }
    let ledger = ledger_from_document(document, ledger_sha256)?;
    if ledger.calibration_outstanding_commitments.0 != 0 {
        return Err(Error::Budget(
            "full-build projection requires calibration commitments to be reconciled first"
                .to_owned(),
        ));
    }
    let reserved_charge = cents(ceiling_cents(projection.total()?)?)?;
    let projected_lifetime_total = checked_sum(&[
        ledger.actual_spend,
        ledger.outstanding_commitments,
        reserved_charge,
    ])?;
    require_lifetime_cap(projected_lifetime_total)?;
    Ok(FullBuildProjectionReview {
        ledger_sha256: ledger.ledger_sha256,
        calibration_evidence_sha256: calibration_evidence.evidence_sha256.clone(),
        projection,
        projected_lifetime_total,
        remaining_lifetime_budget: subtract(MVP_LIFETIME_CAP, projected_lifetime_total),
    })
}

fn derive_full_build_projection(
    evidence: &VerifiedCalibrationEvidence,
    costs: FullBuildNonComputeCosts,
) -> Result<FullBuildCostProjection> {
    let successful_build_elapsed_nanoseconds = evidence
        .remaining_elapsed_nanoseconds
        .checked_add(evidence.startup_elapsed_nanoseconds)
        .ok_or_else(|| Error::Budget("full-build startup time overflowed".to_owned()))?;
    let remaining_compute = rental_charge_nanoseconds(
        successful_build_elapsed_nanoseconds,
        evidence.execution_identity.rental_rate_per_hour,
    )?;
    let measured_cold_restart = rental_charge_nanoseconds(
        evidence.cold_restart_elapsed_nanoseconds,
        evidence.execution_identity.rental_rate_per_hour,
    )?;
    let measured_lost_shard = rental_charge_nanoseconds(
        evidence.lost_shard_elapsed_nanoseconds,
        evidence.execution_identity.rental_rate_per_hour,
    )?;
    let required_execution_nanoseconds = successful_build_elapsed_nanoseconds
        .checked_add(evidence.cold_restart_elapsed_nanoseconds)
        .and_then(|elapsed| elapsed.checked_add(evidence.lost_shard_elapsed_nanoseconds))
        .ok_or_else(|| Error::Budget("full-build execution duration overflowed".to_owned()))?;
    let available_nanoseconds = u128::from(evidence.execution_identity.available_duration_seconds)
        .checked_mul(1_000_000_000)
        .ok_or_else(|| Error::Budget("available rental duration overflowed".to_owned()))?;
    if required_execution_nanoseconds > available_nanoseconds {
        return Err(Error::Budget(
            "projected full build plus failure reserve exceeds the offer's available duration"
                .to_owned(),
        ));
    }
    Ok(FullBuildCostProjection {
        remaining_compute,
        artifact_storage_and_transfer: costs.artifact_storage_and_transfer,
        paid_lazy_inference: costs.paid_lazy_inference,
        one_cold_restart: measured_cold_restart.max(costs.one_cold_restart),
        one_lost_shard: measured_lost_shard.max(costs.one_lost_shard),
    })
}

fn projected_remaining_batch_elapsed_nanoseconds(
    ranges: &[VerifiedTokenRangeMeasurement],
) -> Result<u128> {
    ranges.iter().try_fold(0_u128, |total, range| {
        let remaining_batches = range
            .planned_batches
            .checked_sub(range.measured_batches)
            .expect("verified measured batches are within the range plan");
        let projected = u128::from(range.maximum_elapsed_nanoseconds)
            .checked_mul(u128::from(remaining_batches))
            .ok_or_else(|| {
                Error::Budget("full-build elapsed-time projection overflowed".to_owned())
            })?;
        total.checked_add(projected).ok_or_else(|| {
            Error::Budget("full-build elapsed-time projection overflowed".to_owned())
        })
    })
}

fn projected_lost_shard_elapsed_nanoseconds(
    plan: &RepresentationBatchPlan,
    ranges: &[VerifiedTokenRangeMeasurement],
    setup_elapsed_nanoseconds: u64,
    checkpoint_elapsed_nanoseconds: u64,
) -> Result<u128> {
    let shard_count = plan
        .identity()
        .total_rows
        .div_ceil(plan.identity().shard_rows);
    let mut maximum = 0_u128;
    for ordinal in 0..shard_count {
        let ordinal = u32::try_from(ordinal)
            .map_err(|_| Error::Budget("planned shard ordinal does not fit u32".to_owned()))?;
        let mut elapsed = u128::from(setup_elapsed_nanoseconds)
            .checked_add(u128::from(checkpoint_elapsed_nanoseconds))
            .ok_or_else(|| Error::Budget("lost-shard setup time overflowed".to_owned()))?;
        for batch in plan.shard_batches(ordinal)? {
            let range = ranges
                .iter()
                .find(|range| batch.padded_tokens_per_row <= range.upper_bound)
                .ok_or_else(|| {
                    Error::Budget("planned batch is outside calibrated token ranges".to_owned())
                })?;
            elapsed = elapsed
                .checked_add(u128::from(range.maximum_elapsed_nanoseconds))
                .ok_or_else(|| {
                    Error::Budget("lost-shard elapsed-time projection overflowed".to_owned())
                })?;
        }
        maximum = maximum.max(elapsed);
    }
    if maximum == 0 {
        return Err(Error::Budget(
            "calibration evidence cannot derive a lost-shard reserve".to_owned(),
        ));
    }
    Ok(maximum)
}

fn verify_calibration_evidence(document: &CalibrationEvidenceDocument) -> Result<()> {
    if document.schema_version != CALIBRATION_EVIDENCE_SCHEMA_VERSION
        || document.artifact_kind != CALIBRATION_EVIDENCE_KIND
        || document.reservation_id.is_empty()
        || !is_sha256(&document.reservation_previous_ledger_sha256)
        || !is_sha256(&document.reservation_authorization_sha256)
        || document.reservation_maximum_charge_micro_usd == 0
        || document.batches.is_empty()
        || document.shard_setups.is_empty()
        || document.shard_checkpoints.is_empty()
        || document.cold_start_elapsed_nanoseconds == 0
        || document.finalization_elapsed_nanoseconds == 0
        || document.token_range_upper_bounds.is_empty()
        || !is_sha256(&document.representation_build_identity_sha256)
        || document.calibration_shards.is_empty()
        || !is_sha256(&document.batch_plan_manifest_sha256)
        || !is_sha256(&document.execution_identity_sha256)
    {
        return Err(Error::Budget(
            "calibration evidence has an incompatible identity".to_owned(),
        ));
    }

    if document.token_range_upper_bounds.contains(&0)
        || document
            .token_range_upper_bounds
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
    {
        return Err(Error::Budget(
            "calibration token-range ceilings must be positive and strictly increasing".to_owned(),
        ));
    }
    for batch in &document.batches {
        if batch.end_to_end_elapsed_nanoseconds == 0 {
            return Err(Error::Budget(
                "calibration evidence contains a zero-duration production batch".to_owned(),
            ));
        }
    }
    Ok(())
}

fn publish_calibration_evidence(path: &Path, document: &CalibrationEvidenceDocument) -> Result<()> {
    if path.exists() {
        return Err(Error::Budget(format!(
            "calibration evidence already exists at `{}`",
            path.display()
        )));
    }
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let temporary = sibling_path(path, "next")?;
    if temporary.exists() {
        if !temporary.is_file() {
            return Err(Error::Budget(format!(
                "calibration evidence staging path `{}` is not a file",
                temporary.display()
            )));
        }
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    let mut bytes = serde_json::to_vec_pretty(document).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    bytes.push(b'\n');
    let mut output = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    output
        .write_all(&bytes)
        .and_then(|()| output.sync_all())
        .map_err(|source| io_error("write", &temporary, source))?;
    fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
    sync_parent(path)
}

fn duration_nanoseconds(duration: Duration) -> Result<u64> {
    let nanoseconds = u64::try_from(duration.as_nanos())
        .map_err(|_| Error::Budget("measured duration does not fit u64 nanoseconds".to_owned()))?;
    if nanoseconds == 0 {
        return Err(Error::Budget(
            "calibration contains an unmeasurable zero-duration phase".to_owned(),
        ));
    }
    Ok(nanoseconds)
}

fn set_once(destination: &mut Option<Duration>, elapsed: Duration, name: &str) -> Result<()> {
    if destination.replace(elapsed).is_some() {
        return Err(Error::Budget(format!(
            "calibration measured {name} more than once"
        )));
    }
    Ok(())
}

fn validate_execution_identity(identity: &CalibrationExecutionIdentity) -> Result<()> {
    let required = [
        identity.artifact_kind.as_str(),
        identity.gpu_model.as_str(),
        identity.gpu_device_uuid.as_str(),
        identity.driver_version.as_str(),
        identity.host_cpu.as_str(),
        identity.rental_provider.as_str(),
        identity.rental_offer_id.as_str(),
        identity.rental_instance_id.as_str(),
    ];
    if identity.schema_version != CALIBRATION_EXECUTION_IDENTITY_SCHEMA_VERSION
        || identity.artifact_kind != CALIBRATION_EXECUTION_IDENTITY_KIND
        || !is_sha256(&identity.representation_descriptor_sha256)
        || identity.gpu_model != APPROVED_GPU_MODEL
        || identity.gpu_count != 1
        || identity.gpu_power_limit_watts != REQUIRED_POWER_LIMIT_WATTS
        || !identity.machine_verified
        || identity.reliability_millionths < MIN_RELIABILITY_MILLIONTHS
        || identity.host_memory_bytes < MIN_HOST_MEMORY_BYTES
        || identity.local_nvme_bytes < MIN_LOCAL_NVME_BYTES
        || identity.local_nvme_bandwidth_bytes_per_second
            < MIN_LOCAL_NVME_BANDWIDTH_BYTES_PER_SECOND
        || !identity.on_demand
        || identity.available_duration_seconds < MIN_AVAILABLE_DURATION_SECONDS
        || identity.rental_provider != APPROVED_PROVIDER
        || !driver_at_least(&identity.driver_version, MIN_DRIVER_VERSION)
        || identity.rental_rate_per_hour.0 == 0
        || required.iter().any(|value| value.trim().is_empty())
    {
        return Err(Error::Budget(
            "calibration execution identity does not satisfy the approved hardware contract"
                .to_owned(),
        ));
    }
    Ok(())
}

fn driver_at_least(actual: &str, required: [u32; 3]) -> bool {
    let parsed = actual
        .split('.')
        .map(str::parse::<u32>)
        .collect::<std::result::Result<Vec<_>, _>>();
    let actual = match parsed.as_deref() {
        Ok([major, minor]) => [*major, *minor, 0],
        Ok([major, minor, patch]) => [*major, *minor, *patch],
        _ => return false,
    };
    actual >= required
}

fn token_range_index(upper_bounds: &[u32], padded_tokens_per_row: u32) -> Result<usize> {
    upper_bounds
        .iter()
        .position(|&upper_bound| padded_tokens_per_row <= upper_bound)
        .ok_or_else(|| {
            Error::Budget(format!(
                "planned batch length {padded_tokens_per_row} is outside the approved calibration ranges"
            ))
        })
}

fn verify_evidence_reference(name: &str, path: &Path, expected_sha256: &str) -> Result<()> {
    if hash_file(path)? != expected_sha256 {
        return Err(Error::Budget(format!(
            "calibration evidence {name} changed or does not match its recorded SHA-256"
        )));
    }
    Ok(())
}

fn read_ledger_document(path: &Path) -> Result<(Vec<u8>, BudgetLedgerDocument)> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let document: BudgetLedgerDocument =
        serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
            operation: "decode",
            path: path.to_path_buf(),
            source,
        })?;
    validate_ledger_document(&document)?;
    Ok((bytes, document))
}

fn ledger_from_document(
    document: &BudgetLedgerDocument,
    ledger_sha256: String,
) -> Result<BudgetLedger> {
    Ok(BudgetLedger {
        ledger_sha256,
        lifetime_cap: cents(document.lifetime_cap_cents)?,
        calibration_lifetime_cap: cents(document.calibration_lifetime_cap_cents)?,
        actual_spend: cents(document.actual_spend_cents)?,
        outstanding_commitments: cents(document.outstanding_commitments_cents)?,
        calibration_actual_spend: cents(document.calibration_actual_spend_cents)?,
        calibration_outstanding_commitments: cents(
            document.calibration_outstanding_commitments_cents,
        )?,
    })
}

fn publish_ledger_document(path: &Path, document: &BudgetLedgerDocument) -> Result<String> {
    validate_ledger_document(document)?;
    let mut bytes = serde_json::to_vec_pretty(document).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    bytes.push(b'\n');

    let temporary = sibling_path(path, "next")?;
    if temporary.exists() {
        if !temporary.is_file() {
            return Err(Error::Budget(format!(
                "ledger staging path `{}` is not a file",
                temporary.display()
            )));
        }
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    let mut output = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    output
        .write_all(&bytes)
        .and_then(|()| output.sync_all())
        .map_err(|source| io_error("write", &temporary, source))?;
    fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
    sync_parent(path)?;
    Ok(hash_bytes(&bytes))
}

fn validate_reservation_input(reservation_id: &str, recorded_at_utc: &str) -> Result<()> {
    if reservation_id.is_empty()
        || reservation_id.len() > 128
        || !reservation_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        return Err(Error::Budget(
            "reservation ID must be one nonempty safe identifier".to_owned(),
        ));
    }
    if recorded_at_utc.is_empty() {
        return Err(Error::Budget(
            "reservation has no recorded UTC timestamp".to_owned(),
        ));
    }
    Ok(())
}

fn validate_reservation_binding(binding: &CalibrationReservationBinding) -> Result<()> {
    validate_reservation_input(&binding.reservation_id, "evidence-binding")?;
    if !is_sha256(&binding.previous_ledger_sha256)
        || !is_sha256(&binding.authorization_sha256)
        || binding.maximum_charge.0 == 0
    {
        return Err(Error::Budget(
            "calibration evidence has an invalid reservation binding".to_owned(),
        ));
    }
    Ok(())
}

fn calibration_authorization_sha256(entry: &serde_json::Value) -> Result<String> {
    let bytes = serde_json::to_vec(entry).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("calibration-reservation"),
        source,
    })?;
    Ok(hash_bytes(&bytes))
}

fn full_build_authorization_sha256(entry: &serde_json::Value) -> Result<String> {
    let bytes = serde_json::to_vec(entry).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("full-build-authorization"),
        source,
    })?;
    Ok(hash_bytes(&bytes))
}

fn active_full_build_reservation(
    document: &BudgetLedgerDocument,
    reservation_id: &str,
    calibration_evidence: &VerifiedCalibrationEvidence,
) -> Result<ActiveFullBuildReservation> {
    if document.entries.iter().any(|entry| {
        matches!(
            entry.get("kind").and_then(serde_json::Value::as_str),
            Some("full_build_settlement" | "failed_full_build_settlement")
        ) && entry
            .get("reservation_id")
            .and_then(serde_json::Value::as_str)
            == Some(reservation_id)
    }) {
        return Err(Error::Budget(format!(
            "full-build reservation `{reservation_id}` is already settled"
        )));
    }
    let reservations = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str) == Some("full_build_reservation")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
        .collect::<Vec<_>>();
    let [reservation] = reservations.as_slice() else {
        if reservations.is_empty() {
            return Err(Error::Budget(format!(
                "full-build reservation `{reservation_id}` does not exist"
            )));
        }
        return Err(Error::Budget(format!(
            "full-build reservation `{reservation_id}` has duplicate authorization entries"
        )));
    };
    let expected_fields = [
        (
            "calibration_evidence_sha256",
            calibration_evidence.evidence_sha256(),
        ),
        (
            "representation_build_identity_sha256",
            calibration_evidence.representation_build_identity_sha256(),
        ),
        (
            "batch_plan_manifest_sha256",
            calibration_evidence.batch_plan_manifest_sha256(),
        ),
        (
            "execution_identity_sha256",
            calibration_evidence.execution_identity_sha256(),
        ),
    ];
    if expected_fields.iter().any(|(field, expected)| {
        reservation.get(field).and_then(serde_json::Value::as_str) != Some(*expected)
    }) {
        return Err(Error::Budget(
            "full-build reservation does not match the settled calibration evidence".to_owned(),
        ));
    }
    let read_charge = |field: &str| {
        reservation
            .get(field)
            .and_then(serde_json::Value::as_u64)
            .map(MicroUsd)
            .ok_or_else(|| {
                Error::Budget(format!(
                    "full-build reservation `{reservation_id}` has no valid {field}"
                ))
            })
    };
    let projection = FullBuildCostProjection {
        remaining_compute: read_charge("remaining_compute_micro_usd")?,
        artifact_storage_and_transfer: read_charge("artifact_storage_and_transfer_micro_usd")?,
        paid_lazy_inference: read_charge("paid_lazy_inference_micro_usd")?,
        one_cold_restart: read_charge("one_cold_restart_micro_usd")?,
        one_lost_shard: read_charge("one_lost_shard_micro_usd")?,
    };
    let reserved_cents = reservation
        .get("reserved_maximum_charge_cents")
        .and_then(serde_json::Value::as_u64)
        .ok_or_else(|| {
            Error::Budget(format!(
                "full-build reservation `{reservation_id}` has no valid reserved charge"
            ))
        })?;
    if reserved_cents != ceiling_cents(projection.total()?)?
        || document.outstanding_commitments_cents < reserved_cents
    {
        return Err(Error::Budget(format!(
            "full-build reservation `{reservation_id}` does not match its outstanding commitment"
        )));
    }
    let previous_ledger_sha256 = reservation
        .get("previous_ledger_sha256")
        .and_then(serde_json::Value::as_str)
        .filter(|value| is_sha256(value))
        .ok_or_else(|| {
            Error::Budget(format!(
                "full-build reservation `{reservation_id}` has no valid previous ledger hash"
            ))
        })?
        .to_owned();
    Ok(ActiveFullBuildReservation {
        binding: FullBuildReservationBinding {
            reservation_id: reservation_id.to_owned(),
            previous_ledger_sha256,
            authorization_sha256: full_build_authorization_sha256(reservation)?,
            maximum_charge: cents(reserved_cents)?,
        },
        calibration_evidence_sha256: calibration_evidence.evidence_sha256.clone(),
        representation_build_identity_sha256: calibration_evidence
            .representation_build_identity_sha256
            .clone(),
        batch_plan_manifest_sha256: calibration_evidence.batch_plan_manifest_sha256.clone(),
        projection,
    })
}

fn active_calibration_reservation(
    document: &BudgetLedgerDocument,
    reservation_id: &str,
) -> Result<ActiveCalibrationReservation> {
    if document.entries.iter().any(|entry| {
        matches!(
            entry.get("kind").and_then(serde_json::Value::as_str),
            Some("calibration_settlement" | "failed_calibration_settlement")
        ) && entry
            .get("reservation_id")
            .and_then(serde_json::Value::as_str)
            == Some(reservation_id)
    }) {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` is already settled"
        )));
    }
    let reservations = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str) == Some("calibration_reservation")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(reservation_id)
        })
        .collect::<Vec<_>>();
    let [reservation] = reservations.as_slice() else {
        if reservations.is_empty() {
            return Err(Error::Budget(format!(
                "calibration reservation `{reservation_id}` does not exist"
            )));
        }
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` has duplicate authorization entries"
        )));
    };
    let requested_maximum_charge = reservation
        .get("requested_maximum_charge_micro_usd")
        .and_then(serde_json::Value::as_u64)
        .map(MicroUsd)
        .ok_or_else(|| {
            Error::Budget(format!(
                "calibration reservation `{reservation_id}` has no valid requested charge"
            ))
        })?;
    let non_runtime_charge_reserve_value = reservation.get("non_runtime_charge_reserve_micro_usd");
    let non_runtime_charge_reserve = non_runtime_charge_reserve_value
        .map(|value| {
            value.as_u64().map(MicroUsd).ok_or_else(|| {
                Error::Budget(format!(
                    "calibration reservation `{reservation_id}` has no valid non-runtime reserve"
                ))
            })
        })
        .transpose()?
        .unwrap_or(MicroUsd(0));
    let maximum_runtime_charge =
        calibration_runtime_charge(requested_maximum_charge, non_runtime_charge_reserve)?;
    let reserved_cents = reservation
        .get("reserved_maximum_charge_cents")
        .and_then(serde_json::Value::as_u64)
        .ok_or_else(|| {
            Error::Budget(format!(
                "calibration reservation `{reservation_id}` has no valid reserved charge"
            ))
        })?;
    if reserved_cents != ceiling_cents(requested_maximum_charge)? {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` does not conservatively round its requested charge"
        )));
    }
    if document.outstanding_commitments_cents < reserved_cents
        || document.calibration_outstanding_commitments_cents < reserved_cents
    {
        return Err(Error::Budget(format!(
            "calibration reservation `{reservation_id}` exceeds the ledger's outstanding commitment"
        )));
    }
    let previous_ledger_sha256 = reservation
        .get("previous_ledger_sha256")
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| {
            Error::Budget(format!(
                "calibration reservation `{reservation_id}` has no previous ledger hash"
            ))
        })?
        .to_owned();
    let binding = CalibrationReservationBinding {
        reservation_id: reservation_id.to_owned(),
        previous_ledger_sha256,
        authorization_sha256: calibration_authorization_sha256(reservation)?,
        maximum_charge: cents(reserved_cents)?,
    };
    validate_reservation_binding(&binding)?;
    Ok(ActiveCalibrationReservation {
        binding,
        maximum_total_charge: requested_maximum_charge,
        maximum_runtime_charge,
        non_runtime_charge_reserve,
    })
}

fn require_calibration_execution_claim(
    document: &BudgetLedgerDocument,
    active: &ActiveCalibrationReservation,
) -> Result<()> {
    let claims = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str)
                == Some("calibration_execution_claim")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(active.binding.reservation_id.as_str())
        })
        .collect::<Vec<_>>();
    let [claim] = claims.as_slice() else {
        return Err(Error::Budget(format!(
            "calibration reservation `{}` requires exactly one execution claim before successful settlement",
            active.binding.reservation_id
        )));
    };
    if claim
        .get("reservation_authorization_sha256")
        .and_then(serde_json::Value::as_str)
        != Some(active.binding.authorization_sha256.as_str())
        || !claim
            .get("previous_ledger_sha256")
            .and_then(serde_json::Value::as_str)
            .is_some_and(is_sha256)
    {
        return Err(Error::Budget(format!(
            "calibration reservation `{}` has an invalid execution claim",
            active.binding.reservation_id
        )));
    }
    Ok(())
}

fn require_full_build_execution_claim<'a>(
    document: &'a BudgetLedgerDocument,
    active: &ActiveFullBuildReservation,
) -> Result<&'a serde_json::Value> {
    let claims = document
        .entries
        .iter()
        .filter(|entry| {
            entry.get("kind").and_then(serde_json::Value::as_str)
                == Some("full_build_execution_claim")
                && entry
                    .get("reservation_id")
                    .and_then(serde_json::Value::as_str)
                    == Some(active.binding.reservation_id.as_str())
        })
        .collect::<Vec<_>>();
    let [claim] = claims.as_slice() else {
        return Err(Error::Budget(format!(
            "full-build reservation `{}` requires exactly one execution claim before successful settlement",
            active.binding.reservation_id
        )));
    };
    if claim
        .get("reservation_authorization_sha256")
        .and_then(serde_json::Value::as_str)
        != Some(active.binding.authorization_sha256.as_str())
        || !claim
            .get("previous_ledger_sha256")
            .and_then(serde_json::Value::as_str)
            .is_some_and(is_sha256)
        || !claim
            .get("execution_identity_sha256")
            .and_then(serde_json::Value::as_str)
            .is_some_and(is_sha256)
        || !claim
            .get("control_binary_sha256")
            .and_then(serde_json::Value::as_str)
            .is_some_and(is_sha256)
    {
        return Err(Error::Budget(format!(
            "full-build reservation `{}` has an invalid execution claim",
            active.binding.reservation_id
        )));
    }
    Ok(claim)
}

fn apply_calibration_charge(
    document: &mut BudgetLedgerDocument,
    reserved_cents: u64,
    actual_cents: u64,
    recorded_at_utc: &str,
    record_provider_overrun: bool,
) -> Result<u64> {
    if actual_cents > reserved_cents && !record_provider_overrun {
        return Err(Error::Budget(format!(
            "calibration actual charge of {actual_cents} cents exceeds its {reserved_cents}-cent reservation"
        )));
    }
    if document.outstanding_commitments_cents < reserved_cents
        || document.calibration_outstanding_commitments_cents < reserved_cents
    {
        return Err(Error::Budget(
            "calibration reservation exceeds the ledger's outstanding commitment".to_owned(),
        ));
    }
    document.outstanding_commitments_cents -= reserved_cents;
    document.calibration_outstanding_commitments_cents -= reserved_cents;
    document.actual_spend_cents = document
        .actual_spend_cents
        .checked_add(actual_cents)
        .ok_or_else(|| Error::Budget("lifetime actual-spend cents overflowed".to_owned()))?;
    document.calibration_actual_spend_cents = document
        .calibration_actual_spend_cents
        .checked_add(actual_cents)
        .ok_or_else(|| Error::Budget("calibration actual-spend cents overflowed".to_owned()))?;
    document.reconciled_through_utc = recorded_at_utc.to_owned();
    Ok(reserved_cents.saturating_sub(actual_cents))
}

fn apply_full_build_charge(
    document: &mut BudgetLedgerDocument,
    reserved_cents: u64,
    actual_cents: u64,
    recorded_at_utc: &str,
    record_provider_overrun: bool,
) -> Result<u64> {
    if actual_cents > reserved_cents && !record_provider_overrun {
        return Err(Error::Budget(format!(
            "full-build actual charge of {actual_cents} cents exceeds its {reserved_cents}-cent reservation"
        )));
    }
    if document.outstanding_commitments_cents < reserved_cents {
        return Err(Error::Budget(
            "full-build reservation exceeds the ledger's outstanding commitment".to_owned(),
        ));
    }
    document.outstanding_commitments_cents -= reserved_cents;
    document.actual_spend_cents = document
        .actual_spend_cents
        .checked_add(actual_cents)
        .ok_or_else(|| Error::Budget("lifetime actual-spend cents overflowed".to_owned()))?;
    document.reconciled_through_utc = recorded_at_utc.to_owned();
    Ok(reserved_cents.saturating_sub(actual_cents))
}

fn reject_existing_reservation(
    document: &BudgetLedgerDocument,
    reservation_id: &str,
) -> Result<()> {
    if document.entries.iter().any(|entry| {
        entry
            .get("reservation_id")
            .and_then(serde_json::Value::as_str)
            == Some(reservation_id)
    }) {
        return Err(Error::Budget(format!(
            "budget reservation `{reservation_id}` already exists"
        )));
    }
    Ok(())
}

fn has_successful_full_build_settlement(document: &BudgetLedgerDocument) -> bool {
    document.entries.iter().any(|entry| {
        entry.get("kind").and_then(serde_json::Value::as_str) == Some("full_build_settlement")
    })
}

fn has_active_full_build_reservation(document: &BudgetLedgerDocument) -> bool {
    document.entries.iter().any(|reservation| {
        if reservation.get("kind").and_then(serde_json::Value::as_str)
            != Some("full_build_reservation")
        {
            return false;
        }
        let Some(reservation_id) = reservation
            .get("reservation_id")
            .and_then(serde_json::Value::as_str)
        else {
            return true;
        };
        !document.entries.iter().any(|entry| {
            matches!(
                entry.get("kind").and_then(serde_json::Value::as_str),
                Some("full_build_settlement" | "failed_full_build_settlement")
            ) && entry
                .get("reservation_id")
                .and_then(serde_json::Value::as_str)
                == Some(reservation_id)
        })
    })
}

fn calibration_runtime_charge(
    maximum_total_charge: MicroUsd,
    non_runtime_charge_reserve: MicroUsd,
) -> Result<MicroUsd> {
    if maximum_total_charge.0 == 0 {
        return Err(Error::Budget(
            "calibration reservation requires a nonzero maximum charge".to_owned(),
        ));
    }
    let maximum_runtime_charge = maximum_total_charge
        .0
        .checked_sub(non_runtime_charge_reserve.0)
        .filter(|charge| *charge > 0)
        .ok_or_else(|| {
            Error::Budget(
                "calibration non-runtime reserve must be smaller than its total provider cap"
                    .to_owned(),
            )
        })?;
    Ok(MicroUsd(maximum_runtime_charge))
}

fn ceiling_cents(value: MicroUsd) -> Result<u64> {
    let cents = div_ceil(u128::from(value.0), u128::from(MICRO_USD_PER_CENT));
    u64::try_from(cents)
        .map_err(|_| Error::Budget("micro-USD value does not fit ledger cents".to_owned()))
}

struct LedgerLock {
    _file: File,
}

impl LedgerLock {
    fn acquire(ledger_path: &Path) -> Result<Self> {
        let path = sibling_path(ledger_path, "lock")?;
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(&path)
            .map_err(|source| io_error("open budget-ledger lock at", &path, source))?;
        file.try_lock()
            .map_err(|source| io_error("acquire budget-ledger lock at", &path, source.into()))?;
        Ok(Self { _file: file })
    }
}

impl Drop for LedgerLock {
    fn drop(&mut self) {
        let _ = self._file.unlock();
    }
}

fn sibling_path(path: &Path, suffix: &str) -> Result<PathBuf> {
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::Budget("budget ledger path has no UTF-8 file name".to_owned()))?;
    Ok(path.with_file_name(format!(".{file_name}.{suffix}")))
}

fn sync_parent(path: &Path) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))
}

fn rental_charge(elapsed: Duration, rate_per_hour: MicroUsd) -> Result<MicroUsd> {
    rental_charge_nanoseconds(elapsed.as_nanos(), rate_per_hour)
}

fn rental_charge_nanoseconds(
    elapsed_nanoseconds: u128,
    rate_per_hour: MicroUsd,
) -> Result<MicroUsd> {
    let numerator = elapsed_nanoseconds
        .checked_mul(u128::from(rate_per_hour.0))
        .ok_or_else(|| Error::Budget("elapsed-time cost projection overflowed".to_owned()))?;
    let charge = div_ceil(numerator, NANOS_PER_HOUR);
    MicroUsd::try_from_u128(charge)
}

fn validate_ledger_document(document: &BudgetLedgerDocument) -> Result<()> {
    if document.schema_version != LEDGER_SCHEMA_VERSION {
        return Err(Error::Budget(format!(
            "budget ledger schema {} does not match required schema {LEDGER_SCHEMA_VERSION}",
            document.schema_version
        )));
    }
    if document.scope != LEDGER_SCOPE || document.currency != "USD" {
        return Err(Error::Budget(
            "budget ledger does not cover the entire oracle MVP in USD".to_owned(),
        ));
    }
    if cents(document.lifetime_cap_cents)? != MVP_LIFETIME_CAP {
        return Err(Error::Budget(
            "budget ledger does not freeze the $500 lifetime cap".to_owned(),
        ));
    }
    if cents(document.calibration_lifetime_cap_cents)? != CALIBRATION_LIFETIME_CAP {
        return Err(Error::Budget(
            "budget ledger does not freeze the $25 calibration cap".to_owned(),
        ));
    }
    if document.reconciled_through_utc.is_empty() {
        return Err(Error::Budget(
            "budget ledger has no reconciliation timestamp".to_owned(),
        ));
    }

    let actual = cents(document.actual_spend_cents)?;
    let commitments = cents(document.outstanding_commitments_cents)?;
    let calibration_actual = cents(document.calibration_actual_spend_cents)?;
    let calibration_commitments = cents(document.calibration_outstanding_commitments_cents)?;
    if calibration_actual > actual || calibration_commitments > commitments {
        return Err(Error::Budget(
            "calibration spend or commitments exceed the corresponding lifetime ledger total"
                .to_owned(),
        ));
    }
    checked_sum(&[actual, commitments])?;
    checked_sum(&[calibration_actual, calibration_commitments])?;
    Ok(())
}

fn cents(value: u64) -> Result<MicroUsd> {
    value
        .checked_mul(MICRO_USD_PER_CENT)
        .map(MicroUsd)
        .ok_or_else(|| Error::Budget("cent value does not fit micro-USD".to_owned()))
}

fn checked_sum(values: &[MicroUsd]) -> Result<MicroUsd> {
    values.iter().try_fold(MicroUsd(0), |total, value| {
        total
            .0
            .checked_add(value.0)
            .map(MicroUsd)
            .ok_or_else(|| Error::Budget("budget total overflowed micro-USD".to_owned()))
    })
}

fn require_lifetime_cap(total: MicroUsd) -> Result<()> {
    if total > MVP_LIFETIME_CAP {
        return Err(Error::Budget(format!(
            "projected lifetime total {} micro-USD exceeds the fixed $500 MVP cap",
            total.0
        )));
    }
    Ok(())
}

fn subtract(cap: MicroUsd, used: MicroUsd) -> MicroUsd {
    MicroUsd(
        cap.0
            .checked_sub(used.0)
            .expect("validated budget total is within its cap"),
    )
}

fn div_ceil(numerator: u128, denominator: u128) -> u128 {
    if numerator == 0 {
        0
    } else {
        1 + ((numerator - 1) / denominator)
    }
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct BudgetLedgerDocument {
    schema_version: u32,
    scope: String,
    currency: String,
    lifetime_cap_cents: u64,
    calibration_lifetime_cap_cents: u64,
    actual_spend_cents: u64,
    outstanding_commitments_cents: u64,
    calibration_actual_spend_cents: u64,
    calibration_outstanding_commitments_cents: u64,
    #[allow(dead_code)]
    reserved_remaining_work_cents: Option<u64>,
    reconciled_through_utc: String,
    entries: Vec<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct FinalizedProviderInvoiceDocument {
    count: u64,
    next_token: Option<serde_json::Value>,
    results: Vec<FinalizedProviderInvoice>,
    success: bool,
    total: u64,
}

impl FinalizedProviderInvoiceDocument {
    fn finalized_instance_charge(&self, rental_instance_id: &str) -> Result<MicroUsd> {
        if !self.success
            || self.count != 1
            || self.total != 1
            || self.next_token.is_some()
            || self.results.len() != 1
        {
            return Err(Error::Budget(
                "finalized provider invoice must be one complete successful invoice result"
                    .to_owned(),
            ));
        }
        let invoice = &self.results[0];
        let expected_source = format!("instance-{rental_instance_id}");
        if invoice.kind != "instance" || invoice.source != expected_source {
            return Err(Error::Budget(format!(
                "finalized provider invoice does not name calibrated instance `{rental_instance_id}`"
            )));
        }
        provider_usd_to_micro_usd(&invoice.amount)
    }
}

#[derive(Debug, Deserialize)]
struct FinalizedProviderInvoice {
    amount: serde_json::Number,
    source: String,
    #[serde(rename = "type")]
    kind: String,
}

fn provider_usd_to_micro_usd(amount: &serde_json::Number) -> Result<MicroUsd> {
    let amount = amount.to_string();
    if amount.starts_with('-') || amount.contains(['e', 'E']) {
        return Err(Error::Budget(
            "finalized provider invoice amount must be a nonnegative decimal USD value".to_owned(),
        ));
    }
    let mut pieces = amount.split('.');
    let dollars = pieces.next().unwrap_or_default();
    let fractional = pieces.next().unwrap_or_default();
    if pieces.next().is_some()
        || dollars.is_empty()
        || !dollars.bytes().all(|byte| byte.is_ascii_digit())
        || fractional.len() > 6
        || !fractional.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(Error::Budget(
            "finalized provider invoice amount is not exact to micro-USD".to_owned(),
        ));
    }
    let dollars = dollars.parse::<u64>().map_err(|_| {
        Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
    })?;
    let fractional_digits = fractional.len();
    let fractional = if fractional.is_empty() {
        0
    } else {
        fractional.parse::<u64>().map_err(|_| {
            Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
        })?
    };
    let scale = 10_u64
        .checked_pow(u32::try_from(6 - fractional_digits).map_err(|_| {
            Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
        })?)
        .ok_or_else(|| {
            Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
        })?;
    let whole = dollars.checked_mul(1_000_000).ok_or_else(|| {
        Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
    })?;
    whole
        .checked_add(fractional.checked_mul(scale).ok_or_else(|| {
            Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
        })?)
        .map(MicroUsd)
        .ok_or_else(|| {
            Error::Budget("finalized provider invoice amount does not fit micro-USD".to_owned())
        })
}
