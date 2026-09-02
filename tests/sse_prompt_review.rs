use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use oracle_mvp::sse_mask_review::{
    AtomicSubjectCoverageDecision, AtomicSubjectDistinctnessDecision,
    AtomicSubjectNoteReviewAction, AtomicSubjectNoteReviewRunOutcome,
    AtomicSubjectNoteReviewTuiModel, AtomicSubjectNoteReviewUi, PromptReviewCounts,
    PromptReviewKind, PromptReviewRunOutcome, PromptReviewScreen, PromptReviewUi,
    run_atomic_subject_note_review, run_atomic_subject_prompt_review, run_claim_note_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const SUBJECT_PROMPT: &str = "Candidate atomic-subject prompt.";
const CODEX_VERSION: &str = "codex-cli test-version";
const SUBJECT_SCHEMA_SHA256: &str =
    "ffa0aa2d4a52a1b30f41f0a1761e455471a5127c0e20d74aaeea575a0df2226a";
const CLAIM_PROMPT: &str = "Candidate claim prompt.";
const CLAIM_SCHEMA_SHA256: &str =
    "1365a3d239f08657226fb771b8e7db48974882b8d580005de6e651d288be53a3";
const FIXTURE_NIP19: &str = "nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test";
const FIXTURE_QUERY_NIP19: &str = "npub1qqqqqqqqqqqqqqqqqqqq?relay=x";
const FIXTURE_COMBINING_BOUNDARY_NIP19: &str = "npub1pppppppppppppppppppp";
const SECOND_NOTE: &str = "Solar power will dominate future electricity generation. nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test nſec1ſſſſſſſſſſſſſſſſſſſſ npub1qqqqqqqqqqqqqqqqqqqq?relay=x\u{1c}tail \u{345}npub1pppppppppppppppppppp";

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn control_key(character: char) -> Event {
    Event::Key(KeyEvent::new(
        KeyCode::Char(character),
        KeyModifiers::CONTROL,
    ))
}

fn evidence_at(screen: &ApprovalScreen, index: usize) -> &ApprovalEvidence {
    match &screen.evidence {
        ApprovalEvidenceLayout::Paged(evidence) => &evidence[index],
        ApprovalEvidenceLayout::Stacked { top, bottom } => match index {
            0 => top,
            1 => bottom,
            _ => panic!("stacked evidence contains exactly two panels"),
        },
    }
}

struct Fixture {
    _temporary: tempfile::TempDir,
    run_directory: PathBuf,
    session_path: PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().expect("create fixture directory");
        let run_directory = temporary.path().join("generation");
        fs::create_dir(&run_directory).expect("create run directory");
        let input_path = temporary.path().join("notes.json");
        write_json(
            &input_path,
            &json!({
                "schema_version": 1,
                "notes": [
                    {
                        "note_id": format!("{:064x}", 1),
                        "text": "pypush is serverless; pypush is open-source."
                    },
                    {"note_id": format!("{:064x}", 2), "text": SECOND_NOTE}
                ]
            }),
        );
        let subject_registry_path = temporary.path().join("subject-prompts.json");
        write_json(
            &subject_registry_path,
            &json!({"atomic-subject-candidate-1": SUBJECT_PROMPT}),
        );
        let wrapper_path = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("sse_multivector")
            .join("codex_exec.py");
        write_json(
            &run_directory.join("manifest.json"),
            &json!({
                "schema_version": 1,
                "mode": "atomic_subject_generation",
                "wrapper_sha256": sha256(&fs::read(wrapper_path).expect("read wrapper")),
                "codex_binary": "/test/codex",
                "codex_version": CODEX_VERSION,
                "codex_home": "/test/codex-home",
                "input_path": input_path,
                "input_sha256": sha256(&fs::read(&input_path).expect("read input")),
                "subject_envelope_version": "xml-post-v1",
                "subject_input_normalization_version": "remove-long-ascii-nip19-identifiers-v2",
                "subject": {
                    "prompt_registry_path": subject_registry_path,
                    "prompt_registry_sha256": sha256(&fs::read(&subject_registry_path).expect("read subject registry")),
                    "prompt_version": "atomic-subject-candidate-1",
                    "prompt": SUBJECT_PROMPT,
                    "prompt_sha256": sha256(SUBJECT_PROMPT.as_bytes()),
                    "model": "candidate-subject-model",
                    "reasoning_effort": "high",
                    "response_schema": subject_schema(),
                    "response_schema_sha256": SUBJECT_SCHEMA_SHA256
                },
                "isolation": isolation_contract()
            }),
        );
        let fixture = Self {
            session_path: temporary.path().join("prompt-review-session.json"),
            _temporary: temporary,
            run_directory,
        };
        fixture.publish_output(default_output_notes());
        fixture
    }

    fn publish_output(&self, notes: Value) {
        self.publish_output_with_subject_prompt(notes, SUBJECT_PROMPT);
    }

    fn change_subject_prompt(&self) {
        let manifest_path = self.run_directory.join("manifest.json");
        let mut manifest = read_json(&manifest_path);
        let revised = "A revised candidate atomic-subject prompt.";
        let registry_path = PathBuf::from(
            manifest["subject"]["prompt_registry_path"]
                .as_str()
                .expect("subject registry path"),
        );
        write_json(
            &registry_path,
            &json!({"atomic-subject-candidate-1": revised}),
        );
        manifest["subject"]["prompt"] = json!(revised);
        manifest["subject"]["prompt_sha256"] = json!(sha256(revised.as_bytes()));
        manifest["subject"]["prompt_registry_sha256"] = json!(sha256(
            &fs::read(&registry_path).expect("read revised registry")
        ));
        write_json(&manifest_path, &manifest);
        let notes = read_json(&self.run_directory.join("output.json"))["notes"].clone();
        self.publish_output_with_subject_prompt(notes, revised);
    }

    fn publish_output_with_subject_prompt(&self, notes: Value, prompt: &str) {
        let manifest_path = self.run_directory.join("manifest.json");
        let manifest_sha256 = sha256(&fs::read(&manifest_path).expect("read manifest"));
        write_json(
            &self.run_directory.join("output.json"),
            &json!({"schema_version": 1, "manifest_sha256": manifest_sha256, "notes": notes}),
        );
        let manifest = read_json(&manifest_path);
        let input = read_json(Path::new(
            manifest["input_path"].as_str().expect("input path"),
        ));
        let note_text = input["notes"]
            .as_array()
            .expect("input notes")
            .iter()
            .map(|note| {
                (
                    note["note_id"].as_str().expect("input note ID"),
                    note["text"].as_str().expect("input note text"),
                )
            })
            .collect::<BTreeMap<_, _>>();
        let output = read_json(&self.run_directory.join("output.json"));
        let records = output["notes"]
            .as_array()
            .expect("output notes")
            .iter()
            .map(|note| {
                let note_id = note["note_id"].as_str().expect("note ID");
                let source = note_text[note_id];
                let response = Value::Array(
                    note["subjects"]
                        .as_array()
                        .expect("subjects")
                        .iter()
                        .map(|item| item["text"].clone())
                        .collect(),
                );
                succeeded_result(
                    &manifest,
                    &manifest_sha256,
                    note_id,
                    1,
                    &format!(
                        "{prompt}\n\n<post>\n{}\n</post>",
                        fixture_subject_input(source)
                    ),
                    response,
                )
            })
            .collect::<Vec<_>>();
        write_json_lines(&self.run_directory.join("results.jsonl"), &records);
    }
}

fn succeeded_result(
    manifest: &Value,
    manifest_sha256: &str,
    note_id: &str,
    attempt: u32,
    rendered_prompt: &str,
    response: Value,
) -> Value {
    let final_output = json!({"subjects": response});
    let final_output_raw = final_output.to_string();
    json!({
        "schema_version": 1,
        "manifest_sha256": manifest_sha256,
        "job_key": format!("subject:{note_id}"),
        "stage": "subject",
        "note_id": note_id,
        "attempt": attempt,
        "status": "succeeded",
        "wrapper_sha256": manifest["wrapper_sha256"],
        "codex_version": manifest["codex_version"],
        "model": manifest["subject"]["model"],
        "reasoning_effort": manifest["subject"]["reasoning_effort"],
        "prompt_sha256": sha256(rendered_prompt.as_bytes()),
        "response_schema_sha256": manifest["subject"]["response_schema_sha256"],
        "final_output_raw": final_output_raw,
        "final_output_sha256": sha256(final_output_raw.as_bytes()),
        "response": response
    })
}

fn fixture_subject_input(note: &str) -> String {
    note.replace(FIXTURE_NIP19, "")
        .replace(FIXTURE_QUERY_NIP19, "")
        .replace(FIXTURE_COMBINING_BOUNDARY_NIP19, "")
}

fn isolation_contract() -> Value {
    json!({
        "fresh_process_per_job": true,
        "ephemeral": true,
        "sterile_working_directory_per_job": true,
        "ignore_user_config": true,
        "ignore_rules": true,
        "approval_policy": "never",
        "sandbox": "read-only",
        "web_search": "disabled",
        "shell_environment_inherit": "none",
        "model_instructions": "Follow the user's instructions.\n",
        "model_instructions_sha256": "3d366e0253ede507e29be8ce00a9bd46ba2ebe7c01024bad45305bc0207fcfb1",
        "runtime_context_overrides": [
            "agents.enabled=false",
            "include_permissions_instructions=false",
            "include_apps_instructions=false",
            "include_collaboration_mode_instructions=false",
            "include_environment_context=false",
            "skills.include_instructions=false"
        ],
        "disabled_features": [
            "shell_tool", "unified_exec", "multi_agent", "apps", "plugins",
            "browser_use", "computer_use", "image_generation"
        ]
    })
}

fn subject_schema() -> Value {
    json!({
        "type": "object",
        "properties": {
            "subjects": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["subjects"],
        "additionalProperties": false
    })
}

fn default_output_notes() -> Value {
    json!([
        {
            "note_id": format!("{:064x}", 1),
            "text": "pypush is serverless; pypush is open-source.",
            "subjects": [
                {"source_index": 0, "text": "Serverless operation of pypush"},
                {"source_index": 1, "text": "Open-source availability of pypush"}
            ]
        },
        {
            "note_id": format!("{:064x}", 2),
            "text": SECOND_NOTE,
            "subjects": [
                {"source_index": 0, "text": "Future dominance of solar power generation"}
            ]
        }
    ])
}

struct ClaimFixture {
    _temporary: tempfile::TempDir,
    run_directory: PathBuf,
    session_path: PathBuf,
}

impl ClaimFixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().expect("create claim fixture directory");
        let run_directory = temporary.path().join("generation");
        fs::create_dir(&run_directory).expect("create claim run directory");
        let input_path = temporary.path().join("notes.json");
        let note_id = format!("{:064x}", 31);
        let note =
            "Balance Matter is a talk show on Magic 102.7, and it is a real thought provoker.";
        write_json(
            &input_path,
            &json!({
                "schema_version": 1,
                "notes": [{"note_id": note_id, "text": note}]
            }),
        );
        let registry_path = temporary.path().join("claim-prompts.json");
        write_json(&registry_path, &json!({"CP-test": CLAIM_PROMPT}));
        let wrapper_path = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("sse_multivector")
            .join("claim_exec.py");
        let engine_path = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("sse_multivector")
            .join("codex_exec.py");
        write_json(
            &run_directory.join("manifest.json"),
            &json!({
                "schema_version": 1,
                "mode": "claim_generation",
                "wrapper_sha256": sha256(&fs::read(wrapper_path).expect("read claim wrapper")),
                "engine_sha256": sha256(&fs::read(engine_path).expect("read shared engine")),
                "codex_binary": "/test/codex",
                "codex_version": CODEX_VERSION,
                "codex_home": "/test/codex-home",
                "input_path": input_path,
                "input_sha256": sha256(&fs::read(&input_path).expect("read claim input")),
                "claim_envelope_version": "exact-note-text-v1",
                "claim_input_normalization_version": "none-v1",
                "claim": {
                    "prompt_registry_path": registry_path,
                    "prompt_registry_sha256": sha256(&fs::read(&registry_path).expect("read claim registry")),
                    "prompt_version": "CP-test",
                    "prompt": CLAIM_PROMPT,
                    "prompt_sha256": sha256(CLAIM_PROMPT.as_bytes()),
                    "model": "candidate-claim-model",
                    "reasoning_effort": "low",
                    "response_schema": claim_schema(),
                    "response_schema_sha256": CLAIM_SCHEMA_SHA256
                },
                "isolation": isolation_contract()
            }),
        );
        let manifest_path = run_directory.join("manifest.json");
        let manifest = read_json(&manifest_path);
        let manifest_sha256 = sha256(&fs::read(&manifest_path).expect("read claim manifest"));
        let claims = json!([
            {"source_index": 0, "text": "Balance Matter is a talk show."},
            {"source_index": 1, "text": "Balance Matter airs on Magic 102.7."},
            {"source_index": 2, "text": "Balance Matter is a real thought provoker."}
        ]);
        write_json(
            &run_directory.join("output.json"),
            &json!({
                "schema_version": 1,
                "manifest_sha256": manifest_sha256,
                "notes": [{"note_id": note_id, "text": note, "claims": claims}]
            }),
        );
        let response = claims
            .as_array()
            .expect("claim array")
            .iter()
            .map(|claim| claim["text"].clone())
            .collect::<Vec<_>>();
        let final_output_raw = json!({"claims": response}).to_string();
        let rendered_prompt = format!("{CLAIM_PROMPT}\n\nText:\n{note}");
        write_json_lines(
            &run_directory.join("results.jsonl"),
            &[json!({
                "schema_version": 1,
                "manifest_sha256": manifest_sha256,
                "job_key": format!("claim:{note_id}"),
                "stage": "claim",
                "note_id": note_id,
                "attempt": 1,
                "status": "succeeded",
                "wrapper_sha256": manifest["wrapper_sha256"],
                "codex_version": manifest["codex_version"],
                "model": manifest["claim"]["model"],
                "reasoning_effort": manifest["claim"]["reasoning_effort"],
                "prompt_sha256": sha256(rendered_prompt.as_bytes()),
                "response_schema_sha256": manifest["claim"]["response_schema_sha256"],
                "final_output_raw": final_output_raw,
                "final_output_sha256": sha256(final_output_raw.as_bytes()),
                "response": response
            })],
        );
        Self {
            session_path: temporary.path().join("claim-review-session.json"),
            _temporary: temporary,
            run_directory,
        }
    }
}

fn claim_schema() -> Value {
    json!({
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["claims"],
        "additionalProperties": false
    })
}

struct ScriptedUi {
    actions: VecDeque<ApprovalTuiAction>,
    screens: Vec<PromptReviewScreen>,
}

impl ScriptedUi {
    fn new(actions: impl IntoIterator<Item = ApprovalTuiAction>) -> Self {
        Self {
            actions: actions.into_iter().collect(),
            screens: Vec::new(),
        }
    }
}

impl PromptReviewUi for ScriptedUi {
    fn review_prompt(&mut self, screen: PromptReviewScreen) -> io::Result<ApprovalTuiAction> {
        self.screens.push(screen);
        Ok(self
            .actions
            .pop_front()
            .expect("one action per prompt screen"))
    }
}

fn approved(comment: &str) -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: comment.to_owned(),
    }
}

fn rejected(comment: &str) -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Rejected,
        comment: comment.to_owned(),
    }
}

fn skipped(comment: &str) -> ApprovalTuiAction {
    ApprovalTuiAction::Skip {
        comment: comment.to_owned(),
    }
}

#[test]
fn subject_prompt_review_uses_flat_items_and_never_shows_masks() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([
        approved(""),
        skipped("Needs a clearer subject label"),
        ApprovalTuiAction::SaveComment {
            comment: "Potential missing subject".to_owned(),
        },
        ApprovalTuiAction::Pause,
    ]);

    let outcome =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
            .expect("run subject prompt review");

    assert_eq!(outcome, PromptReviewRunOutcome::Paused);
    assert_eq!(first.screens.len(), 4);
    let first_subject = first.screens[0].approval_screen();
    assert_eq!(
        first_subject.title.as_deref(),
        Some("Serverless operation of pypush")
    );
    assert_eq!(
        evidence_at(&first_subject, 0).body,
        "pypush is serverless; pypush is open-source."
    );
    assert!(!evidence_at(&first_subject, 0).body.contains('⟦'));
    assert_eq!(
        first_subject.scope,
        "Is this a valid atomic subject explicitly and substantively discussed in this note?"
    );
    let first_list = first.screens[2].approval_screen();
    assert!(first_list.title.is_none());
    assert_eq!(
        evidence_at(&first_list, 0).body,
        "pypush is serverless; pypush is open-source."
    );
    assert_eq!(evidence_at(&first_list, 1).title, "Accepted subjects");
    assert_eq!(
        evidence_at(&first_list, 1).body,
        "1. Serverless operation of pypush"
    );
    assert_eq!(first.screens[3].comment(), "Potential missing subject");

    let session = read_session(&fixture.session_path);
    assert!(session.get("notes").is_none());
    assert!(session.get("pairs").is_none());
    assert!(session.get("phase").is_none());
    assert!(!session.to_string().contains("mask"));
    assert_eq!(session["items"].as_array().expect("flat items").len(), 5);
    assert_eq!(session["items"][0]["status"], "approved");
    assert_eq!(session["items"][1]["status"], "skipped");
    assert_eq!(
        session["items"][1]["comment"],
        "Needs a clearer subject label"
    );
    assert_eq!(session["items"][2]["status"], "pending");
    assert_eq!(session["items"][2]["comment"], "Potential missing subject");

    let mut resumed = ScriptedUi::new([
        rejected("Potential missing subject"),
        approved("Useful control"),
        skipped("Not checking completeness yet"),
    ]);
    let outcome = run_atomic_subject_prompt_review(
        &fixture.run_directory,
        &fixture.session_path,
        &mut resumed,
    )
    .expect("resume subject prompt review");

    assert_eq!(
        outcome,
        PromptReviewRunOutcome::Completed {
            subjects: PromptReviewCounts {
                approved: 2,
                rejected: 0,
                skipped: 1,
            },
            subject_lists: PromptReviewCounts {
                approved: 0,
                rejected: 1,
                skipped: 1,
            },
        }
    );
    assert_eq!(resumed.screens.len(), 3);
}

#[test]
fn subject_list_review_shows_only_accepted_subjects_without_changing_prior_decisions() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = json!([
        {"source_index": 0, "text": "Serverless operation of pypush"},
        {"source_index": 1, "text": "Open-source availability of pypush"},
        {"source_index": 2, "text": "Software distribution"}
    ]);
    fixture.publish_output(notes);

    let mut first = ScriptedUi::new([
        approved(""),
        rejected("This is availability, not a separate subject"),
        skipped("Needs another look"),
        ApprovalTuiAction::Pause,
    ]);
    let outcome =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
            .expect("reach the subject-list review");

    assert_eq!(outcome, PromptReviewRunOutcome::Paused);
    let PromptReviewScreen::SubjectList { review, .. } = &first.screens[3] else {
        panic!("expected a subject-list review screen");
    };
    assert_eq!(review.note, "pypush is serverless; pypush is open-source.");
    assert_eq!(
        review.accepted_subjects,
        vec!["Serverless operation of pypush"]
    );
    let list = first.screens[3].approval_screen();
    assert_eq!(
        list.scope,
        "Are any atomic subjects missing, or do any accepted subjects express the same thing?"
    );
    assert!(list.title.is_none());
    assert_eq!(list.approve_label, "No — complete and distinct");
    assert_eq!(list.reject_label, "Yes — missing or repeated");
    assert!(matches!(
        list.evidence,
        ApprovalEvidenceLayout::Stacked { .. }
    ));
    assert_eq!(evidence_at(&list, 1).title, "Accepted subjects");
    assert_eq!(
        evidence_at(&list, 1).body,
        "1. Serverless operation of pypush"
    );
    assert_eq!(
        list.guidance.as_ref().expect("decision guidance").body,
        "This decision records only whether an atomic subject is missing or repeated. It does not change any earlier subject decision."
    );

    for (width, height) in [(72, 24), (100, 32)] {
        let mut model = ApprovalTuiModel::new_prompt_iteration(list.clone(), String::new());
        let backend = TestBackend::new(width, height);
        let mut terminal = Terminal::new(backend).expect("test terminal");
        terminal
            .draw(|frame| model.render(frame))
            .expect("render coverage review");
        let rendered = terminal
            .backend()
            .buffer()
            .content()
            .iter()
            .map(|cell| cell.symbol())
            .collect::<String>();
        let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
        assert!(normalized.contains("Note"), "{rendered}");
        assert!(normalized.contains("Accepted subjects"), "{rendered}");
        assert!(normalized.contains("Serverless operation"), "{rendered}");
        assert!(
            !normalized.contains("Open-source availability"),
            "{rendered}"
        );
        assert!(!normalized.contains("Software distribution"), "{rendered}");
        assert!(
            !normalized.contains("Missing or repeated subjects Missing"),
            "{rendered}"
        );
        assert!(
            normalized.contains("[A] No — complete and distinct"),
            "{rendered}"
        );
        assert!(
            normalized.contains("[R] Yes — missing or repeated"),
            "{rendered}"
        );
    }

    let mut resumed = ScriptedUi::new([approved(""), ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
        .expect("record the independent subject-list decision");
    let session = read_session(&fixture.session_path);
    assert_eq!(session["items"][0]["status"], "approved");
    assert_eq!(session["items"][1]["status"], "rejected");
    assert_eq!(session["items"][2]["status"], "skipped");
    assert_eq!(session["items"][3]["status"], "approved");
}

#[test]
fn subject_list_review_displays_only_accepted_subjects() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = json!([
        {"source_index": 0, "text": "Serverless operation of pypush"},
        {"source_index": 1, "text": "Open-source availability of pypush"},
        {"source_index": 2, "text": "Software distribution"}
    ]);
    fixture.publish_output(notes);

    let mut ui = ScriptedUi::new([
        approved(""),
        rejected("Not an atomic subject"),
        skipped("Needs another look"),
        ApprovalTuiAction::Pause,
    ]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("reach subject-list review");

    let PromptReviewScreen::SubjectList { review, .. } = &ui.screens[3] else {
        panic!("expected a subject-list review screen");
    };
    assert_eq!(
        review.accepted_subjects,
        vec!["Serverless operation of pypush"]
    );
    let list = ui.screens[3].approval_screen();
    assert_eq!(evidence_at(&list, 1).title, "Accepted subjects");
    assert_eq!(
        evidence_at(&list, 1).body,
        "1. Serverless operation of pypush"
    );
    let session = read_session(&fixture.session_path);
    assert_eq!(session["items"][1]["status"], "rejected");
    assert_eq!(session["items"][1]["comment"], "Not an atomic subject");
    assert_eq!(session["items"][2]["status"], "skipped");
    assert_eq!(session["items"][2]["comment"], "Needs another look");
}

#[test]
fn subject_prompt_review_refuses_to_resume_after_the_run_changes() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("create prompt review session");
    fixture.change_subject_prompt();

    let mut resumed = ScriptedUi::new([]);
    let error = run_atomic_subject_prompt_review(
        &fixture.run_directory,
        &fixture.session_path,
        &mut resumed,
    )
    .expect_err("a session must stay bound to one immutable generation run");
    assert!(
        error.to_string().contains("different generation run"),
        "{error}"
    );
}

#[test]
fn subject_prompt_review_resume_uses_the_prompt_frozen_in_the_manifest() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("create prompt review session");
    let manifest = read_json(&fixture.run_directory.join("manifest.json"));
    let registry_path = Path::new(
        manifest["subject"]["prompt_registry_path"]
            .as_str()
            .expect("subject registry path"),
    );
    let mut registry = read_json(registry_path);
    registry["a-later-prompt-version"] = json!("A later prompt.");
    write_json(registry_path, &registry);

    let mut resumed = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
        .expect("resume must not reread the mutable registry");
}

#[test]
fn subject_prompt_review_rejects_output_not_preserved_in_results() {
    let fixture = Fixture::new();
    let output_path = fixture.run_directory.join("output.json");
    let mut output = read_json(&output_path);
    output["notes"][0]["subjects"][0]["text"] = json!("Fabricated subject");
    write_json(&output_path, &output);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("review output must match the result ledger");
    assert!(error.to_string().contains("preserved result"), "{error}");
}

#[test]
fn subject_prompt_review_rejects_changed_source_text_in_output() {
    let fixture = Fixture::new();
    let output_path = fixture.run_directory.join("output.json");
    let mut output = read_json(&output_path);
    output["notes"][0]["text"] = json!("Changed note text");
    write_json(&output_path, &output);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("the output must preserve the exact source note");
    assert!(error.to_string().contains("source text"), "{error}");
}

#[test]
fn subject_prompt_review_rejects_invalid_source_indices() {
    let fixture = Fixture::new();
    let output_path = fixture.run_directory.join("output.json");
    let mut output = read_json(&output_path);
    output["notes"][0]["subjects"][1]["source_index"] = json!(7);
    write_json(&output_path, &output);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("source indices must preserve model order");
    assert!(error.to_string().contains("source index"), "{error}");
}

#[test]
fn subject_prompt_review_rejects_result_bound_to_another_prompt() {
    let fixture = Fixture::new();
    let results_path = fixture.run_directory.join("results.jsonl");
    let mut records = read_json_lines(&results_path);
    records[0]["prompt_sha256"] = json!("f".repeat(64));
    write_json_lines(&results_path, &records);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("the job must use the frozen prompt and note");
    assert!(error.to_string().contains("rendered prompt"), "{error}");
}

#[test]
fn subject_prompt_review_rejects_truncated_result_history() {
    let fixture = Fixture::new();
    let results_path = fixture.run_directory.join("results.jsonl");
    let mut records = read_json_lines(&results_path);
    records[0]["attempt"] = json!(2);
    write_json_lines(&results_path, &records);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("attempts must start at one and remain consecutive");
    assert!(
        error.to_string().contains("nonconsecutive attempt"),
        "{error}"
    );
}

#[test]
fn subject_prompt_review_requires_fresh_isolated_jobs() {
    let fixture = Fixture::new();
    let manifest_path = fixture.run_directory.join("manifest.json");
    let mut manifest = read_json(&manifest_path);
    manifest["isolation"]["fresh_process_per_job"] = json!(false);
    write_json(&manifest_path, &manifest);
    let notes = read_json(&fixture.run_directory.join("output.json"))["notes"].clone();
    fixture.publish_output(notes);
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("every prompt must use a fresh isolated process");
    assert!(error.to_string().contains("fresh process"), "{error}");
}

#[test]
fn subject_prompt_review_surfaces_empty_and_duplicate_lists() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = json!([]);
    fixture.publish_output(notes);
    let mut empty = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut empty)
        .expect("show empty generated subject list");
    let empty_list = empty.screens[0].approval_screen();
    assert!(empty_list.title.is_none());
    assert_eq!(
        evidence_at(&empty_list, 1).body,
        "No accepted atomic subjects."
    );

    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"][1]["text"] = notes[0]["subjects"][0]["text"].clone();
    fixture.publish_output(notes);
    let mut duplicate = ScriptedUi::new([approved(""), approved(""), ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(
        &fixture.run_directory,
        &fixture.session_path,
        &mut duplicate,
    )
    .expect("show duplicate generated labels for review");
    let duplicate_list = duplicate.screens[2].approval_screen();
    let list = &evidence_at(&duplicate_list, 1).body;
    assert_eq!(list.matches("Serverless operation of pypush").count(), 2);
}

#[test]
fn subject_list_review_hides_disapproved_and_skipped_subjects_but_preserves_their_decisions() {
    let fixture = Fixture::new();
    let mut ui = ScriptedUi::new([
        rejected("Not a substantive subject"),
        skipped("Needs another look"),
        ApprovalTuiAction::Pause,
    ]);

    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("reach subject-list review");

    let PromptReviewScreen::SubjectList { review, .. } = &ui.screens[2] else {
        panic!("expected a subject-list review screen");
    };
    assert!(review.accepted_subjects.is_empty());
    let list = ui.screens[2].approval_screen();
    assert_eq!(evidence_at(&list, 1).title, "Accepted subjects");
    assert_eq!(evidence_at(&list, 1).body, "No accepted atomic subjects.");
    let session = read_session(&fixture.session_path);
    assert_eq!(session["items"][0]["status"], "rejected");
    assert_eq!(session["items"][0]["comment"], "Not a substantive subject");
    assert_eq!(session["items"][1]["status"], "skipped");
    assert_eq!(session["items"][1]["comment"], "Needs another look");
}

#[test]
fn subject_prompt_review_stops_without_complete_output() {
    let fixture = Fixture::new();
    fs::remove_file(fixture.run_directory.join("output.json")).expect("remove output");
    let mut ui = ScriptedUi::new([]);
    let error =
        run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("a failed generation run must stop before review");
    assert!(error.to_string().contains("output.json"), "{error}");
}

struct ScriptedNoteUi {
    actions: VecDeque<AtomicSubjectNoteReviewAction>,
    screens: Vec<oracle_mvp::sse_mask_review::AtomicSubjectNoteReviewScreen>,
    drain_requests: Vec<bool>,
}

impl ScriptedNoteUi {
    fn new(actions: impl IntoIterator<Item = AtomicSubjectNoteReviewAction>) -> Self {
        Self {
            actions: actions.into_iter().collect(),
            screens: Vec::new(),
            drain_requests: Vec::new(),
        }
    }
}

impl AtomicSubjectNoteReviewUi for ScriptedNoteUi {
    fn review_note(
        &mut self,
        model: &mut AtomicSubjectNoteReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<AtomicSubjectNoteReviewAction> {
        self.screens.push(model.screen().clone());
        self.drain_requests.push(drain_stale_input);
        Ok(self
            .actions
            .pop_front()
            .expect("one action per note-workspace iteration"))
    }
}

#[test]
fn claim_review_uses_claim_artifacts_and_claim_questions() {
    let fixture = ClaimFixture::new();
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);

    let outcome = run_claim_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("open claim review");

    assert_eq!(outcome, AtomicSubjectNoteReviewRunOutcome::Paused);
    let screen = &ui.screens[0];
    assert_eq!(screen.kind, PromptReviewKind::Claim);
    assert_eq!(
        screen
            .subjects
            .iter()
            .map(|claim| claim.label.as_str())
            .collect::<Vec<_>>(),
        [
            "Balance Matter is a talk show.",
            "Balance Matter airs on Magic 102.7.",
            "Balance Matter is a real thought provoker.",
        ]
    );

    let mut model = AtomicSubjectNoteReviewTuiModel::new(screen.clone());
    let backend = TestBackend::new(72, 24);
    let mut terminal = Terminal::new(backend).expect("claim review terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render claim row");
    let rendered = rendered_terminal(&terminal);
    assert!(
        rendered.contains(
            "Is this one self-contained claim made by the note without added information?"
        ),
        "{rendered}"
    );
    assert!(!rendered.contains("subject"), "{rendered}");

    for _ in 0..screen.subjects.len() {
        assert_eq!(
            model.handle_event(key(KeyCode::Down)),
            AtomicSubjectNoteReviewAction::None
        );
    }
    terminal
        .draw(|frame| model.render(frame))
        .expect("render claim coverage row");
    let rendered = rendered_terminal(&terminal);
    assert!(
        rendered.contains("Do the approved claims include every claim made by the note?"),
        "{rendered}"
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    terminal
        .draw(|frame| model.render(frame))
        .expect("render claim distinctness row");
    let rendered = rendered_terminal(&terminal);
    assert!(
        rendered.contains("Do the approved claims express different claims?"),
        "{rendered}"
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        AtomicSubjectNoteReviewAction::None
    );
    terminal
        .draw(|frame| model.render(frame))
        .expect("render claim help");
    let rendered = rendered_terminal(&terminal);
    assert!(rendered.contains("Claim review help"), "{rendered}");
    assert!(rendered.contains("another proposed claim"), "{rendered}");
    assert!(!rendered.contains("subject"), "{rendered}");

    let session = read_session(&fixture.session_path);
    assert_eq!(session["review_protocol"], "claim-review-v1");
    assert!(session["notes"][0].get("claims").is_some());
    assert!(session["notes"][0].get("subjects").is_none());
}

fn rendered_terminal(terminal: &Terminal<TestBackend>) -> String {
    terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

#[test]
fn note_review_opens_one_workspace_with_every_proposal_for_the_note() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = json!([
        {"source_index": 0, "text": "Serverless operation of pypush"},
        {"source_index": 1, "text": "Open-source availability of pypush"},
        {"source_index": 2, "text": "Cross-platform messaging with pypush"}
    ]);
    fixture.publish_output(notes);
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);

    let outcome =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect("open note-centered review");

    assert_eq!(outcome, AtomicSubjectNoteReviewRunOutcome::Paused);
    assert_eq!(ui.screens.len(), 1);
    let screen = &ui.screens[0];
    assert_eq!(screen.note_index, 0);
    assert_eq!(screen.note_count, 2);
    assert_eq!(screen.note, "pypush is serverless; pypush is open-source.");
    assert_eq!(
        screen
            .subjects
            .iter()
            .map(|subject| subject.label.as_str())
            .collect::<Vec<_>>(),
        [
            "Serverless operation of pypush",
            "Open-source availability of pypush",
            "Cross-platform messaging with pypush",
        ]
    );
    assert!(
        screen
            .subjects
            .iter()
            .all(|subject| subject.outcome.is_none())
    );
    assert!(screen.coverage.is_none());
    assert!(screen.distinctness.is_none());

    let session = read_session(&fixture.session_path);
    assert_eq!(session["schema_version"], 2);
    assert_eq!(session["notes"].as_array().expect("note states").len(), 2);
    assert!(session.get("items").is_none());
}

#[test]
fn note_review_keeps_decisions_editable_and_records_list_problems_separately() {
    let fixture = Fixture::new();
    let mut ui = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 1,
            outcome: ReviewOutcome::Rejected,
        },
        AtomicSubjectNoteReviewAction::SaveSubjectComment {
            subject_index: 1,
            comment: "Incidental property".to_owned(),
        },
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 1,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Missing,
        },
        AtomicSubjectNoteReviewAction::SaveCoverageComment {
            comment: "Missing software distribution".to_owned(),
        },
        AtomicSubjectNoteReviewAction::DecideDistinctness {
            decision: AtomicSubjectDistinctnessDecision::Repeated,
        },
        AtomicSubjectNoteReviewAction::SaveDistinctnessComment {
            comment: "Subjects 1 and 2 overlap".to_owned(),
        },
        AtomicSubjectNoteReviewAction::FinishNote,
        AtomicSubjectNoteReviewAction::Pause,
    ]);

    let outcome =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect("review and revise one note");

    assert_eq!(outcome, AtomicSubjectNoteReviewRunOutcome::Paused);
    assert!(ui.screens[..9].iter().all(|screen| screen.note_index == 0));
    assert_eq!(ui.screens[9].note_index, 1);
    assert_eq!(
        ui.screens[2].selected_index, 1,
        "a disapproved subject stays selected so C comments on that subject"
    );
    assert_eq!(
        ui.screens[5].selected_index,
        ui.screens[5].subjects.len(),
        "a missing-subject decision stays selected so C comments on Coverage"
    );
    assert_eq!(
        ui.drain_requests,
        [
            true, false, false, false, false, false, false, false, false, false
        ]
    );

    let session = read_session(&fixture.session_path);
    let first = &session["notes"][0];
    assert_eq!(first["subjects"][0]["outcome"], "approved");
    assert_eq!(first["subjects"][1]["outcome"], "approved");
    assert_eq!(
        first["subjects"][1]["comment"], "Incidental property",
        "changing a decision must not erase its optional comment"
    );
    assert_eq!(first["coverage"], "missing");
    assert_eq!(first["coverage_comment"], "Missing software distribution");
    assert_eq!(first["distinctness"], "repeated");
    assert_eq!(first["distinctness_comment"], "Subjects 1 and 2 overlap");
    assert_eq!(first["finished"], true);
}

#[test]
fn legacy_flat_session_migrates_without_guessing_why_a_list_was_rejected() {
    let fixture = Fixture::new();
    let mut legacy = ScriptedUi::new([
        approved("Useful"),
        rejected("Incidental"),
        rejected("One of the list checks failed"),
        ApprovalTuiAction::Pause,
    ]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut legacy)
        .expect("create a legacy flat session");

    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("migrate the legacy session");

    let session = read_session(&fixture.session_path);
    let backup_path = PathBuf::from(format!("{}.v1-backup", fixture.session_path.display()));
    let backup = read_session(&backup_path);
    assert_eq!(backup["schema_version"], 1);
    assert_eq!(backup["review_protocol"], "atomic-subject-review-v1");
    assert_eq!(session["schema_version"], 2);
    assert_eq!(session["notes"][0]["subjects"][0]["outcome"], "approved");
    assert_eq!(session["notes"][0]["subjects"][0]["comment"], "Useful");
    assert_eq!(session["notes"][0]["subjects"][1]["outcome"], "rejected");
    assert_eq!(session["notes"][0]["subjects"][1]["comment"], "Incidental");
    assert!(session["notes"][0]["coverage"].is_null());
    assert!(session["notes"][0]["distinctness"].is_null());
    assert_eq!(
        session["notes"][0]["prior_combined_check"]["status"],
        "rejected"
    );
    assert_eq!(
        session["notes"][0]["prior_combined_check"]["comment"],
        "One of the list checks failed"
    );
    assert_eq!(
        session["notes"][0]["selected_index"], 2,
        "an unresolved legacy list check resumes on Coverage"
    );
    assert_eq!(
        ui.screens[0].note_index, 1,
        "resume at the legacy pending item"
    );
}

#[test]
fn legacy_migration_restores_the_exact_pending_subject() {
    let fixture = Fixture::new();
    let mut legacy = ScriptedUi::new([approved("Reviewed"), ApprovalTuiAction::Pause]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut legacy)
        .expect("create a partially reviewed legacy note");

    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("resume the exact pending proposal");

    assert_eq!(ui.screens[0].note_index, 0);
    assert_eq!(ui.screens[0].selected_index, 1);
    assert_eq!(
        ui.screens[0].subjects[1].label,
        "Open-source availability of pypush"
    );
}

#[test]
fn legacy_migration_preserves_approved_and_pending_list_comments() {
    let approved_fixture = Fixture::new();
    let mut approved_legacy = ScriptedUi::new([
        approved(""),
        approved(""),
        approved("Reviewed as one list"),
        ApprovalTuiAction::Pause,
    ]);
    run_atomic_subject_prompt_review(
        &approved_fixture.run_directory,
        &approved_fixture.session_path,
        &mut approved_legacy,
    )
    .expect("create approved legacy list");
    let mut approved_ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(
        &approved_fixture.run_directory,
        &approved_fixture.session_path,
        &mut approved_ui,
    )
    .expect("migrate approved legacy list");
    let approved_session = read_session(&approved_fixture.session_path);
    assert_eq!(approved_session["notes"][0]["finished"], true);
    assert_eq!(
        approved_session["notes"][0]["prior_combined_check"]["status"],
        "approved"
    );
    assert_eq!(
        approved_session["notes"][0]["prior_combined_check"]["comment"],
        "Reviewed as one list"
    );

    let pending_fixture = Fixture::new();
    let mut pending_legacy = ScriptedUi::new([
        approved(""),
        approved(""),
        ApprovalTuiAction::SaveComment {
            comment: "Still considering coverage".to_owned(),
        },
        ApprovalTuiAction::Pause,
    ]);
    run_atomic_subject_prompt_review(
        &pending_fixture.run_directory,
        &pending_fixture.session_path,
        &mut pending_legacy,
    )
    .expect("create pending legacy list comment");
    let mut pending_ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(
        &pending_fixture.run_directory,
        &pending_fixture.session_path,
        &mut pending_ui,
    )
    .expect("migrate pending legacy list comment");
    let pending_session = read_session(&pending_fixture.session_path);
    assert_eq!(
        pending_session["notes"][0]["prior_combined_check"]["status"],
        "pending"
    );
    assert_eq!(
        pending_session["notes"][0]["prior_combined_check"]["comment"],
        "Still considering coverage"
    );
    assert_eq!(pending_session["notes"][0]["selected_index"], 2);
}

#[test]
fn legacy_migration_reopens_skipped_decisions_without_losing_comments() {
    let fixture = Fixture::new();
    let mut legacy = ScriptedUi::new([
        skipped("Subject needs another look"),
        approved(""),
        skipped("List needs another look"),
        ApprovalTuiAction::Pause,
    ]);
    run_atomic_subject_prompt_review(&fixture.run_directory, &fixture.session_path, &mut legacy)
        .expect("create skipped legacy decisions");

    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("migrate skipped legacy decisions");
    let session = read_session(&fixture.session_path);
    assert!(session["notes"][0]["subjects"][0]["outcome"].is_null());
    assert_eq!(
        session["notes"][0]["subjects"][0]["comment"],
        "Subject needs another look"
    );
    assert_eq!(session["notes"][0]["subjects"][1]["outcome"], "approved");
    assert_eq!(
        session["notes"][0]["prior_combined_check"]["status"],
        "skipped"
    );
    assert_eq!(
        session["notes"][0]["prior_combined_check"]["comment"],
        "List needs another look"
    );
    assert_eq!(session["notes"][0]["selected_index"], 0);
}

#[test]
fn note_review_resume_restores_exact_v2_position_decisions_comments_and_progress() {
    let fixture = Fixture::new();
    let mut first = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::SaveSubjectComment {
            subject_index: 0,
            comment: "Good subject".to_owned(),
        },
        AtomicSubjectNoteReviewAction::Pause,
    ]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("pause a v2 review mid-note");

    let mut resumed = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
        .expect("resume a v2 review");
    let screen = &resumed.screens[0];
    assert_eq!(screen.note_index, 0);
    assert_eq!(screen.selected_index, 0);
    assert_eq!(screen.subjects[0].outcome, Some(ReviewOutcome::Approved));
    assert_eq!(screen.subjects[0].comment, "Good subject");
    assert_eq!(screen.decided_review_count, 1);
    assert_eq!(screen.total_review_count, 7);
}

#[test]
fn note_review_refuses_to_resume_after_the_generation_run_changes() {
    let fixture = Fixture::new();
    let mut first = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("create v2 session");
    fixture.change_subject_prompt();

    let mut resumed = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    let error =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
            .expect_err("v2 session must stay bound to its generation run");
    assert!(
        error.to_string().contains("different generation run"),
        "{error}"
    );
}

#[test]
fn note_workspace_renders_context_progress_and_controls_at_minimum_size() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = Value::Array(
        (0..11)
            .map(|index| {
                json!({
                    "source_index": index,
                    "text": format!("Long proposed atomic subject {} with enough detail to wrap cleanly", index + 1)
                })
            })
            .collect(),
    );
    fixture.publish_output(notes);
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("build note workspace screen");
    let mut model = AtomicSubjectNoteReviewTuiModel::new(ui.screens.remove(0));
    for _ in 0..10 {
        assert_eq!(
            model.handle_event(key(KeyCode::Down)),
            AtomicSubjectNoteReviewAction::None
        );
    }

    let backend = TestBackend::new(72, 24);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render note workspace");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("Note 1/2"), "{rendered}");
    assert!(normalized.contains("pypush is serverless"), "{rendered}");
    assert!(
        normalized.contains("Long proposed atomic subject 11"),
        "{rendered}"
    );
    assert!(normalized.contains("[A] Approve"), "{rendered}");
    assert!(normalized.contains("[R] Disapprove"), "{rendered}");
    assert!(normalized.contains("Save/exit"), "{rendered}");
    assert!(!normalized.contains("Skip"), "{rendered}");

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    terminal
        .draw(|frame| model.render(frame))
        .expect("render note-level checks");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("Coverage"), "{rendered}");
    assert!(
        normalized.contains("Do the approved subjects cover every atomic subject in the note?"),
        "{rendered}"
    );
    assert!(normalized.contains("[A] Complete"), "{rendered}");
    assert!(normalized.contains("[R] Missing"), "{rendered}");

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    terminal
        .draw(|frame| model.render(frame))
        .expect("render distinctness check");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("Distinctness"), "{rendered}");
    assert!(
        normalized.contains("Do the approved subjects express different meanings?"),
        "{rendered}"
    );
    assert!(normalized.contains("[A] Distinct"), "{rendered}");
    assert!(normalized.contains("[R] Repeated"), "{rendered}");
}

#[test]
fn note_review_cannot_finish_without_explicit_coverage_and_distinctness_decisions() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["subjects"] = json!([]);
    fixture.publish_output(notes);
    let mut ui = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::FinishNote,
        AtomicSubjectNoteReviewAction::Pause,
    ]);

    let error =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("both note-level checks must be explicit, even for an empty list");

    assert!(error.to_string().contains("coverage"), "{error}");
    let session = read_session(&fixture.session_path);
    assert_eq!(session["notes"][0]["finished"], false);
    assert!(session["notes"][0]["coverage"].is_null());
    assert!(session["notes"][0]["distinctness"].is_null());
}

#[test]
fn note_workspace_reviews_coverage_and_distinctness_as_independent_rows() {
    let fixture = Fixture::new();
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("build note workspace screen");
    let mut model = AtomicSubjectNoteReviewTuiModel::new(ui.screens.remove(0));

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('a'))),
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Complete,
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Missing,
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('c'))),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('x'))),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        AtomicSubjectNoteReviewAction::SaveCoverageComment {
            comment: "x".to_owned(),
        }
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('a'))),
        AtomicSubjectNoteReviewAction::DecideDistinctness {
            decision: AtomicSubjectDistinctnessDecision::Distinct,
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        AtomicSubjectNoteReviewAction::DecideDistinctness {
            decision: AtomicSubjectDistinctnessDecision::Repeated,
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('u'))),
        AtomicSubjectNoteReviewAction::ClearDistinctness
    );
}

#[test]
fn completed_note_review_reopens_for_edits() {
    let fixture = Fixture::new();
    let mut first = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 1,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Complete,
        },
        AtomicSubjectNoteReviewAction::DecideDistinctness {
            decision: AtomicSubjectDistinctnessDecision::Distinct,
        },
        AtomicSubjectNoteReviewAction::FinishNote,
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Approved,
        },
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Complete,
        },
        AtomicSubjectNoteReviewAction::DecideDistinctness {
            decision: AtomicSubjectDistinctnessDecision::Distinct,
        },
        AtomicSubjectNoteReviewAction::FinishNote,
        AtomicSubjectNoteReviewAction::Pause,
    ]);
    let outcome =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut first)
            .expect("complete note review");
    assert_eq!(
        outcome,
        AtomicSubjectNoteReviewRunOutcome::Completed {
            subjects: PromptReviewCounts {
                approved: 3,
                rejected: 0,
                skipped: 0,
            },
            notes_missing_subjects: 0,
            notes_with_repeated_subjects: 0,
        }
    );
    assert!(first.screens.last().expect("final screen").finished);

    let mut finished_model = AtomicSubjectNoteReviewTuiModel::new(
        first.screens.last().expect("finished screen").clone(),
    );
    let backend = TestBackend::new(100, 32);
    let mut terminal = Terminal::new(backend).expect("normal-size test terminal");
    terminal
        .draw(|frame| finished_model.render(frame))
        .expect("render completed review");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("All notes finished"), "{rendered}");
    assert!(!normalized.contains("[Enter]"), "{rendered}");

    let mut unchanged = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::DecideCoverage {
            decision: AtomicSubjectCoverageDecision::Complete,
        },
        AtomicSubjectNoteReviewAction::Pause,
    ]);
    let outcome = run_atomic_subject_note_review(
        &fixture.run_directory,
        &fixture.session_path,
        &mut unchanged,
    )
    .expect("repeat a completed decision");
    assert!(matches!(
        outcome,
        AtomicSubjectNoteReviewRunOutcome::Completed { .. }
    ));
    assert_eq!(
        read_session(&fixture.session_path)["notes"][1]["finished"],
        true
    );

    let mut resumed = ScriptedNoteUi::new([
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Rejected,
        },
        AtomicSubjectNoteReviewAction::Pause,
    ]);
    let outcome =
        run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
            .expect("reopen completed review");

    assert_eq!(outcome, AtomicSubjectNoteReviewRunOutcome::Paused);
    assert!(resumed.screens[0].finished);
    let session = read_session(&fixture.session_path);
    assert_eq!(session["notes"][1]["subjects"][0]["outcome"], "rejected");
    assert_eq!(session["notes"][1]["finished"], false);
    assert!(session["notes"][1]["coverage"].is_null());
    assert!(session["notes"][1]["distinctness"].is_null());
}

#[test]
fn note_workspace_help_shows_only_help_controls() {
    let fixture = Fixture::new();
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("build note workspace screen");
    let mut model = AtomicSubjectNoteReviewTuiModel::new(ui.screens.remove(0));
    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        AtomicSubjectNoteReviewAction::None
    );

    let backend = TestBackend::new(72, 24);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render note workspace help");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(
        normalized.contains("Atomic-subject review help"),
        "{rendered}"
    );
    assert!(normalized.contains("Close help"), "{rendered}");
    assert!(normalized.contains("Half-page"), "{rendered}");
    assert!(!normalized.contains("[A] Approve"), "{rendered}");
}

#[test]
fn note_workspace_marks_clipped_comments_and_exposes_editor_navigation() {
    let fixture = Fixture::new();
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("build note workspace screen");
    let mut screen = ui.screens.remove(0);
    screen.subjects[0].comment = "long reviewer comment ".repeat(12);
    let mut model = AtomicSubjectNoteReviewTuiModel::new(screen);

    let backend = TestBackend::new(72, 24);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render clipped comment");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    assert!(rendered.contains('…'), "{rendered}");

    assert_eq!(
        model.handle_event(key(KeyCode::Char('c'))),
        AtomicSubjectNoteReviewAction::None
    );
    terminal
        .draw(|frame| model.render(frame))
        .expect("render comment editor");
    let rendered = terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("[Home/End] Ends"), "{rendered}");
}

#[test]
fn note_workspace_comments_are_optional_editable_and_clearable() {
    let fixture = Fixture::new();
    let mut ui = ScriptedNoteUi::new([AtomicSubjectNoteReviewAction::Pause]);
    run_atomic_subject_note_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("build note workspace screen");
    let mut model = AtomicSubjectNoteReviewTuiModel::new(ui.screens.remove(0));

    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        AtomicSubjectNoteReviewAction::DecideSubject {
            subject_index: 0,
            outcome: ReviewOutcome::Rejected,
        },
        "disapproval does not force a comment modal"
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('c'))),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('x'))),
        AtomicSubjectNoteReviewAction::None,
        "ordinary x remains editable text"
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        AtomicSubjectNoteReviewAction::SaveSubjectComment {
            subject_index: 0,
            comment: "x".to_owned(),
        }
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Char('c'))),
        AtomicSubjectNoteReviewAction::None
    );
    assert_eq!(
        model.handle_event(control_key('k')),
        AtomicSubjectNoteReviewAction::SaveSubjectComment {
            subject_index: 0,
            comment: String::new(),
        }
    );
}

fn read_session(path: &Path) -> Value {
    read_json(path)["session"].clone()
}

fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).expect("read JSON")).expect("decode JSON")
}

fn read_json_lines(path: &Path) -> Vec<Value> {
    fs::read_to_string(path)
        .expect("read JSONL")
        .lines()
        .map(|line| serde_json::from_str(line).expect("decode JSONL line"))
        .collect()
}

fn write_json_lines(path: &Path, values: &[Value]) {
    let mut text = values
        .iter()
        .map(Value::to_string)
        .collect::<Vec<_>>()
        .join("\n");
    text.push('\n');
    fs::write(path, text).expect("write JSONL");
}

fn write_json(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
