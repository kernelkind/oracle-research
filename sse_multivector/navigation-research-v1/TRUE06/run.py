"""Run the frozen TRUE06 pairs through the unchanged production inference function."""
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
from true_category_probe import REVISION
from true_generated_title_probe import prepare_inputs
from true_holdout_probe import run_inference


if __name__ == "__main__":
    started = time.monotonic()
    plan = json.loads((HERE / "plan.json").read_text())
    for name, digest in plan["preservation_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Frozen input or implementation changed: {name}")
    fixture = json.loads((HERE / "fixture.json").read_text())
    titles_path = ROOT / "sse_multivector/hdbv2-node-titles-v21-astra-low/titles.json"
    titles = json.loads(titles_path.read_text())
    inputs = prepare_inputs(fixture, titles)
    if len(inputs) != plan["selection"]["model_directions"]:
        raise ValueError("Unexpected number of admitted directions")
    snapshot = Path(plan["unchanged"]["snapshot"]).resolve(strict=True)
    if snapshot.name != REVISION:
        raise ValueError("Wrong model revision")
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
        "experiment": "TRUE06", "revision": REVISION,
        "plan_sha256": sha256(HERE / "plan.json"),
        "fixture_sha256": sha256(HERE / "fixture.json"),
        "semantic_review_sha256": sha256(HERE / "semantic-review.json"),
        "source_titles_sha256": sha256(titles_path),
        "inputs_sha256": sha256(output / "inputs.json"),
        "source_sha256": source_hashes,
        "python_executable": sys.executable, "python_version": sys.version,
    })
    run_inference(snapshot, inputs, output, 4, started, experiment="TRUE06")
