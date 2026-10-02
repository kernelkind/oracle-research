import unittest
import json
import os
import struct
import subprocess
import sys
import tempfile
from argparse import Namespace
from unittest.mock import patch
from pathlib import Path

from sse_multivector.prominence_cosine import cosine, rank_rows
from sse_multivector import test_experiment as fixtures


class ProminenceCosineTests(unittest.TestCase):
    def test_saved_context_comparison_needs_no_mp_masks_or_saved_vectors(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector.experiment_inputs import prepare_context_prominence
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='one', node_id='music', node_title='Music',
                note_id='a'*64, text='Music cheers me up.', subject_id='SP1',
                subject='Music.', context='Music brings joy.', source={})
            carrier = root/'subjects.json'
            carrier.write_text(json.dumps({'notes': [dict(note_id=evidence['note_id'],
                text=evidence['text'], subjects=[dict(id='SP1', subject='Music.',
                                                     context=evidence['context'])])]}))
            original_carrier = carrier.read_bytes()
            evidence['source']['subjects'] = dict(path=str(carrier), sha256=pc.sha(carrier))
            case = prepare_context_prominence({'cases': [evidence]}, basis='node_title')[0]
            case.update(status='valid', parsed={'prominence': 80})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            plan = {'dataset': {'adapter': 'subject_contexts', 'prominence_basis': 'node_title'},
                    'run_directory': str(root)}
            command = ['prominence_cosine.py', 'prepare', str(root/'out'),
                       '--experiments', str(root), '--worker-config', str(config),
                       '--post-order', 'highest']
            with patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case]}), \
                 patch.object(pc, 'load_vectors', side_effect=AssertionError('unused vectors')):
                with patch('sys.argv', command):
                    pc.main()
            output = root/'out'
            saved = pc.read(output/'plan.json')
            flat = [(n, s) for n in pc.read(output/'worker-request.json')['notes']
                    for s in n['subjects']]
            item = saved['cases'][0]
            self.assertEqual(item['subject_id'], 'SP1')
            self.assertEqual(flat[item['mask_row']][0]['text'], evidence['context'])
            self.assertEqual(flat[item['mask_row']][1]['byte_spans'], [[0, 17]])
            self.assertEqual(saved['replays'], {})
            self.assertIsNone(saved['vectors'])
            fresh = [(1, 0)] * len(flat)
            fresh[item['mask_row']] = (0, 1)
            result = output/'result'
            result.mkdir()
            (result/'raw-vectors.f32le').write_bytes(struct.pack(
                '<'+'f'*(2*len(flat)), *(v for row in fresh for v in row)))
            (result/'worker-receipt.json').write_text(json.dumps(dict(encoder,
                request_sha256=pc.sha(output/'worker-request.json'),
                proposal_sha256=pc.sha(output/'plan.json'),
                rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in flat])))
            pc.collect(output)
            comparison = pc.read(output/'comparison.json')
            self.assertEqual(comparison['posts']['music'][0]['linear_product'], 40)
            self.assertEqual(comparison['parity'], {})
            carrier.write_text('{}\n')
            with self.assertRaisesRegex(ValueError, 'protected artifact changed'):
                pc.collect(output)
            carrier.write_bytes(original_carrier)
            config.write_text(config.read_text()+' ')
            with self.assertRaisesRegex(ValueError, 'protected artifact changed'):
                pc.collect(output)

    def test_subject_and_context_are_encoded_together_with_fixed_prominence(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector.experiment_inputs import prepare_context_prominence
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='tea-context', node_id='tea', node_title='Tea',
                note_id='a'*64, text='Tea warms me.', mask_ids=['V1'], byte_spans=[[0, 3]],
                subject_number='1', subject='☕ Tea', context='Tea warms the writer.')
            case = prepare_context_prominence({'cases': [evidence]}, basis='node_title')[0]
            original_inputs = dict(case['inputs'])
            case.update(status='valid', parsed={'prominence': 20})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<2f', 1, 0))
            rows = [dict(short_id='V1', ordinal=0, note_id='a'*64, note_short_id='N1',
                         byte_spans=[[0, 3]], fragments=['Tea'], subject_entries=[dict(
                             number='1', subject=evidence['subject'], context=evidence['context'])])]
            plan = {'dataset': {'adapter': 'subject_contexts', 'prominence_basis': 'node_title'},
                    'run_directory': str(root)}
            args = Namespace(output=root/'out', vectors=root, experiments=[root],
                             worker_config=config, replay=['V1'], post_order='highest',
                             include_subject=True)
            with patch.object(pc, 'load_vectors', return_value=(rows, encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case]}):
                pc.prepare(args)
                saved = pc.read(args.output/'plan.json')
                item = saved['cases'][0]
                flat = [(n, s) for n in pc.read(args.output/'worker-request.json')['notes']
                        for s in n['subjects']]
                note, selection = flat[item['mask_row']]
                expected_text = evidence['subject'] + '\n' + evidence['context']
                self.assertEqual(note['text'], expected_text)
                self.assertEqual(selection['byte_spans'], [[0, len(expected_text.encode())]])
                self.assertEqual(item['representation'], 'subject_context')
                self.assertEqual(item['subject'], evidence['subject'])
                self.assertEqual(item['context'], evidence['context'])
                self.assertEqual(item['prominence'], 20)
                self.assertEqual(case['inputs'], original_inputs)
                self.assertEqual(case['evidence'], evidence)
                replay_note, replay_selection = flat[saved['replays']['V1']['row']]
                self.assertEqual(replay_note['text'], evidence['text'])
                self.assertEqual(replay_selection['byte_spans'], evidence['byte_spans'])
                fresh = [(1, 0)] * len(flat)
                fresh[item['mask_row']] = (0, 1)
                result = args.output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack(
                    '<' + 'f' * (2*len(fresh)), *(v for row in fresh for v in row)))
                (result/'worker-receipt.json').write_text(json.dumps(dict(
                    encoder, request_sha256=pc.sha(args.output/'worker-request.json'),
                    proposal_sha256=pc.sha(args.output/'plan.json'),
                    rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in flat])))
                pc.collect(args.output)
                comparison = pc.read(args.output/'comparison.json')
                self.assertEqual(comparison['groups']['tea'][0]['representation'], 'subject_context')
                self.assertEqual(comparison['posts']['tea'][0]['linear_product'], 10)
                command = ['prominence_cosine.py', 'prepare', str(root/'cli'),
                           '--experiments', str(root), '--vectors', str(root),
                           '--worker-config', str(config), '--replay', 'V1',
                           '--post-order', 'highest', '--include-subject']
                with patch('sys.argv', command):
                    pc.main()
                self.assertEqual(pc.read(root/'cli/worker-request.json')['notes'],
                                 pc.read(args.output/'worker-request.json')['notes'])
                original_output = args.output
                args.output = root/'default'
                args.include_subject = False
                pc.prepare(args)
                default_plan = pc.read(args.output/'plan.json')
                default_flat = [(n, s) for n in pc.read(args.output/'worker-request.json')['notes']
                                for s in n['subjects']]
                self.assertEqual(default_flat[default_plan['cases'][0]['mask_row']][0]['text'],
                                 evidence['context'])
                args.output = root/'wrong-reuse'
                args.reuse_encoding = original_output
                with self.assertRaisesRegex(ValueError, 'encoder notes differ'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                args.reuse_encoding = None
                args.include_subject = True
                args.output = root/'conflicting'
                args.relevance_source_text = [(evidence['id'], 'Tea')]
                with self.assertRaisesRegex(ValueError, 'cannot combine'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                args.relevance_source_text = None
                plan['dataset']['adapter'] = 'generic'
                with self.assertRaisesRegex(ValueError, 'requires saved SP'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())

    def test_selected_cases_reuse_complete_encoding_with_fresh_prominence(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector import experiment_inputs
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = [dict(id=title.lower(), node_id=title.lower(), node_title=title,
                note_id=letter*64, text=f'{title} warms me.', mask_ids=[mid],
                byte_spans=[[0, len(title)]], subject_number='1', subject=title,
                context=f'The writer drinks {title.lower()}.')
                for title, letter, mid in [('Tea', 'a', 'V1'), ('Coffee', 'b', 'V2')]]
            cases = experiment_inputs.prepare_context_prominence(
                {'cases': evidence}, basis='node_title')
            for case in cases:
                case.update(status='valid', parsed={'prominence': 30})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<4f', 1, 0, 0, 1))
            rows = [dict(short_id=e['mask_ids'][0], ordinal=i, note_id=e['note_id'],
                note_short_id=f'N{i}', byte_spans=e['byte_spans'], fragments=[e['subject']],
                subject_entries=[dict(number='1', subject=e['subject'], context=e['context'])])
                for i, e in enumerate(evidence)]
            plan = {'dataset': {'adapter': 'subject_contexts', 'prominence_basis': 'node_title'},
                    'run_directory': str(root)}
            command = ['prominence_cosine.py', 'prepare', str(root/'out'),
                       '--experiments', str(root), '--vectors', str(root),
                       '--worker-config', str(config), '--replay', 'V1', 'V2',
                       '--post-order', 'highest']
            with patch.object(pc, 'load_vectors', return_value=(rows, encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': cases}):
                with patch('sys.argv', command):
                    pc.main()
                output = root/'out'
                saved = pc.read(output/'plan.json')
                request = pc.read(output/'worker-request.json')
                flat = [(n, s) for n in request['notes'] for s in n['subjects']]
                fresh = [(1, 0)] * len(flat)
                fresh[saved['title_rows']['coffee']] = (0, 1)
                fresh[saved['replays']['V2']['row']] = (0, 1)
                result = output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack(
                    '<' + 'f' * (2*len(fresh)), *(v for row in fresh for v in row)))
                (result/'worker-receipt.json').write_text(json.dumps(dict(
                    encoder, request_sha256=pc.sha(output/'worker-request.json'),
                    proposal_sha256=pc.sha(output/'plan.json'),
                    rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n, s in flat])))
                pc.collect(output)
                before = pc.read(output/'comparison.json')
                cases[1]['parsed']['prominence'] = 60
                for mid in ('V2', 'V1'):
                    selected = root/f'selected-{mid}'
                    args = command[:]
                    args[2] = str(selected)
                    args[args.index('--replay')+1:args.index('--post-order')] = [mid]
                    args += ['--only', 'coffee', '--reuse-encoding', str(output)]
                    with patch('sys.argv', args):
                        pc.main()
                    self.assertFalse((selected/'result').exists())
                    self.assertEqual(pc.read(selected/'worker-request.json')['notes'], request['notes'])
                    pc.collect(selected)
                    after = pc.read(selected/'comparison.json')
                    self.assertEqual(list(after['groups']), ['coffee'])
                    self.assertEqual(after['raw_vectors_sha256'], before['raw_vectors_sha256'])
                    self.assertEqual(after['worker_receipt_sha256'], before['worker_receipt_sha256'])
                    row = after['groups']['coffee'][0]
                    self.assertEqual(row['cosine'], before['groups']['coffee'][0]['cosine'])
                    self.assertEqual(row['prominence'], 60)
                    self.assertEqual(row['linear_product'], 30)
                    self.assertEqual(list(after['parity']), [mid])

    def test_source_text_relevance_preserves_post_evidence_and_fixed_prominence(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector import experiment_inputs
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = '☕ Tea warms me.\n\n#teatime'
            source_text = 'Tea warms me.\n\n#teatime'
            evidence = dict(id='tea-context', node_id='tea', node_title='Tea',
                note_id='a'*64, text=text, mask_ids=['V1'], byte_spans=[[4, 7]],
                subject_number='1', subject='Tea', context='The writer drinks tea.')
            case = experiment_inputs.prepare_context_prominence(
                {'cases': [evidence]}, basis='node_title')[0]
            original_inputs = dict(case['inputs'])
            case.update(status='valid', parsed={'prominence': 50})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<2f', 1, 0))
            rows = [dict(short_id='V1', ordinal=0, note_id='a'*64, note_short_id='N1',
                         byte_spans=[[4, 7]], fragments=['Tea'], subject_entries=[dict(
                             number='1', subject='Tea', context=evidence['context'])])]
            plan = {'dataset': {'adapter': 'subject_contexts', 'prominence_basis': 'node_title'},
                    'run_directory': str(root)}
            command = ['prominence_cosine.py', 'prepare', str(root/'out'),
                       '--experiments', str(root), '--vectors', str(root),
                       '--worker-config', str(config), '--replay', 'V1',
                       '--post-order', 'highest']
            option = ['--relevance-source-text', evidence['id'], source_text]
            with patch.object(pc, 'load_vectors', return_value=(rows, encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case]}):
                with patch('sys.argv', command + option):
                    pc.main()
                output = root/'out'
                saved = pc.read(output/'plan.json')
                item = saved['cases'][0]
                flat = [(n, s) for n in pc.read(output/'worker-request.json')['notes']
                        for s in n['subjects']]
                note, selection = flat[item['mask_row']]
                self.assertEqual(note['text'], source_text)
                self.assertEqual(selection['byte_spans'], [[0, len(source_text.encode())]])
                self.assertEqual(item['representation'], 'source_text')
                self.assertEqual(item['relevance_source_text'], source_text)
                self.assertEqual(item['relevance_source_spans'], [[4, len(text.encode())]])
                self.assertEqual(item['context'], evidence['context'])
                self.assertEqual(item['prominence'], 50)
                replay_note, replay_selection = flat[saved['replays']['V1']['row']]
                self.assertEqual(replay_note['text'], text)
                self.assertEqual(replay_selection['byte_spans'], [[4, 7]])
                self.assertEqual(case['inputs'], original_inputs)
                self.assertEqual(case['evidence'], evidence)
                fresh = [(1, 0)] * len(flat)
                fresh[item['mask_row']] = (0, 1)
                result = output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack(
                    '<' + 'f' * (2*len(fresh)), *(v for row in fresh for v in row)))
                (result/'worker-receipt.json').write_text(json.dumps(dict(
                    encoder, request_sha256=pc.sha(output/'worker-request.json'),
                    proposal_sha256=pc.sha(output/'plan.json'),
                    rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in flat])))
                pc.collect(output)
                comparison = pc.read(output/'comparison.json')
                self.assertEqual(comparison['posts']['tea'][0]['linear_product'], 25)
                self.assertEqual(comparison['groups']['tea'][0]['relevance_source_text'], source_text)
                for index, (options, message) in enumerate((
                    (['--relevance-source-text', evidence['id'], 'Rewritten tea.'], 'exact nonempty'),
                    (['--relevance-source-text', evidence['id'], ' '], 'exact nonempty'),
                    (option + option, 'duplicate relevance source'),
                    (['--relevance-source-text', 'unknown', 'Tea'], 'unknown relevance source'),
                    (['--relevance-source-text', evidence['id'], 'Tea warms me.',
                      '--reuse-encoding', str(output)], 'encoder notes differ'),
                )):
                    with self.subTest(options=options):
                        command[2] = str(root/f'bad-{index}')
                        with patch('sys.argv', command + options), \
                             self.assertRaisesRegex(ValueError, message):
                            pc.main()
                        self.assertFalse(Path(command[2]).exists())

    def test_subject_context_is_encoded_as_complete_text_and_uses_new_prominence(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector import experiment_inputs
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='tea-context', node_id='tea', node_title='Tea',
                note_id='a'*64, text='Tea warms me.', mask_ids=['V1'], byte_spans=[[0, 3]],
                subject_number='1', subject='Tea', context='Tea warms the writer.')
            case = experiment_inputs.prepare_context_prominence({'cases': [evidence]})[0]
            case.update(status='valid', parsed={'prominence': 20})
            other = dict(evidence, id='tea-other-context', subject_number='2',
                         context='The writer drinks tea.')
            other_case = experiment_inputs.prepare_context_prominence({'cases': [other]})[0]
            other_case.update(status='valid', parsed={'prominence': 30})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<2f', 1, 0))
            rows = [dict(short_id='V1', ordinal=0, note_id='a'*64, note_short_id='N1',
                         byte_spans=[[0, 3]], fragments=['Tea'], subject_entries=[dict(
                             number=e['subject_number'], subject='Tea', context=e['context'])
                             for e in (evidence, other)])]
            args = Namespace(output=root/'out', vectors=root, experiments=[root],
                             worker_config=config, replay=['V1'], include_inverse=False,
                             post_order='highest')
            plan = {'dataset': {'adapter': 'subject_contexts'}, 'run_directory': str(root)}
            with patch.object(pc, 'load_vectors', return_value=(rows, encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case, other_case]}):
                pc.prepare(args)
                saved = pc.read(args.output/'plan.json')
                item = saved['cases'][0]
                flat = [(n, s) for n in pc.read(args.output/'worker-request.json')['notes']
                        for s in n['subjects']]
                note, selection = flat[item['mask_row']]
                self.assertEqual(note['text'], evidence['context'])
                self.assertEqual(selection['byte_spans'], [[0, len(evidence['context'].encode())]])
                self.assertEqual(item['representation'], 'context')
                self.assertEqual(flat[saved['replays']['V1']['row']][0]['text'], evidence['text'])
                fresh = [(1, 0)] * len(flat)
                fresh[item['mask_row']] = (0, 1)
                fresh[saved['cases'][1]['mask_row']] = (-1, 0)
                result = args.output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack(
                    '<' + 'f' * (2*len(fresh)), *(v for row in fresh for v in row)))
                (result/'worker-receipt.json').write_text(json.dumps(dict(
                    encoder, request_sha256=pc.sha(args.output/'worker-request.json'),
                    proposal_sha256=pc.sha(args.output/'plan.json'),
                    rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in flat])))
                pc.collect(args.output)
                comparison = pc.read(args.output/'comparison.json')
                row = comparison['groups']['tea'][0]
                self.assertEqual(row['linear_product'], 10)
                self.assertEqual(row['context'], evidence['context'])
                post = comparison['posts']['tea'][0]
                self.assertEqual(post['prominence'], 30)
                self.assertEqual(post['linear_product'], 10)
                self.assertEqual(post['prominence_case'], other['id'])
                self.assertEqual(post['linear_product_case'], evidence['id'])
                self.assertEqual(post['context_count'], 2)
                self.assertEqual(comparison['post_rankings']['tea'],
                                 {'prominence': ['a'*64], 'linear_product': ['a'*64]})
                args.reuse_encoding = args.output
                args.output = root/'subject'
                plan['dataset']['prominence_basis'] = 'subject'
                for original, e, prominence in ((case, evidence, 40), (other_case, other, 80)):
                    original['inputs'] = experiment_inputs.prepare_context_prominence(
                        {'cases': [e]}, basis='subject')[0]['inputs']
                    original['parsed']['prominence'] = prominence
                pc.prepare(args)
                self.assertFalse((args.output/'result').exists())
                pc.collect(args.output)
                reused = pc.read(args.output/'comparison.json')
                self.assertEqual(reused['groups']['tea'][0]['cosine'], row['cosine'])
                self.assertEqual(reused['groups']['tea'][0]['prominence_basis'], 'subject')
                self.assertEqual(reused['posts']['tea'][0]['linear_product'], 20)
                self.assertEqual(reused['posts']['tea'][0]['prominence'], 80)
                self.assertEqual(reused['raw_vectors_sha256'], comparison['raw_vectors_sha256'])
                args.output = root/'node-title'
                plan['dataset']['prominence_basis'] = 'node_title'
                for original, e in ((case, evidence), (other_case, other)):
                    original['inputs'] = experiment_inputs.prepare_context_prominence(
                        {'cases': [e]}, basis='node_title')[0]['inputs']
                    original['parsed']['prominence'] = 50
                pc.prepare(args)
                self.assertFalse((args.output/'result').exists())
                pc.collect(args.output)
                node_result = pc.read(args.output/'comparison.json')
                self.assertEqual(node_result['raw_vectors_sha256'], comparison['raw_vectors_sha256'])
                self.assertTrue(all(r['prominence_basis'] == 'node_title'
                                    and r['prominence'] == 50 for r in node_result['groups']['tea']))
                self.assertEqual(node_result['posts']['tea'][0]['prominence'], 50)
                self.assertEqual(node_result['posts']['tea'][0]['linear_product'], 25)
                self.assertEqual(node_result['posts']['tea'][0]['linear_product_case'], evidence['id'])
                other_case['evidence']['context'] = 'A changed context.'
                rows[0]['subject_entries'][1]['context'] = 'A changed context.'
                args.output = root/'changed-encoding'
                with self.assertRaisesRegex(ValueError, 'encoder notes differ'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                other_case['evidence']['context'] = other['context']
                rows[0]['subject_entries'][1]['context'] = other['context']
                raw_path = args.reuse_encoding/'result/raw-vectors.f32le'
                raw_bytes = raw_path.read_bytes()
                raw_path.write_bytes(raw_bytes + b'changed')
                with self.assertRaisesRegex(ValueError, 'protected artifact changed'):
                    pc.collect(root/'subject')
                raw_path.write_bytes(raw_bytes)
                args.output = root/'bad'
                case['inputs']['INPUT_JSON'] = json.dumps({'node_title': 'Different', 'post': evidence['text']})
                with self.assertRaisesRegex(ValueError, 'model input'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())

    def test_combined_mask_encodes_exact_union_and_replays_original_spans(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector.experiment_inputs import prepare_prominence
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='photo-combined', node_id='photo', node_title='Photography',
                            note_id='a'*64, text='Take photos twice.', mask_ids=['V1', 'V2'],
                            byte_spans=[[5, 11], [12, 17]])
            case = prepare_prominence({'cases': [evidence]})[0]
            case.update(status='valid', parsed={'prominence': 20})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<4f', 1, 0, 1, 0))
            rows = [dict(short_id=mid, ordinal=i, note_id='a'*64, note_short_id='N1',
                         byte_spans=spans, fragments=fragments)
                    for i, (mid, spans, fragments) in enumerate((
                        ('V1', [[5, 11]], ['photos']), ('V2', [[12, 17]], ['twice'])))]
            args = Namespace(output=root/'out', vectors=root, experiments=[root],
                             worker_config=config, replay=['V1'], include_inverse=True)
            plan = {'dataset': {'adapter': 'prominence', 'combine_masks': True},
                    'run_directory': str(root)}
            with patch.object(pc, 'load_vectors', return_value=(rows, encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case]}):
                pc.prepare(args)
                saved = pc.read(args.output/'plan.json')
                item = saved['cases'][0]
                flat = [(n, s) for n in pc.read(args.output/'worker-request.json')['notes']
                        for s in n['subjects']]
                self.assertIsNone(item['ordinal'])
                self.assertEqual(item['fragments'], ['photos', 'twice'])
                self.assertEqual(flat[item['mask_row']][1]['byte_spans'], evidence['byte_spans'])
                self.assertEqual(flat[item['inverse_row']][1]['byte_spans'], [[0, 5], [11, 12], [17, 18]])
                self.assertEqual(flat[saved['replays']['V1']['row']][1]['byte_spans'], [[5, 11]])
                fresh = [(1, 0)] * len(flat)
                fresh[item['mask_row']] = (0, 1)
                fresh[item['full_post_row']] = (1, 1)
                result = args.output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack(
                    '<' + 'f' * (2 * len(fresh)), *(v for row in fresh for v in row)))
                (result/'worker-receipt.json').write_text(json.dumps(dict(
                    encoder, request_sha256=pc.sha(args.output/'worker-request.json'),
                    proposal_sha256=pc.sha(args.output/'plan.json'),
                    rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n, s in flat])))
                pc.collect(args.output)
                row = pc.read(args.output/'comparison.json')['groups']['photo'][0]
                self.assertEqual(row['cosine'], 0)
                self.assertEqual(row['inverse_product'], 90)
                self.assertEqual(row['mask_ids'], ['V1', 'V2'])
                args.output = root/'without-inverse'
                args.include_inverse = False
                pc.prepare(args)
                item = pc.read(args.output/'plan.json')['cases'][0]
                self.assertIn('mask_row', item)
                self.assertNotIn('inverse_row', item)
                args.output = root/'bad-union'
                evidence['byte_spans'] = [[5, 17]]
                case['inputs'] = prepare_prominence({'cases': [evidence]})[0]['inputs']
                with self.assertRaisesRegex(ValueError, 'union'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())

    def test_prepare_selected_generic_prominence_validates_exact_model_input(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector.experiment_inputs import prepare_prominence
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='photo-V1', node_id='photo', node_title='Photography',
                            note_id='a'*64, text='Take photos.', mask_ids=['V1'],
                            byte_spans=[[5, 11]])
            case = prepare_prominence({'cases': [evidence]})[0]
            case.update(status='valid', parsed={'prominence': 20, 'allocation': []})
            other = dict(id='other', status='unrun', evidence={'node_id': 'other'})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<2f', 1, 0))
            row = dict(short_id='V1', ordinal=0, note_id='a'*64, note_short_id='N1',
                       byte_spans=[[5, 11]], fragments=['photos'])
            args = Namespace(output=root/'out', vectors=root, experiments=[root],
                             worker_config=config, replay=['V1'], node=['photo'])
            plan = {'dataset': {'adapter': 'generic'}, 'run_directory': str(root)}
            with patch.object(pc, 'load_vectors', return_value=([row], encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case, other]}):
                pc.prepare(args)
                saved = json.loads((args.output/'plan.json').read_text())
                self.assertEqual([c['id'] for c in saved['cases']], ['photo-V1'])
                request = json.loads((args.output/'worker-request.json').read_text())
                self.assertEqual([n['text'] for n in request['notes']], ['Photography', 'Take photos.'])
                args.output = root/'selected-case'
                args.only = ['photo-V1']
                other['evidence']['node_id'] = 'photo'
                pc.prepare(args)
                self.assertEqual(len(pc.read(args.output/'plan.json')['cases']), 1)
                args.only = ['missing']
                args.output = root/'missing-case'
                with self.assertRaisesRegex(ValueError, 'case'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                args.only = None
                other['evidence']['node_id'] = 'other'
                args.output = root/'inverse'
                args.include_inverse = True
                pc.prepare(args)
                inverse_plan = pc.read(args.output/'plan.json')
                inverse_request = pc.read(args.output/'worker-request.json')
                item = inverse_plan['cases'][0]
                flat = [(n, s) for n in inverse_request['notes'] for s in n['subjects']]
                note, subject = flat[item['inverse_row']]
                self.assertEqual(note['text'], 'Take photos.')
                self.assertEqual(subject['byte_spans'], [[0, 5], [11, 12]])
                note, subject = flat[item['full_post_row']]
                self.assertEqual(note['text'], 'Take photos.')
                self.assertEqual(subject['byte_spans'], [[0, 12]])
                result = args.output/'result'
                result.mkdir()
                (result/'raw-vectors.f32le').write_bytes(struct.pack('<8f', 1, 0, 1, 0, 0, 1, 1, 1))
                receipt = dict(encoder, request_sha256=pc.sha(args.output/'worker-request.json'),
                               proposal_sha256=pc.sha(args.output/'plan.json'),
                               rows=[dict(note_id=n['note_id'], subject_id=s['subject_id'])
                                     for n, s in flat])
                (result/'worker-receipt.json').write_text(json.dumps(receipt))
                pc.collect(args.output)
                comparison = pc.read(args.output/'comparison.json')
                self.assertEqual(comparison['groups']['photo'][0]['inverse_product'], 60)
                self.assertEqual(comparison['groups']['photo'][0]['inverse_cosine'], 0)

                full_evidence = dict(evidence, id='photo-full', mask_ids=['V2'], byte_spans=[[0, 12]])
                full_case = prepare_prominence({'cases': [full_evidence]})[0]
                full_case.update(status='valid', parsed={'prominence': 100})
                full_row = dict(row, short_id='V2', ordinal=1,
                                byte_spans=[[0, 12]], fragments=['Take photos.'])
                vectors.write_bytes(struct.pack('<4f', 1, 0, 1, 1))
                args.output = root/'deduplicated'
                with patch.object(pc, 'load_vectors', return_value=(
                        [row, full_row], encoder, vectors, 'f', {})), \
                     patch.object(pc.experiment, 'report', return_value={'cases': [case, full_case]}):
                    pc.prepare(args)
                    dedup = pc.read(args.output/'plan.json')['cases']
                    self.assertEqual(dedup[0]['full_post_row'], dedup[1]['full_post_row'])
                    self.assertIsNone(dedup[1]['inverse_row'])
                    self.assertEqual(dedup[1]['inverse_spans'], [])
                args.output = root/'filtered'
                args.exclude_references = True
                linked = dict(evidence, text='Take photos. https://example.com')
                linked_case = prepare_prominence({'cases': [linked]})[0]
                linked_case.update(status='valid', parsed={'prominence': 20})
                vectors.write_bytes(struct.pack('<2f', 1, 0))
                with patch.object(pc.experiment, 'report', return_value={'cases': [linked_case]}):
                    pc.prepare(args)
                filtered = pc.read(args.output/'plan.json')
                request = pc.read(args.output/'worker-request.json')
                item = filtered['cases'][0]
                flat = [(n, s) for n in request['notes'] for s in n['subjects']]
                self.assertEqual(item['excluded_spans'], [[13, len(linked['text'])]])
                self.assertEqual(item['inverse_spans'], [[0, 5], [11, 13]])
                self.assertEqual(item['full_post_spans'], [[0, 13]])
                self.assertEqual(flat[item['inverse_row']][0]['text'], linked['text'])
                self.assertEqual(flat[item['full_post_row']][1]['byte_spans'], [[0, 13]])
                self.assertEqual(flat[filtered['replays']['V1']['row']][1]['byte_spans'], [[5, 11]])
                args.output = root/'bad-input'
                case['inputs']['INPUT_JSON'] = json.dumps({'mask': ['Take'], 'marked_post': '⟦Take⟧ photos.'})
                with self.assertRaisesRegex(ValueError, 'input'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                args.node = ['absent']
                with self.assertRaisesRegex(ValueError, 'node'):
                    pc.prepare(args)

    def test_linear_product_matches_viewer_formula(self):
        rows = [dict(id='a', prominence=80, cosine=0),
                dict(id='b', prominence=50, cosine=1),
                dict(id='c', prominence=90, cosine=-1)]
        ranks = rank_rows(rows)
        self.assertEqual([r['linear_product'] for r in rows], [40, 50, 0])
        self.assertEqual(ranks['linear_product'], ['b', 'a', 'c'])

    def test_inverse_product_and_full_post_baseline(self):
        rows = [dict(id='a', prominence=20, cosine=1, inverse_cosine=0,
                     full_post_cosine=.5),
                dict(id='b', prominence=10, cosine=1, inverse_cosine=.8,
                     full_post_cosine=.9),
                dict(id='c', prominence=100, cosine=.6, inverse_cosine=None,
                     full_post_cosine=.6)]
        ranks = rank_rows(rows)
        self.assertEqual([r['inverse_product'] for r in rows], [60, 91, 80])
        self.assertEqual([r['full_post_score'] for r in rows], [75, 95, 80])
        self.assertEqual(ranks['inverse_product'], ['b', 'c', 'a'])
        self.assertEqual(ranks['full_post_score'], ['b', 'c', 'a'])
        rows[-1]['prominence'] = 99
        with self.assertRaisesRegex(ValueError, 'inverse'):
            rank_rows(rows)

    def test_inverse_spans_are_exact_utf8_complement(self):
        from sse_multivector.prominence_cosine import inverse_spans
        self.assertEqual(inverse_spans('☕ coffee ☕', [[4, 10]]), [[0, 4], [10, 14]])
        self.assertEqual(inverse_spans('tea', [[0, 3]]), [])
        self.assertEqual(inverse_spans('tea tea', [[0, 3], [4, 7]]), [[3, 4]])
        for spans in ([[1, 3]], [[0, 4], [3, 7]], [[0, 100]]):
            with self.assertRaises(ValueError):
                inverse_spans('☕ tea', spans)

    def test_reference_exclusion_preserves_utf8_context_and_surrounding_words(self):
        from sse_multivector.prominence_cosine import excluded_reference_spans, subtract_spans
        identifier = 'nostr:npub1' + 'q' * 58
        text = '☕ Eggs (https://example.com/' + 'a'*64 + '). ' + identifier + ' #eggs ' + 'b'*64
        excluded = excluded_reference_spans(text)
        raw = text.encode()
        self.assertEqual([raw[a:b].decode() for a, b in excluded],
                         ['https://example.com/' + 'a'*64, identifier, 'b'*64])
        kept = subtract_spans([[0, len(raw)]], excluded)
        self.assertEqual(''.join(raw[a:b].decode() for a, b in kept), '☕ Eggs ().  #eggs ')
        self.assertEqual(subtract_spans([[0, 5], [8, 15]], [[3, 10]]), [[0, 3], [10, 15]])
        self.assertEqual(subtract_spans([[0, 3]], [[0, 3]]), [])
        self.assertEqual(excluded_reference_spans('Ordinary eggs #eggs note1short'), [])

    def test_refresh_vectors_are_loaded_with_verified_rows_spans_and_bytes(self):
        from sse_multivector.prominence_cosine import load_vectors, sha
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "worker-result").mkdir()
            request = {"proposal_sha256": "source", "notes": [dict(note_id="N", text="Tea",
                       subjects=[dict(subject_id="S", byte_spans=[[0, 3]])]) ]}
            mapping = {"vectors": [dict(note_id="N", worker_subject_id="S", short_id="V1",
                       byte_spans=[[0, 3]], fragments=["Tea"])]}
            (root / "worker-request.json").write_text(json.dumps(request))
            (root / "vector-map.json").write_text(json.dumps(mapping))
            raw = root / "worker-result/raw-vectors.f32le"
            raw.write_bytes(struct.pack('<2f', 3, 4))
            receipt = dict(request_sha256=sha(root / "worker-request.json"),
                           proposal_sha256="source", model={"dimensions": 2}, row_count=1,
                           rows=[dict(note_id="N", subject_id="S", ordinal=0)],
                           files={raw.name: {"sha256": sha(raw)}})
            (root / "worker-result/worker-receipt.json").write_text(json.dumps(receipt))
            rows, encoder, vector_file, code, protected = load_vectors(root)
            self.assertEqual(rows[0]['ordinal'], 0)
            self.assertEqual((vector_file, code), (raw, 'f'))
            self.assertEqual(protected[str(raw)], sha(raw))
            mapping['vectors'][0]['byte_spans'] = [[1, 3]]
            (root / "vector-map.json").write_text(json.dumps(mapping))
            with self.assertRaisesRegex(ValueError, 'span'):
                load_vectors(root)
            mapping['vectors'][0]['byte_spans'] = [[0, 3]]
            (root / "vector-map.json").write_text(json.dumps(mapping))
            raw.write_bytes(struct.pack('<2f', 4, 3))
            with self.assertRaisesRegex(ValueError, 'hash'):
                load_vectors(root)

    def test_cosine_is_normalized_and_product_is_unclipped(self):
        self.assertAlmostEqual(cosine([3, 4], [6, 8]), 1)
        self.assertAlmostEqual(cosine([1, 0], [0, 3]), 0)
        self.assertAlmostEqual(cosine([1, 0], [-1, 0]), -1)
        with self.assertRaises(ValueError):
            cosine([0, 0], [1, 0])
        with self.assertRaises(ValueError):
            cosine([1], [1, 2])

    def test_three_rankings_preserve_cases_and_distinguish_the_product(self):
        rows = [dict(id="a", prominence=100, cosine=.2),
                dict(id="b", prominence=60, cosine=.8),
                dict(id="c", prominence=0, cosine=1),
                dict(id="d", prominence=90, cosine=-.1)]
        result = rank_rows(rows)
        self.assertEqual(result["prominence"], ["a", "d", "b", "c"])
        self.assertEqual(result["cosine"], ["c", "b", "a", "d"])
        self.assertEqual(result["product"], ["b", "a", "c", "d"])
        self.assertEqual(rows[-1]["product"], -9)


class ProminenceSourceReplacementTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def test_node_description_provenance_preserves_cached_encoder_inputs(self):
        from sse_multivector import prominence_cosine as pc
        self.prepare_source_cases()
        self.compare_cli('baseline-encoding', '--include-subject')
        baseline = self.root/'baseline-encoding'
        before = pc.read(baseline/'worker-request.json')['notes']
        rows = [(note, subject) for note in before for subject in note['subjects']]
        (baseline/'result').mkdir()
        (baseline/'result/raw-vectors.f32le').write_bytes(struct.pack(
            '<' + 'f' * (2 * len(rows)), *([1., 0.] * len(rows))))
        (baseline/'result/worker-receipt.json').write_text(json.dumps(dict(self.encoder,
            request_sha256=pc.sha(baseline/'worker-request.json'),
            proposal_sha256=pc.sha(baseline/'plan.json'),
            rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n, s in rows])))
        pc.collect(baseline)
        description = dict(node_id='bitcoin', node_title='Bitcoin',
                           description='Bitcoin transactions, privacy and block transmission.')
        self.write('descriptions.json', dict(schema_version=1, nodes=[description]))
        source = pc.read(self.root/'source.json')
        source['descriptions'] = 'descriptions.json'
        self.write('source.json', source)
        self.prepare('described')
        answer = dict(missing_meaning='', prominence=100, allocation=[dict(
            meaning='Bitcoin.', points=100, represented=100, missing=0)])
        self.cli('run', 'described', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        command = [sys.executable, str(Path(__file__).with_name('prominence_cosine.py')),
            'prepare', str(self.root/'described-comparison'), '--experiments', str(self.root/'described'),
            '--worker-config', str(self.root/'encoder.json'), '--include-subject',
            '--post-order', 'highest', '--reuse-encoding', str(self.root/'baseline-encoding')]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(pc.read(self.root/'described-comparison/worker-request.json')['notes'], before)
        saved = pc.read(self.root/'described-comparison/plan.json')
        self.assertEqual(saved['protected'][str(self.root/'descriptions.json')],
                         pc.sha(self.root/'descriptions.json'))
        pc.collect(self.root/'described-comparison')
        reused = pc.read(self.root/'described-comparison/comparison.json')
        original = pc.read(baseline/'comparison.json')
        self.assertEqual(reused['raw_vectors_sha256'], original['raw_vectors_sha256'])
        self.assertEqual(reused['posts'], original['posts'])
        case = pc.experiment.report(self.root/'described')['cases'][0]
        variants = [dict(node_description='Conflicting meaning.'),
            dict(node_description_record={**description, 'node_id': 'other'}),
            dict(node_description_record={**description, 'node_title': 'Other'}),
            dict(description_source={**case['evidence']['description_source'], 'sha256': '0'*64})]
        for number, changes in enumerate(variants + ['node_description',
                'node_description_record', 'description_source']):
            invalid = {**case, 'evidence': dict(case['evidence'])}
            if isinstance(changes, str):
                del invalid['evidence'][changes]
            else:
                invalid['evidence'].update(changes)
            args = Namespace(output=self.root/f'invalid-{number}', vectors=None,
                experiments=[self.root/'described'], worker_config=self.root/'encoder.json',
                replay=[], post_order='highest', include_subject=True)
            with self.subTest(changes=changes), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [invalid]}), \
                 self.assertRaises(ValueError):
                pc.prepare(args)
            self.assertFalse(args.output.exists())
        (self.root/'descriptions.json').write_text('{}')
        command[3] = str(self.root/'tampered-description')
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('source changed', result.stderr)

    def prepare_source_cases(self):
        self.source_text = 'When running a node, use Tor.\n\nSparrow helps.'
        self.post = '☕ ' + self.source_text
        self.write('subjects.json', {'notes': [dict(note_id='a'*64,
            text=self.post, subjects=[dict(id=sid, subject='Bitcoin node privacy.',
                context=context) for sid, context in (
                    ('SP1', 'Running a node over Tor.'),
                    ('SP2', 'Sparrow helps with node privacy.'))]),
            dict(note_id='d'*64, text='Bitcoin blocks propagate.', subjects=[dict(
                id='SP3', subject='Bitcoin block transmission.',
                context='A Bitcoin block is transmitted.')])]})
        self.write('hierarchy.json', {'graph': {'nodes': [
            dict(group='bitcoin', title='Bitcoin')]}})
        self.write('source.json', dict(schema_version=1, subjects='subjects.json',
            hierarchy='hierarchy.json', selections=[dict(id=cid, node_id='bitcoin',
                note_id=note, subject_id=sid) for cid, note, sid in (
                    ('privacy1', 'a'*64, 'SP1'), ('privacy2', 'a'*64, 'SP2'),
                    ('control', 'd'*64, 'SP3'))]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_contexts', path='source.json',
                              prominence_basis='node_title')
        self.write('spec.json', spec)
        self.prompt.write_text('GENERIC PROMPT CONTEXT PROMINENCE\n{INPUT_JSON}')
        self.prepare()
        answer = dict(missing_meaning='', prominence=100, allocation=[dict(
            meaning='Bitcoin.', points=100, represented=100, missing=0)])
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        self.encoder = dict(checkpoint_sha256='b'*64,
            base_model_artifact_tree_sha256='c'*64, model={'dimensions': 2},
            note_batch_size=1)
        self.write('encoder.json', dict(self.encoder, device='cpu'))
        self.originals = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.original_calls = self.calls()

    def compare_cli(self, destination, *options, ok=True):
        result = subprocess.run([sys.executable,
            str(Path(__file__).with_name('prominence_cosine.py')),
            'prepare', str(self.root/destination), '--experiments', str(self.root/'E1'),
            '--worker-config', str(self.root/'encoder.json'), '--post-order', 'highest',
            *options], cwd=self.root, env=os.environ, text=True, capture_output=True,
            timeout=30)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_source_replacement_encodes_copy_preserves_sources_and_collects(self):
        from sse_multivector import prominence_cosine as pc
        self.prepare_source_cases()
        options = []
        for cid in ('privacy1', 'privacy2'):
            options += ['--relevance-source-text', cid, self.source_text,
                        '--relevance-source-replace', cid, 'a node', 'a Bitcoin node']
        self.compare_cli('comparison', *options)
        output = self.root/'comparison'
        plan = pc.read(output/'plan.json')
        rows = [(n, s) for n in pc.read(output/'worker-request.json')['notes']
                for s in n['subjects']]
        self.assertEqual(len(rows), 3)
        cases = {c['id']: c for c in plan['cases']}
        self.assertEqual(cases['privacy1']['mask_row'], cases['privacy2']['mask_row'])
        edited = self.source_text.replace('a node', 'a Bitcoin node', 1)
        for cid in ('privacy1', 'privacy2'):
            case = cases[cid]
            note, selection = rows[case['mask_row']]
            self.assertEqual(note['text'], edited)
            self.assertEqual(selection['byte_spans'], [[0, len(edited.encode())]])
            self.assertEqual(case['relevance_source_text'], self.source_text)
            self.assertEqual(case['relevance_source_spans'], [[4, len(self.post.encode())]])
            self.assertEqual(case['relevance_source_replacement'],
                             dict(before='a node', after='a Bitcoin node'))
            self.assertEqual(case['relevance_text'], edited)
            self.assertEqual(case['prominence'], 100)
        control = cases['control']
        self.assertEqual(rows[control['mask_row']][0]['text'],
                         'A Bitcoin block is transmitted.')
        self.assertNotIn('relevance_source_replacement', control)
        fresh = [(1, 0)] * len(rows)
        fresh[cases['privacy1']['mask_row']] = (0, 1)
        result = output/'result'
        result.mkdir()
        (result/'raw-vectors.f32le').write_bytes(struct.pack(
            '<'+'f'*(2*len(fresh)), *(value for row in fresh for value in row)))
        (result/'worker-receipt.json').write_text(json.dumps(dict(self.encoder,
            request_sha256=pc.sha(output/'worker-request.json'),
            proposal_sha256=pc.sha(output/'plan.json'),
            rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in rows])))
        pc.collect(output)
        comparison = pc.read(output/'comparison.json')
        privacy = next(p for p in comparison['posts']['bitcoin'] if p['note_id']=='a'*64)
        self.assertEqual(privacy['linear_product'], 50)
        self.assertEqual(privacy['linear_product_case'], 'privacy1')
        for case in comparison['groups']['bitcoin']:
            if case['id'].startswith('privacy'):
                self.assertEqual(case['relevance_text'], edited)
                self.assertEqual(case['relevance_source_text'], self.source_text)
        self.assertEqual(self.calls(), self.original_calls)
        for path, content in self.originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_source_replacement_refuses_unbound_ambiguous_or_empty_copies(self):
        self.prepare_source_cases()
        source = ['--relevance-source-text', 'privacy1', self.source_text]
        replacement = ['--relevance-source-replace', 'privacy1', 'a node', 'a Bitcoin node']
        invalid = [
            (replacement, 'requires --relevance-source-text'),
            (source + replacement + replacement, 'duplicate relevance source replacement'),
            (source + ['--relevance-source-replace', 'privacy1', '', 'Bitcoin'], 'nonempty phrase'),
            (source + ['--relevance-source-replace', 'privacy1', 'a node', 'a node'], 'nonempty phrase'),
            (source + ['--relevance-source-replace', 'privacy1', 'coffee', 'Bitcoin'], 'exactly once'),
            (source + ['--relevance-source-replace', 'privacy1', 'o', 'Bitcoin'], 'exactly once'),
            (source + ['--relevance-source-replace', 'privacy1', self.source_text, ''], 'nonempty relevance'),
            (['--relevance-source-text', 'privacy1', self.source_text.replace('a node', 'a Bitcoin node')],
             'exact nonempty post fragment'),
            (source + replacement + ['--include-inverse'], 'no literal inverse'),
            (source + replacement + ['--include-subject'], 'cannot combine'),
            (['--relevance-source-text', 'missing', self.source_text,
              '--relevance-source-replace', 'missing', 'a node', 'a Bitcoin node'],
             'unknown relevance source'),
            (source + replacement + ['--only', 'control'], 'unknown relevance source'),
        ]
        for index, (options, message) in enumerate(invalid):
            with self.subTest(options=options):
                name = f'bad-{index}'
                result = self.compare_cli(name, *options, ok=False)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root/name).exists())
        self.assertEqual(self.calls(), self.original_calls)
        for path, content in self.originals.items():
            self.assertEqual(path.read_bytes(), content)

    def test_source_replacement_cannot_reuse_original_text_encoding(self):
        self.prepare_source_cases()
        source = ['--relevance-source-text', 'privacy1', self.source_text,
                  '--relevance-source-text', 'privacy2', self.source_text]
        self.compare_cli('original', *source)
        result = self.compare_cli('changed', *source,
            '--relevance-source-replace', 'privacy1', 'a node', 'a Bitcoin node',
            '--relevance-source-replace', 'privacy2', 'a node', 'a Bitcoin node',
            '--reuse-encoding', str(self.root/'original'), ok=False)
        self.assertIn('reused encoder notes differ', result.stderr)
        self.assertFalse((self.root/'changed').exists())
        self.assertEqual(self.calls(), self.original_calls)
        for path, content in self.originals.items():
            self.assertEqual(path.read_bytes(), content)


class ProminencePoolingTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls
    prepare_source_cases = ProminenceSourceReplacementTests.prepare_source_cases
    compare_cli = ProminenceSourceReplacementTests.compare_cli

    def prepare_pooling_cases(self):
        self.prepare_source_cases()
        self.encoder['model'] = dict(base_model='fixture/t5', dimensions=2,
            maximum_tokens=512, pooling='selected-contextual-token-mean-linear-relu-linear-v1')
        self.write('encoder.json', dict(self.encoder, device='cpu'))
        self.originals[self.root/'encoder.json'] = (self.root/'encoder.json').read_bytes()

    def write_vectors(self, output):
        from sse_multivector import prominence_cosine as pc
        plan = pc.read(output/'plan.json')
        rows = [(n, s) for n in pc.read(output/'worker-request.json')['notes']
                for s in n['subjects']]
        fresh = [(1, 0)] * len(rows)
        fresh[plan['cases'][0]['mask_row']] = (0, 1)
        result = output/'result'
        result.mkdir()
        (result/'raw-vectors.f32le').write_bytes(struct.pack(
            '<'+'f'*(2*len(fresh)), *(v for row in fresh for v in row)))
        receipt = dict(plan['encoder'], request_sha256=pc.sha(output/'worker-request.json'),
            proposal_sha256=pc.sha(output/'plan.json'),
            rows=[dict(note_id=n['note_id'], subject_id=s['subject_id']) for n,s in rows])
        (result/'worker-receipt.json').write_text(json.dumps(receipt))

    def test_pooling_override_keeps_inputs_and_scores_and_binds_collection(self):
        from sse_multivector import prominence_cosine as pc
        self.prepare_pooling_cases()
        self.compare_cli('projected')
        self.compare_cli('means', '--pooling', 'selected-contextual-token-mean-v1')
        projected, means = self.root/'projected', self.root/'means'
        before, after = pc.read(projected/'plan.json'), pc.read(means/'plan.json')
        self.assertEqual(before['cases'], after['cases'])
        self.assertEqual(before['title_rows'], after['title_rows'])
        self.assertEqual(pc.read(projected/'worker-request.json')['notes'],
                         pc.read(means/'worker-request.json')['notes'])
        expected = dict(self.encoder['model'], pooling='selected-contextual-token-mean-v1')
        self.assertEqual(after['encoder']['model'], expected)
        self.assertEqual(pc.read(means/'worker-config.json')['model'], expected)
        self.write_vectors(means)
        pc.collect(means)
        comparison = pc.read(means/'comparison.json')
        self.assertEqual(comparison['parity'], {})
        self.assertEqual(comparison['groups']['bitcoin'][0]['linear_product'], 50)
        receipt_path = means/'result/worker-receipt.json'
        receipt = pc.read(receipt_path)
        receipt['model'] = self.encoder['model']
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'worker identity differs: model'):
            pc.collect(means)
        for path, content in self.originals.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(self.calls(), self.original_calls)

    def test_pooling_override_refuses_replay_and_wrong_encoding_reuse(self):
        self.prepare_pooling_cases()
        self.compare_cli('projected')
        self.write_vectors(self.root/'projected')
        from sse_multivector import prominence_cosine as pc
        pc.collect(self.root/'projected')
        result = self.compare_cli('wrong-reuse', '--pooling',
            'selected-contextual-token-mean-v1', '--reuse-encoding',
            str(self.root/'projected'), ok=False)
        self.assertIn('reused encoder identity differs: model', result.stderr)
        self.assertFalse((self.root/'wrong-reuse').exists())
        result = self.compare_cli('replay', '--pooling',
            'selected-contextual-token-mean-v1', '--replay', 'V1', ok=False)
        self.assertIn('pooling override', result.stderr)
        self.assertFalse((self.root/'replay').exists())
        result = self.compare_cli('unknown', '--pooling', 'unknown', ok=False)
        self.assertIn('invalid choice', result.stderr)
        self.assertFalse((self.root/'unknown').exists())


if __name__ == "__main__":
    unittest.main()
