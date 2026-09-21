"""Offline MPv3.35 checks; validates syntax/preservation, not model behavior."""

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
    assert "Sharing a concept with the subject is not sufficient." in prompt, "contribution distinction is absent"
    assert "individual passages and fragments need not express it on their own" in prompt
    assert "cover every passage" in prompt and "including repetitions" in prompt
    assert "including repetitions expressing only part" not in prompt
    old_rows, new_rows = base_checks.examples(original), base_checks.examples(prompt)
    assert len(old_rows) == len(new_rows) == 7
    changed_subjects = {"Reading books", "Continuing to read books despite noise"}
    for old, new in zip(old_rows, new_rows, strict=True):
        assert old[:2] == new[:2], "example post or subject changed"
        post, subject, response = new
        assert list(response) == base_checks.FIELDS
        assert response["meaning"] == old[2]["meaning"]
        assert response["expressible"] == old[2]["expressible"]
        assert isinstance(response["evidence"], str) and response["evidence"]
        expected = old[2]["mask"]
        if subject in changed_subjects:
            assert expected[-1] == {"word": 18, "text": "books"}
            expected = expected[:-1]
        else:
            assert response == old[2]
        assert response["mask"] == expected
        base_checks.selection.decode(json.dumps({"mask": response["mask"]}), post)
    edits = json.loads((HERE / "prompt-edits.json").read_text())
    assert edits["base_sha256"] == BASE_HASH
    expected = original
    for edit in edits["edits"]:
        assert expected.count(edit["old"]) == 1
        expected = expected.replace(edit["old"], edit["new"], 1)
    assert expected == prompt, "unrequested prompt changes"
    receipt = json.loads((HERE / "mask-prompt.md.revision.json").read_text())
    assert receipt["base_sha256"] == BASE_HASH
    assert receipt["prompt_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    print("PASS: three exact edits; seven valid examples; baseline and output format preserved. No inference.")


if __name__ == "__main__":
    main()
