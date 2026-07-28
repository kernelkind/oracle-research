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
use oracle_mvp::reference_tui::{ApprovalScreen, ApprovalTuiAction};
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
    approve_all_leaf_mappings(&mut focus_session, &draft, &approved);
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

fn approve_all_leaf_mappings_and_focus(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_leaf_mappings(session, hierarchy, approved);
    session
        .record_focus_coverage(hierarchy, approved, approved_hierarchy_decision())
        .expect("approve focus-concentration coverage");
}

fn approve_all_leaf_mappings(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    while !session.all_leaves_approved(hierarchy, approved) {
        let target = session
            .reviewable_targets(hierarchy, approved)
            .expect("list reviewable leaf items")
            .into_iter()
            .next()
            .expect("an unapproved leaf has a reviewable atomic item");
        let is_leaf_item = match &target {
            HierarchyReviewTarget::Membership { .. } => true,
            HierarchyReviewTarget::Subject { node_id } => {
                hierarchy.node(node_id).is_some_and(SubjectNode::is_leaf)
            }
            HierarchyReviewTarget::ParentChild { .. } => false,
        };
        assert!(
            is_leaf_item,
            "leaf approval helper reached non-leaf item {target:?}"
        );
        session
            .record(hierarchy, approved, target, approved_hierarchy_decision())
            .expect("approve atomic leaf item");
    }
}

fn approve_all_remaining_hierarchy_items(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    while !session.review_is_complete(hierarchy, approved) {
        let target = session
            .reviewable_targets(hierarchy, approved)
            .expect("list reviewable hierarchy items")
            .into_iter()
            .next()
            .expect("an incomplete hierarchy has a reviewable atomic item");
        session
            .record(hierarchy, approved, target, approved_hierarchy_decision())
            .expect("approve atomic hierarchy item");
    }
}

fn approve_complete_hierarchy(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_leaf_mappings_and_focus(session, hierarchy, approved);
    approve_all_remaining_hierarchy_items(session, hierarchy, approved);
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
fn hierarchy_validation_requires_every_leaf_to_demonstrate_all_membership_strengths() {
    let approved = approved_notes();
    let mut hierarchy = hierarchy(&approved);
    let software = hierarchy
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "software")
        .expect("software leaf");
    for membership in &mut software.memberships {
        if membership.strength == MembershipStrength::Incidental {
            membership.strength = MembershipStrength::Substantive;
        }
    }

    let error = hierarchy
        .validate(&approved)
        .expect_err("a reference leaf without every membership strength is incomplete");
    assert!(error.to_string().contains("software"), "{error}");
    assert!(error.to_string().contains("Incidental"), "{error}");
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
fn hierarchy_review_unlocks_parents_only_after_approved_children() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");

    let initial_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list initial reviewable items");
    assert_eq!(initial_targets.len(), 16);
    assert!(
        initial_targets.iter().all(|target| matches!(
            target,
            HierarchyReviewTarget::Membership { subject_id, .. } if subject_id == "software"
        )),
        "the first leaf's memberships are reviewed before later leaves"
    );
    let error = session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Subject {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: String::new(),
            },
        )
        .expect_err("an internal node cannot be judged before its children");
    assert!(
        error.to_string().contains("not currently reviewable"),
        "{error}"
    );

    approve_all_leaf_mappings(&mut session, &hierarchy, &approved);
    assert!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list gated items")
            .is_empty(),
        "parent review stays locked until focus coverage is approved"
    );
    session
        .record_focus_coverage(
            &hierarchy,
            &approved,
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: String::new(),
            },
        )
        .expect("approve focus coverage");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list first parent relationships"),
        vec![
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "software".to_owned(),
            },
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "hardware".to_owned(),
            },
        ]
    );
}

#[test]
fn hierarchy_review_groups_each_height_in_root_tree_order() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");

    assert!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list first reviewable items")
            .iter()
            .all(|target| matches!(
                target,
                HierarchyReviewTarget::Membership { subject_id, .. }
                    if subject_id == "software"
            )),
        "leaf memberships follow depth-first root and sibling order"
    );
    approve_all_leaf_mappings_and_focus(&mut session, &hierarchy, &approved);
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list first internal relationships"),
        vec![
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "software".to_owned(),
            },
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "hardware".to_owned(),
            },
        ],
        "parent-child relationships retain root and sibling order"
    );
}

#[test]
fn rejected_internal_edge_keeps_its_sibling_reviewable_but_blocks_the_parent_subject() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_leaf_mappings_and_focus(&mut session, &hierarchy, &approved);

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "software".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "Software should not be directly under Technology.".to_owned(),
            },
        )
        .expect("reject one internal relationship");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list sibling relationship after rejection"),
        vec![HierarchyReviewTarget::ParentChild {
            parent_id: "technology".to_owned(),
            child_id: "hardware".to_owned(),
        }],
        "one rejected relationship must not suppress its undecided sibling"
    );

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "hardware".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve the sibling relationship");
    let next_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("continue to independent parent");
    assert!(
        !next_targets.contains(&HierarchyReviewTarget::Subject {
            node_id: "technology".to_owned(),
        }),
        "a parent subject cannot be approved while one of its relationships is rejected"
    );
    assert_eq!(
        next_targets,
        vec![
            HierarchyReviewTarget::ParentChild {
                parent_id: "life".to_owned(),
                child_id: "food".to_owned(),
            },
            HierarchyReviewTarget::ParentChild {
                parent_id: "life".to_owned(),
                child_id: "outdoors".to_owned(),
            },
        ],
        "an independent parent remains reviewable"
    );
}

#[test]
fn changed_leaf_invalidates_only_that_leaf_and_its_ancestors() {
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

    let software_note_id = revised.node("software").expect("software leaf").memberships[0]
        .note_id
        .clone();
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Membership {
            subject_id: "software".to_owned(),
            note_id: software_note_id,
        }
    ));
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Subject {
            node_id: "software".to_owned(),
        }
    ));
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::ParentChild {
            parent_id: "technology".to_owned(),
            child_id: "software".to_owned(),
        }
    ));
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Subject {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Subject {
            node_id: "hardware".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Subject {
            node_id: "life".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::ParentChild {
            parent_id: "all-subjects".to_owned(),
            child_id: "technology".to_owned(),
        }
    ));
    assert!(
        !session.review_is_complete(&revised, &approved),
        "invalidated descendants make the hierarchy incomplete even though the root edge itself is unchanged"
    );
    assert!(
        !session.focus_coverage_is_approved(&revised, &approved),
        "changing a leaf mapping invalidates the focus-coverage decision"
    );
}

#[test]
fn parent_only_revision_preserves_the_approved_focus_coverage_gate() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_leaf_mappings_and_focus(&mut session, &hierarchy, &approved);

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
        session.focus_coverage_is_approved(&revised, &approved),
        "a parent-only edit does not change the reviewed leaf membership map"
    );
    assert_eq!(
        session
            .reviewable_targets(&revised, &approved)
            .expect("list first parent relationships"),
        vec![
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "software".to_owned(),
            },
            HierarchyReviewTarget::ParentChild {
                parent_id: "technology".to_owned(),
                child_id: "hardware".to_owned(),
            },
        ]
    );
}

#[test]
fn rejected_focus_coverage_blocks_parent_review_and_publication() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_leaf_mappings(&mut session, &hierarchy, &approved);
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
    let error = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect_err("rejected focus coverage prevents publication");
    assert!(
        error.to_string().contains("focus-concentration coverage"),
        "{error}"
    );
}

#[test]
fn hierarchy_publication_requires_each_current_hidden_root_edge() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_leaf_mappings_and_focus(&mut session, &hierarchy, &approved);
    loop {
        let target = session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list reviewable hierarchy items")
            .into_iter()
            .next()
            .expect("a parent item is reviewable before root choices");
        if matches!(
            &target,
            HierarchyReviewTarget::ParentChild { parent_id, .. }
                if parent_id == "all-subjects"
        ) {
            break;
        }
        session
            .record(&hierarchy, &approved, target, approved_hierarchy_decision())
            .expect("approve reviewable internal item");
    }
    let error = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect_err("the root choices remain unapproved");
    assert!(error.to_string().contains("relationships"), "{error}");

    let root_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list hidden-root relationships");
    assert_eq!(
        root_targets,
        vec![
            HierarchyReviewTarget::ParentChild {
                parent_id: "all-subjects".to_owned(),
                child_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::ParentChild {
                parent_id: "all-subjects".to_owned(),
                child_id: "life".to_owned(),
            },
        ],
        "the hidden root has relationship decisions but no subject decision"
    );
    for target in root_targets {
        session
            .record(&hierarchy, &approved, target, approved_hierarchy_decision())
            .expect("approve one hidden-root relationship");
    }
    let frozen = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect("publish approved hierarchy");
    assert_eq!(frozen.notes.len(), 64);
    assert_eq!(frozen.nodes.len(), 7);
}

#[test]
fn changing_the_hidden_root_definition_preserves_top_level_choice_approvals() {
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
    revised
        .validate(&approved)
        .expect("hidden-root definition may change structurally");

    for child_id in ["technology", "life"] {
        assert!(
            session.is_approved(
                &revised,
                &approved,
                &HierarchyReviewTarget::ParentChild {
                    parent_id: "all-subjects".to_owned(),
                    child_id: child_id.to_owned(),
                }
            ),
            "changing an unseen root definition must not invalidate {child_id}'s visible top-level choice"
        );
    }
    assert!(
        session.review_is_complete(&revised, &approved),
        "the hidden root has no subject decision of its own"
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
fn hierarchy_runner_approves_exactly_one_membership_per_action() {
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
        .expect("approve one membership, then pause"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(ui.screens.len(), 2);
    let first = &ui.screens[0];
    assert_eq!(first.title, "Membership · Software · Central");
    assert_eq!(
        first.scope,
        "Does this note express “Software” at Central strength?"
    );
    assert_eq!(first.approve_label, "Approve — yes");
    assert_eq!(first.reject_label, "Reject — no, explain");
    assert_eq!(
        first.evidence.len(),
        1,
        "one action must decide exactly one membership"
    );
    assert!(
        ui.screens[1].title.starts_with("Membership · Software · "),
        "the next membership in the same leaf follows: {:?}",
        ui.screens[1]
    );
}

#[test]
fn hierarchy_runner_reviews_the_leaf_subject_after_its_memberships() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let software_memberships = draft
        .node("software")
        .expect("software leaf")
        .memberships
        .len();
    let mut actions = (0..software_memberships)
        .map(|_| approve_action())
        .collect::<Vec<_>>();
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
        .expect("approve one leaf's memberships, then pause"),
        ReviewRunOutcome::Paused
    );
    let leaf = ui.screens.last().expect("leaf subject screen");
    assert_eq!(leaf.title, "Leaf subject · Software");
    assert_eq!(
        leaf.scope,
        "Should “Software” remain as a leaf navigation choice?"
    );
    assert_eq!(leaf.approve_label, "Approve — keep this leaf");
    assert_eq!(leaf.reject_label, "Reject — explain what should change");
}

#[test]
fn hierarchy_runner_reviews_each_parent_child_relationship_separately() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let membership_count = draft
        .nodes
        .iter()
        .map(|node| node.memberships.len())
        .sum::<usize>();
    let leaf_count = draft.nodes.iter().filter(|node| node.is_leaf()).count();
    let decisions_before_first_edge = membership_count + leaf_count + 1;
    let mut actions = (0..decisions_before_first_edge)
        .map(|_| approve_action())
        .collect::<Vec<_>>();
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
        .expect("reach first parent-child relationship"),
        ReviewRunOutcome::Paused
    );
    let relationship = ui.screens.last().expect("relationship screen");
    assert_eq!(relationship.title, "Relationship · Technology → Software");
    assert_eq!(
        relationship.scope,
        "Does “Software” belong directly under “Technology”?"
    );
    assert_eq!(
        relationship.approve_label,
        "Approve — keep this relationship"
    );
    assert_eq!(
        relationship.reject_label,
        "Reject — explain where it belongs"
    );
}

#[test]
fn hierarchy_runner_migrates_only_an_empty_schema_two_session() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    write_review_session_value(
        &session_path,
        &LegacyHierarchySessionFixture {
            schema_version: 2,
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
            temp.path().join("approved-hierarchy.json"),
            &mut ui,
        )
        .expect("migrate the empty bundled session"),
        ReviewRunOutcome::Paused
    );
    let migrated: serde_json::Value =
        serde_json::from_slice(&fs::read(&session_path).expect("read migrated session"))
            .expect("decode migrated session");
    assert_eq!(migrated["session"]["schema_version"], 3);
    assert_eq!(migrated["session"]["history"], serde_json::json!([]));
    assert_eq!(
        migrated["session"]["focus_coverage_history"],
        serde_json::json!([])
    );
}

#[test]
fn hierarchy_runner_refuses_nonempty_schema_two_bundled_state() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let cases = [
        (
            "node-history",
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
            "focus-history",
            LegacyHierarchySessionFixture {
                schema_version: 2,
                history: Vec::new(),
                focus_coverage_history: vec![LegacyFocusCoverageRecordFixture {
                    leaf_map_revision_sha256: "0".repeat(64),
                    decision: approved_hierarchy_decision(),
                }],
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
                .contains("old bundled hierarchy review contains decisions"),
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
fn hierarchy_runner_reviews_leaves_then_parents_then_hidden_root() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let membership_count = draft
        .nodes
        .iter()
        .map(|node| node.memberships.len())
        .sum::<usize>();
    let leaf_count = draft.nodes.iter().filter(|node| node.is_leaf()).count();
    let internal_edge_count = 4;
    let visible_parent_count = 2;
    let root_edge_count = 2;
    let decision_count = membership_count
        + leaf_count
        + 1
        + internal_edge_count
        + visible_parent_count
        + root_edge_count;
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
    let mut cursor = 0;
    for (node_id, label) in [
        ("software", "Software"),
        ("hardware", "Hardware"),
        ("food", "Food"),
        ("outdoors", "Outdoors"),
    ] {
        let membership_count = draft.node(node_id).expect("fixture leaf").memberships.len();
        assert!(
            ui.screens[cursor..cursor + membership_count]
                .iter()
                .all(|screen| screen
                    .title
                    .starts_with(&format!("Membership · {label} · "))),
            "every membership is decided separately before the leaf subject"
        );
        cursor += membership_count;
        assert_eq!(ui.screens[cursor].title, format!("Leaf subject · {label}"));
        cursor += 1;
    }
    assert_eq!(ui.screens[cursor].title, "Focus-concentration coverage");
    cursor += 1;
    assert_eq!(
        ui.screens[cursor..cursor + 3]
            .iter()
            .map(|screen| screen.title.as_str())
            .collect::<Vec<_>>(),
        vec![
            "Relationship · Technology → Software",
            "Relationship · Technology → Hardware",
            "Parent subject · Technology",
        ]
    );
    cursor += 3;
    assert_eq!(
        ui.screens[cursor..cursor + 3]
            .iter()
            .map(|screen| screen.title.as_str())
            .collect::<Vec<_>>(),
        vec![
            "Relationship · Everyday life → Food",
            "Relationship · Everyday life → Outdoors",
            "Parent subject · Everyday life",
        ]
    );
    cursor += 3;
    assert_eq!(
        ui.screens[cursor..]
            .iter()
            .map(|screen| screen.title.as_str())
            .collect::<Vec<_>>(),
        vec![
            "Top-level choice · Technology",
            "Top-level choice · Everyday life",
        ],
        "the hidden root has separate edge decisions and no subject decision"
    );
    let life_subject = ui
        .screens
        .iter()
        .find(|screen| screen.title == "Parent subject · Everyday life")
        .expect("everyday-life parent subject screen");
    assert_eq!(life_subject.evidence.len(), 1);
    assert!(life_subject.evidence[0]
        .body
        .contains("Approved direct children:\n\n• Food\n  Notes about Food"));
    assert!(life_subject.evidence[0]
        .body
        .contains("• Outdoors\n  Notes about Outdoors"));
    assert!(approved_path.is_file());
}

#[test]
fn hierarchy_runner_audits_focus_coverage_after_leaf_weights_and_before_parents() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let leaf_count = draft.nodes.iter().filter(|node| node.is_leaf()).count();
    let membership_count = draft
        .nodes
        .iter()
        .map(|node| node.memberships.len())
        .sum::<usize>();
    let leaf_decision_count = membership_count + leaf_count;
    let mut actions = (0..leaf_decision_count)
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
        ui.screens[leaf_decision_count].title,
        "Focus-concentration coverage"
    );
    assert_eq!(
        ui.screens[leaf_decision_count].scope,
        "Is any part of the focus-concentration spectrum missing from this 64-note reference set?"
    );
    let guidance = ui.screens[leaf_decision_count]
        .guidance
        .as_ref()
        .expect("focus coverage explains the membership scale");
    assert_eq!(guidance.title, "Membership scale");
    assert!(guidance.body.contains("Central"));
    assert!(guidance.body.contains("Substantive"));
    assert!(guidance.body.contains("Incidental"));
    let rendered_inventory = ui.screens[leaf_decision_count]
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
    let coverage_panels = ui.screens[leaf_decision_count]
        .evidence
        .iter()
        .map(|evidence| evidence.title.as_str())
        .collect::<Vec<_>>();
    assert!(coverage_panels.contains(&"1 membership · Central"));
    assert!(coverage_panels.contains(&"1 membership · Substantive"));
    assert!(coverage_panels.contains(&"1 membership · Incidental"));
    assert!(coverage_panels.contains(&"2 memberships · Central + Substantive"));
}

#[test]
fn leaf_review_shows_each_notes_current_membership_strength() {
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
        .expect("open first leaf"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(ui.screens[0].title, "Membership · Software · Central");
    assert_eq!(ui.screens[0].evidence.len(), 1);
    assert!(
        ui.screens[0].evidence[0]
            .annotation
            .contains("This action decides only this note’s Central membership."),
        "the screen must identify the one membership strength being decided"
    );
}

#[test]
fn leaf_review_keeps_note_text_primary_and_memberships_secondary() {
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
        .expect("open first leaf"),
        ReviewRunOutcome::Paused
    );
    let evidence = &ui.screens[0].evidence[0];
    assert_eq!(evidence.title, "Candidate note");
    assert!(evidence.body.starts_with("Real diagnostic note number"));
    assert!(!evidence.body.contains("Complete proposed map:"));
    assert!(!evidence.body.contains("\nNote:\n"));
    assert!(evidence.annotation.starts_with("Subject: Software"));
}

#[test]
fn leaf_review_states_the_exact_decision_and_only_current_membership() {
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
        .expect("open first leaf"),
        ReviewRunOutcome::Paused
    );
    let screen = &ui.screens[0];
    assert_eq!(
        screen.scope,
        "Does this note express “Software” at Central strength?"
    );
    assert_eq!(screen.approve_label, "Approve — yes");
    assert_eq!(screen.reject_label, "Reject — no, explain");
    let guidance = screen
        .guidance
        .as_ref()
        .expect("leaf review explains the membership scale");
    assert_eq!(guidance.title, "Membership scale");
    assert_eq!(
        guidance.body,
        "Central: the subject is one of the note’s main points.\n\n\
         Substantive: the subject materially matters to the note, but is not a main point.\n\n\
         Incidental: the subject appears only as a minor or supporting detail.\n\n\
         These are ordered categories, not percentages."
    );
    assert_eq!(screen.evidence.len(), 1);
    assert!(screen.evidence[0]
        .annotation
        .starts_with("Subject: Software"));
    assert!(
        !screen.evidence[0].annotation.contains("Food"),
        "memberships reviewed on other leaf screens are not part of this atomic decision"
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
fn tracked_crec_116_draft_is_bound_and_preserves_weighted_multi_membership() {
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

    for leaf in draft.nodes.iter().filter(|node| node.is_leaf()) {
        let strengths = leaf
            .memberships
            .iter()
            .map(|membership| membership.strength)
            .collect::<std::collections::BTreeSet<_>>();
        assert_eq!(
            strengths,
            [
                MembershipStrength::Incidental,
                MembershipStrength::Substantive,
                MembershipStrength::Central,
            ]
            .into_iter()
            .collect(),
            "leaf {} must demonstrate every membership strength",
            leaf.node_id
        );
    }

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
}

#[test]
fn tracked_books_subject_uses_concrete_navigation_language() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v2.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let books = draft.node("books").expect("books subject");

    assert_eq!(books.label, "Books, reading, and history");
    assert_eq!(
        books.scope,
        "Books and reading, historical knowledge, and the preservation and accessibility of written works."
    );
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
fn hierarchy_approvals_invalidate_only_atomic_items_derived_from_changed_note_evidence() {
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

    let changed_membership = HierarchyReviewTarget::Membership {
        subject_id: "software".to_owned(),
        note_id: revised_notes.notes[0].note_id.clone(),
    };
    assert!(
        !session.is_approved(&revised_draft, &revised_notes, &changed_membership),
        "approval of the old note text was silently reused for its membership"
    );
    assert!(!session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Subject {
            node_id: "software".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Subject {
            node_id: "hardware".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::ParentChild {
            parent_id: "technology".to_owned(),
            child_id: "software".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Subject {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::ParentChild {
            parent_id: "all-subjects".to_owned(),
            child_id: "technology".to_owned(),
        }
    ));
    assert!(
        !session.focus_coverage_is_approved(&revised_draft, &revised_notes),
        "the focus review is bound to the complete leaf membership map"
    );
    assert!(
        !session.review_is_complete(&revised_draft, &revised_notes),
        "preserved parent and edge decisions must not hide an invalidated descendant"
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
