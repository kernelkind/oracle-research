"""Frozen baseline evidence uses the production historical publisher."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest


class BaselineStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'source'
        self.output = self.root/'publication'

    def write(self, name, value):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True)+'\n').encode()
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def member(self, name, value):
        binding = self.write('extracted/'+name, value)
        return {'member': name, 'member_sha256': binding['sha256'], 'source': binding}

    def fixture(self):
        notes = {'schema_version': 1, 'notes': [
            {'note_id': 'a', 'text': 'Tea.'}, {'note_id': 'b', 'text': 'Sun.'}]}
        posts = self.member('input/notes.json', notes)
        generation = self.member('generation/manifest.json', {'schema_version': 2,
            'input_sha256': posts['source']['sha256'], 'codex_home': '/private/account',
            'api_key': 'PRIVATE-KEY', 'codex_version': 'saved-cli',
            'takeaway': {'model': 'saved/model', 'reasoning_effort': 'max',
                         'prompt_version': 'TPv3.82', 'prompt': 'Saved instruction.'},
            'prominence': {'prompt_version': 'PPv2'}, 'mask': {'prompt_version': 'MPv3.4'},
            'isolation': {'fresh_process_per_job': True, 'web_search': 'disabled'}})
        answers = self.member('generation/output.json', {'schema_version': 2,
            'manifest_sha256': generation['source']['sha256'], 'notes': [
                {'note_id': 'a', 'takeaways': [{'text': 'Tea', 'prominence': 100, 'fragments': ['Tea']}]},
                {'note_id': 'b', 'takeaways': [{'text': 'Sun', 'prominence': 0, 'fragments': ['Sun']}]}]})
        vectors = [{'ordinal': i, 'subject_id': 'S'+str(i), 'note_id': note,
                    'takeaway_index': 0, 'takeaway': text, 'prominence': score,
                    'fragments': [text], 'byte_spans': [[0, 3]]}
                   for i, (note, text, score) in enumerate([('a', 'Tea', 100), ('b', 'Sun', 0)])]
        mapping = self.member('vectors/vector-map.json', {'schema_version': 1,
            'generation_output_sha256': answers['source']['sha256'],
            'note_count': 2, 'vector_count': 2, 'vectors': vectors})
        vm = self.member('vectors/manifest.json', {'schema_version': 1,
            'generation_output_sha256': answers['source']['sha256'], 'vector_count': 2,
            'normalization': 'saved-normalization', 'files': {'vector-map.json': {
                'sha256': mapping['source']['sha256']}}})
        segments = self.member('segments/segments.json', {'schema_version': 1,
            'artifact_id': 'saved-segments', 'selection_rule': 'saved-rule',
            'pairwise_min_cosine': .25, 'source_vector_count': 2, 'source_note_count': 2,
            'segment_count': 1, 'represented_vector_count': 2, 'represented_note_count': 2,
            'source_partition_region_count': 1, 'excluded_partition_regions': 0,
            'segments': [{'segment_id': 'C1', 'vector_ordinals': [0, 1],
                          'note_ids': ['a', 'b'], 'minimum_within_cosine': .5,
                          'members': vectors}]})
        sm = self.member('segments/manifest.json', {'schema_version': 1,
            'vector_manifest_sha256': vm['source']['sha256'],
            'vector_map_sha256': mapping['source']['sha256'], 'selection_rule': 'saved-rule',
            'pairwise_min_cosine_bits': struct.unpack('<Q', struct.pack('<d', .25))[0],
            'files': {'segments.json': {'sha256': segments['source']['sha256']}}})
        request = self.member('worker-input.json', {'schema_version': 1,
            'proposal_sha256': answers['member_sha256'], 'notes': [
                {'note_id': row['note_id'], 'text': row['text'], 'subjects': [
                    {'subject_id': vector['subject_id'], 'byte_spans': vector['byte_spans']}
                    for vector in vectors if vector['note_id'] == row['note_id']]}
                for row in notes['notes']]})
        encoder = self.member('worker-config.json', {'request_sha256': request['member_sha256'],
            'checkpoint_sha256': '1'*64, 'checkpoint_path': '/private/model'})
        return {'profile': 'baseline-study', 'kind': 'crec',
            'archive': self.write('baseline.tar.zst', 'Frozen archive bytes.'),
            'members': {'posts': posts, 'generation': generation, 'answers': answers,
                        'vector_map': mapping, 'vector_manifest': vm,
                        'segments': segments, 'segment_manifest': sm,
                        'request': request, 'encoder': encoder}}

    def export(self, selection):
        from .historical_study_publication import export_results
        path = self.root/'selection.json'
        path.write_text(json.dumps({'schema_version': 1, 'studies': {'baseline': selection}}))
        return export_results(self.source, path, 'baseline', self.output)

    def rows(self, name):
        return [json.loads(line) for line in (self.output/name).read_text().splitlines()]

    def test_final_assembled_answers_segments_and_methods_are_source_bound(self):
        selection = self.fixture()
        self.export(selection)
        answers = self.rows('answers.jsonl')
        self.assertEqual(len(answers), 2)
        self.assertEqual(answers[1]['data']['takeaways'][0]['prominence'], 0)
        self.assertEqual(answers[0]['representation'], 'parsed_assembled_answer')
        segment = next(r for r in self.rows('results.jsonl') if r['type'] == 'segment')
        self.assertEqual(segment['vector_ordinals'], [0, 1])
        self.assertNotIn('members', segment)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['archive'], selection['archive'])
        self.assertEqual(metadata['member_sources']['answers'], selection['members']['answers'])
        self.assertIsNone(metadata['subject_provenance']['generated_subjects_deprecated'])
        self.assertEqual(metadata['parameters']['generation']['isolation']['fresh_process_per_job'], True)
        published = ''.join(p.read_text() for p in self.output.iterdir())
        self.assertNotIn('PRIVATE-KEY', published)
        self.assertNotIn('/private/account', published)

    def test_declared_archive_member_and_exact_mask_bindings_fail_closed(self):
        selection = self.fixture()
        selection['members']['answers']['member_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'archive member/counterpart hash differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())
        selection = self.fixture()
        request = json.loads((self.source/'extracted/worker-input.json').read_text())
        request['notes'][0]['subjects'][0]['byte_spans'] = [[1, 3]]
        selection['members']['request'] = self.member('worker-input.json', request)
        with self.assertRaisesRegex(ValueError, 'encoder request differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())

    def geometry_fixture(self, occurrence=1, overlap_field=True):
        proposal = self.member('proposal.json', {'schema_version': 2, 'proposal_id': 'saved',
            'subject_instruction': 'Enumerate narrow subjects.', 'mask_instruction': 'Select source fragments.',
            'notes': [{'note_id': note, 'subjects': [{'subject_id': 'S'+str(i), 'label': text,
                'status': 'masked', 'fragments': [{'text': text, 'occurrence': occurrence}]}]}
                for i, (note, text) in enumerate([('a', 'Tea'), ('b', 'Sun')])]})
        request = self.member('worker-input.json', {'schema_version': 1,
            'proposal_sha256': proposal['member_sha256'], 'notes': [
                {'note_id': note, 'text': text+'.', 'subjects': [{'subject_id': 'S'+str(i),
                    'byte_spans': [[0, 3]]}]} for i, (note, text) in enumerate([('a', 'Tea'), ('b', 'Sun')])]})
        subjects = [{'ordinal': i, 'note_id': note, 'subject_id': 'S'+str(i), 'label': text,
            'fragments': [{'text': text, 'occurrence': occurrence}], 'raw_norm': 1.25,
            'selected_token_indices': [0], 'nearest_overall': {'ordinal': 1-i, 'cosine': .123},
            'cross_note_ranking': ['DUPLICATED-RANKING'], 'top_cross_note_neighbors': []}
            for i, (note, text) in enumerate([('a', 'Tea'), ('b', 'Sun')])]
        analysis = self.member('analysis/analysis.json', {'schema_version': 1,
            'diagnostic_id': 'saved-diagnostic', 'proposal_sha256': proposal['member_sha256'],
            'note_count': 2, 'subject_count': 2, 'dimensions': 3,
            'rules': {'cosine': 'saved-f64-rule', 'ranking': 'saved-tie-rule'},
            'pair_counts': {'all': 1, 'same_note': 0, 'cross_note': 1},
            'distributions': {'cross_note': {'count': 1, 'minimum': .123, 'mean': .123}},
            'nearest_overall_from_same_note': 0, 'nearest_overall_from_other_note': 2,
            'subjects': subjects, 'pairs': [{'left_ordinal': 0, 'right_ordinal': 1,
                'left_note_id': 'a', 'left_subject_id': 'S0', 'right_note_id': 'b',
                'right_subject_id': 'S1', 'cosine': .123, 'same_note': False,
                **({'token_overlap': None} if overlap_field else {})}]})
        manifest = self.member('analysis/manifest.json', {'schema_version': 1,
            'request_sha256': request['member_sha256'], 'proposal_sha256': proposal['member_sha256'],
            'note_count': 2, 'subject_count': 2, 'dimensions': 3,
            'worker': {'checkpoint_sha256': '1'*64},
            'files': {'analysis.json': {'sha256': analysis['member_sha256']}}})
        encoder = self.member('config.json', {'checkpoint_sha256': '1'*64,
            'request_sha256': request['member_sha256'], 'checkpoint_path': '/private/model'})
        return {'profile': 'baseline-study', 'kind': 'geometry',
            'archive': self.write('geometry.tar.zst', 'Frozen archive.'),
            'members': dict(proposal=proposal, request=request, analysis=analysis,
                            manifest=manifest, encoder=encoder),
            'reused_answers': {'publication': 'numerical/previous', 'records': 2,
                               'status': 'Existing answers reused as diagnostic inputs.'}}

    def test_unique_geometry_measurements_and_source_methods_without_duplicate_answers(self):
        selection = self.geometry_fixture()
        self.export(selection)
        self.assertEqual(self.rows('answers.jsonl'), [])
        pair = self.rows('results.jsonl')[0]
        self.assertEqual(pair, {'type': 'pair', 'left_ordinal': 0, 'right_ordinal': 1,
                              'cosine': .123, 'same_note': False, 'token_overlap': None})
        subject = next(row for row in self.rows('inputs.jsonl') if row['type'] == 'diagnostic_subject')
        self.assertEqual(subject['raw_norm'], 1.25)
        self.assertEqual(subject['selected_token_indices'], [0])
        self.assertNotIn('cross_note_ranking', subject)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['diagnostic']['distributions']['cross_note']['mean'], .123)
        self.assertEqual(metadata['counts']['pairs'], 1)
        self.assertEqual(metadata['reused_answers']['publication'], 'numerical/previous')
        self.output = self.root/'wrong-encoder'
        value = json.loads((self.source/'extracted/config.json').read_text())
        value['request_sha256'] = '0'*64
        selection['members']['encoder'] = self.member('config.json', value)
        with self.assertRaisesRegex(ValueError, 'encoder/request source binding differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())

    def test_geometry_fragment_occurrence_must_match_the_frozen_request(self):
        with self.assertRaisesRegex(ValueError, 'fragment occurrence'):
            self.export(self.geometry_fixture(occurrence=2))
        self.assertFalse(self.output.exists())

    def test_cross_note_pair_without_overlap_field_keeps_its_native_shape(self):
        self.export(self.geometry_fixture(overlap_field=False))
        self.assertNotIn('token_overlap', self.rows('results.jsonl')[0])

    def test_reused_notes_are_not_counted_as_fresh_final_jobs(self):
        selection = self.fixture()
        members = selection['members']
        def value(name):
            return json.loads((self.source/members[name]['source']['path']).read_text())
        def replace(name, content):
            members[name] = self.member(members[name]['member'], content)
            return members[name]['member_sha256']
        baseline_posts = self.member('baseline/input/notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'a', 'text': 'Tea.'}, {'note_id': 'c', 'text': 'Moon.'}]})
        baseline_generation = self.member('baseline/generation/manifest.json', {
            'schema_version': 2, 'input_sha256': baseline_posts['member_sha256']})
        baseline_answers = self.member('baseline/generation/output.json', {'schema_version': 2,
            'manifest_sha256': baseline_generation['member_sha256'], 'notes': [
                {'note_id': 'a', 'takeaways': [{'text': 'Tea', 'prominence': 100, 'fragments': ['Tea']}]},
                {'note_id': 'c', 'takeaways': [{'text': 'Moon', 'prominence': 0, 'fragments': ['Moon']}]}]})
        members.update(baseline_posts=baseline_posts, baseline_generation=baseline_generation,
                       baseline_answers=baseline_answers)
        generation = value('generation')
        generation['reuse_source'] = {name+'_sha256': binding['member_sha256'] for name, binding in [
            ('input', baseline_posts), ('manifest', baseline_generation), ('output', baseline_answers)]}
        generation_sha = replace('generation', generation)
        answers = value('answers'); answers['manifest_sha256'] = generation_sha
        answer_sha = replace('answers', answers)
        mapping = value('vector_map'); mapping['generation_output_sha256'] = answer_sha
        mapping_sha = replace('vector_map', mapping)
        vm = value('vector_manifest'); vm['generation_output_sha256'] = answer_sha
        vm['files']['vector-map.json']['sha256'] = mapping_sha
        vm_sha = replace('vector_manifest', vm)
        sm = value('segment_manifest'); sm['vector_manifest_sha256'] = vm_sha
        sm['vector_map_sha256'] = mapping_sha
        replace('segment_manifest', sm)
        request = value('request'); request['proposal_sha256'] = answer_sha
        request_sha = replace('request', request)
        encoder = value('encoder'); encoder['request_sha256'] = request_sha
        replace('encoder', encoder)
        self.export(selection)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['reuse']['reused_notes'], 1)
        self.assertEqual(metadata['reuse']['new_notes'], 1)
        self.assertEqual(metadata['reuse']['reused_final_jobs'], 3)
        self.assertEqual(metadata['reuse']['new_final_jobs'], 3)
        self.assertEqual(self.rows('answers.jsonl')[0]['execution'], 'reused')


if __name__ == '__main__':
    unittest.main()
