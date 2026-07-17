import hashlib
import json
import os
import platform
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FRAME_LENGTH = struct.Struct("<Q")
METADATA_LENGTH = struct.Struct("<I")


def read_exact(stream, length):
    data = bytearray()
    while len(data) < length:
        chunk = stream.read(length - len(data))
        if not chunk:
            raise AssertionError(f"worker ended after {len(data)} of {length} bytes")
        data.extend(chunk)
    return bytes(data)


def read_frame(stream):
    frame_length = FRAME_LENGTH.unpack(read_exact(stream, FRAME_LENGTH.size))[0]
    body = read_exact(stream, frame_length)
    metadata_length = METADATA_LENGTH.unpack(body[: METADATA_LENGTH.size])[0]
    metadata_end = METADATA_LENGTH.size + metadata_length
    metadata = json.loads(body[METADATA_LENGTH.size : metadata_end])
    return metadata, body[metadata_end:]


def write_frame(stream, metadata, payload=b""):
    metadata_bytes = json.dumps(
        metadata, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    body = METADATA_LENGTH.pack(len(metadata_bytes)) + metadata_bytes + payload
    stream.write(FRAME_LENGTH.pack(len(body)))
    stream.write(body)
    stream.flush()


def write_model_lock(model_dir, lock_path):
    files = []
    for path in sorted(model_dir.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(model_dir).as_posix(),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    lock_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model_id": "Alibaba-NLP/gte-Qwen2-7B-instruct",
                "model_revision": "a8d08b36ada9cacfe34c4d6f80957772a025daf2",
                "files": files,
            }
        ),
        encoding="utf-8",
    )


def fake_runtime_environment(root):
    for distribution, version in (
        ("torch", "2.12.1+cu130"),
        ("transformers", "4.41.2"),
        ("cuda-toolkit", "13.0.2"),
    ):
        normalized = distribution.replace("-", "_")
        metadata = root / f"{normalized}-{version}.dist-info" / "METADATA"
        metadata.parent.mkdir()
        metadata.write_text(
            f"Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n",
            encoding="utf-8",
        )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(root), environment.get("PYTHONPATH")))
    )
    return environment


class WorkerProtocolTest(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("GTE_TEST_MODEL_BUNDLE"),
        "set GTE_TEST_MODEL_BUNDLE to exercise the pinned tokenizer",
    )
    def test_pinned_tokenizer_appends_the_golden_eos_token_over_the_protocol(self):
        worker = Path(__file__).with_name("worker.py")
        bundle = Path(os.environ["GTE_TEST_MODEL_BUNDLE"])
        dependency_lock = Path(__file__).with_name("requirements.lock")
        process = subprocess.Popen(
            [
                sys.executable,
                str(worker),
                "--model-dir",
                str(bundle / "model"),
                "--model-lock-path",
                str(bundle / "model-lock.json"),
                "--dependency-lock-path",
                str(dependency_lock),
                "--device",
                "cpu",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        def cleanup_process():
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

        self.addCleanup(cleanup_process)
        hello, payload = read_frame(process.stdout)
        self.assertEqual(payload, b"")
        self.assertEqual(hello["python_version"], "3.12.3")
        self.assertEqual(hello["torch_version"], "2.12.1")
        self.assertEqual(hello["torch_build_version"], "2.12.1+cu130")
        self.assertEqual(hello["torch_cuda_version"], "13.0")
        self.assertEqual(hello["transformers_version"], "4.41.2")
        self.assertEqual(hello["cuda_version"], "13.0.2")

        for request_id, role, expected_length in (
            ("golden-document", "document", 2),
            ("golden-query", "query", 21),
        ):
            text = b"hello"
            write_frame(
                process.stdin,
                {
                    "type": "token_lengths",
                    "request_id": request_id,
                    "role": role,
                    "text_lengths": [len(text)],
                },
                text,
            )
            response, payload = read_frame(process.stdout)
            self.assertEqual(response["type"], "token_lengths")
            self.assertEqual(response["request_id"], request_id)
            self.assertEqual(struct.unpack("<I", payload), (expected_length,))

        write_frame(
            process.stdin,
            {"type": "shutdown", "request_id": "golden-shutdown"},
        )
        read_frame(process.stdout)
        process.stdin.close()
        self.assertEqual(process.wait(timeout=5), 0, process.stderr.read().decode())

    def test_worker_handshake_and_clean_shutdown_without_model_loading(self):
        worker = Path(__file__).with_name("worker.py")
        identity_root = tempfile.TemporaryDirectory()
        self.addCleanup(identity_root.cleanup)
        identity_root_path = Path(identity_root.name)
        model_dir = identity_root_path / "model"
        model_dir.mkdir()
        (model_dir / "fixture.txt").write_text("locked fixture\n", encoding="utf-8")
        model_lock = identity_root_path / "model-lock.json"
        dependency_lock = identity_root_path / "requirements.lock"
        write_model_lock(model_dir, model_lock)
        dependency_lock.write_bytes(b"dependency lock\n")
        runtime_root = identity_root_path / "runtime"
        runtime_root.mkdir()
        process = subprocess.Popen(
            [
                sys.executable,
                str(worker),
                "--model-dir",
                str(model_dir),
                "--model-lock-path",
                str(model_lock),
                "--dependency-lock-path",
                str(dependency_lock),
                "--device",
                "cpu",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=fake_runtime_environment(runtime_root),
        )

        def cleanup_process():
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

        self.addCleanup(cleanup_process)

        hello, payload = read_frame(process.stdout)
        self.assertEqual(payload, b"")
        self.assertEqual(hello["type"], "hello")
        self.assertEqual(hello["protocol"], "nd-gte-framed-stdio")
        self.assertEqual(hello["protocol_version"], 1)
        self.assertEqual(hello["model_id"], "Alibaba-NLP/gte-Qwen2-7B-instruct")
        self.assertEqual(
            hello["model_revision"], "a8d08b36ada9cacfe34c4d6f80957772a025daf2"
        )
        self.assertEqual(hello["dimensions"], 3584)
        self.assertEqual(hello["model_token_ceiling"], 32768)
        self.assertEqual(hello["scalar_type"], "float32")
        self.assertEqual(hello["byte_order"], "little")
        self.assertEqual(hello["execution_device"], "cpu")
        self.assertEqual(hello["python_version"], platform.python_version())
        self.assertEqual(hello["torch_version"], "2.12.1")
        self.assertEqual(hello["torch_build_version"], "2.12.1+cu130")
        self.assertEqual(hello["torch_cuda_version"], "13.0")
        self.assertEqual(hello["transformers_version"], "4.41.2")
        self.assertEqual(hello["cuda_version"], "13.0.2")
        self.assertEqual(
            hello["worker_sha256"], hashlib.sha256(worker.read_bytes()).hexdigest()
        )
        self.assertEqual(
            hello["model_lock_sha256"],
            hashlib.sha256(model_lock.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            hello["dependency_lock_sha256"],
            hashlib.sha256(dependency_lock.read_bytes()).hexdigest(),
        )

        write_frame(
            process.stdin,
            {"type": "shutdown", "request_id": "protocol-test-shutdown"},
        )
        response, payload = read_frame(process.stdout)
        self.assertEqual(payload, b"")
        self.assertEqual(
            response,
            {
                "type": "ok",
                "request_id": "protocol-test-shutdown",
                "operation": "shutdown",
            },
        )
        process.stdin.close()
        self.assertEqual(process.wait(timeout=5), 0, process.stderr.read().decode())

    def test_worker_rejects_a_model_directory_that_no_longer_matches_its_lock(self):
        worker = Path(__file__).with_name("worker.py")
        identity_root = tempfile.TemporaryDirectory()
        self.addCleanup(identity_root.cleanup)
        identity_root_path = Path(identity_root.name)
        model_dir = identity_root_path / "model"
        model_dir.mkdir()
        model_file = model_dir / "fixture.txt"
        model_file.write_text("locked fixture\n", encoding="utf-8")
        model_lock = identity_root_path / "model-lock.json"
        dependency_lock = identity_root_path / "requirements.lock"
        write_model_lock(model_dir, model_lock)
        model_file.write_text("changed after locking\n", encoding="utf-8")
        dependency_lock.write_bytes(b"dependency lock\n")
        process = subprocess.run(
            [
                sys.executable,
                str(worker),
                "--model-dir",
                str(model_dir),
                "--model-lock-path",
                str(model_lock),
                "--dependency-lock-path",
                str(dependency_lock),
                "--device",
                "cpu",
            ],
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, b"")
        self.assertIn(
            b"model directory does not match its supplied lock", process.stderr
        )


if __name__ == "__main__":
    unittest.main()
