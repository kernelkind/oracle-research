"""Resumable native vLLM generation of an approved saved-note collection.

The original inputs and merged checkpoint stay immutable. No model packages
are imported until execution, and completed answers are never regenerated.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import uuid


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def policy_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def require(condition, message):
    if not condition:
        raise ValueError(message)


class GeneratedTokens:
    """Accumulate DELTA tokens through natural EOS, without phase limits."""
    def __init__(self, closing, eos):
        self.closing = closing
        self.eos = set(eos)
        self.tokens = []
        self.close = None
        self.finished = False

    def feed(self, delta):
        for token in delta:
            if self.finished:
                break
            require(type(token) is int and token >= 0, "Invalid generated token ID")
            if self.close is None and token == self.closing:
                self.close = len(self.tokens)
            self.tokens.append(token)
            self.finished = token in self.eos
        return self.finished

    def split(self, finish_reason="stop"):
        if self.close is None:
            return self.tokens, [], True
        ended = bool(self.tokens and self.tokens[-1] in self.eos)
        return (self.tokens[:self.close], self.tokens[self.close + 1:],
                not ended or finish_reason == "length")


def engine_settings(policy, merged, *, max_num_active_seqs=None):
    ceiling = policy["batch_size"]
    active = ceiling if max_num_active_seqs is None else max_num_active_seqs
    require(type(ceiling) is int and type(active) is int and 1 <= active <= ceiling <= 8,
            "Invalid active sequence count")
    sizes = [size for size in (1, 2, 4, 8) if size <= ceiling]
    return dict(model=str(merged), dtype="bfloat16", kv_cache_dtype="auto",
        mamba_cache_dtype="bfloat16", mamba_ssm_cache_dtype="float32",
        language_model_only=True, max_model_len=policy["max_context_tokens"],
        max_num_seqs=ceiling, max_num_active_seqs=active, max_num_batched_tokens=1024,
        enable_chunked_prefill=True, enable_prefix_caching=True,
        mamba_cache_mode="align", distributed_executor_backend="uni",
        attention_config={"backend": "TRITON_ATTN"}, gdn_prefill_backend="triton",
        async_scheduling=False, enforce_eager=False, gpu_memory_utilization=0.60,
        compilation_config=dict(mode=0, cudagraph_mode="FULL_DECODE_ONLY",
            cudagraph_capture_sizes=sizes, max_cudagraph_capture_size=max(sizes)),
        kv_cache_memory_bytes=policy["kv_cache_memory_bytes"], safetensors_load_strategy="eager",
        load_format="safetensors", generation_config="vllm", seed=17, disable_log_stats=True)


def sampling_settings(policy):
    require(type(policy.get("do_sample")) is bool, "Expected an explicit sampling policy")
    if not policy["do_sample"]:
        return dict(temperature=0, top_p=1, top_k=-1)
    approved = dict(temperature=1.0, top_p=0.95, top_k=20, min_p=0.0,
                    presence_penalty=0.0, repetition_penalty=1.0)
    settings = {key: policy.get(key) for key in approved}
    require(settings == approved and type(settings["top_k"]) is int
        and all(type(value) in (int, float) for value in settings.values()),
        "Expected the approved sampling parameters")
    return settings


def load_inputs(directory):
    directory = Path(directory).resolve()
    inputs = read(directory / "inputs.json")
    reference = inputs["original_inputs"]
    original_path = (directory / reference["path"]).resolve()
    require(digest(original_path) == reference["sha256"], "Original input source changed")
    original = read(original_path)
    for key in ("seed", "model", "revision", "checkpoint", "checkpoint_sha256", "dataset_sha256", "notes"):
        require(inputs[key] == original[key], "Original inputs changed: " + key)
    require(len({n["index"] for n in inputs["notes"]}) == len(inputs["notes"])
        and len({n["note_id"] for n in inputs["notes"]}) == len(inputs["notes"]), "Duplicate note identities")
    policy = inputs["generation_policy"]
    require(policy.get("stop_policy") == "natural_eos" and policy.get("thought_budget_tokens") is None
        and policy.get("final_budget_tokens") is None and policy.get("enable_thinking") is True
        and policy.get("reasoning_effort") == "xhigh",
        "Expected the approved natural-EOS thinking policy")
    sampling_settings(policy)
    require(type(policy["gpu_memory_limit_bytes"]) is int and policy["gpu_memory_limit_bytes"] > 0
        and type(policy["kv_cache_memory_bytes"]) is int
        and 0 < policy["kv_cache_memory_bytes"] < policy["gpu_memory_limit_bytes"], "Invalid memory limits")
    require(policy["gpu_memory_limit_bytes"] == 96 * 1024**3
        and policy["kv_cache_memory_bytes"] == 40 * 1024**3, "Memory limits differ from approved limits")
    merged = original_path.parent / "merged-model"
    config = read(merged / "config.json")
    native_context = config.get("text_config", config)["max_position_embeddings"]
    require(policy["max_context_tokens"] == native_context, "Context differs from the native model context")
    export = read(merged / "export-provenance.json")
    require(export["status"] == "complete" and export["inputs_sha256"] == reference["sha256"]
        and export["checkpoint_sha256"] == inputs["checkpoint_sha256"], "Merged checkpoint provenance differs")
    for name, expected in export["files"].items():
        path = merged / name
        require(path.stat().st_size == expected["size"] and digest(path) == expected["sha256"],
                "Merged file changed: " + name)
    engine_settings(policy, merged)
    return inputs, original, original_path, merged


def validate_saved(path, note, inputs, policy, prompt_sha, runtime_root, tokenizer, closing, eos,
                   require_natural=False):
    record = read(path)
    for key in ("note_id", "index", "messages"):
        require(record[key] == note[key], "Saved note identity changed: " + key)
    for key in ("model", "revision", "checkpoint_sha256"):
        require(record[key] == inputs[key], "Saved model identity changed: " + key)
    require(record["generation_policy_sha256"] == policy_digest(policy)
        and record["rendered_prompt_sha256"] == prompt_sha, "Saved prompt or policy changed")
    runtime_reference = record["runtime_receipt"]
    runtime_path = (runtime_root / runtime_reference["path"]).resolve()
    require(digest(runtime_path) == runtime_reference["sha256"], "Runtime receipt changed")
    runtime = read(runtime_path)
    require(runtime["input_sha256"] == digest(runtime_root / "inputs.json")
        and runtime["generation_policy"] == policy, "Runtime inputs or policy differ")
    for key in ("model", "revision", "checkpoint_sha256"):
        require(runtime[key] == inputs[key], "Runtime model identity differs: " + key)
    require(set(runtime["eos_token_ids"]) == set(eos)
        and runtime["closing_think_token_id"] == closing, "Runtime token boundaries differ")
    answer = record["answer"]
    require(isinstance(answer["raw"], str) and type(answer["tokens"]) is int and answer["tokens"] >= 0
        and type(answer["truncated"]) is bool, "Invalid saved answer metadata")
    require(require_natural or "generated_token_ids" in record, "Missing generated token provenance")
    if require_natural or "generated_token_ids" in record:
        tokens = record.get("generated_token_ids")
        if tokens is None:
            tokens = tokenizer.encode(record["raw_response"], add_special_tokens=False)
        state = GeneratedTokens(closing, eos)
        state.feed(tokens)
        thoughts, final, truncated = state.split(record.get("finish_reason", "stop"))
        require(tokenizer.decode(final, skip_special_tokens=True) == answer["raw"], "Saved final answer differs")
        require(tokenizer.decode(thoughts, skip_special_tokens=True) == record["reasoning"], "Saved reasoning differs")
        if "generated_token_ids" in record:
            require(len(state.tokens) == record["total_generated_tokens"]
                and len(thoughts) == record["reasoning_tokens"] and len(final) == answer["tokens"]
                and truncated == answer["truncated"], "Saved token accounting differs")
        if require_natural:
            require(answer["truncated"] is False and not truncated and state.finished,
                    "Reused generation lacks natural EOS evidence")
            require(record["total_generated_tokens"] == record["reasoning_tokens"] + answer["tokens"] + 1,
                    "Legacy token accounting differs")
    return record


def prepare(directory, tokenizer, loaded=None):
    directory = Path(directory).resolve()
    inputs, original, original_path, merged = loaded if loaded is not None else load_inputs(directory)
    policy = inputs["generation_policy"]
    closing = tokenizer.convert_tokens_to_ids("</think>")
    require(tokenizer.encode("</think>", add_special_tokens=False) == [closing], "Invalid closing-think token")
    eos = read(merged / "generation_config.json")["eos_token_id"]
    eos = [eos] if type(eos) is int else eos
    reused = {}
    for reference in inputs.get("reused_generations", []):
        index = reference["index"]
        require(index not in reused and reference["generation_policy"] == original["generation_policy"],
                "Duplicate reused generation or changed legacy policy")
        path = (directory / reference["path"]).resolve()
        require(digest(path) == reference["sha256"], "Reused generation changed")
        reused[index] = (reference, path)
    require(set(reused) <= {n["index"] for n in inputs["notes"]}, "Reused generation outside selected notes")
    expected_new = {directory / "generations" / f"note-{n['index']:04}" / "subjects.json"
                    for n in inputs["notes"] if n["index"] not in reused}
    require(set((directory / "generations").rglob("subjects.json")) <= expected_new,
            "Unexpected saved answer outside selected notes")
    pending, paths = {}, []
    for note in inputs["notes"]:
        rendered = tokenizer.apply_chat_template(note["messages"], tokenize=False,
            add_generation_prompt=True, enable_thinking=True, reasoning_effort=policy["reasoning_effort"])
        require(rendered.endswith("<think>\n"), "Native thinking prefix differs")
        token_ids = tokenizer.encode(rendered, add_special_tokens=False)
        require(len(token_ids) < policy["max_context_tokens"], "Prompt exhausts native context")
        prompt_sha = hashlib.sha256(rendered.encode()).hexdigest()
        if note["index"] in reused:
            reference, path = reused[note["index"]]
            require(reference["note_id"] == note["note_id"], "Reused note identity differs")
            validate_saved(path, note, original, reference["generation_policy"], prompt_sha,
                original_path.parent, tokenizer, closing, eos, require_natural=True)
        else:
            path = directory / "generations" / f"note-{note['index']:04}" / "subjects.json"
            if path.exists():
                validate_saved(path, note, inputs, policy, prompt_sha, directory, tokenizer, closing, eos)
            else:
                pending[str(note["index"])] = (note, token_ids, prompt_sha, path)
        paths.append(path)
    marker = directory / "generation.complete.json"
    if marker.exists():
        expected = {os.path.relpath(path, directory): digest(path) for path in paths}
        require(not pending and read(marker) == expected, "Completion marker differs from selected answers")
    return inputs, merged, closing, eos, pending, paths


def complete(directory, paths):
    write(Path(directory) / "generation.complete.json",
          {os.path.relpath(path, directory): digest(path) for path in paths})


def cache_snapshot(engine, last_seen):
    scheduler = engine.engine_core.engine_core.scheduler
    for key, request in scheduler.requests.items():
        last_seen[key] = dict(num_preemptions=request.num_preemptions,
                             num_computed_tokens=request.num_computed_tokens)
    return dict(running=len(scheduler.running), waiting=len(scheduler.waiting),
        cache_usage=scheduler.kv_cache_manager.usage,
        cumulative_preemptions=sum(row["num_preemptions"] for row in last_seen.values()),
        request_counters=dict(last_seen))


def run(directory, *, max_num_active_seqs=None, note_indexes=None):
    from transformers import AutoTokenizer
    directory = Path(directory).resolve()
    loaded = load_inputs(directory)
    inputs, _, original_path, merged = loaded
    selected = {note["index"] for note in inputs["notes"]} if note_indexes is None else set(note_indexes)
    require(all(type(index) is int for index in selected)
        and selected <= {note["index"] for note in inputs["notes"]}, "Unknown note index")
    tokenizer = AutoTokenizer.from_pretrained(merged, local_files_only=True, trust_remote_code=False)
    inputs, merged, closing, eos, all_pending, paths = prepare(directory, tokenizer, loaded)
    pending = {key: value for key, value in all_pending.items() if int(key) in selected}
    saved = len(paths) - len(all_pending)
    settings = engine_settings(inputs["generation_policy"], merged, max_num_active_seqs=max_num_active_seqs)
    if not pending:
        if not all_pending:
            complete(directory, paths)
            print("GENERATION COMPLETE; saved answers verified, no model loaded", flush=True)
        else:
            print("GENERATION PARTIAL; selected answers verified, no model loaded",
                json.dumps(dict(saved=saved, total=len(paths), remaining=len(all_pending))), flush=True)
        return
    import torch
    from vllm import EngineArgs, LLMEngine, SamplingParams
    from vllm.sampling_params import RequestOutputKind
    require(os.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING") == "0", "Single-process vLLM is required")
    policy = inputs["generation_policy"]
    torch.set_num_threads(1)
    torch.manual_seed(17)
    torch.backends.cuda.matmul.allow_tf32 = False
    gpu_budget = policy["gpu_memory_limit_bytes"]
    torch.cuda.set_per_process_memory_fraction(gpu_budget / torch.cuda.get_device_properties(0).total_memory, 0)
    started = time.monotonic()
    engine = LLMEngine.from_engine_args(EngineArgs(**settings), enable_multiprocessing=False)
    runtime_path = directory / f"runtime-vllm-{uuid.uuid4().hex}.json"
    runtime = dict(model=inputs["model"], revision=inputs["revision"],
        checkpoint_sha256=inputs["checkpoint_sha256"], input_sha256=digest(directory / "inputs.json"),
        script_sha256=digest(__file__), merged_manifest_sha256=digest(merged / "export-provenance.json"),
        packages={name: importlib.metadata.version(name) for name in ("torch", "transformers", "vllm")},
        pid=os.getpid(), gpu=torch.cuda.get_device_name(0), engine_settings=settings,
        selected_note_indexes=sorted(selected),
        gpu_allocator_budget_bytes=gpu_budget, model_load_seconds=time.monotonic() - started,
        eos_token_ids=eos, closing_think_token_id=closing, generation_policy=policy,
        environment={name: os.environ.get(name) for name in ("VLLM_ENABLE_V1_MULTIPROCESSING",
            "VLLM_USE_FLASHINFER_SAMPLER", "HF_HUB_OFFLINE", "CPATH", "PATH", "OMP_NUM_THREADS")},
        bf16_reduced_precision_reduction=torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
        tf32_matmul=torch.backends.cuda.matmul.allow_tf32)
    write(runtime_path, runtime)
    runtime_identity = dict(path=runtime_path.name, sha256=digest(runtime_path))
    sampling = SamplingParams(**sampling_settings(policy), max_tokens=None,
        stop_token_ids=eos, ignore_eos=False, detokenize=False, skip_special_tokens=False,
        include_stop_str_in_output=True, output_kind=RequestOutputKind.DELTA, seed=17, watermarking=False)
    states = {key: GeneratedTokens(closing, eos) for key in pending}
    for key, (_, token_ids, _, _) in pending.items():
        engine.add_request(key, {"prompt_token_ids": token_ids}, sampling)
    last_report, tick, counters = 0.0, time.monotonic(), {}
    print("Engine ready", json.dumps(dict(saved=saved, pending=len(pending), seconds=runtime["model_load_seconds"])), flush=True)
    while engine.has_unfinished_requests():
        results = engine.step()
        snapshot = cache_snapshot(engine, counters)
        for result in results:
            key = result.request_id
            require(key in states and len(result.outputs) == 1, "Unknown or duplicate generation request")
            state = states[key]
            output = result.outputs[0]
            state.feed(output.token_ids)
            if result.finished:
                require(output.finish_reason in {"stop", "length"}, "Technical generation failure: " + str(output.finish_reason))
                note, _, prompt_sha, destination = pending[key]
                thoughts, final, truncated = state.split(output.finish_reason)
                record = dict(note_id=note["note_id"], index=note["index"], messages=note["messages"],
                    model=inputs["model"], revision=inputs["revision"], checkpoint_sha256=inputs["checkpoint_sha256"],
                    generation_policy_sha256=policy_digest(policy), rendered_prompt_sha256=prompt_sha,
                    runtime_receipt=runtime_identity, finish_reason=output.finish_reason,
                    generated_token_ids=state.tokens,
                    answer=dict(raw=tokenizer.decode(final, skip_special_tokens=True), tokens=len(final), truncated=truncated),
                    reasoning=tokenizer.decode(thoughts, skip_special_tokens=True), reasoning_tokens=len(thoughts),
                    total_generated_tokens=len(state.tokens), raw_response=tokenizer.decode(state.tokens, skip_special_tokens=False),
                    elapsed_session_seconds=time.monotonic() - tick)
                write(destination, record)
                del states[key]
                saved += 1
                print("Saved answer", json.dumps(dict(index=note["index"], saved=saved,
                    percent=100 * saved / len(paths), tokens=len(state.tokens), truncated=truncated)), flush=True)
        now = time.monotonic()
        if now - last_report >= 15:
            print("Generation progress", json.dumps(dict(snapshot, saved=saved, percent=100 * saved / len(paths),
                seconds=round(now - tick, 2), requests={k: len(s.tokens) for k, s in states.items()},
                gpu_memory_reserved_bytes=torch.cuda.memory_reserved())), flush=True)
            last_report = now
    require(not states, "Engine ended with missing answers")
    require(digest(directory / "inputs.json") == runtime["input_sha256"]
        and digest(original_path) == inputs["original_inputs"]["sha256"], "Inputs changed during generation")
    _, _, _, _, remaining, _ = prepare(directory, tokenizer, loaded)
    if not remaining:
        complete(directory, paths)
        print("GENERATION COMPLETE", flush=True)
    else:
        print("GENERATION PARTIAL", json.dumps(dict(saved=saved, total=len(paths), remaining=len(remaining))), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("--max-num-active-seqs", type=int,
        help="Execution-only active request limit, 1..batch_size (default: batch_size); "
             "may be reduced on resume without changing inputs or saved-answer policy.")
    parser.add_argument("--note-index", dest="note_indexes", type=int, action="append",
        help="Generate only this note index; repeat to select several. Inputs stay unchanged, "
             "and completion requires every input note (default: all pending notes).")
    args = parser.parse_args()
    run(args.input_directory, max_num_active_seqs=args.max_num_active_seqs, note_indexes=args.note_indexes)


if __name__ == "__main__":
    main()
