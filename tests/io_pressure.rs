use std::fs;
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

use oracle_mvp::io_pressure::{IoPressureController, ReadAdmission};

#[test]
fn pauses_new_reads_and_recovers_through_one_probe() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);

    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    let observation_started = Instant::now();
    let first = controller.wait_for_read().expect("initial read admission");
    assert_eq!(ReadAdmission::Normal, first.admission());
    assert!(
        observation_started.elapsed() >= Duration::from_millis(1_800),
        "disk reads must wait for the initial two-second observation"
    );
    first.complete().expect("complete initial read");

    write_pressure(&pressure_path, 1_000_000);
    thread::sleep(Duration::from_millis(500));

    let waiting = controller.clone();
    let (sender, receiver) = mpsc::channel();
    let waiter = thread::spawn(move || {
        let permit = waiting.wait_for_read().expect("recovery read admission");
        let admission = permit.admission();
        permit.complete().expect("complete recovery probe");
        sender.send(admission).expect("send recovery admission");
    });

    assert!(
        matches!(
            receiver.recv_timeout(Duration::from_secs(1)),
            Err(mpsc::RecvTimeoutError::Timeout)
        ),
        "high I/O pressure must block the next bounded read"
    );

    let recovery = receiver
        .recv_timeout(Duration::from_secs(14))
        .expect("one recovery probe after the low-pressure cooldown");
    assert_eq!(ReadAdmission::Probe, recovery);
    waiter.join().expect("join recovery waiter");

    let resumed = controller.wait_for_read().expect("normal read after probe");
    assert_eq!(ReadAdmission::Normal, resumed.admission());
    resumed.complete().expect("complete resumed read");
    controller.shutdown().expect("stop pressure monitor");
}

#[test]
fn unreadable_pressure_source_fails_closed_and_wakes_the_reader() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let missing = root.path().join("missing-io.pressure");
    let controller = IoPressureController::start(&missing).expect("start pressure controller");

    let error = match controller.wait_for_read() {
        Ok(_) => panic!("an unreadable pressure source must not admit disk reads"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("reading workload I/O pressure"));
    assert!(
        controller.shutdown().is_err(),
        "the terminal pressure failure must remain observable"
    );
}

#[test]
fn a_normal_read_completed_during_recovery_resumes_without_a_probe() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);

    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    let in_flight = controller.wait_for_read().expect("initial read admission");
    assert_eq!(ReadAdmission::Normal, in_flight.admission());

    write_pressure(&pressure_path, 1_000_000);
    thread::sleep(Duration::from_secs(3));
    in_flight
        .complete()
        .expect("complete admitted read during low-pressure recovery");

    let recovered = controller
        .wait_for_read()
        .expect("normal admission after durable recovery");
    assert_eq!(
        ReadAdmission::Normal,
        recovered.admission(),
        "a completed normal read during the cooldown must replace the recovery probe"
    );
    recovered.complete().expect("complete recovered read");
    controller.shutdown().expect("stop pressure monitor");
}

#[test]
fn moderate_pressure_during_a_probe_cancels_recovery() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);

    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    controller
        .wait_for_read()
        .expect("initial read admission")
        .complete()
        .expect("complete initial read");
    write_pressure(&pressure_path, 1_000_000);
    thread::sleep(Duration::from_millis(500));

    let probe = controller
        .wait_for_read()
        .expect("probe after low-pressure cooldown");
    assert_eq!(ReadAdmission::Probe, probe.admission());

    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let writer_stop = stop.clone();
    let writer_path = pressure_path.clone();
    let writer = thread::spawn(move || {
        let mut total = 1_000_000_u64;
        while !writer_stop.load(std::sync::atomic::Ordering::Relaxed) {
            total += 25_000;
            write_pressure(&writer_path, total);
            thread::sleep(Duration::from_millis(250));
        }
    });
    thread::sleep(Duration::from_secs(3));
    probe
        .complete()
        .expect("the bounded probe itself completed");

    let waiting = controller.clone();
    let (sender, receiver) = mpsc::channel();
    let waiter = thread::spawn(move || sender.send(waiting.wait_for_read()).expect("send result"));
    assert!(
        matches!(
            receiver.recv_timeout(Duration::from_secs(1)),
            Err(mpsc::RecvTimeoutError::Timeout)
        ),
        "pressure at or above five percent must prevent a probe from resuming reads"
    );

    stop.store(true, std::sync::atomic::Ordering::Relaxed);
    writer.join().expect("join pressure writer");
    controller.shutdown().expect("stop pressure monitor");
    assert!(
        receiver
            .recv_timeout(Duration::from_secs(1))
            .expect("shutdown wakes blocked reader")
            .is_err()
    );
    waiter.join().expect("join blocked reader");
}

#[test]
fn no_progress_timeout_stops_the_monitor_before_shutdown_joins_it() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);

    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    controller
        .wait_for_read()
        .expect("initial read admission")
        .complete()
        .expect("complete initial read");
    write_pressure(&pressure_path, 1_000_000);
    thread::sleep(Duration::from_millis(500));

    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let writer_stop = stop.clone();
    let writer_path = pressure_path.clone();
    let writer = thread::spawn(move || {
        let mut total = 1_000_000_u64;
        while !writer_stop.load(std::sync::atomic::Ordering::Relaxed) {
            total += 250_000;
            write_pressure(&writer_path, total);
            thread::sleep(Duration::from_millis(250));
        }
    });
    let error = match controller.wait_for_read() {
        Ok(_) => panic!("sustained pressure without progress must never admit another read"),
        Err(error) => error,
    };
    assert!(
        error
            .to_string()
            .contains("without a completed bounded read")
    );
    stop.store(true, std::sync::atomic::Ordering::Relaxed);
    writer.join().expect("join pressure writer");

    let shutdown_controller = controller.clone();
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        sender
            .send(shutdown_controller.shutdown())
            .expect("send shutdown result");
    });
    assert!(
        receiver
            .recv_timeout(Duration::from_secs(2))
            .expect("shutdown must not hang after terminal pressure failure")
            .is_err(),
        "the terminal failure must remain observable"
    );
}

fn write_pressure(path: &std::path::Path, some_total_microseconds: u64) {
    let temporary = path.with_extension("tmp");
    fs::write(
        &temporary,
        format!(
            "some avg10=0.00 avg60=0.00 avg300=0.00 total={some_total_microseconds}\n\
             full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        ),
    )
    .expect("write pressure sample");
    fs::rename(temporary, path).expect("publish pressure sample");
}
