"""Project the recorded scientific JSON layouts of legacy title studies.

This module reads no files. Callers supply verified source hashes and normalized
saved answers. The closed field vocabulary describes the recorded scientific
formats; additions require review instead of silently disappearing from exports.
"""
import hashlib
import math
import posixpath
import re


_ROOT_FIELDS = {
    'final_comparison': '''schema_version experiment model reasoning_effort source_packets
        historical_comparison results usage_totals conclusion prompt_version comparisons observations
        usage frozen_version groups limitations next_step baseline_version candidate_version
        user_decisions_prefilled assessment_source summary assessment_author counts rows
        baseline trials_per_node limitation candidate trials_per_version_per_node run
        conditions trials unchanged verification comparison_limit''',
    'recorded_assessments': '''schema_version experiment counts review_contract results
        independent_review user_review main_counts independent_counts adjudication review
        main summary user_decisions auditor input assessments conclusion source_session
        source_session_sha256 raw_saved_review chat_clarification chat_confirmation scope
        reviewer status reviews judgments main_reconciliation source source_review
        candidate_version purpose items uncertain_review review_scope groups context_checks
        disagreement_resolutions method reviewers integrity_review user_decisions_prefilled
        reasoning review_limit context response_summary main_adjudication inputs isolation
        original_summary clarification relation_to_main''',
    'recorded_review_comments': 'schema_version batch_sha256 comments',
    'final_findings': '''schema_version experiment prompt_version evaluation_status groups
        status results conclusion scope limits next usage total_input_plus_output usage_scope
        tracking_card plane_update summary target controls unchanged guidance
        what_this_establishes what_this_does_not_establish review_items known_limitations
        user_review_source title_input_constraint sentence_removal_diagnostic
        neutral_explanation_diagnostic source_context_candidate name_interpretation_candidate
        containment_followup review_command all_titles_command references question
        recommendation preserved observations interpretation user_review pairs''',
    'final_title_selection': '''schema_version run_id prompt_version status note user_review
        counts groups outputs''',
    'final_selection_audit': '''schema_version source_packet_inventory prior_probe_directories
        prior_configs prior_groups prior_instance_occurrences prior_distinct_note_span_masks
        selected_groups selected_masks selected_distinct_masks prior_group_overlap
        prior_exact_mask_overlap prior_fragment_array_overlap selected_notes
        previously_seen_notes new_notes selection_auditor limitation''',
    'recorded_assessment_reconciliation': '''schema_version scope main independent agreements
        disagreements final_authority main_review independent_review independent_findings
        other_independently_reviewed_outputs limits''',
    'final_answer_aggregate': 'schema_version group instances responses',
}
_ROOT_FIELDS = {key: set(value.split()) for key, value in _ROOT_FIELDS.items()}
_PARAMETERS = set('''
    schema_version experiment accepted_groups added_sentence approval approval_boundary approved_draft
    assessment base_commit base_prompt base_prompt_sha256 base_prompt_version base_version baseline
    baseline_directory baseline_model baseline_prompt baseline_prompt_version baseline_reasoning_effort
    baseline_user_review baseline_version calls calls_per_node calls_per_variant_per_group
    calls_per_version_per_node candidate candidate_prompt candidate_version canonical_groups change changed
    comparison comparison_limit competing_explanations conditions config_order control controls decision
    deduplication evaluation evidence excluded_groups existing_title_policy existing_v15_groups finding
    frozen frozen_version generation group group_approval group_approval_evidence group_roles groups
    groups_checked guidance guidance_scope hypotheses hypothesis input_contract input_format interpretation
    limitation limitations limits max_concurrent max_concurrent_calls maximum_concurrent_calls model
    new_calls new_groups new_trials_per_missing_group new_v15_groups next next_decision nodes novelty
    only_change other_changes pairs policy preceding_user_approval preserve prior_experiments prior_inputs
    prompt prompt_path prompt_registry_sha256 prompt_sha256 prompt_source prompt_template prompt_version
    prompts purpose question reason reasoning_effort registry_path removed removed_sentence repetitions
    repetitions_per_condition repetitions_per_condition_per_group rerun_groups result reuse_policy reused
    review review_standard roles run run_id sample_limits scope scope_limits selection source_commit
    source_experiment source_packets source_packets_path source_review source_review_sha256 source_sha256
    source_titles status submission_order task total_calls total_fresh_calls total_groups total_planned_calls
    trials trials_per_condition_per_group trials_per_group trials_per_prompt trials_per_version_per_group
    trials_per_version_per_node unchanged user_review_source variable variants version withdrawn_version
    wrapper_sha256
'''.split())
_ROOT_FIELDS['study_parameters'] = _PARAMETERS
_PARAMETER_RUNTIME = set('execution billing budget costs codex_home codex_binary jobs'.split())

_FIELDS = set('''
    a a_id a_meaning accept accepted accepted_by_assistant_or_prior_user accepted_outputs
    adjudication agent agreements all_comments_empty alternative ambiguous analysis approved_count
    assessment assessment_author assessment_source assessment_summary assessments assistant
    assistant_accepted assistant_analysis assistant_assessment assistant_explanation assistant_judgment
    assistant_rejected assistant_uncertain attempt auditor awaiting_user_resolution b b_id b_meaning
    baseline baseline_verdict baseline_version batch_sha256 byte_spans cache_write_input_tokens
    cached_input_tokens candidate candidate_verdict candidate_version chat_clarification
    chat_confirmation claim clarification clarity clear_errors coffee_preparation Coffeechain comment
    comments commercial_chain_titles comparison_limit comparisons concerns conclusion concurrency_caveat
    condition conditions config containment_followup context context_checks controls count counts
    current_input decisions description disagreement_resolutions disagreements distinct_uncertain_titles
    dog_titles duplicates_removed elapsed_seconds evaluation_status evidence exact_source_hash_markers
    experiment explicit_commercial_errors explicitly_user_approved_reused explicitly_user_approved_total
    final_authority final_output_sha256 finding flat_fragments food fragments frozen_version group groups
    guidance historical_a historical_b historical_comparison historical_title_only historical_v11
    historical_v12 historical_v20_title id ids implication independent independent_assessment
    independent_audit independent_counts independent_findings independent_reason independent_review
    independent_verdict input input_plus_output_tokens input_tokens inputs instance instances
    integrity_review interpretation isolation item_id items judgment judgments known_limitations
    limitation limitations limits main main_adjudication main_correction main_counts
    main_reconciliation main_resolution main_review manifest_sha256 mask_check masks meaning method model
    model_and_wrapper_match_baseline model_label name_interpretation_candidate neutral_explanation_diagnostic
    new new_calls new_notes new_user_decisions next next_step no_prior_artifact_changes no_tools_web_or_schema
    node note note_id notes observation observations one_unnumbered_title
    only_two_generation_input_characters_changed origin original original_masks original_summary
    other_independently_reviewed_outputs other_rejected_item other_rejection_reason outcome output_path
    output_tokens outputs pair pairs path preserved previous previously_seen_notes prior_configs
    prior_distinct_note_span_masks prior_exact_mask_overlap prior_experiment prior_fragment_array_overlap
    prior_group_overlap prior_groups prior_instance_occurrences prior_probe_directories prompt prompt_id
    prompt_sha256 prompt_version purpose question rationale raw_response_and_prompt_hashes_match raw_result
    raw_result_path raw_saved_review raw_title reason reasoning reasoning_effort reasoning_output_tokens
    recommendation references reject rejected relation_to_main relationship response response_summary
    responses restored_hashtags result result_path results reused review review_contract review_items
    review_limit review_scope reviewer reviewer_extra_suggestion reviewers reviews role rows run run_id
    same_note_duplicates_removed schema_version scope segment selected_distinct_masks selected_groups
    selected_masks selected_notes selection_auditor selection_reason sentence_removal_diagnostic session
    session_file_sha256 session_path session_sha256 sha256 source source_context_candidate source_instances
    source_packet_inventory source_packets source_review source_session source_session_sha256
    source_vector_ids sources state_sha256 status successful_first_attempts summary surface_for_review
    target text_form_titles title title_input_constraint title_only total total_input_plus_output trial
    trials trials_per_node trials_per_version_per_node uncertain uncertain_outputs uncertain_review
    unchanged unique_threads unique_workspaces url usage usage_scope usage_totals use user_approval
    user_approved user_comment user_decision user_decisions user_decisions_prefilled user_feedback
    user_outcome user_quote user_reply user_review user_review_source vector_id verdict verification
    version versions what_this_does_not_establish what_this_establishes without_sentence wrapper_sha256
'''.split())
_FIELDS.update(_PARAMETERS)
_FIELDS.update('''alternative_result_path arm audit complete_groups_not_trimmed duplicate_fragments
    duplicate_masks_preserved duplicate_policy fragment_order fragment_separator fragment_template
    instance_separator instance_unit mask_instances no_prior_generated_titles_used_for_selection
    numbered_instance_template original_groups previous_exact_masks previously_tested_groups
    previously_used_unique_groups prior_probe_group_ids reasons selected_ids selected_previously_used_groups
    selection_rationale source_grouping_verdict source_notes unique_exact_masks unit
    untested_groups_before_this_run unused_count'''.split())
_RUNTIME = set('''thread_id workspace codex_home run_directory tracking_card plane_update
    review_command all_titles_command current_item'''.split())
_LINKS = set('''config result_path output_path raw_result_path alternative_result_path path source_session session_path
    source_packet_inventory source_review source_packets input inputs prior_probe_directories
    prompt_path prompt_source registry_path source_packets_path source_titles baseline_directory
    prior_experiments prior_inputs user_review_source approved_draft'''.split())
_STRICT_LINKS = set('''config result_path output_path raw_result_path alternative_result_path path
    source_session session_path'''.split())
_PROMPTS = set('''prompt base_prompt candidate_prompt baseline_prompt prompt_template
    fragment_template numbered_instance_template'''.split())
_TEXT = set('''title raw_title response prompt_id group node segment item_id note_id vector_id
    version prompt_version baseline_version candidate_version condition origin reason comment
    assessment_summary judgment relationship clarity a_meaning b_meaning'''.split())
_HEX = re.compile(r'[0-9a-f]{64}\Z')
_ITEM = re.compile(r'(?:[A-Za-z0-9_-]+-)?S[0-9a-f]{10}(?:[-_][A-Za-z0-9_-]+)*\Z')
_VERSION = re.compile(r'v\d+(?:_(?:historical|response|words|assessment|accepted))?\Z')
_AGENT = {
    'main assistant', 'assistant; not user decisions', 'main assistant, not user decisions',
    'main assistant; not user decisions', 'assistant semantic review, not user decisions',
}


def _portable(path):
    return (isinstance(path, str) and bool(path) and not path.startswith('/')
            and '\\' not in path and all(part not in ('', '.', '..') for part in path.split('/')))


def _dynamic(key):
    return bool(_ITEM.fullmatch(key) or _VERSION.fullmatch(key))


def _actor(value, role):
    if role == 'recorded_review_comments' or not isinstance(value, dict):
        return 'unknown'
    labels = [value.get(key) for key in ('assessment_author', 'assessment_source', 'reviewer', 'source')]
    roles = set()
    for label in labels:
        if not isinstance(label, str):
            continue
        normalized = label.strip().lower()
        if normalized in _AGENT:
            roles.add('agent')
        elif normalized == 'user':
            roles.add('user')
    if len(roles) > 1:
        raise ValueError('conflicting recorded actor roles')
    return next(iter(roles), 'unknown')


class _References:
    def __init__(self, source, answers, bindings):
        self.source, self.bindings = source, bindings
        self.suffixes, self.by_run, self.directories = {}, {}, set()
        for path, digest in bindings.items():
            if not _portable(path) or not isinstance(digest, str) or not _HEX.fullmatch(digest):
                raise ValueError('invalid portable source binding')
            parts = path.split('/')
            self.directories.update('/'.join(parts[:index]) for index in range(1, len(parts)))
            for index in range(len(parts)):
                self.suffixes.setdefault('/'.join(parts[index:]), set()).add(path)
        for answer in answers:
            path, output = answer.get('source_path'), answer.get('output')
            if not _portable(path) or not _portable(answer.get('call_id')) or not isinstance(output, str):
                raise ValueError('invalid normalized saved answer')
            if hashlib.sha256(output.encode()).hexdigest() != answer.get('output_sha256'):
                raise ValueError('saved answer hash mismatch')
            self.by_run.setdefault(posixpath.dirname(path), []).append(answer)

    def resolve(self, raw):
        if not isinstance(raw, str):
            raise ValueError('source link must be a string')
        variants = {raw, posixpath.normpath(posixpath.join(posixpath.dirname(self.source), raw))}
        if 'sse_multivector/' in raw:
            variants.add(raw.split('sse_multivector/', 1)[1])
        paths = {path for path in variants if path in self.bindings or path in self.directories}
        if not paths:
            parts = raw.strip('/').split('/')
            # A qualified absent source is not an unrelated file with the same
            # basename. Bare filenames still use their document-relative binding.
            limit = len(parts) if len(parts) == 1 else len(parts) - 1
            for index in range(limit):
                found = self.suffixes.get('/'.join(parts[index:]), set())
                if found:
                    paths = found
                    break
        if len(paths) > 1:
            raise ValueError('ambiguous saved source link')
        return next(iter(paths), None)

    def link(self, raw):
        path = self.resolve(raw)
        if path is None:
            return {'unresolved_source_path_sha256': hashlib.sha256(raw.encode()).hexdigest()}
        if path in self.directories:
            return {'source_directory_ref': path}
        result = {'source_ref': path, 'sha256': self.bindings[path]}
        if posixpath.basename(path) in ('output.json', 'results.jsonl'):
            answers = self.by_run.get(posixpath.dirname(path))
            if answers:
                result['answer_refs'] = [{key: answer[key] for key in
                    ('call_id', 'source_path', 'output_sha256', 'input_ref')
                    if answer.get(key) is not None} for answer in answers]
        return result

    def chosen_input(self, record):
        """Use a chosen call only when its exact masks prove the saved view."""
        instances = record.get('instances')
        if not isinstance(instances, list) or not isinstance(record.get('title'), str):
            return None
        candidates = []
        for key in ('result_path', 'output_path'):
            raw = record.get(key)
            if not isinstance(raw, str):
                continue
            path = self.resolve(raw)
            if path is None:
                continue
            for answer in self.by_run.get(posixpath.dirname(path), []):
                actual = answer.get('input_instances')
                if (answer['output'] == record['title'] and answer.get('input_ref') is not None
                        and _same_instances(instances, actual)):
                    candidates.append(answer)
        if candidates and all(row['input_ref'] == candidates[0]['input_ref'] for row in candidates):
            return candidates[0]
        return None


def _same_instances(recorded, actual):
    if not isinstance(actual, list) or len(recorded) != len(actual):
        return False
    fields = {'instance', 'note_id', 'vector_id', 'byte_spans', 'fragments', 'text',
              'source_instances', 'source_vector_ids'}
    for original, supplied in zip(recorded, actual):
        if (not isinstance(original, dict) or not isinstance(supplied, dict)
                or not {'instance', 'fragments'} <= original.keys() or original.keys() - fields):
            return False
        for key, value in original.items():
            if key == 'instance' and value in supplied.get('source_instances', []):
                continue
            if key == 'vector_id' and value in supplied.get('source_vector_ids', []):
                continue
            if supplied.get(key) != value:
                return False
    return True


def _looks_like_path(value):
    return (isinstance(value, str) and '\n' not in value and
            (value.startswith(('/', './', '../', 'sse_multivector/')) or
             bool(re.search(r'\.(?:jsonl?|txt|md|py|sh)\Z', value))))


def project_record(value, *, role, source, answers, bindings):
    """Return one source-bound record, retaining the native scientific structure.

    Missing external file links become explicit opaque unresolved references;
    ambiguous joins and unknown scientific fields fail. No source files are read.
    """
    if role not in _ROOT_FIELDS:
        raise ValueError(f'unsupported title-study record role: {role}')
    if not _portable(source) or source not in bindings:
        raise ValueError('record source has no portable hash binding')
    if not isinstance(value, dict) and not (isinstance(value, list) and role in (
            'final_comparison', 'final_title_selection')):
        raise ValueError('unknown scientific record shape')
    references = _References(source, answers, bindings)
    active = set()

    def project(item, field=None, depth=0, root=False):
        if depth > 64:
            raise ValueError('scientific record nesting exceeds supported shapes')
        if field in _TEXT and item is not None and not isinstance(item, str):
            raise ValueError(f'unknown scientific shape for {field}')
        if field == 'trial' and (type(item) not in (int, str)):
            raise ValueError('unknown scientific shape for trial')
        if field == 'config' and not isinstance(item, str):
            raise ValueError('unknown scientific shape for config')
        if isinstance(item, str):
            if (field in _STRICT_LINKS or
                    (field in _LINKS | {'source', 'raw_result', 'prior_experiment'} and
                     (_looks_like_path(item) or item in references.bindings or item in references.directories))):
                return references.link(item)
            if field in _PROMPTS:
                return references.link(item) if _looks_like_path(item) else {
                    ('rendered_prompt_sha256' if field == 'prompt' else 'template_sha256'):
                    hashlib.sha256(item.encode()).hexdigest()}
            return item
        if item is None or type(item) in (bool, int):
            return item
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError('nonfinite scientific number')
            return item
        if not isinstance(item, (dict, list)) or id(item) in active:
            raise ValueError('unknown or cyclic scientific record shape')
        active.add(id(item))
        try:
            if isinstance(item, list):
                return [project(child, field, depth + 1) for child in item]
            result = {}
            chosen = references.chosen_input(item) if role == 'final_title_selection' else None
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError('scientific record keys must be strings')
                allowed = _ROOT_FIELDS[role] if root else _FIELDS
                parameter_runtime = role == 'study_parameters' and key in _PARAMETER_RUNTIME
                if key not in allowed and key not in _RUNTIME and not parameter_runtime and not _dynamic(key):
                    raise ValueError(f'unknown scientific field: {key}')
                if parameter_runtime:
                    continue
                if key in _RUNTIME:
                    if child is not None and not isinstance(child, (str, int, list)):
                        raise ValueError(f'unknown runtime field shape: {key}')
                    continue
                if chosen is not None and key == 'instances':
                    result['input_ref'] = chosen['input_ref']
                    continue
                if chosen is not None and key == 'notes':
                    note_ids = list(dict.fromkeys(i.get('note_id') for i in chosen['input_instances']))
                    if child == note_ids:
                        continue
                result[key] = project(child, key, depth + 1)
            return result
        finally:
            active.remove(id(item))

    return {'record_type': role, 'source': {'path': source, 'sha256': bindings[source]},
            'actor': _actor(value, role), 'data': project(value, root=True)}
