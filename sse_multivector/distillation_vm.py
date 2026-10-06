"""Build and test the distillation container in an unprivileged local QEMU VM.

Use a new --directory for a clean-machine check. An existing directory reuses
its stopped VM disk and Docker cache, but snapshots code and results per attempt.
No host Docker daemon, root access, credentials, or rented hardware is used.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time
import urllib.request

from sse_multivector.distillation_run import sha256, write_json
from sse_multivector.distillation_deploy import verify_package


IMAGE_URL = "https://cloud-images.ubuntu.com/noble/20260911/noble-server-cloudimg-amd64.img"
IMAGE_SHA256 = "612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354"
PACKAGE_FILES = (
    "distillation_run.py", "distillation_data.py", "extraction_pipeline.py", "mask_positions.py",
    "test_distillation_run.py", "test_distillation_data.py", "test_distillation_deploy.py", "distillation_deploy.py",
    "test_distillation_candidates.py", "distillation_vast.py", "test_distillation_vast.py",
    "distillation_cache.py", "test_distillation_cache.py",
    "distillation/vast-launch.json",
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
    write_json(destination / "package.json", {name: sha256(destination / "sse_multivector" / name)
                                             for name in PACKAGE_FILES} | {
        "gte/full_build_package.py": sha256(destination / "gte/full_build_package.py")})


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


def execute(directory, cache, preflight_package=None):
    if preflight_package is not None and verify_package(preflight_package)["through"] != "preflight":
        raise ValueError("VM candidate validation requires a preflight package")
    for command in ("qemu-system-x86_64", "qemu-img", "genisoimage", "ssh", "ssh-keygen", "scp"):
        if not shutil.which(command):
            raise RuntimeError(f"missing local prerequisite: {command}")
    with open("/dev/kvm", "rb+") as kvm:
        if fcntl.ioctl(kvm, 0xAE00, 0) != 12:
            raise RuntimeError("KVM API 12 required")
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        base = verified_image(cache)
        attempt = directory / f"attempt-{time.time_ns()}"
        attempt.mkdir()
        package = attempt / "package"
        prepare_package(Path(__file__).resolve().parents[1], package)
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
                script = "set -euo pipefail\nresult_dir=" + result_directory + "\n" + """
cloud-init status --wait
mkdir -p /source "$result_dir"
mount -t 9p -o trans=virtio,version=9p2000.L,ro source /source
docker build --tag notedeck-distillation:local -f /source/sse_multivector/distillation/Dockerfile /source
docker image inspect notedeck-distillation:local > "$result_dir/image.json"
docker run --rm --network none -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v sse_multivector.test_distillation_candidates
docker run --rm --network none -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_run
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
docker run --rm --network distillation-local \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow \\
  -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \\
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_PREFLIGHT_PACKAGE=/results/preflight-package -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_deploy sse_multivector.test_distillation_vast
docker run --rm --network distillation-local \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_cache
docker logs distillation-target > "$result_dir/ssh-target.log" 2>&1
# Replace an actual container while keeping its volume. Both operator phases
# use the frozen shared runner over SSH and run with networking disabled.
docker rm -f distillation-target
docker volume create "$recovery_volume"
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \\
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_VOLUME_STAGE=seed -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_seed_volume_before_container_replacement
docker exec distillation-target /opt/distillation-venv/bin/python -c 'from pathlib import Path; p=Path("/workspace/oracle-full-build/model-cache/hub/models--fixture--cached/snapshots/"+"a"*40+"/config.json"); p.parent.mkdir(parents=True); p.write_text("cached model config")'
docker logs distillation-target > "$result_dir/volume-original.log" 2>&1
docker rm -f distillation-target
start_target -v "$recovery_volume":/workspace
docker exec distillation-target /opt/distillation-venv/bin/python -c 'from huggingface_hub import hf_hub_download; from pathlib import Path; p=hf_hub_download("fixture/cached","config.json",revision="a"*40,cache_dir="/workspace/oracle-full-build/model-cache/hub",local_files_only=True); assert Path(p).read_text()=="cached model config"'
docker run --rm --network distillation-local \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \\
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_VOLUME_STAGE=recover -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_recover_volume_after_container_replacement
docker logs distillation-target > "$result_dir/volume-replacement.log" 2>&1
# Download over the real Hub client to a mounted volume, retrieve evidence,
# destroy the container, then use only the retained cache for two-worker prep
# and fresh pilot training. The replacement's Hub endpoint is unreachable.
docker rm -f distillation-target
docker volume rm "$recovery_volume"
docker volume create "$recovery_volume"
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \\
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CACHE_STAGE=download -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_download_models_on_volume_and_retrieve_evidence
docker logs distillation-target > "$result_dir/cache-download-target.log" 2>&1
docker rm -f distillation-target
start_target -v "$recovery_volume":/workspace
docker run --rm --network distillation-local \\
  -e DISTILLATION_TEST_OUTPUT=/results/workflow -e DISTILLATION_DEPLOY_OUTPUT=/results/deployment-tests \\
  -e DISTILLATION_SSH_TARGET=/results/ssh-target.json -e DISTILLATION_CACHE_STAGE=pilot -v "$result_dir":/results \\
  --entrypoint /opt/distillation-venv/bin/python notedeck-distillation:local -m unittest -v \\
  sse_multivector.test_distillation_deploy.SharedSSHTests.test_cached_models_survive_replacement_and_run_two_worker_prep_and_pilot_offline
docker logs distillation-target > "$result_dir/cache-pilot-target.log" 2>&1
rm "$result_dir/deployment-key" "$result_dir/deployment-key.pub"
docker save notedeck-distillation:local | gzip -1 > "$result_dir/container.tar.gz"
"""
                print("Building container and running offline tests inside VM", flush=True)
                with (attempt / "execution.log").open("w") as log:
                    result = subprocess.run([*ssh, "bash -se"], input=script, text=True,
                                            stdout=log, stderr=subprocess.STDOUT, timeout=2400)
                if result.returncode:
                    raise RuntimeError("VM test command failed; see execution.log and collected workflow logs")
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
        write_json(attempt / "complete.json", {"status": "passed", "vm_stopped": True,
            "container_sha256": sha256(attempt / "results" / "container.tar.gz"),
            "report": "results/workflow/interrupted/report.json"})
        print(f"VM validation passed: {attempt}", flush=True)


def main():
    def terminate(signum, frame):
        raise KeyboardInterrupt("VM launcher interrupted")
    signal.signal(signal.SIGTERM, terminate)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("target/distillation-vm-cache"))
    parser.add_argument("--preflight-package", type=Path)
    args = parser.parse_args()
    execute(args.directory, args.cache, args.preflight_package)


if __name__ == "__main__":
    main()
