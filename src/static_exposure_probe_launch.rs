//! Read-only V1 handoff and launch wiring for the static exposure probe.

use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::Deserialize;

use crate::adaptive_learning_runner::replay_completed_adaptive_learning;
use crate::artifact::hash_file;
use crate::evaluator::{EvaluatorUi, RepetitionAnswer};
use crate::evaluator_tui::FullScreenEvaluator;
use crate::final_evaluation_runner::{FinalEvaluationRunnerConfig, replay_frozen_final_evaluation};
use crate::phase3_binding::Phase3RunnerBinding;
use crate::phase3_cost_preflight::immutable_content_tree_identity;
use crate::snapshot::{Error, Result, io_error, read_manifest, require_directory, require_file};
use crate::static_exposure_probe_runner::{
    CREC_109_EXPOSURE_CEILING, FULL_POOL_ESCAPE_PROBE_PURPOSE, FullPoolExposureGateProtocol,
    FullPoolExposureSeed, StaticExposureProbeInput, StaticExposureProbeRunnerConfig,
    StaticExposureProbeRunnerOutcome, StaticExposureProbeSourceProvenance,
    StaticExposureProbeVerification, build_static_exposure_probe_input,
    replay_completed_static_exposure_probe, run_full_pool_exposure_probe,
    run_static_exposure_probe, verify_full_pool_exposure_probe, verify_static_exposure_probe,
};

const CONFIG_SCHEMA_VERSION: u32 = 1;

pub use crate::static_exposure_probe_runner::STATIC_EXPOSURE_PROBE_PURPOSE;

/// Auditable result of calibrating the CREC-109 hard exposure ceiling from the
/// completed CREC-108 repetition answers.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct FullPoolExposureCalibration {
    ceiling: f64,
    true_positives: usize,
    false_negatives: usize,
    true_negatives: usize,
    false_positives: usize,
}

impl FullPoolExposureCalibration {
    pub const fn ceiling(self) -> f64 {
        self.ceiling
    }

    pub const fn true_positives(self) -> usize {
        self.true_positives
    }

    pub const fn false_negatives(self) -> usize {
        self.false_negatives
    }

    pub const fn true_negatives(self) -> usize {
        self.true_negatives
    }

    pub const fn false_positives(self) -> usize {
        self.false_positives
    }
}

/// Choose the midpoint between adjacent distinct observed scores that
/// maximizes balanced accuracy. Exact ties choose the higher ceiling.
pub fn calibrate_full_pool_exposure_ceiling(
    observations: &[(f64, RepetitionAnswer)],
) -> Result<FullPoolExposureCalibration> {
    if observations.len() != 40 {
        return Err(Error::ExperimentState(
            "full-pool ceiling calibration requires exactly 40 source answers".to_owned(),
        ));
    }
    let positive_count = observations
        .iter()
        .filter(|(_, answer)| *answer == RepetitionAnswer::Yes)
        .count();
    let negative_count = observations.len() - positive_count;
    if positive_count == 0 || negative_count == 0 {
        return Err(Error::ExperimentState(
            "full-pool ceiling calibration requires both repetition answers".to_owned(),
        ));
    }
    let mut scores = observations
        .iter()
        .map(|(exposure, _)| {
            if !exposure.is_finite() || *exposure < 0.0 {
                return Err(Error::ExperimentState(
                    "full-pool calibration exposure must be finite and non-negative".to_owned(),
                ));
            }
            Ok(*exposure)
        })
        .collect::<Result<Vec<_>>>()?;
    scores.sort_by(f64::total_cmp);
    scores.dedup_by(|left, right| left.to_bits() == right.to_bits());
    let mut best: Option<(usize, f64, FullPoolExposureCalibration)> = None;
    for pair in scores.windows(2) {
        let ceiling = pair[0] + (pair[1] - pair[0]) / 2.0;
        if !ceiling.is_finite() {
            return Err(Error::ExperimentState(
                "full-pool calibration midpoint is not finite".to_owned(),
            ));
        }
        let mut calibration = FullPoolExposureCalibration {
            ceiling,
            true_positives: 0,
            false_negatives: 0,
            true_negatives: 0,
            false_positives: 0,
        };
        for (exposure, answer) in observations {
            match (*exposure >= ceiling, *answer) {
                (true, RepetitionAnswer::Yes) => calibration.true_positives += 1,
                (false, RepetitionAnswer::Yes) => calibration.false_negatives += 1,
                (false, RepetitionAnswer::No) => calibration.true_negatives += 1,
                (true, RepetitionAnswer::No) => calibration.false_positives += 1,
            }
        }
        let balanced_accuracy_numerator = calibration.true_positives * negative_count
            + calibration.true_negatives * positive_count;
        if best.as_ref().is_none_or(|(best_score, best_ceiling, _)| {
            balanced_accuracy_numerator > *best_score
                || (balanced_accuracy_numerator == *best_score
                    && ceiling.total_cmp(best_ceiling).is_gt())
        }) {
            best = Some((balanced_accuracy_numerator, ceiling, calibration));
        }
    }
    let calibration = best.map(|(_, _, calibration)| calibration).ok_or_else(|| {
        Error::ExperimentState(
            "full-pool ceiling calibration requires two distinct exposure scores".to_owned(),
        )
    })?;
    if calibration.ceiling.to_bits() != CREC_109_EXPOSURE_CEILING.to_bits() {
        return Err(Error::ExperimentState(format!(
            "source labels produce exposure ceiling {}, expected {}",
            calibration.ceiling, CREC_109_EXPOSURE_CEILING
        )));
    }
    Ok(calibration)
}

/// Frozen source paths and separate mutable outputs for one live probe.
#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StaticExposureProbeLaunchConfig {
    schema_version: u32,
    purpose: String,
    source_phase3_runner_binding_path: PathBuf,
    source_phase4_session_path: PathBuf,
    source_phase4_frozen_orders_path: PathBuf,
    source_phase4_oracle_cache_path: PathBuf,
    source_phase4_launch_receipt_path: PathBuf,
    corpus_path: PathBuf,
    session_path: PathBuf,
    report_path: PathBuf,
}

impl StaticExposureProbeLaunchConfig {
    pub fn source_phase3_runner_binding_path(&self) -> &Path {
        &self.source_phase3_runner_binding_path
    }

    pub fn source_phase4_session_path(&self) -> &Path {
        &self.source_phase4_session_path
    }

    pub fn source_phase4_frozen_orders_path(&self) -> &Path {
        &self.source_phase4_frozen_orders_path
    }

    pub fn source_phase4_oracle_cache_path(&self) -> &Path {
        &self.source_phase4_oracle_cache_path
    }

    pub fn source_phase4_launch_receipt_path(&self) -> &Path {
        &self.source_phase4_launch_receipt_path
    }

    pub fn corpus_path(&self) -> &Path {
        &self.corpus_path
    }

    pub fn session_path(&self) -> &Path {
        &self.session_path
    }

    pub fn report_path(&self) -> &Path {
        &self.report_path
    }

    fn validate(&self) -> Result<()> {
        if self.schema_version != CONFIG_SCHEMA_VERSION {
            return Err(Error::ExperimentState(
                "static exposure probe config has the wrong schema".to_owned(),
            ));
        }
        if self.purpose != STATIC_EXPOSURE_PROBE_PURPOSE {
            return Err(Error::ExperimentState(
                "config is not a static exposure probe".to_owned(),
            ));
        }
        for (label, path) in [
            (
                "source Phase 3 runner binding",
                self.source_phase3_runner_binding_path.as_path(),
            ),
            (
                "source Phase 4 session",
                self.source_phase4_session_path.as_path(),
            ),
            (
                "source Phase 4 frozen orders",
                self.source_phase4_frozen_orders_path.as_path(),
            ),
            (
                "source Phase 4 Oracle cache",
                self.source_phase4_oracle_cache_path.as_path(),
            ),
            (
                "source Phase 4 launch receipt",
                self.source_phase4_launch_receipt_path.as_path(),
            ),
            ("display corpus", self.corpus_path.as_path()),
            ("probe session", self.session_path.as_path()),
            ("probe report", self.report_path.as_path()),
        ] {
            require_absolute_normalized(path, label)?;
        }
        for path in [
            &self.source_phase3_runner_binding_path,
            &self.source_phase4_session_path,
            &self.source_phase4_frozen_orders_path,
            &self.source_phase4_launch_receipt_path,
        ] {
            require_file(path)?;
        }
        require_directory(&self.source_phase4_oracle_cache_path)?;
        require_directory(&self.corpus_path)?;
        let session = resolve_output_path(&self.session_path)?;
        let report = resolve_output_path(&self.report_path)?;
        let phase3_source = canonical_parent(&self.source_phase3_runner_binding_path)?;
        let phase4_source = canonical_parent(&self.source_phase4_session_path)?;
        let corpus = fs::canonicalize(&self.corpus_path)
            .map_err(|source| io_error("resolve", &self.corpus_path, source))?;
        if session == report
            || [&phase3_source, &phase4_source, &corpus]
                .into_iter()
                .any(|source| session.starts_with(source) || report.starts_with(source))
        {
            return Err(Error::ExperimentState(
                "probe outputs must be distinct and outside every read-only source".to_owned(),
            ));
        }
        Ok(())
    }
}

/// Decode and validate one launch config without changing any source.
pub fn read_static_exposure_probe_launch_config(
    path: impl AsRef<Path>,
) -> Result<StaticExposureProbeLaunchConfig> {
    let config: StaticExposureProbeLaunchConfig = read_manifest(path.as_ref())?;
    config.validate()?;
    Ok(config)
}

/// Reconstruct V1 cache-only state and run the isolated probe TUI.
pub fn run_static_exposure_probe_tui(
    config: &StaticExposureProbeLaunchConfig,
) -> Result<StaticExposureProbeRunnerOutcome> {
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    evaluator
        .preparing()
        .map_err(|source| io_error("write", "<terminal-output>", source))?;
    let prepared = prepare_static_exposure_probe(config)?;
    run_static_exposure_probe(&prepared.runner_config, &prepared.input, &mut evaluator)
}

/// Fully verified cache-only source replay and immutable probe input.
pub struct PreparedStaticExposureProbe {
    runner_config: StaticExposureProbeRunnerConfig,
    input: StaticExposureProbeInput,
}

impl PreparedStaticExposureProbe {
    pub fn candidate_count(&self) -> usize {
        self.input.candidates().len()
    }

    pub fn historical_presentation_count(&self) -> usize {
        self.input.historical_presented_event_ids().len()
    }

    pub fn representation_version(&self) -> &str {
        self.input.representation_version()
    }

    pub fn verification_state(&self) -> Result<StaticExposureProbeVerification> {
        verify_static_exposure_probe(&self.runner_config, &self.input)
    }
}

/// Verify and reconstruct everything needed before entering the evaluator TUI.
///
/// This opens no embedding model, performs no Oracle inference, and writes no
/// session or report.
pub fn prepare_static_exposure_probe(
    config: &StaticExposureProbeLaunchConfig,
) -> Result<PreparedStaticExposureProbe> {
    config.validate()?;
    let binding: Phase3RunnerBinding = read_manifest(&config.source_phase3_runner_binding_path)?;
    let phase3_runner_config = binding.runner_config().map_err(Error::ExperimentState)?;
    let initial_presentations = binding
        .initial_presentations()
        .map_err(Error::ExperimentState)?;
    let completed =
        replay_completed_adaptive_learning(&phase3_runner_config, &initial_presentations)?;
    let phase3_runner_binding_sha256 = hash_file(&config.source_phase3_runner_binding_path)?;
    let phase3_session_sha256 = hash_file(binding.session_path())?;
    let phase4_session_sha256 = hash_file(&config.source_phase4_session_path)?;
    let phase4_frozen_orders_sha256 = hash_file(&config.source_phase4_frozen_orders_path)?;
    let phase4_oracle_cache_identity_sha256 =
        immutable_content_tree_identity(&config.source_phase4_oracle_cache_path)?;
    let phase4_launch_receipt_sha256 = hash_file(&config.source_phase4_launch_receipt_path)?;

    let corpus_data_path = config.corpus_path.join("data.mdb");
    require_file(&corpus_data_path)?;
    let actual_corpus_identity = format!("sha256:{}", hash_file(&corpus_data_path)?);
    if actual_corpus_identity != binding.corpus_identity() {
        return Err(Error::ExperimentState(
            "probe display corpus differs from the frozen Phase 3 corpus identity".to_owned(),
        ));
    }
    let phase4_config = FinalEvaluationRunnerConfig {
        corpus_path: config.corpus_path.clone(),
        corpus_identity: binding.corpus_identity().to_owned(),
        session_path: config.source_phase4_session_path.clone(),
        frozen_orders_path: config.source_phase4_frozen_orders_path.clone(),
        report_path: config
            .source_phase4_session_path
            .with_file_name("final-report.json"),
        oracle_cache_path: config.source_phase4_oracle_cache_path.clone(),
        phase3_handoff_identity_sha256: phase3_session_sha256.clone(),
        guarded_launch_identity_sha256: phase4_launch_receipt_sha256.clone(),
        geometry_version: binding.geometry_version().to_owned(),
    };
    let replay = replay_frozen_final_evaluation(&phase4_config, completed)?;
    let source_provenance = StaticExposureProbeSourceProvenance::new(
        phase3_runner_binding_sha256,
        phase3_session_sha256,
        phase4_session_sha256,
        phase4_frozen_orders_sha256.clone(),
        phase4_oracle_cache_identity_sha256,
        phase4_launch_receipt_sha256,
    )?;
    let input = build_static_exposure_probe_input(&replay, phase4_frozen_orders_sha256)?
        .with_source_provenance(source_provenance);
    let runner_config = StaticExposureProbeRunnerConfig {
        corpus_path: config.corpus_path.clone(),
        corpus_identity: binding.corpus_identity().to_owned(),
        session_path: config.session_path.clone(),
        report_path: config.report_path.clone(),
    };
    Ok(PreparedStaticExposureProbe {
        runner_config,
        input,
    })
}

/// Frozen CREC-108 handoff, copied display corpus, and separate mutable
/// outputs for the CREC-109 full-pool escape probe.
#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FullPoolEscapeProbeLaunchConfig {
    schema_version: u32,
    purpose: String,
    source_static_exposure_probe_config_path: PathBuf,
    corpus_path: PathBuf,
    session_path: PathBuf,
    report_path: PathBuf,
}

impl FullPoolEscapeProbeLaunchConfig {
    pub fn source_static_exposure_probe_config_path(&self) -> &Path {
        &self.source_static_exposure_probe_config_path
    }

    pub fn corpus_path(&self) -> &Path {
        &self.corpus_path
    }

    pub fn session_path(&self) -> &Path {
        &self.session_path
    }

    pub fn report_path(&self) -> &Path {
        &self.report_path
    }

    fn validate(&self) -> Result<()> {
        if self.schema_version != CONFIG_SCHEMA_VERSION {
            return Err(Error::ExperimentState(
                "full-pool escape probe config has the wrong schema".to_owned(),
            ));
        }
        if self.purpose != FULL_POOL_ESCAPE_PROBE_PURPOSE {
            return Err(Error::ExperimentState(
                "config is not a full-pool escape probe".to_owned(),
            ));
        }
        for (label, path) in [
            (
                "source static exposure probe config",
                self.source_static_exposure_probe_config_path.as_path(),
            ),
            ("copied display corpus", self.corpus_path.as_path()),
            ("full-pool probe session", self.session_path.as_path()),
            ("full-pool probe report", self.report_path.as_path()),
        ] {
            require_absolute_normalized(path, label)?;
        }
        require_file(&self.source_static_exposure_probe_config_path)?;
        require_directory(&self.corpus_path)?;
        require_file(&self.corpus_path.join("data.mdb"))?;
        Ok(())
    }

    fn validate_against_source(&self, source: &StaticExposureProbeLaunchConfig) -> Result<()> {
        let source_probe_root = canonical_parent(&self.source_static_exposure_probe_config_path)?;
        let source_phase3_root = canonical_parent(source.source_phase3_runner_binding_path())?;
        let source_phase4_root = canonical_parent(source.source_phase4_session_path())?;
        let source_corpus = fs::canonicalize(source.corpus_path())
            .map_err(|error| io_error("resolve", source.corpus_path(), error))?;
        let source_session = resolve_output_path(source.session_path())?;
        let source_report = resolve_output_path(source.report_path())?;
        let destination_corpus = fs::canonicalize(&self.corpus_path)
            .map_err(|error| io_error("resolve", &self.corpus_path, error))?;
        let session = resolve_output_path(&self.session_path)?;
        let report = resolve_output_path(&self.report_path)?;
        let frozen_roots = [
            source_probe_root,
            source_phase3_root,
            source_phase4_root,
            source_corpus,
        ];
        if session == report
            || [source_session, source_report].iter().any(|source| {
                destination_corpus == *source || session == *source || report == *source
            })
            || session.starts_with(&destination_corpus)
            || report.starts_with(&destination_corpus)
            || frozen_roots.iter().any(|root| {
                destination_corpus.starts_with(root)
                    || session.starts_with(root)
                    || report.starts_with(root)
            })
        {
            return Err(Error::ExperimentState(
                "full-pool probe corpus and outputs must be separate from every frozen source"
                    .to_owned(),
            ));
        }
        Ok(())
    }
}

pub fn read_full_pool_escape_probe_launch_config(
    path: impl AsRef<Path>,
) -> Result<FullPoolEscapeProbeLaunchConfig> {
    let config: FullPoolEscapeProbeLaunchConfig = read_manifest(path.as_ref())?;
    config.validate()?;
    let source =
        read_static_exposure_probe_launch_config(&config.source_static_exposure_probe_config_path)?;
    config.validate_against_source(&source)?;
    Ok(config)
}

pub struct PreparedFullPoolEscapeProbe {
    runner_config: StaticExposureProbeRunnerConfig,
    input: StaticExposureProbeInput,
    calibration: FullPoolExposureCalibration,
}

impl PreparedFullPoolEscapeProbe {
    pub fn candidate_count(&self) -> usize {
        self.input.candidates().len()
    }

    pub fn seeded_history_count(&self) -> usize {
        self.input
            .full_pool_exposure_gate()
            .expect("prepared full-pool input has its protocol")
            .seeded_history()
            .len()
    }

    pub const fn calibration(&self) -> FullPoolExposureCalibration {
        self.calibration
    }

    pub fn verification_state(&self) -> Result<StaticExposureProbeVerification> {
        verify_full_pool_exposure_probe(&self.runner_config, &self.input)
    }
}

/// Verify CREC-108, reproduce its calibrated ceiling, bind its exact ordered
/// 40-note history, and prepare CREC-109 without writing any artifact.
pub fn prepare_full_pool_escape_probe(
    config: &FullPoolEscapeProbeLaunchConfig,
) -> Result<PreparedFullPoolEscapeProbe> {
    config.validate()?;
    let source_config =
        read_static_exposure_probe_launch_config(&config.source_static_exposure_probe_config_path)?;
    config.validate_against_source(&source_config)?;
    let source_config_sha256 = hash_file(&config.source_static_exposure_probe_config_path)?;
    let source_prepared = prepare_static_exposure_probe(&source_config)?;
    let source_replay = replay_completed_static_exposure_probe(
        &source_prepared.runner_config,
        &source_prepared.input,
    )?;
    let source_session_sha256 = hash_file(source_config.session_path())?;
    let source_report_sha256 = hash_file(source_config.report_path())?;
    let observations = source_replay
        .presentations()
        .iter()
        .map(|presentation| {
            (
                presentation.source_exposure(),
                presentation.source_repetition(),
            )
        })
        .collect::<Vec<_>>();
    let calibration = calibrate_full_pool_exposure_ceiling(&observations)?;
    let seeded_history = source_replay
        .presentations()
        .iter()
        .map(|presentation| {
            FullPoolExposureSeed::new(
                presentation.event_id(),
                presentation.source_exposure(),
                presentation.source_repetition(),
            )
        })
        .collect::<Result<Vec<_>>>()?;
    let protocol = FullPoolExposureGateProtocol::new(
        seeded_history,
        source_config_sha256,
        source_session_sha256,
        source_report_sha256,
        source_replay.input_identity_sha256().to_owned(),
    )?;
    let input = source_prepared
        .input
        .with_full_pool_exposure_gate(protocol)?;

    let destination_data_path = config.corpus_path.join("data.mdb");
    let destination_corpus_identity = format!("sha256:{}", hash_file(&destination_data_path)?);
    if destination_corpus_identity != source_prepared.runner_config.corpus_identity {
        return Err(Error::ExperimentState(
            "full-pool display corpus differs from the verified source corpus".to_owned(),
        ));
    }
    let runner_config = StaticExposureProbeRunnerConfig {
        corpus_path: config.corpus_path.clone(),
        corpus_identity: destination_corpus_identity,
        session_path: config.session_path.clone(),
        report_path: config.report_path.clone(),
    };
    Ok(PreparedFullPoolEscapeProbe {
        runner_config,
        input,
        calibration,
    })
}

pub fn run_full_pool_escape_probe_tui(
    config: &FullPoolEscapeProbeLaunchConfig,
) -> Result<StaticExposureProbeRunnerOutcome> {
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    evaluator
        .preparing()
        .map_err(|source| io_error("write", "<terminal-output>", source))?;
    let prepared = prepare_full_pool_escape_probe(config)?;
    run_full_pool_exposure_probe(&prepared.runner_config, &prepared.input, &mut evaluator)
}

fn require_absolute_normalized(path: &Path, label: &str) -> Result<()> {
    if !path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                Component::CurDir | Component::ParentDir | Component::Prefix(_)
            )
        })
    {
        return Err(Error::ExperimentState(format!(
            "{label} path must be absolute and normalized"
        )));
    }
    Ok(())
}

fn canonical_parent(path: &Path) -> Result<PathBuf> {
    let parent = path
        .parent()
        .ok_or_else(|| Error::ExperimentState("source path has no parent".to_owned()))?;
    fs::canonicalize(parent).map_err(|source| io_error("resolve", parent, source))
}

fn resolve_output_path(path: &Path) -> Result<PathBuf> {
    match fs::canonicalize(path) {
        Ok(path) => Ok(path),
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
            let parent = path.parent().unwrap_or_else(|| Path::new("."));
            let parent =
                fs::canonicalize(parent).map_err(|source| io_error("resolve", parent, source))?;
            let name = path
                .file_name()
                .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
            Ok(parent.join(name))
        }
        Err(source) => Err(io_error("resolve", path, source)),
    }
}
