"""Build and test the distillation container in an unprivileged local QEMU VM.

Use a new --directory for a clean-machine check. An existing directory reuses
its stopped VM disk, Docker cache and verified test evidence. Use --full to
rerun every test; source, dependency and input changes invalidate cached stages.
No host Docker daemon, root access, credentials, or rented hardware is used.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import signal
import socket
import subprocess
import time
import urllib.request

from sse_multivector.distillation_run import sha256, shared_code_files, write_json
from sse_multivector.distillation_deploy import verify_package


IMAGE_URL = "https://cloud-images.ubuntu.com/noble/20260911/noble-server-cloudimg-amd64.img"
IMAGE_SHA256 = "612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354"
PACKAGE_FILES = (
    "distillation_run.py", "distillation_data.py", "extraction_pipeline.py", "mask_positions.py",
    "_runner_bootstrap.py",
    "test_distillation_run.py", "test_distillation_continuation.py", "test_distillation_data.py", "test_distillation_deploy.py", "distillation_deploy.py",
    "test_distillation_candidates.py", "distillation_vast.py", "test_distillation_vast.py",
    "distillation_cache.py", "test_distillation_cache.py",
    "distillation/vast-launch.json",
    "distillation/qwen-continuation-v1.vast.json",
    "distillation/Dockerfile", "distillation/requirements.in", "distillation/requirements.lock",
    "distillation/requirements-gpu.in", "distillation/requirements-gpu.lock",
)


def prepare_package(source, destination):
    destination.mkdir(parents=True)
    for name in PACKAGE_FILES:
        source_path = source / "sse_multivector" / name
        target = destination / "sse_multivector" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target)
    (destination / "vast").mkdir()
    for name in ("runner.py", "package.py"):
        shutil.copyfile(source / "vast" / name, destination / "vast" / name)
    (destination / "gte").mkdir()
    shutil.copyfile(source / "gte/full_build_package.py", destination / "gte/full_build_package.py")
    shutil.copyfile(source / "gte/calibration_package.py", destination / "gte/calibration_package.py")
    shutil.copyfile(source / "gte/vast_private_create.py", destination / "gte/vast_private_create.py")
    for name, path in shared_code_files().items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    write_json(destination / "package.json", {name: sha256(destination / "sse_multivector" / name)
                                             for name in PACKAGE_FILES} | {
        "gte/full_build_package.py": sha256(destination / "gte/full_build_package.py")} | {
        name: sha256(destination / name) for name in shared_code_files()})


def verified_image(cache):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (IMAGE_SHA256 + ".qcow2")
    if not path.exists():
        temporary = path.with_suffix(".part")
        print("Downloading Ubuntu VM image", flush=True)
        with urllib.request.urlopen(IMAGE_URL, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if sha256(temporary) != IMAGE_SHA256:
            raise ValueError("downloaded VM image hash mismatch")
        temporary.replace(path)
    if sha256(path) != IMAGE_SHA256:
        raise ValueError("cached VM image hash mismatch")
    return path.resolve()


STAGES = ("candidates", "workflow", "deployment")
ARTIFACTS = ("container.tar.gz", "image.json", "runtime.json")
MODEL_FILES = {
    "sse_multivector/" + name for name in (
        "distillation_run.py", "distillation_data.py", "extraction_pipeline.py", "mask_positions.py",
        "test_distillation_run.py", "test_distillation_continuation.py", "test_distillation_data.py", "test_distillation_candidates.py")}
DEPLOYMENT_FILES = {
    "sse_multivector/" + name for name in (
        "distillation_deploy.py", "test_distillation_deploy.py", "distillation_vast.py",
        "test_distillation_vast.py", "distillation_cache.py", "test_distillation_cache.py",
        "distillation/vast-launch.json", "distillation/qwen-continuation-v1.vast.json")
} | {"vast/runner.py", "vast/package.py", "gte/full_build_package.py",
     "gte/calibration_package.py", "gte/vast_private_create.py"}


def file_hashes(directory, excluded=()):
    result = {}
    for path in sorted(directory.rglob("*")):
        name = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise ValueError("verification evidence cannot contain symlinks")
        if path.is_file() and name not in excluded:
            result[name] = sha256(path)
    return result


def verification_keys(package, preflight_package=None):
    files = file_hashes(package, ("package.json",))
    # Everything not explicitly classified is conservative: invalidate all.
    common = {name: digest for name, digest in files.items()
              if name not in MODEL_FILES | DEPLOYMENT_FILES}
    common.update({"vm_runner": sha256(Path(__file__)), "vm_image": IMAGE_SHA256})
    inputs = file_hashes(preflight_package) if preflight_package is not None else None
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    model = {name: value for name, value in files.items() if name in MODEL_FILES}
    return {"all": digest({"files": files, "common": common, "preflight": inputs}), "stages": {
        "candidates": digest({"common": common, "model": model}),
        "workflow": digest({"common": common, "model": model}),
        "deployment": digest({"common": common, "files": files, "preflight": inputs})}}


def valid_stage(directory, key, runtime=None):
    try:
        receipt = json.loads((directory / "passed.json").read_text())
        return (receipt["key"] == key and receipt["status"] == "passed"
                and (runtime is None or receipt["runtime"] == runtime)
                and bool(receipt["files"]) and receipt["files"] == file_hashes(directory, ("passed.json",)))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def verification_plan(directory, keys, full=False, runtime=None):
    if full:
        return {}
    plan = {}
    for attempt in sorted(directory.glob("attempt-*"), reverse=True):
        for name, key in keys["stages"].items():
            path = attempt / "results" / "stages" / name
            if name not in plan and valid_stage(path, key, runtime):
                plan[name] = path
    return plan


def receipt_script(directory, key, runtime, verify=False):
    # Runs on the VM only after the stage and its cleanup both exit successfully.
    return "python3 - " + " ".join(shlex.quote(str(value)) for value in (
        directory, key, json.dumps(runtime, sort_keys=True), "verify" if verify else "seal")) + " <<'RECEIPT'\n" + r"""
import hashlib, json, os, sys
from pathlib import Path
root, key, runtime = Path(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3])
files = {}
for path in sorted(root.rglob('*')):
    if path.is_symlink():
        raise ValueError('verification evidence cannot contain symlinks')
    if path.is_file() and path.relative_to(root).as_posix() != 'passed.json':
        with path.open('rb') as source:
            files[path.relative_to(root).as_posix()] = hashlib.file_digest(source, 'sha256').hexdigest()
receipt = {'status': 'passed', 'key': key, 'runtime': runtime, 'files': files}
if sys.argv[4] == 'verify':
    if not files or json.loads((root / 'passed.json').read_text()) != receipt:
        raise ValueError('uploaded verification evidence mismatch')
    sys.exit(0)
with (root / 'passed.json.tmp').open('w') as output:
    json.dump(receipt, output, sort_keys=True)
    output.flush()
    os.fsync(output.fileno())
(root / 'passed.json.tmp').replace(root / 'passed.json')
RECEIPT
"""


def complete_attempt(directory, keys, full=False):
    if full:
        return None
    for attempt in sorted(directory.glob("attempt-*"), reverse=True):
        try:
            verification = json.loads((attempt / "verification.json").read_text())
            complete = json.loads((attempt / "complete.json").read_text())
            results = attempt / "results"
            if (verification["keys"] == keys and complete["status"] == "passed" and complete["vm_stopped"]
                    and complete["artifacts"] == {name: sha256(results / name) for name in ARTIFACTS}
                    and complete["container_sha256"] == complete["artifacts"]["container.tar.gz"]
                    and all(valid_stage(results / "stages" / name, key, verification["runtime"])
                            for name, key in keys["stages"].items())):
                return attempt
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


BUILD_SCRIPT = r"""
cloud-init status --wait
mkdir -p /source "$result_dir"
mount -t 9p -o trans=virtio,version=9p2000.L,ro source /source
docker build --target runtime --tag notedeck-distillation:runtime -f /source/sse_multivector/distillation/Dockerfile /source
docker image inspect notedeck-distillation:runtime > "$result_dir/runtime.json"
docker build --tag notedeck-distillation:local -f /source/sse_multivector/distillation/Dockerfile /source
docker image inspect notedeck-distillation:local > "$result_dir/image.json"
"""
STAGE_SCRIPTS = {
    'candidates': r"""
docker run --rm --network none -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v sse_multivector.test_distillation_candidates
""",
    'workflow': r"""
docker run --rm --network none -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_run sse_multivector.test_distillation_continuation
""",
    'deployment': r"""
# Launch the exact image as a separate SSH target, as Vast does. It has no
# source mount or fixture volume; the operator must transfer every input.
ssh-keygen -q -t ed25519 -N '' -f "$result_dir/deployment-key"
chmod 600 "$result_dir/deployment-key"
docker network create --internal distillation-local
recovery_volume=distillation-recovery-${result_dir##*/}
cleanup_target() {
  docker logs distillation-target > "$result_dir/ssh-target.log" 2>&1 || true
  docker rm -f distillation-target >/dev/null 2>&1 || true
  docker network rm distillation-local >/dev/null 2>&1 || true
  docker volume rm "$recovery_volume" >/dev/null 2>&1 || true
  rm -f "$result_dir/deployment-key" "$result_dir/deployment-key.pub"
}
trap cleanup_target EXIT
# Model Vast managed SSH: override entrypoint, run the approved onstart,
# attach the temporary key separately. No image-specific SSH daemon.
start_target() {
docker run -d --name distillation-target --network distillation-local --network-alias target "$@" --entrypoint /bin/sh notedeck-distillation:local -c 'ssh-keygen -A && service ssh start && exec sleep infinity'
docker exec distillation-target mkdir -p /root/.ssh
docker exec -i distillation-target sh -c 'cat > /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys' < "$result_dir/deployment-key.pub"
for attempt in $(seq 1 30); do
  if docker exec distillation-target test -f /etc/ssh/ssh_host_ed25519_key; then break; fi
  test "$(docker inspect -f '{{.State.Running}}' distillation-target)" = true
  sleep 1
done
}
start_target
cat > "$result_dir/ssh-target.json" <<'TARGET'
{"host":"root@target","port":22,"identity":"/results/deployment-key"}
TARGET
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow \
  -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_PREFLIGHT_PACKAGE=/results/preflight-package -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy sse_multivector.test_distillation_vast
docker run --rm --network distillation-local \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_cache
docker logs distillation-target > "$result_dir/ssh-target.log" 2>&1
# Replace an actual container while keeping its volume. Both operator phases
# use the frozen shared runner over SSH and run with networking disabled.
docker rm -f distillation-target
docker volume create "$recovery_volume"
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_VOLUME_STAGE=seed -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_seed_volume_before_container_replacement
docker exec distillation-target /opt/distillation-venv/bin/python -c 'from pathlib import Path; p=Path("/workspace/oracle-full-build/model-cache/hub/models--fixture--cached/snapshots/"+"a"*40+"/config.json"); p.parent.mkdir(parents=True); p.write_text("cached model config")'
docker logs distillation-target > "$result_dir/volume-original.log" 2>&1
docker rm -f distillation-target
start_target -v "$recovery_volume":/workspace
docker exec distillation-target /opt/distillation-venv/bin/python -c 'from huggingface_hub import hf_hub_download; from pathlib import Path; p=hf_hub_download("fixture/cached","config.json",revision="a"*40,cache_dir="/workspace/oracle-full-build/model-cache/hub",local_files_only=True); assert Path(p).read_text()=="cached model config"'
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_VOLUME_STAGE=recover -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_recover_volume_after_container_replacement
docker logs distillation-target > "$result_dir/volume-replacement.log" 2>&1
# Download over the real Hub client to a mounted volume, retrieve evidence,
# destroy the container, then use only the retained cache for two-worker prep
# and fresh pilot training. The replacement's Hub endpoint is unreachable.
docker rm -f distillation-target
docker volume rm "$recovery_volume"
docker volume create "$recovery_volume"
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CACHE_STAGE=download -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_download_models_on_volume_and_retrieve_evidence
docker logs distillation-target > "$result_dir/cache-download-target.log" 2>&1
docker rm -f distillation-target
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CACHE_STAGE=pilot -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_cached_models_survive_replacement_and_run_two_worker_prep_and_pilot_offline
docker logs distillation-target > "$result_dir/cache-pilot-target.log" 2>&1
# The actual continuation profile must cold-download its one model, prepare,
# continue from its sealed parent and retain both new test collections on one
# mounted volume. Replace the container and repeat offline from saved work.
docker rm -f distillation-target
docker volume rm "$recovery_volume"
docker volume create "$recovery_volume"
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CONTINUATION_STAGE=seed -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_single_model_continuation_transfers_parent_and_requires_both_test_collections
docker logs distillation-target > "$result_dir/continuation-original.log" 2>&1
docker rm -f distillation-target
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CONTINUATION_STAGE=recover -v "$result_dir":/results \
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_single_model_continuation_reuses_volume_after_container_replacement_offline
docker logs distillation-target > "$result_dir/continuation-replacement.log" 2>&1
rm "$result_dir/deployment-key" "$result_dir/deployment-key.pub"
""",
}


def run_checks(ssh, scp, attempt, result_directory, keys, full):
    prefix = "set -euo pipefail\nresult_dir=" + shlex.quote(result_directory) + "\n"
    def run(script):
        with (attempt / "execution.log").open("a") as log:
            result = subprocess.run([*ssh, "bash -se"], input=script, text=True,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=2400)
        if result.returncode:
            raise RuntimeError("VM command failed; see execution.log and collected stage logs")
    run(prefix + BUILD_SCRIPT)
    inspected = subprocess.run([*ssh, "cat " + shlex.quote(result_directory + "/runtime.json")],
                               capture_output=True, text=True, check=True, timeout=30)
    runtime = json.loads(inspected.stdout)[0]["Id"]
    plan = verification_plan(attempt.parent, keys, full=full, runtime=runtime)
    verification = {"keys": keys, "runtime": runtime, "mode": "full" if full else "cached", "stages": {}}
    write_json(attempt / "verification.json", verification)
    run(prefix + 'mkdir -p "$result_dir/stages"\n')
    for name in STAGES:
        stage_directory = result_directory + "/stages/" + name
        started = time.time()
        reused = plan.get(name)
        print(f"{'Reusing' if reused else 'Running'} VM stage: {name}", flush=True)
        if reused:
            subprocess.run([*scp, "-r", str(reused), "root@127.0.0.1:" + result_directory + "/stages/"],
                           check=True, timeout=300)
            run(receipt_script(stage_directory, keys["stages"][name], runtime, verify=True))
        else:
            setup = "set -euo pipefail\nstage_dir=" + shlex.quote(stage_directory) + "\n"
            setup += 'mkdir -p "$stage_dir"\n'
            if name == "deployment":
                setup += 'cp -a ' + shlex.quote(result_directory + "/stages/workflow/workflow") + ' "$stage_dir/workflow"\n'
                setup += 'if test -d ' + shlex.quote(result_directory + "/preflight-package") + '; then cp -a ' + shlex.quote(result_directory + "/preflight-package") + ' "$stage_dir/preflight-package"; fi\n'
            body = "set -euo pipefail\nresult_dir=" + shlex.quote(stage_directory) + "\n" + STAGE_SCRIPTS[name]
            # A separate bash keeps errexit active. Putting a subshell in an
            # `if` or `||` condition would suppress failures inside the stage.
            # Its EXIT cleanup completes before evidence is sealed.
            command = setup + "trap 'cat \"$stage_dir/stage.log\"' EXIT\n"
            command += 'bash -se >"$stage_dir/stage.log" 2>&1 <<\'STAGE\'\n' + body + '\nSTAGE\n'
            command += receipt_script(stage_directory, keys["stages"][name], runtime)
            run(command)
        verification["stages"][name] = {"key": keys["stages"][name],
            "reused_from": str(reused) if reused else None, "seconds": time.time() - started}
        write_json(attempt / "verification.json", verification)
    print("Exporting verified container", flush=True)
    run(prefix + "trap 'rm -f \"$result_dir/container.tar.gz.part\"' EXIT\n"
        + 'docker save notedeck-distillation:local | gzip -1 > "$result_dir/container.tar.gz.part"\n'
        + 'mv "$result_dir/container.tar.gz.part" "$result_dir/container.tar.gz"\n')
    return verification


def execute(directory, cache, preflight_package=None, full=False):
    if preflight_package is not None and verify_package(preflight_package)["through"] != "preflight":
        raise ValueError("VM candidate validation requires a preflight package")
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempt = directory / f"attempt-{time.time_ns()}"
        attempt.mkdir()
        package = attempt / "package"
        prepare_package(Path(__file__).resolve().parents[1], package)
        if preflight_package is not None:
            snapshot = attempt / "preflight-package"
            shutil.copytree(preflight_package, snapshot)
            verify_package(snapshot)
            preflight_package = snapshot
        keys = verification_keys(package, preflight_package)
        previous = complete_attempt(directory, keys, full=full)
        if previous:
            shutil.rmtree(attempt)
            print(f"VM validation passed (verified cached results): {previous}", flush=True)
            return previous
        for command in ("qemu-system-x86_64", "qemu-img", "genisoimage", "ssh", "ssh-keygen", "scp"):
            if not shutil.which(command):
                raise RuntimeError(f"missing local prerequisite: {command}")
        with open("/dev/kvm", "rb+") as kvm:
            if fcntl.ioctl(kvm, 0xAE00, 0) != 12:
                raise RuntimeError("KVM API 12 required")
        base = verified_image(cache)
        key = directory / "ssh-key"
        if not key.exists():
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
        disk = directory / "disk.qcow2"
        if not disk.exists():
            subprocess.run(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", str(base), str(disk), "64G"], check=True)
        seed = directory / "seed"
        seed.mkdir(exist_ok=True)
        (seed / "meta-data").write_text("instance-id: distillation-local\nlocal-hostname: distillation-local\n")
        (seed / "user-data").write_text("#cloud-config\n" + json.dumps({
            "disable_root": False, "ssh_pwauth": False,
            "users": [{"name": "root", "ssh_authorized_keys": [key.with_suffix(".pub").read_text().strip()]}],
            "package_update": True, "packages": ["docker.io"],
            "runcmd": [["systemctl", "enable", "--now", "docker"]]}) + "\n")
        iso = directory / "seed.iso"
        subprocess.run(["genisoimage", "-quiet", "-output", str(iso), "-volid", "cidata", "-joliet", "-rock",
                        str(seed / "user-data"), str(seed / "meta-data")], check=True)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        options = ["-F", "/dev/null", "-i", str(key), "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
                   "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={directory / 'known_hosts'}"]
        ssh = ["ssh", *options, "-p", str(port), "root@127.0.0.1"]
        cmd = ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-smp", "4", "-m", "12288",
               "-display", "none", "-serial", "stdio", "-monitor", "none",
               "-drive", f"file={disk},if=virtio,format=qcow2",
               "-drive", f"file={iso},media=cdrom,readonly=on",
               "-netdev", f"user,id=net0,hostfwd=tcp:127.0.0.1:{port}-:22",
               "-device", "virtio-net-pci,netdev=net0",
               "-virtfs", f"local,path={package},mount_tag=source,security_model=none,readonly=on"]
        if any("," in str(p) for p in (disk, iso, package)):
            raise ValueError("VM paths cannot contain commas")
        write_json(attempt / "launch.json", {"image_url": IMAGE_URL, "image_sha256": IMAGE_SHA256,
                                            "command": cmd, "started": time.time()})
        connected = False
        result_directory = "/results/" + attempt.name
        with (attempt / "serial.log").open("w") as serial:
            process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=serial, stderr=subprocess.STDOUT)
            print(f"VM started; logs: {attempt}", flush=True)
            try:
                deadline = time.monotonic() + 240
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("VM exited during boot; see serial.log")
                    result = subprocess.run([*ssh, "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if result.returncode == 0:
                        connected = True
                        break
                    time.sleep(2)
                if not connected:
                    raise TimeoutError("VM SSH did not become ready")
                if preflight_package is not None:
                    subprocess.run([*ssh, "mkdir -p " + result_directory], check=True, timeout=30)
                    subprocess.run(["scp", *options, "-P", str(port), "-r", str(preflight_package),
                        "root@127.0.0.1:" + result_directory + "/preflight-package"], check=True, timeout=300)
                print("Building container and checking verification evidence inside VM", flush=True)
                verification = run_checks(ssh, ["scp", *options, "-P", str(port)],
                                          attempt, result_directory, keys, full)
            finally:
                collected = None
                try:
                    if connected and process.poll() is None:
                        print("Collecting results and stopping VM", flush=True)
                        collected = subprocess.run(["scp", *options, "-P", str(port), "-r",
                            "root@127.0.0.1:" + result_directory, str(attempt / "results")], timeout=300)
                finally:
                    try:
                        if connected and process.poll() is None:
                            subprocess.run([*ssh, "poweroff"], stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, timeout=10)
                    finally:
                        try:
                            process.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            process.terminate()
                            try:
                                process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
            if not collected or collected.returncode:
                raise RuntimeError("failed to collect VM results")
        results = attempt / "results"
        if not all(valid_stage(results / "stages" / name, key, verification["runtime"])
                   for name, key in keys["stages"].items()):
            raise RuntimeError("collected VM stage evidence is incomplete or corrupted")
        artifacts = {name: sha256(results / name) for name in ARTIFACTS}
        write_json(attempt / "complete.json", {"status": "passed", "vm_stopped": True,
            "container_sha256": artifacts["container.tar.gz"], "artifacts": artifacts,
            "report": "results/stages/workflow/workflow/interrupted/report.json"})
        print(f"VM validation passed: {attempt}", flush=True)
        return attempt



def main():
    def terminate(signum, frame):
        raise KeyboardInterrupt("VM launcher interrupted")
    signal.signal(signal.SIGTERM, terminate)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("target/distillation-vm-cache"))
    parser.add_argument("--preflight-package", type=Path)
    parser.add_argument("--full", action="store_true", help="rerun all checks; retain Docker build cache")
    args = parser.parse_args()
    execute(args.directory, args.cache, args.preflight_package, full=args.full)


if __name__ == "__main__":
    main()
