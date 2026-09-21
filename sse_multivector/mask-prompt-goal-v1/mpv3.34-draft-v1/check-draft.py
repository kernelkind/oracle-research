"""Offline MPv3.34 contract/preservation checks; no inference or file writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "mpv3.33-draft-v1/mask-prompt.md"
BASE_HASH = "24211ff1362176ac5ad5f531d894d748e3e5abbc1fd9f572fb340811382a3f10"
FIELDS = ["meaning", "expressible", "evidence", "mask"]
spec = importlib.util.spec_from_file_location(
    "selection", ROOT / "position-selection-v6/selection.py"
)
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


def examples(prompt):
    rows = []
    for block in re.findall(r"<example>\s*(.*?)\s*</example>", prompt, re.S):
        post = re.search(r"<example_post>\n(.*?)\n</example_post>", block, re.S).group(1)
        indexed = re.search(
            r"<example_indexed_post>\n(.*?)\n</example_indexed_post>", block, re.S
        ).group(1)
        assert indexed == selection.index_post(post), "indexed post changed or invalid"
        for subject, raw in re.findall(
            r"<subject>(.*?)</subject>\s*<response>(.*?)</response>", block, re.S
        ):
            response = json.loads(raw, object_pairs_hook=selection.unique_object)
            rows.append((post, subject, response))
    return rows


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "mask-prompt.md"
    original = BASE.read_text()
    prompt = path.read_text()
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    old_rows, new_rows = examples(original), examples(prompt)
    assert len(old_rows) == len(new_rows) == 7
    for old, new in zip(old_rows, new_rows):
        assert old[:2] == new[:2], "example post or subject changed"
        post, subject, response = new
        assert list(response) == FIELDS, f"missing or unordered diagnostic fields: {subject}"
        assert isinstance(response["meaning"], str) and response["meaning"].strip()
        assert isinstance(response["evidence"], str) and response["evidence"].strip()
        assert type(response["expressible"]) is bool
        assert response["expressible"] == bool(response["mask"])
        assert response["mask"] == old[2]["mask"], "example selection changed"
        selection.decode(json.dumps({"mask": response["mask"]}), post)

    assert "together union into the exact semantic meaning" in prompt
    assert "occurrence" not in prompt.lower()
    assert 'Return only a JSON object with a "mask" array' not in prompt
    assert prompt[prompt.index("<post>"):] == original[original.index("<post>"):]
    for placeholder in ("{POST}", "{INDEXED_POST}", "{SUBJECT}"):
        assert prompt.count(placeholder) == original.count(placeholder) == 1
    # Position syntax and exclusions are not part of the semantic revision.
    assert prompt.split("Do not select URLs", 1)[1].split("\n\n", 1)[0] == original.split(
        "Do not select URLs", 1
    )[1].split("\n\n", 1)[0]
    start, end = "Use [start, end]", "<examples>"
    assert prompt[prompt.index(start):prompt.index(end)] == original[
        original.index(start):original.index(end)
    ]

    schema = json.loads((HERE / "output-schema.json").read_text())
    old_schema = json.loads((ROOT / "mpv3.28-draft-v1/output-schema.json").read_text())
    expected = {
        "type": "object",
        "properties": {
            "meaning": {"type": "string"},
            "expressible": {"type": "boolean"},
            "evidence": {"type": "string"},
            "mask": old_schema["properties"]["mask"],
        },
        "required": FIELDS,
        "additionalProperties": False,
    }
    assert schema == expected, "schema changed beyond diagnostic fields"
    assert list(schema["properties"]) == FIELDS
    receipt = json.loads((HERE / "mask-prompt.md.revision.json").read_text())
    assert receipt["base_sha256"] == BASE_HASH
    assert receipt["prompt_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"PASS: {len(new_rows)} diagnostic examples; selections, inputs, schema mask property and base hash preserved.")


if __name__ == "__main__":
    main()
