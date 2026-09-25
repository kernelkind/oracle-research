#!/opt/distillation-venv/bin/python
"""Start the image identically on Vast (args mode) and in the local VM."""
import base64
import os
from pathlib import Path
import subprocess


def main():
    key = base64.b64decode(os.environ.pop("DISTILLATION_SSH_PUBLIC_KEY_BASE64"), validate=True).decode().strip()
    if len(key.splitlines()) != 1 or not key.startswith("ssh-ed25519 "):
        raise ValueError("one Ed25519 public key is required")
    ssh = Path("/root/.ssh")
    ssh.mkdir(mode=0o700, exist_ok=True)
    ssh.chmod(0o700)
    authorized = ssh / "authorized_keys"
    authorized.write_text(key + "\n")
    authorized.chmod(0o600)
    subprocess.run(["/usr/bin/ssh-keygen", "-lf", str(authorized)], check=True, stdout=subprocess.DEVNULL)
    Path("/run/sshd").mkdir(exist_ok=True)
    host_key = "/etc/ssh/ssh_host_ed25519_key"
    if not Path(host_key).exists():
        subprocess.run(["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", host_key], check=True)
    # OpenSSH deliberately constructs a fresh session environment. Preserve
    # only runtime settings, including NVIDIA's driver search path and device
    # selection. Never copy provider/registry credentials into SSH sessions.
    names = ("PATH", "LD_LIBRARY_PATH", "CUDA_VISIBLE_DEVICES", "HF_HUB_DISABLE_TELEMETRY",
             "TOKENIZERS_PARALLELISM", "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE")
    environment = []
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            if not value or any(c.isspace() for c in value):
                raise ValueError(f"invalid runtime environment: {name}")
            environment.append(name + "=" + value)
    os.chdir("/work")
    os.execv("/usr/sbin/sshd", ["/usr/sbin/sshd", "-D", "-e", "-h", host_key,
        "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
        "-o", "PermitRootLogin=prohibit-password", "-o", "UsePAM=no",
        "-o", "SetEnv=" + " ".join(environment)])


if __name__ == "__main__":
    main()
