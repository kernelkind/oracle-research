//! Cooperative admission control for bounded disk reads.

use std::collections::VecDeque;
use std::fs;
use std::panic::AssertUnwindSafe;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Condvar, Mutex, MutexGuard, Weak};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use thiserror::Error;

const PRESSURE_PATH_ENVIRONMENT_VARIABLE: &str = "ORACLE_MVP_IO_PRESSURE_PATH";
const SAMPLE_INTERVAL: Duration = Duration::from_millis(250);
const OBSERVATION_WINDOW: Duration = Duration::from_secs(2);
const LOW_PRESSURE_COOLDOWN: Duration = Duration::from_secs(10);
const NO_PROGRESS_TIMEOUT: Duration = Duration::from_secs(60);
const HIGH_PRESSURE_PERCENT: f64 = 20.0;
const LOW_PRESSURE_PERCENT: f64 = 5.0;
const PRESSURE_READ_ATTEMPTS: usize = 3;
const PRESSURE_READ_RETRY_DELAY: Duration = Duration::from_millis(10);

/// A pressure-controller failure.
#[derive(Debug, Error)]
pub enum IoPressureError {
    /// The monitor thread could not be started.
    #[error("failed to start I/O pressure monitor: {0}")]
    Start(#[source] std::io::Error),

    /// Pressure control stopped or failed closed.
    #[error("I/O pressure control failed: {0}")]
    Control(String),
}

/// How one bounded read was admitted.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReadAdmission {
    /// Ordinary admission while pressure is safe.
    Normal,
    /// The sole bounded probe after a low-pressure cooldown.
    Probe,
}

/// Cooperative gate shared by the pressure monitor and a sequential reader.
#[derive(Clone)]
pub struct IoPressureController {
    inner: Arc<Inner>,
}

/// Permission for exactly one bounded disk-read operation.
pub struct ReadPermit {
    controller: IoPressureController,
    admission: ReadAdmission,
    finished: bool,
}

struct Inner {
    pressure_path: PathBuf,
    state: Mutex<State>,
    changed: Condvar,
    monitor: Mutex<Option<JoinHandle<()>>>,
}

struct State {
    mode: Mode,
    read_in_flight: bool,
    low_since: Option<Instant>,
    completed_during_low: bool,
    recovery_ready: bool,
    last_completed_progress: Option<Instant>,
    failure: Option<String>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Mode {
    Observing,
    Running,
    Paused,
    Failed,
    Shutdown,
}

struct PressureSample {
    observed_at: Instant,
    some_total_microseconds: u64,
}

impl IoPressureController {
    /// Start monitoring one explicit cgroup-v2 `io.pressure` file.
    pub fn start(path: impl AsRef<Path>) -> Result<Self, IoPressureError> {
        let inner = Arc::new(Inner {
            pressure_path: path.as_ref().to_owned(),
            state: Mutex::new(State {
                mode: Mode::Observing,
                read_in_flight: false,
                low_since: None,
                completed_during_low: false,
                recovery_ready: false,
                last_completed_progress: None,
                failure: None,
            }),
            changed: Condvar::new(),
            monitor: Mutex::new(None),
        });
        let weak = Arc::downgrade(&inner);
        let handle = thread::Builder::new()
            .name("oracle-io-pressure".to_owned())
            .spawn(move || monitor_entry(weak))
            .map_err(IoPressureError::Start)?;
        *lock(&inner.monitor) = Some(handle);
        Ok(Self { inner })
    }

    /// Start against the configured path, or this process's own cgroup.
    pub fn for_current_cgroup() -> Result<Self, IoPressureError> {
        let path = match std::env::var_os(PRESSURE_PATH_ENVIRONMENT_VARIABLE) {
            Some(path) => PathBuf::from(path),
            None => current_cgroup_pressure_path()?,
        };
        Self::start(path)
    }

    /// Wait until one bounded disk read may begin.
    pub fn wait_for_read(&self) -> Result<ReadPermit, IoPressureError> {
        let mut state = lock(&self.inner.state);
        loop {
            match state.mode {
                Mode::Running if !state.read_in_flight => {
                    state.read_in_flight = true;
                    return Ok(ReadPermit {
                        controller: self.clone(),
                        admission: ReadAdmission::Normal,
                        finished: false,
                    });
                }
                Mode::Paused if state.recovery_ready && !state.read_in_flight => {
                    state.read_in_flight = true;
                    return Ok(ReadPermit {
                        controller: self.clone(),
                        admission: ReadAdmission::Probe,
                        finished: false,
                    });
                }
                Mode::Failed | Mode::Shutdown => return Err(state_error(&state)),
                Mode::Observing | Mode::Running | Mode::Paused => {
                    state = self
                        .inner
                        .changed
                        .wait(state)
                        .unwrap_or_else(std::sync::PoisonError::into_inner);
                }
            }
        }
    }

    /// Stop the monitor and wake any blocked reader.
    pub fn shutdown(&self) -> Result<(), IoPressureError> {
        {
            let mut state = lock(&self.inner.state);
            if state.mode != Mode::Failed {
                state.mode = Mode::Shutdown;
            }
        }
        self.inner.changed.notify_all();
        let handle = lock(&self.inner.monitor).take();
        if let Some(handle) = handle
            && handle.join().is_err()
        {
            fail(&self.inner, "pressure monitor panicked".to_owned());
        }
        let state = lock(&self.inner.state);
        if state.mode == Mode::Failed {
            Err(state_error(&state))
        } else {
            Ok(())
        }
    }

    fn finish_read(
        &self,
        admission: ReadAdmission,
        completed: bool,
    ) -> Result<(), IoPressureError> {
        let now = Instant::now();
        let mut state = lock(&self.inner.state);
        if !state.read_in_flight {
            return Err(IoPressureError::Control(
                "a read permit completed without an admitted read".to_owned(),
            ));
        }
        state.read_in_flight = false;
        if completed && state.mode == Mode::Paused {
            state.last_completed_progress = Some(now);
            if state.low_since.is_some() {
                state.completed_during_low = true;
            }
        }
        match admission {
            ReadAdmission::Normal if completed && state.mode == Mode::Paused => {
                if state.recovery_ready && state.completed_during_low {
                    resume(&mut state);
                }
            }
            ReadAdmission::Normal => {}
            ReadAdmission::Probe
                if state.mode == Mode::Paused && completed && state.recovery_ready =>
            {
                resume(&mut state);
            }
            ReadAdmission::Probe if state.mode == Mode::Paused && !completed => {
                state.low_since = Some(now);
                state.completed_during_low = false;
                state.recovery_ready = false;
            }
            ReadAdmission::Probe => {}
        }
        let failed = matches!(state.mode, Mode::Failed | Mode::Shutdown);
        let error = failed.then(|| state_error(&state));
        drop(state);
        self.inner.changed.notify_all();
        match error {
            Some(error) => Err(error),
            None => Ok(()),
        }
    }
}

impl ReadPermit {
    /// Return how this operation was admitted.
    pub const fn admission(&self) -> ReadAdmission {
        self.admission
    }

    /// Record that the complete bounded read reached RAM successfully.
    pub fn complete(mut self) -> Result<(), IoPressureError> {
        let result = self.controller.finish_read(self.admission, true);
        self.finished = true;
        result
    }
}

impl Drop for ReadPermit {
    fn drop(&mut self) {
        if !self.finished {
            let _ = self.controller.finish_read(self.admission, false);
        }
    }
}

fn monitor_entry(weak: Weak<Inner>) {
    let outcome = std::panic::catch_unwind(AssertUnwindSafe(|| monitor_pressure(weak.clone())));
    let Some(inner) = weak.upgrade() else {
        return;
    };
    match outcome {
        Err(_) => fail(&inner, "pressure monitor panicked".to_owned()),
        Ok(()) => {
            let expected = {
                let state = lock(&inner.state);
                matches!(state.mode, Mode::Failed | Mode::Shutdown)
            };
            if !expected {
                fail(&inner, "pressure monitor stopped unexpectedly".to_owned());
            }
        }
    }
}

fn monitor_pressure(weak: Weak<Inner>) {
    let mut samples = VecDeque::<PressureSample>::new();
    loop {
        let Some(inner) = weak.upgrade() else {
            return;
        };
        if matches!(lock(&inner.state).mode, Mode::Failed | Mode::Shutdown) {
            return;
        }
        let now = Instant::now();
        let total = match read_some_total(&inner.pressure_path) {
            Ok(total) => total,
            Err(error) => {
                fail(
                    &inner,
                    format!(
                        "reading workload I/O pressure from `{}`: {error}",
                        inner.pressure_path.display()
                    ),
                );
                return;
            }
        };
        if samples
            .back()
            .is_some_and(|sample| total < sample.some_total_microseconds)
        {
            restart_observation(&inner);
            samples.clear();
        }
        samples.push_back(PressureSample {
            observed_at: now,
            some_total_microseconds: total,
        });
        while samples.len() > 2
            && samples
                .get(1)
                .is_some_and(|sample| now.duration_since(sample.observed_at) >= OBSERVATION_WINDOW)
        {
            samples.pop_front();
        }
        if let Some(first) = samples
            .front()
            .filter(|sample| now.duration_since(sample.observed_at) >= OBSERVATION_WINDOW)
        {
            let elapsed = now.duration_since(first.observed_at);
            let delta = total.saturating_sub(first.some_total_microseconds);
            let percent = delta as f64 / elapsed.as_micros().max(1) as f64 * 100.0;
            update_pressure(&inner, now, percent);
        }
        check_no_progress(&inner, now);
        drop(inner);
        thread::sleep(SAMPLE_INTERVAL);
    }
}

fn update_pressure(inner: &Inner, now: Instant, percent: f64) {
    let mut state = lock(&inner.state);
    if matches!(state.mode, Mode::Failed | Mode::Shutdown) {
        return;
    }
    if percent >= HIGH_PRESSURE_PERCENT {
        let already_paused = state.mode == Mode::Paused;
        state.mode = Mode::Paused;
        reset_recovery(&mut state);
        if !already_paused {
            state.last_completed_progress = Some(now);
        }
    } else if state.mode == Mode::Observing {
        state.mode = Mode::Running;
    } else if state.mode == Mode::Paused {
        if percent < LOW_PRESSURE_PERCENT {
            let low_since = *state.low_since.get_or_insert(now);
            if now.duration_since(low_since) >= LOW_PRESSURE_COOLDOWN {
                if state.completed_during_low {
                    resume(&mut state);
                } else {
                    state.recovery_ready = true;
                }
            }
        } else {
            reset_recovery(&mut state);
        }
    }
    drop(state);
    inner.changed.notify_all();
}

fn check_no_progress(inner: &Inner, now: Instant) {
    let mut state = lock(&inner.state);
    if state.mode == Mode::Paused
        && state
            .last_completed_progress
            .is_some_and(|progress| now.duration_since(progress) >= NO_PROGRESS_TIMEOUT)
    {
        state.failure =
            Some("I/O pressure remained unsafe without a completed bounded read".to_owned());
        state.mode = Mode::Failed;
    }
    drop(state);
    inner.changed.notify_all();
}

fn restart_observation(inner: &Inner) {
    let mut state = lock(&inner.state);
    match state.mode {
        Mode::Observing | Mode::Running => {
            state.mode = Mode::Observing;
            reset_recovery(&mut state);
        }
        Mode::Paused => {
            reset_recovery(&mut state);
        }
        Mode::Failed | Mode::Shutdown => return,
    }
    drop(state);
    inner.changed.notify_all();
}

fn resume(state: &mut State) {
    state.mode = Mode::Running;
    state.low_since = None;
    state.completed_during_low = false;
    state.recovery_ready = false;
    state.last_completed_progress = None;
}

fn reset_recovery(state: &mut State) {
    state.low_since = None;
    state.completed_during_low = false;
    state.recovery_ready = false;
}

fn fail(inner: &Inner, message: String) {
    {
        let mut state = lock(&inner.state);
        if matches!(state.mode, Mode::Failed | Mode::Shutdown) {
            return;
        }
        state.failure = Some(message);
        state.mode = Mode::Failed;
    }
    inner.changed.notify_all();
}

fn state_error(state: &State) -> IoPressureError {
    IoPressureError::Control(
        state
            .failure
            .clone()
            .unwrap_or_else(|| "pressure controller stopped".to_owned()),
    )
}

fn read_some_total(path: &Path) -> Result<u64, String> {
    let mut last_error = None;
    for attempt in 0..PRESSURE_READ_ATTEMPTS {
        match fs::read_to_string(path)
            .map_err(|error| error.to_string())
            .and_then(|text| parse_some_total(&text))
        {
            Ok(total) => return Ok(total),
            Err(error) => last_error = Some(error),
        }
        if attempt + 1 != PRESSURE_READ_ATTEMPTS {
            thread::sleep(PRESSURE_READ_RETRY_DELAY);
        }
    }
    Err(last_error.unwrap_or_else(|| "pressure file could not be read".to_owned()))
}

fn parse_some_total(text: &str) -> Result<u64, String> {
    let some = text
        .lines()
        .find(|line| line.starts_with("some "))
        .ok_or_else(|| "missing `some` pressure record".to_owned())?;
    let total = some
        .split_ascii_whitespace()
        .find_map(|field| field.strip_prefix("total="))
        .ok_or_else(|| "missing `some total=` field".to_owned())?;
    total
        .parse()
        .map_err(|error| format!("invalid `some total=` value: {error}"))
}

fn current_cgroup_pressure_path() -> Result<PathBuf, IoPressureError> {
    let cgroup = fs::read_to_string("/proc/self/cgroup").map_err(|error| {
        IoPressureError::Control(format!("reading `/proc/self/cgroup`: {error}"))
    })?;
    let relative = cgroup
        .lines()
        .find_map(|line| line.strip_prefix("0::"))
        .ok_or_else(|| {
            IoPressureError::Control(
                "the sampler is not running in a unified cgroup v2 hierarchy".to_owned(),
            )
        })?;
    Ok(Path::new("/sys/fs/cgroup")
        .join(relative.trim_start_matches('/'))
        .join("io.pressure"))
}

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    mutex
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner)
}
