"""Local-weight subject/mask training and evaluation, resumable in one directory.

This does not call teachers or rent hardware. Prompts and decoding reuse the
extraction pipeline. All mutable outputs belong in an ignored artifact directory.
"""
import argparse
import fcntl
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import random
import re
import shutil
import site
import sys
import time
from pathlib import Path

from sse_multivector.extraction_pipeline import prepare_mask_inputs
from sse_multivector.mask_positions import decode, parse_json_response, unique_object


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def load_data(directory, mask_prompt=None):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if manifest["schema_version"] != 2:
        raise ValueError("expected dataset schema 2")
    tasks = set(manifest["tasks"])
    if tasks not in ({"subjects"}, {"subjects", "mask"}):
        raise ValueError("unexpected dataset tasks")
    rows = {}
    for name in ("train", "evaluation", "references"):
        path = directory / (name + ".jsonl")
        if sha256(path) != manifest["outputs"][path.name]:
            raise ValueError(f"dataset hash mismatch: {path.name}")
        rows[name] = [json.loads(line, object_pairs_hook=unique_object)
                      for line in path.read_text().splitlines()]
    if "mask" in tasks:
        if mask_prompt is None or sha256(mask_prompt) not in manifest["inputs"].values():
            raise ValueError("mask prompt hash differs from prepared data")
    train = set(manifest["train_note_ids"])
    evaluation = set(manifest["evaluation_note_ids"])
    if not train or not evaluation or train & evaluation:
        raise ValueError("training/evaluation note split overlaps or is empty")
    if ({r["note_id"] for r in rows["train"]} != train or
            {r["note_id"] for r in rows["evaluation"]} != evaluation):
        raise ValueError("example IDs disagree with split")
    if any(r["task"] not in tasks for r in rows["train"]):
        raise ValueError("unexpected training task")
    references = {r["note_id"]: r for r in rows["references"]}
    if len(references) != len(rows["references"]) or references.keys() != train | evaluation:
        raise ValueError("reference note set differs")
    for note_id in train | evaluation:
        if references[note_id]["split"] != ("train" if note_id in train else "evaluation"):
            raise ValueError("reference split differs")
    rows.update(manifest=manifest, references=references)
    if "mask" in tasks:
        rows["mask_prompt"] = Path(mask_prompt).read_text()
    return rows


def generation_prompt(tokenizer, messages):
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)


def encode_example(tokenizer, row, max_length):
    # Some native templates (Gemma 4) add the empty thought channel only to
    # generation prompts. Use that exact prefix, retaining the native turn end.
    if len(row["completion"]) != 1 or row["completion"][0]["role"] != "assistant":
        raise ValueError("expected one assistant completion")
    answer = row["completion"][0]["content"]
    rendered = tokenizer.apply_chat_template(row["prompt"] + row["completion"], tokenize=False,
                                              enable_thinking=False)
    _, found, ending = rendered.rpartition(answer)
    if not answer or not found or not ending:
        raise ValueError("chat template must preserve the answer and terminate its turn")
    prefix = generation_prompt(tokenizer, row["prompt"])
    prompt = tokenizer.encode(prefix, add_special_tokens=False)
    whole = tokenizer.encode(prefix + answer + ending, add_special_tokens=False)
    if whole[:len(prompt)] != prompt or len(whole) <= len(prompt):
        raise ValueError("chat template does not preserve the generation prefix")
    if len(whole) > max_length:
        raise ValueError(f"training example exceeds max_length: {len(whole)} > {max_length}")
    return {"input_ids": whole, "attention_mask": [1] * len(whole),
            "labels": [-100] * len(prompt) + whole[len(prompt):]}


def preflight(tokenizer, data, config):
    """Validate actual tokenization and configured allowances without model weights."""
    stats = {t: {"examples": 0, "max_tokens": 0, "max_answer_tokens": 0, "total_tokens": 0}
             for t in ("subjects", "mask")}
    for row in data["train"]:
        encoded = encode_example(tokenizer, row, config["max_length"])
        tokens = len(encoded["input_ids"])
        answer = sum(label != -100 for label in encoded["labels"])
        task = row["task"]
        allowance = config["max_new_tokens"][task]
        if answer > allowance or tokens - answer + allowance > config["max_length"]:
            raise ValueError(f"{task} training example exceeds generation allowance")
        s = stats[task]
        s.update(examples=s["examples"] + 1, max_tokens=max(s["max_tokens"], tokens),
                 max_answer_tokens=max(s["max_answer_tokens"], answer), total_tokens=s["total_tokens"] + tokens)
    evaluation_max = 0
    for row in data["evaluation"]:
        length = len(tokenizer.encode(generation_prompt(tokenizer, row["messages"]), add_special_tokens=False))
        if length + config["max_new_tokens"]["subjects"] > config["max_length"]:
            raise ValueError("evaluation input exceeds generation allowance")
        evaluation_max = max(evaluation_max, length)
    return {"training": stats, "evaluation_notes": len(data["evaluation"]),
            "evaluation_max_prompt_tokens": evaluation_max, "enable_thinking": False}


def parse_subjects(raw):
    value = parse_json_response(raw)
    if not isinstance(value, dict) or set(value) != {"subjects"} or not isinstance(value["subjects"], list):
        raise ValueError("expected subjects array")
    numbers = set()
    for subject in value["subjects"]:
        if (not isinstance(subject, dict) or set(subject) != {"number", "context", "subject"}
                or any(not isinstance(v, str) or not v.strip() for v in subject.values())):
            raise ValueError("expected number, context and subject strings")
        if not re.fullmatch(r"[1-9][0-9]*(?:\.[1-9][0-9]*)*", subject["number"]) or subject["number"] in numbers:
            raise ValueError("invalid or repeated subject number")
        parent = subject["number"].rpartition(".")[0]
        if parent and parent not in numbers:
            raise ValueError("subject parent must precede child")
        numbers.add(subject["number"])
    return value["subjects"]


def generate(model, tokenizer, messages, config, task="subjects"):
    batch = generate_batch(model, tokenizer, [messages], config, task)
    return {**batch["answers"][0], "seconds": batch["seconds"]}


def generate_batch(model, tokenizer, messages, config, task, *, encoded=None):
    import torch
    if not messages:
        raise ValueError("generation batch must not be empty")
    if encoded is None:
        encoded = [tokenizer.encode(generation_prompt(tokenizer, prompt), add_special_tokens=False)
                   for prompt in messages]
    if len(encoded) != len(messages) or any(not row for row in encoded):
        raise ValueError("generation batch token rows differ or are empty")
    allowance = config["max_new_tokens"][task]
    width = max(map(len, encoded))
    if width + allowance > config["max_length"]:
        raise ValueError("generation input plus output allowance exceeds max_length")
    # Decoder-only generation must end every row with its real prompt. Build
    # left padding without changing the tokenizer's right padding for training.
    inputs = torch.tensor([[tokenizer.pad_token_id] * (width - len(row)) + row for row in encoded],
                          device=config["device"])
    attention = torch.tensor([[0] * (width - len(row)) + [1] * len(row) for row in encoded],
                             device=config["device"])
    eos = model.generation_config.eos_token_id
    eos = tokenizer.eos_token_id if eos is None else eos
    stop_ids = [eos] if isinstance(eos, int) else eos
    model.eval()
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(input_ids=inputs, attention_mask=attention,
                                do_sample=False, max_new_tokens=allowance, use_cache=True,
                                pad_token_id=tokenizer.pad_token_id,
                                eos_token_id=eos)
    rows = result[:, width:].tolist()  # Also waits for CUDA before stopping the timer.
    elapsed = time.monotonic() - started
    answers = []
    for row in rows:
        stop = next((i for i, token in enumerate(row) if token in stop_ids), None)
        answer = row if stop is None else row[:stop + 1]
        answers.append({"raw": tokenizer.decode(answer, skip_special_tokens=True),
                        "tokens": len(answer), "truncated": stop is None})
    return {"answers": answers, "seconds": elapsed}


def validate_subject_batching(policy):
    """Require explicit frozen memory allowances; no inferred numerical defaults."""
    fields = {"budget_bytes", "workspace_bytes", "prefill_bytes_per_token", "attention_matrix_count"}
    if (not isinstance(policy, dict) or set(policy) != fields
            or any(type(value) is not int or value < 0 for value in policy.values())
            or policy["budget_bytes"] == 0 or policy["prefill_bytes_per_token"] == 0
            or policy["attention_matrix_count"] > 4):
        raise ValueError("invalid subject batching memory policy")


def subject_batch_memory(model, config):
    """Resident tensors and cache shapes for one complete, unquantized model.

    Kernel scratch allowances come from the frozen subject_batching policy.
    Their suitability for the selected GPU still requires preparation evidence.
    """
    if config["quantization"] != "none":
        raise ValueError("dynamic subject batching requires an unquantized model")
    generation = model.generation_config
    # In the pinned Transformers version, None resolves to one greedy sequence.
    if (generation.num_beams not in (None, 1) or generation.num_return_sequences not in (None, 1)
            or generation.cache_implementation not in (None, "dynamic")
            or getattr(generation, "cache_config", None)
            or any(getattr(generation, field, False) for field in (
                "output_scores", "output_logits", "output_attentions",
                "output_hidden_states", "return_dict_in_generate"))):
        raise ValueError("unsupported subject generation settings for the memory policy")
    tensors = list(model.parameters()) + list(model.buffers())
    devices = {(t.device.type, getattr(t.device, "index", None)) for t in tensors}
    if len(devices) != 1 or next(iter(devices))[0] != config["device"]:
        raise ValueError("subject batching requires the complete model on one device")
    policy = config["subject_batching"]
    if config["device"] == "cuda":
        import torch
        capacity = torch.cuda.get_device_properties(next(iter(devices))[1]).total_memory
        if policy["budget_bytes"] > capacity:
            raise ValueError("subject batch budget exceeds GPU memory capacity")
    c = model.config
    if hasattr(c, "get_text_config"):
        c = c.get_text_config()
    if c.model_type not in ("qwen3_5_text", "gemma4_text", "llama"):
        raise ValueError(f"unsupported subject batch cache model: {c.model_type}")
    if getattr(c, "num_kv_shared_layers", 0):
        raise ValueError("subject batch cache sharing is not supported")
    layers = getattr(c, "layer_types", None) or ["full_attention"] * c.num_hidden_layers
    if len(layers) != c.num_hidden_layers or set(layers) - {"full_attention", "sliding_attention", "linear_attention"}:
        raise ValueError("unsupported subject batch cache layers")
    if "sliding_attention" in layers and not getattr(c, "sliding_window", 0):
        raise ValueError("subject batch sliding cache requires a window")
    size = model.get_input_embeddings().weight.element_size()
    d = getattr(c, "head_dim", None) or c.hidden_size // c.num_attention_heads
    full_layer = 2 * (getattr(c, "num_global_key_value_heads", None) or c.num_key_value_heads) * (
        getattr(c, "global_head_dim", None) or d) * size
    sliding_layer = 2 * c.num_key_value_heads * d * size
    recurrent_layer = convolution_layer = 0
    if "linear_attention" in layers:
        if c.model_type != "qwen3_5_text":
            raise ValueError("unsupported recurrent subject batch cache")
        recurrent_layer = c.linear_num_value_heads * c.linear_key_head_dim * c.linear_value_head_dim * 4
        convolution_layer = (2*c.linear_num_key_heads*c.linear_key_head_dim
                             + c.linear_num_value_heads*c.linear_value_head_dim) * c.linear_conv_kernel_dim * size
    return {"resident_bytes": sum(t.numel()*t.element_size() for t in tensors),
            "kv_bytes_per_token": layers.count("full_attention")*full_layer,
            "sliding_bytes_per_token": layers.count("sliding_attention")*sliding_layer,
            "sliding_window": getattr(c, "sliding_window", 0) or 0,
            "state_bytes_per_note": layers.count("linear_attention")*(recurrent_layer+convolution_layer),
            "full_layer_bytes_per_token": full_layer if "full_attention" in layers else 0,
            "sliding_layer_bytes_per_token": sliding_layer if "sliding_attention" in layers else 0,
            "recurrent_layer_bytes": recurrent_layer,
            "attention_heads": c.num_attention_heads,
            "vocab_size": getattr(c, "vocab_size", 0)}


def subject_batch_plan(model, tokenizer, rows, config):
    policy = config["subject_batching"]
    validate_subject_batching(policy)
    memory = subject_batch_memory(model, config)
    encoded = [tokenizer.encode(generation_prompt(tokenizer, row["messages"]), add_special_tokens=False)
               for row in rows]
    allowance = config["max_new_tokens"]["subjects"]

    def estimated_bytes(count, width):
        length = width + allowance
        prefill_cache = (memory["kv_bytes_per_token"] + memory["sliding_bytes_per_token"])*width
        decode_cache = memory["kv_bytes_per_token"]*length + memory["sliding_bytes_per_token"]*min(
            length, memory["sliding_window"])
        cache_copy = max(memory["full_layer_bytes_per_token"]*length,
                         memory["sliding_layer_bytes_per_token"]*max(width, memory["sliding_window"]),
                         memory["recurrent_layer_bytes"])
        per_note = max(prefill_cache, decode_cache) + memory["state_bytes_per_note"] + cache_copy
        # Budget prefill and the longest single-token decode, including FP32 masks.
        per_note += (8 + 4*memory["attention_heads"]*policy["attention_matrix_count"])*max(width*width, length)
        per_note += policy["prefill_bytes_per_token"]*width + 16*memory["vocab_size"]
        return memory["resident_bytes"] + policy["workspace_bytes"] + count*per_note

    batches, indices, width = [], [], 0
    for index, tokens in enumerate(encoded):
        if not tokens or len(tokens) + allowance > config["max_length"]:
            raise ValueError(f"subject input {index} plus output allowance exceeds max_length or is empty")
        if estimated_bytes(1, len(tokens)) > policy["budget_bytes"]:
            raise ValueError(f"subject input {index} cannot fit the frozen memory budget")
        candidate = max(width, len(tokens))
        if indices and estimated_bytes(len(indices)+1, candidate) > policy["budget_bytes"]:
            batches.append({"indices": indices, "prompt_width": width,
                            "estimated_bytes": estimated_bytes(len(indices), width)})
            indices, width = [], 0
        indices.append(index)
        width = max(width, len(tokens))
    if indices:
        batches.append({"indices": indices, "prompt_width": width,
                        "estimated_bytes": estimated_bytes(len(indices), width)})
    plan = {"policy": policy, "memory": memory, "max_new_tokens": allowance,
            "inputs": [{"note_id": row["note_id"], "tokens": len(tokens),
                        "sha256": hashlib.sha256(json.dumps([row["messages"], tokens],
                            ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()}
                       for row, tokens in zip(rows, encoded)], "batches": batches}
    return plan, encoded


def generate_subject_batches(model, tokenizer, rows, config, directory):
    """Publish a complete batch before its per-note files, so resumes never repeat it."""
    plan, encoded = subject_batch_plan(model, tokenizer, rows, config)
    plan_path = directory / "subject-batches.json"
    if plan_path.exists():
        if read_json(plan_path) != plan:
            raise ValueError("saved subject batch plan differs")
    else:
        write_json(plan_path, plan)
    for index, batch in enumerate(plan["batches"]):
        indices = batch["indices"]
        paths = [directory / f"note-{i:04}/subjects.json" for i in indices]
        receipt = directory / f"subjects-{index:04}.json"
        messages = [rows[i]["messages"] for i in indices]
        inputs = {"note_ids": [rows[i]["note_id"] for i in indices], "messages": messages,
                  "input_tokens": [len(encoded[i]) for i in indices], "batch": batch}
        if receipt.exists():
            saved = read_json(receipt)
            if any(saved.get(key) != value for key, value in inputs.items()):
                raise ValueError("saved subject batch input differs")
        else:
            if any(path.exists() for path in paths):
                raise ValueError("saved subject answers have no batch receipt")
            attempt = directory / f"subjects-{index:04}.started.json"
            if attempt.exists():
                raise ValueError("subject batch has an unfinished generation attempt; reconcile it before restarting")
            write_json(attempt, {**inputs, "started_unix": time.time()})
            generated = generate_batch(model, tokenizer, messages, config, "subjects",
                                       encoded=[encoded[i] for i in indices])
            saved = {**inputs, **generated}
            # Preserve defective batch evidence too; never retry an answer-count defect.
            write_json(receipt, saved)
        if len(saved["answers"]) != len(indices):
            raise ValueError("subject generation batch answer count differs")
        for offset, (path, prompt, answer) in enumerate(zip(paths, messages, saved["answers"])):
            value = {"note_id": rows[indices[offset]]["note_id"], "messages": prompt, "answer": answer,
                     "batch": {"file": receipt.name, "offset": offset}}
            if path.exists():
                if read_json(path) != value:
                    raise ValueError("saved subject answer differs from its batch receipt")
            else:
                write_json(path, value)
            yield indices[offset], rows[indices[offset]]


def evaluate(model, tokenizer, data, config, directory):
    """Persist each completed call, including malformed answers, without retries."""
    directory = Path(directory)
    if (directory / "complete.json").exists():
        if not verify_saved(directory):
            raise ValueError("evaluation hash mismatch")
        return read_json(directory / "results.json")

    tasks = config.get("evaluation_tasks", ["subjects", "mask"])
    if tasks not in (["subjects"], ["subjects", "mask"]):
        raise ValueError("invalid evaluation tasks")
    if "subject_batching" in config:
        rows = generate_subject_batches(model, tokenizer, data["evaluation"], config, directory)
    else:
        rows = enumerate(data["evaluation"])

    def call(path, messages, task):
        if path.exists():
            saved = read_json(path)
            if saved["messages"] != messages:
                raise ValueError("saved evaluation input differs")
            return saved["answer"]
        answer = generate(model, tokenizer, messages, config, task)
        write_json(path, {"messages": messages, "answer": answer})
        return answer

    notes = []
    for index, row in rows:
        note_id = row["note_id"]
        original = data["references"][note_id]
        note_directory = directory / f"note-{index:04}"
        answer = call(note_directory / "subjects.json", row["messages"], "subjects")
        result = {"note_id": note_id, "subjects": [], "masks": [], "errors": []}
        try:
            if answer["truncated"]:
                raise ValueError("subject answer reached output limit")
            result["subjects"] = parse_subjects(answer["raw"])
            if len(result["subjects"]) > config["max_subjects"]:
                raise ValueError("subject count exceeds configured limit")
        except (ValueError, TypeError) as error:
            result["errors"].append({"task": "subjects", "error": str(error)})
        if "subject_batching" in config:
            parsed_path = note_directory / "subjects-result.json"
            parsed = {"note_id": note_id, "subjects": result["subjects"], "errors": result["errors"]}
            if parsed_path.exists():
                if read_json(parsed_path) != parsed:
                    raise ValueError("saved parsed subject result differs")
            else:
                write_json(parsed_path, parsed)
            if tasks == ["subjects"]:
                seal = note_directory / "complete.json"
                if seal.exists():
                    if not verify_saved(note_directory):
                        raise ValueError("saved subject response hash mismatch")
                else:
                    write_json(seal, file_hashes(note_directory))
        if result["errors"]:
            notes.append(result)
            continue
        if result["subjects"] and "mask" in tasks:
            _, prompts = prepare_mask_inputs({"schema_version": 1, "notes": [{
                "note_id": note_id, "text": original["text"], "subjects": result["subjects"]}]},
                data["mask_prompt"])
            for start in range(0, len(prompts), config["mask_batch_size"]):
                stop = start + config["mask_batch_size"]
                messages = [[{"role": "user", "content": p.text}] for p in prompts[start:stop]]
                path = note_directory / f"masks-{start:04}.json"
                if path.exists():
                    batch = read_json(path)
                    if batch["messages"] != messages:
                        raise ValueError("saved evaluation input differs")
                else:
                    batch = {"messages": messages, **generate_batch(model, tokenizer, messages, config, "mask")}
                    # Publish the whole batch at once. Resumes retain the same
                    # grouping and never repeat saved malformed/empty answers.
                    write_json(path, batch)
                if len(batch["answers"]) != len(messages):
                    raise ValueError("generation batch answer count differs")
                for subject, answer in zip(result["subjects"][start:stop], batch["answers"]):
                    try:
                        if answer["truncated"]:
                            raise ValueError("mask answer reached output limit")
                        response, spans = decode(answer["raw"], original["text"])
                        result["masks"].append({"subject": subject, "response": response, "spans": spans})
                    except (ValueError, TypeError) as error:
                        result["errors"].append({"task": "mask", "subject": subject, "error": str(error)})
        notes.append(result)
    write_json(directory / "results.json", notes)
    write_json(directory / "complete.json", file_hashes(directory))
    return notes


def matched_count(predictions, references, threshold):
    """Maximum one-to-one matching, independent of output order."""
    edges = [[j for j, ref in enumerate(references)
              if len(pred & ref) / len(pred | ref) >= threshold] for pred in predictions]
    assigned = {}

    def augment(i, seen):
        for j in edges[i]:
            if j not in seen:
                seen.add(j)
                if j not in assigned or augment(assigned[j], seen):
                    assigned[j] = i
                    return True
        return False

    return sum(augment(i, set()) for i in range(len(predictions)))


def summarize(notes, data):
    totals = {"notes": len(notes), "subjects": 0, "valid_masks": 0, "empty_masks": 0,
              "subject_failures": 0, "mask_failures": 0, "predicted_nonempty": 0,
              "reference_nonempty": 0, "matches_80": 0, "exact_matches": 0}
    for result in notes:
        original = data["references"][result["note_id"]]
        text = original["text"]
        words = list(re.finditer(r"\S+", text))

        def selected(spans):
            return frozenset(i for i, word in enumerate(words)
                             if any(a < word.end() and b > word.start() for a, b in spans))

        predicted = [selected([(s["start"], s["end"]) for s in m["spans"]])
                     for m in result["masks"] if m["spans"]]
        encoded = text.encode()
        reference_spans = [[(len(encoded[:a].decode()), len(encoded[:b].decode()))
                           for a, b in s["byte_spans"]]
                          for s in original["subjects"] if s["byte_spans"]]
        references = [selected(spans) for spans in reference_spans]
        def characters(spans):
            return frozenset(i for a, b in spans for i in range(a, b) if not text[i].isspace())
        exact_predictions = {characters([(s["start"], s["end"]) for s in m["spans"]])
                             for m in result["masks"] if m["spans"]}
        exact_references = {characters(spans) for spans in reference_spans}
        # Equal selections from different subjects do not create extra coverage.
        predicted, references = list(set(predicted)), list(set(references))
        totals["subjects"] += len(result["subjects"])
        totals["valid_masks"] += len(result["masks"])
        totals["empty_masks"] += sum(not m["spans"] for m in result["masks"])
        totals["subject_failures"] += sum(e["task"] == "subjects" for e in result["errors"])
        totals["mask_failures"] += sum(e["task"] == "mask" for e in result["errors"])
        totals["predicted_nonempty"] += len(predicted)
        totals["reference_nonempty"] += len(references)
        totals["matches_80"] += matched_count(predicted, references, .8)
        totals["exact_matches"] += len(exact_predictions & exact_references)
    p, r, matches = totals["predicted_nonempty"], totals["reference_nonempty"], totals["matches_80"]
    totals.update(precision_80=matches / p if p else 0., recall_80=matches / r if r else 0.,
                  f1_80=2 * matches / (p + r) if p + r else 0.)
    return totals


def file_hashes(directory):
    return {str(p.relative_to(directory)): sha256(p) for p in sorted(Path(directory).rglob("*"))
            if p.is_file() and p.name not in ("complete.json", "complete.json.tmp")}


def verify_saved(directory):
    return read_json(Path(directory) / "complete.json") == file_hashes(directory)


def load_gpu_packages(config):
    # FLA dispatches to Triton even for CPU tensors if importable. Keep its
    # packaged CUDA kernels optional so this image also supports CPU execution.
    if config["device"] == "cuda":
        site.addsitedir(str(Path(sys.prefix).parent / "distillation-gpu"))


def load_model(config, adapter=None):
    load_gpu_packages(config)
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    options = {"revision": config["revision"], "trust_remote_code": False,
               "dtype": torch.float32 if config["device"] == "cpu" else torch.bfloat16}
    architecture = AutoConfig.from_pretrained(config["model"], revision=config["revision"], trust_remote_code=False)
    if config["device"] == "cuda" and architecture.model_type in ("qwen3_5", "qwen3_5_text"):
        # Fail on a broken CUDA dependency instead of silently using a slow fallback.
        from fla.ops.gated_delta_rule import chunk_gated_delta_rule, fused_recurrent_gated_delta_rule
    if architecture.model_type in ("gemma4", "qwen3_5"):
        options["config"] = architecture.get_text_config()
        if architecture.model_type == "gemma4":
            options["key_mapping"] = {r"^model\.language_model\.": "model."}
    if config["quantization"] == "nf4":
        options.update(device_map={"": config["device"]}, quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16))
    model, loading = AutoModelForCausalLM.from_pretrained(config["model"], output_loading_info=True, **options)
    if loading["missing_keys"] or loading["mismatched_keys"] or loading.get("error_msgs"):
        raise ValueError(f"incomplete model weights: {loading}")
    limit = getattr(model.config, "max_position_embeddings", None)
    if limit is not None and config["max_length"] > limit:
        raise ValueError("max_length exceeds model position limit")
    if config["quantization"] == "none":
        model.to(config["device"])
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    return model


def train(config, tokenizer, data, output):
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import Trainer, TrainerCallback, TrainingArguments, DataCollatorForSeq2Seq, set_seed
    set_seed(config["seed"])
    encoded = {task: [encode_example(tokenizer, row, config["max_length"])
                      for row in data["train"] if row["task"] == task] for task in ("subjects", "mask")}
    if not all(encoded.values()):
        raise ValueError("both training tasks require examples")
    rng = random.Random(config["seed"])
    counts = {"subjects": 0, "mask": 0}
    dataset = []
    for _ in range(config["max_steps"] * config["batch_size"] * config["gradient_accumulation_steps"]):
        task = "subjects" if rng.random() < config["subject_fraction"] else "mask"
        counts[task] += 1
        dataset.append(rng.choice(encoded[task]))
    model = load_model(config)
    if config["quantization"] == "nf4":
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", target_modules=config["lora_target_modules"],
        r=config["lora_rank"], lora_alpha=config["lora_alpha"], lora_dropout=0.))
    model.config.use_cache = False

    class CompletedCheckpoint(TrainerCallback):
        def on_save(self, args, state, control, **kwargs):
            checkpoint = Path(args.output_dir) / f"checkpoint-{state.global_step}"
            write_json(checkpoint / "complete.json", file_hashes(checkpoint))

    checkpoints = output / "checkpoints"
    complete = [p for p in checkpoints.glob("checkpoint-*") if (p / "complete.json").exists()]
    for path in complete:
        if not verify_saved(path):
            raise ValueError(f"checkpoint hash mismatch: {path}")
    resume = max(complete, key=lambda p: int(p.name.split("-")[-1])) if complete else None
    args = TrainingArguments(output_dir=str(checkpoints), use_cpu=config["device"] == "cpu",
        max_steps=config["max_steps"], per_device_train_batch_size=config["batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"], learning_rate=config["learning_rate"],
        lr_scheduler_type="constant", warmup_steps=0, weight_decay=0., optim="adamw_torch",
        save_strategy="steps", save_steps=config["save_steps"], save_total_limit=2,
        logging_steps=config["save_steps"], report_to="none", seed=config["seed"], data_seed=config["seed"],
        bf16=config["device"] != "cpu", dataloader_pin_memory=False, disable_tqdm=True,
        gradient_checkpointing=config["gradient_checkpointing"],
        gradient_checkpointing_kwargs={"use_reentrant": False})
    trainer = Trainer(model=model, args=args, train_dataset=dataset, processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True, label_pad_token_id=-100),
        callbacks=[CompletedCheckpoint()])
    started = time.monotonic()
    if not resume or int(resume.name.split("-")[-1]) < config["max_steps"]:
        trainer.train(resume_from_checkpoint=str(resume) if resume else None)
    else:
        # A previous process completed training but stopped before publishing the adapter.
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        set_peft_model_state_dict(model, load_file(str(resume / "adapter_model.safetensors")))
    staging = output / "adapter.partial"
    if staging.exists():
        shutil.rmtree(staging)
    model.save_pretrained(staging)
    tokenizer.save_pretrained(staging)
    probe_messages = data["evaluation"][0]["messages"]
    before_reload = generate(model, tokenizer, probe_messages, config)
    checkpointing = model.is_gradient_checkpointing
    del trainer, model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    reloaded = load_model(config, staging)
    after_reload = generate(reloaded, tokenizer, probe_messages, config)
    if before_reload["raw"] != after_reload["raw"] or before_reload["tokens"] != after_reload["tokens"]:
        raise ValueError("saved adapter generation differs after reload")
    write_json(staging / "training.json", {"max_steps": config["max_steps"], "sampled_examples": counts,
        "gradient_checkpointing": checkpointing,
        "resumed_from": resume.name if resume else None, "this_process_seconds": time.monotonic() - started,
        "reload_matches": True, "peak_cuda_bytes": torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None})
    write_json(staging / "complete.json", file_hashes(staging))
    staging.rename(output / "adapter")
    return reloaded


def subject_training_plan(data, config):
    """Freeze whole-note block membership, then shuffle only within each block."""
    ids = [row["note_id"] for row in data["train"]]
    milestones = config["training_milestones"]
    if (any(row["task"] != "subjects" for row in data["train"]) or len(set(ids)) != len(ids)):
        raise ValueError("training requires exactly one subject example per note")
    if (not isinstance(milestones, list) or not milestones
            or any(type(n) is not int or n <= 0 for n in milestones)
            or milestones != sorted(set(milestones)) or milestones[-1] != len(ids)):
        raise ValueError("training milestones must increase through the complete note set")
    if config["batch_size"] * config["gradient_accumulation_steps"] != 8:
        raise ValueError("subject training requires eight examples per update")
    order, start = [], 0
    rng = random.Random(config["seed"])
    for stop in milestones:
        block = ids[start:stop]
        rng.shuffle(block)
        order.extend(block)
        start = stop
    return {"note_ids": order, "milestones": milestones, "examples_per_update": 8}


def subject_training_model(config, checkpoint=None):
    """Create FP32 trainable adapters, including both packed Gemma expert weights."""
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    model = load_model(config)
    experts = []
    if getattr(model.config, "enable_moe_block", False):
        if model.config.model_type != "gemma4_text":
            raise ValueError("unsupported subject training experts")
        experts = [name for name, _ in model.named_parameters()
                   if name.endswith((".experts.gate_up_proj", ".experts.down_proj"))]
        if len(experts) != 2 * model.config.num_hidden_layers:
            raise ValueError("subject training expert target coverage differs")
    if checkpoint is None:
        model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM",
            target_modules=config["lora_target_modules"], r=config["lora_rank"],
            lora_alpha=config["lora_alpha"], lora_dropout=0., bias="none", lora_bias=False,
            init_lora_weights=True, target_parameters=experts or None,
            rank_pattern={re.escape(name): 2 for name in experts},
            alpha_pattern={re.escape(name): 32 for name in experts}))
    else:
        model = PeftModel.from_pretrained(model, checkpoint, is_trainable=True)
        verify_adapter(model, checkpoint)
    trainable = [(name, value) for name, value in model.named_parameters() if value.requires_grad]
    if not trainable or any("lora_" not in name or "router" in name or value.dtype != torch.float32
                            for name, value in trainable):
        raise ValueError("subject training requires only FP32 LoRA weights to be trainable")
    model.config.use_cache = False
    if config["gradient_checkpointing"]:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    return model


def verify_adapter(model, checkpoint):
    import torch
    from peft import get_peft_model_state_dict
    from safetensors.torch import load_file
    saved = load_file(str(Path(checkpoint) / "adapter_model.safetensors"))
    actual = get_peft_model_state_dict(model)
    if saved.keys() != actual.keys() or any(not torch.equal(value, actual[name].detach().cpu())
                                            for name, value in saved.items()):
        raise ValueError("saved adapter weights differ after reload")


def training_random_state(state=None):
    import numpy as np
    import torch
    if state is not None:
        random.setstate(state["python"])
        name, keys, position, gaussian, cached = state["numpy"]
        np.random.set_state((name, np.asarray(keys, dtype=np.uint32), position, gaussian, cached))
        torch.set_rng_state(state["torch"])
        if state["cuda"]:
            torch.cuda.set_rng_state_all(state["cuda"])
        return
    name, keys, position, gaussian, cached = np.random.get_state()
    return {"python": random.getstate(), "numpy": (name, keys.tolist(), position, gaussian, cached),
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def subject_checkpoint_metadata(checkpoint, output, plan):
    """A file seal alone cannot establish full checkpoint coverage or counters."""
    checkpoint, output = Path(checkpoint), Path(output)
    required = {"training-state.pt", "training.json", "adapter_model.safetensors", "adapter_config.json"}
    if not required <= {path.name for path in checkpoint.iterdir() if path.is_file()}:
        raise ValueError("subject checkpoint is missing required files")
    if not verify_saved(checkpoint):
        raise ValueError("subject checkpoint hash mismatch")
    metadata = read_json(checkpoint / "training.json")
    cursor = metadata["cursor"]
    if (type(cursor) is not int or cursor not in plan["milestones"]
            or checkpoint.name != f"checkpoint-{cursor}"
            or metadata["consumed_note_ids"] != plan["note_ids"][:cursor]
            or metadata["manifest_sha256"] != sha256(output / "manifest.json")
            or metadata["plan_sha256"] != sha256(output / "training-plan.json")):
        raise ValueError("subject checkpoint identity or cursor differs")
    start, expected_updates = 0, 0
    for stop in plan["milestones"]:
        expected_updates += math.ceil((stop-start)/plan["examples_per_update"])
        start = stop
        if stop == cursor:
            break
    if type(metadata["updates"]) is not int or metadata["updates"] != expected_updates:
        raise ValueError("subject checkpoint update count differs")
    return metadata


def train_subject_block(config, tokenizer, data, output, plan, milestone, previous=None):
    """Continue unmerged training, preserving the actual cursor and token objective."""
    import torch
    from contextlib import nullcontext
    from transformers import DataCollatorForSeq2Seq, set_seed
    output = Path(output)
    identity = {"manifest_sha256": sha256(output / "manifest.json"),
                "plan_sha256": sha256(output / "training-plan.json")}
    state = {"cursor": 0, "updates": 0, "supervised_tokens": 0, "consumed_note_ids": []}
    if previous is not None:
        metadata = subject_checkpoint_metadata(previous, output, plan)
        state = torch.load(Path(previous) / "training-state.pt", map_location="cpu", weights_only=True)
        if (state["identity"] != identity
                or any(state[key] != metadata[key] for key in ("cursor", "updates", "supervised_tokens", "consumed_note_ids"))):
            raise ValueError("subject training checkpoint identity or cursor differs")
    if milestone <= state["cursor"] or milestone not in plan["milestones"]:
        raise ValueError("subject training block must advance to the next milestone")
    next_index = plan["milestones"].index(state["cursor"]) + 1 if state["cursor"] else 0
    if plan["milestones"][next_index] != milestone:
        raise ValueError("subject training cannot skip a milestone")
    set_seed(config["seed"])
    model = subject_training_model(config, previous)
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=config["learning_rate"], betas=(.9, .999), eps=1e-8, weight_decay=0.)
    schedule = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    if previous is not None:
        optimizer.load_state_dict(state["optimizer"])
        schedule.load_state_dict(state["schedule"])
        training_random_state(state["random"])
    by_id = {row["note_id"]: row for row in data["train"]}
    collator = DataCollatorForSeq2Seq(tokenizer, padding=True, label_pad_token_id=-100)
    metrics = []
    started = time.monotonic()
    if config["device"] == "cuda":
        torch.cuda.reset_peak_memory_stats()
    try:
        while state["cursor"] < milestone:
            stop = min(state["cursor"] + plan["examples_per_update"], milestone)
            ids = plan["note_ids"][state["cursor"]:stop]
            rows = [encode_example(tokenizer, by_id[note_id], config["max_length"]) for note_id in ids]
            tokens = sum(sum(label != -100 for label in row["labels"][1:]) for row in rows)
            if not tokens:
                raise ValueError("subject update has no teacher-answer tokens")
            optimizer.zero_grad(set_to_none=True)
            loss_value = 0.
            update_started = time.monotonic()
            for start in range(0, len(rows), config["batch_size"]):
                batch = {key: value.to(config["device"]) for key, value in
                         collator(rows[start:start+config["batch_size"]]).items()}
                count = int((batch["labels"][:, 1:] != -100).sum())
                context = torch.autocast("cuda", dtype=torch.bfloat16) if config["device"] == "cuda" else nullcontext()
                with context:
                    loss = model(**batch, use_cache=False).loss * (count / tokens)
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite subject training loss")
                loss.backward()
                loss_value += float(loss.detach())
                del batch, loss
            norm = torch.nn.utils.clip_grad_norm_(parameters, 1., error_if_nonfinite=True)
            optimizer.step()
            schedule.step()
            state["cursor"] = stop
            state["updates"] += 1
            state["supervised_tokens"] += tokens
            state["consumed_note_ids"].extend(ids)
            metrics.append({"update": state["updates"], "cursor": stop, "note_ids": ids,
                            "supervised_tokens": tokens, "loss": loss_value, "gradient_norm": float(norm),
                            "seconds": time.monotonic()-update_started,
                            "cuda_allocated_bytes": torch.cuda.memory_allocated() if config["device"] == "cuda" else None,
                            "cuda_reserved_bytes": torch.cuda.memory_reserved() if config["device"] == "cuda" else None})
            print(json.dumps({"stage": "subject training", **metrics[-1]}), flush=True)
        optimizer.zero_grad(set_to_none=True)
        checkpoint = output / "checkpoints" / f"checkpoint-{milestone}"
        staging = checkpoint.with_name(checkpoint.name + f".partial-{time.time_ns()}")
        model.save_pretrained(staging)
        tokenizer.save_pretrained(staging)
        state.update(identity=identity, optimizer=optimizer.state_dict(), schedule=schedule.state_dict(),
                     random=training_random_state())
        torch.save(state, staging / "training-state.pt")
        write_json(staging / "training.json", {**identity, "cursor": state["cursor"], "updates": state["updates"],
            "supervised_tokens": state["supervised_tokens"], "consumed_note_ids": state["consumed_note_ids"],
            "updates_this_block": metrics, "seconds": time.monotonic()-started,
            "trainable_parameters": sum(p.numel() for p in parameters),
            "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated() if config["device"] == "cuda" else None,
            "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved() if config["device"] == "cuda" else None})
        write_json(staging / "complete.json", file_hashes(staging))
        if not verify_saved(staging):
            raise ValueError("subject checkpoint publication hash mismatch")
        staging.rename(checkpoint)
        return checkpoint
    finally:
        del model, optimizer, schedule, parameters, state
        gc.collect()
        if config["device"] == "cuda":
            torch.cuda.empty_cache()


def subject_stage_summary(directory, data):
    directory = Path(directory)
    if not verify_saved(directory):
        raise ValueError("subject evaluation hash mismatch")
    results = read_json(directory / "results.json")
    expected = [row["note_id"] for row in data["evaluation"]]
    if [row["note_id"] for row in results] != expected:
        raise ValueError("subject response accounting differs")
    for index, row in enumerate(results):
        note = directory / f"note-{index:04}"
        raw = read_json(note / "subjects.json")
        parsed = read_json(note / "subjects-result.json")
        if (raw["note_id"] != row["note_id"] or raw["messages"] != data["evaluation"][index]["messages"]
                or parsed != {key: row[key] for key in ("note_id", "subjects", "errors")} or row["masks"]):
            raise ValueError("subject response accounting differs")
    return {"notes": len(results), "subject_failures": sum(bool(row["errors"]) for row in results),
            "returned_subjects": sum(len(row["subjects"]) for row in results)}


def preparation_data(data, config):
    """Select existing complete examples; preparation never repairs teacher data."""
    settings = config["preparation"]
    fields = {"max_new_tokens", "cache_fill_tokens", "train_note_ids", "evaluation_note_ids"}
    if not isinstance(settings, dict) or set(settings) != fields:
        raise ValueError("invalid preparation settings")
    for key in ("max_new_tokens", "cache_fill_tokens"):
        if type(settings[key]) is not int or settings[key] < 1:
            raise ValueError(f"invalid preparation {key}")
    if settings["max_new_tokens"] > config["max_new_tokens"]["subjects"]:
        raise ValueError("preparation output limit exceeds the subject allowance")
    selected = dict(data)
    for name, key in (("train", "train_note_ids"), ("evaluation", "evaluation_note_ids")):
        ids = settings[key]
        if (not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
                or len(ids) != len(set(ids))):
            raise ValueError(f"invalid preparation {key}")
        available = {row["note_id"]: row for row in data[name]}
        if set(ids) - available.keys():
            raise ValueError(f"preparation {key} contains notes outside its split")
        selected[name] = [available[i] for i in ids]
    milestones = config["training_milestones"]
    if (not isinstance(milestones, list) or len(milestones) != 2
            or any(type(m) is not int for m in milestones) or not 1 <= milestones[0] <= 8
            or not 1 <= milestones[1]-milestones[0] <= 8):
        raise ValueError("preparation requires exactly two small training updates")
    return selected


def cuda_measurement(config, reset=False):
    """Synchronize timing and retain resident as well as temporary GPU allocations."""
    import torch
    if config["device"] != "cuda":
        return {"peak_cuda_allocated_bytes": None, "peak_cuda_reserved_bytes": None}
    torch.cuda.synchronize()
    if reset:
        torch.cuda.reset_peak_memory_stats()
    return {"peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved()}


def generation_cache_check(model, tokenizer, encoded, config, chunk_tokens):
    """Build real native caches in chunks, then decode at the allowed maximum.

    These synthetic continuation tokens test memory and execution only. They are
    never training examples or semantic evaluation outputs. No cache tensors are
    fabricated, resized or patched outside the model's normal forward path.
    """
    import torch
    if not encoded or any(not row for row in encoded) or type(chunk_tokens) is not int or chunk_tokens < 1:
        raise ValueError("invalid generation cache check shape")
    width = max(map(len, encoded))
    target = width + config["max_new_tokens"]["subjects"]
    if target > config["max_length"]:
        raise ValueError("invalid generation cache check shape")
    inputs = torch.tensor([[tokenizer.pad_token_id]*(width-len(row)) + row
                           + [row[-1]]*(target-width) for row in encoded], device=config["device"])
    attention = torch.tensor([[0]*(width-len(row)) + [1]*(len(row)+target-width)
                              for row in encoded], device=config["device"])
    positions = attention.cumsum(-1)-1
    positions.masked_fill_(attention == 0, 0)
    model.eval()
    cache, done, calls = None, 0, 0
    prefill_seconds = fill_seconds = decode_seconds = 0.
    cuda_measurement(config, reset=True)
    with torch.inference_mode():
        while done < target:
            end = width if done == 0 else min(target-1, done+chunk_tokens) if done < target-1 else target
            started = time.monotonic()
            prepared = model.prepare_inputs_for_generation(inputs[:, :end],
                next_sequence_length=end-done, past_key_values=cache,
                attention_mask=attention[:, :end], position_ids=positions[:, :end],
                is_first_iteration=done == 0, use_cache=True, logits_to_keep=1)
            result = model(**prepared)
            cache = result.past_key_values
            if cache is None or int(cache.get_seq_length()) != end or not bool(torch.isfinite(result.logits).all()):
                raise ValueError("generation cache did not advance or produced nonfinite logits")
            cuda_measurement(config)
            elapsed = time.monotonic()-started
            if done == 0:
                prefill_seconds = elapsed
            elif end == target:
                decode_seconds = elapsed
            else:
                fill_seconds += elapsed
                calls += 1
            del result, prepared
            done = end
    return {"batch_size": len(encoded), "prompt_width": width, "cached_tokens": done,
            "fill_calls": calls, "prefill_seconds": prefill_seconds,
            "fill_seconds": fill_seconds, "decode_seconds": decode_seconds,
            **cuda_measurement(config), "purpose": "Memory check with synthetic continuation; not a quality result."}


def run_subject_preparation(config, tokenizer, data, output):
    """One save/merge/generate/restore cycle and two actual optimizer updates."""
    plan = subject_training_plan(data, config)
    plan_path = output / "training-plan.json"
    if plan_path.exists() and read_json(plan_path) != plan:
        raise ValueError("frozen preparation training plan differs")
    write_json(plan_path, plan)
    stages = output / "preparation"
    checkpoints = [output / "checkpoints" / f"checkpoint-{m}" for m in plan["milestones"]]
    if (output / "report.json").exists():
        if not verify_saved(stages):
            raise ValueError("preparation hash mismatch")
        for checkpoint in checkpoints:
            subject_checkpoint_metadata(checkpoint, output, plan)
        print("stage: preparation complete (reused)", flush=True)
        return
    timing_path = output / "preparation-timings.json"
    timings = read_json(timing_path) if timing_path.exists() else []
    for index, milestone in enumerate(plan["milestones"]):
        checkpoint = checkpoints[index]
        if not (checkpoint / "complete.json").exists():
            if checkpoint.exists():
                raise ValueError("incomplete preparation checkpoint cannot be resumed")
            started = time.monotonic()
            train_subject_block(config, tokenizer, data, output, plan, milestone,
                                checkpoints[index-1] if index else None)
            timings.append({"stage": f"training-{milestone}", "seconds": time.monotonic()-started})
            write_json(timing_path, timings)
        metadata = subject_checkpoint_metadata(checkpoint, output, plan)
        if index:
            continue
        if (stages / "complete.json").exists():
            if not verify_saved(stages):
                raise ValueError("preparation hash mismatch")
            continue
        attempt = stages / "started.json"
        if attempt.exists():
            raise ValueError("unfinished preparation attempt; reconcile saved evidence before restarting")
        write_json(attempt, {"started_unix": time.time(), "checkpoint": str(checkpoint.relative_to(output))})
        cuda_measurement(config, reset=True)
        started = time.monotonic()
        model = load_model(config, checkpoint)
        verify_adapter(model, checkpoint)
        model = model.merge_and_unload(safe_merge=True)
        if any("lora_" in name for name, _ in model.named_parameters()):
            raise ValueError("preparation evaluation still contains adapters")
        merge = {"seconds": time.monotonic()-started, **cuda_measurement(config)}
        try:
            batch_plan, encoded = subject_batch_plan(model, tokenizer, data["evaluation"], config)
            write_json(stages / "subject-batches.json", batch_plan)
            brief = {**config, "max_new_tokens": {"subjects": config["preparation"]["max_new_tokens"]}}
            cache_checks, batches = [], []
            for batch_index, batch in enumerate(batch_plan["batches"]):
                indices = batch["indices"]
                rows = [data["evaluation"][i] for i in indices]
                messages = [row["messages"] for row in rows]
                cuda_measurement(config, reset=True)
                generated = generate_batch(model, tokenizer, messages, brief, "subjects",
                                           encoded=[encoded[i] for i in indices])
                if len(generated["answers"]) != len(rows):
                    raise ValueError("preparation subject response accounting differs")
                receipt = {"indices": indices, **generated, **cuda_measurement(config)}
                write_json(stages / f"subjects-{batch_index:04}.json", receipt)
                for i, row, answer in zip(indices, rows, generated["answers"]):
                    note = stages / f"note-{i:04}"
                    write_json(note / "subjects.json", {"note_id": row["note_id"],
                               "messages": row["messages"], "answer": answer})
                    parsed = {"note_id": row["note_id"], "subjects": [], "errors": []}
                    try:
                        parsed["subjects"] = parse_subjects(answer["raw"])
                    except ValueError as error:
                        parsed["errors"].append({"task": "subjects", "error": str(error)})
                    write_json(note / "subjects-result.json", parsed)
                    write_json(note / "complete.json", file_hashes(note))
                batches.append(receipt)
                check = generation_cache_check(model, tokenizer, [encoded[i] for i in indices],
                                                config, config["preparation"]["cache_fill_tokens"])
                if (config["device"] == "cuda" and
                        check["peak_cuda_reserved_bytes"] > config["subject_batching"]["budget_bytes"]):
                    raise ValueError("observed generation cache peak exceeds the frozen memory budget")
                cache_checks.append(check)
                write_json(stages / f"cache-{batch_index:04}.json", check)
            write_json(stages / "measurements.json", {"subject_answers": len(data["evaluation"]),
                "max_new_tokens": brief["max_new_tokens"]["subjects"], "merge": merge,
                "batches": batches, "cache_checks": cache_checks})
            write_json(stages / "complete.json", file_hashes(stages))
        finally:
            del model
            gc.collect()
            if config["device"] == "cuda":
                import torch
                torch.cuda.empty_cache()
        if not verify_saved(checkpoint):
            raise ValueError("preparation modified the saved training checkpoint")
    write_json(output / "report.json", {"status": "complete", "purpose": "GPU preparation; not a quality comparison.",
        "training": {"examples": metadata["cursor"], "updates": metadata["updates"]},
        "preparation": read_json(stages / "measurements.json"), "stage_timings": timings})
    print("stage: preparation complete", flush=True)


def run_subject_pilot(config, tokenizer, data, output, through):
    plan = subject_training_plan(data, config)
    plan_path = output / "training-plan.json"
    if plan_path.exists():
        if read_json(plan_path) != plan:
            raise ValueError("frozen subject training plan differs")
    else:
        write_json(plan_path, plan)
    baseline = subject_stage_summary(output / "baseline", data)
    previous = None
    stages = []
    for milestone in plan["milestones"]:
        checkpoint = output / "checkpoints" / f"checkpoint-{milestone}"
        if (checkpoint / "complete.json").exists():
            subject_checkpoint_metadata(checkpoint, output, plan)
        elif checkpoint.exists():
            raise ValueError("incomplete subject checkpoint cannot be resumed")
        else:
            print(f"stage: subject training through {milestone} notes", flush=True)
            checkpoint = train_subject_block(config, tokenizer, data, output, plan, milestone, previous)
        stage = output / "evaluations" / checkpoint.name
        if not (stage / "complete.json").exists():
            print(f"stage: merged subject evaluation at {milestone} notes", flush=True)
            model = load_model(config, checkpoint)
            verify_adapter(model, checkpoint)
            model = model.merge_and_unload(safe_merge=True)
            if any("lora_" in name for name, _ in model.named_parameters()):
                raise ValueError("subject evaluation still contains unmerged adapters")
            try:
                evaluate(model, tokenizer, data, config, stage)
            finally:
                del model
                gc.collect()
                if config["device"] == "cuda":
                    import torch
                    torch.cuda.empty_cache()
        summary = subject_stage_summary(stage, data)
        if not verify_saved(checkpoint):
            raise ValueError("subject evaluation changed the training checkpoint")
        stages.append({"notes_trained": milestone, "checkpoint": str(checkpoint.relative_to(output)),
                       "evaluation": summary, "merged_reload_verified": True})
        previous = checkpoint
    if through != "train":
        report = {"status": "complete", "baseline": baseline, "checkpoints": stages,
            "training": {"examples": len(plan["note_ids"]),
                         "updates": read_json(previous / "training.json")["updates"]},
            "semantic_review": "Pending; saved subject answers require local correctness/coverage review."}
        report_path = output / "report.json"
        if report_path.exists() and read_json(report_path) != report:
            raise ValueError("saved subject pilot report differs")
        if not report_path.exists():
            write_json(report_path, report)
    print("stage: subject pilot complete", flush=True)


def run(config_path, output, through="report"):
    import torch
    config, output = read_json(config_path), Path(output)
    required = {"model", "revision", "data", "mask_prompt", "device", "quantization", "seed",
        "max_length", "max_new_tokens", "max_subjects", "max_steps", "save_steps", "batch_size",
        "gradient_accumulation_steps", "learning_rate", "subject_fraction", "lora_rank", "lora_alpha", "threads",
        "gradient_checkpointing", "lora_target_modules", "mask_batch_size"}
    pilot = "training_milestones" in config
    if pilot:
        required = required - {"mask_prompt", "mask_batch_size", "max_steps", "save_steps", "subject_fraction"}
        required |= {"training_milestones", "subject_batching"}
    optional = {"subject_batching", "evaluation_tasks", "preparation"}
    if required - set(config) or set(config) - required - optional:
        raise ValueError(f"configuration fields differ: {set(config) ^ required}")
    if "subject_batching" in config:
        validate_subject_batching(config["subject_batching"])
    if pilot:
        if config.get("evaluation_tasks", ["subjects"]) != ["subjects"] or config["quantization"] != "none":
            raise ValueError("subject pilot requires subjects-only evaluation and an unquantized base")
        config.setdefault("evaluation_tasks", ["subjects"])
    if config.get("evaluation_tasks", ["subjects", "mask"]) not in (["subjects"], ["subjects", "mask"]):
        raise ValueError("invalid evaluation tasks")
    for key in required - {"model", "revision", "data", "mask_prompt", "device", "quantization",
                           "learning_rate", "subject_fraction", "max_new_tokens", "gradient_checkpointing",
                           "lora_target_modules", "training_milestones", "subject_batching"}:
        if type(config[key]) is not int or config[key] < (0 if key == "seed" else 1):
            raise ValueError(f"invalid {key}")
    limits = config["max_new_tokens"]
    if (not isinstance(limits, dict) or set(limits) != ({"subjects"} if pilot else {"subjects", "mask"})
            or any(type(v) is not int or not 0 < v < config["max_length"] for v in limits.values())
            or (not pilot and not 0 < config["subject_fraction"] < 1) or not math.isfinite(config["learning_rate"])
            or config["learning_rate"] <= 0):
        raise ValueError("invalid sampling, learning rate or length")
    targets = config["lora_target_modules"]
    if (type(config["gradient_checkpointing"]) is not bool or
            not (targets == "all-linear" or isinstance(targets, list) and targets
                 and all(isinstance(t, str) and t for t in targets))):
        raise ValueError("invalid checkpointing or LoRA targets")
    if config["device"] not in ("cpu", "cuda") or config["quantization"] not in ("none", "nf4"):
        raise ValueError("unsupported device or quantization")
    if config["quantization"] == "nf4" and config["device"] != "cuda":
        raise ValueError("NF4 requires CUDA")
    load_gpu_packages(config)
    from transformers import AutoTokenizer, set_seed
    local_model = Path(config["model"])
    if not local_model.is_dir() and not re.fullmatch(r"[a-f0-9]{40}", config["revision"] or ""):
        raise ValueError("remote models require an immutable revision")
    data = load_data(config["data"], config.get("mask_prompt"))
    preparing = "preparation" in config
    if (through == "preparation" and not preparing or
            preparing and (not pilot or through not in ("preparation", "preflight"))):
        raise ValueError("preparation mode requires its explicit subject-only configuration")
    if preparing:
        data = preparation_data(data, config)
    if pilot:
        if set(data["manifest"]["tasks"]) != {"subjects"}:
            raise ValueError("subject pilot requires subjects-only data")
        subject_training_plan(data, config)
    torch.set_num_threads(config["threads"])
    set_seed(config["seed"])
    code = Path(__file__).parent
    frozen = {"config": config, "dataset": data["manifest"],
        "code": {name: sha256(code / name) for name in
                 ("distillation_run.py", "distillation_data.py", "extraction_pipeline.py", "mask_positions.py")},
        "python": sys.version,
        "packages": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "peft", "accelerate",
                                                                 "tokenizers", "safetensors", "bitsandbytes", "numpy")
                     + (("fla-core", "einops") if config["device"] == "cuda" else ())},
        "local_model": file_hashes(local_model) if local_model.is_dir() else None}
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest_path = output / "manifest.json"
        if manifest_path.exists():
            if read_json(manifest_path) != frozen:
                raise ValueError("frozen run differs; use a new output directory")
        else:
            write_json(manifest_path, frozen)
        if not pilot and through == "report" and (output / "report.json").exists():
            for stage in ("baseline", "adapter", "trained"):
                if not verify_saved(output / stage):
                    raise ValueError(f"{stage} hash mismatch")
            print("stage: complete (reused)", flush=True)
            return
        tokenizer = AutoTokenizer.from_pretrained(config["model"], revision=config["revision"], trust_remote_code=False)
        if tokenizer.chat_template is None or tokenizer.eos_token_id is None:
            raise ValueError("model requires a chat template and EOS token")
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        write_json(output / "preflight.json", preflight(tokenizer, data, config))
        if through == "preflight":
            print("stage: preflight complete (no model weights loaded)", flush=True)
            return
        if through == "preparation":
            run_subject_preparation(config, tokenizer, data, output)
            return
        print("stage: baseline", flush=True)
        baseline_path = output / "baseline" / "results.json"
        if not (baseline_path.parent / "complete.json").exists():
            model = load_model(config)
            baseline = evaluate(model, tokenizer, data, config, output / "baseline")
            del model
        else:
            if not verify_saved(baseline_path.parent):
                raise ValueError("baseline hash mismatch")
            baseline = read_json(baseline_path)
        if through == "baseline":
            return
        if pilot:
            run_subject_pilot(config, tokenizer, data, output, through)
            return
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("stage: train", flush=True)
        if (output / "adapter").exists():
            if not verify_saved(output / "adapter"):
                raise ValueError("adapter hash mismatch")
            model = load_model(config, output / "adapter")
        else:
            model = train(config, tokenizer, data, output)
        if through == "train":
            return
        print("stage: evaluation", flush=True)
        trained = evaluate(model, tokenizer, data, config, output / "trained")
        write_json(output / "report.json", {"baseline": summarize(baseline, data),
            "trained": summarize(trained, data), "training": read_json(output / "adapter" / "training.json"),
            "semantic_review": "Pending; token overlap is teacher agreement, not semantic correctness.",
            "scoring": "Micro average over unique nonempty source-word selections per note; one-to-one matching.",
            "status": "complete"})
        print("stage: complete", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--through", choices=("preflight", "baseline", "train", "report", "preparation"), default="report")
    args = parser.parse_args()
    run(args.config, args.output, args.through)


if __name__ == "__main__":
    main()
