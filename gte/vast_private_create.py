#!/usr/bin/env python3
"""Launch one private Vast image without placing its registry secret in argv."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path


def vast_create_arguments(
    offer_id: str, image: str, label: str, docker_pat: str, *,
    disk_gb: int = 200, entrypoint: str | None = None, environment: str | None = None,
) -> list[str]:
    if not offer_id.isdecimal() or int(offer_id) <= 0:
        raise ValueError("offer ID must be a positive integer")
    if "@sha256:" not in image or not label.strip():
        raise ValueError("image and label must be immutable and nonempty")
    if not docker_pat or any(character.isspace() for character in docker_pat):
        raise ValueError("Docker credential must be one nonempty token")
    if type(disk_gb) is not int or disk_gb <= 0:
        raise ValueError("disk size must be a positive integer")
    arguments = [
        "vastai",
        "create",
        "instance",
        offer_id,
        "--image",
        image,
        "--login",
        f"-u kernelkind -p {docker_pat} docker.io",
        "--disk",
        str(disk_gb),
        "--label",
        label,
        "--cancel-unavail",
        "--raw",
        "--retry",
        "1",
    ]
    if entrypoint is None:
        arguments[arguments.index("--cancel-unavail"):arguments.index("--cancel-unavail")] = ["--ssh", "--direct"]
    else:
        arguments += ["--entrypoint", entrypoint, "--env", environment or "", "--args"]
    return arguments


def write_attempt_marker(path: Path) -> None:
    """Durably mark the boundary immediately before invoking Vast create."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, b"attempted\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def classify_create_capture(stdout: str, stderr: str, exit_code: int) -> dict[str, object]:
    """Classify the one Vast create call without persisting provider messages."""

    def json_object(value: str) -> dict[str, object] | None:
        try:
            document = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
        return document if isinstance(document, dict) else None

    response = json_object(stdout.strip())
    if response is not None and response.get("success") is True:
        instance_id = response.get("new_contract")
        if (
            isinstance(instance_id, bool)
            or not isinstance(instance_id, (int, str))
            or not str(instance_id).isdecimal()
            or int(instance_id) <= 0
        ):
            return {
                "schema_version": 1,
                "outcome": "ambiguous",
                "success": False,
                "exit_code": exit_code,
            }
        return {
            "schema_version": 1,
            "outcome": "success",
            "success": True,
            "new_contract": instance_id,
        }

    if response is not None and response.get("success") is False:
        return {
            "schema_version": 1,
            "outcome": "definitive_rejection",
            "success": False,
        }

    provider_error = next(
        (
            document
            for line in reversed(stderr.splitlines())
            if (document := json_object(line.strip())) is not None
            and document.get("error") is True
        ),
        None,
    )
    status_code = None if provider_error is None else provider_error.get("status_code")
    if (
        not isinstance(status_code, bool)
        and isinstance(status_code, int)
        and 400 <= status_code < 500
    ):
        return {
            "schema_version": 1,
            "outcome": "definitive_rejection",
            "success": False,
            "status_code": status_code,
        }
    return {
        "schema_version": 1,
        "outcome": "ambiguous",
        "success": False,
        "exit_code": exit_code,
    }


def write_create_outcome(path: Path, document: dict[str, object]) -> None:
    """Publish the sanitized result of the one create call exactly once."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.next")
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(document, output, sort_keys=True, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("offer_id")
    parser.add_argument("image")
    parser.add_argument("label")
    parser.add_argument("attempt_marker", type=Path)
    parser.add_argument("outcome", type=Path)
    parser.add_argument("--disk-gb", type=int, default=200)
    parser.add_argument("--entrypoint")
    parser.add_argument("--environment")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docker_pat = sys.stdin.read().strip()
    arguments = vast_create_arguments(args.offer_id, args.image, args.label, docker_pat,
        disk_gb=args.disk_gb, entrypoint=args.entrypoint, environment=args.environment)
    del docker_pat
    from vastai.cli.main import main as vast_main

    write_attempt_marker(args.attempt_marker)
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = 0
    try:
        sys.argv = arguments
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            vast_main()
    except SystemExit as error:
        exit_code = error.code if isinstance(error.code, int) else 1
    except Exception:
        exit_code = 1
    finally:
        sys.argv = ["vastai"]
        del arguments

    outcome = classify_create_capture(stdout.getvalue(), stderr.getvalue(), exit_code)
    write_create_outcome(args.outcome, outcome)
    if outcome["outcome"] == "success":
        print(json.dumps(outcome, sort_keys=True))
        return 0
    return 10 if outcome["outcome"] == "definitive_rejection" else 11


if __name__ == "__main__":
    raise SystemExit(main())
