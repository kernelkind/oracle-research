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
        (native.root/'epsilon.json').write_text((native.root/'epsilon.json').read_text()+'\n')
        changed = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_section_replacement',
            'collect', str(destination)], cwd=fixtures.PROJECT, text=True, capture_output=True)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn('replacement source changed', changed.stderr)


if __name__ == '__main__':
    unittest.main()
