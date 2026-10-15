"""Native hierarchy construction, including recursive HiGen V5.

The shared experiment runner owns teacher transport, caching and accounting.
Preparation and advancement only freeze inputs and collect saved results.
"""

from copy import deepcopy
from contextlib import ExitStack
from concurrent.futures import FIRST_COMPLETED, Future, wait
from contextvars import copy_context
import fcntl
import heapq
from itertools import count
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import subprocess
from datetime import datetime, timezone
from threading import Event, Thread

from . import canonical_trial as trial
from . import experiment as workflow
from . import worker
from .canonical_receipts import _failure_receipts


POLICY = "hierarchy-generation-v3"
POLICY_V31 = "hierarchy-generation-v3.1"
POLICY_V32 = "hierarchy-generation-v3.2"
POLICY_V4_ROOTS = "hierarchy-generation-v4-roots"
POLICY_V41 = "hierarchy-generation-v4.1"
POLICY_V42 = "hierarchy-generation-v4.2"
POLICY_V43 = "hierarchy-generation-v4.3"
POLICY_V44 = "hierarchy-generation-v4.4"
POLICY_V5 = "hierarchy-generation-v5"
SECTION_POLICIES = (POLICY_V41, POLICY_V42, POLICY_V43, POLICY_V44)
HDBSCAN_POLICIES = (POLICY_V4_ROOTS, *SECTION_POLICIES, POLICY_V5)
TITLE_POLICIES = (POLICY_V32, *HDBSCAN_POLICIES)
MAX_SIBLINGS = 6
MIN_NOTES = 2
PAIR_CHUNK_ROWS = 50000
PAIR_MERGE_FANIN = 32
RUNNER_BACKOFF_SECONDS = 5
RUNNER_BACKOFF_MAX_SECONDS = 60
CODE_FILES = (
    "hierarchy_generation.py",
    "worker.py",
    "experiment_inputs.py",
    "experiment_extension.py",
    "hierarchy_node_pairs.py",
    "canonical_trial.py",
    "canonical_receipts.py",
    "prompt_assembly.py",
)


def summary(state):
    unresolved = [
        *state.get("unresolved", []),
        *[
            dict(
                role=record["role"],
                experiment=record["experiment"],
                case=identifier,
                status=answer["status"],
                error=answer.get("error"),
            )
            for record in state["experiments"]
            for identifier, answer in record.get("answers", {}).items()
            if answer["status"] not in ("valid", "unrun")
        ],
    ]
    result = dict(
        status=state["status"],
        generation_policy=state["generation_policy"],
        canonical_nodes=len(state["nodes"]),
        original_l1s=len(state["originals"]),
        experiments=[
            r["experiment"] for r in state["experiments"] if not r.get("complete")
        ],
        encodings=[
            r["config"] for r in state["encodings"]
            if not r.get("complete") and not r.get("skipped")
        ],
        skipped_encodings=[
            dict(config=r["config"], reason=r["skipped"])
            for r in state["encodings"] if r.get("skipped")
        ],
        unresolved=unresolved,
        diagnostic_errors=[
            dict(role=record['role'], experiment=record['experiment'],
                 case=identifier, errors=answer['diagnostic_errors'])
            for record in state['experiments']
            for identifier, answer in record.get('answers', {}).items()
            if answer.get('diagnostic_errors')
        ],
        skipped_bootstrap=[
            dict(
                local=original["local"],
                case=original["id"],
                experiment=state["experiments"][0]["experiment"],
                reason="null Bootstrap meaning",
            )
            for original in state["originals"]
            if state["families"]
            and "meaning" in original
            and original["meaning"] is None
        ],
    )
    if state["generation_policy"] in (POLICY_V31, POLICY_V32):
        result["discarded_by_cutoff"] = [
            dict(
                family=family["id"], parent=family["parent"], round=index + 1,
                cutoff=round_["cutoff"], nodes=pair["nodes"], cosine=pair["cosine"],
                original_ids=[
                    original for item in pair["nodes"]
                    for original in state["items"][item]["original_ids"]
                ],
            )
            for family in state["families"]
            for index, round_ in enumerate(_applied_rounds(family))
            for pair in round_["pairs"] if pair["cosine"] < round_["cutoff"]
        ]
        parents = {p for n in state["nodes"] for p in n["parents"]}
        represented = {
            e["note_id"] for n in state["nodes"] if n["id"] not in parents
            for e in n["entries"]
        }
        result["notes_not_in_hierarchy"] = (
            [n for n in state["note_ids"] if n not in represented]
            if state["status"] == "complete" else None
        )
    if state["generation_policy"] in HDBSCAN_POLICIES:
        originals = {o["id"]: o for o in state["originals"]}
        def notes(ids):
            return {originals[o]["local"]["note_id"] for i in ids
                    for o in state["items"][i]["original_ids"]}
        result["hdbscan_rounds"] = []
        for family in state["families"]:
            for index, round_ in enumerate(family["rounds"]):
                before = notes(round_["current"])
                after = notes([i for group in round_["groups"] for i in group])
                result["hdbscan_rounds"].append(dict(
                    round=index + 1, input_nodes=len(round_["current"]),
                    groups=len(round_["groups"]),
                    group_sizes=[len(g) for g in round_["groups"]],
                    unassigned_nodes=len(round_["unassigned"]),
                    notes_before=len(before), notes_after=len(after),
                    lost_note_ids=[n for n in state["note_ids"] if n in before - after],
                ))
        represented = ({e["note_id"] for n in state["nodes"] for e in n["entries"]}
                       | set(state.get("direct_note_ids", [])))
        result["notes_not_in_hierarchy"] = (
            [n for n in state["note_ids"] if n not in represented]
            if state["status"] == "complete" else None)
        result["scope"] = ("roots only" if state["generation_policy"] == POLICY_V4_ROOTS
                           else "hierarchy down to original HDBSCAN groups")
        if state['generation_policy'] == POLICY_V5:
            result['scope'] = 'recursive fresh HDBSCAN trees with group leaves'
            result['direct_note_ids'] = state.get('direct_note_ids', [])
            result['hdbscan_section_cuts'] = [
                dict(family=f['id'], parent=f['parent'], round=i+1,
                     selection=r['selection'], conflicting_sections=r.get('conflicting_sections', []))
                for f in state['families'] for i, r in enumerate(f['rounds'])]
        if state["generation_policy"] in SECTION_POLICIES:
            result["hdbscan_section_cuts"] = state.get("hdbscan_sections", {}).get("cuts", [])
    return result


def _experiment(directory, state, role, spec, source, adapter):
    index = len(state["experiments"])
    step = directory / f"batch-{index:05d}"
    step.mkdir(exist_ok=True)
    settings = deepcopy(spec)
    settings["dataset"] = dict(adapter=adapter, path="source.json")
    trial._save_once(step / "source.json", source)
    trial._save_once(step / "spec.json", settings)
    destination = step / "experiment"
    if not destination.exists():
        args = workflow.parser().parse_args(
            [
                "prepare",
                str(destination),
                "--spec",
                str(step / "spec.json"),
                "--history-root",
                state["history_root"],
            ]
        )
        workflow.prepare(args, include_request_preview=False)
    plan, _, _ = workflow.load(destination)
    record = dict(
        role=role,
        experiment=str(destination),
        inputs={row["id"]: row["inputs"] for row in plan["cases"]},
    )
    state["experiments"].append(record)
    return index


def _teacher_spec(path, sources):
    path = Path(path).resolve()
    spec = deepcopy(workflow.read(path))
    runner = spec["runner"]
    if "output_schema_path" in runner:
        if "output_schema" in runner:
            raise ValueError("choose output_schema or output_schema_path")
        schema = workflow.resolve(runner.pop("output_schema_path"), path.parent)
        runner["output_schema"] = workflow.read(schema)
        sources[str(schema)] = trial._hash(schema)
    if "runner_binary" in runner:
        runner["runner_binary"] = str(
            workflow.engine._resolve_executable(
                runner["runner_binary"], "runner_binary", path.parent
            )
        )
    if runner.get("auth_file"):
        runner["auth_file"] = str(workflow.resolve(runner["auth_file"], path.parent))
    prompt = workflow.resolve(spec["prompt"]["path"], path.parent)
    spec["prompt"]["path"] = str(prompt)
    sources.update({str(path): trial._hash(path), str(prompt): trial._hash(prompt)})
    from .experiment_extension import prompt_sources

    sources.update(
        prompt_sources(
            dict(
                id=spec["prompt"]["id"],
                source_path=str(prompt),
                text=prompt.read_text(),
            )
        )
    )
    return spec


def _worker_template(path):
    worker.WorkerConfig.load(path)
    value = deepcopy(workflow.read(path))
    for name in ("checkpoint_path", "base_model_artifact_path"):
        value[name] = str(workflow.resolve(value[name], path.parent))
    return value


def prepare(spec_path, directory, history_root=None):
    spec_path, directory = Path(spec_path).resolve(), Path(directory).resolve()
    cfg = workflow.read(spec_path)
    fields = {
        "schema_version",
        "corpus",
        "note_ids",
        "local_schema_version",
        "bootstrap_spec",
        "consolidation_spec",
        "worker_config",
    }
    policy = cfg.get("generation_policy", POLICY_V5) if isinstance(cfg, dict) else None
    if policy == POLICY_V4_ROOTS:
        fields |= {"bootstrap_hierarchy", "hdbscan_binary"}
    elif policy in (*SECTION_POLICIES, POLICY_V5):
        fields |= {"hdbscan_binary"}
    allowed_fields = (fields, fields | {"generation_policy"})
    if policy in (*SECTION_POLICIES, POLICY_V5):
        allowed_fields += (fields | {"bootstrap_hierarchy"},
                           fields | {"bootstrap_hierarchy", "generation_policy"})
    if (
        not isinstance(cfg, dict)
        or set(cfg) not in allowed_fields
        or policy not in (POLICY, POLICY_V31, *TITLE_POLICIES)
        or type(cfg["schema_version"]) is not int
        or cfg["schema_version"] != 1
        or type(cfg["local_schema_version"]) is not int
        or cfg["local_schema_version"] != 4
        or not isinstance(cfg["note_ids"], list)
        or not cfg["note_ids"]
        or any(not isinstance(n, str) or not n for n in cfg["note_ids"])
        or len(set(cfg["note_ids"])) != len(cfg["note_ids"])
    ):
        raise ValueError("invalid hierarchy generation spec")
    if directory.exists():
        raise ValueError("hierarchy destination already exists")
    corpus_path = workflow.resolve(cfg["corpus"], spec_path.parent)
    corpus = workflow.read(corpus_path)["notes"]
    notes = {row["note_id"]: row for row in corpus}
    if len(notes) != len(corpus) or set(cfg["note_ids"]) - notes.keys():
        raise ValueError("unknown or duplicate corpus note")
    originals = []
    for note_id in cfg["note_ids"]:
        seen = set()
        for entry in notes[note_id]["subjects"]:
            number = entry["number"]
            if number in seen or any(
                not p.isdigit() or int(p) < 1 for p in number.split(".")
            ):
                raise ValueError("invalid or duplicate local number")
            seen.add(number)
            if "." not in number:
                originals.append(
                    dict(
                        id=f"L{len(originals) + 1:05d}",
                        local=dict(note_id=note_id, number=number),
                        subject=entry["subject"],
                    )
                )
        if not any("." not in n for n in seen) or any(
            "." in n and n.rsplit(".", 1)[0] not in seen for n in seen
        ):
            raise ValueError("selected note requires a valid original local tree")
    sources = {
        str(spec_path): trial._hash(spec_path),
        str(corpus_path): trial._hash(corpus_path),
    }
    teacher_specs = {
        name: _teacher_spec(workflow.resolve(cfg[name], spec_path.parent), sources)
        for name in ("bootstrap_spec", "consolidation_spec")
    }
    if policy in TITLE_POLICIES:
        bootstrap = teacher_specs["bootstrap_spec"]
        if bootstrap["prompt"]["id"] != "Hierarchy-bootstrap-v133":
            raise ValueError(f"{policy} requires Hierarchy-bootstrap-v133")
        schema = bootstrap["runner"].get("output_schema")
        output_fields = {"ambiguities", "resolutions", "meaning", "title", "evidence"}
        if (
            not isinstance(schema, dict)
            or set(schema.get("properties", {})) != output_fields
            or set(schema.get("required", [])) != output_fields
        ):
            raise ValueError(f"{policy} requires the Bootstrap title output schema")
    config_path = workflow.resolve(cfg["worker_config"], spec_path.parent)
    worker_config = _worker_template(config_path)
    sources[str(config_path)] = trial._hash(config_path)
    for name in CODE_FILES:
        path = Path(__file__).with_name(name).resolve()
        sources[str(path)] = trial._hash(path)
    state = dict(
        schema_version=3,
        generation_policy=policy,
        status="bootstrap",
        definition=str(spec_path),
        corpus=str(corpus_path),
        note_ids=cfg["note_ids"],
        local_schema_version=4,
        roots=[row["local"] for row in originals],
        originals=originals,
        nodes=[],
        items={},
        vectors={},
        experiments=[],
        encodings=[],
        families=[],
        sources=sources,
        worker_config=worker_config,
        max_siblings=MAX_SIBLINGS,
        min_notes=MIN_NOTES,
        history_root=str(
            Path(history_root).resolve() if history_root else directory.parent
        ),
        **teacher_specs,
    )
    if policy in HDBSCAN_POLICIES:
        from . import hierarchy_hdbscan
        state["hdbscan_binary"] = str(workflow.resolve(cfg["hdbscan_binary"], spec_path.parent))
        if teacher_specs["consolidation_spec"]["prompt"]["id"] != "Hierarchy-consolidated-grouped-v1":
            raise ValueError(f"{policy} requires Hierarchy-consolidated-grouped-v1")
        for path in (Path(state["hdbscan_binary"]), Path(hierarchy_hdbscan.__file__)):
            sources[str(path.resolve())] = trial._hash(path)
        if policy == POLICY_V5:
            path = Path(__file__).with_name("hierarchy_generation_v5.py").resolve()
            sources[str(path)] = trial._hash(path)
    if policy in HDBSCAN_POLICIES and "bootstrap_hierarchy" in cfg:
        source_path = workflow.resolve(cfg["bootstrap_hierarchy"], spec_path.parent)
        source_state = workflow.read(source_path)
        check_state(source_state, verify_current_code=False)
        saved_bootstrap = deepcopy(source_state["bootstrap_spec"])
        saved_timeout = saved_bootstrap["runner"].get("timeout_seconds")
        timeout = teacher_specs["bootstrap_spec"]["runner"].get("timeout_seconds")
        # A longer client deadline does not change a completed meaning. Keep
        # the original producer and its actual deadline in the saved receipt.
        if (policy == POLICY_V5 and type(saved_timeout) in (int, float) and type(timeout) in (int, float)
                and math.isfinite(timeout) and 0 < saved_timeout <= timeout):
            saved_bootstrap["runner"]["timeout_seconds"] = timeout
        if (source_state["generation_policy"] not in (POLICY_V32, *SECTION_POLICIES, POLICY_V5)
                or source_state["note_ids"] != cfg["note_ids"]
                or [{k: o[k] for k in ("id", "local", "subject")}
                    for o in source_state["originals"]] != originals
                or saved_bootstrap != teacher_specs["bootstrap_spec"]
                or source_state["worker_config"] != worker_config
                or not source_state["experiments"][0].get("complete")):
            raise ValueError("V4 requires matching saved Bootstrap-v133 inputs and controls")
        state["bootstrap_hierarchy"] = str(source_path)
        sources[str(source_path)] = trial._hash(source_path)
        state["experiments"] = [deepcopy(source_state["experiments"][0])]
        state["encodings"] = deepcopy([
            e for e in source_state["encodings"] if policy != POLICY_V5 or e.get("complete")])
        state["vectors"] = deepcopy(source_state["vectors"])
        if policy != POLICY_V5:
            for o in source_state["originals"]:
                if o.get("meaning") is not None:
                    key = _vector_key(dict(subject=o["title"], meaning=o["meaning"]))
                    if key not in state["vectors"]:
                        raise ValueError("saved Bootstrap-v133 original vector is missing")
        directory.mkdir(parents=True)
        workflow.write(directory / "state.json", state)
        return summary(state)
    directory.mkdir(parents=True)
    source = dict(
        schema_version=4,
        corpus=str(corpus_path),
        nodes=[dict(id=row["id"], local=row["local"], review={}) for row in originals],
    )
    _experiment(
        directory,
        state,
        "bootstrap",
        state["bootstrap_spec"],
        source,
        "hierarchy_local_nodes",
    )
    workflow.write(directory / "state.json", state)
    return summary(state)


def _payload(state, pair, parent):
    value = dict(
        nodes=[
            dict(
                title=state["items"][i]["subject"], meaning=state["items"][i]["meaning"]
            )
            for i in pair
        ]
    )
    if parent is not None:
        node = next(n for n in state["nodes"] if n["id"] == parent)
        value["parent"] = dict(title=node["subject"], meaning=node["meaning"])
    return value


def _vector_key(item):
    return workflow.inputs.digest(
        dict(
            text=item["subject"] + "\n\n" + item["meaning"],
            byte_spans=[[0, len(item["subject"].encode())]],
        )
    )


def _collect_experiment(record):
    with workflow.report_scope(isolated=True):
        cases = workflow.report(record["experiment"], include_request_preview=False)[
            "cases"
        ]
        if {r["id"]: r["inputs"] for r in cases} != record["inputs"]:
            raise ValueError("hierarchy experiment inputs changed")
        failures = _failure_receipts(record["experiment"], cases)
        if failures is None or any(row["status"] == "invalid_receipt" for row in cases):
            raise ValueError("invalid hierarchy receipt")
        answers = {
            row["id"]: dict(
                output=row.get("parsed"),
                receipt=row.get("receipt"),
                status=row["status"],
                error=row.get("error"),
            )
            for row in cases
        }
        for row in cases:
            if row.get('diagnostic_errors'):
                answers[row['id']]['diagnostic_errors'] = row['diagnostic_errors']
        for identifier, prior in record.get("answers", {}).items():
            if prior["status"] == "valid" and prior != answers[identifier]:
                raise ValueError("saved hierarchy answer changed")
        record["answers"] = answers
        record["complete"] = all(row["status"] == "valid" for row in cases)


def _prepare_encoding(directory, state, ids):
    missing = {}
    assigned = {
        key for job in state["encodings"] if not job.get("skipped")
        for key in job["keys"]
    }
    for identifier in ids:
        item = state["items"][identifier]
        key = _vector_key(item)
        item["vector_key"] = key
        if key not in state["vectors"] and key not in assigned:
            missing.setdefault(key, item)
    if not missing:
        return
    destination = directory / f"encoding-{len(state['encodings']):05d}"
    destination.mkdir(exist_ok=True)
    notes = []
    for key, item in missing.items():
        text = item["subject"] + "\n\n" + item["meaning"]
        notes.append(
            dict(
                note_id=key,
                text=text,
                subjects=[
                    dict(
                        subject_id=key[:16],
                        byte_spans=[[0, len(item["subject"].encode())]],
                    )
                ],
            )
        )
    request = dict(
        schema_version=1, proposal_sha256=workflow.inputs.digest(notes), notes=notes
    )
    trial._save_once(destination / "request.json", request)
    settings = dict(
        state["worker_config"],
        request_path=str(destination / "request.json"),
        request_sha256=trial._hash(destination / "request.json"),
        output_path=str(destination / "worker-result"),
    )
    trial._save_once(destination / "worker-config.json", settings)
    worker.WorkerConfig.load(destination / "worker-config.json")
    worker._load_request(destination / "request.json")
    state["encodings"].append(
        dict(
            config=str(destination / "worker-config.json"),
            config_sha256=trial._hash(destination / "worker-config.json"),
            worker_sha256=state["sources"][str(Path(worker.__file__).resolve())],
            keys=list(missing),
            complete=False,
        )
    )


def _encoding_result(state, index):
    job = state["encodings"][index]
    config_path = Path(job["config"])
    if trial._hash(config_path) != job["config_sha256"]:
        raise ValueError("hierarchy worker config changed")
    config = worker.WorkerConfig.load(config_path)
    if trial._hash(config.request_path) != config.request_sha256:
        raise ValueError("hierarchy worker request changed")
    if not config.output_path.exists():
        if job["complete"]:
            raise ValueError("saved hierarchy vectors missing")
        return None
    receipt_path = config.output_path / "worker-receipt.json"
    raw_path = config.output_path / "raw-vectors.f32le"
    receipt = workflow.read(receipt_path)
    if (
        receipt["request_sha256"] != config.request_sha256
        or receipt["checkpoint_sha256"] != config.checkpoint_sha256
        or receipt["base_model_artifact_tree_sha256"]
        != config.base_model_artifact_tree_sha256
        or receipt["model"] != config.model.to_json()
        or receipt["runtime"]["worker_sha256"] != job["worker_sha256"]
        or receipt["dimensions"] != config.model.dimensions
        or receipt["row_count"] != len(job["keys"])
        or receipt["vector_format"] != worker.VECTOR_FORMAT
    ):
        raise ValueError("hierarchy worker receipt identity differs")
    _, notes = worker._load_request(config.request_path)
    expected = [
        (row.note_id, subject.subject_id) for row in notes for subject in row.subjects
    ]
    actual = [(r["note_id"], r["subject_id"]) for r in receipt["rows"]]
    if actual != expected or [row[0] for row in expected] != job["keys"]:
        raise ValueError("hierarchy worker row identity differs")
    raw = raw_path.read_bytes()
    checksum = workflow.engine._sha256_bytes(raw)
    if (
        checksum != receipt["files"][raw_path.name]["sha256"]
        or len(raw) != len(expected) * config.model.dimensions * 4
        or receipt["files"][raw_path.name]["bytes"] != len(raw)
    ):
        raise ValueError("hierarchy vector hash or shape differs")
    receipt_hash = trial._hash(receipt_path)
    if job.get("receipt_sha256", receipt_hash) != receipt_hash:
        raise ValueError("saved hierarchy worker receipt changed")
    return receipt_hash, tuple(
        struct.iter_unpack("<" + "f" * config.model.dimensions, raw)
    )


def _collect_encodings(state):
    for index, job in enumerate(state["encodings"]):
        result = _encoding_result(state, index)
        if result is None:
            continue
        receipt_hash, rows = result
        for ordinal, (key, vector) in enumerate(zip(job["keys"], rows, strict=True)):
            if not all(math.isfinite(v) for v in vector) or not any(vector):
                raise ValueError("invalid or zero hierarchy SSE vector")
            reference = dict(encoding=index, ordinal=ordinal)
            if state["vectors"].get(key, reference) != reference:
                raise ValueError("conflicting hierarchy vector reference")
            state["vectors"][key] = reference
        job.update(complete=True, receipt_sha256=receipt_hash)


def _skip_unused_encodings(state):
    needed = set()
    for family in state["families"]:
        if family["complete"]:
            continue
        for identifier in family["current"]:
            item = state["items"][identifier]
            if len(family["current"]) > state["max_siblings"] or not item.get("pair"):
                needed.add(item["vector_key"])
    needed.difference_update(state["vectors"])
    for job in state["encodings"]:
        if not job["complete"] and not needed.intersection(job["keys"]):
            job["skipped"] = "no further pairing"


def _rank_pairs(vectors, directory):
    """Score every distinct pair once; spill sorting to bound pair memory."""
    normalized = []
    dimensions = len(vectors[0]) if vectors else 0
    for vector in vectors:
        if len(vector) != dimensions or not all(math.isfinite(v) for v in vector):
            raise ValueError("invalid hierarchy SSE vector dimensions")
        norm = math.sqrt(sum(v * v for v in vector))
        if not norm:
            raise ValueError("zero hierarchy SSE vector")
        normalized.append(tuple(v / norm for v in vector))
    record = struct.Struct("<dII")
    with tempfile.TemporaryDirectory(prefix=".cosine-pairs-", dir=directory) as name:
        root = Path(name)
        chunks, chunk = [], []
        file_numbers = count()

        def write_chunk(values):
            path = root / f"{next(file_numbers):08d}.bin"
            with path.open("xb") as stream:
                for value in values:
                    stream.write(record.pack(*value))
            return path

        def rows(stream):
            while data := stream.read(record.size * 4096):
                yield from record.iter_unpack(data)

        for a, va in enumerate(normalized):
            for b in range(a + 1, len(normalized)):
                score = max(
                    -1.0,
                    min(
                        1.0, sum(x * y for x, y in zip(va, normalized[b], strict=True))
                    ),
                )
                chunk.append((-score, a, b))
                if len(chunk) == PAIR_CHUNK_ROWS:
                    chunks.append(write_chunk(sorted(chunk)))
                    chunk = []
        if chunk:
            chunks.append(write_chunk(sorted(chunk)))
        # Bound open files as well as sort memory for larger exact pair sets.
        while len(chunks) > PAIR_MERGE_FANIN:
            merged = []
            for start in range(0, len(chunks), PAIR_MERGE_FANIN):
                group = chunks[start : start + PAIR_MERGE_FANIN]
                with ExitStack() as stack:
                    merged.append(
                        write_chunk(
                            heapq.merge(
                                *[
                                    rows(stack.enter_context(path.open("rb")))
                                    for path in group
                                ]
                            )
                        )
                    )
                for path in group:
                    path.unlink()
            chunks = merged
        selected, used = [], set()
        with ExitStack() as stack:
            ordered = heapq.merge(
                *[rows(stack.enter_context(path.open("rb"))) for path in chunks]
            )
            for score, a, b in ordered:
                if a not in used and b not in used:
                    selected.append((a, b, -score))
                    used.update((a, b))
                    if len(used) >= len(vectors) - 1:
                        break
        return selected


def _vectors(state, ids):
    batches = {}
    vectors = []
    for identifier in ids:
        reference = state["vectors"][state["items"][identifier]["vector_key"]]
        index = reference["encoding"]
        if index not in batches:
            batches[index] = _encoding_result(state, index)[1]
        vectors.append(batches[index][reference["ordinal"]])
    return vectors


def _pairs(state, ids, directory):
    return [(ids[a], ids[b], score)
            for a, b, score in _rank_pairs(_vectors(state, ids), directory)]


def _children(item):
    return item.get("pair") or item.get("group")


def _new_family(state, parent, ids):
    state["families"].append(
        dict(
            id=f"F{len(state['families']):05d}",
            parent=parent,
            original_ids=list(ids),
            current=list(ids),
            rounds=[],
            complete=False,
        )
    )


def _applied_rounds(family):
    rounds = family["rounds"]
    return rounds[:-1] if family.get("pending") is not None else rounds


def _pairing_round(state, family, pairs):
    cutoff = None
    if state["generation_policy"] in (POLICY_V31, POLICY_V32):
        cutoff = 0.40 + (0.66 - 0.40) * 0.5 ** len(family["rounds"])
    cases = {
        f"{family['id']}-P{index:05d}": [a, b]
        for index, (a, b, score) in enumerate(pairs)
        if cutoff is None or score >= cutoff
    }
    paired = {i for a, b, score in pairs for i in (a, b)}
    result = dict(
        current=list(family["current"]),
        comparisons=len(family["current"]) * (len(family["current"]) - 1) // 2,
        pairs=[dict(nodes=[a, b], cosine=score) for a, b, score in pairs],
        cases=cases,
        unpaired=[i for i in family["current"] if i not in paired],
    )
    if cutoff is not None:
        result["cutoff"] = cutoff
    return result


def _promote(state, family):
    for identifier in family["current"]:
        item = state["items"][identifier]
        node = dict(
            id=f"C{len(state['nodes']) + 1:05d}",
            subject=item["subject"],
            meaning=item["meaning"],
            item=identifier,
            family=family["id"],
            original_ids=item["original_ids"],
            entries=[
                state["originals"][int(i[1:]) - 1]["local"]
                for i in item["original_ids"]
            ],
            parents=[] if family["parent"] is None else [family["parent"]],
        )
        producer = item["producer"]
        experiment = state["experiments"][producer["experiment"]]
        answer = experiment["answers"][producer["case"]]
        node["synthetic" if _children(item) else "bootstrap"] = dict(
            experiment=experiment["experiment"],
            case=producer["case"],
            receipt=answer["receipt"],
        )
        state["nodes"].append(node)
        if (state["generation_policy"] != POLICY_V4_ROOTS
                and len({entry["note_id"] for entry in node["entries"]}) > state["min_notes"]):
            _new_family(state, node["id"], item["original_ids"])
    family["complete"] = True


def _schedule_v41(directory, state):
    from . import hierarchy_hdbscan

    family = state["families"][0]
    if family["complete"] or state["status"] == "blocked_hdbscan":
        return
    if not family["rounds"]:
        ids = family["current"]
        if any(state["items"][i]["vector_key"] not in state["vectors"] for i in ids):
            return
        round_ = hierarchy_hdbscan.round_for(directory, state, family, _vectors(state, ids))
        family["rounds"].append(dict(round_, experiment=None))
        try:
            plan = hierarchy_hdbscan.plan_for(state, round_, _vectors(state, ids))
        except ValueError as error:
            state.update(status="blocked_hdbscan", unresolved=[dict(
                role="hdbscan", error=str(error), result=round_["hdbscan"]["result"])])
            return
        state["hdbscan_sections"] = plan
    plan = state["hdbscan_sections"]
    sections = plan["sections"]
    by_cluster = {s["cluster_id"]: s for s in sections}
    node_ids = {s["cluster_id"]: f"C{i+1:05d}" for i, s in enumerate(sections)}
    nodes = {n["id"]: n for n in state["nodes"]}
    # Each section is independently ready when all of its own children are valid.
    # An unrelated unrun/failed group must not delay it.
    for section in sections:
        if "item" in section or "producer" not in section:
            continue
        producer = section["producer"]
        record = state["experiments"][producer["experiment"]]
        answer = record.get("answers", {}).get(producer["case"], {})
        if answer.get("status") != "valid":
            continue
        group = section["group"] or [by_cluster[c]["item"] for c in section["children"]]
        identifier = f"T{len(state['items']):06d}"
        value = answer["output"]
        item = dict(subject=value["title"], meaning=value["meaning"], group=group,
                    parent=None, original_ids=section["original_ids"], producer=producer)
        state["items"][identifier] = item
        section["item"] = identifier
        node_id = node_ids[section["cluster_id"]]
        node = dict(
            id=node_id, subject=item["subject"], meaning=item["meaning"],
            item=identifier, family=family["id"], section=section["cluster_id"],
            original_ids=item["original_ids"], parents=[],
            entries=[state["originals"][int(i[1:])-1]["local"] for i in item["original_ids"]],
            synthetic=dict(experiment=record["experiment"], case=producer["case"],
                           receipt=answer["receipt"]))
        state["nodes"].append(node)
        nodes[node_id] = node
        for child in section["children"]:
            nodes[node_ids[child]]["parents"] = [node_id]
    requests, ready = [], []
    for section in sections:
        if "producer" in section:
            continue
        if any("item" not in by_cluster[c] for c in section["children"]):
            continue
        group = section["group"] or [by_cluster[c]["item"] for c in section["children"]]
        case = f"H{section['cluster_id']:06d}"
        requests.append(dict(id=case,
                             inputs={"INPUT_JSON": json.dumps(_payload(state, group, None),
                                                               ensure_ascii=False)},
                             evidence=dict(section=section["cluster_id"],
                                           original_ids=section["original_ids"])))
        ready.append((section, case))
    if requests:
        producer = _experiment(directory, state, "consolidation", state["consolidation_spec"],
                               dict(cases=requests), "hierarchy_group_consolidation")
        for section, case in ready:
            section["producer"] = dict(experiment=producer, case=case)
    if all("item" in s for s in sections):
        family["current"] = [by_cluster[c]["item"] for c in plan["roots"]]
        family["complete"] = True
        state["status"] = "complete"


def _schedule(directory, state):
    bootstrap = state["experiments"][0]
    if not bootstrap.get("complete"):
        return
    if not state["items"]:
        unresolved = []
        for original in state["originals"]:
            answer = bootstrap["answers"][original["id"]]
            meaning = answer["output"]["meaning"]
            original["meaning"] = meaning
            if state["generation_policy"] in TITLE_POLICIES:
                original["title"] = answer["output"]["title"]
            if meaning is None:
                unresolved.append(
                    dict(
                        local=original["local"],
                        case=original["id"],
                        experiment=bootstrap["experiment"],
                        reason="null Bootstrap meaning",
                    )
                )
        represented = {
            original["local"]["note_id"]
            for original in state["originals"]
            if original["meaning"] is not None
        }
        if (not represented or state["generation_policy"] != POLICY_V5
                and set(state["note_ids"]) - represented):
            state.update(
                status="blocked_bootstrap",
                unresolved=[
                    row for row in unresolved if row["local"]["note_id"] not in represented
                ],
            )
            return
        for original in state["originals"]:
            if original["meaning"] is None:
                continue
            state["items"][original["id"]] = dict(
                subject=(
                    original["title"]
                    if state["generation_policy"] in TITLE_POLICIES
                    else original["subject"]
                ),
                meaning=original["meaning"],
                original_ids=[original["id"]],
                producer=dict(experiment=0, case=original["id"]),
            )
        _new_family(state, None, list(state["items"]))
        state.update(status="constructing", unresolved=[])
        # Original vectors are frozen once, even if a small initial set needs no consolidation.
        _prepare_encoding(directory, state, list(state["items"]))
    if state["generation_policy"] in SECTION_POLICIES:
        _schedule_v41(directory, state)
        return
    if state["generation_policy"] == POLICY_V5:
        from . import hierarchy_generation_v5
        hierarchy_generation_v5.schedule(directory, state)
        return
    while True:
        changed = False
        ready = []
        requests = []
        for family in list(state["families"]):
            if family["complete"]:
                continue
            if family.get("pending") is not None:
                record = state["experiments"][family["pending"]]
                if not all(
                    record.get("answers", {}).get(case, {}).get("status") == "valid"
                    for case in family["rounds"][-1]["cases"]
                ):
                    continue
                current = []
                for case, pair in family["rounds"][-1]["cases"].items():
                    value = record["answers"][case]["output"]
                    identifier = f"T{len(state['items']):06d}"
                    originals = sorted(
                        i
                        for child in pair
                        for i in state["items"][child]["original_ids"]
                    )
                    state["items"][identifier] = dict(
                        subject=value["title"],
                        meaning=value["meaning"],
                        **({"group": pair} if state["generation_policy"] == POLICY_V4_ROOTS
                           else {"pair": pair}),
                        parent=family["parent"],
                        original_ids=originals,
                        producer=dict(experiment=family["pending"], case=case),
                    )
                    current.append(identifier)
                current.extend(family["rounds"][-1]["unpaired"])
                family["current"] = current
                del family["pending"]
                changed = True
            ids = family["current"]
            if (len(ids) <= state["max_siblings"]
                    and (state["generation_policy"] != POLICY_V4_ROOTS or family["rounds"])):
                originals = [i for i in ids if not _children(state["items"][i])]
                _prepare_encoding(directory, state, originals)
                if any(state["items"][i]["vector_key"] not in state["vectors"] for i in originals):
                    continue
                _promote(state, family)
                changed = True
                continue
            _prepare_encoding(directory, state, ids)
            if any(
                state["items"][i]["vector_key"] not in state["vectors"] for i in ids
            ):
                continue
            if state["generation_policy"] == POLICY_V4_ROOTS:
                from . import hierarchy_hdbscan
                round_ = hierarchy_hdbscan.round_for(directory, state, family, _vectors(state, ids))
            else:
                pairs = _pairs(state, ids, directory)
                round_ = _pairing_round(state, family, pairs)
            cases = round_["cases"]
            if not cases:
                family["rounds"].append(dict(round_, experiment=None))
                family["current"] = round_["unpaired"]
                changed = True
                continue
            requests.extend(
                dict(
                    id=case,
                    inputs={
                        "INPUT_JSON": json.dumps(
                            _payload(state, pair, family["parent"]),
                            ensure_ascii=False,
                        )
                    },
                    evidence=dict(
                        family=family["id"],
                        original_ids=sorted(
                            i
                            for child in pair
                            for i in state["items"][child]["original_ids"]
                        ),
                    ),
                )
                for case, pair in cases.items()
            )
            ready.append((family, round_))
        if ready:
            producer = _experiment(
                directory,
                state,
                "consolidation",
                state["consolidation_spec"],
                dict(cases=requests),
                ("hierarchy_group_consolidation" if state["generation_policy"] == POLICY_V4_ROOTS
                 else "hierarchy_pair_consolidation"),
            )
            for family, round_ in ready:
                family["rounds"].append(dict(round_, experiment=producer))
                family["pending"] = producer
        if not changed:
            break
    if all(family["complete"] for family in state["families"]):
        state["status"] = "complete"


def _check_v41(state):
    from . import hierarchy_hdbscan

    if not state["families"]:
        if state.get("hdbscan_sections") is not None or state["nodes"]:
            raise ValueError("HDBSCAN sections appeared before Bootstrap")
        return
    family = state["families"][0]
    if not family["rounds"]:
        if state.get("hdbscan_sections") is not None or state["nodes"] or family["complete"]:
            raise ValueError("HDBSCAN sections appeared before clustering")
        return
    if len(family["rounds"]) != 1 or family.get("pending") is not None:
        raise ValueError("V4.1/V4.2 must keep a single HDBSCAN tree")
    round_ = family["rounds"][0]
    vectors = _vectors(state, round_["current"])
    hierarchy_hdbscan.check_round(state, family, round_, vectors)
    originals = [o["id"] for o in state["originals"] if o.get("meaning") is not None]
    if family["original_ids"] != originals or round_["current"] != originals:
        raise ValueError("HDBSCAN original input inventory changed")
    try:
        expected = hierarchy_hdbscan.plan_for(state, round_, vectors)
    except ValueError as error:
        if (state["status"] != "blocked_hdbscan" or state.get("hdbscan_sections") is not None
                or state["nodes"] or family["complete"] or family["current"] != originals
                or set(state["items"]) != set(originals) or len(state["experiments"]) != 1
                or state["unresolved"] != [dict(role="hdbscan", error=str(error),
                                              result=round_["hdbscan"]["result"])]):
            raise ValueError("HDBSCAN section blockage differs from saved evidence") from error
        return
    plan = state["hdbscan_sections"]
    if (set(plan) != set(expected) or plan["roots"] != expected["roots"]
            or plan["cuts"] != expected["cuts"] or len(plan["sections"]) != len(expected["sections"])):
        raise ValueError("saved HDBSCAN section cuts changed")
    by_cluster = {s["cluster_id"]: s for s in plan["sections"]}
    node_ids = {s["cluster_id"]: f"C{i+1:05d}" for i, s in enumerate(plan["sections"])}
    parents = {c: s["cluster_id"] for s in plan["sections"] for c in s["children"]}
    nodes = {n["id"]: n for n in state["nodes"]}
    if len(nodes) != len(state["nodes"]):
        raise ValueError("duplicate HDBSCAN section node")
    produced, cases = set(), set()
    for section, frozen in zip(plan["sections"], expected["sections"], strict=True):
        if (set(section) - set(frozen) - {"producer", "item"}
                or any(section.get(k) != v for k, v in frozen.items())):
            raise ValueError("saved HDBSCAN section membership changed")
        producer = section.get("producer")
        if producer is not None:
            index, case = producer["experiment"], producer["case"]
            if (type(index) is not int or not 1 <= index < len(state["experiments"])
                    or case != f"H{section['cluster_id']:06d}"
                    or any("item" not in by_cluster[c] for c in section["children"])):
                raise ValueError("invalid HDBSCAN section producer")
            group = section["group"] or [by_cluster[c]["item"] for c in section["children"]]
            record = state["experiments"][index]
            if (record["role"] != "consolidation" or case not in record["inputs"]
                    or json.loads(record["inputs"][case]["INPUT_JSON"]) != _payload(state, group, None)):
                raise ValueError("HDBSCAN section input differs from native producer")
            cases.add((index, case))
        if "item" not in section:
            continue
        if producer is None or section["item"] in produced:
            raise ValueError("invalid HDBSCAN section item")
        produced.add(section["item"])
        item = state["items"][section["item"]]
        if item["producer"] != producer or item.get("parent") is not None or item["group"] != group:
            raise ValueError("HDBSCAN section item differs from its children")
        node = nodes.get(node_ids[section["cluster_id"]])
        parent = parents.get(section["cluster_id"])
        placement = ([node_ids[parent]] if parent is not None and "item" in by_cluster[parent] else [])
        if (node is None or node.get("section") != section["cluster_id"]
                or node["item"] != section["item"] or node["parents"] != placement
                or node["family"] != family["id"]):
            raise ValueError("canonical placement differs from HDBSCAN section")
    if (len(state["nodes"]) != len(produced) or set(state["items"]) != set(originals) | produced
            or cases != {(i, c) for i, r in enumerate(state["experiments"]) if i
                         for c in r["inputs"]}):
        raise ValueError("unexpected HDBSCAN section items or producers")
    finished = all("item" in s for s in plan["sections"])
    current = [by_cluster[c]["item"] for c in plan["roots"]] if finished else originals
    if (family["complete"] != finished or family["current"] != current
            or (state["status"] == "complete") != finished):
        raise ValueError("HDBSCAN section completion state changed")


def check_state(state, *, verify_receipts=True, verify_current_code=True):
    if (state.get("generation_policy") not in (POLICY, POLICY_V31, *TITLE_POLICIES)
            or state.get("schema_version") != 3):
        raise ValueError("unknown hierarchy generation policy")
    for path, digest in state["sources"].items():
        if trial._hash(path) != digest:
            raise ValueError("hierarchy source changed: " + path)
    if not verify_current_code and any(
        sum(Path(path).name == name and Path(path).parent.name == "sse_multivector"
            for path in state["sources"]) != 1
        for name in CODE_FILES
    ):
        raise ValueError("invalid hierarchy construction source bindings")
    if verify_current_code and any(
        str(Path(__file__).with_name(name).resolve()) not in state["sources"]
        for name in CODE_FILES
    ):
        raise ValueError(
            "hierarchy construction source binding changed; use a reviewed upgrade reason"
        )
    definition = Path(state["definition"])
    cfg = workflow.read(definition)
    if (
        state["generation_policy"] != cfg.get("generation_policy",
            POLICY_V5 if state["generation_policy"] == POLICY_V5 else POLICY)
        or state["max_siblings"] != MAX_SIBLINGS
        or state["min_notes"] != MIN_NOTES
        or state["note_ids"] != cfg["note_ids"]
        or state["local_schema_version"] != cfg["local_schema_version"]
        or state["corpus"] != str(workflow.resolve(cfg["corpus"], definition.parent))
        or state["worker_config"]
        != _worker_template(workflow.resolve(cfg["worker_config"], definition.parent))
        or any(
            state[name]
            != _teacher_spec(workflow.resolve(cfg[name], definition.parent), {})
            for name in ("bootstrap_spec", "consolidation_spec")
        )
    ):
        raise ValueError("saved controls differ from frozen hierarchy definition")
    if state["generation_policy"] in HDBSCAN_POLICIES:
        from . import hierarchy_hdbscan
        expected_source = (str(workflow.resolve(cfg["bootstrap_hierarchy"], definition.parent))
                           if "bootstrap_hierarchy" in cfg else None)
        if (state.get("bootstrap_hierarchy") != expected_source
                or state["hdbscan_binary"] != str(workflow.resolve(cfg["hdbscan_binary"], definition.parent))
                or (verify_current_code and
                    str(Path(hierarchy_hdbscan.__file__).resolve()) not in state["sources"])
                or (not verify_current_code and
                    sum(Path(p).name == "hierarchy_hdbscan.py" for p in state["sources"]) != 1)
                or (state["generation_policy"] != POLICY_V5 and (
                    len(state["families"]) > 1
                    or any(f["parent"] is not None for f in state["families"])))):
            raise ValueError("V4 root-test controls or scope changed")
        if expected_source is not None:
            source = workflow.read(expected_source)
            saved_encodings = [e for e in source["encodings"]
                               if state["generation_policy"] != POLICY_V5 or e.get("complete")]
            if (state["experiments"][0] != source["experiments"][0]
                    or state["encodings"][:len(saved_encodings)] != saved_encodings
                    or (state["generation_policy"] in SECTION_POLICIES and (
                        state["encodings"] != source["encodings"] or state["vectors"] != source["vectors"]))):
                raise ValueError("reused Bootstrap or encoder producer changed")
    trial._ancestors(state["nodes"])
    originals = {r["id"]: r for r in state["originals"]}
    if len(originals) != len(state["originals"]):
        raise ValueError("duplicate original local L1 identity")
    notes = {n["note_id"]: n for n in workflow.read(state["corpus"])["notes"]}
    expected = [
        dict(
            id=f"L{index + 1:05d}",
            local=dict(note_id=note_id, number=entry["number"]),
            subject=entry["subject"],
        )
        for index, (note_id, entry) in enumerate(
            (note_id, entry)
            for note_id in state["note_ids"]
            for entry in notes[note_id]["subjects"]
            if "." not in entry["number"]
        )
    ]
    if [
        {k: row[k] for k in ("id", "local", "subject")} for row in state["originals"]
    ] != expected:
        raise ValueError("original local L1 inventory differs from frozen corpus")
    if state["roots"] != [row["local"] for row in state["originals"]]:
        raise ValueError("original root references changed")
    for row in state["originals"]:
        if state["families"] and "meaning" not in row:
            raise ValueError("original meaning missing after Bootstrap")
        if state["families"] and (
            state["experiments"][0].get("answers", {}).get(row["id"], {}).get("status")
            != "valid"
        ):
            raise ValueError("original Bootstrap answer is not valid")
        if "meaning" in row and row["meaning"] != (
            state["experiments"][0].get("answers", {}).get(row["id"], {}).get("output")
            or {}
        ).get("meaning"):
            raise ValueError("original meaning differs from native Bootstrap")
        if state["generation_policy"] in TITLE_POLICIES and "meaning" in row:
            answer = state["experiments"][0].get("answers", {}).get(row["id"], {})
            if "title" not in row or row["title"] != (answer.get("output") or {}).get("title"):
                raise ValueError("original title differs from native Bootstrap")
    for identifier, item in state["items"].items():
        if _children(item):
            pair = _children(item)
            if (
                len(pair) < 2
                or (state["generation_policy"] not in HDBSCAN_POLICIES and len(pair) != 2)
                or len(set(pair)) != len(pair)
                or any(i not in state["items"] for i in pair)
            ):
                raise ValueError("invalid synthetic original association")
            expected = sorted(
                i for child in pair for i in state["items"][child]["original_ids"]
            )
        else:
            expected = [identifier]
            if (
                identifier not in originals
                or item["subject"] != originals[identifier][
                    "title" if state["generation_policy"] in TITLE_POLICIES else "subject"
                ]
            ):
                raise ValueError("invalid original local L1 item")
        if item["original_ids"] != expected or len(set(expected)) != len(expected):
            raise ValueError("synthetic original L1 associations changed")
        if item.get("vector_key", _vector_key(item)) != _vector_key(item):
            raise ValueError("item encoding identity differs")
        producer = item["producer"]
        record = state["experiments"][producer["experiment"]]
        answer = record.get("answers", {}).get(producer["case"], {})
        value = answer.get("output") or {}
        if answer.get("status") != "valid" or value.get("meaning") != item["meaning"]:
            raise ValueError("item meaning differs from native producer")
        if _children(item):
            if value.get("title") != item["subject"] or json.loads(
                record["inputs"][producer["case"]]["INPUT_JSON"]
            ) != _payload(state, _children(item), item["parent"]):
                raise ValueError("synthetic input differs from native producer")
    for node in state["nodes"]:
        item = state["items"][node["item"]]
        if any(
            node[k] != item[k] for k in ("subject", "meaning", "original_ids")
        ) or node["entries"] != [originals[i]["local"] for i in item["original_ids"]]:
            raise ValueError("canonical node differs from final construction item")
        if state["generation_policy"] in (*SECTION_POLICIES, POLICY_V5):
            continue
        family = next(f for f in state["families"] if f["id"] == node["family"])
        if (
            not family["complete"]
            or node["item"] not in family["current"]
            or node["parents"]
            != ([] if family["parent"] is None else [family["parent"]])
        ):
            raise ValueError("canonical placement differs from family construction")
    by_id = {n["id"]: n for n in state["nodes"]}
    if state["generation_policy"] in SECTION_POLICIES:
        _check_v41(state)
    elif state["generation_policy"] == POLICY_V5:
        from . import hierarchy_generation_v5
        hierarchy_generation_v5.check_state(state, verify_current_code=verify_current_code)
    for family in state["families"]:
        if state["generation_policy"] in (*SECTION_POLICIES, POLICY_V5):
            continue
        expected = (
            [
                identifier
                for identifier, row in originals.items()
                if row.get("meaning") is not None
            ]
            if family["parent"] is None
            else by_id[family["parent"]]["original_ids"]
        )
        members = [
            i
            for item in family["current"]
            for i in state["items"][item]["original_ids"]
        ]
        discarded = []
        if state["generation_policy"] in (POLICY_V31, POLICY_V32):
            for index, round_ in enumerate(family["rounds"]):
                pairs = [(p["nodes"][0], p["nodes"][1], p["cosine"])
                         for p in round_["pairs"]]
                paired = [i for a, b, score in pairs for i in (a, b)]
                if (len(pairs) != len(round_["current"]) // 2
                        or len(paired) != len(set(paired))
                        or set(paired) - set(round_["current"])
                        or any(not math.isfinite(score) or not -1 <= score <= 1
                               for a, b, score in pairs)):
                    raise ValueError("invalid hierarchy cosine pairs")
                controls = _pairing_round(state, dict(
                    id=family["id"], current=round_["current"],
                    rounds=family["rounds"][:index],
                ), pairs)
                if any(round_.get(k) != v for k, v in controls.items()):
                    raise ValueError("saved cutoff or selected pairs changed")
            discarded = [
                original for round_ in _applied_rounds(family)
                for pair in round_["pairs"] if pair["cosine"] < round_["cutoff"]
                for item in pair["nodes"]
                for original in state["items"][item]["original_ids"]
            ]
        if state["generation_policy"] == POLICY_V4_ROOTS:
            from . import hierarchy_hdbscan
            for round_ in family["rounds"]:
                hierarchy_hdbscan.check_round(state, family, round_, _vectors(state, round_["current"]))
            discarded = [
                o for round_ in _applied_rounds(family) for i in round_["unassigned"]
                for o in state["items"][i]["original_ids"]]
        if (
            family["original_ids"] != expected
            or sorted(members + discarded) != sorted(expected)
            or len(members + discarded) != len(set(members + discarded))
        ):
            raise ValueError("family original L1 membership changed")
        if family["complete"] and len(family["current"]) > state["max_siblings"]:
            raise ValueError("canonical family exceeds maximum siblings")
    if state["status"] == "complete":
        represented = {
            entry["note_id"] for node in state["nodes"] for entry in node["entries"]
        }
        if (represented - set(state["note_ids"])
                or (state["generation_policy"] == POLICY
                    and represented != set(state["note_ids"]))):
            raise ValueError("completed hierarchy omits selected notes")
        parents = {p for node in state["nodes"] for p in node["parents"]}
        if not all(f["complete"] for f in state["families"]) or (state["generation_policy"] not in HDBSCAN_POLICIES and any(
            len({e["note_id"] for e in node["entries"]}) > state["min_notes"]
            for node in state["nodes"]
            if node["id"] not in parents
        )):
            raise ValueError("completed hierarchy has unfinished branches")
    if verify_receipts:
        with workflow.report_scope():
            for record in state["experiments"]:
                _collect_experiment(deepcopy(record))
            for index in range(len(state["encodings"])):
                _encoding_result(state, index)


def advance(directory, comment):
    if not isinstance(comment, str) or not comment.strip():
        raise ValueError("an advancement comment is required")
    directory = Path(directory).resolve()
    with workflow.locked(directory), workflow.report_scope():
        state = workflow.read(directory / "state.json")
        check_state(state, verify_receipts=False)
        before = deepcopy(state)
        for record in state["experiments"]:
            _collect_experiment(record)
        _collect_encodings(state)
        _schedule(directory, state)
        _skip_unused_encodings(state)
        check_state(state, verify_receipts=False)
        if state != before:
            workflow.write(directory / "state.json", state)
        return summary(state)


def _resume_sources(directory, reason):
    if reason is None:
        return
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("runner upgrade reason must be nonempty")
    from experiment_runner.scheduling import snapshot

    with workflow.locked(directory):
        state = workflow.read(directory / "state.json")
        names = CODE_FILES + (('hierarchy_hdbscan.py',)
                              if state['generation_policy'] in HDBSCAN_POLICIES else ())
        if state['generation_policy'] == POLICY_V5:
            names += ('hierarchy_generation_v5.py',)
        bound = {
            name: [
                p
                for p in state["sources"]
                if Path(p).name == name and Path(p).parent.name == "sse_multivector"
            ]
            for name in names
        }
        if any(len(paths) != 1 for paths in bound.values()):
            raise ValueError("invalid hierarchy construction source bindings")
        allowed = {paths[0] for paths in bound.values()}
        for path, digest in state["sources"].items():
            if path not in allowed and trial._hash(path) != digest:
                raise ValueError("frozen hierarchy input changed: " + path)
        before, after = {}, {}
        for name, paths in bound.items():
            old = paths[0]
            new = str(Path(__file__).with_name(name).resolve())
            digest = trial._hash(new)
            if old != new or state["sources"][old] != digest:
                before[old] = state["sources"][old]
                after[new] = digest
        if not after:
            return
        for record in state["experiments"]:
            _, config, _ = workflow.load(record["experiment"])
            if snapshot(config.run_directory)["state"] in ("running", "pausing"):
                raise ValueError(
                    "finish active experiments before upgrading construction code"
                )
        state.setdefault("source_upgrades", []).append(
            dict(
                reason=reason,
                before=before,
                after=after,
                graph_sha256=workflow.inputs.digest(state["nodes"]),
            )
        )
        for path in before:
            del state["sources"][path]
        state["sources"].update(after)
        check_state(state)
        workflow.write(directory / "state.json", state)


def _pause_experiments(state):
    from experiment_runner.scheduling import snapshot, pause

    for record in state["experiments"]:
        _, config, _ = workflow.load(record["experiment"])
        if snapshot(config.run_directory)["state"] in ("running", "pausing"):
            pause(config.run_directory, reason="hierarchy execution interrupted")


def _native_command(
    directory, arguments, stop, *, pending_experiment=None, budget=None
):
    """Restart the shared CLI on recoverable failures, preserving its own retries."""
    launcher = Path(workflow.__file__).resolve().parents[1] / "bin/experiment-runner"
    project = Path(__file__).resolve().parents[1]
    logs = directory / "runner-invocations"
    logs.mkdir(exist_ok=True)
    delay = RUNNER_BACKOFF_SECONDS
    failures = 0
    while not stop.is_set():
        invocation = Path(tempfile.mkdtemp(prefix=arguments[0] + "-", dir=logs))
        with (
            (invocation / "stdout.log").open("wb") as out,
            (invocation / "stderr.log").open("wb") as err,
        ):
            process = subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "--project-root",
                    str(project),
                    *arguments,
                ],
                cwd=project,
                stdout=out,
                stderr=err,
            )
        event = dict(
            command=arguments[0],
            invocation=str(invocation),
            exit_code=process.returncode,
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        if process.returncode == 0:
            if failures:
                workflow.engine._append_json_line(
                    directory / "runner-backoff.jsonl",
                    dict(event, event="recovered", failures=failures),
                )
            return invocation
        retry = True
        if pending_experiment is not None:
            report = workflow.report(pending_experiment, include_request_preview=False)
            warmups = report.get("cache_warmup", {}).get("sources", [])
            retry = (
                any(c["status"] == "unrun" for c in report["cases"])
                and all(c["status"] in ("valid", "unrun") for c in report["cases"])
                and (not warmups or warmups[-1].get("status") != "failed")
            )
        else:
            # Advancement makes no model calls. Retry the runner only after
            # checking that its frozen inputs and existing evidence remain valid.
            check_state(workflow.read(directory / "state.json"))
        if (
            budget is not None
            and workflow.engine.PersistentAttemptBudget(budget).remaining() <= 0
        ):
            retry = False
        with (invocation / "stderr.log").open("rb") as stream:
            stream.seek(max(0, (invocation / "stderr.log").stat().st_size - 4096))
            error = stream.read().decode("utf-8", errors="replace").strip()
        event.update(error=error, event="backoff" if retry else "blocked")
        if not retry:
            workflow.engine._append_json_line(directory / "runner-backoff.jsonl", event)
            raise workflow.engine.RunnerError(
                f"shared runner exited {process.returncode}; diagnostics: {invocation}"
            )
        failures += 1
        event.update(delay_seconds=delay, failures=failures)
        workflow.engine._append_json_line(directory / "runner-backoff.jsonl", event)
        print(
            f"Hierarchy: shared runner failed; retrying in {delay:g}s; diagnostics: {invocation}",
            file=sys.stderr,
        )
        if stop.wait(delay):
            return None
        delay = min(delay * 2, RUNNER_BACKOFF_MAX_SECONDS)
    return None


def _native_advance(directory, comment, stop):
    invocation = _native_command(
        directory, ["advance-hierarchy", str(directory), "--comment", comment], stop
    )
    return (
        json.loads((invocation / "stdout.log").read_text())
        if invocation is not None
        else summary(workflow.read(directory / "state.json"))
    )


def _native_teacher(directory, experiment, budget, upgrade_reason, stop, max_provider_attempts=None):
    arguments = ["run", str(experiment)]
    if budget is not None:
        arguments.extend(["--attempt-budget", str(budget)])
    if upgrade_reason is not None:
        arguments.extend(["--runner-upgrade-reason", upgrade_reason])
    if max_provider_attempts is not None:
        arguments.extend(["--max-provider-attempts", str(max_provider_attempts)])
    return _native_command(
        directory, arguments, stop, pending_experiment=experiment, budget=budget
    )


def _start_job(function, arguments):
    """Submit ready native work immediately; the shared runner queues model calls."""
    future = Future()
    context = copy_context()

    def execute():
        if not future.set_running_or_notify_cancel():
            return
        try:
            future.set_result(context.run(function, *arguments))
        except BaseException as error:
            future.set_exception(error)

    thread = Thread(target=execute)
    thread.start()
    return future, thread


def run(
    directory,
    attempt_budget=None,
    comment="Automated hierarchy generation",
    runner_upgrade_reason=None,
    max_provider_attempts=None,
):
    """Coordinate ordinary native batches and one SSE worker; no provider limiter."""
    directory = Path(directory).resolve()
    if max_provider_attempts is not None and (type(max_provider_attempts) is not int or max_provider_attempts < 1):
        raise ValueError('max_provider_attempts must be a positive integer')
    budget = Path(attempt_budget).resolve() if attempt_budget is not None else None
    if budget is not None:
        workflow.engine.PersistentAttemptBudget(budget).remaining()
    with (directory / ".hierarchy-run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("hierarchy execution is already active") from error
        settings = dict(attempt_budget=None if budget is None else str(budget))
        if max_provider_attempts is not None:
            settings['max_provider_attempts'] = max_provider_attempts
        settings_path = directory / "execution-settings.json"
        if not settings_path.exists():
            trial._save_once(settings_path, settings)
        workflow.engine._append_json_line(
            directory / "execution-settings.jsonl",
            dict(settings, max_provider_attempts=max_provider_attempts,
                 runner_upgrade_reason=runner_upgrade_reason,
                 observed_at_utc=datetime.now(timezone.utc).isoformat()),
        )
        _resume_sources(directory, runner_upgrade_reason)
        active, attempted, errors = {}, set(), []
        stop = Event()
        result = _native_advance(directory, comment, stop)
        try:
            while True:
                jobs = [("teacher", p) for p in result["experiments"]]
                jobs.extend(("encoder", p) for p in result["encodings"])
                encoding_active = any(
                    kind == "encoder" for kind, path, thread in active.values()
                )
                if result["status"] not in ("complete", "blocked_bootstrap"):
                    for kind, path in jobs:
                        if (kind, path) in attempted:
                            continue
                        if kind == "encoder" and encoding_active:
                            continue
                        if kind == "teacher":
                            future, thread = _start_job(
                                _native_teacher,
                                (
                                    directory,
                                    Path(path),
                                    budget,
                                    runner_upgrade_reason,
                                    stop,
                                    max_provider_attempts,
                                ),
                            )
                        else:
                            future, thread = _start_job(
                                worker.run_worker, (Path(path),)
                            )
                            encoding_active = True
                        active[future] = (kind, path, thread)
                        attempted.add((kind, path))
                if not active:
                    break
                finished, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in finished:
                    kind, path, thread = active.pop(future)
                    thread.join()
                    try:
                        future.result()
                    except (
                        workflow.engine.RunnerError,
                        ValueError,
                        OSError,
                        ImportError,
                    ) as error:
                        errors.append(dict(kind=kind, path=path, error=str(error)))
                result = _native_advance(directory, comment, stop)
                print(
                    result["generation_policy"] + ": "
                    + json.dumps(
                        {
                            k: result[k]
                            for k in ("status", "canonical_nodes", "original_l1s")
                        }
                    ),
                    file=sys.stderr,
                )
        except BaseException:
            stop.set()
            for future in active:
                future.cancel()
            _pause_experiments(workflow.read(directory / "state.json"))
            raise
        finally:
            for future, (kind, path, thread) in active.items():
                thread.join()
        result = _native_advance(directory, comment, stop)
        result["execution_status"] = (
            result["status"] if result["status"] == "complete" else "blocked"
        )
        result["errors"] = errors
        workflow.write(directory / "run-summary.json", result)
        return result
