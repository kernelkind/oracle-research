#!/usr/bin/env python3
"""Offline native report comparisons; never executes model requests."""
import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256((json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")) + "\n").encode()).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path):
    path = Path(path)
    with (gzip.open(path, "rt") if path.suffix == ".gz" else path.open()) as source:
        return json.load(source)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with (gzip.open(path, "wt") if path.suffix == ".gz" else path.open("w")) as target:
        json.dump(value, target, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        target.write("\n")


def compare_verdicts(baseline, candidate):
    return "agree" if baseline == candidate else "discordant"


def normalize(check, value, mapping):
    if check != "matching" or value is None:
        return value
    if value not in mapping:
        raise ValueError("unknown returned teacher ID")
    return list(mapping[value])


def selected_cases(panel, stage):
    frozen = next(row for row in panel["stages"] if row["size"] == stage)
    keys, aliases = set(frozen["case_keys"]), set(frozen["aliases"])
    result = []
    for row in panel["cases"]:
        if row["key"] in keys:
            selected = [alias for alias in row["aliases"] if alias["alias"] in aliases]
            if not selected:
                raise ValueError("stage prompt has no selected aliases")
            result.append(dict(row, aliases=selected))
    if len(result) != len(keys):
        raise ValueError("unknown or duplicate frozen panel keys")
    return frozen, result


class Native:
    def __init__(self, panel_path):
        self.panel_path = Path(panel_path).resolve()
        self.panel = read(self.panel_path)
        self.panel_hash = file_hash(self.panel_path)
        for path, expected in {**self.panel["sources"], **self.panel["assessment_sources"]}.items():
            if file_hash(path) != expected:
                raise ValueError("frozen panel source changed: " + path)
        project_root = next(path for path in HERE.parents if (path / "experiment-runner.json").is_file())
        sys.path[:0] = [str(project_root), str(project_root.parent / "experiment-runner")]
        from experiment_runner import experiment, inputs, project, extraction_pipeline as engine
        from sse_multivector import distillation_review as review, distillation_review_assessment as assessment
        project.configure(project_root)
        self.experiment, self.inputs, self.engine = experiment, inputs, engine
        self.validator = project.inputs
        selection_path = next(Path(path) for path in self.panel["sources"] if Path(path).name == "selection.json")
        selection = read(selection_path)
        self.selection = dict(path=str(selection_path), sha256=file_hash(selection_path))
        self.invalid_answers = {row["id"] for cohort in ("random", "challenge")
                                for row in selection[cohort]["answers"] if row["errors"]}
        assessment_dir = next(Path(path).parent for path in self.panel["sources"]
                              if Path(path).name == "assessment.complete.json")
        assessed = assessment.load_assessments(assessment_dir, selection)
        if assessed["sources"] != self.panel["assessment_sources"]:
            raise ValueError("frozen assessment bindings differ")
        self.normalizers = {}
        for answer in selection["random"]["answers"] + selection["challenge"]["answers"]:
            teacher = review._TeacherIndex(answer["teacher"])
            mapping = {}
            for group in assessed["contexts"][answer["id"]]:
                numbers = sorted(group["teacher_numbers"])
                for number in numbers:
                    mapping[teacher.by_number[number]] = numbers
            self.normalizers[answer["id"]] = mapping
        self.plans, self.records = {}, {}
        self.files = engine.ReceiptFiles()
        self.pool_keys = {row["key"] for row in self.panel["cases"]}
        self.pool = {row["key"]: row for row in self.panel["cases"]}
        self.aliases = {(row["check"], alias["case_id"]): alias
                       for row in self.panel["cases"] for alias in row["aliases"]}

    def load_group(self, directory):
        directory = str(Path(directory).resolve())
        if directory not in self.plans:
            plan, config, manifest = self.experiment.load(Path(directory))
            self.plans[directory] = plan, config, manifest, {row["id"]: row for row in plan["cases"]}
        return self.plans[directory]

    def validate_row(self, row, directory, effort):
        plan, config, manifest, cases = self.load_group(directory)
        case = cases[row["id"]]
        check = case["evidence"]["check"]
        expected = self.panel["settings"]["baseline"]
        if effort not in ("xhigh", "high", "medium", "low") or config.reasoning_effort != effort:
            raise ValueError("native effort differs")
        for field in ("provider", "model", "transport", "concurrency"):
            if getattr(config, field) != expected[field]:
                raise ValueError("native setting differs: " + field)
        if plan["prompt"]["id"] != expected["prompts"][check]:
            raise ValueError("native approved prompt ID differs")
        sha = hashlib.sha256(case["prompt"].encode()).hexdigest()
        panel_case = self.pool[check + ":" + sha]
        if case["input_sha256"] not in panel_case["all_input_sha256"]:
            raise ValueError("native input hash differs from frozen panel")
        alias = self.aliases.get((check, case["id"]))
        if alias is not None:
            for field in ("answer_id", "cohort", "input_sha256"):
                actual = case["input_sha256"] if field == "input_sha256" else case["evidence"][field]
                if alias[field] != actual:
                    raise ValueError("frozen panel alias differs: " + field)
            if alias["reference_status"] != case["evidence"]["expectation_status"]:
                raise ValueError("frozen panel reference status differs")
            label = case["evidence"]["expected_teacher_id" if check == "matching" else "expected_valid"]
            if label != alias["reference_label"]:
                raise ValueError("frozen panel reference label differs")
        if self.inputs.digest(case["inputs"]) != case["input_sha256"]:
            raise ValueError("native input hash differs")
        for field, actual in (("input_sha256", case["input_sha256"]), ("prompt_sha256", sha)):
            if field in row and row[field] != actual:
                raise ValueError("snapshot " + field + " differs")
        if "inputs" in row and row["inputs"] != case["inputs"]:
            raise ValueError("snapshot inputs differ")
        if "prompt" in row and row["prompt"] != case["prompt"]:
            raise ValueError("snapshot prompt differs")
        result = dict(id=case["id"], experiment=str(Path(directory).resolve()), check=check,
            input_sha256=case["input_sha256"], prompt_sha256=sha, status=row["status"],
            evidence={field: case["evidence"][field] for field in ("answer_id", "cohort", "check")},
            protocol={field: manifest.get(field) for field in ("provider", "model", "runner_version", "runner_sha256",
                "timeout_seconds", "max_output_tokens", "response_schema_sha256", "transport", "prompt_cache_key")},
            prefix_sha256=hashlib.sha256(manifest.get("prompt_cache_prefix", "").encode()).hexdigest(),
            request_sha256=self.engine._prompt_request_key(manifest, case["prompt"]))
        receipt = row.get("receipt")
        if receipt is not None:
            path = receipt["results_path"]
            if Path(path).resolve() != (config.run_directory / "results.jsonl").resolve():
                raise ValueError("snapshot receipt is outside its native group")
            if path not in self.records:
                self.records[path] = {self.inputs.digest(record): record
                                      for record in map(json.loads, (line for line in self.files.lines(Path(path))
                                                                    if line.endswith(b"\n")))}
            record = self.records[path][receipt["record_sha256"]]
            if record["job_key"] != "prompt:" + case.get("job_id", case["id"]):
                raise ValueError("snapshot receipt case differs")
            result.update(receipt=receipt, reused=row.get("reused", False))
            if row["status"] == "valid":
                self.engine.validate_prompt_receipt(replace(config, prompts=(self.engine.PromptJob(
                    case.get("job_id", case["id"]), case["prompt"]),)), manifest, record, files=self.files)
                validated = self.validator.validate(plan["dataset"], case, record["final_output_raw"], config.output_schema)
                if validated["status"] != "valid" or row.get("parsed") != validated["parsed"]:
                    raise ValueError("snapshot verdict differs from verified receipt")
                result["parsed"] = validated["parsed"]
                result["original_receipt"] = record.get("reused_from", receipt)
        elif row["status"] == "valid":
            raise ValueError("semantic panel response lacks a receipt")
        return result

    def snapshot(self, path, effort):
        value = read(path)
        frozen = value.get("frozen_panel_verdicts")
        if value.get("kind") == "effort-study-native-snapshot":
            sha = value.pop("sha256")
            if digest(value) != sha or value["panel_sha256"] != self.panel_hash or value["effort"] != effort:
                raise ValueError("compact snapshot seal, panel or effort differs")
            rows = [self.validate_row(row, row["experiment"], effort) for row in value["rows"]]
            source = value["source_report"]
        else:
            if value["selection"] != self.selection:
                raise ValueError("native evaluator selection differs")
            rows = []
            for native in value["experiments"]:
                for row in native["cases"]:
                    key = row["evidence"]["check"] + ":" + hashlib.sha256(row["prompt"].encode()).hexdigest()
                    if key in self.pool_keys and row.get("origin") != "mechanical":
                        rows.append(self.validate_row(row, native["experiment"], effort))
            source = dict(path=str(Path(path).resolve()), sha256=file_hash(path))
        result = dict(schema_version=1, kind="effort-study-native-snapshot", panel_sha256=self.panel_hash,
                      source_report=source, selection=self.selection, effort=effort, rows=rows)
        if frozen is not None:
            if frozen != freeze_panel(self.panel, result, self.normalizers):
                raise ValueError("frozen baseline decisions differ from validated receipts")
            result["frozen_panel_verdicts"] = frozen
            result["frozen_at_utc"] = value["frozen_at_utc"]
        result["sha256"] = digest(result)
        return result


def outcome(case, aliases, snapshots, mappings):
    relevant = [row for row in snapshots if row["check"] == case["check"]
                and row["prompt_sha256"] == case["prompt_sha256"]]
    states = Counter(row["status"] for row in relevant)
    valid = [row for row in relevant if row["status"] == "valid"]
    raw = {json.dumps(row["parsed"]["teacher_id" if case["check"] == "matching" else "valid"]) for row in valid}
    if not raw:
        return dict(status="missing", snapshot_states=dict(states), receipts=[])
    valid.sort(key=lambda row: (row["experiment"], row["id"], row["receipt"]["record_sha256"]))
    normalized = {json.dumps(normalize(case["check"], json.loads(value), mappings[alias["answer_id"]]))
                  for alias in aliases for value in raw}
    chosen = valid[0]
    chosen_raw = chosen["parsed"]["teacher_id" if case["check"] == "matching" else "valid"]
    return dict(status="valid" if len(normalized) == 1 else "conflicting_verdicts",
        raw_verdicts=[json.loads(value) for value in sorted(raw)],
        raw_alias_variants=len(raw) > 1,
        normalized_verdicts=[json.loads(value) for value in sorted(normalized)], snapshot_states=dict(states),
        chosen=dict(case_id=chosen["id"], experiment=chosen["experiment"], receipt=chosen["receipt"],
                    raw_verdict=chosen_raw, normalized_verdict=normalize(case["check"], chosen_raw,
                                                                       mappings[aliases[0]["answer_id"]])),
        receipts=[dict(case_id=row["id"], experiment=row["experiment"], receipt=row["receipt"],
                       original_receipt=row["original_receipt"], reused=row["reused"]) for row in valid])


def freeze_panel(panel, snapshot, mappings):
    results = {case["key"]: outcome(case, case["aliases"], snapshot["rows"], mappings) for case in panel["cases"]}
    missing = [key for key, row in results.items() if row["status"] == "missing"]
    if missing:
        raise ValueError(f"baseline panel has {len(missing)} missing prompts; bridge them before freezing")
    return results


def reference_agreement(aliases, result):
    resolved = [alias for alias in aliases if alias["reference_status"] != "unresolved"]
    labels = {json.dumps(alias["reference_label"]) for alias in resolved}
    raw = {json.dumps(value) for value in result.get("raw_verdicts", [])}
    status = ("missing_response" if result["status"] == "missing" else "conflicting_response" if len(raw) != 1
              else "unresolved_reference" if not labels else "conflicting_reference" if len(labels) != 1
              else "agrees_reference" if raw == labels else "disagrees_reference")
    return dict(status=status, resolved_occurrences=len(resolved), unresolved_occurrences=len(aliases)-len(resolved),
                labels=[json.loads(value) for value in sorted(labels)])


def analyze(panel, stage, snapshots, mappings):
    frozen, cases = selected_cases(panel, stage)
    candidates = [effort for effort in snapshots if effort != "xhigh"]
    rows, missing = [], defaultdict(list)
    for case in cases:
        aliases = case["aliases"]
        results = {effort: (snapshot["frozen_panel_verdicts"][case["key"]]
                           if effort == "xhigh" and "frozen_panel_verdicts" in snapshot
                           else outcome(case, next(row for row in panel["cases"] if row["key"] == case["key"])["aliases"],
                                        snapshot["rows"], mappings)) for effort, snapshot in snapshots.items()}
        paired = {}
        for effort in candidates:
            baseline, candidate = results.get("xhigh"), results[effort]
            paired[effort] = ("missing" if baseline is None or baseline["status"] == "missing" or candidate["status"] == "missing"
                             else "conflicting_verdicts" if baseline["status"] != "valid" or candidate["status"] != "valid"
                             else compare_verdicts(baseline["normalized_verdicts"], candidate["normalized_verdicts"]))
        for effort, result in results.items():
            if result["status"] == "missing":
                snapshot_rows = [row for row in snapshots[effort]["rows"] if row["check"] == case["check"]
                                 and row["prompt_sha256"] == case["prompt_sha256"]]
                row = next((row for alias in aliases for row in snapshot_rows if row["id"] == alias["case_id"]), None)
                if row is None:
                    raise ValueError("missing frozen pool row; compact/full snapshot omitted its native group")
                missing[(effort, row["experiment"])].append(row["id"])
        rows.append(dict(key=case["key"], input_sha256=case["input_sha256"], prompt_sha256=case["prompt_sha256"],
            aliases=[{key: alias[key] for key in ("alias", "answer_id", "case_id", "note_id", "cohort", "role", "reference_status", "reference_label")}
                     for alias in aliases], results=results, paired=paired,
            raw_agent_reference={effort: reference_agreement(aliases, result) for effort, result in results.items()}))
    def counts(selected, predicate=lambda alias: True):
        return dict(distinct_prompts=len(selected),
            paired={effort: dict(Counter(row["paired"][effort] for row in selected)) for effort in candidates},
            raw_agent_reference={effort: dict(Counter(reference_agreement(
                [alias for alias in row["aliases"] if predicate(alias)], row["results"][effort])["status"] for row in selected))
                                 for effort in snapshots})
    summary = counts(rows)
    summary["roles"] = {role: counts([row for row in rows if any(alias["role"] == role for alias in row["aliases"])],
                                     lambda alias: alias["role"] == role)
                        for role in sorted({alias["role"] for row in rows for alias in row["aliases"]})}
    summary["cohorts"] = {cohort: counts([row for row in rows if any(alias["cohort"] == cohort for alias in row["aliases"])],
                                         lambda alias: alias["cohort"] == cohort)
                          for cohort in ("random", "challenge")}
    summary["roles_by_cohort"] = {role: {cohort: counts([row for row in rows if any(
        alias["role"] == role and alias["cohort"] == cohort for alias in row["aliases"])],
        lambda alias: alias["role"] == role and alias["cohort"] == cohort)
        for cohort in ("random", "challenge")} for role in summary["roles"]}
    summary["paired_complete"] = bool(candidates) and all(value == "agree" or value == "discordant"
        for row in rows for value in row["paired"].values())
    summary["baseline_frozen"] = "frozen_panel_verdicts" in snapshots.get("xhigh", {})
    summary["qualification_blocked"] = not summary["paired_complete"] or not summary["baseline_frozen"]
    return dict(schema_version=1, inference_calls=0, stage=stage, aliases=frozen["aliases"], summary=summary,
        basis="Normalized paired verdict agreement, not accuracy. Same verdicts cancel even if both wrong. "
              "Raw agent-reference agreement is separate; no adjudication or reference changes. Role/cohort sets overlap; global prompts count once.",
        missing_native_pool_cases=[dict(effort=effort, experiment=group, case_ids=sorted(set(ids)))
                                   for (effort, group), ids in sorted(missing.items())], rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--compact", type=Path, help="compact one full/gzip native evaluator report")
    parser.add_argument("--effort", choices=("xhigh", "high", "medium", "low"))
    parser.add_argument("--freeze-baseline", action="store_true", help="freeze all xhigh panel choices after bridging; refuse missing prompts")
    parser.add_argument("--stage", type=int, choices=(5, 10, 20, 40, 60), default=5)
    parser.add_argument("--report", action="append", default=[], metavar="EFFORT=FILE")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is None:
        parser.error("--output is required")
    if args.freeze_baseline and not args.compact:
        parser.error("--freeze-baseline requires --compact")
    native = Native(args.panel)
    if args.compact:
        if not args.effort:
            parser.error("--compact requires --effort")
        result = native.snapshot(args.compact, args.effort)
        if args.freeze_baseline:
            if args.effort != "xhigh" or args.output.exists():
                parser.error("baseline freeze requires xhigh and a new output path")
            result.pop("sha256")
            result["frozen_panel_verdicts"] = freeze_panel(native.panel, result, native.normalizers)
            result["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()
            result["sha256"] = digest(result)
    else:
        snapshots = {}
        for item in args.report:
            effort, path = item.split("=", 1)
            if effort in snapshots:
                parser.error("duplicate report effort")
            snapshots[effort] = native.snapshot(path, effort)
        if "xhigh" not in snapshots:
            parser.error("--report xhigh=FILE is required")
        result = analyze(native.panel, args.stage, snapshots, native.normalizers)
        protocols = {}
        for snapshot in snapshots.values():
            for row in snapshot["rows"]:
                key = row["check"] + ":" + row["prompt_sha256"]
                protocol = row["protocol"], row["prefix_sha256"]
                if key in protocols and protocols[key] != protocol:
                    raise ValueError("paired prompt settings/schema/cache differ beyond effort")
                protocols[key] = protocol
        stage = next(row for row in native.panel["stages"] if row["size"] == args.stage)
        result["pipeline_invalid_saved_outputs"] = [alias for alias, identifier in zip(stage["aliases"], stage["answer_ids"])
                                                   if identifier in native.invalid_answers]
        result.update(panel=dict(path=str(native.panel_path), sha256=native.panel_hash),
                      reports={effort: snapshot["source_report"] for effort, snapshot in snapshots.items()},
                      baseline_freeze=dict(snapshot_sha256=snapshots["xhigh"]["sha256"],
                          frozen_at_utc=snapshots["xhigh"].get("frozen_at_utc")),
                      chronology="Root must freeze xhigh before lower calls. Native receipt provenance is retained; "
                                 "ordering is not inferred from absent receipt timestamps.")
    write(args.output, result)
    if not args.compact:
        from sse_multivector.evaluation_publication import export_comparison
        export_comparison(args.output, result=result, execution_status='complete')
    summary = result.get("summary", {})
    print(json.dumps(dict(output=str(args.output), bytes=args.output.stat().st_size,
        rows=len(result["rows"]), distinct_prompts=summary.get("distinct_prompts"),
        missing_native_cases=sum(len(row["case_ids"]) for row in result.get("missing_native_pool_cases", [])),
        qualification_blocked=summary.get("qualification_blocked")), indent=2))


if __name__ == "__main__":
    main()
