#!/usr/bin/env python3
"""Tests for controlled-suite scoring and semantic-review artifacts."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path

from sse_multivector.fine_segmentation_scoring import (
    REVIEW_CAPACITY,
    apply_semantic_review_response,
    build_candidate_evidence,
    build_representation_diagnostics,
    build_experiment_02_review,
    build_experiment_02_exceptions,
    build_experiment_02_summaries,
    bind_experiment_02_review,
    canonical_projection,
    characterize_experiment_02,
    finalize_candidate_disposition,
    load_verified_candidate_outputs,
    main as scoring_main,
    score_experiment_03,
    score_experiment_04,
    score_experiment_01,
    score_experiment_06,
    validate_experiment_02_coverage,
    validate_semantic_review_response,
    verify_candidate_comparison_artifact,
    verify_finalized_scoring_artifact,
    verify_reviewed_scoring_artifact,
    write_candidate_comparison_artifact,
    write_finalized_scoring_artifact,
    write_reviewed_scoring_artifact,
    write_scoring_artifact,
    write_unavailable_finalized_scoring_artifact,
    _load_manifest_verified_raw_vectors,
)
from sse_multivector.fine_segmentation_suite import compile_approved_protocol


def encoding(readable_id: str, subject: str, text: str, selected: str) -> dict:
    start = text.index(selected)
    return {
        "readable_id": readable_id,
        "subject": subject,
        "text": text,
        "byte_spans": [[start, start + len(selected)]],
        "metadata": {"subject_code": subject},
    }


class FineSegmentationScoringTests(unittest.TestCase):
    def test_review_and_final_artifacts_replay_the_bound_candidate_chain(self) -> None:
        def candidate_evidence(identity: str, suffix: str) -> dict:
            members = [
                f"{subject}{ordinal}{suffix}" for subject in "ABC" for ordinal in (1, 2)
            ]
            encodings = {}
            for member in members:
                subject = member[0]
                value = encoding(member, subject, f"Mask for {member}", member)
                value["metadata"] = {"subject_code": subject, "form": "A"}
                encodings[member] = value
            input_id = f"balanced-{suffix}"
            inputs = [exp2_input(input_id, "balanced", [2, 2, 2], members)]
            output = eligible(
                [
                    {f"A1{suffix}", f"B1{suffix}"},
                    {f"A2{suffix}"},
                    {f"B2{suffix}"},
                    {f"C1{suffix}", f"C2{suffix}"},
                ]
            )
            characterization = characterize_experiment_02(
                inputs, {input_id: output}, encodings
            )
            occurrences = characterization["configurations"][input_id][
                "cross_subject_occurrences"
            ]
            review = build_experiment_02_review(
                occurrences, encodings, review_seed=b"q" * 32
            )
            bind_experiment_02_review(characterization, review)
            summaries = build_experiment_02_summaries(characterization)
            exceptions = build_experiment_02_exceptions(characterization)
            return {
                "schema_version": 1,
                "candidate_identity": identity,
                "candidate_conformance": {"verdict": "pass"},
                "experiment_01": {"verdict": "pass"},
                "experiment_03": {"overall_verdict": "pass"},
                "experiment_04": {"overall_verdict": "pass"},
                "experiment_06": {"overall_verdict": "pass"},
                "experiment_02": {
                    "review": review,
                    "coverage_manifest": {
                        "configurations": list(
                            characterization["configurations"].values()
                        ),
                        "comparisons": characterization["comparisons"],
                        "support_role_by_wording_form": characterization[
                            "support_role_by_wording_form"
                        ],
                    },
                    "frozen_inputs": inputs,
                    "frozen_encodings": encodings,
                    "frozen_expected_configuration_ids": [input_id],
                    "frozen_expected_unequal_configuration_ids": [],
                    "mandatory_summaries": summaries,
                    "exceptions": exceptions,
                    "report_completeness": {"semantic_review_complete": False},
                },
                "review_status": "pending_review",
                "user_disposition": "pending",
                "candidate_selection": "reserved_for_user",
            }

        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            evidence = {
                "hdbscan": candidate_evidence("identity-h", "H"),
                "snn": candidate_evidence("identity-s", "S"),
            }
            write_scoring_artifact(
                scoring,
                evidence,
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            mapping = json.loads(
                (scoring / "internal/review-set-mapping.json").read_text(
                    encoding="utf-8"
                )
            )
            sets = {row["candidate"]: row["review_set"] for row in mapping["sets"]}
            finalized_paths = []
            for candidate in ("hdbscan", "snn"):
                review_set = sets[candidate]
                reviewer_packet = json.loads(
                    (scoring / "review" / f"{review_set}.json").read_text(
                        encoding="utf-8"
                    )
                )
                response = {
                    "schema_version": 1,
                    "review_set": review_set,
                    "judgments": [
                        {
                            "packet": packet["packet"],
                            "verdict": "valid",
                            "fine_subject": "Shared synthetic subject",
                        }
                        for packet in reviewer_packet["packets"]
                    ],
                }
                if candidate == "hdbscan":
                    wrong = dict(response)
                    wrong["review_set"] = sets["snn"]
                    with self.assertRaisesRegex(ValueError, "wrong review set"):
                        write_reviewed_scoring_artifact(
                            scoring,
                            review_set,
                            wrong,
                            root / "wrong-reviewed",
                        )
                reviewed_path = root / f"reviewed-{candidate}"
                write_reviewed_scoring_artifact(
                    scoring, review_set, response, reviewed_path
                )
                reviewed = verify_reviewed_scoring_artifact(scoring, reviewed_path)
                decision_contract = reviewed["evidence"]["experiment_02"][
                    "decision_response_contract"
                ]
                decision = {
                    "schema_version": 1,
                    "candidate_disposition": "proceed",
                    "written_rationale": "The controlled evidence is acceptable.",
                    "exception_dispositions": [
                        {
                            "exception_id": exception_id,
                            "blocks_proceed": False,
                            "rationale": "Reviewed and accepted for this pilot.",
                        }
                        for exception_id in decision_contract["required_exception_ids"]
                    ],
                }
                finalized_path = root / f"finalized-{candidate}"
                write_finalized_scoring_artifact(
                    scoring, reviewed_path, decision, finalized_path
                )
                verify_finalized_scoring_artifact(scoring, finalized_path)
                finalized_paths.append(finalized_path)
            comparison_path = root / "comparison"
            write_candidate_comparison_artifact(
                scoring, finalized_paths, comparison_path
            )
            comparison = verify_candidate_comparison_artifact(
                scoring, finalized_paths, comparison_path
            )
        self.assertEqual("pending", comparison["assistant_recommendation"]["status"])
        self.assertEqual("reserved_for_user", comparison["candidate_selection"])

    def test_unavailable_candidates_reach_bound_final_comparison_without_proceed(
        self,
    ) -> None:
        def capacity_evidence(identity: str) -> dict:
            members = [f"{subject}{ordinal}" for subject in "ABC" for ordinal in (1, 2)]
            encodings = {}
            for member in members:
                value = encoding(member, member[0], f"Mask for {member}", member)
                value["metadata"] = {"subject_code": member[0], "form": "A"}
                encodings[member] = value
            inputs = [exp2_input("balanced", "balanced", [2, 2, 2], members)]
            characterization = characterize_experiment_02(
                inputs,
                {"balanced": eligible([{"A1", "B1"}, {"A2"}, {"B2"}, {"C1", "C2"}])},
                encodings,
            )
            review = build_experiment_02_review(
                characterization["configurations"]["balanced"][
                    "cross_subject_occurrences"
                ],
                encodings,
                review_seed=b"q" * 32,
            )
            review["status"] = "review_capacity_failure"
            review["reviewer_packets"] = []
            review["unavailable_reason"] = "review packet cap exceeded"
            for packet in review["internal_packets"]:
                packet["review_state"] = "unavailable"
            bind_experiment_02_review(characterization, review)
            summaries = build_experiment_02_summaries(characterization)
            exceptions = build_experiment_02_exceptions(characterization)
            required = [
                row["exception_id"] for rows in exceptions.values() for row in rows
            ]
            return {
                "schema_version": 1,
                "candidate_identity": identity,
                "candidate_conformance": {"verdict": "pass"},
                "semantic_scoring": "blocked",
                "experiment_02": {
                    "review": review,
                    "coverage_manifest": {
                        "configurations": list(
                            characterization["configurations"].values()
                        ),
                        "comparisons": characterization["comparisons"],
                        "support_role_by_wording_form": characterization[
                            "support_role_by_wording_form"
                        ],
                    },
                    "frozen_inputs": inputs,
                    "frozen_encodings": encodings,
                    "frozen_expected_configuration_ids": ["balanced"],
                    "frozen_expected_unequal_configuration_ids": [],
                    "mandatory_summaries": summaries,
                    "exceptions": exceptions,
                    "decision_response_contract": {
                        "schema_version": 1,
                        "allowed_candidate_dispositions": ["revise candidate", "stop"],
                        "required_fields": [
                            "schema_version",
                            "candidate_disposition",
                            "written_rationale",
                            "exception_dispositions",
                        ],
                        "exception_disposition_fields": [
                            "exception_id",
                            "blocks_proceed",
                            "rationale",
                        ],
                        "required_exception_ids": required,
                        "proceed_rule": "proceed is unavailable",
                    },
                    "report_completeness": {
                        "coverage_structurally_complete": True,
                        "semantic_review_complete": False,
                        "reason": "review packet cap exceeded",
                    },
                },
                "review_status": "review_capacity_failure",
                "user_disposition": "pending",
                "candidate_selection": "reserved_for_user",
            }

        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            production_conformance_failure = build_candidate_evidence(
                {},
                {},
                candidate_identity="identity-s",
                review_seed=b"q" * 32,
            )
            self.assertIn("experiment_02", production_conformance_failure)
            self.assertEqual(
                {"default", "alternate_order"},
                set(production_conformance_failure["candidate_conformance"]["inputs"]),
            )
            differing = build_candidate_evidence(
                {},
                {
                    "experiment-01/default": eligible([{"A", "B"}]),
                    "candidate-conformance/alternate-order": eligible([{"A"}, {"B"}]),
                },
                candidate_identity="identity-different",
                review_seed=b"q" * 32,
            )
            self.assertTrue(
                differing["candidate_conformance"]["complete_output_difference"]
            )
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": capacity_evidence("identity-h"),
                    "snn": production_conformance_failure,
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            finalized_paths = []
            for candidate in ("hdbscan", "snn"):
                internal = json.loads(
                    (scoring / "internal" / f"{candidate}.json").read_text(
                        encoding="utf-8"
                    )
                )
                required_exception_ids = internal["experiment_02"][
                    "decision_response_contract"
                ]["required_exception_ids"]
                decision = {
                    "schema_version": 1,
                    "candidate_disposition": "revise candidate",
                    "written_rationale": "The unavailable evidence requires revision.",
                    "exception_dispositions": [
                        {
                            "exception_id": exception_id,
                            "blocks_proceed": True,
                            "rationale": "The missing review blocks proceeding.",
                        }
                        for exception_id in required_exception_ids
                    ],
                }
                finalized = root / f"finalized-{candidate}"
                if candidate == "hdbscan":
                    decision_path = root / "capacity-decision.json"
                    decision_path.write_text(json.dumps(decision), encoding="utf-8")
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            0,
                            scoring_main(
                                [
                                    "finalize-unavailable",
                                    str(scoring),
                                    candidate,
                                    str(decision_path),
                                    str(finalized),
                                ]
                            ),
                        )
                else:
                    write_unavailable_finalized_scoring_artifact(
                        scoring, candidate, decision, finalized
                    )
                report = verify_finalized_scoring_artifact(scoring, finalized)
                self.assertEqual(
                    "revise candidate", report["evidence"]["user_disposition"]
                )
                self.assertIsNotNone(
                    report["evidence"]["experiment_02"]["report_completeness"]["reason"]
                )
                finalized_paths.append(finalized)
            comparison_path = root / "comparison"
            write_candidate_comparison_artifact(
                scoring, finalized_paths, comparison_path
            )
            comparison = verify_candidate_comparison_artifact(
                scoring, finalized_paths, comparison_path
            )
        self.assertEqual(2, len(comparison["candidates"]))
        self.assertTrue(
            all(
                candidate["user_disposition"] == "revise candidate"
                for candidate in comparison["candidates"]
            )
        )

    def test_post_review_path_propagates_judgments_and_requires_user_rationales(
        self,
    ) -> None:
        members = [f"{subject}{ordinal}" for subject in "ABC" for ordinal in (1, 2)]
        encodings = {}
        for member in members:
            value = encoding(member, member[0], f"Mask for {member}", member)
            value["metadata"] = {"subject_code": member[0], "form": "A"}
            encodings[member] = value
        inputs = [exp2_input("balanced", "balanced", [2, 2, 2], members)]
        outputs = {"balanced": eligible([{"A1", "B1"}, {"A2"}, {"B2"}, {"C1", "C2"}])}
        characterization = characterize_experiment_02(inputs, outputs, encodings)
        occurrences = characterization["configurations"]["balanced"][
            "cross_subject_occurrences"
        ]
        review = build_experiment_02_review(
            occurrences, encodings, review_seed=b"q" * 32
        )
        bind_experiment_02_review(characterization, review)
        summaries = build_experiment_02_summaries(characterization)
        exceptions = build_experiment_02_exceptions(characterization)
        coverage = {
            "configurations": list(characterization["configurations"].values()),
            "comparisons": characterization["comparisons"],
            "support_role_by_wording_form": characterization[
                "support_role_by_wording_form"
            ],
        }
        evidence = {
            "candidate_identity": "candidate",
            "experiment_02": {
                "review": review,
                "coverage_manifest": coverage,
                "frozen_inputs": inputs,
                "frozen_encodings": encodings,
                "frozen_expected_configuration_ids": ["balanced"],
                "frozen_expected_unequal_configuration_ids": [],
                "mandatory_summaries": summaries,
                "exceptions": exceptions,
            },
            "review_status": "pending_review",
            "user_disposition": "pending",
            "candidate_selection": "reserved_for_user",
        }
        packet = review["internal_packets"][0]["packet"]
        semantic_response = {
            "schema_version": 1,
            "review_set": "RTEST",
            "judgments": [
                {"packet": packet, "verdict": "invalid", "fine_subject": None}
            ],
        }
        tampered = json.loads(json.dumps(evidence))
        tampered["experiment_02"]["coverage_manifest"]["configurations"][0][
            "cross_subject_occurrences"
        ][0]["member_roles"]["A1"]["support_count"] = 999
        with self.assertRaisesRegex(ValueError, "incorrect support role"):
            apply_semantic_review_response(tampered, "RTEST", semantic_response)
        missing_occurrence = json.loads(json.dumps(evidence))
        missing_coverage = missing_occurrence["experiment_02"]["coverage_manifest"]
        missing_coverage["configurations"][0]["cross_subject_occurrences"] = []
        missing_characterization = {
            "configurations": {
                row["configuration_id"]: row
                for row in missing_coverage["configurations"]
            },
            "comparisons": missing_coverage["comparisons"],
        }
        missing_occurrence["experiment_02"]["mandatory_summaries"] = (
            build_experiment_02_summaries(missing_characterization)
        )
        missing_occurrence["experiment_02"]["exceptions"] = (
            build_experiment_02_exceptions(missing_characterization)
        )
        with self.assertRaisesRegex(ValueError, "machine-derived"):
            apply_semantic_review_response(
                missing_occurrence, "RTEST", semantic_response
            )
        reviewed = apply_semantic_review_response(
            evidence,
            "RTEST",
            semantic_response,
        )
        occurrence = reviewed["experiment_02"]["coverage_manifest"]["configurations"][
            0
        ]["cross_subject_occurrences"][0]
        self.assertEqual("invalid", occurrence["review"]["verdict"])
        self.assertEqual(
            1,
            reviewed["experiment_02"]["mandatory_summaries"]["by_schedule"][0][
                "cross_subject_invalid"
            ],
        )
        required = reviewed["experiment_02"]["decision_response_contract"][
            "required_exception_ids"
        ]
        incomplete = {
            "schema_version": 1,
            "candidate_disposition": "proceed",
            "written_rationale": "The observed exceptions are acceptable for this pilot.",
            "exception_dispositions": [],
        }
        with self.assertRaisesRegex(ValueError, "every required exception"):
            finalize_candidate_disposition(reviewed, incomplete)
        complete = {
            **incomplete,
            "exception_dispositions": [
                {
                    "exception_id": exception_id,
                    "blocks_proceed": False,
                    "rationale": "Reviewed and accepted for this controlled characterization.",
                }
                for exception_id in required
            ],
        }
        finalized = finalize_candidate_disposition(reviewed, complete)
        self.assertEqual("proceed", finalized["user_disposition"])
        self.assertTrue(
            finalized["experiment_02"]["report_completeness"]["proceed_eligible"]
        )
        self.assertEqual("reserved_for_user", finalized["candidate_selection"])

    def test_review_binding_updates_singleton_invalid_membership_state(self) -> None:
        characterization = {
            "configurations": {
                "C1": {
                    "cross_subject_occurrences": [
                        {
                            "opaque_members": ["01" * 32, "02" * 32],
                            "readable_members": ["A", "B"],
                            "review": "pending",
                        }
                    ],
                    "subjects": {
                        "A": {
                            "singleton_disposition": {
                                "member": "A",
                                "multi_member_segments": [["A", "B"]],
                                "invalid_membership": "pending_semantic_review",
                            }
                        },
                        "B": {"singleton_disposition": None},
                    },
                }
            }
        }
        review = {
            "status": "review_capacity_failure",
            "internal_packets": [
                {
                    "packet": "P001",
                    "canonical_opaque_members": ["01" * 32, "02" * 32],
                }
            ],
        }
        bind_experiment_02_review(characterization, review)
        singleton = characterization["configurations"]["C1"]["subjects"]["A"][
            "singleton_disposition"
        ]
        self.assertEqual("unavailable", singleton["invalid_membership"])

    def test_raw_representation_vectors_must_match_the_vector_manifest(self) -> None:
        import hashlib
        import struct

        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            raw = struct.pack("<4f", 1.0, 0.0, 0.0, 1.0)
            vector_map = {
                "vector_count": 2,
                "dimensions": 2,
                "vectors": [
                    {"ordinal": 0, "encoding_id": "A"},
                    {"ordinal": 1, "encoding_id": "B"},
                ],
            }
            (root / "raw-vectors.f32le").write_bytes(raw)
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "vector_count": 2,
                        "dimensions": 2,
                        "files": {
                            "raw-vectors.f32le": {
                                "bytes": len(raw),
                                "sha256": hashlib.sha256(raw).hexdigest(),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            values = _load_manifest_verified_raw_vectors(root, vector_map)
            self.assertEqual((1.0, 0.0), values["A"])
            (root / "raw-vectors.f32le").write_bytes(raw + b"drift")
            with self.assertRaisesRegex(ValueError, "manifest"):
                _load_manifest_verified_raw_vectors(root, vector_map)

    def test_canonical_projection_uses_the_frozen_global_rank(self) -> None:
        projected = canonical_projection(
            [["A", "B", "C"]],
            {"A", "C"},
            global_order=["C", "B", "A"],
        )
        self.assertEqual({("C", "A"): 1}, dict(projected))

    def test_semantic_review_response_requires_every_packet_and_subject_for_valid(
        self,
    ) -> None:
        review = {
            "status": "pending_review",
            "internal_packets": [
                {"packet": "P001"},
                {"packet": "P002"},
            ],
        }
        response = {
            "schema_version": 1,
            "review_set": "R123",
            "judgments": [
                {
                    "packet": "P001",
                    "verdict": "valid",
                    "fine_subject": "coffee roasting",
                },
                {"packet": "P002", "verdict": "uncertain", "fine_subject": None},
            ],
        }
        judgments = validate_semantic_review_response(review, "R123", response)
        self.assertEqual("coffee roasting", judgments["P001"]["fine_subject"])

        unexpected = {**response, "candidate": "must-not-be-accepted"}
        with self.assertRaisesRegex(ValueError, "top-level schema"):
            validate_semantic_review_response(review, "R123", unexpected)

        response["judgments"][0]["fine_subject"] = None
        with self.assertRaisesRegex(ValueError, "fine subject"):
            validate_semantic_review_response(review, "R123", response)

    def test_representation_diagnostics_preserve_complete_cosines_and_nearest_same_subject(
        self,
    ) -> None:
        protocol = {
            "encodings": [
                {
                    "encoding_id": "experiment-02/A1",
                    "experiment": "experiment-02",
                    "readable_id": "A1",
                    "metadata": {
                        "neighborhood": "test",
                        "subject_code": "A",
                        "form": "A",
                    },
                },
                {
                    "encoding_id": "experiment-02/A2",
                    "experiment": "experiment-02",
                    "readable_id": "A2",
                    "metadata": {
                        "neighborhood": "test",
                        "subject_code": "A",
                        "form": "B",
                    },
                },
                {
                    "encoding_id": "experiment-02/B1",
                    "experiment": "experiment-02",
                    "readable_id": "B1",
                    "metadata": {
                        "neighborhood": "test",
                        "subject_code": "B",
                        "form": "A",
                    },
                },
            ]
        }
        vectors = {
            "experiment-02/A1": [1.0, 0.0],
            "experiment-02/A2": [0.9, 0.1],
            "experiment-02/B1": [0.0, 1.0],
        }

        diagnostics = build_representation_diagnostics(protocol, vectors)

        experiment = diagnostics["experiments"]["experiment-02"]
        self.assertEqual(3, len(experiment["cosine_matrix"]))
        self.assertAlmostEqual(1.0, experiment["cosine_matrix"][0][0])
        a1 = next(
            row
            for row in experiment["nearest_same_subject"]
            if row["readable_id"] == "A1"
        )
        self.assertEqual(1, a1["nearest_same_subject_rank"])
        self.assertGreater(a1["nearest_same_subject_margin"], 0)

    def test_representation_diagnostics_record_frozen_tokenizer_evidence(self) -> None:
        root = Path(__file__).resolve().parents[1]
        protocol = compile_approved_protocol(root)
        vectors = {
            str(item["encoding_id"]): [1.0, float(index + 1)]
            for index, item in enumerate(protocol["encodings"])
        }
        records = {}
        for item in protocol["encodings"]:
            if item["experiment"] not in {"experiment-03", "experiment-04"}:
                continue
            token_ids = list(range(101, 122))
            if (
                item["experiment"] == "experiment-03"
                and item["metadata"]["version"] == "C"
            ):
                token_ids[10] = 999
            records[str(item["encoding_id"])] = {
                "selected_token_indices": list(range(1, 22)),
                "selected_token_ids": token_ids,
                "token_count": 24,
            }
        diagnostics = build_representation_diagnostics(protocol, vectors, records)
        exp3 = diagnostics["experiments"]["experiment-03"]
        exp4 = diagnostics["experiments"]["experiment-04"]
        self.assertEqual(24, len(exp3["matched_baseline_changed_pairs"]))
        self.assertTrue(
            all(
                row["exactly_one_selected_token_changed"]
                for row in exp3["matched_baseline_changed_pairs"]
            )
        )
        self.assertEqual(48, len(exp3["tokenizer_records"]))
        self.assertEqual(27, len(exp4["tokenizer_records"]))
        self.assertEqual(26, len(exp4["nearest_neighbor_orders"][0]["neighbors"]))

        changed_id = exp3["matched_baseline_changed_pairs"][0]["changed_encoding_id"]
        records[changed_id]["selected_token_indices"] = list(range(2, 23))
        with self.assertRaisesRegex(ValueError, "tokenizer qualification"):
            build_representation_diagnostics(protocol, vectors, records)

    def test_scoring_artifact_hides_candidate_identity_from_reviewer_packets(
        self,
    ) -> None:
        evidence = {}
        for candidate_index, candidate in enumerate(("hdbscan", "snn"), start=1):
            evidence[candidate] = {
                "candidate_identity": f"secret-{candidate}",
                "review_status": "pending_review",
                "user_disposition": "pending",
                "candidate_selection": "reserved_for_user",
                "experiment_02": {
                    "review": {
                        "status": "pending_review",
                        "review_seed_commitment": "a" * 64,
                        "unique_packet_count": 1,
                        "reviewer_packets": [
                            {
                                "packet": "P001",
                                "question": "Are all instances refinements of one fine subject?",
                                "verdicts": ["valid", "invalid", "uncertain"],
                                "instances": [
                                    {
                                        "instance": "I01",
                                        "fragments": [f"mask-{candidate_index}"],
                                    }
                                ],
                            }
                        ],
                    }
                },
            }
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            output = Path(directory) / "scoring"
            report = write_scoring_artifact(
                output,
                evidence,
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            review_files = sorted((output / "review").glob("*.json"))
            reviewer_text = "".join(
                path.read_text(encoding="utf-8") for path in review_files
            )
            reviewer_values = [
                json.loads(path.read_text(encoding="utf-8")) for path in review_files
            ]

        self.assertEqual(2, report["review_set_count"])
        for hidden in ("hdbscan", "snn", "secret-hdbscan", "secret-snn"):
            self.assertNotIn(hidden, reviewer_text)
        for value in reviewer_values:
            self.assertEqual(
                ["packet", "verdict", "fine_subject"],
                value["response_contract"]["judgment_fields"],
            )

    def test_scoring_artifact_does_not_create_a_review_set_when_review_is_unavailable(
        self,
    ) -> None:
        evidence = {
            "hdbscan": {
                "candidate_identity": "secret-hdbscan",
                "review_status": "not_available",
                "user_disposition": "pending",
            }
        }
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            output = Path(directory) / "scoring"
            report = write_scoring_artifact(
                output,
                evidence,
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            review_files = list((output / "review").glob("*.json"))
            status = json.loads((output / "status.json").read_text(encoding="utf-8"))
        self.assertEqual(0, report["review_set_count"])
        self.assertEqual([], review_files)
        self.assertEqual(["not_available"], status["review_states"])

    def test_complete_protocol_builds_every_required_machine_summary_without_selecting(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        protocol = compile_approved_protocol(root)
        encoding_by_id = {item["encoding_id"]: item for item in protocol["encodings"]}
        outputs = {}
        for specification in protocol["inputs"]:
            groups = {}
            for readable, encoding_id in zip(
                specification["readable_members"],
                specification["encoding_ids"],
                strict=True,
            ):
                encoding = encoding_by_id[encoding_id]
                if specification["experiment"] in {
                    "experiment-01",
                    "candidate-conformance",
                    "experiment-06",
                }:
                    subject = encoding["metadata"]["subject_code"]
                elif specification["experiment"] == "experiment-03":
                    subject = encoding["subject"]
                elif specification["experiment"] == "experiment-04":
                    subject = encoding["metadata"]["target_subject"]
                else:
                    subject = encoding["metadata"]["subject_code"]
                groups.setdefault(subject, []).append(readable)
            outputs[specification["input_id"]] = eligible(groups.values())

        evidence = build_candidate_evidence(
            protocol,
            outputs,
            candidate_identity="synthetic-perfect-candidate",
            review_seed=bytes(range(32)),
        )

        self.assertEqual("pass", evidence["candidate_conformance"]["verdict"])
        self.assertEqual("pass", evidence["experiment_01"]["verdict"])
        self.assertEqual("pass", evidence["experiment_06"]["overall_verdict"])
        self.assertEqual("pass", evidence["experiment_03"]["overall_verdict"])
        self.assertEqual("pass", evidence["experiment_04"]["overall_verdict"])
        self.assertEqual(
            512, evidence["experiment_02"]["coverage_validation"]["configuration_count"]
        )
        self.assertEqual(
            480, evidence["experiment_02"]["coverage_validation"]["comparison_count"]
        )
        validation = evidence["experiment_02"]["coverage_validation"]
        self.assertEqual(64, validation["minimum_vector_appearance_count"])
        self.assertEqual(64, validation["maximum_vector_appearance_count"])
        self.assertEqual(96, validation["support_role_counts"]["balanced-4"])
        self.assertEqual(192, validation["support_role_counts"]["dense-singleton-1"])
        self.assertIn(
            "support_role_by_wording_form",
            evidence["experiment_02"]["coverage_manifest"],
        )
        summaries = evidence["experiment_02"]["mandatory_summaries"]
        self.assertEqual(16, len(summaries["by_neighborhood_and_condition"]))
        self.assertEqual(9, len(summaries["by_exact_support_role"]))
        for row in summaries["by_exact_support_role"]:
            self.assertIn("cross_subject_valid", row)
            self.assertIn("cross_subject_invalid", row)
            self.assertIn("cross_subject_uncertain", row)
            self.assertIn("cross_subject_unavailable", row)
        self.assertEqual(8, len(summaries["by_schedule"]))
        for row in summaries["by_neighborhood_and_condition"]:
            if row["total_projected_comparisons"] != "not_applicable":
                self.assertEqual(
                    row["total_projected_comparisons"],
                    row["eligible_projected_comparisons"]
                    + row["unavailable_projected_comparisons"],
                )
        singleton_roles = {
            row["support_role"]: row
            for row in summaries["by_exact_support_role"]
            if row["support_role"] in {"singleton-1", "dense-singleton-1"}
        }
        for row in singleton_roles.values():
            self.assertEqual("not_applicable", row["total_survival_comparisons"])
            self.assertEqual("not_applicable", row["survived"])
        self.assertIn("exceptions", evidence["experiment_02"])
        self.assertFalse(
            evidence["experiment_02"]["report_completeness"]["semantic_review_complete"]
        )
        self.assertEqual("pending", evidence["user_disposition"])
        self.assertEqual("reserved_for_user", evidence["candidate_selection"])

    def test_reads_the_verified_runner_schema_and_restores_readable_ids(self) -> None:
        protocol = {
            "inputs": [
                {
                    "input_id": "input-1",
                    "experiment": "experiment-01",
                    "readable_members": ["A", "B"],
                    "opaque_ids": ["01" * 32, "02" * 32],
                }
            ]
        }
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            (root / "runs").mkdir()
            for repetition in (1, 2):
                run = root / "runs" / f"{repetition:064x}"
                run.mkdir()
                response = {
                    "artifact": {
                        "result": {
                            "fine_output": {
                                "segments": [["01" * 32, "02" * 32]],
                                "unassigned": [],
                            }
                        },
                        "canonical_fine_output_json": json.dumps(
                            {"segments": [["01" * 32, "02" * 32]], "unassigned": []},
                            separators=(",", ":"),
                        ),
                    }
                }
                (run / "response.json").write_text(
                    json.dumps(response), encoding="utf-8"
                )
                (run / "fine-output.json").write_text(
                    json.dumps(
                        {"segments": [["01" * 32, "02" * 32]], "unassigned": []},
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                (run / "record.json").write_text(
                    json.dumps(
                        {
                            "run_id": f"{repetition:064x}",
                            "candidate": "snn",
                            "candidate_identity": "snn-controlled-suite-config-v1",
                            "input_id": "input-1",
                            "experiment": "experiment-01",
                            "repetition": repetition,
                            "status": "valid",
                            "integrity_error": None,
                            "fine_output_sha256": "a" * 64,
                        }
                    ),
                    encoding="utf-8",
                )
            (root / "completion.json").write_text(
                json.dumps(
                    {
                        "complete": True,
                        "logical_input_count": 1,
                        "repetitions_per_input": 2,
                        "candidate_counts": {"snn": 2, "hdbscan": 0},
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_verified_candidate_outputs(protocol, root, "snn")

        self.assertEqual(["A", "B"], loaded["input-1"]["segments"][0])
        self.assertEqual(2, len(loaded["input-1"]["invocation_record_ids"]))
        self.assertEqual(
            ["valid", "valid"],
            [row["status"] for row in loaded["input-1"]["invocations"]],
        )
        self.assertTrue(loaded["input-1"]["eligible"])

    def test_verified_runner_integrity_failure_becomes_scoped_ineligible_input(
        self,
    ) -> None:
        protocol = {
            "inputs": [
                {
                    "input_id": "input-1",
                    "experiment": "experiment-02",
                    "readable_members": ["A", "B"],
                    "opaque_ids": ["01" * 32, "02" * 32],
                }
            ]
        }
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            (root / "runs").mkdir()
            for repetition in (1, 2):
                run = root / "runs" / f"{repetition:064x}"
                run.mkdir()
                (run / "record.json").write_text(
                    json.dumps(
                        {
                            "run_id": f"{repetition:064x}",
                            "candidate": "snn",
                            "candidate_identity": "snn-controlled-suite-config-v1",
                            "input_id": "input-1",
                            "experiment": "experiment-02",
                            "repetition": repetition,
                            "status": "integrity-failure",
                            "integrity_error": "output-contract failure",
                            "fine_output_sha256": None,
                        }
                    ),
                    encoding="utf-8",
                )
            (root / "completion.json").write_text(
                json.dumps(
                    {
                        "complete": True,
                        "logical_input_count": 1,
                        "repetitions_per_input": 2,
                        "candidate_counts": {"snn": 2, "hdbscan": 0},
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_verified_candidate_outputs(protocol, root, "snn")

        self.assertFalse(loaded["input-1"]["eligible"])
        self.assertIn("output-contract failure", loaded["input-1"]["integrity_failure"])

    def test_verified_runner_repeatability_difference_becomes_ineligible_input(
        self,
    ) -> None:
        protocol = {
            "inputs": [
                {
                    "input_id": "input-1",
                    "experiment": "experiment-02",
                    "readable_members": ["A", "B"],
                    "opaque_ids": ["01" * 32, "02" * 32],
                }
            ]
        }
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            (root / "runs").mkdir()
            fine_outputs = (
                {"segments": [["01" * 32, "02" * 32]], "unassigned": []},
                {"segments": [], "unassigned": ["01" * 32, "02" * 32]},
            )
            for repetition, fine_output in enumerate(fine_outputs, start=1):
                run = root / "runs" / f"{repetition:064x}"
                run.mkdir()
                (run / "fine-output.json").write_text(
                    json.dumps(fine_output, separators=(",", ":")), encoding="utf-8"
                )
                (run / "record.json").write_text(
                    json.dumps(
                        {
                            "run_id": f"{repetition:064x}",
                            "candidate": "snn",
                            "candidate_identity": "snn-controlled-suite-config-v1",
                            "input_id": "input-1",
                            "experiment": "experiment-02",
                            "repetition": repetition,
                            "status": "valid",
                            "integrity_error": None,
                            "fine_output_sha256": f"{repetition:064x}",
                        }
                    ),
                    encoding="utf-8",
                )
            (root / "completion.json").write_text(
                json.dumps(
                    {
                        "complete": True,
                        "logical_input_count": 1,
                        "repetitions_per_input": 2,
                        "candidate_counts": {"snn": 2, "hdbscan": 0},
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_verified_candidate_outputs(protocol, root, "snn")

        self.assertFalse(loaded["input-1"]["eligible"])
        self.assertEqual(
            "repeatability failure", loaded["input-1"]["integrity_failure"]
        )

    def test_experiment_01_requires_every_complete_cohort_and_rejects_mixing(
        self,
    ) -> None:
        cohorts = {
            name: {f"{name}-{ordinal}" for ordinal in range(1, 7)}
            for name in ("A", "B", "C", "D", "E", "F")
        }
        segments = [set(members) for members in cohorts.values()]
        segments.append({"A-1", "A-2"})

        passing = score_experiment_01(segments, cohorts)
        self.assertEqual("pass", passing["verdict"])
        self.assertEqual([], passing["mixed_segments"])

        failing = score_experiment_01(
            [*segments, {"A-1", "B-1"}],
            cohorts,
        )
        self.assertEqual("recovery_failure", failing["verdict"])
        self.assertEqual([["A-1", "B-1"]], failing["mixed_segments"])

    def test_review_pool_deduplicates_member_sets_and_exposes_only_complete_masks(
        self,
    ) -> None:
        encodings = {
            "A1": encoding("A1", "A", "Before alpha after", "alpha"),
            "B1": encoding("B1", "B", "Before beta after", "beta"),
        }
        occurrences = [
            {
                "configuration_id": "config-1",
                "opaque_members": ["01" * 32, "02" * 32],
                "readable_members": ["A1", "B1"],
                "member_roles": {
                    "A1": {"support_role": "balanced-4", "support_count": 4},
                    "B1": {"support_role": "balanced-4", "support_count": 4},
                },
                "review": "pending",
            },
            {
                "configuration_id": "config-2",
                "opaque_members": ["02" * 32, "01" * 32],
                "readable_members": ["B1", "A1"],
                "member_roles": {
                    "A1": {"support_role": "imbalanced-2", "support_count": 2},
                    "B1": {"support_role": "imbalanced-8", "support_count": 8},
                },
                "review": "pending",
            },
        ]

        review = build_experiment_02_review(
            occurrences,
            encodings,
            review_seed=bytes(range(32)),
        )

        self.assertEqual("pending_review", review["status"])
        self.assertEqual(1, review["unique_packet_count"])
        self.assertEqual(2, len(review["internal_packets"][0]["occurrences"]))
        self.assertTrue(
            all(
                "review" not in occurrence
                for occurrence in review["internal_packets"][0]["occurrences"]
            )
        )
        packet = review["reviewer_packets"][0]
        self.assertEqual(2, len(packet["instances"]))
        self.assertEqual(
            {"alpha", "beta"},
            {instance["fragments"][0] for instance in packet["instances"]},
        )
        serialized = repr(packet)
        for hidden in (
            "config-1",
            "config-2",
            "balanced-4",
            "imbalanced-2",
            "A1",
            "B1",
            "Before",
            "after",
        ):
            self.assertNotIn(hidden, serialized)

    def test_review_capacity_failure_never_subsamples(self) -> None:
        encodings = {}
        occurrences = []
        for ordinal in range(REVIEW_CAPACITY + 1):
            left = f"A{ordinal}"
            right = f"B{ordinal}"
            encodings[left] = encoding(left, "A", f"left {ordinal}", f"left {ordinal}")
            encodings[right] = encoding(
                right, "B", f"right {ordinal}", f"right {ordinal}"
            )
            occurrences.append(
                {
                    "configuration_id": f"config-{ordinal}",
                    "opaque_members": [f"{ordinal + 1:064x}", f"{ordinal + 1000:064x}"],
                    "readable_members": [left, right],
                    "member_roles": {
                        left: {"support_role": "balanced-4", "support_count": 4},
                        right: {"support_role": "balanced-4", "support_count": 4},
                    },
                }
            )

        review = build_experiment_02_review(
            occurrences,
            encodings,
            review_seed=b"x" * 32,
        )

        self.assertEqual("review_capacity_failure", review["status"])
        self.assertEqual(101, review["unique_packet_count"])
        self.assertEqual([], review["reviewer_packets"])
        self.assertEqual(101, len(review["internal_packets"]))

    def test_coverage_validator_requires_every_configuration_and_comparison(
        self,
    ) -> None:
        expected = ["balanced", "unequal-1", "unequal-2"]
        members = [f"{subject}{ordinal}" for subject in "ABC" for ordinal in (1, 2)]
        encodings = {
            member: {"metadata": {"subject_code": member[0], "form": "A"}}
            for member in members
        }
        inputs = [
            exp2_input("balanced", "balanced", [2, 2, 2], members),
            exp2_input("unequal-1", "imbalanced", [2, 2, 2], members),
            exp2_input("unequal-2", "imbalanced", [2, 2, 2], members),
        ]
        outputs = {
            item: eligible([[f"{subject}1", f"{subject}2"] for subject in "ABC"])
            for item in expected
        }
        characterization = characterize_experiment_02(inputs, outputs, encodings)
        manifest = {
            "configurations": list(characterization["configurations"].values()),
            "comparisons": characterization["comparisons"],
            "support_role_by_wording_form": characterization[
                "support_role_by_wording_form"
            ],
        }
        summaries = build_experiment_02_summaries(characterization)
        exceptions = build_experiment_02_exceptions(characterization)
        report = validate_experiment_02_coverage(
            manifest,
            frozen_inputs=inputs,
            frozen_encodings=encodings,
            expected_configuration_ids=expected,
            expected_unequal_configuration_ids=expected[1:],
            mandatory_summaries=summaries,
            exceptions=exceptions,
        )
        self.assertEqual(3, report["configuration_count"])
        self.assertEqual(2, report["comparison_count"])

        tampered_summaries = json.loads(json.dumps(summaries))
        tampered_summaries["by_schedule"][0]["eligible_configurations"] += 1
        with self.assertRaisesRegex(ValueError, "summary tables"):
            validate_experiment_02_coverage(
                manifest,
                frozen_inputs=inputs,
                frozen_encodings=encodings,
                expected_configuration_ids=expected,
                expected_unequal_configuration_ids=expected[1:],
                mandatory_summaries=tampered_summaries,
                exceptions=exceptions,
            )

        tampered = json.loads(json.dumps(manifest))
        tampered["comparisons"][0]["projection"] = {"garbage": True}
        with self.assertRaisesRegex(ValueError, "projection differs"):
            validate_experiment_02_coverage(
                tampered,
                frozen_inputs=inputs,
                frozen_encodings=encodings,
                expected_configuration_ids=expected,
                expected_unequal_configuration_ids=expected[1:],
                mandatory_summaries=summaries,
                exceptions=exceptions,
            )

        tampered = json.loads(json.dumps(manifest))
        tampered["comparisons"][0]["subject_survival"][0]["verdict"] = "did_not_survive"
        with self.assertRaisesRegex(ValueError, "survival verdicts"):
            validate_experiment_02_coverage(
                tampered,
                frozen_inputs=inputs,
                frozen_encodings=encodings,
                expected_configuration_ids=expected,
                expected_unequal_configuration_ids=expected[1:],
                mandatory_summaries=summaries,
                exceptions=exceptions,
            )

        manifest["comparisons"].pop()
        with self.assertRaisesRegex(ValueError, "comparison coverage"):
            validate_experiment_02_coverage(
                manifest,
                frozen_inputs=inputs,
                frozen_encodings=encodings,
                expected_configuration_ids=expected,
                expected_unequal_configuration_ids=expected[1:],
                mandatory_summaries=summaries,
                exceptions=exceptions,
            )

    def test_experiment_06_scores_duplicate_addition_and_combined_preservation(
        self,
    ) -> None:
        left_groups = [
            {f"{letter}{ordinal}" for ordinal in range(1, 3)} for letter in "ABC"
        ]
        right_groups = [
            {f"{letter}{ordinal}" for ordinal in range(1, 3)} for letter in "DEF"
        ]
        outputs = {
            "L0": eligible(left_groups),
            "R0": eligible(right_groups),
            "duplicates": eligible(
                [
                    {"A1", "A1'", "A2", "A2'"},
                    left_groups[1],
                    left_groups[2],
                ]
            ),
            "unrelated": eligible([*left_groups, right_groups[0]]),
            "combined": eligible([*left_groups, *right_groups]),
        }
        for record in outputs.values():
            members = set().union(*(set(segment) for segment in record["segments"]))
            record["input_member_order"] = list(reversed(sorted(members)))
        result = score_experiment_06(
            outputs,
            left_groups=left_groups,
            right_groups=right_groups,
            duplicate_aliases={"A1'": "A1", "A2'": "A2"},
            imported_experiment_01_passed=True,
        )
        self.assertEqual("pass", result["overall_verdict"])
        self.assertEqual("pass", result["conditions"]["duplicates"]["verdict"])
        self.assertEqual("pass", result["conditions"]["unrelated_addition"]["verdict"])
        self.assertTrue(
            result["conditions"]["unrelated_addition"]["projection"]["provenance"]
        )
        self.assertIn(
            sorted(right_groups[0]),
            result["conditions"]["unrelated_addition"]["added_subject_only_segments"],
        )
        self.assertEqual("pass", result["conditions"]["combined"]["verdict"])

        outputs["unrelated"] = eligible([*left_groups, {"C1", "D1"}])
        result = score_experiment_06(
            outputs,
            left_groups=left_groups,
            right_groups=right_groups,
            duplicate_aliases={"A1'": "A1", "A2'": "A2"},
            imported_experiment_01_passed=True,
        )
        self.assertEqual(
            "stability_failure",
            result["conditions"]["unrelated_addition"]["verdict"],
        )

        result = score_experiment_06(
            outputs,
            left_groups=left_groups,
            right_groups=right_groups,
            duplicate_aliases={"A1'": "A1", "A2'": "A2"},
            imported_experiment_01_passed=False,
        )
        self.assertEqual("no_verdict", result["conditions"]["combined"]["verdict"])
        self.assertEqual(
            "no_verdict", result["conditions"]["combined"]["sides"]["L"]["verdict"]
        )
        self.assertEqual(
            "no_verdict", result["conditions"]["combined"]["sides"]["R"]["verdict"]
        )

        invalid = {
            "eligible": False,
            "integrity_failure": "candidate exited with status 9",
            "segments": [],
            "unassigned": [],
        }
        invalid_outputs = {**outputs, "duplicates": invalid, "combined": invalid}
        result = score_experiment_06(
            invalid_outputs,
            left_groups=left_groups,
            right_groups=right_groups,
            duplicate_aliases={"A1'": "A1", "A2'": "A2"},
            imported_experiment_01_passed=False,
        )
        self.assertEqual(
            "candidate exited with status 9",
            result["conditions"]["duplicates"]["input"]["integrity_failure"],
        )
        self.assertEqual(
            "candidate exited with status 9",
            result["conditions"]["combined"]["input"]["integrity_failure"],
        )

    def test_experiment_03_requires_both_one_sided_controls_before_both_arm(
        self,
    ) -> None:
        groups = {
            "COACH": {
                "COACH-SPORTS": {f"CS{index}" for index in range(4)},
                "COACH-VEHICLE": {f"CV{index}" for index in range(4)},
            }
        }
        baseline_segments = list(groups["COACH"].values())
        outputs = {
            "experiment-03/BASELINE": eligible(baseline_segments),
            "experiment-03/COACH-SPORTS-ONLY": eligible(baseline_segments),
            "experiment-03/COACH-VEHICLE-ONLY": eligible(baseline_segments),
            "experiment-03/COACH-BOTH": eligible(baseline_segments),
        }
        result = score_experiment_03(outputs, groups)
        self.assertEqual("pass", result["traps"]["COACH"]["verdict"])

        outputs["experiment-03/COACH-BOTH"] = eligible(
            [*baseline_segments, {"CS0", "CV0"}]
        )
        result = score_experiment_03(outputs, groups)
        self.assertEqual(
            "lexical_collision_failure", result["traps"]["COACH"]["verdict"]
        )

        outputs["experiment-03/COACH-SPORTS-ONLY"] = eligible(
            [*baseline_segments, {"CS0", "CV0"}]
        )
        result = score_experiment_03(outputs, groups)
        self.assertEqual(
            "one_sided_control_prerequisite_failure",
            result["traps"]["COACH"]["verdict"],
        )
        self.assertEqual(2, len(result["traps"]["COACH"]["controls"]))

    def test_experiment_03_shape_diagnostic_uses_all_subject_relationships(
        self,
    ) -> None:
        groups = {
            "COACH": {
                "COACH-SPORTS": {"CS1", "CS2"},
                "COACH-VEHICLE": {"CV1", "CV2"},
            },
            "BANK": {
                "BANK-FINANCIAL": {"BF1", "BF2"},
                "BANK-RIVER": {"BR1", "BR2"},
            },
        }
        baseline_segments = [
            cohort for trap in groups.values() for cohort in trap.values()
        ]
        outputs = {"experiment-03/BASELINE": eligible(baseline_segments)}
        for trap, subjects in groups.items():
            for subject in subjects:
                suffix = subject.removeprefix(trap + "-")
                segments = baseline_segments
                if trap == "COACH" and suffix == "SPORTS":
                    segments = [*baseline_segments, {"BF1", "BR1"}]
                outputs[f"experiment-03/{trap}-{suffix}-ONLY"] = eligible(segments)
            outputs[f"experiment-03/{trap}-BOTH"] = eligible(baseline_segments)

        result = score_experiment_03(outputs, groups)

        self.assertEqual("pass", result["traps"]["COACH"]["verdict"])
        self.assertEqual(
            "semantic_change", result["traps"]["COACH"]["controls"][0]["shape"]
        )
        self.assertIn(
            ["BF1", "BR1"],
            result["traps"]["COACH"]["controls"][0]["complete_output_difference"][
                "segments_added"
            ],
        )

    def test_experiment_04_compares_mixed_profile_only_after_control_is_preserved(
        self,
    ) -> None:
        subject_members = {
            subject: {f"{subject}{index}" for index in range(3)}
            for subject in (
                "COFFEE",
                "BICYCLE",
                "WATERCOLOR",
                "TELESCOPE",
                "SOURDOUGH",
                "PASSPORT",
            )
        }
        controls = {
            "COFFEE": "COFFEE0",
            "BICYCLE": "BICYCLE0",
            "WATERCOLOR": "WATERCOLOR0",
        }
        baseline = eligible(subject_members.values())
        mixed = "COFFEE-TELESCOPE"
        stable_treatment_segments = [
            *subject_members.values(),
            {mixed, *subject_members["COFFEE"]},
        ]
        result = score_experiment_04(
            baseline,
            {mixed: eligible(stable_treatment_segments)},
            subject_members=subject_members,
            controls=controls,
            treatment_targets={mixed: "COFFEE"},
            treatment_contexts={mixed: "TELESCOPE"},
            treatment_forms={mixed: "A"},
        )
        self.assertEqual("pass", result["treatments"][mixed]["verdict"])

        changed = [
            *stable_treatment_segments,
            {mixed, next(iter(subject_members["TELESCOPE"]))},
        ]
        result = score_experiment_04(
            baseline,
            {mixed: eligible(changed)},
            subject_members=subject_members,
            controls=controls,
            treatment_targets={mixed: "COFFEE"},
            treatment_contexts={mixed: "TELESCOPE"},
            treatment_forms={mixed: "A"},
        )
        self.assertEqual(
            "context_membership_change_failure",
            result["treatments"][mixed]["verdict"],
        )
        self.assertEqual(["TELESCOPE"], result["treatments"][mixed]["gained"])
        self.assertEqual(
            "matching_context",
            result["treatments"][mixed]["relationship_changes"][0]["classification"],
        )
        self.assertIn("reference_graphs", result["treatments"][mixed])
        self.assertIn("anchor_projection", result["treatments"][mixed])
        self.assertIn("by_outer_form", result["diagnostic_patterns"])

        broken_reference = [
            segment
            for segment in stable_treatment_segments
            if segment != subject_members["PASSPORT"]
        ]
        result = score_experiment_04(
            baseline,
            {mixed: eligible(broken_reference)},
            subject_members=subject_members,
            controls=controls,
            treatment_targets={mixed: "COFFEE"},
            treatment_contexts={mixed: "TELESCOPE"},
            treatment_forms={mixed: "A"},
        )
        withheld = result["treatments"][mixed]
        self.assertEqual("no_verdict", withheld["verdict"])
        self.assertIn("complete_output", withheld)
        self.assertIn("anchor_projection", withheld)
        self.assertIn("reference_graphs", withheld)

        invalid_baseline = {
            "eligible": False,
            "integrity_failure": "repeatability failure",
            "segments": [],
            "unassigned": [],
        }
        auxiliary_member = next(iter(subject_members["TELESCOPE"]))
        treatment_with_auxiliary = eligible(
            [*stable_treatment_segments, {auxiliary_member}]
        )
        result = score_experiment_04(
            invalid_baseline,
            {mixed: treatment_with_auxiliary},
            subject_members=subject_members,
            controls=controls,
            treatment_targets={mixed: "COFFEE"},
            treatment_contexts={mixed: "TELESCOPE"},
            treatment_forms={mixed: "A"},
        )
        withheld = result["treatments"][mixed]
        self.assertEqual("no_verdict", withheld["verdict"])
        self.assertEqual(
            len(treatment_with_auxiliary["segments"]),
            len(withheld["anchor_projection"]),
        )
        self.assertIn(
            [auxiliary_member],
            [row["members"] for row in withheld["unsupported_auxiliary_segments"]],
        )
        invalid_treatment = {
            "eligible": False,
            "integrity_failure": "candidate process exited with status 7",
            "segments": [],
            "unassigned": [],
        }
        result = score_experiment_04(
            invalid_baseline,
            {mixed: invalid_treatment},
            subject_members=subject_members,
            controls=controls,
            treatment_targets={mixed: "COFFEE"},
            treatment_contexts={mixed: "TELESCOPE"},
            treatment_forms={mixed: "A"},
        )
        withheld = result["treatments"][mixed]
        self.assertEqual(
            "candidate process exited with status 7",
            withheld["treatment_integrity_reason"],
        )

    def test_experiment_02_characterization_preserves_exact_support_roles_and_survival(
        self,
    ) -> None:
        encodings = {
            **{
                f"A{index}": {"metadata": {"subject_code": "A"}}
                for index in range(1, 9)
            },
            **{
                f"B{index}": {"metadata": {"subject_code": "B"}}
                for index in range(1, 9)
            },
            **{
                f"C{index}": {"metadata": {"subject_code": "C"}}
                for index in range(1, 9)
            },
        }
        balanced_members = [
            f"{letter}{index}" for letter in "ABC" for index in range(1, 5)
        ]
        unequal_members = [
            *[f"A{index}" for index in range(1, 9)],
            "B1",
            "B2",
            "C1",
            "C2",
        ]
        inputs = [
            exp2_input("balanced", "balanced", [4, 4, 4], balanced_members),
            exp2_input("unequal", "imbalanced", [8, 2, 2], unequal_members),
            exp2_input("unequal-2", "imbalanced", [8, 2, 2], unequal_members),
        ]
        outputs = {
            "balanced": eligible(
                [{f"{letter}{index}" for index in range(1, 5)} for letter in "ABC"]
            ),
            "unequal": eligible(
                [
                    {f"A{index}" for index in range(1, 9)},
                    {"B1", "B2"},
                    {"C1", "C2"},
                ]
            ),
            "unequal-2": eligible(
                [
                    {f"A{index}" for index in range(1, 9)},
                    {"B1", "B2"},
                    {"C1", "C2"},
                ]
            ),
        }
        characterization = characterize_experiment_02(inputs, outputs, encodings)
        unequal = characterization["configurations"]["unequal"]
        self.assertEqual("imbalanced-8", unequal["subjects"]["A"]["support_role"])
        self.assertEqual("imbalanced-2", unequal["subjects"]["B"]["support_role"])
        self.assertEqual(
            6,
            sum(
                row["verdict"] == "survived"
                for comparison in characterization["comparisons"]
                for row in comparison["subject_survival"]
            ),
        )
        self.assertEqual(
            [3, 3],
            [
                len(comparison["subject_survival"])
                for comparison in characterization["comparisons"]
            ],
        )
        for comparison in characterization["comparisons"]:
            self.assertTrue(comparison["projection"]["balanced_provenance"])
            self.assertTrue(comparison["projection"]["unequal_provenance"])


def eligible(segments: Iterable[Iterable[str]], unassigned: Iterable[str] = ()) -> dict:
    invocations = [
        {
            "run_id": f"run-{repetition}",
            "repetition": repetition,
            "status": "valid",
            "integrity_error": None,
            "fine_output_sha256": "a" * 64,
            "execution_profile": {"frozen": True},
            "execution_profile_sha256": "b" * 64,
            "actual_argv": ["candidate", "request.json"],
            "return_code": 0,
            "files": {
                "request.json": "1" * 64,
                "stdout.bin": "2" * 64,
                "stderr.bin": "3" * 64,
                "response.json": "4" * 64,
                "fine-output.json": "5" * 64,
            },
        }
        for repetition in (1, 2)
    ]
    return {
        "eligible": True,
        "integrity_failure": None,
        "segments": [sorted(segment) for segment in segments],
        "unassigned": sorted(unassigned),
        "invocation_record_ids": ["run-1", "run-2"],
        "canonical_output_sha256": "a" * 64,
        "invocations": invocations,
    }


def exp2_input(
    input_id: str,
    condition: str,
    allocation: list[int],
    members: list[str],
) -> dict:
    return {
        "input_id": input_id,
        "readable_members": members,
        "opaque_ids": [f"{index + 1:064x}" for index in range(len(members))],
        "metadata": {
            "neighborhood": "test",
            "schedule": 1,
            "condition": condition,
            "allocation": allocation,
            "subjects": ["A", "B", "C"],
        },
    }


if __name__ == "__main__":
    unittest.main()
