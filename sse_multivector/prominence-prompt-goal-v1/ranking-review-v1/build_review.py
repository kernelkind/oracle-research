"""Build the model-output-review batch for the PPv10 ranking review.

Reads only local, already-saved study artifacts and the review layout
definition. Runs no model calls and writes one derived artifact, review.json,
the schema-1 batch consumed by the existing `model-output-review` TUI.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOAL = ROOT.parent
REPO = ROOT.parents[2]
PROMPT = GOAL / "ppv10-draft-v1" / "PPv10.md"
GROUPS_FILE = ROOT / "review-groups.json"
OUTPUT = ROOT / "review.json"

MODEL_PANE = "PPv10 prominence · {model} reasoning {effort}"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def band(score):
    """Map a prominence score to its PPv10 anchor band name."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("score must be an integer")
    bands = {"central": (90, 100), "major": (70, 89), "secondary": (40, 69),
             "incidental": (10, 39), "absent": (0, 9)}
    for name, (low, high) in bands.items():
        if low <= score <= high:
            return name
    raise ValueError("score outside 0-100")


BAND_LABELS = {
    "central": "central 90–100", "major": "major 70–89", "secondary": "secondary 40–69",
    "incidental": "incidental 10–39", "absent": "essentially absent 0–9",
}


def verdict(higher_score, lower_score):
    """Mechanical order check for one predeclared pair: ordered, tie, or reversed."""
    band(higher_score)
    band(lower_score)
    gap = higher_score - lower_score
    if gap > 0:
        return "ordered", gap
    if gap == 0:
        return "tie", 0
    return "reversed", gap


def check_coverage(placements, case_ids):
    """Require every case to be placed in exactly one review group or singleton slot."""
    seen = []
    for placement in placements:
        seen.extend(placement["cases"])
    if sorted(seen) != sorted(set(seen)):
        raise ValueError("a case is placed more than once")
    if sorted(seen) != sorted(case_ids):
        raise ValueError("review layout does not cover every scored case")


def check_comparisons(comparisons, placements):
    """Require both cases of every predeclared comparison to share one review group."""
    owners = {}
    for placement in placements:
        for case_id in placement["cases"]:
            owners[case_id] = placement["id"]
    for comparison in comparisons:
        for key in ("higher", "lower"):
            if comparison.get(key) not in owners:
                raise ValueError("comparison references an unplaced case")
        if owners[comparison["higher"]] != owners[comparison["lower"]]:
            raise ValueError("comparison cases do not share one review group")


def check_review(review):
    """Mirror the model-output-review loader's schema-1 validation."""
    if review.get("schema_version") != 1 or not review.get("title", "").strip() \
            or not review.get("notes"):
        raise ValueError("expected a nonempty schema-1 review")
    models = [result.get("model", "") for result in review["notes"][0].get("results", [])]
    if not models or len(set(models)) != len(models):
        raise ValueError("expected a nonempty list of distinct models")
    ids = set()
    for note in review["notes"]:
        model_input = note.get("model_input")
        if any(not str(note.get(key, "")).strip() for key in ("id", "title", "text")) \
                or (model_input is not None and not model_input.strip()) \
                or note["id"] in ids:
            raise ValueError("empty note fields or duplicate note IDs")
        ids.add(note["id"])
        if [result.get("model", "") for result in note.get("results", [])] != models:
            raise ValueError("all notes must have the same models in the same order")
        if any(not str(result.get(key, "")).strip()
               for result in note.get("results", []) for key in ("model", "output", "comment")):
            raise ValueError("model names, outputs, and comments must not be empty")


def load_study(name):
    """Merge one study's plan, saved inputs, and saved scores by case id."""
    directory = GOAL / name
    plan = read(directory / "plan.json")
    inputs = read(directory / "inputs.json")
    results = read(directory / "results.json")
    scores = {record["id"]: record for record in results["results"]}
    cases = {}
    for item in inputs:
        case = dict(item)
        case["mask"] = item["input"]["mask"]
        case["study"] = name
        case["score"] = scores[item["id"]]["score"]
        case["raw"] = scores[item["id"]]["raw"]
        cases[item["id"]] = case
    return {
        "name": name,
        "cases": cases,
        "comparisons": plan["comparisons"],
        "prompt_sha256": plan["prompt_sha256"],
        "summary": {"model": results["model"],
                    "reasoning_effort": results["reasoning_effort"],
                    "provider": plan["provider"],
                    "calls": results["new_calls"],
                    "tokens": results["usage"]["totalTokens"]},
    }


def build_context():
    """Assemble the full review model from the saved artifacts; raises on any gap."""
    definition = read(GROUPS_FILE)
    if digest(PROMPT) != definition["prompt_sha256"]:
        raise ValueError("prompt text does not match the recorded PPv10 hash")
    studies = {name: load_study(name) for name in definition["studies"]}
    for study in studies.values():
        if study["prompt_sha256"] != definition["prompt_sha256"]:
            raise ValueError(f"{study['name']} was not scored with the recorded PPv10 hash")
    cases = {case_id: case for study in studies.values()
             for case_id, case in study["cases"].items()}
    groups = definition["groups"]
    singletons = definition["singletons"]
    placements = list(groups) + [{"id": f"singleton-{item['id']}", "cases": [item["id"]]}
                                 for item in singletons]
    check_coverage(placements, list(cases))
    all_comparisons = [comparison for study in studies.values()
                       for comparison in study["comparisons"]]
    check_comparisons(all_comparisons, placements)

    group_views = []
    for group in groups:
        members = sorted((cases[case_id] for case_id in group["cases"]),
                         key=lambda case: (-case["score"], case["id"]))
        comparisons = []
        for comparison in all_comparisons:
            if comparison["higher"] in group["cases"]:
                high, low = cases[comparison["higher"]], cases[comparison["lower"]]
                result, gap = verdict(high["score"], low["score"])
                comparisons.append({**comparison, "result": result, "gap": gap,
                                    "higher_score": high["score"],
                                    "lower_score": low["score"],
                                    "informational": not comparison["kind"].startswith("clear")})
        group_views.append({**group, "cases_sorted": members, "comparisons": comparisons})

    clear_counts = {"ordered": 0, "tie": 0, "reversed": 0}
    for comparison in all_comparisons:
        if comparison["kind"].startswith("clear"):
            high, low = cases[comparison["higher"]], cases[comparison["lower"]]
            result, _gap = verdict(high["score"], low["score"])
            clear_counts[result] += 1

    summaries = [study["summary"] for study in studies.values()]
    for summary in summaries[1:]:
        if (summary["model"], summary["reasoning_effort"]) != \
                (summaries[0]["model"], summaries[0]["reasoning_effort"]):
            raise ValueError("studies disagree on the scorer model")

    return {
        "prompt_version": definition["prompt_version"],
        "prompt_status": definition["prompt_status"],
        "prompt_sha256": definition["prompt_sha256"],
        "caveats": definition["caveats"],
        "disagreements": {case_id: item["text"] for item in definition["preserved_disagreements"]
                          for case_id in item["cases"]},
        "cases": cases,
        "groups": group_views,
        "singletons": [{"case": cases[item["id"]], "commentary": item["commentary"]}
                       for item in singletons],
        "clear_counts": clear_counts,
        "informational_pairs": sum(1 for comparison in all_comparisons
                                  if not comparison["kind"].startswith("clear")),
        "scorer": summaries[0],
        "provenance": [{"path": str(path.relative_to(REPO)), "sha256": digest(path)}
                       for path in [PROMPT, GROUPS_FILE] +
                       [GOAL / name / file for name in definition["studies"]
                        for file in ("plan.json", "inputs.json", "results.json")]],
    }


def _comment(case, assessment, group_line, order_lines, disagreement, context):
    expectation = case.get("expectation") or \
        "None recorded for this case; see the predeclared order checks above."
    scorer = context["scorer"]
    parts = [f"My assessment: {assessment}"]
    if disagreement:
        parts.append(f"Preserved disagreement: {disagreement}")
    parts.append(group_line)
    if order_lines:
        parts.append("Predeclared order checks — mechanical order only, ties and "
                     "reversals kept separate, not an accuracy rate:")
        parts.append("\n".join(order_lines))
    parts.append("Predeclared expectation, recorded before inference by the assistant, "
                 f"not a gold label: {expectation}")
    parts.append(f"Scorer: {scorer['model']} reasoning {scorer['reasoning_effort']} via "
                 f"{scorer['provider']}; one saved call per case; unchanged PPv10 "
                 f"(sha256 {context['prompt_sha256'][:12]}…).")
    parts.append("Limits: saved masks unchanged and from several extraction versions; "
                 "prominence is not mask correctness, category membership, truth, quality, "
                 "usefulness, or personal interest; the production registry still freezes "
                 "PPv2 and PPv10 is not production-frozen.")
    return "\n\n".join(parts)


def render_review(context):
    """Render the schema-1 model-output-review batch, one note per mask/post pair."""
    notes = []
    for group in context["groups"]:
        ranking = ", ".join(f"{case['id']} {case['score']}" for case in group["cases_sorted"])
        group_label = f"{group['id']} · {group['title']}"
        group_line = (f"Group {group_label} "
                      f"({group['kind'].replace('_', '-')}), score-sorted: {ranking}.")
        order_lines = [
            f"{comparison['higher']} ({comparison['higher_score']}) > "
            f"{comparison['lower']} ({comparison['lower_score']}) "
            f"{comparison['kind']}: {comparison['result']}, gap {comparison['gap']}"
            f"{' (informational only)' if comparison['informational'] else ''}"
            for comparison in group["comparisons"]]
        for rank, case in enumerate(group["cases_sorted"], 1):
            notes.append(_note(case, group_label=group_label, rank=rank,
                               total=len(group["cases_sorted"]),
                               assessment=group["commentary"], group_line=group_line,
                               order_lines=order_lines, context=context))
    for singleton in context["singletons"]:
        case = singleton["case"]
        notes.append(_note(case, group_label="Singleton", rank=None, total=None,
                           assessment=singleton["commentary"],
                           group_line="Singleton · no predeclared comparison in its "
                                      "study plan.",
                           order_lines=[], context=context))
    review = {
        "schema_version": 1,
        "title": (f"PPv10 prominence ranking review v1 · {context['prompt_version']}: "
                  f"{context['prompt_status']} · mechanical order checks only"),
        "notes": notes,
    }
    check_review(review)
    return review


def _note(case, group_label, rank, total, assessment, group_line, order_lines, context):
    name = band(case["score"])
    score_text = f"score {case['score']} · {BAND_LABELS[name]}"
    if rank is None:
        title = f"{group_label} · {score_text}"
    else:
        title = f"{group_label} · rank {rank}/{total} · {score_text}"
    return {
        "id": case["id"],
        "title": title,
        "text": case["text"],
        "model_input": json.dumps(case["input"], ensure_ascii=False, indent=2),
        "results": [{
            "model": MODEL_PANE.format(model=context["scorer"]["model"],
                                       effort=context["scorer"]["reasoning_effort"]),
            "output": case["raw"],
            "comment": _comment(case, assessment, group_line, order_lines,
                                context["disagreements"].get(case["id"]), context),
        }],
    }


def main():
    context = build_context()
    review = render_review(context)
    OUTPUT.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    counts = context["clear_counts"]
    print(f"wrote {OUTPUT}")
    print(f"{len(review['notes'])} notes, 1 model pane; clear comparisons: "
          f"{counts['ordered']} ordered, {counts['tie']} ties, "
          f"{counts['reversed']} reversed (mechanical, not accuracy)")


if __name__ == "__main__":
    main()
