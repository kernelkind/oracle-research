import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).with_name("codex_exec.py")


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
stage = "mask" if prompt.startswith("MASK INSTRUCTION") else "takeaway"
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

if os.environ.get("FAKE_CODEX_FAIL_STAGE") == stage:
    print("fixture child failure", file=sys.stderr)
    raise SystemExit(23)

if stage == "takeaway":
    response = [
        "The author finds Rust pleasant.",
        "Tea helps the author.",
    ]
elif os.environ.get("FAKE_CODEX_INVALID_MASK") == "1":
    response = ["not present in the source note"]
elif "The author finds Rust pleasant." in prompt:
    response = ["Rust is pleasant"]
else:
    response = ["Tea helps"]

response_object = {
    "fragments" if stage == "mask" else "takeaways": response,
}
output_path.write_text(json.dumps(response_object), encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": "fixture-thread"}))
print(json.dumps({"type": "turn.started"}))
if os.environ.get("FAKE_CODEX_MISSING_COMPLETION") == "1":
    raise SystemExit(0)
print(json.dumps({
    "type": "item.completed",
    "item": {
        "id": "fixture-message",
        "type": "agent_message",
        "text": json.dumps(response_object),
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
        self.config_path = self.root / "config.json"
        self.write_config()

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

    def calls(self) -> list[dict[str, object]]:
        if not self.log_path.exists():
            return []
        return json.loads(self.log_path.read_text(encoding="utf-8"))

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

        calls_before = len(self.calls())
        blocked = self.invoke()
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--retry-failed", blocked.stderr)
        self.assertEqual(calls_before, len(self.calls()))

        resumed = self.invoke("--retry-failed")
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        self.assertTrue((self.run_directory / "output.json").is_file())
        self.assertEqual(calls_before + 2, len(self.calls()))

    def test_rejects_mask_fragments_absent_from_the_source_note(self) -> None:
        completed = self.invoke(extra_environment={"FAKE_CODEX_INVALID_MASK": "1"})

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("is not present in the source note", completed.stderr)
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
