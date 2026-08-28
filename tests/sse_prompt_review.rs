use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::ApprovalTuiAction;
use oracle_mvp::sse_mask_review::{
    PromptReviewCounts, PromptReviewRunOutcome, PromptReviewScreen, PromptReviewUi,
    run_subject_mask_prompt_review,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const SUBJECT_PROMPT: &str = "Candidate atomic-subject prompt.";
const MASK_PROMPT: &str = "Candidate atomic-subject mask prompt with {POST} and {TAKEAWAY}.";
const CODEX_VERSION: &str = "codex-cli test-version";
const TAKEAWAY_SCHEMA_SHA256: &str =
    "81840eb6f10337de473a8ba0698b7549107857321deb1fc59d6e1c9e10fceb90";
const MASK_SCHEMA_SHA256: &str = "8a6b8dbcba24d155a62f55d30a5bd038c0144f99fa4af9c3d72dcb5541dd3b43";
const FIXTURE_NIP19: &str = "nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test";
const FIXTURE_QUERY_NIP19: &str = "npub1qqqqqqqqqqqqqqqqqqqq?relay=x";
const FIXTURE_COMBINING_BOUNDARY_NIP19: &str = "npub1pppppppppppppppppppp";
const SECOND_NOTE: &str = "Solar power will dominate future electricity generation. nostr:npub1qqqqqqqqqqqqqqqqqqqq?relay=test nſec1ſſſſſſſſſſſſſſſſſſſſ npub1qqqqqqqqqqqqqqqqqqqq?relay=x\u{1c}tail \u{345}npub1pppppppppppppppppppp";

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
                    {
                        "note_id": format!("{:064x}", 2),
                        "text": SECOND_NOTE
                    }
                ]
            }),
        );
        let takeaway_registry_path = temporary.path().join("takeaway-prompts.json");
        let mask_registry_path = temporary.path().join("mask-prompts.json");
        write_json(
            &takeaway_registry_path,
            &json!({"atomic-subject-candidate-1": SUBJECT_PROMPT}),
        );
        write_json(
            &mask_registry_path,
            &json!({"atomic-mask-candidate-1": MASK_PROMPT}),
        );
        let wrapper_path = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("sse_multivector")
            .join("codex_exec.py");
        write_json(
            &run_directory.join("manifest.json"),
            &json!({
                "schema_version": 1,
                "wrapper_sha256": sha256(&fs::read(wrapper_path).expect("read wrapper")),
                "codex_binary": "/test/codex",
                "codex_version": CODEX_VERSION,
                "codex_home": "/test/codex-home",
                "input_path": input_path,
                "input_sha256": sha256(&fs::read(&input_path).expect("read input")),
                "takeaway_envelope_version": "xml-post-v1",
                "takeaway_input_normalization_version": "remove-long-ascii-nip19-identifiers-v2",
                "takeaway": {
                    "prompt_registry_path": takeaway_registry_path,
                    "prompt_registry_sha256": sha256(&fs::read(&takeaway_registry_path).expect("read takeaway registry")),
                    "prompt_version": "atomic-subject-candidate-1",
                    "prompt": SUBJECT_PROMPT,
                    "prompt_sha256": sha256(SUBJECT_PROMPT.as_bytes()),
                    "model": "candidate-subject-model",
                    "reasoning_effort": "high",
                    "response_schema": takeaway_schema(),
                    "response_schema_sha256": TAKEAWAY_SCHEMA_SHA256
                },
                "mask": {
                    "prompt_registry_path": mask_registry_path,
                    "prompt_registry_sha256": sha256(&fs::read(&mask_registry_path).expect("read mask registry")),
                    "prompt_version": "atomic-mask-candidate-1",
                    "prompt": MASK_PROMPT,
                    "prompt_sha256": sha256(MASK_PROMPT.as_bytes()),
                    "model": "candidate-mask-model",
                    "reasoning_effort": "medium",
                    "response_schema": mask_schema(),
                    "response_schema_sha256": MASK_SCHEMA_SHA256
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
        let mut manifest = read_json(&self.run_directory.join("manifest.json"));
        let revised = "A revised candidate atomic-subject prompt.";
        let registry_path = PathBuf::from(
            manifest["takeaway"]["prompt_registry_path"]
                .as_str()
                .expect("takeaway registry path"),
        );
        write_json(
            &registry_path,
            &json!({"atomic-subject-candidate-1": revised}),
        );
        manifest["takeaway"]["prompt"] = json!(revised);
        manifest["takeaway"]["prompt_sha256"] = json!(sha256(revised.as_bytes()));
        manifest["takeaway"]["prompt_registry_sha256"] = json!(sha256(
            &fs::read(&registry_path).expect("read revised registry")
        ));
        write_json(&self.run_directory.join("manifest.json"), &manifest);
        let notes = read_json(&self.run_directory.join("output.json"))["notes"].clone();
        self.publish_output_with_subject_prompt(notes, revised);
    }

    fn publish_output_with_subject_prompt(&self, notes: Value, prompt: &str) {
        let manifest_path = self.run_directory.join("manifest.json");
        let manifest_sha256 = sha256(&fs::read(&manifest_path).expect("read manifest"));
        write_json(
            &self.run_directory.join("output.json"),
            &json!({
                "schema_version": 1,
                "manifest_sha256": manifest_sha256,
                "notes": notes
            }),
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
        let mut records = Vec::new();
        for note in output["notes"].as_array().expect("output notes") {
            let note_id = note["note_id"].as_str().expect("note ID");
            let source = note_text[note_id];
            let takeaways = note["takeaways"].as_array().expect("takeaways");
            let response =
                Value::Array(takeaways.iter().map(|item| item["text"].clone()).collect());
            records.push(succeeded_result(
                &manifest,
                &manifest_sha256,
                "takeaway",
                note_id,
                None,
                1,
                &format!(
                    "{prompt}\n\n<post>\n{}\n</post>",
                    fixture_takeaway_input(source)
                ),
                response,
            ));
            for (index, takeaway) in takeaways.iter().enumerate() {
                let rendered_prompt = MASK_PROMPT.replace("{POST}", source).replace(
                    "{TAKEAWAY}",
                    takeaway["text"].as_str().expect("takeaway text"),
                );
                records.push(succeeded_result(
                    &manifest,
                    &manifest_sha256,
                    "mask",
                    note_id,
                    Some(index),
                    1,
                    &rendered_prompt,
                    takeaway["fragments"].clone(),
                ));
            }
        }
        write_json_lines(&self.run_directory.join("results.jsonl"), &records);
    }
}

fn succeeded_result(
    manifest: &Value,
    manifest_sha256: &str,
    stage_name: &str,
    note_id: &str,
    takeaway_index: Option<usize>,
    attempt: u32,
    rendered_prompt: &str,
    response: Value,
) -> Value {
    let stage = &manifest[stage_name];
    let final_output = match stage_name {
        "takeaway" => json!({"takeaways": response}),
        "mask" => json!({"fragments": response}),
        _ => panic!("unsupported fixture stage"),
    };
    let final_output_raw = final_output.to_string();
    json!({
        "schema_version": 1,
        "manifest_sha256": manifest_sha256,
        "job_key": match takeaway_index {
            Some(index) => format!("{stage_name}:{note_id}:{index}"),
            None => format!("{stage_name}:{note_id}"),
        },
        "stage": stage_name,
        "note_id": note_id,
        "takeaway_index": takeaway_index,
        "attempt": attempt,
        "status": "succeeded",
        "wrapper_sha256": manifest["wrapper_sha256"],
        "codex_version": manifest["codex_version"],
        "model": stage["model"],
        "reasoning_effort": stage["reasoning_effort"],
        "prompt_sha256": sha256(rendered_prompt.as_bytes()),
        "response_schema_sha256": stage["response_schema_sha256"],
        "final_output_raw": final_output_raw,
        "final_output_sha256": sha256(final_output_raw.as_bytes()),
        "response": response
    })
}

fn fixture_takeaway_input(note: &str) -> String {
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
            "shell_tool",
            "unified_exec",
            "multi_agent",
            "apps",
            "plugins",
            "browser_use",
            "computer_use",
            "image_generation"
        ]
    })
}

fn takeaway_schema() -> Value {
    json!({
        "type": "object",
        "properties": {
            "takeaways": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["takeaways"],
        "additionalProperties": false
    })
}

fn mask_schema() -> Value {
    json!({
        "type": "object",
        "properties": {
            "fragments": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1
            }
        },
        "required": ["fragments"],
        "additionalProperties": false
    })
}

fn default_output_notes() -> Value {
    json!([
        {
            "note_id": format!("{:064x}", 1),
            "takeaways": [
                {
                    "text": "Serverless operation of pypush",
                    "fragments": ["pypush", "serverless"]
                },
                {
                    "text": "Open-source availability of pypush",
                    "fragments": ["pypush", "open-source"]
                }
            ]
        },
        {
            "note_id": format!("{:064x}", 2),
            "takeaways": [{
                "text": "Future dominance of solar power generation",
                "fragments": ["Solar power will dominate future electricity generation"]
            }]
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
fn prompt_iteration_reviews_bound_run_pairs_and_persists_partial_statuses() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([
        approved(""),
        skipped("Need a clearer subject label"),
        ApprovalTuiAction::SaveComment {
            comment: "Potential missing subject".to_owned(),
        },
        ApprovalTuiAction::Pause,
    ]);

    let outcome =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
            .expect("run prompt review");

    assert_eq!(outcome, PromptReviewRunOutcome::Paused);
    assert_eq!(first.screens.len(), 4);
    assert_eq!(
        first.screens[0].screen.title,
        "Serverless operation of pypush"
    );
    assert_eq!(
        first.screens[0].screen.evidence[0].body,
        "⟦pypush⟧ is ⟦serverless⟧; pypush is open-source."
    );
    assert!(
        first.screens[0]
            .screen
            .scope
            .contains("valid atomic subject")
    );
    assert_eq!(first.screens[2].screen.title, "Atomic-subject list");
    assert_eq!(
        first.screens[2].screen.evidence[0].body,
        "pypush is serverless; pypush is open-source."
    );
    assert!(
        first.screens[2].screen.evidence[1]
            .body
            .contains("Open-source availability of pypush")
    );
    assert_eq!(first.screens[3].comment, "Potential missing subject");

    let session = read_session(&fixture.session_path);
    assert_eq!(session["notes"][0]["pairs"][0]["status"], "approved");
    assert_eq!(session["notes"][0]["pairs"][1]["status"], "skipped");
    assert_eq!(
        session["notes"][0]["pairs"][1]["comment"],
        "Need a clearer subject label"
    );
    assert_eq!(session["notes"][0]["subject_list"]["status"], "pending");
    assert_eq!(
        session["notes"][0]["subject_list"]["comment"],
        "Potential missing subject"
    );
    assert_eq!(session["notes"][1]["pairs"][0]["status"], "pending");

    let mut resumed = ScriptedUi::new([
        rejected("Potential missing subject"),
        approved("Useful control"),
        skipped("Not checking completeness yet"),
    ]);
    let outcome =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
            .expect("resume prompt review");

    assert_eq!(
        outcome,
        PromptReviewRunOutcome::Completed {
            pairs: PromptReviewCounts {
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
fn prompt_iteration_refuses_to_resume_after_the_generation_run_changes() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("create prompt review session");

    fixture.change_subject_prompt();

    let mut resumed = ScriptedUi::new([]);
    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
            .expect_err("a session must stay bound to one immutable generation run");
    assert!(
        error.to_string().contains("different generation run"),
        "{error}"
    );
}

#[test]
fn prompt_iteration_resume_does_not_depend_on_the_live_prompt_registry() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut first)
        .expect("create prompt review session");

    let manifest = read_json(&fixture.run_directory.join("manifest.json"));
    let registry_path = Path::new(
        manifest["takeaway"]["prompt_registry_path"]
            .as_str()
            .expect("takeaway registry path"),
    );
    let mut registry = read_json(registry_path);
    registry["a-later-prompt-version"] = json!("A prompt added after this run completed.");
    write_json(registry_path, &registry);

    let mut resumed = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut resumed)
        .expect("resume must use the prompt frozen in the generation manifest");
}

#[test]
fn prompt_iteration_rejects_output_that_does_not_match_preserved_results() {
    let fixture = Fixture::new();
    let output_path = fixture.run_directory.join("output.json");
    let mut output = read_json(&output_path);
    output["notes"][0]["takeaways"][0]["text"] = json!("Fabricated subject");
    write_json(&output_path, &output);
    let mut ui = ScriptedUi::new([]);

    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("review output must match the model result ledger");
    assert!(error.to_string().contains("preserved result"), "{error}");
}

#[test]
fn prompt_iteration_rejects_a_result_bound_to_another_rendered_prompt() {
    let fixture = Fixture::new();
    let results_path = fixture.run_directory.join("results.jsonl");
    let mut records = read_json_lines(&results_path);
    records[0]["prompt_sha256"] = json!("f".repeat(64));
    write_json_lines(&results_path, &records);
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("the recorded job must use the manifest prompt and bound note");
    assert!(error.to_string().contains("rendered prompt"), "{error}");
}

#[test]
fn prompt_iteration_rejects_a_truncated_result_history() {
    let fixture = Fixture::new();
    let results_path = fixture.run_directory.join("results.jsonl");
    let mut records = read_json_lines(&results_path);
    records[0]["attempt"] = json!(2);
    write_json_lines(&results_path, &records);
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("result attempts must start at one and remain consecutive");
    assert!(
        error.to_string().contains("nonconsecutive attempt"),
        "{error}"
    );
}

#[test]
fn prompt_iteration_accepts_an_obsolete_mask_after_a_retry_shrinks_the_subject_list() {
    let fixture = Fixture::new();
    let manifest_path = fixture.run_directory.join("manifest.json");
    let manifest = read_json(&manifest_path);
    let manifest_sha256 = sha256(&fs::read(&manifest_path).expect("read manifest"));
    let output_path = fixture.run_directory.join("output.json");
    let mut output = read_json(&output_path);
    output["notes"][0]["takeaways"] = json!([output["notes"][0]["takeaways"][0].clone()]);
    write_json(&output_path, &output);

    let note_id = format!("{:064x}", 1);
    let source = "pypush is serverless; pypush is open-source.";
    let response = json!(["Serverless operation of pypush"]);
    let mut records = read_json_lines(&fixture.run_directory.join("results.jsonl"));
    records.push(succeeded_result(
        &manifest,
        &manifest_sha256,
        "takeaway",
        &note_id,
        None,
        2,
        &format!("{SUBJECT_PROMPT}\n\n<post>\n{source}\n</post>"),
        response,
    ));
    write_json_lines(&fixture.run_directory.join("results.jsonl"), &records);

    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
        .expect("the old second mask was valid before the subject-list retry");
    assert_eq!(ui.screens[0].screen.title, "Serverless operation of pypush");
}

#[test]
fn prompt_iteration_rejects_an_obsolete_mask_index_that_never_existed() {
    let fixture = Fixture::new();
    let manifest_path = fixture.run_directory.join("manifest.json");
    let manifest = read_json(&manifest_path);
    let manifest_sha256 = sha256(&fs::read(&manifest_path).expect("read manifest"));
    let note_id = format!("{:064x}", 1);
    let source = "pypush is serverless; pypush is open-source.";
    let rendered_prompt = MASK_PROMPT
        .replace("{POST}", source)
        .replace("{TAKEAWAY}", "Fabricated subject");
    let mut records = read_json_lines(&fixture.run_directory.join("results.jsonl"));
    records.push(succeeded_result(
        &manifest,
        &manifest_sha256,
        "mask",
        &note_id,
        Some(5),
        1,
        &rendered_prompt,
        json!(["pypush"]),
    ));
    write_json_lines(&fixture.run_directory.join("results.jsonl"), &records);

    let mut ui = ScriptedUi::new([]);
    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("a stale mask must have belonged to an earlier generated list");
    assert!(error.to_string().contains("mask index"), "{error}");
}

#[test]
fn prompt_iteration_requires_fresh_isolated_generation_jobs() {
    let fixture = Fixture::new();
    let manifest_path = fixture.run_directory.join("manifest.json");
    let mut manifest = read_json(&manifest_path);
    manifest["isolation"]["fresh_process_per_job"] = json!(false);
    write_json(&manifest_path, &manifest);
    let notes = read_json(&fixture.run_directory.join("output.json"))["notes"].clone();
    fixture.publish_output(notes);
    let mut ui = ScriptedUi::new([]);

    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("every prompt must use a fresh isolated process");
    assert!(error.to_string().contains("fresh process"), "{error}");
}

#[test]
fn prompt_iteration_surfaces_empty_and_duplicate_subject_lists() {
    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["takeaways"] = json!([]);
    fixture.publish_output(notes);
    let mut empty = ScriptedUi::new([ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut empty)
        .expect("show empty generated subject list");
    assert_eq!(empty.screens[0].screen.title, "Atomic-subject list");
    assert_eq!(
        empty.screens[0].screen.evidence[1].body,
        "No atomic subjects generated."
    );

    let fixture = Fixture::new();
    let mut notes = default_output_notes();
    notes[0]["takeaways"][1]["text"] = notes[0]["takeaways"][0]["text"].clone();
    fixture.publish_output(notes);
    let mut duplicate = ScriptedUi::new([skipped(""), skipped(""), ApprovalTuiAction::Pause]);
    run_subject_mask_prompt_review(
        &fixture.run_directory,
        &fixture.session_path,
        &mut duplicate,
    )
    .expect("show duplicate generated labels for review");
    let list = &duplicate.screens[2].screen.evidence[1].body;
    assert_eq!(list.matches("Serverless operation of pypush").count(), 2);
}

#[test]
fn prompt_iteration_stops_when_generation_did_not_publish_output() {
    let fixture = Fixture::new();
    fs::remove_file(fixture.run_directory.join("output.json")).expect("remove output");
    let mut ui = ScriptedUi::new([]);

    let error =
        run_subject_mask_prompt_review(&fixture.run_directory, &fixture.session_path, &mut ui)
            .expect_err("a failed generation run must stop before review");
    assert!(error.to_string().contains("output.json"), "{error}");
}

fn read_session(path: &Path) -> Value {
    let envelope = read_json(path);
    envelope["session"].clone()
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
