"""Compact training inputs reach the real loader and deterministic training plan."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_data, distillation_run
from sse_multivector import test_distillation_data as data_fixtures


class PublishedTrainingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        data_fixtures.DistillationDataTests().prepare(self.root)
        splits = self.root/'splits.json'
        splits.write_text(json.dumps(dict(train=['3','2'], validation=['0','1'], test=['5','4'])))
        self.native = self.root/'native'
        self.manifest = distillation_data.prepare(self.root/'source.json', self.root/'annotations.json',
            self.root/'subjects.txt', None, 'ASv6.100', None, 2, 'fixture', self.native,
            tasks=('subjects',), splits_path=splits)
        self.published = self.root/'published'
        self.published.mkdir()
        metadata = self.published/'metadata'
        metadata.mkdir()
        files=[]
        for name, digest in self.manifest['outputs'].items():
            shutil.copyfile(self.native/name, self.published/name)
            files.append(dict(name=name, source_sha256=digest, bytes=(self.native/name).stat().st_size))
        rows=[dict(split=split, position=index, note_id=note)
              for split in ('train','evaluation','test')
              for index,note in enumerate(self.manifest[split+'_note_ids'])]
        payloads={'files.jsonl':files,'splits.jsonl':rows,'training-settings.jsonl':[]}
        bindings={}
        for name,values in payloads.items():
            path=metadata/name
            path.write_text(''.join(json.dumps(row)+'\n' for row in values))
            bindings[name]=dict(sha256=distillation_run.sha256(path), bytes=path.stat().st_size, records=len(values))
        distillation_run.write_json(metadata/'experiment.json',dict(schema_version=1,
            format='prepared-training-inputs-publication-v1', source_id='fixture',
            seed=self.manifest['seed'],tasks=self.manifest['tasks'],
            split_counts=dict(train=2,evaluation=2,test=2),
            subject_instruction_sha256=self.manifest['subject_instruction_sha256'],files=bindings))

    def test_published_data_preserves_all_native_rows_and_training_order(self):
        native=distillation_run.load_data(self.native)
        actual=distillation_run.load_data(self.published)
        for key in ('train','evaluation','test','references'):
            self.assertEqual(actual[key],native[key])
        config=dict(seed=17,batch_size=1,gradient_accumulation_steps=8,training_milestones=[2])
        self.assertEqual(distillation_run.subject_training_plan(actual,config),
                         distillation_run.subject_training_plan(native,config))
        self.assertEqual(actual['manifest']['source_format'],'prepared-training-inputs-publication-v1')
        self.assertEqual(actual['manifest']['publication_source_id'],'fixture')

    def test_changed_prepared_rows_or_split_metadata_are_rejected(self):
        with (self.published/'train.jsonl').open('ab') as stream:
            stream.write(b'{}\n')
        with self.assertRaisesRegex(ValueError,'hash'):
            distillation_run.load_data(self.published)
        shutil.copyfile(self.native/'train.jsonl',self.published/'train.jsonl')
        with (self.published/'metadata/splits.jsonl').open('ab') as stream:
            stream.write(b'{}\n')
        with self.assertRaisesRegex(ValueError,'hash'):
            distillation_run.load_data(self.published)

    def test_plan_checks_inputs_without_importing_the_model_runtime(self):
        config=json.loads((Path(__file__).parent/'distillation/subject-pilot-qwen-v1.json').read_bytes())
        config.update(data=str(self.published),training_milestones=[2])
        path=self.root/'config.json'
        distillation_run.write_json(path,config)
        original_import=__import__
        def offline_import(name,*args,**kwargs):
            if name.split('.')[0] in ('torch','transformers','peft'):
                raise AssertionError('plan loaded a model runtime')
            return original_import(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=offline_import):
            distillation_run.run(path,self.root/'plan',through='plan')
        result=distillation_run.read_json(self.root/'plan/input-check.json')
        self.assertEqual(result['split_counts'],dict(train=2,evaluation=2,test=2))
        self.assertEqual(result['model_weights_loaded'],False)
        self.assertEqual(distillation_run.read_json(self.root/'plan/training-plan.json')['milestones'],[2])

    def test_cli_prepares_and_checks_continuation_from_a_readers_own_checkpoint(self):
        config=json.loads((Path(__file__).parent/'distillation/subject-pilot-qwen-v1.json').read_bytes())
        config.update(data=str(self.published),training_milestones=[2])
        data=distillation_run.load_data(self.published)
        parent=self.root/'parent'
        distillation_run.write_json(parent/'manifest.json',dict(config=config,dataset=data['manifest'],local_model=None))
        plan=distillation_run.save_subject_training_plan(data,config,parent)
        checkpoint=parent/'checkpoints/checkpoint-2'
        checkpoint.mkdir(parents=True)
        for name in ('adapter_config.json','adapter_model.safetensors','training-state.pt'):
            (checkpoint/name).write_bytes(b'sealed checkpoint fixture')
        distillation_run.write_json(checkpoint/'training.json',dict(cursor=2,updates=1,
            consumed_note_ids=plan['note_ids'],manifest_sha256=distillation_run.sha256(parent/'manifest.json'),
            plan_sha256=distillation_run.sha256(parent/'training-plan.json')))
        distillation_run.write_json(checkpoint/'complete.json',distillation_run.file_hashes(checkpoint))
        destination=self.root/'continuation.json'
        command=[sys.executable,'-m','sse_multivector.distillation_run']
        result=subprocess.run([*command,'--prepare-continuation',str(parent),'--data',str(self.published),
            '--output',str(destination)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([*command,str(destination),'--through','plan','--output',str(self.root/'continuation-plan')],
                              capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        continued=distillation_run.read_json(self.root/'continuation-plan/training-plan.json')
        self.assertEqual(continued['milestones'],[2,4,6])
        self.assertEqual(continued['note_ids'][:2],plan['note_ids'])
