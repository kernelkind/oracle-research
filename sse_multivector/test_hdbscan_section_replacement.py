"""Replace one native section and recluster through production worker paths."""
import json
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from sse_multivector import hdbscan_epsilon_review as review
from sse_multivector import test_hierarchy_generation_v3 as fixtures
from sse_multivector import worker


class SectionReplacementTests(unittest.TestCase):
    def test_next_section_names_changed_groups_reuses_exact_groups_and_keeps_original_filter(self):
        native = fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.prepare_v41(count=82)
        binary = native.root/'hdbscan-fixture'
        from sse_multivector import hierarchy_generation, hierarchy_hdbscan
        initial = native.state()
        original_request, _ = hierarchy_hdbscan.request_for(initial, initial['families'][0]['current'],
            hierarchy_generation._vectors(initial, initial['families'][0]['current']))
        opaque_ids = sorted(i['opaque_id'] for i in original_request['inputs'])
        original_groups = [opaque_ids[i:i+3] for i in range(0, len(opaque_ids)-2, 3)]
        binary.write_text(binary.read_text().replace(
            '1/((k-i-1)/10)', '1/(((k-i-1)/10)**0.3)').replace(
            'n=len(ids); k=len(groups)',
            f'if len(ids) != 82:\n    groups=[g for g in {original_groups!r} if set(g) <= set(ids)]\n'
            'n=len(ids); k=len(groups)\nif n != 82 and k > 2:\n'
            '    groups[0][-1], groups[1][-1] = groups[1][-1], groups[0][-1]'))
        native.cli('prepare-hierarchy', 'v41', '--spec', spec)
        native.cli('run-hierarchy', 'v41')
        state = json.loads((native.root/'v41/state.json').read_text())
        analysis = review.saved_review(native.root/'v41/state.json')
        first = next(s for s in analysis['sections'] if len(s['groups']) >= 2)
        label = f"S{analysis['sections'].index(first)+1:02d}"
        native.write('epsilon.json', analysis)
        native.write('section.json', dict(schema_version=1, epsilon_review='epsilon.json', section=label))
        specification = deepcopy(state['consolidation_spec'])

        def prepare_model(name, source):
            native.write(name+'.source.json', source)
            native.write(name+'.spec.json', {**specification, 'dataset': dict(
                adapter='hierarchy_group_consolidation', path=name+'.source.json')})
            native.cli('prepare', name, '--spec', name+'.spec.json')

        prepare_model('first-section', dict(schema_version=1, epsilon_review='epsilon.json', section=label))
        native.cli('run', 'first-section')

        def replacement(*args):
            completed = subprocess.run([sys.executable, '-m',
                'sse_multivector.hdbscan_section_replacement', *map(str, args)],
                cwd=fixtures.PROJECT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
            return completed

        replacement('prepare', native.root/'first', '--experiment', native.root/'first-section', '--case', label)
        first_plan = json.loads((native.root/'first/replacement.json').read_text())['plan']
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=fixtures.FixtureEncoder()):
            worker.run_worker(first_plan['pool']['encodings'][-1]['config'])
        replacement('collect', native.root/'first')
        replacement('prepare', native.root/'filtered', '--from-replacement', native.root/'first',
                    '--exclude-unassigned')
        replacement('collect', native.root/'filtered')
        derived = json.loads((native.root/'filtered/analysis.json').read_text())
        selected = next(s for s in derived['sections'] if len(s['groups']) >= 3)
        second_label = f"S{derived['sections'].index(selected)+1:02d}"
        source = dict(schema_version=1, replacement_review=str(native.root/'filtered/analysis.json'),
                      section=second_label, stage='groups')
        prepare_model('changed-groups', source)
        changed = json.loads(native.cli('show', 'changed-groups', '--json').stdout)
        self.assertEqual(len(changed['cases']), 2)
        self.assertTrue(all(len(json.loads(c['inputs']['INPUT_JSON'])['nodes']) == 3
                            for c in changed['cases']))
        self.assertTrue(all('parent' not in json.loads(c['inputs']['INPUT_JSON']) for c in changed['cases']))
        pending_source = dict(source, stage='section', group_experiment=str(native.root/'changed-groups'))
        native.write('pending.source.json', pending_source)
        native.write('pending.spec.json', {**specification, 'dataset': dict(
            adapter='hierarchy_group_consolidation', path='pending.source.json')})
        pending = native.cli('prepare', 'pending', '--spec', 'pending.spec.json', ok=False)
        self.assertIn('group definition requires one valid native result', pending.stderr)
        native.cli('run', 'changed-groups')
        # A one-group section already has its final definition; reuse the exact native result.
        single = next(s for s in derived['sections'] if len(s['groups']) == 1)
        single_label = f"S{derived['sections'].index(single)+1:02d}"
        single_source = dict(source, section=single_label, stage='section')
        prepare_model('single-group', single_source)
        one = json.loads(native.cli('show', 'single-group', '--case', single_label).stdout)
        self.assertEqual(len(json.loads(one['inputs']['INPUT_JSON'])['nodes']), 3)
        producer = one['evidence']['group_nodes'][0]['producer']
        previous_calls = len(native.calls())
        replacement('prepare', native.root/'single-reused', '--experiment', producer['experiment'],
                    '--case', producer['case'], '--replacement-review', native.root/'filtered/analysis.json',
                    '--section', single_label)
        reused_plan = json.loads((native.root/'single-reused/replacement.json').read_text())['plan']
        self.assertTrue(reused_plan['reused_definition'])
        self.assertEqual(reused_plan['receipt'], producer['receipt'])
        self.assertEqual(len(native.calls()), previous_calls)
        source.update(stage='section', group_experiment=str(native.root/'changed-groups'))
        prepare_model('second-section', source)
        second = json.loads(native.cli('show', 'second-section', '--case', second_label).stdout)
        payload = json.loads(second['inputs']['INPUT_JSON'])
        self.assertEqual(len(payload['nodes']), len(selected['groups']))
        producers = second['evidence']['group_nodes']
        self.assertEqual(sum(p['reused'] for p in producers), len(selected['groups'])-2)
        for witness in producers:
            saved = json.loads(native.cli('show', witness['producer']['experiment'],
                '--case', witness['producer']['case']).stdout)
            self.assertEqual(payload['nodes'][selected['groups'].index(witness['group'])], saved['parsed'])
        native.cli('run', 'second-section')
        # Independently named disjoint sections must apply together without losing either result.
        proposals = dict(schema_version=1, replacement_review=str(native.root/'filtered/analysis.json'),
            proposals=[dict(experiment=str(native.root/'second-section'), case=second_label),
                       dict(experiment=producer['experiment'], case=producer['case'], section=single_label)])
        native.write('round.json', proposals)
        combined = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_root_round',
            'prepare', str(native.root/'combined'), '--source', str(native.root/'round.json')],
            cwd=fixtures.PROJECT, capture_output=True, text=True)
        self.assertEqual(combined.returncode, 0, combined.stdout+combined.stderr)
        joint = json.loads((native.root/'combined/replacement.json').read_text())['plan']
        self.assertEqual(joint['replacement_ids'], ['R00002', 'R00003'])
        self.assertEqual(len(joint['root_changes']), 2)
        expected_removed = {i for g in derived['groups']
                            if g['id'] in selected['groups']+single['groups'] for i in g['original_ids']}
        before = json.loads((native.root/'filtered/replacement.json').read_text())['plan']
        self.assertEqual(joint['current_ids'],
            [i for i in before['current_ids'] if i not in expected_removed]+['R00002', 'R00003'])
        self.assertEqual(joint['excluded_unassigned_ids'], before['excluded_unassigned_ids'])
        self.assertEqual(len(joint['pool']['encodings']), len(before['pool']['encodings']))
        replacement('collect', native.root/'combined')
        replacement('roots', native.root/'combined', '--name', 'combined-roots')
        joint_view = json.loads((native.root/'combined/combined-roots.json').read_text())
        self.assertEqual([r['slots'] for r in joint_view['roots']], [[1], [2], [3]])
        self.assertEqual(joint_view['root_count'], 3)
        native.write('overlap.json', dict(proposals, proposals=[proposals['proposals'][0]]*2))
        overlap = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_root_round',
            'prepare', str(native.root/'overlap'), '--source', str(native.root/'overlap.json')],
            cwd=fixtures.PROJECT, capture_output=True, text=True)
        self.assertNotEqual(overlap.returncode, 0)
        self.assertIn('overlap', overlap.stderr)
        self.assertFalse((native.root/'overlap').exists())
        replacement('prepare', native.root/'second', '--experiment', native.root/'second-section',
                    '--case', second_label)
        before = json.loads((native.root/'filtered/replacement.json').read_text())['plan']
        after = json.loads((native.root/'second/replacement.json').read_text())['plan']
        removed = {i for g in derived['groups'] if g['id'] in selected['groups'] for i in g['original_ids']}
        self.assertEqual(after['current_ids'], [i for i in before['current_ids'] if i not in removed]+['R00002'])
        self.assertEqual(after['excluded_unassigned_ids'], before['excluded_unassigned_ids'])
        self.assertTrue(set(after['excluded_unassigned_ids']).isdisjoint(after['current_ids']))
        ungrouped = set(before['current_ids'])-{i for g in derived['groups'] for i in g['original_ids']}
        self.assertTrue(ungrouped)
        self.assertTrue(ungrouped <= set(after['current_ids']))
        # This controlled teacher returns the same definition, so reuse its vector too.
        self.assertEqual(len(after['pool']['encodings']), len(before['pool']['encodings']))
        self.assertEqual(after['pool']['items']['R00002']['vector_key'],
                         before['pool']['items']['R00001']['vector_key'])
        if 'R00001' not in removed:
            self.assertEqual(after['pool']['items']['R00001'], before['pool']['items']['R00001'])
        replacement('collect', native.root/'second')
        final = json.loads((native.root/'second/analysis.json').read_text())
        self.assertEqual(final['replacement']['id'], 'R00002')
        self.assertEqual(final['provenance']['new_encodings'], 0)
        original_ids = {o for i in removed for o in before['pool']['items'][i]['original_ids']}
        self.assertEqual(set(final['replacement']['original_ids']), original_ids)
        self.assertEqual(json.loads((native.root/'v41/state.json').read_text()), state)
        replacement('roots', native.root/'second', '--name', 'proposed-roots')
        roots = json.loads((native.root/'second/proposed-roots.json').read_text())
        self.assertEqual([r['id'] for r in roots['roots']], ['R00001', 'R00002'])
        self.assertEqual([r['slots'] for r in roots['roots']], [[1], [2]])
        self.assertEqual(roots['root_count'], 2)
        self.assertEqual(roots['represented_notes'], len({n for r in roots['roots'] for n in r['note_ids']}))
        self.assertTrue((native.root/'second/proposed-roots.svg').exists())
        self.assertTrue((native.root/'second/proposed-roots.md').exists())
        derived['groups'][0]['titles'] = ['Altered visualization']
        native.write('filtered/analysis.json', derived)
        tampered = native.cli('prepare', 'tampered-next', '--spec', 'changed-groups.spec.json', ok=False)
        self.assertIn('replacement review differs from saved native evidence', tampered.stderr)

    def test_replace_all_members_keep_noise_and_count_original_note_support(self):
        native = fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.prepare_v41()
        binary = native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            '1/((k-i-1)/10)', '1/(((k-i-1)/10)**0.3)'))
        native.cli('prepare-hierarchy', 'v41', '--spec', spec)
        native.cli('run-hierarchy', 'v41')
        state_path = native.root/'v41/state.json'
        analysis = review.saved_review(state_path)
        section = next(s for s in analysis['sections'] if len(s['groups']) >= 2)
        label = f"S{analysis['sections'].index(section)+1:02d}"
        native.write('epsilon.json', analysis)
        native.write('section.json', dict(schema_version=1, epsilon_review='epsilon.json',
                                          section=label))
        state = json.loads(state_path.read_text())
        specification = deepcopy(state['consolidation_spec'])
        specification['dataset'] = dict(adapter='hierarchy_group_consolidation', path='section.json')
        native.write('section.spec.json', specification)
        native.cli('prepare', 'named-section', '--spec', 'section.spec.json')
        native.cli('run', 'named-section')
        destination = native.root/'recluster'
        prepare = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'prepare', str(destination), '--experiment', str(native.root/'named-section'),
            '--case', label], cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertEqual(prepare.returncode, 0, prepare.stdout+prepare.stderr)
        plan = json.loads((destination/'replacement.json').read_text())['plan']
        pool = plan['pool']
        groups = {g['id']: g for g in analysis['groups']}
        removed = sorted(i for g in section['groups'] for i in groups[g]['original_ids'])
        self.assertEqual(plan['removed_ids'], removed)
        originals = state['families'][0]['rounds'][0]['current']
        self.assertEqual(plan['current_ids'], [i for i in originals if i not in removed]+['R00001'])
        unassigned = set(originals)-{i for g in analysis['groups'] for i in g['original_ids']}
        self.assertTrue(unassigned)
        self.assertTrue(unassigned <= set(plan['current_ids']))
        self.assertEqual(pool['items']['R00001']['original_ids'], removed)
        self.assertEqual(len(pool['encodings'][-1]['keys']), 1)
        request = json.loads(Path(pool['encodings'][-1]['config']).with_name('request.json').read_text())
        item = pool['items']['R00001']
        self.assertEqual(request['notes'][0]['text'], item['subject']+'\n\n'+item['meaning'])
        self.assertEqual(request['notes'][0]['subjects'][0]['byte_spans'],
                         [[0, len(item['subject'].encode())]])
        for i in plan['current_ids'][:-1]:
            self.assertEqual(pool['items'][i], state['items'][i])
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=fixtures.FixtureEncoder()):
            worker.run_worker(pool['encodings'][-1]['config'])
        collect = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'collect', str(destination)], cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertEqual(collect.returncode, 0, collect.stdout+collect.stderr)
        result = json.loads((destination/'analysis.json').read_text())
        self.assertEqual(result['encoded_entries'], len(plan['current_ids']))
        self.assertEqual(result['provenance']['new_encodings'], 1)
        self.assertEqual(result['provenance']['new_model_calls'], 0)
        assigned = next(g for g in result['groups'] if 'R00001' in g['original_ids'])
        expected_notes = {o['local']['note_id'] for o in state['originals'] if o['id'] in removed}
        self.assertTrue(expected_notes <= set(assigned['note_ids']))
        self.assertEqual(result['replacement']['note_ids'], sorted(expected_notes))
        self.assertEqual(len(result['replacement']['original_ids']), len(removed))
        self.assertTrue((destination/'reclustered-sections.svg').exists())
        self.assertEqual(json.loads(state_path.read_text()), state)
        # Reuse the exact synthetic encoding while excluding original noise.
        filtered = native.root/'grouped-only'
        again = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'prepare', str(filtered), '--from-replacement', str(destination), '--exclude-unassigned'],
            cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertEqual(again.returncode, 0, again.stdout+again.stderr)
        filtered_plan = json.loads((filtered/'replacement.json').read_text())['plan']
        grouped = {i for g in analysis['groups'] for i in g['original_ids']}
        self.assertEqual(filtered_plan['current_ids'],
                         [i for i in originals if i in grouped and i not in removed]+['R00001'])
        self.assertEqual(filtered_plan['first_new_encoding'], len(filtered_plan['pool']['encodings']))
        self.assertEqual(filtered_plan['excluded_unassigned_ids'], sorted(unassigned))
        root_key = item['vector_key']
        self.assertEqual(filtered_plan['pool']['vectors'][root_key]['encoding'], len(pool['encodings'])-1)
        self.assertEqual(filtered_plan['pool']['encodings'][-1]['config'], pool['encodings'][-1]['config'])
        collected = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'collect', str(filtered)], cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertEqual(collected.returncode, 0, collected.stdout+collected.stderr)
        filtered_result = json.loads((filtered/'analysis.json').read_text())
        self.assertEqual(filtered_result['provenance']['new_encodings'], 0)
        self.assertEqual(filtered_result['provenance']['reused_vectors'], len(filtered_plan['current_ids']))
        self.assertEqual(filtered_result['replacement']['original_ids'], removed)
        (native.root/'epsilon.json').write_text((native.root/'epsilon.json').read_text()+'\n')
        changed = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'collect', str(destination)], cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn('replacement source changed', changed.stderr)


if __name__ == '__main__':
    unittest.main()
