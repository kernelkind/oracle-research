use std::fs::{self, File};
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::budget::MicroUsd;
use oracle_mvp::gte::TokenRole;
use oracle_mvp::gte_budget::{
    CALIBRATION_LIFETIME_CAP, CalibrationEvidencePaths, CalibrationExecutionIdentity,
    CalibrationRecorder, CalibrationRecorderConfig, FullBuildNonComputeCosts, MVP_LIFETIME_CAP,
    MonotonicCostGuard, VerifiedCalibrationEvidence, claim_calibration_execution,
    read_active_calibration_reservation, read_budget_ledger, reserve_calibration,
    reserve_full_build, settle_calibration, settle_failed_calibration,
    validate_calibration_selection,
};
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::representation::{
    RepresentationBuildConfig, RepresentationDescriptor, RepresentationEncoder,
    build_representation_shards, build_representation_shards_observed,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::snapshot::Result;
use sha2::{Digest, Sha256};
use tempfile::TempDir;

#[test]
fn checked_in_ledger_freezes_both_caps_and_zero_calibration_spend() {
    let ledger =
        read_budget_ledger(&Path::new(env!("CARGO_MANIFEST_DIR")).join("budget-ledger.json"))
            .expect("read checked-in budget ledger");

    assert_eq!(ledger.lifetime_cap, MVP_LIFETIME_CAP);
    assert_eq!(ledger.calibration_lifetime_cap, CALIBRATION_LIFETIME_CAP);
    assert_eq!(ledger.calibration_actual_spend, MicroUsd(0));
    assert_eq!(ledger.calibration_outstanding_commitments, MicroUsd(0));
}

#[test]
fn cli_reserves_calibration_before_any_paid_inputs_exist() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::MissingInputs,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );

    let output = run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]);
    assert_command_succeeded(&output);
    let admission: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("decode reservation admission");
    assert_eq!(
        admission["maximum_runtime_charge_micro_usd"],
        MicroUsd::from_dollars(8).0
    );
    let reserved = read_budget_ledger(&fixture.path).expect("read persisted reservation");
    assert_eq!(reserved.outstanding_commitments, MicroUsd::from_dollars(10));
    assert_eq!(
        reserved.calibration_outstanding_commitments,
        MicroUsd::from_dollars(10)
    );

    let reservation = ledger_entries(&fixture.path)
        .into_iter()
        .find(|entry| entry["kind"] == "calibration_reservation")
        .expect("calibration reservation entry");
    assert_eq!(
        reservation["requested_maximum_charge_micro_usd"],
        MicroUsd::from_dollars(10).0
    );
    assert_eq!(
        reservation["non_runtime_charge_reserve_micro_usd"],
        MicroUsd::from_dollars(2).0
    );

    let reserved_bytes = fs::read(&fixture.path).expect("read reserved ledger bytes");
    let duplicate = run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:01:00Z",
    ]);
    assert_command_failed_with(&duplicate, "already exists");
    assert_eq!(
        fs::read(&fixture.path).expect("read duplicate-rejected ledger"),
        reserved_bytes
    );
}

#[test]
fn cli_calibration_requires_an_existing_exact_reservation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    fixture.write_calibration_evidence();
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    let initial_ledger = fs::read(&fixture.path).expect("read initial ledger");

    let output = run_gte_oracle(&[
        "calibrate-shards",
        config_path.to_str().expect("UTF-8 config path"),
        "0",
    ]);
    assert_command_failed_with(&output, "does not exist");
    assert_eq!(
        fs::read(&fixture.path).expect("read rejected calibration ledger"),
        initial_ledger
    );
}

#[test]
fn cli_calibration_consumes_but_never_recreates_the_reservation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    fixture.write_calibration_evidence();
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    let reserve = run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]);
    assert_command_succeeded(&reserve);
    let reserved_ledger = fs::read(&fixture.path).expect("read reserved ledger");

    write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(3),
    );
    let mismatch = run_gte_oracle(&[
        "calibrate-shards",
        config_path.to_str().expect("UTF-8 config path"),
        "0",
    ]);
    assert_command_failed_with(&mismatch, "does not match");
    assert_eq!(
        fs::read(&fixture.path).expect("read mismatch-rejected ledger"),
        reserved_ledger
    );

    write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    let exact = run_gte_oracle(&[
        "calibrate-shards",
        config_path.to_str().expect("UTF-8 config path"),
        "0",
    ]);
    assert!(!exact.status.success());
    let stderr = String::from_utf8(exact.stderr).expect("UTF-8 stderr");
    assert!(!stderr.contains("already exists"), "{stderr}");
    assert!(!stderr.contains("does not match"), "{stderr}");
    assert!(!stderr.contains("does not exist"), "{stderr}");
    let claimed_ledger = fs::read(&fixture.path).expect("read claimed reservation ledger");
    assert_ne!(claimed_ledger, reserved_ledger, "{stderr}");
    assert!(
        ledger_entries(&fixture.path)
            .into_iter()
            .any(|entry| entry["kind"] == "calibration_execution_claim")
    );

    let duplicate = run_gte_oracle(&[
        "calibrate-shards",
        config_path.to_str().expect("UTF-8 config path"),
        "0",
    ]);
    assert_command_failed_with(&duplicate, "already claimed");
    assert_eq!(
        fs::read(&fixture.path).expect("read duplicate-execution ledger"),
        claimed_ledger
    );
}

#[test]
fn cli_success_settlement_verifies_evidence_and_releases_commitment() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::MissingInputs,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    assert_command_succeeded(&run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]));
    fixture.write_calibration_evidence();
    claim_calibration_via_cli(
        &fixture,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::CompletedCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );

    let settled = run_gte_oracle(&[
        "settle-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "3250000",
        "2026-07-17T13:00:00Z",
    ]);
    assert_command_succeeded(&settled);
    let ledger = read_budget_ledger(&fixture.path).expect("read settled ledger");
    assert_eq!(ledger.actual_spend, MicroUsd::from_cents(325));
    assert_eq!(ledger.outstanding_commitments, MicroUsd(0));
    assert_eq!(ledger.calibration_outstanding_commitments, MicroUsd(0));

    let settled_bytes = fs::read(&fixture.path).expect("read settled ledger bytes");
    let duplicate = run_gte_oracle(&[
        "settle-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "3250000",
        "2026-07-17T13:01:00Z",
    ]);
    assert_command_failed_with(&duplicate, "already settled");
    assert_eq!(
        fs::read(&fixture.path).expect("read duplicate settlement ledger"),
        settled_bytes
    );
}

#[test]
fn cli_settlement_rejects_mutated_evidence_without_ledger_mutation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::MissingInputs,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    assert_command_succeeded(&run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]));
    let calibration = fixture.write_calibration_evidence();
    claim_calibration_via_cli(
        &fixture,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::CompletedCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    fs::write(
        &calibration.paths.execution_identity_path,
        b"changed execution identity",
    )
    .expect("mutate execution identity");
    let reserved_ledger = fs::read(&fixture.path).expect("read reserved ledger");

    let output = run_gte_oracle(&[
        "settle-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "3250000",
        "2026-07-17T13:00:00Z",
    ]);
    assert_command_failed_with(&output, "execution identity");
    assert_eq!(
        fs::read(&fixture.path).expect("read verifier-rejected ledger"),
        reserved_ledger
    );
}

#[test]
fn cli_failed_settlement_records_provider_overrun() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::MissingInputs,
        MicroUsd::from_dollars(2),
        MicroUsd::from_cents(50),
    );
    assert_command_succeeded(&run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]));
    let failure_evidence_path = fixture.directory.path().join("provider-charge.txt");
    fs::write(&failure_evidence_path, b"provider charge after failed run")
        .expect("write failure evidence");

    let settled = run_gte_oracle(&[
        "settle-failed-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        failure_evidence_path
            .to_str()
            .expect("UTF-8 failure evidence path"),
        "26000000",
        "2026-07-17T13:00:00Z",
    ]);
    assert_command_succeeded(&settled);
    let ledger = read_budget_ledger(&fixture.path).expect("read failed-run settlement");
    assert_eq!(ledger.actual_spend, MicroUsd::from_dollars(26));
    assert_eq!(ledger.outstanding_commitments, MicroUsd(0));
    let entry = ledger_entries(&fixture.path)
        .into_iter()
        .find(|entry| entry["kind"] == "failed_calibration_settlement")
        .expect("failed calibration settlement entry");
    assert_eq!(
        entry["failure_evidence_sha256"],
        sha256_file(&failure_evidence_path)
    );

    let settled_bytes = fs::read(&fixture.path).expect("read failed settlement bytes");
    let duplicate = run_gte_oracle(&[
        "settle-failed-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        failure_evidence_path
            .to_str()
            .expect("UTF-8 failure evidence path"),
        "26000000",
        "2026-07-17T13:01:00Z",
    ]);
    assert_command_failed_with(&duplicate, "already settled");
    assert_eq!(
        fs::read(&fixture.path).expect("read duplicate failure settlement ledger"),
        settled_bytes
    );
}

#[test]
fn cli_full_build_projection_is_repeatable_and_read_only() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::MissingInputs,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    assert_command_succeeded(&run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]));
    fixture.write_calibration_evidence();
    claim_calibration_via_cli(
        &fixture,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::CompletedCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );
    assert_command_succeeded(&run_gte_oracle(&[
        "settle-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "3250000",
        "2026-07-17T13:00:00Z",
    ]));
    let non_compute_costs_path = fixture.directory.path().join("non-compute-costs.json");
    fs::write(
        &non_compute_costs_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "artifact_storage_and_transfer_micro_usd": 1_000_000_u64,
            "one_cold_restart_micro_usd": 1_000_000_u64,
            "one_lost_shard_micro_usd": 1_000_000_u64
        }))
        .expect("encode non-compute costs"),
    )
    .expect("write non-compute costs");
    let settled_ledger = fs::read(&fixture.path).expect("read settled ledger");

    let arguments = [
        "project-full-build",
        config_path.to_str().expect("UTF-8 config path"),
        non_compute_costs_path
            .to_str()
            .expect("UTF-8 non-compute costs path"),
    ];
    let first = run_gte_oracle(&arguments);
    assert_command_succeeded(&first);
    let second = run_gte_oracle(&arguments);
    assert_command_succeeded(&second);
    assert_eq!(first.stdout, second.stdout);
    let projection: serde_json::Value =
        serde_json::from_slice(&first.stdout).expect("decode projection output");
    let component_total = [
        "remaining_compute_micro_usd",
        "artifact_storage_and_transfer_micro_usd",
        "paid_lazy_inference_micro_usd",
        "one_cold_restart_micro_usd",
        "one_lost_shard_micro_usd",
    ]
    .into_iter()
    .map(|field| projection[field].as_u64().expect("projection component"))
    .sum::<u64>();
    assert_eq!(projection["total_micro_usd"], component_total);
    assert!(
        projection["projected_lifetime_total_micro_usd"]
            .as_u64()
            .expect("projected lifetime total")
            >= component_total
    );
    assert_eq!(
        fs::read(&fixture.path).expect("read projection-reviewed ledger"),
        settled_ledger
    );
}

#[test]
fn calibration_reservation_is_persisted_before_another_attempt_can_be_admitted() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);

    let admission = reserve_calibration(
        &fixture.path,
        "calibration-attempt-1",
        MicroUsd::from_dollars(20),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve the first bounded attempt");
    let reserved = read_budget_ledger(&fixture.path).expect("read persisted reservation");
    assert_eq!(reserved.outstanding_commitments, MicroUsd::from_dollars(20));
    assert_eq!(
        reserved.calibration_outstanding_commitments,
        MicroUsd::from_dollars(20)
    );
    assert_eq!(admission.ledger_sha256, reserved.ledger_sha256);

    let error = reserve_calibration(
        &fixture.path,
        "calibration-attempt-2",
        MicroUsd::from_dollars(6),
        "2026-07-16T20:01:00Z",
    )
    .expect_err("the second attempt must observe the first reservation");
    assert!(error.to_string().contains("$25"), "{error}");

    let error = reserve_calibration(
        &fixture.path,
        "calibration-attempt-1",
        MicroUsd::from_dollars(1),
        "2026-07-16T20:02:00Z",
    )
    .expect_err("one reservation identity cannot be reused");
    assert!(error.to_string().contains("already exists"), "{error}");

    let unchanged = read_budget_ledger(&fixture.path).expect("read rejected state");
    assert_eq!(unchanged.ledger_sha256, reserved.ledger_sha256);
}

#[test]
fn active_calibration_reservation_rejects_duplicate_authorization_entries() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "duplicated-calibration",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration");
    let mut ledger: serde_json::Value =
        serde_json::from_slice(&fs::read(&fixture.path).expect("read ledger"))
            .expect("decode ledger");
    let duplicate = ledger["entries"][0].clone();
    ledger["entries"]
        .as_array_mut()
        .expect("ledger entries")
        .push(duplicate);
    fs::write(
        &fixture.path,
        serde_json::to_vec_pretty(&ledger).expect("encode duplicated ledger"),
    )
    .expect("write duplicated ledger");

    let error = read_active_calibration_reservation(
        &fixture.path,
        "duplicated-calibration",
        MicroUsd::from_dollars(10),
        MicroUsd(0),
    )
    .expect_err("duplicate authorization entries must fail closed");
    assert!(error.to_string().contains("duplicate"), "{error}");
}

#[test]
fn calibration_reservation_enforces_the_lifetime_cap_and_rounds_up_to_cents() {
    let fixture = LedgerFixture::new(49_000, 500, 0, 0);
    let error = reserve_calibration(
        &fixture.path,
        "too-expensive",
        MicroUsd::from_dollars(6),
        "2026-07-16T20:00:00Z",
    )
    .expect_err("a calibration reservation cannot exceed the lifetime MVP cap");
    assert!(error.to_string().contains("$500"), "{error}");

    let rounding_fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &rounding_fixture.path,
        "rounded-reservation",
        MicroUsd(1),
        "2026-07-16T20:00:00Z",
    )
    .expect("sub-cent maximum is reserved conservatively");
    let ledger = read_budget_ledger(&rounding_fixture.path).expect("read rounded reservation");
    assert_eq!(ledger.outstanding_commitments, MicroUsd::from_cents(1));
    assert_eq!(
        ledger.calibration_outstanding_commitments,
        MicroUsd::from_cents(1)
    );
}

#[test]
fn calibration_settlement_atomically_records_actual_spend_and_releases_the_commitment() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "completed-calibration",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration before rented work");
    claim_calibration_execution(
        &fixture.path,
        "completed-calibration",
        MicroUsd::from_dollars(10),
        MicroUsd(0),
    )
    .expect("claim calibration before successful settlement");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify completed calibration evidence");

    let settled = settle_calibration(
        &fixture.path,
        "completed-calibration",
        &evidence,
        MicroUsd::from_cents(325),
        "2026-07-16T20:30:00Z",
    )
    .expect("atomically settle actual provider charge");
    assert_eq!(settled.actual_spend, MicroUsd::from_cents(325));
    assert_eq!(settled.calibration_actual_spend, MicroUsd::from_cents(325));
    assert_eq!(settled.outstanding_commitments, MicroUsd(0));
    assert_eq!(settled.calibration_outstanding_commitments, MicroUsd(0));

    let error = settle_calibration(
        &fixture.path,
        "completed-calibration",
        &evidence,
        MicroUsd::from_cents(325),
        "2026-07-16T20:31:00Z",
    )
    .expect_err("one reservation cannot be settled twice");
    assert!(error.to_string().contains("already settled"), "{error}");

    reserve_full_build(
        &fixture.path,
        "full-build-after-settlement",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(1),
            paid_lazy_inference: MicroUsd(0),
            one_cold_restart: MicroUsd::from_dollars(1),
            one_lost_shard: MicroUsd::from_dollars(1),
        },
        "2026-07-16T20:32:00Z",
    )
    .expect("settlement makes the full-build budget review reachable");
}

#[test]
fn successful_calibration_settlement_requires_the_execution_claim() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "unclaimed-calibration",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration before rented work");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify completed calibration evidence");

    let error = settle_calibration(
        &fixture.path,
        "unclaimed-calibration",
        &evidence,
        MicroUsd::from_cents(325),
        "2026-07-16T20:30:00Z",
    )
    .expect_err("successful evidence must not settle from an unclaimed ledger");
    assert!(error.to_string().contains("execution claim"), "{error}");
}

#[test]
fn calibration_evidence_can_only_settle_the_reservation_that_paid_for_it() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "calibration-a",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve the calibration that will produce the evidence");
    claim_calibration_execution(
        &fixture.path,
        "calibration-a",
        MicroUsd::from_dollars(10),
        MicroUsd(0),
    )
    .expect("claim the calibration that produced the evidence");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify reservation-bound evidence");
    reserve_calibration(
        &fixture.path,
        "calibration-b",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:01:00Z",
    )
    .expect("reserve an independent calibration");

    let error = settle_calibration(
        &fixture.path,
        "calibration-b",
        &evidence,
        MicroUsd::from_dollars(1),
        "2026-07-16T20:30:00Z",
    )
    .expect_err("evidence from calibration A cannot settle calibration B");
    assert!(error.to_string().contains("bound"), "{error}");

    settle_calibration(
        &fixture.path,
        "calibration-a",
        &evidence,
        MicroUsd::from_dollars(1),
        "2026-07-16T20:31:00Z",
    )
    .expect("the evidence settles its own reservation");
}

#[test]
fn calibration_evidence_binds_the_complete_authorization_record() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "exact-authorization",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify reservation-bound evidence");

    let mut ledger: serde_json::Value =
        serde_json::from_slice(&fs::read(&fixture.path).expect("read ledger"))
            .expect("decode ledger");
    ledger["entries"][0]["requested_maximum_charge_micro_usd"] = serde_json::json!(9_999_999_u64);
    fs::write(
        &fixture.path,
        serde_json::to_vec_pretty(&ledger).expect("encode changed ledger"),
    )
    .expect("change the authorization record without changing its rounded cap");

    let error = settle_calibration(
        &fixture.path,
        "exact-authorization",
        &evidence,
        MicroUsd::from_dollars(1),
        "2026-07-16T20:30:00Z",
    )
    .expect_err("evidence cannot settle a different authorization record");
    assert!(error.to_string().contains("authorization"), "{error}");
}

#[test]
fn calibration_settlement_rejects_actual_cost_above_its_reservation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "bounded-calibration",
        MicroUsd::from_dollars(2),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration");
    claim_calibration_execution(
        &fixture.path,
        "bounded-calibration",
        MicroUsd::from_dollars(2),
        MicroUsd(0),
    )
    .expect("claim calibration");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify completed calibration evidence");
    let before = read_budget_ledger(&fixture.path).expect("read reserved ledger");

    let error = settle_calibration(
        &fixture.path,
        "bounded-calibration",
        &evidence,
        MicroUsd::from_cents(201),
        "2026-07-16T20:30:00Z",
    )
    .expect_err("actual cost cannot exceed the pre-work reservation");
    assert!(error.to_string().contains("exceeds"), "{error}");
    assert_eq!(
        read_budget_ledger(&fixture.path)
            .expect("read unchanged ledger")
            .ledger_sha256,
        before.ledger_sha256
    );
}

#[test]
fn failed_calibration_is_reconciled_without_unlocking_a_full_build() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "failed-calibration",
        MicroUsd::from_dollars(10),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration");
    let failure_evidence = fixture.directory.path().join("provider-failure.txt");
    fs::write(&failure_evidence, b"provider instance terminated\n")
        .expect("write provider failure evidence");

    let settled = settle_failed_calibration(
        &fixture.path,
        "failed-calibration",
        &failure_evidence,
        MicroUsd::from_cents(325),
        "2026-07-16T20:30:00Z",
    )
    .expect("reconcile failed attempt");

    assert_eq!(settled.actual_spend, MicroUsd::from_cents(325));
    assert_eq!(settled.calibration_actual_spend, MicroUsd::from_cents(325));
    assert_eq!(settled.outstanding_commitments, MicroUsd(0));
    assert_eq!(settled.calibration_outstanding_commitments, MicroUsd(0));
    assert!(
        fs::read_to_string(&fixture.path)
            .expect("read ledger")
            .contains("failed_calibration_settlement")
    );
}

#[test]
fn failed_calibration_records_the_provider_charge_even_if_teardown_overruns() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "overrun-calibration",
        MicroUsd::from_dollars(2),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve calibration");
    let failure_evidence = fixture.directory.path().join("provider-overrun.txt");
    fs::write(
        &failure_evidence,
        b"provider teardown exceeded the reservation\n",
    )
    .expect("write provider failure evidence");

    let settled = settle_failed_calibration(
        &fixture.path,
        "overrun-calibration",
        &failure_evidence,
        MicroUsd::from_dollars(26),
        "2026-07-16T20:30:00Z",
    )
    .expect("the ledger must record the provider's actual charge");

    assert_eq!(settled.actual_spend, MicroUsd::from_dollars(26));
    assert_eq!(settled.outstanding_commitments, MicroUsd(0));
}

#[test]
fn full_build_requires_the_exact_calibration_evidence_to_be_settled() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify calibration evidence");

    let error = reserve_full_build(
        &fixture.path,
        "unaccounted-full-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(1),
            paid_lazy_inference: MicroUsd(0),
            one_cold_restart: MicroUsd::from_dollars(1),
            one_lost_shard: MicroUsd::from_dollars(1),
        },
        "2026-07-16T20:32:00Z",
    )
    .expect_err("unsettled calibration evidence cannot unlock full-build review");
    assert!(error.to_string().contains("settled"), "{error}");
}

#[test]
fn concurrent_calibration_reservations_cannot_reuse_one_ledger_state() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let barrier = Arc::new(Barrier::new(2));
    let attempts = ["concurrent-1", "concurrent-2"]
        .into_iter()
        .map(|reservation_id| {
            let path = fixture.path.clone();
            let barrier = barrier.clone();
            thread::spawn(move || {
                barrier.wait();
                reserve_calibration(
                    &path,
                    reservation_id,
                    MicroUsd::from_dollars(20),
                    "2026-07-16T20:00:00Z",
                )
            })
        })
        .collect::<Vec<_>>();
    let results = attempts
        .into_iter()
        .map(|attempt| attempt.join().expect("reservation thread"))
        .collect::<Vec<_>>();

    assert_eq!(results.iter().filter(|result| result.is_ok()).count(), 1);
    assert_eq!(results.iter().filter(|result| result.is_err()).count(), 1);
    assert_eq!(
        read_budget_ledger(&fixture.path)
            .expect("read one winning reservation")
            .outstanding_commitments,
        MicroUsd::from_dollars(20)
    );
}

#[test]
fn calibration_evidence_must_be_a_verified_file_and_drives_compute_projection() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "measured-calibration",
        MicroUsd::from_dollars(20),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve measured calibration");
    claim_calibration_execution(
        &fixture.path,
        "measured-calibration",
        MicroUsd::from_dollars(20),
        MicroUsd(0),
    )
    .expect("claim measured calibration");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("open plan-bound calibration evidence");
    assert_eq!(evidence.measured_batches(), 2);
    assert_eq!(evidence.measured_rows(), 4);
    assert_eq!(evidence.elapsed(), Duration::from_secs(16));

    let missing = VerifiedCalibrationEvidence::open(
        &fixture.directory.path().join("missing.json"),
        &calibration.paths,
    )
    .expect_err("an in-memory assertion cannot replace an evidence artifact");
    assert!(missing.to_string().contains("read"), "{missing}");

    fs::write(
        calibration.paths.execution_identity_path.as_path(),
        b"tampered execution identity",
    )
    .expect("tamper referenced execution identity");
    let error = reserve_full_build(
        &fixture.path,
        "changed-evidence",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(10),
            paid_lazy_inference: MicroUsd::from_dollars(5),
            one_cold_restart: MicroUsd::from_dollars(20),
            one_lost_shard: MicroUsd::from_dollars(15),
        },
        "2026-07-16T20:59:00Z",
    )
    .expect_err("referenced evidence must still match when the budget is reserved");
    assert!(error.to_string().contains("changed"), "{error}");
    calibration.restore_execution_identity();
    settle_calibration(
        &fixture.path,
        "measured-calibration",
        &evidence,
        MicroUsd::from_dollars(20),
        "2026-07-16T20:59:30Z",
    )
    .expect("settle the exact evidence before full-build review");

    let admission = reserve_full_build(
        &fixture.path,
        "complete-gte-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(10),
            paid_lazy_inference: MicroUsd::from_dollars(5),
            one_cold_restart: MicroUsd::from_dollars(20),
            one_lost_shard: MicroUsd::from_dollars(15),
        },
        "2026-07-16T21:00:00Z",
    )
    .expect("reserve the evidence-derived complete build");

    // The verified plan has two batches of each exact shape. Shard 0 measured
    // one 2x2 batch at 1 second and one 2x4 batch at 2 seconds. The completed
    // shard is reusable. The approved range conservatively applies its slower
    // 2-second measured batch to both remaining batches: 4 seconds. The one
    // remaining shard setup adds 1 second, its checkpoint adds 3 seconds, and
    // final verification scales from 4 seconds over half the rows to 8
    // seconds. A fresh full-build rental also repeats the measured 5-second
    // cold start: 21 seconds total. At the execution identity's $360/hour
    // rate that costs $2.10.
    assert_eq!(
        admission.projection.remaining_compute(),
        MicroUsd::from_cents(210)
    );
    assert_eq!(
        admission.projected_lifetime_total,
        MicroUsd::from_cents(7_210)
    );
    assert_eq!(
        read_budget_ledger(&fixture.path)
            .expect("read full-build reservation")
            .outstanding_commitments,
        MicroUsd::from_cents(5_210)
    );

    let error = reserve_full_build(
        &fixture.path,
        "another-complete-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(1),
            paid_lazy_inference: MicroUsd(0),
            one_cold_restart: MicroUsd::from_dollars(1),
            one_lost_shard: MicroUsd::from_dollars(1),
        },
        "2026-07-16T21:01:00Z",
    )
    .expect_err("the one complete build cannot be reserved twice");
    assert!(error.to_string().contains("already exists"), "{error}");
}

#[test]
fn full_build_rejects_an_evidence_derived_projection_over_the_lifetime_cap() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "expensive-calibration",
        MicroUsd::from_dollars(20),
        "2026-07-16T20:00:00Z",
    )
    .expect("reserve expensive calibration");
    claim_calibration_execution(
        &fixture.path,
        "expensive-calibration",
        MicroUsd::from_dollars(20),
        MicroUsd(0),
    )
    .expect("claim expensive calibration");
    let calibration = fixture.write_calibration_evidence_with_rate(MicroUsd::from_dollars(600_000));
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("open calibration evidence");
    settle_calibration(
        &fixture.path,
        "expensive-calibration",
        &evidence,
        MicroUsd::from_dollars(20),
        "2026-07-16T20:59:30Z",
    )
    .expect("settle expensive calibration");
    let error = reserve_full_build(
        &fixture.path,
        "too-expensive-complete-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd::from_dollars(10),
            paid_lazy_inference: MicroUsd::from_dollars(5),
            one_cold_restart: MicroUsd::from_dollars(20),
            one_lost_shard: MicroUsd::from_dollars(15),
        },
        "2026-07-16T21:00:00Z",
    )
    .expect_err("the measured projection exceeds $500");
    assert!(error.to_string().contains("$500"), "{error}");
    assert_eq!(
        read_budget_ledger(&fixture.path)
            .expect("read unchanged ledger")
            .outstanding_commitments,
        MicroUsd(0)
    );
}

#[test]
fn full_build_projection_includes_checkpoint_finalization_and_failure_overhead() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "overhead-calibration",
        MicroUsd::from_dollars(25),
        "2026-07-16T01:00:00Z",
    )
    .expect("reserve calibration");
    claim_calibration_execution(
        &fixture.path,
        "overhead-calibration",
        MicroUsd::from_dollars(25),
        MicroUsd(0),
    )
    .expect("claim calibration");
    let calibration = fixture.write_calibration_evidence_with_rate(MicroUsd::from_dollars(360));
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify complete-pipeline evidence");
    settle_calibration(
        &fixture.path,
        "overhead-calibration",
        &evidence,
        MicroUsd::from_dollars(1),
        "2026-07-16T02:00:00Z",
    )
    .expect("settle calibration");

    let admission = reserve_full_build(
        &fixture.path,
        "overhead-full-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd(0),
            paid_lazy_inference: MicroUsd(0),
            one_cold_restart: MicroUsd(1),
            one_lost_shard: MicroUsd(1),
        },
        "2026-07-16T03:00:00Z",
    )
    .expect("admit projection with measured overhead");
    assert_eq!(
        admission.projection.remaining_compute(),
        MicroUsd(2_100_000)
    );
    assert_eq!(admission.projection.one_cold_restart(), MicroUsd(1_300_000));
    assert_eq!(admission.projection.one_lost_shard(), MicroUsd(800_000));
}

#[test]
fn cold_restart_reserve_includes_discovering_the_existing_representation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "restart-discovery-calibration",
        MicroUsd::from_dollars(25),
        "2026-07-16T01:00:00Z",
    )
    .expect("reserve calibration");
    claim_calibration_execution(
        &fixture.path,
        "restart-discovery-calibration",
        MicroUsd::from_dollars(25),
        MicroUsd(0),
    )
    .expect("claim calibration");
    let calibration = fixture.write_calibration_evidence_with_rate(MicroUsd::from_dollars(360));
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify complete-pipeline evidence");
    settle_calibration(
        &fixture.path,
        "restart-discovery-calibration",
        &evidence,
        MicroUsd::from_dollars(1),
        "2026-07-16T02:00:00Z",
    )
    .expect("settle calibration");

    let admission = reserve_full_build(
        &fixture.path,
        "restart-discovery-full-build",
        &evidence,
        FullBuildNonComputeCosts {
            artifact_storage_and_transfer: MicroUsd(0),
            paid_lazy_inference: MicroUsd(0),
            one_cold_restart: MicroUsd(1),
            one_lost_shard: MicroUsd(1),
        },
        "2026-07-16T03:00:00Z",
    )
    .expect("admit projection with restart discovery");

    // The measured 5-second model startup plus the conservatively projected
    // 8-second full-artifact finalization bounds one restart and shard scan.
    assert_eq!(admission.projection.one_cold_restart(), MicroUsd(1_300_000));
    assert_eq!(
        admission.projection.remaining_compute(),
        MicroUsd(2_100_000)
    );
}

#[test]
fn production_observer_atomically_writes_verifiable_calibration_evidence() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let admission = reserve_calibration(
        &fixture.path,
        "observed-calibration",
        MicroUsd::from_dollars(25),
        "2026-07-16T00:00:00Z",
    )
    .expect("reserve observed calibration");
    let calibration = fixture.write_calibration_evidence();
    let representation_path = fixture.directory.path().join("observed-representation");
    let evidence_path = fixture.directory.path().join("observed-evidence.json");
    let paths = CalibrationEvidencePaths {
        representation_path: representation_path.clone(),
        ..calibration.paths.clone()
    };
    let mut recorder = CalibrationRecorder::new(CalibrationRecorderConfig {
        rental_started_at: Instant::now() - Duration::from_secs(1),
        rental_rate_per_hour: MicroUsd::from_dollars(360),
        maximum_charge: MicroUsd::from_dollars(25),
        maximum_work_unit: Duration::from_secs(60),
        reservation: admission.evidence_binding(),
    })
    .expect("create guarded recorder");
    let mut encoder = FixtureEncoder {
        descriptor: fixture_descriptor(),
    };

    build_representation_shards_observed(
        fixture.directory.path().join("english.ndb"),
        &paths.ordered_event_ids_path,
        &representation_path,
        &RepresentationBuildConfig {
            token_audit_path: paths.token_audit_path.clone(),
            batch_plan_path: paths.batch_plan_path.clone(),
            shard_ordinals: vec![0],
        },
        &mut encoder,
        &mut recorder,
    )
    .expect("run measured production build");
    let evidence = recorder
        .publish(&evidence_path, &paths, vec![4])
        .expect("publish and verify measured evidence");

    assert!(evidence_path.is_file());
    assert_eq!(evidence.measured_batches(), 2);
    assert_eq!(evidence.measured_rows(), 4);
}

#[test]
fn evidence_publication_reserves_one_more_bounded_work_unit() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let admission = reserve_calibration(
        &fixture.path,
        "publication-guard-calibration",
        MicroUsd::from_dollars(25),
        "2026-07-16T00:00:00Z",
    )
    .expect("reserve calibration");
    let calibration = fixture.write_calibration_evidence();
    let representation_path = fixture.directory.path().join("guarded-representation");
    let evidence_path = fixture.directory.path().join("guarded-evidence.json");
    let paths = CalibrationEvidencePaths {
        representation_path: representation_path.clone(),
        ..calibration.paths.clone()
    };
    let rental_started_at = Instant::now();
    let mut recorder = CalibrationRecorder::new(CalibrationRecorderConfig {
        rental_started_at,
        rental_rate_per_hour: MicroUsd::from_dollars(3_600),
        maximum_charge: MicroUsd::from_dollars(1),
        maximum_work_unit: Duration::from_millis(500),
        reservation: admission.evidence_binding(),
    })
    .expect("create guarded recorder");
    let mut encoder = FixtureEncoder {
        descriptor: fixture_descriptor(),
    };
    build_representation_shards_observed(
        fixture.directory.path().join("english.ndb"),
        &paths.ordered_event_ids_path,
        &representation_path,
        &RepresentationBuildConfig {
            token_audit_path: paths.token_audit_path.clone(),
            batch_plan_path: paths.batch_plan_path.clone(),
            shard_ordinals: vec![0],
        },
        &mut encoder,
        &mut recorder,
    )
    .expect("run measured production build");
    let reserve_must_fail_at = rental_started_at + Duration::from_millis(600);
    thread::sleep(reserve_must_fail_at.saturating_duration_since(Instant::now()));

    let error = recorder
        .publish(&evidence_path, &paths, vec![4])
        .expect_err("publication must reserve another bounded work unit");
    assert!(error.to_string().contains("cost cap exceeded"), "{error}");
    assert!(!evidence_path.exists());
}

#[test]
fn calibration_evidence_remains_verifiable_after_the_representation_grows() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    reserve_calibration(
        &fixture.path,
        "growing-representation-calibration",
        MicroUsd::from_dollars(25),
        "2026-07-16T00:00:00Z",
    )
    .expect("reserve calibration");
    claim_calibration_execution(
        &fixture.path,
        "growing-representation-calibration",
        MicroUsd::from_dollars(25),
        MicroUsd(0),
    )
    .expect("claim calibration");
    let calibration = fixture.write_calibration_evidence();
    let evidence =
        VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
            .expect("verify evidence against its calibration shard");

    let mut encoder = FixtureEncoder {
        descriptor: fixture_descriptor(),
    };
    build_representation_shards(
        fixture.directory.path().join("english.ndb"),
        &calibration.paths.ordered_event_ids_path,
        &calibration.paths.representation_path,
        &RepresentationBuildConfig {
            token_audit_path: calibration.paths.token_audit_path.clone(),
            batch_plan_path: calibration.paths.batch_plan_path.clone(),
            shard_ordinals: vec![1],
        },
        &mut encoder,
    )
    .expect("extend the same production representation with another shard");

    VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect("later shards must not invalidate immutable calibration evidence");
    settle_calibration(
        &fixture.path,
        "growing-representation-calibration",
        &evidence,
        MicroUsd::from_dollars(20),
        "2026-07-16T00:01:00Z",
    )
    .expect("the originally opened evidence remains valid for settlement");
}

#[test]
fn calibration_evidence_still_binds_the_exact_calibration_shard() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut document: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    document["calibration_shards"][0]["vectors"]["sha256"] = serde_json::json!("0".repeat(64));
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&document).expect("encode changed shard identity"),
    )
    .expect("write changed shard identity");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("evidence cannot name different calibration vector bytes");
    assert!(
        error.to_string().contains("changed or is missing"),
        "{error}"
    );
}

#[test]
fn calibration_evidence_rejects_duplicate_or_non_reusable_batch_addresses() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut document: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    let first = document["batches"][0].clone();
    document["batches"]
        .as_array_mut()
        .expect("batch array")
        .push(first);
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&document).expect("encode duplicate evidence"),
    )
    .expect("write duplicate evidence");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("one production batch address cannot be measured twice");
    assert!(error.to_string().contains("duplicate"), "{error}");

    calibration.restore_evidence();
    let mut document: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    document["batches"]
        .as_array_mut()
        .expect("batch array")
        .pop();
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&document).expect("encode partial-shard evidence"),
    )
    .expect("write partial-shard evidence");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("partial temporary shard work is not reusable production evidence");
    assert!(error.to_string().contains("every batch"), "{error}");
}

#[test]
fn calibration_projection_refuses_an_unmeasured_approved_range() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence_with_unique_second_shard_shape();
    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("an approved range needs a measured batch that upper-bounds its planned work");
    assert!(error.to_string().contains("upper-bounds"), "{error}");
}

#[test]
fn calibration_selection_is_proved_from_the_plan_before_paid_work() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();

    validate_calibration_selection(
        &calibration.paths.ordered_event_ids_path,
        &calibration.paths.token_audit_path,
        &calibration.paths.batch_plan_path,
        &[0],
        &[4],
    )
    .expect("one full production shard covers the approved range");

    let error = validate_calibration_selection(
        &calibration.paths.ordered_event_ids_path,
        &calibration.paths.token_audit_path,
        &calibration.paths.batch_plan_path,
        &[0],
        &[2, 4],
    )
    .expect_err("one measured batch per range is not several production batches");
    assert!(error.to_string().contains("requires several"), "{error}");

    let different_shape_fixture = LedgerFixture::new(0, 0, 0, 0);
    let different_shape =
        different_shape_fixture.write_calibration_evidence_with_unique_second_shard_shape();
    let error = validate_calibration_selection(
        &different_shape.paths.ordered_event_ids_path,
        &different_shape.paths.token_audit_path,
        &different_shape.paths.batch_plan_path,
        &[0],
        &[34],
    )
    .expect_err("selected batches must upper-bound every unmeasured shape in their range");
    assert!(error.to_string().contains("upper-bounds"), "{error}");
}

#[test]
fn cli_selection_preflight_binds_the_configured_ranges_and_active_reservation() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let _calibration = fixture.write_calibration_evidence();
    let config_path = write_calibration_cli_config(
        &fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    );

    let validate = || {
        run_gte_oracle(&[
            "validate-calibration-selection",
            config_path.to_str().expect("UTF-8 config path"),
            "0",
            "4",
        ])
    };
    assert_command_failed_with(&validate(), "does not exist");

    assert_command_succeeded(&run_gte_oracle(&[
        "reserve-calibration",
        config_path.to_str().expect("UTF-8 config path"),
        "2026-07-17T12:00:00Z",
    ]));
    assert_command_succeeded(&validate());

    let mut config: serde_json::Value =
        serde_json::from_slice(&fs::read(&config_path).expect("read config"))
            .expect("decode config");
    config["calibration"]["token_range_upper_bounds"] = serde_json::json!([5]);
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode changed config"),
    )
    .expect("write changed config");
    assert_command_failed_with(&validate(), "configured token ranges");

    config["calibration"]["token_range_upper_bounds"] = serde_json::json!([4]);
    config["container_image"] = serde_json::json!("kernelkind/oracle-mvp:mutable");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode mutable-image config"),
    )
    .expect("write mutable-image config");
    assert_command_failed_with(&validate(), "immutable digest");

    config["container_image"] =
        serde_json::json!(format!("kernelkind/oracle-mvp@sha256:{}", "5".repeat(64)));
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode mismatched-worker config"),
    )
    .expect("write mismatched-worker config");
    let launched_model_lock = PathBuf::from(
        config["worker"]["model_lock_path"]
            .as_str()
            .expect("worker model lock path"),
    );
    fs::write(launched_model_lock, b"different lock").expect("change launched model lock");
    assert_command_failed_with(&validate(), "descriptor-bound inputs");

    fs::write(
        PathBuf::from(
            config["worker"]["model_lock_path"]
                .as_str()
                .expect("worker model lock path"),
        ),
        b"fixture",
    )
    .expect("restore launched model lock");
    let approved_model_dir = config["worker"]["model_dir"].clone();
    let wrong_model_dir = fixture.directory.path().join("wrong-model");
    fs::create_dir(&wrong_model_dir).expect("create wrong model directory");
    config["worker"]["model_dir"] = serde_json::json!(wrong_model_dir);
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode wrong-model config"),
    )
    .expect("write wrong-model config");
    assert_command_failed_with(&validate(), "model directory");

    config["worker"]["model_dir"] = approved_model_dir;
    config["cuda_version"] = serde_json::json!("wrong");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode wrong-runtime config"),
    )
    .expect("write wrong-runtime config");
    assert_command_failed_with(&validate(), "runtime identity");

    config["cuda_version"] = serde_json::json!("13.0.2");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode restored config"),
    )
    .expect("write restored config");
    claim_calibration_execution(
        &fixture.path,
        "cli-calibration",
        MicroUsd::from_dollars(10),
        MicroUsd::from_dollars(2),
    )
    .expect("claim the calibration once");
    assert_command_failed_with(&validate(), "already claimed");
}

#[test]
fn calibration_rejects_a_nonapproved_gpu_model() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence_with_gpu_model("NVIDIA H100 80GB HBM3");
    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("only the frozen RTX PRO 6000 WS hardware may provide calibration evidence");
    assert!(error.to_string().contains("approved hardware"), "{error}");
}

#[test]
fn calibration_requires_the_frozen_600_watt_power_limit() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut identity: serde_json::Value = serde_json::from_slice(
        &fs::read(&calibration.paths.execution_identity_path).expect("read execution identity"),
    )
    .expect("decode execution identity");
    identity["gpu_power_limit_watts"] = serde_json::json!(601_u32);
    fs::write(
        &calibration.paths.execution_identity_path,
        serde_json::to_vec_pretty(&identity).expect("encode execution identity"),
    )
    .expect("write changed execution identity");
    let mut evidence: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    evidence["execution_identity_sha256"] =
        serde_json::json!(sha256_file(&calibration.paths.execution_identity_path));
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&evidence).expect("encode evidence"),
    )
    .expect("write evidence for changed execution identity");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("the calibration hardware contract requires exactly 600 watts");
    assert!(error.to_string().contains("hardware contract"), "{error}");
}

#[test]
fn calibration_accepts_a_newer_two_component_driver_version() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut identity: serde_json::Value = serde_json::from_slice(
        &fs::read(&calibration.paths.execution_identity_path).expect("read execution identity"),
    )
    .expect("decode execution identity");
    identity["driver_version"] = serde_json::json!("595.84");
    fs::write(
        &calibration.paths.execution_identity_path,
        serde_json::to_vec_pretty(&identity).expect("encode execution identity"),
    )
    .expect("write changed execution identity");
    let mut evidence: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    evidence["execution_identity_sha256"] =
        serde_json::json!(sha256_file(&calibration.paths.execution_identity_path));
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&evidence).expect("encode evidence"),
    )
    .expect("write evidence for changed execution identity");

    VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect("a newer two-component NVIDIA driver satisfies the minimum");
}

#[test]
fn calibration_rejects_a_blank_rental_instance_id() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut identity: serde_json::Value = serde_json::from_slice(
        &fs::read(&calibration.paths.execution_identity_path).expect("read execution identity"),
    )
    .expect("decode execution identity");
    identity["rental_instance_id"] = serde_json::json!("  ");
    fs::write(
        &calibration.paths.execution_identity_path,
        serde_json::to_vec_pretty(&identity).expect("encode execution identity"),
    )
    .expect("write changed execution identity");
    let mut evidence: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    evidence["execution_identity_sha256"] =
        serde_json::json!(sha256_file(&calibration.paths.execution_identity_path));
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&evidence).expect("encode evidence"),
    )
    .expect("write evidence for changed execution identity");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("the instance that incurred the charge must be identified");
    assert!(error.to_string().contains("hardware contract"), "{error}");
}

#[test]
fn calibration_requires_at_least_one_day_of_offer_availability() {
    let fixture = LedgerFixture::new(0, 0, 0, 0);
    let calibration = fixture.write_calibration_evidence();
    let mut identity: serde_json::Value = serde_json::from_slice(
        &fs::read(&calibration.paths.execution_identity_path).expect("read execution identity"),
    )
    .expect("decode execution identity");
    identity["available_duration_seconds"] = serde_json::json!(86_399_u64);
    fs::write(
        &calibration.paths.execution_identity_path,
        serde_json::to_vec_pretty(&identity).expect("encode execution identity"),
    )
    .expect("write changed execution identity");
    let mut evidence: serde_json::Value =
        serde_json::from_slice(&fs::read(&calibration.evidence_path).expect("read evidence"))
            .expect("decode evidence");
    evidence["execution_identity_sha256"] =
        serde_json::json!(sha256_file(&calibration.paths.execution_identity_path));
    fs::write(
        &calibration.evidence_path,
        serde_json::to_vec_pretty(&evidence).expect("encode evidence"),
    )
    .expect("write evidence for changed execution identity");

    let error = VerifiedCalibrationEvidence::open(&calibration.evidence_path, &calibration.paths)
        .expect_err("the selected offer must remain available for at least one day");
    assert!(error.to_string().contains("hardware contract"), "{error}");
}

#[test]
fn monotonic_guard_reserves_the_next_observed_interval_before_work() {
    let started_at = Instant::now();
    let guard = MonotonicCostGuard::new(started_at, MicroUsd::from_cents(360), MicroUsd(1_000))
        .expect("valid guard");

    let observation = guard
        .check_at(started_at + Duration::from_secs(1), Duration::ZERO)
        .expect("one second at $3.60/hour costs exactly 1,000 micro-USD");
    assert_eq!(observation.projected_charge, MicroUsd(1_000));

    let error = guard
        .check_at(started_at + Duration::from_secs(1), Duration::from_nanos(1))
        .expect_err("the observer must stop before starting work beyond the reservation");
    assert!(
        error.to_string().contains("elapsed-time cost cap"),
        "{error}"
    );
}

#[derive(Clone, Copy)]
enum CalibrationCliConfigState {
    MissingInputs,
    FreshCalibrationOutput,
    CompletedCalibrationOutput,
}

fn claim_calibration_via_cli(
    fixture: &LedgerFixture,
    maximum_total_charge: MicroUsd,
    non_runtime_charge_reserve: MicroUsd,
) {
    let config_path = write_calibration_cli_config(
        fixture,
        CalibrationCliConfigState::FreshCalibrationOutput,
        maximum_total_charge,
        non_runtime_charge_reserve,
    );
    let output = run_gte_oracle(&[
        "calibrate-shards",
        config_path.to_str().expect("UTF-8 config path"),
        "0",
    ]);
    assert!(!output.status.success(), "fixture worker must stop the run");
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(!stderr.contains("execution claim"), "{stderr}");
    assert!(
        ledger_entries(&fixture.path)
            .into_iter()
            .any(|entry| entry["kind"] == "calibration_execution_claim")
    );
}

fn write_calibration_cli_config(
    fixture: &LedgerFixture,
    state: CalibrationCliConfigState,
    maximum_total_charge: MicroUsd,
    non_runtime_charge_reserve: MicroUsd,
) -> PathBuf {
    let root = fixture.directory.path();
    let missing = root.join("missing");
    let uses_real_inputs = !matches!(state, CalibrationCliConfigState::MissingInputs);
    let path = |real: PathBuf, missing_name: &str| {
        if uses_real_inputs {
            real
        } else {
            missing.join(missing_name)
        }
    };
    let model_lock_path = path(root.join("model.lock.json"), "model.lock.json");
    let worker_source_path = path(root.join("worker.py"), "worker.py");
    let dependency_lock_path = path(root.join("requirements.lock"), "requirements.lock");
    let worker_model_lock_path = path(
        root.join("worker-model.lock.json"),
        "worker-model.lock.json",
    );
    let worker_dependency_lock_path = path(
        root.join("worker-requirements.lock"),
        "worker-requirements.lock",
    );
    let model_dir = path(root.join("model"), "model");
    if uses_real_inputs {
        for file in [
            &model_lock_path,
            &dependency_lock_path,
            &worker_model_lock_path,
            &worker_dependency_lock_path,
        ] {
            fs::write(file, b"fixture").expect("write CLI fixture input");
        }
        fs::write(&worker_source_path, b"#!/bin/sh\nexit 1\n").expect("write CLI fixture worker");
        fs::set_permissions(&worker_source_path, fs::Permissions::from_mode(0o755))
            .expect("make CLI fixture worker executable");
        fs::create_dir_all(&model_dir).expect("create CLI fixture model directory");
    }
    let representation_path = match state {
        CalibrationCliConfigState::CompletedCalibrationOutput => root.join("representation"),
        CalibrationCliConfigState::FreshCalibrationOutput => root.join("paid-representation"),
        CalibrationCliConfigState::MissingInputs => missing.join("representation"),
    };
    let evidence_path = match state {
        CalibrationCliConfigState::CompletedCalibrationOutput => {
            root.join("calibration-evidence.json")
        }
        CalibrationCliConfigState::FreshCalibrationOutput => {
            root.join("paid-calibration-evidence.json")
        }
        CalibrationCliConfigState::MissingInputs => missing.join("calibration-evidence.json"),
    };
    let config_path = root.join("calibration-run.json");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "corpus_path": path(root.join("english.ndb"), "english.ndb"),
            "ordered_event_ids_path": path(
                root.join("ordered-event-ids.bin"),
                "ordered-event-ids.bin"
            ),
            "token_audit_path": path(root.join("token-audit"), "token-audit"),
            "batch_plan_path": path(root.join("batch-plan"), "batch-plan"),
            "representation_path": representation_path,
            "model_lock_path": model_lock_path,
            "worker_source_path": worker_source_path,
            "dependency_lock_path": dependency_lock_path,
            "container_image": format!("fixture@sha256:{}", "5".repeat(64)),
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": if uses_real_inputs {
                    worker_source_path.clone()
                } else {
                    missing.join("python")
                },
                "model_dir": model_dir,
                "model_lock_path": worker_model_lock_path,
                "dependency_lock_path": worker_dependency_lock_path,
                "device": "cuda"
            },
            "batch_size": 2,
            "shard_rows": 4,
            "calibration": {
                "ledger_path": fixture.path,
                "reservation_id": "cli-calibration",
                "maximum_total_charge_micro_usd": maximum_total_charge.0,
                "non_runtime_charge_reserve_micro_usd": non_runtime_charge_reserve.0,
                "execution_identity_path": path(
                    root.join("execution-identity.json"),
                    "execution-identity.json"
                ),
                "evidence_path": evidence_path,
                "token_range_upper_bounds": [4],
                "maximum_work_unit_seconds": 10
            }
        }))
        .expect("encode calibration CLI config"),
    )
    .expect("write calibration CLI config");
    config_path
}

fn run_gte_oracle(arguments: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .args(arguments)
        .output()
        .expect("run gte-oracle")
}

fn assert_command_succeeded(output: &std::process::Output) {
    assert!(
        output.status.success(),
        "command failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn assert_command_failed_with(output: &std::process::Output, expected: &str) {
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains(expected),
        "expected `{expected}` in: {stderr}"
    );
}

fn ledger_entries(path: &Path) -> Vec<serde_json::Value> {
    let ledger: serde_json::Value =
        serde_json::from_slice(&fs::read(path).expect("read ledger entries"))
            .expect("decode ledger entries");
    ledger["entries"]
        .as_array()
        .expect("ledger entries array")
        .clone()
}

struct LedgerFixture {
    directory: TempDir,
    path: PathBuf,
}

impl LedgerFixture {
    fn new(
        actual_spend_cents: u64,
        outstanding_commitments_cents: u64,
        calibration_actual_spend_cents: u64,
        calibration_outstanding_commitments_cents: u64,
    ) -> Self {
        let directory = tempfile::tempdir().expect("create fixture directory");
        let path = directory.path().join("budget-ledger.json");
        fs::write(
            &path,
            format!(
                r#"{{
  "schema_version": 2,
  "scope": "Entire oracle MVP effort",
  "currency": "USD",
  "lifetime_cap_cents": 50000,
  "calibration_lifetime_cap_cents": 2500,
  "actual_spend_cents": {actual_spend_cents},
  "outstanding_commitments_cents": {outstanding_commitments_cents},
  "calibration_actual_spend_cents": {calibration_actual_spend_cents},
  "calibration_outstanding_commitments_cents": {calibration_outstanding_commitments_cents},
  "reserved_remaining_work_cents": null,
  "reconciled_through_utc": "2026-07-16T00:00:00Z",
  "entries": []
}}"#
            ),
        )
        .expect("write fixture ledger");
        Self { directory, path }
    }

    fn write_calibration_evidence(&self) -> CalibrationFixture {
        self.write_calibration_evidence_with_rate(MicroUsd::from_dollars(360))
    }

    fn write_calibration_evidence_with_rate(
        &self,
        rental_rate_per_hour: MicroUsd,
    ) -> CalibrationFixture {
        self.build_calibration_fixture(
            &[1, 2, 3, 4, 1, 2, 3, 4],
            &[4],
            rental_rate_per_hour,
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        )
    }

    fn write_calibration_evidence_with_gpu_model(&self, gpu_model: &str) -> CalibrationFixture {
        self.build_calibration_fixture(
            &[1, 2, 3, 4, 1, 2, 3, 4],
            &[4],
            MicroUsd::from_dollars(360),
            gpu_model,
        )
    }

    fn write_calibration_evidence_with_unique_second_shard_shape(&self) -> CalibrationFixture {
        self.build_calibration_fixture(
            &[1, 2, 3, 4, 1, 2, 33, 34],
            &[4, 34],
            MicroUsd::from_dollars(360),
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        )
    }

    fn build_calibration_fixture(
        &self,
        lengths: &[usize],
        token_range_upper_bounds: &[u32],
        rental_rate_per_hour: MicroUsd,
        gpu_model: &str,
    ) -> CalibrationFixture {
        let ledger: serde_json::Value = serde_json::from_slice(
            &fs::read(&self.path).expect("read fixture ledger for evidence binding"),
        )
        .expect("decode fixture ledger for evidence binding");
        let reservation = ledger["entries"].as_array().and_then(|entries| {
            entries.iter().rev().find(|entry| {
                entry["kind"] == "calibration_reservation"
                    && !entries.iter().any(|settlement| {
                        matches!(
                            settlement["kind"].as_str(),
                            Some("calibration_settlement" | "failed_calibration_settlement")
                        ) && settlement["reservation_id"] == entry["reservation_id"]
                    })
            })
        });
        let reservation_id = reservation
            .and_then(|entry| entry["reservation_id"].as_str())
            .unwrap_or("fixture-unreserved-calibration");
        let reservation_previous_ledger_sha256 = reservation
            .and_then(|entry| entry["previous_ledger_sha256"].as_str())
            .map(str::to_owned)
            .unwrap_or_else(|| "0".repeat(64));
        let reservation_authorization_sha256 = reservation
            .map(|entry| {
                sha256(&serde_json::to_vec(entry).expect("encode reservation authorization"))
            })
            .unwrap_or_else(|| "0".repeat(64));
        let reservation_maximum_charge_micro_usd = reservation
            .and_then(|entry| entry["reserved_maximum_charge_cents"].as_u64())
            .unwrap_or(2_500)
            * 10_000;
        let ndb_path = self.directory.path().join("english.ndb");
        let ndb = Ndb::new(
            ndb_path.to_str().expect("UTF-8 NDB path"),
            &Config::new().set_mapsize(512 * 1024 * 1024),
        )
        .expect("open calibration NDB");
        let events = lengths
            .iter()
            .enumerate()
            .map(|(index, length)| signed_event(&"x".repeat(*length), index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit calibration event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);

        let ordered_event_ids_path = self.directory.path().join("ordered-event-ids.bin");
        let mut ordered = File::create(&ordered_event_ids_path).expect("create ordered IDs");
        for event in &events {
            ordered
                .write_all(&event_id(event))
                .expect("write ordered event ID");
        }
        ordered.sync_all().expect("sync ordered IDs");

        let descriptor = fixture_descriptor();
        let token_audit_path = self.directory.path().join("token-audit");
        let mut counter = FixtureTokenCounter {
            descriptor: descriptor.clone(),
        };
        audit_ordered_gte_tokens(
            &ndb_path,
            &ordered_event_ids_path,
            &token_audit_path,
            &OrderedGteTokenAuditConfig {
                batch_size: 2,
                shard_rows: 4,
            },
            &mut counter,
        )
        .expect("create verified token audit");

        let batch_plan_path = self.directory.path().join("batch-plan");
        let plan = create_representation_batch_plan(
            &ordered_event_ids_path,
            &token_audit_path,
            &batch_plan_path,
            &RepresentationBatchPlanConfig {
                shard_rows: 4,
                batch_rows: 2,
            },
        )
        .expect("create immutable production batch plan");

        let representation_path = self.directory.path().join("representation");
        let mut encoder = FixtureEncoder { descriptor };
        let built = build_representation_shards(
            &ndb_path,
            &ordered_event_ids_path,
            &representation_path,
            &RepresentationBuildConfig {
                token_audit_path: token_audit_path.clone(),
                batch_plan_path: batch_plan_path.clone(),
                shard_ordinals: vec![0],
            },
            &mut encoder,
        )
        .expect("build one reusable calibration shard");

        let execution_identity = CalibrationExecutionIdentity {
            schema_version: 2,
            artifact_kind: "gte-calibration-execution-identity".to_owned(),
            representation_descriptor_sha256: built.manifest.descriptor_sha256.clone(),
            gpu_model: gpu_model.to_owned(),
            gpu_device_uuid: "GPU-fixture".to_owned(),
            gpu_count: 1,
            gpu_power_limit_watts: 600,
            driver_version: "580.95.05".to_owned(),
            machine_verified: true,
            reliability_millionths: 999_000,
            host_cpu: "fixture-cpu".to_owned(),
            host_memory_bytes: 128 * 1024 * 1024 * 1024,
            local_nvme_bytes: 200_000_000_000,
            local_nvme_bandwidth_bytes_per_second: 1_000_000_000,
            on_demand: true,
            available_duration_seconds: 86_400,
            rental_provider: "vast.ai".to_owned(),
            rental_offer_id: "fixture-offer".to_owned(),
            rental_instance_id: "fixture-instance".to_owned(),
            rental_rate_per_hour,
        };
        let execution_identity_path = self.directory.path().join("execution-identity.json");
        let execution_identity_bytes =
            serde_json::to_vec_pretty(&execution_identity).expect("encode execution identity");
        fs::write(&execution_identity_path, &execution_identity_bytes)
            .expect("write execution identity");

        let evidence_path = self.directory.path().join("calibration-evidence.json");
        let evidence_bytes = serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 6,
            "artifact_kind": "gte-calibration-evidence",
            "reservation_id": reservation_id,
            "reservation_previous_ledger_sha256": reservation_previous_ledger_sha256,
            "reservation_authorization_sha256": reservation_authorization_sha256,
            "reservation_maximum_charge_micro_usd": reservation_maximum_charge_micro_usd,
            "representation_build_identity_sha256": built.manifest.build_identity_sha256,
            "calibration_shards": built.manifest.shards,
            "batch_plan_manifest_sha256": plan.identity().manifest_sha256,
            "execution_identity_sha256": sha256_file(&execution_identity_path),
            "token_range_upper_bounds": token_range_upper_bounds,
            "cold_start_elapsed_nanoseconds": 5_000_000_000_u64,
            "shard_setups": [
                {
                    "shard_ordinal": 0,
                    "elapsed_nanoseconds": 1_000_000_000_u64
                }
            ],
            "shard_checkpoints": [
                {
                    "shard_ordinal": 0,
                    "elapsed_nanoseconds": 3_000_000_000_u64
                }
            ],
            "finalization_elapsed_nanoseconds": 4_000_000_000_u64,
            "batches": [
                {
                    "shard_ordinal": 0,
                    "batch_ordinal": 0,
                    "end_to_end_elapsed_nanoseconds": 1_000_000_000_u64
                },
                {
                    "shard_ordinal": 0,
                    "batch_ordinal": 1,
                    "end_to_end_elapsed_nanoseconds": 2_000_000_000_u64
                }
            ]
        }))
        .expect("encode calibration evidence");
        fs::write(&evidence_path, &evidence_bytes).expect("write calibration evidence");

        CalibrationFixture {
            evidence_path,
            evidence_bytes,
            execution_identity_bytes,
            paths: CalibrationEvidencePaths {
                ordered_event_ids_path,
                token_audit_path,
                batch_plan_path,
                representation_path,
                execution_identity_path,
            },
        }
    }
}

struct CalibrationFixture {
    evidence_path: PathBuf,
    evidence_bytes: Vec<u8>,
    execution_identity_bytes: Vec<u8>,
    paths: CalibrationEvidencePaths,
}

impl CalibrationFixture {
    fn restore_evidence(&self) {
        fs::write(&self.evidence_path, &self.evidence_bytes).expect("restore evidence");
    }

    fn restore_execution_identity(&self) {
        fs::write(
            &self.paths.execution_identity_path,
            &self.execution_identity_bytes,
        )
        .expect("restore execution identity");
    }
}

struct FixtureTokenCounter {
    descriptor: RepresentationDescriptor,
}

impl OrderedGteTokenCounter for FixtureTokenCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        let query_prefix = if role == TokenRole::Query { 10 } else { 0 };
        Ok(texts
            .iter()
            .map(|text| u32::try_from(text.len() + query_prefix).expect("fixture token length"))
            .collect())
    }
}

struct FixtureEncoder {
    descriptor: RepresentationDescriptor,
}

impl RepresentationEncoder for FixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        Ok(texts.iter().flat_map(|_| [1.0, 0.0, 0.0]).collect())
    }

    fn encode_queries(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        self.encode_documents(texts)
    }
}

fn fixture_descriptor() -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/gte".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: "2".repeat(64),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:".to_owned() + &"5".repeat(64),
        torch_version: "2.12.1".to_owned(),
        transformers_version: "4.41.2".to_owned(),
        cuda_version: "13.0.2".to_owned(),
        execution_device: "cuda".to_owned(),
        dimensions: 3,
        model_token_ceiling: 100,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture-query-instruction".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn signed_event(content: &str, offset: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + offset)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign event")
        .json()
        .expect("event JSON")
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let transaction = Transaction::new(ndb).expect("read transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "NDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event value");
    let value = value["id"].as_str().expect("event ID");
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (hex(chunk[0]) << 4) | hex(chunk[1]);
    }
    output
}

fn hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn sha256_file(path: &Path) -> String {
    sha256(&fs::read(path).expect("read hash input"))
}
