"""Run the successful controller's regression cases against its generalization."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gte"))
import test_vast_full_build as reference_tests


# Configuration parsing is local; remote-access failures must not stand in for it.
FAKE_COMMAND = reference_tests.FAKE_COMMAND.replace(
    'if tool == "ssh":\n',
    'if tool == "ssh":\n'
    '    if "-G" in args:\n'
    '        if state.get("fail_ssh_config"):\n'
    '            print("local SSH configuration rejected", file=sys.stderr)\n'
    '            raise SystemExit(255)\n'
    '        raise SystemExit(0)\n')


class GeneralizedControllerTest(reference_tests.VastFullBuildCliTest):
    def operation_contract(self):
        config = super().operation_contract()
        # The shared runner now requires an explicit transfer budget. The
        # reference provider fixture models zero transfer charges; no production GTE
        # contracts or frozen controllers are modified by this fixture.
        config["limits"]["transfer_allowance_micro_usd"] = 0
        return config

    def setUp(self):
        self.enterContext(mock.patch.object(reference_tests, "CLI", ROOT / "vast/runner.py"))
        self.enterContext(mock.patch.object(reference_tests, "FAKE_COMMAND", FAKE_COMMAND))
        super().setUp()
        definition = importlib.util.spec_from_file_location("vast_full_build", self.operator)
        operator = importlib.util.module_from_spec(definition)
        self.enterContext(mock.patch.dict(sys.modules, {"vast_full_build": operator}))
        definition.loader.exec_module(operator)
        self.enterContext(mock.patch.object(reference_tests, "vast_full_build", operator))

    def test_prepare_rejects_local_ssh_failure_before_provider_or_reservation(self):
        self.set_provider(fail_ssh_config=True)
        ledger_before = self.ledger.read_bytes()
        result = self.invoke("prepare")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("local SSH configuration", result.stderr)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        self.assertEqual(self.provider()["reservation_calls"], 0)
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertFalse(any(call["tool"] == "vastai" for call in self.calls()))

    def test_run_rechecks_local_ssh_before_reservation_or_create(self):
        prepared = self.prepare()
        self.set_provider(fail_ssh_config=True)
        ledger_before = self.ledger.read_bytes()
        result = self.invoke("run", "--approve", prepared["approval_sha256"])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("local SSH configuration", result.stderr)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        self.assertEqual(self.provider()["reservation_calls"], 0)
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertFalse((self.root / "launch/create-request-attempted.txt").exists())

    def test_local_ssh_preflight_does_not_block_existing_instance_cleanup(self):
        self.start_running_build()
        self.set_provider(fail_ssh_config=True, remote_status="terminal")
        calls_before = len(self.calls())
        result = self.invoke("run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output_json(result)["state"], "settled")
        self.assertFalse(any(call["tool"] == "ssh" and "-G" in call["argv"]
                             for call in self.calls()[calls_before:]))
        self.assertEqual(self.provider()["destroy_calls"], 1)


class CommandContractTest(unittest.TestCase):
    def test_only_approved_boundaries_differ_from_successful_controller(self):
        original = ast.parse((ROOT / "gte/vast_full_build.py").read_text())
        generalized = ast.parse((ROOT / "vast/runner.py").read_text())
        definitions = lambda tree: {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        before, after = definitions(original), definitions(generalized)
        # Configuration boundaries plus the approved ownership/readiness and
        # cost-estimation repairs, plus explicit local SSH configuration/preflight.
        # Optional workload startup/endpoint settings are approved. Command
        # workloads now preserve instances until explicit stop; GTE retains
        # its original deletion behavior. Approved unbounded command jobs add
        # completeness reviews; explicit continuation and observation reuse the
        # same worker/transfer flow with attempt-bound retrieval receipts.
        allowed_changes = {"Context", "verify_reviewed_artifacts", "select_offer", "verify_image",
            "ensure_retrieval_destination", "refresh_approved_offer", "ensure_reservation", "invoke_private_create",
            "recover_or_freeze_create", "record_instance_ownership", "freeze_running_instance", "remote_arguments",
            "remote_status_report", "remote_prepare_worker", "remote_controller", "publish_verified_result", "settle", "prepare",
            "verify_destroy_ownership", "cost_record_from_instance", "live_cost_record",
            "record_pre_worker_cost", "status_once", "ssh_options", "run", "ensure_ssh", "main", "parse_args",
            "cleanup_preworker_instance", "ledger_reconciliation_state", "destroy_without_remote_retrieval",
            "cleanup_terminal", "stop", "ensure_retrieved", "remote_json", "ensure_worker_started",
            "remote_worker", "remote_supervise", "remote_stop", "destroy_instance", "worker_status"}
        self.assertTrue(set(before) <= set(after))
        changed = {name for name in before if ast.dump(before[name]) != ast.dump(after[name])}
        self.assertEqual(changed, allowed_changes)
        # In particular, these execute the original control flow, without a substitute controller.
        for name in ("tar_upload_directory", "tar_download_directory",
                     "ensure_remote_prepared", "invoke_destroy_request", "ensure_final_charge"):
            self.assertEqual(ast.dump(before[name]), ast.dump(after[name]), name)
        # Progressive retrieval is optional for command workloads. Removing its
        # branches must leave the established terminal retrieval flow identical.
        body = after["ensure_retrieved"].body
        for node in list(body):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "progressive" for t in node.targets):
                body.remove(node)
            elif isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "progressive":
                index = body.index(node)
                body[index:index+1] = node.orelse
        # Fresh retrieval must also match the requested worker attempt.
        receipt_guard = body[1].body[1]
        receipt_guard.test = ast.parse('not isinstance(receipt, dict) or receipt.get("instance_id") != instance_id', mode='eval').body
        self.assertEqual(ast.dump(before["ensure_retrieved"]), ast.dump(after["ensure_retrieved"]))
        # Endpoint resolution is the only change to the proven attachment and
        # authentication-readiness loop; preserve its retries and receipts.
        replacement = ast.parse("target = resolve_ssh_target(context, instance_id)").body[0]
        body = after["ensure_ssh"].body[-2].body[0].body
        index = next(i for i, node in enumerate(body) if ast.dump(node) == ast.dump(replacement))
        body[index:index + 1] = ast.parse('''result = completed_process(["vastai", "ssh-url", instance_id])
target = parse_vast_ssh_target(result.stdout)''').body
        self.assertEqual(ast.dump(before["ensure_ssh"]), ast.dump(after["ensure_ssh"]))
        # The run flow adds the local preflight and preserves command instances.
        # Apart from those branches, retain the original GTE flow.
        preflight = ast.parse('''if (
            instance_id is None
            and not context.path("launch/create-request-attempted.txt").exists()
            and not context.path("launch/preclaim-failure.log").exists()
        ):
            verify_local_ssh(context)
        ''').body[0]
        body = after["run"].body[0].body
        matches = [node for node in body if ast.dump(node) == ast.dump(preflight)]
        self.assertEqual(len(matches), 1)
        body.remove(matches[0])
        preservation = ast.parse('''if context.command_workload:
            return preserved_instance_result(context, instance_id)
        ''').body[0]
        branches = [node for node in ast.walk(after["run"]) if isinstance(node, ast.If)]
        removed = 0
        for branch in branches:
            for node in list(branch.body):
                if ast.dump(node) == ast.dump(preservation):
                    branch.body.remove(node)
                    removed += 1
        self.assertEqual(removed, 1)
        policy = ast.parse("not context.command_workload", mode="eval").body
        calls = []
        for node in ast.walk(after["run"]):
            if isinstance(node, ast.Call):
                for keyword in list(node.keywords):
                    if keyword.arg == "delete" and ast.dump(keyword.value) == ast.dump(policy):
                        node.keywords.remove(keyword)
                        calls.append(node.func.id)
        self.assertCountEqual(calls, ["ledger_reconciliation_state", "cleanup_terminal",
                                     *["cleanup_preworker_instance"] * 3])
        self.assertEqual(ast.dump(before["run"]), ast.dump(after["run"]))
        options = after["ssh_options"].body[0].value.elts
        self.assertEqual([node.value for node in options[1:3]], ["-F", "/dev/null"])
        del options[1:3]
        self.assertEqual(ast.dump(before["ssh_options"]), ast.dump(after["ssh_options"]))

    def test_command_contract_does_not_require_gte_vectors_or_checkpoints(self):
        definition = importlib.util.spec_from_file_location("generalized_vast", ROOT / "vast/runner.py")
        operator = importlib.util.module_from_spec(definition)
        sys.modules[definition.name] = operator
        definition.loader.exec_module(operator)
        config = {
            "schema_version": 1, "artifact_kind": "vast-command-operation",
            "label": "two-gpu-pilot", "image": "docker.io/example/image@sha256:" + "a" * 64,
            "canonical_ledger_path": "/tmp/budget-ledger.json",
            "pins": {key: "b" * 64 for key in (
                "operator_sha256", "control_sha256s_sha256", "transport_manifest_sha256",
                "execution_package_manifest_sha256")},
            "limits": {"disk_gb": 100, "maximum_rental_rate_micro_usd_per_hour": 562000,
                "reservation_ceiling_micro_usd": 10000000, "lifetime_budget_micro_usd": 1000000000,
                "setup_cost_micro_usd": 1000000, "manual_stop_cost_micro_usd": 9000000},
            "timing": {"provider_attempts": 120, "provider_poll_seconds": 5,
                "preparation_attempts": 120, "preparation_poll_seconds": 30,
                "destroy_attempts": 120, "destroy_poll_seconds": 5,
                "invoice_retry_attempts": 12, "invoice_retry_seconds": 5,
                "invoice_confirmation_seconds": 300, "invoice_not_before_seconds": 88200,
                "status_watch_seconds": 900},
            "workload": {"command": ["/usr/bin/python3", "pilot.py"], "outputs": ["run"],
                "python": "/usr/bin/python3", "environment": {}, "work_seconds": 6000},
        }
        config["limits"]["transfer_allowance_micro_usd"] = 0
        operator.Context(Path("/tmp/run"), Path("/tmp/contract.json"), Path("/tmp/budget-ledger.json"), config).validate()


if __name__ == "__main__":
    unittest.main()
