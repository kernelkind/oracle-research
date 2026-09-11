import copy
import unittest

from seed_subject_relations import prepare_experiment, summarize
from group_description_relations import score_pairs


class SeedSubjectRelationsTests(unittest.TestCase):
    def setUp(self):
        a = dict(short_id='V1', note_short_id='N1', fragments=['Rise'], subject='Getting up.')
        aa = dict(a, short_id='V2', subject='Waking up.')
        b = dict(short_id='V3', note_short_id='N2', fragments=['costs rise'], subject='Rising costs.')
        c = dict(short_id='V4', note_short_id='N3', fragments=['GM'], subject='A greeting.')
        self.evidence = [dict(row=0, aliases=[a, aa]), dict(row=1, aliases=[b]), dict(row=2, aliases=[c])]
        self.groups = [dict(id='g1', seeds=[dict(row=0, source=a)], evidence=self.evidence[:2]),
                       dict(id='g2', seeds=[dict(row=2, source=c)], evidence=self.evidence[2:])]
        self.fixture = dict(template='This text is about {}.')

    def test_candidates_use_every_seed_alias_without_rewriting(self):
        before = copy.deepcopy((self.groups, self.evidence))
        candidates, pairs = prepare_experiment(self.groups, self.evidence, self.fixture)
        self.assertEqual({c['text'] for c in candidates if c['kind'] == 'subject'},
                         {'Getting up.', 'Waking up.', 'A greeting.'})
        raw = next(c for c in candidates if c['text'] == 'Rise')
        self.assertEqual([a['short_id'] for a in raw['sources']], ['V1', 'V2'])
        self.assertEqual((self.groups, self.evidence), before)
        relation = [p for p in pairs if p['measurement'] == 'relation']
        self.assertEqual(len(relation), 6)
        self.assertTrue(all(p['child_group'] != p['parent_group'] for p in relation))
        self.assertTrue(any(p['premise'] == 'This text is about Getting up..' for p in pairs))

    def test_coverage_preserves_aliases_but_counts_distinct_notes(self):
        candidates, pairs = prepare_experiment(self.groups, self.evidence, self.fixture)
        for p in pairs:
            p['score'] = .9 if p.get('vector') in {'V1', 'V2'} else .1
        result = summarize(candidates, pairs)
        c = next(x for x in candidates if x['text'] == 'Getting up.')
        coverage = next(r for r in result['coverage'] if r['candidate'] == c['id'])
        self.assertEqual(coverage['notes'], ['N1', 'N2'])
        self.assertEqual(coverage['supported_notes'], ['N1'])
        self.assertEqual(coverage['supported_rows'], [0])
        self.assertEqual(coverage['unsupported_vectors'], ['V3'])

    def test_alternative_relation_disagreement_is_not_hidden(self):
        candidates, pairs = prepare_experiment(self.groups, self.evidence, self.fixture)
        for p in pairs:
            p['score'] = .9 if p['premise'] == 'This text is about Getting up..' else .1
        summary = summarize(candidates, pairs)
        row = next(r for r in summary['relations'] if r['child_group'] == 'g1'
                   and r['parent_group'] == 'g2' and r['kind'] == 'subject')
        self.assertEqual(row['combinations'], 2)
        self.assertEqual(row['positive_combinations'], 1)
        self.assertEqual((row['minimum'], row['maximum']), (.1, .9))

    def test_inconsistent_or_duplicate_source_records_are_rejected(self):
        for evidence in [self.evidence + [self.evidence[0]], self.evidence[1:]]:
            with self.assertRaises(ValueError):
                prepare_experiment(self.groups, evidence, self.fixture)
        changed = copy.deepcopy(self.groups)
        changed[0]['evidence'][0]['aliases'][0]['subject'] = 'different'
        with self.assertRaises(ValueError):
            prepare_experiment(changed, self.evidence, self.fixture)

    def test_empty_scoring_batch_fails_before_loading(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            score_pairs([], {}, None)


if __name__ == '__main__':
    unittest.main()
