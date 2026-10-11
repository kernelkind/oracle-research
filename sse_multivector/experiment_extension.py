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


def review(args):
    directory = args.experiment.resolve()
    if args.cosine_comparison and not args.ui:
        raise ValueError("--cosine-comparison requires --ui")
    if args.flagged_only and not args.ui:
        raise ValueError("--flagged-only requires --ui")
    if args.only and not args.ui:
        raise ValueError("--only requires --ui")
    if (args.view or args.node or args.ordering or args.check) and not args.ui:
        raise ValueError("--view/--node/--ordering/--check require --ui")
    if args.ordering and not args.cosine_comparison:
        raise ValueError("--ordering requires --cosine-comparison")
    with locked(directory):
        result = report(directory)
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
        if not all((args.case, args.role, args.verdict, args.comment)):
            raise ValueError(
                "recording review requires --case, --role agent|user, --verdict and --comment"
            )
        case = next((c for c in result["cases"] if c["id"] == args.case), None)
        if case is None:
            raise ValueError("unknown case")
        engine._append_json_line(
            directory / "reviews.jsonl",
            {
                "case_id": args.case,
                "role": args.role,
                "verdict": args.verdict,
                "comment": args.comment,
                "time": datetime.now(timezone.utc).isoformat(),
                "input_sha256": case["input_sha256"],
                "output_sha256": inputs.digest(case["output"]),
            },
        )
        write(directory / "report.json", report(directory))
        print(f"Recorded {args.role} review for {args.case}. Model calls made: 0")


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
    p = commands.add_parser('catalogue-hierarchies', help='version saved hierarchies and collect recorded parameters; no inference')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--saved-only', action='store_true', help='rebuild the catalogue from retained records without discovering new outputs')
    p = commands.add_parser('prepare-canonical-traversal', help='prepare the approved L1-first traversal policy; no inference')
    p.add_argument('directory', type=Path)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--history-root', type=Path)
    p = commands.add_parser('advance-canonical-traversal', help='collect native answers, apply guarded placements and prepare reached comparisons; no inference')
    p.add_argument('directory', type=Path)
    p.add_argument('--comment', required=True)
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
    p = commands.add_parser('prepare-distillation-review-evaluation', help='prepare the native complete-answer review workflow; no inference')
    p.add_argument('selection', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--assessments', type=Path)
    p.add_argument('--runner-binary', type=Path)
    p.add_argument('--history-root', type=Path)
    p.add_argument('--reasoning-effort', choices=('xhigh', 'high', 'medium', 'low'))
    p.add_argument('--answer-id', action='append', help='prepare only this frozen answer ID; repeat for a subset')
    p.add_argument('--relationship-history-root', type=Path, help='override saved-request history for relationship checks only')
    p.add_argument('--relationship-runner-binary', type=Path, help='override the worker for relationship checks only')
    p.add_argument('--relationship-prompt', type=Path, help='bind this relationship prompt; requires --relationship-prompt-id')
    p.add_argument('--relationship-prompt-id', help='version ID for --relationship-prompt; other checks retain their defaults')
    p = commands.add_parser('show-distillation-review-evaluation', help='collect native trial results; no inference')
    p.add_argument('evaluation', type=Path)
    p.add_argument('--output', type=Path)
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
    if args.command in ('prepare-canonical-traversal', 'advance-canonical-traversal'):
        from . import canonical_traversal
        result = (canonical_traversal.prepare(args.spec, args.directory, args.history_root)
                  if args.command == 'prepare-canonical-traversal' else
                  canonical_traversal.advance(args.directory, args.comment))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
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
    elif args.command in {'show-distillation-review-trial', 'assess-distillation-review', 'freeze-distillation-review-assessments'}:
        from . import distillation_review_assessment as assessment
        if args.command == 'show-distillation-review-trial':
            result = assessment.inspect(args.selection, args.answer, teacher_only=args.teacher_only)
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
    elif args.command in {'prepare-distillation-review-evaluation', 'show-distillation-review-evaluation', 'run-distillation-review-evaluation'}:
        from . import distillation_review_evaluation as evaluation
        if args.command == 'prepare-distillation-review-evaluation':
            result = evaluation.prepare(args.selection, args.output, runner_binary=args.runner_binary,
                history_root=args.history_root, assessment_directory=args.assessments,
                reasoning_effort=args.reasoning_effort, relationship_prompt=args.relationship_prompt,
                relationship_prompt_id=args.relationship_prompt_id,
                relationship_runner_binary=args.relationship_runner_binary, answer_ids=args.answer_id,
                relationship_history_root=args.relationship_history_root)
        elif args.command == 'run-distillation-review-evaluation':
            result = evaluation.run(args.evaluation, max_new_attempts=args.max_new_attempts,
                attempt_budget_path=args.attempt_budget, runner_upgrade_reason=args.runner_upgrade_reason,
                answer_ids=args.answer_id)
        else:
            result = evaluation.report(args.evaluation)
            if args.output:
                write(args.output, result)
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

def code_files(dataset):
    directory = Path(__file__).parent
    names = ['experiment_inputs.py', 'experiment_extension.py', 'grouped_masks.py',
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
    names += ['canonical_trial.py', 'canonical_receipts.py', 'hierarchy_node_pairs.py', 'canonical_graph_search.py', 'canonical_traversal.py']
    names += ['corpus_inputs.py', 'canonical_candidate_selection.py', 'canonical_candidate_measurement.py', 'canonical_comparison_policy.py', 'canonical_selection_ranking.py', 'canonical_hierarchy_audit.py', 'canonical_hierarchy_shape.py', 'canonical_hierarchy_viewer.py', 'canonical_policy_evaluation.py', 'subject_matching_probe.py']
    if dataset['adapter'] in {'bounded_parent_guides', 'bounded_parent_comparisons'}:
        names += ['parent_guide_measurement.py', 'parent_guide_workflow.py', 'ancestor_cosine_probe.py']
    if dataset['adapter'] in {'distillation_review', 'distillation_matching', 'distillation_verdict', 'distillation_review_evaluation'}:
        names += ['distillation_review.py', 'distillation_run.py']
    if dataset['adapter'] == 'distillation_matching':
        names += ['distillation_matching.py']
    if dataset['adapter'] == 'distillation_verdict':
        names += ['distillation_verdict.py']
    if dataset['adapter'] == 'distillation_review_evaluation':
        names += ['distillation_review_evaluation.py', 'distillation_review_assessment.py',
                  'distillation_review_trial.py', 'distillation_review_preview.py',
                  'distillation_matching.py', 'distillation_verdict.py']
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
