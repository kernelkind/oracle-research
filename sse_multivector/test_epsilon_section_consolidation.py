"""Saved epsilon sections enter consolidation through native preparation."""
import json
import unittest

from sse_multivector import hdbscan_epsilon_review as review
from sse_multivector import test_hierarchy_generation_v3 as fixtures


class EpsilonSectionConsolidationTests(unittest.TestCase):
    def test_native_section_keeps_exact_group_meanings_and_freezes_producers(self):
        native = fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.prepare_v41()
        binary = native.root / 'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            '1/((k-i-1)/10)', '1/(((k-i-1)/10)**0.3)'))
        native.cli('prepare-hierarchy', 'v41', '--spec', spec)
        native.cli('run-hierarchy', 'v41')
        state_path = native.root / 'v41/state.json'
        analysis = review.saved_review(state_path)
        section = next(s for s in analysis['sections'] if len(s['groups']) >= 2)
        label = f"S{analysis['sections'].index(section)+1:02d}"
        native.write('epsilon.json', analysis)
        native.write('section.json', dict(schema_version=1, epsilon_review='epsilon.json',
                                          section=label))
        state = json.loads(state_path.read_text())
        specification = state['consolidation_spec']
        specification['dataset'] = dict(adapter='hierarchy_group_consolidation',
                                       path='section.json')
        native.write('section.spec.json', specification)
        native.cli('prepare', 'section-trial', '--spec', 'section.spec.json')
        envelope = json.loads((native.root/'section-trial/experiment.json').read_text())
        plan = envelope['plan']
        case = json.loads(native.cli('show', 'section-trial', '--case', label).stdout)
        payload = json.loads(case['inputs']['INPUT_JSON'])
        groups = {g['id']: g for g in analysis['groups']}
        wanted = [next(n for n in state['nodes']
                       if set(n['original_ids']) == set(groups[g]['original_ids']))
                  for g in section['groups']]
        self.assertEqual(payload, dict(nodes=[dict(title=n['subject'], meaning=n['meaning'])
                                             for n in wanted]))
        self.assertEqual(case['evidence']['groups'], section['groups'])
        self.assertIn(str(state_path), plan['sources'])
        self.assertIn(str(native.root/'epsilon.json'), plan['sources'])
        for node in wanted:
            self.assertIn(node['synthetic']['receipt']['results_path'], plan['sources'])
        native.cli('run', 'section-trial')
        result = json.loads(native.cli('show', 'section-trial', '--case', label).stdout)
        self.assertEqual(result['status'], 'valid')
        self.assertEqual(len(plan['cases']), 1)
        # Saved visualization edits cannot redirect a native source silently.
        analysis['sections'][analysis['sections'].index(section)]['groups'].pop()
        native.write('epsilon.json', analysis)
        failure = native.cli('prepare', 'tampered', '--spec', 'section.spec.json', ok=False)
        self.assertIn('epsilon review differs from saved native evidence', failure.stderr)


if __name__ == '__main__':
    unittest.main()
