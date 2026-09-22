"""Build the read-only PPv10 ranking review UI from saved study artifacts.

Reads only local, already-saved study outputs and the review layout definition.
Runs no model calls and writes one derived artifact, review.html.
"""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOAL = ROOT.parent
PROMPT = GOAL / "ppv10-draft-v1" / "PPv10.md"
GROUPS_FILE = ROOT / "review-groups.json"
OUTPUT = ROOT / "review.html"

SEPARATE_STUDY = "ppv10-mpv3.43-muse13high-v1"

BANDS = {
    "central": (90, 100, "central 90–100"),
    "major": (70, 89, "major 70–89"),
    "secondary": (40, 69, "secondary 40–69"),
    "incidental": (10, 39, "incidental 10–39"),
    "absent": (0, 9, "essentially absent 0–9"),
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def band(score):
    """Map a prominence score to its PPv10 anchor band name."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("score must be an integer")
    for name, (low, high, _label) in BANDS.items():
        if low <= score <= high:
            return name
    raise ValueError("score outside 0-100")


def verdict(higher_score, lower_score):
    """Mechanical order check for one predeclared pair: ordered, tie, or reversed."""
    if band(higher_score) is None or band(lower_score) is None:
        raise ValueError("scores must be valid")
    gap = higher_score - lower_score
    if gap > 0:
        return "ordered", gap
    if gap == 0:
        return "tie", 0
    return "reversed", gap


def marked_html(marked_post):
    """Render the complete marked post with escaped text and highlighted selections."""
    if not marked_post or marked_post.count("⟦") != marked_post.count("⟧") or "⟦" not in marked_post:
        raise ValueError("missing or unbalanced mask markers")
    return (html.escape(marked_post)
            .replace("⟦", "<mark>").replace("⟧", "</mark>"))


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
        case["marked_post"] = item["input"]["marked_post"]
        case["study"] = name
        case["score"] = scores[item["id"]]["score"]
        cases[item["id"]] = case
    return {
        "name": name,
        "cases": cases,
        "comparisons": plan["comparisons"],
        "prompt_sha256": plan["prompt_sha256"],
        "summary": {"model": results["model"],
                    "reasoning_effort": results["reasoning_effort"],
                    "calls": results["new_calls"],
                    "tokens": results["usage"]["totalTokens"]},
    }


def load_separate_probe():
    """Load the separately saved Muse probe as one case card."""
    directory = GOAL / SEPARATE_STUDY
    inputs = read(directory / "inputs.json")
    results = read(directory / "results.json")
    return {
        "id": results["case"],
        "study": SEPARATE_STUDY,
        "label": "Coffee-bean note scored with the saved MPv3.43 mask",
        "note_id": inputs["note_id"],
        "source_id": "",
        "source": "saved mask from meta/muse-spark-1.3 mask work",
        "expectation": "",
        "mask": results["fragments"],
        "marked_post": inputs["input"]["marked_post"],
        "score": results["score"],
        "summary": {"model": results["model"],
                    "reasoning_effort": results["reasoning_effort"],
                    "calls": 1,
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

    separate = None
    if (GOAL / SEPARATE_STUDY / "results.json").exists():
        probe = load_separate_probe()
        separate = {**probe,
                    "commentary": next(item["commentary"] for item in definition["separate_work"]
                                      if item["id"] == probe["id"])}

    provenance = [{"path": str(PROMPT.relative_to(ROOT.parents[2])), "sha256": digest(PROMPT)},
                  {"path": str(GROUPS_FILE.relative_to(ROOT.parents[2])), "sha256": digest(GROUPS_FILE)}]
    for name in definition["studies"]:
        for file in ("plan.json", "inputs.json", "results.json"):
            path = GOAL / name / file
            provenance.append({"path": str(path.relative_to(ROOT.parents[2])),
                               "sha256": digest(path)})

    return {
        "prompt_version": definition["prompt_version"],
        "prompt_status": definition["prompt_status"],
        "prompt_sha256": definition["prompt_sha256"],
        "purpose": definition["purpose"],
        "caveats": definition["caveats"],
        "disagreements": definition["preserved_disagreements"],
        "open_questions": definition["open_questions"],
        "cases": cases,
        "groups": group_views,
        "singletons": [{"case": cases[item["id"]], "commentary": item["commentary"]}
                       for item in singletons],
        "separate": separate,
        "clear_counts": clear_counts,
        "informational_pairs": sum(1 for c in all_comparisons
                                  if not c["kind"].startswith("clear")),
        "study_summaries": [{"name": name, **study["summary"]}
                            for name, study in studies.items()],
        "provenance": provenance,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _case_card(case, rank=None):
    name = band(case["score"])
    label = BANDS[name][2]
    mask = " ".join(f"<code>{html.escape(fragment)}</code>" for fragment in case["mask"])
    source = html.escape(" · ".join(part for part in
                                   (case["study"], case.get("source_id", ""),
                                    case.get("source", "")) if part))
    expectation = (f'<p class="expectation"><b>Predeclared expectation:</b> '
                   f'{html.escape(case["expectation"])}</p>'
                   if case.get("expectation") else "")
    rank_html = f'<span class="rank">#{rank}</span>' if rank is not None else ""
    return f"""
      <article class="case">
        <div class="case-head">{rank_html}<span class="score band-{name}">{case["score"]}</span>
          <span class="band band-{name}">{label}</span>
          <span class="cid">{html.escape(case["id"])}</span>
          <span class="case-label">{html.escape(case["label"])}</span></div>
        <p class="mask">mask: {mask}</p>
        {expectation}
        <details><summary>complete marked post</summary>
          <pre class="post">{marked_html(case["marked_post"])}</pre></details>
        <p class="prov">{source}</p>
      </article>"""


def _comparison_row(comparison):
    result = comparison["result"]
    suffix = " · informational" if comparison["informational"] else ""
    return f"""
      <div class="comparison">
        <span class="pair">{html.escape(comparison["higher"])} ({comparison["higher_score"]})
          &gt; {html.escape(comparison["lower"])} ({comparison["lower_score"]})</span>
        <span class="tag">{html.escape(comparison["kind"])}</span>
        <span class="result result-{result}">{result}, gap {comparison["gap"]}{suffix}</span>
        <p class="reason">{html.escape(comparison["reason"])}</p>
      </div>"""


def render_html(context):
    """Render the complete self-contained read-only review page."""
    counts = context["clear_counts"]
    informational = context["informational_pairs"]
    caveats = "".join(f"\n        <li>{html.escape(text)}</li>"
                      for text in context["caveats"])
    disagreements = "".join(
        f'\n        <li><b>{html.escape(", ".join(item["cases"]))}:</b> {html.escape(item["text"])}</li>'
        for item in context["disagreements"])
    open_questions = "".join(f"\n        <li>{html.escape(text)}</li>"
                             for text in context["open_questions"])

    group_sections = []
    for group in context["groups"]:
        cards = "".join(_case_card(case, rank)
                        for rank, case in enumerate(group["cases_sorted"], 1))
        rows = "".join(_comparison_row(comparison)
                       for comparison in group["comparisons"])
        group_sections.append(f"""
    <section class="group">
      <h2>{html.escape(group["id"])} · {html.escape(group["title"])}
        <span class="kind">{html.escape(group["kind"].replace("_", "-"))}</span></h2>
      <p class="commentary">{html.escape(group["commentary"])}</p>
      <p class="sort-note">Cases sorted by saved score, highest first. Rank is display order, not a claim of correctness.</p>
      <div class="cases">{cards}</div>
      <div class="comparisons"><h3>Predeclared comparisons</h3>{rows}</div>
    </section>""")

    singleton_cards = "".join(
        f'<div class="singleton">{_case_card(item["case"])}'
        f'<p class="commentary">{html.escape(item["commentary"])}</p></div>'
        for item in context["singletons"])

    separate_html = ""
    if context["separate"]:
        probe = context["separate"]
        summary = probe["summary"]
        separate_html = f"""
    <section class="group separate">
      <h2>Separate work · one-call Muse probe</h2>
      <p class="commentary">{html.escape(probe["commentary"])}</p>
      {_case_card(probe)}
      <p class="prov">{html.escape(probe["study"])} · {html.escape(summary["model"])} ·
        reasoning {html.escape(str(summary["reasoning_effort"]))}</p>
    </section>"""

    summaries = " · ".join(
        f'{html.escape(item["name"])}: {html.escape(item["model"])} reasoning '
        f'{html.escape(str(item["reasoning_effort"]))}, {item["calls"]} calls, '
        f'{item["tokens"]} reported tokens'
        for item in context["study_summaries"])
    provenance = "".join(
        f'\n        <li><code>{html.escape(item["path"])}</code> sha256 {html.escape(item["sha256"])}</li>'
        for item in context["provenance"])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'">
  <title>PPv10 ranking review v1 · read-only</title>
  <link rel="icon" href="data:,">
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, sans-serif; color: #e6edf3; }}
    body {{ margin: 0; background: #161b22; }}
    header {{ padding: 16px 24px; border-bottom: 1px solid #374151; background: #1c2531; }}
    h1 {{ margin: 0 0 6px; font-size: 20px; }}
    h2 {{ font-size: 17px; margin: 0 0 4px; }}
    h3 {{ font-size: 14px; margin: 12px 0 4px; color: #9fb0c3; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 18px 24px 48px; }}
    .status {{ font-size: 14px; }}
    .banner {{ background: #2d2410; border: 1px solid #806020; border-radius: 6px;
      padding: 10px 14px; font-size: 14px; margin: 14px 0; }}
    .summary {{ background: #1c2531; border: 1px solid #374151; border-radius: 6px;
      padding: 10px 14px; font-size: 14px; }}
    ul {{ margin: 6px 0; padding-left: 22px; font-size: 14px; }}
    li {{ margin: 3px 0; }}
    section.group {{ background: #1c2531; border: 1px solid #374151; border-radius: 8px;
      padding: 14px 16px; margin: 16px 0; }}
    .kind {{ font-size: 12px; font-weight: normal; color: #9fb0c3;
      border: 1px solid #536378; border-radius: 10px; padding: 1px 8px; margin-left: 8px; }}
    .commentary {{ font-size: 14px; margin: 6px 0; }}
    .sort-note {{ font-size: 12px; color: #8b949e; }}
    article.case {{ border: 1px solid #374151; border-radius: 6px; padding: 10px 12px;
      margin: 10px 0; background: #161b22; }}
    .case-head {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }}
    .rank {{ color: #8b949e; font-size: 13px; }}
    .score {{ font-size: 20px; font-weight: 700; padding: 1px 9px; border-radius: 6px; }}
    .band {{ font-size: 12px; }}
    .cid {{ font-family: ui-monospace, monospace; font-size: 13px; color: #9fb0c3; }}
    .case-label {{ font-size: 14px; }}
    .band-central {{ background: #12351f; color: #3fb950; border: 1px solid #2ea04366; }}
    .band-major {{ background: #10263d; color: #58a6ff; border: 1px solid #388bfd66; }}
    .band-secondary {{ background: #2d2410; color: #d29922; border: 1px solid #bb800966; }}
    .band-incidental {{ background: #331c0e; color: #db6d28; border: 1px solid #bd561d66; }}
    .band-absent {{ background: #21262d; color: #8b949e; border: 1px solid #484f58; }}
    .mask {{ font-size: 13px; margin: 8px 0 4px; }}
    .mask code {{ background: #21262d; border-radius: 4px; padding: 1px 5px; }}
    .expectation {{ font-size: 13px; margin: 4px 0; color: #c9d5e3; }}
    details {{ margin: 6px 0; }}
    summary {{ cursor: pointer; font-size: 13px; color: #79c0ff; }}
    pre.post {{ white-space: pre-wrap; word-break: break-word; background: #0d1117;
      border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-size: 13px; }}
    mark {{ background: #1f6feb55; color: inherit; border-bottom: 2px solid #58a6ff;
      border-radius: 2px; padding: 0 1px; }}
    .prov {{ font-size: 12px; color: #8b949e; margin: 6px 0 0; }}
    .comparisons {{ margin-top: 8px; }}
    .comparison {{ border-left: 3px solid #536378; padding: 4px 10px; margin: 8px 0; }}
    .pair {{ font-family: ui-monospace, monospace; font-size: 13px; }}
    .tag {{ font-size: 12px; color: #9fb0c3; margin-left: 10px; }}
    .result {{ font-size: 12px; margin-left: 10px; }}
    .result-ordered {{ color: #3fb950; }}
    .result-tie {{ color: #d29922; }}
    .result-reversed {{ color: #f85149; }}
    .reason {{ font-size: 13px; margin: 4px 0 0; color: #c9d5e3; }}
    .disagreement {{ background: #331c0e; border: 1px solid #bd561d66; border-radius: 6px;
      padding: 10px 14px; font-size: 14px; }}
    footer {{ border-top: 1px solid #374151; padding: 14px 24px; font-size: 12px;
      color: #8b949e; }}
    footer code {{ word-break: break-all; }}
    button {{ font: inherit; padding: 5px 12px; cursor: pointer; background: #263445;
      color: #e5e7eb; border: 1px solid #536378; border-radius: 5px; margin-left: 8px; }}
  </style>
</head>
<body>
  <header>
    <h1>Prominence ranking review v1 — {html.escape(context["prompt_version"])}
      <span class="kind">{html.escape(context["prompt_status"])}</span>
      <button type="button" id="expand">Expand all posts</button>
      <button type="button" id="collapse">Collapse all</button></h1>
    <p class="status">Read-only review of already-saved scores grouped by selection meaning.
      No inference was run to build this page. {html.escape(context["purpose"])}</p>
    <p class="status">Prompt sha256 {html.escape(context["prompt_sha256"])}
      (verified at build time against PPv10.md).</p>
  </header>
  <main>
    <div class="banner"><b>Standing limits:</b>
      <ul>{caveats}</ul></div>
    <div class="summary">Mechanical order checks on predeclared pairs:
      <b>{counts["ordered"]}</b> clear ordered · <b>{counts["tie"]}</b> clear ties ·
      <b>{counts["reversed"]}</b> clear reversed; {informational} tentative/related pairs are
      informational only. Counts are not an accuracy measurement and the expectations are
      assistant predeclarations, not user-approved gold labels.</div>
{"".join(group_sections)}
    <section class="group">
      <h2>Single cases with no predeclared comparison</h2>
      {singleton_cards}
    </section>
    <section class="group disagreement">
      <h2>Preserved disagreements</h2>
      <ul>{disagreements}</ul>
    </section>
    <section class="group">
      <h2>Open questions</h2>
      <ul>{open_questions}</ul>
    </section>
{separate_html}
  </main>
  <footer>
    <p>Saved runs: {summaries}. Subscription catalog cost fields are not invoices.</p>
    <p>Build inputs and hashes:</p>
    <ul>{provenance}</ul>
    <p>Generated {html.escape(context["generated"])} by build_review.py from saved artifacts
      only. review.html is a derived local artifact and is excluded from commits.</p>
  </footer>
  <script>
    document.getElementById('expand').addEventListener('click', () =>
      document.querySelectorAll('details').forEach(d => d.open = true));
    document.getElementById('collapse').addEventListener('click', () =>
      document.querySelectorAll('details').forEach(d => d.open = false));
  </script>
</body>
</html>
"""


def main():
    context = build_context()
    OUTPUT.write_text(render_html(context), encoding="utf-8")
    counts = context["clear_counts"]
    print(f"wrote {OUTPUT}")
    print(f"cases: {len(context['cases'])}, groups: {len(context['groups'])}, "
          f"clear comparisons: {counts}")


if __name__ == "__main__":
    main()
