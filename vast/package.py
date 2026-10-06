#!/usr/bin/env python3
"""Freeze a command workload for the successful Vast controller. No provider calls."""
import argparse
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import shutil
import sys

import runner

ROOT = Path(__file__).resolve().parents[1]

# These are the successful controller's timings, not a new startup deadline.
TIMING = {"provider_attempts": 120, "provider_poll_seconds": 5,
          "preparation_attempts": 120, "preparation_poll_seconds": 30,
          "destroy_attempts": 120, "destroy_poll_seconds": 5,
          "invoice_retry_attempts": 12, "invoice_retry_seconds": 5,
          "invoice_confirmation_seconds": 300, "invoice_not_before_seconds": 88200,
          "status_watch_seconds": 900}


def freeze(spec: dict, root: Path, ledger: Path) -> Path:
    if spec.get("version") != 2:
        raise runner.OperationError("use a version-2 command workload specification")
    root = root.resolve()
    ledger = ledger.resolve()
    if root.exists():
        raise runner.OperationError("choose a new operation directory; existing runs are immutable")
    limits = spec["limits"]
    micro = lambda value: int((Decimal(str(value)) * 1_000_000).to_integral_value(rounding=ROUND_CEILING))
    maximum = runner.required_positive_int(limits, "maximum_charge_cents") * 10000
    rate = micro(limits["maximum_hourly_usd"])
    if rate <= 0:
        raise runner.OperationError("maximum_hourly_usd must be positive")
    seconds = runner.required_positive_int(limits, "session_seconds")
    offer = spec["offer"]
    transfer = Decimal(0)
    for direction in ("inbound", "outbound"):
        gigabytes = runner.required_nonnegative_int(limits, direction + "_gb")
        price = runner.full_build_package.decimal_field(offer, "inet_down_cost" if direction == "inbound" else "inet_up_cost")
        transfer += gigabytes * price * 1_000_000
    transfer_micro = int(transfer.to_integral_value(rounding=ROUND_CEILING))
    estimate = Decimal(rate) * seconds / 3600 + transfer_micro
    if estimate > maximum:
        raise runner.OperationError("session and transfer allowances exceed the maximum charge")
    workload = {"command": spec["command"], "outputs": spec["outputs"],
                "python": spec.get("python", "/usr/bin/python3"), "environment": spec.get("environment", {}),
                "work_seconds": None if 'work_seconds' in limits and limits['work_seconds'] is None
                                else runner.required_positive_int(limits, "work_seconds")}
    if "progressive_copy" in spec:
        workload["progressive_copy"] = spec["progressive_copy"]
    for key in ("resumable", "status_command"):
        if key in spec:
            workload[key] = spec[key]
    if workload["work_seconds"] is not None and workload["work_seconds"] >= seconds:
        raise runner.OperationError("work_seconds must leave time for retrieval before session_seconds")
    document = {"schema_version": 1, "artifact_kind": "vast-command-operation", "label": spec["label"],
        "image": spec["image"], "canonical_ledger_path": str(ledger), "selected_offer": offer,
        "onstart": spec.get("onstart", ""), "ssh_direct": spec.get("ssh_direct", False),
        "workload": workload, "timing": TIMING.copy(),
        "session_seconds": seconds, "cleanup_seconds": limits.get("cleanup_seconds", 0),
        "limits": {"disk_gb": spec["disk_gb"], "maximum_rental_rate_micro_usd_per_hour": rate,
            "transfer_allowance_micro_usd": transfer_micro,
            "reservation_ceiling_micro_usd": maximum, "lifetime_budget_micro_usd": 1_000_000_000,
            "setup_cost_micro_usd": runner.required_positive_int(limits, "setup_cost_cents") * 10000,
            "manual_stop_cost_micro_usd": runner.required_positive_int(limits, "manual_stop_cost_cents") * 10000},
        "pins": {key: "0" * 64 for key in ("operator_sha256", "control_sha256s_sha256",
                 "transport_manifest_sha256", "execution_package_manifest_sha256")}}
    config = root / "operation-contract.json"
    if "local_volume" in spec:
        document["local_volume"] = spec["local_volume"]
    context = runner.Context(root, config, ledger, document)
    context.validate()
    runner.validate_offer(context, offer, str(offer.get("id")))
    runner.command_budget(context)
    sources = []
    for entry in spec["inputs"]:
        source = Path(entry["source"]).absolute()
        relative = runner.command_relative_path(entry["destination"])
        if not source.exists() or source.is_symlink():
            raise runner.OperationError("input is missing or is a symbolic link")
        if relative.parts[0] in ("budget-ledger.json", "package-manifest.json", "full-build-attempts"):
            raise runner.OperationError("input destination conflicts with controller files")
        if any(relative == other or relative in other.parents or other in relative.parents for _, other in sources):
            raise runner.OperationError("input destinations overlap")
        sources.append((source, relative))
    if not sources:
        raise runner.OperationError("provide at least one workload input")
    control = root / "transport/control"
    control.mkdir(parents=True, mode=0o700)
    shutil.copyfile(ROOT / "vast/runner.py", control / "vast_full_build.py")
    for name in ("calibration_package.py", "full_build_package.py", "vast_private_create.py"):
        shutil.copyfile(ROOT / "gte" / name, control / name)
    sums = "".join(f"{runner.sha256_file(path)}  {path.relative_to(root)}\n" for path in sorted(control.iterdir()))
    runner.atomic_bytes(control / "SHA256SUMS", sums.encode())
    payload = root / "transport/workload"
    payload.mkdir()
    for source, relative in sources:
        destination = payload / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, symlinks=True)
        else:
            shutil.copy2(source, destination)
    runner.full_build_package.write_manifest(payload, payload / "package-manifest.json", "vast-command-inputs")
    runner.full_build_package.write_manifest(root / "transport", root / "transport/transport-manifest.json", "vast-command-transport")
    document["pins"] = {
        "operator_sha256": runner.sha256_file(control / "vast_full_build.py"),
        "control_sha256s_sha256": runner.sha256_file(control / "SHA256SUMS"),
        "transport_manifest_sha256": runner.sha256_file(root / "transport/transport-manifest.json"),
        "execution_package_manifest_sha256": runner.sha256_file(payload / "package-manifest.json")}
    if "recover_from" in spec:
        source = Path(spec["recover_from"]).resolve()
        prior_config = source / "operation-contract.json"
        prior = runner.read_json(prior_config)
        proof = runner.read_json(source / "launch/destruction-confirmation.json")
        retrieved = runner.read_json(source / "launch/retrieval-verification.json")
        if (workload.get("resumable") is not True or "local_volume" not in document
                or prior.get("local_volume") != document["local_volume"]
                or prior.get("image") != document["image"] or prior.get("workload") != workload
                or prior["pins"]["execution_package_manifest_sha256"]
                != document["pins"]["execution_package_manifest_sha256"]):
            raise runner.OperationError("replacement requires the same volume, image and frozen workload")
        if (proof.get("absent_from_complete_inventory") is not True
                or proof.get("absence_observations", 0) < 2
                or proof.get("instance_id") != retrieved.get("instance_id")
                or not retrieved.get("instance_id")):
            raise runner.OperationError("replacement requires verified retrieval and instance destruction")
        saved = next((source / path for path in ("result.next/work", "result/work")
                      if (source / path).is_dir()), None)
        if saved is None:
            raise runner.OperationError("replacement has no retrieved work")
        records = runner.validate_file_records(saved, retrieved.get("work_files"))
        document["volume_recovery"] = {"previous_contract_sha256": runner.sha256_file(prior_config),
            "previous_instance_id": retrieved["instance_id"],
            "previous_attempt": runner.parse_attempt_id(retrieved.get("attempt_id")), "work_files": records}
    runner.atomic_json(config, document)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args()
    config = freeze(runner.read_json(args.spec), args.root, args.ledger)
    print(config)


if __name__ == "__main__":
    main()
