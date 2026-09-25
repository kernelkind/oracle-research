"""Local-weight subject/mask training and evaluation, resumable in one directory.

This does not call teachers or rent hardware. Prompts and decoding reuse the
extraction pipeline. All mutable outputs belong in an ignored artifact directory.
"""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path

from sse_multivector.extraction_pipeline import prepare_mask_inputs
from sse_multivector.mask_positions import decode, unique_object


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


def load_data(directory, mask_prompt):
    directory, mask_prompt = Path(directory), Path(mask_prompt)
    manifest = read_json(directory / "manifest.json")
    if manifest["schema_version"] != 2:
        raise ValueError("expected two-task dataset schema 2")
    rows = {}
    for name in ("train", "evaluation", "references"):
        path = directory / (name + ".jsonl")
        if sha256(path) != manifest["outputs"][path.name]:
            raise ValueError(f"dataset hash mismatch: {path.name}")
        rows[name] = [json.loads(line, object_pairs_hook=unique_object)
                      for line in path.read_text().splitlines()]
    if sha256(mask_prompt) not in manifest["inputs"].values():
        raise ValueError("mask prompt hash differs from prepared data")
    train = set(manifest["train_note_ids"])
    evaluation = set(manifest["evaluation_note_ids"])
    if not train or not evaluation or train & evaluation:
        raise ValueError("training/evaluation note split overlaps or is empty")
    if ({r["note_id"] for r in rows["train"]} != train or
            {r["note_id"] for r in rows["evaluation"]} != evaluation):
        raise ValueError("example IDs disagree with split")
    if any(r["task"] not in ("subjects", "mask") for r in rows["train"]):
        raise ValueError("unexpected training task")
    references = {r["note_id"]: r for r in rows["references"]}
    if len(references) != len(rows["references"]) or references.keys() != train | evaluation:
        raise ValueError("reference note set differs")
    for note_id in train | evaluation:
        if references[note_id]["split"] != ("train" if note_id in train else "evaluation"):
            raise ValueError("reference split differs")
    rows.update(manifest=manifest, references=references, mask_prompt=mask_prompt.read_text())
    return rows


def encode_example(tokenizer, row, max_length):
    prompt = tokenizer.apply_chat_template(row["prompt"], tokenize=True, add_generation_prompt=True, return_dict=False)
    whole = tokenizer.apply_chat_template(row["prompt"] + row["completion"], tokenize=True, return_dict=False)
    if whole[:len(prompt)] != prompt or len(whole) <= len(prompt):
        raise ValueError("chat template does not preserve the generation prefix")
    if len(whole) > max_length:
        raise ValueError(f"training example exceeds max_length: {len(whole)} > {max_length}")
    return {"input_ids": whole, "attention_mask": [1] * len(whole),
            "labels": [-100] * len(prompt) + whole[len(prompt):]}


def parse_subjects(raw):
    value = json.loads(raw, object_pairs_hook=unique_object)
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


def generate(model, tokenizer, messages, config):
    import torch
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
    if len(encoded) + config["max_new_tokens"] > config["max_length"]:
        raise ValueError("generation input plus output allowance exceeds max_length")
    inputs = torch.tensor([encoded], device=config["device"])
    eos = model.generation_config.eos_token_id
    eos = tokenizer.eos_token_id if eos is None else eos
    stop_ids = [eos] if isinstance(eos, int) else eos
    model.eval()
    started = time.monotonic()
    with torch.inference_mode():
        result = model.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                                do_sample=False, max_new_tokens=config["max_new_tokens"],
                                pad_token_id=tokenizer.pad_token_id,
                                eos_token_id=eos)
    answer = result[0, len(encoded):].tolist()
    return {"raw": tokenizer.decode(answer, skip_special_tokens=True),
            "tokens": len(answer), "seconds": time.monotonic() - started,
            "truncated": not answer or answer[-1] not in stop_ids}


def evaluate(model, tokenizer, data, config, directory):
    """Persist each completed call, including malformed answers, without retries."""
    directory = Path(directory)
    if (directory / "complete.json").exists():
        if not verify_saved(directory):
            raise ValueError("evaluation hash mismatch")
        return read_json(directory / "results.json")

    def call(path, messages):
        if path.exists():
            saved = read_json(path)
            if saved["messages"] != messages:
                raise ValueError("saved evaluation input differs")
            return saved["answer"]
        answer = generate(model, tokenizer, messages, config)
        write_json(path, {"messages": messages, "answer": answer})
        return answer

    notes = []
    for index, row in enumerate(data["evaluation"]):
        note_id = row["note_id"]
        original = data["references"][note_id]
        note_directory = directory / f"note-{index:04}"
        answer = call(note_directory / "subjects.json", row["messages"])
        result = {"note_id": note_id, "subjects": [], "masks": [], "errors": []}
        try:
            if answer["truncated"]:
                raise ValueError("subject answer reached output limit")
            result["subjects"] = parse_subjects(answer["raw"])
            if len(result["subjects"]) > config["max_subjects"]:
                raise ValueError("subject count exceeds configured limit")
        except (ValueError, TypeError) as error:
            result["errors"].append({"task": "subjects", "error": str(error)})
            notes.append(result)
            continue
        if result["subjects"]:
            _, prompts = prepare_mask_inputs({"schema_version": 1, "notes": [{
                "note_id": note_id, "text": original["text"], "subjects": result["subjects"]}]},
                data["mask_prompt"])
            for number, (subject, prompt) in enumerate(zip(result["subjects"], prompts)):
                answer = call(note_directory / f"mask-{number:04}.json",
                              [{"role": "user", "content": prompt.text}])
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


def load_model(config, adapter=None):
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    options = {"revision": config["revision"], "trust_remote_code": False,
               "dtype": torch.float32 if config["device"] == "cpu" else torch.bfloat16}
    if config["quantization"] == "nf4":
        options.update(device_map={"": config["device"]}, quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16))
    model = AutoModelForCausalLM.from_pretrained(config["model"], **options)
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
    model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", target_modules="all-linear",
        r=config["lora_rank"], lora_alpha=config["lora_alpha"], lora_dropout=0.))

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
        bf16=config["device"] != "cpu", dataloader_pin_memory=False, disable_tqdm=True)
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
    del trainer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    reloaded = load_model(config, staging)
    after_reload = generate(reloaded, tokenizer, probe_messages, config)
    if before_reload["raw"] != after_reload["raw"] or before_reload["tokens"] != after_reload["tokens"]:
        raise ValueError("saved adapter generation differs after reload")
    write_json(staging / "training.json", {"max_steps": config["max_steps"], "sampled_examples": counts,
        "resumed_from": resume.name if resume else None, "this_process_seconds": time.monotonic() - started,
        "reload_matches": True, "peak_cuda_bytes": torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None})
    write_json(staging / "complete.json", file_hashes(staging))
    staging.rename(output / "adapter")
    return reloaded


def run(config_path, output, through="report"):
    import torch
    from transformers import AutoTokenizer, set_seed
    config, output = read_json(config_path), Path(output)
    required = {"model", "revision", "data", "mask_prompt", "device", "quantization", "seed",
        "max_length", "max_new_tokens", "max_subjects", "max_steps", "save_steps", "batch_size",
        "gradient_accumulation_steps", "learning_rate", "subject_fraction", "lora_rank", "lora_alpha", "threads"}
    if set(config) != required:
        raise ValueError(f"configuration fields differ: {set(config) ^ required}")
    for key in required - {"model", "revision", "data", "mask_prompt", "device", "quantization",
                           "learning_rate", "subject_fraction"}:
        if type(config[key]) is not int or config[key] < (0 if key == "seed" else 1):
            raise ValueError(f"invalid {key}")
    if (not 0 < config["subject_fraction"] < 1 or not math.isfinite(config["learning_rate"])
            or config["learning_rate"] <= 0 or config["max_new_tokens"] >= config["max_length"]):
        raise ValueError("invalid sampling, learning rate or length")
    if config["device"] not in ("cpu", "cuda") or config["quantization"] not in ("none", "nf4"):
        raise ValueError("unsupported device or quantization")
    if config["quantization"] == "nf4" and config["device"] != "cuda":
        raise ValueError("NF4 requires the GPU validation run")
    local_model = Path(config["model"])
    if not local_model.is_dir() and not re.fullmatch(r"[a-f0-9]{40}", config["revision"] or ""):
        raise ValueError("remote models require an immutable revision")
    data = load_data(config["data"], config["mask_prompt"])
    torch.set_num_threads(config["threads"])
    set_seed(config["seed"])
    code = Path(__file__).parent
    frozen = {"config": config, "dataset": data["manifest"],
        "code": {name: sha256(code / name) for name in
                 ("distillation_run.py", "distillation_data.py", "extraction_pipeline.py", "mask_positions.py")},
        "python": sys.version,
        "packages": {p: importlib.metadata.version(p) for p in ("torch", "transformers", "peft", "accelerate",
                                                                 "tokenizers", "safetensors", "bitsandbytes", "numpy")},
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
        if through == "report" and (output / "report.json").exists():
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
        # Check every training example before baseline inference, without truncation.
        for row in data["train"]:
            encode_example(tokenizer, row, config["max_length"])
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
    parser.add_argument("--through", choices=("baseline", "train", "report"), default="report")
    args = parser.parse_args()
    run(args.config, args.output, args.through)


if __name__ == "__main__":
    main()
