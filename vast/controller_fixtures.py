"""Local fake provider and CLI lifecycle fixture for command-workload tests."""
import hashlib
import json
import os
import fcntl
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import termios
import time
import unittest
from pathlib import Path


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
        and args[args.index("--entrypoint") + 1] == "/usr/bin/tar"
        and args[-1] == "--version"
    ):
        state["image_tar_checks"] += 1
        write_state(state)
        if not state.get("image_tar_available", True):
            print("/usr/bin/tar: not found", file=sys.stderr)
            raise SystemExit(127)
        print("tar (GNU tar) 1.35")
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

if tool == "tar":
    if args == ["--version"]:
        state["local_tar_checks"] += 1
        write_state(state)
        if not state.get("local_tar_available", True):
            print("tar: not found", file=sys.stderr)
            raise SystemExit(127)
        print("tar (GNU tar) 1.35")
        raise SystemExit(0)
    if "-cf" in args and args[-1] == ".":
        print("fixture tar stream")
        raise SystemExit(0)
    if "-xf" in args and "-C" in args:
        marker = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        destination = Path(args[args.index("-C") + 1])
        destination.mkdir(parents=True, exist_ok=True)
        if "FAKE_TAR_WORK" in marker:
            payload = b"complete vectors\n"
            if state.get("retrieval_mode") == "corrupt":
                payload = b"corrupt vectors\n"
            (destination / "result.bin").write_bytes(payload)
            attempt = destination / "full-build-attempts/001"
            attempt.mkdir(parents=True, exist_ok=True)
            terminal_kind = state.get("remote_terminal_kind", "full-build.exit")
            terminal_status = 0 if terminal_kind == "full-build.exit" else 74
            (attempt / terminal_kind).write_text(
                f"{terminal_status}\n", encoding="utf-8"
            )
            (destination / "budget-ledger.json").write_bytes(
                (root / "launch/reserved-budget-ledger.json").read_bytes()
            )
        elif "FAKE_TAR_PREPARATION" in marker:
            attempt = destination / "001"
            attempt.mkdir(parents=True, exist_ok=True)
            failed = state.get("remote_prepare_mode") == "failed"
            log = (
                "fixture model preparation failed\n"
                if failed
                else "fixture model preparation complete\n"
            )
            if state.get("preparation_retrieval_mode") == "corrupt":
                log = "corrupt preparation evidence\n"
            (attempt / "preparation.log").write_text(log, encoding="utf-8")
            (attempt / "preparation.exit").write_text(
                "75\n" if failed else "0\n", encoding="utf-8"
            )
        else:
            print("unrecognized fixture tar stream", file=sys.stderr)
            raise SystemExit(75)
        raise SystemExit(0)
    print("unsupported fixture tar invocation", file=sys.stderr)
    raise SystemExit(64)

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
    if "/usr/bin/tar --version" in joined:
        state["remote_tar_checks"] += 1
        write_state(state)
        if not state.get("remote_tar_available", True):
            print("/usr/bin/tar: not found", file=sys.stderr)
            raise SystemExit(127)
        print("tar (GNU tar) 1.35")
    elif "/usr/bin/rsync --version" in joined:
        state["remote_rsync_checks"] += 1
        write_state(state)
        if not state.get("remote_rsync_available", True):
            print("/usr/bin/rsync: not found", file=sys.stderr)
            raise SystemExit(127)
        print("rsync  version 3.2.7  protocol version 31")
    elif "rm -rf -- /workspace/oracle-full-build/" in joined:
        remote_directory = args[-1]
        if remote_directory.endswith("/transport"):
            state["transport_clean_calls"] += 1
            if state.get("remote_transport_dirty"):
                state["transport_clean_after_interruption"] += 1
            state["remote_transport_dirty"] = False
            state["remote_transport_complete"] = False
        elif remote_directory.endswith("/launch"):
            state["launch_clean_calls"] += 1
        write_state(state)
    elif "/usr/bin/tar" in args and "-xf" in args:
        remote_directory = args[args.index("-C") + 1]
        sys.stdin.buffer.read()
        state["copy_calls"] += 1
        if remote_directory.endswith("/transport"):
            state["transport_copy_calls"] += 1
            interrupted = state.get("fail_transport_tar") or (
                state.get("fail_transport_tar_once")
                and state["transport_copy_calls"] == 1
            )
            incomplete = (
                state.get("simulate_incomplete_transport_once")
                and state["transport_copy_calls"] == 1
            )
            state["remote_transport_complete"] = not (interrupted or incomplete)
            state["remote_transport_dirty"] = interrupted or incomplete
            write_state(state)
            if interrupted:
                print("transport tar stream interrupted", file=sys.stderr)
                raise SystemExit(75)
        elif remote_directory.endswith("/launch"):
            state["launch_copy_calls"] += 1
            write_state(state)
    elif "/usr/bin/tar" in args and "-cf" in args:
        remote_directory = args[args.index("-C") + 1]
        state["copy_calls"] += 1
        if remote_directory.endswith("/preparation-attempts"):
            state["preparation_evidence_copy_calls"] += 1
            write_state(state)
            if state.get("fail_preparation_evidence_copy"):
                print("preparation evidence copy interrupted", file=sys.stderr)
                raise SystemExit(75)
            print("FAKE_TAR_PREPARATION")
        elif remote_directory.endswith("/work"):
            state["work_evidence_copy_calls"] += 1
            write_state(state)
            print("FAKE_TAR_WORK")
            crash_parent_once(state, "crash_after_retrieval_copy")
        else:
            print("unknown remote tar source", file=sys.stderr)
            raise SystemExit(75)
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
            payloads = {
                "001/preparation.log": b"fixture model preparation failed\n",
                "001/preparation.exit": b"75\n",
            }
            emit({
                "prepared": False,
                "state": "failed",
                "exit_status": 75,
                "evidence_files": [
                    {
                        "path": path,
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                    for path, payload in payloads.items()
                ],
            })
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


FAKE_COMMAND = FAKE_COMMAND.replace(
    'if tool == "ssh":\n',
    'if tool == "ssh":\n'
    '    if "-G" in args:\n'
    '        if state.get("fail_ssh_config"):\n'
    '            print("local SSH configuration rejected", file=sys.stderr)\n'
    '            raise SystemExit(255)\n'
    '        raise SystemExit(0)\n').replace(
    'if tool == "nvidia-smi":\n',
    'if tool == "nvidia-smi":\n'
    '    if "--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total" in args:\n'
    '        print("0, GPU-fixture, 37, 2048, 98304")\n'
    '        raise SystemExit(0)\n')

TIMING = {'provider_attempts': 2, 'provider_poll_seconds': 0, 'preparation_attempts': 2, 'preparation_poll_seconds': 0, 'destroy_attempts': 2, 'destroy_poll_seconds': 0, 'invoice_retry_attempts': 2, 'invoice_retry_seconds': 0, 'invoice_confirmation_seconds': 0, 'invoice_not_before_seconds': 0, 'status_watch_seconds': 0}

class ControllerFixture(unittest.TestCase):
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
                "work_evidence_copy_calls": 0,
                "local_tar_checks": 0,
                "image_tar_checks": 0,
                "remote_tar_checks": 0,
                "local_rsync_checks": 0,
                "image_rsync_checks": 0,
                "remote_rsync_checks": 0,
                "transport_clean_calls": 0,
                "transport_clean_after_interruption": 0,
                "launch_clean_calls": 0,
                "launch_copy_calls": 0,
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
            "tar",
            "rsync",
            "vastai",
            "uvx",
            "ssh",
            "ssh-keygen",
            "nvidia-smi",
        ):
            shutil.copy2(fake, self.bin / name)

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

    def calls(self):
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if line
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
