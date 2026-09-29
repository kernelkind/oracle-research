import unittest

from sse_multivector.teacher_mask_neighbors import best_connections, mask_inputs


class TeacherMaskNeighborsTests(unittest.TestCase):
    def test_mask_adapter_preserves_unicode_empty_and_duplicate_masks(self):
        cases = [dict(id=str(i), status=status,
                      evidence=dict(note_id='n'),
                      inputs=dict(POST='☕ tea', SUBJECT=subject), ranges=ranges)
                 for i, (subject, status, ranges) in enumerate([
                     ('Tea', 'valid', [dict(start=2, end=5)]),
                     ('Drink', 'valid', [dict(start=2, end=5)]),
                     ('Coffee', 'empty', []),
                 ])]
        request, mapping, preserved = mask_inputs(cases)
        self.assertEqual(len(mapping['vectors']), 1)
        self.assertEqual(request[0]['subjects'][0]['byte_spans'], [[4, 7]])
        self.assertEqual(len(preserved['notes'][0]['subjects']), 3)
        self.assertEqual(len(mapping['vectors'][0]['subject_entries']), 2)
        cases[0]['status'] = 'failed'
        with self.assertRaises(ValueError):
            mask_inputs(cases)

    def test_compares_both_arms_to_same_reference_excluding_entire_query_cohort(self):
        rows = [dict(vector_id=k, note_id=n) for k, n in
                [('a', 'q'), ('self', 'q2'), ('r', 'reference')]]
        candidate = [dict(vector_id='b', note_id='q')]
        vectors = dict(a=[1., 0.], self=[1., 0.], r=[0., 1.], b=[0., 2.])
        result = best_connections(rows, candidate, vectors, ['q', 'q2'])
        q = [r for r in result if r['query_note'] == 'q']
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0]['reference_id'], 'r')
        self.assertEqual(q[0]['baseline']['cosine'], 0.)
        self.assertEqual(q[0]['candidate']['cosine'], 1.)
        self.assertEqual(q[0]['candidate']['vector_id'], 'b')
        self.assertIsNone([r for r in result if r['query_note'] == 'q2'][0]['candidate'])

    def test_zero_vector_is_not_a_connection(self):
        with self.assertRaises(ValueError):
            best_connections([dict(vector_id='r', note_id='r')],
                             [dict(vector_id='q', note_id='q')],
                             dict(r=[1., 0.], q=[0., 0.]), ['q'])

    def test_interleaved_notes_keep_their_own_mask_ranges(self):
        cases = [dict(id=str(i), status='valid', evidence=dict(note_id=n),
                      inputs=dict(POST='tea coffee', SUBJECT=str(i)),
                      ranges=[dict(start=start, end=end)])
                 for i, (n, start, end) in enumerate([
                     ('a', 0, 3), ('b', 4, 10), ('a', 4, 10)])]
        _, _, preserved = mask_inputs(cases)
        self.assertEqual([[s['fragments'] for s in n['subjects']]
                          for n in preserved['notes']], [[['tea'], ['coffee']], [['coffee']]])


if __name__ == '__main__':
    unittest.main()
