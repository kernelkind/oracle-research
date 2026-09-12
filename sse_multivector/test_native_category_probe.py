import copy
import unittest

from native_category_probe import make_requests, attach_scores


class NativeCategoryProbeTests(unittest.TestCase):
    def test_single_condition_never_supplies_competing_categories(self):
        records = [dict(row=1, subject='First.'), dict(row=2, subject='Second.')]
        requests = make_requests(records, ['coffee', 'morning greetings'], conditions=['single'])
        self.assertEqual(len(requests), 4)
        self.assertTrue(all(r['condition'] == 'single' and len(r['labels']) == 1
                            for r in requests))
        self.assertEqual([(r['row'], r['labels'][0]) for r in requests],
                         [(1, 'coffee'), (2, 'coffee'),
                          (1, 'morning greetings'), (2, 'morning greetings')])
        for conditions in [[], ['single', 'single'], ['missing']]:
            with self.assertRaises(ValueError):
                make_requests(records, ['coffee'], conditions=conditions)

    def test_conditions_preserve_subjects_and_category_mapping(self):
        records = [dict(row=17, subject='A concrete subject.', text='Full note.',
                        fragments=['concrete']),
                   dict(row=3, subject='Another subject.', text='Other full note.',
                        fragments=['Another'])]
        before = copy.deepcopy(records)
        requests = make_requests(records, ['broad', 'narrow'])
        self.assertEqual(len(requests), 8)
        first = [r for r in requests if r['row'] == 17]
        self.assertEqual([r['labels'] for r in first],
                         [['broad', 'narrow'], ['narrow', 'broad'], ['broad'], ['narrow']])
        self.assertTrue(all(r['text'] == 'A concrete subject.' for r in first))
        self.assertEqual(records, before)

    def test_sigmoids_are_independent_and_retain_low_scores(self):
        request = dict(labels=['narrow', 'broad'])
        scores = attach_scores(request, [-2.0, 2.0])
        self.assertEqual([s['label'] for s in scores], ['narrow', 'broad'])
        self.assertEqual([s['accepted'] for s in scores], [False, True])
        self.assertAlmostEqual(scores[0]['score'], 0.11920292202211755)
        same = attach_scores(dict(labels=['a', 'b']), [2.0, 2.0])
        self.assertTrue(all(s['accepted'] for s in same))
        self.assertGreater(sum(s['score'] for s in same), 1.0)

    def test_rejects_ambiguous_ids_labels_or_incomplete_logits(self):
        good = [dict(row=1, subject='Subject')]
        for records, labels in [(good * 2, ['x']), (good, ['x', 'x']),
                                (good, []), ([dict(row=1, subject='')], ['x'])]:
            with self.assertRaises(ValueError):
                make_requests(records, labels)
        for logits in [[], [1.0, 2.0], [float('nan')]]:
            with self.assertRaises(ValueError):
                attach_scores(dict(labels=['a']), logits)


if __name__ == '__main__':
    unittest.main()
