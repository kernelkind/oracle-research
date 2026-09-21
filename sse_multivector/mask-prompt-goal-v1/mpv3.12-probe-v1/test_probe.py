import json
import unittest

from probe import build_config, previous


class ScopeProbeTest(unittest.TestCase):
    def test_only_mpv312_edits_change_saved_requests(self):
        original = json.loads((previous.HERE / 'config.json').read_text())
        revised = build_config()
        self.assertEqual(len(revised['prompts']), 6)
        edits = json.loads((previous.HERE.parent / 'mpv3.12-draft-v1/prompt-edits.json').read_text())['edits']
        for before, after in zip(original['prompts'], revised['prompts']):
            self.assertEqual(before['prompt_id'], after['prompt_id'])
            restored = after['text']
            for edit in reversed(edits):
                restored = restored.replace(edit['new'], edit['old'])
            self.assertEqual(restored, before['text'])
            self.assertNotIn('A fragment is one continuous range', after['text'])
        self.assertEqual({k: v for k, v in revised.items() if k != 'prompts'},
                         {k: v for k, v in original.items() if k != 'prompts'})


if __name__ == '__main__':
    unittest.main()
