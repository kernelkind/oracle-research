import contextlib
import hashlib
import json
import os
import fcntl
import pty
import select
import shlex
import signal
import shutil
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from pathlib import Path


CLI = Path(__file__).with_name("vast_full_build.py")
SECRET = "docker-read-only-pat-that-must-not-be-recorded"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def write_manifest(root, manifest_path, kind):
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != manifest_path:
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "artifact_kind": kind,
            "total_bytes": sum(record["bytes"] for record in files),
            "files": files,
        },
    )


FAKE_COMMAND = r'''#!/usr/bin/env python3
import hashlib
import json
import os
import signal
import sys
from pathlib import Path


tool = Path(sys.argv[0]).name
args = sys.argv[1:]
root = Path(os.environ["FAKE_FULL_BUILD_ROOT"])
state_path = Path(os.environ["FAKE_PROVIDER_STATE"])
log_path = Path(os.environ["FAKE_COMMAND_LOG"])


def read_state():
    return json.loads(state_path.read_text(encoding="utf-8"))


def write_state(state):
    temporary = state_path.with_suffix(".next")
    temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(state_path)


def record():
    with log_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps({"tool": tool, "argv": args}, sort_keys=True) + "\n")


def emit(document):
    print(json.dumps(document, sort_keys=True))


def crash_parent_once(state, hook):
    if not state.get(hook) or state.get(hook + "_triggered"):
        return
    state[hook + "_triggered"] = True
    write_state(state)
    os.kill(os.getppid(), signal.SIGKILL)
    raise SystemExit(137)


def offer():
    return {
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
        "dph_total": 1.25,
    }


def instance(identifier=900000024):
    return {
        "id": identifier,
        "label": "crec-test-gte-full-build",
        "actual_status": "running",
        "intended_status": "running",
        "machine_id": 37297,
        "bundle_id": 1075352023,
        "image_uuid": "docker.io/kernelkind/oracle-mvp@sha256:" + "9" * 64,
        "gpu_name": "RTX PRO 6000 WS",
        "num_gpus": 1,
        "disk_space": 6409.4,
        "dph_total": 1.25,
        "is_bid": False,
        "verification": "verified",
        "duration": 0,
        "inet_down_billed": 0,
        "inet_down_cost": 0,
        "inet_up_billed": 0,
        "inet_up_cost": 0,
        "ssh_host": "fake.example",
        "ssh_port": 2222,
    }


def projection():
    return {
        "remaining_compute_micro_usd": 36676185,
        "artifact_storage_and_transfer_micro_usd": 10000000,
        "paid_lazy_inference_micro_usd": 0,
        "one_cold_restart_micro_usd": 148419,
        "one_lost_shard_micro_usd": 173723,
        "total_micro_usd": 46998327,
        "projected_lifetime_total_micro_usd": 48270000,
        "remaining_lifetime_budget_micro_usd": 451730000,
    }


def create_instance(ambiguous=False):
    state = read_state()
    state["create_calls"] += 1
    if not state["instances"]:
        created = instance()
        if state.get("created_instance_status"):
            created["actual_status"] = state["created_instance_status"]
        if state.get("created_instance_intended_status"):
            created["intended_status"] = state[
                "created_instance_intended_status"
            ]
        state["instances"] = [created]
    write_state(state)
    if ambiguous:
        return 11
    emit({"success": True, "new_contract": 900000024})
    return 0


record()
state = read_state()

if tool == "vastai":
    if args[:2] == ["search", "offers"]:
        emit([offer()])
    elif args[:2] == ["show", "instances"]:
        state["show_instances_calls"] += 1
        inventory = state["instances"]
        transient_step = state.get("transient_destroy_inventory_step")
        if transient_step == 0:
            inventory = []
            state["transient_destroy_inventory_step"] = 1
        elif transient_step == 1:
            inventory = [state["transient_destroy_bound_instance"]]
            state["instances"] = inventory
            state["transient_destroy_inventory_step"] = 2
            state["transient_destroy_reappearance_observations"] += 1
        elif state.get("teardown_mutated_inventory_remaining", 0) > 0:
            state["teardown_mutated_inventory_observations"] += 1
            state["teardown_mutated_inventory_remaining"] -= 1
            if state["teardown_mutated_inventory_remaining"] == 0:
                state["instances"] = []
        write_state(state)
        emit(inventory)
    elif args[:2] == ["show", "instance"]:
        state["show_instance_calls"] += 1
        write_state(state)
        crash_parent_once(state, "crash_on_first_show_instance")
        if state.get("fail_show_instance_call") == state["show_instance_calls"]:
            print("provider cost query failed", file=sys.stderr)
            raise SystemExit(76)
        if not state["instances"]:
            emit({"success": False, "msg": "not found"})
            raise SystemExit(1)
        emit(state["instances"][0])
    elif args[:2] == ["create", "instance"]:
        raise SystemExit(create_instance(state.get("create_mode") == "ambiguous"))
    elif args[:2] == ["attach", "ssh"]:
        if state.get("attach_ssh_output_mode") == "python_repr":
            print("{'success': True, 'msg': 'ssh key attached'}")
        else:
            emit({"success": True})
    elif args and args[0] == "ssh-url":
        print("root@fake.example -p 2222")
    elif args[:2] == ["destroy", "instance"]:
        if not (
            (root / "launch/retrieval-verification.json").is_file()
            or (root / "launch/preworker-instance-failure.log").is_file()
            or state.get("allow_destroy_without_retrieval")
        ):
            print("retrieval was not verified", file=sys.stderr)
            raise SystemExit(73)
        state["destroy_request_calls"] += 1
        if state.get("fail_destroy"):
            write_state(state)
            print("temporary provider destroy failure", file=sys.stderr)
            raise SystemExit(75)
        if not state["instances"]:
            write_state(state)
            print("instance not found", file=sys.stderr)
            raise SystemExit(1)
        state["destroy_calls"] += 1
        if (
            state.get("transient_destroy_absence_then_reappearance")
            and "transient_destroy_inventory_step" not in state
        ):
            state["transient_destroy_bound_instance"] = state["instances"][0]
            state["transient_destroy_inventory_step"] = 0
            state["instances"] = []
        elif state.get("teardown_mutated_inventory_once"):
            state["instances"][0]["actual_status"] = "exited"
            state["instances"][0]["intended_status"] = "stopped"
            state["teardown_mutated_inventory_remaining"] = 1
        else:
            state["instances"] = []
        write_state(state)
        crash_parent_once(state, "crash_after_destroy_response")
    elif args[:2] == ["show", "invoices-v1"]:
        state["invoice_calls"] += 1
        first_observations = list(
            (root / "launch/invoice-cycles").glob("*/first/observed-at.txt")
        )
        confirmation_observations = list(
            (root / "launch/invoice-cycles").glob(
                "*/confirmation/observed-at.txt"
            )
        )
        if first_observations and not confirmation_observations:
            crash_parent_once(state, "crash_after_first_invoice_snapshot")
        if (
            state.get("fail_invoice_snapshot_once")
            and state["invoice_calls"] <= 2
        ):
            write_state(state)
            print("temporary invoice failure", file=sys.stderr)
            raise SystemExit(74)
        amount = "1.250000"
        if state.get("invoice_mode") == "unstable" and state["invoice_calls"] % 2 == 0:
            amount = "1.260000"
        write_state(state)
        rows = [{
            "amount": amount,
            "source": "instance-900000024",
            "type": "instance",
            "metadata": {"label": "crec-test-gte-full-build"},
        }]
        emit({"success": True, "count": 1, "total": 1, "next_token": None, "results": rows})
    else:
        emit({"success": True})
    raise SystemExit(0)

if tool == "uvx":
    if any(value.endswith("vast_private_create.py") for value in args):
        marker = Path(args[-2])
        outcome = Path(args[-1])
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("attempted\n", encoding="utf-8")
        create_mode = state.get("create_mode", "success")
        if create_mode == "definitive_rejection":
            state["create_calls"] += 1
            write_state(state)
            code = 1
            result = {
                "schema_version": 1,
                "outcome": "definitive_rejection",
                "success": False,
                "exit_code": 1,
            }
        else:
            ambiguous = create_mode == "ambiguous"
            code = create_instance(ambiguous)
            state = read_state()
            result = (
                {"schema_version": 1, "outcome": "ambiguous", "success": False, "exit_code": 1}
                if ambiguous
                else {"schema_version": 1, "outcome": "success", "success": True, "new_contract": 900000024}
            )
        write = json.dumps(result, sort_keys=True, indent=2) + "\n"
        outcome.write_text(write, encoding="utf-8")
        crash_parent_once(state, "crash_after_create_outcome")
        if create_mode == "success":
            emit(result)
        raise SystemExit(code)
    raise SystemExit(0)

if tool == "docker":
    if args[:2] == ["image", "inspect"]:
        print("fixture-image-source-commit")
        raise SystemExit(0)
    if (
        args[:4] == ["run", "--rm", "--network", "none"]
        and "--entrypoint" in args
        and args[args.index("--entrypoint") + 1] == "/usr/bin/rsync"
        and args[-1] == "--version"
    ):
        state["image_rsync_checks"] += 1
        write_state(state)
        if not state.get("image_rsync_available", True):
            print("/usr/bin/rsync: not found", file=sys.stderr)
            raise SystemExit(127)
        print("rsync  version 3.2.7  protocol version 31")
        raise SystemExit(0)
    joined = " ".join(args)
    if "describe-representation" in args:
        emit({"descriptor_sha256": "d" * 64, "total_rows": 100})
    elif "project-full-build" in args:
        emit(projection())
    elif "reserve-full-build" in args:
        ledger = root / "execution/work/budget-ledger.json"
        document = json.loads(ledger.read_text(encoding="utf-8"))
        state["reservation_calls"] += 1
        crash_parent_once(state, "crash_before_reservation_mutation")
        reservation_entries = [
            entry
            for entry in document.get("entries", [])
            if entry.get("kind") == "full_build_reservation"
        ]
        if reservation_entries:
            previous = state["reservation_previous_sha256"]
        else:
            previous = hashlib.sha256(ledger.read_bytes()).hexdigest()
            document["outstanding_commitments_cents"] = 4700
            document.setdefault("entries", []).append(
                {
                    "kind": "full_build_reservation",
                    "reservation_id": "crec-test-full-build-v1",
                    "previous_ledger_sha256": previous,
                    "reserved_maximum_charge_cents": 4700,
                }
            )
            ledger.write_text(
                json.dumps(document, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            state["reservation_mutations"] += 1
            state["reservation_previous_sha256"] = previous
        reserved = hashlib.sha256(ledger.read_bytes()).hexdigest()
        state["reservation_ledger_sha256"] = reserved
        write_state(state)
        crash_parent_once(state, "crash_after_reservation_mutation")
        returned_projection = projection()
        if state.get("reservation_projection_mode") == "mismatch":
            returned_projection["one_lost_shard_micro_usd"] += 1
            returned_projection["total_micro_usd"] += 1
            returned_projection["projected_lifetime_total_micro_usd"] += 1
            returned_projection["remaining_lifetime_budget_micro_usd"] -= 1
        elif state.get("reservation_projection_mode") == "over_ceiling":
            returned_projection["remaining_compute_micro_usd"] = 36677859
            returned_projection["total_micro_usd"] = 47000001
            returned_projection["projected_lifetime_total_micro_usd"] = 48271674
            returned_projection["remaining_lifetime_budget_micro_usd"] = 451728326
        emit({
            "reservation_id": "crec-test-full-build-v1",
            "previous_ledger_sha256": previous,
            "ledger_sha256": reserved,
            **returned_projection,
        })
    elif "settle-full-build" in args or "settle-failed-full-build" in args:
        state["settle_calls"] += 1
        working = Path(args[args.index("-w") + 1])
        relative_working = working.relative_to("/workspace/oracle-full-build")
        operation = "settle-full-build" if "settle-full-build" in args else "settle-failed-full-build"
        operation_index = args.index(operation)
        config_path = root / relative_working / args[operation_index + 1]
        config = json.loads(config_path.read_text(encoding="utf-8"))
        ledger_path = root / relative_working / config["full_build"]["ledger_path"]
        pre_settlement_sha256 = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if operation == "settle-full-build":
            actual_charge = int(args[operation_index + 2])
            recorded_at = args[operation_index + 3]
        else:
            actual_charge = int(args[operation_index + 3])
            recorded_at = args[operation_index + 4]
        settlement_kind = (
            "full_build_settlement"
            if operation == "settle-full-build"
            else "failed_full_build_settlement"
        )
        settlement_entries = [
            entry
            for entry in ledger.get("entries", [])
            if entry.get("kind") == settlement_kind
        ]
        if not settlement_entries:
            ledger["outstanding_commitments_cents"] = 0
            ledger["actual_spend_cents"] = ledger.get("actual_spend_cents", 0) + 125
            ledger.setdefault("entries", []).append(
                {
                    "kind": settlement_kind,
                    "reservation_id": "crec-test-full-build-v1",
                    "actual_charge_micro_usd": actual_charge,
                    "recorded_at_utc": recorded_at,
                    "previous_ledger_sha256": pre_settlement_sha256,
                }
            )
            ledger_path.write_text(
                json.dumps(ledger, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            state["settlement_mutations"] += 1
        write_state(state)
        crash_parent_once(state, "crash_after_settlement_mutation")
        emit({
            "reservation_id": "crec-test-full-build-v1",
            "actual_charge_micro_usd": 1250000,
            "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        })
    elif "freeze-offer" in args:
        emit([offer()])
    elif "freeze-instance" in args:
        emit(instance())
    elif "freeze-create" in args:
        emit({"success": True, "new_contract": 900000024})
    elif "finalize-provider-invoice" in args:
        emit({"actual_charge_micro_usd": 1250000, "invoice_rows": 1})
    elif "verify-representation" in args:
        emit({
            "manifest": {
                "complete": True,
                "completed_rows": 100,
                "total_rows": 100,
                "build_identity_sha256": "b" * 64,
                "shards": [{"ordinal": 0, "vectors": {"bytes": 1433600}}],
            }
        })
    elif "validate-provider-invoice-page" in args or "verify" in args:
        emit({"result": "pass"})
    else:
        emit({"success": True})
    raise SystemExit(0)

if tool == "ssh-keygen":
    destination = Path(args[args.index("-f") + 1])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("private fixture key\n", encoding="utf-8")
    destination.with_suffix(destination.suffix + ".pub").write_text(
        "ssh-ed25519 fixture\n", encoding="utf-8"
    )
    raise SystemExit(0)

if tool == "rsync":
    if args == ["--version"]:
        state["local_rsync_checks"] += 1
        write_state(state)
        if not state.get("local_rsync_available", True):
            print("rsync: not found", file=sys.stderr)
            raise SystemExit(127)
        print("rsync  version 3.2.7  protocol version 31")
        raise SystemExit(0)
    source = args[-2]
    destination = args[-1]
    state["copy_calls"] += 1
    if source == str(root / "transport") + "/":
        state["transport_copy_calls"] += 1
        state["remote_transport_complete"] = not (
            state.get("simulate_incomplete_transport_once")
            and state["transport_copy_calls"] == 1
        )
        if state.get("fail_transport_rsync"):
            write_state(state)
            print("transport rsync interrupted", file=sys.stderr)
            raise SystemExit(75)
    elif source.endswith(":/workspace/oracle-full-build/preparation-attempts/"):
        state["preparation_evidence_copy_calls"] += 1
        local_destination = Path(destination.rstrip("/")) / "001"
        local_destination.mkdir(parents=True, exist_ok=True)
        failed = state.get("remote_prepare_mode") == "failed"
        log = (
            "fixture model preparation failed\n"
            if failed
            else "fixture model preparation complete\n"
        )
        (local_destination / "preparation.log").write_text(log, encoding="utf-8")
        (local_destination / "preparation.exit").write_text(
            "75\n" if failed else "0\n", encoding="utf-8"
        )
        write_state(state)
        if state.get("fail_preparation_evidence_copy"):
            print("preparation evidence copy interrupted", file=sys.stderr)
            raise SystemExit(75)
    elif source.endswith(":/workspace/oracle-full-build/work/"):
        local_destination = Path(destination.rstrip("/"))
        local_destination.mkdir(parents=True, exist_ok=True)
        payload = b"complete vectors\n"
        if state.get("retrieval_mode") == "corrupt":
            payload = b"corrupt vectors\n"
        (local_destination / "result.bin").write_bytes(payload)
        attempt = local_destination / "full-build-attempts/001"
        attempt.mkdir(parents=True, exist_ok=True)
        terminal_kind = state.get("remote_terminal_kind", "full-build.exit")
        terminal_status = 0 if terminal_kind == "full-build.exit" else 74
        (attempt / terminal_kind).write_text(
            f"{terminal_status}\n", encoding="utf-8"
        )
        (local_destination / "budget-ledger.json").write_bytes(
            (root / "launch/reserved-budget-ledger.json").read_bytes()
        )
        write_state(state)
        crash_parent_once(state, "crash_after_retrieval_copy")
    write_state(state)
    emit({"success": True})
    raise SystemExit(0)

if tool == "ssh":
    joined = " ".join(args)
    if state.get("fail_all_ssh"):
        print("ssh unavailable", file=sys.stderr)
        raise SystemExit(75)
    if "/usr/bin/rsync --version" in joined:
        state["remote_rsync_checks"] += 1
        write_state(state)
        if not state.get("remote_rsync_available", True):
            print("/usr/bin/rsync: not found", file=sys.stderr)
            raise SystemExit(127)
        print("rsync  version 3.2.7  protocol version 31")
    elif "_remote-verify-transfer" in joined:
        state["remote_verification_calls"] += 1
        verified = state.get("remote_transport_complete", False)
        if not verified:
            state["transfer_receipt_on_failed_verification"] = (
                root / "launch/remote-transfer-verified.json"
            ).exists()
            state["prepare_calls_on_failed_verification"] = state[
                "remote_prepare_calls"
            ]
        write_state(state)
        emit({
            "verified": verified,
            "instance_id": "900000024",
            "transport_manifest_sha256": hashlib.sha256(
                (root / "transport/transport-manifest.json").read_bytes()
            ).hexdigest(),
            "operation_config_sha256": hashlib.sha256(
                (root / "launch/remote/operation-contract.json").read_bytes()
            ).hexdigest(),
        })
    elif "_remote-prepare" in joined:
        state["remote_prepare_calls"] += 1
        write_state(state)
        if state.get("remote_prepare_mode") == "failed":
            emit({"prepared": False, "state": "failed", "exit_status": 75})
        elif state["remote_prepare_calls"] <= state.get(
            "remote_prepare_running_polls", 0
        ):
            emit({"prepared": False, "state": "running"})
        else:
            state["remote_prepared"] = True
            write_state(state)
            emit({"prepared": True, "state": "complete"})
    elif "_remote-worker" in joined:
        state["worker_start_calls"] += 1
        if (
            state.get("lose_worker_without_start_once")
            and state["worker_start_calls"] == 1
        ):
            write_state(state)
            raise SystemExit(75)
        if (
            state.get("lose_worker_ack_once")
            and state["worker_start_calls"] == 1
        ):
            state["remote_status"] = "running"
            write_state(state)
            raise SystemExit(75)
        if state.get("fail_worker_start_once") and state["worker_start_calls"] == 1:
            write_state(state)
            raise SystemExit(75)
        state["remote_status"] = "running"
        write_state(state)
        emit({"started": True, "acknowledged": True})
    elif "_remote-seal" in joined:
        if state.get("remote_status") != "terminal":
            raise SystemExit(75)
        state["seal_calls"] += 1
        write_state(state)
        terminal_kind = state.get("remote_terminal_kind", "full-build.exit")
        terminal_status = 0 if terminal_kind == "full-build.exit" else 74
        payloads = {
            "result.bin": b"complete vectors\n",
            f"full-build-attempts/001/{terminal_kind}": (
                f"{terminal_status}\n".encode("utf-8")
            ),
            "budget-ledger.json": (root / "launch/reserved-budget-ledger.json").read_bytes(),
        }
        preparation_payloads = {
            "001/preparation.log": b"fixture model preparation complete\n",
            "001/preparation.exit": b"0\n",
        }
        emit({
            "terminal": True,
            "terminal_record": {
                "kind": terminal_kind,
                "exit_status": terminal_status,
            },
            "work_files": [
                {
                    "path": path,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
                for path, payload in payloads.items()
            ],
            "preparation_files": [
                {
                    "path": path,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
                for path, payload in preparation_payloads.items()
            ],
        })
    elif "_remote-stop" in joined:
        state["remote_status"] = "terminal"
        write_state(state)
        emit({"stop_requested": True})
    elif "_remote-abort-unstarted" in joined:
        state["remote_abort_calls"] += 1
        if state.get("remote_status", "absent") != "absent":
            write_state(state)
            print("worker is not absent", file=sys.stderr)
            raise SystemExit(75)
        state["remote_status"] = "terminal"
        state["remote_terminal_kind"] = "start.exit"
        write_state(state)
        emit({
            "aborted_unstarted": True,
            "state": "terminal",
            "attempt_id": "001",
            "kind": "start.exit",
            "exit_status": 74,
        })
    else:
        response = {"remote_status": state.get("remote_status", "absent")}
        if response["remote_status"] == "running":
            response.update({"started": True, "execution_committed": True})
        response.update(state.get("remote_telemetry", {}))
        emit(response)
    raise SystemExit(0)

if tool == "nvidia-smi":
    print("37, 2048, 98304")
    raise SystemExit(0)

emit({"success": True})
'''


class VastFullBuildCliTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "run"
        self.root.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "commands.jsonl"
        self.log.write_text("", encoding="utf-8")
        self.provider_state = self.base / "provider-state.json"
        write_json(
            self.provider_state,
            {
                "instances": [],
                "create_calls": 0,
                "reservation_calls": 0,
                "reservation_mutations": 0,
                "copy_calls": 0,
                "transport_copy_calls": 0,
                "preparation_evidence_copy_calls": 0,
                "local_rsync_checks": 0,
                "image_rsync_checks": 0,
                "remote_rsync_checks": 0,
                "destroy_request_calls": 0,
                "destroy_calls": 0,
                "invoice_calls": 0,
                "settle_calls": 0,
                "settlement_mutations": 0,
                "seal_calls": 0,
                "show_instance_calls": 0,
                "show_instances_calls": 0,
                "teardown_mutated_inventory_observations": 0,
                "transient_destroy_reappearance_observations": 0,
                "remote_prepare_calls": 0,
                "remote_verification_calls": 0,
                "remote_transport_complete": False,
                "remote_abort_calls": 0,
                "worker_start_calls": 0,
                "remote_status": "absent",
                "retrieval_mode": "valid",
                "invoice_mode": "stable",
            },
        )
        fake = self.bin / "fake-command"
        fake.write_text(FAKE_COMMAND, encoding="utf-8")
        fake.chmod(0o755)
        for name in (
            "docker",
            "rsync",
            "vastai",
            "uvx",
            "ssh",
            "ssh-keygen",
            "nvidia-smi",
        ):
            shutil.copy2(fake, self.bin / name)

        self.ledger = self.base / "budget-ledger.json"
        write_json(
            self.ledger,
            {
                "schema_version": 2,
                "scope": "Entire oracle MVP effort",
                "currency": "USD",
                "lifetime_cap_cents": 50000,
                "calibration_lifetime_cap_cents": 2500,
                "actual_spend_cents": 127,
                "outstanding_commitments_cents": 0,
                "calibration_actual_spend_cents": 127,
                "calibration_outstanding_commitments_cents": 0,
                "reserved_remaining_work_cents": None,
                "entries": [],
            },
        )
        self.make_frozen_fixture()
        self.operator = self.root / "transport/control/vast_full_build.py"
        self.config = self.base / "operation-contract.json"
        write_json(self.config, self.operation_contract())
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "PATH": os.pathsep.join((str(self.bin), self.environment["PATH"])),
                "FAKE_FULL_BUILD_ROOT": str(self.root),
                "FAKE_PROVIDER_STATE": str(self.provider_state),
                "FAKE_COMMAND_LOG": str(self.log),
                "VAST_API_KEY": "fixture-vast-api-key",
            }
        )

    def make_frozen_fixture(self):
        control = self.root / "transport/control"
        control.mkdir(parents=True)
        operator = control / "vast_full_build.py"
        operator.write_bytes(CLI.read_bytes() if CLI.exists() else b"missing operator\n")
        controller = control / "gte-oracle"
        controller.write_bytes(b"fixture controller\n")
        controller.chmod(0o755)
        (control / "gte-oracle-source-commit.txt").write_text(
            "fixture-controller-source-commit\n", encoding="utf-8"
        )
        (control / "calibration_package.py").write_bytes(
            Path(__file__).with_name("calibration_package.py").read_bytes()
        )
        (control / "full_build_package.py").write_bytes(
            Path(__file__).with_name("full_build_package.py").read_bytes()
        )
        (control / "vast_private_create.py").write_bytes(b"fixture private create\n")
        sums = control / "SHA256SUMS"
        sums.write_text(
            "\n".join(
                f"{sha256(path)}  {path.relative_to(self.root).as_posix()}"
                for path in sorted(control.iterdir())
                if path != sums
            )
            + "\n",
            encoding="utf-8",
        )
        (self.root / "transport/payload.bin").write_bytes(b"transport payload\n")
        (self.root / "transport/work-seed").mkdir()
        shutil.copy2(
            self.ledger, self.root / "transport/work-seed/budget-ledger.json"
        )

        package = self.root / "execution/package"
        (package / "run").mkdir(parents=True)
        write_json(
            package / "run/full-build-config.json",
            {
                "container_image": "docker.io/kernelkind/oracle-mvp@sha256:" + "9" * 64,
                "full_build": {
                    "reservation_id": "crec-test-full-build-v1",
                    "ledger_path": "work/budget-ledger.json",
                    "artifact_storage_and_transfer_micro_usd": 10000000,
                    "one_cold_restart_micro_usd": 148419,
                    "one_lost_shard_micro_usd": 173723,
                },
            },
        )
        (package / "payload.bin").write_bytes(b"execution payload\n")
        (self.root / "execution/work").mkdir(parents=True)
        shutil.copy2(self.ledger, self.root / "execution/work/budget-ledger.json")

        write_manifest(
            self.root / "transport",
            self.root / "transport/transport-manifest.json",
            "gte-full-build-transport",
        )
        write_manifest(
            package,
            package / "package-manifest.json",
            "gte-full-build-execution-package",
        )

    def operation_contract(self):
        return {
            "schema_version": 1,
            "artifact_kind": "gte-vast-full-build-operation",
            "canonical_ledger_path": str(self.ledger),
            "label": "crec-test-gte-full-build",
            "image": "docker.io/kernelkind/oracle-mvp@sha256:" + "9" * 64,
            "pins": {
                "operator_sha256": sha256(
                    self.root / "transport/control/vast_full_build.py"
                ),
                "controller_sha256": sha256(
                    self.root / "transport/control/gte-oracle"
                ),
                "control_sha256s_sha256": sha256(
                    self.root / "transport/control/SHA256SUMS"
                ),
                "transport_manifest_sha256": sha256(
                    self.root / "transport/transport-manifest.json"
                ),
                "execution_package_manifest_sha256": sha256(
                    self.root / "execution/package/package-manifest.json"
                ),
                "controller_source_commit": "fixture-controller-source-commit",
                "image_source_commit": "fixture-image-source-commit",
                "descriptor_sha256": "d" * 64,
            },
            "limits": {
                "disk_gb": 200,
                "maximum_rental_rate_micro_usd_per_hour": 1359260,
                "reservation_ceiling_micro_usd": 47000000,
                "lifetime_budget_micro_usd": 500000000,
                "artifact_storage_and_transfer_micro_usd": 10000000,
                "one_cold_restart_micro_usd": 148419,
                "one_lost_shard_micro_usd": 173723,
                "setup_cost_micro_usd": 4000000,
                "manual_stop_cost_micro_usd": 42000000,
            },
            "offer_queries": {
                "us": "gpu_name=RTX_PRO_6000_WS num_gpus=1 geolocation in [US]",
                "global": "gpu_name=RTX_PRO_6000_WS num_gpus=1",
            },
            "expected": {
                "represented_rows": 50,
                "total_rows": 100,
                "completed_shards": 1,
                "final_vector_bytes": 1433600,
                "build_identity_sha256": "b" * 64,
            },
            "corpus": {"bytes": 1, "sha256": "c" * 64},
            "timing": {
                "provider_attempts": 2,
                "provider_poll_seconds": 0,
                "preparation_attempts": 2,
                "preparation_poll_seconds": 0,
                "destroy_attempts": 2,
                "destroy_poll_seconds": 0,
                "invoice_retry_attempts": 2,
                "invoice_retry_seconds": 0,
                "invoice_confirmation_seconds": 0,
                "invoice_not_before_seconds": 0,
                "status_watch_seconds": 0,
            },
        }

    def invoke(self, *arguments, input_text=None):
        result = subprocess.run(
            [
                sys.executable,
                str(self.operator),
                "--root",
                str(self.root),
                "--config",
                str(self.config),
                *arguments,
            ],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            env=self.environment,
            timeout=10,
        )
        self.assertNotIn(
            "can't open file",
            result.stderr,
            "the production full-build CLI does not exist",
        )
        return result

    def invoke_repo_operator(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--root",
                str(self.root),
                "--config",
                str(self.config),
                *arguments,
            ],
            text=True,
            capture_output=True,
            check=False,
            env=self.environment,
            timeout=10,
        )

    def spawn_status_watch(self):
        return subprocess.Popen(
            [
                sys.executable,
                str(self.operator),
                "--root",
                str(self.root),
                "--config",
                str(self.config),
                "status",
                "--watch",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.environment,
            bufsize=1,
        )

    def read_watch_document(self, process, timeout=3):
        self.assertIsNotNone(process.stdout)
        readable, _, _ = select.select([process.stdout], [], [], timeout)
        self.assertTrue(readable, "status --watch produced no snapshot")
        line = process.stdout.readline()
        self.assertTrue(line, "status --watch exited without another snapshot")
        return json.loads(line)

    def invoke_with_tty_secret(self, *arguments):
        command = [
            sys.executable,
            str(self.operator),
            "--root",
            str(self.root),
            "--config",
            str(self.config),
            *arguments,
        ]
        master, slave = pty.openpty()

        def make_controlling_terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        process = subprocess.Popen(
            command,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=self.environment,
            preexec_fn=make_controlling_terminal,
            close_fds=True,
        )
        os.close(slave)
        output = bytearray()
        sent = False
        deadline = time.monotonic() + 10
        try:
            while time.monotonic() < deadline:
                readable, _, _ = select.select([master], [], [], 0.1)
                if readable:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        chunk = b""
                    if chunk:
                        output.extend(chunk)
                        if not sent and b"Docker read-only PAT:" in output:
                            os.write(master, (SECRET + "\n").encode())
                            sent = True
                    else:
                        try:
                            process.wait(timeout=0.5)
                        except subprocess.TimeoutExpired:
                            pass
                        break
                if process.poll() is not None:
                    break
            if process.poll() is None:
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    self.fail(
                        "production CLI timed out waiting on its TTY: "
                        + output.decode("utf-8", errors="replace")
                    )
            while True:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                output.extend(chunk)
        finally:
            os.close(master)
        text = output.decode("utf-8", errors="replace").replace("\r\n", "\n")
        return subprocess.CompletedProcess(
            command,
            process.wait(),
            stdout=text,
            stderr=text,
        )

    def output_json(self, result):
        for line in reversed(result.stdout.splitlines()):
            try:
                document = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(document, dict):
                return document
        self.fail(f"CLI returned no JSON object: {result.stdout!r} {result.stderr!r}")

    def invoke_hidden(self, root, config, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--root",
                str(root),
                "--config",
                str(config),
                *arguments,
            ],
            text=True,
            capture_output=True,
            check=False,
            env=self.environment,
            timeout=10,
        )

    def calls(self):
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def matching_calls(self, *needles):
        return [
            call
            for call in self.calls()
            if all(needle in " ".join(call["argv"]) for needle in needles)
        ]

    def prepare(self):
        result = self.invoke("prepare")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.output_json(result)
        plan_path = Path(document["plan"])
        self.assertTrue(plan_path.is_relative_to(self.root))
        self.assertEqual(document["approval_sha256"], sha256(plan_path))
        self.assertEqual(document["state"], "awaiting_approval")
        return document

    def set_provider(self, **changes):
        document = json.loads(self.provider_state.read_text(encoding="utf-8"))
        document.update(changes)
        write_json(self.provider_state, document)

    def provider(self):
        return json.loads(self.provider_state.read_text(encoding="utf-8"))

    def set_instance(self, **changes):
        document = self.provider()
        self.assertEqual(len(document["instances"]), 1, document)
        document["instances"][0].update(changes)
        write_json(self.provider_state, document)

    def recorded_cost_durations(self):
        durations = []
        for path in self.root.joinpath("launch").rglob("*.json"):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                isinstance(document, dict)
                and document.get("instance_id") == "900000024"
                and isinstance(document.get("duration_seconds"), int)
            ):
                durations.append(document["duration_seconds"])
        return durations

    def tree_snapshot(self):
        return {
            path.relative_to(self.root).as_posix(): (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_size,
                path.stat().st_mtime_ns,
                path.stat().st_mode,
            )
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }

    def assert_no_paid_call(self, calls):
        rendered = [f'{call["tool"]} {" ".join(call["argv"])}' for call in calls]
        forbidden = ("reserve-full-build", "create instance", "vast_private_create.py")
        self.assertFalse(
            any(any(value in command for value in forbidden) for command in rendered),
            rendered,
        )

    def start_running_build(self, *, fail_once=False, ambiguous=False):
        prepared = self.prepare()
        self.set_provider(
            fail_worker_start_once=fail_once,
            create_mode="ambiguous" if ambiguous else "success",
        )
        first = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        if first.returncode != 0:
            if (self.root / "launch/create-request-attempted.txt").exists():
                resumed = self.invoke("run")
            else:
                resumed = self.invoke_with_tty_secret("run")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            result = resumed
        else:
            result = first
        self.assertEqual(self.output_json(result)["state"], "running")
        return prepared

    def finish_running_build(self):
        self.set_provider(remote_status="terminal", retrieval_mode="valid")
        completed = self.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.output_json(completed)["state"], "settled")
        return completed

    def assert_one_finalized_paid_run(
        self,
        settlement_kind="full_build_settlement",
        *,
        expected_destroy_calls=1,
    ):
        state = self.provider()
        self.assertEqual(state["reservation_mutations"], 1, state)
        self.assertEqual(state["create_calls"], 1, state)
        self.assertEqual(state["destroy_calls"], expected_destroy_calls, state)
        self.assertEqual(state["settlement_mutations"], 1, state)
        self.assertTrue((self.root / "result/settlement/settlement-result.json").is_file())
        self.assertFalse((self.root / "result.next").exists())
        settled_ledger = self.root / "result/settlement/budget-ledger.json"
        self.assertEqual(self.ledger.read_bytes(), settled_ledger.read_bytes())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        kinds = [entry.get("kind") for entry in ledger.get("entries", [])]
        self.assertEqual(kinds.count("full_build_reservation"), 1, kinds)
        self.assertEqual(kinds.count(settlement_kind), 1, kinds)

    def test_prepare_is_free_and_emits_a_hash_bound_approval_plan(self):
        ledger_before = self.ledger.read_bytes()
        prepared = self.prepare()
        plan = json.loads(Path(prepared["plan"]).read_text(encoding="utf-8"))
        self.assertEqual(plan["label"], "crec-test-gte-full-build")
        self.assertEqual(plan["offer"]["id"], 45236567)
        self.assertEqual(plan["reservation_ceiling_micro_usd"], 47000000)
        self.assertEqual(
            plan["canonical_ledger_sha256"], hashlib.sha256(ledger_before).hexdigest()
        )
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        self.assert_no_paid_call(self.calls())

    def test_prepare_refuses_missing_local_rsync_before_provider_use(self):
        self.set_provider(local_rsync_available=False)
        rejected = self.invoke("prepare")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("rsync", rejected.stderr.lower())
        self.assertEqual(self.provider()["local_rsync_checks"], 1)
        self.assertFalse(
            any(call["tool"] == "vastai" for call in self.calls()),
            self.calls(),
        )

    def test_prepare_refuses_image_without_rsync_before_provider_use(self):
        self.set_provider(image_rsync_available=False)
        rejected = self.invoke("prepare")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("rsync", rejected.stderr.lower())
        self.assertEqual(self.provider()["image_rsync_checks"], 1)
        self.assertEqual(self.provider()["local_rsync_checks"], 0)
        self.assertFalse(
            any(call["tool"] == "vastai" for call in self.calls()),
            self.calls(),
        )

    def test_public_ledger_override_is_rejected_before_any_mutation(self):
        identical_copy = self.base / "byte-identical-budget-ledger.json"
        shutil.copy2(self.ledger, identical_copy)
        root_before = self.tree_snapshot()
        provider_before = self.provider_state.read_bytes()
        ledger_before = self.ledger.read_bytes()
        calls_before = self.calls()

        rejected = self.invoke(
            "--ledger", str(identical_copy), "prepare"
        )

        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(
            rejected.stderr.lower(), r"(unrecognized|ledger|canonical)"
        )
        self.assertEqual(self.calls(), calls_before)
        self.assertEqual(self.tree_snapshot(), root_before)
        self.assertEqual(self.provider_state.read_bytes(), provider_before)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        self.assertEqual(identical_copy.read_bytes(), ledger_before)

    def test_repo_source_operator_cannot_enter_the_reviewed_paid_workflow(self):
        rejected = self.invoke_repo_operator("prepare")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(
            rejected.stderr.lower(), r"(transport|frozen|operator|source)"
        )
        self.assert_no_paid_call(self.calls())

    def test_run_rejects_missing_or_wrong_approval_before_reservation_or_create(self):
        self.prepare()
        ledger_before = self.ledger.read_bytes()
        call_count = len(self.calls())
        missing = self.invoke("run")
        wrong = self.invoke("run", "--approve", "0" * 64, input_text=SECRET + "\n")
        self.assertNotEqual(missing.returncode, 0)
        self.assertNotEqual(wrong.returncode, 0)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        self.assert_no_paid_call(self.calls()[call_count:])

    def test_create_reentry_rechecks_unique_label_before_writing_its_marker(self):
        prepared = self.prepare()
        self.set_provider(crash_before_reservation_mutation=True)
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue(
            (self.root / "launch/approval.json").is_file(), interrupted.stderr
        )
        self.assertFalse(
            (self.root / "launch/create-request-attempted.txt").exists()
        )
        state = self.provider()
        state["instances"] = [
            {"id": 99999999, "label": "crec-test-gte-full-build"}
        ]
        write_json(self.provider_state, state)

        rejected = self.invoke_with_tty_secret("run")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(rejected.stderr.lower(), r"(live instance|label)")
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertFalse(
            (self.root / "launch/create-request-attempted.txt").exists()
        )

    def test_status_watch_is_nonbilling_after_zero_cost_definitive_create_rejection(self):
        prepared = self.prepare()
        self.set_provider(create_mode="definitive_rejection")
        rejected_create = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(rejected_create.returncode, 0, rejected_create.stderr)
        self.assertEqual(self.output_json(rejected_create)["state"], "settled")
        charge = json.loads(
            (self.root / "launch/provider-final-charge.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(charge["actual_charge_micro_usd"], 0)
        self.assertEqual(self.provider()["instances"], [])
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )

        watched = self.invoke("status", "--watch")
        self.assertEqual(watched.returncode, 0, watched.stderr)
        snapshots = [
            json.loads(line)
            for line in watched.stdout.splitlines()
            if line
        ]
        self.assertTrue(snapshots)
        self.assertTrue(
            all(snapshot["state"] == "settled" for snapshot in snapshots),
            snapshots,
        )
        self.assertTrue(
            all(snapshot["billing_possible"] is False for snapshot in snapshots),
            snapshots,
        )

    def test_created_instance_that_never_runs_is_stopped_and_destroyed_once(self):
        prepared = self.prepare()
        self.set_provider(created_instance_status="loading")
        not_running = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(not_running.returncode, 0, not_running.stderr)
        self.assertEqual(self.output_json(not_running)["state"], "settled")
        self.assertTrue((self.root / "launch/create-result.json").is_file())
        self.assertTrue(
            (self.root / "launch/instance-ownership.json").is_file()
        )
        self.assertTrue(
            (self.root / "launch/create-authorized-destroy.json").is_file()
        )
        self.assertEqual(self.provider()["create_calls"], 1)
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["create_calls"], 1)
        self.assertEqual(self.provider()["destroy_calls"], 1)

        repeated = self.invoke("stop")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(self.provider()["destroy_calls"], 1)

    def test_stop_recovers_successful_create_outcome_before_instance_runs(self):
        prepared = self.prepare()
        self.set_provider(
            created_instance_status="loading",
            crash_after_create_outcome=True,
        )
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue((self.root / "launch/create-api-outcome.json").is_file())
        self.assertFalse((self.root / "launch/create-result.json").exists())
        self.assertEqual(self.provider()["create_calls"], 1)

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertTrue((self.root / "launch/create-result.json").is_file())
        self.assertEqual(self.provider()["create_calls"], 1)
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_interrupted_resumption_never_reserves_or_creates_twice(self):
        self.start_running_build(fail_once=True)
        self.assertEqual(len(self.matching_calls("reserve-full-build")), 1)
        create_calls = self.matching_calls("vast_private_create.py") + self.matching_calls(
            "create", "instance"
        )
        self.assertEqual(len(create_calls), 1)
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["create_calls"], 1)
        self.assertTrue((self.root / "launch/create-request-attempted.txt").is_file())

    def test_ambiguous_create_is_reconciled_by_unique_label_without_a_second_create(self):
        self.start_running_build(ambiguous=True)
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["create_calls"], 1)
        create_calls = self.matching_calls("vast_private_create.py") + self.matching_calls(
            "create", "instance"
        )
        self.assertEqual(len(create_calls), 1)
        self.assertGreaterEqual(len(self.matching_calls("show", "instances")), 2)

    def test_ambiguous_create_binds_stopped_exact_match_only_for_teardown(self):
        prepared = self.prepare()
        self.set_provider(
            create_mode="ambiguous",
            created_instance_status="exited",
            created_instance_intended_status="stopped",
        )

        cleaned = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(cleaned.returncode, 0, cleaned.stderr)
        self.assertEqual(self.output_json(cleaned)["state"], "settled")
        self.assertTrue((self.root / "launch/create-result.json").is_file())
        self.assertTrue(
            (self.root / "launch/instance-ownership.json").is_file()
        )
        self.assertTrue(
            (self.root / "launch/preworker-instance-failure.log").is_file()
        )
        self.assertFalse((self.root / "launch/instance.json").exists())
        self.assertEqual(self.provider()["worker_start_calls"], 0)
        self.assertEqual(self.provider()["remote_prepare_calls"], 0)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_stop_binds_stopped_exact_instance_after_create_result_crash(self):
        prepared = self.prepare()
        self.set_provider(crash_on_first_show_instance=True)
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue((self.root / "launch/create-result.json").is_file())
        self.assertFalse(
            (self.root / "launch/instance-ownership.json").exists()
        )
        self.assertFalse((self.root / "launch/instance.json").exists())
        self.set_instance(actual_status="exited", intended_status="stopped")

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertTrue(
            (self.root / "launch/instance-ownership.json").is_file()
        )
        self.assertTrue(
            (self.root / "launch/instance-ownership-validation.json").is_file()
        )
        self.assertFalse((self.root / "launch/instance.json").exists())
        self.assertEqual(self.provider()["worker_start_calls"], 0)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_worker_start_lost_acknowledgement_reconciles_the_same_attempt(self):
        prepared = self.prepare()
        self.set_provider(lose_worker_ack_once=True)
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue(
            (self.root / "launch/worker-invocations/001.json").is_file()
        )
        self.assertFalse(
            (self.root / "launch/worker-invocations/001.terminal.json").exists()
        )

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "running")
        starts = self.matching_calls("_remote-worker")
        self.assertEqual(len(starts), 1, starts)
        self.assertTrue(
            all("001" in call["argv"] and "002" not in call["argv"] for call in starts),
            starts,
        )
        self.assertEqual(self.provider()["worker_start_calls"], 1)
        self.assertTrue(self.matching_calls("_remote-status", "001"))
        acknowledgement = json.loads(
            (self.root / "launch/worker-started.json").read_text(encoding="utf-8")
        )
        self.assertEqual(acknowledgement["attempt_id"], "001")

    def test_every_ssh_call_is_bounded_and_noninteractive(self):
        self.start_running_build()
        ssh_calls = [call for call in self.calls() if call["tool"] == "ssh"]
        self.assertTrue(ssh_calls)
        required_options = (
            "BatchMode=yes",
            "IdentitiesOnly=yes",
            "ConnectTimeout=15",
            "ConnectionAttempts=2",
            "ServerAliveInterval=15",
            "ServerAliveCountMax=3",
            "StrictHostKeyChecking=accept-new",
        )
        for call in ssh_calls:
            argv = call["argv"]
            for option in required_options:
                self.assertTrue(
                    any(
                        argv[index : index + 2] == ["-o", option]
                        for index in range(len(argv) - 1)
                    ),
                    (option, call),
                )
            known_hosts = [
                argv[index + 1]
                for index in range(len(argv) - 1)
                if argv[index] == "-o"
                and argv[index + 1].startswith("UserKnownHostsFile=")
            ]
            self.assertEqual(len(known_hosts), 1, call)
            self.assertTrue(
                known_hosts[0].endswith("/launch/ssh/known_hosts"),
                call,
            )

    def test_attach_ssh_accepts_zero_exit_python_repr_then_proves_ssh_url(self):
        prepared = self.prepare()
        self.set_provider(attach_ssh_output_mode="python_repr")
        running = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(running.returncode, 0, running.stderr)
        self.assertEqual(self.output_json(running)["state"], "running")

        attachment = json.loads(
            (self.root / "launch/ssh-attached.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(attachment),
            {
                "schema_version",
                "instance_id",
                "public_key_sha256",
                "attached_at_utc",
            },
        )
        self.assertEqual(str(attachment["instance_id"]), "900000024")
        self.assertEqual(len(self.matching_calls("attach", "ssh")), 1)
        self.assertTrue(self.matching_calls("ssh-url", "900000024"))
        captured_repr = b"{'success': True, 'msg': 'ssh key attached'}"
        self.assertTrue(
            all(
                captured_repr not in path.read_bytes()
                for path in self.root.rglob("*")
                if path.is_file()
            )
        )

    def test_crash_after_reservation_mutation_resumes_without_duplicate_reservation(self):
        prepared = self.prepare()
        self.set_provider(crash_after_reservation_mutation=True)
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        state = self.provider()
        self.assertEqual(state["reservation_mutations"], 1)
        self.assertEqual(state["create_calls"], 0)
        self.assertFalse(
            (self.root / "launch/full-build-reservation.json").exists()
        )

        resumed = self.invoke_with_tty_secret("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "running")
        self.finish_running_build()
        self.assert_one_finalized_paid_run()

    def test_crash_after_create_outcome_resumes_without_a_second_create(self):
        prepared = self.prepare()
        self.set_provider(crash_after_create_outcome=True)
        interrupted = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue(
            (self.root / "launch/create-request-attempted.txt").is_file()
        )
        self.assertTrue((self.root / "launch/create-api-outcome.json").is_file())
        self.assertEqual(self.provider()["create_calls"], 1)

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "running")
        self.finish_running_build()
        self.assert_one_finalized_paid_run()

    def test_crash_after_retrieval_copy_resumes_before_destroy(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            crash_after_retrieval_copy=True,
        )
        interrupted = self.invoke("run")
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertFalse(
            (self.root / "launch/retrieval-verification.json").exists()
        )
        state = self.provider()
        self.assertEqual(state["destroy_calls"], 0)
        self.assertEqual(state["settlement_mutations"], 0)

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        self.assert_one_finalized_paid_run()

    def test_lost_destroy_exit_requires_durable_attempt_and_repeated_absence(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            crash_after_destroy_response=True,
        )
        interrupted = self.invoke("run")
        self.assertNotEqual(interrupted.returncode, 0)
        state = self.provider()
        self.assertEqual(state["destroy_calls"], 1)
        self.assertEqual(state["instances"], [])
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )
        attempted = json.loads(
            (self.root / "launch/destroy-request-attempted.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(str(attempted["instance_id"]), "900000024")
        self.assertFalse((self.root / "launch/destroy-response.json").exists())
        observations_before_resume = state["show_instances_calls"]

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        state = self.provider()
        self.assertGreaterEqual(
            state["show_instances_calls"] - observations_before_resume,
            self.operation_contract()["timing"]["destroy_attempts"],
        )
        self.assertEqual(state["destroy_calls"], 1)
        self.assertGreaterEqual(state["destroy_request_calls"], 2)
        self.assert_one_finalized_paid_run()

    def test_destroy_tolerates_bound_instance_lifecycle_mutation_during_teardown(self):
        contract = json.loads(self.config.read_text(encoding="utf-8"))
        contract["timing"]["destroy_attempts"] = 3
        write_json(self.config, contract)
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            teardown_mutated_inventory_once=True,
        )

        completed = self.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.output_json(completed)["state"], "settled")
        state = self.provider()
        self.assertEqual(
            state["teardown_mutated_inventory_observations"], 1, state
        )
        self.assertEqual(state["instances"], [])
        self.assertEqual(state["destroy_calls"], 1)
        self.assertGreaterEqual(state["destroy_request_calls"], 1)
        self.assertTrue(
            (self.root / "launch/destruction-confirmation.json").is_file()
        )
        self.assert_one_finalized_paid_run()

    def test_transient_destroy_absence_followed_by_bound_instance_is_not_confirmation(self):
        contract = json.loads(self.config.read_text(encoding="utf-8"))
        contract["timing"]["destroy_attempts"] = 3
        write_json(self.config, contract)
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            transient_destroy_absence_then_reappearance=True,
        )

        unresolved = self.invoke("run")
        self.assertNotEqual(unresolved.returncode, 0)
        self.assertRegex(unresolved.stderr.lower(), r"destruct|unresolved|billing")
        state = self.provider()
        self.assertEqual(
            state["transient_destroy_reappearance_observations"], 1, state
        )
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        proof = json.loads(
            (self.root / "launch/destruction-confirmation.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreaterEqual(proof["absence_observations"], 2)
        self.assert_one_finalized_paid_run(expected_destroy_calls=2)

    def test_partial_instance_ownership_binding_is_reconstructed_before_teardown(self):
        self.start_running_build()
        ownership = self.root / "launch/instance-ownership.json"
        validation = self.root / "launch/instance-ownership-validation.json"
        self.assertTrue(ownership.is_file())
        validation.unlink()
        (self.root / "launch/instance.json").unlink()
        (self.root / "launch/pre-transfer-instance-validation.json").unlink()

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertTrue(validation.is_file())
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run()

    def test_crash_after_first_invoice_snapshot_reuses_it_and_settles_once(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            crash_after_first_invoice_snapshot=True,
        )
        interrupted = self.invoke("run")
        self.assertNotEqual(interrupted.returncode, 0)
        first = next(
            self.root.glob("launch/invoice-cycles/*/first/invoice.json")
        )
        self.assertTrue(first.is_file())
        first_sha256 = sha256(first)
        state_after_interruption = self.provider()
        self.assertEqual(state_after_interruption["settlement_mutations"], 0)
        self.assertFalse(
            list(
                self.root.glob(
                    "launch/invoice-cycles/*/confirmation/observed-at.txt"
                )
            )
        )

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        self.assertEqual(sha256(first), first_sha256)
        self.assertEqual(
            self.provider()["invoice_calls"],
            state_after_interruption["invoice_calls"] + 1,
        )
        self.assert_one_finalized_paid_run()

    def test_crash_after_settlement_ledger_mutation_resumes_the_same_settlement(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            crash_after_settlement_mutation=True,
        )
        interrupted = self.invoke("run")
        self.assertNotEqual(interrupted.returncode, 0)
        state = self.provider()
        self.assertEqual(state["settlement_mutations"], 1)
        self.assertFalse(
            (self.root / "result/settlement/settlement-result.json").exists()
        )
        self.assertNotEqual(
            self.ledger.read_bytes(),
            next(
                self.root.glob(
                    "result/settlement-attempts/*/budget-ledger.json"
                )
            ).read_bytes(),
        )

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        self.assertEqual(
            len(list(self.root.glob("result/settlement-attempts/*"))),
            1,
        )
        self.assert_one_finalized_paid_run()

    def test_hidden_remote_worker_rejects_a_held_worker_lock_without_starting(self):
        remote = self.base / "remote-lock"
        work = remote / "work"
        work.mkdir(parents=True)
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)
        lock_path = work / "full-build.lock"
        with lock_path.open("a+b") as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--root",
                    str(remote),
                    "--config",
                    str(remote_config),
                    "_remote-worker",
                    "--attempt",
                    "001",
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lock is held", result.stderr)
        self.assertFalse((work / "full-build-attempts/001").exists())

    def test_status_is_strictly_read_only(self):
        self.start_running_build()
        root_before = self.tree_snapshot()
        ledger_before = self.ledger.read_bytes()
        calls_before = len(self.calls())
        result = self.invoke("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output_json(result)["state"], "running")
        self.assertEqual(self.tree_snapshot(), root_before)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)
        new_calls = self.calls()[calls_before:]
        self.assert_no_paid_call(new_calls)
        self.assertFalse(
            any("destroy instance" in " ".join(call["argv"]) for call in new_calls)
        )

    def test_status_watch_survives_paid_preworker_states_until_destruction(self):
        contract = self.operation_contract()
        contract["timing"]["status_watch_seconds"] = 1
        write_json(self.config, contract)
        prepared = self.prepare()
        self.set_provider(remote_prepare_running_polls=2)
        preparing = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(preparing.returncode, 0, preparing.stderr)
        self.assertEqual(self.output_json(preparing)["state"], "preparing")

        watcher = self.spawn_status_watch()
        snapshots = []
        try:
            snapshots.append(self.read_watch_document(watcher))
            self.assertEqual(snapshots[-1]["state"], "instance_verified")
            self.assertTrue(snapshots[-1]["billing_possible"])
            time.sleep(0.2)
            continued_after_instance = watcher.poll() is None

            self.set_provider(
                remote_prepare_running_polls=0,
                fail_worker_start_once=True,
            )
            preworker_failure = self.invoke("run")
            self.assertNotEqual(preworker_failure.returncode, 0)
            self.assertTrue(
                (self.root / "launch/remote-prepared.json").is_file()
            )
            self.assertFalse(
                (self.root / "launch/worker-started.json").exists()
            )

            if watcher.poll() is not None:
                watcher.communicate(timeout=1)
                watcher = self.spawn_status_watch()
            while True:
                snapshot = self.read_watch_document(watcher)
                snapshots.append(snapshot)
                if snapshot["state"] == "remote_prepared":
                    break
            self.assertTrue(snapshot["billing_possible"])
            time.sleep(0.2)
            continued_after_remote_prepared = watcher.poll() is None

            stopped = self.invoke("stop")
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            self.assertTrue(
                (self.root / "launch/destruction-confirmation.json").is_file()
            )
            remaining_stdout, remaining_stderr = watcher.communicate(timeout=3)
            self.assertEqual(watcher.returncode, 0, remaining_stderr)
            for line in remaining_stdout.splitlines():
                snapshots.append(json.loads(line))
        finally:
            if watcher.poll() is None:
                watcher.kill()
                watcher.communicate()

        self.assertTrue(
            continued_after_instance,
            "status --watch exited while the verified instance could still bill",
        )
        self.assertTrue(
            continued_after_remote_prepared,
            "status --watch exited while the prepared pre-worker instance could still bill",
        )
        self.assertTrue(
            any(
                snapshot.get("billing_possible") is False
                and snapshot.get("state") in ("invoice_pending", "settled")
                for snapshot in snapshots
            ),
            snapshots,
        )
        self.assertEqual(self.provider()["destroy_calls"], 1)

    def test_status_watch_exits_when_a_billing_worker_becomes_terminal(self):
        contract = self.operation_contract()
        contract["timing"]["status_watch_seconds"] = 1
        write_json(self.config, contract)
        self.start_running_build()

        watcher = self.spawn_status_watch()
        try:
            running = self.read_watch_document(watcher)
            self.assertEqual(running["state"], "running")
            self.assertTrue(running["billing_possible"])

            self.set_provider(remote_status="terminal", retrieval_mode="valid")
            remaining_stdout, remaining_stderr = watcher.communicate(timeout=3)
            self.assertEqual(watcher.returncode, 0, remaining_stderr)
        finally:
            if watcher.poll() is None:
                watcher.kill()
                watcher.communicate()

        snapshots = [
            json.loads(line)
            for line in remaining_stdout.splitlines()
            if line
        ]
        self.assertTrue(
            any(
                snapshot.get("state") == "terminal"
                and snapshot.get("billing_possible") is True
                for snapshot in snapshots
            ),
            snapshots,
        )
        self.assertEqual(len(self.provider()["instances"]), 1)
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["destroy_calls"], 1)

    def test_retrieval_corruption_prevents_destroy_and_settlement(self):
        self.start_running_build()
        ledger_before = self.ledger.read_bytes()
        copies_before = json.loads(
            self.provider_state.read_text(encoding="utf-8")
        )["copy_calls"]
        self.set_provider(remote_status="terminal", retrieval_mode="corrupt")
        rejected = self.invoke("run")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertNotIn("Traceback", rejected.stderr)
        self.assertRegex(
            rejected.stderr.lower(), r"retriev|integrity|checksum|sha-?256|manifest"
        )
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["seal_calls"], 1)
        self.assertGreater(state["copy_calls"], copies_before)
        self.assertEqual(state["destroy_calls"], 0)
        self.assertEqual(state["settle_calls"], 0)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)

    def test_terminal_cleanup_verifies_retrieval_before_destroy_and_settlement(self):
        self.start_running_build()
        ledger_before = self.ledger.read_bytes()
        self.set_provider(remote_status="terminal", retrieval_mode="valid")
        completed = self.invoke("run")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.output_json(completed)["state"], "settled")
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["destroy_calls"], 1)
        self.assertGreaterEqual(state["invoice_calls"], 2)
        self.assertEqual(state["settle_calls"], 1)
        self.assertTrue((self.root / "result").is_dir())
        self.assertFalse((self.root / "result.next").exists())
        self.assertEqual(
            (
                self.root
                / "result/audit/preparation-attempts/001/preparation.exit"
            ).read_text(encoding="utf-8"),
            "0\n",
        )
        self.assertNotEqual(self.ledger.read_bytes(), ledger_before)

        remote_shell = shlex.join(
            [
                "ssh",
                "-i",
                str(self.root / "launch/ssh/id_ed25519"),
                "-o",
                "BatchMode=yes",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "ConnectTimeout=15",
                "-o",
                "ConnectionAttempts=2",
                "-o",
                "ServerAliveInterval=15",
                "-o",
                "ServerAliveCountMax=3",
                "-o",
                "StrictHostKeyChecking=accept-new",
                "-o",
                f"UserKnownHostsFile={self.root / 'launch/ssh/known_hosts'}",
                "-p",
                "2222",
            ]
        )
        common = [
            "--archive",
            "--no-owner",
            "--no-group",
            "--partial",
            "--delete",
            "--timeout=60",
            "--rsync-path=/usr/bin/rsync",
            "--rsh",
            remote_shell,
        ]
        downloads = [
            call["argv"]
            for call in self.calls()
            if call["tool"] == "rsync"
            and len(call["argv"]) >= 2
            and call["argv"][-2].startswith("root@fake.example:")
        ]
        self.assertCountEqual(
            downloads,
            [
                [
                    *common,
                    "root@fake.example:/workspace/oracle-full-build/work/",
                    f"{self.root / 'result.next/work'}/",
                ],
                [
                    *common,
                    "root@fake.example:/workspace/oracle-full-build/preparation-attempts/",
                    f"{self.root / 'result.next/audit/preparation-attempts'}/",
                ],
            ],
        )

        commands = [f'{call["tool"]} {" ".join(call["argv"])}' for call in self.calls()]
        destroy_index = next(index for index, value in enumerate(commands) if "destroy instance" in value)
        absence_index = next(
            index
            for index, value in enumerate(commands[destroy_index + 1 :], destroy_index + 1)
            if "show instances" in value
        )
        invoice_index = next(
            index
            for index, value in enumerate(commands[absence_index + 1 :], absence_index + 1)
            if "show invoices-v1" in value
        )
        self.assertLess(destroy_index, absence_index)
        self.assertLess(absence_index, invoice_index)

    def test_stop_reuses_local_retrieval_after_later_provider_failure(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            fail_destroy=True,
        )

        interrupted = self.invoke("stop")
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertTrue(
            (self.root / "launch/retrieval-verification.json").is_file()
        )
        self.assertTrue((self.root / "result").is_dir())
        self.assertFalse(
            (
                self.root
                / "launch/result-loss-ledger-reconciliation.json"
            ).exists()
        )
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )
        self.assertEqual(len(self.provider()["instances"]), 1)
        self.assertEqual(self.provider()["destroy_calls"], 0)

        self.set_provider(fail_destroy=False)
        resumed = self.invoke("stop")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        self.assertFalse(
            (
                self.root
                / "launch/result-loss-ledger-reconciliation.json"
            ).exists()
        )
        self.assert_one_finalized_paid_run()

    def test_rerun_after_destroy_skips_ssh_destroy_create_and_reservation(self):
        self.start_running_build()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="valid",
            fail_invoice_snapshot_once=True,
        )
        interrupted = self.invoke("run")
        self.assertNotEqual(interrupted.returncode, 0)
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["destroy_calls"], 1)
        calls_before = len(self.calls())

        resumed = self.invoke("run")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.output_json(resumed)["state"], "settled")
        state = json.loads(self.provider_state.read_text(encoding="utf-8"))
        self.assertEqual(state["destroy_calls"], 1)
        self.assertEqual(state["create_calls"], 1)
        self.assertEqual(state["settle_calls"], 1)
        rerun_calls = self.calls()[calls_before:]
        rendered = [f'{call["tool"]} {" ".join(call["argv"])}' for call in rerun_calls]
        for forbidden in (
            "reserve-full-build",
            "vast_private_create.py",
            "create instance",
            "destroy instance",
            "ssh ",
        ):
            self.assertFalse(any(forbidden in command for command in rendered), rendered)

    def test_hidden_remote_status_derives_running_and_terminal_from_real_receipts(self):
        remote = self.base / "remote"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "full-build.pid").write_text(
            f"{os.getpid()}\n", encoding="utf-8"
        )
        (attempt / "controller.pid").write_text(
            f"{os.getpid()}\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        def remote_status():
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--root",
                    str(remote),
                    "--config",
                    str(remote_config),
                    "_remote-status",
                    "--attempt",
                    "001",
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        self.assertEqual(remote_status()["state"], "running")
        (attempt / "full-build.exit").write_text("0\n", encoding="utf-8")
        terminal = remote_status()
        self.assertEqual(terminal["state"], "terminal")
        self.assertEqual(terminal["exit_status"], 0)

    def test_remote_preparation_poll_recovers_one_spawned_pid_without_respawning(self):
        remote = self.base / "remote-preparation-running"
        attempt = remote / "preparation-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "preparation.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        pid_path = attempt / "preparation.pid"
        pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        lock_path = remote / "preparation-attempts/preparation.lock"
        with lock_path.open("a+b") as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            first = self.invoke_hidden(
                remote, remote_config, "_remote-prepare"
            )
            second = self.invoke_hidden(
                remote, remote_config, "_remote-prepare"
            )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout)["state"], "running")
        self.assertEqual(json.loads(second.stdout)["state"], "running")
        self.assertEqual(pid_path.read_text(encoding="utf-8"), f"{os.getpid()}\n")
        self.assertFalse((attempt / "preparation.exit").exists())

    def test_dead_remote_preparation_owner_becomes_durable_terminal_evidence(self):
        remote = self.base / "remote-preparation-dead"
        attempt = remote / "preparation-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "preparation.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "preparation.pid").write_text(
            "2147483647\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        result = self.invoke_hidden(remote, remote_config, "_remote-prepare")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertIn(document["state"], ("failed", "orphaned"))
        exit_status = int(
            (attempt / "preparation.exit").read_text(encoding="utf-8").strip()
        )
        self.assertNotEqual(exit_status, 0)
        self.assertTrue(
            (attempt / "preparation.orphaned")
            .read_text(encoding="utf-8")
            .strip()
        )

    def test_remote_status_is_starting_before_controller_pid_is_durable(self):
        remote = self.base / "remote-controller-handshake"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.pid").write_text(
            f"{os.getpid()}\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        result = self.invoke_hidden(
            remote, remote_config, "_remote-status", "--attempt", "001"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual(document["state"], "starting")
        self.assertFalse(document["controller_alive"])

    def test_unstarted_orphan_terminalizes_as_start_exit_and_allows_fresh_attempt(self):
        remote = self.base / "remote-unstarted-orphan"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.pid").write_text(
            "2147483647\n", encoding="utf-8"
        )
        preparation = remote / "preparation-attempts/001"
        preparation.mkdir(parents=True)
        (preparation / "preparation.exit").write_text("0\n", encoding="utf-8")
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        terminalized = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "001"
        )
        self.assertEqual(terminalized.returncode, 0, terminalized.stderr)
        document = json.loads(terminalized.stdout)
        self.assertFalse(document["acknowledged"])
        self.assertEqual(document["kind"], "start.exit")
        self.assertNotEqual(document["exit_status"], 0)
        self.assertTrue((attempt / "start.exit").is_file())
        self.assertFalse((attempt / "full-build.orphaned").exists())

        fresh = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "002"
        )
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        self.assertTrue(
            (remote / "work/full-build-attempts/002").is_dir()
        )

    def test_started_orphan_terminalizes_as_final_full_build_orphan(self):
        remote = self.base / "remote-started-orphan"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "full-build.pid").write_text(
            "2147483647\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        terminalized = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "001"
        )
        self.assertEqual(terminalized.returncode, 0, terminalized.stderr)
        document = json.loads(terminalized.stdout)
        self.assertFalse(document["acknowledged"])
        self.assertEqual(document["kind"], "full-build.orphaned")
        self.assertTrue((attempt / "full-build.orphaned").is_file())
        self.assertFalse((attempt / "start.exit").exists())

        refused = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "002"
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertRegex(
            refused.stderr.lower(), r"(final|cleanup|orphan|execution)"
        )
        self.assertFalse(
            (remote / "work/full-build-attempts/002").exists()
        )

    def test_completed_full_build_attempt_blocks_a_second_execution(self):
        remote = self.base / "remote-completed-attempt"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "full-build.exit").write_text("0\n", encoding="utf-8")
        preparation = remote / "preparation-attempts/001"
        preparation.mkdir(parents=True)
        (preparation / "preparation.exit").write_text("0\n", encoding="utf-8")
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        refused = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "002"
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertRegex(refused.stderr.lower(), r"(prior|final|execution|cleanup)")
        self.assertFalse(
            (remote / "work/full-build-attempts/002").exists()
        )

    def test_started_without_a_live_controller_is_orphaned(self):
        remote = self.base / "remote-started-without-controller"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        status = self.invoke_hidden(
            remote, remote_config, "_remote-status", "--attempt", "001"
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        document = json.loads(status.stdout)
        self.assertEqual(document["state"], "orphaned")
        self.assertTrue(document["started"])
        self.assertFalse(document["controller_alive"])

    def test_controller_pid_crash_window_consumes_the_execution(self):
        remote = self.base / "remote-controller-pid-crash"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.pid").write_text(
            "2147483647\n", encoding="utf-8"
        )
        (attempt / "controller.pid").write_text(
            "2147483647\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)

        terminalized = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "001"
        )
        self.assertEqual(terminalized.returncode, 0, terminalized.stderr)
        document = json.loads(terminalized.stdout)
        self.assertEqual(document["kind"], "full-build.orphaned")
        self.assertTrue((attempt / "full-build.orphaned").is_file())
        self.assertFalse((attempt / "start.exit").exists())

        refused = self.invoke_hidden(
            remote, remote_config, "_remote-worker", "--attempt", "002"
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertFalse(
            (remote / "work/full-build-attempts/002").exists()
        )

    def test_remote_stop_targets_controller_group_and_preserves_supervisor_exit(self):
        remote = self.base / "remote-controller-stop"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        marker = attempt / "controller-stopped"
        controller_code = """
import signal
import sys
import time
from pathlib import Path
marker = Path(sys.argv[1])
def stopped(_signal, _frame):
    marker.write_text("stopped\\n", encoding="utf-8")
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stopped)
print("ready", flush=True)
while True:
    time.sleep(0.1)
"""
        supervisor_code = """
import sys
import time
from pathlib import Path
marker = Path(sys.argv[1])
exit_path = Path(sys.argv[2])
deadline = time.monotonic() + 5
while not marker.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not marker.exists():
    raise SystemExit(75)
exit_path.write_text("143\\n", encoding="utf-8")
"""
        controller = subprocess.Popen(
            [sys.executable, "-c", controller_code, str(marker)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.assertEqual(controller.stdout.readline().strip(), "ready")
        controller.stdout.close()
        supervisor = subprocess.Popen(
            [
                sys.executable,
                "-c",
                supervisor_code,
                str(marker),
                str(attempt / "full-build.exit"),
            ],
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            (attempt / "full-build.started").write_text(
                "2026-07-20T00:00:00Z\n", encoding="utf-8"
            )
            (attempt / "full-build.pid").write_text(
                f"{supervisor.pid}\n", encoding="utf-8"
            )
            (attempt / "controller.pid").write_text(
                f"{controller.pid}\n", encoding="utf-8"
            )
            remote_config = remote / "operation-contract.json"
            shutil.copy2(self.config, remote_config)
            stopped = self.invoke_hidden(
                remote,
                remote_config,
                "_remote-stop",
                "--attempt",
                "001",
            )
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            self.assertTrue(json.loads(stopped.stdout)["stop_requested"])
            self.assertEqual(controller.wait(timeout=3), 0)
            self.assertEqual(supervisor.wait(timeout=3), 0)
            self.assertEqual(
                (attempt / "full-build.exit").read_text(encoding="utf-8"),
                "143\n",
            )
        finally:
            for process in (controller, supervisor):
                if process.poll() is None:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)

    def test_remote_preparation_transfers_and_verifies_once_across_polling(self):
        prepared = self.prepare()
        self.set_provider(remote_prepare_running_polls=2)
        preparing = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(preparing.returncode, 0, preparing.stderr)
        self.assertEqual(self.output_json(preparing)["state"], "preparing")

        running = self.invoke("run")
        self.assertEqual(running.returncode, 0, running.stderr)
        self.assertEqual(self.output_json(running)["state"], "running")
        transport_source = f"{self.root / 'transport'}/"
        transport_copies = [
            call
            for call in self.calls()
            if call["tool"] == "rsync"
            and len(call["argv"]) >= 2
            and call["argv"][-2] == transport_source
        ]
        self.assertEqual(len(transport_copies), 1, transport_copies)
        remote_prepare_calls = self.provider()["remote_prepare_calls"]
        remote_verification_calls = self.provider()["remote_verification_calls"]
        self.assertEqual(remote_verification_calls, 1)

        for _ in range(3):
            observed = self.invoke("status")
            self.assertEqual(observed.returncode, 0, observed.stderr)
        self.assertEqual(
            self.provider()["remote_prepare_calls"], remote_prepare_calls
        )
        self.assertEqual(
            self.provider()["remote_verification_calls"],
            remote_verification_calls,
        )
        self.assertEqual(
            len(
                [
                    call
                    for call in self.calls()
                    if call["tool"] == "rsync"
                    and len(call["argv"]) >= 2
                    and call["argv"][-2] == transport_source
                ]
            ),
            1,
        )

    def test_initial_upload_uses_direct_rsync_instead_of_vast_copy(self):
        prepared = self.prepare()
        started = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(started.returncode, 0, started.stderr)

        calls = self.calls()
        self.assertFalse(
            any(
                call["tool"] == "vastai" and call["argv"][:1] == ["copy"]
                for call in calls
            ),
            calls,
        )
        self.assertTrue(
            any(call["tool"] == "rsync" for call in calls),
            calls,
        )
        rsync_calls = [
            call for call in calls
            if call["tool"] == "rsync" and call["argv"] != ["--version"]
        ]
        self.assertEqual(len(rsync_calls), 2, rsync_calls)
        expected_sources = {
            f"{self.root / 'transport'}/",
            f"{self.root / 'launch/remote'}/",
        }
        expected_destinations = {
            "root@fake.example:/workspace/oracle-full-build/transport/",
            "root@fake.example:/workspace/oracle-full-build/launch/",
        }
        self.assertEqual(
            {call["argv"][-2] for call in rsync_calls}, expected_sources
        )
        self.assertEqual(
            {call["argv"][-1] for call in rsync_calls}, expected_destinations
        )
        for call in rsync_calls:
            arguments = call["argv"]
            for option in (
                "--archive",
                "--no-owner",
                "--no-group",
                "--partial",
                "--delete",
                "--timeout=60",
                "--rsync-path=/usr/bin/rsync",
            ):
                self.assertIn(option, arguments)
            remote_shell = arguments[arguments.index("--rsh") + 1]
            for option in (
                "BatchMode=yes",
                "IdentitiesOnly=yes",
                "ConnectTimeout=15",
                "ConnectionAttempts=2",
                "ServerAliveInterval=15",
                "ServerAliveCountMax=3",
                "StrictHostKeyChecking=accept-new",
                "UserKnownHostsFile=",
                "-p 2222",
            ):
                self.assertIn(option, remote_shell)
        mkdir_commands = [
            call for call in calls
            if call["tool"] == "ssh" and "mkdir" in call["argv"]
        ]
        self.assertEqual(len(mkdir_commands), 2, mkdir_commands)
        self.assertEqual(
            {call["argv"][-1] for call in mkdir_commands},
            {
                "/workspace/oracle-full-build/transport",
                "/workspace/oracle-full-build/launch",
            },
        )

    def test_failed_rsync_never_advances_to_remote_verification_or_worker(self):
        prepared = self.prepare()
        self.set_provider(fail_transport_rsync=True)
        waiting = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(waiting.returncode, 0, waiting.stderr)
        self.assertEqual(self.output_json(waiting)["state"], "preparing")
        state = self.provider()
        self.assertEqual(state["transport_copy_calls"], 2)
        self.assertEqual(state["remote_verification_calls"], 0)
        self.assertEqual(state["worker_start_calls"], 0)

    def test_missing_remote_rsync_never_starts_transfer_or_worker(self):
        prepared = self.prepare()
        self.set_provider(remote_rsync_available=False)
        rejected = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(rejected.returncode, 0, rejected.stderr)
        self.assertEqual(self.output_json(rejected)["state"], "settled")
        state = self.provider()
        self.assertEqual(state["remote_rsync_checks"], 1)
        self.assertEqual(state["copy_calls"], 0)
        self.assertEqual(state["remote_verification_calls"], 0)
        self.assertEqual(state["worker_start_calls"], 0)
        self.assertEqual(state["destroy_calls"], 1)
        self.assertEqual(state["instances"], [])
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_unstarted_unresolved_worker_refreshes_cost_before_any_retry(self):
        prepared = self.prepare()
        self.set_provider(lose_worker_without_start_once=True)
        unresolved = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(unresolved.returncode, 0)
        self.assertEqual(self.provider()["worker_start_calls"], 1)
        self.assertIn(0, self.recorded_cost_durations())

        self.set_instance(duration=12000)
        refused = self.invoke("run")
        self.assertNotEqual(refused.returncode, 0)
        self.assertRegex(refused.stderr.lower(), r"setup.*cost|cost.*gate")
        self.assertEqual(self.provider()["worker_start_calls"], 1)
        self.assertFalse((self.root / "launch/worker-started.json").exists())
        self.assertFalse(
            (self.root / "launch/worker-invocations/002.json").exists()
        )
        durations = self.recorded_cost_durations()
        self.assertIn(0, durations)
        self.assertIn(12000, durations)

    def test_stop_durably_aborts_an_absent_recorded_worker_then_settles(self):
        prepared = self.prepare()
        self.set_provider(lose_worker_without_start_once=True)
        unresolved = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(unresolved.returncode, 0)
        self.assertTrue(
            (self.root / "launch/worker-invocations/001.json").is_file()
        )

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["remote_abort_calls"], 1)
        self.assertTrue(
            (
                self.root
                / "result/work/full-build-attempts/001/start.exit"
            ).is_file()
        )
        self.assertFalse(
            (
                self.root
                / "result/work/full-build-attempts/001/full-build.exit"
            ).exists()
        )
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_status_passes_through_remote_progress_disk_and_gpu(self):
        self.start_running_build()
        telemetry = {
            "progress": {
                "completed_rows": 25,
                "total_rows": 100,
                "completed_shards": 0,
                "total_shards": 1,
            },
            "disk": {
                "total_bytes": 200_000_000_000,
                "used_bytes": 50_000_000_000,
                "available_bytes": 150_000_000_000,
            },
            "gpu": {
                "utilization_percent": 37,
                "memory_used_bytes": 2_147_483_648,
                "memory_total_bytes": 103_079_215_104,
            },
        }
        self.set_provider(remote_telemetry=telemetry)
        status = self.invoke("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        document = self.output_json(status)
        for field, expected in telemetry.items():
            self.assertEqual(document["remote"][field], expected)

    def test_hidden_remote_status_collects_progress_disk_and_gpu(self):
        remote = self.base / "remote-telemetry"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "controller.pid").write_text(
            f"{os.getpid()}\n", encoding="utf-8"
        )
        remote_config = remote / "operation-contract.json"
        shutil.copy2(self.config, remote_config)
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--root",
                str(remote),
                "--config",
                str(remote_config),
                "_remote-status",
                "--attempt",
                "001",
            ],
            text=True,
            capture_output=True,
            check=False,
            env=self.environment,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual(document["state"], "running")
        self.assertIn("progress", document)
        self.assertIn("disk", document)
        self.assertIn("gpu", document)
        self.assertEqual(document["progress"]["completed_rows"], 0)
        self.assertEqual(document["progress"]["total_rows"], 100)
        self.assertGreater(document["disk"]["total_bytes"], 0)
        self.assertGreaterEqual(document["disk"]["available_bytes"], 0)
        self.assertEqual(document["gpu"]["utilization_percent"], 37)
        self.assertEqual(document["gpu"]["memory_used_bytes"], 2_147_483_648)
        self.assertEqual(document["gpu"]["memory_total_bytes"], 103_079_215_104)

    def test_remote_progress_separates_reused_checkpoint_from_fresh_shards(self):
        remote = self.base / "remote-shard-progress"
        attempt = remote / "work/full-build-attempts/001"
        attempt.mkdir(parents=True)
        (attempt / "full-build.started").write_text(
            "2026-07-20T00:00:00Z\n", encoding="utf-8"
        )
        (attempt / "controller.pid").write_text(
            f"{os.getpid()}\n", encoding="utf-8"
        )
        rows_per_shard = 100
        vector_bytes = rows_per_shard * 14336
        shards = remote / "work/representation/shards"
        manifests = {}
        for ordinal in (157, 159):
            start_row = ordinal * rows_per_shard
            shard = shards / f"{ordinal:06d}"
            shard.mkdir(parents=True)
            vectors = shard / "vectors.f32le"
            vectors.write_bytes(b"\0" * vector_bytes)
            write_json(
                shard / "manifest.json",
                {
                    "ordinal": ordinal,
                    "start_row": start_row,
                    "rows": rows_per_shard,
                    "descriptor_sha256": "d" * 64,
                    "build_identity_sha256": "b" * 64,
                    "vectors": {
                        "file": f"shards/{ordinal:06d}/vectors.f32le",
                        "records": rows_per_shard,
                        "bytes": vector_bytes,
                    },
                },
            )
            manifests[ordinal] = shard / "manifest.json"
        now = time.time()
        os.utime(manifests[157], (now, now))
        old_new_shard = now - 7200
        os.utime(manifests[159], (old_new_shard, old_new_shard))
        temporary = shards / ".000160.tmp"
        temporary.mkdir()
        write_json(
            temporary / "manifest.json",
            {"ordinal": 160, "start_row": 16000, "rows": 100},
        )
        self.assertFalse(
            (remote / "work/representation/manifest.json").exists()
        )
        build_config = remote / "package/run/full-build-config.json"
        write_json(build_config, {"shard_rows": rows_per_shard})
        contract = self.operation_contract()
        contract["expected"].update(
            {
                "represented_rows": rows_per_shard,
                "total_rows": 16000,
                "completed_shards": 160,
                "final_vector_bytes": 16000 * 14336,
                "checkpoint_shard_ordinal": 157,
                "checkpoint_vector_sha256": sha256(
                    shards / "000157/vectors.f32le"
                ),
            }
        )
        remote_config = remote / "operation-contract.json"
        write_json(remote_config, contract)

        result = self.invoke_hidden(
            remote, remote_config, "_remote-status", "--attempt", "001"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        progress = json.loads(result.stdout)["progress"]
        self.assertEqual(progress["completed_rows"], 200)
        self.assertEqual(progress["completed_shards"], 2)
        self.assertEqual(progress["total_rows"], 16000)
        self.assertEqual(progress["reused_checkpoint_rows"], 100)
        self.assertEqual(progress["completed_new_rows"], 100)
        self.assertEqual(progress["completed_new_shards"], 1)
        self.assertGreaterEqual(
            progress["newest_new_shard_age_seconds"], 7100
        )
        self.assertLessEqual(
            progress["newest_new_shard_age_seconds"], 7300
        )

    def test_status_exposes_provider_cost_query_failure(self):
        self.start_running_build()
        self.set_instance(duration="not-a-duration")
        status = self.invoke("status")
        self.assertEqual(status.returncode, 0, status.stderr)
        document = self.output_json(status)
        self.assertIsInstance(document.get("cost_error"), str)
        self.assertIn("provider", document["cost_error"].lower())
        self.assertIsNone(document.get("manual_stop_recommended"))
        self.assertNotIn("cost", document)

    def test_reservation_projection_must_exactly_match_the_approved_plan(self):
        prepared = self.prepare()
        baseline = self.ledger.read_bytes()
        self.set_provider(reservation_projection_mode="mismatch")
        rejected = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(
            rejected.stderr.lower(), r"reservation.*(projection|approved|plan)"
        )
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertFalse(
            (self.root / "launch/full-build-reservation.json").exists()
        )
        self.assertTrue(
            (self.root / "launch/rejected-reservation.json").is_file()
        )
        self.assertEqual(self.ledger.read_bytes(), baseline)
        self.assertEqual(
            (self.root / "execution/work/budget-ledger.json").read_bytes(),
            baseline,
        )
        self.set_provider(reservation_projection_mode="exact")
        repeated = self.invoke("run")
        self.assertNotEqual(repeated.returncode, 0)
        self.assertRegex(
            repeated.stderr.lower(), r"(rejected|reservation|hard stop)"
        )
        self.assertEqual(self.provider()["reservation_mutations"], 1)
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertEqual(self.ledger.read_bytes(), baseline)

    def test_reservation_projection_must_not_exceed_its_ceiling(self):
        prepared = self.prepare()
        self.set_provider(reservation_projection_mode="over_ceiling")
        rejected = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(
            rejected.stderr.lower(), r"reservation.*(ceiling|projection)"
        )
        self.assertEqual(self.provider()["create_calls"], 0)
        self.assertFalse(
            (self.root / "launch/full-build-reservation.json").exists()
        )

    def test_stop_is_not_gated_by_deep_local_artifact_verification(self):
        self.start_running_build()
        (self.root / "transport/payload.bin").write_bytes(b"corrupted locally\n")

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run()

    def test_stop_bound_instance_does_not_require_approval_plan_file(self):
        self.start_running_build()
        approval = json.loads(
            (self.root / "launch/approval.json").read_text(encoding="utf-8")
        )
        plan = self.root / f"launch/plans/{approval['approval_sha256']}.json"
        plan.unlink()

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run()

    def test_stop_bound_instance_does_not_parse_corrupt_approval_plan(self):
        self.start_running_build()
        approval = json.loads(
            (self.root / "launch/approval.json").read_text(encoding="utf-8")
        )
        plan = self.root / f"launch/plans/{approval['approval_sha256']}.json"
        write_json(plan, {"corrupt": True})

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(self.output_json(stopped)["state"], "settled")
        self.assertEqual(self.provider()["destroy_calls"], 1)
        self.assert_one_finalized_paid_run()

    def test_stop_falls_back_to_provider_destroy_when_bound_instance_loses_ssh(self):
        self.start_running_build()
        reserved_ledger = self.ledger.read_bytes()
        self.set_provider(fail_all_ssh=True, allow_destroy_without_retrieval=True)

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(
            self.output_json(stopped)["state"],
            "ledger_reconciliation_required",
        )
        self.assertEqual(self.provider()["destroy_calls"], 1)
        loss_evidence = [
            path
            for path in self.root.joinpath("launch").rglob("*")
            if path.is_file()
            and "result" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
            and "loss" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
        ]
        self.assertTrue(loss_evidence)
        self.assertEqual(self.ledger.read_bytes(), reserved_ledger)
        self.assertEqual(self.provider()["settlement_mutations"], 0)
        self.assertFalse(
            (self.root / "result/settlement/settlement-result.json").exists()
        )

    def test_stop_destroys_after_terminal_retrieval_loss_without_settling(self):
        self.start_running_build()
        reserved_ledger = self.ledger.read_bytes()
        self.set_provider(
            remote_status="terminal",
            retrieval_mode="corrupt",
            allow_destroy_without_retrieval=True,
        )

        stopped = self.invoke("stop")
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(
            self.output_json(stopped)["state"],
            "ledger_reconciliation_required",
        )
        state = self.provider()
        self.assertEqual(state["destroy_calls"], 1)
        self.assertEqual(state["settlement_mutations"], 0)
        self.assertEqual(self.ledger.read_bytes(), reserved_ledger)
        self.assertFalse(
            (self.root / "launch/retrieval-verification.json").exists()
        )
        loss_evidence = [
            path
            for path in self.root.joinpath("launch").rglob("*")
            if path.is_file()
            and "result" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
            and "loss" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
        ]
        self.assertTrue(loss_evidence)

    def test_irretrievable_preparation_evidence_retries_before_destroy(self):
        prepared = self.prepare()
        self.set_provider(
            remote_prepare_mode="failed",
            fail_preparation_evidence_copy=True,
        )
        completed = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.output_json(completed)["state"], "settled")
        commands = self.calls()
        evidence_copies = [
            index
            for index, call in enumerate(commands)
            if call["tool"] == "rsync"
            and len(call["argv"]) >= 2
            and "/preparation-attempts/" in call["argv"][-2]
        ]
        self.assertEqual(len(evidence_copies), 2, evidence_copies)
        destroy = next(
            index
            for index, call in enumerate(commands)
            if call["tool"] == "vastai"
            and call["argv"][:2] == ["destroy", "instance"]
        )
        self.assertTrue(all(copy < destroy for copy in evidence_copies))
        irretrievable = [
            path
            for path in self.root.rglob("*")
            if path.is_file()
            and "preparation" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
            and "irretrievable" in (
                path.name.lower()
                + " "
                + path.read_text(encoding="utf-8", errors="replace").lower()
            )
        ]
        self.assertTrue(irretrievable)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_preparation_failure_evidence_is_retrieved_before_destroy(self):
        prepared = self.prepare()
        self.set_provider(remote_prepare_mode="failed")
        completed = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.output_json(completed)["state"], "settled")
        commands = self.calls()
        evidence_copy = next(
            index
            for index, call in enumerate(commands)
            if call["tool"] == "rsync"
            and len(call["argv"]) >= 2
            and "/preparation-attempts/" in call["argv"][-2]
        )
        destroy = next(
            index
            for index, call in enumerate(commands)
            if call["tool"] == "vastai"
            and call["argv"][:2] == ["destroy", "instance"]
        )
        self.assertLess(evidence_copy, destroy)
        self.assertEqual(self.provider()["preparation_evidence_copy_calls"], 1)
        logs = [
            path
            for path in self.root.rglob("preparation.log")
            if "fixture model preparation failed"
            in path.read_text(encoding="utf-8")
        ]
        self.assertTrue(logs)
        self.assert_one_finalized_paid_run("failed_full_build_settlement")

    def test_status_refuses_settled_state_when_canonical_ledger_differs(self):
        self.start_running_build()
        self.finish_running_build()
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        ledger["actual_spend_cents"] += 1
        write_json(self.ledger, ledger)

        status = self.invoke("status")
        if status.returncode == 0:
            document = self.output_json(status)
            self.assertNotEqual(document.get("state"), "settled")
            self.assertIn(
                "ledger",
                json.dumps(document, sort_keys=True).lower(),
            )
        else:
            self.assertIn("ledger", status.stderr.lower())

    def test_invoice_pending_reports_next_eligible_observation_time(self):
        contract = self.operation_contract()
        contract["timing"]["invoice_not_before_seconds"] = 3600
        write_json(self.config, contract)
        self.start_running_build()
        self.set_provider(remote_status="terminal", retrieval_mode="valid")

        pending = self.invoke("run")
        self.assertEqual(pending.returncode, 0, pending.stderr)
        document = self.output_json(pending)
        self.assertEqual(document["state"], "invoice_pending")
        recorded = (
            self.root / "launch/invoice-not-before-utc.txt"
        ).read_text(encoding="utf-8").strip()
        self.assertIn("next_eligible_observation_utc", document)
        self.assertEqual(document["next_eligible_observation_utc"], recorded)

    def test_zero_exit_incomplete_transport_is_reverified_and_retried(self):
        prepared = self.prepare()
        self.set_provider(simulate_incomplete_transport_once=True)
        running = self.invoke_with_tty_secret(
            "run", "--approve", prepared["approval_sha256"]
        )
        self.assertEqual(running.returncode, 0, running.stderr)
        self.assertEqual(self.output_json(running)["state"], "running")
        state = self.provider()
        self.assertEqual(state["transport_copy_calls"], 2)
        self.assertEqual(state["remote_verification_calls"], 2)
        self.assertFalse(state["transfer_receipt_on_failed_verification"])
        self.assertEqual(state["prepare_calls_on_failed_verification"], 0)
        self.assertEqual(state["remote_prepare_calls"], 1)
        self.assertEqual(state["destroy_calls"], 0)
        self.assertEqual(len(state["instances"]), 1)
        receipt = json.loads(
            (self.root / "launch/remote-transfer-verified.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn('"verified": true', json.dumps(receipt, sort_keys=True))

    def test_destroy_refuses_id_match_without_bound_label_ownership(self):
        self.start_running_build()
        self.set_instance(label="different-operation")
        self.set_provider(remote_status="terminal", retrieval_mode="valid")

        rejected = self.invoke("run")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertRegex(
            rejected.stderr.lower(), r"(ownership|identity|label|bound)"
        )
        state = self.provider()
        self.assertEqual(state["destroy_calls"], 0)
        self.assertEqual(len(state["instances"]), 1)
        self.assertFalse(
            (self.root / "launch/destruction-confirmation.json").exists()
        )

    def test_registry_secret_never_appears_in_argv_output_or_artifacts(self):
        self.start_running_build(fail_once=True)
        status = self.invoke("status")
        searchable = [self.config, self.ledger, self.log, self.provider_state]
        searchable.extend(path for path in self.root.rglob("*") if path.is_file())
        for path in searchable:
            self.assertNotIn(SECRET.encode(), path.read_bytes(), str(path))
        self.assertNotIn(SECRET, status.stdout)
        self.assertNotIn(SECRET, status.stderr)


if __name__ == "__main__":
    unittest.main()
