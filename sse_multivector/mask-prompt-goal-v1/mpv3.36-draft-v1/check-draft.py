"""Offline MPv3.36 example/format checks; not a model or semantic evaluation."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE_DIR = HERE.parent / "mpv3.34-draft-v1"
BASE = BASE_DIR / "mask-prompt.md"
BASE_HASH = "922fce5818b865cc77d5a365fa1cae9ea14ee3b733de712d3298ee88fbf8e725"
spec = importlib.util.spec_from_file_location("base_checks", BASE_DIR / "check-draft.py")
base_checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_checks)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "mask-prompt.md"
    original, prompt = BASE.read_text(), path.read_text()
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    old_rows, rows = base_checks.examples(original), base_checks.examples(prompt)
    assert any(subject == "Books" for _, subject, _ in rows), "missing positive Books/hashtag contrast"
    assert len(old_rows) == 7 and len(rows) == 8
    assert rows[:4] == old_rows[:4], "bicycle/furniture examples changed"
    expected_reading = {
        "Books": ["book", "books"],
        "Reading books": ["reading", "book"],
        "Continuing to read books despite noise": ["Despite the noise,", "kept reading", "book"],
        "Noise reduction while reading books": [],
    }
    for post, subject, response in rows:
        assert list(response) == base_checks.FIELDS
        assert isinstance(response["meaning"], str) and response["meaning"].strip()
        assert isinstance(response["evidence"], str) and response["evidence"].strip()
        assert type(response["expressible"]) is bool
        assert response["expressible"] == bool(response["mask"])
        ranges = base_checks.selection.decode(json.dumps({"mask": response["mask"]}), post)
        if subject in expected_reading:
            assert post.endswith("I also collect #books.")
            assert [post[r["start"]:r["end"]] for r in ranges] == expected_reading[subject]
            if subject == "Books":
                assert response["mask"][-1] == {"word": 21, "text": "books"}
    assert rows[-1][2] == old_rows[-1][2], "empty reduction response changed"

    assert "together union into the exact semantic meaning for the supplied subject" in prompt
    assert "Complete these three steps in order:" in prompt
    assert '1. Understand the target. In "meaning"' in prompt
    assert "2. Determine whether it is expressible." in prompt
    assert "3. Construct the mask." in prompt
    assert "including repetitions expressing only part" not in prompt
    # Output syntax, exclusions, diagnostics and actual input layout stay byte-identical.
    start, end = "Do not select URLs", "<examples>"
    assert prompt[prompt.index(start):prompt.index(end)] == original[
        original.index(start):original.index(end)
    ]
    assert prompt[prompt.index("<post>"):] == original[original.index("<post>"):]
    for placeholder in ("{POST}", "{INDEXED_POST}", "{SUBJECT}"):
        assert prompt.count(placeholder) == original.count(placeholder) == 1

    request = json.loads((HERE / "prompt-edits.json").read_text())
    assert request["base_sha256"] == BASE_HASH
    expected = original
    for edit in request["edits"]:
        assert original.count(edit["old"]) == 1
        expected = expected.replace(edit["old"], edit["new"], 1)
    assert expected == prompt, "changes beyond the declared revision"
    receipt = json.loads((HERE / "mask-prompt.md.revision.json").read_text())
    assert receipt["base_sha256"] == BASE_HASH
    assert receipt["prompt_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert receipt["edits"] == request["edits"]
    print("PASS: eight decoded examples; exact revision; baseline, output contract and inputs preserved. No inference.")


if __name__ == "__main__":
    main()
