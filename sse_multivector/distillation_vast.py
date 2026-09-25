"""Run one admitted pilot rental: create once, wait, retrieve, destroy.

Publication and a committed budget reservation precede this command. Nothing
is installed or edited on the rental. Vast credentials stay on the controller.
"""
import argparse
import base64
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

from gte.calibration_package import validate_instance_against_offer
from sse_multivector import distillation_deploy as deploy
from sse_multivector.distillation_run import read_json, write_json, sha256


VAST = ["uvx", "--offline", "--from", "vastai==1.4.1", "vastai"]


class Vast:
    def __init__(self, credential_file):
        self.credential_file = credential_file
        self.environment = {**os.environ, "VASTAI_NO_UPDATE_CHECK": "1"}
        if not self.environment.get("VAST_API_KEY"):
            self.environment["VAST_API_KEY"] = Path("/run/secrets/vast-api-key").read_text().strip()

    def command(self, *arguments):
        result = subprocess.run([*VAST, *arguments, "--raw", "--retry", "1"],
            capture_output=True, text=True, timeout=60, env=self.environment)
        if result.returncode:
            raise ConnectionError("Vast command failed: " + " ".join(arguments[:2]))
        value = json.loads(result.stdout)
        if isinstance(value, dict) and (value.get("error") or value.get("success") is False):
            raise ConnectionError("Vast did not acknowledge command")
        return value

    def offers(self, settings):
        return self.command("search", "offers", settings["search_query"],
                            *[x for x in settings["search_options"] if x != "--raw"])

    def instances(self):
        return self.command("show", "instances")

    def destroy(self, instance_id):
        return self.command("destroy", "instance", str(instance_id), "-y")

    def create(self, offer, image, label, key, settings, output):
        # Existing secret-safe Vast launcher records an exclusive attempt marker
        # before the API call. Ambiguous create calls are never repeated.
        public_key = base64.b64encode(key.with_suffix(".pub").read_bytes()).decode()
        command = ["uvx", "--offline", "--from", "vastai==1.4.1", "python3",
            str(deploy.CODE_ROOT / "gte/vast_private_create.py"), str(offer["id"]), image, label,
            str(output / "create-attempted"), str(output / "create-outcome.json"),
            "--disk-gb", str(settings["disk_gb"]), "--entrypoint", settings["entrypoint"],
            "--environment", "-p 22:22 -e DISTILLATION_SSH_PUBLIC_KEY_BASE64=" + public_key]
        with self.credential_file.open() as credential:
            result = subprocess.run(command, stdin=credential, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=120, env=self.environment)
        if result.returncode:
            raise ConnectionError("Vast create did not acknowledge success; recovering by unique label")


def validate_instance(row, offer, image, label, settings):
    validate_instance_against_offer(offer, {"success": True, "new_contract": row["id"]},
        row, image, int(Decimal(str(settings["offer_maximums"]["dph_total"])) * 1_000_000),
        expected_label=label, require_running=False)
    if Decimal(str(row["disk_space"])) < settings["disk_gb"]:
        raise ValueError("instance has insufficient disk")
    for counter, allowance in (("inet_down_billed", "inbound_gb"), ("inet_up_billed", "outbound_gb")):
        value = Decimal(str(row[counter]))
        if not value.is_finite() or value < 0 or value > settings[allowance]:
            raise ValueError("instance transfer allowance exceeded: " + counter)


def owned_instances(provider, label):
    return [row for row in provider.instances() if row.get("label") == label]


def destroy_owned(provider, label, output, timeout_seconds):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            rows = owned_instances(provider, label)
            if not rows:
                write_json(output / "destroyed.json", {"verified": True, "label": label, "time": time.time()})
                return
            for row in rows:
                provider.destroy(row["id"])
        except (ConnectionError, subprocess.TimeoutExpired):
            pass
        time.sleep(2)
    raise TimeoutError("Vast destruction could not be confirmed; see rental.json for ownership")


def run_rental(package, output, settings, image, offer, key, provider):
    package, output, key = Path(package).resolve(), Path(output).resolve(), Path(key).resolve()
    job = deploy.verify_package(package)
    deploy.check_offer(settings, offer)
    if job["timeout_seconds"] > settings["worker_timeout_seconds"]:
        raise ValueError("package runtime exceeds launch limit")
    if not re.fullmatch(re.escape(settings["image_repository"]) + r"@sha256:[a-f0-9]{64}", image):
        raise ValueError("published image digest required")
    output.mkdir(parents=True, exist_ok=True)
    with deploy.locked(output / ".rental.lock"):
        contract = {"package_sha256": sha256(package / "manifest.json"), "image": image,
                    "offer": offer, "settings": settings, "key": str(key)}
        path = output / "rental.json"
        if path.exists():
            state = read_json(path)
            if state["contract"] != contract:
                raise ValueError("rental inputs changed")
            if (output / "destroyed.json").exists():
                return read_json(output / "outcome.json")
        else:
            state = {"contract": contract, "label": settings["label"] + "-" + uuid.uuid4().hex[:12],
                     "started": time.time(), "deadline": time.time() + settings["rental_hours"] * 3600}
            write_json(path, state)
        label = state["label"]
        outcome = {"state": "failed", "error": "controller interrupted"}
        child = None
        command = None
        try:
            if not (output / "create-attempted").exists():
                try:
                    provider.create(offer, image, label, key, settings, output)
                except (ConnectionError, subprocess.TimeoutExpired):
                    pass
            receipt = output / "create-outcome.json"
            if receipt.exists() and read_json(receipt).get("outcome") == "definitive_rejection":
                raise RuntimeError("Vast rejected creation; no replacement rental attempted")
            # Reserve 15 minutes of the original allowance for retrieval and
            # cleanup. The persisted creation time survives controller restarts.
            work_deadline = state["deadline"] - 900
            ready_deadline = min(work_deadline, state["started"] + 3600)
            row = None
            while time.time() < ready_deadline:
                try:
                    rows = owned_instances(provider, label)
                    if len(rows) > 1:
                        raise ValueError("multiple instances have this rental label")
                    if rows:
                        row = rows[0]
                        if receipt.exists() and read_json(receipt).get("success"):
                            if str(read_json(receipt)["new_contract"]) != str(row["id"]):
                                raise ValueError("creation receipt and instance differ")
                        state["instance_id"] = row["id"]
                        write_json(path, state)
                        if (row["actual_status"] == "running" and row.get("public_ipaddr")
                                and row.get("ports", {}).get("22/tcp")):
                            validate_instance(row, offer, image, label, settings)
                            break
                        if row["actual_status"] in ("exited", "error"):
                            raise RuntimeError("container startup failed")
                except (ConnectionError, subprocess.TimeoutExpired):
                    pass
                time.sleep(5)
            else:
                raise TimeoutError("Vast container did not become ready")
            target = {"host": "root@" + row["public_ipaddr"],
                      "port": int(row["ports"]["22/tcp"][0]["HostPort"]), "identity": str(key)}
            command = [sys.executable, "-m", "sse_multivector.distillation_deploy", "run",
                "--package", str(package), "--output", str(output / "deployment"),
                "--host", target["host"], "--port", str(target["port"]), "--identity", str(key)]
            with (output / "operator.log").open("a") as log:
                child = subprocess.Popen(command, cwd=deploy.CODE_ROOT, stdout=log, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, start_new_session=True)
                last_contact = time.time()
                while child.poll() is None:
                    if time.time() >= work_deadline:
                        raise TimeoutError("rental deadline reached")
                    try:
                        rows = owned_instances(provider, label)
                        if len(rows) != 1:
                            raise RuntimeError("rental disappeared")
                        validate_instance(rows[0], offer, image, label, settings)
                        last_contact = time.time()
                    except (ConnectionError, subprocess.TimeoutExpired):
                        if time.time() - last_contact > 300:
                            raise TimeoutError("Vast monitoring unavailable for five minutes")
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                result = output / "deployment/result/deployment.json"
                if result.exists():
                    deploy.verify_manifest(result.parent, result.parent / "manifest.json")
                    outcome = read_json(result)
                else:
                    raise RuntimeError("SSH operator failed; see operator.log")
        except Exception as error:
            outcome = {"state": "failed", "error": str(error)}
        finally:
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            if command is not None and not (output / "deployment/result/manifest.json").exists():
                try:
                    with (output / "operator.log").open("a") as log:
                        deploy.run_process([*command, "--stop"], timeout=180, cwd=deploy.CODE_ROOT,
                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            write_json(output / "outcome.json", outcome)
            # This also recovers a lost create acknowledgement by unique label.
            # No duplicate create is ever sent, even after controller restart.
            if (output / "create-attempted").exists():
                destroy_owned(provider, label, output, 600)
        return outcome


def require_reservation(package, output, image, settings, reservation_id):
    """Require the committed prelaunch reservation; never edit the ledger here."""
    path = deploy.CODE_ROOT / "budget-ledger.json"
    committed = subprocess.run(["git", "show", "HEAD:budget-ledger.json"], cwd=deploy.CODE_ROOT,
                              capture_output=True, check=True).stdout
    if path.read_bytes() != committed:
        raise ValueError("budget ledger must be committed before launch")
    ledger = json.loads(committed)
    if (ledger["schema_version"] != 3 or ledger["currency"] != "USD"
            or ledger["scope"] != "Entire oracle MVP effort" or ledger["lifetime_cap_cents"] != 100000):
        raise ValueError("invalid budget ledger")
    amounts = [ledger[k] for k in ("actual_spend_cents", "outstanding_commitments_cents", "reserved_remaining_work_cents")]
    if any(type(v) is not int or v < 0 for v in amounts) or sum(amounts) > 100000:
        raise ValueError("budget ledger exceeds lifetime ceiling")
    entries = [e for e in ledger["entries"] if e.get("reservation_id") == reservation_id]
    if len(entries) != 1:
        raise ValueError("one unused distillation reservation is required")
    entry = entries[0]
    if (entry.get("kind") != "distillation_reservation" or entry.get("image") != image
            or entry.get("package_sha256") != sha256(Path(package) / "manifest.json")
            or entry.get("reserved_maximum_charge_cents") != settings["approved_maximum_usd"] * 100
            or Path(entry.get("deployment_directory", "")).resolve() != output.resolve()
            or amounts[1] < entry["reserved_maximum_charge_cents"]):
        raise ValueError("budget reservation does not cover this image and package")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--settings", type=Path, default=Path("sse_multivector/distillation/vast-launch.json"))
    parser.add_argument("--offer-id", type=int, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--pull-credential-file", type=Path, required=True)
    parser.add_argument("--reservation-id", required=True)
    args = parser.parse_args()
    settings = read_json(args.settings)
    require_reservation(args.package, args.output, args.image, settings, args.reservation_id)
    # Check both keys and the local SDK before any paid call.
    public = subprocess.run(["ssh-keygen", "-y", "-P", "", "-f", str(args.identity)],
                            check=True, capture_output=True, text=True).stdout
    supplied = args.identity.with_suffix(".pub").read_text()
    if not public.startswith("ssh-ed25519 ") or public.split()[:2] != supplied.split()[:2]:
        raise ValueError("matching Ed25519 SSH key files are required")
    credential = args.pull_credential_file.read_text().strip()
    if not credential or any(c.isspace() for c in credential):
        raise ValueError("registry pull credential must be one nonempty token")
    del credential
    subprocess.run([*VAST, "--version"], check=True, stdout=subprocess.DEVNULL)
    provider = Vast(args.pull_credential_file)
    saved = args.output / "rental.json"
    if saved.exists():
        offer = read_json(saved)["contract"]["offer"]
    else:
        offers = provider.offers(settings)
        matches = [o for o in offers if o["id"] == args.offer_id]
        if len(matches) != 1:
            raise ValueError("selected offer is no longer available within launch limits")
        offer = matches[0]
    def terminate(signum, frame):
        raise KeyboardInterrupt("rental controller interrupted")
    signal.signal(signal.SIGTERM, terminate)
    outcome = run_rental(args.package, args.output, settings, args.image, offer, args.identity, provider)
    print(json.dumps(outcome))
    if outcome["state"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
