#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import vast_full_build_terminal_guard as terminal_guard


class FakeContext:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.config_path = root / "operation.json"
        self.operator_path = root / "transport/control/vast_full_build.py"
        self.label = "test-full-build"
        self.image = "example.invalid/oracle@sha256:" + "1" * 64
        self.expected = {"total_rows": 3, "final_vector_bytes": 3 * 4 * 2}

    def path(self, relative: str) -> Path:
        return self.root / relative


class FakeOperator:
    class OperationError(RuntimeError):
        pass

    def __init__(self, root: Path, *, publication_succeeds: bool) -> None:
        self.root = root
        self.publication_succeeds = publication_succeeds
        self.destroy_calls = 0
        self.fail_after_destroy_once = False
        self.fail_before_destroy_once = False

    def ensure_retrieved(self, *_args: object) -> dict[str, object]:
        receipt = {"instance_id": "900000029", "verified": True}
        path = self.root / "launch/retrieval-verification.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return receipt

    def publish_verified_result(self, *_args: object) -> bool:
        if self.publication_succeeds:
            audit = self.root / "result/audit"
            audit.mkdir(parents=True, exist_ok=True)
            (audit / "local-verification.json").write_text(
                json.dumps({"representation_version": "a" * 64}),
                encoding="utf-8",
            )
        return self.publication_succeeds

    def destroy_instance(self, *_args: object) -> dict[str, object]:
        proof = self.root / "launch/destruction-confirmation.json"
        if proof.is_file():
            return json.loads(proof.read_text(encoding="utf-8"))
        if self.fail_before_destroy_once:
            self.fail_before_destroy_once = False
            raise self.OperationError("destroy was not attempted")
        self.destroy_calls += 1
        result = {"destroyed": True, "instance_id": "900000029"}
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(json.dumps(result), encoding="utf-8")
        if self.fail_after_destroy_once:
            self.fail_after_destroy_once = False
            raise self.OperationError("destroy response was lost")
        return result

    def ensure_final_charge(self, *_args: object) -> dict[str, object]:
        return {"actual_charge_micro_usd": 1}

    def settle(self, *_args: object) -> dict[str, object]:
        return {"state": "settled"}


class TerminalGuardTests(unittest.TestCase):
    def test_loading_frozen_operator_does_not_modify_its_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "transport/control"
            control.mkdir(parents=True)
            helper_name = f"terminal_guard_helper_{root.name.replace('-', '_')}"
            (control / f"{helper_name}.py").write_text(
                "VALUE = 7\n", encoding="utf-8"
            )
            (control / "vast_full_build.py").write_text(
                f"import {helper_name}\nLOADED = {helper_name}.VALUE\n",
                encoding="utf-8",
            )
            try:
                with mock.patch.object(sys, "dont_write_bytecode", False):
                    module = terminal_guard.load_frozen_operator(root)
                self.assertEqual(module.LOADED, 7)
                self.assertFalse((control / "__pycache__").exists())
            finally:
                sys.modules.pop(helper_name, None)

    def test_manual_summary_contains_every_final_release_gate(self) -> None:
        report = {
            "review_sha256": "0" * 64,
            "guard_sha256": "1" * 64,
            "operation_config_sha256": "2" * 64,
            "frozen_operator_sha256": "3" * 64,
            "instance_id": "900000029",
            "image": "image@sha256:" + "1" * 64,
            "representation_version": "a" * 64,
            "payload_manifest": {"sha256": "b" * 64},
            "remote_terminal": {"exit_status": 0},
            "retrieval_receipt_sha256": "c" * 64,
            "retrieval": {"work_files": [1]},
            "bound_receipts": {"launch/create-result.json": "4" * 64},
            "remote_checks": {
                "query_config_sha256": "5" * 64,
                "sample_event_ids": ["6" * 64],
                "similar_notes": {"responses": [1]},
                "vectors": {"vectors": [1]},
            },
            "local_checks": {
                "package": {"files": 166},
                "control": {"files": 7},
                "sealed_files": {"work_file_count": 999},
                "vectors": {"vectors": [1]},
            },
            "syncfs_completed": True,
            "final_revalidation": {
                "remote_seal": {"work_files_sha256": "d" * 64},
                "live_instance": {"id": 900000029},
            },
            "warnings": [],
        }
        summary = terminal_guard.manual_summary(report)
        self.assertEqual(summary["review_sha256"], "0" * 64)
        self.assertEqual(summary["guard_sha256"], "1" * 64)
        self.assertEqual(summary["operation_config_sha256"], "2" * 64)
        self.assertEqual(summary["frozen_operator_sha256"], "3" * 64)
        self.assertEqual(summary["bound_receipts"], report["bound_receipts"])
        self.assertEqual(summary["retrieval_receipt_sha256"], "c" * 64)
        self.assertEqual(summary["retrieval"], report["retrieval"])
        self.assertEqual(summary["query_config_sha256"], "5" * 64)
        self.assertEqual(summary["sample_event_ids"], ["6" * 64])
        self.assertEqual(summary["local_package"], {"files": 166})
        self.assertEqual(summary["local_control"], {"files": 7})
        self.assertEqual(summary["local_sealed_files"], {"work_file_count": 999})
        self.assertTrue(summary["syncfs_completed"])
        self.assertEqual(summary["final_revalidation"], report["final_revalidation"])

    def test_tty_write_retries_partial_writes_until_every_byte_is_shown(self) -> None:
        calls: list[bytes] = []

        def partial(_descriptor: int, content: bytes) -> int:
            calls.append(content)
            return min(2, len(content))

        with mock.patch.object(terminal_guard.os, "write", side_effect=partial):
            terminal_guard.write_all(9, b"abcdef")

        self.assertEqual(calls, [b"abcdef", b"cdef", b"ef"])

    def test_remote_query_config_changes_only_the_execution_device_to_cpu(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "result.next/package/run/full-build-config.json"
            config_path.parent.mkdir(parents=True)
            original = {
                "corpus_path": "package/corpus-root/ndb",
                "representation_path": "work/representation",
                "worker": {
                    "program": "/opt/gte-venv/bin/python",
                    "worker_path": "/opt/oracle-mvp/gte/worker.py",
                    "device": "cuda",
                },
            }
            config_path.write_text(json.dumps(original), encoding="utf-8")
            runtime = SimpleNamespace(context=FakeContext(root))

            content, digest, remote_path = terminal_guard.cpu_query_config(runtime)
            changed = json.loads(content)

            self.assertEqual(changed["worker"]["device"], "cpu")
            changed["worker"]["device"] = "cuda"
            self.assertEqual(changed, original)
            self.assertEqual(digest, terminal_guard.sha256_bytes(content))
            self.assertEqual(
                remote_path,
                f"/tmp/gte-terminal-query-{digest}.json",
            )

    def test_similar_notes_review_identity_ignores_runtime_timings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = SimpleNamespace(context=FakeContext(root))
            source = "1" * 64
            version = "a" * 64

            def response(elapsed: int) -> dict[str, object]:
                return {
                    "metrics": {
                        "source_loading_ns": elapsed,
                        "query_encoding_ns": elapsed + 1,
                        "matrix_scan_ns": elapsed + 2,
                        "result_merge_ns": elapsed + 3,
                        "encoded_queries": 1,
                        "cache_hits": 0,
                        "matrix_passes": 1,
                        "scanned_rows": 3,
                        "scan_block_rows": 2,
                    },
                    "responses": [
                        {
                            "source_event_id": source,
                            "representation_version": version,
                            "represented_rows": 3,
                            "total_rows": 3,
                            "complete": True,
                            "candidates": [
                                {
                                    "event_id": f"{rank:064x}",
                                    "rank": rank,
                                    "cosine_score": 1.0 - rank / 100,
                                }
                                for rank in range(1, 11)
                            ],
                        }
                    ],
                }

            first = terminal_guard.validate_similar_notes(
                runtime, response(10), version, source
            )
            second = terminal_guard.validate_similar_notes(
                runtime, response(999), version, source
            )
            self.assertEqual(first, second)

    def test_failed_local_publication_never_destroys_the_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator = FakeOperator(root, publication_succeeds=False)
            runtime = SimpleNamespace(
                operator=operator,
                context=FakeContext(root),
                instance_id="900000029",
                attempt_id="001",
                private_key=root / "id_ed25519",
                target=["root@example.invalid"],
                remote={"state": "terminal", "kind": "full-build.exit", "exit_status": 0},
            )
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "run_remote_read_only_checks",
                    return_value={"representation_version": "a" * 64},
                ),
            ):
                with self.assertRaisesRegex(
                    terminal_guard.GuardError, "local publication did not succeed"
                ):
                    terminal_guard.run_review(root, root / "operation.json")

            self.assertEqual(operator.destroy_calls, 0)

    def successful_review(
        self, root: Path
    ) -> tuple[FakeOperator, SimpleNamespace, dict[str, object]]:
        (root / "transport/control").mkdir(parents=True)
        (root / "transport/control/vast_full_build.py").write_text(
            "# frozen test operator\n", encoding="utf-8"
        )
        (root / "operation.json").write_text("{}\n", encoding="utf-8")
        operator = FakeOperator(root, publication_succeeds=True)
        runtime = SimpleNamespace(
            operator=operator,
            context=FakeContext(root),
            instance_id="900000029",
            attempt_id="001",
            private_key=root / "id_ed25519",
            target=["root@example.invalid"],
            remote={"state": "terminal", "kind": "full-build.exit", "exit_status": 0},
        )
        with (
            mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
            mock.patch.object(
                terminal_guard,
                "run_remote_read_only_checks",
                return_value={
                    "representation_version": "a" * 64,
                    "verification": {"complete": True},
                    "similar_notes": {"responses": [{"candidates": [1]}]},
                },
            ),
            mock.patch.object(
                terminal_guard,
                "run_local_release_checks",
                return_value={
                    "representation_version": "a" * 64,
                    "package": {"files": 166},
                    "control": {"files": 7},
                    "vectors": {"vectors": 3},
                },
            ),
            mock.patch.object(terminal_guard, "sync_result"),
        ):
            review = terminal_guard.run_review(root, root / "operation.json")
        return operator, runtime, review

    def test_review_publishes_a_hash_bound_report_but_never_destroys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, _runtime, review = self.successful_review(root)

            self.assertEqual(review["state"], "awaiting_manual_destroy_approval")
            self.assertEqual(review["instance_id"], "900000029")
            self.assertEqual(review["representation_version"], "a" * 64)
            self.assertRegex(str(review["review_sha256"]), r"^[0-9a-f]{64}$")
            report = Path(str(review["report_path"]))
            self.assertTrue(report.is_file())
            self.assertEqual(terminal_guard.sha256_file(report), review["review_sha256"])
            self.assertEqual(operator.destroy_calls, 0)

    def test_destroy_rejects_the_wrong_report_hash_before_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, _review = self.successful_review(root)
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(terminal_guard, "read_tty_confirmation") as confirmation,
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "review"):
                    terminal_guard.run_destroy(
                        root, root / "operation.json", "0" * 64
                    )
            confirmation.assert_not_called()
            self.assertEqual(operator.destroy_calls, 0)

    def test_destroy_revalidation_failure_keeps_the_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    side_effect=terminal_guard.GuardError("deep verification failed"),
                ),
                mock.patch.object(terminal_guard, "read_tty_confirmation") as confirmation,
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "deep verification"):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )
            confirmation.assert_not_called()
            self.assertEqual(operator.destroy_calls, 0)

    def test_review_sync_failure_keeps_the_instance_and_writes_no_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "transport/control").mkdir(parents=True)
            (root / "transport/control/vast_full_build.py").write_text(
                "# frozen test operator\n", encoding="utf-8"
            )
            (root / "operation.json").write_text("{}\n", encoding="utf-8")
            operator = FakeOperator(root, publication_succeeds=True)
            runtime = SimpleNamespace(
                operator=operator,
                context=FakeContext(root),
                instance_id="900000029",
                attempt_id="001",
                private_key=root / "id_ed25519",
                target=["root@example.invalid"],
                remote={"state": "terminal", "kind": "full-build.exit", "exit_status": 0},
            )
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "run_remote_read_only_checks",
                    return_value={"representation_version": "a" * 64},
                ),
                mock.patch.object(
                    terminal_guard,
                    "run_local_release_checks",
                    return_value={"representation_version": "a" * 64},
                ),
                mock.patch.object(
                    terminal_guard,
                    "sync_result",
                    side_effect=terminal_guard.GuardError("sync failed"),
                ),
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "sync failed"):
                    terminal_guard.run_review(root, root / "operation.json")

            self.assertEqual(operator.destroy_calls, 0)
            self.assertFalse((root / "launch/terminal-reviews").exists())

    def test_local_release_failure_writes_no_report_and_never_destroys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator = FakeOperator(root, publication_succeeds=True)
            runtime = SimpleNamespace(
                operator=operator,
                context=FakeContext(root),
                instance_id="900000029",
                attempt_id="001",
                private_key=root / "id_ed25519",
                target=["root@example.invalid"],
                remote={"state": "terminal", "kind": "full-build.exit", "exit_status": 0},
            )
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "run_remote_read_only_checks",
                    return_value={"representation_version": "a" * 64},
                ),
                mock.patch.object(
                    terminal_guard,
                    "run_local_release_checks",
                    side_effect=terminal_guard.GuardError("local vector smoke failed"),
                ),
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "vector smoke"):
                    terminal_guard.run_review(root, root / "operation.json")

            self.assertEqual(operator.destroy_calls, 0)
            self.assertFalse((root / "launch/terminal-reviews").exists())

    def test_destroy_rejects_a_changed_payload_before_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            (root / "result/audit/local-verification.json").write_text(
                "changed\n", encoding="utf-8"
            )
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    side_effect=lambda _runtime, report: terminal_guard.verify_payload_manifest(
                        report
                    ),
                ),
                mock.patch.object(terminal_guard, "read_tty_confirmation") as confirmation,
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "changed"):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )
            confirmation.assert_not_called()
            self.assertEqual(operator.destroy_calls, 0)

    def test_post_destroy_settlement_files_do_not_change_the_payload_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _operator, _runtime, review = self.successful_review(root)
            report = terminal_guard.read_json(Path(str(review["report_path"])))
            settlement = root / "result/settlement"
            settlement.mkdir()
            (settlement / "provider-invoice.json").write_text(
                "{}\n", encoding="utf-8"
            )

            verified = terminal_guard.verify_payload_manifest(report)

            self.assertEqual(
                verified["excluded_top_level_paths"],
                ["settlement", "settlement-attempts"],
            )

    def test_post_destroy_settlement_attempts_do_not_change_the_payload_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _operator, _runtime, review = self.successful_review(root)
            report = terminal_guard.read_json(Path(str(review["report_path"])))
            attempt = root / "result/settlement-attempts/attempt-1"
            attempt.mkdir(parents=True)
            (attempt / "published.json").write_text("{}\n", encoding="utf-8")

            verified = terminal_guard.verify_payload_manifest(report)

            self.assertEqual(
                verified["excluded_top_level_paths"],
                ["settlement", "settlement-attempts"],
            )

    def test_destroy_rejects_the_wrong_tty_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    return_value="DESTROY THE WRONG INSTANCE",
                ),
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "confirmation differed"):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )
            self.assertEqual(operator.destroy_calls, 0)

    def test_fresh_revalidation_exercises_every_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator = FakeOperator(root, publication_succeeds=True)
            operator.sanitized_live_instances = mock.Mock(
                return_value=[{"id": 900000029, "label": "test-full-build"}]
            )
            operator.verify_destroy_ownership = mock.Mock(return_value=True)
            runtime = SimpleNamespace(
                operator=operator,
                context=FakeContext(root),
                instance_id="900000029",
                attempt_id="001",
                private_key=root / "id_ed25519",
                target=["root@example.invalid"],
                remote={"state": "terminal"},
            )
            remote = {"representation_version": "a" * 64}
            local = {"representation_version": "a" * 64}
            report = {
                "representation_version": "a" * 64,
                "remote_checks": remote,
                "local_checks": local,
            }
            manifest = {"file_count": 200, "total_bytes": 1234}
            with (
                mock.patch.object(
                    terminal_guard,
                    "fresh_remote_seal",
                    return_value={"work_files_sha256": "b" * 64},
                ) as seal,
                mock.patch.object(
                    terminal_guard, "run_remote_read_only_checks", return_value=remote
                ) as remote_check,
                mock.patch.object(
                    terminal_guard, "run_local_release_checks", return_value=local
                ) as local_check,
                mock.patch.object(terminal_guard, "sync_result") as sync,
                mock.patch.object(
                    terminal_guard, "verify_payload_manifest", return_value=manifest
                ) as payload,
            ):
                result = terminal_guard.revalidate_before_destroy(runtime, report)

            seal.assert_called_once_with(runtime)
            remote_check.assert_called_once_with(runtime)
            local_check.assert_called_once_with(runtime, "a" * 64, remote)
            sync.assert_called_once_with(runtime)
            payload.assert_called_once_with(report)
            operator.sanitized_live_instances.assert_called_once_with()
            operator.verify_destroy_ownership.assert_called_once()
            self.assertEqual(result["payload_file_count"], 200)
            self.assertEqual(operator.destroy_calls, 0)

    def test_destroy_requires_the_exact_tty_challenge_and_destroys_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)

            def confirm(presented: dict[str, object], challenge: str) -> str:
                self.assertEqual(
                    presented["final_revalidation"], {"verified": True}
                )
                return challenge

            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ),
                mock.patch.object(terminal_guard, "sync_result"),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    side_effect=confirm,
                ),
            ):
                result = terminal_guard.run_destroy(
                    root,
                    root / "operation.json",
                    str(review["review_sha256"]),
                )

            self.assertEqual(result["state"], "settled")
            self.assertEqual(operator.destroy_calls, 1)
            self.assertTrue(
                (root / "launch/manual-destroy-approval.json").is_file()
            )

    def test_retry_after_durable_approval_does_not_prompt_or_destroy_twice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            operator.fail_after_destroy_once = True
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ),
                mock.patch.object(terminal_guard, "sync_result"),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    side_effect=lambda _report, challenge: challenge,
                ),
            ):
                with self.assertRaisesRegex(
                    FakeOperator.OperationError, "destroy response was lost"
                ):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )

            self.assertTrue((root / "launch/manual-destroy-approval.json").is_file())
            with (
                mock.patch.object(
                    terminal_guard,
                    "load_runtime",
                    side_effect=AssertionError("authorized retry must not require SSH"),
                ),
                mock.patch.object(
                    terminal_guard, "load_recovery_runtime", return_value=runtime
                ),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    side_effect=AssertionError("must not re-enter pre-approval checks"),
                ),
                mock.patch.object(terminal_guard, "sync_result"),
                mock.patch.object(terminal_guard, "read_tty_confirmation") as confirmation,
            ):
                result = terminal_guard.run_destroy(
                    root,
                    root / "operation.json",
                    str(review["review_sha256"]),
                )

            confirmation.assert_not_called()
            self.assertEqual(result["state"], "settled")
            self.assertEqual(operator.destroy_calls, 1)

    def test_approval_before_any_destroy_attempt_revalidates_and_prompts_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            operator.fail_before_destroy_once = True
            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ) as revalidate,
                mock.patch.object(terminal_guard, "sync_result"),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    side_effect=lambda _report, challenge: challenge,
                ) as confirmation,
            ):
                with self.assertRaisesRegex(
                    FakeOperator.OperationError, "destroy was not attempted"
                ):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )
                result = terminal_guard.run_destroy(
                    root,
                    root / "operation.json",
                    str(review["review_sha256"]),
                )

            self.assertEqual(revalidate.call_count, 2)
            self.assertEqual(confirmation.call_count, 2)
            self.assertEqual(result["state"], "settled")
            self.assertEqual(operator.destroy_calls, 1)

    def create_uncrossed_authorization(
        self,
        root: Path,
        operator: FakeOperator,
        runtime: SimpleNamespace,
        review: dict[str, object],
    ) -> None:
        operator.fail_before_destroy_once = True
        with (
            mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
            mock.patch.object(
                terminal_guard,
                "revalidate_before_destroy",
                return_value={"verified": True},
            ),
            mock.patch.object(terminal_guard, "sync_result"),
            mock.patch.object(
                terminal_guard,
                "read_tty_confirmation",
                side_effect=lambda _report, challenge: challenge,
            ),
        ):
            with self.assertRaisesRegex(
                FakeOperator.OperationError, "destroy was not attempted"
            ):
                terminal_guard.run_destroy(
                    root,
                    root / "operation.json",
                    str(review["review_sha256"]),
                )

    def test_persisted_authorization_must_match_the_exact_challenge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            self.create_uncrossed_authorization(root, operator, runtime, review)
            approval = root / "launch/manual-destroy-approval.json"
            document = json.loads(approval.read_text(encoding="utf-8"))
            document["challenge_sha256"] = "0" * 64
            approval.write_text(json.dumps(document), encoding="utf-8")

            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ),
                mock.patch.object(terminal_guard, "sync_result"),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    side_effect=lambda _report, challenge: challenge,
                ),
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "challenge"):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )

            self.assertEqual(operator.destroy_calls, 0)

    def test_sync_failure_after_authorization_still_prevents_destroy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            operator, runtime, review = self.successful_review(root)
            self.create_uncrossed_authorization(root, operator, runtime, review)

            with (
                mock.patch.object(terminal_guard, "load_runtime", return_value=runtime),
                mock.patch.object(
                    terminal_guard,
                    "revalidate_before_destroy",
                    return_value={"verified": True},
                ),
                mock.patch.object(
                    terminal_guard,
                    "sync_result",
                    side_effect=terminal_guard.GuardError("sync failed after approval"),
                ),
                mock.patch.object(
                    terminal_guard,
                    "read_tty_confirmation",
                    side_effect=lambda _report, challenge: challenge,
                ),
            ):
                with self.assertRaisesRegex(terminal_guard.GuardError, "sync failed"):
                    terminal_guard.run_destroy(
                        root,
                        root / "operation.json",
                        str(review["review_sha256"]),
                    )

            self.assertTrue((root / "launch/manual-destroy-approval.json").is_file())
            self.assertEqual(operator.destroy_calls, 0)


if __name__ == "__main__":
    unittest.main()
