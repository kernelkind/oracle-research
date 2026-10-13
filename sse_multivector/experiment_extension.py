"""Oracle input/view commands; execution is owned by experiment-runner."""
import json
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from . import experiment_inputs as inputs
from experiment_runner import extraction_pipeline as engine
from experiment_runner.experiment import read, write, report, load, locked

def relation_diagnostics(cases):
    """Compare five-way decisions and exact A/B reversals, without gold claims."""
    inverse = {'equivalent': 'equivalent', 'a_parent_of_b': 'b_parent_of_a',
               'b_parent_of_a': 'a_parent_of_b', 'neither': 'neither', 'uncertain': 'uncertain'}

    def relation(case):
        parsed = case.get('parsed')
        value = parsed.get('relation') if isinstance(parsed, dict) else None
        return value if case.get('status') == 'valid' and isinstance(value, str) and value in inverse else None

    counts, confusion, by_input = Counter(), Counter(), {}
    for case in cases:
        value = relation(case)
        if value is not None:
            counts[value] += 1
            prior = relation(case.get('baseline') or {})
            if prior is not None:
                confusion[prior, value] += 1
        try:
            data = json.loads(case['inputs']['INPUT_JSON'])
            if set(data) != {'A', 'B'} or not all(isinstance(data[k], list) for k in ('A', 'B')):
                continue
            key = json.dumps([data['A'], data['B']], sort_keys=True, ensure_ascii=False)
            reverse = json.dumps([data['B'], data['A']], sort_keys=True, ensure_ascii=False)
        except (KeyError, TypeError, ValueError):
            continue
        by_input.setdefault(key, []).append((case, reverse))
    if not counts:
        return None
    pairs, seen = [], set()
    for key, rows in by_input.items():
        if len(rows) != 1 or key in seen:
            continue
        case, reverse = rows[0]
        other = by_input.get(reverse, [])
        # Repeated ordered inputs and self-identical A/B groups are ambiguous;
        # do not pick a partner by case ID or count self-agreement as evidence.
        if key == reverse or len(other) != 1:
            continue
        seen.update((key, reverse))
        values = [relation(case), relation(other[0][0])]
        comparable = all(v is not None for v in values)
        pairs.append({'cases': [case['id'], other[0][0]['id']], 'relations': values,
                      'consistent': values[1] == inverse[values[0]] if comparable else None})
    return {'interpretation': 'Teacher agreement and reversal consistency are diagnostic, not accuracy.',
            'relation_counts': dict(counts),
            'baseline_comparable': sum(confusion.values()),
            'baseline_agree': sum(n for (a, b), n in confusion.items() if a == b),
            'baseline_confusion': [{'baseline': a, 'candidate': b, 'count': n}
                                   for (a, b), n in sorted(confusion.items())],
            'reversal_comparable': sum(p['consistent'] is not None for p in pairs),
            'reversal_consistent': sum(p['consistent'] is True for p in pairs),
            'reversal_pairs': pairs}


def collect(directories, output, worker_config=None):
    """Publish validated extraction inputs without inference or source writes."""
    output = output.expanduser().resolve()
    if output.exists():
        raise ValueError("collection output already exists")
    bundles, protected, provenance = [], {}, []
    for directory in directories:
        directory = directory.expanduser().resolve()
        if output == directory or directory in output.parents:
            raise ValueError("collection output must be outside saved experiments")
        plan, _, _ = load(directory)
        if "path" not in plan["dataset"]:
            raise ValueError("collect requires source-bound preparation; import or prepare a new experiment")
        if plan['dataset']['adapter'] in {'subject_pairs', 'bootstrap_student_inputs', 'compare_student_inputs'}:
            reviews_path = directory / 'reviews.jsonl'
            if reviews_path.exists():
                protected[str(reviews_path)] = engine._sha256_file(reviews_path)
        result = report(directory)
        if any(c["status"] not in {"valid", "empty"} or not c.get("receipt") for c in result["cases"]):
            raise ValueError("collect requires complete valid saved answers")
        plan = {**plan, "experiment": str(directory)}
        bundles.append((plan, result))
        for source, expected in plan["sources"].items():
            if source in protected and protected[source] != expected:
                raise ValueError(f"conflicting source hashes: {source}")
            protected[source] = expected
        protected[str(directory / "experiment.json")] = engine._sha256_file(directory / "experiment.json")
        for name, expected in plan["files"].items():
            protected[str(directory / name)] = expected
        for case in result["cases"]:
            path = case["receipt"]["results_path"]
            if path not in protected:
                protected[path] = engine._sha256_file(Path(path))
        provenance.append(dict(experiment=str(directory), prompt_id=plan["prompt"]["id"],
                               settings=result["settings"], sources=plan["sources"], cases=[dict(id=c["id"],
                               receipt=c["receipt"], reused=c.get("reused", False)) for c in result["cases"]]))
    adapters = {p["dataset"]["adapter"] for p, _ in bundles}
    if adapters == {"subjects"}:
        files = inputs.hierarchy_inputs.collect_subjects(bundles)
    elif adapters in ({'bootstrap_student_inputs'}, {'compare_student_inputs'}):
        from . import bootstrap_student_inputs, compare_student_inputs
        collector = (bootstrap_student_inputs if adapters == {'bootstrap_student_inputs'}
                     else compare_student_inputs)
        collector_path = Path(collector.__file__).resolve()
        protected[str(collector_path)] = engine._sha256_file(collector_path)
        protected[str(Path(__file__).resolve())] = engine._sha256_file(Path(__file__))
        files = collector.collect(bundles)
    elif adapters == {'subject_pairs'}:
        decisions, prompts, seen = [], {}, set()
        for plan, result in bundles:
            prompt_hash = engine._sha256_bytes(plan['prompt']['text'].encode())
            prompts.setdefault(prompt_hash, dict(text=plan['prompt']['text'], prompt_ids=[]))
            if plan['prompt']['id'] not in prompts[prompt_hash]['prompt_ids']:
                prompts[prompt_hash]['prompt_ids'].append(plan['prompt']['id'])
            planned = {case['id']: case for case in plan['cases']}
            for case in result['cases']:
                key = (plan['experiment'], case['id'])
                if key in seen:
                    raise ValueError('duplicate collected subject-pair decision')
                seen.add(key)
                answer = json.loads(case['output'],
                                    object_pairs_hook=engine._position_decoder().unique_object)
                if (not isinstance(answer, dict) or set(answer) != {'relation', 'reason'}
                        or not isinstance(answer['reason'], str)
                        or not isinstance(answer['relation'], str)
                        or answer['relation'] not in {'equivalent', 'a_parent_of_b',
                                                     'b_parent_of_a', 'neither', 'uncertain'}):
                    raise ValueError('unsupported subject-pair relation/reason answer')
                decisions.append(dict(experiment=plan['experiment'], case_id=case['id'],
                    prompt_id=plan['prompt']['id'], prompt_sha256=prompt_hash,
                    input_sha256=planned[case['id']]['input_sha256'], inputs=case['inputs'],
                    answer=answer, evidence=case['evidence'], reviews=case['reviews'],
                    receipt=case['receipt']))
        if not decisions:
            raise ValueError('subject-pair collection requires saved decisions')
        protected[str(Path(__file__).resolve())] = engine._sha256_file(Path(__file__))
        files = {'relationships.json': dict(schema_version=1, prompts=prompts, cases=decisions,
            semantic_status='Provisional saved model decisions; reviews do not automatically '
                            'approve training targets or establish semantic gold.')}
    elif adapters <= {"masks", "grouped_masks"}:
        files = inputs.hierarchy_inputs.collect_masks(bundles)
    elif adapters == {"node_descriptions"}:
        nodes = {}
        for _, result in bundles:
            for case in result["cases"]:
                evidence = case["evidence"]
                value = inputs.validate_node_description(case["parsed"],
                    evidence["node_id"], evidence["node_title"])
                if value["node_id"] in nodes:
                    raise ValueError(f'duplicate collected node description: {value["node_id"]}')
                nodes[value["node_id"]] = value
        files = {"node-descriptions.json": dict(schema_version=1, nodes=list(nodes.values()))}
    elif adapters == {"node_sorting"}:
        nodes, judgments = {}, {}
        for _, result in bundles:
            for case in result['cases']:
                evidence = case['evidence']
                nid, note_id = evidence['node_id'], evidence['note_id']
                value = inputs.validate_node_sorting(case['parsed'])
                node = nodes.setdefault(nid, dict(node_id=nid, node_title=evidence['node_title'], posts=[]))
                if node['node_title'] != evidence['node_title']:
                    raise ValueError(f'conflicting sorting node title: {nid}')
                key = (nid, note_id)
                if key in judgments:
                    prior, post = judgments[key]
                    if prior['inputs'] != case['inputs'] or prior['parsed'] != value:
                        raise ValueError(f'conflicting node/post sorting judgment: {nid}/{note_id}')
                    if case['id'] not in post['case_ids']:
                        post['case_ids'].append(case['id'])
                else:
                    post = dict(note_id=note_id, **value, case_ids=[case['id']])
                    judgments[key] = (case, post)
                    node['posts'].append(post)
        for node in nodes.values():
            node['posts'].sort(key=lambda p: (-p['sorting_score'], p['note_id']))
            node['order'] = [post['note_id'] for post in node['posts']]
        files = {'node-sorting.json': dict(schema_version=1,
                  nodes=[nodes[nid] for nid in sorted(nodes)])}
    else:
        raise ValueError("collect supports subjects, subject_pairs, bootstrap_student_inputs, compare_student_inputs, masks, grouped_masks, node_descriptions and node_sorting experiments")
    if worker_config is not None:
        if not adapters <= {"masks", "grouped_masks"}:
            raise ValueError("--worker-config requires mask experiments")
        worker_config = worker_config.expanduser().resolve()
        protected[str(worker_config)] = engine._sha256_file(worker_config)
        settings = read(worker_config)
    for path, expected in protected.items():
        if engine._sha256_file(Path(path)) != expected:
            raise ValueError(f"protected source changed: {path}")
    files["provenance.json"] = dict(schema_version=1, sources=protected, experiments=provenance,
                                    inference_calls=0)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".experiment-collect-", dir=output.parent) as temporary:
        staged = Path(temporary)
        for name, value in files.items():
            write(staged / name, value)
        if "worker-request.json" in files:
            request = files["worker-request.json"]
            request["proposal_sha256"] = engine._sha256_file(staged / "masked-posts.json")
            write(staged / "worker-request.json", request)
            try:
                from .worker import _load_request, WorkerConfig
            except ImportError:
                from worker import _load_request, WorkerConfig
            _load_request(staged / "worker-request.json")
            if worker_config is not None:
                files["worker-config.json"] = {**settings,
                    "request_path": str(output / "worker-request.json"),
                    "request_sha256": engine._sha256_file(staged / "worker-request.json"),
                    "output_path": str(output / "worker-result")}
                write(staged / "worker-config.json", files["worker-config.json"])
                WorkerConfig.load(staged / "worker-config.json")
        (staged / ".gitignore").write_text("*\n")
        for path, expected in protected.items():
            if engine._sha256_file(Path(path)) != expected:
                raise ValueError(f"protected source changed: {path}")
        output.mkdir()
        for child in staged.iterdir():
            child.rename(output / child.name)
    return dict(output=str(output), files=sorted(files), inference_calls=0)


def _import_reviews(directories, result):
    """Transfer current attributed judgments only between exact saved answers."""
    def identity(case):
        return case.get("evidence", {}).get("check"), case["prompt"], case["input_sha256"], case["output"]

    def recorded_identity(row):
        source = row.get("source")
        if not isinstance(source, dict):
            return None
        return (row["case_id"], row["role"], row["verdict"], row["comment"],
                row["input_sha256"], row["output_sha256"], source.get("experiment"),
                source.get("case_id"), source.get("review_sha256"))

    targets = {}
    seen = set()
    for case in result["cases"]:
        if case["status"] in {"valid", "empty"} and isinstance(case["output"], str):
            targets.setdefault(identity(case), []).append(case)
        seen.update(recorded_identity(row) for row in case["reviews"])
    rows, protected = [], {}
    now = datetime.now(timezone.utc).isoformat()
    for directory in dict.fromkeys(Path(item).expanduser().resolve() for item in directories):
        if str(directory) == result["experiment"]:
            raise ValueError("cannot import reviews from the destination experiment")
        plan, _, _ = load(directory)
        references = {**plan["sources"], **{str(directory / name): checksum
                      for name, checksum in plan["files"].items()}}
        for path in (directory / "experiment.json", directory / "run/manifest.json",
                     directory / "reviews.jsonl", directory / "run/results.jsonl"):
            if path.exists():
                references[str(path)] = engine._sha256_file(path)
        for path, expected in references.items():
            if path in protected and protected[path] != expected:
                raise ValueError("conflicting review source hashes: " + path)
            if engine._sha256_file(Path(path)) != expected:
                raise ValueError("review source changed: " + path)
            protected[path] = expected
        source_report = report(directory, include_request_preview=False)
        if source_report["adapter"] != result["adapter"]:
            continue
        assessments = set()
        for case in source_report["cases"]:
            if case["status"] not in {"valid", "empty"} or not isinstance(case["output"], str):
                continue
            for judgment in case["reviews"]:
                if judgment.get("current") is not True or judgment.get("verdict") == "comment":
                    continue
                if (judgment.get("role") not in {"agent", "user"}
                        or judgment.get("verdict") not in {"accept", "reject", "uncertain"}
                        or not isinstance(judgment.get("comment"), str) or not judgment["comment"].strip()):
                    raise ValueError("invalid attributed source review")
                assessment = identity(case) + (judgment["role"], judgment["verdict"], judgment["comment"])
                if assessment in assessments:
                    continue
                assessments.add(assessment)
                original = {key: value for key, value in judgment.items() if key != "current"}
                provenance = dict(experiment=str(directory),
                    experiment_sha256=references[str(directory / "experiment.json")],
                    reviews_sha256=references.get(str(directory / "reviews.jsonl")),
                    case_id=case["id"], review_sha256=inputs.digest(original),
                    time=judgment.get("time"), receipt=case.get("receipt"))
                for target in targets.get(identity(case), []):
                    row = dict(case_id=target["id"], role=judgment["role"], verdict=judgment["verdict"],
                        comment=judgment["comment"], time=now, input_sha256=target["input_sha256"],
                        output_sha256=inputs.digest(target["output"]), source=provenance)
                    key = recorded_identity(row)
                    if key not in seen:
                        rows.append(row)
                        seen.add(key)
    for path, expected in protected.items():
        if engine._sha256_file(Path(path)) != expected:
            raise ValueError("review source changed: " + path)
    return rows


def review(args):
    directory = args.experiment.resolve()
    if args.cosine_comparison and not args.ui:
        raise ValueError("--cosine-comparison requires --ui")
    if args.flagged_only and not args.ui:
        raise ValueError("--flagged-only requires --ui")
    if args.case and args.only:
        raise ValueError("--case and --only cannot be combined")
    if args.from_experiment and (args.ui or any((args.case, args.only, args.role, args.verdict, args.comment))):
        raise ValueError("--from-experiment cannot be combined with UI or a new judgment")
    if (args.view or args.node or args.ordering or args.check) and not args.ui:
        raise ValueError("--view/--node/--ordering/--check require --ui")
    if args.ordering and not args.cosine_comparison:
        raise ValueError("--ordering requires --cosine-comparison")
    with locked(directory):
        result = report(directory, include_request_preview=args.ui)
        if args.ui:
            if any((args.case, args.role, args.verdict, args.comment)):
                raise ValueError("--ui cannot record a CLI judgment")
            plan, _, _ = load(directory)
            prominence_view = args.view == "prominence" or plan["dataset"]["adapter"] == "prominence"
            if (args.node or args.check) and not prominence_view:
                raise ValueError("--node/--check require the prominence view")
            if args.node:
                available = {c.get("evidence", {}).get("node_id") for c in result["cases"]}
                unknown = set(args.node) - available
                if unknown:
                    raise ValueError(f"unknown --node IDs: {', '.join(sorted(unknown))}")
                result = {**result, "cases": [c for c in result["cases"]
                          if c.get("evidence", {}).get("node_id") in args.node]}
            selected = None
            if args.flagged_only or args.only:
                if not prominence_view and plan["dataset"]["adapter"] not in {"titles", "masks"}:
                    raise ValueError("--flagged-only/--only support titles, masks and prominence")
                requested = set(args.only or [])
                unknown = requested - {c["id"] for c in result["cases"]}
                if unknown:
                    raise ValueError(f"unknown --only case IDs: {', '.join(sorted(unknown))}")
                selected = [
                    c["id"] for c in result["cases"]
                    if (not requested or c["id"] in requested)
                    and (not args.flagged_only or inputs.is_flagged(c))
                ]
                if not selected:
                    print("No flagged cases. No model calls or review decisions changed.")
                    return
                if prominence_view or plan["dataset"]["adapter"] == "titles":
                    result = {**result, "cases": [c for c in result["cases"] if c["id"] in selected]}
            batch, excluded = inputs.review_batch(plan, result, view=args.view)
            if args.cosine_comparison:
                if not prominence_view:
                    raise ValueError("--cosine-comparison requires prominence cases")
                try:
                    from .prominence_ranking import add_rankings
                except ImportError:
                    from prominence_ranking import add_rankings
                batch = add_rankings(batch, result, read(args.cosine_comparison))
                if args.ordering:
                    if args.ordering not in {order["name"] for order in batch["orderings"]}:
                        raise ValueError(f"unknown ordering: {args.ordering}")
                    batch["orderings"].sort(key=lambda order: order["name"] != args.ordering)
            if prominence_view:
                # Comments are separate from approval sessions and model outputs.
                batch_path = directory / ("ui-" + inputs.digest(batch)[:16] + ".json")
                write(batch_path, batch)
                binary = (
                    args.ui_binary
                    or Path(__file__).resolve().parents[1]
                    / "target/release/model-output-review"
                )
                print(
                    f"UI: {len(batch['notes'])} mask entries; c: comment. No model calls or implied decisions."
                )
                viewer_options = (["--check"] if args.check else
                                  ["--comments", str(directory / "ui-comments.json")])
                completed = subprocess.run(
                    [str(binary), str(batch_path), *viewer_options],
                    check=False,
                )
                if completed.returncode:
                    raise ValueError(f"review UI exited with {completed.returncode}")
                write(directory / "report.json", report(directory))
                return
            print(
                f"UI: {len(selected) if selected is not None else len(batch['items'])} cases; "
                f"{len(excluded)} not supported by this UI (still in show/report.json)."
            )
            for item in excluded:
                print(f"  {item['id']}: {item['reason']}")
            if not batch["items"]:
                raise ValueError(
                    "no compatible UI cases; use show --case and review --case"
                )
            # A content-addressed session cannot misapply old decisions to changed outputs.
            name = "ui-" + inputs.digest(batch)[:16]
            batch_path = directory / (name + ".json")
            write(batch_path, batch)
            ui_path = directory / "review-ui.json"
            bindings = read(ui_path) if ui_path.exists() else []
            session_name = name + "-session.json"
            if not any(b["session_path"] == session_name for b in bindings):
                included = {item["item_id"] for item in batch["items"]}
                bindings.append(
                    {
                        "batch_path": batch_path.name,
                        "batch_sha256": inputs.digest(batch),
                        "session_path": session_name,
                        "cases": {
                            c["id"]: {
                                "input_sha256": c["input_sha256"],
                                "output_sha256": inputs.digest(c["output"]),
                            }
                            for c in result["cases"]
                            if c["id"] in included
                        },
                    }
                )
                write(ui_path, bindings)
            binary = (
                args.ui_binary
                or Path(__file__).resolve().parents[1]
                / "target/release/sse-mask-review"
            )
            command = (
                "review-titles"
                if plan["dataset"]["adapter"] == "titles"
                else "review-masks"
            )
            completed = subprocess.run(
                [
                    str(binary),
                    command,
                    str(batch_path),
                    str(directory / (name + "-session.json")),
                    *(["--only", ",".join(selected)]
                      if selected is not None and plan["dataset"]["adapter"] == "masks" else []),
                ],
                check=False,
            )
            if completed.returncode:
                raise ValueError(f"review UI exited with {completed.returncode}")
            write(directory / "report.json", report(directory))
            return
        if args.from_experiment:
            rows = _import_reviews(args.from_experiment, result)
        elif not all((args.case or args.only, args.role, args.verdict, args.comment)):
            raise ValueError(
                "recording review requires --case or --only, --role agent|user, --verdict and --comment"
            )
        else:
            selected = args.only or [args.case]
            cases = {case["id"]: case for case in result["cases"]}
            if len(selected) != len(set(selected)) or set(selected) - cases.keys():
                raise ValueError("unknown or duplicate review case IDs")
            rows = [dict(case_id=identifier, role=args.role, verdict=args.verdict,
                comment=args.comment, time=datetime.now(timezone.utc).isoformat(),
                input_sha256=cases[identifier]["input_sha256"],
                output_sha256=inputs.digest(cases[identifier]["output"])) for identifier in selected]
        for row in rows:
            engine._append_json_line(directory / "reviews.jsonl", row)
        write(directory / "report.json", report(directory, include_request_preview=False))
        print(f"Recorded {len(rows)} attributed reviews. Model calls made: 0")


def unreviewed_evaluation(directory, premise_audits=None):
    """Find required exact output versions needing assessment before freezing."""
    from . import distillation_coverage_search as coverage
    from . import distillation_review as review
    directory = Path(directory).expanduser().resolve()
    path = directory / "evaluation.json"
    result, assessments, protected = coverage._snapshot(
        dict(path=str(path), sha256=engine._sha256_file(path)), directory)
    references = [dict(path=str(Path(item).expanduser().resolve()),
        sha256=engine._sha256_file(Path(item).expanduser().resolve())) for item in premise_audits or []]
    audits = coverage._premise_audits(references, directory, protected)
    required = set()
    for cohort in ("random", "challenge"):
        for answer in result[cohort]["answers"]:
            if answer["errors"]:
                continue
            checks = answer["checks"]
            required.update((check, row["id"]) for check in ("matching", "support") for row in checks[check])
            supported = {row["evidence"]["student_number"] for row in checks["support"]
                         if row["status"] == "valid" and row["parsed"]["valid"] is True}
            required.update(("relationship", row["id"]) for row in checks["relationship"]
                if row["evidence"]["role"] == "actual_relationship"
                and row["evidence"]["student_number"] in supported)
            teacher = review._TeacherIndex(answer["teacher"])
            groups = assessments["contexts"].get(answer["id"])
            if groups is None:
                raise ValueError("unreviewed preflight requires frozen teacher meanings")
            for group in groups:
                if not group["required"]:
                    continue
                identifiers = {teacher.by_number[number] for number in group["teacher_numbers"]}
                matches = {row["evidence"]["student_number"] for row in checks["matching"]
                           if row["status"] == "valid" and row["parsed"]["teacher_id"] in identifiers}
                required.update(("relationship", row["id"]) for row in checks["relationship"]
                    if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]
                    and row["evidence"]["heading_number"] in matches)
    versions, pending = {}, []
    for native in result["experiments"]:
        for row in native["cases"]:
            if (row["evidence"]["check"], row["id"]) not in required or row.get("origin") == "mechanical":
                continue
            if row["status"] != "valid":
                pending.append(dict(experiment=native["experiment"], case_id=row["id"],
                                    check=row["evidence"]["check"], status=row["status"]))
                continue
            check = row["evidence"]["check"]
            key = (check, row["prompt"], json.dumps(row["inputs"], sort_keys=True, ensure_ascii=False), row["output"])
            group = versions.setdefault(key, dict(check=check, origin=row.get("origin", "semantic"),
                input_sha256=row["input_sha256"], inputs=row["inputs"], prompt=row["prompt"],
                output=row["output"], parsed=row["parsed"], aliases=[], assessments=[]))
            bound = coverage._bound_premise_audits(row, audits)[1]
            current = [item for item in row["reviews"] if item.get("current") is True
                and item.get("role") in {"agent", "user"} and item.get("verdict") in {"accept", "reject", "uncertain"}
                and isinstance(item.get("comment"), str) and item["comment"].strip()]
            group["aliases"].append(dict(experiment=native["experiment"], case_id=row["id"],
                evidence=row["evidence"], reviewed=bool(current or bound), receipt=row.get("receipt")))
            group["assessments"].extend(dict(experiment=native["experiment"], case_id=row["id"], review=item)
                                        for item in current)
            group["assessments"].extend(dict(premise_audit=item) for item in bound)
    # An exact assessment on an unused alias still proves this complete version;
    # it does not make the unused comparison part of the required workload.
    for native in result["experiments"]:
        for row in native["cases"]:
            if (row["evidence"]["check"], row["id"]) in required or row["status"] != "valid" or row.get("origin") == "mechanical":
                continue
            key = (row["evidence"]["check"], row["prompt"],
                   json.dumps(row["inputs"], sort_keys=True, ensure_ascii=False), row["output"])
            group = versions.get(key)
            if group is None:
                continue
            group["assessments"].extend(dict(experiment=native["experiment"], case_id=row["id"], review=item)
                for item in row["reviews"] if item.get("current") is True and item.get("role") in {"agent", "user"}
                and item.get("verdict") in {"accept", "reject", "uncertain"}
                and isinstance(item.get("comment"), str) and item["comment"].strip())
    unreviewed = [group for group in versions.values() if not group["assessments"]]
    reusable = [group for group in versions.values()
                if group["assessments"] and any(not alias["reviewed"] for alias in group["aliases"])]
    for filename, checksum in protected.items():
        if engine._sha256_file(Path(filename)) != checksum:
            raise ValueError("preflight source changed: " + filename)
    return dict(schema_version=1, output=str(directory), inference_calls=0, sources=protected,
        summary=dict(required_semantic_versions=len(versions), unreviewed_versions=len(unreviewed),
            pending_required_outputs=len(pending),
            unreviewed_aliases=sum(len(group["aliases"]) for group in unreviewed),
            reusable_review_versions=len(reusable),
            aliases_needing_reusable_reviews=sum(not alias["reviewed"] for group in reusable for alias in group["aliases"])),
        unreviewed=unreviewed, reusable_reviews=reusable, pending=pending,
        semantic_status="Accept, reject and uncertain are assessments; only accepted premises can settle coverage.")


def score_review(args):
    """Score an explicitly supplied report without creating a model receipt."""
    try:
        from . import distillation_review
    except ImportError:
        import distillation_review
    plan, _, _ = load(args.experiment)
    if plan["dataset"]["adapter"] != "distillation_review":
        raise ValueError("score-review requires a distillation_review experiment")
    case = next((case for case in plan["cases"] if case["id"] == args.case), None)
    if case is None:
        raise ValueError("unknown review case")
    raw = args.report.read_bytes()
    result = distillation_review.score_saved_output(case, case["evidence"]["student_output_raw"], raw.decode())
    return dict(schema_version=1, source_kind="supplied_report", inference_calls=0,
                experiment=str(args.experiment.resolve()), case_id=case["id"],
                input_sha256=case["input_sha256"], report_path=str(args.report.resolve()),
                report_sha256=engine._sha256_bytes(raw),
                scoring_code_sha256=engine._sha256_file(Path(distillation_review.__file__)), **result)


def add_commands(commands):
    commands.choices["review"].add_argument("--from-experiment", type=Path, action="append",
        help="import current attributed reviews of exact saved prompts, inputs and outputs; repeat for sources")
    for action in commands.choices["review"]._actions:
        if "--only" in action.option_strings:
            action.help = "review these cases with one explicit judgment, or select cases in the UI (repeatable)"
    p = commands.add_parser('catalogue-hierarchies', help='version saved hierarchies and collect recorded parameters; no inference')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--saved-only', action='store_true', help='rebuild the catalogue from retained records without discovering new outputs')
    p = commands.add_parser('prepare-hierarchy', help='prepare V3 Bootstrap and SSE pair consolidation; no inference')
    p.add_argument('directory', type=Path)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--history-root', type=Path)
    p = commands.add_parser('advance-hierarchy', help='collect V3 meanings and vectors and prepare the next consolidation; no inference')
    p.add_argument('directory', type=Path)
    p.add_argument('--comment', required=True)
    p = commands.add_parser('run-hierarchy', help='run V3 construction automatically until complete or blocked')
    p.add_argument('directory', type=Path)
    p.add_argument('--attempt-budget', type=Path,
                   help='optional explicitly supplied persistent attempt allowance')
    p.add_argument('--comment', default='Automated hierarchy generation V3')
    p.add_argument('--runner-upgrade-reason',
                   help='record an explicitly reviewed construction/adapter code fix; frozen data stays unchanged')
    p = commands.add_parser('summarize-experiments', help='summarize native saved usage across experiments; no inference')
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True, help='fresh summary report; never overwrite')
    p = commands.add_parser('prepare-distillation-review-trial', help='freeze a complete-answer validation trial; no inference')
    p.add_argument('manifest', type=Path)
    p.add_argument('--model-output', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--random-count', type=int, default=50)
    p.add_argument('--hard-count', type=int, default=10)
    p.add_argument('--seed', default='DS-final-20261009')
    p = commands.add_parser('show-distillation-review-trial', help='inspect frozen source evidence; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--answer')
    p.add_argument('--teacher-only', action='store_true')
    p = commands.add_parser('assess-distillation-review', help='record source-bound pre-call judgments; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--answer', required=True)
    p.add_argument('--directory', type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--teacher-meanings')
    group.add_argument('--expectations')
    group.add_argument('--wording-expectations', help='one judgment per identical input; expand every numbered occurrence')
    group.add_argument('--required-numbers', help='comma-separated teacher representatives; only exact repeats are grouped')
    p.add_argument('--optional-numbers', help='comma-separated explicitly optional teacher representatives')
    p.add_argument('--reason', required=True)
    p = commands.add_parser('freeze-distillation-review-assessments', help='seal complete pre-call judgments; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--directory', type=Path, required=True)
    p = commands.add_parser('prepare-distillation-review-inventory', help='freeze reusable teacher contexts without candidate labels; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--from-assessments', type=Path, action='append', default=[])
    p = commands.add_parser('prepare-distillation-review-evaluation', help='prepare the native complete-answer review workflow; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--assessments', type=Path)
    p.add_argument('--runner-binary', type=Path)
    p.add_argument('--history-root', type=Path)
    p.add_argument('--reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'))
    p.add_argument('--matching-reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'),
                   help='override reasoning effort for matching checks only')
    p.add_argument('--support-reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'),
                   help='override reasoning effort for support checks only')
    p.add_argument('--answer-id', action='append', help='prepare only this frozen answer ID; repeat for a subset')
    p.add_argument('--relationship-history-root', type=Path, help='override saved-request history for relationship checks only')
    p.add_argument('--relationship-runner-binary', type=Path, help='override the worker for relationship checks only')
    p.add_argument('--relationship-prompt', type=Path, help='bind this relationship prompt; requires --relationship-prompt-id')
    p.add_argument('--relationship-prompt-id', help='version ID for --relationship-prompt; other checks retain their defaults')
    p.add_argument('--actual-edges-only', action='store_true', help='prepare core checks; compatibility pairs are constructed only when reached')
    p = commands.add_parser('prepare-distillation-coverage-search', help='prepare coverage searches from completed native checks; no inference')
    p.add_argument('evaluation', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--answer-id', action='append', help='prepare only this frozen answer ID; repeat for a subset')
    p.add_argument('--runner-binary', type=Path)
    p.add_argument('--history-root', type=Path)
    p.add_argument('--reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'), default='xhigh')
    p.add_argument('--policy', choices=('audited', 'grading'), default='audited',
                   help='freeze whether grading requires independent complete-output audit acceptance')
    p.add_argument('--correction-experiment', type=Path, action='append',
                   help='native exact-input fallback decisions; repeat for multiple groups')
    p.add_argument('--correction-case', action='append',
                   help='use only these saved native correction case IDs; repeat for multiple cases')
    p.add_argument('--premise-audit', type=Path, action='append',
                   help='bind an existing complete-output audit JSONL for conditional reuse; repeat for multiple audits')
    p = commands.add_parser('collect-distillation-coverage-search', help='collect audited native coverage results; no inference')
    p.add_argument('coverage', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verification-experiment', type=Path, action='append',
                   help='native DSL witness or fallback experiment; repeat for multiple groups')
    p.add_argument('--correction-experiment', type=Path, action='append',
                   help='native exact-input fallback decisions; repeat for multiple groups')
    p.add_argument('--correction-case', action='append',
                   help='use only these saved native correction case IDs; repeat for multiple cases')
    p.add_argument('--premise-audit', type=Path, action='append',
                   help='existing exact complete-output audit JSONL; repeat for multiple audits')
    p.add_argument('--adjudication', type=Path, action='append',
                   help='immutable source-bound agent verdict; requires frozen grading policy')
    p.add_argument('--automatic', action='store_true', help='produce automatic grades with bounded final decisions')
    p.add_argument('--required-experiment', type=Path, action='append', help='native missing-check judgments')
    p.add_argument('--final-experiment', type=Path, action='append', help='fresh native final DSM or DCS decisions')
    p = commands.add_parser('prepare-distillation-automatic-grading', help='freeze automatic grading batches; no inference')
    p.add_argument('coverage', type=Path, nargs='?')
    p.add_argument('--evaluation', type=Path, help='start from an unrun sparse evaluation')
    p.add_argument('--coverage-reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'), default='high')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verification-experiment', type=Path, action='append')
    p.add_argument('--required-experiment', type=Path, action='append')
    p.add_argument('--final-experiment', type=Path, action='append')
    p.add_argument('--answer-id', action='append')
    p.add_argument('--runner-binary', type=Path)
    p.add_argument('--history-root', type=Path)
    p = commands.add_parser('run-distillation-automatic-grading', help='finish every selected answer without manual review')
    p.add_argument('directory', type=Path)
    p.add_argument('--runner-upgrade-reason', help='record an explicitly reviewed code update when resuming native groups')
    p = commands.add_parser('compare-distillation-grades', help='compare original automated saved grades with agent-audited grades; no inference')
    p.add_argument('coverage', type=Path)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--automated-report', type=Path, help='compare an existing native automatic final report')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verification-experiment', type=Path, action='append',
                   help='original fixed native DSL witness group; excludes audit-selected fallbacks')
    p = commands.add_parser('adjudicate-distillation-review', help='record an immutable source-bound agent decision; no inference')
    p.add_argument('experiment', type=Path)
    p.add_argument('--case', required=True)
    p.add_argument('--output', type=Path, required=True)
    decision = p.add_mutually_exclusive_group()
    decision.add_argument('--teacher-id', help='matching teacher ID or literal null')
    decision.add_argument('--valid', choices=('true', 'false'), help='support or relationship verdict')
    p.add_argument('--classification', choices=('correct', 'incorrect', 'uncertain'), required=True)
    p.add_argument('--rule', required=True, help='exact approved rule excerpt from the saved prompt')
    p.add_argument('--reason', required=True)
    p = commands.add_parser('show-distillation-review-evaluation', help='collect native trial results; no inference')
    p.add_argument('evaluation', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--unreviewed', action='store_true', help='show distinct required output versions still needing attributed assessment before freezing')
    p.add_argument('--premise-audit', type=Path, action='append', help='recognize existing exact complete-output assessments; requires --unreviewed')
    p = commands.add_parser('run-distillation-review-evaluation', help='run prepared native groups with a shared attempt limit')
    p.add_argument('evaluation', type=Path)
    p.add_argument('--max-new-attempts', type=int)
    p.add_argument('--attempt-budget', type=Path)
    p.add_argument('--runner-upgrade-reason')
    p.add_argument('--answer-id', action='append', help='run only this frozen answer ID; repeat for a nested subset')
    p = commands.add_parser('preview-distillation-review',
                            help='count complete saved validation review work; no inference')
    p.add_argument('manifest', type=Path)
    p.add_argument('--model-output', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--estimate', action='store_true', help='estimate rendered tokens and eligible repeated prefixes')
    p.add_argument('--timing-experiment', type=Path, action='append', default=[],
                   help='use verified fresh native calls with the same approved prompt/settings for runtime estimates')
    p = commands.add_parser('rank-distillation-generations',
                            help='rank frozen teacher generation sizes and select training extremes; no inference')
    p.add_argument('manifest', type=Path)
    p.add_argument('--top', type=int, default=5)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('score-review', help='validate and score a supplied semantic review report; no inference')
    p.add_argument('experiment', type=Path)
    p.add_argument('--case', required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p = commands.add_parser('count-post-tokens', help='save complete original-post SSE token counts; no inference')
    p.add_argument('source', type=Path)
    p.add_argument('--tokenizer', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('review-post-sample', help='save source-bound agent English/form decisions; no inference')
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--accept', default='')
    p.add_argument('--reject', default='')
    p.add_argument('--forms', action='append', default=[], metavar='FORM:ORDINALS')
    p.add_argument('--reason', required=True)
    p = commands.add_parser('freeze-post-sample', help='freeze original posts and three author-separated splits; no inference')
    p.add_argument('destination', type=Path)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--preview', action='store_true', help='save pending English reviews without freezing a sample')
    p = commands.add_parser('prepare-bounded-hierarchy',
                            help='freeze a bounded multi-pass hierarchy build; no inference')
    p.add_argument('destination', type=Path)
    p.add_argument('--spec', type=Path, required=True)
    p = commands.add_parser('measure-root-candidates',
                            help='size root-candidate supplements on a saved build; no inference')
    p.add_argument('build', type=Path)
    p.add_argument('destination', type=Path)
    p.add_argument('--pair', action='append', default=[], metavar='NODE_ID:NODE_ID',
                   help='track this diagnostic comparison in the prepared candidate lists')
    p = commands.add_parser('measure-parent-guides',
                            help='size one draft parent-guide pass; no inference or new vectors')
    p.add_argument('build', type=Path)
    p.add_argument('destination', type=Path)
    p.add_argument('--prompt', type=Path, required=True)
    p.add_argument('--prompt-id', required=True)
    p = commands.add_parser('prepare-parent-guide-vectors',
                            help='prepare source-bound standalone guide-name SSE requests; no inference')
    p.add_argument('source', type=Path)
    p.add_argument('destination', type=Path)
    p = commands.add_parser("collect", help="collect valid saved SP/MP answers into reusable inputs; no inference")
    p.add_argument("experiments", type=Path, nargs="+")
    p.add_argument("--output", type=Path, required=True, help="fresh output directory outside saved experiments")
    p.add_argument("--worker-config", type=Path, help="bind supplied SSE settings to collected masks; does not run SSE")
    p = commands.add_parser('export-hierarchy', help='export saved subject-pair ancestor answers to a separate test view; no inference')
    p.add_argument('experiment', type=Path)
    p.add_argument('--base', type=Path, help='existing validated export referenced by these additional comparisons')
    p.add_argument('--combine-equivalent', action='store_true',
                   help='HG6 only: combine saved equivalences in --base; preserve links and flag changed HG7 inputs, without inference')
    p.add_argument('--inherit-equivalent-judgments', action='store_true',
                   help='with --combine-equivalent, inherit consistent saved judgments through the merges; no new model receipts')
    p.add_argument('--source', type=Path, required=True, help='saved masked-posts.json and vector-map.json directory')
    p.add_argument('--output', type=Path, required=True, help='fresh directory outside saved sources')
    p = commands.add_parser('export-parent-guides',
                            help='apply saved parent-guide judgments to a separate bounded-build snapshot; no inference')
    p.add_argument('build', type=Path, help='saved bounded build with its frozen final hierarchy')
    p.add_argument('output', type=Path, help='fresh directory outside saved sources')
    p.add_argument('--comparisons', type=Path, nargs='+', required=True,
                   help='complete source-bound BCPv5 experiments; include earlier supplementary trials')
    p = commands.add_parser('compare-parent-policies',
                            help='compare fixed-membership saved-parent rules in two new views; no inference')
    p.add_argument('snapshot', type=Path, help='complete saved bounded hierarchy export')
    p.add_argument('output', type=Path, help='fresh directory outside saved sources')

    p = commands.add_parser('audit-canonical-trial', help='measure saved canonical note sets and browsing choices; no inference or graph changes')
    p.add_argument('directory', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-choices', type=int, default=6)
    p.add_argument('--work-budget', type=int, default=200000)
    p = commands.add_parser('measure-canonical-candidates', help='measure candidate selection against saved native comparisons; no inference or graph changes')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('evaluate-canonical-policy-trial', help='compare native frozen baseline and policy trials; no inference')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('export-canonical-viewer', help='export saved canonical nodes and original notes for review; no inference')
    p.add_argument('directory', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('shape-canonical-trial', help='select saved canonical nodes and witnessed containment edges; no inference')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--work-budget', type=int, default=200000)
    p.add_argument('--max-choices', type=int, default=6)
    p = commands.add_parser('measure-subject-vectors',
                            help='measure saved subject-vector loading and normalization; no inference')
    p.add_argument('--probe', type=Path, required=True)
    p.add_argument('--compact', action='store_true')
    p.add_argument('--output', type=Path, required=True)


def handle_command(args):
    if args.command == 'catalogue-hierarchies':
        from .hierarchy_catalogue import catalogue
        print(json.dumps(catalogue(args.source, args.registry, args.output, saved_only=args.saved_only), indent=2))
        return 0
    if args.command in ('prepare-hierarchy', 'advance-hierarchy', 'run-hierarchy'):
        from . import hierarchy_generation
        if args.command == 'prepare-hierarchy':
            result = hierarchy_generation.prepare(args.spec, args.directory, args.history_root)
        elif args.command == 'run-hierarchy':
            result = hierarchy_generation.run(args.directory, args.attempt_budget, args.comment,
                                             args.runner_upgrade_reason)
        else:
            result = hierarchy_generation.advance(args.directory, args.comment)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(args.command == 'run-hierarchy' and result['status'] != 'complete')
    if args.command == 'summarize-experiments':
        from .experiment_usage_summary import summarize_experiments, compact_summary
        output = args.output.expanduser().resolve()
        if output.exists():
            raise ValueError('experiment summary output already exists')
        result = summarize_experiments(args.spec, load_report=report)
        write(output, result)
        print(json.dumps(compact_summary(result, output), ensure_ascii=False, indent=2))
    elif args.command == 'prepare-distillation-review-trial':
        from . import distillation_review_trial
        result = distillation_review_trial.prepare_trial(args.manifest, args.model_output, args.output,
            random_count=args.random_count, hard_count=args.hard_count, seed=args.seed)
        print(json.dumps({key: result[key] for key in ('selection_path', 'inference_calls', 'selection_policy')}, indent=2))
    elif args.command in {'show-distillation-review-trial', 'assess-distillation-review', 'freeze-distillation-review-assessments', 'prepare-distillation-review-inventory'}:
        from . import distillation_review_assessment as assessment
        if args.command == 'show-distillation-review-trial':
            result = assessment.inspect(args.selection, args.answer, teacher_only=args.teacher_only)
        elif args.command == 'prepare-distillation-review-inventory':
            result = assessment.prepare_inventory(args.selection, args.output,
                source_directories=args.from_assessments)
        elif args.command == 'assess-distillation-review':
            if args.wording_expectations is not None:
                if args.optional_numbers is not None:
                    raise ValueError('optional representatives require --required-numbers')
                result = assessment.record_wording_expectations(args.selection, args.answer, args.directory,
                    json.loads(args.wording_expectations), reason=args.reason)
            elif args.required_numbers is not None:
                if args.optional_numbers is None:
                    raise ValueError('explicit optional representatives required, including an empty string')
                result = assessment.record_exact_groups(args.selection, args.answer, args.directory,
                    [n for n in args.required_numbers.split(',') if n],
                    [n for n in args.optional_numbers.split(',') if n], reason=args.reason)
            else:
                if args.optional_numbers is not None:
                    raise ValueError('optional representatives require --required-numbers')
                result = assessment.record(args.selection, args.answer, args.directory,
                    teacher_meanings=json.loads(args.teacher_meanings) if args.teacher_meanings is not None else None,
                    expectations=json.loads(args.expectations) if args.expectations is not None else None, reason=args.reason)
        else:
            result = assessment.freeze(args.selection, args.directory)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'prepare-distillation-coverage-search':
        from . import distillation_coverage_search
        result = distillation_coverage_search.prepare(args.evaluation, args.output,
            answer_ids=args.answer_id, runner_binary=args.runner_binary, history_root=args.history_root,
            premise_audits=args.premise_audit, reasoning_effort=args.reasoning_effort,
            policy=args.policy, correction_experiments=args.correction_experiment,
            correction_case_ids=args.correction_case)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'collect-distillation-coverage-search':
        from . import distillation_coverage_search
        result = distillation_coverage_search.collect(args.coverage, args.output,
            verification_experiments=args.verification_experiment, premise_audits=args.premise_audit,
            correction_experiments=args.correction_experiment, correction_case_ids=args.correction_case,
            adjudications=args.adjudication, automatic=args.automatic,
            required_experiments=args.required_experiment, final_experiments=args.final_experiment)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command in {'prepare-distillation-automatic-grading', 'run-distillation-automatic-grading'}:
        from . import distillation_review_automatic
        if args.command == 'prepare-distillation-automatic-grading':
            result = distillation_review_automatic.prepare(args.coverage, args.output,
                verification_experiments=args.verification_experiment,
                required_experiments=args.required_experiment, final_experiments=args.final_experiment,
                answer_ids=args.answer_id, runner_binary=args.runner_binary, history_root=args.history_root,
                evaluation_path=args.evaluation, coverage_reasoning_effort=args.coverage_reasoning_effort)
        else:
            result = distillation_review_automatic.run(args.directory, runner_upgrade_reason=args.runner_upgrade_reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(result['status'] == 'failed')
    elif args.command == 'adjudicate-distillation-review':
        from . import distillation_review_adjudication
        decision = (dict(teacher_id=None if args.teacher_id == 'null' else args.teacher_id)
                    if args.teacher_id is not None else dict(valid=args.valid == 'true') if args.valid is not None else None)
        result = distillation_review_adjudication.record(args.experiment, args.case, args.output,
            decision=decision, classification=args.classification, rule=args.rule, reason=args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'compare-distillation-grades':
        from . import distillation_grade_comparison
        result = distillation_grade_comparison.compare(args.coverage, args.reference, args.output,
            verification_experiments=args.verification_experiment, automated_report=args.automated_report)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command in {'prepare-distillation-review-evaluation', 'show-distillation-review-evaluation', 'run-distillation-review-evaluation'}:
        from . import distillation_review_evaluation as evaluation
        if args.command == 'prepare-distillation-review-evaluation':
            result = evaluation.prepare(args.selection, args.output, runner_binary=args.runner_binary,
                history_root=args.history_root, assessment_directory=args.assessments,
                reasoning_effort=args.reasoning_effort, relationship_prompt=args.relationship_prompt,
                matching_reasoning_effort=args.matching_reasoning_effort,
                support_reasoning_effort=args.support_reasoning_effort,
                relationship_prompt_id=args.relationship_prompt_id,
                relationship_runner_binary=args.relationship_runner_binary, answer_ids=args.answer_id,
                relationship_history_root=args.relationship_history_root, actual_edges_only=args.actual_edges_only)
        elif args.command == 'run-distillation-review-evaluation':
            result = evaluation.run(args.evaluation, max_new_attempts=args.max_new_attempts,
                attempt_budget_path=args.attempt_budget, runner_upgrade_reason=args.runner_upgrade_reason,
                answer_ids=args.answer_id)
        else:
            if args.premise_audit and not args.unreviewed:
                raise ValueError('--premise-audit requires --unreviewed')
            result = (unreviewed_evaluation(args.evaluation, args.premise_audit) if args.unreviewed
                      else evaluation.report(args.evaluation))
            if args.output:
                write(args.output, result)
            if args.unreviewed:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return
        compact = {key: result[key] for key in ('output', 'inference_calls', 'summary', 'usage') if key in result}
        if args.command == 'prepare-distillation-review-evaluation':
            compact['experiments'] = result['experiments']
        if args.command == 'show-distillation-review-evaluation' and args.output:
            compact['report'] = str(args.output)
        print(json.dumps(compact, ensure_ascii=False, indent=2))
    elif args.command == 'preview-distillation-review':
        from . import distillation_review_preview
        if args.output.exists():
            raise ValueError('review preview output already exists')
        result = distillation_review_preview.preview(args.manifest, args.model_output,
            estimate=args.estimate, timing_experiments=args.timing_experiment)
        write(args.output, result)
        summary = dict(output=str(args.output), inference_calls=result['inference_calls'], totals=result['totals'])
        if 'estimates' in result:
            summary['estimates'] = result['estimates']
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.command in {'count-post-tokens', 'review-post-sample', 'freeze-post-sample'}:
        try:
            from . import post_sampling
        except ImportError:
            import post_sampling
        if args.command == 'count-post-tokens':
            result = post_sampling.count_tokens(args.source, args.tokenizer, args.output)
        elif args.command == 'review-post-sample':
            result = post_sampling.review(args.source, args.output, args.accept, args.reject, args.forms, args.reason)
        else:
            result = post_sampling.freeze(args.spec, args.destination, args.preview)
        print(json.dumps(result, indent=2))
    elif args.command == 'rank-distillation-generations':
        try:
            from . import distillation_review
        except ImportError:
            import distillation_review
        if args.output.exists():
            raise ValueError('generation ranking output already exists')
        result = distillation_review.rank_generations(args.manifest, args.top)
        write(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'score-review':
        result = score_review(args)
        if args.output:
            if args.output.exists():
                raise ValueError('score-review output already exists')
            write(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'prepare-bounded-hierarchy':
        try:
            from .bounded_hierarchy_build import prepare_build
        except ImportError:
            from bounded_hierarchy_build import prepare_build
        print(json.dumps(prepare_build(args.spec, args.destination), indent=2))
    elif args.command == 'measure-root-candidates':
        try:
            from .root_candidate_measurement import measure_build
        except ImportError:
            from root_candidate_measurement import measure_build
        pairs = [tuple(pair.split(':')) for pair in args.pair]
        if any((len(pair) != 2 for pair in pairs)):
            raise ValueError('--pair requires NODE_ID:NODE_ID')
        result = measure_build(args.build, args.destination, diagnostic_pairs=pairs)
        fields = ('root_quota', 'minimum_existing_candidates', 'catalogue_mode', 'query_scope', 'status', 'reason', 'discovery_requests', 'maximum_verification_requests', 'maximum_first_attempt_requests', 'maximum_attempts_with_one_retry', 'maximum_rendered_input_tokens_first_attempt', 'within_remaining_budget_with_one_retry_each')
        print(json.dumps({**{k: result[k] for k in ('measurement_id', 'inference_attempts', 'node_count', 'root_search', 'baseline', 'total_seconds', 'process_peak_rss_kib')}, 'measurement_report': str(args.destination.resolve() / 'report.json'), 'profiles': [{k: p[k] for k in fields if k in p} for p in result['profiles']]}, indent=2))
    elif args.command == 'measure-parent-guides':
        try:
            from .parent_guide_measurement import measure_build
        except ImportError:
            from parent_guide_measurement import measure_build
        result = measure_build(args.build, args.destination, prompt=args.prompt, prompt_id=args.prompt_id)
        fields = ('measurement_id', 'inference_attempts', 'prompt_id', 'node_count', 'discovery_requests', 'rendered_input_tokens', 'maximum_parent_guides', 'maximum_unique_resolved_pairs', 'maximum_verification_requests', 'maximum_first_attempt_requests', 'maximum_attempts_with_one_retry', 'maximum_rendered_input_tokens_first_attempt', 'remaining_attempts', 'within_remaining_budget_with_one_retry_each', 'requires_new_versioned_pass_authorization')
        print(json.dumps({**{k: result[k] for k in fields}, 'model_settings': {k: result['source_runner'][k] for k in ('provider', 'model', 'reasoning_effort')}, 'guaranteed_comparisons_per_request': result['comparison_capacity']['guaranteed_pairs_per_request'], 'measurement_report': str(args.destination.resolve() / 'report.json')}, indent=2))
    elif args.command == 'prepare-parent-guide-vectors':
        try:
            from .parent_guide_vectors import prepare_vectors
        except ImportError:
            from parent_guide_vectors import prepare_vectors
        print(json.dumps(prepare_vectors(args.source, args.destination, report), indent=2))
    elif args.command == 'measure-canonical-candidates':
        try:
            from .canonical_candidate_measurement import measure
        except ImportError:
            from canonical_candidate_measurement import measure
        result = measure(args.source, args.output)
        print(json.dumps({'output': str(args.output.resolve()),
                          'inference_calls': result['inference_calls'],
                          'baseline': {'totals': result['baseline']['totals']},
                          'profiles': [{key: value for key, value in profile.items() if key != 'steps'}
                                       for profile in result['profiles']]},
                         ensure_ascii=False, indent=2))
    elif args.command == 'evaluate-canonical-policy-trial':
        from .canonical_policy_evaluation import evaluate_source
        result = evaluate_source(args.source, args.output)
        print(json.dumps({'output': str(args.output.resolve()), **{
            key: result[key] for key in ('inference_calls', 'schedule', 'reductions', 'quality', 'warnings')
        }}, ensure_ascii=False, indent=2))
    elif args.command == 'audit-canonical-trial':
        try:
            from .canonical_hierarchy_audit import audit_trial
        except ImportError:
            from canonical_hierarchy_audit import audit_trial
        result = audit_trial(args.directory, args.output, args.max_choices, args.work_budget)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    elif args.command == 'export-canonical-viewer':
        try:
            from .canonical_hierarchy_viewer import export_viewer
        except ImportError:
            from canonical_hierarchy_viewer import export_viewer
        print(json.dumps(export_viewer(args.directory, args.output), ensure_ascii=False, indent=2))
        return 0
    elif args.command == 'shape-canonical-trial':
        try:
            from .canonical_hierarchy_shape import shape_trial
        except ImportError:
            from canonical_hierarchy_shape import shape_trial
        result = shape_trial(args.source, args.output, args.work_budget, args.max_choices)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    elif args.command == 'measure-subject-vectors':
        try:
            from .subject_matching_probe import measure_subject_vector_loading
        except ImportError:
            from subject_matching_probe import measure_subject_vector_loading
        if args.output.exists():
            raise ValueError('measurement output already exists')
        result = measure_subject_vector_loading(args.probe, compact=args.compact)
        write(args.output, result)
        print(json.dumps(result, indent=2))

    elif args.command == 'collect':
        print(json.dumps(collect(args.experiments, args.output, args.worker_config), indent=2))
    elif args.command == 'export-parent-guides':
        try:
            from .parent_guide_export import export_parent_guides
        except ImportError:
            from parent_guide_export import export_parent_guides
        print(json.dumps(export_parent_guides(args.build, args.comparisons, args.output), ensure_ascii=False))
    elif args.command == 'compare-parent-policies':
        try:
            from .parent_guide_export import compare_parent_policies
        except ImportError:
            from parent_guide_export import compare_parent_policies
        print(json.dumps(compare_parent_policies(args.snapshot, args.output), ensure_ascii=False))
    elif args.command == 'export-hierarchy':
        try:
            from .subject_hierarchy import export_comparisons
        except ImportError:
            from subject_hierarchy import export_comparisons
        print(json.dumps(export_comparisons(args.experiment, args.source, args.output, args.base, args.combine_equivalent, args.inherit_equivalent_judgments), indent=2))
    else:
        return NotImplemented
    return 0

def prompt_sources(prompt):
    """Bind paired definition-writing prompts before native preparation."""
    import re
    from . import prompt_assembly
    path = Path(prompt['source_path']).resolve()
    match = re.fullmatch(r'Hierarchy-(bootstrap|consolidation|pair-consolidation)-v([0-9]+)', prompt['id'])
    minimum={'bootstrap':129,'consolidation':21,'pair-consolidation':2}
    managed = bool(match and int(match[2]) >= minimum[match[1]])
    spec_path = path.with_suffix('.assembly.json')
    if not spec_path.exists():
        if managed:
            raise ValueError('this prompt version requires a paired assembly')
        return {}
    spec, output, content = prompt_assembly.compile_spec(spec_path)
    if managed and (spec['prompt_id'] != prompt['id'] or output != path):
        raise ValueError('prompt version differs from its assembly')
    if managed and 'shared' not in spec:
        raise ValueError('this prompt version requires a paired assembly')
    if 'shared' not in spec:
        return {}
    prompt_assembly.assemble(spec_path, 'check')
    if content.decode('utf-8') != prompt['text'] or output != path:
        raise ValueError('prompt text differs from its paired assembly')
    peer_path, peer, peer_output, _ = prompt_assembly.paired_spec(spec_path, spec)
    if managed:
        other_family = 'consolidation' if match[1] == 'bootstrap' else 'bootstrap'
        if not re.fullmatch('Hierarchy-' + other_family + r'-v[0-9]+', peer['prompt_id']):
            raise ValueError('definition-writing companion has the wrong prompt family')
    paths = {spec_path, peer_path, output, peer_output}
    for location, manifest in ((spec_path, spec), (peer_path, peer)):
        paths.update(prompt_assembly.pinned_file(part, location.parent)
                     for part in manifest['parts'] if 'path' in part)
    return {str(source): engine._sha256_file(source) for source in sorted(paths)}


def code_files(dataset):
    directory = Path(__file__).parent
    names = ['experiment_inputs.py', 'experiment_extension.py', 'prompt_assembly.py', 'grouped_masks.py',
             'local_model.py', 'local_weight_model.py', 'distillation_run.py',
             'hierarchy_inputs.py', 'bounded_hierarchy_candidates.py',
             'bounded_hierarchy_workflow.py', 'bounded_hierarchy_graph.py', 'bounded_hierarchy_build.py']
    if dataset['adapter'] == 'subject_pairs':
        names += ['subject_pair_candidates.py']
    if dataset['adapter'] == 'bootstrap_student_inputs':
        names += ['bootstrap_student_inputs.py']
    if dataset['adapter'] == 'compare_student_inputs':
        names += ['bootstrap_student_inputs.py', 'compare_student_inputs.py']
    if dataset['adapter'] == 'hierarchy_node_pairs':
        names += ['hierarchy_node_pair_consistency.py']
    names += ['canonical_trial.py', 'canonical_receipts.py', 'hierarchy_node_pairs.py', 'canonical_graph_search.py', 'hierarchy_generation.py']
    names += ['corpus_inputs.py', 'canonical_candidate_selection.py', 'canonical_candidate_measurement.py', 'canonical_comparison_policy.py', 'canonical_selection_ranking.py', 'canonical_hierarchy_audit.py', 'canonical_hierarchy_shape.py', 'canonical_hierarchy_viewer.py', 'canonical_policy_evaluation.py', 'subject_matching_probe.py']
    if dataset['adapter'] in {'bounded_parent_guides', 'bounded_parent_comparisons'}:
        names += ['parent_guide_measurement.py', 'parent_guide_workflow.py', 'ancestor_cosine_probe.py']
    if dataset['adapter'] in {'distillation_review', 'distillation_matching', 'distillation_verdict', 'distillation_review_evaluation', 'distillation_coverage_search'}:
        names += ['distillation_review.py', 'distillation_run.py', 'distillation_review_automatic.py']
    if dataset['adapter'] == 'distillation_matching':
        names += ['distillation_matching.py']
    if dataset['adapter'] == 'distillation_verdict':
        names += ['distillation_verdict.py']
    if dataset['adapter'] in {'distillation_review_evaluation', 'distillation_coverage_search'}:
        names += ['distillation_review_evaluation.py', 'distillation_review_assessment.py',
                  'distillation_review_trial.py', 'distillation_review_preview.py',
                  'distillation_matching.py', 'distillation_verdict.py']
    if dataset['adapter'] == 'distillation_coverage_search':
        names += ['distillation_coverage_search.py', 'distillation_review_adjudication.py']
    return {name: directory / name for name in names if (directory / name).exists()}

def consolidation_shapes(plan, cases):
    """Check proposed grouping against saved note sets without changing a graph."""
    from graphlib import TopologicalSorter
    summaries, menus = [], {}
    for case in cases:
        summary = dict(case=case['id'], status=case['status'], applied=False)
        if case['status'] != 'valid' or case.get('parsed') is None:
            summaries.append(summary)
            continue
        if case.get('evidence', {}).get('synthetic'):
            summary['qualification'] = ('Synthetic meaning edits; saved-menu note sets do not '
                                        'establish shape quality for these altered topics.')
            summaries.append(summary)
            continue
        path = case.get('evidence', {}).get('menu')
        if path is None:
            summary['qualification'] = 'No saved menu supplied; note-set shape checks are unavailable.'
            summaries.append(summary)
            continue
        if path not in menus:
            if engine._sha256_file(Path(path)) != plan['sources'][path]:
                raise ValueError('consolidation menu changed during shape review')
            nodes = {node['id']: node for node in read(Path(path))['nodes']}
            notes = {key: {entry['note_id'] for entry in node['entries']}
                     for key, node in nodes.items()}
            order = list(TopologicalSorter({key: node['parents'] for key, node in nodes.items()}).static_order())
            for child in reversed(order):
                for parent in nodes[child]['parents']:
                    notes[parent].update(notes[child])
            menus[path] = notes
        notes = menus[path]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        children = case['parsed']['children']
        represented = set().union(*(notes[child] for child in children))
        equal = [child for child in children if notes[child] == represented]
        parent = payload['parent']
        equal_parent = parent is not None and represented == notes[parent['id']]
        before = len(payload['siblings'])
        after = before - len(children) + 1
        summary.update(title=case['parsed']['title'], choices_before=before, choices_after=after,
            new_parent_choices=len(children), proposed_note_count=len(represented),
            child_note_counts={child: len(notes[child]) for child in children},
            equal_note_set_children=equal, equal_note_set_parent=equal_parent,
            local_group_constraints_met=not equal and not equal_parent and after < before
                                        and after <= 6 and len(children) <= 6,
            qualification='Prospective local grouping only; not full traversal, semantic approval '
                          'or a generated hierarchy. Existing branches are unchanged.')
        summaries.append(summary)
    return summaries


def enrich_report(result, plan, cases):
    if result['adapter'] == 'canonical_consolidation':
        result['consolidation_shapes'] = consolidation_shapes(plan, cases)
    diagnostics = (relation_diagnostics(cases)
                   if result['adapter'] in {'generic', 'subject_pairs'}
                   and (plan.get('preparation') or {}).get('source_adapter') != 'hierarchy_node_pairs'
                   else None)
    if diagnostics is not None:
        result['relation_diagnostics'] = diagnostics
    if result['adapter'] == 'hierarchy_node_pairs':
        from . import hierarchy_node_pair_consistency
        result['node_pair_consistency'] = hierarchy_node_pair_consistency.summarize(cases)
    if result["adapter"] == "distillation_verdict":
        try:
            from . import distillation_verdict
        except ImportError:
            import distillation_verdict
        result["qualification"] = distillation_verdict.qualification(
            cases, plan["preparation"]["qualification_case_ids"])
    if result["adapter"] == "distillation_review":
        try:
            from . import distillation_review
        except ImportError:
            import distillation_review
        result["qualification"] = distillation_review.qualification(
            cases, plan["preparation"]["qualification_case_ids"])
    if result["adapter"] == "distillation_matching":
        try:
            from . import distillation_matching
        except ImportError:
            import distillation_matching
        result["qualification"] = distillation_matching.qualification(
            cases, plan["preparation"]["qualification_case_ids"])
        token_counts = [case["evidence"]["input_tokens"] for case in cases
                        if case.get("origin") != "mechanical"]
        result["prepared_inputs"] = dict(tokenizer="o200k_base", calls=len(token_counts),
            rendered_input_tokens=sum(token_counts),
            min_rendered_input_tokens=min(token_counts, default=0),
            max_rendered_input_tokens=max(token_counts, default=0),
            max_teacher_subjects=max((case["evidence"]["distinct_teacher_subjects"]
                                      for case in cases), default=0))
    return result
