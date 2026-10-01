import hashlib
import json
import math
import struct
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch
from pathlib import Path

from sse_multivector.worker import (
    EncodedSubject,
    WorkerConfig,
    canonical_tree_sha256,
    select_token_indices,
    run_worker,
    validate_token_lengths,
)


class DeterministicEncoder:
    def __init__(self) -> None:
        self.calls = []

    def encode(self, notes):
        self.calls.append(notes)
        rows = []
        for note in notes:
            for subject in note.subjects:
                rows.append(
                    EncodedSubject(
                        note_id=note.note_id,
                        subject_id=subject.subject_id,
                        vector=(
                            float(len(note.text)),
                            float(len(subject.byte_spans)),
                            float(int(subject.subject_id[-1], 16) + 1),
                        ),
                        selected_token_indices=tuple(
                            range(1, len(subject.byte_spans) + 1)
                        ),
                        selected_token_ids=tuple(
                            range(101, 101 + len(subject.byte_spans))
                        ),
                        token_count=max(2, len(note.text)),
                    )
                )
        return rows


class WorkerTests(unittest.TestCase):
    def test_rejects_overlong_notes_instead_of_truncating_them(self):
        validate_token_lengths((("11" * 32, 512),), maximum_tokens=512)
        with self.assertRaisesRegex(
            ValueError, "tokenizes to 513 tokens.*truncation is forbidden"
        ):
            validate_token_lengths((("22" * 32, 513),), maximum_tokens=512)

    def test_maps_utf8_byte_spans_to_wholly_contained_non_special_tokens(self):
        text = "☕ Rust + Rust!"
        encoded = text.encode("utf-8")
        second_rust_start = encoded.rindex(b"Rust")
        second_rust_end = second_rust_start + len(b"Rust")
        offsets = [
            (0, 0),
            (0, 1),
            (2, 6),
            (7, 8),
            (9, 13),
            (13, 14),
            (0, 0),
        ]

        selected = select_token_indices(
            text,
            ((second_rust_start, second_rust_end),),
            offsets,
        )

        self.assertEqual((4,), selected)

    def test_unions_discontinuous_spans_but_rejects_empty_token_masks(self):
        text = "Rust while drinking tea"
        offsets = [(0, 4), (5, 10), (11, 19), (20, 23), (0, 0)]
        encoded = text.encode("utf-8")
        rust = (encoded.index(b"Rust"), encoded.index(b"Rust") + len(b"Rust"))
        tea = (encoded.index(b"tea"), encoded.index(b"tea") + len(b"tea"))

        self.assertEqual(
            (0, 3),
            select_token_indices(text, (rust, tea), offsets),
        )
        with self.assertRaisesRegex(ValueError, "selects no complete tokenizer token"):
            select_token_indices(text, ((1, 3),), offsets)

    def test_adjacent_fragments_select_tokens_covered_by_their_union(self):
        text = "☕ grownostr"
        offsets = [(0, 1), (2, 7), (7, 10), (10, 11), (0, 0)]
        # UTF-8 spans split grow|nostr inside the first word token.
        whole = ((4, 13),)
        split = ((4, 8), (8, 13))
        expected = select_token_indices(text, whole, offsets)
        self.assertEqual(expected, (1, 2, 3))
        self.assertEqual(select_token_indices(text, split, offsets), expected)
        self.assertEqual(select_token_indices(text, ((4, 8), (7, 13)), offsets), expected)
        self.assertEqual(select_token_indices(text, ((4, 8), (8, 10), (10, 13)), offsets), expected)

    def test_fragment_union_never_fills_a_gap_or_rounds_partial_tokens(self):
        text = "grownostr"
        offsets = [(0, 5), (5, 8), (8, 9)]
        self.assertEqual(select_token_indices(text, ((0, 3), (4, 9)), offsets), (1, 2))
        self.assertEqual(select_token_indices(text, ((1, 4), (4, 9)), offsets), (1, 2))

    def test_runs_one_grouped_request_and_publishes_bound_raw_vectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = {
                "schema_version": 1,
                "proposal_sha256": "ab" * 32,
                "notes": [
                    {
                        "note_id": "11" * 32,
                        "text": "Rust while drinking tea",
                        "subjects": [
                            {
                                "subject_id": "0000000000000001",
                                "byte_spans": [[0, 4]],
                            },
                            {
                                "subject_id": "0000000000000002",
                                "byte_spans": [[20, 23]],
                            },
                        ],
                    },
                    {
                        "note_id": "22" * 32,
                        "text": "Growing tomatoes!",
                        "subjects": [
                            {
                                "subject_id": "0000000000000003",
                                "byte_spans": [[0, 17]],
                            }
                        ],
                    },
                ],
            }
            request_path = root / "worker-input.json"
            request_bytes = (
                json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n"
            ).encode()
            request_path.write_bytes(request_bytes)
            checkpoint_path = root / "checkpoint.ckpt"
            checkpoint_path.write_bytes(b"official checkpoint fixture")
            tokenizer = root / "tokenizer"
            tokenizer.mkdir()
            (tokenizer / "tokenizer.json").write_text("{}\n")
            output = root / "worker-output"
            encoder = DeterministicEncoder()
            config = {
                "schema_version": 1,
                "request_path": str(request_path),
                "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_sha256": hashlib.sha256(
                    checkpoint_path.read_bytes()
                ).hexdigest(),
                "base_model_artifact_path": str(tokenizer),
                "base_model_artifact_tree_sha256": canonical_tree_sha256(tokenizer),
                "model": {
                    "base_model": "fixture/sentence-encoder",
                    "dimensions": 3,
                    "maximum_tokens": 512,
                    "pooling": ("selected-contextual-token-mean-linear-relu-linear-v1"),
                },
                "device": "cpu",
                "container_image": "sha256:" + ("ef" * 32),
                "note_batch_size": 2,
                "output_path": str(output),
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config, sort_keys=True) + "\n")

            with patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=encoder,
            ):
                report = run_worker(config_path)

            self.assertEqual(1, len(encoder.calls))
            self.assertEqual(2, len(encoder.calls[0]))
            self.assertEqual(3, report.row_count)
            self.assertEqual(3, report.dimensions)
            values = struct.unpack("<9f", (output / "raw-vectors.f32le").read_bytes())
            self.assertTrue(all(math.isfinite(value) for value in values))
            self.assertEqual(
                (
                    23.0,
                    1.0,
                    2.0,
                    23.0,
                    1.0,
                    3.0,
                    17.0,
                    1.0,
                    4.0,
                ),
                values,
            )
            receipt = json.loads((output / "worker-receipt.json").read_text())
            self.assertEqual(
                ["0000000000000001", "0000000000000002", "0000000000000003"],
                [row["subject_id"] for row in receipt["rows"]],
            )
            self.assertEqual(
                [23, 23, 17], [row["token_count"] for row in receipt["rows"]]
            )
            self.assertEqual(
                [[101], [101], [101]],
                [row["selected_token_ids"] for row in receipt["rows"]],
            )
            self.assertEqual(
                hashlib.sha256((output / "raw-vectors.f32le").read_bytes()).hexdigest(),
                receipt["files"]["raw-vectors.f32le"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256(request_bytes).hexdigest(),
                receipt["request_sha256"],
            )
            self.assertEqual(
                "sha256:" + ("ef" * 32),
                receipt["container_image"],
            )

    def test_rejects_labels_in_the_encoder_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = {
                "schema_version": 1,
                "proposal_sha256": "ab" * 32,
                "notes": [
                    {
                        "note_id": "11" * 32,
                        "text": "Rust",
                        "subjects": [
                            {
                                "subject_id": "0000000000000001",
                                "label": "Rust programming",
                                "byte_spans": [[0, 4]],
                            }
                        ],
                    }
                ],
            }
            request_path = root / "request.json"
            request_bytes = (
                json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n"
            ).encode()
            request_path.write_bytes(request_bytes)
            checkpoint = root / "checkpoint.ckpt"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer = root / "tokenizer"
            tokenizer.mkdir()
            (tokenizer / "tokenizer.json").write_text("{}")
            config = {
                "schema_version": 1,
                "request_path": str(request_path),
                "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                "checkpoint_path": str(checkpoint),
                "checkpoint_sha256": hashlib.sha256(
                    checkpoint.read_bytes()
                ).hexdigest(),
                "base_model_artifact_path": str(tokenizer),
                "base_model_artifact_tree_sha256": canonical_tree_sha256(tokenizer),
                "model": {
                    "base_model": "fixture/sentence-encoder",
                    "dimensions": 3,
                    "maximum_tokens": 512,
                    "pooling": ("selected-contextual-token-mean-linear-relu-linear-v1"),
                },
                "device": "cpu",
                "container_image": "fixture/sse@sha256:" + ("ef" * 32),
                "note_batch_size": 1,
                "output_path": str(root / "output"),
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config, sort_keys=True) + "\n")

            with patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=DeterministicEncoder(),
            ):
                with self.assertRaisesRegex(ValueError, "unexpected field.*label"):
                    run_worker(config_path)


class OfficialSsePoolingTests(unittest.TestCase):
    def setUp(self):
        try:
            import torch
            from tokenizers import Tokenizer, models, pre_tokenizers
            from transformers import PreTrainedTokenizerFast, T5Config, T5EncoderModel
        except ImportError:
            self.skipTest("SSE inference dependencies are not installed")
        self.torch = torch
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        artifact = self.root / "model"
        artifact.mkdir()
        tokenizer = Tokenizer(models.WordLevel(
            {"<unk>": 0, "<pad>": 1, "coffee": 2, "eggs": 3, "☕": 4},
            unk_token="<unk>",
        ))
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
        self.tokenizer = PreTrainedTokenizerFast(
            tokenizer_object=tokenizer, unk_token="<unk>", pad_token="<pad>",
            model_input_names=["input_ids", "attention_mask"],
        )
        self.tokenizer.save_pretrained(artifact)
        model_config = T5Config(vocab_size=5, d_model=4, d_ff=8, d_kv=2,
                                num_heads=2, num_layers=1, dropout_rate=0,
                                pad_token_id=1)
        model_config.save_pretrained(artifact)
        with torch.random.fork_rng():
            torch.manual_seed(8)
            self.reference = T5EncoderModel(model_config).float().eval()
        self.linear1 = torch.nn.Linear(4, 2)
        self.linear2 = torch.nn.Linear(2, 3)
        with torch.no_grad():
            self.linear1.weight.copy_(torch.tensor([[1., 0., -1., 0.],
                                                    [0., 1., 0., -1.]]))
            self.linear1.bias.copy_(torch.tensor([.25, -.5]))
            self.linear2.weight.copy_(torch.tensor([[1., 0.], [0., 1.], [1., -1.]]))
            self.linear2.bias.copy_(torch.tensor([.5, 1., -.25]))
        state = {"encoder." + k: v for k, v in self.reference.state_dict().items()}
        for name, layer in (("linear1", self.linear1), ("linear2", self.linear2)):
            state.update({"mlp." + name + "." + k: v
                          for k, v in layer.state_dict().items()})
        checkpoint = self.root / "checkpoint.ckpt"
        torch.save(dict(state_dict=state, hyper_parameters=dict(params=Namespace(
            model_name="fixture/t5", final_output_dim=3))), checkpoint)
        request = dict(schema_version=1, proposal_sha256="ab"*32, notes=[dict(
            note_id="11"*32, text="☕ coffee eggs coffee", subjects=[
                dict(subject_id="01"*8, byte_spans=[[4, 10], [16, 22]]),
                dict(subject_id="02"*8, byte_spans=[[0, 22]])])])
        self.request_path = self.root / "request.json"
        self.request_path.write_text(json.dumps(request, ensure_ascii=False))
        self.config = dict(schema_version=1, request_path=str(self.request_path),
            request_sha256=hashlib.sha256(self.request_path.read_bytes()).hexdigest(),
            checkpoint_path=str(checkpoint),
            checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            base_model_artifact_path=str(artifact),
            base_model_artifact_tree_sha256=canonical_tree_sha256(artifact),
            model=dict(base_model="fixture/t5", dimensions=3, maximum_tokens=32,
                       pooling="selected-contextual-token-mean-linear-relu-linear-v1"),
            device="cpu", container_image="sha256:"+"ef"*32, note_batch_size=1,
            output_path=str(self.root / "projected"))

    def run_config(self, pooling, dimensions, name):
        config = dict(self.config, model=dict(self.config["model"], pooling=pooling,
                      dimensions=dimensions), output_path=str(self.root / name))
        path = self.root / (name + ".json")
        path.write_text(json.dumps(config))
        run_worker(path)
        receipt = json.loads((self.root / name / "worker-receipt.json").read_text())
        raw = (self.root / name / "raw-vectors.f32le").read_bytes()
        return list(struct.iter_unpack("<" + "f"*dimensions, raw)), receipt

    def test_worker_emits_selected_token_mean_before_projection(self):
        torch = self.torch
        projected, projected_receipt = self.run_config(
            "selected-contextual-token-mean-linear-relu-linear-v1", 3, "projected")
        means, mean_receipt = self.run_config(
            "selected-contextual-token-mean-v1", 4, "means")
        tokens = self.tokenizer("☕ coffee eggs coffee", return_tensors="pt")
        with torch.inference_mode():
            hidden = self.reference(**tokens).last_hidden_state[0]
            # The first selection excludes both the emoji and eggs.
            for i, selected in enumerate(([1, 3], [0, 1, 2, 3])):
                expected = hidden[selected].mean(dim=0)
                self.assertEqual(means[i], tuple(expected.tolist()))
                transformed = self.linear2(torch.relu(self.linear1(expected)))
                self.assertEqual(projected[i], tuple(transformed.tolist()))
        self.assertEqual(projected_receipt["rows"], mean_receipt["rows"])
        self.assertEqual(mean_receipt["model"]["pooling"],
                         "selected-contextual-token-mean-v1")
        self.assertEqual(mean_receipt["dimensions"], 4)
        self.assertEqual(mean_receipt["request_sha256"],
                         projected_receipt["request_sha256"])
        self.assertEqual(mean_receipt["checkpoint_sha256"],
                         projected_receipt["checkpoint_sha256"])

    def test_mean_pooling_checks_backbone_dimensions_and_rejects_unknown_rules(self):
        with self.assertRaisesRegex(ValueError, "output dimension"):
            self.run_config("selected-contextual-token-mean-v1", 3, "wrong-mean")
        self.assertFalse((self.root / "wrong-mean").exists())
        with self.assertRaisesRegex(ValueError, "output dimension"):
            self.run_config("selected-contextual-token-mean-linear-relu-linear-v1",
                            4, "wrong-projection")
        self.assertFalse((self.root / "wrong-projection").exists())
        path = self.root / "unknown.json"
        config = dict(self.config, model=dict(self.config["model"], pooling="unknown"))
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "unsupported pooling rule"):
            WorkerConfig.load(path)


if __name__ == "__main__":
    unittest.main()
