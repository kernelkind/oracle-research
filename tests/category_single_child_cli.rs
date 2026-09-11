use std::process::Command;

#[test]
fn category_cli_accepts_single_child_absorption_without_changing_the_saved_view() {
    let run = |flags: &[&str]| {
        Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
            .args([
                "--categories",
                "sse_multivector/geometric-hierarchy-v1/GDC09/categories.json",
                "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json",
            ])
            .args(flags)
            .output()
            .unwrap()
    };
    let original = run(&["--check"]);
    assert!(original.status.success());
    let original_text = String::from_utf8(original.stdout).unwrap();
    assert!(original_text.contains("219 categories · 100 notes"));

    for flags in [
        ["--absorb-single-children", "--check"],
        ["--check", "--absorb-single-children"],
    ] {
        let collapsed = run(&flags);
        assert!(
            collapsed.status.success(),
            "{}",
            String::from_utf8_lossy(&collapsed.stderr)
        );
        let text = String::from_utf8(collapsed.stdout).unwrap();
        assert!(text.contains("single-child absorption"), "{text}");
        assert!(text.contains("categories · 100 notes"), "{text}");
        assert!(!text.contains("219 categories · 100 notes"), "{text}");
        for line in text.lines().filter(|line| line.starts_with("  Children:")) {
            assert!(line.contains(','), "remaining single child: {line}");
        }
    }
    let unchanged = run(&["--check"]);
    assert!(unchanged.status.success());
    assert_eq!(String::from_utf8(unchanged.stdout).unwrap(), original_text);
}
