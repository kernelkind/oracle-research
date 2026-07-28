use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io;

use oracle_mvp::reference_map::{
    ApprovedHierarchy, ApprovedNoteSet, BroadNarrowRole, HierarchyDraft, HierarchyReviewDecision,
    HierarchyReviewSession, HierarchyReviewTarget, LeafMembership, MembershipStrength,
    NoteProposal, NoteReviewDecision, NoteReviewSession, PairMembership, ProposedNote,
    ReferenceNavigation, ReviewOutcome, SelectionSource, SubjectNode,
};
use oracle_mvp::reference_review::{
    load_verified_note_proposal, run_hierarchy_review, run_note_review, ApprovalUi,
    ReviewRunOutcome,
};
use oracle_mvp::reference_tui::{ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction};
use sha2::{Digest, Sha256};

fn proposed_note(index: usize) -> ProposedNote {
    ProposedNote {
        slot: u8::try_from(index + 1).expect("fixture slot fits u8"),
        note_id: format!("{:064x}", index + 1),
        pubkey: format!("{:064x}", index + 10_000),
        content: format!("Real diagnostic note number {index}"),
        contrast_pair: (index < 16).then(|| PairMembership {
            pair_id: format!("contrast-{:02}", index / 2 + 1),
            partner_slot: u8::try_from(index ^ 1).expect("fixture partner fits u8") + 1,
            broad_narrow_role: None,
        }),
        broad_narrow_pair: (16..32).contains(&index).then(|| PairMembership {
            pair_id: format!("breadth-{:02}", (index - 16) / 2 + 1),
            partner_slot: u8::try_from((index - 16) ^ 1).expect("fixture partner fits u8") + 17,
            broad_narrow_role: Some(if index % 2 == 0 {
                BroadNarrowRole::Broad
            } else {
                BroadNarrowRole::Narrow
            }),
        }),
        niche_or_sparse_case: (32..40)
            .contains(&index)
            .then(|| format!("niche-or-sparse-case-{:02}", index - 31)),
    }
}

fn proposal() -> NoteProposal {
    NoteProposal {
        schema_version: 3,
        proposal_id: "crec-115-selection-v2".to_owned(),
        source: SelectionSource {
            sample_path: "target/crec-113-formal-v1/sample/sample.jsonl".to_owned(),
            sample_sha256: "8edb8a51246201100e6ba7cf7bf1bbf9cd501881d7c70b8a9cfc7a380d1b168e"
                .to_owned(),
            split: "learning".to_owned(),
        },
        notes: (0..64).map(proposed_note).collect(),
    }
}

#[test]
fn proposal_validation_enforces_diagnostic_coverage() {
    let proposal = proposal();
    proposal.validate().expect("approved fixture is valid");

    let mut missing_pair = proposal.clone();
    missing_pair.notes[0].contrast_pair = None;
    let error = missing_pair
        .validate()
        .expect_err("every declared pair has exactly two reciprocal members");
    assert!(error.to_string().contains("contrast pair"), "{error}");

    let mut duplicated_niche = proposal;
    duplicated_niche.notes[33].niche_or_sparse_case =
        duplicated_niche.notes[32].niche_or_sparse_case.clone();
    let error = duplicated_niche
        .validate()
        .expect_err("niche/sparse markers identify eight distinct cases");
    assert!(
        error.to_string().contains("niche or sparse case"),
        "{error}"
    );
}

#[test]
fn changed_candidates_reopen_without_discarding_unchanged_approvals() {
    let original = proposal();
    let mut session = NoteReviewSession::new(&original).expect("create session");
    for note in &original.notes {
        session
            .record(
                &original,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("record approval");
    }
    assert_eq!(session.approved_count(&original), 64);

    let mut revised = original.clone();
    revised.proposal_id = "crec-115-selection-v2".to_owned();
    revised.notes[7].note_id = format!("{:064x}", 99_999);
    revised.notes[7].content = "A manually selected replacement note".to_owned();
    revised.validate().expect("replacement preserves quotas");

    session
        .reconcile(&revised)
        .expect("reconcile revised proposal");
    assert_eq!(session.approved_count(&revised), 63);
    assert_eq!(session.pending_slots(&revised), vec![8]);
    assert!(
        session
            .decision_for(&revised, 7)
            .expect("unchanged slot remains decided")
            .outcome
            == ReviewOutcome::Approved
    );
    assert!(session.decision_for(&revised, 8).is_none());
}

#[test]
fn removing_legacy_ambiguity_metadata_preserves_approvals_and_reopens_rejections() {
    let proposal = proposal();
    let approved_sha256 = legacy_note_sha256(&proposal.notes[0], true);
    let rejected_sha256 = legacy_note_sha256(&proposal.notes[1], true);
    let mut session: NoteReviewSession = serde_json::from_value(serde_json::json!({
        "schema_version": 1,
        "decisions": {
            "1": {
                "note_sha256": approved_sha256,
                "decision": {
                    "outcome": "approved",
                    "comment": ""
                }
            },
            "2": {
                "note_sha256": rejected_sha256,
                "decision": {
                    "outcome": "rejected",
                    "comment": "Why is this interpretively ambiguous?"
                }
            }
        }
    }))
    .expect("decode legacy review session");

    session
        .reconcile(&proposal)
        .expect("migrate legacy review session");

    assert_eq!(session.approved_count(&proposal), 1);
    assert_eq!(
        session
            .decision_for(&proposal, 1)
            .expect("legacy approval remains current")
            .outcome,
        ReviewOutcome::Approved
    );
    assert!(
        session.decision_for(&proposal, 2).is_none(),
        "a rejection of the removed annotation must be reviewed again"
    );
}

#[test]
fn rejection_decisions_require_an_actionable_comment() {
    let proposal = proposal();
    let mut note_session = NoteReviewSession::new(&proposal).expect("create note session");
    let error = note_session
        .record(
            &proposal,
            1,
            NoteReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "  ".to_owned(),
            },
        )
        .expect_err("blank candidate rejection is not actionable");
    assert!(error.to_string().contains("rejection comment"), "{error}");

    let approved = approved_notes();
    let draft = hierarchy(&approved);
    let mut hierarchy_session =
        HierarchyReviewSession::new(&draft, &approved).expect("create hierarchy session");
    let target = hierarchy_session
        .reviewable_targets(&draft, &approved)
        .expect("list reviewable hierarchy items")
        .into_iter()
        .next()
        .expect("the first membership is reviewable");
    let error = hierarchy_session
        .record(
            &draft,
            &approved,
            target,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: String::new(),
            },
        )
        .expect_err("blank hierarchy rejection is not actionable");
    assert!(error.to_string().contains("rejection comment"), "{error}");

    let mut focus_session =
        HierarchyReviewSession::new(&draft, &approved).expect("create focus session");
    approve_all_note_maps(&mut focus_session, &draft, &approved);
    approve_all_branches(&mut focus_session, &draft, &approved);
    let error = focus_session
        .record_focus_coverage(
            &draft,
            &approved,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: String::new(),
            },
        )
        .expect_err("blank focus-coverage rejection is not actionable");
    assert!(error.to_string().contains("rejection comment"), "{error}");
}

#[test]
fn approved_set_requires_all_64_current_candidates_to_be_approved() {
    let proposal = proposal();
    let mut session = NoteReviewSession::new(&proposal).expect("create session");
    for note in &proposal.notes {
        session
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: if note.slot == 64 {
                        ReviewOutcome::Rejected
                    } else {
                        ReviewOutcome::Approved
                    },
                    comment: if note.slot == 64 {
                        "The candidate text is truncated.".to_owned()
                    } else {
                        String::new()
                    },
                },
            )
            .expect("record decision");
    }
    let error = ApprovedNoteSet::from_review(&proposal, &session)
        .expect_err("one rejection prevents publication");
    assert!(error.to_string().contains("63 of 64"), "{error}");

    session
        .record(
            &proposal,
            64,
            NoteReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: "Approved after reconsideration.".to_owned(),
            },
        )
        .expect("replace the current decision");
    let approved = ApprovedNoteSet::from_review(&proposal, &session)
        .expect("all current candidates are approved");
    assert_eq!(approved.notes.len(), 64);
    assert_eq!(
        approved
            .notes
            .iter()
            .map(|note| (note.slot, note.note_id.clone()))
            .collect::<BTreeMap<_, _>>()
            .len(),
        64
    );

    let mut tampered_identity = approved.clone();
    tampered_identity.proposal_sha256 = "f".repeat(64);
    let error = tampered_identity
        .validate()
        .expect_err("the approved set must verify its proposal identity");
    assert!(error.to_string().contains("proposal SHA-256"), "{error}");
}

fn approved_notes() -> ApprovedNoteSet {
    let proposal = proposal();
    let mut session = NoteReviewSession::new(&proposal).expect("create session");
    for note in &proposal.notes {
        session
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("approve note");
    }
    ApprovedNoteSet::from_review(&proposal, &session).expect("publish fixture notes")
}

fn hierarchy(approved: &ApprovedNoteSet) -> HierarchyDraft {
    let leaf = |id: &str, label: &str, slots: std::ops::RangeInclusive<usize>| SubjectNode {
        node_id: id.to_owned(),
        label: label.to_owned(),
        scope: format!("Notes about {label}"),
        children: vec![],
        memberships: slots
            .map(|slot| LeafMembership {
                note_id: approved.notes[slot - 1].note_id.clone(),
                strength: if slot % 3 == 0 {
                    MembershipStrength::Central
                } else if slot % 3 == 1 {
                    MembershipStrength::Substantive
                } else {
                    MembershipStrength::Incidental
                },
            })
            .collect(),
    };
    let mut draft = HierarchyDraft {
        schema_version: 1,
        draft_id: "crec-116-reference-v1".to_owned(),
        approved_notes_sha256: approved.identity().expect("approved notes identity"),
        root_node_id: "all-subjects".to_owned(),
        nodes: vec![
            SubjectNode {
                node_id: "all-subjects".to_owned(),
                label: "All subjects".to_owned(),
                scope: "Hidden navigation root".to_owned(),
                children: vec!["technology".to_owned(), "life".to_owned()],
                memberships: vec![],
            },
            SubjectNode {
                node_id: "technology".to_owned(),
                label: "Technology".to_owned(),
                scope: "Computing and engineered systems".to_owned(),
                children: vec!["software".to_owned(), "hardware".to_owned()],
                memberships: vec![],
            },
            SubjectNode {
                node_id: "life".to_owned(),
                label: "Everyday life".to_owned(),
                scope: "Daily activities and personal experience".to_owned(),
                children: vec!["food".to_owned(), "outdoors".to_owned()],
                memberships: vec![],
            },
            leaf("software", "Software", 1..=16),
            leaf("hardware", "Hardware", 17..=32),
            leaf("food", "Food", 33..=48),
            leaf("outdoors", "Outdoors", 49..=64),
        ],
    };
    draft
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "food")
        .expect("food leaf")
        .memberships
        .extend([
            LeafMembership {
                note_id: approved.notes[2].note_id.clone(),
                strength: MembershipStrength::Substantive,
            },
            LeafMembership {
                note_id: approved.notes[24].note_id.clone(),
                strength: MembershipStrength::Central,
            },
        ]);
    draft
}

fn approve_all_note_maps_branches_and_focus(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_note_maps(session, hierarchy, approved);
    approve_all_branches(session, hierarchy, approved);
    session
        .record_focus_coverage(hierarchy, approved, approved_hierarchy_decision())
        .expect("approve focus-concentration coverage");
}

fn approve_all_note_maps(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    while !session.all_note_maps_approved(hierarchy, approved) {
        let target = session
            .reviewable_targets(hierarchy, approved)
            .expect("list reviewable note maps")
            .into_iter()
            .next()
            .expect("an unapproved note has a reviewable note map");
        assert!(matches!(target, HierarchyReviewTarget::NoteMap { .. }));
        session
            .record(hierarchy, approved, target, approved_hierarchy_decision())
            .expect("approve note map");
    }
}

fn approve_all_branches(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    while !session.all_branches_approved(hierarchy, approved) {
        let target = session
            .reviewable_targets(hierarchy, approved)
            .expect("list reviewable hierarchy branches")
            .into_iter()
            .next()
            .expect("an incomplete hierarchy has a reviewable branch");
        assert!(matches!(target, HierarchyReviewTarget::Branch { .. }));
        session
            .record(hierarchy, approved, target, approved_hierarchy_decision())
            .expect("approve hierarchy branch");
    }
}

fn approve_complete_hierarchy(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_note_maps_branches_and_focus(session, hierarchy, approved);
}

fn approved_hierarchy_decision() -> HierarchyReviewDecision {
    HierarchyReviewDecision {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }
}

#[test]
fn hierarchy_validation_enforces_grounded_bounded_tree() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    hierarchy
        .validate(&approved)
        .expect("grounded four-leaf hierarchy is valid");

    let mut too_wide = hierarchy.clone();
    for index in 0..7 {
        let id = format!("extra-{index}");
        too_wide.nodes[0].children.push(id.clone());
        too_wide.nodes.push(SubjectNode {
            node_id: id,
            label: format!("Extra {index}"),
            scope: "Deliberately exceeds the child bound".to_owned(),
            children: vec![],
            memberships: vec![LeafMembership {
                note_id: approved.notes[0].note_id.clone(),
                strength: MembershipStrength::Incidental,
            }],
        });
    }
    let error = too_wide
        .validate(&approved)
        .expect_err("every internal node is limited to eight choices");
    assert!(error.to_string().contains("at most 8 children"), "{error}");

    let mut root_leaf = hierarchy;
    root_leaf.nodes = vec![SubjectNode {
        node_id: root_leaf.root_node_id.clone(),
        label: "Everything".to_owned(),
        scope: "A flat list without subject navigation".to_owned(),
        children: vec![],
        memberships: approved
            .notes
            .iter()
            .map(|note| LeafMembership {
                note_id: note.note_id.clone(),
                strength: MembershipStrength::Central,
            })
            .collect(),
    }];
    let error = root_leaf
        .validate(&approved)
        .expect_err("the hidden root must expose subject choices");
    assert!(
        error.to_string().contains("root must be internal"),
        "{error}"
    );
}

#[test]
fn hierarchy_validation_allows_an_honest_leaf_with_sparse_strength_coverage() {
    let approved = approved_notes();
    let mut hierarchy = hierarchy(&approved);
    let software = hierarchy
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "software")
        .expect("software leaf");
    for membership in &mut software.memberships {
        membership.strength = MembershipStrength::Central;
    }

    hierarchy
        .validate(&approved)
        .expect("a real subject does not require artificial examples at every strength");
}

#[test]
fn hierarchy_allows_a_diffuse_note_without_a_central_membership() {
    let approved = approved_notes();
    let mut hierarchy = hierarchy(&approved);
    let diffuse_note_id = approved.notes[24].note_id.as_str();
    for membership in hierarchy
        .nodes
        .iter_mut()
        .flat_map(|node| &mut node.memberships)
        .filter(|membership| membership.note_id == diffuse_note_id)
    {
        membership.strength = MembershipStrength::Substantive;
    }

    hierarchy
        .validate(&approved)
        .expect("several substantive memberships are a valid diffuse focus pattern");
}

#[test]
fn hierarchy_review_unlocks_branches_only_after_all_note_maps_are_approved() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");

    let initial_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list initial reviewable items");
    assert_eq!(initial_targets.len(), 64);
    assert_eq!(
        initial_targets.first(),
        Some(&HierarchyReviewTarget::NoteMap {
            note_id: approved.notes[0].note_id.clone(),
        })
    );
    assert_eq!(
        initial_targets.last(),
        Some(&HierarchyReviewTarget::NoteMap {
            note_id: approved.notes[63].note_id.clone(),
        })
    );
    assert!(
        initial_targets
            .iter()
            .all(|target| matches!(target, HierarchyReviewTarget::NoteMap { .. })),
        "the first stage reviews complete note maps"
    );
    let error = session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Branch {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: String::new(),
            },
        )
        .expect_err("a branch cannot be judged before every note map");
    assert!(
        error.to_string().contains("not currently reviewable"),
        "{error}"
    );

    approve_all_note_maps(&mut session, &hierarchy, &approved);
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list root branches"),
        vec![
            HierarchyReviewTarget::Branch {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Branch {
                node_id: "life".to_owned(),
            },
        ]
    );
    let error = session
        .record_focus_coverage(
            &hierarchy,
            &approved,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: String::new(),
            },
        )
        .expect_err("coverage remains locked until every branch is approved");
    assert!(
        error
            .to_string()
            .contains("every note map and hierarchy branch"),
        "{error}"
    );
}

#[test]
fn hierarchy_review_orders_note_maps_then_root_branches() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");

    let note_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list note maps");
    let expected_note_targets = approved
        .notes
        .iter()
        .map(|note| HierarchyReviewTarget::NoteMap {
            note_id: note.note_id.clone(),
        })
        .collect::<Vec<_>>();
    assert_eq!(
        note_targets, expected_note_targets,
        "note maps follow approved-note slot order"
    );
    approve_all_note_maps(&mut session, &hierarchy, &approved);
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list root branches"),
        vec![
            HierarchyReviewTarget::Branch {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Branch {
                node_id: "life".to_owned(),
            },
        ],
        "branch reviews follow hidden-root child order"
    );
}

#[test]
fn rejected_branch_keeps_its_sibling_reviewable_but_blocks_coverage() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_note_maps(&mut session, &hierarchy, &approved);

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Branch {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "Item 2 does not belong under this branch.".to_owned(),
            },
        )
        .expect("reject one branch");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list sibling branch after rejection"),
        vec![HierarchyReviewTarget::Branch {
            node_id: "life".to_owned(),
        }],
        "one rejected branch must not suppress its undecided sibling"
    );

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Branch {
                node_id: "life".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve the sibling branch");
    assert!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list targets after both branch decisions")
            .is_empty(),
        "a rejected branch blocks the final coverage check"
    );
    let error = session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect_err("coverage cannot approve a rejected branch");
    assert!(
        error
            .to_string()
            .contains("every note map and hierarchy branch"),
        "{error}"
    );
}

#[test]
fn rejected_note_map_keeps_other_notes_reviewable_but_blocks_branches() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    let rejected_target = HierarchyReviewTarget::NoteMap {
        note_id: approved.notes[0].note_id.clone(),
    };
    session
        .record(
            &hierarchy,
            &approved,
            rejected_target,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "The Software assignment is not expressed.".to_owned(),
            },
        )
        .expect("reject the first note map");

    let remaining = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list remaining note maps");
    assert_eq!(remaining.len(), 63);
    assert!(remaining
        .iter()
        .all(|target| matches!(target, HierarchyReviewTarget::NoteMap { .. })));
    for target in remaining {
        session
            .record(&hierarchy, &approved, target, approved_hierarchy_decision())
            .expect("decide every remaining note map");
    }

    assert!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list targets after all note-map decisions")
            .is_empty(),
        "a rejected note map blocks branch review after the remaining notes are gathered"
    );
    assert_eq!(
        session
            .decision_counts(&hierarchy, &approved)
            .expect("count grouped decisions"),
        (63, 1, 67)
    );
}

#[test]
fn changed_leaf_definition_preserves_note_assignments_but_reopens_its_root_branch() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let mut revised = hierarchy.clone();
    revised.draft_id = "crec-116-reference-v2".to_owned();
    revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "software")
        .expect("software leaf")
        .scope = "Software construction and programming tools".to_owned();
    revised.validate(&approved).expect("revised hierarchy");

    for note in &approved.notes {
        assert!(
            session.is_approved(
                &revised,
                &approved,
                &HierarchyReviewTarget::NoteMap {
                    note_id: note.note_id.clone(),
                }
            ),
            "a hidden definition does not change displayed subject assignments"
        );
    }
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Branch {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Branch {
            node_id: "life".to_owned(),
        }
    ));
    assert!(
        session.focus_coverage_is_approved(&revised, &approved),
        "a scope-only edit does not change the membership summary shown by the coverage check"
    );
    let next_targets = session
        .reviewable_targets(&revised, &approved)
        .expect("list reopened branch");
    assert_eq!(
        next_targets,
        vec![HierarchyReviewTarget::Branch {
            node_id: "technology".to_owned(),
        }]
    );
}

#[test]
fn note_map_revision_matches_only_the_displayed_v2_evidence() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let note = &approved.notes[0];
    let target = HierarchyReviewTarget::NoteMap {
        note_id: note.note_id.clone(),
    };
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    session
        .record(&hierarchy, &approved, target, approved_hierarchy_decision())
        .expect("approve first note assignments");

    let serialized = serde_json::to_value(&session).expect("serialize hierarchy session");
    let actual_revision = serialized["history"][0]["target_revision_sha256"]
        .as_str()
        .expect("stored note-map revision");
    let displayed_assignments = vec![("Software", MembershipStrength::Substantive)];
    let expected_revision = sha256(
        &serde_json::to_vec(&(
            "note-map-review-v2",
            note.slot,
            note.note_id.as_str(),
            note.content.as_str(),
            displayed_assignments,
        ))
        .expect("encode displayed note-map evidence"),
    );

    assert_eq!(actual_revision, expected_revision);
}

#[test]
fn changed_membership_invalidates_its_note_map_and_focus_but_not_branches() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let changed_note_id = approved.notes[0].note_id.clone();
    let mut revised = hierarchy;
    revised.draft_id = "crec-116-membership-revision".to_owned();
    revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "software")
        .expect("software leaf")
        .memberships
        .iter_mut()
        .find(|membership| membership.note_id == changed_note_id)
        .expect("changed note membership")
        .strength = MembershipStrength::Central;
    revised.validate(&approved).expect("revised hierarchy");

    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::NoteMap {
            note_id: changed_note_id,
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::NoteMap {
            note_id: approved.notes[1].note_id.clone(),
        }
    ));
    for node_id in ["technology", "life"] {
        assert!(session.is_approved(
            &revised,
            &approved,
            &HierarchyReviewTarget::Branch {
                node_id: node_id.to_owned(),
            }
        ));
    }
    assert!(!session.focus_coverage_is_approved(&revised, &approved));
}

#[test]
fn changed_leaf_label_invalidates_the_displayed_coverage_summary() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let mut revised = hierarchy;
    revised.draft_id = "crec-116-label-revision".to_owned();
    revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "food")
        .expect("food leaf")
        .label = "Food and cooking".to_owned();
    revised.validate(&approved).expect("revised hierarchy");

    assert!(
        !session.focus_coverage_is_approved(&revised, &approved),
        "the final summary visibly contains subject labels"
    );
}

#[test]
fn parent_only_revision_preserves_note_maps_and_focus_but_reopens_its_branch() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let mut revised = hierarchy;
    revised.draft_id = "crec-116-parent-revision".to_owned();
    revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "technology")
        .expect("technology parent")
        .scope = "Software and hardware systems".to_owned();
    revised
        .validate(&approved)
        .expect("revised parent is valid");

    assert!(
        session.all_note_maps_approved(&revised, &approved),
        "a parent-only edit does not change any visible note map"
    );
    assert!(
        session.focus_coverage_is_approved(&revised, &approved),
        "a parent-only edit does not change the reviewed leaf membership map"
    );
    assert_eq!(
        session
            .reviewable_targets(&revised, &approved)
            .expect("list reopened branch"),
        vec![HierarchyReviewTarget::Branch {
            node_id: "technology".to_owned(),
        }]
    );
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Branch {
            node_id: "life".to_owned(),
        }
    ));
}

#[test]
fn rejected_focus_coverage_blocks_grouped_publication() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_note_maps(&mut session, &hierarchy, &approved);
    approve_all_branches(&mut session, &hierarchy, &approved);
    session
        .record_focus_coverage(
            &hierarchy,
            &approved,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "The set lacks a note with several substantive memberships.".to_owned(),
            },
        )
        .expect("record the concrete coverage gap");

    assert!(session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list items after rejected focus coverage")
        .is_empty());
    assert!(!session.review_is_complete(&hierarchy, &approved));
    let error = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect_err("rejected focus coverage prevents publication");
    assert!(
        error.to_string().contains("focus-concentration coverage"),
        "{error}"
    );
}

#[test]
fn hierarchy_publication_requires_each_current_root_branch() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_note_maps(&mut session, &hierarchy, &approved);
    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Branch {
                node_id: "technology".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve first root branch");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list remaining root branch"),
        vec![HierarchyReviewTarget::Branch {
            node_id: "life".to_owned(),
        }]
    );
    let error = session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect_err("coverage cannot bypass an unapproved root branch");
    assert!(error.to_string().contains("hierarchy branch"), "{error}");

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Branch {
                node_id: "life".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve final root branch");
    session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect("approve final coverage check");
    let frozen = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect("publish approved hierarchy");
    assert_eq!(frozen.notes.len(), 64);
    assert_eq!(frozen.nodes.len(), 7);
}

#[test]
fn changing_the_hidden_root_definition_preserves_root_branch_approvals() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let mut revised = hierarchy;
    let root_node_id = revised.root_node_id.clone();
    let root = revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == root_node_id)
        .expect("hidden root");
    root.label = "Unseen internal root label".to_owned();
    root.scope = "Unseen internal root description".to_owned();
    root.children.reverse();
    revised
        .validate(&approved)
        .expect("hidden-root definition may change structurally");

    for child_id in ["technology", "life"] {
        assert!(
            session.is_approved(
                &revised,
                &approved,
                &HierarchyReviewTarget::Branch {
                    node_id: child_id.to_owned(),
                }
            ),
            "changing unseen root metadata or ordering must not invalidate {child_id}'s visible branch"
        );
    }
    assert!(
        session.review_is_complete(&revised, &approved),
        "the hidden root has no review screen of its own"
    );
    ApprovedHierarchy::from_review(&revised, &approved, &session)
        .expect("publish after changing only unseen hidden-root fields");
}

fn frozen_hierarchy() -> ApprovedHierarchy {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);
    ApprovedHierarchy::from_review(&hierarchy, &approved, &session).expect("freeze hierarchy")
}

#[test]
fn navigation_advances_one_edge_and_back_restores_each_cursor() {
    let hierarchy = frozen_hierarchy();
    let mut navigation = ReferenceNavigation::new(&hierarchy).expect("open frozen hierarchy");
    assert_eq!(navigation.current_node_id(), "all-subjects");

    navigation.move_next(&hierarchy);
    assert_eq!(navigation.selected_index(), 1);
    navigation.enter(&hierarchy).expect("enter life");
    assert_eq!(navigation.current_node_id(), "life");

    navigation.move_next(&hierarchy);
    assert_eq!(navigation.selected_index(), 1);
    navigation.enter(&hierarchy).expect("enter outdoors");
    assert_eq!(navigation.current_node_id(), "outdoors");

    navigation.back();
    assert_eq!(navigation.current_node_id(), "life");
    assert_eq!(navigation.selected_index(), 1);
    navigation.back();
    assert_eq!(navigation.current_node_id(), "all-subjects");
    assert_eq!(navigation.selected_index(), 1);
}

#[test]
fn leaf_notes_use_strength_then_note_id_and_multi_membership_remains_multi_path() {
    let hierarchy = frozen_hierarchy();
    let food = hierarchy
        .leaf_notes("food")
        .expect("resolve ordered food notes");
    assert_eq!(
        food.first().expect("food leaf has notes").note_id,
        hierarchy.notes[24].note_id,
        "the added central multi-membership note leads the leaf"
    );
    let hardware = hierarchy
        .leaf_notes("hardware")
        .expect("resolve ordered hardware notes");
    assert!(
        hardware
            .iter()
            .any(|note| note.note_id == hierarchy.notes[24].note_id),
        "the same note remains reachable from its other approved leaf"
    );
}

#[derive(Default)]
struct ScriptedUi {
    actions: VecDeque<ApprovalTuiAction>,
    screens: Vec<ApprovalScreen>,
}

impl ScriptedUi {
    fn new(actions: impl IntoIterator<Item = ApprovalTuiAction>) -> Self {
        Self {
            actions: actions.into_iter().collect(),
            screens: Vec::new(),
        }
    }
}

impl ApprovalUi for ScriptedUi {
    fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction> {
        self.screens.push(screen);
        self.actions
            .pop_front()
            .ok_or_else(|| io::Error::other("scripted UI has no action"))
    }
}

fn approve_action() -> ApprovalTuiAction {
    ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }
}

fn write_json(path: &std::path::Path, value: &impl serde::Serialize) {
    fs::write(
        path,
        serde_json::to_vec_pretty(value).expect("encode fixture"),
    )
    .expect("write fixture");
}

fn write_review_session_value(path: &std::path::Path, session: &impl serde::Serialize) {
    let state_sha256 = sha256(&serde_json::to_vec(session).expect("encode session state"));
    write_json(
        path,
        &serde_json::json!({
            "schema_version": 1,
            "state_sha256": state_sha256,
            "session": session,
        }),
    );
}

#[derive(serde::Serialize)]
struct LegacyHierarchySessionFixture {
    schema_version: u32,
    history: Vec<LegacyHierarchyRecordFixture>,
    focus_coverage_history: Vec<LegacyFocusCoverageRecordFixture>,
}

#[derive(serde::Serialize)]
struct LegacyHierarchyRecordFixture {
    node_id: String,
    node_revision_sha256: String,
    decision: HierarchyReviewDecision,
}

#[derive(serde::Serialize)]
struct LegacyFocusCoverageRecordFixture {
    leaf_map_revision_sha256: String,
    decision: HierarchyReviewDecision,
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn legacy_note_sha256(note: &ProposedNote, interpretive_ambiguity: bool) -> String {
    #[derive(serde::Serialize)]
    struct LegacyProposedNote<'a> {
        slot: u8,
        note_id: &'a str,
        pubkey: &'a str,
        content: &'a str,
        interpretive_ambiguity: bool,
        contrast_pair: &'a Option<PairMembership>,
        broad_narrow_pair: &'a Option<PairMembership>,
        niche_or_sparse_case: &'a Option<String>,
    }

    sha256(
        &serde_json::to_vec(&LegacyProposedNote {
            slot: note.slot,
            note_id: &note.note_id,
            pubkey: &note.pubkey,
            content: &note.content,
            interpretive_ambiguity,
            contrast_pair: &note.contrast_pair,
            broad_narrow_pair: &note.broad_narrow_pair,
            niche_or_sparse_case: &note.niche_or_sparse_case,
        })
        .expect("encode legacy proposed note"),
    )
}

fn write_source_bound_proposal(directory: &std::path::Path) -> (std::path::PathBuf, NoteProposal) {
    let sample_path = directory.join("sample.jsonl");
    let proposal_path = directory.join("proposal.json");
    let mut fixture = proposal();
    fixture.source.sample_path = "sample.jsonl".to_owned();
    let sample = fixture
        .notes
        .iter()
        .map(|note| {
            serde_json::json!({
                "split": "learning",
                "note_id": note.note_id,
                "pubkey": note.pubkey,
                "content": note.content,
            })
            .to_string()
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n";
    fs::write(&sample_path, sample.as_bytes()).expect("write sample");
    fixture.source.sample_sha256 = sha256(sample.as_bytes());
    write_json(&proposal_path, &fixture);
    (proposal_path, fixture)
}

#[test]
fn hierarchy_runner_reviews_one_note_map_per_action() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut ui = ScriptedUi::new([approve_action(), ApprovalTuiAction::Pause]);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("approve one note map, then pause"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(ui.screens.len(), 2);
    let first = &ui.screens[0];
    assert_eq!(first.title, "Note map · Slot 01");
    assert_eq!(first.scope, "Are these subject assignments correct?");
    assert_eq!(first.approve_label, "Approve these assignments");
    assert_eq!(first.reject_label, "Reject — name the exact correction");
    assert_eq!(first.evidence_layout, ApprovalEvidenceLayout::Stacked);
    assert_eq!(first.evidence.len(), 2);
    assert_eq!(first.evidence[0].body, "Real diagnostic note number 0");
    assert!(first.evidence[1].body.contains("Software — Substantive"));
    assert!(!first.evidence[0]
        .body
        .contains("Real diagnostic note number 1"));
    assert_eq!(ui.screens[1].title, "Note map · Slot 02");
}

#[test]
fn hierarchy_runner_opens_first_root_branch_after_all_note_maps() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut actions = (0..64).map(|_| approve_action()).collect::<Vec<_>>();
    actions.push(ApprovalTuiAction::Pause);
    let mut ui = ScriptedUi::new(actions);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("approve every note map, then pause"),
        ReviewRunOutcome::Paused
    );
    let branch = ui.screens.last().expect("first root branch screen");
    assert_eq!(branch.title, "Hierarchy branch · Technology");
    assert_eq!(
        branch.scope,
        "Does this complete branch contain a concrete subject or hierarchy problem?"
    );
    assert_eq!(
        branch.approve_label,
        "Approve — all subjects and relationships are correct"
    );
    assert_eq!(branch.reject_label, "Reject — name the exact correction");
}

#[test]
fn hierarchy_runner_reviews_a_complete_root_branch_once() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut actions = (0..65).map(|_| approve_action()).collect::<Vec<_>>();
    actions.push(ApprovalTuiAction::Pause);
    let mut ui = ScriptedUi::new(actions);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("approve the first complete branch, then pause"),
        ReviewRunOutcome::Paused
    );
    let technology = &ui.screens[64];
    assert_eq!(technology.title, "Hierarchy branch · Technology");
    assert_eq!(technology.evidence.len(), 1);
    assert!(technology
        .guidance
        .as_ref()
        .expect("branch decision is explained")
        .body
        .contains(
            "Approving accepts every displayed subject definition and parent–child relationship."
        ));
    let branch = &technology.evidence[0].body;
    assert!(branch.contains("[01] Technology"));
    assert!(branch.contains("[02] Software"));
    assert!(branch.contains("[03] Hardware"));
    assert_eq!(
        ui.screens[65].title, "Hierarchy branch · Everyday life",
        "one branch approval advances directly to the next root branch"
    );
}

#[test]
fn hierarchy_runner_migrates_only_empty_prior_sessions_to_schema_four() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    for prior_schema in [2, 3] {
        let session_path = temp
            .path()
            .join(format!("hierarchy-session-schema-{prior_schema}.json"));
        write_review_session_value(
            &session_path,
            &LegacyHierarchySessionFixture {
                schema_version: prior_schema,
                history: Vec::new(),
                focus_coverage_history: Vec::new(),
            },
        );
        let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);
        assert_eq!(
            run_hierarchy_review(
                &notes_path,
                &draft_path,
                &session_path,
                temp.path()
                    .join(format!("approved-hierarchy-{prior_schema}.json")),
                &mut ui,
            )
            .expect("migrate the empty prior session"),
            ReviewRunOutcome::Paused
        );
        assert_eq!(ui.screens[0].title, "Note map · Slot 01");
        let migrated: serde_json::Value =
            serde_json::from_slice(&fs::read(&session_path).expect("read migrated session"))
                .expect("decode migrated session");
        assert_eq!(migrated["session"]["schema_version"], 4);
        assert_eq!(migrated["session"]["history"], serde_json::json!([]));
        assert_eq!(
            migrated["session"]["focus_coverage_history"],
            serde_json::json!([])
        );
    }
}

#[test]
fn hierarchy_runner_refuses_nonempty_prior_review_state() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let cases = [
        (
            "schema-2-node-history",
            LegacyHierarchySessionFixture {
                schema_version: 2,
                history: vec![LegacyHierarchyRecordFixture {
                    node_id: "software".to_owned(),
                    node_revision_sha256: "0".repeat(64),
                    decision: approved_hierarchy_decision(),
                }],
                focus_coverage_history: Vec::new(),
            },
        ),
        (
            "schema-2-focus-history",
            LegacyHierarchySessionFixture {
                schema_version: 2,
                history: Vec::new(),
                focus_coverage_history: vec![LegacyFocusCoverageRecordFixture {
                    leaf_map_revision_sha256: "0".repeat(64),
                    decision: approved_hierarchy_decision(),
                }],
            },
        ),
        (
            "schema-3-node-history",
            LegacyHierarchySessionFixture {
                schema_version: 3,
                history: vec![LegacyHierarchyRecordFixture {
                    node_id: "software".to_owned(),
                    node_revision_sha256: "0".repeat(64),
                    decision: approved_hierarchy_decision(),
                }],
                focus_coverage_history: Vec::new(),
            },
        ),
    ];

    for (name, session) in cases {
        let session_path = temp.path().join(format!("{name}.json"));
        write_review_session_value(&session_path, &session);
        let mut ui = ScriptedUi::new([]);
        let error = run_hierarchy_review(
            &notes_path,
            &draft_path,
            &session_path,
            temp.path().join(format!("{name}-approved.json")),
            &mut ui,
        )
        .expect_err("non-empty bundled state must not be silently reinterpreted");
        assert!(
            error
                .to_string()
                .contains("cannot be reinterpreted as note-map and branch reviews"),
            "{name}: {error}"
        );
        assert!(
            ui.screens.is_empty(),
            "{name}: invalid legacy state reached the review UI"
        );
    }
}

#[test]
fn note_review_screen_asks_only_for_a_concrete_disqualifying_problem() {
    let temp = tempfile::tempdir().expect("tempdir");
    let (proposal_path, _) = write_source_bound_proposal(temp.path());
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    assert_eq!(
        run_note_review(
            &proposal_path,
            temp.path().join("session.json"),
            temp.path().join("approved.json"),
            &mut ui,
        )
        .expect("open the first review screen"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(ui.screens[0].title, "Slot 01");
    assert_eq!(
        ui.screens[0].scope,
        "Is there a concrete reason this note should not be included in the 64-note reference set?"
    );
    assert_eq!(
        ui.screens[0].approve_label,
        "Approve — no disqualifying problem"
    );
    assert_eq!(ui.screens[0].reject_label, "Reject — explain the problem");
    let comparison = &ui.screens[0].evidence[1];
    assert_eq!(
        comparison.body, "Real diagnostic note number 1",
        "the comparison panel must contain only the exact note text"
    );
    assert!(
        comparison
            .annotation
            .contains("Shown only to judge this relationship"),
        "the comparison explanation belongs outside the note panel"
    );
    let guidance = ui.screens[0]
        .guidance
        .as_ref()
        .expect("note review must provide an optional rejection guide");
    assert_eq!(guidance.title, "Rejection guide");
    assert!(guidance.body.contains("missing context"));
    assert!(guidance.body.contains("Do not reject merely because"));
    assert!(guidance
        .body
        .contains("A URL is only a problem when its contents are necessary"));
    let rendered = format!("{:?}", ui.screens[0]).to_lowercase();
    assert!(
        !rendered.contains("single subject")
            && !rendered.contains("mixed subject")
            && !rendered.contains("why selected"),
        "the review must not claim a discrete focus category"
    );
}

#[test]
fn note_review_runner_resumes_at_the_first_undecided_slot() {
    let temp = tempfile::tempdir().expect("tempdir");
    let (proposal_path, _) = write_source_bound_proposal(temp.path());
    let session_path = temp.path().join("session.json");
    let approved_path = temp.path().join("approved.json");

    let mut first = ScriptedUi::new([
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: "Good diagnostic note.".to_owned(),
        },
        ApprovalTuiAction::Pause,
    ]);
    assert_eq!(
        run_note_review(&proposal_path, &session_path, &approved_path, &mut first)
            .expect("first pass"),
        ReviewRunOutcome::Paused
    );
    assert!(first.screens[0].title.contains("Slot 01"));
    assert!(first.screens[1].title.contains("Slot 02"));

    let mut resumed = ScriptedUi::new((0..63).map(|_| ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }));
    assert_eq!(
        run_note_review(&proposal_path, &session_path, &approved_path, &mut resumed)
            .expect("resumed pass"),
        ReviewRunOutcome::Approved
    );
    assert!(resumed.screens[0].title.contains("Slot 02"));
    assert!(approved_path.is_file());
}

#[test]
fn note_review_runner_rejects_content_not_present_in_its_bound_source() {
    let temp = tempfile::tempdir().expect("tempdir");
    let (proposal_path, mut fixture) = write_source_bound_proposal(temp.path());
    fixture.notes[0].content.push_str(" fabricated");
    write_json(&proposal_path, &fixture);
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    let error = run_note_review(
        &proposal_path,
        temp.path().join("session.json"),
        temp.path().join("approved.json"),
        &mut ui,
    )
    .expect_err("the review runner must enforce source binding itself");
    assert!(
        error.to_string().contains("does not exactly match"),
        "{error}"
    );
    assert!(ui.screens.is_empty(), "unverified content reached the UI");
}

#[test]
fn hierarchy_runner_reviews_each_note_once_then_each_root_branch_once_then_coverage() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let root = draft.node(&draft.root_node_id).expect("hidden root");
    let decision_count = notes.notes.len() + root.children.len() + 1;
    let mut ui = ScriptedUi::new((0..decision_count).map(|_| approve_action()));
    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            &session_path,
            &approved_path,
            &mut ui,
        )
        .expect("hierarchy review"),
        ReviewRunOutcome::Approved
    );
    assert_eq!(ui.screens.len(), decision_count);

    for (index, screen) in ui.screens[..64].iter().enumerate() {
        assert_eq!(screen.title, format!("Note map · Slot {:02}", index + 1));
        assert!(
            screen.evidence[0]
                .body
                .contains(&format!("Real diagnostic note number {index}")),
            "each note is read exactly once in approved-note order"
        );
    }

    let multi_subject = &ui.screens[2];
    assert_eq!(
        multi_subject.scope,
        "Are these subject assignments correct?"
    );
    assert!(multi_subject.evidence[1]
        .body
        .contains("Software — Central"));
    assert!(multi_subject.evidence[1]
        .body
        .contains("Food — Substantive"));

    assert_eq!(
        ui.screens[64..66]
            .iter()
            .map(|screen| screen.title.as_str())
            .collect::<Vec<_>>(),
        vec![
            "Hierarchy branch · Technology",
            "Hierarchy branch · Everyday life",
        ],
        "each top-level branch is loaded once"
    );
    assert_eq!(ui.screens[66].title, "Focus-concentration coverage");
    assert!(
        ui.screens
            .iter()
            .all(|screen| screen.heading.contains("67 total")),
        "the UI must state the reduced interaction count"
    );
    assert!(approved_path.is_file());
}

#[test]
fn hierarchy_runner_audits_focus_coverage_after_note_maps_and_branches() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let decisions_before_coverage = 64 + 2;
    let mut actions = (0..decisions_before_coverage)
        .map(|_| ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new(),
        })
        .collect::<Vec<_>>();
    actions.push(ApprovalTuiAction::Pause);
    let mut ui = ScriptedUi::new(actions);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            &session_path,
            &approved_path,
            &mut ui,
        )
        .expect("pause at focus coverage"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].title,
        "Focus-concentration coverage"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].scope,
        "Do the 64 note maps include both concentrated and distributed focus patterns?"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].approve_label,
        "Approve — both patterns are represented"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].reject_label,
        "Reject — describe the missing pattern"
    );
    let guidance = ui.screens[decisions_before_coverage]
        .guidance
        .as_ref()
        .expect("focus coverage explains its decision");
    assert_eq!(guidance.title, "Coverage check");
    assert!(guidance.body.contains("Concentrated"));
    assert!(guidance.body.contains("Distributed"));
    assert!(guidance.body.contains("Central"));
    assert!(guidance.body.contains("Substantive"));
    assert!(guidance.body.contains("Incidental"));
    let rendered_inventory = ui.screens[decisions_before_coverage]
        .evidence
        .iter()
        .map(|evidence| format!("{}\n{}", evidence.annotation, evidence.body))
        .collect::<Vec<_>>()
        .join("\n");
    assert!(rendered_inventory.contains("Central"));
    assert!(rendered_inventory.contains("Substantive"));
    assert!(rendered_inventory.contains("Incidental"));
    assert!(
        !rendered_inventory.contains('%'),
        "ordinal memberships must not be presented as invented percentages"
    );
    assert!(
        !rendered_inventory.contains("Real diagnostic note number"),
        "the final check summarizes the maps without making the reviewer reread notes"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].evidence.len(),
        1,
        "the reviewer scrolls one complete coverage summary instead of switching panels"
    );
    assert!(rendered_inventory.contains("1 membership · Central"));
    assert!(rendered_inventory.contains("1 membership · Substantive"));
    assert!(rendered_inventory.contains("1 membership · Incidental"));
    assert!(rendered_inventory.contains("2 memberships · Central + Substantive"));
}

#[test]
fn note_map_review_shows_every_current_membership_and_strength() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut ui = ScriptedUi::new([approve_action(), approve_action(), ApprovalTuiAction::Pause]);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("open the third note map"),
        ReviewRunOutcome::Paused
    );
    let screen = &ui.screens[2];
    assert_eq!(screen.title, "Note map · Slot 03");
    assert_eq!(screen.evidence.len(), 2);
    assert!(screen.evidence[1].body.contains("Software — Central"));
    assert!(screen.evidence[1].body.contains("Food — Substantive"));
}

#[test]
fn note_map_review_shows_one_exact_note_and_its_assignments() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("open first note map"),
        ReviewRunOutcome::Paused
    );
    let screen = &ui.screens[0];
    assert_eq!(screen.evidence_layout, ApprovalEvidenceLayout::Stacked);
    assert_eq!(screen.evidence.len(), 2);
    let note = &screen.evidence[0];
    let assignments = &screen.evidence[1];
    assert_eq!(note.title, "Note");
    assert_eq!(note.body, "Real diagnostic note number 0");
    assert_eq!(assignments.title, "Proposed subject map");
    assert!(assignments.body.contains("Software — Substantive"));
    assert!(
        !assignments.body.contains("Food —"),
        "only this note's proposed memberships are listed"
    );
    assert!(
        !assignments.body.contains("Real diagnostic note number 0")
            && !assignments.body.contains("Real diagnostic note number 1"),
        "note text never appears in the proposed subject map"
    );
    assert!(
        !assignments.body.contains("Notes about Software"),
        "subject definitions never appear in the proposed subject map"
    );
    assert!(
        !note.body.contains("Real diagnostic note number 1"),
        "another note is never mixed into the grouped decision"
    );
}

#[test]
fn note_map_review_separates_raw_note_from_compact_subject_assignments() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut ui = ScriptedUi::new([ApprovalTuiAction::Pause]);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("open first note map"),
        ReviewRunOutcome::Paused
    );

    let screen = &ui.screens[0];
    assert_eq!(screen.scope, "Are these subject assignments correct?");
    assert_eq!(screen.approve_label, "Approve these assignments");
    assert_eq!(screen.evidence_layout, ApprovalEvidenceLayout::Stacked);
    assert_eq!(screen.evidence.len(), 2);
    assert_eq!(screen.evidence[0].title, "Note");
    assert_eq!(screen.evidence[0].body, notes.notes[0].content);
    assert_eq!(screen.evidence[1].title, "Proposed subject map");
    assert_eq!(screen.evidence[1].body, "Software — Substantive");
    assert!(
        !screen.evidence[1].body.contains("Notes about Software"),
        "subject definitions are not part of note-map review"
    );
    assert!(
        !screen.scope.contains("complete") && !screen.approve_label.contains("complete"),
        "the UI must not claim the proposed assignments exhaust the note's meaning"
    );
}

#[test]
fn note_map_review_states_the_grouped_decision_and_rejection_criteria() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut ui = ScriptedUi::new([approve_action(), approve_action(), ApprovalTuiAction::Pause]);

    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            temp.path().join("hierarchy-session.json"),
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("open multi-subject note map"),
        ReviewRunOutcome::Paused
    );
    let screen = &ui.screens[2];
    assert_eq!(screen.scope, "Are these subject assignments correct?");
    assert_eq!(screen.approve_label, "Approve these assignments");
    assert_eq!(screen.reject_label, "Reject — name the exact correction");
    let guidance = screen
        .guidance
        .as_ref()
        .expect("note-map review explains the grouped decision");
    assert_eq!(guidance.title, "Note-map review");
    assert!(guidance
        .body
        .contains("Approving accepts each listed subject and strength."));
    assert!(guidance
        .body
        .contains("listed subject is not actually expressed"));
    assert!(guidance.body.contains("membership strength is wrong"));
    assert!(guidance.body.contains("Central:"));
    assert!(guidance.body.contains("Substantive:"));
    assert!(guidance.body.contains("Incidental:"));
    assert!(
        !guidance.body.contains("missing") && !guidance.body.contains("description"),
        "assignment approval does not claim exhaustiveness or depend on hidden definitions"
    );
    assert_eq!(screen.evidence.len(), 2);
    assert!(screen.evidence[1].body.contains("Software — Central"));
    assert!(screen.evidence[1].body.contains("Food — Substantive"));
    assert!(
        !screen.evidence[1].body.contains("[1]"),
        "the compact map contains only subject labels and strengths"
    );
}

#[test]
fn verified_note_proposal_is_bound_to_the_real_learning_sample() {
    let temp = tempfile::tempdir().expect("tempdir");
    let sample_path = temp.path().join("sample.jsonl");
    let proposal_path = temp.path().join("proposal.json");
    let mut fixture = proposal();
    fixture.source.sample_path = "sample.jsonl".to_owned();
    let sample = fixture
        .notes
        .iter()
        .map(|note| {
            serde_json::json!({
                "split": "learning",
                "note_id": note.note_id,
                "pubkey": note.pubkey,
                "content": note.content,
            })
            .to_string()
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n";
    fs::write(&sample_path, sample.as_bytes()).expect("write sample");
    fixture.source.sample_sha256 = sha256(sample.as_bytes());
    write_json(&proposal_path, &fixture);

    assert_eq!(
        load_verified_note_proposal(&proposal_path).expect("verified proposal"),
        fixture
    );

    let mut fabricated = fixture;
    fabricated.notes[0].content.push_str(" changed");
    write_json(&proposal_path, &fabricated);
    let error = load_verified_note_proposal(&proposal_path)
        .expect_err("content not present in the bound sample must fail");
    assert!(
        error.to_string().contains("does not exactly match"),
        "{error}"
    );
}

#[test]
fn tracked_crec_115_proposal_is_complete_and_source_bound() {
    let proposal = load_verified_note_proposal("reference_map/crec-115-note-proposal-v2.json")
        .expect("tracked CREC-115 proposal");
    assert_eq!(proposal.notes.len(), 64);
    assert_eq!(
        proposal
            .notes
            .iter()
            .map(|note| note.note_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        64
    );
}

#[test]
fn tracked_crec_115_revision_uses_the_balanced_candidate_set() {
    let proposal = load_verified_note_proposal("reference_map/crec-115-note-proposal-v2.json")
        .expect("tracked CREC-115 proposal");
    let expected = [
        (
            55,
            "f82b8f1742cf74cb2ab19bdbfa249e9685f035b1856c17673444686919ca7807",
        ),
        (
            58,
            "58e8c1ebebaf100ee5e3d1a217912c2723bf8b1ecd3543e3db28f1a81b7cdf92",
        ),
        (
            61,
            "474a14dc8aab2970ad2efed18be1e4f000322bf269ad90e8586e6847c0ca95c9",
        ),
        (
            62,
            "d2dfe7c80ca031b768e525e904f3c5d1d962faf297158f59a1959b06d585225d",
        ),
        (
            63,
            "8384ac9f054d38e55628cea9395080dce3fa2f8be7a2fa9bd9f2ab9acc0c94ae",
        ),
        (
            64,
            "54646e5fe43713934c879371c5ce462337b78d7db728c68f088614e27844f7db",
        ),
    ];

    for (slot, note_id) in expected {
        let note = proposal
            .notes
            .iter()
            .find(|note| note.slot == slot)
            .expect("expected proposal slot");
        assert_eq!(note.note_id, note_id, "unexpected note in slot {slot}");
    }
}

#[test]
fn tracked_crec_115_plan_matches_the_source_bound_proposal() {
    let plan: serde_json::Value = serde_json::from_slice(
        &fs::read("reference_map/crec-115-note-metadata-v2.json").expect("read selection plan"),
    )
    .expect("decode selection plan");
    let proposal: serde_json::Value = serde_json::from_slice(
        &fs::read("reference_map/crec-115-note-proposal-v2.json").expect("read note proposal"),
    )
    .expect("decode note proposal");

    assert_eq!(plan["schema_version"], proposal["schema_version"]);
    assert_eq!(plan["proposal_id"], proposal["proposal_id"]);
    assert_eq!(plan["source"], proposal["source"]);

    let projected_notes = proposal["notes"]
        .as_array()
        .expect("proposal notes")
        .iter()
        .map(|note| {
            serde_json::json!({
                "slot": note["slot"],
                "note_id": note["note_id"],
                "contrast_pair": note["contrast_pair"],
                "broad_narrow_pair": note["broad_narrow_pair"],
                "niche_or_sparse_case": note["niche_or_sparse_case"],
            })
        })
        .collect::<Vec<_>>();
    assert_eq!(
        plan["notes"].as_array().expect("planned notes").as_slice(),
        projected_notes
    );
}

#[test]
fn tracked_crec_116_draft_uses_independent_overlapping_subjects() {
    let proposal = load_verified_note_proposal("reference_map/crec-115-note-proposal-v2.json")
        .expect("tracked CREC-115 proposal");
    let mut review = NoteReviewSession::new(&proposal).expect("create complete review");
    for note in &proposal.notes {
        review
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("approve tracked candidate");
    }
    let approved =
        ApprovedNoteSet::from_review(&proposal, &review).expect("derive expected approved set");
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v2.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    draft
        .validate(&approved)
        .expect("tracked draft is bound and structurally valid");
    let grouped_review =
        HierarchyReviewSession::new(&draft, &approved).expect("create grouped review");
    assert_eq!(
        grouped_review
            .decision_counts(&draft, &approved)
            .expect("count tracked review decisions")
            .2,
        73,
        "the tracked review is 64 note maps, 8 root branches, and one coverage check"
    );

    let memberships = draft
        .nodes
        .iter()
        .flat_map(|node| &node.memberships)
        .collect::<Vec<_>>();
    let memberships_per_note =
        memberships
            .iter()
            .fold(BTreeMap::<&str, usize>::new(), |mut counts, membership| {
                *counts.entry(membership.note_id.as_str()).or_default() += 1;
                counts
            });
    assert!(
        proposal
            .notes
            .iter()
            .any(|note| memberships_per_note[note.note_id.as_str()] >= 2),
        "the reference must contain at least one note with multiple weighted memberships"
    );
    assert!(
        proposal.notes.iter().any(|note| {
            memberships
                .iter()
                .filter(|membership| membership.note_id == note.note_id)
                .map(|membership| membership.strength)
                .collect::<std::collections::BTreeSet<_>>()
                .len()
                >= 2
        }),
        "the reference must exercise different membership strengths"
    );

    let all_strengths = memberships
        .iter()
        .map(|membership| membership.strength)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        all_strengths,
        [
            MembershipStrength::Incidental,
            MembershipStrength::Substantive,
            MembershipStrength::Central,
        ]
        .into_iter()
        .collect(),
        "the complete map must exercise the ordinal scale"
    );
    assert!(
        draft
            .nodes
            .iter()
            .filter(|node| node.is_leaf())
            .any(|leaf| {
                leaf.memberships
                    .iter()
                    .map(|membership| membership.strength)
                    .collect::<std::collections::BTreeSet<_>>()
                    == [MembershipStrength::Central].into_iter().collect()
            }),
        "an honestly sparse subject must not be padded with artificial weak memberships"
    );

    let history_books_note = "7d52bf12d1dba7ef59001b7d70189cd7139fd12b9e2972c6faa5b634d5166217";
    for subject_id in ["books-reading", "history"] {
        let subject = draft.node(subject_id).expect("independent subject");
        assert!(
            subject.memberships.iter().any(|membership| {
                membership.note_id == history_books_note
                    && membership.strength == MembershipStrength::Central
            }),
            "the note must independently map to {subject_id}"
        );
    }
    for obsolete_compound in [
        "books",
        "programming-storage",
        "markets",
        "visual-design",
        "music-rhythm",
        "activity",
        "family",
        "substances",
        "energy-climate",
        "travel-place",
    ] {
        assert!(
            draft.node(obsolete_compound).is_none(),
            "compound subject {obsolete_compound} must not remain"
        );
    }
}

#[test]
fn tracked_books_and_history_subjects_are_separate() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v2.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let books = draft.node("books-reading").expect("books subject");
    let history = draft.node("history").expect("history subject");

    assert_eq!(books.label, "Books and reading");
    assert_eq!(
        books.scope,
        "Choosing, reading, recommending, accessing, and discussing books."
    );
    assert_eq!(history.label, "History");
}

#[test]
fn approved_hierarchy_detects_changes_to_frozen_notes_and_subjects() {
    let frozen = frozen_hierarchy();

    let mut changed_note = frozen.clone();
    changed_note.notes[0].content.push_str(" tampered");
    let error = changed_note
        .validate()
        .expect_err("changing frozen note content must break its identity");
    assert!(error.to_string().contains("SHA-256"), "{error}");

    let mut changed_subject = frozen;
    changed_subject.nodes[0].label = "Changed after approval".to_owned();
    let error = changed_subject
        .validate()
        .expect_err("changing an approved subject must break its identity");
    assert!(error.to_string().contains("SHA-256"), "{error}");
}

#[test]
fn changed_note_evidence_invalidates_only_its_note_map() {
    let original_notes = approved_notes();
    let original_draft = hierarchy(&original_notes);
    let mut session = HierarchyReviewSession::new(&original_draft, &original_notes)
        .expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &original_draft, &original_notes);

    let mut revised_proposal = proposal();
    revised_proposal.notes[0].content = "Changed evidence for the same note ID".to_owned();
    let mut revised_note_session =
        NoteReviewSession::new(&revised_proposal).expect("create revised note session");
    for note in &revised_proposal.notes {
        revised_note_session
            .record(
                &revised_proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("approve revised evidence");
    }
    let revised_notes = ApprovedNoteSet::from_review(&revised_proposal, &revised_note_session)
        .expect("publish revised notes");
    let mut revised_draft = original_draft;
    revised_draft.approved_notes_sha256 = revised_notes.identity().expect("revised note identity");
    revised_draft
        .validate(&revised_notes)
        .expect("same tree is valid for revised note evidence");

    let changed_note_map = HierarchyReviewTarget::NoteMap {
        note_id: revised_notes.notes[0].note_id.clone(),
    };
    assert!(
        !session.is_approved(&revised_draft, &revised_notes, &changed_note_map),
        "approval of the old note text must not be reused for its complete map"
    );
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::NoteMap {
            note_id: revised_notes.notes[1].note_id.clone(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Branch {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Branch {
            node_id: "life".to_owned(),
        }
    ));
    assert!(
        session.focus_coverage_is_approved(&revised_draft, &revised_notes),
        "unchanged membership evidence preserves the final coverage decision"
    );
    assert!(
        !session.review_is_complete(&revised_draft, &revised_notes),
        "preserved branch decisions must not hide an invalidated note map"
    );
}

#[cfg(unix)]
#[test]
fn approved_artifact_publication_never_replaces_an_existing_directory_entry() {
    use std::os::unix::fs::symlink;

    let temp = tempfile::tempdir().expect("tempdir");
    let (proposal_path, _) = write_source_bound_proposal(temp.path());
    let approved_path = temp.path().join("approved.json");
    symlink("missing-original-artifact", &approved_path).expect("create dangling artifact link");
    let mut ui = ScriptedUi::new((0..64).map(|_| ApprovalTuiAction::Submit {
        outcome: ReviewOutcome::Approved,
        comment: String::new(),
    }));

    let error = run_note_review(
        &proposal_path,
        temp.path().join("session.json"),
        &approved_path,
        &mut ui,
    )
    .expect_err("create-once publication must not replace any directory entry");
    assert!(error.to_string().contains("already exists"), "{error}");
    assert!(fs::symlink_metadata(&approved_path)
        .expect("artifact link remains")
        .file_type()
        .is_symlink());
}
