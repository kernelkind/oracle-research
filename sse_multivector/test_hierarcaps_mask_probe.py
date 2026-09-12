"""Tests for the exact-input HierarCaps diagnostic, without downloading a model."""
import copy
import math
import unittest

from hierarcaps_mask_probe import prepare_inputs, pair_scores, verify_loading


class HierarCapsProbeTests(unittest.TestCase):
    def setUp(self):
        self.alias = dict(short_id='V1', vector_id='one', note_id='note',
                          note_short_id='N1', text='é Music here',
                          fragments=['Music', 'here'], byte_spans=[[3, 8], [9, 13]],
                          subject='This generated subject must never be encoded')
        self.evidence = [dict(aliases=[self.alias])]
        self.original = dict(vectors=[copy.deepcopy(self.alias)])

    def test_only_original_mask_fragments_reach_model_input(self):
        rows = prepare_inputs(self.evidence, self.original, ['V1'])
        self.assertEqual(rows[0]['model_input'], 'Music here')
        self.assertEqual(rows[0]['text'], 'é Music here')
        self.assertNotIn('subject', rows[0])

    def test_utf8_source_ranges_must_match_exact_fragments(self):
        self.alias['byte_spans'] = [[2, 7], [9, 13]]
        with self.assertRaises(ValueError):
            prepare_inputs(self.evidence, self.original, ['V1'])

    def test_changed_copy_cannot_replace_original_mask(self):
        self.alias['fragments'] = ['Music']
        self.alias['byte_spans'] = [[3, 8]]
        with self.assertRaises(ValueError):
            prepare_inputs(self.evidence, self.original, ['V1'])

    def test_reversed_fragments_are_not_silently_sorted(self):
        for row in (self.alias, self.original['vectors'][0]):
            row['fragments'].reverse()
            row['byte_spans'].reverse()
        with self.assertRaises(ValueError):
            prepare_inputs(self.evidence, self.original, ['V1'])

    def test_unknown_or_duplicate_ids_fail(self):
        for ids in (['missing'], ['V1', 'V1']):
            with self.assertRaises(ValueError):
                prepare_inputs(self.evidence, self.original, ids)
        self.evidence.append(copy.deepcopy(self.evidence[0]))
        with self.assertRaises(ValueError):
            prepare_inputs(self.evidence, self.original, ['V1'])

    def test_native_exterior_angle_in_both_directions(self):
        root, a, b = [1., 0.], [0., 1.], [-1., 0.]
        forward = pair_scores(root, a, b)
        reverse = pair_scores(root, b, a)
        self.assertAlmostEqual(forward['angle_radians'], math.pi / 2)
        self.assertAlmostEqual(reverse['angle_radians'], 3 * math.pi / 4)
        self.assertAlmostEqual(forward['cosine'], 0.)

    def test_identical_vectors_and_root_have_no_directional_angle(self):
        self.assertIsNone(pair_scores([1., 0.], [0., 1.], [0., 1.])['angle_radians'])
        self.assertIsNone(pair_scores([1., 0.], [1., 0.], [0., 1.])['angle_radians'])

    def test_bad_vectors_are_rejected(self):
        for b in ([0., 2.], [float('nan'), 0.], [1., 0., 0.]):
            with self.assertRaises(ValueError):
                pair_scores([1., 0.], [0., 1.], b)

    def test_loading_must_not_randomly_initialize_text_parameters(self):
        verify_loading(dict(missing_keys=[], mismatched_keys=[], error_msgs=[],
                            unexpected_keys=['vision_model.embeddings.weight',
                                             'visual_projection.weight', 'logit_scale']))
        for key in ('missing_keys', 'mismatched_keys', 'error_msgs', 'unexpected_keys'):
            with self.assertRaises(ValueError):
                verify_loading({key: ['text_model.embeddings.weight']})


if __name__ == '__main__':
    unittest.main()
