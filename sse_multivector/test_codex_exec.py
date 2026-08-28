import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("codex_exec.py")
APPROVED_PROMINENCE_PROMPT = """Assign a prominence score to the one fixed takeaway below.

The score has one downstream meaning: the takeaway's vector may place this complete post in a fine-subject result matching the takeaway's complete meaning. Score how strongly the complete post is about that complete meaning so the score can help order notes within that result.

Read the complete post and the takeaway first. Judge this pair independently; no other takeaway exists. Consider the takeaway's complete meaning, including its subject, relationships, qualifications, and stance. Count any part of the post that directly states, explains, supports, exemplifies, evaluates, or applies that complete meaning. Do not reduce the score because some of the same source meaning could also support a different takeaway.

Distinguish semantic focus from scope. A framing meaning can apply to the entire post without the post being about it. Content merely contained within a frame does not count as developing that frame.

Choose any integer from 0 through 100:
- 90-100: The post is centrally and extensively about this complete meaning.
- 70-89: This complete meaning is a major focus of the post.
- 40-69: This complete meaning is a clear secondary focus.
- 10-39: This complete meaning is genuine but brief or incidental.
- 0-9: This complete meaning is unsupported or effectively absent.

Use the full integer range rather than treating the scale anchors as the only allowed values. Judge semantic prominence only, not quality, value, seriousness, or personal interest. Do not rewrite the takeaway.

Return only a JSON object: {"prominence":0}"""


FAKE_CODEX = r"""#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys


def append_log(value):
    path = Path(os.environ["FAKE_CODEX_LOG"])
    existing = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    existing.append(value)
    path.write_text(json.dumps(existing), encoding="utf-8")


if "--version" in sys.argv:
    print("codex-cli fixture-1.0")
    raise SystemExit(0)

if len(sys.argv) > 1 and sys.argv[1] == "login":
    append_log({
        "kind": "login",
        "argv": sys.argv[1:],
        "codex_home": os.environ.get("CODEX_HOME"),
    })
    raise SystemExit(0)

prompt = sys.stdin.read()
argv = sys.argv[1:]
output_path = Path(argv[argv.index("--output-last-message") + 1])
if prompt.startswith("GENERIC PROMPT"):
    stage = "prompt"
elif prompt.startswith("SUBJECT INSTRUCTION"):
    stage = "subject"
elif prompt.startswith("MASK INSTRUCTION"):
    stage = "mask"
elif prompt.startswith("PROMINENCE INSTRUCTION"):
    stage = "prominence"
else:
    stage = "takeaway"
append_log({
    "kind": "exec",
    "stage": stage,
    "argv": argv,
    "codex_home": os.environ.get("CODEX_HOME"),
    "cwd": os.getcwd(),
    "cwd_entries": sorted(os.listdir()),
    "prompt": prompt,
    "credential_environment": {
        key: value
        for key, value in os.environ.items()
        if key.startswith(("CODEX_", "OPENAI_", "CHATGPT_"))
    },
})

mutation_path = os.environ.get("FAKE_CODEX_MUTATE_PATH")
if mutation_path is not None:
    path = Path(mutation_path)
    path.write_bytes(path.read_bytes() + b"\n")

if os.environ.get("FAKE_CODEX_FAIL_STAGE") == stage:
    print("fixture child failure", file=sys.stderr)
    raise SystemExit(23)

if stage == "prompt":
    response_object = None
    output_text = f"Response to: {prompt}"
elif stage == "takeaway":
    response = (
        ["Tea helps the author."]
        if os.environ.get("FAKE_CODEX_REVISED_TAKEAWAYS") == "1"
        else
        []
        if os.environ.get("FAKE_CODEX_EMPTY_TAKEAWAYS") == "1"
        else [
            "The author finds Rust pleasant.",
            "Tea helps the author.",
        ]
    )
elif stage == "subject":
    response = (
        ["Solar power generation."]
        if "Solar power" in prompt
        else ["Rust programming.", "Tea drinking."]
    )
elif stage == "prominence":
    invalid_prominence = os.environ.get("FAKE_CODEX_INVALID_PROMINENCE")
    response = {
        "bool": True,
        "string": "85",
        "low": -1,
        "high": 101,
        "zero": 0,
    }.get(
        invalid_prominence,
        85 if "The author finds Rust pleasant." in prompt else 25,
    )
elif os.environ.get("FAKE_CODEX_INVALID_MASK") == "1":
    response = ["not present in the source note"]
elif os.environ.get("FAKE_CODEX_URL_MASK") == "1":
    response = ["https://example.com/source"]
elif "The author finds Rust pleasant." in prompt:
    response = ["Rust is pleasant"]
else:
    response = ["Tea helps"]

if stage != "prompt":
    response_object = {
        {
            "takeaway": "takeaways",
            "subject": "subjects",
            "prominence": "prominence",
            "mask": "fragments",
        }[stage]: response,
    }
    output_text = json.dumps(response_object)
output_path.write_text(output_text, encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": "fixture-thread"}))
print(json.dumps({"type": "turn.started"}))
if os.environ.get("FAKE_CODEX_MISSING_COMPLETION") == "1":
    raise SystemExit(0)
print(json.dumps({
    "type": "item.completed",
    "item": {
        "id": "fixture-message",
        "type": "agent_message",
        "text": output_text,
    },
}))
print(json.dumps({
    "type": "turn.completed",
    "usage": {
        "input_tokens": 100,
        "cached_input_tokens": 0,
        "output_tokens": 20,
        "reasoning_output_tokens": 5,
    },
}))
"""


class CodexExecRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fake_codex = self.root / "codex"
        self.fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        self.fake_codex.chmod(0o755)
        self.log_path = self.root / "codex-calls.json"
        self.codex_home = self.root / "dedicated-codex-home"
        self.codex_home.mkdir(mode=0o700)
        self.auth_path = self.codex_home / "auth.json"
        self.auth_path.write_text("fixture credentials", encoding="utf-8")
        self.auth_path.chmod(0o600)
        self.run_directory = self.root / "run"
        self.notes_path = self.root / "notes.json"
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [
                        {
                            "note_id": "note-1",
                            "text": "Rust is pleasant. Tea helps.",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.takeaway_prompts = self.root / "takeaway-prompts.json"
        self.takeaway_prompts.write_text(
            json.dumps(
                {
                    "frozen_takeaway_prompt_version": "TP-test",
                    "TP-test": "TAKEAWAY INSTRUCTION",
                }
            ),
            encoding="utf-8",
        )
        self.mask_prompts = self.root / "mask-prompts.json"
        self.mask_prompts.write_text(
            json.dumps(
                {
                    "MP-test": (
                        "MASK INSTRUCTION\n\n<post>\n{POST}\n</post>\n\n"
                        "<takeaway>\n{TAKEAWAY}\n</takeaway>"
                    )
                }
            ),
            encoding="utf-8",
        )
        self.subject_prompts = self.root / "subject-prompts.json"
        self.subject_prompts.write_text(
            json.dumps({"AS-test": "SUBJECT INSTRUCTION"}),
            encoding="utf-8",
        )
        self.subject_config_path = self.root / "subject-config.json"
        self.subject_run_directory = self.root / "subject-run"
        self.config_path = self.root / "config.json"
        self.write_config()
        self.write_subject_config()

    def write_config(
        self,
        *,
        codex_home: Path | None = None,
        takeaway_effort: str | None = "high",
        takeaway_model: str = "candidate/takeaway",
    ) -> None:
        takeaway = {
            "prompt_registry_path": str(self.takeaway_prompts),
            "prompt_version": "TP-test",
            "model": takeaway_model,
        }
        if takeaway_effort is not None:
            takeaway["reasoning_effort"] = takeaway_effort
        self.config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "codex_binary": str(self.fake_codex),
                    "codex_home": str(codex_home or self.codex_home),
                    "input_path": str(self.notes_path),
                    "run_directory": str(self.run_directory),
                    "takeaway": takeaway,
                    "mask": {
                        "prompt_registry_path": str(self.mask_prompts),
                        "prompt_version": "MP-test",
                        "model": "candidate/mask",
                        "reasoning_effort": "medium",
                    },
                }
            ),
            encoding="utf-8",
        )

    def invoke(
        self,
        *extra_arguments: str,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["FAKE_CODEX_LOG"] = str(self.log_path)
        environment["CODEX_URL"] = "https://ambient-codex.invalid"
        environment["CODEX_SQLITE_HOME"] = "/ambient/codex-sqlite"
        environment["CODEX_ACCESS_TOKEN"] = "ambient-codex-token"
        environment["OPENAI_API_KEY"] = "ambient-openai-key"
        environment["CHATGPT_BASE_URL"] = "https://ambient-chatgpt.invalid"
        environment.update(extra_environment or {})
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "run",
                str(self.config_path),
                *extra_arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def write_subject_config(self) -> None:
        self.subject_config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "codex_binary": str(self.fake_codex),
                    "codex_home": str(self.codex_home),
                    "input_path": str(self.notes_path),
                    "run_directory": str(self.subject_run_directory),
                    "subject": {
                        "prompt_registry_path": str(self.subject_prompts),
                        "prompt_version": "AS-test",
                        "model": "candidate/subject",
                        "reasoning_effort": "low",
                    },
                }
            ),
            encoding="utf-8",
        )

    def invoke_subjects(
        self,
        *extra_arguments: str,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["FAKE_CODEX_LOG"] = str(self.log_path)
        environment["CODEX_URL"] = "https://ambient-codex.invalid"
        environment["OPENAI_API_KEY"] = "ambient-openai-key"
        environment.update(extra_environment or {})
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "subjects",
                str(self.subject_config_path),
                *extra_arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def invoke_prompt_config(
        self,
        config_path: Path,
        *extra_arguments: str,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["FAKE_CODEX_LOG"] = str(self.log_path)
        environment["CODEX_URL"] = "https://ambient-codex.invalid"
        environment["OPENAI_API_KEY"] = "ambient-openai-key"
        environment.update(extra_environment or {})
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "prompt",
                str(config_path),
                *extra_arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def invoke_direct_prompt(
        self,
        text: str,
        *,
        stdin: str | None = None,
        include_model: bool = True,
        include_effort: bool = True,
        extra_environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        temporary_root = self.root / "direct-temporary-files"
        temporary_root.mkdir(exist_ok=True)
        environment = os.environ.copy()
        environment["FAKE_CODEX_LOG"] = str(self.log_path)
        environment["TMPDIR"] = str(temporary_root)
        environment["CODEX_URL"] = "https://ambient-codex.invalid"
        environment["OPENAI_API_KEY"] = "ambient-openai-key"
        environment.update(extra_environment or {})
        arguments = [
            sys.executable,
            str(RUNNER),
            "prompt",
            "--codex-home",
            str(self.codex_home),
            "--codex-binary",
            str(self.fake_codex),
            "--text",
            text,
        ]
        if include_model:
            arguments.extend(("--model", "candidate/label"))
        if include_effort:
            arguments.extend(("--reasoning-effort", "low"))
        return subprocess.run(
            arguments,
            input=stdin,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def calls(self) -> list[dict[str, object]]:
        if not self.log_path.exists():
            return []
        return json.loads(self.log_path.read_text(encoding="utf-8"))

    def enable_prominence(self) -> None:
        prominence_prompts = self.root / "prominence-prompts.json"
        prominence_prompts.write_text(
            json.dumps(
                {
                    "frozen_prominence_prompt_version": "PP-test",
                    "PP-test": "PROMINENCE INSTRUCTION",
                }
            ),
            encoding="utf-8",
        )
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["schema_version"] = 2
        config["prominence"] = {
            "prompt_registry_path": str(prominence_prompts),
            "prompt_version": "PP-test",
            "model": "candidate/prominence",
            "reasoning_effort": "high",
        }
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def enable_prior_run_reuse(
        self,
        *,
        source_input: Path,
        source_run: Path,
    ) -> dict[str, object]:
        runner_upgrades = source_run / "runner-upgrades.jsonl"
        provenance = {
            "input_path": str(source_input),
            "input_sha256": hashlib.sha256(source_input.read_bytes()).hexdigest(),
            "run_directory": str(source_run),
            "manifest_sha256": hashlib.sha256(
                (source_run / "manifest.json").read_bytes()
            ).hexdigest(),
            "results_sha256": hashlib.sha256(
                (source_run / "results.jsonl").read_bytes()
            ).hexdigest(),
            "runner_upgrades_sha256": (
                hashlib.sha256(runner_upgrades.read_bytes()).hexdigest()
                if runner_upgrades.exists()
                else None
            ),
            "output_sha256": hashlib.sha256(
                (source_run / "output.json").read_bytes()
            ).hexdigest(),
        }
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(2, config["schema_version"])
        config["schema_version"] = 3
        config["reuse_source"] = provenance
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        return provenance

    def prepare_prior_run_reuse(self) -> tuple[Path, Path, dict[str, object]]:
        self.enable_prominence()
        original_input = self.notes_path
        original_run = self.run_directory
        completed = self.invoke()
        self.assertEqual(0, completed.returncode, completed.stderr)

        source_root = self.root / "extracted-source"
        source_root.mkdir()
        source_input = source_root / "notes.json"
        source_run = source_root / "run"
        shutil.copy2(original_input, source_input)
        shutil.copytree(original_run, source_run)
        source_manifest = json.loads(
            (source_run / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(str(original_input), source_manifest["input_path"])
        self.assertNotEqual(str(source_input), source_manifest["input_path"])

        target_input = self.root / "corrected-notes.json"
        target_input.write_bytes(source_input.read_bytes())
        self.notes_path = target_input
        self.run_directory = self.root / "corrected-run"
        self.write_config()
        self.enable_prominence()
        provenance = self.enable_prior_run_reuse(
            source_input=source_input,
            source_run=source_run,
        )
        return source_input, source_run, provenance

    def test_subjects_generates_only_ordered_subjects_in_fresh_processes(
        self,
    ) -> None:
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [
                        {
                            "note_id": "note-1",
                            "text": "Rust is pleasant. Tea helps.",
                        },
                        {
                            "note_id": "note-2",
                            "text": "Solar power will dominate electricity generation.",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        completed = self.invoke_subjects()

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(["subject", "subject"], [call["stage"] for call in calls])
        self.assertEqual(2, len({call["cwd"] for call in calls}))
        for call in calls:
            self.assertIn("--output-schema", call["argv"])
            self.assertEqual([], call["cwd_entries"])
            self.assertIn("candidate/subject", call["argv"])
            self.assertIn('model_reasoning_effort="low"', call["argv"])
        self.assertEqual(
            "SUBJECT INSTRUCTION\n\n"
            "<post>\nRust is pleasant. Tea helps.\n</post>",
            calls[0]["prompt"],
        )
        self.assertEqual(
            "SUBJECT INSTRUCTION\n\n"
            "<post>\nSolar power will dominate electricity generation.\n</post>",
            calls[1]["prompt"],
        )

        output = json.loads(
            (self.subject_run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [
                {
                    "note_id": "note-1",
                    "text": "Rust is pleasant. Tea helps.",
                    "subjects": [
                        {"source_index": 0, "text": "Rust programming."},
                        {"source_index": 1, "text": "Tea drinking."},
                    ],
                },
                {
                    "note_id": "note-2",
                    "text": "Solar power will dominate electricity generation.",
                    "subjects": [
                        {"source_index": 0, "text": "Solar power generation."}
                    ],
                },
            ],
            output["notes"],
        )
        manifest = json.loads(
            (self.subject_run_directory / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("atomic_subject_generation", manifest["mode"])
        self.assertEqual("AS-test", manifest["subject"]["prompt_version"])
        self.assertEqual("candidate/subject", manifest["subject"]["model"])
        self.assertEqual("xml-post-v1", manifest["subject_envelope_version"])
        self.assertEqual(
            "remove-long-ascii-nip19-identifiers-v2",
            manifest["subject_input_normalization_version"],
        )
        self.assertNotIn("mask", manifest)
        self.assertTrue(
            (self.subject_run_directory / "subject-output-schema.json").is_file()
        )
        subject_schema = json.loads(
            (self.subject_run_directory / "subject-output-schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["subjects"], subject_schema["required"])
        self.assertEqual(
            "array", subject_schema["properties"]["subjects"]["type"]
        )
        self.assertFalse(
            (self.subject_run_directory / "mask-output-schema.json").exists()
        )
        records = [
            json.loads(line)
            for line in (self.subject_run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            ["subject:note-1", "subject:note-2"],
            [record["job_key"] for record in records],
        )
        self.assertTrue(all("subject_index" not in record for record in records))
        self.assertTrue(all("takeaway_index" not in record for record in records))
        self.assertEqual(
            [["Rust programming.", "Tea drinking."], ["Solar power generation."]],
            [record["response"] for record in records],
        )
        self.assertEqual(
            {"subjects": ["Rust programming.", "Tea drinking."]},
            json.loads(records[0]["final_output_raw"]),
        )

    def test_subjects_rejects_a_mask_stage_before_spawning(self) -> None:
        config = json.loads(self.subject_config_path.read_text(encoding="utf-8"))
        config["mask"] = {
            "prompt_registry_path": str(self.mask_prompts),
            "prompt_version": "MP-test",
            "model": "candidate/mask",
            "reasoning_effort": "medium",
        }
        self.subject_config_path.write_text(json.dumps(config), encoding="utf-8")

        completed = self.invoke_subjects()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("`config.mask` is not supported", completed.stderr)
        self.assertEqual([], self.calls())
        self.assertFalse(self.subject_run_directory.exists())

    def test_subjects_resumes_and_retries_only_failed_jobs(self) -> None:
        failed = self.invoke_subjects(
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "subject"}
        )

        self.assertNotEqual(0, failed.returncode)
        self.assertFalse((self.subject_run_directory / "output.json").exists())
        self.assertEqual(1, len([call for call in self.calls() if call["kind"] == "exec"]))

        blocked = self.invoke_subjects()

        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--retry-failed", blocked.stderr)
        self.assertEqual(1, len([call for call in self.calls() if call["kind"] == "exec"]))

        retried = self.invoke_subjects("--retry-failed")

        self.assertEqual(0, retried.returncode, retried.stderr)
        self.assertTrue((self.subject_run_directory / "output.json").is_file())
        self.assertEqual(2, len([call for call in self.calls() if call["kind"] == "exec"]))

        records = [
            json.loads(line)
            for line in (self.subject_run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual([1, 2], [record["attempt"] for record in records])
        self.assertEqual(["failed", "succeeded"], [record["status"] for record in records])

        calls_before = len(self.calls())
        resumed = self.invoke_subjects()
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_subjects_max_new_jobs_pauses_between_notes(self) -> None:
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [
                        {"note_id": "note-1", "text": "Rust is pleasant."},
                        {"note_id": "note-2", "text": "Solar power is useful."},
                    ],
                }
            ),
            encoding="utf-8",
        )

        first = self.invoke_subjects("--max-new-jobs", "1")

        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(
            {"complete": False, "completed_notes": 1, "new_jobs": 1},
            json.loads(first.stdout),
        )
        self.assertFalse((self.subject_run_directory / "output.json").exists())

        second = self.invoke_subjects("--max-new-jobs", "1")

        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(
            {
                "complete": True,
                "completed_notes": 2,
                "new_jobs": 1,
                "notes": 2,
                "subjects": 3,
            },
            json.loads(second.stdout),
        )
        self.assertTrue((self.subject_run_directory / "output.json").is_file())
        self.assertEqual(2, len([call for call in self.calls() if call["kind"] == "exec"]))

    def test_runs_each_generation_in_a_fresh_isolated_codex_exec(self) -> None:
        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(3, len(calls))
        self.assertEqual(
            ["takeaway", "mask", "mask"],
            [call["stage"] for call in calls],
        )
        self.assertEqual(3, len({call["cwd"] for call in calls}))
        for call in calls:
            argv = call["argv"]
            self.assertIn("exec", argv)
            self.assertIn("--ephemeral", argv)
            self.assertIn("--ignore-user-config", argv)
            self.assertIn("--ignore-rules", argv)
            self.assertIn("--strict-config", argv)
            self.assertIn("--skip-git-repo-check", argv)
            self.assertIn("--cd", argv)
            self.assertEqual(call["cwd"], argv[argv.index("--cd") + 1])
            self.assertIn("--sandbox", argv)
            self.assertIn("read-only", argv)
            self.assertIn("--output-schema", argv)
            self.assertIn("--output-last-message", argv)
            self.assertIn("--json", argv)
            self.assertIn("--color", argv)
            self.assertEqual("never", argv[argv.index("--color") + 1])
            self.assertNotIn("resume", argv)
            self.assertIn('web_search="disabled"', argv)
            self.assertIn('approval_policy="never"', argv)
            self.assertIn('shell_environment_policy.inherit="none"', argv)
            self.assertIn("project_root_markers=[]", argv)
            model_instructions = self.run_directory / "model-instructions.md"
            self.assertIn(
                f"model_instructions_file={json.dumps(str(model_instructions))}",
                argv,
            )
            for context_override in (
                "agents.enabled=false",
                "include_permissions_instructions=false",
                "include_apps_instructions=false",
                "include_collaboration_mode_instructions=false",
                "include_environment_context=false",
                "skills.include_instructions=false",
            ):
                self.assertIn(context_override, argv)
            adjacent_arguments = set(zip(argv, argv[1:]))
            for feature in (
                "shell_tool",
                "unified_exec",
                "multi_agent",
                "apps",
                "plugins",
                "browser_use",
                "computer_use",
                "image_generation",
            ):
                self.assertIn(("--disable", feature), adjacent_arguments)
            self.assertEqual(str(self.codex_home), call["codex_home"])
            self.assertEqual(
                {"CODEX_HOME": str(self.codex_home)},
                call["credential_environment"],
            )
            self.assertTrue(Path(call["cwd"]).is_relative_to(self.codex_home))
            self.assertEqual([], call["cwd_entries"])
        self.assertIn("--model", calls[0]["argv"])
        self.assertIn("candidate/takeaway", calls[0]["argv"])
        self.assertIn('model_reasoning_effort="high"', calls[0]["argv"])
        self.assertIn("candidate/mask", calls[1]["argv"])
        self.assertIn('model_reasoning_effort="medium"', calls[1]["argv"])
        self.assertEqual(
            "TAKEAWAY INSTRUCTION\n\n" "<post>\nRust is pleasant. Tea helps.\n</post>",
            calls[0]["prompt"],
        )
        self.assertIn(
            "<takeaway>\nThe author finds Rust pleasant.\n</takeaway>",
            calls[1]["prompt"],
        )
        self.assertEqual(0o700, self.codex_home.stat().st_mode & 0o777)
        self.assertEqual(
            "Follow the user's instructions.\n",
            (self.run_directory / "model-instructions.md").read_text(
                encoding="utf-8"
            ),
        )

        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {
                "schema_version": 1,
                "notes": [
                    {
                        "note_id": "note-1",
                        "takeaways": [
                            {
                                "text": "The author finds Rust pleasant.",
                                "fragments": ["Rust is pleasant"],
                            },
                            {
                                "text": "Tea helps the author.",
                                "fragments": ["Tea helps"],
                            },
                        ],
                    }
                ],
            },
            {
                "schema_version": output["schema_version"],
                "notes": output["notes"],
            },
        )
        manifest = json.loads(
            (self.run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("candidate/takeaway", manifest["takeaway"]["model"])
        self.assertEqual("high", manifest["takeaway"]["reasoning_effort"])
        self.assertEqual("candidate/mask", manifest["mask"]["model"])
        self.assertEqual("medium", manifest["mask"]["reasoning_effort"])
        self.assertEqual("codex-cli fixture-1.0", manifest["codex_version"])
        self.assertEqual(
            "Follow the user's instructions.\n",
            manifest["isolation"]["model_instructions"],
        )
        self.assertEqual(
            hashlib.sha256(b"Follow the user's instructions.\n").hexdigest(),
            manifest["isolation"]["model_instructions_sha256"],
        )
        self.assertEqual(
            [
                "agents.enabled=false",
                "include_permissions_instructions=false",
                "include_apps_instructions=false",
                "include_collaboration_mode_instructions=false",
                "include_environment_context=false",
                "skills.include_instructions=false",
            ],
            manifest["isolation"]["runtime_context_overrides"],
        )

    def test_pipeline_v2_scores_each_takeaway_in_its_own_process(self) -> None:
        self.enable_prominence()

        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(
            ["takeaway", "prominence", "mask", "prominence", "mask"],
            [call["stage"] for call in calls],
        )
        self.assertEqual(5, len({call["cwd"] for call in calls}))
        first_prominence = calls[1]
        second_prominence = calls[3]
        self.assertIn("candidate/prominence", first_prominence["argv"])
        self.assertIn('model_reasoning_effort="high"', first_prominence["argv"])
        self.assertIn(
            "<complete_post>\nRust is pleasant. Tea helps.\n</complete_post>",
            first_prominence["prompt"],
        )
        self.assertIn(
            "<takeaway>\nThe author finds Rust pleasant.\n</takeaway>",
            first_prominence["prompt"],
        )
        self.assertNotIn("Tea helps the author.", first_prominence["prompt"])
        self.assertIn(
            "<takeaway>\nTea helps the author.\n</takeaway>",
            second_prominence["prompt"],
        )
        self.assertNotIn(
            "The author finds Rust pleasant.", second_prominence["prompt"]
        )
        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, output["schema_version"])
        self.assertEqual(
            [85, 25],
            [item["prominence"] for item in output["notes"][0]["takeaways"]],
        )
        prominence_schema = json.loads(
            (self.run_directory / "prominence-output-schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {"type": "integer", "minimum": 0, "maximum": 100},
            prominence_schema["properties"]["prominence"],
        )
        manifest = json.loads(
            (self.run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("PP-test", manifest["prominence"]["prompt_version"])
        self.assertEqual("candidate/prominence", manifest["prominence"]["model"])
        self.assertEqual(
            "xml-complete-post-takeaway-v1",
            manifest["prominence_envelope_version"],
        )

    def test_ppv2_registry_contains_the_approved_prompt(self) -> None:
        registry = json.loads(
            (RUNNER.parent / "prominence-prompt-versions.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("PPv2", registry["frozen_prominence_prompt_version"])
        self.assertEqual(APPROVED_PROMINENCE_PROMPT, registry["PPv2"])

    def test_pipeline_v2_rejects_invalid_prominence_scores(self) -> None:
        for invalid, expected in (
            ("bool", "prominence response must be an integer"),
            ("string", "prominence response must be an integer"),
            ("low", "prominence response must be between 0 and 100"),
            ("high", "prominence response must be between 0 and 100"),
        ):
            with self.subTest(invalid=invalid):
                self.run_directory = self.root / f"run-{invalid}"
                self.write_config()
                self.enable_prominence()

                completed = self.invoke(
                    extra_environment={"FAKE_CODEX_INVALID_PROMINENCE": invalid}
                )

                self.assertNotEqual(0, completed.returncode)
                self.assertIn(expected, completed.stderr)
                self.assertFalse((self.run_directory / "output.json").exists())

    def test_pipeline_v2_preserves_zero_prominence(self) -> None:
        self.enable_prominence()

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_INVALID_PROMINENCE": "zero"}
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [0, 0],
            [item["prominence"] for item in output["notes"][0]["takeaways"]],
        )

    def test_pipeline_v2_skips_later_stages_for_empty_takeaways(self) -> None:
        self.enable_prominence()

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_EMPTY_TAKEAWAYS": "1"}
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(["takeaway"], [call["stage"] for call in calls])
        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], output["notes"][0]["takeaways"])

    def test_pipeline_v2_requires_prominence_before_spawning(self) -> None:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["schema_version"] = 2
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("config.prominence", completed.stderr)
        self.assertEqual([], self.calls())

    def test_pipeline_v2_reuses_prominence_when_resuming_a_failed_mask(self) -> None:
        self.enable_prominence()

        failed = self.invoke(extra_environment={"FAKE_CODEX_FAIL_STAGE": "mask"})

        self.assertNotEqual(0, failed.returncode)
        self.assertEqual(
            ["takeaway", "prominence", "mask"],
            [call["stage"] for call in self.calls() if call["kind"] == "exec"],
        )

        resumed = self.invoke("--retry-failed")

        self.assertEqual(0, resumed.returncode, resumed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(
            [
                "takeaway",
                "prominence",
                "mask",
                "mask",
                "prominence",
                "mask",
            ],
            [call["stage"] for call in calls],
        )
        records = [
            json.loads(line)
            for line in (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [
                "takeaway:note-1",
                "prominence:note-1:0",
                "mask:note-1:0",
                "mask:note-1:0",
                "prominence:note-1:1",
                "mask:note-1:1",
            ],
            [record["job_key"] for record in records],
        )

    def test_audited_retry_of_semantically_invalid_success_rebuilds_changed_children(
        self,
    ) -> None:
        self.enable_prominence()
        initial = self.invoke()
        self.assertEqual(0, initial.returncode, initial.stderr)

        retried = self.invoke(
            "--retry-job",
            "takeaway:note-1",
            "--retry-reason",
            "semantic output contradicted the frozen prompt",
            "--max-new-jobs",
            "1",
            extra_environment={"FAKE_CODEX_REVISED_TAKEAWAYS": "1"},
        )
        self.assertEqual(0, retried.returncode, retried.stderr)
        records = [
            json.loads(line)
            for line in (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual("takeaway:note-1", records[-1]["job_key"])
        self.assertEqual(2, records[-1]["attempt"])
        self.assertEqual(
            "semantic output contradicted the frozen prompt",
            records[-1]["retry_reason"],
        )

        blocked = self.invoke()
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("rendered prompt changed", blocked.stderr)

        rebuilt = self.invoke("--retry-failed")
        self.assertEqual(0, rebuilt.returncode, rebuilt.stderr)
        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            ["Tea helps the author."],
            [item["text"] for item in output["notes"][0]["takeaways"]],
        )
        records = [
            json.loads(line)
            for line in (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            ["upstream rendered prompt changed", "upstream rendered prompt changed"],
            [record["retry_reason"] for record in records[-2:]],
        )

    def test_runner_upgrade_is_explicit_and_bound_to_new_result_records(self) -> None:
        initial = self.invoke()
        self.assertEqual(0, initial.returncode, initial.stderr)

        manifest_path = self.run_directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        original_wrapper = "f" * 64
        manifest["wrapper_sha256"] = original_wrapper
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        results_path = self.run_directory / "results.jsonl"
        records = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
        ]
        for record in records:
            record["manifest_sha256"] = manifest_sha256
            record.pop("wrapper_sha256", None)
        results_path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        results_prefix = results_path.read_bytes()
        (self.run_directory / "output.json").unlink()

        blocked = self.invoke(
            "--retry-job",
            "takeaway:note-1",
            "--retry-reason",
            "replace a semantically invalid result",
            "--max-new-jobs",
            "1",
        )
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--runner-upgrade-reason", blocked.stderr)

        resumed = self.invoke(
            "--retry-job",
            "takeaway:note-1",
            "--retry-reason",
            "replace a semantically invalid result",
            "--runner-upgrade-reason",
            "add audited semantic retries",
            "--max-new-jobs",
            "1",
        )
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        current_wrapper = hashlib.sha256(RUNNER.read_bytes()).hexdigest()
        upgrade = json.loads(
            (self.run_directory / "runner-upgrades.jsonl")
            .read_text(encoding="utf-8")
            .strip()
        )
        self.assertEqual(original_wrapper, upgrade["from_wrapper_sha256"])
        self.assertEqual(current_wrapper, upgrade["to_wrapper_sha256"])
        self.assertEqual("add audited semantic retries", upgrade["reason"])
        self.assertEqual(len(records) + 1, upgrade["first_result_line"])
        self.assertEqual(len(results_prefix), upgrade["results_prefix_bytes"])
        self.assertEqual(
            hashlib.sha256(results_prefix).hexdigest(),
            upgrade["results_prefix_sha256"],
        )
        latest = json.loads(results_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(current_wrapper, latest["wrapper_sha256"])

        upgrade_bytes = (self.run_directory / "runner-upgrades.jsonl").read_bytes()
        calls_before = len(self.calls())
        same_wrapper = self.invoke()
        self.assertEqual(0, same_wrapper.returncode, same_wrapper.stderr)
        self.assertEqual(calls_before, len(self.calls()))
        self.assertEqual(
            upgrade_bytes,
            (self.run_directory / "runner-upgrades.jsonl").read_bytes(),
        )

        valid_results = results_path.read_bytes()
        tampered = bytearray(valid_results)
        tampered[0] = ord("{") if tampered[0] != ord("{") else ord("[")
        results_path.write_bytes(tampered)
        rejected = self.invoke()
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("results prefix", rejected.stderr)
        self.assertEqual(calls_before, len(self.calls()))
        results_path.write_bytes(valid_results)

    def test_pipeline_v2_normalizes_prominence_input_but_not_mask_input(
        self,
    ) -> None:
        identifier = (
            "nostr:npub1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
        )
        original = f"Rust is pleasant. {identifier} Tea helps."
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [{"note_id": "note-1", "text": original}],
                }
            ),
            encoding="utf-8",
        )
        self.enable_prominence()

        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        for call in (calls[1], calls[3]):
            self.assertEqual("prominence", call["stage"])
            self.assertNotIn(identifier, call["prompt"])
        for call in (calls[2], calls[4]):
            self.assertEqual("mask", call["stage"])
            self.assertIn(identifier, call["prompt"])
        manifest = json.loads(
            (self.run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "remove-long-ascii-nip19-identifiers-v2",
            manifest["prominence_input_normalization_version"],
        )

    def test_pipeline_rejects_non_integer_schema_versions(self) -> None:
        for invalid in (True, 1.0):
            with self.subTest(invalid=invalid):
                self.run_directory = self.root / f"run-schema-{type(invalid).__name__}"
                self.write_config()
                config = json.loads(self.config_path.read_text(encoding="utf-8"))
                config["schema_version"] = invalid
                self.config_path.write_text(json.dumps(config), encoding="utf-8")

                completed = self.invoke()

                self.assertNotEqual(0, completed.returncode)
                self.assertIn(
                    "unsupported pipeline config schema version",
                    completed.stderr,
                )
                self.assertEqual([], self.calls())

    def test_takeaway_generation_removes_metadata_but_masks_original_text(
        self,
    ) -> None:
        folded_identifier = "nſec1" + "ſ" * 52
        combining_boundary_identifier = "npub1" + "p" * 52
        original = (
            "Rust is pleasant.\n    Tea helps. @Override "
            "nostr:npub1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq "
            f"{folded_identifier} \u0345{combining_boundary_identifier} "
            "https://example.com/source docs.example.org/path "
            "#GPL #OpenSource npub1friend"
        )
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [{"note_id": "note-1", "text": original}],
                }
            ),
            encoding="utf-8",
        )

        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        takeaway_prompt = calls[0]["prompt"]
        self.assertIn("\n    Tea helps. @Override", takeaway_prompt)
        self.assertNotIn("nostr:npub1", takeaway_prompt)
        self.assertIn(folded_identifier, takeaway_prompt)
        self.assertNotIn(combining_boundary_identifier, takeaway_prompt)
        self.assertIn("\u0345", takeaway_prompt)
        self.assertIn("https://example.com/source", takeaway_prompt)
        self.assertIn("docs.example.org/path", takeaway_prompt)
        self.assertIn("#GPL #OpenSource npub1friend", takeaway_prompt)
        self.assertIn(f"<post>\n{original}\n</post>", calls[1]["prompt"])
        manifest = json.loads(
            (self.run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "remove-long-ascii-nip19-identifiers-v2",
            manifest["takeaway_input_normalization_version"],
        )

    def test_runs_generic_prompts_without_adding_tools_or_prompt_text(self) -> None:
        prompt_run_directory = self.root / "prompt-run"
        prompts = [
            {"prompt_id": "segment-1", "text": "GENERIC PROMPT ONE"},
            {"prompt_id": "segment-2", "text": "GENERIC PROMPT TWO"},
        ]
        config_path = self.root / "prompt-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "codex_binary": str(self.fake_codex),
                    "codex_home": str(self.codex_home),
                    "run_directory": str(prompt_run_directory),
                    "model": "candidate/label",
                    "reasoning_effort": "low",
                    "prompts": prompts,
                }
            ),
            encoding="utf-8",
        )

        completed = self.invoke_prompt_config(config_path)

        self.assertEqual(0, completed.returncode, completed.stderr)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(["prompt", "prompt"], [call["stage"] for call in calls])
        self.assertEqual([row["text"] for row in prompts], [call["prompt"] for call in calls])
        self.assertEqual(2, len({call["cwd"] for call in calls}))
        for call in calls:
            argv = call["argv"]
            self.assertNotIn("--output-schema", argv)
            self.assertIn("--output-last-message", argv)
            self.assertIn('web_search="disabled"', argv)
            self.assertIn('approval_policy="never"', argv)
            self.assertIn("candidate/label", argv)
            self.assertIn('model_reasoning_effort="low"', argv)
            self.assertEqual([], call["cwd_entries"])
            self.assertEqual(
                {"CODEX_HOME": str(self.codex_home)},
                call["credential_environment"],
            )
            adjacent_arguments = set(zip(argv, argv[1:]))
            for feature in (
                "shell_tool",
                "unified_exec",
                "multi_agent",
                "apps",
                "plugins",
                "browser_use",
                "computer_use",
                "image_generation",
            ):
                self.assertIn(("--disable", feature), adjacent_arguments)

        output = json.loads(
            (prompt_run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [
                {"prompt_id": "segment-1", "response": "Response to: GENERIC PROMPT ONE"},
                {"prompt_id": "segment-2", "response": "Response to: GENERIC PROMPT TWO"},
            ],
            output["responses"],
        )
        manifest = json.loads(
            (prompt_run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual("prompt", manifest["mode"])
        self.assertEqual("candidate/label", manifest["model"])
        self.assertEqual("low", manifest["reasoning_effort"])
        self.assertEqual(prompts, manifest["prompts"])

    def test_direct_prompt_prints_response_without_persistent_run_files(self) -> None:
        completed = self.invoke_direct_prompt("GENERIC PROMPT DIRECT")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("Response to: GENERIC PROMPT DIRECT", completed.stdout)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual(1, len(calls))
        call = calls[0]
        self.assertEqual("GENERIC PROMPT DIRECT", call["prompt"])
        self.assertIn("candidate/label", call["argv"])
        self.assertIn('model_reasoning_effort="low"', call["argv"])
        self.assertEqual([], call["cwd_entries"])
        self.assertEqual(
            {"CODEX_HOME": str(self.codex_home)},
            call["credential_environment"],
        )
        self.assertEqual([], list((self.root / "direct-temporary-files").iterdir()))
        self.assertEqual([], list((self.codex_home / "job-workspaces").iterdir()))
        self.assertFalse(self.run_directory.exists())

    def test_direct_prompt_reads_text_from_stdin(self) -> None:
        completed = self.invoke_direct_prompt("-", stdin="GENERIC PROMPT FROM STDIN")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("Response to: GENERIC PROMPT FROM STDIN", completed.stdout)
        calls = [call for call in self.calls() if call["kind"] == "exec"]
        self.assertEqual("GENERIC PROMPT FROM STDIN", calls[0]["prompt"])

    def test_direct_prompt_surfaces_child_failure_without_persistent_files(
        self,
    ) -> None:
        completed = self.invoke_direct_prompt(
            "GENERIC PROMPT DIRECT",
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "prompt"},
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("codex exec exited with status 23", completed.stderr)
        self.assertIn("fixture child failure", completed.stderr)
        self.assertEqual([], list((self.root / "direct-temporary-files").iterdir()))
        self.assertEqual([], list((self.codex_home / "job-workspaces").iterdir()))

    def test_direct_prompt_requires_explicit_model_and_effort(self) -> None:
        missing_model = self.invoke_direct_prompt(
            "GENERIC PROMPT DIRECT",
            include_model=False,
        )
        missing_effort = self.invoke_direct_prompt(
            "GENERIC PROMPT DIRECT",
            include_effort=False,
        )

        self.assertNotEqual(0, missing_model.returncode)
        self.assertIn("--model", missing_model.stderr)
        self.assertNotEqual(0, missing_effort.returncode)
        self.assertIn("--reasoning-effort", missing_effort.stderr)
        self.assertEqual([], self.calls())

    def test_generic_prompt_failure_is_audited_and_requires_explicit_retry(
        self,
    ) -> None:
        prompt_run_directory = self.root / "prompt-run"
        config_path = self.root / "prompt-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "codex_binary": str(self.fake_codex),
                    "codex_home": str(self.codex_home),
                    "run_directory": str(prompt_run_directory),
                    "model": "candidate/label",
                    "reasoning_effort": "low",
                    "prompts": [
                        {"prompt_id": "segment-1", "text": "GENERIC PROMPT ONE"}
                    ],
                }
            ),
            encoding="utf-8",
        )

        failed = self.invoke_prompt_config(
            config_path,
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "prompt"},
        )

        self.assertNotEqual(0, failed.returncode)
        self.assertFalse((prompt_run_directory / "output.json").exists())
        record = json.loads(
            (prompt_run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.assertEqual("failed", record["status"])
        self.assertIsNone(record["response_schema_sha256"])

        calls_before = len(self.calls())
        blocked = self.invoke_prompt_config(config_path)
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--retry-failed", blocked.stderr)
        self.assertEqual(calls_before, len(self.calls()))

        retried = self.invoke_prompt_config(config_path, "--retry-failed")
        self.assertEqual(0, retried.returncode, retried.stderr)
        self.assertTrue((prompt_run_directory / "output.json").is_file())

    def test_generic_prompt_config_rejects_duplicate_ids_before_spawning(
        self,
    ) -> None:
        config_path = self.root / "prompt-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "codex_binary": str(self.fake_codex),
                    "codex_home": str(self.codex_home),
                    "run_directory": str(self.root / "prompt-run"),
                    "model": "candidate/label",
                    "reasoning_effort": "low",
                    "prompts": [
                        {"prompt_id": "duplicate", "text": "GENERIC PROMPT ONE"},
                        {"prompt_id": "duplicate", "text": "GENERIC PROMPT TWO"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        completed = self.invoke_prompt_config(config_path)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("duplicate prompt_id", completed.stderr)
        self.assertEqual([], self.calls())

    def test_refuses_the_users_normal_codex_home_before_spawning(self) -> None:
        self.write_config(codex_home=Path.home() / ".codex")

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("dedicated CODEX_HOME", completed.stderr)
        self.assertEqual([], self.calls())
        self.assertFalse(self.run_directory.exists())

    def test_does_not_chmod_or_use_an_existing_insecure_codex_home(self) -> None:
        self.codex_home.chmod(0o755)

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("must have mode 0700", completed.stderr)
        self.assertEqual(0o755, self.codex_home.stat().st_mode & 0o777)
        self.assertEqual([], self.calls())

    def test_refuses_to_run_without_file_credentials(self) -> None:
        self.auth_path.unlink()

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("auth.json is missing", completed.stderr)
        self.assertEqual([], self.calls())

    def test_refuses_insecure_file_credential_permissions_without_changing_them(
        self,
    ) -> None:
        self.auth_path.chmod(0o644)

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("auth.json must have mode 0600", completed.stderr)
        self.assertEqual(0o644, self.auth_path.stat().st_mode & 0o777)
        self.assertEqual([], self.calls())

    def test_uses_object_root_output_schemas_required_by_codex(self) -> None:
        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        takeaway_schema = json.loads(
            (self.run_directory / "takeaway-output-schema.json").read_text(
                encoding="utf-8"
            )
        )
        mask_schema = json.loads(
            (self.run_directory / "mask-output-schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("object", takeaway_schema["type"])
        self.assertEqual(["takeaways"], takeaway_schema["required"])
        self.assertEqual("array", takeaway_schema["properties"]["takeaways"]["type"])
        self.assertEqual("object", mask_schema["type"])
        self.assertEqual(["fragments"], mask_schema["required"])
        self.assertEqual("array", mask_schema["properties"]["fragments"]["type"])

    def test_requires_model_and_reasoning_effort_before_spawning(self) -> None:
        self.write_config(takeaway_effort=None)

        completed = self.invoke()

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("takeaway.reasoning_effort", completed.stderr)
        self.assertEqual([], self.calls())

    def test_failed_child_is_audited_and_requires_an_explicit_retry(self) -> None:
        failed = self.invoke(extra_environment={"FAKE_CODEX_FAIL_STAGE": "mask"})

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("codex exec exited with status 23", failed.stderr)
        self.assertFalse((self.run_directory / "output.json").exists())
        records = [
            json.loads(line)
            for line in (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(["succeeded", "failed"], [row["status"] for row in records])
        self.assertEqual("codex exec exited with status 23", records[-1]["error"])
        self.assertEqual("fixture child failure\n", records[-1]["stderr"])
        self.assertNotIn("fixture child failure", failed.stderr)

        calls_before = len(self.calls())
        blocked = self.invoke()
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--retry-failed", blocked.stderr)
        self.assertEqual(calls_before, len(self.calls()))

        resumed = self.invoke("--retry-failed")
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        self.assertTrue((self.run_directory / "output.json").is_file())
        self.assertEqual(calls_before + 2, len(self.calls()))

    def test_max_new_jobs_pauses_and_resumes_without_replaying_cached_jobs(self) -> None:
        self.enable_prominence()

        expected_stages = [
            "takeaway",
            "prominence",
            "mask",
            "prominence",
            "mask",
        ]
        for expected_call_count, expected_stage in enumerate(expected_stages, start=1):
            completed = self.invoke("--max-new-jobs", "1")

            self.assertEqual(0, completed.returncode, completed.stderr)
            calls = [call for call in self.calls() if call["kind"] == "exec"]
            self.assertEqual(expected_call_count, len(calls))
            self.assertEqual(expected_stage, calls[-1]["stage"])
            status = json.loads(completed.stdout)
            self.assertEqual(1, status["new_jobs"])
            self.assertEqual(
                1 if expected_call_count == len(expected_stages) else 0,
                status["completed_notes"],
            )
            self.assertEqual(
                expected_call_count == len(expected_stages),
                status["complete"],
            )
            self.assertEqual(
                expected_call_count == len(expected_stages),
                (self.run_directory / "output.json").exists(),
            )

        completed = self.invoke("--max-new-jobs", "1")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            {
                "complete": True,
                "completed_notes": 1,
                "completed_takeaways": 2,
                "new_jobs": 0,
                "notes": 1,
                "takeaways": 2,
            },
            json.loads(completed.stdout),
        )
        self.assertEqual(5, len([call for call in self.calls() if call["kind"] == "exec"]))

    def test_pipeline_v3_reuses_identical_prior_jobs_without_codex_calls(self) -> None:
        _, source_run, provenance = self.prepare_prior_run_reuse()
        calls_before = len(self.calls())
        source_references = {}
        for line_number, line in enumerate(
            (source_run / "results.jsonl").read_bytes().splitlines(keepends=True),
            start=1,
        ):
            record = json.loads(line)
            source_references[record["job_key"]] = {
                "result_line": line_number,
                "result_sha256": hashlib.sha256(line).hexdigest(),
                "result_attempt": record["attempt"],
            }

        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(calls_before, len(self.calls()))
        source_output = json.loads(
            (source_run / "output.json").read_text(encoding="utf-8")
        )
        output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(source_output["notes"], output["notes"])
        manifest = json.loads(
            (self.run_directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provenance, manifest["reuse_source"])
        records = [
            json.loads(line)
            for line in (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(5, len(records))
        for record in records:
            reused_from = record["reused_from"]
            self.assertEqual("reused", record["execution"])
            self.assertEqual(
                {
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_output_tokens": 0,
                },
                record["usage"],
            )
            self.assertEqual(
                provenance["results_sha256"],
                reused_from["results_sha256"],
            )
            for field, expected in source_references[record["job_key"]].items():
                self.assertEqual(expected, reused_from[field])

    def test_pipeline_v3_requires_the_same_prompt_version_for_reuse(self) -> None:
        self.prepare_prior_run_reuse()
        calls_before = len(self.calls())
        registry = json.loads(self.mask_prompts.read_text(encoding="utf-8"))
        registry["MP-alias"] = registry["MP-test"]
        self.mask_prompts.write_text(json.dumps(registry), encoding="utf-8")
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["mask"]["prompt_version"] = "MP-alias"
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "mask"}
        )

        self.assertNotEqual(0, completed.returncode)
        new_calls = self.calls()[calls_before:]
        self.assertEqual(1, len(new_calls))
        self.assertEqual("mask", new_calls[0]["stage"])

    def test_pipeline_v3_rejects_a_tampered_cached_reused_response(self) -> None:
        self.prepare_prior_run_reuse()
        completed = self.invoke()
        self.assertEqual(0, completed.returncode, completed.stderr)
        calls_before = len(self.calls())
        results_path = self.run_directory / "results.jsonl"
        records = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
        ]
        for record in records:
            if record["job_key"] == "mask:note-1:0":
                self.assertEqual(["Rust is pleasant"], record["response"])
                record["response"] = ["Tea helps"]
                break
        else:
            self.fail("fixture reused mask result is missing")
        results_path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

        resumed = self.invoke()

        self.assertNotEqual(0, resumed.returncode)
        self.assertIn("does not match its reuse source", resumed.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_pipeline_v3_cannot_hide_tampered_reuse_by_removing_its_marker(
        self,
    ) -> None:
        self.prepare_prior_run_reuse()
        completed = self.invoke()
        self.assertEqual(0, completed.returncode, completed.stderr)
        calls_before = len(self.calls())
        results_path = self.run_directory / "results.jsonl"
        records = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
        ]
        for record in records:
            if record["job_key"] == "mask:note-1:0":
                record["response"] = ["Tea helps"]
                del record["execution"]
                del record["reused_from"]
                break
        else:
            self.fail("fixture reused mask result is missing")
        results_path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

        resumed = self.invoke()

        self.assertNotEqual(0, resumed.returncode)
        self.assertIn("is missing required reuse provenance", resumed.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_pipeline_v3_validates_all_source_output_before_target_jobs(self) -> None:
        _, source_run, _ = self.prepare_prior_run_reuse()
        output_path = source_run / "output.json"
        output = json.loads(output_path.read_text(encoding="utf-8"))
        output["notes"][0]["takeaways"][0]["text"] = "tampered takeaway"
        output_path.write_text(json.dumps(output), encoding="utf-8")
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["reuse_source"]["output_sha256"] = hashlib.sha256(
            output_path.read_bytes()
        ).hexdigest()
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        calls_before = len(self.calls())

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "takeaway"}
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("does not match its output artifact", completed.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_pipeline_v3_ignores_invalid_jobs_for_notes_excluded_from_target(
        self,
    ) -> None:
        self.mask_prompts.write_text(
            json.dumps(
                {
                    "MP-test": (
                        "MASK INSTRUCTION\n\n<post>\n{POST}\n</post>\n\n"
                        "<takeaway>\n{TAKEAWAY}\n</takeaway>"
                    ),
                    "MPv3.4": (
                        "MASK INSTRUCTION\n\n<post>\n{POST}\n</post>\n\n"
                        "<takeaway>\n{TAKEAWAY}\n</takeaway>"
                    )
                }
            ),
            encoding="utf-8",
        )
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["mask"]["prompt_version"] = "MPv3.4"
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        source_notes = json.loads(self.notes_path.read_text(encoding="utf-8"))
        source_notes["notes"].append(
            {
                "note_id": "note-2",
                "text": (
                    "Rust is pleasant. Tea helps. "
                    "https://example.com/source"
                ),
            }
        )
        self.notes_path.write_text(json.dumps(source_notes), encoding="utf-8")
        _, source_run, _ = self.prepare_prior_run_reuse()

        output_path = source_run / "output.json"
        output = json.loads(output_path.read_text(encoding="utf-8"))
        output["notes"][1]["takeaways"][0]["fragments"] = [
            "https://example.com/source"
        ]
        output_path.write_text(json.dumps(output), encoding="utf-8")
        results_path = source_run / "results.jsonl"
        records = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
        ]
        for record in records:
            if record["job_key"] == "mask:note-2:0":
                record["response"] = ["https://example.com/source"]
        results_path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        target = json.loads(self.notes_path.read_text(encoding="utf-8"))
        target["notes"] = target["notes"][:1]
        self.notes_path.write_text(json.dumps(target), encoding="utf-8")
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["mask"]["prompt_version"] = "MPv3.4"
        config["reuse_source"]["results_sha256"] = hashlib.sha256(
            results_path.read_bytes()
        ).hexdigest()
        config["reuse_source"]["output_sha256"] = hashlib.sha256(
            output_path.read_bytes()
        ).hexdigest()
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        calls_before = len(self.calls())

        completed = self.invoke()

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(calls_before, len(self.calls()))
        target_output = json.loads(
            (self.run_directory / "output.json").read_text(encoding="utf-8")
        )
        self.assertEqual(["note-1"], [note["note_id"] for note in target_output["notes"]])

    def test_pipeline_v3_rechecks_source_hashes_when_a_partial_run_exits(self) -> None:
        _, source_run, _ = self.prepare_prior_run_reuse()
        registry = json.loads(self.mask_prompts.read_text(encoding="utf-8"))
        registry["MP-test"] = (
            "MASK INSTRUCTION CHANGED\n\n<post>\n{POST}\n</post>\n\n"
            "<takeaway>\n{TAKEAWAY}\n</takeaway>"
        )
        self.mask_prompts.write_text(json.dumps(registry), encoding="utf-8")
        source_results = source_run / "results.jsonl"

        completed = self.invoke(
            "--max-new-jobs",
            "1",
            extra_environment={"FAKE_CODEX_MUTATE_PATH": str(source_results)},
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("reuse source results hash", completed.stderr)
        self.assertTrue((self.run_directory / "results.jsonl").is_file())

    def test_pipeline_v3_does_not_reuse_a_changed_note(self) -> None:
        self.prepare_prior_run_reuse()
        calls_before = len(self.calls())
        notes = json.loads(self.notes_path.read_text(encoding="utf-8"))
        notes["notes"][0]["text"] = "Rust changed. Tea helps."
        self.notes_path.write_text(json.dumps(notes), encoding="utf-8")

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "takeaway"}
        )

        self.assertNotEqual(0, completed.returncode)
        new_calls = self.calls()[calls_before:]
        self.assertEqual(1, len(new_calls))
        self.assertEqual("takeaway", new_calls[0]["stage"])

    def test_pipeline_v3_does_not_reuse_a_changed_rendered_prompt(self) -> None:
        self.prepare_prior_run_reuse()
        calls_before = len(self.calls())
        registry = json.loads(self.mask_prompts.read_text(encoding="utf-8"))
        registry["MP-test"] = (
            "MASK INSTRUCTION CHANGED\n\n<post>\n{POST}\n</post>\n\n"
            "<takeaway>\n{TAKEAWAY}\n</takeaway>"
        )
        self.mask_prompts.write_text(json.dumps(registry), encoding="utf-8")

        completed = self.invoke(
            extra_environment={"FAKE_CODEX_FAIL_STAGE": "mask"}
        )

        self.assertNotEqual(0, completed.returncode)
        new_calls = self.calls()[calls_before:]
        self.assertEqual(1, len(new_calls))
        self.assertEqual("mask", new_calls[0]["stage"])

    def test_pipeline_v3_rejects_tampered_prior_results_and_manifest(self) -> None:
        _, source_run, _ = self.prepare_prior_run_reuse()
        calls_before = len(self.calls())
        results_path = source_run / "results.jsonl"
        manifest_path = source_run / "manifest.json"
        original_results = results_path.read_bytes()
        original_manifest = manifest_path.read_bytes()

        results_path.write_bytes(original_results + b"\n")
        tampered_results = self.invoke()
        self.assertNotEqual(0, tampered_results.returncode)
        self.assertIn("reuse source results hash", tampered_results.stderr)
        self.assertEqual(calls_before, len(self.calls()))

        results_path.write_bytes(original_results)
        manifest_path.write_bytes(original_manifest + b"\n")
        tampered_manifest = self.invoke()
        self.assertNotEqual(0, tampered_manifest.returncode)
        self.assertIn("reuse source manifest hash", tampered_manifest.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_rejects_mask_fragments_absent_from_the_source_note(self) -> None:
        completed = self.invoke(extra_environment={"FAKE_CODEX_INVALID_MASK": "1"})

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("is not present in the source note", completed.stderr)
        self.assertFalse((self.run_directory / "output.json").exists())

    def test_rejects_url_mask_fragments_for_the_frozen_mask_contract(self) -> None:
        self.mask_prompts.write_text(
            json.dumps(
                {
                    "MPv3.4": (
                        "MASK INSTRUCTION\n\n<post>\n{POST}\n</post>\n\n"
                        "<takeaway>\n{TAKEAWAY}\n</takeaway>"
                    )
                }
            ),
            encoding="utf-8",
        )
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        config["mask"]["prompt_version"] = "MPv3.4"
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        self.notes_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "notes": [
                        {
                            "note_id": "note-1",
                            "text": (
                                "Rust is pleasant. Tea helps. "
                                "https://example.com/source"
                            ),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        completed = self.invoke(extra_environment={"FAKE_CODEX_URL_MASK": "1"})

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("must not contain a URL", completed.stderr)
        self.assertFalse((self.run_directory / "output.json").exists())

    def test_exit_zero_without_a_completed_turn_is_still_audited_as_failure(
        self,
    ) -> None:
        completed = self.invoke(
            extra_environment={"FAKE_CODEX_MISSING_COMPLETION": "1"}
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("turn.completed", completed.stderr)
        self.assertFalse((self.run_directory / "output.json").exists())
        record = json.loads(
            (self.run_directory / "results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.assertEqual("failed", record["status"])

    def test_does_not_reuse_a_run_directory_for_different_model_settings(self) -> None:
        first = self.invoke()
        self.assertEqual(0, first.returncode, first.stderr)
        calls_before = len(self.calls())
        self.write_config(takeaway_model="different/model")

        second = self.invoke()

        self.assertNotEqual(0, second.returncode)
        self.assertIn("run manifest does not match", second.stderr)
        self.assertEqual(calls_before, len(self.calls()))

    def test_login_uses_the_dedicated_home_and_file_credentials(self) -> None:
        environment = os.environ.copy()
        environment["FAKE_CODEX_LOG"] = str(self.log_path)

        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "login",
                "--codex-home",
                str(self.codex_home),
                "--codex-binary",
                str(self.fake_codex),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(1, len(self.calls()))
        call = self.calls()[0]
        self.assertEqual("login", call["kind"])
        self.assertEqual(str(self.codex_home), call["codex_home"])
        self.assertIn('cli_auth_credentials_store="file"', call["argv"])


if __name__ == "__main__":
    unittest.main()
