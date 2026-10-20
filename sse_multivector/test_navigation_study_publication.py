"""Navigation studies export saved measurements through the shared publisher."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class NavigationStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, name, value):
        raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return dict(path=name, sha256=hashlib.sha256(raw).hexdigest())

    def fixture(self):
        inputs = self.save('study/inputs.json', [dict(row=7, canonical_row=0, note='N7',
            subject='Tea', alias_ids=['V7'], fragments=['Tea'], text='Tea & coffee.')])
        config = self.save('study/config.json', dict(model='saved-model', model_revision='pinned',
            input_sha256=inputs['sha256'], threshold=0.5, device='cpu',
            batch_size=4, packages=dict(torch='saved'), snapshot='/private/ACCOUNT_CANARY'))
        scores = self.save('study/scores.json', [dict(row=7, text='Tea', condition='single',
            labels=['drinks'], rendered='RENDERED_CANARY', token_ids=[123],
            scores=[dict(label='drinks', logit=0.0, score=0.5, accepted=True)])])
        self.select(dict(kind='gliclass', inputs=inputs, configuration=config, scores=scores))

    def select(self, selection):
        self.save('selection.json', dict(schema_version=1, studies={'nav-test':
            dict(profile='navigation-study', **selection)}))

    def export(self):
        from sse_multivector.historical_study_publication import export_results
        output = self.root/'publication'
        export_results(self.root, self.root/'selection.json', 'nav-test', output)
        return output

    def rows(self, output, name):
        return [json.loads(line) for line in (output/name).read_text().splitlines()]

    def test_native_logits_scores_and_decisions_are_preserved_without_requests(self):
        self.fixture()
        output = self.export()
        row = self.rows(output, 'results.jsonl')[0]
        self.assertEqual(row['scores'], [dict(label='drinks', logit=0.0, score=0.5, accepted=True)])
        self.assertEqual(row['row'], 7)
        self.assertEqual(self.rows(output, 'answers.jsonl'), [])
        raw = ''.join(path.read_text() for path in output.iterdir())
        self.assertNotIn('RENDERED_CANARY', raw)
        self.assertNotIn('ACCOUNT_CANARY', raw)
        self.assertNotIn('token_ids', raw)

    def existing_references(self, *, wrong_fragment=False):
        self.fixture()
        selected=json.loads((self.root/'selection.json').read_text())['studies']['nav-test']
        previous=self.save('previous/inputs.jsonl',dict(row=7,note='N7',subject='Tea',description='Tea & coffee.'))
        grounding=self.save('previous/masks.jsonl',dict(row=0,canonical_id='canonical',aliases=[dict(
            short_id='V7',subject='Tea',note_short_id='N7',fragments=['WRONG' if wrong_fragment else 'Tea'])]))
        selected['existing_inputs']=dict(**previous,publication='numerical/previous-inputs',rows=1)
        selected['existing_grounding']=dict(**grounding,publication='numerical/previous-masks',rows=1)
        selected.pop('profile')
        self.select(selected)

    def test_existing_inputs_and_grounding_are_validated_and_referenced_once(self):
        self.existing_references()
        output=self.export()
        meta=json.loads((output/'experiment.json').read_text())
        self.assertEqual(meta['references']['grounding']['publication'],'numerical/previous-masks')
        case=next(row for row in self.rows(output,'inputs.jsonl') if row['type']=='case_input')
        self.assertEqual(case['data']['grounding'],dict(canonical_row=0,alias_ids=['V7']))
        self.assertNotIn('source',case)
        self.assertNotIn('text',case['data'])

    def test_wrong_existing_fragment_fails_without_publishing_a_repaired_mask(self):
        self.existing_references(wrong_fragment=True)
        with self.assertRaisesRegex(ValueError,'grounding differs'):
            self.export()

    def test_duplicate_native_request_is_rejected(self):
        self.fixture()
        spec=json.loads((self.root/'selection.json').read_text());selection=spec['studies']['nav-test']
        rows=json.loads((self.root/'study/scores.json').read_text());selection['scores']=self.save('study/scores.json',rows*2)
        self.save('selection.json',spec)
        with self.assertRaisesRegex(ValueError,'duplicate native'):
            self.export()

    def test_configuration_must_bind_exact_saved_input_bytes(self):
        self.fixture()
        spec=json.loads((self.root/'selection.json').read_text());selection=spec['studies']['nav-test']
        config=json.loads((self.root/'study/config.json').read_text());config['input_sha256']='0'*64
        selection['configuration']=self.save('study/config.json',config);self.save('selection.json',spec)
        with self.assertRaisesRegex(ValueError,'configuration input hash differs'):
            self.export()

    def rse_fixture(self, *, incomplete=False):
        inputs=self.save('study/inputs.json',[dict(id=name,case='C1',domain='test',wording=1,
            role='candidate',text=name,model_input=name) for name in ('A','B')])
        config=self.save('study/config.json',dict(inputs_sha256=inputs['sha256'],relation_index=0,
            normalized_before_translation=False))
        rows=[dict(first=a,second=b,cosine=1.0000000000000002,entailment=-0.125)
              for a in ('A','B') for b in ('A','B')]
        scores=self.save('study/scores.json',rows[:-1] if incomplete else rows)
        self.select(dict(kind='rse',inputs=inputs,configuration=config,scores=scores))

    def test_rse_keeps_both_native_values_without_rounding_or_clamping(self):
        self.rse_fixture()
        output=self.export()
        rows=self.rows(output,'results.jsonl')
        self.assertEqual(len(rows),4)
        self.assertEqual(rows[0]['cosine'],1.0000000000000002)
        self.assertEqual(rows[0]['entailment'],-0.125)
        self.assertEqual(json.loads((output/'experiment.json').read_text())['input']['subject_provenance_status'],
                         'not_applicable')

    def test_incomplete_rse_matrix_is_rejected(self):
        self.rse_fixture(incomplete=True)
        with self.assertRaisesRegex(ValueError,'incomplete ordered RSE'):
            self.export()

    def lmms_fixture(self, *, pos=False, changed_target=False):
        source=self.save('study/inputs.json',[dict(row=1,note='N1',subject='Tea',text='Tea.',
            canonical_row=0,alias_ids=['V1'],fragments=['Tea'])])
        word=dict(text='Tea',lemma='tea',upos='NOUN',start_char=0,end_char=3)
        match=dict(key='tea%1',cosine=1.0000000000000002,synset='tea.n.01',definition='Saved definition.')
        row=dict(row=1,note='N1',subject='Tea',word_index=0,word=word,
            candidates={name:dict(available=1) for name in ('saved','surface','unrestricted')},
            matches={name:[match] for name in ('saved','surface','unrestricted')})
        previous=self.save('study/previous-scores.json',[row])
        config=self.save('study/config.json',dict(input_sha256=source['sha256'],
            source_hashes=dict(scores=previous['sha256']),model_encoding=not pos))
        selection=dict(kind='lmms-pos' if pos else 'lmms',inputs=source,configuration=config)
        if pos:
            row.pop('candidates');row['candidate_keys']=[];row['matches']=[]
            if changed_target:row['word_index']=1
            selection.update(source_scores=previous,source_experiment='original-USM01')
        selection['scores']=self.save('study/scores.json',[row]);self.select(selection)

    def test_lmms_keeps_ranking_identity_definitions_and_full_precision(self):
        self.lmms_fixture()
        output=self.export();row=self.rows(output,'results.jsonl')[0]
        self.assertEqual(row['matches']['surface'][0]['cosine'],1.0000000000000002)
        self.assertEqual(row['word']['text'],'Tea')
        self.assertEqual(row['matches']['saved'][0]['definition'],'Saved definition.')

    def test_pos_control_retains_empty_result_and_records_vector_reuse(self):
        self.lmms_fixture(pos=True)
        output=self.export()
        self.assertEqual(self.rows(output,'results.jsonl')[0]['matches'],[])
        meta=json.loads((output/'experiment.json').read_text())
        self.assertIs(meta['reuse']['model_encoding'],False)
        self.assertEqual(meta['counts']['empty_rankings'],1)

    def test_pos_control_rejects_changed_source_target(self):
        self.lmms_fixture(pos=True,changed_target=True)
        with self.assertRaisesRegex(ValueError,'reused LMMS target context differs'):
            self.export()

    def test_unchanged_reexport_is_byte_stable_and_preserves_source(self):
        self.fixture()
        source=self.root/'study/scores.json';original=(source.read_bytes(),source.stat().st_mtime_ns)
        output=self.export();before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
        self.export()
        self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
        self.assertEqual(original,(source.read_bytes(),source.stat().st_mtime_ns))


if __name__ == '__main__':
    unittest.main()
