use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use oracle_mvp::sse_mask_review::{
    PromptReviewCounts, PromptReviewRunOutcome, PromptReviewScreen, PromptReviewUi,
    run_atomic_subject_prompt_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const SUBJECT_PROMPT: &str = "Candidate atomic-subject prompt.";
const CODEX_VERSION: &str = "codex-cli test-version";
const SUBJECT_SCHEMA_SHA256: &str =
    "ffa0aa2d4a52a1b30f41f0a1761e455471a5127c0e20d74aaeea575a0df2226a";
const FIXTURE_NIP19: &str = "nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test";
const FIXTURE_QUERY_NIP19: &str = "npub1qqqqqqqqqqqqqqqqqqqq?relay=x";
const FIXTURE_COMBINING_BOUNDARY_NIP19: &str = "npub1pppppppppppppppppppp";
const SECOND_NOTE: &str = "Solar power will dominate future electricity generation. nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test nſec1ſſſſſſſſſſſſſſſſſſſſ npub1qqqqqqqqqqqqqqqqqqqq?relay=x\u{1c}tail \u{345}npub1pppppppppppppppppppp";

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
