"""Unsigned hierarchy publication preserves the saved graph without a signer."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import tracemalloc
import unittest
import uuid

from sse_multivector import canonical_hierarchy_nostr as nostr


class UnsignedHierarchyTests(unittest.TestCase):
    def node(self, identifier, *, parents=(), entries=(), note_ids=()):
        return dict(id=identifier, subject='Heading '+identifier, meaning='Definition '+identifier,
                    parents=list(parents), entries=[dict(note_id=note) for note in entries],
                    note_ids=list(note_ids))

    def test_saved_definition_and_synthetic_note_ids_are_exported_without_signing(self):
        state = {'nodes': [
            {'id': 'C001', 'subject': 'Coffee', 'meaning': 'Coffee cultivation.',
             'parents': [], 'entries': [{'note_id': 'historical-post'}]}]}

        events = list(nostr.unsigned_events(state))

        self.assertEqual(len(events), 2)
        self.assertEqual(set(events[0]), {'kind', 'tags', 'content'})
        self.assertEqual(events[0]['kind'], nostr.NODE_KIND)
        self.assertEqual(events[0]['content'], 'Coffee cultivation.')
        self.assertIn(['title', 'Coffee'], events[0]['tags'])
        self.assertIn(['e', 'historical-post'], events[0]['tags'])
        self.assertEqual(events[1], {
            'kind': nostr.ENTRY_KIND,
            'tags': [['child', events[0]['tags'][0][1]]], 'content': ''})

    def test_dag_edges_root_order_and_only_ancestor_duplicate_notes_are_preserved(self):
        state = {'nodes': [
            self.node('left', entries=['shared', 'left-only'], note_ids=['extra']),
            self.node('right', entries=['shared', 'right-only']),
            self.node('leaf', parents=['left', 'right'], entries=['shared', 'shared']),
            self.node('sibling', parents=['left'], entries=['shared'])],
            'shape': {'roots': ['right', 'left']}}
        original = copy.deepcopy(state)

        events = list(nostr.unsigned_events(state))

        by_title = {event['tags'][1][1]: event for event in events[:-1]}
        by_id = {identifier: by_title['Heading '+identifier]
                 for identifier in ['left', 'right', 'leaf', 'sibling']}
        ids = {identifier: event['tags'][0][1] for identifier, event in by_id.items()}
        children = lambda event: [tag for tag in event['tags'] if tag[0] == 'child']
        notes = lambda event: [tag[1] for tag in event['tags'] if tag[0] == 'e']
        self.assertEqual(children(by_id['left']), [['child', ids['leaf']],
                                                ['child', ids['sibling']]])
        self.assertEqual(children(by_id['right']), [['child', ids['leaf']]])
        self.assertEqual(events[-1]['tags'], [['child', ids['right']], ['child', ids['left']]])
        self.assertEqual(notes(by_id['left']), ['left-only', 'extra'])
        self.assertEqual(notes(by_id['right']), ['right-only'])
        self.assertEqual(notes(by_id['leaf']), ['shared'])
        self.assertEqual(notes(by_id['sibling']), ['shared'])
        self.assertEqual(state, original)
        # Every output is directly serializable; all child links are unsigned UUIDs.
        json.dumps(events)
        for event in events:
            self.assertEqual(set(event), {'kind', 'tags', 'content'})
            for tag in children(event):
                self.assertEqual(len(tag), 2)
                self.assertEqual(str(uuid.UUID(tag[1])), tag[1])

    def test_menu_nodes_and_file_scoped_ids_ignore_private_paths_and_status(self):
        state = dict(nodes=[self.node('raw')], menu=dict(nodes=[self.node('retained')]),
                     corpus='/private/location/notes.json', status='stopped')

        events = list(nostr.unsigned_events(state))
        state.update(corpus='/other/location/notes.json', status='complete')

        self.assertEqual(events, list(nostr.unsigned_events(state)))
        self.assertEqual(events[0]['tags'][1], ['title', 'Heading retained'])
        self.assertEqual(events[0]['tags'][0], ['d', str(uuid.uuid5(
            nostr.UNSIGNED_NAMESPACE, 'retained'))])

    def test_empty_failed_state_retains_an_empty_entry(self):
        self.assertEqual(list(nostr.unsigned_events(dict(status='failed', nodes=[]))), [
            dict(kind=nostr.ENTRY_KIND, tags=[], content='')])

    def test_unsigned_data_accepts_more_than_500_direct_note_references(self):
        notes = [f'synthetic-{index}' for index in range(601)]

        events = list(nostr.unsigned_events({'nodes': [self.node('root', note_ids=notes)]}))

        self.assertEqual([tag[1] for tag in events[0]['tags'] if tag[0] == 'e'], notes)

    def test_malformed_saved_graphs_fail_before_emitting_any_record(self):
        valid = {'nodes': [self.node('root')]}
        cases = [
            (dict(nodes=[self.node('root'), self.node('root')]), 'unique'),
            (dict(nodes=[self.node('root', parents=['unknown'])]), 'unknown'),
            (dict(nodes=[self.node('root', parents=['root'])]), 'cycle'),
            (dict(nodes=[self.node('a', parents=['b']), self.node('b', parents=['a'])]), 'cycle'),
            (dict(valid, shape={'roots': []}), 'roots'),
            (dict(valid, shape={'roots': ['root', 'root']}), 'roots'),
            (dict(valid, shape={'roots': ['unknown']}), 'roots'),
            (dict(valid, shape={'roots': 'root'}), 'roots'),
            (dict(valid, shape=[]), 'shape'),
            (dict(valid, menu=[]), 'menu'),
            (dict(nodes={}), 'nodes'),
        ]
        for field, value, message in [
            ('id', '', 'IDs'), ('subject', '', 'title'), ('subject', [], 'title'),
            ('meaning', None, 'meaning'), ('meaning', ' ', 'meaning'),
            ('parents', 'root', 'parents'), ('parents', ['root', 'root'], 'unique'),
            ('entries', None, 'memberships'), ('entries', [{}], 'memberships'),
            ('entries', [{'note_id': ''}], 'memberships'),
            ('note_ids', 'note', 'memberships'), ('note_ids', [None], 'memberships')]:
            node = self.node('root')
            node[field] = value
            cases.append((dict(nodes=[node]), message))
        for state, message in cases:
            with self.subTest(state=state):
                events = nostr.unsigned_events(state)
                with self.assertRaisesRegex(ValueError, message):
                    next(events)

    def test_deep_graph_does_not_keep_a_membership_set_for_every_ancestor(self):
        nodes = [self.node(f'node-{index}', parents=[f'node-{index-1}'] if index else [])
                 for index in range(1200)]
        nodes[-1]['note_ids'] = [f'note-{index}' for index in range(400)]
        tracemalloc.start()
        try:
            count = sum(1 for event in nostr.unsigned_events(dict(nodes=nodes)))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(count, 1201)
        self.assertLess(peak, 8*1024*1024,
                        'a deep graph retained copied memberships for every ancestor')

    @unittest.skipUnless(shutil.which('nak'), 'offline signed-export regression requires nak')
    def test_existing_signed_export_keeps_signed_links_and_empty_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trial = root/'trial'
            trial.mkdir()
            note_id = hashlib.sha256(b'original public test post').hexdigest()
            corpus = root/'corpus.json'
            corpus.write_text(json.dumps({'notes': [{'note_id': note_id, 'text': 'Original post.'}]}))
            nodes = [self.node('parent', entries=[note_id]),
                     self.node('child', parents=['parent'], entries=[note_id])]
            (trial/'state.json').write_text(json.dumps(dict(
                nodes=nodes, status='complete', corpus=str(corpus),
                sources={str(corpus): hashlib.sha256(corpus.read_bytes()).hexdigest()})))
            secret = root/'test-key'
            # Public fixture material; never an account or user credential.
            secret.write_text(hashlib.sha256(b'public offline signing test fixture').hexdigest())
            secret.chmod(0o600)

            nostr.export_nostr(trial, root/'signed.jsonl', secret, created_at=1)

            events = [json.loads(line) for line in (root/'signed.jsonl').read_text().splitlines()]
            self.assertEqual([event['kind'] for event in events],
                             [nostr.NODE_KIND, nostr.NODE_KIND, nostr.ENTRY_KIND])
            for event in events:
                self.assertEqual(event['content'], '')
                self.assertEqual(len(event['id']), 64)
                self.assertEqual(len(event['pubkey']), 64)
                self.assertEqual(len(event['sig']), 128)
            self.assertEqual([tag for tag in events[1]['tags'] if tag[0] == 'child'],
                             [['child', events[0]['tags'][0][1], events[0]['id']]])
            self.assertEqual(events[-1]['tags'],
                             [['child', events[1]['tags'][0][1], events[1]['id']]])


if __name__ == '__main__':
    unittest.main()
