use std::fs;

use oracle_mvp::containment_review::{ContainmentReview, run_containment_decision_review};
use oracle_mvp::reference_tui::{ApprovalEvidenceLayout, ApprovalTuiAction};
use serde_json::{Value, json};

fn packet() -> Value {
    json!({
        "schema_version":1, "experiment":"TRUE04", "threshold":0.142,
        "items":[{
            "item_id":"U001", "a":"Recipes and Their Results", "b":"Crockpot Meat Dishes",
            "assessment":"Ambiguous", "reason":"The dishes need not describe recipes.",
            "decisions":[{
                "id":"S001-contains-S002", "a_id":"S001", "b_id":"S002",
                "native":false, "score":0.1, "cutoff":false,
                "model_input":"premise: This text is about Crockpot Meat Dishes. hypothesis: This text is about Recipes and Their Results."
            }]
        }]
    })
}

fn titles() -> Value {
    json!({"schema_version":1, "groups":[
        {"group":"S001", "title":"Recipes and Their Results", "instances":[
            {"instance":"V237", "fragments":["pancakes", "recipe", "Let us know how it tastes!"]},
            {"instance":"V663", "fragments":["Irish soda bread recipe I tried out recently", "very pleased", "turned out great"]}
        ]},
        {"group":"S002", "title":"Crockpot Meat Dishes", "instances":[
            {"instance":"V103", "fragments":["I have", "crockpot of beef stew"]},
            {"instance":"V826", "fragments":["I got up early and put the roast and veggies in the crockpot"]}
        ]}
    ]})
}

fn write(path: &std::path::Path, value: &Value) {
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}

#[test]
fn titles_and_all_exact_masks_have_separate_panels_and_old_session_resumes_unchanged() {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("pairs.json");
    let catalog = temp.path().join("titles.json");
    let session = temp.path().join("decisions.json");
    write(&input, &packet());
    write(&catalog, &titles());
    let mut calls = 0;
    run_containment_decision_review(&input, &session, None, |_, _| {
        calls += 1;
        Ok(if calls == 1 {
            ApprovalTuiAction::SaveComment {
                comment: "My previous comment".into(),
            }
        } else {
            ApprovalTuiAction::Pause
        })
    })
    .unwrap();
    let saved = fs::read(&session).unwrap();
    let original = fs::read(&input).unwrap();
    let source = fs::read(&catalog).unwrap();
    ContainmentReview::load(&input, None).unwrap().with_titles(&catalog).unwrap()
        .run_decisions(&session, None, |screen, comment| {
            assert_eq!(comment, "My previous comment");
            let ApprovalEvidenceLayout::Paged(panels) = screen.evidence else { panic!() };
            assert_eq!(panels.len(), 3);
            assert_eq!(panels[0].title, "A (proposed parent): Recipes and Their Results");
            assert_eq!(panels[1].title, "B (proposed child): Crockpot Meat Dishes");
            assert_eq!(panels[0].body, "V237  ⟦pancakes⟧ ⟦recipe⟧ ⟦Let us know how it tastes!⟧\n\nV663  ⟦Irish soda bread recipe I tried out recently⟧ ⟦very pleased⟧ ⟦turned out great⟧");
            assert_eq!(panels[1].body, "V103  ⟦I have⟧ ⟦crockpot of beef stew⟧\n\nV826  ⟦I got up early and put the roast and veggies in the crockpot⟧");
            assert_eq!(panels[2].title, "My comment");
            assert_eq!(panels[2].body, "The dishes need not describe recipes.");
            assert!(screen.guidance.unwrap().body.contains("TRUE saw only the category titles"));
            Ok(ApprovalTuiAction::Pause)
        }).unwrap();
    assert_eq!(fs::read(&session).unwrap(), saved);
    assert_eq!(fs::read(&input).unwrap(), original);
    assert_eq!(fs::read(&catalog).unwrap(), source);

    run_containment_decision_review(&input, &session, None, |_, comment| {
        Ok(ApprovalTuiAction::Submit {
            outcome: oracle_mvp::reference_map::ReviewOutcome::Approved,
            comment,
        })
    })
    .unwrap();
    let completed = fs::read(&session).unwrap();
    ContainmentReview::load(&input, None)
        .unwrap()
        .with_titles(&catalog)
        .unwrap()
        .run_decisions(&session, None, |_, _| panic!("reopened completed review"))
        .unwrap();
    assert_eq!(fs::read(&session).unwrap(), completed);
    ContainmentReview::load(&input, None)
        .unwrap()
        .with_titles(&catalog)
        .unwrap()
        .run_decisions(&session, Some("U001"), |screen, comment| {
            assert!(screen.heading.contains("Yes (contains)"));
            assert_eq!(comment, "My previous comment");
            Ok(ApprovalTuiAction::Pause)
        })
        .unwrap();
}

#[test]
fn repeated_titles_union_groups_and_only_deduplicate_same_vector_id() {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("pairs.json");
    let catalog = temp.path().join("titles.json");
    let mut p = packet();
    let mut d = p["items"][0]["decisions"][0].clone();
    d["a_id"] = json!("S003");
    d["id"] = json!("S003-contains-S002");
    p["items"][0]["decisions"].as_array_mut().unwrap().push(d);
    let mut t = titles();
    t["groups"].as_array_mut().unwrap().push(json!({
        "group":"S003", "title":"Recipes and Their Results", "instances":[
            {"instance":"V237", "fragments":["pancakes", "recipe", "Let us know how it tastes!"]},
            {"instance":"V999", "fragments":["pancakes", "recipe", "Let us know how it tastes!"]}
        ]
    }));
    write(&input, &p);
    write(&catalog, &t);
    ContainmentReview::load(&input, None)
        .unwrap()
        .with_titles(&catalog)
        .unwrap()
        .run_decisions(temp.path().join("decisions.json"), None, |screen, _| {
            let ApprovalEvidenceLayout::Paged(panels) = screen.evidence else {
                panic!()
            };
            assert_eq!(panels[0].body.matches("V237 ").count(), 1);
            assert!(panels[0].body.contains("V999 "));
            assert_eq!(panels[0].body.matches("⟦pancakes⟧").count(), 2);
            assert_eq!(panels[1].body.matches("V103 ").count(), 1);
            Ok(ApprovalTuiAction::Pause)
        })
        .unwrap();
}

#[test]
fn invalid_mask_catalog_is_rejected_before_review_or_session_creation() {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("pairs.json");
    let catalog = temp.path().join("titles.json");
    write(&input, &packet());
    for case in 0..6 {
        let mut t = titles();
        match case {
            0 => t["groups"][0]["group"] = json!("Missing"),
            1 => t["groups"][0]["title"] = json!("Wrong title"),
            2 => t["groups"][0]["instances"] = json!([]),
            3 => t["groups"][0]["instances"][0]["fragments"] = json!([""]),
            4 => {
                let duplicate = t["groups"][0].clone();
                t["groups"].as_array_mut().unwrap().push(duplicate);
            }
            5 => {
                t["groups"][1]["instances"][0]["instance"] = json!("V237");
            }
            _ => unreachable!(),
        }
        write(&catalog, &t);
        assert!(
            ContainmentReview::load(&input, None)
                .unwrap()
                .with_titles(&catalog)
                .is_err(),
            "case {case}"
        );
    }
    assert_eq!(fs::read_dir(temp.path()).unwrap().count(), 2);
}

#[test]
fn saved_title_catalog_cannot_be_used_as_session() {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("pairs.json");
    let catalog = temp.path().join("titles.json");
    write(&input, &packet());
    write(&catalog, &titles());
    let original = fs::read(&catalog).unwrap();
    let result = ContainmentReview::load(&input, None)
        .unwrap()
        .with_titles(&catalog)
        .unwrap()
        .run_decisions(&catalog, None, |_, _| panic!("opened terminal"));
    assert!(result.is_err());
    assert_eq!(fs::read(catalog).unwrap(), original);
}

#[test]
fn titles_cli_validates_masks_before_non_tty_rejection_without_writes() {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("pairs.json");
    let catalog = temp.path().join("titles.json");
    let session = temp.path().join("decisions.json");
    write(&input, &packet());
    write(&catalog, &titles());
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
        .arg(&input)
        .arg("--titles")
        .arg(&catalog)
        .arg("--session")
        .arg(&session)
        .output()
        .unwrap();
    assert!(String::from_utf8_lossy(&output.stderr).contains("interactive terminal"));
    assert_eq!(fs::read_dir(temp.path()).unwrap().count(), 2);
}

#[test]
fn every_actual_uncertain_pair_contains_exact_masks_for_every_original_group() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
    let input = root.join(
        "sse_multivector/navigation-research-v1/TRUE04/collection-review/uncertainty-review.json",
    );
    let titles = root.join("sse_multivector/navigation-research-v1/TRUE04/titles.json");
    let packet: Value = serde_json::from_slice(&fs::read(&input).unwrap()).unwrap();
    let source: Value = serde_json::from_slice(&fs::read(&titles).unwrap()).unwrap();
    let temp = tempfile::tempdir().unwrap();
    let mut index = 0;
    let mut count = 0;
    ContainmentReview::load(&input, None)
        .unwrap()
        .with_titles(&titles)
        .unwrap()
        .run_decisions(temp.path().join("decisions.json"), None, |screen, _| {
            let item = &packet["items"][index];
            let ApprovalEvidenceLayout::Paged(panels) = &screen.evidence else {
                panic!()
            };
            assert_eq!(panels.len(), 3);
            for (side, key) in ["a_id", "b_id"].into_iter().enumerate() {
                let mut seen = std::collections::BTreeSet::new();
                let mut expected = Vec::new();
                for d in item["decisions"].as_array().unwrap() {
                    let group = source["groups"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .find(|g| g["group"] == d[key])
                        .unwrap();
                    for mask in group["instances"].as_array().unwrap() {
                        let id = mask["instance"].as_str().unwrap();
                        if !seen.insert(id) {
                            continue;
                        }
                        expected.push(format!(
                            "{id}  {}",
                            mask["fragments"]
                                .as_array()
                                .unwrap()
                                .iter()
                                .map(|f| format!("⟦{}⟧", f.as_str().unwrap()))
                                .collect::<Vec<_>>()
                                .join(" ")
                        ));
                    }
                }
                assert_eq!(panels[side].body, expected.join("\n\n"));
                count += seen.len();
            }
            assert_eq!(panels[2].body, item["reason"].as_str().unwrap());
            for (width, height) in [(72, 24), (100, 40)] {
                let mut model =
                    oracle_mvp::reference_tui::ApprovalTuiModel::new_navigable_stacked_review(
                        screen.clone(),
                        String::new(),
                    );
                let mut terminal =
                    ratatui::Terminal::new(ratatui::backend::TestBackend::new(width, height))
                        .unwrap();
                terminal.draw(|frame| model.render(frame)).unwrap();
                let buffer = terminal.backend().buffer();
                let text = (0..height)
                    .map(|y| {
                        (0..width)
                            .map(|x| buffer[(x, y)].symbol())
                            .collect::<String>()
                    })
                    .collect::<Vec<_>>()
                    .join("\n");
                let normalized = text.split_whitespace().collect::<Vec<_>>().join(" ");
                for panel in panels {
                    assert!(
                        normalized.contains(&panel.title),
                        "{}: missing title {} at {width}x{height}:\n{text}",
                        item["item_id"],
                        panel.title
                    );
                }
                assert!(text.contains("[A]"), "{text}");
                assert!(text.contains("[R]"), "{text}");
                assert!(text.contains("[Ctrl-C]"), "{text}");
                assert!(!text.contains("Native:"));
            }
            index += 1;
            Ok(if index == 65 {
                ApprovalTuiAction::Pause
            } else {
                ApprovalTuiAction::NextItem
            })
        })
        .unwrap();
    assert_eq!(index, 65);
    assert_eq!(count, 625);
}
