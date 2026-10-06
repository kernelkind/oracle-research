"""Measure local five-way classification capacity with synthetic token tensors.

No teachers, corpus labels, prompt experiments, quality claims or rentals.
Encoder full/LoRA training and causal-LM LoRA use native model code; the latter
reuses the existing subject training loader. All outputs belong under target/.
"""
import argparse
import gc
import importlib.metadata
import math
import os
import platform
import re
import statistics
import time
from pathlib import Path

from sse_multivector.distillation_run import (
    file_hashes, read_json, sha256, subject_training_model, write_json)


def validate_config(config):
    fields = {"model", "revision", "architecture", "method", "lengths", "train_batch_size",
              "inference_batch_sizes", "steps", "warmup_steps", "repetitions", "learning_rate",
              "memory_budget_gib", "reserve_gib", "seed"}
    if not fields <= set(config) <= fields | {"quantization", "pointer_config"}:
        raise ValueError("unexpected or missing benchmark configuration fields")
    if not re.fullmatch(r"[0-9a-f]{40}", config["revision"]):
        raise ValueError("model revision must be an immutable commit")
    if config["architecture"] not in {"encoder", "causal_lm", "pointer"} or config["method"] not in {"full", "lora"}:
        raise ValueError("expected encoder/causal_lm/pointer and full/lora")
    if config["architecture"] in {"causal_lm", "pointer"} and config["method"] != "lora":
        raise ValueError("causal LM and pointer benchmarks require LoRA")
    if (config['architecture'] == 'pointer') != ('pointer_config' in config):
        raise ValueError('pointer_config is required only for native pointer training')
    if 'pointer_config' in config and (not isinstance(config['pointer_config'], str) or not config['pointer_config']):
        raise ValueError('pointer_config must name the pinned native configuration')
    quantization = config.get("quantization", "none")
    if quantization not in {"none", "nf4"} or quantization != "none" and config["architecture"] not in {"causal_lm", "pointer"}:
        raise ValueError("quantization must be none, or nf4 for causal/pointer LoRA")
    for name in ("lengths", "inference_batch_sizes"):
        values = config[name]
        if not isinstance(values, list) or not values or any(type(n) is not int or n <= 0 for n in values):
            raise ValueError(f"{name} must contain positive integers")
    if config['architecture'] == 'pointer' and min(config['lengths']) < 7:
        raise ValueError('pointer lengths require five distinct option positions and a decision position')
    for name in ("train_batch_size", "steps", "warmup_steps", "repetitions"):
        if type(config[name]) is not int or config[name] <= 0:
            raise ValueError(f"{name} must be a positive integer")
    for name in ("learning_rate", "memory_budget_gib", "reserve_gib"):
        if not isinstance(config[name], (int, float)) or not math.isfinite(config[name]) or config[name] <= 0:
            raise ValueError(f"{name} must be positive and finite")
    if type(config["seed"]) is not int or not isinstance(config["model"], str) or not config["model"]:
        raise ValueError("expected model identity and integer seed")


def available_memory():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise ValueError("system MemAvailable unavailable")


def admit(config, available):
    if available < (config["memory_budget_gib"] + config["reserve_gib"]) * 2 ** 30:
        raise ValueError("insufficient available system memory for benchmark budget plus reserve")


def run(config_path, output, *, stage='all'):
    import torch
    from transformers import AutoConfig, AutoModelForSequenceClassification
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training

    config_path, output = Path(config_path).resolve(), Path(output).resolve()
    config = read_json(config_path)
    validate_config(config)
    if stage not in {'all', 'train', 'verify'}:
        raise ValueError('benchmark stage must be all, train or verify')
    if output.exists() and stage != 'verify':
        raise FileExistsError(output)
    available = available_memory()
    admit(config, available)
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise ValueError("benchmark requires BF16 CUDA")
    output.mkdir(parents=True, exist_ok=stage == 'verify')
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(min(1., config["memory_budget_gib"] * 2 ** 30 / total))
    torch.manual_seed(config["seed"])
    torch.set_num_threads(4)
    report = {"schema_version": 1, "workload": "synthetic token tensors, five labels; no SHR quality estimate",
              "config": config, "config_sha256": sha256(config_path),
              "code_sha256": {str(p): sha256(p) for p in (Path(__file__), Path(__file__).with_name("distillation_run.py"))},
              "system": {"architecture": platform.machine(), "gpu": torch.cuda.get_device_name(0),
                         "available_bytes_before_load": available, "cuda_total_bytes": total},
              "versions": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft")},
              "training": [], "inference": [], "complete": False}
    if stage == 'verify':
        report = read_json(output/'report.json')
        if (report['config_sha256'] != sha256(config_path) or not report.get('checkpoint_saved')
                or report['checkpoint_hashes'] != file_hashes(output/'checkpoint')):
            raise ValueError('checkpoint or configuration differs from saved training')
        if report['complete']:
            raise ValueError('checkpoint verification is already complete')
        for name, digest in report['code_sha256'].items():
            if sha256(Path(__file__).with_name(Path(name).name)) != digest:
                raise ValueError('checkpoint verification code differs from training')

    def publish():
        write_json(output / "report.json", report)

    def sync_time():
        torch.cuda.synchronize()
        return time.perf_counter()

    def reserve():
        if available_memory() < config["reserve_gib"] * 2 ** 30:
            raise ValueError("system memory fell below the configured reserve")

    lm_config = dict(model=config["model"], revision=config["revision"], device="cuda",
                     quantization=config.get("quantization", "none"), max_length=max(config["lengths"]), efficient_attention=True,
                     lora_target_modules="all-linear", lora_rank=16, lora_alpha=32,
                     gradient_checkpointing=True)

    pointer = None

    def load(checkpoint=None):
        nonlocal pointer
        if config['architecture'] == 'pointer':
            from sse_multivector.local_weight_model import LocalWeights
            path = (config_path.parent / config['pointer_config']).resolve()
            native = read_json(path)
            if (native['kind'] != 'pointer' or any(native[k] != config[k] for k in
                    ('model', 'revision', 'quantization', 'memory_budget_gib', 'reserve_gib'))):
                raise ValueError('pointer source or resource binding differs from benchmark')
            report['pointer_config_sha256'] = sha256(path)
            report['code_sha256']['local_weight_model.py'] = sha256(Path(__file__).with_name('local_weight_model.py'))
            report['pointer_upstream_model_sha256'] = native['upstream_model_sha256']
            pointer = LocalWeights(path)
            pointer.model = prepare_model_for_kbit_training(pointer.model, use_gradient_checkpointing=True)
            if checkpoint:
                if isinstance(pointer.model, PeftModel):
                    pointer.model.delete_adapter('default')
                    pointer.model.load_adapter(checkpoint, adapter_name='default', is_trainable=True)
                else:
                    pointer.model = PeftModel.from_pretrained(pointer.model, checkpoint, is_trainable=True)
                saved = torch.load(checkpoint / 'head.pt', map_location='cpu', weights_only=True)
                if saved['source_config_sha256'] != sha256(path):
                    raise ValueError('saved pointer head source binding differs')
                pointer.head.load_state_dict(saved['head'], strict=True)
                pointer.head.temperature = saved['temperature']
            elif not isinstance(pointer.model, PeftModel):
                pointer.model = get_peft_model(pointer.model, LoraConfig(task_type='FEATURE_EXTRACTION',
                    target_modules='all-linear', r=16, lora_alpha=32, lora_dropout=0.))
            pointer.model.set_adapter('default')
            pointer.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            pointer.model.config.use_cache = False
            return pointer.model
        if config["architecture"] == "causal_lm":
            return subject_training_model(lm_config, checkpoint)
        options = dict(num_labels=5, dtype=torch.float32, device_map={"": "cuda"},
                       trust_remote_code=False)
        architecture = AutoConfig.from_pretrained(checkpoint if checkpoint and config["method"] == "full"
                                                 else config["model"], revision=config["revision"])
        if architecture.model_type == "modernbert":
            options.update(attn_implementation="sdpa")
        if checkpoint and config["method"] == "full":
            return AutoModelForSequenceClassification.from_pretrained(checkpoint, **options)
        model = AutoModelForSequenceClassification.from_pretrained(
            config["model"], revision=config["revision"], ignore_mismatched_sizes=True, **options)
        if config["method"] == "lora":
            model = (PeftModel.from_pretrained(model, checkpoint, is_trainable=True) if checkpoint else
                     get_peft_model(model, LoraConfig(task_type="SEQ_CLS", target_modules="all-linear",
                                                     r=16, lora_alpha=32, lora_dropout=0.)))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        return model

    def batch(length, size):
        return {"input_ids": torch.randint(5, model.config.vocab_size, (size, length), device="cuda"),
                "attention_mask": torch.ones((size, length), dtype=torch.long, device="cuda")}

    def logits(inputs):
        with torch.autocast("cuda", dtype=torch.bfloat16):
            if pointer is not None:
                h = model(**inputs).last_hidden_state.float()
                size, length, width = h.shape
                ends = torch.linspace(1, length - 2, 5, device='cuda').long()
                owner = torch.arange(size, device='cuda').repeat_interleave(5)
                return pointer.head.many(h[:, -1], h[:, ends].reshape(-1, width), owner).reshape(size, 5)
            if config["architecture"] == "encoder":
                return model(**inputs).logits
            # Qwen's native one-position projection avoids projecting the whole
            # synthetic sequence over its vocabulary merely to score five IDs.
            return model(**inputs, logits_to_keep=1).logits[:, -1, 1000:1005]

    publish()
    try:
        checkpoint = output/'checkpoint'
        if stage == 'verify':
            saved = torch.load(checkpoint/'probe.pt', map_location='cpu', weights_only=True)
            if saved['config_sha256'] != sha256(config_path):
                raise ValueError('synthetic probe configuration differs')
            probe = {k: v.to('cuda') for k, v in saved['inputs'].items()}
            before = saved['logits']
        else:
            start = sync_time()
            model = load()
            report["load_seconds"] = sync_time() - start
            report['gradient_checkpointing'] = model.is_gradient_checkpointing
            limit = getattr(model.config, "max_position_embeddings", None)
            if limit is not None and max(config["lengths"]) > limit:
                raise ValueError("requested complete sequence exceeds model position limit")
            parameters = [p for p in model.parameters() if p.requires_grad]
            if pointer is not None:
                parameters += list(pointer.head.parameters())
            stored = sum(p.numel() for p in model.parameters())
            # PEFT accounts for the packed storage of four-bit weights.
            total = model.get_nb_trainable_parameters()[1] if config["method"] == "lora" else stored
            if pointer is not None:
                total += sum(p.numel() for p in pointer.head.parameters())
                stored += sum(p.numel() for p in pointer.head.parameters())
            report["parameters"] = {"total": total, "stored_tensor_elements": stored,
                                    "trainable": sum(p.numel() for p in parameters)}
            if pointer is not None:
                report['parameters']['pointer_head'] = sum(p.numel() for p in pointer.head.parameters())
            optimizer = torch.optim.AdamW(parameters, lr=config["learning_rate"])
            for length in config["lengths"]:
                model.train()
                if pointer is not None:
                    pointer.head.train()
                inputs = batch(length, config["train_batch_size"])
                times, losses, warmup = [], [], []
                torch.cuda.reset_peak_memory_stats()
                for step in range(config["warmup_steps"] + config["steps"]):
                    reserve()
                    start = sync_time()
                    optimizer.zero_grad(set_to_none=True)
                    labels = (torch.arange(config["train_batch_size"], device="cuda") + step) % 5
                    loss = torch.nn.functional.cross_entropy(logits(inputs).float(), labels)
                    loss.backward()
                    norm = torch.nn.utils.clip_grad_norm_(parameters, 1.)
                    if not torch.isfinite(loss) or not torch.isfinite(norm) or norm <= 0:
                        raise ValueError("nonfinite loss/gradient or zero gradient")
                    optimizer.step()
                    seconds = sync_time() - start
                    (warmup if step < config["warmup_steps"] else times).append(seconds)
                    losses.append(loss.item())
                report["training"].append({"tokens_per_example": length, "batch_size": config["train_batch_size"],
                    "steps": config["steps"], "step_seconds": times, "warmup_step_seconds": warmup,
                    "median_step_seconds": statistics.median(times), "losses": losses,
                    "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "available_system_bytes_after": available_memory()})
                publish()
            optimizer.zero_grad(set_to_none=True)
            del optimizer, parameters, inputs, loss, norm
            model.eval()
            if pointer is not None:
                pointer.head.eval()
            probe = batch(min(config["lengths"]), 1)
            with torch.inference_mode():
                before = logits(probe).float().cpu()
            checkpoint = output / "checkpoint"
            start = sync_time()
            model.save_pretrained(checkpoint)
            if pointer is not None:
                torch.save({'head': pointer.head.state_dict(), 'temperature': pointer.head.temperature,
                            'source_config_sha256': report['pointer_config_sha256']}, checkpoint / 'head.pt')
            torch.save({'inputs': {k: v.cpu() for k, v in probe.items()}, 'logits': before,
                        'config_sha256': sha256(config_path)}, checkpoint / 'probe.pt')
            report["save_seconds"] = sync_time() - start
            report["checkpoint_hashes"] = file_hashes(checkpoint)
            report['checkpoint_saved'] = True
            report['training_pid'] = os.getpid()
            report['awaiting_verification'] = True
            del model
            pointer = None
            gc.collect()
            torch.cuda.empty_cache()
            if stage == 'train':
                return report
        start = sync_time()
        model = load(checkpoint)
        report["reload_seconds"] = sync_time() - start
        report['verification_pid'] = os.getpid()
        model.eval()
        if pointer is not None:
            pointer.head.eval()
        with torch.inference_mode():
            after = logits(probe).float().cpu()
        torch.testing.assert_close(after, before, rtol=1e-4, atol=1e-4)
        report["reload_matches"] = True
        for length in config["lengths"]:
            for size in config["inference_batch_sizes"]:
                reserve()
                inputs = batch(length, size)
                torch.cuda.reset_peak_memory_stats()
                with torch.inference_mode():
                    logits(inputs)  # Unmeasured inference warmup for this shape.
                    times = []
                    for _ in range(config["repetitions"]):
                        start = sync_time()
                        values = logits(inputs)
                        seconds = sync_time() - start
                        if values.shape != (size, 5) or not torch.isfinite(values).all():
                            raise ValueError("invalid five-way inference scores")
                        times.append(seconds)
                median = statistics.median(times)
                report["inference"].append({"tokens_per_example": length, "batch_size": size,
                    "seconds": times, "median_batch_seconds": median, "examples_per_second": size / median,
                    "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated()})
                publish()
        report["complete"] = True
        report['awaiting_verification'] = False
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        publish()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument('--stage', choices=['all', 'train', 'verify'], default='all',
                        help='verify a saved synthetic probe in a fresh worker without repeating training')
    args = parser.parse_args()
    result = run(args.config, args.output, stage=args.stage)
    action = 'Completed' if result['complete'] else 'Saved checkpoint; verification pending'
    print(f"{action} {result['config']['model']}: {args.output / 'report.json'}")


if __name__ == "__main__":
    main()
