"""Saved TRUE orchestration preserves inputs and reuses verified answers."""
import json
from pathlib import Path
import tempfile
import unittest

from hierarchy_build import consolidate_nodes, titles_from_report, save
from hierarchy_true_scoring import prepare, collect, verify
from test_hierarchy_build import report_for
from test_true_graph_categories import fixture
from true_category_graph import prepare_inputs
from hierarcaps_mask_probe import sha256


class HierarchyTrueScoringTests(unittest.TestCase):
    def setup_inputs(self, root):
        from hierarchy_true_scoring import CODE, SHARED
        titles_dir = root/'titles'; titles_dir.mkdir()
        nodes = consolidate_nodes(fixture()['canonical']['source_packets'])
        report = report_for(nodes['source_packets'])
        titles = titles_from_report(nodes['source_packets'], report)
        pairs = prepare_inputs(titles)
        for name, value in [('nodes',nodes),('title-report',report),('titles',titles),('true-inputs',pairs)]:
            save(titles_dir/f'{name}.json', value)
        bundle = root/'cache'; bundle.mkdir(); run = bundle/'run'; run.mkdir()
        save(run/'config.json', {'experiment':'test', 'device':'cpu'})
        save(run/'model-files.json', {'synthetic':'fixture'})
        reference = dict(config=json.loads((run/'config.json').read_text()),
            model_files_sha256=sha256(run/'model-files.json'),
            source_sha256={n:sha256(CODE/n) for n in SHARED})
        save(bundle/'reference.json',reference)
        rows = [dict(r, predicted=False, generated_text='0', generated_token_ids=[0,632,1],
                     eos_terminated=True, entailment_score=.1, threshold_predicted=False) for r in pairs]
        (run/'scores.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        save(run/'completion.json', {'scores_sha256':sha256(run/'scores.jsonl')})
        protected = {str(CODE/n):sha256(CODE/n) for n in SHARED}
        save(bundle/'plan.json', {'protected_sha256':protected,'cache_sources':[]})
        save(run/'started.json', {'plan_sha256':sha256(bundle/'plan.json')})
        return titles_dir, bundle, pairs

    def test_reuse_all_and_collect_without_inference(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); titles,bundle,pairs=self.setup_inputs(root)
            out=root/'scoring'
            plan=prepare(titles,bundle,out)
            self.assertEqual(plan['fresh_inputs'],0)
            self.assertEqual(plan['directions'],len(pairs))
            rows=collect(out)
            self.assertEqual(len(rows),len(pairs))
            self.assertTrue(all(r['score_origin']['reused'] for r in rows))
            self.assertFalse((out/'run').exists())
            with self.assertRaises(FileExistsError): prepare(titles,bundle,out)

    def test_frozen_inputs_and_cached_receipts_cannot_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); titles,bundle,_=self.setup_inputs(root)
            out=root/'scoring'; prepare(titles,bundle,out)
            (out/'inputs.json').write_text('[]')
            with self.assertRaises(ValueError): verify(out)
            (bundle/'run/scores.jsonl').write_text('')
            with self.assertRaises(ValueError): prepare(titles,bundle,root/'bad')

    def test_missing_answers_block_collection_until_complete_fresh_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); titles,bundle,pairs=self.setup_inputs(root)
            cached=bundle/'run/scores.jsonl'
            rows=[json.loads(line) for line in cached.read_text().splitlines()]
            missing=rows.pop()
            cached.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            (bundle/'run/completion.json').write_text(json.dumps({'scores_sha256':sha256(cached)}))
            out=root/'scoring'; plan=prepare(titles,bundle,out)
            self.assertEqual(plan['fresh_inputs'],1)
            with self.assertRaises(FileNotFoundError): collect(out)
            self.assertFalse((out/'scores.json').exists())
            run=out/'run'; run.mkdir()
            for name in ('config.json','model-files.json'):
                (run/name).write_bytes((bundle/'run'/name).read_bytes())
            (run/'scores.jsonl').write_text(json.dumps(missing)+'\n')
            save(run/'completion.json',{'scores_sha256':sha256(run/'scores.jsonl')})
            scores=collect(out)
            self.assertEqual(len(scores),len(pairs))
            self.assertEqual(sum(not r['score_origin']['reused'] for r in scores),1)


if __name__ == '__main__': unittest.main()
