"""Build the model-output-review batch for the PPv10 node-note order review.

The batch is the node-note walk: one complete note per card, stepped in the
order the saved scores produce, each card answering only where the note sits,
which mask places it there, and its score. Analysis lives in README.md, not in
the cards. Reads only local, already-saved study artifacts, the saved HDBv2
(hdbscan-cross-note) membership, and the layout definition. Runs no model
calls and writes one derived artifact, review.json.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOAL = ROOT.parent
REPO = ROOT.parents[2]
CORPUS = GOAL.parent / "real-note-fine-segmentation-v1"
PROMPT = GOAL / "ppv10-draft-v1" / "PPv10.md"
GROUPS_FILE = ROOT / "review-groups.json"
VECTOR_MAP = CORPUS / "vectors" / "vector-map.json"
PACKETS = CORPUS / "hdbscan-cross-note" / "review" / "review.json"
TITLES = GOAL.parent / "hdbv2-node-titles-v21-astra-low" / "titles.json"
NAV_CATEGORIES = GOAL.parent / "navigation-research-v1" / "TRUE14" / "categories.json"
VERDICTS = CORPUS / "review-handoff" / "baseline" / "user-response.json"
OUTPUT = ROOT / "review.json"

MODEL_PANE = "PPv10 prominence · {model} reasoning {effort}"

BAND_LABELS = {
    "central": "central 90–100", "major": "major 70–89", "secondary": "secondary 40–69",
    "incidental": "incidental 10–39", "absent": "essentially absent 0–9",
}


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


def _mask_lines(masks):
    """Verified mask display: one line per mask, bracketed fragments separated by
    spaces (fine-segmentation-review render_instances convention), then its score."""
    return "\n".join(
        f"{label}  " + " ".join(f"⟦{fragment}⟧" for fragment in fragments)
        + f" — score {score if score is not None else 'unscored'}"
        for label, fragments, score in masks)


def check_coverage(placements, case_ids):
    """Require every case to sit in exactly one node or gap section."""
    seen = [case for placed in placements.values() for case in placed]
    if sorted(seen) != sorted(set(seen)):
        raise ValueError("a case is placed more than once")
    if sorted(seen) != sorted(case_ids):
        raise ValueError("review layout does not cover every scored case")


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


def load_nodes():
    """Load saved HDBv2 (hdbscan-cross-note) nodes and their member masks."""
    entries = read(VECTOR_MAP)["vectors"]
    vectors = {vector["vector_id"]: vector for vector in entries}
    subjects = {vector["reviewed_subject_id"]: vector for vector in entries}
    nodes = {packet["packet"]: packet["instances"]
             for packet in read(PACKETS)["packets"]}
    return vectors, subjects, nodes


def load_titles():
    """Saved node titles (hdbv2-node-titles-v21, then TRUE14 hierarchy labels)
    and saved user semantic-review verdicts."""
    generated = {entry["group"]: entry["title"] for entry in read(TITLES)["groups"]}
    labels = {node["node_id"]: node["label"]
              for node in read(NAV_CATEGORIES)["nodes"]}
    verdicts = {item["packet"]: item["verdict"] for item in read(VERDICTS)["judgments"]}
    titles = {}
    for node_id in set(generated) | set(labels):
        if node_id in generated:
            titles[node_id] = {"title": generated[node_id],
                               "source": "hdbv2-node-titles-v21"}
        else:
            titles[node_id] = {"title": labels[node_id], "source": "TRUE14 label"}
    for node_id, entry in titles.items():
        entry["verdict"] = verdicts.get(node_id)
    return titles


def build_context():
    """Assemble the review model from saved artifacts; raises on any gap."""
    definition = read(GROUPS_FILE)
    if digest(PROMPT) != definition["prompt_sha256"]:
        raise ValueError("prompt text does not match the recorded PPv10 hash")
    studies = {name: load_study(name) for name in definition["studies"]}
    for study in studies.values():
        if study["prompt_sha256"] != definition["prompt_sha256"]:
            raise ValueError(f"{study['name']} was not scored with the recorded PPv10 hash")
    cases = {case_id: case for study in studies.values()
             for case_id, case in study["cases"].items()}
    vectors, subjects, nodes = load_nodes()
    titles = load_titles()

    placements = {}
    for case in cases.values():
        if case["format"] != "corpus":
            case["short_id"] = None
            placements.setdefault("outside-corpus", []).append(case["id"])
            continue
        vector = subjects.get(case["source_id"])
        case["short_id"] = vector["short_id"] if vector else None
        node_id = None
        if vector is not None:
            for candidate, instances in nodes.items():
                if any(instance["vector_id"] == vector["vector_id"]
                       for instance in instances):
                    node_id = candidate
                    break
        placements.setdefault(node_id or "unassigned", []).append(case["id"])
    check_coverage(placements, list(cases))

    node_ids = {node["id"] for node in definition["nodes"]}
    derived_sections = {key: sorted(value) for key, value in placements.items()
                        if key not in node_ids}
    declared_sections = {section["id"]: sorted(section["cases"])
                         for section in definition["sections"]}
    if derived_sections != declared_sections:
        raise ValueError("declared gap sections do not match the derived placement")

    node_views = [_node_view(node, nodes[node["id"]], vectors, cases,
                             placements[node["id"]], titles.get(node["id"]))
                  for node in definition["nodes"]]
    section_views = [_section_view(section, cases) for section in definition["sections"]]

    owner = {case: key for key, placed in placements.items() for case in placed}
    comparisons = []
    for study in studies.values():
        for comparison in study["comparisons"]:
            high, low = cases[comparison["higher"]], cases[comparison["lower"]]
            result, gap = verdict(high["score"], low["score"])
            comparisons.append({**comparison, "result": result, "gap": gap,
                                "higher_score": high["score"], "lower_score": low["score"],
                                "crosses": None if owner[comparison["higher"]] ==
                                owner[comparison["lower"]]
                                else (owner[comparison["higher"]], owner[comparison["lower"]])})

    summaries = [study["summary"] for study in studies.values()]
    for summary in summaries[1:]:
        if (summary["model"], summary["reasoning_effort"]) != \
                (summaries[0]["model"], summaries[0]["reasoning_effort"]):
            raise ValueError("studies disagree on the scorer model")

    return {
        "prompt_version": definition["prompt_version"],
        "prompt_status": definition["prompt_status"],
        "prompt_sha256": definition["prompt_sha256"],
        "disagreements": {case_id: item["text"] for item in definition["preserved_disagreements"]
                          for case_id in item["cases"]},
        "cases": cases,
        "placement_of": owner,
        "placements": placements,
        "nodes": node_views,
        "sections": section_views,
        "comparisons": comparisons,
        "scorer": summaries[0],
        "provenance": [{"path": str(path.relative_to(REPO)), "sha256": digest(path)}
                       for path in [PROMPT, GROUPS_FILE, VECTOR_MAP, PACKETS,
                                    TITLES, NAV_CATEGORIES, VERDICTS] +
                       [GOAL / name / file for name in definition["studies"]
                        for file in ("plan.json", "inputs.json", "results.json")]],
    }


def _node_view(node, instances, vectors, cases, case_ids, title_entry):
    """Group one node's masks by note and order notes by their best saved score."""
    scored = {cases[case_id]["source_id"]: cases[case_id] for case_id in case_ids}
    by_note = {}
    for instance in instances:
        vector = vectors[instance["vector_id"]]
        by_note.setdefault(vector["note_short_id"], []).append((instance, vector))
    rows = []
    for note_short, members in by_note.items():
        member_cases = [scored.get(vector["reviewed_subject_id"]) for _, vector in members]
        best = max((case["score"] for case in member_cases if case), default=None)
        members = sorted(zip(members, member_cases),
                         key=lambda pair: pair[0][0]["byte_spans"][0])
        rows.append({"note_short": note_short, "members": members, "best": best,
                     "text": members[0][0][0]["text"]})
    rows.sort(key=lambda row: (row["best"] is None, -(row["best"] or 0), row["note_short"]))
    return {"id": node["id"], "rows": rows,
            "title": (title_entry or {}).get("title"),
            "title_source": (title_entry or {}).get("source"),
            "verdict": (title_entry or {}).get("verdict")}


def _section_view(section, cases):
    """Group a gap section's cases by note, best score first."""
    by_note = {}
    for case_id in section["cases"]:
        case = cases[case_id]
        by_note.setdefault(case["note_id"], []).append(case)
    rows = []
    for _note_id, members in by_note.items():
        members.sort(key=lambda case: case["id"])
        first = members[0]
        note_short = (first["source_id"].rsplit("-", 1)[0]
                      if first["format"] == "corpus"
                      else "+".join(case["id"] for case in members))
        rows.append({"note_short": note_short,
                     "cases": members,
                     "best": max(case["score"] for case in members),
                     "text": first["text"]})
    rows.sort(key=lambda row: (-row["best"], row["note_short"]))
    return {"id": section["id"], "title": section["title"], "label": section["label"],
            "rows": rows}


def render_review(context):
    """Render the node-note walk: one complete note per card, in order."""
    notes = []
    for node in context["nodes"]:
        total = len(node["rows"])
        title = f'"{node["title"]}"' if node["title"] else "(no saved title)"
        name = f"{node['id']} {title}"
        for index, row in enumerate(node["rows"], 1):
            position = f"position {index} of {total}"
            notes.append(_note_card(
                context, name=name,
                placement_line=f"{name} · {position} · order shown is the saved "
                               f"scores, display only",
                row=row, position=position, in_node=True,
                member_cases=[case for (_i, _v), case in row["members"] if case],
                mask_labels=[(instance["instance"], vector["fragments"],
                              case["score"] if case else None)
                             for (instance, vector), case in row["members"]]))
    for section in context["sections"]:
        total = len(section["rows"])
        for index, row in enumerate(section["rows"], 1):
            position = f"{index} of {total} (unordered)"
            notes.append(_note_card(
                context, name=section["id"],
                placement_line=f"{section['id']} ({section['label']}) · {position}",
                row=row, position=position, in_node=False,
                member_cases=row["cases"],
                mask_labels=[(case.get("short_id") or case["id"], case["mask"],
                              case["score"]) for case in row["cases"]]))
    review = {
        "schema_version": 1,
        "title": (f"PPv10 node-note order review v1 · {context['prompt_version']}: "
                  f"{context['prompt_status']} · the node-note walk, one complete note "
                  f"per card"),
        "notes": notes,
    }
    check_review(review)
    return review


def _score_text(member_cases):
    scores = sorted({case["score"] for case in member_cases}, reverse=True)
    return "score " + ", ".join(str(score) for score in scores) if scores else "no score"


def _note_card(context, name, placement_line, row, position, member_cases, mask_labels,
               in_node):
    key = row["note_short"]
    title = f"{name} · {position} · {key} · {_score_text(member_cases)}"
    lines = [placement_line, _mask_lines(mask_labels)]
    if in_node and row["best"] is None:
        lines.append("position unknown: this note has no saved score")
    if in_node and len(mask_labels) > 1:
        lines.append(f"{len(mask_labels)} masks in this node; how they combine is "
                     f"undecided (no sum/max/average)")
    case_ids = {case["id"] for case in member_cases}
    for comparison in context["comparisons"]:
        if not case_ids & {comparison["higher"], comparison["lower"]}:
            continue
        words = {"ordered": "holds", "tie": "no separation", "reversed": "REVERSED"}
        line = (f"predeclared {comparison['higher']} over {comparison['lower']}: "
                f"{words[comparison['result']]} ({comparison['higher_score']} vs "
                f"{comparison['lower_score']})")
        if comparison["crosses"]:
            line += (f" — spans two placements ({comparison['higher']} in "
                     f"{comparison['crosses'][0]}, {comparison['lower']} in "
                     f"{comparison['crosses'][1]})")
        lines.append(line)
    for case in member_cases:
        disagreement = context["disagreements"].get(case["id"])
        if disagreement:
            lines.append(f"PRESERVED DISAGREEMENT ({case['id']}): {disagreement}")
    scorer = context["scorer"]
    lines.append(f"one saved call per mask · {scorer['model']} {scorer['reasoning_effort']} "
                 f"via {scorer['provider']} · PPv10 unchanged "
                 f"{context['prompt_sha256'][:12]}…")
    card = {
        "id": f"{name.split()[0]}-{key}",
        "title": title,
        "text": row["text"],
        "results": [{"model": _model_pane(context),
                     "output": _outputs_block(member_cases)
                     or "no saved output — this mask was never scored",
                     "comment": "\n".join(lines)}],
    }
    if member_cases:
        card["model_input"] = _inputs_block(member_cases)
    return card


def _model_pane(context):
    scorer = context["scorer"]
    return MODEL_PANE.format(model=scorer["model"], effort=scorer["reasoning_effort"])


def _outputs_block(cases):
    return "\n".join(f"{case['id']}: {case['raw']}" for case in cases)


def _inputs_block(cases):
    return "\n\n".join(
        f"{case['id']} — exact scorer input:\n"
        f"{json.dumps(case['input'], ensure_ascii=False, indent=2)}" for case in cases)


def main():
    context = build_context()
    review = render_review(context)
    OUTPUT.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"{len(review['notes'])} note cards: {len(context['nodes'])} nodes then "
          f"{len(context['sections'])} gap sections (analysis lives in README.md)")


if __name__ == "__main__":
    main()
