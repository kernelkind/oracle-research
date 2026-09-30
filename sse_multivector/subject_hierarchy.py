"""Lossless saved-SP hierarchy export for the existing DAG browser.

No inference or semantic repairs. The comparison export is a separate test of
saved ancestor answers, not a change to LG01 or a production conflict policy.
"""

import json
from pathlib import Path


def reachable(n, edges):
    outgoing = [set() for _ in range(n)]
    for a, b in edges:
        if not (0 <= a < n and 0 <= b < n):
            raise ValueError("edge outside graph")
        outgoing[a].add(b)
    result = set()
    for start in range(n):
        pending, visited = list(outgoing[start]), set()
        while pending:
            target = pending.pop()
            if target not in visited:
                visited.add(target)
                pending.extend(outgoing[target] - visited)
        result.update((start, target) for target in visited)
    return result


def browser_spec(inputs, result, masks, source_hash):
    """Preserve SP sources, exact masks and empty-mask posts in the DAG browser."""
    subjects, groups = inputs["subjects"], result["groups"]
    version = result["experiment_id"]
    ids = [f"S{g[0]:04d}" for g in groups]
    children = {i: [] for i in range(len(groups))}
    nonroots = set()
    for a, b in result.get("browsing_edges", result["edges"]):
        children[a].append(b)
        nonroots.add(b)
    names = [" / ".join(dict.fromkeys(subjects[m]["subject"] for m in g)) for g in groups]
    nodes, own_notes, own_masks = [], {}, {}
    for i, group in enumerate(groups):
        own_notes[i], own_masks[i], origins = set(), {}, []
        for m in group:
            s = subjects[m]
            own_notes[i].add(s["note_short_id"])
            mask_ids = []
            for v in s["mask_vector_ids"]:
                mask = masks[v]
                identity = mask["note_short_id"], tuple(map(tuple, mask["byte_spans"]))
                own_masks[i].setdefault(identity, set()).add(mask["short_id"])
                mask_ids.append(mask["short_id"])
            origins.append(f'{s["note_short_id"]} SP {s["number"]}: {s["subject"]} '
                           f'({", ".join(mask_ids) or "empty mask"})')
        analysis = result.get("analysis", f"{version} experimental subject matching; original SP links only. "
                              "No title generation or new placements.")
        nodes.append(dict(node_id=ids[i], label=names[i],
                          children=[ids[j] for j in sorted(children[i], key=lambda j: (names[j], ids[j]))],
                          note_ids=sorted(own_notes[i]),
                          analysis=analysis + "\nOriginal subjects:\n" + "\n".join(origins)))
    paths = reachable(len(groups), result["edges"])
    nodes.insert(0, dict(node_id="root", label="All subjects", note_ids=[],
                         children=[ids[i] for i in sorted(set(children) - nonroots,
                                                         key=lambda j: (names[j], ids[j]))],
                         analysis=f"{version} navigation root, not an inferred subject. All SP subjects retained; "
                         "no display collapsing. Empty masks show original posts without highlights."))
    note_masks, instances = {}, {}
    for node in nodes:
        key = node["node_id"]
        if key == "root":
            included = range(len(groups))
        else:
            i = ids.index(key)
            included = [i] + [b for a, b in sorted(paths) if a == i]
        notes, combined = set(), {}
        for i in included:
            notes.update(own_notes[i])
            for identity, aliases in own_masks[i].items():
                combined.setdefault(identity, set()).update(aliases)
        individual = {p: [] for p in sorted(notes)}
        for (p, spans), aliases in sorted(combined.items()):
            individual[p].append(dict(ids=sorted(aliases), byte_spans=[list(s) for s in spans]))
        instances[key] = individual
        note_masks[key] = {p: [list(s) for s in sorted({tuple(s) for m in items for s in m["byte_spans"]})]
                           for p, items in individual.items()}
    return dict(schema_version=2, hierarchy_id=f"{version} · saved SP hierarchies · experimental matching",
                source_sha256=source_hash, root_node_id="root", nodes=nodes,
                notes=[dict(note_id=p["note_id"], note_short_id=p["note_short_id"])
                       for p in inputs["posts"]], note_masks=note_masks, mask_instances=instances)


def _export_bundle(directory, source, base=None, ancestry=(), combine_equivalent=False):
    """Rebuild a complete export in memory; no inference or source writes."""
    try:
        from . import experiment as workflow
        from . import experiment_inputs as adapters
        from .extraction_pipeline import _sha256_file
    except ImportError:
        import experiment as workflow
        import experiment_inputs as adapters
        from extraction_pipeline import _sha256_file

    directory, source = (Path(p).resolve() for p in (directory, source))
    if directory in ancestry:
        raise ValueError("cyclic export provenance")
    ancestry = (*ancestry, directory)
    plan, _, _ = workflow.load(directory)
    prep = plan.get("preparation")
    if plan["dataset"]["adapter"] != "subject_pairs":
        raise ValueError("export requires a subject-pair experiment")
    if combine_equivalent and base is None:
        raise ValueError("--combine-equivalent requires --base")
    if base is None and not prep:
        raise ValueError("export requires a combined subject-pair experiment or --base")
    if base is not None and prep:
        raise ValueError("--base requires ordinary additional subject-pair comparisons")
    protected = dict(plan["sources"])

    def protect(path, expected=None):
        path = Path(path).resolve()
        actual = _sha256_file(path)
        if actual != protected.get(str(path), expected or actual) or (expected and actual != expected):
            raise ValueError(f"protected source changed: {path}")
        protected[str(path)] = actual
        return path

    for path, expected in list(protected.items()):
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected source changed: {path}")
    protect(directory / "experiment.json")
    for name in plan["files"]:
        protect(directory / name)

    if base is None:
        inputs, hierarchy, comparisons, prep = _initial_comparisons(
            directory, plan, protect, workflow, adapters)
    else:
        inputs, hierarchy, comparisons, prep = _continued_comparisons(
            Path(base).resolve(), directory, source, plan, protect, workflow, adapters, ancestry)
    if combine_equivalent:
        hierarchy, comparisons, prep = _combine_saved_equivalences(
            inputs, hierarchy, comparisons, prep, directory, plan, workflow, adapters)

    groups = hierarchy["groups"]
    by_id = {f"S{members[0]:04d}": g for g, members in enumerate(groups)}
    sp_edges = {tuple(e) for e in hierarchy.get("sp_edges", hierarchy["edges"])}
    starting_edges = {tuple(e) for e in hierarchy["edges"]}
    proposals, neither = [], []
    for c in comparisons:
        a, b = by_id[c["A"]], by_id[c["B"]]
        relation = c["answer"]["relation"]
        if relation == "equivalent":
            raise ValueError("new equivalent answer requires a separate HG6 decision")
        if relation in {"a_parent_of_b", "b_parent_of_a"}:
            edge = (a, b) if relation == "a_parent_of_b" else (b, a)
            proposals.append(dict(edge=list(edge), comparison_id=c["id"]))
        elif relation == "neither":
            neither.append((a, b))
        elif relation != "uncertain":
            raise ValueError("unsupported subject comparison answer")
    edges = sorted(starting_edges | {tuple(p["edge"]) for p in proposals})
    paths = reachable(len(groups), edges)
    if any(a == b for a, b in paths):
        raise ValueError("ancestor answers create a cycle; no conflict policy applied")
    if any((a, b) in paths or (b, a) in paths for a, b in neither):
        raise ValueError("neither answer conflicts with ancestry; no conflict policy applied")
    owners = hierarchy["member_to_group"]
    if any(owners[a] != owners[b] and (owners[a], owners[b]) not in paths for a, b in inputs["edges"]):
        raise ValueError("combined hierarchy loses SP ancestry")
    outgoing = {g: set() for g in range(len(groups))}
    for a, b in edges:
        outgoing[a].add(b)
    browsing = [(a, b) for a, b in edges if not any(c != b and (c, b) in paths for c in outgoing[a])]
    if reachable(len(groups), browsing) != paths:
        raise ValueError("browsing simplification loses ancestry")

    posts = workflow.read(protect(source / "masked-posts.json"))
    mappings = workflow.read(protect(source / "vector-map.json"))["vectors"]
    originals = {p["note_id"]: p["text"] for p in posts["notes"]}
    masks = {v["vector_id"]: v for v in mappings}
    if len(originals) != len(posts["notes"]) or len(masks) != len(mappings):
        raise ValueError("duplicate post or mask vector identity")
    if any(originals.get(p["note_id"]) != p["text"] for p in inputs["posts"]):
        raise ValueError("saved SP post differs from original source")
    selected_masks = {}
    for s in inputs["subjects"]:
        if not s["mask_vector_ids"] and (s["byte_spans"] or s["fragments"]):
            raise ValueError("nonempty subject mask has no vector")
        for vid in s["mask_vector_ids"]:
            m = masks[vid]
            if any(s[k] != m[k] for k in ("note_id", "note_short_id", "byte_spans", "fragments")):
                raise ValueError("mask provenance mismatch")
            raw = originals[s["note_id"]].encode()
            if [raw[a:b].decode() for a, b in m["byte_spans"]] != m["fragments"]:
                raise ValueError("mask differs from original post")
            selected_masks[vid] = m
    result = dict(hierarchy, experiment_id=plan["prompt"]["id"] + "-ancestor-test-v1",
                  sp_edges=[list(e) for e in sorted(sp_edges)], ancestor_proposals=proposals,
                  browsing_edges=[list(e) for e in browsing],
                  analysis="Isolated saved-answer test: preserved SP links plus current BCP ancestor answers. "
                  "Redundant browsing links omitted; no title generation, node removal or membership expansion.")
    result["edges"] = [list(e) for e in edges]
    if combine_equivalent:
        result["experiment_id"] = plan["prompt"]["id"] + "-hg6-test-v1"
        result["analysis"] = (
            "Isolated HG6 test: saved equivalences combined; existing relationships preserved. "
            "Changed-input comparisons remain pending HG7, not current judgments. "
            "No inference, new ancestor placement, title generation or membership expansion.")
    view = browser_spec(inputs, result, selected_masks, protected[str(source / "masked-posts.json")])
    view["hierarchy_id"] = plan["prompt"]["id"] + " · saved ancestor-application test"
    if combine_equivalent:
        view["hierarchy_id"] = plan["prompt"]["id"] + " · saved HG6 equivalence test"
    summary = dict(posts=len(inputs["posts"]), subjects=len(inputs["subjects"]), nodes=len(groups),
        roots=len(view["nodes"][0]["children"]), comparisons=len(comparisons),
        ancestor_answers=len(proposals), new_ancestor_links=len(set(edges) - starting_edges),
        sp_links=len(sp_edges), underlying_links=len(edges), browsing_links=len(browsing),
        browsing_links_omitted=len(edges) - len(browsing),
        uncertain_answers=sum(c["answer"]["relation"] == "uncertain" for c in comparisons),
        sp_order_preserved=True, browsing_ancestry_preserved=True, inference_calls=0)
    if "pending_comparisons" in prep:
        summary["pending_comparisons"] = len(prep["pending_comparisons"])
    if combine_equivalent:
        summary["nodes_combined"] = prep["summary"]["original_nodes"] - len(groups)
    provenance = dict(protected_sha256=protected, subjects=inputs["subjects"], original_edges=inputs["edges"],
        preparation=prep, comparisons=comparisons, masks=list(selected_masks.values()),
        export=dict(experiment=str(directory), source=str(source),
                    base=str(Path(base).resolve()) if base is not None else None),
        implementation_sha256={str(Path(p).resolve()): _sha256_file(Path(p))
                               for p in (__file__, workflow.__file__, adapters.__file__)})
    if combine_equivalent:
        provenance["export"]["combine_equivalent"] = True
    for path, expected in protected.items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected source changed during export: {path}")
    return dict(results=result, categories=view, provenance=provenance, summary=summary)


def _combine_saved_equivalences(inputs, hierarchy, comparisons, previous_prep,
                                directory, plan, workflow, adapters):
    """Apply HG6 only; remap retained judgments and expose changed HG7 inputs."""
    report = workflow.report(directory)
    if any(c["parsed"]["relation"] != "equivalent" for c in report["cases"]):
        raise ValueError("merge-only export requires only equivalent answers")
    references = report["cases"][0]["evidence"]["source"]
    source = dict(inputs=inputs, hierarchy=hierarchy, pairs=[], source=references)
    _, prep = adapters.combine_subject_pairs(source, [report], plan["prompt"]["text"])
    combined = prep["hierarchy"]
    mapping = prep["original_node_to_combined"]
    owners = combined["member_to_group"]
    remap = {g: owners[members[0]] for g, members in enumerate(hierarchy["groups"])}
    combined["sp_edges"] = [list(e) for e in sorted({
        (remap[a], remap[b]) for a, b in hierarchy["sp_edges"] if remap[a] != remap[b]})]
    previous = list(comparisons)
    for pending in previous_prep.get("pending_comparisons", []):
        prior_mapping = previous_prep["original_node_to_combined"]
        previous.extend(dict(c, A=prior_mapping.get(c["A"], c["A"]),
                             B=prior_mapping.get(c["B"], c["B"]))
                        for c in pending["previous_comparisons"])
    pairs, internal = {}, []
    for prior in previous:
        a, b = mapping[prior["A"]], mapping[prior["B"]]
        if a == b:
            if prior["answer"]["relation"] == "neither":
                raise ValueError("equivalence conflicts with saved neither answer; no repair applied")
            internal.append(prior)
        else:
            pairs.setdefault(tuple(sorted((a, b))), []).append(prior)
    current, pending = [], []
    combined_source = dict(source, hierarchy=combined)
    for (a, b), priors in sorted(pairs.items()):
        for prior in priors:
            pair = dict(id=prior["id"], A=mapping[prior["A"]], B=mapping[prior["B"]])
            case = adapters.prepare_subject_pairs(dict(combined_source, pairs=[pair]))[0]
            if case["inputs"] == prior["inputs"]:
                current.append(dict(prior, A=pair["A"], B=pair["B"]))
                break
        else:
            pair = dict(id=a + "-" + b, A=a, B=b)
            case = adapters.prepare_subject_pairs(dict(combined_source, pairs=[pair]))[0]
            pending.append(dict(case, previous_comparisons=priors))
    prep.update(previous_preparation=previous_prep, previous_comparisons=previous,
                remapped_internal_comparisons=internal, pending_comparisons=pending)
    return combined, current, prep


def _initial_comparisons(directory, plan, protect, workflow, adapters):
    """Rebuild the HG6 partition and validate unchanged HG5 and changed HG7 inputs."""
    prep = plan["preparation"]
    priors = (prep["equivalent_answers"] + prep["internal_comparisons"]
              + [p for c in prep["unchanged_comparisons"] for p in c["previous_comparisons"]]
              + [p for c in plan["cases"] for p in c["evidence"]["previous_comparisons"]])
    directories = {Path(p["experiment"]).resolve() for p in priors}
    report_paths = [Path(p).parent for p in plan["sources"]
                    if Path(p).name == "experiment.json" and Path(p).parent in directories]
    if set(report_paths) != directories:
        raise ValueError("comparison experiment is not bound to prepared sources")
    reports = [workflow.report(p) for p in report_paths]
    if not reports or not reports[0]["cases"]:
        raise ValueError("no saved source comparisons")
    references = reports[0]["cases"][0]["evidence"]["source"]
    references = dict(inputs=references["inputs"],
                      hierarchy=references.get("hierarchy", references.get("results")))
    # Older evidence used repo-relative paths. Resolve only to the exact source
    # already frozen by the combined preparation, never by an ID/name match.
    for key, ref in list(references.items()):
        path = Path(ref["path"])
        if not path.is_absolute():
            matches = [p for p, sha in plan["sources"].items()
                       if sha == ref["sha256"] and Path(p).parts[-len(path.parts):] == path.parts]
            if len(matches) != 1:
                raise ValueError("source reference does not uniquely match prepared provenance")
            references[key] = {**ref, "path": matches[0]}
    original = {key: workflow.read(protect(ref["path"], ref["sha256"])) for key, ref in references.items()}
    inputs = original["inputs"]
    selected, rebuilt = adapters.combine_subject_pairs(
        dict(**original, pairs=[], source=references), reports, plan["prompt"]["text"])
    if rebuilt != prep:
        raise ValueError("saved combined preparation differs from source comparisons")
    expected_cases = {c["id"]: c for c in selected["cases"]}
    current = workflow.report(directory)
    for report in [*reports, current]:
        protect(Path(report["experiment"]) / "experiment.json")
        for case in report["cases"]:
            if case["status"] != "valid" or not case.get("receipt"):
                raise ValueError(f"comparison is not valid: {case['id']}")
            protect(case["receipt"]["results_path"])
        for key in ("provider", "model", "reasoning_effort", "output_schema", "timeout_seconds", "max_output_tokens"):
            if report["settings"].get(key) != current["settings"].get(key):
                raise ValueError(f"comparison model settings differ: {key}")

    comparisons = []
    for c in prep["unchanged_comparisons"]:
        prior = c["source"]
        comparisons.append(dict(id=c["id"], A=c["A"], B=c["B"], answer=prior["answer"],
            inputs=prior["inputs"], receipt=prior["receipt"], experiment=prior["experiment"],
            prompt_id=prior["prompt_id"], settings=prior["settings"], stage="HG5"))
    if {c["id"] for c in current["cases"]} != set(expected_cases):
        raise ValueError("changed comparison inventory differs from preparation")
    for c in current["cases"]:
        expected = expected_cases[c["id"]]
        if (c["inputs"] != expected["inputs"] or c["evidence"] != expected["evidence"]
                or c["prompt"] != adapters.render(plan["prompt"]["text"], expected["inputs"])):
            raise ValueError("changed comparison inputs differ from combined nodes")
        comparisons.append(dict(id=c["id"], A=c["evidence"]["A"]["node_id"],
            B=c["evidence"]["B"]["node_id"], answer=c["parsed"], inputs=c["inputs"],
            receipt=c["receipt"], experiment=current["experiment"], prompt_id=current["prompt_id"],
            settings=current["settings"], stage="HG7"))

    return inputs, prep["hierarchy"], comparisons, prep


def _continued_comparisons(base, directory, source, plan, protect, workflow, adapters, ancestry):
    """Replay the base export, then validate additional inputs against that exact graph."""
    saved = {name: workflow.read(protect(base / f"{name}.json"))
             for name in ("results", "categories", "provenance", "summary")}
    previous = saved["provenance"]
    for path, expected in previous["protected_sha256"].items():
        protect(path, expected)
    origin = previous.get("export")
    if origin is None:
        # First-generation exports predate the explicit replay descriptor.
        candidates = []
        for path in previous["protected_sha256"]:
            if Path(path).name == "experiment.json":
                old = workflow.load(Path(path).parent)[0]
                if old.get("preparation") and old["preparation"] == previous["preparation"]:
                    candidates.append(Path(path).parent)
        if len(candidates) != 1:
            raise ValueError("base export has no unique combined source experiment")
        origin = dict(experiment=str(candidates[0]), source=str(source), base=None)
    required = {"experiment", "source", "base"}
    if (not isinstance(origin, dict) or set(origin) not in (required, required | {"combine_equivalent"})
            or ("combine_equivalent" in origin and origin["combine_equivalent"] is not True)):
        raise ValueError("invalid base export provenance")
    rebuilt = _export_bundle(origin["experiment"], origin["source"], origin["base"], ancestry,
                             origin.get("combine_equivalent", False))
    for name in ("results", "categories", "summary"):
        if saved[name] != rebuilt[name]:
            raise ValueError(f"base export {name} differs from saved comparisons")
    for name in ("protected_sha256", "subjects", "original_edges", "preparation", "comparisons", "masks"):
        if previous[name] != rebuilt["provenance"][name]:
            raise ValueError(f"base export provenance {name} differs from saved comparisons")
    if "export" in previous and previous["export"] != rebuilt["provenance"]["export"]:
        raise ValueError("base export replay descriptor changed")

    current = workflow.report(directory)
    if not current["cases"]:
        raise ValueError("no additional comparisons")
    references = current["cases"][0]["evidence"]["source"]
    if set(references) != {"inputs", "hierarchy"}:
        raise ValueError("additional comparison source must name inputs and hierarchy")
    for ref in references.values():
        path = str(Path(ref["path"]).resolve())
        if plan["sources"].get(path) != ref["sha256"]:
            raise ValueError("comparison source is not bound to prepared sources")
        protect(path, ref["sha256"])
    if Path(references["hierarchy"]["path"]).resolve() != base / "results.json":
        raise ValueError("comparison hierarchy does not match --base")
    input_ref = references["inputs"]
    if previous["protected_sha256"].get(str(Path(input_ref["path"]).resolve())) != input_ref["sha256"]:
        raise ValueError("comparison inputs do not match base export sources")
    inputs = workflow.read(input_ref["path"])
    if inputs["subjects"] != previous["subjects"] or inputs["edges"] != previous["original_edges"]:
        raise ValueError("comparison subjects or SP links differ from base export")
    old_plan = workflow.load(origin["experiment"])[0]
    if any(plan["prompt"][k] != old_plan["prompt"][k] for k in ("id", "text")):
        raise ValueError("additional comparison prompt differs from base export")
    for c in previous["comparisons"]:
        for key in ("provider", "model", "reasoning_effort", "output_schema", "timeout_seconds", "max_output_tokens"):
            if c["settings"].get(key) != current["settings"].get(key):
                raise ValueError(f"comparison model settings differ: {key}")

    pairs = [dict(id=c["id"], A=c["evidence"]["A"]["node_id"], B=c["evidence"]["B"]["node_id"])
             for c in plan["cases"]]
    rules = {c["evidence"].get("selection", {}).get("rule") for c in plan["cases"]}
    selection = dict(pairs=pairs)
    if rules != {None}:
        if len(rules) != 1 or None in rules:
            raise ValueError("mixed additional comparison selection rules")
        selection = dict(selection=rules.pop())
    expected = adapters.prepare(dict(adapter="subject_pairs", select=[p["id"] for p in pairs]),
        dict(inputs=inputs, hierarchy=saved["results"], **selection, source=references), plan["prompt"]["text"])
    by_id = {c["id"]: c for c in expected}
    if {c["id"] for c in current["cases"]} != set(by_id):
        raise ValueError("additional comparison inventory differs from preparation")
    comparisons = list(previous["comparisons"])
    used_ids = {c["id"] for c in comparisons}
    used_pairs = {frozenset((c["A"], c["B"])) for c in comparisons}
    for c in current["cases"]:
        if c["status"] != "valid" or not c.get("receipt"):
            raise ValueError(f"comparison is not valid: {c['id']}")
        protect(c["receipt"]["results_path"])
        if any(c[k] != by_id[c["id"]][k] for k in ("inputs", "evidence", "prompt")):
            raise ValueError("additional comparison inputs differ from base nodes")
        a, b = c["evidence"]["A"]["node_id"], c["evidence"]["B"]["node_id"]
        pair = frozenset((a, b))
        if c["id"] in used_ids or pair in used_pairs:
            raise ValueError("duplicate saved comparison; no replacement policy applied")
        used_ids.add(c["id"])
        used_pairs.add(pair)
        comparisons.append(dict(id=c["id"], A=a, B=b, answer=c["parsed"], inputs=c["inputs"],
            receipt=c["receipt"], experiment=current["experiment"], prompt_id=current["prompt_id"],
            settings=current["settings"], stage="HG5"))
    preparation = previous["preparation"]
    if "pending_comparisons" in preparation:
        completed = {frozenset((c["A"], c["B"])) for c in comparisons}
        preparation = dict(preparation, pending_comparisons=[
            c for c in preparation["pending_comparisons"]
            if frozenset((c["evidence"]["A"]["node_id"], c["evidence"]["B"]["node_id"])) not in completed])
    return inputs, saved["results"], comparisons, preparation


def export_comparisons(directory, source, output, base=None, combine_equivalent=False):
    """Apply receipt-validated ancestor answers to a fresh, separately authorized export."""
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"output exists: {output}")
    bundle = _export_bundle(directory, source, base, combine_equivalent=combine_equivalent)
    protected = bundle["provenance"]["protected_sha256"]
    forbidden = {Path(directory).resolve(), Path(source).resolve()}
    forbidden.update(Path(p).parent for p in protected if Path(p).name in {"experiment.json", "provenance.json"})
    if any(output.is_relative_to(path) for path in forbidden):
        raise ValueError("output must be separate from saved source directories")
    output.mkdir(parents=True, exist_ok=False)
    for name, value in bundle.items():
        with (output / f"{name}.json").open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    return bundle["summary"]
