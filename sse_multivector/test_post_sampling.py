"""Exercise the native offline selection CLI with source-bound receipts."""
import hashlib, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PostSamplingTests(unittest.TestCase):
    def cli(self, root, *arguments):
        return subprocess.run([sys.executable,str(ROOT/'sse_multivector/experiment.py'),*map(str,arguments)],
            cwd=ROOT,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))

    def test_automatic_sample_uses_only_mechanical_rules_and_preserves_hash_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            seed = 'automatic-test-v1'
            records = [dict(note_id=f'{i:064x}', pubkey='a'*64,
                text=f'Original post {i}', root_non_quote=True,
                canonical_event_id_verified=True, language_decision='keep_english',
                event=dict(id=f'{i:064x}', content=f'Original post {i}')) for i in range(8)]
            for r in records:
                r['selection_order_sha256'] = hashlib.sha256(seed.encode()+bytes.fromhex(r['note_id'])).hexdigest()
            records.sort(key=lambda r: (r['selection_order_sha256'], r['note_id']))
            records[0]['root_non_quote'] = False
            records[1]['text'] = ' \n '
            records[2]['language_decision'] = 'exclude_non_english'
            records[3]['text'] = 'Long source post'
            # These near-identical texts and repeated author must not trigger curation.
            records[4]['text'] = 'See nostr:'+'b'*64
            records[5]['text'] = records[4]['text']
            for r in records:
                r['event']['content'] = r['text']
            source = root/'candidates.jsonl'
            source.write_text(''.join(json.dumps(r)+'\n' for r in records))
            counts = dict(source_sha256=sha(source), maximum_tokens=512, records=[dict(
                note_id=r['note_id'], text_sha256=hashlib.sha256(r['text'].encode()).hexdigest(),
                tokens=513 if i == 3 else 20) for i, r in enumerate(records)])
            tokens = root/'tokens.json'; tokens.write_text(json.dumps(counts))
            receipt = root/'export.json'; receipt.write_text(json.dumps(dict(
                canonical_event_ids_verified=True, candidates_sha256=sha(source),
                config=dict(selection_domain=seed))))
            config = dict(selection_mode='automatic', candidates=str(source), token_counts=str(tokens),
                candidate_manifest=str(receipt), seed=seed, count=3)
            spec = root/'spec.json'; spec.write_text(json.dumps(config))
            result = self.cli(root, 'freeze-post-sample', root/'sample', '--spec', spec)
            self.assertEqual(result.returncode, 0, result.stderr)
            selected = json.loads((root/'sample/notes.json').read_text())['notes']
            self.assertEqual([n['note_id'] for n in selected], [r['note_id'] for r in records[4:7]])
            self.assertEqual([n['text'] for n in selected], [r['text'] for r in records[4:7]])
            manifest = json.loads((root/'sample/manifest.json').read_text())
            self.assertEqual(manifest['selection_mode'], 'automatic')
            self.assertEqual(manifest['review_needed'], 0)
            self.assertEqual(manifest['exclusions'], dict(reply_or_quote=1, empty_text=1,
                source_language_filter=1, over_512_tokens=1))
            self.assertEqual(manifest['authors'], 1)
            originals = [json.loads(s) for s in (root/'sample/original-events.jsonl').read_text().splitlines()]
            self.assertEqual(originals, [r['event'] for r in records[4:7]])
            # Seed, source and token evidence cannot silently drift.
            config['seed'] = 'different-seed'
            spec.write_text(json.dumps(config))
            result = self.cli(root, 'freeze-post-sample', root/'bad-seed', '--spec', spec)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('selection domain', result.stderr)
            self.assertFalse((root/'bad-seed').exists())
            config['seed'] = seed
            spec.write_text(json.dumps(config))
            counts['records'][4]['text_sha256'] = '0'*64
            tokens.write_text(json.dumps(counts))
            result = self.cli(root, 'freeze-post-sample', root/'bad-tokens', '--spec', spec)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('token receipt text', result.stderr)
            self.assertFalse((root/'bad-tokens').exists())

    def test_preview_requires_reviews_and_freeze_excludes_references_replies_and_copies(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            texts=['Address reply', 'Quote post', 'Read nostr:'+'a'*64+' for background', 'Identical copied sentence',
                   'Identical copied sentence', 'Apricots\u2028taste wonderful.', 'Bicycle wheels need repairs.',
                   'Clarinets require practice.', 'Dragons belong in stories.', 'Elephants have trunks.']
            records=[dict(note_id=f'{i:064x}',pubkey=f'{i:064x}',text=text,selection_order_sha256=f'{i:064x}',
                root_non_quote=i>1,canonical_event_id_verified=True,language_decision='keep_english') for i,text in enumerate(texts)]
            source=root/'candidates.jsonl';source.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
            tokens=root/'tokens.json';tokens.write_text(json.dumps(dict(source_sha256=sha(source),maximum_tokens=512,
                records=[dict(note_id=r['note_id'],text_sha256=hashlib.sha256(r['text'].encode()).hexdigest(),tokens=20) for r in records])))
            prior=root/'prior.json';prior.write_text(json.dumps(dict(notes=[])))
            spec=root/'spec.json';spec.write_text(json.dumps(dict(candidates=str(source),token_counts=str(tokens),prior_review=str(prior),
                reviews=str(root/'reviews.jsonl'),development_sources=[],seed='test',splits=dict(train=2,validation=1,test=1))))
            r=self.cli(root,'freeze-post-sample',root/'incomplete','--spec',spec)
            self.assertNotEqual(r.returncode,0)
            self.assertFalse((root/'incomplete').exists())
            r=self.cli(root,'freeze-post-sample',root/'preview','--spec',spec,'--preview')
            self.assertEqual(r.returncode,0,r.stderr)
            with (root/'preview/review-needed.jsonl').open() as f:
                pending=[json.loads(s) for s in f]
            self.assertEqual([r['ordinal'] for r in pending],[4,6,7,8])
            r=self.cli(root,'review-post-sample',source,'--output',root/'reviews.jsonl','--accept','4,6-8',
                       '--forms','FACT:4,6-8','--reason','Full original prose is English.')
            self.assertEqual(r.returncode,0,r.stderr)
            r=self.cli(root,'freeze-post-sample',root/'sample','--spec',spec)
            self.assertEqual(r.returncode,0,r.stderr)
            manifest=json.loads((root/'sample/manifest.json').read_text())
            self.assertEqual(manifest['exclusions'],dict(reply_or_quote=2,inline_note_reference=1,repeated_template=1))
            # A saved review is immutable evidence rather than a silently replaced judgment.
            r=self.cli(root,'review-post-sample',source,'--output',root/'reviews.jsonl','--reject','4','--reason','changed opinion')
            self.assertNotEqual(r.returncode,0)
            self.assertIn('already has a saved review',r.stderr)

    def test_freeze_preserves_originals_and_keeps_development_authors_out_of_holdouts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); rows=[]
            for i in range(12):
                word=['apricots','bicycles','clarinets','dragons','elephants','flowers','gardens','horses','iguanas','jellyfish','kangaroos','lemons'][i]
                rows.append(dict(note_id=f'{i:064x}', pubkey=f'{i//2:064x}', text=f'{word} are the unique subject of this original post.',
                    selection_order_sha256=f'{i:064x}', root_non_quote=True, canonical_event_id_verified=True,
                    language_decision='keep_english'))
            candidates=root/'candidates.jsonl'; candidates.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            tokens=root/'tokens.json'; tokens.write_text(json.dumps(dict(source_sha256=sha(candidates),
                maximum_tokens=512, records=[dict(note_id=r['note_id'], text_sha256=hashlib.sha256(r['text'].encode()).hexdigest(),tokens=20) for r in rows])))
            review=root/'review.json'; review.write_text(json.dumps(dict(notes=[dict(r,include_in_pool=True,forms=['PERSONAL'],source=dict(origin='frozen-1000')) for r in rows])))
            exposed=root/'development.json'; exposed.write_text(json.dumps(dict(notes=[dict(note_id=rows[0]['note_id']),
                dict(note_id='f'*64,pubkey=rows[4]['pubkey'],text='A different earlier post by this author.') ])))
            config=root/'config.json'; config.write_text(json.dumps(dict(candidates=str(candidates), token_counts=str(tokens),
                prior_review=str(review), reviews=str(root/'reviews.jsonl'), development_sources=[str(exposed)],
                seed='fixed', splits=dict(train=8,validation=2,test=2))))
            result=subprocess.run([sys.executable,str(ROOT/'sse_multivector/experiment.py'),'freeze-post-sample',str(root/'sample'),
                '--spec',str(config)],cwd=ROOT,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(result.returncode,0,result.stderr)
            selected=json.loads((root/'sample/notes.json').read_text())['notes']
            self.assertEqual(len(selected),12)
            self.assertTrue(all(n['text']==rows[int(n['note_id'],16)]['text'] for n in selected))
            authors={}
            for n in selected: authors.setdefault(n['pubkey'],set()).add(n['origin']['split'])
            self.assertTrue(all(len(s)==1 for s in authors.values()))
            self.assertEqual(authors[rows[0]['pubkey']],{'train'})
            self.assertEqual(authors[rows[4]['pubkey']],{'train'})
            self.assertEqual(json.loads((root/'sample/manifest.json').read_text())['split_counts'],dict(train=8,validation=2,test=2))
            # An unrelated source edit cannot be accepted under an old token receipt.
            rows[0]['text']='Changed source text'; candidates.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            result=subprocess.run([sys.executable,str(ROOT/'sse_multivector/experiment.py'),'freeze-post-sample',str(root/'bad'),
                '--spec',str(config)],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('token receipt source',result.stderr)
            self.assertFalse((root/'bad').exists())

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__': unittest.main()
