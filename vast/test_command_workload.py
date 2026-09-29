import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import package
import runner
from test_generalization import FAKE_COMMAND


class CommandWorkloadTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "operation"
        self.ledger = self.base / "budget-ledger.json"
        runner.atomic_json(self.ledger, {"lifetime_cap_cents": 100000, "actual_spend_cents": 0,
            "outstanding_commitments_cents": 0, "reserved_remaining_work_cents": 0, "entries": []})
        self.input = self.base / "input.txt"
        self.input.write_text("real workload input\n")
        self.offer = {"id": 123, "machine_id": 456, "bundle_id": 789, "num_gpus": 2,
            "gpu_name": "Tesla V100", "rentable": True, "rented": False, "is_bid": False,
            "verification": "verified", "disk_space": 100, "dph_total": .5,
            "inet_down_cost": .01, "inet_up_cost": .01}
        self.spec = {"version": 2, "label": "command-test", "offer": self.offer,
            "image": "docker.io/example/image@sha256:" + "a" * 64, "disk_gb": 100,
            "inputs": [{"source": str(self.input), "destination": "input.txt"}],
            "python": sys.executable,
            "command": [sys.executable, "-c", "from pathlib import Path; import os; "
                "Path('output.txt').write_text(Path('../package/input.txt').read_text() + os.environ['MARKER']); "
                "Path('invocations').open('a').write('once\\n')"],
            "environment": {"MARKER": "tested"}, "outputs": ["output.txt"],
            "limits": {"maximum_charge_cents": 1000, "maximum_hourly_usd": .562,
                "session_seconds": 7200, "work_seconds": 6000, "setup_cost_cents": 100,
                "manual_stop_cost_cents": 900, "inbound_gb": 20, "outbound_gb": 10}}

    def freeze(self):
        self.config = package.freeze(self.spec, self.root, self.ledger)
        self.operator = self.root / "transport/control/vast_full_build.py"
        definition = importlib.util.spec_from_file_location("frozen_command_operator", self.operator)
        self.module = importlib.util.module_from_spec(definition)
        self.enterContext(mock.patch.dict(sys.modules, {definition.name: self.module}))
        definition.loader.exec_module(self.module)
        self.context = self.module.Context.load(argparse.Namespace(root=self.root, config=self.config, operation="run"))

    def call(self, *arguments, returncode=0):
        result = subprocess.run([sys.executable, str(self.operator), "--root", str(self.root),
            "--config", str(self.config), *arguments], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, returncode, result.stderr)
        return json.loads(result.stdout) if returncode == 0 else result

    def transfer_receipts(self):
        for filename in ("approval-plan", "approval", "offer", "create-result", "instance", "pre-transfer-instance-validation"):
            runner.atomic_json(self.root / f"launch/{filename}.json", {})
        shutil.copyfile(self.ledger, self.root / "launch/reserved-budget-ledger.json")
        runner.atomic_json(self.root / "launch/full-build-reservation.json", {"ledger_sha256": runner.sha256_file(self.ledger)})
        self.assertTrue(self.call("_remote-verify-transfer")["verified"])

    def prepare_and_run(self):
        self.transfer_receipts()
        for _ in range(100):
            if self.call("_remote-prepare").get("prepared"):
                break
            time.sleep(.05)
        else:
            self.fail("real remote preparation did not finish")
        self.call("_remote-worker", "--attempt", "001")
        for _ in range(100):
            status = self.call("_remote-status", "--attempt", "001")
            if status["state"] == "terminal":
                break
            time.sleep(.05)
        else:
            self.fail("real worker did not finish")
        return status

    def test_real_command_preparation_execution_sealing_and_no_second_execution(self):
        self.freeze()
        self.assertEqual(self.prepare_and_run()["exit_status"], 0)
        self.assertEqual((self.root / "work/output.txt").read_text(), "real workload input\ntested")
        self.call("_remote-worker", "--attempt", "001")
        self.assertIn("consumed", self.call("_remote-worker", "--attempt", "002", returncode=1).stderr)
        self.assertEqual((self.root / "work/invocations").read_text(), "once\n")
        sealed = self.call("_remote-seal", "--attempt", "001")
        self.module.validate_file_records(self.root / "work", sealed["work_files"])
        (self.root / "work/output.txt").write_text("corruption")
        with self.assertRaisesRegex(self.module.OperationError, "integrity"):
            self.module.validate_file_records(self.root / "work", sealed["work_files"])

    def test_failing_workload_keeps_nonzero_terminal_evidence(self):
        self.spec["command"] = [sys.executable, "-c", "raise SystemExit(7)"]
        self.freeze()
        self.assertEqual(self.prepare_and_run()["exit_status"], 7)
        self.assertTrue(self.call("_remote-seal", "--attempt", "001")["terminal"])

    def test_changed_input_is_rejected_before_preparation(self):
        self.freeze()
        (self.root / "transport/workload/input.txt").write_text("changed")
        with self.assertRaisesRegex(self.module.OperationError, "verification failed"):
            self.module.verify_reviewed_artifacts(self.context)

    def test_real_ssh_configuration_ignores_inherited_files_and_keeps_options(self):
        self.freeze()
        private_key = self.root / "launch/ssh/id_ed25519"
        self.module.verify_local_ssh(self.context)
        self.assertFalse(private_key.parent.exists())
        private_key.parent.mkdir(parents=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
                       check=True, capture_output=True, timeout=10)
        result = subprocess.run(
            self.module.ssh_arguments(self.context, private_key, ["-vv", "-G", "root@127.0.0.1"]),
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Reading configuration data", result.stderr.replace(
            "Reading configuration data /dev/null", ""))
        values = dict(line.split(" ", 1) for line in result.stdout.splitlines())
        expected = {"user": "root", "hostname": "127.0.0.1", "port": "22",
            "batchmode": "yes", "identitiesonly": "yes", "connecttimeout": "15",
            "connectionattempts": "2", "serveraliveinterval": "15", "serveralivecountmax": "3",
            "stricthostkeychecking": "accept-new", "identityfile": str(private_key),
            "userknownhostsfile": str(self.root / "launch/ssh/known_hosts")}
        for name, value in expected.items():
            self.assertEqual(values[name], value, name)
        self.assertEqual([line for line in result.stdout.splitlines() if line.startswith("identityfile ")],
                         [f"identityfile {private_key}"])

    def test_workload_launch_settings_are_frozen_and_forwarded_to_create(self):
        self.spec.update(onstart="ssh-keygen -A && service ssh start", ssh_direct=True)
        self.freeze()
        self.assertEqual(self.context.config["onstart"], self.spec["onstart"])
        self.assertIs(self.context.config["ssh_direct"], True)
        with mock.patch.dict(os.environ, {"VAST_API_KEY": "fake-api-key"}), \
                mock.patch.object(self.module.subprocess, "run") as create:
            self.module.invoke_private_create(self.context, self.offer, "fake-registry-token")
        args = create.call_args.args[0]
        self.assertEqual(args[args.index("--onstart-cmd") + 1], self.spec["onstart"])
        self.assertNotIn("fake-registry-token", args)
        self.assertEqual(create.call_args.kwargs["input"], b"fake-registry-token")

    def test_packager_rejects_invalid_launch_settings_before_writing(self):
        for field, value in (("onstart", None), ("onstart", ["command"]),
                             ("onstart", "bad\0script"), ("ssh_direct", "false"),
                             ("ssh_direct", 1)):
            with self.subTest(field=field, value=value):
                self.spec[field] = value
                root = self.base / f"invalid-{field}-{len(str(value))}"
                with self.assertRaisesRegex(runner.OperationError, field):
                    package.freeze(self.spec, root, self.ledger)
                self.assertFalse(root.exists())
                del self.spec[field]

    def test_direct_ssh_retries_real_authentication_with_current_port(self):
        self.spec["ssh_direct"] = True
        self.freeze()
        self.context.config["timing"].update(provider_attempts=2, provider_poll_seconds=0)
        directory = self.root / "launch/ssh"
        directory.mkdir(parents=True)
        (directory / "id_ed25519").write_text("fake private key")
        (directory / "id_ed25519.pub").write_text("ssh-ed25519 fake-public-key")
        instances = [{"id": 42, "public_ipaddr": "198.51.100.42",
                      "ports": {"22/tcp": [{"HostIp": "0.0.0.0", "HostPort": port},
                                           {"HostIp": "::", "HostPort": port}]}}
                     for port in ("35960", "36002")]
        authenticated = []

        def process(args, **kwargs):
            if args[:3] == ["vastai", "attach", "ssh"]:
                return subprocess.CompletedProcess(args, 0, b"attached", b"")
            self.assertEqual(args[0], "ssh", "direct mode must not ask ssh-url for a proxy")
            self.assertEqual(args[-1], "true")
            self.assertTrue((self.root / "launch/ssh-attach-delivered.json").exists())
            self.assertFalse((self.root / "launch/ssh-attached.json").exists())
            authenticated.append(args)
            if len(authenticated) == 1:
                raise self.module.OperationError("public key not usable yet")
            return subprocess.CompletedProcess(args, 0, b"", b"")

        with mock.patch.object(self.module, "vast_json", side_effect=instances) as provider, \
                mock.patch.object(self.module, "completed_process", side_effect=process) as commands:
            _, target = self.module.ensure_ssh(self.context, "42")
        self.assertEqual(target, ["-p", "36002", "root@198.51.100.42"])
        self.assertEqual([args[args.index("-p") + 1] for args in authenticated], ["35960", "36002"])
        self.assertEqual(provider.call_args_list, [mock.call(["show", "instance", "42", "--raw"])] * 2)
        self.assertEqual(sum(c.args[0][:3] == ["vastai", "attach", "ssh"] for c in commands.call_args_list), 1)
        self.assertTrue((self.root / "launch/ssh-attached.json").exists())

    def test_direct_endpoint_refuses_missing_invalid_or_wrong_instance_without_proxy(self):
        self.spec["ssh_direct"] = True
        self.freeze()
        good = {"id": 42, "public_ipaddr": "198.51.100.42",
                "ports": {"22/tcp": [{"HostPort": "35960"}]}}
        bad = [{**good, "id": 43}, {**good, "public_ipaddr": "host;command"},
               {**good, "public_ipaddr": "0.0.0.0"}, {**good, "ports": None},
               {**good, "ports": {"22/tcp": []}}]
        bad += [{**good, "ports": {"22/tcp": [{"HostPort": p}]}}
                for p in (None, True, 0, 65536, "22 -oProxyCommand=bad")]
        bad.append({**good, "ports": {"22/tcp": [{"HostPort": "22"}, {"HostPort": "23"}]}})
        with mock.patch.object(self.module, "completed_process", side_effect=AssertionError("no proxy fallback")):
            for instance in bad:
                with self.subTest(instance=instance), self.assertRaises(self.module.OperationError):
                    self.module.resolve_ssh_target(self.context, "42", instance)
            ipv6 = {**good, "public_ipaddr": "2001:db8::42",
                    "ports": {"22/tcp": [{"HostIp": "0.0.0.0", "HostPort": "22"},
                                         {"HostIp": "::", "HostPort": "35960"}]}}
            self.assertEqual(self.module.resolve_ssh_target(self.context, "42", ipv6),
                             ["-p", "35960", "root@2001:db8::42"])

    def test_actual_100gb_two_gpu_instance_admitted_by_original_readiness_loop(self):
        self.freeze()
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance):
            result = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(result["num_gpus"], 2)
        self.assertEqual(result["disk_space"], 100)

    def test_readiness_accepts_distinct_bundle_ids_and_records_both(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=2, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "bundle_id": 987, "label": self.spec["label"],
                    "image_uuid": self.spec["image"], "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance) as provider:
            actual = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(actual["bundle_id"], 987)
        self.assertEqual(provider.call_count, 1)
        receipt = runner.read_json(self.root / "launch/pre-transfer-instance-validation.json")
        self.assertEqual(receipt["offer_bundle_id"], "789")
        self.assertEqual(receipt["bundle_id"], "987")

    def test_running_hardware_mismatch_reports_field_without_retry(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=3, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "num_gpus": 1, "label": self.spec["label"],
                    "image_uuid": self.spec["image"], "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", return_value=instance) as provider:
            with self.assertRaisesRegex(self.module.OperationError, "num_gpus"):
                self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(provider.call_count, 1)
        self.assertFalse((self.root / "launch/pre-transfer-instance-validation.json").exists())

    def test_stop_destroys_created_instance_even_when_hardware_is_rejected(self):
        self.freeze()
        self.context.config["timing"].update(destroy_attempts=2, destroy_poll_seconds=0)
        runner.atomic_json(self.root / "launch/create-result.json", {"success": True, "new_contract": 42})
        runner.atomic_json(self.root / "launch/offer.json", [self.offer])
        instance = {**self.offer, "id": 42, "num_gpus": 1, "label": self.spec["label"],
                    "image_uuid": self.spec["image"]}
        # Provider inventory/destruction and deferred billing are the only fakes.
        # stop, ownership checks, destroy requests and absence verification are real.
        with mock.patch.object(self.module, "sanitized_live_instances", side_effect=[[instance], [], []]), \
                mock.patch.object(self.module, "completed_process", return_value=subprocess.CompletedProcess([], 0, b"", b"")) as command, \
                mock.patch.object(self.module, "ensure_final_charge", return_value=None), \
                mock.patch.object(self.module, "invoice_pending_result", return_value={"state": "invoice_pending"}):
            self.assertEqual(self.module.stop(self.context)["state"], "invoice_pending")
        self.assertEqual(command.call_count, 1)
        self.assertEqual(command.call_args.args[0][:4], ["vastai", "destroy", "instance", "42"])
        proof = runner.read_json(self.root / "launch/destruction-confirmation.json")
        self.assertEqual(proof["absence_observations"], 2)

    def test_readiness_retries_provider_failure_and_waits_for_running(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=4, provider_poll_seconds=0)
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", side_effect=[
                self.module.OperationError("temporary provider failure"),
                {**instance, "actual_status": "loading"}, {**instance, "actual_status": "created"}, instance]) as provider:
            actual = self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(actual["actual_status"], "running")
        self.assertEqual(provider.call_count, 4)

    def test_cleanup_refuses_other_instance_or_conflicting_label(self):
        self.freeze()
        runner.atomic_json(self.root / "launch/create-result.json", {"success": True, "new_contract": 42})
        runner.atomic_json(self.root / "launch/offer.json", [self.offer])
        for identifier, label in ((99, self.spec["label"]), (42, "other-operation")):
            with self.subTest(identifier=identifier, label=label):
                with self.assertRaises(self.module.OperationError):
                    self.module.verify_destroy_ownership(self.context, "42", {"id": identifier, "label": label})

    def test_admission_still_rejects_changed_approved_terms(self):
        self.freeze()
        instance = {**self.offer, "id": 42, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        for field, value in (("machine_id", 999), ("gpu_name", "Other GPU"), ("num_gpus", 1),
                             ("disk_space", 99), ("dph_total", .6), ("is_bid", True),
                             ("verification", "unverified"), ("label", "other-operation"),
                             ("image_uuid", "example/wrong@sha256:" + "b" * 64)):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, field):
                    self.module.validate_instance_against_offer(self.offer, {"success": True, "new_contract": 42},
                        {**instance, field: value}, self.spec["image"], 562000,
                        expected_label=self.spec["label"], minimum_disk_gb=100)

    def test_missing_instance_waits_but_wrong_instance_id_does_not(self):
        self.freeze()
        self.context.config["timing"].update(provider_attempts=3, provider_poll_seconds=0)
        instance = {**self.offer, "id": 99, "label": self.spec["label"], "image_uuid": self.spec["image"],
                    "actual_status": "running", "intended_status": "running"}
        with mock.patch.object(self.module, "vast_json", side_effect=[{"instances": None}, instance]) as provider:
            with self.assertRaisesRegex(self.module.OperationError, "instance.*(match|ID)"):
                self.module.freeze_running_instance(self.context, self.offer, {"new_contract": 42, "success": True})
        self.assertEqual(provider.call_count, 2)

    def test_selected_offer_is_an_input_not_a_search_to_repeat(self):
        self.freeze()
        query, offer = self.module.select_offer(self.context)
        with mock.patch.object(self.module, "search_offers", side_effect=AssertionError("must not repeat offer selection")):
            self.assertEqual(self.module.refresh_approved_offer(self.context, {"offer": offer, "offer_query": query}), offer)

    def test_package_rejects_unrecognized_old_spec_and_overlapping_inputs(self):
        self.spec["version"] = 1
        with self.assertRaisesRegex(runner.OperationError, "version-2"):
            package.freeze(self.spec, self.root, self.ledger)
        self.spec["version"] = 2
        self.spec["inputs"].append(self.spec["inputs"][0])
        with self.assertRaisesRegex(runner.OperationError, "overlap"):
            package.freeze(self.spec, self.root, self.ledger)
        self.assertFalse(self.root.exists())

    def test_cost_estimate_preserves_unknown_charges_and_rounds_up(self):
        self.spec["limits"].update(inbound_gb=1, outbound_gb=0)
        self.offer["inet_down_cost"] = 0.000000001
        self.freeze()
        self.assertEqual(self.context.limits["transfer_allowance_micro_usd"], 1)
        base = {"id": 42, "duration": 0.000001, "dph_total": .5}
        for fields in ({}, {"inet_down_billed": None, "inet_up_billed": None},
                       {"inet_down_billed": 0, "inet_up_billed": 0},
                       {"inet_down_billed": "unverified", "inet_up_billed": 999999999999}):
            with self.subTest(fields=fields):
                cost = self.module.cost_record_from_instance(self.context, "42", {**base, **fields})
                self.assertEqual(cost["estimated_rental_micro_usd"], 1)
                self.assertEqual(cost["estimated_total_micro_usd"], 2)
                self.assertIsNone(cost["provider_reported_total_micro_usd"])

    def test_cost_estimate_rejects_invalid_duration_rate_and_identity(self):
        self.freeze()
        base = {"id": 42, "duration": 60, "dph_total": .5}
        for field in ("duration", "dph_total"):
            for value in (None, True, -1, float("nan"), float("inf"), "invalid"):
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(self.module.OperationError, field):
                        self.module.cost_record_from_instance(self.context, "42", {**base, field: value})
        for rate in (0, .562001):
            with self.assertRaisesRegex(self.module.OperationError, "dph_total"):
                self.module.cost_record_from_instance(self.context, "42", {**base, "dph_total": rate})
        with self.assertRaisesRegex(self.module.OperationError, "instance ID"):
            self.module.cost_record_from_instance(self.context, "43", base)

    def test_contract_refuses_missing_or_invalid_transfer_allowance(self):
        self.freeze()
        self.context.limits.pop("transfer_allowance_micro_usd")
        with self.assertRaisesRegex(self.module.OperationError, "transfer_allowance"):
            self.context.validate()
        for value in (None, True, -1, 10_000_001):
            self.context.limits["transfer_allowance_micro_usd"] = value
            with self.assertRaisesRegex(self.module.OperationError, "transfer.allowance"):
                self.context.validate()
        self.context.limits["transfer_allowance_micro_usd"] = 0
        self.context.validate()  # Explicitly approved zero is different from missing.

    def test_packaging_refuses_unknown_transfer_prices_and_excess_budget(self):
        for field in ("inet_down_cost", "inet_up_cost"):
            price = self.offer.pop(field)
            with self.assertRaisesRegex(ValueError, field):
                package.freeze(self.spec, self.root, self.ledger)
            self.assertFalse(self.root.exists())
            self.offer[field] = price
        self.spec["limits"]["inbound_gb"] = 1000
        with self.assertRaisesRegex(runner.OperationError, "exceed.*maximum charge"):
            package.freeze(self.spec, self.root, self.ledger)
        self.assertFalse(self.root.exists())

    def lifecycle_fixture(self):
        import test_vast_full_build as original
        fixture = original.VastFullBuildCliTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        # Retain the successful controller's provider fixture; account only for
        # the now-configurable private-create disk argument, not a new fake lifecycle.
        command = FAKE_COMMAND.replace(
            'marker = Path(args[-2])\n        outcome = Path(args[-1])',
            'offset = next(i for i, a in enumerate(args) if a.endswith("vast_private_create.py"))\n'
            '        marker = Path(args[offset + 4])\n        outcome = Path(args[offset + 5])')
        command = command.replace('"ssh_host": "fake.example",',
            '"public_ipaddr": "198.51.100.42", "ports": {"22/tcp": [{"HostPort": "35960"}]},\n'
            '        "ssh_host": "fake.example",')
        for name in ("docker", "tar", "vastai", "uvx", "ssh", "ssh-keygen", "nvidia-smi"):
            (fixture.bin / name).write_text(command)
        offer_result = subprocess.run([str(fixture.bin / "vastai"), "search", "offers"],
            env=fixture.environment, capture_output=True, text=True, check=True)
        self.spec.update(offer=json.loads(offer_result.stdout)[0], label="crec-test-gte-full-build",
                         image="docker.io/kernelkind/oracle-mvp@sha256:" + "9" * 64, disk_gb=200,
                         outputs=["result.bin"])
        self.spec["limits"]["maximum_hourly_usd"] = 1.36
        self.freeze()
        configuration = runner.read_json(self.config)
        configuration["timing"] = fixture.operation_contract()["timing"]
        runner.atomic_json(self.config, configuration, replace=True)
        fixture.root, fixture.operator, fixture.config, fixture.ledger = self.root, self.operator, self.config, self.ledger
        fixture.environment["FAKE_FULL_BUILD_ROOT"] = str(self.root)
        prepared = fixture.prepare()
        missing = fixture.invoke("run", "--approve", prepared["approval_sha256"])
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 0)
        ledger = runner.read_json(self.ledger)
        ledger["outstanding_commitments_cents"] = 1000
        ledger["entries"] = [{**prepared["reservation"], "reservation_id": "fixture", "status": "reserved"}]
        runner.atomic_json(self.ledger, ledger, replace=True)
        message = self.base / "commit-message"
        message.write_text("Reserve simulated command workload\n")
        for args in (["init", "--quiet"], ["add", self.ledger.name],
                     ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-F", str(message)]):
            subprocess.run(["git", "-C", str(self.base), *args], check=True, capture_output=True)
        return fixture

    def test_command_prepare_and_run_reject_local_ssh_failure_without_spending(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(fail_ssh_config=True)
        ledger_before = self.ledger.read_bytes()
        for operation in ("prepare", "run"):
            with self.subTest(operation=operation):
                result = fixture.invoke(operation)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("local SSH configuration", result.stderr)
                self.assertEqual(self.ledger.read_bytes(), ledger_before)
                self.assertEqual(fixture.provider()["create_calls"], 0)
                self.assertFalse((self.root / "launch/full-build-reservation.json").exists())
                self.assertFalse((self.root / "launch/create-request-attempted.txt").exists())

    def test_command_lifecycle_uses_original_recovery_transfer_and_destroy(self):
        self.spec.update(onstart="ssh-keygen -A && service ssh start", ssh_direct=True)
        fixture = self.lifecycle_fixture()
        fixture.set_provider(lose_worker_ack_once=True)
        first = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(first.returncode, 0)
        resumed = fixture.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(fixture.output_json(resumed)["state"], "running")
        self.assertEqual(fixture.provider()["create_calls"], 1)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        # Status and resumed execution must resolve the current mapping, not
        # the original port or the proxy returned by ssh-url.
        fixture.set_instance(ports={"22/tcp": [{"HostPort": "36002"}]})
        status = fixture.invoke("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(fixture.output_json(status)["state"], "running")
        fixture.set_provider(remote_status="terminal")
        completed = fixture.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(fixture.output_json(completed)["state"], "ledger_reconciliation_required")
        self.assertTrue((self.root / "result/audit/local-verification.json").exists())
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)
        self.assertEqual(fixture.invoke("run").returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 1)

        calls = fixture.calls()
        self.assertFalse(any(c["tool"] == "vastai" and c["argv"][:1] == ["ssh-url"] for c in calls))
        create = next(c["argv"] for c in calls if c["tool"] == "uvx")
        self.assertEqual(create[create.index("--onstart-cmd") + 1], self.spec["onstart"])
        ssh = [c["argv"] for c in calls if c["tool"] == "ssh" and "-G" not in c["argv"]]
        self.assertTrue(all("root@198.51.100.42" in args for args in ssh))
        self.assertEqual(ssh[-1][ssh[-1].index("-p") + 1], "36002")

    def test_cli_distinct_bundles_reach_worker_and_stop_deletes_once(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(bundle_id=418499128)
        started = fixture.invoke("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.output_json(started)["state"], "running")
        receipt = runner.read_json(self.root / "launch/pre-transfer-instance-validation.json")
        self.assertEqual(receipt["bundle_id"], "418499128")
        self.assertEqual(receipt["offer_bundle_id"], str(self.spec["offer"]["bundle_id"]))
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["create_calls"], 1)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])

    def test_cli_null_transfer_billing_uses_estimate_and_reconciles_actual_charge(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(duration=60, inet_down_billed=None, inet_up_billed=None,
                             inet_down_cost=None, inet_up_cost=None)
        started = fixture.invoke("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.output_json(started)["state"], "running")
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        cost = fixture.output_json(fixture.invoke("status"))["cost"]
        # 30 GB at the saved offer's $0.0078125/GB, plus one minute at
        # the approved maximum $1.36/hour. None of these are posted charges.
        self.assertEqual(cost["transfer_allowance_micro_usd"], 234375)
        self.assertEqual(cost["estimated_rental_micro_usd"], 22667)
        self.assertEqual(cost["estimated_total_micro_usd"], 257042)
        self.assertIsNone(cost["provider_reported_total_micro_usd"])
        self.assertNotIn("conservative_observed_total_micro_usd", cost)
        # Missing counters are also unknown, not an observed zero charge.
        instances = fixture.provider()["instances"]
        for key in ("inet_down_billed", "inet_up_billed", "inet_down_cost", "inet_up_cost"):
            instances[0].pop(key)
        fixture.set_provider(instances=instances)
        absent_cost = fixture.output_json(fixture.invoke("status"))["cost"]
        self.assertEqual(absent_cost["estimated_total_micro_usd"], cost["estimated_total_micro_usd"])
        self.assertIsNone(absent_cost["provider_reported_total_micro_usd"])
        fixture.set_instance(duration=25000)
        warning = fixture.output_json(fixture.invoke("status"))
        self.assertTrue(warning["manual_stop_recommended"])
        self.assertIsNone(warning["cost"]["provider_reported_total_micro_usd"])
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        actual = runner.read_json(self.root / "launch/provider-final-charge.json")
        self.assertEqual(actual["actual_charge_micro_usd"], 1250000)
        # The estimate must neither settle the ledger nor release its reserve.
        self.assertEqual(runner.read_json(self.ledger)["actual_spend_cents"], 0)
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)

    def test_cli_setup_gate_includes_full_transfer_allowance_when_billing_unknown(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        self.assertNotEqual(fixture.invoke_with_tty_secret("run").returncode, 0)
        fixture.set_instance(duration=2500, inet_down_billed=None, inet_up_billed=None)
        refused = fixture.invoke("run")
        self.assertEqual(refused.returncode, 0, refused.stderr)
        self.assertIn("setup cost estimate", (self.root / "launch/preworker-instance-failure.log").read_text())
        receipt = runner.read_json(next((self.root / "launch/pre-worker-cost-observations").glob("*.json")))
        self.assertLess(receipt["estimated_rental_micro_usd"], 1_000_000)
        self.assertGreater(receipt["estimated_total_micro_usd"], 1_000_000)
        self.assertEqual(fixture.provider()["worker_start_calls"], 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)

    def test_cli_changed_transfer_allowance_invalidates_approval_before_create(self):
        fixture = self.lifecycle_fixture()
        configuration = runner.read_json(self.config)
        configuration["limits"]["transfer_allowance_micro_usd"] = 0
        runner.atomic_json(self.config, configuration, replace=True)
        rejected = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(fixture.provider()["create_calls"], 0)

    def test_cli_changed_startup_or_endpoint_invalidates_approval_before_create(self):
        fixture = self.lifecycle_fixture()
        original = runner.read_json(self.config)
        for field, value in (("onstart", "ssh-keygen -A && service ssh start"), ("ssh_direct", True)):
            with self.subTest(field=field):
                configuration = {**original, field: value}
                runner.atomic_json(self.config, configuration, replace=True)
                rejected = fixture.invoke_with_tty_secret("run")
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(fixture.provider()["create_calls"], 0)

    def test_direct_port_disappearing_does_not_prevent_stop_and_verified_deletion(self):
        self.spec["ssh_direct"] = True
        fixture = self.lifecycle_fixture()
        started = fixture.invoke_with_tty_secret("run")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(fixture.provider()["worker_start_calls"], 1)
        fixture.set_instance(ports=None)
        fixture.set_provider(allow_destroy_without_retrieval=True)
        stopped = fixture.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])
        self.assertTrue((self.root / "launch/destruction-confirmation.json").exists())
        self.assertEqual(runner.read_json(self.ledger)["outstanding_commitments_cents"], 1000)
        self.assertFalse(any(c["tool"] == "vastai" and c["argv"][:1] == ["ssh-url"]
                             for c in fixture.calls()))

    def test_cli_hardware_rejection_cleans_up_without_uploading_or_starting(self):
        fixture = self.lifecycle_fixture()
        fixture.set_provider(crash_on_first_show_instance=True)
        interrupted = fixture.invoke_with_tty_secret("run")
        self.assertNotEqual(interrupted.returncode, 0)
        fixture.set_instance(num_gpus=99, bundle_id=418499128)
        previous_queries = fixture.provider()["show_instance_calls"]
        rejected = fixture.invoke("run")
        self.assertEqual(rejected.returncode, 0, rejected.stderr)
        self.assertIn("num_gpus", (self.root / "launch/preworker-instance-failure.log").read_text())
        self.assertEqual(fixture.provider()["show_instance_calls"], previous_queries + 1)
        self.assertEqual(fixture.provider()["remote_prepare_calls"], 0)
        self.assertEqual(fixture.provider()["worker_start_calls"], 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)
        self.assertEqual(fixture.provider()["instances"], [])
        self.assertEqual(fixture.invoke("stop").returncode, 0)
        self.assertEqual(fixture.provider()["destroy_calls"], 1)

    def test_watch_resumes_shared_run_until_cleanup_without_second_approval(self):
        self.freeze()
        states = [{'state': 'preparing'}, {'state': 'running'}, {'state': 'invoice_pending'}]
        with mock.patch.object(self.module, 'run', side_effect=states) as run, mock.patch.object(runner.time, 'sleep'):
            self.assertEqual(self.module.run_watch(self.context, 'approved'), states[-1])
        self.assertEqual(run.call_args_list, [mock.call(self.context, 'approved'),
            mock.call(self.context, None), mock.call(self.context, None)])

    def test_watch_keeps_original_deadline_and_stops_on_expiry(self):
        self.freeze()
        runner.atomic_json(self.root / 'launch/watch-deadline.json', {'deadline_utc': '2000-01-01T00:00:00Z'})
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        with mock.patch.object(self.module, 'run') as run, mock.patch.object(self.module, 'stop', return_value={'state': 'invoice_pending'}) as stop:
            self.assertEqual(self.module.run_watch(self.context, None)['state'], 'invoice_pending')
        run.assert_not_called()
        stop.assert_called_once_with(self.context)

    def test_watch_reserves_cleanup_time_and_cleans_up_after_controller_error(self):
        self.spec['limits']['cleanup_seconds'] = 600
        self.freeze()
        self.assertEqual(self.context.config['cleanup_seconds'], 600)
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        now = self.module.utc_now()
        with mock.patch.object(self.module, 'utc_now', return_value=now), \
                mock.patch.object(self.module, 'run', side_effect=ValueError('bad provider response')), \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaisesRegex(ValueError, 'bad provider response'):
                self.module.run_watch(self.context, None)
        deadline = runner.read_json(self.root / 'launch/watch-deadline.json')['deadline_utc']
        remaining = (self.module.parse_utc(deadline, 'deadline') - now).total_seconds()
        self.assertAlmostEqual(remaining, 6600, delta=1)
        stop.assert_called_once_with(self.context)


    def test_interrupt_during_watch_poll_still_uses_shared_cleanup(self):
        self.freeze()
        runner.atomic_bytes(self.root / 'launch/create-request-attempted.txt', b'attempted')
        with mock.patch.object(self.module, 'run', return_value={'state': 'running'}), \
                mock.patch.object(self.module.time, 'sleep', side_effect=KeyboardInterrupt), \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaises(KeyboardInterrupt):
                self.module.run_watch(self.context, None)
        stop.assert_called_once_with(self.context)

    def test_second_watch_cannot_interrupt_the_active_operator(self):
        self.freeze()
        with self.module.file_lock(self.root / 'watch.lock', blocking=False), \
                mock.patch.object(self.module, 'run', return_value={'state': 'invoice_pending'}) as run, \
                mock.patch.object(self.module, 'stop') as stop:
            with self.assertRaisesRegex(self.module.OperationError, "lock is held"):
                self.module.run_watch(self.context, None)
        run.assert_not_called()
        stop.assert_not_called()



if __name__ == "__main__":
    unittest.main()
