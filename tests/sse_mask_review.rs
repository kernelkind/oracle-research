use std::collections::VecDeque;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_review::ApprovalUi;
use oracle_mvp::reference_tui::{ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel};
use oracle_mvp::sse_mask_review::{
    MaskReviewRunOutcome, load_verified_mask_proposal, run_mask_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

struct Fixture {
    _temporary: tempfile::TempDir,
    proposal_path: PathBuf,
    session_path: PathBuf,
    approved_path: PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().expect("create fixture directory");
        let sample_path = temporary.path().join("sample.jsonl");
        let note_set_path = temporary.path().join("note-set.json");
        let proposal_path = temporary.path().join("mask-proposal.json");
        let session_path = temporary.path().join("mask-session.json");
        let approved_path = temporary.path().join("approved-masks.json");
        let rows = [
            json!({
                "split": "learning",
                "note_id": format!("{:064x}", 1),
                "pubkey": format!("{:064x}", 101),
                "content": "Open-source tools are reusable."
            }),
            json!({
                "split": "learning",
                "note_id": format!("{:064x}", 2),
                "pubkey": format!("{:064x}", 102),
                "content": "Private browsing protects users."
            }),
            json!({
                "split": "learning",
                "note_id": format!("{:064x}", 3),
                "pubkey": format!("{:064x}", 103),
                "content": "Open-source apps can protect private messages."
            }),
        ];
        let mut sample = rows
            .iter()
            .map(Value::to_string)
            .collect::<Vec<_>>()
            .join("\n");
        sample.push('\n');
        fs::write(&sample_path, sample.as_bytes()).expect("write sample");
        let note_set = json!({
            "schema_version": 1,
            "status": "approved",
            "source": {
                "path": "sample.jsonl",
                "sha256": sha256(sample.as_bytes())
            },
            "subjects": [
                {
                    "id": "open_source",
                    "label": "Open-source software",
                    "reference_note_ids": [format!("{:064x}", 1)]
                },
                {
                    "id": "privacy",
                    "label": "Digital privacy",
                    "reference_note_ids": [format!("{:064x}", 2)]
                }
            ],
            "mixed_notes": [
                {
                    "note_id": format!("{:064x}", 3),
                    "subject_ids": ["open_source", "privacy"]
                }
            ],
            "invariants": {
                "subject_count": 2,
                "reference_notes_per_subject": 1,
                "reference_note_count": 2,
                "mixed_note_count": 1,
                "subjects_per_mixed_note": 2,
                "mixed_masks_per_subject": 1,
                "total_note_count": 3,
                "unique_note_count": 3,
                "unique_author_count": 3,
                "required_split": "learning"
            }
        });
        write_json(&note_set_path, &note_set);
        let note_set_bytes = fs::read(&note_set_path).expect("read note set");
        let proposal = json!({
            "schema_version": 1,
            "proposal_id": "test-mask-proposal",
            "note_set": {
                "path": "note-set.json",
                "sha256": sha256(&note_set_bytes)
            },
            "masks": [
                {
                    "note_id": format!("{:064x}", 1),
                    "subject_id": "open_source",
                    "fragments": ["Open-source tools"]
                },
                {
                    "note_id": format!("{:064x}", 2),
                    "subject_id": "privacy",
                    "fragments": ["Private browsing"]
                },
                {
                    "note_id": format!("{:064x}", 3),
                    "subject_id": "open_source",
                    "fragments": ["Open-source apps"]
                },
                {
                    "note_id": format!("{:064x}", 3),
                    "subject_id": "privacy",
                    "fragments": ["protect private messages"]
                }
            ]
        });
        write_json(&proposal_path, &proposal);
        Self {
            _temporary: temporary,
            proposal_path,
            session_path,
            approved_path,
        }
    }

    fn proposal_json(&self) -> Value {
        serde_json::from_slice(&fs::read(&self.proposal_path).expect("read proposal"))
            .expect("decode proposal")
    }

    fn replace_proposal(&self, proposal: &Value) {
        write_json(&self.proposal_path, proposal);
    }
}

#[derive(Default)]
struct ScriptedUi {
    actions: VecDeque<ApprovalTuiAction>,
    screens: Vec<ApprovalScreen>,
}

impl ScriptedUi {
    fn with_actions(actions: impl IntoIterator<Item = ApprovalTuiAction>) -> Self {
        Self {
            actions: actions.into_iter().collect(),
            screens: Vec::new(),
        }
    }
}

impl ApprovalUi for ScriptedUi {
    fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction> {
        self.screens.push(screen);
        Ok(self
            .actions
            .pop_front()
            .expect("script contains one action per shown screen"))
    }
}

fn approval() -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }
}

fn rejection(comment: &str) -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Rejected,
        comment: comment.to_owned(),
    }
}

#[test]
fn runner_shows_one_source_bound_mask_and_pauses_without_approving_it() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::with_actions([ApprovalTuiAction::Pause]);

    let outcome = run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("run review");

    assert_eq!(outcome, MaskReviewRunOutcome::Paused);
    assert_eq!(ui.screens.len(), 1);
    let screen = &ui.screens[0];
    assert!(screen.heading.contains("Primary mask 1 of 4"));
    assert_eq!(screen.title, "Reference note · only mask");
    assert!(screen.scope.contains("Subject: Open-source software"));
    assert!(
        screen
            .scope
            .contains("Does the highlight faithfully isolate “Open-source software”?")
    );
    assert_eq!(screen.evidence.len(), 1);
    assert_eq!(screen.evidence[0].title, "Note");
    assert_eq!(screen.evidence[0].body, "⟦Open-source tools⟧ are reusable.");
    assert!(fixture.session_path.exists(), "pause state is durable");
    assert!(!fixture.approved_path.exists());
}

#[test]
fn mixed_note_masks_are_reviewed_separately_and_resume_at_the_only_pending_mask() {
    let fixture = Fixture::new();
    let mut first =
        ScriptedUi::with_actions([approval(), approval(), approval(), ApprovalTuiAction::Pause]);
    let outcome = run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut first,
    )
    .expect("run first review");
    assert_eq!(outcome, MaskReviewRunOutcome::Paused);
    assert_eq!(first.screens[2].title, "Mixed note · first of two masks");
    assert_eq!(first.screens[3].title, "Mixed note · second of two masks");

    let mut resumed = ScriptedUi::with_actions([approval()]);
    let outcome = run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut resumed,
    )
    .expect("resume review");
    assert_eq!(outcome, MaskReviewRunOutcome::Approved);
    assert_eq!(resumed.screens.len(), 1);
    assert!(
        resumed.screens[0]
            .scope
            .contains("Subject: Digital privacy")
    );
    assert!(fixture.approved_path.exists());
}

#[test]
fn revising_one_rejected_mask_reopens_only_that_mask() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::with_actions([
        approval(),
        rejection("Select the actual privacy claim."),
        approval(),
        approval(),
    ]);
    let outcome = run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("run rejected review");
    assert_eq!(
        outcome,
        MaskReviewRunOutcome::NeedsRevision {
            approved: 3,
            rejected: 1
        }
    );

    let mut revised = fixture.proposal_json();
    revised["masks"][1]["fragments"] = json!(["protects users"]);
    fixture.replace_proposal(&revised);

    let mut resumed = ScriptedUi::with_actions([ApprovalTuiAction::Pause]);
    let outcome = run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut resumed,
    )
    .expect("reconcile revised proposal");
    assert_eq!(outcome, MaskReviewRunOutcome::Paused);
    assert_eq!(resumed.screens.len(), 1);
    assert_eq!(
        resumed.screens[0].evidence[0].body,
        "Private browsing ⟦protects users⟧."
    );
}

#[test]
fn proposal_validation_rejects_missing_fragments_overlaps_and_wrong_assignments() {
    let fixture = Fixture::new();
    let mut missing = fixture.proposal_json();
    missing["masks"][0]["fragments"] = json!(["not present"]);
    fixture.replace_proposal(&missing);
    let error =
        load_verified_mask_proposal(&fixture.proposal_path).expect_err("fragment must exist");
    assert!(error.to_string().contains("absent from note"), "{error}");

    let fixture = Fixture::new();
    let mut overlapping = fixture.proposal_json();
    overlapping["masks"][0]["fragments"] = json!(["Open-source tools", "tools are"]);
    fixture.replace_proposal(&overlapping);
    let error =
        load_verified_mask_proposal(&fixture.proposal_path).expect_err("spans must not overlap");
    assert!(error.to_string().contains("overlap"), "{error}");

    let fixture = Fixture::new();
    let mut wrong = fixture.proposal_json();
    wrong["masks"][0]["subject_id"] = json!("privacy");
    fixture.replace_proposal(&wrong);
    let error = load_verified_mask_proposal(&fixture.proposal_path)
        .expect_err("mask assignments must match the frozen note set");
    assert!(error.to_string().contains("review order"), "{error}");
}

#[test]
fn production_screen_renders_the_subject_highlight_and_deliberate_controls() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::with_actions([ApprovalTuiAction::Pause]);
    run_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("build production screen");
    let mut model = ApprovalTuiModel::new(ui.screens.remove(0));
    let backend = TestBackend::new(100, 32);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render screen");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(rendered.contains("⟦Open-source tools⟧"), "{rendered}");
    assert!(
        normalized.contains("Subject: Open-source software"),
        "{rendered}"
    );
    assert!(normalized.contains("[A] No problem"), "{rendered}");
    assert!(normalized.contains("[R] Needs revision"), "{rendered}");
    assert!(normalized.contains("[Ctrl-C] Pause"), "{rendered}");
}

fn write_json(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
