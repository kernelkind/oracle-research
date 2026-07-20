import unittest
import tempfile
from pathlib import Path

from vast_private_create import (
    classify_create_capture,
    vast_create_arguments,
    write_attempt_marker,
)


class VastPrivateCreateTest(unittest.TestCase):
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
