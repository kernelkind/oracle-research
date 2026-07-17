#!/usr/bin/env python3
"""Persistent framed-stdio worker for the frozen GTE Oracle encoder."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import struct
import sys
import traceback
from pathlib import Path
from typing import BinaryIO, NoReturn


MODEL_ID = "Alibaba-NLP/gte-Qwen2-7B-instruct"
MODEL_REVISION = "a8d08b36ada9cacfe34c4d6f80957772a025daf2"
DIMENSIONS = 3584
MODEL_TOKEN_CEILING = 32768
QUERY_PREFIX = (
    "Instruct: Given a note, retrieve other notes related to the interests it expresses"
    "\nQuery: "
)

PROTOCOL = "nd-gte-framed-stdio"
PROTOCOL_VERSION = 1
FRAME_LENGTH = struct.Struct("<Q")
METADATA_LENGTH = struct.Struct("<I")
UINT32 = struct.Struct("<I")
MAX_FRAME_BYTES = 256 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024
MAX_BATCH_ROWS = 4096
HASH_BUFFER_BYTES = 1024 * 1024


class WorkerError(Exception):
    """A request error that can be returned without terminating the worker."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProtocolError(Exception):
    """A malformed frame for which stream synchronization is not guaranteed."""


def read_exact(stream: BinaryIO, length: int, *, allow_clean_eof: bool = False) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = stream.read(length - len(data))
        if not chunk:
            if allow_clean_eof and not data:
                return b""
            raise ProtocolError(
                f"input ended after {len(data)} of {length} required bytes"
            )
        data.extend(chunk)
    return bytes(data)


def read_frame(stream: BinaryIO) -> tuple[dict[str, object], bytes] | None:
    frame_header = read_exact(stream, FRAME_LENGTH.size, allow_clean_eof=True)
    if not frame_header:
        return None
    frame_length = FRAME_LENGTH.unpack(frame_header)[0]
    if frame_length < METADATA_LENGTH.size:
        raise ProtocolError("frame is shorter than its metadata-length prefix")
    if frame_length > MAX_FRAME_BYTES:
        raise ProtocolError(
            f"frame length {frame_length} exceeds limit {MAX_FRAME_BYTES}"
        )

    body = read_exact(stream, frame_length)
    metadata_length = METADATA_LENGTH.unpack_from(body)[0]
    if metadata_length > MAX_METADATA_BYTES:
        raise ProtocolError(
            f"metadata length {metadata_length} exceeds limit {MAX_METADATA_BYTES}"
        )
    metadata_end = METADATA_LENGTH.size + metadata_length
    if metadata_end > len(body):
        raise ProtocolError("metadata length exceeds frame body")
    try:
        metadata = json.loads(body[METADATA_LENGTH.size : metadata_end])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"metadata is not valid UTF-8 JSON: {error}") from error
    if not isinstance(metadata, dict):
        raise ProtocolError("metadata must be a JSON object")
    return metadata, body[metadata_end:]


def write_frame(
    stream: BinaryIO, metadata: dict[str, object], payload: bytes = b""
) -> None:
    metadata_bytes = json.dumps(
        metadata, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    body_length = METADATA_LENGTH.size + len(metadata_bytes) + len(payload)
    if body_length > MAX_FRAME_BYTES:
        raise RuntimeError(f"response frame exceeds limit {MAX_FRAME_BYTES}")
    stream.write(FRAME_LENGTH.pack(body_length))
    stream.write(METADATA_LENGTH.pack(len(metadata_bytes)))
    stream.write(metadata_bytes)
    stream.write(payload)
    stream.flush()


def require_string(metadata: dict[str, object], field: str) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value:
        raise WorkerError("invalid_request", f"`{field}` must be a nonempty string")
    return value


def decode_texts(metadata: dict[str, object], payload: bytes) -> list[str]:
    raw_lengths = metadata.get("text_lengths")
    if not isinstance(raw_lengths, list):
        raise WorkerError("invalid_request", "`text_lengths` must be an array")
    if not raw_lengths:
        raise WorkerError("invalid_request", "a request must contain at least one text")
    if len(raw_lengths) > MAX_BATCH_ROWS:
        raise WorkerError(
            "batch_too_large",
            f"batch contains {len(raw_lengths)} rows; limit is {MAX_BATCH_ROWS}",
        )

    lengths: list[int] = []
    total = 0
    for index, value in enumerate(raw_lengths):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise WorkerError(
                "invalid_request",
                f"`text_lengths[{index}]` must be a nonnegative integer",
            )
        total += value
        if total > len(payload):
            raise WorkerError(
                "invalid_request", "text lengths exceed the request payload"
            )
        lengths.append(value)
    if total != len(payload):
        raise WorkerError(
            "invalid_request", "text lengths do not consume the request payload"
        )

    texts: list[str] = []
    start = 0
    for index, length in enumerate(lengths):
        end = start + length
        try:
            texts.append(payload[start:end].decode("utf-8"))
        except UnicodeDecodeError as error:
            raise WorkerError(
                "invalid_utf8", f"text {index} is not valid UTF-8: {error}"
            ) from error
        start = end
    return texts


def prepare_texts(role: str, texts: list[str]) -> list[str]:
    if role == "document":
        return texts
    if role == "query":
        return [QUERY_PREFIX + text for text in texts]
    raise WorkerError(
        "invalid_request", "`role` must be either `document` or `query`"
    )


def load_pinned_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not create pinned module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def verify_pinned_model_bundle(model_dir: Path, model_lock_path: Path) -> None:
    verifier_path = Path(__file__).resolve().with_name("model_bundle.py")
    if not verifier_path.is_file():
        fatal(f"model-bundle verifier does not exist: {verifier_path}")
    try:
        verifier = load_pinned_module(
            "oracle_mvp_pinned_gte_model_bundle", verifier_path
        )
        verifier.verify_bundle(model_dir, model_lock_path)
    except Exception as error:
        fatal(f"model directory does not match its supplied lock: {error}")


def cuda_build_version(torch_build_version: str) -> str:
    marker = "+cu"
    if marker not in torch_build_version:
        fatal(
            f"PyTorch distribution {torch_build_version} does not identify a CUDA build"
        )
    digits = torch_build_version.rsplit(marker, 1)[1]
    if len(digits) < 2 or not digits.isdecimal():
        fatal(f"PyTorch CUDA build suffix is invalid: {torch_build_version}")
    return f"{int(digits[:-1])}.{digits[-1]}"


def runtime_identity() -> dict[str, str]:
    try:
        torch_build = importlib.metadata.version("torch")
        transformers = importlib.metadata.version("transformers")
        cuda = importlib.metadata.version("cuda-toolkit")
    except importlib.metadata.PackageNotFoundError as error:
        fatal(f"required runtime distribution is unavailable: {error}")
    return {
        "python_version": platform.python_version(),
        "torch_version": torch_build.split("+", 1)[0],
        "torch_build_version": torch_build,
        "torch_cuda_version": cuda_build_version(torch_build),
        "transformers_version": transformers,
        "cuda_version": cuda,
    }


class GteEncoder:
    """Lazily loaded tokenizer and FP32 model for one persistent process."""

    def __init__(self, model_dir: Path, device: str):
        self.model_dir = model_dir
        self.device_name = device
        self._torch = None
        self._tokenizer = None
        self._model = None

    def _require_model_dir(self) -> None:
        if not self.model_dir.is_dir():
            raise WorkerError(
                "model_unavailable",
                f"model directory does not exist: {self.model_dir}",
            )

    def _load_tokenizer(self):
        if self._tokenizer is not None:
            return self._tokenizer
        self._require_model_dir()
        try:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                self.model_dir,
                local_files_only=True,
                trust_remote_code=True,
            )
        except Exception as error:
            raise WorkerError(
                "tokenizer_load_failed", f"could not load pinned tokenizer: {error}"
            ) from error
        try:
            probe = tokenizer(
                "oracle-mvp-tokenizer-contract-probe",
                add_special_tokens=True,
                padding=False,
                truncation=False,
                return_attention_mask=False,
            )["input_ids"]
        except Exception as error:
            raise WorkerError(
                "tokenizer_contract_mismatch",
                f"could not verify the pinned tokenizer contract: {error}",
            ) from error
        if (
            getattr(tokenizer, "add_eos_token", None) is not True
            or getattr(tokenizer, "model_max_length", None) != MODEL_TOKEN_CEILING
            or not isinstance(probe, list)
            or not probe
            or probe[-1] != getattr(tokenizer, "eos_token_id", None)
        ):
            raise WorkerError(
                "tokenizer_contract_mismatch",
                "pinned tokenizer does not append EOS at the approved token ceiling",
            )
        self._tokenizer = tokenizer
        return tokenizer

    def _configure_torch(self):
        if self._torch is not None:
            return self._torch
        try:
            import torch
        except Exception as error:
            raise WorkerError(
                "runtime_unavailable", f"could not import PyTorch: {error}"
            ) from error

        if self.device_name == "cuda" and not torch.cuda.is_available():
            raise WorkerError("device_unavailable", "CUDA is not available")
        try:
            torch.backends.fp32_precision = "ieee"
            torch.backends.cuda.matmul.fp32_precision = "ieee"
            torch.backends.cudnn.fp32_precision = "ieee"
            torch.use_deterministic_algorithms(True)
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
        except Exception as error:
            raise WorkerError(
                "runtime_configuration_failed",
                f"could not enforce deterministic IEEE FP32 execution: {error}",
            ) from error
        self._torch = torch
        return torch

    def _load_model(self):
        if self._model is not None:
            return self._model
        self._require_model_dir()
        torch = self._configure_torch()
        try:
            from transformers import AutoConfig

            # Transformers' remote-code dependency scanner incorrectly treats the
            # model's conditional FlashAttention import as mandatory. Import the
            # exact hash-locked local module directly instead. Eager attention
            # never executes its optional FlashAttention class.
            modeling_path = self.model_dir / "modeling_qwen.py"
            if not modeling_path.is_file():
                raise RuntimeError(f"missing pinned model code: {modeling_path}")
            module = load_pinned_module(
                "oracle_mvp_pinned_gte_modeling_qwen", modeling_path
            )
            model_class = getattr(module, "Qwen2Model", None)
            if model_class is None:
                raise RuntimeError("pinned model code does not define Qwen2Model")
            config = AutoConfig.from_pretrained(
                self.model_dir,
                local_files_only=True,
                trust_remote_code=False,
            )
            config.use_cache = False
            config.is_causal = False
            model = model_class.from_pretrained(
                self.model_dir,
                config=config,
                local_files_only=True,
                torch_dtype=torch.float32,
                attn_implementation="eager",
            )
            model.config.use_cache = False
            model.to(self.device_name)
            model.eval()
        except Exception as error:
            raise WorkerError(
                "model_load_failed", f"could not load pinned FP32 model: {error}"
            ) from error

        hidden_size = getattr(model.config, "hidden_size", None)
        if hidden_size != DIMENSIONS:
            raise WorkerError(
                "model_contract_mismatch",
                f"model hidden size is {hidden_size}, expected {DIMENSIONS}",
            )
        if getattr(model.config, "_attn_implementation", None) != "eager":
            raise WorkerError(
                "model_contract_mismatch", "model did not select eager attention"
            )
        if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
            raise WorkerError(
                "model_contract_mismatch", "model contains non-FP32 parameters"
            )
        self._model = model
        return model

    def _token_ids(self, prepared_texts: list[str]) -> list[list[int]]:
        tokenizer = self._load_tokenizer()
        try:
            encoded = tokenizer(
                prepared_texts,
                add_special_tokens=True,
                padding=False,
                truncation=False,
                return_attention_mask=False,
            )
        except Exception as error:
            raise WorkerError("tokenization_failed", str(error)) from error
        input_ids = encoded.get("input_ids")
        if not isinstance(input_ids, list) or len(input_ids) != len(prepared_texts):
            raise WorkerError(
                "tokenizer_contract_mismatch", "tokenizer returned an invalid batch"
            )
        if any(not isinstance(row, list) or not row for row in input_ids):
            raise WorkerError(
                "tokenizer_contract_mismatch",
                "tokenizer returned an empty or invalid token sequence",
            )
        return input_ids

    def token_lengths(self, role: str, texts: list[str]) -> list[int]:
        prepared = prepare_texts(role, texts)
        input_ids = self._token_ids(prepared)
        return [len(row) for row in input_ids]

    def encode(self, role: str, texts: list[str]) -> bytes:
        prepared = prepare_texts(role, texts)
        tokenizer = self._load_tokenizer()
        torch = self._configure_torch()
        model = self._load_model()
        try:
            tokenized = tokenizer(
                prepared,
                add_special_tokens=True,
                padding=True,
                truncation=False,
                return_tensors="pt",
            )
        except Exception as error:
            raise WorkerError("tokenization_failed", str(error)) from error

        input_ids = tokenized.get("input_ids")
        attention_mask = tokenized.get("attention_mask")
        if input_ids is None or attention_mask is None:
            raise WorkerError(
                "tokenizer_contract_mismatch",
                "tokenizer did not return input IDs and an attention mask",
            )
        if input_ids.ndim != 2 or input_ids.shape[0] != len(prepared):
            raise WorkerError(
                "tokenizer_contract_mismatch", "tokenizer returned an invalid tensor batch"
            )
        if input_ids.shape[1] == 0 or torch.any(attention_mask.sum(dim=1) == 0):
            raise WorkerError(
                "tokenizer_contract_mismatch", "tokenizer returned an empty sequence"
            )

        limits = [
            limit
            for limit in (
                getattr(model.config, "max_position_embeddings", None),
                getattr(tokenizer, "model_max_length", None),
            )
            if isinstance(limit, int) and limit < 2**31
        ]
        maximum_positions = min(limits) if limits else None
        if maximum_positions is not None and input_ids.shape[1] > maximum_positions:
            raise WorkerError(
                "input_too_long",
                f"batch requires {input_ids.shape[1]} tokens; model limit is {maximum_positions}",
            )

        model_inputs = {
            key: value.to(self.device_name)
            for key, value in tokenized.items()
            if hasattr(value, "to")
        }
        try:
            with torch.inference_mode():
                outputs = model(**model_inputs, use_cache=False, is_causal=False)
                hidden = outputs.last_hidden_state
                mask = model_inputs["attention_mask"]
                if bool(torch.all(mask[:, -1] == 1)):
                    pooled = hidden[:, -1]
                else:
                    last_indices = mask.sum(dim=1) - 1
                    rows = torch.arange(hidden.shape[0], device=hidden.device)
                    pooled = hidden[rows, last_indices]
                vectors = torch.nn.functional.normalize(pooled, p=2, dim=1)
        except RuntimeError as error:
            raise WorkerError("inference_failed", str(error)) from error

        expected_shape = (len(prepared), DIMENSIONS)
        if tuple(vectors.shape) != expected_shape:
            raise WorkerError(
                "model_contract_mismatch",
                f"embedding shape is {tuple(vectors.shape)}, expected {expected_shape}",
            )
        if vectors.dtype != torch.float32:
            raise WorkerError(
                "model_contract_mismatch",
                f"embedding dtype is {vectors.dtype}, expected torch.float32",
            )
        if not bool(torch.isfinite(vectors).all()):
            raise WorkerError("invalid_embedding", "embedding contains NaN or infinity")
        norms = torch.linalg.vector_norm(vectors, dim=1)
        if not bool(torch.all(torch.abs(norms - 1.0) <= 1e-5)):
            raise WorkerError("invalid_embedding", "embedding is not L2 normalized")

        array = vectors.detach().cpu().contiguous().numpy()
        if array.dtype.name != "float32":
            raise WorkerError(
                "model_contract_mismatch", f"serialized dtype is {array.dtype}"
            )
        return array.astype("<f4", copy=False).tobytes(order="C")


def handle_request(
    encoder: GteEncoder, metadata: dict[str, object], payload: bytes
) -> tuple[dict[str, object], bytes, bool]:
    request_type = metadata.get("type")
    request_id = require_string(metadata, "request_id")
    if request_type == "shutdown":
        if payload:
            raise WorkerError("invalid_request", "shutdown payload must be empty")
        return (
            {"type": "ok", "request_id": request_id, "operation": "shutdown"},
            b"",
            True,
        )
    if request_type not in {"token_lengths", "encode"}:
        raise WorkerError(
            "invalid_request", "`type` must be `token_lengths`, `encode`, or `shutdown`"
        )

    role = require_string(metadata, "role")
    texts = decode_texts(metadata, payload)
    if request_type == "token_lengths":
        lengths = encoder.token_lengths(role, texts)
        if any(length > 0xFFFFFFFF for length in lengths):
            raise WorkerError("result_too_large", "token length does not fit uint32")
        result = b"".join(UINT32.pack(length) for length in lengths)
        return (
            {
                "type": "token_lengths",
                "request_id": request_id,
                "rows": len(lengths),
                "payload_format": "uint32-le",
            },
            result,
            False,
        )

    vectors = encoder.encode(role, texts)
    expected_bytes = len(texts) * DIMENSIONS * 4
    if len(vectors) != expected_bytes:
        raise RuntimeError(
            f"serialized embedding bytes are {len(vectors)}, expected {expected_bytes}"
        )
    return (
        {
            "type": "embeddings",
            "request_id": request_id,
            "rows": len(texts),
            "dimensions": DIMENSIONS,
            "payload_format": "float32-le-row-major",
        },
        vectors,
        False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(HASH_BUFFER_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def hello(
    model_dir: Path,
    model_lock_path: Path,
    dependency_lock_path: Path,
    device: str,
) -> dict[str, object]:
    if model_dir.resolve() != (model_lock_path.parent / "model").resolve():
        fatal("model directory is not the sibling bound by the supplied model lock")
    for name, path in (
        ("model lock", model_lock_path),
        ("dependency lock", dependency_lock_path),
    ):
        if not path.is_file():
            fatal(f"{name} does not exist: {path}")
    verify_pinned_model_bundle(model_dir, model_lock_path)
    identity = runtime_identity()
    return {
        "type": "hello",
        "protocol": PROTOCOL,
        "protocol_version": PROTOCOL_VERSION,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dimensions": DIMENSIONS,
        "model_token_ceiling": MODEL_TOKEN_CEILING,
        "scalar_type": "float32",
        "byte_order": "little",
        "execution_device": device,
        "worker_sha256": sha256_file(Path(__file__).resolve()),
        "model_lock_sha256": sha256_file(model_lock_path),
        "dependency_lock_sha256": sha256_file(dependency_lock_path),
        **identity,
    }


def fatal(message: str) -> NoReturn:
    print(message, file=sys.stderr, flush=True)
    raise SystemExit(2)


def run(
    model_dir: Path,
    model_lock_path: Path,
    dependency_lock_path: Path,
    device: str,
) -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    encoder = GteEncoder(model_dir, device)
    write_frame(
        stdout,
        hello(model_dir, model_lock_path, dependency_lock_path, device),
    )
    while True:
        try:
            frame = read_frame(stdin)
        except ProtocolError as error:
            fatal(f"fatal protocol error: {error}")
        if frame is None:
            return 0
        metadata, payload = frame
        request_id = metadata.get("request_id")
        try:
            response, response_payload, should_exit = handle_request(
                encoder, metadata, payload
            )
        except WorkerError as error:
            write_frame(
                stdout,
                {
                    "type": "error",
                    "request_id": request_id if isinstance(request_id, str) else None,
                    "code": error.code,
                    "message": str(error),
                },
            )
            continue
        except Exception:
            traceback.print_exc(file=sys.stderr)
            write_frame(
                stdout,
                {
                    "type": "error",
                    "request_id": request_id if isinstance(request_id, str) else None,
                    "code": "internal_error",
                    "message": "worker encountered an internal error",
                },
            )
            continue
        write_frame(stdout, response, response_payload)
        if should_exit:
            return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-dir",
        type=Path,
        required=True,
        help="mounted directory containing the exact pinned model snapshot",
    )
    parser.add_argument(
        "--model-lock-path",
        type=Path,
        required=True,
        help="checksum lock adjacent to the mounted model directory",
    )
    parser.add_argument(
        "--dependency-lock-path",
        type=Path,
        required=True,
        help="hash-locked Python dependency record used by this worker",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cuda",
        help="PyTorch execution device (default: cuda)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    arguments = parse_args()
    raise SystemExit(
        run(
            arguments.model_dir,
            arguments.model_lock_path,
            arguments.dependency_lock_path,
            arguments.device,
        )
    )
