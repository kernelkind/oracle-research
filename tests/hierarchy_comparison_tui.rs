use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hierarchy_comparison_tui::HierarchyComparison;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use unicode_width::UnicodeWidthStr;

fn manifest() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/manual-coffee-hierarchy-v1/m06-comparison.json")
}

fn spec() -> serde_json::Value {
    serde_json::from_slice(&std::fs::read(manifest()).unwrap()).unwrap()
}

fn key(model: &mut HierarchyComparison, code: KeyCode) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn screen(model: &mut HierarchyComparison, width: u16, height: u16) -> String {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..height)
        .map(|y| {
            let mut line = String::new();
            let mut x = 0;
            while x < width {
                let symbol = buffer[(x, y)].symbol();
                line.push_str(symbol);
                x += symbol.width().max(1) as u16;
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn select(model: &mut HierarchyComparison, index: usize) {
    key(model, KeyCode::F(2));
    for _ in 0..spec()["pages"].as_array().unwrap().len() {
        key(model, KeyCode::Up);
    }
    for _ in 0..index {
        key(model, KeyCode::Down);
    }
}

fn page_index(kind: &str, group_id: Option<usize>) -> usize {
    spec()["pages"]
        .as_array()
        .unwrap()
        .iter()
        .position(|page| page["kind"] == kind && group_id.is_none_or(|id| page["group_id"] == id))
        .unwrap()
}

#[test]
fn comparison_preserves_manual_original_note_state_when_returning_to_menu() {
    let mut model = HierarchyComparison::load(&manifest()).unwrap();
    select(&mut model, page_index("manual", None));
    let menu = screen(&mut model, 80, 24);
    assert!(menu.contains("Coffee preparation"), "{menu}");
    assert!(menu.contains("F2"), "{menu}");
    key(&mut model, KeyCode::Enter);
    let first = screen(&mut model, 80, 24);
    for expected in ["Coffee preparation", "N036", "Note 1 of 5", "F2"] {
        assert!(first.contains(expected), "Missing {expected}: {first}");
    }
    key(&mut model, KeyCode::Char('l'));
    let second = screen(&mut model, 80, 24);
    assert!(second.contains("N045"), "{second}");
    assert!(!key(&mut model, KeyCode::F(2)));
    assert_eq!(screen(&mut model, 80, 24), menu);
    key(&mut model, KeyCode::Enter);
    assert_eq!(screen(&mut model, 80, 24), second);
}

#[test]
fn saved_merge_views_keep_numeric_groups_nested_masks_and_original_notes() {
    let mut model = HierarchyComparison::load(&manifest()).unwrap();
    select(&mut model, page_index("merge", Some(1605)));
    key(&mut model, KeyCode::Enter);
    let group = screen(&mut model, 100, 35);
    for expected in ["minimum 5 notes", "Showing branch 1605", "19 notes", "F2"] {
        assert!(group.contains(expected), "Missing {expected}: {group}");
    }
    assert!(!group.contains("Coffee preparation"), "{group}");

    select(&mut model, page_index("merge", Some(951)));
    key(&mut model, KeyCode::Enter);
    let smaller = screen(&mut model, 100, 35);
    assert!(smaller.contains("Showing branch 951"), "{smaller}");
    assert!(smaller.contains("minimum 2 notes"), "{smaller}");
    assert!(smaller.contains('⟦') && smaller.contains('⟧'), "{smaller}");
    key(&mut model, KeyCode::Char('G'));
    key(&mut model, KeyCode::Enter);
    let original = screen(&mut model, 100, 35);
    assert!(original.contains("Original note"), "{original}");
    assert!(
        original.contains('⟦') && original.contains('⟧'),
        "{original}"
    );
    assert!(
        original.lines().last().unwrap().contains("F2"),
        "{original}"
    );
    key(&mut model, KeyCode::F(2));
    key(&mut model, KeyCode::Enter);
    assert_eq!(screen(&mut model, 100, 35), original);
    key(&mut model, KeyCode::Esc);
    assert!(screen(&mut model, 100, 35).contains("Showing branch 951"));
}

fn temporary_spec(value: &serde_json::Value) -> (tempfile::TempDir, PathBuf) {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("comparison.json");
    let mut value = value.clone();
    for field in [
        "manual_hierarchy",
        "source_notes",
        "vector_map",
        "merge_history",
    ] {
        value[field] = manifest()
            .parent()
            .unwrap()
            .join(value[field].as_str().unwrap())
            .to_str()
            .unwrap()
            .into();
    }
    std::fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
    (directory, path)
}

#[test]
fn long_analysis_scrolls_at_80_columns_and_keeps_its_position_per_page() {
    let mut value = spec();
    value["pages"][0]["analysis"] = format!(
        "First analysis marker.\n{}\nLast analysis marker.",
        (0..100)
            .map(|index| format!("Analysis line {index:03}."))
            .collect::<Vec<_>>()
            .join("\n")
    )
    .into();
    let (_directory, path) = temporary_spec(&value);
    let mut model = HierarchyComparison::load(&path).unwrap();
    let initial = screen(&mut model, 80, 24);
    assert!(initial.contains("First analysis marker."), "{initial}");
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Char('d'),
        KeyModifiers::CONTROL,
    )));
    let middle = screen(&mut model, 80, 24);
    assert!(!middle.contains("First analysis marker."), "{middle}");
    key(&mut model, KeyCode::Char('G'));
    let end = screen(&mut model, 80, 24);
    assert!(end.contains("Last analysis marker."), "{end}");
    key(&mut model, KeyCode::Down);
    screen(&mut model, 80, 24);
    key(&mut model, KeyCode::Up);
    assert_eq!(screen(&mut model, 80, 24), end);
    key(&mut model, KeyCode::Char('g'));
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model, 80, 24), initial);
}

#[test]
fn comparison_rejects_changed_input_bytes_and_missing_or_hidden_groups() {
    let mut value = spec();
    value["input_sha256"]["manual_hierarchy"] = "0".repeat(64).into();
    let (_directory, path) = temporary_spec(&value);
    let error = HierarchyComparison::load(&path)
        .err()
        .expect("reject changed source");
    assert!(error.to_string().contains("SHA-256"), "{error}");

    let mut value = spec();
    let index = page_index("merge", Some(951));
    value["pages"][index]["min_notes"] = 5.into();
    let (_directory, path) = temporary_spec(&value);
    let error = HierarchyComparison::load(&path)
        .err()
        .expect("reject hidden group");
    assert!(error.to_string().contains("951"), "{error}");
}

#[test]
fn comparison_footer_and_exit_remain_available_in_a_small_terminal() {
    let mut model = HierarchyComparison::load(&manifest()).unwrap();
    select(&mut model, page_index("manual", None));
    key(&mut model, KeyCode::Enter);
    let small = screen(&mut model, 40, 10);
    assert!(small.contains("F2"), "{small}");
    assert!(!key(&mut model, KeyCode::F(2)));
    assert!(screen(&mut model, 80, 24).contains("Coffee preparation"));
    assert!(key(&mut model, KeyCode::Char('q')));
}

#[test]
fn comparison_masks_show_original_vector_ids_and_source_note_numbers() {
    let mut model = HierarchyComparison::load(&manifest()).unwrap();
    select(&mut model, page_index("merge", Some(951)));
    key(&mut model, KeyCode::Enter);
    let masks = screen(&mut model, 100, 35);
    for expected in ["V410", "V411", "V793", "N052", "N086"] {
        assert!(masks.contains(expected), "Missing {expected}: {masks}");
    }
    key(&mut model, KeyCode::Char('G'));
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model, 100, 35);
    let heading = note.lines().next().unwrap();
    assert!(heading.contains("Original note"), "{note}");
    assert!(
        heading.contains("N052") || heading.contains("N086"),
        "{note}"
    );
    assert!(heading.contains('V'), "{note}");
}

#[test]
fn comparison_can_reveal_parent_masks_without_changing_default_hiding() {
    let mut value = spec();
    let index = page_index("merge", Some(1605));
    value["pages"][index]["group_id"] = 1098.into();
    value["pages"][index]["min_notes"] = 2.into();
    let (_directory, path) = temporary_spec(&value);
    let mut model = HierarchyComparison::load(&path).unwrap();
    select(&mut model, index);
    key(&mut model, KeyCode::Enter);
    let initial = screen(&mut model, 120, 50);
    assert!(initial.contains("Showing branch 1098"), "{initial}");
    assert!(
        !initial.contains("V283") && !initial.contains("V284"),
        "{initial}"
    );
    key(&mut model, KeyCode::Char('a'));
    let all = screen(&mut model, 120, 50);
    for expected in ["V283", "V284", "N036", "All parent masks"] {
        assert!(all.contains(expected), "Missing {expected}: {all}");
    }
    key(&mut model, KeyCode::Char('a'));
    assert_eq!(screen(&mut model, 120, 50), initial);
}

#[test]
fn comparison_resize_prompts_include_the_persistent_footer_row() {
    let mut model = HierarchyComparison::load(&manifest()).unwrap();
    select(&mut model, page_index("manual", None));
    key(&mut model, KeyCode::Enter);
    let too_short = screen(&mut model, 80, 23);
    assert!(too_short.contains("72 × 24"), "{too_short}");
    assert!(!screen(&mut model, 80, 24).contains("Resize"));

    select(&mut model, page_index("merge", Some(951)));
    key(&mut model, KeyCode::Enter);
    let too_short = screen(&mut model, 80, 12);
    assert!(too_short.contains("60 × 13"), "{too_short}");
    assert!(!screen(&mut model, 80, 13).contains("Resize"));
}

#[test]
fn hiding_a_selected_parent_mask_selects_its_visible_containing_group() {
    let mut value = spec();
    let index = page_index("merge", Some(1605));
    value["pages"][index]["group_id"] = 1098.into();
    value["pages"][index]["min_notes"] = 2.into();
    let (_directory, path) = temporary_spec(&value);
    let mut model = HierarchyComparison::load(&path).unwrap();
    select(&mut model, index);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('a'));
    for _ in 0..100 {
        let current = screen(&mut model, 120, 50);
        if current
            .lines()
            .any(|line| line.contains('▶') && line.contains("V283"))
        {
            break;
        }
        key(&mut model, KeyCode::Char('j'));
    }
    let selected = screen(&mut model, 120, 50);
    assert!(
        selected
            .lines()
            .any(|line| line.contains('▶') && line.contains("V283")),
        "{selected}"
    );
    key(&mut model, KeyCode::Enter);
    let original = screen(&mut model, 120, 50);
    assert!(
        original.contains("Original note · V283, V284 · N036"),
        "{original}"
    );
    assert!(
        original.contains('⟦') && original.contains('⟧'),
        "{original}"
    );
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('a'));
    let hidden = screen(&mut model, 120, 50);
    assert!(!hidden.contains("V283"), "{hidden}");
    assert!(
        hidden
            .lines()
            .any(|line| line.contains('▶') && line.contains("1098")),
        "{hidden}"
    );
}
