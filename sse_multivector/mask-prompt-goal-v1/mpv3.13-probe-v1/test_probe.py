import json
import unittest

from probe import build_config, previous


class DefinitionsProbeTest(unittest.TestCase):
    def test_only_approved_definitions_change_in_the_six_requests(self):
        baseline = json.loads((previous.HERE / 'config.json').read_text())
        revised = build_config()
        self.assertEqual(len(revised['prompts']), 6)
        edit = json.loads((previous.HERE.parent / 'mpv3.13-draft-v1/prompt-edits.json').read_text())['edits'][0]
        for before, after in zip(baseline['prompts'], revised['prompts']):
            self.assertEqual(before['prompt_id'], after['prompt_id'])
            self.assertEqual(after['text'].replace(edit['new'], edit['old']), before['text'])
        self.assertEqual({k: v for k, v in revised.items() if k != 'prompts'},
                         {k: v for k, v in baseline.items() if k != 'prompts'})


if __name__ == '__main__':
    unittest.main()
