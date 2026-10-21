import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from full_build_package import (
    exact_instance_invoice_rows,
    merge_provider_invoice_pages,
    verify_manifest,
    validate_provider_invoice_page,
    write_manifest,
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FullBuildPackageTest(unittest.TestCase):
    def test_invoice_totals_only_exact_instance_rows_and_rejects_incomplete_evidence(self):
        selected = {"source": "instance-42", "type": "instance", "amount": "1.200001",
                    "metadata": {"label": "training-fixture"}}
        other = {**selected, "source": "instance-43", "amount": "99"}
        invoice = {"success": True, "count": 2, "total": 2, "next_token": None,
                   "results": [selected, other]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invoice.json"
            path.write_text(json.dumps(invoice))
            rows, amount, digest = exact_instance_invoice_rows(path, "42", "training-fixture")
            self.assertEqual(rows, [selected])
            self.assertEqual(str(amount), "1.200001")
            self.assertEqual(len(digest), 64)
            for changes, message in (({"next_token": "next"}, "complete"),
                                     ({"total": 3}, "complete"),
                                     ({"results": [other], "count": 1, "total": 1}, "not available"),
                                     ({"results": [{**selected, "metadata": {"label": "another-job"}}, other]}, "instance row"),
                                     ({"results": [{**selected, "amount": "0.0000001"}, other]}, "micro-USD")):
                with self.subTest(changes=changes):
                    path.write_text(json.dumps({**invoice, **changes}))
                    with self.assertRaisesRegex(ValueError, message):
                        exact_instance_invoice_rows(path, "42", "training-fixture")

    def test_provider_invoice_page_validation_rejects_cli_error_output(self):
        valid = {
            "success": True,
            "count": 1,
            "total": 3,
            "next_token": "next-page",
            "results": [{"amount": "1.25", "source": "instance-1"}],
        }
        with tempfile.TemporaryDirectory() as temporary:
            page = Path(temporary) / "page.json"
            page.write_text(json.dumps(valid), encoding="utf-8")
            self.assertEqual(validate_provider_invoice_page(page), valid)

            for invalid in (
                "",
                "not JSON",
                json.dumps({"success": False, "msg": "temporary API error"}),
                json.dumps(dict(valid, count=0)),
                json.dumps(dict(valid, total=0)),
                json.dumps(dict(valid, next_token="")),
            ):
                with self.subTest(invalid=invalid):
                    page.write_text(invalid, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "invoice page"):
                        validate_provider_invoice_page(page)


    def test_provider_invoice_pages_are_merged_only_when_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "000001.json"
            second = root / "000002.json"
            output = root / "merged.json"
            rows = [
                {
                    "source": "instance-900000024",
                    "type": "instance",
                    "metadata": {"label": "crec-72-gte-full-build"},
                    "amount": "1.000000",
                    "start": 1,
                },
                {
                    "source": "instance-900000024",
                    "type": "instance",
                    "metadata": {"label": "crec-72-gte-full-build"},
                    "amount": "2.000000",
                    "start": 2,
                },
            ]
            first.write_text(
                json.dumps(
                    {
                        "success": True,
                        "count": 1,
                        "total": 2,
                        "next_token": "page-two",
                        "results": rows[:1],
                    }
                ),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "success": True,
                        "count": 1,
                        "total": 2,
                        "next_token": None,
                        "results": rows[1:],
                    }
                ),
                encoding="utf-8",
            )

            merged = merge_provider_invoice_pages([first, second], output)
            self.assertEqual(merged["results"], rows)
            self.assertEqual(merged["count"], 2)
            self.assertEqual(merged["total"], 2)
            self.assertIsNone(merged["next_token"])

            with self.assertRaisesRegex(ValueError, "terminal"):
                merge_provider_invoice_pages([first], output)


    def test_manifest_verifies_exact_files_and_rejects_lmdb_lock_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "control").mkdir()
            (root / "control" / "gte-oracle").write_bytes(b"controller")
            (root / "corpus").mkdir()
            (root / "corpus" / "data.mdb.zst").write_bytes(b"compressed")
            manifest_path = root / "transport-manifest.json"
            manifest_path.with_name(".transport-manifest.json.next").write_bytes(
                b"interrupted manifest"
            )

            manifest = write_manifest(root, manifest_path, "gte-full-build-transport")
            self.assertEqual(verify_manifest(root, manifest_path), manifest)
            (root / "control" / "gte-oracle").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_manifest(root, manifest_path)

            (root / "control" / "gte-oracle").write_bytes(b"controller")
            (root / "corpus" / "lock.mdb").write_bytes(b"transient")
            with self.assertRaisesRegex(ValueError, "lock.mdb"):
                write_manifest(root, manifest_path, "gte-full-build-transport")


if __name__ == "__main__":
    unittest.main()
