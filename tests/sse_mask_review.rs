use std::collections::VecDeque;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_review::ApprovalUi;
use oracle_mvp::reference_tui::{ApprovalScreen, ApprovalTuiAction};
use oracle_mvp::sse_mask_review::{
    ReviewStage, SubjectMaskReviewRunOutcome, SubjectMaskReviewUi, SubjectReviewAction,
    SubjectReviewScreen, SubjectReviewTuiModel, load_verified_subject_mask_proposal,
    run_subject_mask_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const SUBJECT_INSTRUCTION: &str = "Enumerate every atomic subject explicitly and substantively discussed in the provided text.\n\nAn atomic subject is the smallest coherent semantic idea that remains meaningful as a distinct focus.\n\n<RAW NOTE>\n\nReturn only a JSON array of subject strings.";
const MASK_INSTRUCTION: &str = "Mask only the narrowest portion or portions of the provided text that directly express the provided atomic subject.\n\nAtomic subject:\n<SUBJECT>\n\nText:\n<RAW NOTE>\n\nReturn only a JSON array of exact substrings copied from the text, in source order. If the subject is not expressed, return \"unsupported\".";
const TAKEAWAY_INSTRUCTION: &str = "This text is a social media post. Identify each substantive point the user communicates. Summarize every independent point as a separate, concise takeaway in your own words. Combine details when they jointly express one point. Ground each takeaway in the text itself.\n\nReturn only a JSON array of strings.";
const TAKEAWAY_MASK_INSTRUCTION: &str = "Mask only the narrowest portion or portions of the provided text that directly express the provided takeaway.\n\nTakeaway:\n<TAKEAWAY>\n\nText:\n<RAW NOTE>\n\nReturn only a JSON array of exact substrings copied from the text, in source order. If the takeaway is not expressed, return \"unsupported\".";
const SUBJECT_1: &str = "1111111111111111";
const SUBJECT_2: &str = "2222222222222222";
const SUBJECT_3: &str = "3333333333333333";

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
        let proposal_path = temporary.path().join("subject-mask-proposal.json");
        let session_path = temporary.path().join("review-session.json");
        let approved_path = temporary.path().join("approved-subject-masks.json");
        let first_note_id = format!("{:064x}", 1);
        let second_note_id = format!("{:064x}", 2);
        let rows = [
            json!({
                "split": "learning",
                "note_id": first_note_id,
                "pubkey": format!("{:064x}", 101),
                "content": "pypush is serverless; pypush is open-source."
            }),
            json!({
                "split": "learning",
                "note_id": second_note_id,
                "pubkey": format!("{:064x}", 102),
                "content": "Solar power will dominate future electricity generation."
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
            "schema_version": 2,
            "status": "approved",
            "source": {
                "path": "sample.jsonl",
                "sha256": sha256(sample.as_bytes())
            },
            "note_ids": [first_note_id, second_note_id],
            "invariants": {
                "note_count": 2,
                "unique_note_count": 2,
                "unique_author_count": 2,
                "required_split": "learning"
            }
        });
        write_json(&note_set_path, &note_set);
        let note_set_bytes = fs::read(&note_set_path).expect("read note set");
        let proposal = json!({
            "schema_version": 2,
            "proposal_id": "test-generated-subject-masks",
            "note_set": {
                "path": "note-set.json",
                "sha256": sha256(&note_set_bytes)
            },
            "subject_instruction": SUBJECT_INSTRUCTION,
            "mask_instruction": MASK_INSTRUCTION,
            "notes": [
                {
                    "note_id": format!("{:064x}", 1),
                    "subjects": [
                        {
                            "subject_id": SUBJECT_1,
                            "label": "Serverless operation of pypush",
                            "status": "masked",
                            "fragments": [
                                {"text": "pypush", "occurrence": 1},
                                {"text": "serverless", "occurrence": 1}
                            ]
                        },
                        {
                            "subject_id": SUBJECT_2,
                            "label": "Open-source availability of pypush",
                            "status": "masked",
                            "fragments": [
                                {"text": "pypush", "occurrence": 2},
                                {"text": "open-source", "occurrence": 1}
                            ]
                        }
                    ]
                },
                {
                    "note_id": format!("{:064x}", 2),
                    "subjects": [
                        {
                            "subject_id": SUBJECT_3,
                            "label": "Future dominance of solar power generation",
                            "status": "masked",
                            "fragments": [
                                {
                                    "text": "Solar power will dominate future electricity generation",
                                    "occurrence": 1
                                }
                            ]
                        }
                    ]
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
    subject_actions: VecDeque<SubjectReviewAction>,
    approval_actions: VecDeque<ApprovalTuiAction>,
    subject_screens: Vec<SubjectReviewScreen>,
    approval_screens: Vec<ApprovalScreen>,
}

impl ScriptedUi {
    fn with_actions(
        subject_actions: impl IntoIterator<Item = SubjectReviewAction>,
        approval_actions: impl IntoIterator<Item = ApprovalTuiAction>,
    ) -> Self {
        Self {
            subject_actions: subject_actions.into_iter().collect(),
            approval_actions: approval_actions.into_iter().collect(),
            ..Self::default()
        }
    }
}

impl ApprovalUi for ScriptedUi {
    fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction> {
        self.approval_screens.push(screen);
        Ok(self
            .approval_actions
            .pop_front()
            .expect("script contains one action per mask screen"))
    }
}

impl SubjectMaskReviewUi for ScriptedUi {
    fn review_subjects(&mut self, screen: SubjectReviewScreen) -> io::Result<SubjectReviewAction> {
        self.subject_screens.push(screen);
        Ok(self
            .subject_actions
            .pop_front()
            .expect("script contains one action per subject screen"))
    }
}

fn subject_approval(subject_id: &str) -> SubjectReviewAction {
    SubjectReviewAction::Decide {
        subject_id: subject_id.to_owned(),
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }
}

fn mask_approval() -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }
}

fn mask_rejection(comment: &str) -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Rejected,
        comment: comment.to_owned(),
    }
}

#[test]
fn generated_subjects_and_note_completeness_are_reviewed_before_any_mask() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::with_actions(
        [subject_approval(SUBJECT_1), SubjectReviewAction::Pause],
        [],
    );

    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut first,
    )
    .expect("run first subject review");

    assert_eq!(outcome, SubjectMaskReviewRunOutcome::Paused);
    assert_eq!(first.subject_screens.len(), 2);
    assert!(first.approval_screens.is_empty());
    let first_screen = &first.subject_screens[0];
    assert_eq!(
        first_screen.note,
        "pypush is serverless; pypush is open-source."
    );
    assert_eq!(first_screen.choices.len(), 2);
    assert_eq!(first_screen.choices[0].subject_id, SUBJECT_1);
    assert_eq!(first_screen.choices[1].subject_id, SUBJECT_2);
    assert_eq!(first_screen.choices[0].outcome, None);
    assert_eq!(
        first.subject_screens[1].choices[0].outcome,
        Some(ReviewOutcome::Approved)
    );

    let mut resumed = ScriptedUi::with_actions(
        [
            subject_approval(SUBJECT_2),
            SubjectReviewAction::Complete,
            SubjectReviewAction::Pause,
        ],
        [],
    );
    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut resumed,
    )
    .expect("resume subject review");

    assert_eq!(outcome, SubjectMaskReviewRunOutcome::Paused);
    assert!(resumed.approval_screens.is_empty());
    assert_eq!(
        resumed
            .subject_screens
            .last()
            .expect("second note screen")
            .note,
        "Solar power will dominate future electricity generation."
    );
}

#[test]
fn all_subjects_and_completeness_unlock_individual_mask_review_and_publication() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::with_actions(
        [
            subject_approval(SUBJECT_1),
            subject_approval(SUBJECT_2),
            SubjectReviewAction::Complete,
            subject_approval(SUBJECT_3),
            SubjectReviewAction::Complete,
        ],
        [mask_approval(), mask_approval(), mask_approval()],
    );

    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("run complete review");

    assert_eq!(outcome, SubjectMaskReviewRunOutcome::Approved);
    assert_eq!(ui.approval_screens.len(), 3);
    assert_eq!(
        ui.approval_screens[1].evidence[0].body,
        "pypush is serverless; ⟦pypush⟧ is ⟦open-source⟧."
    );
    let approved: Value =
        serde_json::from_slice(&fs::read(&fixture.approved_path).expect("read approved artifact"))
            .expect("decode approved artifact");
    assert_eq!(
        approved["notes"].as_array().expect("approved notes").len(),
        2
    );
}

#[test]
fn rejected_or_missing_subjects_block_mask_review() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::with_actions(
        [
            subject_approval(SUBJECT_1),
            SubjectReviewAction::Decide {
                subject_id: SUBJECT_2.to_owned(),
                outcome: ReviewOutcome::Rejected,
                comment: "This combines availability with the software subject.".to_owned(),
            },
            subject_approval(SUBJECT_3),
            SubjectReviewAction::Missing {
                comment: "The note also discusses electricity generation.".to_owned(),
            },
        ],
        [],
    );

    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("run subject rejection");

    assert_eq!(
        outcome,
        SubjectMaskReviewRunOutcome::NeedsRevision {
            stage: ReviewStage::Subjects,
            approved: 2,
            rejected: 1,
            missing_subject_notes: 1,
        }
    );
    assert!(ui.approval_screens.is_empty());
    assert!(!fixture.approved_path.exists());
}

#[test]
fn revising_one_rejected_mask_reopens_only_that_mask() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::with_actions(
        [
            subject_approval(SUBJECT_1),
            subject_approval(SUBJECT_2),
            SubjectReviewAction::Complete,
            subject_approval(SUBJECT_3),
            SubjectReviewAction::Complete,
        ],
        [
            mask_approval(),
            mask_rejection("Remove the repeated software name."),
            mask_approval(),
        ],
    );
    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut first,
    )
    .expect("run rejected mask review");
    assert_eq!(
        outcome,
        SubjectMaskReviewRunOutcome::NeedsRevision {
            stage: ReviewStage::Masks,
            approved: 2,
            rejected: 1,
            missing_subject_notes: 0,
        }
    );

    let mut revised = fixture.proposal_json();
    revised["notes"][0]["subjects"][1]["fragments"] =
        json!([{"text": "open-source", "occurrence": 1}]);
    fixture.replace_proposal(&revised);
    let mut resumed = ScriptedUi::with_actions([], [ApprovalTuiAction::Pause]);
    let outcome = run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut resumed,
    )
    .expect("reconcile revised mask");

    assert_eq!(outcome, SubjectMaskReviewRunOutcome::Paused);
    assert!(resumed.subject_screens.is_empty());
    assert_eq!(resumed.approval_screens.len(), 1);
    assert_eq!(
        resumed.approval_screens[0].evidence[0].body,
        "pypush is serverless; pypush is ⟦open-source⟧."
    );
}

#[test]
fn unsupported_masks_and_invalid_occurrences_fail_before_review() {
    let fixture = Fixture::new();
    let mut unsupported = fixture.proposal_json();
    unsupported["notes"][0]["subjects"][0]["status"] = json!("unsupported");
    unsupported["notes"][0]["subjects"][0]["fragments"] = json!([]);
    fixture.replace_proposal(&unsupported);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("unsupported result must stop before review");
    assert!(
        error
            .to_string()
            .contains("mask agent returned unsupported"),
        "{error}"
    );

    let fixture = Fixture::new();
    let mut invalid_occurrence = fixture.proposal_json();
    invalid_occurrence["notes"][0]["subjects"][1]["fragments"][0]["occurrence"] = json!(3);
    fixture.replace_proposal(&invalid_occurrence);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("missing occurrence must fail");
    assert!(error.to_string().contains("occurrence 3"), "{error}");
}

#[test]
fn proposal_validation_rejects_empty_overlapping_and_out_of_order_masks() {
    let fixture = Fixture::new();
    let mut empty = fixture.proposal_json();
    empty["notes"][0]["subjects"][0]["fragments"] = json!([]);
    fixture.replace_proposal(&empty);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("empty mask must fail");
    assert!(
        error.to_string().contains("contains no fragments"),
        "{error}"
    );

    let fixture = Fixture::new();
    let mut overlapping = fixture.proposal_json();
    overlapping["notes"][0]["subjects"][0]["fragments"] = json!([
        {"text": "pypush", "occurrence": 1},
        {"text": "pypush is serverless", "occurrence": 1}
    ]);
    fixture.replace_proposal(&overlapping);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("overlapping mask must fail");
    assert!(error.to_string().contains("overlap"), "{error}");

    let fixture = Fixture::new();
    let mut out_of_order = fixture.proposal_json();
    out_of_order["notes"][0]["subjects"][1]["fragments"] = json!([
        {"text": "open-source", "occurrence": 1},
        {"text": "pypush", "occurrence": 2}
    ]);
    fixture.replace_proposal(&out_of_order);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("out-of-order mask must fail");
    assert!(error.to_string().contains("not in source order"), "{error}");
}

#[test]
fn proposal_validation_accepts_the_approved_generation_prompts() {
    let fixture = Fixture::new();
    load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect("the proposal must accept the exact approved generation prompts");
}

#[test]
fn proposal_validation_accepts_the_approved_takeaway_generation_profile() {
    let fixture = Fixture::new();
    let mut proposal = fixture.proposal_json();
    proposal["subject_instruction"] = json!(TAKEAWAY_INSTRUCTION);
    proposal["mask_instruction"] = json!(TAKEAWAY_MASK_INSTRUCTION);
    fixture.replace_proposal(&proposal);

    load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect("the proposal must accept the exact approved takeaway generation profile");
}

#[test]
fn proposal_validation_rejects_a_mixed_generation_profile() {
    let fixture = Fixture::new();
    let mut proposal = fixture.proposal_json();
    proposal["subject_instruction"] = json!(TAKEAWAY_INSTRUCTION);
    fixture.replace_proposal(&proposal);

    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("prompts from different approved profiles must not be mixed");
    assert!(error.to_string().contains("generation prompts"), "{error}");

    let fixture = Fixture::new();
    let mut proposal = fixture.proposal_json();
    proposal["mask_instruction"] = json!(TAKEAWAY_MASK_INSTRUCTION);
    fixture.replace_proposal(&proposal);

    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("prompts from different approved profiles must not be mixed");
    assert!(error.to_string().contains("generation prompts"), "{error}");
}

#[test]
fn proposal_validation_pins_both_approved_generation_prompts() {
    let fixture = Fixture::new();
    let mut changed_subject_prompt = fixture.proposal_json();
    changed_subject_prompt["subject_instruction"] = json!("List some topics that seem relevant.");
    fixture.replace_proposal(&changed_subject_prompt);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("changed subject prompt must fail");
    assert!(error.to_string().contains("generation prompts"), "{error}");

    let fixture = Fixture::new();
    let mut changed_mask_prompt = fixture.proposal_json();
    changed_mask_prompt["mask_instruction"] = json!("Highlight words related to the subject.");
    fixture.replace_proposal(&changed_mask_prompt);
    let error = load_verified_subject_mask_proposal(&fixture.proposal_path)
        .expect_err("changed mask prompt must fail");
    assert!(error.to_string().contains("generation prompts"), "{error}");
}

#[test]
fn subject_tui_selects_one_proposal_and_keeps_the_note_box_note_only() {
    let fixture = Fixture::new();
    let proposal =
        load_verified_subject_mask_proposal(&fixture.proposal_path).expect("verified proposal");
    let mut ui = ScriptedUi::with_actions([SubjectReviewAction::Pause], []);
    run_subject_mask_review(
        &fixture.proposal_path,
        &fixture.session_path,
        &fixture.approved_path,
        &mut ui,
    )
    .expect("build production subject screen");
    let screen = ui.subject_screens.remove(0);
    assert_eq!(screen.note, "pypush is serverless; pypush is open-source.");
    assert!(!screen.note.contains("Proposed subjects"));
    assert_eq!(proposal.note_count(), 2);
    assert_eq!(proposal.subject_count(), 3);

    let mut model = SubjectReviewTuiModel::new(screen);
    assert_eq!(
        model.handle_event(Event::Key(KeyEvent::new(KeyCode::Down, KeyModifiers::NONE))),
        SubjectReviewAction::None
    );
    assert_eq!(
        model.handle_event(Event::Key(KeyEvent::new(
            KeyCode::Char('a'),
            KeyModifiers::NONE
        ))),
        subject_approval(SUBJECT_2)
    );

    let backend = TestBackend::new(100, 32);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render subject review");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("Proposed subjects"), "{rendered}");
    assert!(
        normalized.contains("Serverless operation of pypush"),
        "{rendered}"
    );
    assert!(
        normalized.contains("Open-source availability of pypush"),
        "{rendered}"
    );
    assert!(normalized.contains("[A] Approve selected"), "{rendered}");
    assert!(normalized.contains("[R] Reject and explain"), "{rendered}");
}

#[test]
fn subject_tui_switches_to_a_distinct_completeness_question() {
    let screen = SubjectReviewScreen {
        heading: "SSE subject review · Note 1 of 1 · 2 of 2 decided".to_owned(),
        note: "pypush is serverless; pypush is open-source.".to_owned(),
        choices: vec![
            oracle_mvp::sse_mask_review::SubjectReviewChoice {
                subject_id: SUBJECT_1.to_owned(),
                label: "Serverless operation of pypush".to_owned(),
                outcome: Some(ReviewOutcome::Approved),
            },
            oracle_mvp::sse_mask_review::SubjectReviewChoice {
                subject_id: SUBJECT_2.to_owned(),
                label: "Open-source availability of pypush".to_owned(),
                outcome: Some(ReviewOutcome::Approved),
            },
        ],
        selected_index: 0,
    };
    let mut model = SubjectReviewTuiModel::new(screen);
    let backend = TestBackend::new(100, 32);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render completeness screen");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(
        normalized.contains(
            "Does this list include every narrow, independent subject explicitly discussed by this note?"
        ),
        "{rendered}"
    );
    assert!(normalized.contains("[Enter] List complete"), "{rendered}");
    assert!(
        normalized.contains("[M] Report missing subject"),
        "{rendered}"
    );
    assert!(!normalized.contains("[A] Approve selected"), "{rendered}");
}

fn write_json(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
