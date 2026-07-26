#!/usr/bin/env python3
"""Train and publish one sparse, corpus-induced note-topic relation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import time
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import Tensor, nn


RELATION_FORMAT = "canonical-sparse-note-topic-relation-v1"
READ_CHUNK_BYTES = 8 * 1024 * 1024


def _require_plain_int(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"`{name}` must be an integer >= {minimum}")
    return value


def _require_number(value: object, name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"`{name}` must be a number")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"`{name}` must be finite and >= {minimum}")
    return number


def _require_mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"`{name}` must be an object")
    return value


@dataclass(frozen=True)
class IoBudget:
    max_source_read_bytes: int
    max_durable_write_bytes: int


@dataclass(frozen=True)
class IoPlan:
    source_read_bytes: int
    durable_write_bytes: int

    def require_admitted(self, budget: IoBudget) -> None:
        if self.source_read_bytes > budget.max_source_read_bytes:
            raise ValueError(
                "planned source-read budget exceeded: "
                f"{self.source_read_bytes} > {budget.max_source_read_bytes} bytes"
            )
        if self.durable_write_bytes > budget.max_durable_write_bytes:
            raise ValueError(
                "planned durable-write budget exceeded: "
                f"{self.durable_write_bytes} > "
                f"{budget.max_durable_write_bytes} bytes"
            )


@dataclass(frozen=True)
class InputConfig:
    matrix_path: Path
    note_ids_path: Path
    dimensions: int
    start_row: int
    learning_rows: int
    evaluation_rows: int

    @property
    def total_rows(self) -> int:
        return self.learning_rows + self.evaluation_rows

    @property
    def byte_offset(self) -> int:
        return self.start_row * self.dimensions * 4

    @property
    def byte_length(self) -> int:
        return self.total_rows * self.dimensions * 4

    @property
    def note_ids_byte_offset(self) -> int:
        return self.start_row * 32

    @property
    def note_ids_byte_length(self) -> int:
        return self.total_rows * 32

    @property
    def source_read_bytes(self) -> int:
        return self.byte_length + self.note_ids_byte_length


@dataclass(frozen=True)
class ModelConfig:
    dictionary_size: int
    average_k: int
    batch_size: int
    steps: int
    learning_rate: float
    seed: int
    warmup_steps: int
    dead_tokens: int
    auxiliary_k: int
    auxiliary_penalty: float
    gradient_clip: float
    maximum_relation_entries: int
    device: str


@dataclass(frozen=True)
class ExperimentConfig:
    schema_version: int
    purpose: str
    input: InputConfig
    model: ModelConfig
    io_budget: IoBudget
    output_path: Path

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ExperimentConfig":
        schema_version = _require_plain_int(
            raw.get("schema_version"), "schema_version", minimum=1
        )
        if schema_version != 1:
            raise ValueError(f"unsupported schema version {schema_version}")
        purpose = raw.get("purpose")
        if not isinstance(purpose, str) or not purpose:
            raise ValueError("`purpose` must be a nonempty string")

        input_raw = _require_mapping(raw.get("input"), "input")
        matrix_path_raw = input_raw.get("matrix_path")
        if not isinstance(matrix_path_raw, str) or not matrix_path_raw:
            raise ValueError("`input.matrix_path` must be a nonempty string")
        note_ids_path_raw = input_raw.get("note_ids_path")
        if not isinstance(note_ids_path_raw, str) or not note_ids_path_raw:
            raise ValueError("`input.note_ids_path` must be a nonempty string")
        input_config = InputConfig(
            matrix_path=Path(matrix_path_raw),
            note_ids_path=Path(note_ids_path_raw),
            dimensions=_require_plain_int(
                input_raw.get("dimensions"), "input.dimensions", minimum=1
            ),
            start_row=_require_plain_int(
                input_raw.get("start_row"), "input.start_row"
            ),
            learning_rows=_require_plain_int(
                input_raw.get("learning_rows"), "input.learning_rows", minimum=1
            ),
            evaluation_rows=_require_plain_int(
                input_raw.get("evaluation_rows"), "input.evaluation_rows", minimum=1
            ),
        )

        model_raw = _require_mapping(raw.get("model"), "model")
        dictionary_size = _require_plain_int(
            model_raw.get("dictionary_size"), "model.dictionary_size", minimum=1
        )
        average_k = _require_plain_int(
            model_raw.get("average_k"), "model.average_k", minimum=1
        )
        if average_k > dictionary_size:
            raise ValueError("`model.average_k` cannot exceed dictionary size")
        batch_size = _require_plain_int(
            model_raw.get("batch_size"), "model.batch_size", minimum=1
        )
        default_maximum_entries = (
            input_config.total_rows * min(dictionary_size, average_k * 8)
        )
        model_config = ModelConfig(
            dictionary_size=dictionary_size,
            average_k=average_k,
            batch_size=batch_size,
            steps=_require_plain_int(
                model_raw.get("steps"), "model.steps", minimum=1
            ),
            learning_rate=_require_number(
                model_raw.get("learning_rate"),
                "model.learning_rate",
                minimum=sys.float_info.min,
            ),
            seed=_require_plain_int(model_raw.get("seed"), "model.seed"),
            warmup_steps=_require_plain_int(
                model_raw.get("warmup_steps", 0), "model.warmup_steps"
            ),
            dead_tokens=_require_plain_int(
                model_raw.get("dead_tokens", 10_000_000),
                "model.dead_tokens",
                minimum=1,
            ),
            auxiliary_k=_require_plain_int(
                model_raw.get(
                    "auxiliary_k",
                    min(dictionary_size, max(1, input_config.dimensions // 2)),
                ),
                "model.auxiliary_k",
                minimum=1,
            ),
            auxiliary_penalty=_require_number(
                model_raw.get("auxiliary_penalty", 1.0 / 32.0),
                "model.auxiliary_penalty",
            ),
            gradient_clip=_require_number(
                model_raw.get("gradient_clip", 1.0),
                "model.gradient_clip",
                minimum=sys.float_info.min,
            ),
            maximum_relation_entries=_require_plain_int(
                model_raw.get("maximum_relation_entries", default_maximum_entries),
                "model.maximum_relation_entries",
                minimum=input_config.total_rows,
            ),
            device=str(model_raw.get("device", "cpu")),
        )
        if model_config.warmup_steps > model_config.steps:
            raise ValueError("`model.warmup_steps` cannot exceed training steps")
        if model_config.batch_size > input_config.learning_rows:
            raise ValueError(
                "`model.batch_size` cannot exceed the number of learning rows"
            )
        if model_config.auxiliary_k > dictionary_size:
            raise ValueError("`model.auxiliary_k` cannot exceed dictionary size")
        if model_config.device not in {"cpu", "cuda", "auto"}:
            raise ValueError("`model.device` must be `cpu`, `cuda`, or `auto`")

        budget_raw = _require_mapping(raw.get("io_budget"), "io_budget")
        io_budget = IoBudget(
            max_source_read_bytes=_require_plain_int(
                budget_raw.get("max_source_read_bytes"),
                "io_budget.max_source_read_bytes",
            ),
            max_durable_write_bytes=_require_plain_int(
                budget_raw.get("max_durable_write_bytes"),
                "io_budget.max_durable_write_bytes",
            ),
        )
        output_path_raw = raw.get("output_path")
        if not isinstance(output_path_raw, str) or not output_path_raw:
            raise ValueError("`output_path` must be a nonempty string")
        return cls(
            schema_version=schema_version,
            purpose=purpose,
            input=input_config,
            model=model_config,
            io_budget=io_budget,
            output_path=Path(output_path_raw),
        )


class BatchTopKSae(nn.Module):
    """BatchTopK sparse autoencoder with thresholded standalone inference."""

    def __init__(
        self, input_dimensions: int, dictionary_size: int, average_k: int
    ) -> None:
        super().__init__()
        if input_dimensions < 1 or dictionary_size < 1:
            raise ValueError("model dimensions must be positive")
        if average_k < 1 or average_k > dictionary_size:
            raise ValueError("average_k must be within the dictionary")
        self.input_dimensions = input_dimensions
        self.dictionary_size = dictionary_size
        self.average_k = average_k
        self.decoder_bias = nn.Parameter(torch.zeros(input_dimensions))
        self.encoder = nn.Linear(input_dimensions, dictionary_size, bias=True)
        self.decoder = nn.Linear(dictionary_size, input_dimensions, bias=False)
        self.register_buffer(
            "tokens_since_active", torch.zeros(dictionary_size, dtype=torch.int64)
        )
        self.reset_parameters()

    @torch.no_grad()
    def reset_parameters(self) -> None:
        nn.init.kaiming_uniform_(self.decoder.weight, a=math.sqrt(5))
        self._normalize_decoder_columns()
        self.encoder.weight.copy_(self.decoder.weight.T)
        self.encoder.bias.zero_()
        self.decoder_bias.zero_()
        self.tokens_since_active.zero_()

    @staticmethod
    def select_batch_topk(activations: Tensor, average_k: int) -> Tensor:
        if activations.ndim != 2:
            raise ValueError("activations must be a two-dimensional tensor")
        count = min(activations.numel(), activations.shape[0] * average_k)
        if count < 1:
            return torch.zeros_like(activations)
        values, indexes = torch.topk(activations.flatten(), count, sorted=False)
        return (
            torch.zeros_like(activations)
            .flatten()
            .scatter(0, indexes, values)
            .reshape_as(activations)
        )

    def dense_activations(self, inputs: Tensor) -> Tensor:
        return torch.relu(self.encoder(inputs - self.decoder_bias))

    def encode_training(self, inputs: Tensor) -> Tensor:
        return self.select_batch_topk(
            self.dense_activations(inputs), self.average_k
        )

    def encode_inference(self, inputs: Tensor, threshold: float) -> Tensor:
        activations = self.dense_activations(inputs)
        return torch.where(activations > threshold, activations, 0.0)

    def decode(self, activations: Tensor) -> Tensor:
        return self.decoder(activations) + self.decoder_bias

    def forward_training(self, inputs: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        dense = self.dense_activations(inputs)
        sparse = self.select_batch_topk(dense, self.average_k)
        active = sparse.sum(dim=0) > 0
        self.tokens_since_active.add_(inputs.shape[0])
        self.tokens_since_active[active] = 0
        return self.decode(sparse), sparse, dense

    def auxiliary_loss(
        self,
        inputs: Tensor,
        reconstruction: Tensor,
        dense_activations: Tensor,
        *,
        dead_tokens: int,
        auxiliary_k: int,
        penalty: float,
    ) -> Tensor:
        dead = self.tokens_since_active >= dead_tokens
        dead_count = int(dead.sum())
        if dead_count == 0 or penalty == 0:
            return torch.zeros((), dtype=inputs.dtype, device=inputs.device)
        selected = torch.topk(
            dense_activations[:, dead],
            min(auxiliary_k, dead_count),
            dim=1,
            sorted=False,
        )
        auxiliary = torch.zeros_like(dense_activations[:, dead]).scatter(
            1, selected.indices, selected.values
        )
        residual = (inputs - reconstruction).detach()
        auxiliary_reconstruction = auxiliary @ self.decoder.weight[:, dead].T
        squared_error = (auxiliary_reconstruction - residual).float().pow(2)
        numerator = squared_error.sum(dim=1).mean()
        centered = residual - residual.mean(dim=0, keepdim=True)
        denominator = centered.float().pow(2).sum(dim=1).mean()
        normalized = (numerator / denominator).nan_to_num(0.0)
        return penalty * normalized

    @torch.no_grad()
    def project_decoder_gradient(self) -> None:
        if self.decoder.weight.grad is None:
            return
        normalized = self.decoder.weight
        parallel = (self.decoder.weight.grad * normalized).sum(
            dim=0, keepdim=True
        ) * normalized
        self.decoder.weight.grad.sub_(parallel)

    @torch.no_grad()
    def normalize_decoder(self) -> None:
        self._normalize_decoder_columns()

    @torch.no_grad()
    def _normalize_decoder_columns(self) -> None:
        norms = self.decoder.weight.norm(dim=0, keepdim=True).clamp_min_(1e-12)
        self.decoder.weight.div_(norms)


@torch.no_grad()
def geometric_median(
    rows: Tensor, *, maximum_iterations: int = 100, tolerance: float = 1e-5
) -> Tensor:
    if rows.ndim != 2 or rows.shape[0] < 1:
        raise ValueError("geometric median requires at least one row")
    estimate = rows.mean(dim=0)
    for _ in range(maximum_iterations):
        distances = torch.linalg.vector_norm(rows - estimate, dim=1)
        if bool(torch.any(distances <= tolerance)):
            return rows[int(torch.argmin(distances))].clone()
        inverse = distances.reciprocal()
        updated = (rows * inverse[:, None]).sum(dim=0) / inverse.sum()
        if float(torch.linalg.vector_norm(updated - estimate)) <= tolerance:
            return updated
        estimate = updated
    return estimate


@torch.no_grad()
def calibrate_inference_threshold(
    model: BatchTopKSae,
    embeddings: Tensor,
    average_k: int,
    *,
    batch_size: int | None = None,
) -> float:
    """Average the minimum retained activation across fixed training batches."""

    if embeddings.ndim != 2 or embeddings.shape[0] < 1:
        raise ValueError("threshold calibration requires a nonempty matrix")
    batch_size = batch_size or embeddings.shape[0]
    boundaries: list[float] = []
    for start in range(0, embeddings.shape[0], batch_size):
        dense = model.dense_activations(
            embeddings[start : start + batch_size]
        )
        retained = model.select_batch_topk(dense, average_k)
        positive = retained[retained > 0]
        if positive.numel():
            boundaries.append(float(positive.min()))
    if not boundaries:
        return 0.0
    return sum(boundaries) / len(boundaries)


class SparseRelation:
    """One sparse matrix with note-major storage and a topic-major permutation."""

    def __init__(
        self,
        *,
        note_offsets: Tensor,
        topic_ids: Tensor,
        weights: Tensor,
        topic_offsets: Tensor,
        topic_edge_order: Tensor,
        source_topic_ids: Tensor,
        note_ids: Tensor,
    ) -> None:
        self.note_offsets = note_offsets.to(dtype=torch.int64, device="cpu")
        self.topic_ids = topic_ids.to(dtype=torch.int32, device="cpu")
        self.weights = weights.to(dtype=torch.float32, device="cpu")
        self.topic_offsets = topic_offsets.to(dtype=torch.int64, device="cpu")
        self.topic_edge_order = topic_edge_order.to(dtype=torch.int64, device="cpu")
        self.source_topic_ids = source_topic_ids.to(
            dtype=torch.int32, device="cpu"
        )
        self.note_ids = note_ids.to(dtype=torch.uint8, device="cpu")

    @property
    def topic_count(self) -> int:
        return int(self.source_topic_ids.numel())

    @property
    def note_count(self) -> int:
        return int(self.note_offsets.numel() - 1)

    @property
    def entry_count(self) -> int:
        return int(self.weights.numel())

    @classmethod
    def from_activations(cls, activations: Tensor) -> "SparseRelation":
        if activations.ndim != 2:
            raise ValueError("activations must be a two-dimensional tensor")
        return cls.from_activation_batches(
            [activations],
            topic_count=activations.shape[1],
            maximum_entries=activations.numel(),
            learning_note_count=activations.shape[0],
        )

    @classmethod
    def from_activation_batches(
        cls,
        batches: Iterable[Tensor],
        *,
        topic_count: int,
        maximum_entries: int,
        learning_note_count: int | None = None,
        note_ids: Tensor | None = None,
    ) -> "SparseRelation":
        if topic_count < 1:
            raise ValueError("topic count must be positive")
        if learning_note_count is not None and learning_note_count < 1:
            raise ValueError("learning note count must be positive")
        row_parts: list[Tensor] = []
        topic_parts: list[Tensor] = []
        weight_parts: list[Tensor] = []
        learning_topics = torch.zeros(topic_count, dtype=torch.bool)
        note_count = 0
        entry_count = 0
        for batch in batches:
            if batch.ndim != 2 or batch.shape[1] != topic_count:
                raise ValueError("activation batch dimensions do not match")
            if batch.shape[0] < 1:
                continue
            batch = batch.detach().to(dtype=torch.float32, device="cpu")
            if not bool(torch.all(torch.isfinite(batch))):
                raise ValueError("activations contain a non-finite value")
            if bool(torch.any(batch < 0)):
                raise ValueError("activations cannot be negative")
            present = batch > 0
            counts = present.sum(dim=1, dtype=torch.int64)
            entry_count += int(counts.sum())
            if entry_count > maximum_entries:
                raise ValueError(
                    "inferred relation exceeds `maximum_relation_entries`; "
                    "nothing was published"
                )
            indexes = present.nonzero(as_tuple=False)
            if indexes.numel():
                global_rows = indexes[:, 0] + note_count
                row_parts.append(global_rows.to(torch.int64))
                topic_parts.append(indexes[:, 1].to(torch.int32))
                weight_parts.append(batch[present])
                learning_end = (
                    note_count + batch.shape[0]
                    if learning_note_count is None
                    else min(note_count + batch.shape[0], learning_note_count)
                )
                learning_rows_in_batch = max(0, learning_end - note_count)
                if learning_rows_in_batch:
                    learning_topics |= present[:learning_rows_in_batch].any(dim=0)
            note_count += batch.shape[0]
        if note_count < 1:
            raise ValueError("relation requires at least one note")
        if learning_note_count is not None and learning_note_count > note_count:
            raise ValueError("learning note count exceeds relation notes")
        source_topic_ids = learning_topics.nonzero(as_tuple=False).flatten().to(
            torch.int32
        )
        if source_topic_ids.numel() == 0:
            raise ValueError("no feature was active on a learning note")

        source_rows = (
            torch.cat(row_parts)
            if row_parts
            else torch.empty(0, dtype=torch.int64)
        )
        source_topics = (
            torch.cat(topic_parts)
            if topic_parts
            else torch.empty(0, dtype=torch.int32)
        )
        raw_weights = (
            torch.cat(weight_parts)
            if weight_parts
            else torch.empty(0, dtype=torch.float32)
        )
        remap = torch.full((topic_count,), -1, dtype=torch.int32)
        remap[source_topic_ids.to(torch.int64)] = torch.arange(
            source_topic_ids.numel(), dtype=torch.int32
        )
        retained = remap[source_topics.to(torch.int64)] >= 0
        rows = source_rows[retained]
        topic_ids = remap[source_topics[retained].to(torch.int64)]
        raw_weights = raw_weights[retained]
        counts = torch.bincount(rows, minlength=note_count)
        note_offsets = torch.cat(
            (torch.zeros(1, dtype=torch.int64), counts.cumsum(dim=0))
        )
        row_mass = torch.zeros(note_count, dtype=torch.float32)
        row_mass.scatter_add_(0, rows, raw_weights)
        weights = raw_weights / row_mass[rows]

        weight_order = torch.argsort(weights, descending=True, stable=True)
        topic_edge_order = weight_order[
            torch.argsort(
                topic_ids[weight_order].to(torch.int64), stable=True
            )
        ]
        compact_topic_count = int(source_topic_ids.numel())
        topic_counts = torch.bincount(
            topic_ids.to(torch.int64), minlength=compact_topic_count
        )
        topic_offsets = torch.cat(
            (torch.zeros(1, dtype=torch.int64), topic_counts.cumsum(dim=0))
        )
        if note_ids is None:
            note_id_bytes = bytearray(note_count * 32)
            for index in range(note_count):
                struct.pack_into("<Q", note_id_bytes, index * 32, index)
            note_ids = torch.frombuffer(
                note_id_bytes, dtype=torch.uint8
            ).clone().reshape(note_count, 32)
        relation = cls(
            note_offsets=note_offsets,
            topic_ids=topic_ids,
            weights=weights,
            topic_offsets=topic_offsets,
            topic_edge_order=topic_edge_order,
            source_topic_ids=source_topic_ids,
            note_ids=note_ids,
        )
        if relation.note_count != note_count:
            raise AssertionError("constructed relation lost note rows")
        relation.validate()
        return relation

    def note_id(self, note: int) -> bytes:
        if note < 0 or note >= self.note_count:
            raise IndexError("note is outside the relation")
        return bytes(self.note_ids[note].tolist())

    def topics_for_note_id(self, note_id: bytes) -> list[tuple[int, float]]:
        if len(note_id) != 32:
            raise ValueError("NoteId must be exactly 32 bytes")
        target = torch.tensor(list(note_id), dtype=torch.uint8)
        matches = torch.all(self.note_ids == target, dim=1).nonzero(
            as_tuple=False
        )
        if matches.shape[0] != 1:
            raise KeyError("NoteId is not present in the relation")
        return self.topics_for_note(int(matches[0]))

    def topics_for_note(self, note: int) -> list[tuple[int, float]]:
        if note < 0 or note >= self.note_count:
            raise IndexError("note is outside the relation")
        start = int(self.note_offsets[note])
        end = int(self.note_offsets[note + 1])
        return [
            (int(topic), float(weight))
            for topic, weight in zip(
                self.topic_ids[start:end].tolist(),
                self.weights[start:end].tolist(),
                strict=True,
            )
        ]

    def notes_for_topic(self, topic: int) -> list[tuple[int, float]]:
        if topic < 0 or topic >= self.topic_count:
            raise IndexError("topic is outside the relation")
        start = int(self.topic_offsets[topic])
        end = int(self.topic_offsets[topic + 1])
        edges = self.topic_edge_order[start:end]
        notes = torch.searchsorted(
            self.note_offsets[1:], edges, right=True
        )
        return [
            (int(note), float(self.weights[int(edge)]))
            for note, edge in zip(notes.tolist(), edges.tolist(), strict=True)
        ]

    def validate(self) -> None:
        if self.topic_count < 1:
            raise ValueError("relation has no topics")
        if self.source_topic_ids.shape != (self.topic_count,):
            raise ValueError("source topic IDs are malformed")
        if bool(
            torch.any(self.source_topic_ids[1:] <= self.source_topic_ids[:-1])
        ):
            raise ValueError("source topic IDs are not strictly increasing")
        if self.note_ids.shape != (self.note_count, 32):
            raise ValueError("NoteIds are malformed")
        unique_note_ids = {bytes(row.tolist()) for row in self.note_ids}
        if len(unique_note_ids) != self.note_count:
            raise ValueError("NoteIds are not unique")
        if self.note_offsets.ndim != 1 or self.note_offsets.numel() < 1:
            raise ValueError("note offsets are malformed")
        if self.topic_offsets.shape != (self.topic_count + 1,):
            raise ValueError("topic offsets are malformed")
        if int(self.note_offsets[0]) != 0 or int(self.topic_offsets[0]) != 0:
            raise ValueError("offsets must start at zero")
        if bool(torch.any(self.note_offsets[1:] < self.note_offsets[:-1])):
            raise ValueError("note offsets are not monotonic")
        if bool(torch.any(self.topic_offsets[1:] < self.topic_offsets[:-1])):
            raise ValueError("topic offsets are not monotonic")
        if int(self.note_offsets[-1]) != self.entry_count:
            raise ValueError("note offsets do not consume the relation")
        if int(self.topic_offsets[-1]) != self.entry_count:
            raise ValueError("topic offsets do not consume the relation")
        if self.topic_ids.shape != (self.entry_count,):
            raise ValueError("topic IDs do not match relation entries")
        if self.topic_edge_order.shape != (self.entry_count,):
            raise ValueError("topic permutation does not match relation entries")
        if bool(torch.any(self.topic_ids < 0)) or bool(
            torch.any(self.topic_ids >= self.topic_count)
        ):
            raise ValueError("relation contains an invalid topic ID")
        if not bool(torch.all(torch.isfinite(self.weights))) or bool(
            torch.any(self.weights <= 0)
        ):
            raise ValueError("relation weights must be finite and positive")
        if self.entry_count:
            expected = torch.arange(self.entry_count, dtype=torch.int64)
            if not torch.equal(torch.sort(self.topic_edge_order).values, expected):
                raise ValueError("topic edge order is not a permutation")
            ordered_topics = self.topic_ids[self.topic_edge_order]
            if bool(torch.any(ordered_topics[1:] < ordered_topics[:-1])):
                raise ValueError("topic edge order is not topic-major")
            ordered_weights = self.weights[self.topic_edge_order]
            for topic in range(self.topic_count):
                start = int(self.topic_offsets[topic])
                end = int(self.topic_offsets[topic + 1])
                if bool(
                    torch.any(
                        ordered_weights[start + 1 : end]
                        > ordered_weights[start : end - 1]
                    )
                ):
                    raise ValueError(
                        "topic edges are not ordered by descending weight"
                    )
        for note in range(self.note_count):
            start = int(self.note_offsets[note])
            end = int(self.note_offsets[note + 1])
            if start != end and not math.isclose(
                float(self.weights[start:end].sum()),
                1.0,
                rel_tol=1e-5,
                abs_tol=1e-6,
            ):
                raise ValueError("assigned note weights do not sum to one")

    @staticmethod
    def _tensor_bytes(tensor: Tensor) -> bytes:
        if sys.byteorder != "little":
            raise RuntimeError("relation format requires a little-endian host")
        contiguous = tensor.detach().to(device="cpu").contiguous()
        return contiguous.numpy().tobytes(order="C")

    def _serialized_files(self) -> dict[str, bytes]:
        return {
            "note-offsets.u64le": self._tensor_bytes(self.note_offsets),
            "topic-ids.u32le": self._tensor_bytes(self.topic_ids),
            "weights.f32le": self._tensor_bytes(self.weights),
            "topic-offsets.u64le": self._tensor_bytes(self.topic_offsets),
            "topic-edge-order.u64le": self._tensor_bytes(self.topic_edge_order),
            "source-topic-ids.u32le": self._tensor_bytes(self.source_topic_ids),
            "note-ids.bin": self._tensor_bytes(self.note_ids),
        }

    def publish(
        self,
        output_path: Path,
        *,
        metadata: dict[str, Any],
        maximum_write_bytes: int,
    ) -> int:
        self.validate()
        files = self._serialized_files()
        file_bytes = sum(len(contents) for contents in files.values())
        manifest_base = {
            "schema_version": 1,
            "relation_format": RELATION_FORMAT,
            "note_count": self.note_count,
            "topic_count": self.topic_count,
            "entry_count": self.entry_count,
            "weight_semantics": "positive activation normalized within each note",
            "topic_semantics": (
                "compact IDs for features active on at least one learning note"
            ),
            "metadata": metadata,
            "files": {
                name: {
                    "bytes": len(contents),
                    "sha256": hashlib.sha256(contents).hexdigest(),
                }
                for name, contents in files.items()
            },
        }
        manifest_bytes = (
            json.dumps(
                manifest_base,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode()
        total_bytes = file_bytes + len(manifest_bytes)
        if total_bytes > maximum_write_bytes:
            raise ValueError(
                "actual durable-write budget exceeded before publication: "
                f"{total_bytes} > {maximum_write_bytes} bytes"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            raise FileExistsError(f"output path already exists: {output_path}")
        staging: Path | None = Path(
            tempfile.mkdtemp(prefix=f".{output_path.name}.", dir=output_path.parent)
        )
        try:
            assert staging is not None
            for name, contents in files.items():
                with (staging / name).open("xb") as output:
                    output.write(contents)
                    output.flush()
                    os.fsync(output.fileno())
            with (staging / "manifest.json").open("xb") as output:
                output.write(manifest_bytes)
                output.flush()
                os.fsync(output.fileno())
            os.replace(staging, output_path)
            parent_descriptor = os.open(output_path.parent, os.O_RDONLY)
            try:
                os.fsync(parent_descriptor)
            finally:
                os.close(parent_descriptor)
            staging = None
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging)
        return total_bytes

    @classmethod
    def open(cls, path: Path) -> "SparseRelation":
        manifest = json.loads((path / "manifest.json").read_text())
        if manifest.get("relation_format") != RELATION_FORMAT:
            raise ValueError("unsupported relation format")
        files = _require_mapping(manifest.get("files"), "manifest.files")

        def verified_bytes(name: str) -> bytes:
            spec = _require_mapping(files.get(name), f"manifest.files.{name}")
            contents = (path / name).read_bytes()
            if len(contents) != spec.get("bytes"):
                raise ValueError(f"relation file length mismatch: {name}")
            if hashlib.sha256(contents).hexdigest() != spec.get("sha256"):
                raise ValueError(f"relation file hash mismatch: {name}")
            return contents

        def tensor_from(name: str, dtype: torch.dtype) -> Tensor:
            return torch.frombuffer(
                bytearray(verified_bytes(name)), dtype=dtype
            ).clone()

        relation = cls(
            note_offsets=tensor_from("note-offsets.u64le", torch.int64),
            topic_ids=tensor_from("topic-ids.u32le", torch.int32),
            weights=tensor_from("weights.f32le", torch.float32),
            topic_offsets=tensor_from("topic-offsets.u64le", torch.int64),
            topic_edge_order=tensor_from(
                "topic-edge-order.u64le", torch.int64
            ),
            source_topic_ids=tensor_from(
                "source-topic-ids.u32le", torch.int32
            ),
            note_ids=tensor_from("note-ids.bin", torch.uint8).reshape(-1, 32),
        )
        if relation.topic_count != _require_plain_int(
            manifest.get("topic_count"), "manifest.topic_count", minimum=1
        ):
            raise ValueError("manifest topic count does not match relation")
        if relation.note_count != manifest.get("note_count"):
            raise ValueError("manifest note count does not match relation")
        if relation.entry_count != manifest.get("entry_count"):
            raise ValueError("manifest entry count does not match relation")
        relation.validate()
        return relation


def _estimate_relation_bytes(config: ExperimentConfig) -> int:
    rows = config.input.total_rows
    entries = config.model.maximum_relation_entries
    fixed = (
        (rows + 1) * 8
        + rows * 32
        + (config.model.dictionary_size + 1) * 8
        + config.model.dictionary_size * 4
    )
    per_entry = 4 + 4 + 8
    return fixed + entries * per_entry + 64 * 1024


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    return torch.device(requested)


def _read_exact_range(
    path: Path, *, offset: int, length: int
) -> tuple[bytearray, str]:
    expected_end = offset + length
    descriptor = os.open(path, os.O_RDONLY)
    try:
        size = os.fstat(descriptor).st_size
        if size < expected_end:
            raise ValueError(
                f"{path} ends at {size} bytes; requested range ends at "
                f"{expected_end}"
            )
        if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_RANDOM"):
            os.posix_fadvise(
                descriptor,
                offset,
                length,
                os.POSIX_FADV_RANDOM,
            )
        contents = bytearray(length)
        view = memoryview(contents)
        read = 0
        digest = hashlib.sha256()
        while read < length:
            chunk = os.pread(
                descriptor,
                min(READ_CHUNK_BYTES, length - read),
                offset + read,
            )
            if not chunk:
                raise OSError(f"{path} ended before the admitted range")
            view[read : read + len(chunk)] = chunk
            digest.update(chunk)
            read += len(chunk)
        if hasattr(os, "posix_fadvise") and hasattr(os, "POSIX_FADV_DONTNEED"):
            os.posix_fadvise(
                descriptor,
                offset,
                length,
                os.POSIX_FADV_DONTNEED,
            )
    finally:
        os.close(descriptor)
    return contents, digest.hexdigest()


def _read_inputs(config: InputConfig) -> tuple[Tensor, Tensor, str, str]:
    matrix_bytes, matrix_sha256 = _read_exact_range(
        config.matrix_path, offset=config.byte_offset, length=config.byte_length
    )
    note_id_bytes, note_ids_sha256 = _read_exact_range(
        config.note_ids_path,
        offset=config.note_ids_byte_offset,
        length=config.note_ids_byte_length,
    )
    embeddings = torch.frombuffer(
        matrix_bytes, dtype=torch.float32
    ).clone().reshape(config.total_rows, config.dimensions)
    note_ids = torch.frombuffer(
        note_id_bytes, dtype=torch.uint8
    ).clone().reshape(config.total_rows, 32)
    return embeddings, note_ids, matrix_sha256, note_ids_sha256


def _training_batches(
    row_count: int, batch_size: int, steps: int, *, seed: int
) -> Iterable[Tensor]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    order = torch.empty(0, dtype=torch.int64)
    cursor = 0
    for _ in range(steps):
        if cursor + batch_size > order.numel():
            order = torch.randperm(row_count, generator=generator)
            cursor = 0
        indexes = order[cursor : cursor + batch_size]
        cursor += batch_size
        if indexes.numel() < batch_size:
            missing = batch_size - indexes.numel()
            order = torch.randperm(row_count, generator=generator)
            indexes = torch.cat((indexes, order[:missing]))
            cursor = missing
        yield indexes


@dataclass(frozen=True)
class ExperimentReport:
    total_rows: int
    dictionary_size: int
    relation_entries: int
    inference_threshold: float
    final_loss: float
    final_reconstruction_loss: float
    source_bytes_read: int
    durable_bytes_written: int
    elapsed_seconds: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "total_rows": self.total_rows,
            "dictionary_size": self.dictionary_size,
            "relation_entries": self.relation_entries,
            "inference_threshold": self.inference_threshold,
            "final_loss": self.final_loss,
            "final_reconstruction_loss": self.final_reconstruction_loss,
            "source_bytes_read": self.source_bytes_read,
            "durable_bytes_written": self.durable_bytes_written,
            "elapsed_seconds": self.elapsed_seconds,
        }


def run_experiment(config: ExperimentConfig) -> ExperimentReport:
    """Execute the admitted production path without scanning the source matrix."""

    started = time.monotonic()
    planned = IoPlan(
        source_read_bytes=config.input.source_read_bytes,
        durable_write_bytes=_estimate_relation_bytes(config),
    )
    planned.require_admitted(config.io_budget)
    embeddings, note_ids, matrix_sha256, note_ids_sha256 = _read_inputs(config.input)
    if not bool(torch.all(torch.isfinite(embeddings))):
        raise ValueError("input embeddings contain a non-finite value")

    torch.manual_seed(config.model.seed)
    torch.use_deterministic_algorithms(True)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.model.seed)
    device = _resolve_device(config.model.device)
    learning = embeddings[: config.input.learning_rows].to(device)
    model = BatchTopKSae(
        config.input.dimensions,
        config.model.dictionary_size,
        config.model.average_k,
    ).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.model.learning_rate, betas=(0.9, 0.999)
    )

    final_loss = math.nan
    final_reconstruction_loss = math.nan
    model.train()
    batches = iter(
        _training_batches(
            config.input.learning_rows,
            config.model.batch_size,
            config.model.steps,
            seed=config.model.seed,
        )
    )
    first_indexes = next(batches)
    with torch.no_grad():
        model.decoder_bias.copy_(
            geometric_median(learning[first_indexes.to(device)])
        )
    for step, indexes in enumerate(
        chain((first_indexes,), batches),
        start=1,
    ):
        batch = learning[indexes.to(device)]
        optimizer.zero_grad(set_to_none=True)
        reconstruction, _, dense = model.forward_training(batch)
        reconstruction_loss = (
            (reconstruction - batch).float().pow(2).sum(dim=1).mean()
        )
        auxiliary_loss = model.auxiliary_loss(
            batch,
            reconstruction,
            dense,
            dead_tokens=config.model.dead_tokens,
            auxiliary_k=config.model.auxiliary_k,
            penalty=config.model.auxiliary_penalty,
        )
        loss = reconstruction_loss + auxiliary_loss
        if not bool(torch.isfinite(loss)):
            raise ValueError(f"training produced a non-finite loss at step {step}")
        loss.backward()
        model.project_decoder_gradient()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), config.model.gradient_clip
        )
        if config.model.warmup_steps:
            scale = min(1.0, step / config.model.warmup_steps)
            for group in optimizer.param_groups:
                group["lr"] = config.model.learning_rate * scale
        optimizer.step()
        model.normalize_decoder()
        final_loss = float(loss.detach())
        final_reconstruction_loss = float(reconstruction_loss.detach())

    model.eval()
    threshold = calibrate_inference_threshold(
        model,
        learning,
        config.model.average_k,
        batch_size=config.model.batch_size,
    )
    if not math.isfinite(threshold):
        raise ValueError("threshold calibration produced a non-finite value")
    all_embeddings = embeddings.to(device)

    def inferred_batches() -> Iterable[Tensor]:
        with torch.no_grad():
            for start in range(
                0, config.input.total_rows, config.model.batch_size
            ):
                yield model.encode_inference(
                    all_embeddings[start : start + config.model.batch_size],
                    threshold,
                ).cpu()

    relation = SparseRelation.from_activation_batches(
        inferred_batches(),
        topic_count=config.model.dictionary_size,
        maximum_entries=config.model.maximum_relation_entries,
        learning_note_count=config.input.learning_rows,
        note_ids=note_ids,
    )
    metadata = {
        "purpose": config.purpose,
        "matrix_range_sha256": matrix_sha256,
        "note_ids_range_sha256": note_ids_sha256,
        "start_row": config.input.start_row,
        "input_dimensions": config.input.dimensions,
        "learning_rows": config.input.learning_rows,
        "evaluation_rows": config.input.evaluation_rows,
        "dictionary_size": config.model.dictionary_size,
        "average_k": config.model.average_k,
        "inference_threshold": threshold,
        "seed": config.model.seed,
        "steps": config.model.steps,
        "batch_size": config.model.batch_size,
        "learning_rate": config.model.learning_rate,
        "warmup_steps": config.model.warmup_steps,
        "dead_tokens": config.model.dead_tokens,
        "auxiliary_k": config.model.auxiliary_k,
        "auxiliary_penalty": config.model.auxiliary_penalty,
        "gradient_clip": config.model.gradient_clip,
        "device": str(device),
        "torch_version": torch.__version__,
        "threshold_calibration": (
            "arithmetic mean of minimum positive BatchTopK activations "
            "over fixed sequential learning batches"
        ),
    }
    written = relation.publish(
        config.output_path,
        metadata=metadata,
        maximum_write_bytes=config.io_budget.max_durable_write_bytes,
    )
    return ExperimentReport(
        total_rows=config.input.total_rows,
        dictionary_size=config.model.dictionary_size,
        relation_entries=relation.entry_count,
        inference_threshold=threshold,
        final_loss=final_loss,
        final_reconstruction_loss=final_reconstruction_loss,
        source_bytes_read=config.input.source_read_bytes,
        durable_bytes_written=written,
        elapsed_seconds=time.monotonic() - started,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    arguments = parser.parse_args()
    config = ExperimentConfig.from_dict(json.loads(arguments.config.read_text()))
    report = run_experiment(config)
    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
