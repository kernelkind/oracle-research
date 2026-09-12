import unittest

from mask_candidate_coverage import inventory


class CandidateCoverageTests(unittest.TestCase):
    def test_shared_features_need_not_be_complete_masks(self):
        records = [
            dict(row=0, aliases=[dict(note_short_id='A', fragments=['fresh bread'])]),
            dict(row=1, aliases=[dict(note_short_id='B', fragments=['baking bread'])]),
            dict(row=2, aliases=[dict(note_short_id='B', fragments=['baking bread'])]),
            dict(row=3, aliases=[dict(note_short_id='C', fragments=['baking'])]),
            dict(row=4, aliases=[dict(note_short_id='D', fragments=['I', '😴'])]),
            dict(row=5, aliases=[dict(note_short_id='E', fragments=['I', 'work'])]),
        ]
        result = {d['feature']: d for d in inventory(records)}
        self.assertEqual(set(result), {'bread', 'baking', 'i'})
        self.assertEqual(result['bread']['rows'], [0, 1, 2])
        self.assertEqual(result['bread']['notes'], ['A', 'B'])
        self.assertEqual(result['bread']['whole_mask_rows'], [])
        self.assertFalse(result['bread']['mdh02_candidate'])
        self.assertEqual(result['baking']['whole_mask_rows'], [3])
        self.assertTrue(result['baking']['mdh02_candidate'])
        self.assertEqual(result['i']['whole_mask_rows'], [])

    def test_two_rows_from_one_note_do_not_establish_recurrence(self):
        records = [dict(row=i, aliases=[dict(note_short_id='A', fragments=['bread'])])
                   for i in range(2)]
        self.assertEqual(inventory(records), [])

    def test_alias_disagreement_is_not_silently_ignored(self):
        records = [dict(row=0, aliases=[
            dict(note_short_id='A', fragments=['bread']),
            dict(note_short_id='A', fragments=['coffee']),
        ])]
        with self.assertRaisesRegex(ValueError, 'aliases disagree'):
            inventory(records)


if __name__ == '__main__':
    unittest.main()
