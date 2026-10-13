"""Native V3 hierarchy construction by SSE pairing and pair consolidation.

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
    return dict(
        status=state["status"],
        generation_policy=POLICY,
        canonical_nodes=len(state["nodes"]),
        original_l1s=len(state["originals"]),
        experiments=[
            r["experiment"] for r in state["experiments"] if not r.get("complete")
        ],
        encodings=[r["config"] for r in state["encodings"] if not r.get("complete")],
        unresolved=unresolved,
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
    if (
        not isinstance(cfg, dict)
        or set(cfg) != fields
        or type(cfg["schema_version"]) is not int
        or cfg["schema_version"] != 1
        or type(cfg["local_schema_version"]) is not int
        or cfg["local_schema_version"] != 4
        or not isinstance(cfg["note_ids"], list)
        or not cfg["note_ids"]
        or any(not isinstance(n, str) or not n for n in cfg["note_ids"])
        or len(set(cfg["note_ids"])) != len(cfg["note_ids"])
    ):
        raise ValueError("invalid hierarchy generation V3 spec")
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
    config_path = workflow.resolve(cfg["worker_config"], spec_path.parent)
    worker_config = _worker_template(config_path)
    sources[str(config_path)] = trial._hash(config_path)
    for name in CODE_FILES:
        path = Path(__file__).with_name(name).resolve()
        sources[str(path)] = trial._hash(path)
    state = dict(
        schema_version=3,
        generation_policy=POLICY,
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
        for identifier, prior in record.get("answers", {}).items():
            if prior["status"] == "valid" and prior != answers[identifier]:
                raise ValueError("saved hierarchy answer changed")
        record["answers"] = answers
        record["complete"] = all(row["status"] == "valid" for row in cases)


def _prepare_encoding(directory, state, ids):
    missing = {}
    assigned = {key for job in state["encodings"] for key in job["keys"]}
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


def _pairs(state, ids, directory):
    batches = {}
    vectors = []
    for identifier in ids:
        reference = state["vectors"][state["items"][identifier]["vector_key"]]
        index = reference["encoding"]
        if index not in batches:
            batches[index] = _encoding_result(state, index)[1]
        vectors.append(batches[index][reference["ordinal"]])
    return [(ids[a], ids[b], score) for a, b, score in _rank_pairs(vectors, directory)]


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
        node["synthetic" if item.get("pair") else "bootstrap"] = dict(
            experiment=experiment["experiment"],
            case=producer["case"],
            receipt=answer["receipt"],
        )
        state["nodes"].append(node)
        if len({entry["note_id"] for entry in node["entries"]}) > state["min_notes"]:
            _new_family(state, node["id"], item["original_ids"])
    family["complete"] = True


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
        if set(state["note_ids"]) - represented:
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
                subject=original["subject"],
                meaning=original["meaning"],
                original_ids=[original["id"]],
                producer=dict(experiment=0, case=original["id"]),
            )
        _new_family(state, None, list(state["items"]))
        state.update(status="constructing", unresolved=[])
        # Original vectors are frozen once, even if a small initial set needs no consolidation.
        _prepare_encoding(directory, state, list(state["items"]))
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
                        pair=pair,
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
            _prepare_encoding(directory, state, ids)
            if any(
                state["items"][i]["vector_key"] not in state["vectors"] for i in ids
            ):
                continue
            if len(ids) <= state["max_siblings"]:
                _promote(state, family)
                changed = True
                continue
            pairs = _pairs(state, ids, directory)
            cases = {
                f"{family['id']}-P{index:05d}": [a, b]
                for index, (a, b, score) in enumerate(pairs)
            }
            paired = {i for pair in cases.values() for i in pair}
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
            ready.append(
                (
                    family,
                    dict(
                        current=list(ids),
                        comparisons=len(ids) * (len(ids) - 1) // 2,
                        pairs=[
                            dict(nodes=[a, b], cosine=score) for a, b, score in pairs
                        ],
                        cases=cases,
                        unpaired=[i for i in ids if i not in paired],
                    ),
                )
            )
        if ready:
            producer = _experiment(
                directory,
                state,
                "consolidation",
                state["consolidation_spec"],
                dict(cases=requests),
                "hierarchy_pair_consolidation",
            )
            for family, round_ in ready:
                family["rounds"].append(dict(round_, experiment=producer))
                family["pending"] = producer
        if not changed:
            break
    if all(family["complete"] for family in state["families"]):
        state["status"] = "complete"


def check_state(state, *, verify_receipts=True):
    if state.get("generation_policy") != POLICY or state.get("schema_version") != 3:
        raise ValueError("unknown hierarchy generation policy")
    for path, digest in state["sources"].items():
        if trial._hash(path) != digest:
            raise ValueError("hierarchy source changed: " + path)
    if any(
        str(Path(__file__).with_name(name).resolve()) not in state["sources"]
        for name in CODE_FILES
    ):
        raise ValueError(
            "hierarchy construction source binding changed; use a reviewed upgrade reason"
        )
    definition = Path(state["definition"])
    cfg = workflow.read(definition)
    if (
        state["max_siblings"] != MAX_SIBLINGS
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
    for identifier, item in state["items"].items():
        if item.get("pair"):
            pair = item["pair"]
            if (
                len(pair) != 2
                or pair[0] == pair[1]
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
                or item["subject"] != originals[identifier]["subject"]
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
        if item.get("pair"):
            if value.get("title") != item["subject"] or json.loads(
                record["inputs"][producer["case"]]["INPUT_JSON"]
            ) != _payload(state, item["pair"], item["parent"]):
                raise ValueError("synthetic input differs from native producer")
    for node in state["nodes"]:
        item = state["items"][node["item"]]
        if any(
            node[k] != item[k] for k in ("subject", "meaning", "original_ids")
        ) or node["entries"] != [originals[i]["local"] for i in item["original_ids"]]:
            raise ValueError("canonical node differs from final construction item")
        family = next(f for f in state["families"] if f["id"] == node["family"])
        if (
            not family["complete"]
            or node["item"] not in family["current"]
            or node["parents"]
            != ([] if family["parent"] is None else [family["parent"]])
        ):
            raise ValueError("canonical placement differs from family construction")
    by_id = {n["id"]: n for n in state["nodes"]}
    for family in state["families"]:
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
        if (
            family["original_ids"] != expected
            or sorted(members) != sorted(expected)
            or len(members) != len(set(members))
        ):
            raise ValueError("family original L1 membership changed")
        if family["complete"] and len(family["current"]) > state["max_siblings"]:
            raise ValueError("canonical family exceeds maximum siblings")
    if state["status"] == "complete":
        if {
            entry["note_id"] for node in state["nodes"] for entry in node["entries"]
        } != set(state["note_ids"]):
            raise ValueError("completed hierarchy omits selected notes")
        parents = {p for node in state["nodes"] for p in node["parents"]}
        if not all(f["complete"] for f in state["families"]) or any(
            len({e["note_id"] for e in node["entries"]}) > state["min_notes"]
            for node in state["nodes"]
            if node["id"] not in parents
        ):
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
        bound = {
            name: [
                p
                for p in state["sources"]
                if Path(p).name == name and Path(p).parent.name == "sse_multivector"
            ]
            for name in CODE_FILES
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
            f"Hierarchy V3: shared runner failed; retrying in {delay:g}s; diagnostics: {invocation}",
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


def _native_teacher(directory, experiment, budget, upgrade_reason, stop):
    arguments = ["run", str(experiment)]
    if budget is not None:
        arguments.extend(["--attempt-budget", str(budget)])
    if upgrade_reason is not None:
        arguments.extend(["--runner-upgrade-reason", upgrade_reason])
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
    comment="Automated hierarchy generation V3",
    runner_upgrade_reason=None,
):
    """Coordinate ordinary native batches and one SSE worker; no provider limiter."""
    directory = Path(directory).resolve()
    budget = Path(attempt_budget).resolve() if attempt_budget is not None else None
    if budget is not None:
        workflow.engine.PersistentAttemptBudget(budget).remaining()
    with (directory / ".hierarchy-run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("hierarchy execution is already active") from error
        trial._save_once(
            directory / "execution-settings.json",
            dict(attempt_budget=None if budget is None else str(budget)),
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
                    "Hierarchy V3: "
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
