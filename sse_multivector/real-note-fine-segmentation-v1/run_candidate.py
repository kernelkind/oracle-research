#!/usr/bin/env python3
"""Save and freshly replay one frozen HDBSCAN request before packaging its review."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sse_multivector.real_note_segmentation import package_review  # noqa: E402


def sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as destination:
        json.dump(value, destination, ensure_ascii=False, sort_keys=True, allow_nan=False)
        destination.write("\n")


def run(vectors, binary, pinned_sha, output, configuration=None):
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists: {output}")
    vectors, binary, output = (path.resolve() for path in (vectors, binary, output))
    output.mkdir(parents=True, exist_ok=False)
    invocations = []
    stage = "validate binary and request"
    try:
        if len(pinned_sha) != 64 or any(c not in "0123456789abcdef" for c in pinned_sha):
            raise ValueError("a pre-frozen lowercase binary SHA-256 is required")
        if sha(binary) != pinned_sha:
            raise ValueError("candidate binary SHA-256 differs from the pre-frozen pin")
        source = vectors / "candidate-request.json"
        source_raw = source.read_bytes()
        request = json.loads(source_raw)
        if request.get("candidate") != "hdbscan" or "hdbscan_configuration" in request:
            raise ValueError("expected the unchanged HDBSCAN request from finalize_vectors")
        parameters = {
            "min_samples": 2,
            "min_cluster_size": 2,
            "selection_method": "excess_of_mass",
        }
        identity = "hdbscan-controlled-suite-config-v1"
        request_path = output / "request.json"
        if configuration is None:
            with request_path.open("xb") as destination:
                destination.write(source_raw)
        else:
            parameters = json.loads(configuration.read_bytes())
            request["hdbscan_configuration"] = parameters
            identity = "hdbscan-explicit-config-v1"
            write_json(request_path, request)
        request_sha = sha(request_path)
        files = {"request.json": request_sha}
        for name in ("response", "replay"):
            stage = f"execute {name}"
            if sha(binary) != pinned_sha:
                raise ValueError("candidate binary SHA-256 differs before invocation")
            if sha(request_path) != request_sha:
                raise ValueError("saved request SHA-256 differs before invocation")
            invocation = {
                "argv": [str(binary), str(request_path)],
                "working_directory": str(ROOT),
                "timeout_seconds": 300,
                "started_unix_ns": time.time_ns(),
                "binary_sha256_before": pinned_sha,
                "request_sha256_before": request_sha,
                "return_code": None,
            }
            invocations.append(invocation)
            try:
                with (output / f"{name}.json").open("xb") as stdout, (
                    output / f"{name}.stderr"
                ).open("xb") as stderr:
                    process = subprocess.run(
                        invocation["argv"],
                        cwd=ROOT,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout,
                        stderr=stderr,
                        timeout=300,
                        check=False,
                    )
                    invocation["return_code"] = process.returncode
            finally:
                invocation["finished_unix_ns"] = time.time_ns()
                invocation["binary_sha256_after"] = sha(binary)
                invocation["request_sha256_after"] = sha(request_path)
                if invocation["binary_sha256_after"] != pinned_sha:
                    raise ValueError("candidate binary SHA-256 differs after invocation")
                if invocation["request_sha256_after"] != request_sha:
                    raise ValueError("saved request SHA-256 differs after invocation")
            if process.returncode != 0:
                raise ValueError(f"candidate {name} exited {process.returncode}; see {name}.stderr")
            files.update({f"{name}.{suffix}": sha(output / f"{name}.{suffix}") for suffix in ("json", "stderr")})
        stage = "compare complete responses"
        response = json.loads((output / "response.json").read_bytes())
        replay = json.loads((output / "replay.json").read_bytes())
        if response != replay:
            raise ValueError("fresh replay differs from the full parsed saved response")
        if response.get("schema_version") != 1 or response.get("candidate_identity") != identity:
            raise ValueError("candidate response identity differs from the saved request")
        artifact = response["artifact"]
        if artifact["manifest"]["parameters"] != parameters or json.loads(
            artifact["canonical_configuration_json"]
        ) != parameters:
            raise ValueError("candidate parameters differ from the saved request")
        proof = {
            "schema_version": 1,
            "runner_sha256": sha(__file__),
            "candidate_binary": str(binary),
            "candidate_binary_sha256": pinned_sha,
            "source_vector_artifact": str(vectors),
            "source_request_sha256": hashlib.sha256(source_raw).hexdigest(),
            "candidate_identity": identity,
            "hdbscan_configuration": parameters,
            "configuration_file": str(configuration.resolve()) if configuration else None,
            "invocations": invocations,
            "files": files,
            "full_parsed_response_equal": True,
        }
        write_json(output / "replay-proof.json", proof)
        stage = "package verified review"
        pending = output / ".review-pending"
        package_review(vectors, output / "response.json", pending)
        pending.rename(output / "review")
        return {"output": str(output), "replay_verified": True, "review_packaged": True}
    except Exception as error:
        write_json(output / "failure.json", {
            "schema_version": 1,
            "stage": stage,
            "error": str(error),
            "candidate_binary": str(binary),
            "candidate_binary_sha256": pinned_sha,
            "invocations": invocations,
            "review_admitted": False,
        })
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vector_artifact", type=Path)
    parser.add_argument("candidate_binary", type=Path)
    parser.add_argument("candidate_binary_sha256")
    parser.add_argument("output", type=Path)
    parser.add_argument("--hdbscan-configuration", type=Path)
    args = parser.parse_args()
    try:
        report = run(
            args.vector_artifact, args.candidate_binary, args.candidate_binary_sha256,
            args.output, args.hdbscan_configuration,
        )
    except Exception as error:
        parser.exit(1, f"candidate replay failed: {error}\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
