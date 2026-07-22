//! Non-evaluative execution of the first full Phase 3 learning wave.

use std::ffi::{OsStr, OsString};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Read, Write};
use std::os::unix::ffi::{OsStrExt, OsStringExt};
use std::os::unix::fs::{
    DirBuilderExt, FileTypeExt, MetadataExt, OpenOptionsExt, PermissionsExt, symlink,
};
use std::path::Path;
use std::time::Instant;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::adaptive_learning_runner::{
    AdaptiveLearningRunnerConfig, AdaptiveLearningRunnerOutcome, run_adaptive_learning,
};
use crate::candidate_order::{CandidateOrderOracle, CandidateOrderPhase};
use crate::evaluator::{
    CompletionView, EvaluatorUi, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView,
    RestOutcome, RestView,
};
use crate::fp32_oracle::{SimilarNotesRequest, SimilarNotesWaveResponse, VectorsForNotesResponse};
use crate::representation::EventId;
use crate::snapshot::{Error, Result, io_error, read_manifest};

/// Exact Docker arguments used to launch the CPU query-role worker. The
/// explicit entrypoint is required because the pinned image's default
/// entrypoint is the Phase 2 orchestration binary, not the framed Python worker.
pub fn gte_container_prefix_arguments(
    container_name: &str,
    model_bundle_mount: &str,
    container_image: &str,
) -> Vec<OsString> {
    [
        "run".into(),
        "--rm".into(),
        "--pull=never".into(),
        "--name".into(),
        container_name.into(),
        "--interactive".into(),
        "--network".into(),
        "none".into(),
        "--read-only".into(),
        "--shm-size=1g".into(),
        "--tmpfs".into(),
        "/runtime-tmp:rw,nosuid,nodev,size=1g".into(),
        "--tmpfs".into(),
        "/root/.cache:rw,nosuid,nodev,size=2g".into(),
        "-e".into(),
        "PYTHONDONTWRITEBYTECODE=1".into(),
        "-e".into(),
        "TMPDIR=/runtime-tmp".into(),
        "-e".into(),
        "HF_HUB_OFFLINE=1".into(),
        "-e".into(),
        "TRANSFORMERS_OFFLINE=1".into(),
        "-e".into(),
        "TOKENIZERS_PARALLELISM=false".into(),
        "-v".into(),
        model_bundle_mount.into(),
        "--entrypoint".into(),
        "/opt/gte-venv/bin/python".into(),
        container_image.into(),
    ]
    .into_iter()
    .collect()
}

/// Measurements proving where a first-round preflight stopped.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct FirstRoundCostObservation {
    elapsed_ns: u64,
    preparing_calls: u64,
    rating_requests: u64,
    accepted_decisions: u64,
    presentation_number: usize,
    frozen_wave_size: usize,
}

/// Measurements proving a fresh process can recover from only durable cache state.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct FirstRoundReplayObservation {
    elapsed_ns: u64,
    preparing_calls: u64,
    recovery_requests: u64,
    rating_requests: u64,
    accepted_decisions: u64,
}

impl FirstRoundReplayObservation {
    pub const fn elapsed_ns(&self) -> u64 {
        self.elapsed_ns
    }

    pub const fn preparing_calls(&self) -> u64 {
        self.preparing_calls
    }

    pub const fn recovery_requests(&self) -> u64 {
        self.recovery_requests
    }

    pub const fn rating_requests(&self) -> u64 {
        self.rating_requests
    }

    pub const fn accepted_decisions(&self) -> u64 {
        self.accepted_decisions
    }
}

/// Proof that creating a disposable representation root left its source tree unchanged.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationViewObservation {
    source_metadata_before: String,
    source_metadata_after: String,
}

impl RepresentationViewObservation {
    pub fn source_metadata_before(&self) -> &str {
        &self.source_metadata_before
    }

    pub fn source_metadata_after(&self) -> &str {
        &self.source_metadata_after
    }
}

/// Create an atomically published representation root whose identity files are
/// private copies and whose large immutable index and shard directories are
/// read-only references to the source tree. The source verification receipt is
/// deliberately not copied; the caller must deep-verify this new view against
/// its disposable corpus and ordered-ID copies.
pub fn prepare_disposable_representation_view(
    source: impl AsRef<Path>,
    destination: impl AsRef<Path>,
) -> Result<RepresentationViewObservation> {
    let source = source.as_ref();
    let destination = destination.as_ref();
    if destination.exists() {
        return Err(Error::ArtifactExists(destination.to_owned()));
    }
    let source = fs::canonicalize(source).map_err(|error| io_error("resolve", source, error))?;
    for file in ["manifest.json", "build-identity.json"] {
        require_regular_file(&source.join(file))?;
    }
    for directory in ["index", "shards"] {
        require_directory(&source.join(directory))?;
    }
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    require_directory(parent)?;
    let parent = fs::canonicalize(parent).map_err(|error| io_error("resolve", parent, error))?;
    let name = destination.file_name().ok_or_else(|| {
        Error::Invariant("disposable representation path has no file name".to_owned())
    })?;
    let destination = parent.join(name);
    if destination.starts_with(&source) {
        return Err(Error::Invariant(
            "disposable representation must be outside its immutable source".to_owned(),
        ));
    }
    let stage = parent.join(stage_name(name)?);
    if stage.exists() {
        return Err(Error::IncompleteStage(stage));
    }
    let source_metadata_before = immutable_tree_metadata_fingerprint(&source)?;
    fs::create_dir(&stage).map_err(|error| io_error("create", &stage, error))?;
    let staged = (|| {
        for file in ["manifest.json", "build-identity.json"] {
            let target = stage.join(file);
            fs::copy(source.join(file), &target)
                .map_err(|error| io_error("copy", &target, error))?;
            File::open(&target)
                .and_then(|file| file.sync_all())
                .map_err(|error| io_error("sync", &target, error))?;
        }
        symlink(source.join("index"), stage.join("index"))
            .map_err(|error| io_error("link", stage.join("index"), error))?;
        symlink(source.join("shards"), stage.join("shards"))
            .map_err(|error| io_error("link", stage.join("shards"), error))?;
        File::open(&stage)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| io_error("sync", &stage, error))?;
        let source_metadata_after = immutable_tree_metadata_fingerprint(&source)?;
        if source_metadata_after != source_metadata_before {
            return Err(Error::Invariant(
                "immutable representation source changed while its disposable view was prepared"
                    .to_owned(),
            ));
        }
        fs::rename(&stage, &destination)
            .map_err(|error| io_error("publish", &destination, error))?;
        File::open(&parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| io_error("sync", &parent, error))?;
        Ok(RepresentationViewObservation {
            source_metadata_before,
            source_metadata_after,
        })
    })();
    if staged.is_err() && stage.exists() {
        let _ = fs::remove_dir_all(&stage);
    }
    staged
}

/// Hash every path and immutable stat field in a tree without following links.
pub fn immutable_tree_metadata_fingerprint(root: impl AsRef<Path>) -> Result<String> {
    let root = root.as_ref();
    require_directory(root)?;
    let mut hasher = Sha256::new();
    fingerprint_entry(root, Path::new(""), &mut hasher)?;
    Ok(format!("{:x}", hasher.finalize()))
}

/// Resolve an absent output beneath its real parent and reject any path that
/// would write inside an immutable source tree. This function performs no write.
pub fn resolve_output_outside_tree(
    immutable_root: impl AsRef<Path>,
    output: impl AsRef<Path>,
) -> Result<std::path::PathBuf> {
    let immutable_root = fs::canonicalize(immutable_root.as_ref())
        .map_err(|error| io_error("resolve", immutable_root.as_ref(), error))?;
    let output = output.as_ref();
    if !output.is_absolute() {
        return Err(Error::Invariant(format!(
            "output path must be absolute: `{}`",
            output.display()
        )));
    }
    match fs::symlink_metadata(output) {
        Ok(_) => return Err(Error::ArtifactExists(output.to_owned())),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(error) => return Err(io_error("read metadata for", output, error)),
    }
    let parent = output.parent().ok_or_else(|| {
        Error::Invariant(format!("output path has no parent: `{}`", output.display()))
    })?;
    let parent = fs::canonicalize(parent).map_err(|error| io_error("resolve", parent, error))?;
    let name = output.file_name().ok_or_else(|| {
        Error::Invariant(format!(
            "output path has no file name: `{}`",
            output.display()
        ))
    })?;
    if matches!(name.as_bytes(), b"" | b"." | b"..") {
        return Err(Error::Invariant(
            "output path has a special file name".to_owned(),
        ));
    }
    let resolved = parent.join(name);
    if resolved.starts_with(&immutable_root) {
        return Err(Error::Invariant(format!(
            "output `{}` would modify immutable tree `{}`",
            resolved.display(),
            immutable_root.display()
        )));
    }
    Ok(resolved)
}

/// Create a new owner-only directory for disposable preflight state.
pub fn create_private_preflight_directory(path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    let mut builder = fs::DirBuilder::new();
    builder.mode(0o700);
    builder
        .create(path)
        .map_err(|error| io_error("create", path, error))?;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700))
        .map_err(|error| io_error("set permissions on", path, error))
}

/// Atomically publish one owner-only JSON artifact without replacing anything.
pub fn write_private_json_atomic<T: Serialize>(path: impl AsRef<Path>, value: &T) -> Result<()> {
    let path = path.as_ref();
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    require_directory(parent)?;
    match fs::symlink_metadata(path) {
        Ok(_) => return Err(Error::ArtifactExists(path.to_owned())),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(error) => return Err(io_error("read metadata for", path, error)),
    }
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = parent.join(format!(".{name}.tmp"));
    match fs::symlink_metadata(&temporary) {
        Ok(_) => return Err(Error::IncompleteStage(temporary)),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(error) => return Err(io_error("read metadata for", &temporary, error)),
    }
    let mut options = OpenOptions::new();
    options.create_new(true).write(true).mode(0o600);
    let file = options
        .open(&temporary)
        .map_err(|error| io_error("create", &temporary, error))?;
    file.set_permissions(fs::Permissions::from_mode(0o600))
        .map_err(|error| io_error("set permissions on", &temporary, error))?;
    let mut writer = BufWriter::new(file);
    let result = (|| {
        serde_json::to_writer_pretty(&mut writer, value).map_err(|source| Error::Manifest {
            operation: "encode",
            path: temporary.clone(),
            source,
        })?;
        writer
            .write_all(b"\n")
            .and_then(|()| writer.flush())
            .map_err(|error| io_error("write", &temporary, error))?;
        writer
            .get_ref()
            .sync_all()
            .map_err(|error| io_error("sync", &temporary, error))?;
        fs::rename(&temporary, path).map_err(|error| io_error("publish", path, error))?;
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| io_error("sync", parent, error))
    })();
    if result.is_err() && temporary.exists() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

/// Hash the relative paths, kinds, lengths, and bytes of a regular-file tree.
/// Permissions and timestamps are deliberately excluded so a replaying reader
/// can refresh owner-only modes without appearing to alter cached responses.
pub fn immutable_content_tree_identity(root: impl AsRef<Path>) -> Result<String> {
    let root = root.as_ref();
    require_directory(root)?;
    let mut hasher = Sha256::new();
    content_identity_entry(root, Path::new(""), &mut hasher)?;
    Ok(format!("{:x}", hasher.finalize()))
}

impl FirstRoundCostObservation {
    pub const fn elapsed_ns(&self) -> u64 {
        self.elapsed_ns
    }

    pub const fn preparing_calls(&self) -> u64 {
        self.preparing_calls
    }

    pub const fn rating_requests(&self) -> u64 {
        self.rating_requests
    }

    pub const fn accepted_decisions(&self) -> u64 {
        self.accepted_decisions
    }

    pub const fn presentation_number(&self) -> usize {
        self.presentation_number
    }

    pub const fn frozen_wave_size(&self) -> usize {
        self.frozen_wave_size
    }
}

/// Exercise the production runner through its first frozen wave, then stop at
/// the evaluator boundary without rendering or accepting a judgment.
pub fn run_first_round_cost_preflight<O>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
) -> Result<FirstRoundCostObservation>
where
    O: CandidateOrderOracle,
{
    if config.session_path.exists() {
        return Err(Error::ExperimentState(format!(
            "first-round cost preflight requires a fresh session path: `{}`",
            config.session_path.display()
        )));
    }
    let started = Instant::now();
    let mut evaluator = PauseBeforeFirstRating::default();
    let outcome = run_adaptive_learning(config, oracle, &mut evaluator)?;
    if !matches!(outcome, AdaptiveLearningRunnerOutcome::Paused)
        || evaluator.preparing_calls != 2
        || evaluator.rating_requests != 1
        || evaluator.presentation_number != 1
    {
        return Err(Error::Invariant(
            "first-round cost preflight did not stop at the first rating boundary".to_owned(),
        ));
    }

    let session: serde_json::Value = read_manifest(&config.session_path)?;
    let waves = session
        .get("rounds")
        .and_then(serde_json::Value::as_array)
        .filter(|rounds| rounds.len() == 1)
        .and_then(|rounds| rounds[0].get("waves"))
        .and_then(serde_json::Value::as_array)
        .filter(|waves| waves.len() == 1)
        .ok_or_else(|| {
            Error::Invariant("first-round preflight did not persist exactly one wave".to_owned())
        })?;
    let wave = &waves[0];
    let frozen_wave_size = wave
        .get("presentation_order")
        .and_then(serde_json::Value::as_array)
        .map(Vec::len)
        .ok_or_else(|| {
            Error::Invariant("first-round preflight did not persist its frozen order".to_owned())
        })?;
    let accepted_decisions = wave
        .get("decisions")
        .and_then(serde_json::Value::as_array)
        .map(Vec::len)
        .ok_or_else(|| {
            Error::Invariant("first-round preflight has no decision ledger".to_owned())
        })?;
    let minimum_wave_size = CandidateOrderPhase::Learning.primary_count();
    let maximum_wave_size = minimum_wave_size.checked_mul(2).ok_or_else(|| {
        Error::Invariant("first-round preflight wave-size bound overflowed".to_owned())
    })?;
    if !(minimum_wave_size..=maximum_wave_size).contains(&frozen_wave_size)
        || accepted_decisions != 0
        || !session
            .get("pending_presentation")
            .is_some_and(serde_json::Value::is_object)
    {
        return Err(Error::Invariant(
            "first-round preflight persisted an invalid evaluator boundary".to_owned(),
        ));
    }

    Ok(FirstRoundCostObservation {
        elapsed_ns: elapsed_ns(started),
        preparing_calls: evaluator.preparing_calls,
        rating_requests: evaluator.rating_requests,
        accepted_decisions: accepted_decisions as u64,
        presentation_number: evaluator.presentation_number,
        frozen_wave_size,
    })
}

/// Reopen the deliberately paused first wave with an Oracle implementation
/// that rejects every backend request. Success proves the durable cache is
/// sufficient for recovery without query inference or another matrix scan.
pub fn replay_first_round_cost_preflight(
    config: &AdaptiveLearningRunnerConfig,
) -> Result<FirstRoundReplayObservation> {
    if !config.session_path.is_file() {
        return Err(Error::ExperimentState(format!(
            "first-round cost replay requires an existing session: `{}`",
            config.session_path.display()
        )));
    }
    let started = Instant::now();
    let mut oracle = CacheOnlyOracle {
        representation_version: config.compact_settings.representation_version().to_owned(),
    };
    let mut evaluator = PauseDuringRecovery::default();
    let outcome = run_adaptive_learning(config, &mut oracle, &mut evaluator)?;
    if !matches!(outcome, AdaptiveLearningRunnerOutcome::Paused)
        || evaluator.preparing_calls != 1
        || evaluator.recovery_requests != 1
        || evaluator.rating_requests != 0
    {
        return Err(Error::Invariant(
            "first-round cost replay did not stop at pending-presentation recovery".to_owned(),
        ));
    }
    let session: serde_json::Value = read_manifest(&config.session_path)?;
    let accepted_decisions = session
        .get("rounds")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|round| round.get("waves").and_then(serde_json::Value::as_array))
        .flatten()
        .filter_map(|wave| wave.get("decisions").and_then(serde_json::Value::as_array))
        .map(Vec::len)
        .sum::<usize>();
    if accepted_decisions != 0 {
        return Err(Error::Invariant(
            "first-round cost replay accepted an evaluator decision".to_owned(),
        ));
    }
    Ok(FirstRoundReplayObservation {
        elapsed_ns: elapsed_ns(started),
        preparing_calls: evaluator.preparing_calls,
        recovery_requests: evaluator.recovery_requests,
        rating_requests: evaluator.rating_requests,
        accepted_decisions: accepted_decisions as u64,
    })
}

#[derive(Default)]
struct PauseBeforeFirstRating {
    preparing_calls: u64,
    rating_requests: u64,
    presentation_number: usize,
}

impl EvaluatorUi for PauseBeforeFirstRating {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.rating_requests += 1;
        self.presentation_number = view.presentation_number();
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        Err(io::Error::other(
            "fresh first-round preflight unexpectedly requested recovery",
        ))
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Err(io::Error::other(
            "first-round preflight unexpectedly requested a rest",
        ))
    }

    fn preparing(&mut self) -> io::Result<()> {
        self.preparing_calls += 1;
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        Err(io::Error::other(
            "first-round preflight unexpectedly completed learning",
        ))
    }
}

#[derive(Default)]
struct PauseDuringRecovery {
    preparing_calls: u64,
    recovery_requests: u64,
    rating_requests: u64,
}

impl EvaluatorUi for PauseDuringRecovery {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.rating_requests += 1;
        Err(io::Error::other(
            "cache replay unexpectedly requested a fresh rating",
        ))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        self.recovery_requests += 1;
        Ok(RecoveryOutcome::Paused)
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Err(io::Error::other(
            "cache replay unexpectedly requested a rest",
        ))
    }

    fn preparing(&mut self) -> io::Result<()> {
        self.preparing_calls += 1;
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        Err(io::Error::other(
            "cache replay unexpectedly completed learning",
        ))
    }
}

struct CacheOnlyOracle {
    representation_version: String,
}

impl CandidateOrderOracle for CacheOnlyOracle {
    fn representation_version(&self) -> &str {
        &self.representation_version
    }

    fn similar_notes_wave(
        &mut self,
        _requests: &[SimilarNotesRequest],
        _representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        Err(Error::Invariant(
            "cache replay attempted a similar_notes backend request".to_owned(),
        ))
    }

    fn vectors_for_notes(
        &mut self,
        _note_ids: &[EventId],
        _representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        Err(Error::Invariant(
            "cache replay attempted a vector backend request".to_owned(),
        ))
    }
}

fn elapsed_ns(started: Instant) -> u64 {
    u64::try_from(started.elapsed().as_nanos()).unwrap_or(u64::MAX)
}

fn require_regular_file(path: &Path) -> Result<()> {
    let metadata =
        fs::metadata(path).map_err(|error| io_error("read metadata for", path, error))?;
    if !metadata.is_file() {
        return Err(Error::ArtifactMissing(path.to_owned()));
    }
    Ok(())
}

fn require_directory(path: &Path) -> Result<()> {
    let metadata =
        fs::metadata(path).map_err(|error| io_error("read metadata for", path, error))?;
    if !metadata.is_dir() {
        return Err(Error::ArtifactMissing(path.to_owned()));
    }
    Ok(())
}

fn stage_name(name: &OsStr) -> Result<std::ffi::OsString> {
    let mut bytes = Vec::with_capacity(name.as_bytes().len() + 5);
    bytes.push(b'.');
    bytes.extend_from_slice(name.as_bytes());
    bytes.extend_from_slice(b".tmp");
    if bytes == b"..tmp" || bytes == b"...tmp" {
        return Err(Error::Invariant(
            "disposable representation path has a special file name".to_owned(),
        ));
    }
    Ok(std::ffi::OsString::from_vec(bytes))
}

fn fingerprint_entry(root: &Path, relative: &Path, hasher: &mut Sha256) -> Result<()> {
    let path = root.join(relative);
    let metadata =
        fs::symlink_metadata(&path).map_err(|error| io_error("read metadata for", &path, error))?;
    let relative_bytes = relative.as_os_str().as_bytes();
    hasher.update((relative_bytes.len() as u64).to_le_bytes());
    hasher.update(relative_bytes);
    let file_type = metadata.file_type();
    let kind = if file_type.is_file() {
        b'f'
    } else if file_type.is_dir() {
        b'd'
    } else if file_type.is_symlink() {
        b'l'
    } else if file_type.is_block_device() {
        b'b'
    } else if file_type.is_char_device() {
        b'c'
    } else if file_type.is_fifo() {
        b'p'
    } else if file_type.is_socket() {
        b's'
    } else {
        b'?'
    };
    hasher.update([kind]);
    for value in [
        metadata.len(),
        metadata.dev(),
        metadata.ino(),
        u64::from(metadata.mode()),
        metadata.mtime() as u64,
        metadata.mtime_nsec() as u64,
        metadata.ctime() as u64,
        metadata.ctime_nsec() as u64,
    ] {
        hasher.update(value.to_le_bytes());
    }
    if file_type.is_symlink() {
        let target = fs::read_link(&path).map_err(|error| io_error("read link", &path, error))?;
        let bytes = target.as_os_str().as_bytes();
        hasher.update((bytes.len() as u64).to_le_bytes());
        hasher.update(bytes);
    } else if file_type.is_dir() {
        let mut names = fs::read_dir(&path)
            .map_err(|error| io_error("read", &path, error))?
            .map(|entry| {
                entry
                    .map(|entry| entry.file_name())
                    .map_err(|error| io_error("read", &path, error))
            })
            .collect::<Result<Vec<_>>>()?;
        names.sort_by(|left, right| left.as_bytes().cmp(right.as_bytes()));
        for name in names {
            fingerprint_entry(root, &relative.join(name), hasher)?;
        }
    }
    Ok(())
}

fn content_identity_entry(root: &Path, relative: &Path, hasher: &mut Sha256) -> Result<()> {
    let path = root.join(relative);
    let metadata =
        fs::symlink_metadata(&path).map_err(|error| io_error("read metadata for", &path, error))?;
    let relative_bytes = relative.as_os_str().as_bytes();
    hasher.update((relative_bytes.len() as u64).to_le_bytes());
    hasher.update(relative_bytes);
    if metadata.is_dir() {
        hasher.update([b'd']);
        let mut names = fs::read_dir(&path)
            .map_err(|error| io_error("read", &path, error))?
            .map(|entry| {
                entry
                    .map(|entry| entry.file_name())
                    .map_err(|error| io_error("read", &path, error))
            })
            .collect::<Result<Vec<_>>>()?;
        names.sort_by(|left, right| left.as_bytes().cmp(right.as_bytes()));
        for name in names {
            content_identity_entry(root, &relative.join(name), hasher)?;
        }
    } else if metadata.is_file() {
        hasher.update([b'f']);
        hasher.update(metadata.len().to_le_bytes());
        let mut reader =
            BufReader::new(File::open(&path).map_err(|error| io_error("open", &path, error))?);
        let mut buffer = [0_u8; 64 * 1024];
        loop {
            let bytes = reader
                .read(&mut buffer)
                .map_err(|error| io_error("read", &path, error))?;
            if bytes == 0 {
                break;
            }
            hasher.update(&buffer[..bytes]);
        }
    } else {
        return Err(Error::Invariant(format!(
            "content tree contains a non-regular entry: `{}`",
            path.display()
        )));
    }
    Ok(())
}
