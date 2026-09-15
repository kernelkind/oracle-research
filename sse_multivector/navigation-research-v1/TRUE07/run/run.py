"""TRUE07: frozen manual title variants; unchanged production inference."""
import json
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION
from true_generated_title_probe import prepare_inputs
from true_holdout_probe import run_inference


if __name__ == "__main__":
    started = time.monotonic()
    plan = json.loads((HERE / "plan.json").read_text())
    for name, digest in plan["preservation_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Frozen source changed: {name}")
    fixture = json.loads((HERE / "fixture.json").read_text())
    titles_path = HERE / "variants.json"
    if sha256(titles_path) != fixture["source_titles_sha256"]:
        raise ValueError("Frozen variants changed")
    titles = json.loads(titles_path.read_text())
    inputs = prepare_inputs(fixture, titles)
    for row in inputs:
        row["domain"] = "manual-title-variants"
        row["relationship"] = row["id"].split("-")[0]
        row["a_wording"] = int(row["a_id"].rsplit("-w", 1)[1])
        row["b_wording"] = int(row["b_id"].rsplit("-w", 1)[1])
    if len(inputs) != 60 or len({row["model_input"] for row in inputs}) != 60:
        raise ValueError("Expected 60 unique directed inputs")
    if sum(row["expected"] for row in inputs) != 12:
        raise ValueError("Expected 12 positive and 48 negative judgments")
    frozen = json.loads((HERE / "frozen.json").read_text())
    for name, digest in frozen["files"].items():
        if sha256(HERE / name) != digest:
            raise ValueError(f"Frozen experiment changed: {name}")
    if inputs != json.loads((HERE / "inputs.json").read_text()):
        raise ValueError("Prepared inputs differ from pre-inference freeze")
    snapshot = Path(plan["unchanged"]["snapshot"]).resolve(strict=True)
    if (snapshot.name != REVISION or snapshot.parent.name != "snapshots"
            or snapshot.parent.parent.name != "models--" + MODEL_ID.replace("/", "--")):
        raise ValueError("Wrong model snapshot")
    output = HERE / "run"
    output.mkdir(exist_ok=False)
    save_json(output / "inputs.json", inputs)
    source_hashes = {}
    for source in [Path(__file__), *(CODE / name for name in (
            "true_generated_title_probe.py", "true_holdout_probe.py",
            "true_category_probe.py", "hierarcaps_mask_probe.py"))]:
        shutil.copyfile(source, output / source.name)
        source_hashes[source.name] = sha256(output / source.name)
    save_json(output / "started.json", {
        "experiment": "TRUE07", "revision": REVISION,
        "frozen_sha256": sha256(HERE / "frozen.json"),
        "source_titles_sha256": sha256(titles_path),
        "inputs_sha256": sha256(output / "inputs.json"),
        "source_sha256": source_hashes,
        "python_executable": sys.executable, "python_version": sys.version,
    })
    run_inference(snapshot, inputs, output, 4, started, experiment="TRUE07")

