use std::fs;
use std::process::Command;

use oracle_mvp::reference_map::NoteProposal;
use sha2::{Digest, Sha256};

#[test]
fn reference_map_cli_rejects_an_incomplete_review_command() {
    let output = Command::new(env!("CARGO_BIN_EXE_reference-map"))
        .arg("notes")
        .output()
        .expect("run reference-map");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("utf-8 stderr");
    assert!(
        stderr.contains(
            "usage: reference-map notes <proposal.json> <session.json> <approved-notes.json>"
        ),
        "{stderr}"
    );
}

#[test]
fn reference_map_cli_rejects_an_unknown_mode() {
    let output = Command::new(env!("CARGO_BIN_EXE_reference-map"))
        .arg("invent")
        .output()
        .expect("run reference-map");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("utf-8 stderr");
    assert!(stderr.contains("unknown mode `invent`"), "{stderr}");
}

#[test]
fn reference_map_cli_prepares_a_source_bound_review_proposal() {
    let temp = tempfile::tempdir().expect("tempdir");
    let sample_path = temp.path().join("sample.jsonl");
    let plan_path = temp.path().join("plan.json");
    let proposal_path = temp.path().join("proposal.json");
    let mut sample = String::new();
    let notes = (0..64)
        .map(|index| {
            let slot = index + 1;
            let note_id = format!("{slot:064x}");
            let pubkey = format!("{:064x}", slot + 10_000);
            let content = format!("Source-bound reference note {slot}");
            sample.push_str(
                &serde_json::json!({
                    "split": "learning",
                    "note_id": note_id,
                    "pubkey": pubkey,
                    "content": content,
                })
                .to_string(),
            );
            sample.push('\n');
            let contrast_pair = (index < 16).then(|| {
                serde_json::json!({
                    "pair_id": format!("contrast-{:02}", index / 2 + 1),
                    "partner_slot": (index ^ 1) + 1,
                    "broad_narrow_role": null,
                })
            });
            let broad_narrow_pair = ((16..32).contains(&index)).then(|| {
                serde_json::json!({
                    "pair_id": format!("breadth-{:02}", (index - 16) / 2 + 1),
                    "partner_slot": ((index - 16) ^ 1) + 17,
                    "broad_narrow_role": if index % 2 == 0 { "broad" } else { "narrow" },
                })
            });
            serde_json::json!({
                "slot": slot,
                "note_id": note_id,
                "composition": match index {
                    0..24 => "single",
                    24..56 => "mixed",
                    _ => "ambiguous",
                },
                "selection_rationale": format!("Diagnostic semantic case {slot}"),
                "contrast_pair": contrast_pair,
                "broad_narrow_pair": broad_narrow_pair,
                "niche_subject": ((32..40).contains(&index))
                    .then(|| format!("niche-{slot}")),
            })
        })
        .collect::<Vec<_>>();
    fs::write(&sample_path, sample.as_bytes()).expect("write sample");
    let plan = serde_json::json!({
        "schema_version": 1,
        "proposal_id": "cli-preparation-test",
        "source": {
            "sample_path": "sample.jsonl",
            "sample_sha256": format!("{:x}", Sha256::digest(sample.as_bytes())),
            "split": "learning",
        },
        "notes": notes,
    });
    fs::write(
        &plan_path,
        serde_json::to_vec_pretty(&plan).expect("encode plan"),
    )
    .expect("write plan");

    let output = Command::new(env!("CARGO_BIN_EXE_reference-map"))
        .args([
            "prepare-notes",
            plan_path.to_str().expect("utf-8 plan"),
            proposal_path.to_str().expect("utf-8 proposal"),
        ])
        .output()
        .expect("prepare proposal");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let proposal: NoteProposal =
        serde_json::from_slice(&fs::read(&proposal_path).expect("read generated proposal"))
            .expect("decode generated proposal");
    proposal.validate().expect("generated proposal is valid");
    assert_eq!(proposal.notes[0].content, "Source-bound reference note 1");
}
