import unittest
import tempfile
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import textwrap
from unittest.mock import patch
from pathlib import Path

from vast_private_create import (
    classify_create_capture,
    vast_create_arguments,
    write_attempt_marker,
)


class VastPrivateCreateTest(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("vastai"), "requires pinned Vast SDK")
    def test_real_cli_preserves_rejection_reason_without_credentials(self):
        program = textwrap.dedent('''
            import io, json, os, sys, tempfile
            from pathlib import Path
            from unittest.mock import patch
            import requests
            from vast_private_create import main
            response = requests.Response()
            response.status_code = 400
            response._content = json.dumps({"success": False,
                "msg": "Invalid volume mount; registry=fake-token api=fake-api-key"}).encode()
            with tempfile.TemporaryDirectory() as tmp:
                marker, outcome = Path(tmp) / "attempt", Path(tmp) / "outcome.json"
                argv = ["helper", "123", "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
                    "pilot", str(marker), str(outcome), "--local-volume-id", "881"]
                with patch("sys.argv", argv), patch("sys.stdin", io.StringIO("fake-token")), \\
                        patch.dict(os.environ, {"VASTAI_NO_UPDATE_CHECK": "1", "VAST_API_KEY": "fake-api-key"}), \\
                        patch("requests.sessions.Session.send", return_value=response) as send:
                    assert main() == 10
                assert send.call_count == 1
                assert marker.exists()
                result = json.loads(outcome.read_text())
                assert result["outcome"] == "definitive_rejection"
                assert result["status_code"] == 400
                assert result["msg"] == "Invalid volume mount; registry=[REDACTED] api=[REDACTED]"
                assert "fake-token" not in outcome.read_text()
                assert "fake-api-key" not in outcome.read_text()
        ''')
        result = subprocess.run([sys.executable, "-B", "-c", program], cwd=Path(__file__).parent,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("fake-token", result.stdout + result.stderr)
        self.assertNotIn("fake-api-key", result.stdout + result.stderr)

    def test_volume_uses_the_pinned_clis_explicit_link_option(self):
        arguments = vast_create_arguments('123', 'docker.io/kernelkind/oracle-mvp@sha256:' + '4'*64,
            'pilot', 'secret', local_volume_id=881)
        self.assertEqual(arguments[arguments.index('--link-volume') + 1], '881')
        self.assertEqual(arguments[arguments.index('--mount-path') + 1], '/workspace/oracle-full-build')

    @unittest.skipUnless(importlib.util.find_spec("vastai"), "requires pinned Vast SDK")
    def test_real_cli_passes_optional_onstart_without_replacing_managed_ssh(self):
        # Vast's parser is process-global. Exercise the real helper entry point
        # and pinned CLI in a fresh process, intercepting only the paid API boundary.
        program = textwrap.dedent('''
            import io, json, os, sys, tempfile
            from pathlib import Path
            from unittest.mock import patch
            from vastai.cli.commands import instances
            from vast_private_create import main
            with tempfile.TemporaryDirectory() as tmp:
                marker, outcome = Path(tmp) / "attempt", Path(tmp) / "outcome.json"
                hook = "ssh-keygen -A && service ssh start"
                argv = ["helper", "123", "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
                        "pilot", str(marker), str(outcome), "--disk-gb", "100", "--onstart-cmd", hook,
                        "--local-volume-id", "881"]
                with patch("sys.argv", argv), patch("sys.stdin", io.StringIO("fake-token")), \\
                        patch.dict(os.environ, {"VASTAI_NO_UPDATE_CHECK": "1"}), \\
                        patch.object(instances, "get_client", return_value=object()), \\
                        patch.object(instances.instances_api, "create_instance", return_value={"success": True, "new_contract": 42}) as create, \\
                        patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden")):
                    assert main() == 0
                assert create.call_count == 1
                assert create.call_args.kwargs["runtype"] == "ssh_direc ssh_proxy"
                assert create.call_args.kwargs["onstart_cmd"] == hook
                assert create.call_args.kwargs["disk"] == 100
                assert create.call_args.kwargs["volume_info"] == {
                    "mount_path": "/workspace/oracle-full-build", "create_new": False, "volume_id": 881}
                assert marker.exists()
                assert json.loads(outcome.read_text())["new_contract"] == 42
        ''')
        result = subprocess.run([sys.executable, "-c", program], cwd=Path(__file__).parent,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("fake-token", result.stdout + result.stderr)

    def test_onstart_rejects_non_scripts_and_entrypoint_conflict(self):
        args = ("123", "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64, "pilot", "fake-token")
        for hook in (123, ["command"], "bad\0command"):
            with self.subTest(hook=hook), self.assertRaisesRegex(ValueError, "onstart"):
                vast_create_arguments(*args, onstart=hook)
        with self.assertRaisesRegex(ValueError, "managed SSH"):
            vast_create_arguments(*args, onstart="true", entrypoint="")

    @unittest.skipUnless(importlib.util.find_spec("vastai"), "requires the pinned Vast SDK")
    def test_real_vast_cli_sends_args_mode_and_public_key(self):
        from vastai.cli.main import main
        from vastai.cli.commands import instances
        arguments = vast_create_arguments("123", "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
            "pilot", "secret", disk_gb=300, entrypoint="/usr/local/bin/distillation-sshd",
            environment="-p 22:22 -e DISTILLATION_SSH_PUBLIC_KEY_BASE64=a2V5")
        with patch("sys.argv", arguments), patch.object(instances, "get_client", return_value=object()), \
                patch.object(instances.instances_api, "create_instance", return_value={"success": True, "new_contract": 456}) as create, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                main()
            self.assertEqual(stopped.exception.code, 0)
        payload = create.call_args.kwargs
        self.assertEqual(payload["runtype"], "args")
        self.assertEqual(payload["onstart_cmd"], "/usr/local/bin/distillation-sshd")
        self.assertEqual(payload["disk"], 300)
        self.assertEqual(payload["env"]["DISTILLATION_SSH_PUBLIC_KEY_BASE64"], "a2V5")
        self.assertIn("-p 22:22", payload["env"])

    def test_entrypoint_mode_preserves_image_and_exposes_ssh_without_injection(self):
        arguments = vast_create_arguments("123", "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
            "pilot", "secret", disk_gb=300, entrypoint="/usr/local/bin/distillation-sshd",
            environment="-p 22:22 -e DISTILLATION_SSH_PUBLIC_KEY_BASE64=a2V5")
        self.assertNotIn("--ssh", arguments)
        self.assertNotIn("--direct", arguments)
        self.assertEqual(arguments[-1], "--args")
        self.assertEqual(arguments[arguments.index("--disk") + 1], "300")
        self.assertIn("/usr/local/bin/distillation-sshd", arguments)

    def test_secret_is_only_added_to_the_in_process_argument_list(self):
        arguments = vast_create_arguments(
            "45236567",
            "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
            "crec-72-gte-full-build",
            "read-only-secret",
        )
        self.assertEqual(arguments[:3], ["vastai", "create", "instance"])
        self.assertIn("-u kernelkind -p read-only-secret docker.io", arguments)
        self.assertIn("--cancel-unavail", arguments)
        self.assertEqual(arguments[-2:], ["--retry", "1"])

        with self.assertRaisesRegex(ValueError, "credential"):
            vast_create_arguments(
                "45236567",
                "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
                "crec-72-gte-full-build",
                "contains whitespace",
            )

    def test_attempt_marker_is_atomic_and_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "create-request-attempted.txt"
            write_attempt_marker(marker)
            self.assertEqual(marker.read_text(encoding="utf-8"), "attempted\n")
            with self.assertRaises(FileExistsError):
                write_attempt_marker(marker)

    def test_create_capture_distinguishes_success_rejection_and_ambiguity(self):
        self.assertEqual(
            classify_create_capture(
                '{"success": true, "new_contract": 900000024}', "", 0
            ),
            {
                "schema_version": 1,
                "outcome": "success",
                "success": True,
                "new_contract": 900000024,
            },
        )
        self.assertEqual(
            classify_create_capture(
                "",
                '{"error": true, "status_code": 400, "msg": "unavailable"}',
                0,
            ),
            {
                "schema_version": 1,
                "outcome": "definitive_rejection",
                "success": False,
                "status_code": 400,
                "msg": "unavailable",
            },
        )
        self.assertEqual(
            classify_create_capture('{"success": false, "msg": "unavailable"}', "", 0)[
                "outcome"
            ],
            "definitive_rejection",
        )
        self.assertEqual(
            classify_create_capture(
                "",
                '{"error": true, "status_code": 503, "msg": "upstream"}',
                1,
            )["outcome"],
            "ambiguous",
        )


if __name__ == "__main__":
    unittest.main()
