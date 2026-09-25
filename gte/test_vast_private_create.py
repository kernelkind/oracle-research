import unittest
import tempfile
import contextlib
import importlib.util
import io
from unittest.mock import patch
from pathlib import Path

from vast_private_create import (
    classify_create_capture,
    vast_create_arguments,
    write_attempt_marker,
)


class VastPrivateCreateTest(unittest.TestCase):
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
