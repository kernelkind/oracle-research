"""Bounded persistent local-weight inference, served only on loopback.

Native causal text generation reuses the distillation loader. An optional
pointer decision checkpoint uses its pinned upstream encoder and head.
"""
import gc
import importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
import string
import sys
import time
from types import SimpleNamespace

from sse_multivector.distillation_benchmark import admit, available_memory
from sse_multivector.distillation_run import load_model, read_json, sha256


def checkpoint_name(config, config_sha256):
    key = 'adapter' if 'adapter' in config else 'model'
    revision = config['adapter_revision'] if key == 'adapter' else config['revision']
    return f'{config[key]}/{revision}/{config_sha256}'


def choice_prompt(state, question, readout):
    """Preserve the complete state and make the answer interface explicit."""
    keys = list(question['criteria'])
    if not 2 <= len(keys) <= 26 or readout not in {'generation', 'options'}:
        raise ValueError('expected 2 to 26 choices and a supported readout')
    codes = list(string.ascii_uppercase[:len(keys)])
    options = '\n'.join(f'({code}) {key}: {question["criteria"][key]}'
                        for code, key in zip(codes, keys))
    suffix = ('Return the JSON object requested by the state, using the selected relation label.'
              if readout == 'generation' else
              'For this answer, return only the selected option letter, replacing the earlier JSON output format.')
    return state + '\n\n# Decision question\n' + question['instructions'] + '\nOptions:\n' + options + '\n' + suffix


class LocalWeights:
    def __init__(self, path):
        import torch
        from transformers import AutoTokenizer
        self.config = c = read_json(path)
        self.config_sha256 = sha256(path)
        if (c['kind'] not in {'causal_lm', 'pointer'} or len(c['revision']) != 40
                or c['quantization'] not in {'none', 'nf4'}
                or c.get('readout', 'generation') not in {'generation', 'options'}
                or c.get('prompt_layout', 'chat') not in {'chat', 'schema', 'decider'}):
            raise ValueError('expected a pinned causal LM or pointer checkpoint')
        admit(c, available_memory())
        torch.set_num_threads(4)
        total = torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(min(1., c['memory_budget_gib'] * 2**30 / total))
        self.name = checkpoint_name(c, self.config_sha256)
        self.tokenizer = AutoTokenizer.from_pretrained(c['model'], revision=c['revision'])
        full_pointer = c['kind'] == 'pointer' and 'adapter' not in c
        model = load_model(dict(c, device='cuda', max_length=c['max_input_tokens'], efficient_attention=True,
                               backbone_only=full_pointer))
        self.head = self.encoder = self.choice_encoder = self.decider_encoder = None
        if c['kind'] == 'pointer':
            from peft import PeftModel
            from huggingface_hub import snapshot_download
            upstream = Path(c['upstream_path'])
            if sha256(upstream/'kev'/'model.py') != c['upstream_model_sha256']:
                raise ValueError('pointer implementation differs from its pinned source')
            sys.path.insert(0, str(upstream))
            from kev.model import encode, PointerHead
            repository = c['model'] if full_pointer else c['adapter']
            revision = c['revision'] if full_pointer else c['adapter_revision']
            checkpoint = (repository if Path(repository).is_dir() else snapshot_download(
                repository, revision=revision, allow_patterns=['*.json', '*.safetensors', 'head.pt']))
            meta = torch.load(Path(checkpoint)/'head.pt', map_location='cpu', weights_only=True)
            base = c['base_model'] if full_pointer else c['model']
            base_revision = c['base_revision'] if full_pointer else c['revision']
            if (meta['base'] != base or meta.get('base_revision') != base_revision
                    or (meta.get('weights') == 'full') != full_pointer
                    or meta.get('option_isolation', False) or meta.get('special_embeddings', False)):
                raise ValueError('unsupported pointer checkpoint or mismatched foundation')
            self.model = (model if full_pointer else
                          PeftModel.from_pretrained(model.model, checkpoint, is_trainable=False))
            self.head = PointerHead(self.model.config.hidden_size, meta.get('head_dim', 256)).to('cuda')
            self.head.load_state_dict(meta['head'], strict=True)
            self.head.temperature = meta.get('temperature', 1.)
            self.head.eval()
            self.encoder = encode
            if not full_pointer:
                self.adapter_path = checkpoint
            self.meta = meta
            del model
            gc.collect()
            torch.cuda.empty_cache()
        else:
            self.model = model
            if 'adapter' in c:
                from peft import PeftModel, get_peft_model_state_dict
                from peft.utils.save_and_load import load_peft_weights
                from huggingface_hub import snapshot_download
                adapter = (c['adapter'] if Path(c['adapter']).is_dir() else snapshot_download(
                    c['adapter'], revision=c['adapter_revision'], allow_patterns=['*.json', '*.safetensors']))
                if sha256(Path(adapter)/'adapter_model.safetensors') != c['adapter_sha256']:
                    raise ValueError('causal adapter weight hash differs')
                mapping = c.get('adapter_key_mapping')
                self.model = PeftModel.from_pretrained(model, adapter, is_trainable=False, key_mapping=mapping)
                expected = load_peft_weights(adapter, device='cpu', key_mapping=mapping)
                actual = get_peft_model_state_dict(self.model)
                if (set(actual) != set(expected) or any(
                        not torch.equal(actual[k].cpu(), expected[k].to(actual[k].dtype)) for k in actual)):
                    raise ValueError('causal adapter weights differ after loading')
                self.adapter_path = adapter
            if c.get('prompt_layout') in {'schema', 'decider'}:
                upstream = Path(c['upstream_path'])
                for name, expected in c['upstream_source_sha256'].items():
                    if Path(name).name != name or sha256(upstream/name) != expected:
                        raise ValueError('schema prompt source differs from its pinned implementation')
                if c['prompt_layout'] == 'schema':
                    sys.path.insert(0, str(upstream))
                    from serving_schema import prepare_prompts
                    self.choice_encoder = prepare_prompts
                else:
                    spec = importlib.util.spec_from_file_location('decider_prompt', upstream/'prompt.py')
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.decider_encoder = module.build
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
        prefix = c.get('answer_prefix', '')
        if (not isinstance(prefix, str) or prefix and (c['kind'] != 'causal_lm'
                or c.get('readout', 'generation') != 'options' or c.get('prompt_layout', 'chat') != 'chat')):
            raise ValueError('answer_prefix requires chat option scoring')
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
                readout = c.get('readout', 'generation')
                messages = body['messages']
                choice_encoder = getattr(self, 'choice_encoder', None)
                decider_encoder = getattr(self, 'decider_encoder', None)
                if decider_encoder is not None:
                    if readout != 'options':
                        raise ValueError('decider layout requires option scoring')
                    if len(self.tokenizer.encode('Context:\n' + prompt, add_special_tokens=False)) > c['max_input_tokens']:
                        raise ValueError('complete decider state exceeds its configured limit')
                    question = c['question']
                    keys = list(question['criteria'])
                    record = SimpleNamespace(context=prompt, qs=[SimpleNamespace(text=question['instructions'],
                        options=[f'{k}: {question["criteria"][k]}' for k in keys], gold=0)])
                    prepared = decider_encoder(record, self.tokenizer,
                        rng=SimpleNamespace(shuffle=lambda options: None), max_options=len(keys),
                        max_ctx_tokens=c['max_input_tokens'])
                    if prepared['perms'] != [list(range(len(keys)))] or prepared['slots'] != [len(prepared['ids'])-1]:
                        raise ValueError('decider option order or answer slot differs')
                    inputs = {'input_ids': torch.tensor([prepared['ids']])}
                    inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])
                    metadata['choice_prompt'] = self.tokenizer.decode(prepared['ids'], skip_special_tokens=False)
                elif choice_encoder is not None:
                    if readout != 'options':
                        raise ValueError('schema layout requires option scoring')
                    question = c['question']
                    schema = {question['output_field']: {'type': 'enum', 'description': question['instructions'],
                        'choices': list(question['criteria']), 'choice_descriptions': question['criteria']}}
                    prepared = choice_encoder(self.tokenizer, prompt, schema, c['max_input_tokens'])
                    inputs = {'input_ids': torch.tensor([prepared.full_ids[0]])}
                    inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])
                    metadata['choice_prompt'] = self.tokenizer.decode(prepared.full_ids[0], skip_special_tokens=False)
                elif 'question' in c:
                    prompt = choice_prompt(prompt, c['question'], readout)
                    messages = [{'role': 'user', 'content': prompt}]
                    metadata['choice_prompt'] = prompt
                elif readout == 'options':
                    raise ValueError('option scoring requires a choice question')
                if choice_encoder is None and decider_encoder is None:
                    if prefix:
                        rendered = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                            enable_thinking=False, tokenize=False) + prefix
                        inputs = self.tokenizer(rendered, add_special_tokens=False, return_tensors='pt')
                        metadata.update(answer_prefix=prefix, scoring_prompt=rendered)
                    else:
                        inputs = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                            enable_thinking=False, tokenize=True, return_dict=True, return_tensors='pt')
                inputs.pop('token_type_ids', None)
                tokens = inputs['input_ids'].shape[-1]
                cap = (1 if readout == 'options' else
                       min(body.get('max_tokens', c['max_new_tokens']), c['max_new_tokens']))
                if tokens + cap > c['max_input_tokens']:
                    raise ValueError('complete chat input plus output reserve exceeds its configured limit')
                inputs = {k: v.to('cuda') for k, v in inputs.items()}
                if readout == 'options':
                    keys = list(c['question']['criteria'])
                    codes = list(string.ascii_uppercase[:len(keys)])
                    encoded = [self.tokenizer.encode(code, add_special_tokens=False) for code in codes]
                    if (any(len(row) != 1 or row[0] in self.tokenizer.all_special_ids for row in encoded)
                            or len({row[0] for row in encoded}) != len(keys)):
                        raise ValueError('option codes must be distinct single tokens')
                    if choice_encoder is not None:
                        if [row[0] for row in encoded] != prepared.candidate_ids[0]:
                            raise ValueError('schema option codes differ at the answer boundary')
                    elif decider_encoder is None:
                        rendered = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                            enable_thinking=False, tokenize=False) + prefix
                        input_ids = inputs['input_ids'][0].tolist()
                        if any(self.tokenizer.encode(rendered + code, add_special_tokens=False) != input_ids + row
                               for code, row in zip(codes, encoded)):
                            raise ValueError('option code tokenization changes at the answer boundary')
                    temperature = c.get('temperature', 1.)
                    if isinstance(temperature, bool) or not math.isfinite(temperature) or temperature <= 0:
                        raise ValueError('choice temperature must be positive and finite')
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        logits = self.model(**inputs, use_cache=False, logits_to_keep=1).logits[0, -1].float()
                    z = logits[[row[0] for row in encoded]]
                    if not torch.isfinite(logits).all():
                        raise ValueError('nonfinite language-model scores')
                    p = (z / temperature).softmax(-1)
                    top = logits.argmax().item()
                    metadata.update(probabilities=dict(zip(keys, p.cpu().tolist())),
                        option_logits=dict(zip(keys, z.cpu().tolist())), option_codes=dict(zip(keys, codes)),
                        option_probability_mass=(z.logsumexp(-1)-logits.logsumexp(-1)).exp().item(),
                        unrestricted_top_token_id=top, unrestricted_top_token=self.tokenizer.decode([top]),
                        temperature=temperature, readout=readout)
                    raw = json.dumps({c['question']['output_field']: keys[p.argmax().item()],
                                      **{k: '' for k in c['question'].get('empty_fields', [])}})
                    output_tokens, stop = 0, 'stop'
                else:
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
