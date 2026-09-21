"""Offline MPv3.37 checks: requested text, preservation and example decoding only."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "mpv3.36-draft-v1/mask-prompt.md"
BASE_HASH = "d460ed88a1ae18e0e5c5a9a3f335465ff40df27393c6c0129f77763104190ffd"
spec = importlib.util.spec_from_file_location("base_checks", ROOT / "mpv3.34-draft-v1/check-draft.py")
base_checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_checks)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "mask-prompt.md"
    original, prompt = BASE.read_text(), path.read_text()
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    step = prompt.split("2. Determine whether it is expressible.", 1)[1].split("\n\n3.", 1)[0]
    assert "all required meaning, details and relationships" in step, "missing explicit completeness requirement"
    assert "without having to include meaning the target does not specify" in step
    assert "both conditions" in step
    assert "removed" not in step and "removing" not in step
    request = json.loads((HERE / "prompt-edits.json").read_text())
    assert request["base_sha256"] == BASE_HASH and len(request["edits"]) == 1
    edit = request["edits"][0]
    assert edit["old"].startswith("2. Determine whether it is expressible.")
    assert "\n\n" not in edit["old"] and "\n\n" not in edit["new"]
    assert original.count(edit["old"]) == 1
    assert prompt == original.replace(edit["old"], edit["new"], 1), "changes outside step 2"
    rows = base_checks.examples(prompt)
    assert rows == base_checks.examples(original) and len(rows) == 8
    for post, _, response in rows:
        assert list(response) == base_checks.FIELDS
        base_checks.selection.decode(json.dumps({"mask": response["mask"]}), post)
    receipt = json.loads((HERE / "mask-prompt.md.revision.json").read_text())
    assert receipt["base_sha256"] == BASE_HASH
    assert receipt["prompt_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert receipt["edits"] == request["edits"]
    print("PASS: only step 2 changed; eight examples decode unchanged; baseline and receipt verified. No inference.")


if __name__ == "__main__":
    main()
