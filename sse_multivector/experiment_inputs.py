"""Input preparation and mechanical validation for the shared experiment workflow.

Adapters return explicit template variables separately from review-only evidence.
Execution, history, baselines and human judgments do not belong here.
"""

import hashlib
import json
from graphlib import CycleError, TopologicalSorter
from itertools import combinations
from pathlib import Path
import re

try:
    from . import extraction_pipeline as engine
    from . import grouped_masks
    from . import hierarchy_inputs
    from . import corpus_inputs
    from .prepare_category_title_inputs import prepare as prepare_titles
except ImportError:
    import extraction_pipeline as engine
    import grouped_masks
    import hierarchy_inputs
    import corpus_inputs
    from prepare_category_title_inputs import prepare as prepare_titles


def digest(value):
    return hashlib.sha256(engine._canonical_json_bytes(value)).hexdigest()


def render(template, inputs):
    if not isinstance(inputs, dict) or not inputs:
        raise ValueError("case inputs must be a nonempty object of template variables")
    for key, value in inputs.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not isinstance(value, str):
            raise ValueError(
                "template variables must be UPPER_CASE names with string values"
            )
        if "{" + key + "}" not in template:
            raise ValueError(f"unused input variable: {key}")

    # Only named placeholders are interpreted; literal JSON braces remain intact.
    def substitute(match):
        key = match[1]
        if key not in inputs:
            raise ValueError(f"missing template variable: {key}")
        return inputs[key]

    return re.sub(r"\{([A-Z][A-Z0-9_]*)\}", substitute, template)


def prepare_file(dataset, path, template, load_report=None):
    """Load dataset references and hash the exact bytes used for preparation."""
    path = Path(path).resolve()
    sources = {}

    def read_bytes(source_path):
        raw = source_path.read_bytes()
        sources[str(source_path)] = hashlib.sha256(raw).hexdigest()
        return raw

    def read(source_path):
        return json.loads(read_bytes(source_path))

    source = read(path)
    preparation = None
    if dataset['adapter'] == 'canonical_consolidation':
        prepared = source if 'cases' in source else dict(
            cases=prepare_consolidations(source, path.parent, read))
        return prepare({**dataset, 'adapter': 'generic'}, prepared, template), sources, dict(
            application_allowed=False, purpose='Synthetic proposal only; normal traversal owns placement.')
    if dataset['adapter'] in {'canonical_consolidation_pairs', 'canonical_consolidation_review'}:
        pairwise = dataset['adapter'] == 'canonical_consolidation_pairs'
        cases = prepare_saved_consolidations(source, path.parent, read, load_report, sources,
                                             pairwise=pairwise)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, dict(
            application_allowed=False, purpose='Review saved proposals; full placement is separate.')
    if dataset['adapter'] == 'hierarchy_prominence':
        return prepare({**dataset, 'adapter': 'generic'}, source, template), sources, dict(
            application_allowed=False, purpose='Fixed-meaning prominence for local selection.')
    if dataset['adapter'] == 'canonical_shaping_nomination':
        cases = prepare_shaping_nominations(source, path.parent, sources)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, dict(
            application_allowed=False, purpose='Nomination only; normal traversal owns placement.')
    if dataset['adapter'] == 'compare_student_inputs':
        from . import compare_student_inputs
        cases, protected, preparation = compare_student_inputs.prepare(source, path.parent)
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] == 'bootstrap_student_inputs':
        from . import bootstrap_student_inputs
        cases, protected, preparation = bootstrap_student_inputs.prepare(source, path.parent)
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] in {'generic', 'hierarchy_node_pairs'} and 'prepared_experiment' in source:
        fixed_meanings = dataset['adapter'] == 'hierarchy_node_pairs'
        fields = {'prepared_experiment'} | ({'input_view'} if fixed_meanings else set())
        if fixed_meanings and 'input_order' in source:
            fields.add('input_order')
        engine._expect_fields(source, 'prepared input source', fields)
        if fixed_meanings and source['input_view'] not in ('fixed_meanings', 'symmetric_fixed_meanings'):
            raise ValueError('prepared node pairs input_view must be fixed_meanings or symmetric_fixed_meanings')
        if 'input_order' in source and (source['input_view'] != 'symmetric_fixed_meanings'
                                      or source['input_order'] is None):
            raise ValueError('input_order requires symmetric_fixed_meanings and an A/B order array')
        reference = source['prepared_experiment']
        engine._expect_fields(reference, 'prepared experiment reference', {'path', 'sha256'})
        directory = engine._resolve_path(reference['path'], 'prepared experiment', path.parent)
        envelope_path = directory / 'experiment.json'
        if engine._sha256_file(envelope_path) != reference['sha256']:
            raise ValueError('prepared experiment reference hash differs')
        from experiment_runner.experiment import load
        plan, _, _ = load(directory)
        if fixed_meanings and plan['dataset']['adapter'] != 'hierarchy_node_pairs':
            raise ValueError('fixed_meanings requires a hierarchy_node_pairs prepared experiment')
        if any('mechanical' in case for case in plan['cases']):
            raise ValueError('input-only reuse cannot inherit mechanical answers')
        cases = [{key: case[key] for key in ('id', 'inputs', 'evidence') if key in case}
                 for case in plan['cases']]
        protected = {**plan['sources'], **{
            str(directory / name): expected for name, expected in plan['files'].items()}}
        manifest = Path(plan['run_directory']) / 'manifest.json'
        protected[str(manifest)] = engine._sha256_file(manifest)
        for name, expected in protected.items():
            if engine._sha256_file(Path(name)) != expected:
                raise ValueError('prepared input source changed: ' + name)
            if name in sources and sources[name] != expected:
                raise ValueError('conflicting prepared input source hash: ' + name)
        sources.update(protected)
        sources[str(envelope_path)] = reference['sha256']
        preparation = dict(source_experiment=str(directory),
            source_experiment_sha256=reference['sha256'], source_adapter=plan['dataset']['adapter'],
            source_prompt_id=plan['prompt']['id'], application_allowed=False)
        if fixed_meanings:
            from . import hierarchy_node_pairs
            if source['input_view'] == 'symmetric_fixed_meanings':
                cases = [hierarchy_node_pairs.project_symmetric_fixed_meanings(
                    case, input_order=source.get('input_order')) for case in cases]
            else:
                cases = [hierarchy_node_pairs.project_fixed_meanings(case) for case in cases]
            preparation['input_view'] = source['input_view']
            if 'input_order' in source:
                preparation['input_order'] = source['input_order']
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    saved_counterexamples = dataset['adapter'] == 'generic' and 'saved_counterexamples' in source
    saved_comparisons = (dataset['adapter'] in {'generic', 'hierarchy_node_pairs'}
                         and 'saved_comparisons' in source)
    if saved_counterexamples or saved_comparisons or dataset['adapter'] in {
            'hierarchy_node_pairs', 'hierarchy_local_nodes', 'hierarchy_meaning_diagnostics'}:
        try:
            from . import hierarchy_node_pairs as node_pairs
        except ImportError:
            import hierarchy_node_pairs as node_pairs
        reports = {}

        def saved_report(directory):
            directory = Path(directory).resolve()
            if load_report is None:
                raise ValueError('local_meaning_from requires validated experiment reports')
            if directory not in reports:
                envelope = read(directory / 'experiment.json')
                plan = envelope['plan']
                protected = {**plan['sources'], **{
                    str(directory / name): expected for name, expected in plan['files'].items()}}
                for name in ('reviews.jsonl', 'execution-settings.jsonl'):
                    path = directory / name
                    if path.exists():
                        protected[str(path)] = engine._sha256_file(path)
                result = load_report(directory)
                manifest = Path(plan['run_directory']) / 'manifest.json'
                protected[str(manifest)] = engine._sha256_file(manifest)
                for case in result['cases']:
                    if case.get('receipt'):
                        receipt = Path(case['receipt']['results_path'])
                        protected[str(receipt)] = engine._sha256_file(receipt)
                for file, expected in protected.items():
                    if engine._sha256_file(Path(file)) != expected:
                        raise ValueError('saved meaning source changed: ' + file)
                    if file in sources and sources[file] != expected:
                        raise ValueError('conflicting saved meaning source hash: ' + file)
                    sources[file] = expected
                reports[directory] = result
            return reports[directory]

        if saved_comparisons:
            cases, preparation = node_pairs.create_saved_comparisons(
                source, base=path.parent, read=read, load_report=saved_report)
        elif saved_counterexamples:
            cases, preparation = node_pairs.create_counterexample_checks(
                source, base=path.parent, read=read, load_report=saved_report)
        elif dataset['adapter'] == 'hierarchy_meaning_diagnostics':
            cases, preparation = node_pairs.create_meaning_diagnostic_source(
                source, base=path.parent, read=read, load_report=saved_report)
        else:
            cases, preparation = node_pairs.create_source(
                source, base=path.parent, read=read, load_report=saved_report,
                local_only=dataset['adapter'] == 'hierarchy_local_nodes')
        return prepare({**dataset, 'adapter': 'generic'}, {'cases': cases}, template), sources, preparation
    if dataset['adapter'] == 'distillation_verdict':
        try:
            from . import distillation_verdict
        except ImportError:
            import distillation_verdict
        cases, protected, preparation = distillation_verdict.prepare_source(
            source, path.parent, dataset.get('select'), include_post='{POST}' in template,
            include_teacher_contexts='{TEACHER_CONTEXTS}' in template)
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] == 'distillation_matching':
        try:
            from . import distillation_matching
        except ImportError:
            import distillation_matching
        cases, protected, preparation = distillation_matching.prepare_source(
            source, path.parent, dataset.get('select'), include_post='{POST}' in template)
        sources.update(protected)
        rendered = prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template)
        import tiktoken
        encoding = tiktoken.get_encoding('o200k_base')
        for case in rendered:
            case['evidence']['input_tokens'] = len(encoding.encode(case['prompt'], disallowed_special=()))
        return rendered, sources, preparation
    if dataset['adapter'] == 'distillation_coverage_search':
        from . import distillation_coverage_search
        cases, protected, preparation = distillation_coverage_search.prepare_source(
            source, path.parent, dataset.get('select'))
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] == 'distillation_review_evaluation':
        from . import distillation_review_evaluation
        cases, protected, preparation = distillation_review_evaluation.prepare_source(
            source, path.parent, dataset.get('select'), include_post='{POST}' in template,
            include_teacher_contexts='{TEACHER_CONTEXTS}' in template)
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] == 'distillation_review':
        try:
            from . import distillation_review
        except ImportError:
            import distillation_review
        cases, protected, preparation = distillation_review.prepare_source(
            source, path.parent, dataset.get('select'), load_report)
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] in {'posts', 'subjects'} and 'sources' in source:
        source = corpus_inputs.load(source, path.parent, read, read_bytes=read_bytes)
    if dataset['adapter'] in {'bounded_parent_guides', 'bounded_parent_comparisons'}:
        try:
            from . import parent_guide_workflow as guides
        except ImportError:
            import parent_guide_workflow as guides
        if dataset['adapter'] == 'bounded_parent_guides':
            prior_paths = engine._validate_string_array(
                source.get('prior_guides', []), 'prior parent-guide experiments', allow_empty=True)
            prior_directories = [engine._resolve_path(p, 'prior parent-guide experiment', path.parent)
                                 for p in prior_paths]
            if len(set(prior_directories)) != len(prior_directories):
                raise ValueError('duplicate prior parent-guide experiment')
            if prior_directories and load_report is None:
                raise ValueError('guide reuse requires validated experiment reports')
            cases, protected, preparation = guides.create_guide_source(
                source, template, base=path.parent, selected=dataset.get('select'),
                prior_reports=[load_report(p) for p in prior_directories])
        else:
            if load_report is None:
                raise ValueError('parent comparisons require validated experiment reports')
            paths = engine._validate_string_array(
                source.get('discoveries'), 'parent-guide experiments', allow_empty=False)
            directories = [engine._resolve_path(p, 'parent-guide experiment', path.parent) for p in paths]
            if len(set(directories)) != len(directories):
                raise ValueError('duplicate parent-guide experiment')
            reports = [load_report(p) for p in directories]
            prior_paths = engine._validate_string_array(
                source.get('prior_comparisons', []), 'prior comparison experiments', allow_empty=True)
            prior_directories = [engine._resolve_path(p, 'prior comparison experiment', path.parent)
                                 for p in prior_paths]
            if len(set(prior_directories)) != len(prior_directories):
                raise ValueError('duplicate prior comparison experiment')
            cases, protected, preparation = guides.build_comparison_source(
                source, reports, template, base=path.parent, selected=dataset.get('select'),
                prior_reports=[load_report(p) for p in prior_directories])
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, {'cases': cases}, template), sources, preparation
    if dataset['adapter'] in {'bounded_discovery', 'bounded_comparisons'}:
        try:
            from . import bounded_hierarchy_workflow as bounded
        except ImportError:
            import bounded_hierarchy_workflow as bounded
        if dataset['adapter'] == 'bounded_discovery':
            cases, protected, preparation = bounded.create_discovery_source(
                source, template, base=path.parent, selected=dataset.get('select'))
        elif 'original_sp_edges' in source:
            cases, protected, preparation = bounded.build_sp_link_comparison_source(
                source, template, base=path.parent, selected=dataset.get('select'))
        else:
            if load_report is None:
                raise ValueError('bounded comparisons require validated experiment reports')
            paths = engine._validate_string_array(
                source.get('discoveries'), 'discovery experiments', allow_empty=False)
            directories = [engine._resolve_path(p, 'discovery experiment', path.parent)
                           for p in paths]
            if len(set(directories)) != len(directories):
                raise ValueError('duplicate discovery experiment')
            reports = [load_report(p) for p in directories]
            cases, protected, preparation = bounded.build_comparison_source(
                source, reports, template, base=path.parent, selected=dataset.get('select'))
        sources.update(protected)
        return prepare({**dataset, 'adapter': 'generic'}, {'cases': cases}, template), sources, preparation
    if dataset['adapter'] == 'hierarchy_construction':
        engine._expect_fields(source, 'hierarchy construction',
                              {'schema_version', 'inputs', 'hierarchy'})
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected hierarchy construction schema_version 1')
        references = {}
        for key in ('inputs', 'hierarchy'):
            source_path = engine._resolve_path(source[key], key, path.parent)
            source[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        source['source'] = references
    if dataset['adapter'] == 'parent_candidates':
        engine._expect_fields(source, 'parent candidates',
                              {'schema_version', 'inputs', 'hierarchy', 'judgments', 'nodes'})
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected parent candidates schema_version 1')
        references = {}
        for key in ('inputs', 'hierarchy', 'judgments'):
            source_path = engine._resolve_path(source[key], key, path.parent)
            source[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        source['source'] = references
    if dataset['adapter'] == 'node_descriptions':
        engine._expect_fields(source, 'node descriptions',
            {'schema_version', 'source_packets', 'hierarchy'} | ({'nodes'} & source.keys()))
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected node descriptions schema_version 1')
        references = {}
        for key in ('source_packets', 'hierarchy'):
            source_path = engine._resolve_path(source[key], key, path.parent)
            source[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        source['source'] = references
    if dataset['adapter'] in {'subject_contexts', 'node_sorting'}:
        selector = 'nodes' if 'nodes' in source else 'selections'
        engine._expect_fields(source, 'subject contexts',
                              {'schema_version', 'subjects', 'hierarchy', selector}
                              | ({'descriptions'} & source.keys()))
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected subject contexts schema_version 1')
        references = {}
        for key in ('subjects', 'hierarchy') + (('descriptions',) if 'descriptions' in source else ()):
            source_path = engine._resolve_path(source[key], key, path.parent)
            source[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        source['source'] = references
    if dataset['adapter'] == 'subject_pairs' and 'registry' in source:
        try:
            from . import subject_pair_candidates
        except ImportError:
            import subject_pair_candidates
        cases, preparation = subject_pair_candidates.prepare(source, path.parent, read)
        return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, preparation
    if dataset['adapter'] == 'subject_pairs':
        modes = [key for key in ('pairs', 'comparisons', 'selection', 'parent_candidates') if key in source]
        if len(modes) != 1:
            raise ValueError('subject pairs require exactly one of pairs, comparisons, selection or parent_candidates')
        mode = modes[0]
        engine._expect_fields(source, 'subject pairs',
            {'schema_version', 'inputs', 'hierarchy', mode}
            | ({'exclude_compared'} if mode == 'selection' and 'exclude_compared' in source else set()))
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected subject pairs schema_version 1')
        if mode == 'selection' and source[mode] not in {
                'same_worded_siblings', 'shared_child_parents', 'hg4'}:
            raise ValueError('unknown subject pair selection rule')
        loaded, references = {}, {}
        for key in ('inputs', 'hierarchy'):
            source_path = engine._resolve_path(source[key], key, path.parent)
            loaded[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        if mode in {'comparisons', 'parent_candidates'}:
            paths = engine._validate_string_array(source[mode], mode, allow_empty=False)
            paths = [engine._resolve_path(p, 'comparison experiment', path.parent) for p in paths]
            if len(paths) != len(set(paths)):
                raise ValueError('duplicate comparison experiment')
            if load_report is None:
                raise ValueError('comparison preparation requires validated experiment reports')
            reports = []
            for directory in paths:
                envelope = read(directory / 'experiment.json')
                result = load_report(directory)
                # The shared report loader validates frozen plans and actual receipts.
                for name in envelope['plan']['files']:
                    file = directory / name
                    sources[str(file)] = engine._sha256_file(file)
                for case in result['cases']:
                    if case.get('receipt'):
                        file = Path(case['receipt']['results_path'])
                        sources[str(file)] = engine._sha256_file(file)
                reports.append(result)
            base = dict(**loaded, pairs=[], source=references)
            if mode == 'parent_candidates':
                cases = prepare_parent_candidate_pairs(base, reports)
                return prepare({**dataset, 'adapter': 'generic'}, dict(cases=cases), template), sources, None
            source, preparation = combine_subject_pairs(base, reports, template)
        else:
            exclusion = source.get('exclude_compared')
            source = dict(**loaded, **{mode: source[mode]}, source=references)
            if exclusion is not None:
                history_path = engine._resolve_path(exclusion, 'exclude_compared', path.parent)
                history = read(history_path)
                saved_hierarchy = history.get('preparation', {}).get('hierarchy', {})
                if (history.get('subjects') != loaded['inputs']['subjects']
                        or any(saved_hierarchy.get(k) != loaded['hierarchy'][k]
                               for k in ('groups', 'member_to_group'))):
                    raise ValueError('saved judgment subjects or nodes differ from selected hierarchy')
                if not isinstance(history.get('comparisons'), list):
                    raise ValueError('saved judgments require comparisons')
                excluded = set()
                for prior in history['comparisons']:
                    pair = {k: prior[k] for k in ('id', 'A', 'B')}
                    expected = prepare_subject_pairs(dict(**loaded, pairs=[pair], source=references))[0]
                    if (prior.get('inputs') != expected['inputs']
                            or prior.get('answer', {}).get('relation') not in {
                                'equivalent', 'a_parent_of_b', 'b_parent_of_a', 'neither', 'uncertain'}):
                        raise ValueError('saved judgment inputs differ or answer is invalid')
                    excluded.add(frozenset((prior['A'], prior['B'])))
                cases = prepare_subject_pairs(source, dataset.get('select'))
                source = dict(cases=[c for c in cases if frozenset((
                    c['evidence']['A']['node_id'], c['evidence']['B']['node_id'])) not in excluded])
                # The selection/history sources are hash-bound; already prepared
                # inputs and nomination evidence use the ordinary generic path.
                return prepare({**dataset, 'adapter': 'generic'}, source, template), sources, None
    effective = {**dataset, 'adapter': 'generic'} if preparation is not None else dataset
    return prepare(effective, source, template), sources, preparation


def prepare_parent_candidate_pairs(source, reports):
    """Use receipt-validated nominations as ordinary pair inputs, not placements."""
    prepare_subject_pairs(source)
    subjects, groups = source['inputs']['subjects'], source['hierarchy']['groups']
    by_id = {f'S{members[0]:04d}': members for members in groups}
    pairs, nominations = {}, {}
    for report in reports:
        if report['adapter'] != 'parent_candidates':
            raise ValueError('expected a parent_candidates experiment')
        for case in report['cases']:
            if case['status'] != 'valid' or not case.get('receipt'):
                raise ValueError(f"parent candidate case is not valid: {case['id']}")
            for key, reference in source['source'].items():
                saved = case['evidence']['source'].get(key)
                if not saved or saved['sha256'] != reference['sha256']:
                    raise ValueError('parent candidate source hash differs from saved hierarchy inputs')
            a = case['evidence']['A']['node_id']
            if a not in by_id or case['evidence']['A']['subject_entries'] != [subjects[i] for i in by_id[a]]:
                raise ValueError('parent candidate query differs from saved hierarchy node')
            payload = json.loads(case['inputs']['INPUT_JSON'])
            catalogue = {c['id']: c['subjects'] for c in payload['candidates']}
            for nomination in case['parsed']['candidates']:
                b = nomination['id']
                if (b not in by_id or b == a or catalogue.get(b) != list(dict.fromkeys(
                        subjects[i]['subject'] for i in by_id[b]))):
                    raise ValueError('parent candidate nomination differs from saved hierarchy node')
                key = tuple(sorted((a, b)))
                pair = pairs.setdefault(key, dict(id=a + '-' + b, A=a, B=b))
                expected = prepare_subject_pairs(dict(source, pairs=[pair]))[0]
                query_key = 'A' if pair['A'] == a else 'B'
                if payload['A'] != json.loads(expected['inputs']['INPUT_JSON'])[query_key]:
                    raise ValueError('parent candidate query contexts differ from saved hierarchy node')
                nominations.setdefault(key, []).append(dict(
                    experiment=report['experiment'], case_id=case['id'],
                    prompt_id=report['prompt_id'], settings=report['settings'],
                    candidate=nomination, receipt=case['receipt']))
    cases = prepare_subject_pairs(dict(source, pairs=list(pairs.values())))
    for case in cases:
        key = tuple(sorted(case['evidence'][k]['node_id'] for k in ('A', 'B')))
        case['evidence']['parent_candidates'] = nominations[key]
    return cases


def combine_subject_pairs(source, reports, template):
    """Combine saved equivalent nodes and remap only previously compared pairs.

    Reports must come from the shared receipt-validating loader. No new pair
    selection, ancestor application, retitling or semantic judgment happens here.
    """
    prepare_subject_pairs(source)  # Validate the complete original partition/edges.
    subjects, original = source['inputs']['subjects'], source['hierarchy']
    groups = original['groups']
    by_id = {f'S{members[0]:04d}': g for g, members in enumerate(groups)}
    parent = list(range(len(groups)))

    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    comparisons, equivalences = [], []
    for report in reports:
        for case in report['cases']:
            if case['status'] != 'valid' or not case.get('receipt'):
                raise ValueError(f"comparison is not valid: {case['id']}")
            evidence = case['evidence']
            saved_sources = evidence['source']
            for key, reference in source['source'].items():
                saved = saved_sources.get(key, saved_sources.get('results') if key == 'hierarchy' else None)
                if not saved or saved['sha256'] != reference['sha256']:
                    raise ValueError('comparison source hash differs from saved hierarchy inputs')
            pair = dict(id=case['id'], A=evidence['A']['node_id'], B=evidence['B']['node_id'])
            expected = prepare_subject_pairs({**source, 'pairs': [pair]})[0]
            if (case['inputs'] != expected['inputs']
                    or case['prompt'] != render(template, expected['inputs'])
                    or any(evidence[k]['subject_entries'] != expected['evidence'][k]['subject_entries']
                           for k in ('A', 'B'))):
                raise ValueError('comparison inputs differ from original nodes or prompt')
            answer = case['parsed']
            if (set(answer) != {'relation', 'reason'} or not isinstance(answer['reason'], str)
                    or answer['relation'] not in {'equivalent', 'a_parent_of_b', 'b_parent_of_a',
                                                  'neither', 'uncertain'}):
                raise ValueError('unsupported subject comparison answer')
            prior = dict(experiment=report['experiment'], case_id=case['id'],
                         A=pair['A'], B=pair['B'], inputs=case['inputs'],
                         answer=answer, receipt=case['receipt'],
                         prompt_id=report['prompt_id'], settings=report['settings'],
                         reviews=case.get('reviews', []),
                         shared_children=evidence.get('shared_children', []))
            comparisons.append(prior)
            if answer['relation'] == 'equivalent':
                a, b = find(by_id[pair['A']]), find(by_id[pair['B']])
                parent[b] = a
                equivalences.append(prior)

    components = {}
    for g, members in enumerate(groups):
        components.setdefault(find(g), []).extend(members)
    merged = sorted((sorted(m) for m in components.values()), key=lambda m: m[0])
    owners = {i: g for g, members in enumerate(merged) for i in members}
    remap = {g: owners[members[0]] for g, members in enumerate(groups)}
    edges = sorted({(remap[a], remap[b]) for a, b in original['edges'] if remap[a] != remap[b]})
    outgoing = {g: set() for g in range(len(merged))}
    incoming = {g: set() for g in range(len(merged))}
    for a, b in edges:
        outgoing[a].add(b)
        incoming[b].add(a)
    try:
        list(TopologicalSorter(incoming).static_order())
    except CycleError as error:
        raise ValueError('equivalent-node combination creates an SP cycle; no repair applied') from error
    descendants = {}
    for a, b in source['inputs']['edges']:
        a, b = owners[a], owners[b]
        if a == b:
            continue
        if a not in descendants:
            pending, visited = list(outgoing[a]), set()
            while pending:
                child = pending.pop()
                if child not in visited:
                    visited.add(child)
                    pending.extend(outgoing[child] - visited)
            descendants[a] = visited
        if b not in descendants[a]:
            raise ValueError('equivalent-node combination loses SP ancestry')

    hierarchy = dict(groups=merged, member_to_group=[owners[i] for i in range(len(subjects))],
                     edges=[list(e) for e in edges])
    mapping = {nid: f'S{merged[remap[g]][0]:04d}' for nid, g in by_id.items()}
    pairs, internal = {}, []
    for prior in comparisons:
        a, b = mapping[prior['A']], mapping[prior['B']]
        if a == b:
            internal.append(prior)
        else:
            key = tuple(sorted((remap[by_id[prior['A']]], remap[by_id[prior['B']]])))
            pairs.setdefault(key, []).append(prior)

    combined_source = {**source, 'hierarchy': hierarchy}
    cases, unchanged = [], []
    for (ga, gb), previous in sorted(pairs.items()):
        a, b = f'S{merged[ga][0]:04d}', f'S{merged[gb][0]:04d}'
        pair = dict(id=a + '-' + b, A=a, B=b)
        # Keep unchanged judgments as source-bound evidence, not new model jobs.
        # This does not weaken the executor's exact transport/request cache rules.
        saved = None
        for prior in previous:
            trial = dict(id=prior['case_id'], A=mapping[prior['A']], B=mapping[prior['B']])
            candidate = prepare_subject_pairs({**combined_source, 'pairs': [trial]})[0]
            if candidate['inputs'] == prior['inputs']:
                pair = trial
                saved = prior
                break
        if saved is not None:
            unchanged.append(dict(id=pair['id'], A=pair['A'], B=pair['B'],
                                  source=saved, previous_comparisons=previous))
            continue
        case = prepare_subject_pairs({**combined_source, 'pairs': [pair]})[0]
        case['evidence']['previous_comparisons'] = previous
        for key in ('A', 'B'):
            nid = case['evidence'][key]['node_id']
            case['evidence'][key]['original_nodes'] = [old for old, new in mapping.items() if new == nid]
        cases.append(case)
    preparation = dict(
        hierarchy=hierarchy, original_node_to_combined=mapping,
        equivalent_answers=equivalences, internal_comparisons=internal,
        unchanged_comparisons=unchanged,
        summary=dict(original_nodes=len(groups), combined_nodes=len(merged),
            equivalent_answers=len(equivalences), internal_comparisons=len(internal),
            original_comparisons=len(comparisons), current_pairs=len(pairs),
            changed_pairs=len(cases), unchanged_pairs=len(unchanged)))
    # Already prepared evidence is preserved through the ordinary rendering path.
    return dict(cases=cases), preparation


def prepare_subject_pairs(source, selected=None):
    """Compare saved SP hierarchy nodes using explicit pairs or a selection rule."""
    inputs, hierarchy = source['inputs'], source['hierarchy']
    subjects, groups = inputs['subjects'], hierarchy['groups']
    posts = {p['note_id']: p for p in inputs['posts']}
    if len(posts) != len(inputs['posts']):
        raise ValueError('duplicate source post identity')
    for i, subject in enumerate(subjects):
        if type(subject['index']) is not int or subject['index'] != i:
            raise ValueError('subject index does not match saved position')
        engine._expect_string(subject['subject'], 'subject')
        if not isinstance(subject['context'], str):
            raise ValueError('subject context must be a string')
        if subject['note_id'] not in posts:
            raise ValueError('subject refers to an unknown source post')

    owners, nodes = {}, {}
    for g, members in enumerate(groups):
        if not isinstance(members, list) or not members:
            raise ValueError('hierarchy group must be nonempty')
        for i in members:
            if type(i) is not int or not 0 <= i < len(subjects) or i in owners:
                raise ValueError('invalid or repeated hierarchy subject member')
            owners[i] = g
        # Same identity as subject_matching_probe.browser_spec; not the group index.
        nodes[f'S{members[0]:04d}'] = g
    if set(owners) != set(range(len(subjects))):
        raise ValueError('hierarchy groups do not cover the saved subjects')
    if hierarchy['member_to_group'] != [owners[i] for i in range(len(subjects))]:
        raise ValueError('hierarchy member mapping differs from groups')

    def edges(value, size):
        for edge in value:
            if (not isinstance(edge, list) or len(edge) != 2
                    or any(type(i) is not int or not 0 <= i < size for i in edge)):
                raise ValueError('invalid hierarchy or SP edge')
            yield edge

    children = {g: set() for g in range(len(groups))}
    for a, b in edges(hierarchy['edges'], len(groups)):
        children[a].add(b)
    witnesses = {}
    for a, b in edges(inputs['edges'], len(subjects)):
        witnesses.setdefault((owners[a], owners[b]), set()).add(subjects[a]['note_short_id'])

    nominations = {}
    if 'selection' in source:
        rule = source['selection']
        if rule not in {'same_worded_siblings', 'shared_child_parents', 'hg4'}:
            raise ValueError('unknown subject pair selection rule')
        browsing_children = {g: set() for g in range(len(groups))}
        browsing_parents = {g: set() for g in range(len(groups))}
        for a, b in edges(hierarchy.get('browsing_edges', hierarchy['edges']), len(groups)):
            browsing_children[a].add(b)
            browsing_parents[b].add(a)
        sibling_nominations = {}
        if rule in {'same_worded_siblings', 'hg4'}:
            for parent, siblings in browsing_children.items():
                by_wording = {}
                for g in sorted(siblings):
                    nid = f'S{groups[g][0]:04d}'
                    for wording in {subjects[i]['subject'] for i in groups[g]}:
                        by_wording.setdefault(wording, []).append(nid)
                for wording, siblings in by_wording.items():
                    for pair in combinations(sorted(siblings), 2):
                        parent_id = f'S{groups[parent][0]:04d}'
                        sibling_nominations.setdefault(pair, {}).setdefault(parent_id, set()).add(wording)
            for pair, parents in sorted(sibling_nominations.items()):
                for parent, wordings in sorted(parents.items()):
                    nomination = dict(parent=parent, matching_subjects=sorted(wordings))
                    if rule == 'hg4':
                        nomination['rule'] = 'same_worded_siblings'
                    nominations.setdefault(pair, []).append(nomination)
        if rule in {'shared_child_parents', 'hg4'}:
            for child, parents in browsing_parents.items():
                child_posts = sorted({subjects[i]['note_short_id'] for i in groups[child]})
                if len({subjects[i]['note_id'] for i in groups[child]}) < 2:
                    continue
                for pair in combinations(sorted(f'S{groups[g][0]:04d}' for g in parents), 2):
                    nomination = dict(child=f'S{groups[child][0]:04d}', posts=child_posts)
                    if rule == 'hg4':
                        nomination['rule'] = 'shared_child_parents'
                    nominations.setdefault(pair, []).append(nomination)
        pairs = [dict(id=f'{a}-{b}', A=a, B=b) for a, b in sorted(nominations)]
    else:
        pairs = source['pairs']

    def node(nid):
        g = nodes[nid]
        entries, seen = [], set()
        for i in groups[g]:
            subject = subjects[i]
            pair = subject['subject'], subject['context']
            if pair not in seen:
                seen.add(pair)
                entries.append(dict(subject=pair[0], context=pair[1]))
        return entries, dict(node_id=nid, group_index=g,
                             subject_entries=[subjects[i] for i in groups[g]])

    cases, ids = [], set()
    for pair in pairs:
        engine._expect_fields(pair, 'subject pair', {'id', 'A', 'B'})
        cid = engine._expect_identifier(pair['id'], 'case.id')
        if cid in ids:
            raise ValueError('duplicate case identity')
        ids.add(cid)
        for key in ('A', 'B'):
            nid = engine._expect_string(pair[key], f'pair.{key}')
            if nid not in nodes:
                raise ValueError(f'unknown hierarchy node: {nid}')
        if pair['A'] == pair['B']:
            raise ValueError('subject pair must name distinct hierarchy nodes')
        if selected is not None and cid not in selected:
            continue
        ea, a = node(pair['A'])
        eb, b = node(pair['B'])
        ga, gb = a['group_index'], b['group_index']
        shared = [dict(id=f'S{groups[g][0]:04d}',
                       names=list(dict.fromkeys(subjects[i]['subject'] for i in groups[g])),
                       a_posts=sorted(witnesses.get((ga, g), [])),
                       b_posts=sorted(witnesses.get((gb, g), [])))
                  for g in sorted(children[ga] & children[gb])]
        post_ids = sorted({s['note_id'] for n in (a, b) for s in n['subject_entries']})
        cases.append(dict(id=cid,
            inputs={'INPUT_JSON': json.dumps({'A': ea, 'B': eb}, ensure_ascii=False, indent=2)},
            evidence=dict(A=a, B=b, source=source['source'], shared_children=shared,
                          source_posts=[posts[p] for p in post_ids])))
        if 'selection' in source:
            cases[-1]['evidence']['selection'] = dict(
                rule=source['selection'], nominations=nominations[(pair['A'], pair['B'])])
    if selected is not None and set(selected) - ids:
        raise ValueError('unknown case requested')
    return cases


def prepare_hierarchy_construction(source, selected=None):
    """Schedule existing nodes once by source post, against the full saved graph."""
    base = dict(inputs=source['inputs'], hierarchy=source['hierarchy'],
                pairs=[], source=source['source'])
    prepare_subject_pairs(base)
    subjects, groups = base['inputs']['subjects'], base['hierarchy']['groups']
    node_ids = [f'S{min(members):04d}' for members in groups]
    incoming = {g: set() for g in range(len(groups))}
    for a, b in base['hierarchy']['edges']:
        incoming[b].add(a)
    try:
        list(TopologicalSorter(incoming).static_order())
    except CycleError as error:
        raise ValueError('hierarchy construction source contains a cycle') from error
    post_names = {}
    for s in subjects:
        name = engine._expect_identifier(s['note_short_id'], 'note_short_id')
        if name in post_names and post_names[name] != s['note_id']:
            raise ValueError('duplicate source post short identity')
        post_names[name] = s['note_id']
    if len(set(post_names.values())) != len(post_names):
        raise ValueError('source post has inconsistent short identities')

    nodes, evidence, queries = [], [], {}
    for nid, members in sorted(zip(node_ids, groups)):
        entries = list(dict.fromkeys((subjects[i]['subject'], subjects[i]['context'])
                                     for i in members))
        nodes.append(dict(id=nid, entries=[dict(subject=s, context=c) for s, c in entries]))
        evidence.append(dict(node_id=nid, subject_entries=[subjects[i] for i in members]))
        owner = min(subjects[i]['note_short_id'] for i in members)
        queries.setdefault(owner, []).append(nid)
    if selected is not None and set(selected) - queries.keys():
        raise ValueError('unknown case requested')
    catalogue = json.dumps(dict(nodes=nodes, links=[
        dict(ancestor=a, descendant=b) for a, b in sorted(set(
            (node_ids[a], node_ids[b]) for a, b in base['hierarchy']['edges']))]),
        ensure_ascii=False, separators=(',', ':'))
    return [dict(id=post, inputs=dict(CATALOGUE_JSON=catalogue,
                  QUERY_JSON=json.dumps(dict(nodes=ids), ensure_ascii=False)),
                 evidence=dict(scheduling_post=post, nodes=evidence,
                               source_posts=base['inputs']['posts'], source=source['source']))
            for post, ids in sorted(queries.items()) if selected is None or post in selected]


def prepare_consolidations(source, base, read):
    """Gather complete sibling groups and explicitly declared diagnostic edits."""
    from . import canonical_trial as trial
    engine._expect_fields(source, 'consolidation source', {'schema_version', 'state', 'menu', 'selections'})
    if type(source['schema_version']) is not int or source['schema_version'] != 1:
        raise ValueError('consolidation requires schema 1')

    def bound(reference):
        engine._expect_fields(reference, 'consolidation reference', {'path', 'sha256'})
        path = engine._resolve_path(reference['path'], 'consolidation reference', base)
        if engine._sha256_file(path) != reference['sha256']:
            raise ValueError('consolidation source changed: ' + str(path))
        return read(path), path

    state, state_path = bound(source['state'])
    menu, menu_path = bound(source['menu'])
    if state['status'] != 'complete' or menu['status'] != 'shaped_candidate':
        raise ValueError('consolidation requires a completed graph and saved menu')
    raw = {node['id']: node for node in state['nodes']}
    nodes = {node['id']: node for node in menu['nodes']}
    if len(raw) != len(state['nodes']) or len(nodes) != len(menu['nodes']):
        raise ValueError('duplicate consolidation canonical ID')
    raw_ancestors = trial._ancestors(state['nodes'])
    trial._ancestors(menu['nodes'])
    for identifier, node in nodes.items():
        if (identifier not in raw or any(node[key] != raw[identifier][key]
                for key in ('subject', 'meaning', 'entries'))
                or set(node['parents']) - raw_ancestors[identifier]):
            raise ValueError('consolidation menu changed original meanings or relationships')

    def supplied(node):
        engine._expect_string(node['subject'], 'canonical title')
        engine._expect_string(node['meaning'], 'canonical meaning')
        return dict(id=node['id'], title=node['subject'], meaning=node['meaning'])

    if not isinstance(source['selections'], list) or not source['selections']:
        raise ValueError('consolidation selections must be nonempty')
    cases = []
    for selection in source['selections']:
        fields = {'id', 'parent'} | ({'meaning_edits'} if 'meaning_edits' in selection else set())
        engine._expect_fields(selection, 'consolidation selection', fields)
        parent = selection['parent']
        if parent is not None and (not isinstance(parent, str) or parent not in nodes):
            raise ValueError('unknown consolidation parent')
        siblings = [node for node in menu['nodes'] if
                    (not node['parents'] if parent is None else parent in node['parents'])]
        if not 3 <= len(siblings) <= 512:
            raise ValueError('consolidation requires between three and 512 siblings')
        payload = dict(parent=None if parent is None else supplied(nodes[parent]),
                       siblings=[supplied(node) for node in sorted(siblings, key=lambda n: n['id'])])
        evidence = dict(state=str(state_path), menu=str(menu_path), parent=parent,
                        application_allowed=False)
        if 'meaning_edits' in selection:
            edits = selection['meaning_edits']
            if not isinstance(edits, list) or not edits:
                raise ValueError('meaning edits must be a nonempty array')
            offered = {node['id']: node for node in payload['siblings']}
            seen = set()
            for edit in edits:
                engine._expect_fields(edit, 'meaning edit', {'id', 'before', 'after'})
                for key in ('id', 'before', 'after'):
                    engine._expect_string(edit[key], 'meaning edit ' + key)
                if edit['id'] not in offered:
                    raise ValueError('meaning edit targets an unknown sibling')
                if edit['id'] in seen:
                    raise ValueError('duplicate meaning edit')
                seen.add(edit['id'])
                if offered[edit['id']]['meaning'] != edit['before']:
                    raise ValueError('meaning edit before differs from saved meaning')
                if edit['after'] == edit['before']:
                    raise ValueError('meaning edit must change the saved meaning')
                offered[edit['id']]['meaning'] = edit['after']
            evidence.update(synthetic=True, meaning_edits=edits)
        cases.append(dict(id=selection['id'], inputs=dict(INPUT_JSON=json.dumps(payload, ensure_ascii=False)),
                          evidence=evidence))
    return cases


def prepare_saved_consolidations(source, base, read, load_report, sources, *, pairwise):
    """Load verified saved proposals for whole-group review or edge comparisons."""
    from . import canonical_trial as trial
    fields = {'schema_version', 'proposals'}
    if isinstance(source, dict) and 'include_nomination' in source:
        fields.add('include_nomination')
    engine._expect_fields(source, 'consolidation comparisons', fields)
    include_nomination = source.get('include_nomination', True)
    if type(include_nomination) is not bool:
        raise ValueError('include_nomination must be a boolean')
    if pairwise and 'include_nomination' in source:
        raise ValueError('include_nomination is only supported for whole-group review')
    if (type(source['schema_version']) is not int or source['schema_version'] != 1
            or not isinstance(source['proposals'], list) or not source['proposals']):
        raise ValueError('consolidation comparisons require schema 1 and nonempty proposals')
    if load_report is None:
        raise ValueError('consolidation comparisons require validated experiment reports')
    cases = []
    for index, item in enumerate(source['proposals'], 1):
        fields = {'experiment', 'case'} | ({'meaning_edit'} if 'meaning_edit' in item else set())
        engine._expect_fields(item, 'saved proposal', fields)
        if pairwise and 'meaning_edit' in item:
            raise ValueError('meaning_edit is only supported for whole-group review')
        engine._expect_fields(item['experiment'], 'proposal experiment', {'path', 'sha256'})
        directory = engine._resolve_path(item['experiment']['path'], 'proposal experiment', base)
        envelope = directory / 'experiment.json'
        if engine._sha256_file(envelope) != item['experiment']['sha256']:
            raise ValueError('consolidation proposal experiment changed')
        plan = read(envelope)['plan']
        if plan['dataset']['adapter'] != 'canonical_consolidation':
            raise ValueError('expected a native consolidation experiment')
        for path, expected in {**plan['sources'], **{
                str(directory / name): sha for name, sha in plan['files'].items()}}.items():
            if engine._sha256_file(Path(path)) != expected:
                raise ValueError('consolidation producer source changed: ' + path)
            if path in sources and sources[path] != expected:
                raise ValueError('conflicting consolidation producer source: ' + path)
            sources[path] = expected
        report = load_report(directory)
        rows = [row for row in report['cases'] if row['id'] == item['case']]
        if len(rows) != 1 or rows[0]['status'] != 'valid' or not rows[0].get('receipt'):
            raise ValueError('consolidation comparison requires a valid saved proposal')
        saved = rows[0]
        proposal = saved.get('parsed')
        if proposal is None:
            raise ValueError('a null proposal has no comparisons')
        validate(plan['dataset'], saved, saved['output'], None)
        receipt_path = Path(saved['receipt']['results_path']).resolve()
        sources[str(receipt_path)] = engine._sha256_file(receipt_path)
        offered = json.loads(saved['inputs']['INPUT_JSON'])
        if not pairwise:
            proposal_input = dict(proposal) if include_nomination else {
                key: proposal[key] for key in ('title', 'meaning')}
            evidence = dict(proposal_experiment=str(directory), proposal_case=item['case'],
                            proposal_receipt=saved['receipt'], application_allowed=False)
            if 'meaning_edit' in item:
                edit = item['meaning_edit']
                engine._expect_fields(edit, 'proposal meaning edit', {'before', 'after'})
                for key in ('before', 'after'):
                    engine._expect_string(edit[key], 'proposal meaning edit ' + key)
                if not edit['after'].strip():
                    raise ValueError('proposal meaning edit after must not be blank')
                if edit['before'] != proposal['meaning']:
                    raise ValueError('proposal meaning edit before differs from saved meaning')
                if edit['after'] == edit['before']:
                    raise ValueError('proposal meaning edit must change the saved meaning')
                proposal_input['meaning'] = edit['after']
                evidence.update(synthetic=True, meaning_edit=edit)
            cases.append(dict(id=f'proposal-{index}',
                inputs=dict(INPUT_JSON=json.dumps({**offered, 'proposal': proposal_input}, ensure_ascii=False)),
                evidence=evidence))
            continue
        state = read(Path(saved['evidence']['state']))
        nodes = {node['id']: node for node in state['nodes']}
        ancestors = trial._ancestors(state['nodes'])

        def node(identifier):
            return {key: nodes[identifier][key] for key in ('id', 'subject', 'meaning', 'parents')}

        targets = offered['siblings'] + ([offered['parent']] if offered['parent'] is not None else [])
        for target in targets:
            identifier = target['id']
            if (identifier not in nodes or target['title'] != nodes[identifier]['subject']
                    or target['meaning'] != nodes[identifier]['meaning']):
                raise ValueError('proposal target differs from original canonical meaning')
            canonical = {**node(identifier),
                'ancestors': [node(key) for key in sorted(ancestors[identifier])],
                'descendants': [node(key) for key in sorted(nodes) if identifier in ancestors[key]]}
            payload = dict(local=dict(subject=proposal['title'], meaning=proposal['meaning']),
                           canonical=canonical)
            cases.append(dict(id=f'proposal-{index}-{identifier}',
                inputs=dict(INPUT_JSON=json.dumps(payload, ensure_ascii=False)),
                evidence=dict(proposal_experiment=str(directory), proposal_case=item['case'],
                    proposal_receipt=saved['receipt'], canonical_id=identifier,
                    intended_child=identifier in proposal['children'],
                    supplied_parent=offered['parent'] is not None and identifier == offered['parent']['id'],
                    application_allowed=False)))
    return cases


def prepare_shaping_nominations(source, base, sources):
    """Gather whole sibling groups and bounded original locals from saved SSE rankings."""
    from . import canonical_trial as trial
    engine._expect_fields(source, 'shaping nomination', {'schema_version', 'max_candidates', 'selections'})
    if (source['schema_version'] != 1 or type(source['max_candidates']) is not int
            or not 1 <= source['max_candidates'] <= 32):
        raise ValueError('shaping nomination requires schema 1 and at most 32 candidates')

    def read_bound(path, expected):
        path = Path(path).resolve()
        if engine._sha256_file(path) != expected:
            raise ValueError('shaping nomination source changed: ' + str(path))
        if str(path) in sources and sources[str(path)] != expected:
            raise ValueError('conflicting shaping nomination source: ' + str(path))
        sources[str(path)] = expected
        return json.loads(path.read_bytes())

    if not isinstance(source['selections'], list) or not source['selections']:
        raise ValueError('shaping nomination selections must be nonempty')
    cases = []
    for selection in source['selections']:
        engine._expect_fields(selection, 'shaping selection', {'id', 'nomination'})
        engine._expect_string(selection['id'], 'shaping selection id')
        reference = selection['nomination']
        engine._expect_fields(reference, 'nomination reference', {'path', 'sha256'})
        path = engine._resolve_path(reference['path'], 'nomination', base)
        report = read_bound(path, reference['sha256'])
        if report['schema_version'] != 1 or report['max_choices'] != 6:
            raise ValueError('expected whole-group SSE nomination schema 1 with K=6')
        protected = report['sources']
        for name, expected in protected.items():
            if engine._sha256_file(Path(name)) != expected:
                raise ValueError('shaping nomination source changed: ' + name)
            if name in sources and sources[name] != expected:
                raise ValueError('conflicting shaping nomination source: ' + name)
            sources[name] = expected
        for name in ('state', 'menu'):
            if report[name] not in protected:
                raise ValueError('shaping nomination is missing a protected ' + name)
        state = read_bound(report['state'], protected[report['state']])
        menu = read_bound(report['menu'], protected[report['menu']])
        if (state['status'] != 'complete' or menu['status'] != 'shaped_candidate'
                or state['corpus'] != menu['corpus'] or state['corpus'] not in protected):
            raise ValueError('shaping nomination requires a frozen completed graph and menu')
        corpus = read_bound(state['corpus'], protected[state['corpus']])
        raw = {node['id']: node for node in state['nodes']}
        nodes = {node['id']: node for node in menu['nodes']}
        raw_ancestors, ancestors = trial._ancestors(state['nodes']), trial._ancestors(menu['nodes'])
        for identifier, node in nodes.items():
            if (identifier not in raw or any(node[key] != raw[identifier][key]
                    for key in ('subject', 'meaning', 'entries'))
                    or set(node['parents']) - raw_ancestors[identifier]):
                raise ValueError('shaping menu changed original canonical evidence or relationships')
        parent = report['parent']
        if parent is not None and parent not in nodes:
            raise ValueError('unknown shaping parent')
        siblings = [node for node in menu['nodes'] if
            (not node['parents'] if parent is None else parent in node['parents'])]
        if len(siblings) <= 6 or set(report['siblings']) != {n['id'] for n in siblings}:
            raise ValueError('shaping nomination must contain the whole overcrowded sibling group')
        notes = {note['note_id']: note for note in corpus['notes']}
        entries = {(note['note_id'], row['number']): row
                   for note in corpus['notes'] for row in note['subjects']}
        mapping = {(entry['note_id'], entry['number']): node['id']
                   for node in state['nodes'] for entry in node['entries']}
        processed = {(step['local']['note_id'], step['local']['number']) for step in state['steps']}
        selected_notes = {entry['note_id'] for entry in state['roots']}
        all_note_ids = sorted(selected_notes | {entry['note_id'] for node in menu['nodes']
                                               for entry in node['entries']})
        note_ids = {nid: f'N{i+1:03d}' for i, nid in enumerate(all_note_ids)}
        local_entries, offered, seen_subjects = [], {}, set()
        for rank, candidate in enumerate(report['ranked'], 1):
            local = candidate['local']
            key = local['note_id'], local['number']
            if key not in entries or entries[key]['subject'] != candidate['subject']:
                raise ValueError('shaping candidate differs from its original local entry')
            if key in processed or key[0] not in selected_notes:
                raise ValueError('shaping candidate is already processed or outside selected notes')
            mapped = mapping.get((key[0], key[1].rsplit('.', 1)[0])) if '.' in key[1] else None
            allowed = sorted({n['id'] for n in trial._eligible(state, local, mapped)}
                             & {n['id'] for n in siblings})
            if len(allowed) < 2 or candidate['subject'] in seen_subjects:
                continue
            seen_subjects.add(candidate['subject'])
            branch = []
            parts = key[1].split('.')
            for depth in range(1, len(parts)):
                ancestor = entries.get((key[0], '.'.join(parts[:depth])))
                if ancestor is None:
                    raise ValueError('incomplete original local ancestor branch')
                branch.append({field: ancestor[field] for field in ('subject', 'context')})
            identifier = f'L{len(local_entries)+1:03d}'
            local_entries.append(dict(id=identifier, note_id=note_ids[key[0]],
                **{field: entries[key][field] for field in ('subject', 'context')},
                ancestors=branch, eligible_siblings=allowed))
            offered[identifier] = dict(local=local, sse_rank=rank)
            if len(local_entries) == source['max_candidates']:
                break
        footprints = {nid: {entry['note_id'] for entry in node['entries']}
                      for nid, node in nodes.items()}
        order = TopologicalSorter({nid: node['parents'] for nid, node in nodes.items()}).static_order()
        for child in reversed(list(order)):
            for ancestor in nodes[child]['parents']:
                footprints[ancestor].update(footprints[child])
        def canonical(node):
            return dict(id=node['id'], subject=node['subject'], meaning=node['meaning'],
                        parents=node['parents'], note_ids=sorted(note_ids[n] for n in footprints[node['id']]))
        payload = dict(max_choices=6, parent=None if parent is None else canonical(nodes[parent]),
            ancestors=[] if parent is None else [canonical(nodes[n]) for n in sorted(ancestors[parent])],
            siblings=[canonical(n) for n in sorted(siblings, key=lambda n: n['id'])],
            local_entries=local_entries, posts=[dict(id=note_ids[n], text=notes[n]['text'])
                for n in sorted({offered[row['id']]['local']['note_id'] for row in local_entries})])
        cases.append(dict(id=selection['id'], inputs=dict(INPUT_JSON=json.dumps(payload, ensure_ascii=False)),
            evidence=dict(nomination=str(path), offered=offered, note_ids=note_ids)))
    return cases


def prepare_parent_candidates(source, selected=None):
    """Nominate broader parents from the full unrelated, unjudged node catalogue."""
    try:
        from .subject_hierarchy import reachable
    except ImportError:
        from subject_hierarchy import reachable
    base = dict(inputs=source['inputs'], hierarchy=source['hierarchy'],
                pairs=[], source=source['source'])
    prepare_subject_pairs(base)  # Reuse production partition and source validation.
    subjects, groups = base['inputs']['subjects'], base['hierarchy']['groups']
    history = source['judgments']
    if history.get('subjects') != subjects or not isinstance(history.get('comparisons'), list):
        raise ValueError('saved judgment subjects differ or comparisons are missing')
    judged = set()
    for prior in history['comparisons']:
        pair = {k: prior[k] for k in ('id', 'A', 'B')}
        expected = prepare_subject_pairs(dict(base, pairs=[pair]))[0]
        if (prior.get('inputs') != expected['inputs']
                or prior.get('answer', {}).get('relation') not in {
                    'equivalent', 'a_parent_of_b', 'b_parent_of_a', 'neither', 'uncertain'}):
            raise ValueError('saved judgment inputs differ or answer is invalid')
        judged.add(frozenset((prior['A'], prior['B'])))
    nodes = engine._validate_string_array(source['nodes'], 'nodes', allow_empty=False)
    if len(nodes) != len(set(nodes)):
        raise ValueError('duplicate parent candidate query')
    by_id = {f'S{members[0]:04d}': g for g, members in enumerate(groups)}
    if set(nodes) - by_id.keys():
        raise ValueError('unknown parent candidate query node')
    if selected is not None and set(selected) - set(nodes):
        raise ValueError('unknown case requested')
    edges = base['hierarchy']['edges']
    incoming = {g: set() for g in range(len(groups))}
    for a, b in edges:
        incoming[b].add(a)
    try:
        list(TopologicalSorter(incoming).static_order())
    except CycleError as error:
        raise ValueError('parent candidate hierarchy contains a cycle') from error
    paths = reachable(len(groups), edges)
    catalogue = [dict(id=nid, subjects=list(dict.fromkeys(
        subjects[i]['subject'] for i in groups[g]))) for nid, g in by_id.items()]
    cases = []
    for nid in nodes:
        g = by_id[nid]
        if incoming[g]:
            raise ValueError('parent candidate query must be top-level')
        if selected is not None and nid not in selected:
            continue
        entries = list(dict.fromkeys((subjects[i]['subject'], subjects[i]['context'])
                                     for i in groups[g]))
        candidates = [c for c in catalogue if c['id'] != nid
            and (g, by_id[c['id']]) not in paths and (by_id[c['id']], g) not in paths
            and frozenset((nid, c['id'])) not in judged]
        payload = dict(A=[dict(subject=s, context=c) for s, c in entries], candidates=candidates)
        posts = {subjects[i]['note_id'] for i in groups[g]}
        cases.append(dict(id=nid,
            inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False, indent=2)},
            evidence=dict(A=dict(node_id=nid, group_index=g,
                subject_entries=[subjects[i] for i in groups[g]]),
                source=source['source'],
                source_posts=[p for p in base['inputs']['posts'] if p['note_id'] in posts])))
    return cases


def union_spans(spans):
    """Union validated byte spans, preserving every gap in the source text."""
    result = []
    for start, end in sorted(spans):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def prepare_prominence(source, selected=None, combine_masks=False):
    """Render saved masks, optionally unioned per node/post; metadata stays review-only."""
    if 'memberships' in source:
        nodes = source['memberships']['nodes']
        available = {node['group']: node for node in nodes}
        if len(available) != len(nodes):
            raise ValueError('duplicate hierarchy node identity')
        if selected is not None and set(selected) - available.keys():
            raise ValueError('unknown hierarchy node requested')
        members = []
        for nid, node in available.items():
            if selected is not None and nid not in selected:
                continue
            for mask in node['matched_instances']:
                aliases = []
                for origin in mask.get('origins', []):
                    original = origin['source_instance']
                    if any(original[key] != mask[key] for key in ('note_id', 'byte_spans')):
                        raise ValueError('hierarchy mask origin differs from direct member')
                    aliases.append(original['instance'])
                aliases = list(dict.fromkeys(aliases or [mask['instance']]))
                raw = mask['text'].encode()
                if [raw[a:b].decode() for a, b in mask['byte_spans']] != mask['fragments']:
                    raise ValueError('hierarchy mask fragments differ from source spans')
                members.append(dict(id=f'{nid}-{aliases[0]}', node_id=nid,
                                    node_title=node['title'], note_id=mask['note_id'],
                                    text=mask['text'], mask_ids=aliases, byte_spans=mask['byte_spans']))
        source, selected = {'cases': members}, None
    if source.get("adapter") == "titles":
        available = {c["id"]: c for c in source["cases"]}
        if len(available) != len(source["cases"]):
            raise ValueError("duplicate title case identity")
        if selected is not None and set(selected) - available.keys():
            raise ValueError("unknown title group requested")
        members = []
        for cid, case in available.items():
            if selected is not None and cid not in selected:
                continue
            if case["status"] != "valid":
                raise ValueError(f"title is not valid: {cid}")
            packet = case["evidence"]["packet"]
            if packet["packet"] != cid:
                raise ValueError("title packet identity mismatch")
            # Reuse the title adapter's exact-span validation and same-post deduplication.
            group = prepare_titles({"packets": [packet]}, "{NUMBERED_INSTANCES}", [cid])[0]
            posts = {i["note_id"]: i["text"] for i in packet["instances"]}
            for mask in group["sources"]:
                members.append(dict(id=f"{cid}-{mask['instance']}", node_id=cid,
                                    node_title=case["parsed"]["title"], note_id=mask["note_id"],
                                    text=posts[mask["note_id"]], mask_ids=mask["source_instances"],
                                    byte_spans=mask["byte_spans"]))
        source, selected = {"cases": members}, None
    cases, nodes, posts, ids = [], {}, {}, set()
    for item in source["cases"]:
        engine._expect_fields(
            item,
            "prominence case",
            {
                "id",
                "node_id",
                "node_title",
                "note_id",
                "text",
                "mask_ids",
                "byte_spans",
            },
        )
        for field in ("id", "node_id", "node_title", "note_id", "text"):
            engine._expect_string(item[field], field)
        if item["id"] in ids:
            raise ValueError("duplicate case identity")
        ids.add(item["id"])
        mask_ids = engine._validate_string_array(
            item["mask_ids"], "mask_ids", allow_empty=False
        )
        if len(set(mask_ids)) != len(mask_ids):
            raise ValueError("duplicate mask IDs")
        for lookup, key, value in (
            (nodes, item["node_id"], item["node_title"]),
            (posts, item["note_id"], item["text"]),
        ):
            if key in lookup and lookup[key] != value:
                raise ValueError("conflicting node title or source post")
            lookup[key] = value
        raw, cursor, marked, fragments = item["text"].encode("utf-8"), 0, [], []
        spans = item["byte_spans"]
        if not isinstance(spans, list) or not spans:
            raise ValueError("prominence requires a nonempty saved mask")
        for span in spans:
            if (
                not isinstance(span, list)
                or len(span) != 2
                or any(type(x) is not int for x in span)
                or not cursor <= span[0] < span[1] <= len(raw)
            ):
                raise ValueError("invalid prominence mask byte spans")
            start, end = span
            fragment = raw[start:end].decode("utf-8")
            marked.extend((raw[cursor:start].decode("utf-8"), "⟦", fragment, "⟧"))
            fragments.append(fragment)
            cursor = end
        marked.append(raw[cursor:].decode("utf-8"))
        payload = {"mask": fragments, "marked_post": "".join(marked)}
        cases.append(
            {
                "id": item["id"],
                "evidence": item,
                "inputs": {"INPUT_JSON": json.dumps(payload, ensure_ascii=False)},
            }
        )
    if selected is not None:
        if set(selected) - ids:
            raise ValueError("unknown case requested")
        cases = [c for c in cases if c["id"] in selected]
    if combine_masks:
        posts = {}
        for case in cases:
            e = case['evidence']
            key = e['node_id'], e['note_id']
            combined = posts.setdefault(key, dict(e, id='P' + digest(key)[:24],
                                                   mask_ids=[], byte_spans=[]))
            combined['mask_ids'].extend(e['mask_ids'])
            combined['byte_spans'].extend(e['byte_spans'])
        for combined in posts.values():
            combined['mask_ids'] = list(dict.fromkeys(combined['mask_ids']))
            combined['byte_spans'] = union_spans(combined['byte_spans'])
        return prepare_prominence({'cases': list(posts.values())})
    return cases


def prepare_context_prominence(source, basis='context'):
    """Prominence inputs from a saved context, SP subject or node title and post."""
    if basis not in ('context', 'subject', 'node_title'):
        raise ValueError('prominence_basis must be context, subject or node_title')
    fields = ('id', 'node_id', 'node_title', 'note_id', 'text', 'mask_ids', 'byte_spans')
    cases = []
    for evidence in source['cases']:
        identity = 'subject_id' if 'subject_id' in evidence else 'subject_number'
        if identity == 'subject_id':
            engine._expect_fields(evidence, 'saved subject context',
                {'id', 'node_id', 'node_title', 'note_id', 'text',
                 'subject_id', 'subject', 'context', 'source'})
            for key in ('id', 'node_id', 'subject_id'):
                engine._expect_identifier(evidence[key], key)
            for key in ('node_title', 'note_id', 'text'):
                engine._expect_string(evidence[key], key)
                if not evidence[key].strip():
                    raise ValueError(f'empty saved context field: {key}')
            case = dict(id=evidence['id'], evidence=dict(evidence))
        else:
            case = prepare_prominence({'cases': [{k: evidence[k] for k in fields}]})[0]
        for key in (identity, 'subject', 'context'):
            engine._expect_string(evidence[key], key)
            if not evidence[key].strip():
                raise ValueError(f'empty subject context field: {key}')
        case['evidence'] = dict(case['evidence'], **{
            k: evidence[k] for k in (identity, 'subject', 'context')})
        if 'source' in evidence:
            case['evidence']['source'] = evidence['source']
        case['inputs'] = {'INPUT_JSON': json.dumps(
            {basis: evidence[basis], 'post': evidence['text']}, ensure_ascii=False)}
        cases.append(case)
    return cases


def prepare_subject_contexts(source, selected=None, basis='context'):
    """Select exact saved SP entries belonging directly to the specified node."""
    posts = source['subjects']['notes']
    by_id = {p['note_id']: p for p in posts}
    if len(by_id) != len(posts):
        raise ValueError('duplicate source post identity')
    selections = source.get('selections')
    if selections and any('subject_id' in s for s in selections):
        # Explicit saved SP entries can test existing titles without a new
        # hierarchy build or MP generation. They are diagnostic assignments,
        # not members added to the preserved hierarchy.
        nodes = source['hierarchy']['graph']['nodes']
        titles = {n['group']: n['title'] for n in nodes}
        if len(titles) != len(nodes):
            raise ValueError('duplicate hierarchy node identity')
        cases, ids = [], set()
        for selection in selections:
            engine._expect_fields(selection, 'saved subject selection',
                {'id', 'node_id', 'note_id', 'subject_id'})
            cid = engine._expect_identifier(selection['id'], 'case.id')
            if cid in ids:
                raise ValueError('duplicate context case identity')
            ids.add(cid)
            post = by_id.get(selection['note_id'])
            matches = [s for s in post['subjects']
                       if s.get('id') == selection['subject_id']] if post else []
            if len(matches) != 1:
                raise ValueError('unknown or duplicate saved subject')
            if selection['node_id'] not in titles:
                raise ValueError('unknown context hierarchy node')
            subject = matches[0]
            cases.append(dict(selection, node_title=titles[selection['node_id']],
                text=post['text'], subject=subject['subject'], context=subject['context'],
                source=source['source']))
        if selected is not None:
            if set(selected) - ids:
                raise ValueError('unknown subject context case requested')
            cases = [c for c in cases if c['id'] in selected]
        return prepare_context_prominence({'cases': cases}, basis)
    members = prepare_prominence(source['hierarchy'])
    if 'nodes' in source:
        nodes = engine._validate_string_array(source['nodes'], 'nodes', allow_empty=False)
        if len(nodes) != len(set(nodes)):
            raise ValueError('duplicate subject context node')
        if set(nodes) - {m['evidence']['node_id'] for m in members}:
            raise ValueError('unknown subject context node or no direct members')
        selections, seen = [], set()
        for member in members:
            e = member['evidence']
            if e['node_id'] not in nodes:
                continue
            post = by_id.get(e['note_id'])
            subjects = [s for s in post['subjects']
                        if s['byte_spans'] == e['byte_spans']] if post else []
            if not subjects:
                raise ValueError('direct hierarchy member has no saved SP context')
            for subject in subjects:
                key = (e['node_id'], e['note_id'], subject['number'])
                if key not in seen:
                    seen.add(key)
                    selections.append(dict(id='context-' + digest(key)[:24],
                        node_id=e['node_id'], note_id=e['note_id'], number=subject['number']))
    cases, ids = [], set()
    for selection in selections:
        engine._expect_fields(selection, 'subject context selection',
                              {'id', 'node_id', 'note_id', 'number'})
        cid = engine._expect_identifier(selection['id'], 'case.id')
        if cid in ids:
            raise ValueError('duplicate context case identity')
        ids.add(cid)
        if selection['note_id'] not in by_id:
            raise ValueError('unknown subject context post')
        post = by_id[selection['note_id']]
        subjects = [s for s in post['subjects'] if s['number'] == selection['number']]
        if len(subjects) != 1:
            raise ValueError('unknown or duplicate subject number')
        subject = subjects[0]
        matching = [m['evidence'] for m in members
                    if m['evidence']['node_id'] == selection['node_id']
                    and m['evidence']['note_id'] == selection['note_id']
                    and m['evidence']['byte_spans'] == subject['byte_spans']]
        if not matching or any(m['text'] != post['text'] for m in matching):
            raise ValueError('SP context is not a direct hierarchy member')
        raw = post['text'].encode()
        if [raw[a:b].decode() for a,b in subject['byte_spans']] != subject['fragments']:
            raise ValueError('SP context mask differs from source post')
        evidence = dict(matching[0], id=cid, subject_number=subject['number'],
                        subject=subject['subject'], context=subject['context'],
                        source=source['source'])
        evidence['mask_ids'] = list(dict.fromkeys(mid for m in matching for mid in m['mask_ids']))
        if selected is None or cid in selected:
            cases.append(evidence)
    if selected is not None and set(selected) - ids:
        raise ValueError('unknown subject context case requested')
    return prepare_context_prominence({'cases': cases}, basis)


def prepare_posts(source, selected=None):
    """Use complete saved posts as inputs, keeping extraction data out of prompts."""
    if type(source.get('schema_version')) is not int or source['schema_version'] != 1:
        raise ValueError('expected posts schema_version 1')
    if not isinstance(source.get('notes'), list):
        raise ValueError('posts require a notes array')
    cases, note_ids, identifiers = [], set(), set()
    for note in source['notes']:
        note_id = engine._expect_string(note['note_id'], 'note_id')
        text = engine._expect_string(note['text'], 'post text')
        origin = note.get('origin', {})
        if not isinstance(origin, dict):
            raise ValueError('post origin must be an object')
        identifier = engine._expect_identifier(origin.get('prompt_id', note_id), 'post identity')
        if note_id in note_ids or identifier in identifiers:
            raise ValueError('duplicate post identity')
        note_ids.add(note_id)
        identifiers.add(identifier)
        cases.append(dict(id=identifier, inputs={'POST': text},
                          evidence=dict(note_id=note_id, text=text, origin=origin)))
    if selected is not None:
        if set(selected) - identifiers:
            raise ValueError('unknown post requested')
        cases = [case for case in cases if case['id'] in selected]
    return cases


def validate_node_description(value, node_id=None, node_title=None):
    """Validate saved meaning and preserve the exact existing node identity."""
    if not isinstance(value, dict) or set(value) != {'node_id', 'node_title', 'description'}:
        raise ValueError('expected exact node_id, node_title and description fields')
    engine._expect_identifier(value['node_id'], 'node_id')
    for key in ('node_title', 'description'):
        engine._expect_string(value[key], key)
        if not value[key].strip():
            raise ValueError(f'empty node description {key}')
    if len(value['description']) > 1200:
        raise ValueError('node description exceeds 1200 characters')
    if node_id is not None and value['node_id'] != node_id:
        raise ValueError('node description identity differs')
    if node_title is not None and value['node_title'] != node_title:
        raise ValueError('node description title differs')
    return value


def validate_node_sorting(value):
    """Validate a direct sorting judgment without prominence allocations."""
    if (not isinstance(value, dict) or set(value) != {'sorting_score', 'reason'}
            or type(value['sorting_score']) is not int or not 0 <= value['sorting_score'] <= 100
            or not isinstance(value['reason'], str) or not value['reason'].strip()):
        raise ValueError('expected integer sorting_score from 0 through 100 and nonempty reason')
    return value


def prepare_node_descriptions(source, selected=None):
    """Bound exact complete-post context without changing saved node membership."""
    prepare_titles(source['source_packets'], '{NUMBERED_INSTANCES}', [])
    packets = {p['packet']: p for p in source['source_packets']['packets']}
    nodes = source['hierarchy']['graph']['nodes']
    by_id = {}
    for node in nodes:
        nid = engine._expect_identifier(node['group'], 'node_id')
        if nid in by_id:
            raise ValueError('duplicate hierarchy node identity')
        engine._expect_string(node['title'], 'node_title')
        if not node['title'].strip():
            raise ValueError('empty hierarchy node title')
        by_id[nid] = node
    requested = source.get('nodes', list(by_id))
    engine._validate_string_array(requested, 'nodes', allow_empty=False)
    if len(set(requested)) != len(requested) or set(requested) - set(by_id):
        raise ValueError('duplicate or unknown description node requested')
    if selected is not None:
        if set(selected) - set(requested):
            raise ValueError('unknown description case requested')
        requested = [nid for nid in requested if nid in selected]
    cases = []
    for nid in requested:
        node = by_id[nid]
        packet_ids = [nid] if nid in packets else node.get('source_group_ids', [nid])
        engine._validate_string_array(packet_ids, 'source_group_ids', allow_empty=False)
        if len(packet_ids) != len(set(packet_ids)) or set(packet_ids) - set(packets):
            raise ValueError(f'missing or duplicate source packets for node: {nid}')
        if 'sources' in node:
            packet_masks = {(item['note_id'], tuple(map(tuple, item['byte_spans'])))
                            for pid in packet_ids for item in packets[pid]['instances']}
            graph_masks = {(item['note_id'], tuple(map(tuple, item['byte_spans'])))
                           for item in node['sources']}
            if packet_masks != graph_masks:
                raise ValueError(f'node description source masks differ from hierarchy: {nid}')
        posts, masks = {}, {}
        for pid in packet_ids:
            for item in packets[pid]['instances']:
                note_id = engine._expect_identifier(item['note_id'], 'note_id')
                posts[note_id] = item['text']
                key = tuple(tuple(span) for span in item['byte_spans'])
                masks.setdefault(note_id, {})[key] = item['fragments']
        payload = dict(node_id=nid, node_title=node['title'], instances=[])
        selected_ids, skipped = [], []
        for note_id in sorted(posts):
            instance = dict(note_id=note_id, post=posts[note_id],
                            masks=[fragments for _, fragments in sorted(masks[note_id].items())])
            candidate = {**payload, 'instances': payload['instances'] + [instance]}
            reason = ('post_limit' if len(selected_ids) >= 8 else
                      'character_limit' if len(json.dumps(candidate, ensure_ascii=False)) > 12000 else None)
            if reason:
                skipped.append(dict(note_id=note_id, reason=reason))
            else:
                payload = candidate
                selected_ids.append(note_id)
        if not selected_ids:
            raise ValueError(f'no complete posts fit node description input: {nid}')
        rendered = json.dumps(payload, ensure_ascii=False)
        cases.append(dict(id=nid, inputs={'INPUT_JSON': rendered}, evidence=dict(
            node_id=nid, node_title=node['title'], node=node,
            packets=[packets[pid] for pid in packet_ids], source=source['source'],
            candidate_note_ids=sorted(posts), selected_note_ids=selected_ids,
            skipped_note_ids=[item['note_id'] for item in skipped], skipped_posts=skipped,
            input_characters=len(rendered))))
    return cases


def attach_node_descriptions(cases, source):
    descriptions = source['descriptions']
    engine._expect_fields(descriptions, 'collected node descriptions', {'schema_version', 'nodes'})
    if type(descriptions['schema_version']) is not int or descriptions['schema_version'] != 1:
        raise ValueError('expected collected node descriptions schema_version 1')
    if not isinstance(descriptions['nodes'], list):
        raise ValueError('node descriptions must be an array')
    by_id = {}
    for record in descriptions['nodes']:
        validate_node_description(record)
        if record['node_id'] in by_id:
            raise ValueError('duplicate node description identity')
        by_id[record['node_id']] = record
    for case in cases:
        evidence = case['evidence']
        record = by_id.get(evidence['node_id'])
        if record is None:
            raise ValueError(f'missing node description: {evidence["node_id"]}')
        validate_node_description(record, evidence['node_id'], evidence['node_title'])
        payload = json.loads(case['inputs']['INPUT_JSON'])
        payload['node_description'] = record['description']
        case['inputs']['INPUT_JSON'] = json.dumps(payload, ensure_ascii=False)
        evidence.update(node_description=record['description'], node_description_record=record,
                        description_source=source['source']['descriptions'])


def prepare(dataset, source, template):
    adapter = dataset["adapter"]
    if "select" in dataset:
        selected = engine._validate_string_array(
            dataset["select"], "dataset.select", allow_empty=False
        )
        if len(set(selected)) != len(selected):
            raise ValueError("duplicate selection IDs")
    if adapter != "masks" and "mask_format" in dataset:
        raise ValueError("mask_format is only supported by the masks adapter")
    if 'combine_masks' in dataset:
        if adapter != 'prominence' or type(dataset['combine_masks']) is not bool:
            raise ValueError('combine_masks requires the prominence adapter and a boolean')
    if 'prominence_basis' in dataset and adapter != 'subject_contexts':
        raise ValueError('prominence_basis requires the subject_contexts adapter')
    if adapter == "generic":
        cases = source["cases"]
        for case in cases:
            engine._expect_fields(
                case, "case", {"id", "inputs"} | ({"evidence", "mechanical"} & case.keys())
            )
        if len({c["id"] for c in cases}) != len(cases):
            raise ValueError("duplicate case identity")
        if "select" in dataset:
            if set(dataset["select"]) - {c["id"] for c in cases}:
                raise ValueError("unknown case requested")
            cases = [c for c in cases if c["id"] in dataset["select"]]
    elif adapter in {"posts", "subjects"}:
        cases = prepare_posts(source, dataset.get('select'))
    elif adapter == "prominence":
        cases = prepare_prominence(source, dataset.get("select"), dataset.get('combine_masks', False))
    elif adapter == "subject_pairs":
        cases = prepare_subject_pairs(source, dataset.get("select"))
    elif adapter == 'hierarchy_construction':
        cases = prepare_hierarchy_construction(source, dataset.get('select'))
    elif adapter == 'parent_candidates':
        cases = prepare_parent_candidates(source, dataset.get('select'))
    elif adapter in {'subject_contexts', 'node_sorting'}:
        basis = 'node_title' if adapter == 'node_sorting' else dataset.get('prominence_basis', 'context')
        cases = prepare_subject_contexts(source, dataset.get('select'),
                                         basis)
        if 'descriptions' in source:
            if basis != 'node_title':
                raise ValueError('node descriptions require node_title prominence basis')
            attach_node_descriptions(cases, source)
    elif adapter == 'node_descriptions':
        cases = prepare_node_descriptions(source, dataset.get('select'))
    elif adapter == "titles":
        groups = prepare_titles(
            source, "{NUMBERED_INSTANCES}", dataset.get("select", [])
        )
        packets = {p["packet"]: p for p in source["packets"]}
        cases = [
            {
                "id": g["group"],
                "inputs": {"NUMBERED_INSTANCES": g["prompt"]},
                "evidence": {**g, "packet": packets[g["group"]]},
            }
            for g in groups
        ]
    elif adapter == "grouped_masks":
        cases = grouped_masks.prepare(source, dataset.get("select"))
    elif adapter == "masks":
        format_ = dataset.get("mask_format", "word_positions")
        items, _ = engine.prepare_mask_inputs(
            source, template, format_, dataset.get("select")
        )
        cases = []
        occurrences = {}
        for item in items:
            inputs = {"POST": item["note"], "SUBJECT": item["subject"]}
            if format_ == "word_positions":
                inputs["INDEXED_POST"] = engine._position_decoder().index_post(
                    item["note"]
                )
            # Independent of batch order, while changed text still fails input pairing.
            identifier = "M" + digest([item["note_id"], item["subject"]])[:24]
            occurrences[identifier] = occurrences.get(identifier, 0) + 1
            if occurrences[identifier] > 1:
                identifier += "-" + str(occurrences[identifier])
            cases.append({"id": identifier, "inputs": inputs, "evidence": item})
    else:
        raise ValueError(f"unknown dataset adapter: {adapter}")
    if not cases:
        raise ValueError("dataset contains no cases")
    ids = set()
    for case in cases:
        identifier = engine._expect_identifier(case["id"], "case.id")
        if identifier in ids:
            raise ValueError(f"duplicate case identity: {identifier}")
        ids.add(identifier)
        case["prompt"] = render(template, case["inputs"])
        case["input_sha256"] = digest(case["inputs"])
    return cases


def validate(dataset, case, raw, schema):
    """Check output mechanics, never semantic correctness."""
    adapter = dataset["adapter"]
    result = {"status": "valid", "output": raw}
    if adapter == 'canonical_consolidation':
        from .canonical_traversal import validate_consolidation
        result['parsed'] = validate_consolidation(raw, json.loads(case['inputs']['INPUT_JSON']))
    if adapter == 'canonical_consolidation_pairs':
        from . import hierarchy_node_pairs
        meaning = json.loads(case['inputs']['INPUT_JSON'])['local']['meaning']
        diagnostics = isinstance(schema, dict) and 'questions' in schema.get('properties', {})
        result['parsed'] = hierarchy_node_pairs.validate(raw, diagnostics=diagnostics, meaning=meaning)
        if result['parsed']['meaning'] != meaning:
            raise ValueError('Compare answer must copy the fixed local meaning exactly')
    if adapter == 'canonical_shaping_nomination':
        value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        engine._expect_fields(value, 'shaping nomination output', {'candidate_id', 'children', 'reason'})
        payload = json.loads(case['inputs']['INPUT_JSON'])
        offered = {row['id']: row for row in payload['local_entries']}
        children = engine._validate_string_array(value['children'], 'children', allow_empty=True)
        engine._expect_string(value['reason'], 'nomination reason')
        selected = value['candidate_id']
        if selected is None:
            if children:
                raise ValueError('a null nomination cannot select children')
        elif (not isinstance(selected, str) or selected not in offered
                or len(set(children)) != len(children) or not 2 <= len(children) <= payload['max_choices']
                or len(children) >= len(payload['siblings'])
                or set(children) - set(offered[selected]['eligible_siblings'])):
            raise ValueError('invalid, duplicate or unsupplied shaping nominee or children')
        result['parsed'] = value
    if adapter == 'compare_student_inputs':
        from . import compare_student_inputs
        answer = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        meaning = json.loads(case['inputs']['INPUT_JSON'])['local']['meaning']
        result['parsed'] = compare_student_inputs.validate_answer(answer, meaning)
    if adapter in {'hierarchy_node_pairs', 'hierarchy_local_nodes'}:
        try:
            from . import hierarchy_node_pairs as node_pairs
        except ImportError:
            import hierarchy_node_pairs as node_pairs
        if adapter == 'hierarchy_local_nodes':
            post = json.loads(case['inputs']['INPUT_JSON'])['local']['post']
            properties = schema.get('properties', {}) if isinstance(schema, dict) else {}
            diagnostic = 'evidence' in properties
            ambiguity_diagnostics = bool({'ambiguities', 'resolutions'} & properties.keys())
            result['parsed'] = node_pairs.validate_meaning(
                raw, post=post, diagnostic=diagnostic, ambiguity_diagnostics=ambiguity_diagnostics)
        else:
            properties = schema.get('properties', {}) if isinstance(schema, dict) else {}
            diagnostics = bool({'questions', 'answers'} & properties.keys())
            payload = json.loads(case['inputs']['INPUT_JSON'])
            symmetric = set(payload) == {'A', 'B'}
            meaning = None if symmetric else payload['local'].get('meaning')
            result['parsed'] = node_pairs.validate(
                raw, diagnostics=diagnostics, meaning=meaning, symmetric=symmetric)
    if adapter == 'distillation_verdict':
        try:
            from . import distillation_verdict
        except ImportError:
            import distillation_verdict
        return distillation_verdict.validate(case, raw)
    if adapter == 'distillation_matching':
        try:
            from . import distillation_matching
        except ImportError:
            import distillation_matching
        return distillation_matching.validate(case, raw)
    if adapter == 'distillation_coverage_search':
        from . import distillation_coverage_search
        return distillation_coverage_search.validate(case, raw)
    if adapter == 'distillation_review_evaluation':
        from . import distillation_review_evaluation
        return distillation_review_evaluation.validate(case, raw)
    if adapter == 'distillation_review':
        try:
            from . import distillation_review
        except ImportError:
            import distillation_review
        return distillation_review.validate(case, raw)
    if adapter == 'node_sorting':
        result['parsed'] = validate_node_sorting(json.loads(
            raw, object_pairs_hook=engine._position_decoder().unique_object))
    if adapter == 'node_descriptions':
        value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        result['parsed'] = validate_node_description(value, case['evidence']['node_id'],
                                                    case['evidence']['node_title'])
    if adapter == 'bounded_parent_guides':
        try:
            from .parent_guide_workflow import validate_guides
        except ImportError:
            from parent_guide_workflow import validate_guides
        result['parsed'] = validate_guides(case, raw)
    if adapter in {'bounded_discovery', 'bounded_comparisons', 'bounded_parent_comparisons'}:
        try:
            from . import bounded_hierarchy_workflow as bounded
        except ImportError:
            import bounded_hierarchy_workflow as bounded
        validator = (bounded.validate_discovery if adapter == 'bounded_discovery'
                     else bounded.validate_comparisons)
        result['parsed'] = validator(case, raw)
    if adapter == "subjects":
        value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        hierarchy_inputs.validate_subjects(value)
        result["parsed"] = value
    if adapter == 'hierarchy_construction':
        value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        engine._expect_fields(value, 'construction proposals', {'equivalences', 'ancestors'})
        supplied = {n['id'] for n in json.loads(case['inputs']['CATALOGUE_JSON'])['nodes']}
        query = set(json.loads(case['inputs']['QUERY_JSON'])['nodes'])
        for field in ('equivalences', 'ancestors'):
            if not isinstance(value[field], list):
                raise ValueError('construction proposals must be arrays')
            seen = set()
            for proposal in value[field]:
                fields = {'nodes', 'reason'} if field == 'equivalences' else {'ancestor', 'descendant', 'reason'}
                engine._expect_fields(proposal, 'construction proposal', fields)
                ids = (engine._validate_string_array(proposal['nodes'], 'equivalent nodes', allow_empty=False)
                       if field == 'equivalences' else [proposal['ancestor'], proposal['descendant']])
                if (len(ids) < 2 or any(not isinstance(nid, str) or nid not in supplied for nid in ids)
                        or len(set(ids)) != len(ids) or not set(ids) & query
                        or not isinstance(proposal['reason'], str) or not proposal['reason'].strip()):
                    raise ValueError('invalid or unsupplied construction proposal')
                key = tuple(sorted(ids)) if field == 'equivalences' else tuple(ids)
                if key in seen:
                    raise ValueError('duplicate construction proposal')
                seen.add(key)
        result['parsed'] = value
    if adapter == 'parent_candidates':
        value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
        if not isinstance(value, dict) or set(value) != {'candidates'} or not isinstance(value['candidates'], list):
            raise ValueError('expected a parent candidate array')
        eligible = {c['id'] for c in json.loads(case['inputs']['INPUT_JSON'])['candidates']}
        seen = set()
        for candidate in value['candidates']:
            if (not isinstance(candidate, dict) or set(candidate) != {'id', 'reason'}
                    or not isinstance(candidate['id'], str) or candidate['id'] not in eligible
                    or candidate['id'] in seen or not isinstance(candidate['reason'], str)
                    or not candidate['reason'].strip()):
                raise ValueError('invalid, duplicate or unsupplied parent candidate')
            seen.add(candidate['id'])
        result['parsed'] = value
    if adapter == "grouped_masks":
        result.update(grouped_masks.validate(case, raw))
    if adapter in {'prominence', 'subject_contexts', 'hierarchy_prominence'}:
        value = json.loads(
            raw, object_pairs_hook=engine._position_decoder().unique_object
        )
        if (
            not isinstance(value, dict)
            or (schema is None and adapter == 'prominence' and set(value) != {"prominence"})
            or type(value.get("prominence")) is not int
            or not 0 <= value["prominence"] <= 100
        ):
            raise ValueError("expected one integer prominence score from 0 through 100")
        result["parsed"] = value
        if adapter in {'subject_contexts', 'hierarchy_prominence'}:
            if set(value) != {'prominence', 'missing_meaning', 'allocation'} or not isinstance(value['missing_meaning'], str):
                raise ValueError('expected context prominence diagnostics')
            allocation = value['allocation']
            if not isinstance(allocation, list) or not allocation:
                raise ValueError('expected nonempty context prominence allocation')
            for entry in allocation:
                if (not isinstance(entry, dict) or set(entry) != {'meaning', 'points', 'represented', 'missing'}
                        or not isinstance(entry['meaning'], str)
                        or any(type(entry[k]) is not int or not 0 <= entry[k] <= 100
                               for k in ('points', 'represented', 'missing'))
                        or entry['represented'] + entry['missing'] != entry['points']):
                    raise ValueError('invalid context prominence allocation')
            if (sum(e['points'] for e in allocation) != 100
                    or sum(e['represented'] for e in allocation) != value['prominence']):
                raise ValueError('context prominence allocation totals differ')
    if schema is not None or adapter == "titles":
        result["parsed"] = json.loads(raw)
    if adapter == "titles":
        value = result["parsed"]
        if (
            not isinstance(value, dict)
            or set(value) != {"title"}
            or not isinstance(value["title"], str)
            or not value["title"].strip()
        ):
            raise ValueError("expected a nonempty JSON title string")
    if adapter == "masks":
        format_ = dataset.get("mask_format", "word_positions")
        fragments, mapped, ambiguous = engine._map_mask_fragments(
            raw, case["inputs"]["POST"], format_
        )
        result.update(
            status="valid" if fragments else "empty",
            fragments=mapped,
            ambiguous_occurrences=ambiguous,
        )
        if format_ == "word_positions":
            diagnostics, ranges = engine._position_decoder().decode(
                raw, case["inputs"]["POST"]
            )
            result.update(
                ranges=ranges,
                diagnostics={k: v for k, v in diagnostics.items() if k != "mask"},
            )
    return result


def is_flagged(case):
    """Current user decisions take precedence; an empty mask alone is not a failure."""
    reviews = [r for r in case["reviews"] if r["current"]]
    users = [r for r in reviews if r["role"] == "user" and r["verdict"] != "comment"]
    if users:
        return users[-1]["verdict"] in {"reject", "uncertain"}
    agents = [r for r in reviews if r["role"] == "agent"]
    return case["status"] not in {"valid", "empty"} or bool(
        agents and agents[-1]["verdict"] in {"reject", "uncertain"}
    )


def review_batch(plan, report, view=None):
    """Translate compatible cases to the existing UI; list all unsupported cases."""
    adapter = plan["dataset"]["adapter"]
    if view == "prominence":
        if adapter not in {"generic", "prominence"}:
            raise ValueError("prominence view requires generic or prominence inputs")
        fields = ("id", "node_id", "node_title", "note_id", "text", "mask_ids", "byte_spans")
        for case in report["cases"]:
            evidence = case.get("evidence", {})
            if any(key not in evidence for key in fields):
                raise ValueError(f"missing prominence evidence: {case['id']}")
            expected = prepare_prominence({"cases": [{key: evidence[key] for key in fields}]})[0]
            if (case["id"] != evidence["id"] or set(case["inputs"]) != {"INPUT_JSON"}
                    or json.loads(case["inputs"]["INPUT_JSON"]) !=
                    json.loads(expected["inputs"]["INPUT_JSON"])):
                raise ValueError(f"model input differs from prominence evidence: {case['id']}")
            if case["status"] == "valid":
                parsed = case.get("parsed")
                score = parsed.get("prominence") if isinstance(parsed, dict) else None
                if type(score) is not int or not 0 <= score <= 100:
                    raise ValueError(f"invalid prominence score: {case['id']}")
        return prominence_review_batch(plan, report), []
    if adapter == "prominence":
        return prominence_review_batch(plan, report), []
    if adapter not in {"titles", "masks"}:
        raise ValueError(
            "generic experiments use review --case, not a task-specific UI"
        )
    items, excluded = [], []
    for case in report["cases"]:
        if adapter == "titles" and case["status"] != "valid":
            excluded.append({"id": case["id"], "reason": case["status"]})
            continue
        if adapter == "titles":
            baseline = case["baseline"]
            items.append(
                {
                    "item_id": case["id"],
                    "candidate_title": case["parsed"]["title"],
                    "baseline_title": (
                        baseline.get("parsed", {}).get("title") if baseline else None
                    )
                    or "(no valid baseline)",
                    "instances": case["evidence"]["instances"],
                }
            )
        else:
            items.append(
                {
                    "item_id": case["id"],
                    "note_id": case["evidence"]["note_id"],
                    "subject": case["inputs"]["SUBJECT"],
                    "note": case["inputs"]["POST"],
                    "fragments": case["fragments"] if case["status"] == "valid" else [],
                }
            )
        assessments = [
            r for r in case["reviews"] if r["role"] == "agent" and r["current"]
        ]
        if assessments:
            latest = assessments[-1]
            items[-1]["assessment"] = f"Agent: {latest['verdict']}. {latest['comment']}"
        if adapter == "masks":
            items[-1]["details"] = "Generated mask; not semantically approved."
            if case["status"] != "valid":
                items[-1]["details"] = "\n\n".join(
                    str(value) for value in (
                        f"Result status: {case['status']}", case.get("error"),
                        case.get("output"),
                    ) if value
                )
                items[-1]["result_status"] = case["status"]
    batch = {
        "schema_version": 1,
        "batch_id": "experiment-" + digest(items)[:16],
    }
    if adapter == "titles":
        batch.update(
            candidate_version=plan["prompt"]["id"],
            baseline_version=plan.get("baseline_prompt_id") or "none",
        )
    # Keep Rust struct field order for review_state::value_sha256 compatibility.
    batch["items"] = items
    return batch, excluded


def prominence_comment_key(case):
    return digest({"id": case["id"], "prompt": case["prompt"], "output": case["output"]})


def prominence_comments(envelope):
    session = envelope["session"]
    checksum = hashlib.sha256(engine._ordered_json_bytes(session)[:-1]).hexdigest()
    if envelope.get("schema_version") != 1 or envelope.get("state_sha256") != checksum:
        raise ValueError("review comments failed their state hash")
    return session["comments"]


def prominence_review_batch(plan, report):
    """Full-post, single-mask cards; scores order masks, never aggregated posts."""
    groups = {}
    for case in report["cases"]:
        groups.setdefault(case["evidence"]["node_id"], []).append(case)
    notes = []
    for cases in groups.values():
        cases = sorted(
            cases,
            key=lambda c: (
                c["status"] != "valid",
                -c["parsed"]["prominence"] if c["status"] == "valid" else 0,
                c["id"],
            ),
        )
        scored = sum(c["status"] == "valid" for c in cases)
        for position, case in enumerate(cases, 1):
            evidence = case["evidence"]
            valid = case["status"] == "valid"
            score = case["parsed"]["prominence"] if valid else None
            place = (
                f"{position}/{scored} · score {score}"
                if valid
                else f"unranked · {case['status']}"
            )
            comments = [
                "One mask per entry; repeated posts are intentional. Equal scores are tied."
            ]
            if case.get("error"):
                comments.append(str(case["error"]))
            for review in case["reviews"]:
                if review["current"] and review["verdict"] != "comment":
                    comments.append(
                        f"{review['role']}: {review['verdict']}. {review['comment']}"
                    )
            baseline = case.get("baseline")
            if (
                baseline
                and baseline.get("status") == "valid"
                and isinstance(baseline.get("parsed"), dict)
                and type(baseline["parsed"].get("prominence")) is int
            ):
                comments.append(
                    f"Baseline prominence: {baseline['parsed']['prominence']}"
                )
            notes.append(
                {
                    "id": case["id"],
                    "title": (
                        f"{evidence['node_title']} [{evidence['node_id']}] · {place} · "
                        f"{evidence['note_id']} · {', '.join(evidence['mask_ids'])}"
                    ),
                    "text": json.loads(case["inputs"]["INPUT_JSON"])["marked_post"],
                    "model_input": case["prompt"],
                    "results": [
                        {
                            "model": plan["prompt"]["id"],
                            "comment_key": prominence_comment_key(case),
                            "output": (
                                f"Prominence: {score} / 100"
                                if valid
                                else case.get("output") or f"No output: {case['status']}"
                            ),
                            "comment": "\n".join(comments),
                        }
                    ],
                }
            )
    return {
        "schema_version": 1,
        "title": f"{plan['prompt']['id']} · prominence prompt evaluation · one mask per post entry",
        "notes": notes,
    }


def ui_reviews(binding, batch, envelope):
    """Read the existing UI's hashed session, never synthesize human decisions."""

    def ui_hash(value):
        # serde_json::to_vec preserves struct/BTreeMap order and emits no newline.
        return hashlib.sha256(engine._ordered_json_bytes(value)[:-1]).hexdigest()

    session = envelope["session"]
    if (
        envelope.get("schema_version") != 1
        or envelope.get("state_sha256") != ui_hash(session)
        or session.get("batch_sha256") != ui_hash(batch)
        or digest(batch) != binding["batch_sha256"]
    ):
        raise ValueError("review UI session or batch hash differs")
    result = []
    for identifier, decision in session["decisions"].items():
        if decision["outcome"] is None:
            continue
        result.append(
            {
                "case_id": identifier,
                "role": "user",
                "source": binding["session_path"],
                "verdict": {
                    "approved": "accept",
                    "rejected": "reject",
                    "skipped": "uncertain",
                }[decision["outcome"]],
                "comment": decision["comment"],
                **binding["cases"][identifier],
            }
        )
    return result
