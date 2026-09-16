use std::fs;
use std::path::Path;

use oracle_mvp::budget::MicroUsd;
use oracle_mvp::gte_budget::{read_budget_ledger, reserve_calibration};
use serde_json::json;

#[test]
fn checked_in_ledger_has_the_approved_thousand_dollar_cap_and_zero_reserve() {
    assert_eq!(
        oracle_mvp::budget::MVP_HARD_BUDGET,
        MicroUsd::from_dollars(1_000)
    );
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("budget-ledger.json");
    let ledger = read_budget_ledger(&path).expect("read the production ledger");
    assert_eq!(ledger.lifetime_cap, MicroUsd::from_dollars(1_000));
    assert_eq!(ledger.calibration_lifetime_cap, MicroUsd::from_dollars(25));
    let document: serde_json::Value = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
    assert_eq!(document["reserved_remaining_work_cents"], json!(0));
}

#[test]
fn reservation_accepts_exactly_one_thousand_dollars_then_rejects_one_cent_more() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("budget-ledger.json");
    fs::write(
        &path,
        serde_json::to_vec_pretty(&json!({
            "schema_version": 2,
            "scope": "Entire oracle MVP effort",
            "currency": "USD",
            "lifetime_cap_cents": 100_000,
            "calibration_lifetime_cap_cents": 2_500,
            "actual_spend_cents": 99_500,
            "outstanding_commitments_cents": 400,
            "calibration_actual_spend_cents": 0,
            "calibration_outstanding_commitments_cents": 0,
            "reserved_remaining_work_cents": 0,
            "reconciled_through_utc": "2026-09-16T00:00:00Z",
            "entries": []
        }))
        .unwrap(),
    )
    .unwrap();

    let admission = reserve_calibration(
        &path,
        "last-dollar",
        MicroUsd::from_dollars(1),
        "2026-09-16T00:01:00Z",
    )
    .expect("the approved cap includes its exact boundary");
    assert_eq!(
        admission.projected_lifetime_total,
        MicroUsd::from_dollars(1_000)
    );
    assert_eq!(admission.remaining_lifetime_budget, MicroUsd(0));

    let before = fs::read(&path).unwrap();
    let error = reserve_calibration(
        &path,
        "one-cent-too-many",
        MicroUsd::from_cents(1),
        "2026-09-16T00:02:00Z",
    )
    .expect_err("the higher cap remains a hard ceiling");
    assert!(error.to_string().contains("$1,000"), "{error}");
    assert_eq!(fs::read(path).unwrap(), before);
}
