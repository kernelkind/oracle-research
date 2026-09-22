"""Build the model-output-review batch for the PPv10 node-note order review.

Reads only local, already-saved study artifacts, the saved HDBv2 hierarchy
(hdbscan-cross-note) membership, and the review layout definition. Runs no
model calls and writes one derived artifact, review.json, the schema-1 batch
consumed by the existing `model-output-review` TUI. Cards are hierarchy nodes
plus the placement gaps; the question on each node card is node-note order.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOAL = ROOT.parent
REPO = ROOT.parents[2]
CORPUS = GOAL.parent / "real-note-fine-segmentation-v1"
PROMPT = GOAL / "ppv10-draft-v1" / "PPv10.md"
GROUPS_FILE = ROOT / "review-groups.json"
VECTOR_MAP = CORPUS / "vectors" / "vector-map.json"
PACKETS = CORPUS / "hdbscan-cross-note" / "review" / "review.json"
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


def mark_spans(text, byte_spans):
    """Render complete note text with the masks' UTF-8 byte spans merged and marked."""
    source = text.encode("utf-8")
    spans = []
    for start, end in byte_spans:
        if not 0 <= start < end <= len(source):
            raise ValueError("invalid byte span")
        left = len(source[:start].decode("utf-8"))
        right = left + len(source[start:end].decode("utf-8"))
        spans.append([left, right])
    if not spans:
        raise ValueError("empty mask spans")
    merged = []
    for left, right in sorted(spans):
        if merged and left <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], right)
        else:
            merged.append([left, right])
    parts, cursor = [], 0
    for left, right in merged:
        parts.extend((text[cursor:left], "⟦", text[left:right], "⟧"))
        cursor = right
    parts.append(text[cursor:])
    return "".join(parts)


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

    placements = {}
    for case in cases.values():
        if case["format"] != "corpus":
            placements.setdefault("outside-corpus", []).append(case["id"])
            continue
        vector = subjects.get(case["source_id"])
        node_id = None
        if vector is not None:
            for candidate, instances in nodes.items():
                if any(instance["vector_id"] == vector["vector_id"]
                       for instance in instances):
                    node_id = candidate
                    break
        placements.setdefault(node_id or "unassigned", []).append(case["id"])
    check_coverage(placements, list(cases))

    declared_sections = {section["id"]: section["cases"]
                         for section in definition["sections"]}
    derived_sections = {key: sorted(value) for key, value in placements.items()
                        if key not in {node["id"] for node in definition["nodes"]}}
    if derived_sections != {key: sorted(value)
                            for key, value in declared_sections.items()}:
        raise ValueError("declared gap sections do not match the derived placement")

    node_views = []
    for node in definition["nodes"]:
        node_views.append(_node_view(node, nodes[node["id"]], vectors, cases,
                                     placements[node["id"]]))
    section_views = [{"id": section["id"], "title": section["title"],
                      "commentary": section["commentary"],
                      "cases_sorted": sorted((cases[case_id] for case_id in section["cases"]),
                                             key=lambda case: (-case["score"], case["id"]))}
                     for section in definition["sections"]]

    all_comparisons = [comparison for study in studies.values()
                       for comparison in study["comparisons"]]
    owner = {case: key for key, placed in placements.items() for case in placed}
    comparisons_by_card = {}
    for comparison in all_comparisons:
        high, low = cases[comparison["higher"]], cases[comparison["lower"]]
        result, gap = verdict(high["score"], low["score"])
        entry = {**comparison, "result": result, "gap": gap,
                 "higher_score": high["score"], "lower_score": low["score"],
                 "informational": not comparison["kind"].startswith("clear"),
                 "crosses": None if owner[comparison["higher"]] == owner[comparison["lower"]]
                 else (owner[comparison["higher"]], owner[comparison["lower"]])}
        comparisons_by_card.setdefault(owner[comparison["higher"]], []).append(entry)

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
        "expectations_note": definition["expectations_note"],
        "limits_note": definition["limits_note"],
        "cases": cases,
        "placement_of": {case: key for key, placed in placements.items()
                         for case in placed},
        "placements": placements,
        "nodes": node_views,
        "sections": section_views,
        "comparisons_by_card": comparisons_by_card,
        "clear_counts": {result: sum(1 for entry in
                                     [e for group in comparisons_by_card.values()
                                      for e in group]
                                     if entry["kind"].startswith("clear")
                                     and entry["result"] == result)
                         for result in ("ordered", "tie", "reversed")},
        "scorer": summaries[0],
        "provenance": [{"path": str(path.relative_to(REPO)), "sha256": digest(path)}
                       for path in [PROMPT, GROUPS_FILE, VECTOR_MAP, PACKETS] +
                       [GOAL / name / file for name in definition["studies"]
                        for file in ("plan.json", "inputs.json", "results.json")]],
    }


def _node_view(node, instances, vectors, cases, case_ids):
    """Group one node's masks by note and order notes by their best saved score."""
    scored = {}
    for case_id in case_ids:
        scored[cases[case_id]["source_id"]] = cases[case_id]
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
        rows.append({"note_short": note_short, "members": members, "best": best})
    rows.sort(key=lambda row: (row["best"] is None, -(row["best"] or 0), row["note_short"]))
    return {"id": node["id"], "commentary": node["commentary"], "rows": rows,
            "note_count": len(rows), "mask_count": len(instances),
            "scored_count": len(case_ids)}


def display(text):
    """Whitespace-collapsed card face; the exact saved text stays under i."""
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()


def _order_line(row):
    masks = " + ".join(
        f"{instance['instance']}={case['score'] if case else 'unscored'}"
        for (instance, _vector), case in row["members"])
    if row["best"] is None:
        line = f"  {row['note_short']}: no score — position unknown — masks here: {masks}"
    else:
        line = f"  {row['note_short']}: {row['best']} — masks here: {masks}"
    if len(row["members"]) > 1:
        line += f" — {len(row['members'])} masks here; how they combine is undecided"
    return line


def _comment(parts):
    return "\n\n".join(part for part in parts if part)


def _checks_block(card_id, comparisons):
    lines = ["PREDECLARED CHECKS — before inference, not gold labels; "
             "not an accuracy rate"]
    if not comparisons:
        lines.append("  none for this card")
        return "\n".join(lines)
    words = {"ordered": "as expected", "tie": "no separation", "reversed": "REVERSED"}
    for comparison in comparisons:
        line = (f"  {words[comparison['result']]}: {comparison['higher']} over "
                f"{comparison['lower']} ({comparison['higher_score']} vs "
                f"{comparison['lower_score']}, gap {abs(comparison['gap'])})")
        if comparison["informational"]:
            line += " — tentative/related, informational only"
        if comparison["crosses"]:
            line += (f" — spans two cards ({comparison['higher']} in "
                     f"{comparison['crosses'][0]}, {comparison['lower']} in "
                     f"{comparison['crosses'][1]}); not this node's order")
        lines.append(line)
    return "\n".join(lines)


def _expectations_block(cases_in_order, note):
    lines = ["EXPECTATIONS — recorded before inference, not gold labels"]
    for case in cases_in_order:
        lines.append(f"  {case['id']}: " + (case.get("expectation") or "none recorded"))
    return "\n".join(lines)


def _scorer_block(context):
    scorer = context["scorer"]
    return ("PROVENANCE\n"
            f"  one saved call per mask · {scorer['model']} "
            f"{scorer['reasoning_effort']} via {scorer['provider']} · "
            f"PPv10 unchanged (sha256 {context['prompt_sha256'][:12]}…)")


def _disagreement(case, context):
    text = context["disagreements"].get(case["id"])
    return f"PRESERVED DISAGREEMENT\n  {case['id']}: {text}" if text else ""


def _card_cases(node, context):
    return [case for row in node["rows"] for (_instance, _vector), case in row["members"]
            if case] if "rows" in node else node["cases_sorted"]


def render_review(context):
    """Render the schema-1 batch: hierarchy node cards first, then the gap sections."""
    notes = [_node_card(node, context) for node in context["nodes"]]
    notes += [_section_card(section, context) for section in context["sections"]]
    review = {
        "schema_version": 1,
        "title": (f"PPv10 node-note order review v1 · {context['prompt_version']}: "
                  f"{context['prompt_status']} · HDBv2 nodes; mechanical display order only"),
        "notes": notes,
    }
    check_review(review)
    return review


def _node_card(node, context):
    cases = _card_cases(node, context)
    scored, total = node["scored_count"], node["mask_count"]
    if scored == total:
        status = f"order complete ({scored}/{total} masks scored)"
    elif scored > 1:
        status = f"order partial ({scored}/{total} masks scored)"
    else:
        status = f"order unscored ({total - scored} of {total} masks unscored)"
    header = (f"NODE {node['id']} · {node['note_count']} notes · {total} masks · {status}\n"
              f"Opening this node: are the most-about notes first? Shown order is the "
              f"saved scores, display only.\n"
              f"(Note text whitespace-collapsed here; exact text and scorer input under i.)\n\n")
    blocks = []
    for index, row in enumerate(node["rows"], 1):
        score = f"score {row['best']}" if row["best"] is not None else "no score"
        masks = " · ".join(
            f"{instance['instance']}={case['score'] if case else 'unscored'}"
            for (instance, _vector), case in row["members"])
        text = row["members"][0][0][0]["text"]
        flat = [span for (instance, _v), _c in row["members"]
                for span in instance["byte_spans"]]
        blocks.append(f"{index} · {row['note_short']} · {score}\n"
                      f"  masks here: {masks}\n{display(mark_spans(text, flat))}")
    comment = _comment([
        "WHAT THIS NODE IS\n  " + node["commentary"],
        "ORDER (node-note order)\n" + "\n".join(_order_line(row) for row in node["rows"]),
        _checks_block(node["id"], context["comparisons_by_card"].get(node["id"], [])),
        _expectations_block(cases, context["expectations_note"]),
        *(_disagreement(case, context) for case in cases),
        _scorer_block(context),
        f"LIMITS\n  {context['limits_note']}",
    ])
    return {
        "id": node["id"],
        "title": f"{node['id']} · {node['note_count']} notes, {total} masks · {status}",
        "text": header + "\n\n".join(blocks),
        "model_input": _inputs_block(cases),
        "results": [{"model": _model_pane(context), "output": _outputs_block(cases),
                     "comment": comment}],
    }


def _section_card(section, context):
    cases = section["cases_sorted"]
    header = (f"{section['title']}\nNo node-note order to judge until these masks are "
              f"placed in nodes.\n\n")
    blocks = [f"{case['id']} · score {case['score']} · {BAND_LABELS[band(case['score'])]}"
              f" · {case['label']}\n{display(case['input']['marked_post'])}"
              for case in cases]
    comment = _comment([
        "WHAT THIS IS\n  " + section["commentary"],
        _checks_block(section["id"], context["comparisons_by_card"].get(section["id"], [])),
        _expectations_block(cases, context["expectations_note"]),
        *(_disagreement(case, context) for case in cases),
        _scorer_block(context),
        f"LIMITS\n  {context['limits_note']}",
    ])
    return {
        "id": section["id"],
        "title": section["title"],
        "text": header + "\n\n".join(blocks),
        "model_input": _inputs_block(cases),
        "results": [{"model": _model_pane(context), "output": _outputs_block(cases),
                     "comment": comment}],
    }


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
    counts = context["clear_counts"]
    print(f"wrote {OUTPUT}")
    print(f"{len(review['notes'])} cards: {len(context['nodes'])} nodes + "
          f"{len(context['sections'])} gap sections; clear comparisons: "
          f"{counts['ordered']} ordered, {counts['tie']} ties, "
          f"{counts['reversed']} reversed (mechanical, not accuracy)")


if __name__ == "__main__":
    main()
