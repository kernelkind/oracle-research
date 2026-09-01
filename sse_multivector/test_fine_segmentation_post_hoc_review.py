#!/usr/bin/env python3
"""Tests for the separate HDBSCAN capacity-failure review path."""

from __future__ import annotations

import hashlib
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector.fine_segmentation_scoring import (
    build_experiment_02_review,
    main as scoring_main,
    verify_post_hoc_hdbscan_review_artifact,
    verify_post_hoc_hdbscan_reviewed_artifact,
    validate_semantic_review_response,
    write_post_hoc_hdbscan_review_artifact,
    write_post_hoc_hdbscan_reviewed_artifact,
    write_scoring_artifact,
)


POST_HOC_PACKET_COUNT = 177
POST_HOC_OCCURRENCE_COUNT = 191
POST_HOC_JUDGMENT_COUNT = 9
POST_HOC_GROUP_SUBJECTS = tuple(
    (f"SUBJECT-{ordinal:02d}-A", f"SUBJECT-{ordinal:02d}-B")
    for ordinal in range(POST_HOC_JUDGMENT_COUNT)
)


def _encoding(readable_id: str, text: str) -> dict[str, object]:
    return {
        "readable_id": readable_id,
        "subject": readable_id[0],
        "text": text,
        "byte_spans": [[0, len(text.encode("utf-8"))]],
        "metadata": {"subject_code": readable_id[0]},
    }


def _capacity_failed_evidence(
    identity: str,
    *,
    packet_count: int = POST_HOC_PACKET_COUNT,
    occurrence_count: int = POST_HOC_OCCURRENCE_COUNT,
    subject_group_count: int = POST_HOC_JUDGMENT_COUNT,
) -> dict[str, object]:
    encodings: dict[str, dict[str, object]] = {}
    occurrences = []
    for ordinal in range(packet_count):
        group_ordinal = ordinal % subject_group_count
        left = f"A{group_ordinal:03d}"
        right = f"B{ordinal:03d}"
        left_subject = f"SUBJECT-{group_ordinal:02d}-A"
        right_subject = f"SUBJECT-{group_ordinal:02d}-B"
        encodings[left] = _encoding(left, f"alpha meaning {group_ordinal}")
        encodings[right] = _encoding(right, f"beta meaning {ordinal}")
        occurrences.append(
            {
                "configuration_id": f"hidden-config-{ordinal}",
                "opaque_members": [
                    f"{group_ordinal + 1:064x}",
                    f"{ordinal + 1000:064x}",
                ],
                "readable_members": [left, right],
                "member_roles": {
                    left: {"subject": left_subject, "support_count": 4},
                    right: {"subject": right_subject, "support_count": 4},
                },
                "review": "pending",
            }
        )
    for repeat in range(occurrence_count - packet_count):
        repeated = copy.deepcopy(occurrences[repeat % packet_count])
        repeated["configuration_id"] = f"hidden-config-repeat-{repeat}"
        occurrences.append(repeated)
    review = build_experiment_02_review(
        occurrences,
        encodings,
        review_seed=b"q" * 32,
    )
    coverage_occurrences = []
    for packet in review["internal_packets"]:
        for occurrence in packet["occurrences"]:
            coverage_occurrences.append(
                {
                    **copy.deepcopy(occurrence),
                    "review": {
                        "packet": packet["packet"],
                        "verdict": "unavailable",
                        "reason": "review_capacity_failure",
                    },
                }
            )
    return {
        "schema_version": 1,
        "candidate_identity": identity,
        "review_status": "review_capacity_failure",
        "experiment_02": {
            "review": review,
            "coverage_manifest": {
                "configurations": [{"cross_subject_occurrences": coverage_occurrences}]
            },
        },
        "candidate_selection": "reserved_for_user",
    }


def _artifact_digests(root: Path) -> dict[Path, str]:
    return {
        path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


class PostHocHdbscanReviewTests(unittest.TestCase):
    def test_review_collapses_exact_packets_to_nine_subject_combinations(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    )
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )

            report = write_post_hoc_hdbscan_review_artifact(
                scoring, root / "post-hoc-review"
            )

        self.assertEqual(POST_HOC_JUDGMENT_COUNT, report["judgment_count"])
        self.assertEqual(POST_HOC_PACKET_COUNT, report["exact_packet_count"])
        self.assertEqual(POST_HOC_OCCURRENCE_COUNT, report["occurrence_count"])

    def test_cli_prepares_and_verifies_the_post_hoc_review(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    )
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            artifact = root / "post-hoc-review"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    scoring_main(
                        ["prepare-post-hoc-review", str(scoring), str(artifact)]
                    ),
                )
                self.assertEqual(
                    0,
                    scoring_main(
                        ["verify-post-hoc-review", str(scoring), str(artifact)]
                    ),
                )

    def test_review_projects_every_packet_without_changing_frozen_scoring(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    ),
                    "snn": _capacity_failed_evidence("snn-controlled-suite-config-v1"),
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            before = _artifact_digests(scoring)
            artifact = root / "post-hoc-review"
            write_post_hoc_hdbscan_review_artifact(scoring, artifact)
            report = verify_post_hoc_hdbscan_review_artifact(scoring, artifact)
            after = _artifact_digests(scoring)

            reviewer = json.loads((artifact / "review.json").read_text())
            status = json.loads((artifact / "status.json").read_text())

        self.assertEqual(before, after)
        self.assertEqual(
            "fine-segmentation-post-hoc-review-v2", report["artifact_type"]
        )
        self.assertEqual(POST_HOC_JUDGMENT_COUNT, report["judgment_count"])
        self.assertEqual(POST_HOC_PACKET_COUNT, report["exact_packet_count"])
        self.assertEqual(POST_HOC_OCCURRENCE_COUNT, report["occurrence_count"])
        self.assertEqual(
            {
                "schema_version",
                "review_set",
                "instructions",
                "packets",
                "response_contract",
            },
            set(reviewer),
        )
        self.assertEqual(2, reviewer["schema_version"])
        self.assertEqual(POST_HOC_JUDGMENT_COUNT, len(reviewer["packets"]))
        self.assertEqual(
            [f"P{ordinal:03d}" for ordinal in range(1, 10)],
            [packet["packet"] for packet in reviewer["packets"]],
        )
        self.assertEqual(
            {
                "schema_version": 2,
                "review_set": reviewer["review_set"],
                "judgments": "exactly one judgment for every packet",
                "judgment_fields": ["packet", "verdict"],
                "allowed_verdicts": ["valid", "invalid", "uncertain"],
            },
            reviewer["response_contract"],
        )
        self.assertEqual(
            "Every instance is recognizable as a refinement of one fine subject.",
            reviewer["instructions"]["valid"],
        )
        self.assertEqual("review_capacity_failure", status["source_review_status"])
        self.assertEqual(POST_HOC_JUDGMENT_COUNT, status["judgment_count"])
        self.assertEqual(POST_HOC_PACKET_COUNT, status["exact_packet_count"])
        self.assertEqual(POST_HOC_OCCURRENCE_COUNT, status["occurrence_count"])
        self.assertFalse(status["changes_frozen_protocol_result"])
        self.assertEqual(
            186,
            sum(len(packet["instances"]) for packet in reviewer["packets"]),
        )
        for packet in reviewer["packets"]:
            self.assertEqual(
                {"packet", "question", "verdicts", "instances"}, set(packet)
            )
            self.assertEqual(
                [
                    f"I{ordinal:02d}"
                    for ordinal in range(1, len(packet["instances"]) + 1)
                ],
                [instance["instance"] for instance in packet["instances"]],
            )
            fragments = [
                tuple(instance["fragments"]) for instance in packet["instances"]
            ]
            self.assertEqual(len(fragments), len(set(fragments)))
            self.assertTrue(
                all(
                    set(instance) == {"instance", "fragments"}
                    for instance in packet["instances"]
                )
            )
        serialized = json.dumps(reviewer)
        self.assertNotIn("fine_subject", serialized)
        for subjects in POST_HOC_GROUP_SUBJECTS:
            for subject in subjects:
                self.assertNotIn(subject, serialized)
        for hidden in (
            "hidden-config",
            "opaque_id",
            "readable_id",
            "support_count",
            "candidate_identity",
            "hdbscan",
        ):
            self.assertNotIn(hidden, serialized)

    def test_completed_response_is_replayable_but_does_not_override_capacity_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    )
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            review_artifact = root / "post-hoc-review"
            review_report = write_post_hoc_hdbscan_review_artifact(
                scoring, review_artifact
            )
            reviewer = review_report["review"]
            verdicts = ("valid", "invalid", "uncertain")
            response = {
                "schema_version": 2,
                "review_set": reviewer["review_set"],
                "judgments": [
                    {
                        "packet": packet["packet"],
                        "verdict": verdicts[index % len(verdicts)],
                    }
                    for index, packet in enumerate(reviewer["packets"])
                ],
            }
            labeled = copy.deepcopy(response)
            labeled["judgments"][0]["fine_subject"] = "Shared synthetic meaning"
            with self.assertRaisesRegex(ValueError, "unexpected fields"):
                write_post_hoc_hdbscan_reviewed_artifact(
                    scoring,
                    review_artifact,
                    labeled,
                    root / "labeled-reviewed",
                )
            incomplete = copy.deepcopy(response)
            incomplete["judgments"].pop()
            with self.assertRaisesRegex(ValueError, "every packet"):
                write_post_hoc_hdbscan_reviewed_artifact(
                    scoring,
                    review_artifact,
                    incomplete,
                    root / "incomplete-reviewed",
                )
            reviewed_artifact = root / "post-hoc-reviewed"
            write_post_hoc_hdbscan_reviewed_artifact(
                scoring,
                review_artifact,
                response,
                reviewed_artifact,
            )
            replay = verify_post_hoc_hdbscan_reviewed_artifact(
                scoring, review_artifact, reviewed_artifact
            )

        self.assertEqual("review_capacity_failure", replay["source_review_status"])
        self.assertFalse(replay["changes_frozen_protocol_result"])
        self.assertFalse(replay["proceed_eligible"])
        self.assertEqual(POST_HOC_JUDGMENT_COUNT, replay["judgment_count"])
        self.assertEqual(POST_HOC_PACKET_COUNT, replay["exact_packet_count"])
        self.assertEqual(POST_HOC_OCCURRENCE_COUNT, replay["occurrence_count"])
        self.assertEqual(
            POST_HOC_JUDGMENT_COUNT,
            sum(replay["judgment_verdict_counts"].values()),
        )
        self.assertEqual(
            POST_HOC_PACKET_COUNT,
            sum(replay["exact_packet_verdict_counts"].values()),
        )
        self.assertEqual(
            POST_HOC_OCCURRENCE_COUNT,
            sum(replay["occurrence_verdict_counts"].values()),
        )
        self.assertNotIn("fine_subject", json.dumps(replay))
        exact_verdicts = {
            row["exact_packet"]: (row["review_packet"], row["verdict"])
            for row in replay["exact_packets"]
        }
        self.assertEqual(POST_HOC_PACKET_COUNT, len(exact_verdicts))
        review_packet_counts: dict[str, int] = {}
        for review_packet, _verdict in exact_verdicts.values():
            review_packet_counts[review_packet] = (
                review_packet_counts.get(review_packet, 0) + 1
            )
        self.assertTrue(all(count > 1 for count in review_packet_counts.values()))
        for occurrence in replay["occurrences"]:
            self.assertEqual(
                exact_verdicts[occurrence["exact_packet"]],
                (occurrence["review_packet"], occurrence["verdict"]),
            )

    def test_review_rejects_wrong_locked_packet_or_occurrence_count(self) -> None:
        cases = (
            (
                POST_HOC_PACKET_COUNT - 1,
                POST_HOC_OCCURRENCE_COUNT,
                POST_HOC_JUDGMENT_COUNT,
                "177 exact packets",
            ),
            (
                POST_HOC_PACKET_COUNT,
                POST_HOC_OCCURRENCE_COUNT - 1,
                POST_HOC_JUDGMENT_COUNT,
                "191 occurrences",
            ),
            (
                POST_HOC_PACKET_COUNT,
                POST_HOC_OCCURRENCE_COUNT,
                POST_HOC_JUDGMENT_COUNT - 1,
                "9 distinct subject combinations",
            ),
        )
        for packet_count, occurrence_count, subject_group_count, error in cases:
            with self.subTest(
                packet_count=packet_count,
                occurrence_count=occurrence_count,
                subject_group_count=subject_group_count,
            ):
                with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
                    root = Path(directory)
                    scoring = root / "scoring"
                    write_scoring_artifact(
                        scoring,
                        {
                            "hdbscan": _capacity_failed_evidence(
                                "hdbscan-controlled-suite-config-v1",
                                packet_count=packet_count,
                                occurrence_count=occurrence_count,
                                subject_group_count=subject_group_count,
                            )
                        },
                        review_seed=b"r" * 32,
                        source_bindings={"candidate_runs_sha256": "b" * 64},
                    )

                    with self.assertRaisesRegex(ValueError, error):
                        write_post_hoc_hdbscan_review_artifact(
                            scoring, root / "post-hoc-review"
                        )

    def test_review_output_rejects_every_scoring_path_overlap_without_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    )
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            before = _artifact_digests(scoring)

            for output in (scoring, scoring / "review", root):
                with self.subTest(output=output):
                    with self.assertRaisesRegex(ValueError, "overlap"):
                        write_post_hoc_hdbscan_review_artifact(scoring, output)
                    self.assertEqual(before, _artifact_digests(scoring))

    def test_reviewed_output_rejects_every_source_path_overlap_without_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {
                    "hdbscan": _capacity_failed_evidence(
                        "hdbscan-controlled-suite-config-v1"
                    )
                },
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            review_parent = root / "reviews"
            review_artifact = review_parent / "review"
            report = write_post_hoc_hdbscan_review_artifact(scoring, review_artifact)
            response = {
                "schema_version": 2,
                "review_set": report["review"]["review_set"],
                "judgments": [
                    {"packet": packet["packet"], "verdict": "uncertain"}
                    for packet in report["review"]["packets"]
                ],
            }
            scoring_before = _artifact_digests(scoring)
            review_before = _artifact_digests(review_artifact)

            for output in (
                scoring,
                scoring / "reviewed",
                review_artifact,
                review_artifact / "reviewed",
                review_parent,
            ):
                with self.subTest(output=output):
                    with self.assertRaisesRegex(ValueError, "overlap"):
                        write_post_hoc_hdbscan_reviewed_artifact(
                            scoring, review_artifact, response, output
                        )
                    self.assertEqual(scoring_before, _artifact_digests(scoring))
                    self.assertEqual(review_before, _artifact_digests(review_artifact))

    def test_review_rejects_an_internal_occurrence_not_bound_to_formal_coverage(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            evidence = _capacity_failed_evidence("hdbscan-controlled-suite-config-v1")
            evidence["experiment_02"]["coverage_manifest"]["configurations"][0][
                "cross_subject_occurrences"
            ].pop()
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {"hdbscan": evidence},
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )
            with self.assertRaisesRegex(ValueError, "formal Experiment 2 coverage"):
                write_post_hoc_hdbscan_review_artifact(
                    scoring, root / "post-hoc-review"
                )

    def test_review_rejects_one_exact_packet_with_inconsistent_subject_sets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            evidence = _capacity_failed_evidence("hdbscan-controlled-suite-config-v1")
            packets = evidence["experiment_02"]["review"]["internal_packets"]
            packet = next(item for item in packets if len(item["occurrences"]) == 2)
            changed = packet["occurrences"][1]
            member = changed["readable_members"][0]
            changed["member_roles"][member]["subject"] = "CHANGED-SUBJECT"
            coverage = evidence["experiment_02"]["coverage_manifest"]["configurations"][
                0
            ]["cross_subject_occurrences"]
            retained = next(
                occurrence
                for occurrence in coverage
                if occurrence["review"]["packet"] == packet["packet"]
                and occurrence["configuration_id"] == changed["configuration_id"]
            )
            retained["member_roles"][member]["subject"] = "CHANGED-SUBJECT"
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {"hdbscan": evidence},
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )

            with self.assertRaisesRegex(
                ValueError, "one exact packet has inconsistent subject combinations"
            ):
                write_post_hoc_hdbscan_review_artifact(
                    scoring, root / "post-hoc-review"
                )

    def test_review_rejects_subjects_swapped_between_members(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            evidence = _capacity_failed_evidence("hdbscan-controlled-suite-config-v1")
            packets = evidence["experiment_02"]["review"]["internal_packets"]
            packet = next(item for item in packets if len(item["occurrences"]) == 2)
            changed = packet["occurrences"][1]
            left, right = changed["readable_members"]
            left_subject = changed["member_roles"][left]["subject"]
            right_subject = changed["member_roles"][right]["subject"]
            changed["member_roles"][left]["subject"] = right_subject
            changed["member_roles"][right]["subject"] = left_subject
            coverage = evidence["experiment_02"]["coverage_manifest"]["configurations"][
                0
            ]["cross_subject_occurrences"]
            retained = next(
                occurrence
                for occurrence in coverage
                if occurrence["review"]["packet"] == packet["packet"]
                and occurrence["configuration_id"] == changed["configuration_id"]
            )
            retained["member_roles"][left]["subject"] = right_subject
            retained["member_roles"][right]["subject"] = left_subject
            scoring = root / "scoring"
            write_scoring_artifact(
                scoring,
                {"hdbscan": evidence},
                review_seed=b"r" * 32,
                source_bindings={"candidate_runs_sha256": "b" * 64},
            )

            with self.assertRaisesRegex(
                ValueError,
                "one exact packet has inconsistent member-to-subject mappings",
            ):
                write_post_hoc_hdbscan_review_artifact(
                    scoring, root / "post-hoc-review"
                )

    def test_primary_review_path_still_rejects_the_capacity_failed_source(self) -> None:
        evidence = _capacity_failed_evidence("hdbscan-controlled-suite-config-v1")
        review = evidence["experiment_02"]["review"]
        with self.assertRaisesRegex(ValueError, "not available"):
            validate_semantic_review_response(
                review,
                "not-a-primary-review-set",
                {"schema_version": 1, "review_set": "x", "judgments": []},
            )

    def test_primary_review_path_still_requires_and_retains_fine_subjects(self) -> None:
        review = {
            "status": "pending_review",
            "internal_packets": [{"packet": "P001"}],
        }
        response = {
            "schema_version": 1,
            "review_set": "R-primary",
            "judgments": [
                {
                    "packet": "P001",
                    "verdict": "valid",
                    "fine_subject": "Shared synthetic meaning",
                }
            ],
        }

        judgments = validate_semantic_review_response(review, "R-primary", response)

        self.assertEqual(response["judgments"][0], judgments["P001"])


if __name__ == "__main__":
    unittest.main()
