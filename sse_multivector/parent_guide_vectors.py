"""Prepare only saved exact-unmatched parent names for unchanged standalone SSE.

This prepares source-bound worker files; it never launches an encoder or model.
The resulting probe retains ordinary subject-vector receipts and reuse identity.
"""

import hashlib
from pathlib import Path

try:
    from . import experiment as workflow
    from . import parent_guide_workflow as guides
    from . import worker
    from .subject_matching_probe import load_subject_vectors
except ImportError:
    import experiment as workflow
    import parent_guide_workflow as guides
    import worker
    from subject_matching_probe import load_subject_vectors


def _raw_reference(value, base):
    expected = None
    if isinstance(value, dict):
        guides.bounded._fields(value, {"path", "sha256"}, "source reference")
        expected, value = value["sha256"], value["path"]
    if not isinstance(value, str) or not value:
        raise ValueError("source reference path must be a nonempty string")
    path = (base / value).resolve()
    measured = worker._sha256_file(path)
    if expected is not None and expected != measured:
        raise ValueError(f"protected source changed: {path}")
    return path, dict(path=str(path), sha256=measured)


def prepare_vectors(source_path, destination, load_report):
    """Prepare unique exact-absent names, reusing compatible saved vectors first."""
    source_path, destination = Path(source_path).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    source_hash = worker._sha256_file(source_path)
    source = guides.bounded._parse(source_path.read_bytes())
    required = {"schema_version", "inputs", "hierarchy", "discoveries", "subject_probe",
                "worker_config", "worker_source"}
    allowed = required | ({"judgments"} & source.keys()) if isinstance(source, dict) else required
    guides.bounded._fields(source, allowed, "parent-guide vector source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected parent-guide vector source schema_version 1")
    if not callable(load_report):
        raise ValueError("parent-guide vectors require validated experiment reports")
    base = source_path.parent
    loaded, references, protected = guides.bounded._read_sources(
        {key: source[key] for key in ("schema_version", "inputs", "hierarchy", "judgments") if key in source}, base)
    protected[str(source_path)] = source_hash
    directories = guides.bounded.engine._validate_string_array(
        source["discoveries"], "parent-guide experiments", allow_empty=False)
    directories = [(base / path).resolve() for path in directories]
    if len(set(directories)) != len(directories):
        raise ValueError("duplicate parent-guide experiment")
    reports = [load_report(path) for path in directories]
    _, _, resolution = guides.resolve_exact_guides(loaded["inputs"], loaded["hierarchy"],
        reports, references, history=loaded.get("judgments"))
    for report in reports:
        guides._protect_report(report, protected)
    names = list(dict.fromkeys(record["name"] for record in resolution["unresolved_guides"]
                              if record.get("reason") == "exact_name_absent"))
    probe = source["subject_probe"]
    if not isinstance(probe, str) or not probe:
        raise ValueError("subject_probe must be a saved probe directory")
    probe = (base / probe).resolve()
    vectors, receipt, vector_sources = load_subject_vectors(probe)
    protected.update(vector_sources)
    config, config_reference = guides.bounded._read_reference(source["worker_config"], base)
    worker.WorkerConfig.load(Path(config_reference["path"]))
    protected[config_reference["path"]] = config_reference["sha256"]
    worker_source, worker_reference = _raw_reference(source["worker_source"], base)
    protected[str(worker_source)] = worker_reference["sha256"]
    if worker_reference["sha256"] != receipt.get("runtime", {}).get("worker_sha256"):
        raise ValueError("frozen worker source differs from saved subject-vector runtime")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model",
                "device", "note_batch_size", "container_image"):
        if config[key] != receipt.get(key):
            raise ValueError(f"worker identity differs from saved subject vectors: {key}")
    checkpoint = Path(config["checkpoint_path"])
    if worker._sha256_file(checkpoint) != config["checkpoint_sha256"]:
        raise ValueError("checkpoint does not match its configured SHA-256")
    if worker.canonical_tree_sha256(Path(config["base_model_artifact_path"])) != config["base_model_artifact_tree_sha256"]:
        raise ValueError("base-model artifact tree does not match its configured SHA-256")
    protected[str(checkpoint.resolve())] = config["checkpoint_sha256"]

    notes = []
    for name in names:
        raw = name.encode("utf-8")
        identity = hashlib.sha256(raw).hexdigest()
        if (identity, identity[:16]) not in vectors:
            notes.append(dict(note_id=identity, text=name, subjects=[
                dict(subject_id=identity[:16], byte_spans=[[0, len(raw)]])]))
    for path, expected in protected.items():
        if worker._sha256_file(Path(path)) != expected:
            raise ValueError(f"source changed during parent-guide vector preparation: {path}")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / ".gitignore").write_text("*\n")
    workflow.write(destination / "inputs.json", dict(schema_version=1,
        encoding="standalone-subject-full-text", names=names,
        source=references, discoveries=[str(path) for path in directories],
        protected_sha256=protected, reused_probes=[str(probe)], new_encodings=len(notes),
        worker_config=config_reference, worker_source=worker_reference,
        exact_absent_guides=[record for record in resolution["unresolved_guides"]
                            if record.get("reason") == "exact_name_absent"]))
    if notes:
        request_path = destination / "worker-request.json"
        workflow.write(request_path, dict(schema_version=1,
            proposal_sha256=worker._sha256_file(destination / "inputs.json"), notes=notes))
        worker._load_request(request_path)
        config.update(request_path=str(request_path), request_sha256=worker._sha256_file(request_path),
                      output_path=str(destination / "worker-result"))
        workflow.write(destination / "worker-config.json", config)
        worker.WorkerConfig.load(destination / "worker-config.json")
    return dict(output=str(destination), unique_names=len(names), reused_encodings=len(names) - len(notes),
                new_encodings=len(notes), inference_calls=0, worker_source=str(worker_source),
                worker_config=str(destination / "worker-config.json") if notes else None)
