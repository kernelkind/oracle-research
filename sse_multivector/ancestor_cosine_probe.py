"""Plot saved mask-to-subject cosines along explicitly selected SP paths.

Read-only to source data: no inference, merges, or placement decisions. A case
identifies a mask and a particular SP occurrence of B, not all occurrences of
that wording or all possible branches. Root depth is zero; B is included.
"""

import argparse
import hashlib
import html
import math
from pathlib import Path
import struct
import textwrap

from sse_multivector.subject_order_probe import read, save
from sse_multivector.worker import _sha256_file


def ancestor_path(subjects, post, number):
    selected = [s for s in subjects if s["note_short_id"] == post]
    by_number = {s["number"]: s for s in selected}
    if len(by_number) != len(selected):
        raise ValueError("duplicate SP number")
    components = number.split(".")
    numbers = [".".join(components[:i]) for i in range(1, len(components) + 1)]
    if any(n not in by_number for n in numbers):
        raise ValueError(f"missing B or ancestor: {post}/{number}")
    return [by_number[n] for n in numbers]


def cosine(a, b):
    if not a or len(a) != len(b) or not all(math.isfinite(v) for v in (*a, *b)):
        raise ValueError("invalid vectors")
    norm = math.sqrt(sum(v*v for v in a) * sum(v*v for v in b))
    if not norm:
        raise ValueError("zero vector")
    return max(-1., min(1., sum(x*y for x, y in zip(a, b, strict=True)) / norm))


def score_path(mask, path, subject_vectors):
    points = [dict(subject=s["subject"], number=s.get("number"), depth=i, cosine=cosine(mask, v))
              for i, (s, v) in enumerate(zip(path, subject_vectors, strict=True))]
    maximum = max(p["cosine"] for p in points)
    return points, [i for i, p in enumerate(points) if abs(p["cosine"] - maximum) <= 1e-12]


def marked_post(text, byte_spans):
    raw, cursor, parts = text.encode(), 0, []
    for start, end in byte_spans:
        if not (cursor <= start < end <= len(raw)):
            raise ValueError("invalid mask spans")
        parts.extend([html.escape(raw[cursor:start].decode()), "<mark>",
                      html.escape(raw[start:end].decode()), "</mark>"])
        cursor = end
    parts.append(html.escape(raw[cursor:].decode()))
    return "".join(parts)


def load_vectors(folder):
    receipt_path, raw_path = folder / "worker-receipt.json", folder / "raw-vectors.f32le"
    receipt, raw = read(receipt_path), raw_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt["files"][raw_path.name]["sha256"]:
        raise ValueError(f"vector hash mismatch: {folder}")
    if len(raw) != receipt["row_count"] * receipt["dimensions"] * 4:
        raise ValueError("vector shape mismatch")
    vectors = struct.iter_unpack("<" + "f" * receipt["dimensions"], raw)
    rows = {(r["note_id"], r["subject_id"]): v for r, v in zip(receipt["rows"], vectors, strict=True)}
    if len(rows) != receipt["row_count"]:
        raise ValueError("duplicate worker row identities")
    return rows, receipt


def prepare_curves(source, probe, cases):
    inputs = read(probe / "inputs.json")
    mv, mr = load_vectors(source / "worker-result")
    sv, sr = load_vectors(probe / "worker-result")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "runtime"):
        if mr[key] != sr[key]:
            raise ValueError(f"SSE identity mismatch: {key}")
    if sr["proposal_sha256"] != _sha256_file(probe / "inputs.json"):
        raise ValueError("subject vectors do not match these inputs")
    for path, expected in inputs["protected_sha256"].items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected SOv1 input changed: {path}")
    subjects = inputs["subjects"]
    masks = {v["short_id"]: v for v in read(source / "vector-map.json")["vectors"]}
    posts = {p["note_id"]: p for p in inputs["posts"]}
    curves = []
    for case in cases:
        short_id, b_post, b_number = case.split(":")
        mask = masks[short_id]
        owners = [s for s in subjects if mask["vector_id"] in s["mask_vector_ids"]]
        if not owners:
            raise ValueError(f"mask not present in saved probe: {short_id}")
        for owner in owners:
            if (owner["note_id"] != mask["note_id"] or owner["byte_spans"] != mask["byte_spans"]
                    or owner["fragments"] != mask["fragments"]):
                raise ValueError("mask provenance mismatch")
        post = posts[mask["note_id"]]
        if [post["text"].encode()[a:b].decode() for a, b in mask["byte_spans"]] != mask["fragments"]:
            raise ValueError("mask differs from saved post")
        path = ancestor_path(subjects, b_post, b_number)
        anchors = [sv[(hashlib.sha256(s["subject"].encode()).hexdigest(), s["encoding_id"])] for s in path]
        points, peaks = score_path(mv[(mask["note_id"], mask["worker_subject_id"])], path, anchors)
        curves.append(dict(case=case, mask_id=short_id, source_post=post["note_short_id"],
                           source_subjects=list(dict.fromkeys(s["subject"] for s in owners)),
                           text=post["text"], fragments=mask["fragments"], byte_spans=mask["byte_spans"],
                           b_post=b_post, b_number=b_number, points=points, peaks=peaks))
    protected = [probe / "inputs.json", source / "vector-map.json", Path(__file__).resolve()]
    protected += [p / "worker-result" / f for p in (source, probe)
                  for f in ("worker-receipt.json", "raw-vectors.f32le")]
    return dict(experiment_id="ACv1", cases=curves,
                selection="explicit illustrative SP paths; not an automated candidate search",
                interpretation="a maximum is a candidate only; no acceptance threshold or placement applied",
                sources={str(p.resolve()): _sha256_file(p) for p in protected})


def plot_curves(report, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    curves = report["cases"]
    rows = math.ceil(len(curves) / 2)
    fig, axes = plt.subplots(rows, 2, figsize=(16, 4.7 * rows), squeeze=False)
    floor = min(0, min(p["cosine"] for c in curves for p in c["points"])) - .03
    for i, ax in enumerate(axes.flat):
        if i >= len(curves):
            ax.set_visible(False)
            continue
        c = curves[i]
        x, y = [p["depth"] for p in c["points"]], [p["cosine"] for p in c["points"]]
        ax.plot(x, y, "o-", color="#176b86", linewidth=2.5, markersize=7)
        for j in c["peaks"]:
            ax.plot(x[j], y[j], "*", color="#b85300", markersize=17, zorder=4)
        for depth, value in zip(x, y):
            ax.annotate(f"{value:.4f}", (depth, value), xytext=(0, 11), textcoords="offset points",
                        ha="center", fontsize=11, color="#132e3c")
        ax.set_xticks(x, [f"Depth {p['depth']}\n" + textwrap.fill(p["subject"], 26) for p in c["points"]], fontsize=10)
        ax.set_xlim(-.35, max(x) + .35)
        ax.set_ylim(floor, 1.08)
        ax.set_yticks([0, .2, .4, .6, .8, 1])
        ax.set_ylabel("Mask-to-subject cosine", fontsize=11)
        ax.grid(axis="y", alpha=.2)
        ax.spines[["top", "right"]].set_visible(False)
        title = f"{i+1}. {c['mask_id']} — {' / '.join(c['source_subjects'])}"
        ax.set_title(title + f"\nA from {c['source_post']}; B = {c['b_post']} SP {c['b_number']}", fontsize=12, pad=16)
    fig.suptitle("ACv1 · Where does each mask's cosine peak along a saved SP path?", fontsize=17, y=.985)
    fig.text(.5, .958, "Each point uses that subject's saved SSE vector. Orange star = maximum, not an approved placement.",
             ha="center", fontsize=12)
    fig.subplots_adjust(top=.91, bottom=.115, left=.065, right=.95, hspace=1.0, wspace=.30)
    fig.savefig(output / "curves.png", dpi=150)
    fig.savefig(output / "curves.svg")
    plt.close(fig)


def render_html(report):
    parts = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">',
             '<title>ACv1 — mask-to-ancestor cosine</title><style>body{font:17px/1.6 system-ui;max-width:1100px;',
             'margin:32px auto;padding:0 20px;color:#172d3b}img{width:100%}details{margin:24px 0}',
             'mark{background:#ffe293}blockquote{white-space:pre-wrap;margin:12px 0;padding:16px;',
             'background:#f3f6f8}td,th{text-align:left;padding:6px 20px 6px 0}h2{font-size:20px}</style>',
             '<h1>ACv1 — mask-to-ancestor cosine</h1><p>Saved vectors only. Each selected SP path is shown',
             ' root first, including B. Peaks are candidates, not decisions. These are illustrative paths,',
             ' not a complete search of all branches. No hierarchy was changed.</p>',
             '<a href="curves.png"><img src="curves.svg" alt="Six labeled mask-to-subject cosine curves"></a>']
    for c in report["cases"]:
        parts.append(f'<details><summary>{html.escape(c["mask_id"])} · ' +
                     html.escape(" / ".join(c["source_subjects"])) +
                     f' → {html.escape(c["b_post"])} SP {html.escape(c["b_number"])}</summary>')
        parts.append(f'<p>Mask {c["mask_id"]}, source post {c["source_post"]}:</p><blockquote>' +
                     marked_post(c["text"], c["byte_spans"]) + '</blockquote>')
        parts.append('<table><tr><th>Depth</th><th>SP subject</th><th>Cosine</th></tr>')
        for p in c["points"]:
            parts.append(f'<tr><td>{p["depth"]}</td><td>{html.escape(p["subject"])}</td><td>{p["cosine"]:.6f}</td></tr>')
        parts.append('</table></details>')
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--case", action="append", required=True, help="MASK_ID:POST_SHORT_ID:SP_NUMBER")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare_curves(args.source.resolve(), args.probe.resolve(), args.case)
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "curves.json", report)
    plot_curves(report, args.output)
    with (args.output / "index.html").open("x") as stream:
        stream.write(render_html(report))
    for c in report["cases"]:
        print(c["case"], [(p["subject"], round(p["cosine"], 4)) for p in c["points"]])


if __name__ == "__main__":
    main()
