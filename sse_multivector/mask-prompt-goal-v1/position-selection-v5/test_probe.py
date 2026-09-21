import unittest

from probe import build_config, expectations, load_cases


class StressProbeTests(unittest.TestCase):
    def test_only_unmarked_source_and_subject_enter_requests(self):
        cases = load_cases()
        config = build_config(cases)
        self.assertEqual(len(config['prompts']), 6)
        self.assertEqual(config['model'], 'gpt-6-astra')
        self.assertEqual(config['reasoning_effort'], 'low')
        self.assertIsNone(config['auth_file'])
        for case, job in zip(cases, config['prompts']):
            source, required, forbidden = expectations(case)
            self.assertTrue(required)
            self.assertTrue(forbidden)
            self.assertIn('<post>\n' + source + '\n</post>', job['text'])
            self.assertIn('<subject>\n' + case['subject'] + '\n</subject>', job['text'])
            self.assertNotIn(case['required_marked_note'], job['text'])
            self.assertNotIn(case['excluded_marked_note'], job['text'])

    def test_fixture_annotation_cannot_change_source(self):
        case = dict(load_cases()[0], excluded_marked_note='changed ⟦text⟧')
        with self.assertRaises(ValueError):
            expectations(case)

    def test_fixture_annotations_cannot_overlap(self):
        case = load_cases()[0].copy()
        case['excluded_marked_note'] = case['required_marked_note']
        with self.assertRaises(ValueError):
            expectations(case)


if __name__ == '__main__':
    unittest.main()
