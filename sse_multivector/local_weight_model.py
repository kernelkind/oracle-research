"""Bounded persistent local-weight inference, served only on loopback.

Native causal text generation reuses the distillation loader. An optional
pointer decision checkpoint uses its pinned upstream encoder and head.
"""
import gc
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
import time

from sse_multivector.distillation_benchmark import admit, available_memory
from sse_multivector.distillation_run import load_model, read_json, sha256


class LocalWeights:
    def __init__(self, path):
        import torch
        from transformers import AutoTokenizer
        self.config = c = read_json(path)
        self.config_sha256 = sha256(path)
        if (c['kind'] not in {'causal_lm', 'pointer'} or len(c['revision']) != 40
                or c['quantization'] not in {'none', 'nf4'}):
            raise ValueError('expected a pinned causal LM or pointer checkpoint')
        admit(c, available_memory())
        torch.set_num_threads(4)
        total = torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(min(1., c['memory_budget_gib'] * 2**30 / total))
        self.name = f"{c['model']}/{c['revision']}/{self.config_sha256}"
        self.tokenizer = AutoTokenizer.from_pretrained(c['model'], revision=c['revision'])
        model = load_model(dict(c, device='cuda', max_length=c['max_input_tokens'], efficient_attention=True))
        self.head = self.encoder = None
        if c['kind'] == 'pointer':
            from peft import PeftModel, prepare_model_for_kbit_training
            from huggingface_hub import snapshot_download
            upstream = Path(c['upstream_path'])
            if sha256(upstream/'kev'/'model.py') != c['upstream_model_sha256']:
                raise ValueError('pointer implementation differs from its pinned source')
            sys.path.insert(0, str(upstream))
            from kev.model import encode, PointerHead
            adapter = snapshot_download(c['adapter'], revision=c['adapter_revision'],
                                        allow_patterns=['*.json', '*.safetensors', 'head.pt'])
            meta = torch.load(Path(adapter)/'head.pt', map_location='cpu', weights_only=True)
            if (meta['base'] != c['model'] or meta.get('base_revision') != c['revision']
                    or meta.get('option_isolation', False) or meta.get('special_embeddings', False)):
                raise ValueError('unsupported pointer checkpoint or mismatched foundation')
            backbone = model.model
            if c.get('trainable', False):
                backbone = prepare_model_for_kbit_training(backbone, use_gradient_checkpointing=True)
            self.model = PeftModel.from_pretrained(backbone, adapter, is_trainable=c.get('trainable', False))
            self.head = PointerHead(self.model.config.hidden_size, meta.get('head_dim', 256)).to('cuda')
            self.head.load_state_dict(meta['head'], strict=True)
            self.head.temperature = meta.get('temperature', 1.)
            self.head.eval()
            self.encoder = encode
            self.adapter_path = adapter
            self.meta = meta
            del model
            gc.collect()
            torch.cuda.empty_cache()
        else:
            self.model = model
        self.model.eval()

    def pointer_logits(self, encoded):
        import torch
        inputs = {k: torch.tensor([v], device='cuda') for k, v in
                  [('input_ids', encoded['ids']), ('position_ids', encoded['pos'])]}
        inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])
        with torch.autocast('cuda', dtype=torch.bfloat16):
            h = self.model(**inputs).last_hidden_state[0].float()
            return self.head(h[encoded['decide_idx'][0]], h[encoded['opt_idx'][0]])

    def complete(self, body):
        import torch
        c = self.config
        if body['model'] != self.name or len(body['messages']) != 1 or body['messages'][0]['role'] != 'user':
            raise ValueError('request differs from the loaded model or one-user-message contract')
        if available_memory() < c['reserve_gib'] * 2**30:
            raise ValueError('system memory fell below reserve')
        prompt = body['messages'][0]['content']
        metadata = {'config_sha256': self.config_sha256, 'quantization': c['quantization']}
        torch.cuda.reset_peak_memory_stats()
        start = time.monotonic()
        with torch.inference_mode():
            if self.encoder is not None:
                question = c['question']
                keys = list(question['criteria'])
                record = {'state': prompt, 'questions': [{'instr': question['instructions'],
                          'options': [f'{k}: {question["criteria"][k]}' for k in keys], 'label': 0}]}
                encoded = self.encoder(self.tokenizer, record, max_state=c['max_input_tokens'],
                                       max_branch=c['max_input_tokens'], strict=True)
                tokens = len(encoded['ids'])
                if tokens > c['max_input_tokens']:
                    raise ValueError('complete pointer input exceeds its configured limit')
                z = self.pointer_logits(encoded)
                p = z.float().softmax(-1)
                if not torch.isfinite(p).all():
                    raise ValueError('nonfinite pointer scores')
                raw = json.dumps({question['output_field']: keys[p.argmax().item()],
                                  **{k: '' for k in question.get('empty_fields', [])}})
                metadata['probabilities'] = dict(zip(keys, p.cpu().tolist()))
                output_tokens, stop = 0, 'stop'
            else:
                inputs = self.tokenizer.apply_chat_template(body['messages'], add_generation_prompt=True,
                    enable_thinking=False, tokenize=True, return_dict=True, return_tensors='pt')
                tokens = inputs['input_ids'].shape[-1]
                cap = min(body.get('max_tokens', c['max_new_tokens']), c['max_new_tokens'])
                if tokens + cap > c['max_input_tokens']:
                    raise ValueError('complete chat input plus output reserve exceeds its configured limit')
                inputs = {k: v.to('cuda') for k, v in inputs.items()}
                output = self.model.generate(**inputs, max_new_tokens=cap, do_sample=False,
                                             pad_token_id=self.tokenizer.eos_token_id)
                generated = output[0, tokens:]
                output_tokens = len(generated)
                raw = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
                eos = self.model.generation_config.eos_token_id
                stop = 'stop' if generated[-1].item() in ([eos] if isinstance(eos, int) else eos) else 'length'
        torch.cuda.synchronize()
        metadata.update(seconds=time.monotonic()-start, input_tokens=tokens,
                        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated())
        return {'model': self.name, 'raw_text': raw, 'stop_reason': stop, 'metadata': metadata,
                'usage': {'input': tokens, 'output': output_tokens, 'cacheRead': 0, 'cacheWrite': 0}}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if self.path != '/complete':
                raise ValueError('unknown local endpoint')
            count = int(self.headers['Content-Length'])
            if not 0 < count <= 8*1024*1024:
                raise ValueError('invalid request length')
            reply = self.server.backend.complete(json.loads(self.rfile.read(count)))
            status = 200
        except Exception as error:
            reply, status = {'error': f'{type(error).__name__}: {error}'}, 400
        encoded = json.dumps(reply, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def serve(path, port):
    backend = LocalWeights(path)
    with HTTPServer(('127.0.0.1', port), Handler) as server:
        server.backend = backend
        print(json.dumps({'ready': True, 'model': backend.name}), flush=True)
        server.serve_forever()
