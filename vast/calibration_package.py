#!/usr/bin/env python3
"""Validate and sanitize provider instance and immutable image identities."""

from __future__ import annotations

from decimal import Decimal


def require_number(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Vast offer field {field} is not numeric")
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError(f"Vast offer field {field} is not finite")
    return number


def created_instance_id(create_result: object) -> str:
    if not isinstance(create_result, dict) or create_result.get("success") is not True:
        raise ValueError("Vast create result is invalid")
    value = create_result.get("new_contract")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, str))
        or not str(value).strip()
    ):
        raise ValueError("Vast create result has no instance ID")
    return str(value)


def freeze_create_result(raw_create_result: object) -> dict[str, object]:
    created_instance_id(raw_create_result)
    assert isinstance(raw_create_result, dict)
    return {
        "success": True,
        "new_contract": raw_create_result["new_contract"],
    }


def instance_from_document(document: object) -> dict[str, object]:
    if isinstance(document, dict) and "instances" in document:
        document = document.get("instances")
    if not isinstance(document, dict):
        raise ValueError("actual Vast instance must be one JSON object")
    return document


INSTANCE_RECORD_FIELDS = (
    "id",
    "machine_id",
    "bundle_id",
    "actual_status",
    "intended_status",
    "image_uuid",
    "gpu_name",
    "num_gpus",
    "disk_space",
    "dph_total",
    "is_bid",
    "verification",
    "label",
)


def freeze_instance_record(create_result: object, raw_instance: object) -> dict[str, object]:
    expected_id = created_instance_id(create_result)
    instance = instance_from_document(raw_instance)
    if str(instance.get("id")) != expected_id:
        raise ValueError("actual instance does not match the Vast create result")
    return {field: instance.get(field) for field in INSTANCE_RECORD_FIELDS}


def sanitize_instance_list(raw_instances: object) -> list[dict[str, object]]:
    """Project a Vast instance inventory onto non-secret audit fields."""
    if isinstance(raw_instances, dict) and "instances" in raw_instances:
        raw_instances = raw_instances.get("instances")
    if not isinstance(raw_instances, list):
        raise ValueError("Vast instance inventory must be a list")
    records = []
    for instance in raw_instances:
        if not isinstance(instance, dict):
            raise ValueError("Vast instance inventory contains a non-object row")
        records.append({field: instance.get(field) for field in INSTANCE_RECORD_FIELDS})
    return records


def normalized_image_ref(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("container image reference is invalid")
    normalized = value.strip()
    if normalized.startswith("docker.io/"):
        normalized = normalized[len("docker.io/") :]
    return normalized


def immutable_image_ref(value: object) -> str:
    normalized = normalized_image_ref(value)
    try:
        repository, digest = normalized.rsplit("@sha256:", 1)
    except ValueError as error:
        raise ValueError("container image must use an immutable digest") from error
    if (
        not repository
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("container image must use an immutable digest")
    return normalized
