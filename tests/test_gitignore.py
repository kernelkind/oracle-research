"""Exercise the repository's actual ignore rules through Git, without staging."""

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GitIgnoreTests(unittest.TestCase):
    def ignored(self, paths):
        result = subprocess.run(
            ["git", "-c", "core.excludesFile=/dev/null", "check-ignore",
             "--no-index", "--stdin", "-z"],
            cwd=ROOT, input="\0".join(paths) + "\0",
            text=True, capture_output=True, check=False,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return set(result.stdout.rstrip("\0").split("\0")) if result.stdout else set()

    def test_experiment_data_and_blobs_are_ignored(self):
        paths = [
            "sse_multivector/hierarchy-refresh-v1/mask-run/results.jsonl",
            "sse_multivector/hierarchy-refresh-v1/hdbscan-request.json",
            "sse_multivector/hierarchy-refresh-v1/mask-run/manifest.json",
            "sse_multivector/hierarchy-refresh-v1/mask-run/prompt-output-schema.json",
            "sse_multivector/subject-prompt-goal-v1/future-run/subject-output-schema.json",
            "sse_multivector/hierarchy-refresh-v1/subject-config.json",
            "sse_multivector/hierarchy-refresh-v1/true-identical-title-run/scores.jsonl",
            "sse_multivector/hierarchy-refresh-v1/worker-result/raw-vectors.f32le",
            "sse_multivector/hierarchy-refresh-v1/true-identical-title-run/first-token-logits.npy",
            "sse_multivector/geometric-hierarchy-v1/future-run/vectors.npz",
            "sse_multivector/mask-prompt-goal-v1/pronoun-sse-v1/run/cosines.csv",
            "sse_multivector/mask-prompt-goal-v1/mpv3.43-nonfood-v1/review-session.json",
            "sse_multivector/mask-prompt-goal-v1/mpv3.43-nonfood-v1/.review-session.json.lock",
            "sse_multivector/subject-prompt-goal-v1/future-run/model.stdout",
            "sse_multivector/subject-prompt-goal-v1/future-run/model.stderr",
            "sse_multivector/subject-prompt-goal-v1/future-run/stderr.txt",
            "sse_multivector/hierarchy-refresh-v1/subject-execution.log",
            "sse_multivector/subject-prompt-goal-v1/asv6.31-museum-example-v1/generated-index.txt",
            "sse_multivector/subject-prompt-goal-v1/asv6.31-museum-example-v1/completed-index-v1.txt",
            "sse_multivector/future-experiment-v2/nested/results.json",
        ]
        self.assertEqual(self.ignored(paths), set(paths))

    def test_code_prompts_docs_and_schema_sources_remain_visible(self):
        paths = [
            "sse_multivector/hierarchy_refresh.py",
            "sse_multivector/mask_positions.py",
            "sse_multivector/run-hierarchy-refresh.sh",
            "sse_multivector/test_hierarchy_refresh.py",
            "sse_multivector/hierarchy-refresh-v1/prepare.py",
            "sse_multivector/hierarchy-refresh-v1/run/prepare.mjs",
            "sse_multivector/hierarchy-refresh-v1/run/README.md",
            "sse_multivector/mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md",
            "sse_multivector/subject-prompt-goal-v1/asv6.48/ASv6.48.md",
            "sse_multivector/hdbv2-node-description-probe-v21/prompt.txt",
            "sse_multivector/subject-prompt-goal-v1/example/output-schema.json",
            "sse_multivector/subject-prompt-goal-v1/example/schemas/selection.json",
            "sse_multivector/subject-prompt-goal-v1/example/prompt-versions.json",
            "sse_multivector/subject-prompt-goal-v1/example/package.json",
            "sse_multivector/subject-prompt-goal-v1/example/package-lock.json",
            "sse_multivector/subject-prompt-goal-v1/example/edits.json",
            "sse_multivector/mask-prompt-goal-v1/example/prompt-edits.json",
            "sse_multivector/subject-prompt-goal-v1/example/ASv6.48.md.revision.json",
            "sse_multivector/atomic-subject-prompt-versions.json",
            "sse_multivector/frontier_runner/package.json",
            "sse_multivector/frontier_runner/package-lock.json",
            "tests/fixtures/example.json",
            "sse_multivector/future-experiment-v2/tests/fixtures/example.json",
            "sse_multivector/future-experiment-v2/tests/fixtures/example.jsonl",
            "docs/planning/release-decisions.md",
            "budget-ledger.json",
            "models/gte-multilingual-base-tokenizer.lock.json",
        ]
        self.assertEqual(self.ignored(paths), set())

    def test_existing_cache_and_dependency_exclusions_still_apply(self):
        paths = [
            "target/debug/oracle",
            "reference_map/.review.lock",
            "sse_multivector/__pycache__/pipeline.cpython-311.pyc",
            "sse_multivector/.model-request-history/entry.json",
            ".budget-ledger.json.lock",
            "sse_multivector/frontier_runner/node_modules/example/index.js",
            "sse_multivector/geometric-hierarchy-v1/GDC01S/coordinate-snapshots.npz",
        ]
        self.assertEqual(self.ignored(paths), set(paths))


if __name__ == "__main__":
    unittest.main()
