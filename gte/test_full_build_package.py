import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from full_build_package import (
    finalize_provider_invoice,
    freeze_full_build_offer,
    merge_provider_invoice_pages,
    model_payload_identity,
    reconstruct_corpus,
    restore_model_metadata,
    verify_manifest,
    verify_model_payload,
    write_manifest,
    write_model_payload_identity,
)
from model_bundle import verify_bundle, write_lock


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FullBuildPackageTest(unittest.TestCase):
    def test_full_build_offer_is_frozen_only_after_every_paid_gate_passes(self):
        offer = {
            "id": 45236567,
            "machine_id": 37297,
            "bundle_id": 1075352023,
            "gpu_name": "RTX PRO 6000 WS",
            "num_gpus": 1,
            "gpu_max_power": 600.0,
            "reliability": 0.998,
            "cpu_arch": "amd64",
            "cpu_ram": 192708,
            "disk_space": 6409.4,
            "disk_bw": 12083.2,
            "inet_down": 2327.2,
            "inet_down_cost": 0.0078125,
            "inet_up": 2348.4,
            "inet_up_cost": 0.0078125,
            "direct_port_count": 299,
            "driver_version": "595.80",
            "duration": 172800,
            "rentable": True,
            "rented": False,
            "is_bid": False,
            "verification": "verified",
            "vericode": 1,
            "dph_total": 1.3592592592592592,
        }
        invalid = {
            "gpu_name": "RTX 4090",
            "num_gpus": 2,
            "gpu_max_power": 599,
            "reliability": 0.994,
            "cpu_arch": "arm64",
            "cpu_ram": 137438,
            "disk_space": 199,
            "disk_bw": 999,
            "inet_down": 499,
            "inet_down_cost": 0.020001,
            "inet_up": 99,
            "inet_up_cost": 0.020001,
            "direct_port_count": 0,
            "driver_version": "580.95.04",
            "duration": 172799,
            "rentable": False,
            "rented": True,
            "is_bid": True,
            "verification": "unverified",
            "vericode": 0,
            "dph_total": 1.3592600001,
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "offers.json"
            output = root / "offer.json"
            source.write_text(json.dumps([offer]), encoding="utf-8")
            self.assertEqual(
                freeze_full_build_offer(source, str(offer["id"]), output), [offer]
            )

            for field, value in invalid.items():
                with self.subTest(field=field):
                    rejected = dict(offer)
                    rejected[field] = value
                    source.write_text(json.dumps([rejected]), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        freeze_full_build_offer(source, str(offer["id"]), output)

            for field, value in (("machine_id", 0), ("bundle_id", -1)):
                with self.subTest(field=field):
                    rejected = dict(offer)
                    rejected[field] = value
                    source.write_text(json.dumps([rejected]), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, field):
                        freeze_full_build_offer(source, str(offer["id"]), output)

            rejected = dict(offer)
            rejected["gpu_max_power"] = 601
            source.write_text(json.dumps([rejected]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gpu_max_power"):
                freeze_full_build_offer(source, str(offer["id"]), output)

            refreshed = dict(offer)
            refreshed["machine_id"] += 1
            source.write_text(json.dumps([refreshed]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved offer"):
                freeze_full_build_offer(
                    source, str(offer["id"]), output, approved_offer_path=output
                )

            for field, value in (
                ("dph_total", 1.3592593),
                ("inet_down_cost", 0.008),
                ("inet_up_cost", 0.008),
            ):
                with self.subTest(refreshed_field=field):
                    refreshed = dict(offer)
                    refreshed[field] = value
                    source.write_text(json.dumps([refreshed]), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "approved offer"):
                        freeze_full_build_offer(
                            source,
                            str(offer["id"]),
                            root / f"refreshed-{field}.json",
                            approved_offer_path=output,
                        )

    def test_finalized_invoice_is_complete_exact_and_retryable(self):
        rows = [
            {
                "amount": "1.200001",
                "source": "instance-900000024",
                "type": "instance",
                "metadata": {"label": "crec-72-gte-full-build"},
            },
            {
                "amount": "0.062",
                "source": "instance-900000024",
                "type": "instance",
                "metadata": {"label": "crec-72-gte-full-build"},
            },
            {
                "amount": "99",
                "source": "instance-other",
                "type": "instance",
                "metadata": {"label": "other"},
            },
        ]
        document = {
            "success": True,
            "count": len(rows),
            "total": len(rows),
            "next_token": None,
            "results": rows,
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "invoice.json"
            confirmation = root / "invoice-confirmation.json"
            output = root / "charge.json"
            source.write_text(json.dumps(document), encoding="utf-8")
            confirmation.write_text(json.dumps(document), encoding="utf-8")
            output.with_name(f".{output.name}.next").write_text(
                "interrupted", encoding="utf-8"
            )

            result = finalize_provider_invoice(
                source,
                confirmation,
                "900000024",
                "crec-72-gte-full-build",
                "2026-07-20T00:30:00Z",
                "2026-07-20T00:31:00Z",
                "2026-07-20T00:36:00Z",
                output,
            )
            self.assertEqual(result["actual_charge_micro_usd"], 1_262_001)
            self.assertEqual(result["invoice_rows"], 2)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

            unlabeled = dict(document)
            unlabeled["results"] = [rows[0], dict(rows[1], metadata={})]
            unlabeled["count"] = unlabeled["total"] = 2
            source.write_text(json.dumps(unlabeled), encoding="utf-8")
            confirmation.write_text(json.dumps(unlabeled), encoding="utf-8")
            result = finalize_provider_invoice(
                source,
                confirmation,
                "900000024",
                "crec-72-gte-full-build",
                "2026-07-20T00:30:00Z",
                "2026-07-20T00:31:00Z",
                "2026-07-20T00:36:00Z",
                output,
            )
            self.assertEqual(result["actual_charge_micro_usd"], 1_262_001)
            self.assertEqual(result["invoice_rows"], 2)

            for field, value in (
                ("success", False),
                ("next_token", "next"),
                ("count", len(rows) - 1),
                ("total", len(rows) + 1),
            ):
                with self.subTest(field=field):
                    invalid = dict(document)
                    invalid[field] = value
                    source.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "complete"):
                        finalize_provider_invoice(
                            source,
                            confirmation,
                            "900000024",
                            "crec-72-gte-full-build",
                            "2026-07-20T00:30:00Z",
                            "2026-07-20T00:31:00Z",
                            "2026-07-20T00:36:00Z",
                            output,
                        )

            for field, value in (("type", "gpu"), ("metadata", {"label": "wrong"})):
                with self.subTest(match_field=field):
                    invalid = dict(document)
                    invalid["results"] = [dict(rows[0], **{field: value})]
                    invalid["count"] = invalid["total"] = 1
                    source.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "instance row"):
                        finalize_provider_invoice(
                            source,
                            confirmation,
                            "900000024",
                            "crec-72-gte-full-build",
                            "2026-07-20T00:30:00Z",
                            "2026-07-20T00:31:00Z",
                            "2026-07-20T00:36:00Z",
                            output,
                        )

            invalid = dict(document)
            invalid["results"] = [dict(rows[0], source="instance-wrong")]
            invalid["count"] = invalid["total"] = 1
            source.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not available"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            invalid = dict(document)
            invalid["results"] = [dict(rows[0], amount="0.0000001")]
            invalid["count"] = invalid["total"] = 1
            source.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "micro-USD"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            source.write_text(json.dumps(document), encoding="utf-8")
            confirmation.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not-before"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:29:59Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            with self.assertRaisesRegex(ValueError, "five minutes"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:35:59Z",
                    output,
                )

            changed = dict(document)
            changed["results"] = [rows[0], dict(rows[1], amount="0.063")]
            changed["count"] = changed["total"] = 2
            confirmation.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not stable"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

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

    def test_runbook_preserves_the_calibrated_identity_and_paid_boundary(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a",
            runbook,
        )
        self.assertIn("PAID BOUNDARY -- STOP HERE DURING CREC-72", runbook)
        self.assertIn("rental rate at most 1.359260 USD/hour", runbook)
        self.assertNotIn("1.359259 USD/hour", runbook)
        self.assertIn("/usr/bin/gzip", runbook)
        self.assertNotIn("zstd", runbook)
        self.assertIn("gte-oracle run-full-build \\", runbook)
        self.assertIn("run-full-build takes no shard ordinal", runbook)
        self.assertIn("only on the same Vast\n  instance", runbook)
        self.assertIn("No watchdog is used", runbook)
        stable = runbook.index("verify-model-payload")
        metadata = runbook.index("restore-model-metadata")
        production = runbook.index("verify package.next/bundle")
        self.assertLess(stable, metadata)
        self.assertLess(metadata, production)

    def test_runbook_has_one_executable_state_correct_paid_path(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )

        for offer_gate in (
            "direct_port_count>=1",
            "driver_version>=580.95.05",
            "inet_down>=500",
            "inet_down_cost<=0.02",
            "inet_up>=100",
            "inet_up_cost<=0.02",
            "duration>=2",
            "rented=false",
            "--type on-demand",
            "--storage 200",
        ):
            self.assertIn(offer_gate, runbook)

        self.assertIn("artifact_storage_and_transfer_micro_usd: 10000000", runbook)
        self.assertIn("umask 077", runbook)
        self.assertIn("--user \"$(id -u):$(id -g)\"", runbook)
        self.assertIn("--entrypoint /workspace/oracle-full-build/transport/control/gte-oracle", runbook)
        self.assertNotIn("    control/gte-oracle reserve-full-build", runbook)
        self.assertNotIn("    control/gte-oracle settle-full-build", runbook)

        self.assertIn("capture-identity", runbook)
        self.assertIn("launch/offer.json", runbook)
        self.assertIn("launch/create-result.json", runbook)
        self.assertIn("launch/instance.json", runbook)
        self.assertIn("transport/work-seed/budget-ledger.json", runbook)
        self.assertIn("vast_private_create.py", runbook)
        self.assertNotIn('--login "$DOCKER_LOGIN"', runbook)
        self.assertNotIn("create provider failure with no matching live instance", runbook)
        self.assertIn("create-request-attempted.txt", runbook)
        self.assertIn("create-api-outcome.json", runbook)
        self.assertIn("sanitize-instances", runbook)
        self.assertNotIn(
            'vastai show instances --raw \\\n    > "$LOCAL_ROOT/launch/live-instances',
            runbook,
        )
        self.assertIn("definitive_rejection", runbook)
        self.assertIn("request was not attempted", runbook)
        self.assertIn("if vastai show instances --raw", runbook)
        self.assertIn('test "$OFFER_ID" = "$APPROVED_OFFER_ID"', runbook)
        self.assertLess(
            runbook.index('test "$OFFER_ID" = "$APPROVED_OFFER_ID"'),
            runbook.index('"$LOCAL_ROOT/transport/control/vast_private_create.py"'),
        )
        self.assertIn("recover-create", runbook)
        self.assertIn("live instance already uses the full-build label", runbook)
        self.assertLess(
            runbook.index("live instance already uses the full-build label"),
            runbook.index("PAID BOUNDARY -- STOP HERE DURING CREC-72"),
        )
        self.assertIn("validate-instance", runbook)
        self.assertLess(runbook.index("validate-instance"), runbook.index("vastai copy"))
        self.assertIn("preparation.pid", runbook)
        self.assertIn("preparation.exit", runbook)
        self.assertIn("nohup setsid", runbook)
        self.assertIn(
            "flock --nonblock --conflict-exit-code 75 work/full-build.lock bash -c",
            runbook,
        )
        self.assertIn("work/full-build-attempts/$ATTEMPT_ID", runbook)
        self.assertIn('ATTEMPT_ID=${ATTEMPT_ID:?}', runbook)
        self.assertIn("$ATTEMPT/full-build.pid", runbook)
        self.assertIn("$ATTEMPT/full-build.exit", runbook)
        self.assertIn("$ATTEMPT/full-build.log", runbook)
        self.assertIn("$ATTEMPT/full-build.started", runbook)
        self.assertIn("worker-invocations/$ATTEMPT_ID.txt", runbook)
        self.assertIn("worker-start-not-delivered", runbook)
        self.assertIn(
            '[[ "$(cat "$prior/start.exit")" =~ ^[0-9]+$ ]]',
            runbook,
        )
        self.assertIn(
            'test "$(cat "$prior/start.exit")" -ne 0',
            runbook,
        )
        self.assertIn(
            '[[ "$(cat "$ATTEMPT/start.exit")" =~ ^[0-9]+$ ]]',
            runbook,
        )
        self.assertIn(
            'test "$(cat "$ATTEMPT/start.exit")" -ne 0',
            runbook,
        )
        self.assertIn("status=75", runbook)
        self.assertIn(
            'test -s "$ATTEMPT/full-build.orphaned"',
            runbook,
        )

        self.assertIn("result.next/work", runbook)
        self.assertIn("result.next/package", runbook)
        self.assertIn("result.next/control", runbook)
        self.assertIn('mv "$LOCAL_ROOT/result.next" "$LOCAL_ROOT/result"', runbook)
        self.assertIn("local-verification-failure.log", runbook)
        self.assertIn(
            '(cd "$LOCAL_ROOT/result.next/work" && sha256sum -c retrieval.sha256) '
            '\\\n    || { post_create_stop result-integrity; false; }',
            runbook,
        )
        self.assertIn(
            "REMOTE BUILD EXITED ZERO BUT LOCAL VERIFICATION FAILED",
            runbook,
        )
        self.assertIn(
            "FAILURE_EVIDENCE=audit/local-verification-failure.log",
            runbook,
        )
        self.assertNotIn("result/work.partial", runbook)
        self.assertIn("calibration-evidence.json", runbook)
        self.assertIn("calibration-execution-identity.json", runbook)

        self.assertIn("Derive the settlement from durable state", runbook)
        self.assertIn("may contain zero or one execution claim", runbook)
        self.assertNotIn("export SETTLEMENT_CASE=success", runbook)
        self.assertIn("full-build.exit", runbook)
        self.assertIn("claimed remote ledger is irretrievable", runbook)
        self.assertIn("canonical budget-ledger.json", runbook)
        self.assertIn("show invoices-v1 --charges --charge-type instance", runbook)
        self.assertGreaterEqual(runbook.count("fetch_complete_invoice \\"), 2)
        self.assertIn("INVOICE_NOT_BEFORE_UTC", runbook)
        self.assertIn("CONFIRMATION_OBSERVED_AT_UTC", runbook)
        self.assertIn("finalized provider invoice", runbook)
        self.assertIn("destroy_status", runbook)
        self.assertIn("live-list absence is the proof", runbook)
        self.assertIn("IMAGE_SOURCE_COMMIT=c9861a60cd6706ecd5a8f255914ebd10390bc444", runbook)
        self.assertIn("gte-oracle-source-commit.txt", runbook)
        self.assertIn("settlement/full-build-config.json", runbook)
        self.assertIn("settlement/settlement-manifest.json", runbook)
        self.assertIn("SETTLEMENT_LEDGER_SHA", runbook)
        self.assertNotIn('if test ! -f "$SETTLED_LEDGER"', runbook)
        self.assertIn('rm -rf "$LOCAL_ROOT/launch/ssh"', runbook)
        self.assertIn("destroy_instance", runbook)
        self.assertLess(
            runbook.index(
                'mv "$LOCAL_ROOT/launch/destroyed-at.txt.next" '
                '\\\n            "$LOCAL_ROOT/launch/destroyed-at.txt"'
            ),
            runbook.index(
                'mv "$LOCAL_ROOT/launch/live-instances.json.next" '
                '\\\n            "$LOCAL_ROOT/launch/destruction-confirmation.json"'
            ),
        )
        self.assertIn("setup-cost-gate", runbook)
        self.assertIn("CONTROLLER_SHA256", runbook)
        self.assertIn("CONTROL_SHA256SUMS_SHA256", runbook)
        self.assertGreaterEqual(runbook.count("verify_control_files"), 4)
        self.assertIn("TRANSPORT_MANIFEST_SHA256", runbook)
        self.assertIn("EXECUTION_PACKAGE_MANIFEST_SHA256", runbook)
        self.assertGreaterEqual(runbook.count("verify_reviewed_artifacts"), 4)
        paid = runbook.split("PAID BOUNDARY -- STOP HERE DURING CREC-72", 1)[1]
        self.assertNotIn("package_helper manifest \\\n    transport", paid)

    def test_worker_start_returns_only_after_its_lock_is_acquired(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        lines = runbook.splitlines()
        start = next(
            index
            for index, line in enumerate(lines)
            if "<<'REMOTE_WORKER'" in line
        ) + 1
        end = next(
            index for index in range(start, len(lines)) if lines[index] == "REMOTE_WORKER"
        )
        worker = "\n".join(lines[start:end])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "work").mkdir()
            worker = worker.replace(
                "cd /workspace/oracle-full-build", f"cd {root}"
            ).replace(
                'test "$(cat preparation-attempts/001/preparation.exit)" = 0',
                "true",
            )
            controller = """  setsid transport/control/gte-oracle run-full-build \\
    package/run/full-build-config.json \\
    > \"$ATTEMPT/full-build.log\" 2>&1 &"""
            self.assertIn(controller, worker)
            self.assertNotIn("' bash \"$ATTEMPT\" 8>&-", worker)
            start_lock_release = worker.index("exec 8>&-")
            worker_lock = worker.index(
                "flock --nonblock --conflict-exit-code 75 9"
            )
            started = worker.index(
                'mv "$ATTEMPT/full-build.started.next" '
                '"$ATTEMPT/full-build.started"'
            )
            self.assertLess(worker_lock, started)
            self.assertLess(started, start_lock_release)
            worker = worker.replace(
                controller,
                '  setsid sleep 2 > "$ATTEMPT/full-build.log" 2>&1 &',
            )
            result = subprocess.run(
                ["bash", "-s", "--", "001"],
                input=worker,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            attempt = root / "work/full-build-attempts/001"
            try:
                self.assertTrue((attempt / "full-build.started").is_file())
                lock = subprocess.run(
                    ["flock", "--nonblock", str(root / "work/full-build.lock"), "true"],
                    check=False,
                )
                self.assertNotEqual(lock.returncode, 0)
            finally:
                for _ in range(50):
                    if (attempt / "full-build.exit").is_file():
                        break
                    time.sleep(0.1)

    def test_worker_precondition_rejection_publishes_terminal_evidence(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        lines = runbook.splitlines()
        start = next(
            index for index, line in enumerate(lines) if "<<'REMOTE_WORKER'" in line
        ) + 1
        end = next(
            index for index in range(start, len(lines)) if lines[index] == "REMOTE_WORKER"
        )
        worker = "\n".join(lines[start:end])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "work").mkdir()
            worker = worker.replace(
                "cd /workspace/oracle-full-build", f"cd {root}"
            ).replace(
                'test "$(cat preparation-attempts/001/preparation.exit)" = 0',
                "false",
            )
            result = subprocess.run(
                ["bash", "-s", "--", "001"],
                input=worker,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            start_exit = root / "work/full-build-attempts/001/start.exit"
            self.assertTrue(start_exit.is_file(), result.stderr)
            self.assertNotEqual(int(start_exit.read_text(encoding="utf-8")), 0)

    def test_worker_not_delivered_recovery_publishes_terminal_evidence(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        lines = runbook.splitlines()
        start = next(
            index
            for index, line in enumerate(lines)
            if "<<'REMOTE_WORKER_NOT_DELIVERED'" in line
        ) + 1
        end = next(
            index
            for index in range(start, len(lines))
            if lines[index] == "REMOTE_WORKER_NOT_DELIVERED"
        )
        recovery = "\n".join(lines[start:end])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "work/full-build-attempts").mkdir(parents=True)
            recovery = recovery.replace(
                "cd /workspace/oracle-full-build", f"cd {root}"
            )
            result = subprocess.run(
                ["bash", "-s", "--", "001"],
                input=recovery,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            attempt = root / "work/full-build-attempts/001"
            self.assertEqual(
                (attempt / "start-preconditions.log").read_text(encoding="utf-8"),
                "worker-start-not-delivered\n",
            )
            self.assertEqual(
                (attempt / "start.exit").read_text(encoding="utf-8"), "74\n"
            )

    def test_worker_not_delivered_recovery_terminalizes_an_empty_attempt(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        lines = runbook.splitlines()
        start = next(
            index
            for index, line in enumerate(lines)
            if "<<'REMOTE_WORKER_NOT_DELIVERED'" in line
        ) + 1
        end = next(
            index
            for index in range(start, len(lines))
            if lines[index] == "REMOTE_WORKER_NOT_DELIVERED"
        )
        recovery = "\n".join(lines[start:end])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = root / "work/full-build-attempts/001"
            attempt.mkdir(parents=True)
            recovery = recovery.replace(
                "cd /workspace/oracle-full-build", f"cd {root}"
            )
            result = subprocess.run(
                ["bash", "-s", "--", "001"],
                input=recovery,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (attempt / "start-recovery.log").read_text(encoding="utf-8"),
                "worker-start-not-delivered\n",
            )
            self.assertEqual(
                (attempt / "start.exit").read_text(encoding="utf-8"), "74\n"
            )

    def test_model_payload_identity_ignores_cache_metadata_but_not_payload_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            metadata = model / ".huggingface" / "download"
            metadata.mkdir(parents=True)
            (model / "config.json").write_bytes(b"config\n")
            (model / "weights.safetensors").write_bytes(b"weights\n")
            (metadata / "config.json.metadata").write_bytes(b"first metadata\n")
            lock = root / "model-lock.json"
            lock.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "model_id": "Alibaba-NLP/gte-Qwen2-7B-instruct",
                        "model_revision": "a8d08b36ada9cacfe34c4d6f80957772a025daf2",
                        "files": [
                            {
                                "path": "config.json",
                                "bytes": 7,
                                "sha256": sha256(b"config\n"),
                            },
                            {
                                "path": "weights.safetensors",
                                "bytes": 8,
                                "sha256": sha256(b"weights\n"),
                            },
                            {
                                "path": ".huggingface/download/config.json.metadata",
                                "bytes": 15,
                                "sha256": sha256(b"first metadata\n"),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            identity_path = root / "model-payload.json"

            identity = write_model_payload_identity(lock, identity_path)
            self.assertEqual(len(identity["files"]), 2)
            self.assertEqual(
                verify_model_payload(model, lock, identity_path), identity
            )

            (metadata / "config.json.metadata").write_bytes(b"different metadata\n")
            self.assertEqual(
                verify_model_payload(model, lock, identity_path), identity,
                "download cache metadata is not runtime model payload",
            )

            lock_document = json.loads(lock.read_text(encoding="utf-8"))
            lock_document["files"][2] = {
                "path": ".huggingface/download/config.json.metadata",
                "bytes": 19,
                "sha256": sha256(b"different metadata\n"),
            }
            lock.write_text(json.dumps(lock_document), encoding="utf-8")
            self.assertEqual(
                model_payload_identity(lock),
                identity,
                "cache records in the legacy lock must not define stable identity",
            )
            self.assertEqual(verify_model_payload(model, lock, identity_path), identity)

            (model / "weights.safetensors").write_bytes(b"changed\n")
            with self.assertRaisesRegex(ValueError, "payload file"):
                verify_model_payload(model, lock, identity_path)

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

    def test_corpus_reconstruction_publishes_only_exact_decompressed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "data.mdb"
            source.write_bytes((b"nostr corpus\n" * 4096) + b"end")
            compressed = root / "data.mdb.gz"
            with compressed.open("wb") as output:
                subprocess.run(
                    ["gzip", "--no-name", "--stdout", str(source)],
                    check=True,
                    stdout=output,
                )
            expected = source.read_bytes()
            destination = root / "published" / "data.mdb"

            reconstruct_corpus(
                compressed,
                destination,
                len(expected),
                sha256(expected),
                Path("gzip"),
            )
            self.assertEqual(destination.read_bytes(), expected)
            self.assertEqual(
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )["sha256"],
                sha256(expected),
                "an exact published corpus is a read-only resume",
            )

            destination.write_bytes(b"wrong existing corpus")
            with self.assertRaisesRegex(ValueError, "existing corpus"):
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )

            destination.unlink()
            corrupted = bytearray(compressed.read_bytes())
            corrupted[len(corrupted) // 2] ^= 1
            compressed.write_bytes(corrupted)
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )
            self.assertFalse(destination.exists())
            self.assertFalse(destination.with_name("data.mdb.next").exists())

    def test_exact_legacy_metadata_restores_the_production_model_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "legacy"
            fresh = root / "fresh"
            for model in (legacy, fresh):
                (model / ".huggingface" / "download").mkdir(parents=True)
                (model / "config.json").write_bytes(b"config\n")
                (model / "weights.safetensors").write_bytes(b"weights\n")
            legacy_metadata = legacy / ".huggingface"
            (legacy_metadata / "download" / "config.json.metadata").write_bytes(
                b"legacy metadata\n"
            )
            (fresh / ".huggingface" / "download" / "config.json.metadata").write_bytes(
                b"fresh metadata\n"
            )
            lock = root / "model-lock.json"
            write_lock(legacy, lock)
            identity_path = root / "model-payload.json"
            write_model_payload_identity(lock, identity_path)

            self.assertEqual(
                verify_model_payload(fresh, lock, identity_path)["files"],
                model_payload_identity(lock)["files"],
            )
            with self.assertRaisesRegex(ValueError, "does not match its lock"):
                verify_bundle(fresh, lock)

            transported_metadata = root / "transported-huggingface"
            shutil.copytree(legacy_metadata, transported_metadata)
            restore_model_metadata(fresh, transported_metadata)
            self.assertEqual(verify_bundle(fresh, lock)["files"], write_lock(legacy, lock)["files"])


if __name__ == "__main__":
    unittest.main()
