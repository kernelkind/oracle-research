use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::fs;
use std::io;

use oracle_mvp::reference_map::{
    ApprovedHierarchy, ApprovedNoteSet, BroadNarrowRole, HierarchyDraft, HierarchyReviewDecision,
    HierarchyReviewSession, HierarchyReviewTarget, LeafMembership, MembershipStrength,
    NoteProposal, NoteReviewDecision, NoteReviewSession, PairMembership, ProposedNote,
    ReferenceNavigation, ReviewOutcome, SelectionSource, SubjectNode, REFERENCE_NOTE_COUNT,
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
    let retained_slots = (1_u8..=40)
        .chain([42, 44, 46, 48, 52, 54, 57, 60])
        .collect::<BTreeSet<_>>();
    NoteProposal {
        schema_version: 3,
        proposal_id: "crec-115-selection-v2".to_owned(),
        source: SelectionSource {
            sample_path: "target/crec-113-formal-v1/sample/sample.jsonl".to_owned(),
            sample_sha256: "8edb8a51246201100e6ba7cf7bf1bbf9cd501881d7c70b8a9cfc7a380d1b168e"
                .to_owned(),
            split: "learning".to_owned(),
        },
        notes: (0..64)
            .map(proposed_note)
            .filter(|note| retained_slots.contains(&note.slot))
            .collect(),
    }
}

#[test]
fn stratified_reference_proposal_accepts_sparse_source_slots() {
    proposal()
        .validate()
        .expect("the 48-note subset preserves stable source slots");
}

#[test]
fn subject_nodes_serialize_as_titles_relationships_and_memberships_only() {
    let approved = approved_notes();
    let draft = hierarchy(&approved);
    assert_eq!(
        draft.schema_version, 2,
        "removing a serialized subject field requires a new hierarchy schema"
    );
    let encoded = serde_json::to_value(&draft).expect("encode hierarchy draft");
    let nodes = encoded["nodes"].as_array().expect("encoded subject nodes");

    assert!(
        nodes.iter().all(|node| node.get("scope").is_none()),
        "subject descriptions must not exist in serialized hierarchy data"
    );
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
    assert_eq!(session.approved_count(&original), REFERENCE_NOTE_COUNT);

    let mut revised = original.clone();
    revised.proposal_id = "crec-115-selection-v2".to_owned();
    revised.notes[7].note_id = format!("{:064x}", 99_999);
    revised.notes[7].content = "A manually selected replacement note".to_owned();
    revised.validate().expect("replacement preserves quotas");

    session
        .reconcile(&revised)
        .expect("reconcile revised proposal");
    assert_eq!(session.approved_count(&revised), REFERENCE_NOTE_COUNT - 1);
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
    approve_all_parents(&mut focus_session, &draft, &approved);
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
fn approved_set_requires_all_current_candidates_to_be_approved() {
    let proposal = proposal();
    let last_slot = proposal.notes.last().expect("last candidate").slot;
    let mut session = NoteReviewSession::new(&proposal).expect("create session");
    for note in &proposal.notes {
        session
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: if note.slot == last_slot {
                        ReviewOutcome::Rejected
                    } else {
                        ReviewOutcome::Approved
                    },
                    comment: if note.slot == last_slot {
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
    assert!(
        error.to_string().contains(&format!(
            "{} of {REFERENCE_NOTE_COUNT}",
            REFERENCE_NOTE_COUNT - 1
        )),
        "{error}"
    );

    session
        .record(
            &proposal,
            last_slot,
            NoteReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: "Approved after reconsideration.".to_owned(),
            },
        )
        .expect("replace the current decision");
    let approved = ApprovedNoteSet::from_review(&proposal, &session)
        .expect("all current candidates are approved");
    assert_eq!(approved.notes.len(), REFERENCE_NOTE_COUNT);
    assert_eq!(
        approved
            .notes
            .iter()
            .map(|note| (note.slot, note.note_id.clone()))
            .collect::<BTreeMap<_, _>>()
            .len(),
        REFERENCE_NOTE_COUNT
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
        schema_version: 2,
        draft_id: "crec-116-reference-v1".to_owned(),
        approved_notes_sha256: approved.identity().expect("approved notes identity"),
        root_node_id: "all-subjects".to_owned(),
        nodes: vec![
            SubjectNode {
                node_id: "all-subjects".to_owned(),
                label: "All subjects".to_owned(),
                children: vec!["technology".to_owned(), "life".to_owned()],
                memberships: vec![],
            },
            SubjectNode {
                node_id: "technology".to_owned(),
                label: "Technology".to_owned(),
                children: vec!["software".to_owned(), "hardware".to_owned()],
                memberships: vec![],
            },
            SubjectNode {
                node_id: "life".to_owned(),
                label: "Everyday life".to_owned(),
                children: vec!["food".to_owned(), "outdoors".to_owned()],
                memberships: vec![],
            },
            leaf("software", "Software", 1..=12),
            leaf("hardware", "Hardware", 13..=24),
            leaf("food", "Food", 25..=36),
            leaf("outdoors", "Outdoors", 37..=48),
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
                note_id: approved.notes[12].note_id.clone(),
                strength: MembershipStrength::Central,
            },
        ]);
    draft
}

fn approve_all_note_maps_parents_and_focus(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_note_maps(session, hierarchy, approved);
    approve_all_parents(session, hierarchy, approved);
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

fn approve_all_parents(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    while !session.all_parents_approved(hierarchy, approved) {
        let target = session
            .reviewable_targets(hierarchy, approved)
            .expect("list reviewable hierarchy parents")
            .into_iter()
            .next()
            .expect("an incomplete hierarchy has a reviewable parent");
        assert!(matches!(target, HierarchyReviewTarget::Parent { .. }));
        session
            .record(hierarchy, approved, target, approved_hierarchy_decision())
            .expect("approve hierarchy parent");
    }
}

fn approve_complete_hierarchy(
    session: &mut HierarchyReviewSession,
    hierarchy: &HierarchyDraft,
    approved: &ApprovedNoteSet,
) {
    approve_all_note_maps_parents_and_focus(session, hierarchy, approved);
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
    let diffuse_note_id = approved.notes[12].note_id.as_str();
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
fn hierarchy_review_unlocks_parents_only_after_all_note_maps_are_approved() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");

    let initial_targets = session
        .reviewable_targets(&hierarchy, &approved)
        .expect("list initial reviewable items");
    assert_eq!(initial_targets.len(), REFERENCE_NOTE_COUNT);
    assert_eq!(
        initial_targets.first(),
        Some(&HierarchyReviewTarget::NoteMap {
            note_id: approved.notes[0].note_id.clone(),
        })
    );
    assert_eq!(
        initial_targets.last(),
        Some(&HierarchyReviewTarget::NoteMap {
            note_id: approved.notes[REFERENCE_NOTE_COUNT - 1].note_id.clone(),
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
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Approved,
                comment: String::new(),
            },
        )
        .expect_err("a parent cannot be judged before every note map");
    assert!(
        error.to_string().contains("not currently reviewable"),
        "{error}"
    );

    approve_all_note_maps(&mut session, &hierarchy, &approved);
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list parents"),
        vec![
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
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
        .expect_err("coverage remains locked until every parent is approved");
    assert!(
        error
            .to_string()
            .contains("every note map and hierarchy parent"),
        "{error}"
    );
}

#[test]
fn hierarchy_review_orders_note_maps_then_parents() {
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
            .expect("list hierarchy parents"),
        vec![
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
            },
        ],
        "parent reviews proceed from the deepest groupings to the hidden root"
    );
}

#[test]
fn rejected_parent_keeps_other_parents_reviewable_but_blocks_coverage() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_note_maps(&mut session, &hierarchy, &approved);

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
            },
            HierarchyReviewDecision {
                outcome: ReviewOutcome::Rejected,
                comment: "Item 2 does not belong under this parent.".to_owned(),
            },
        )
        .expect("reject one parent");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list other parents after rejection"),
        vec![
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
        ],
        "one rejected parent must not suppress undecided parents"
    );

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve the next parent");
    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve the final parent");
    assert!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list targets after every parent decision")
            .is_empty(),
        "a rejected parent blocks the final coverage check"
    );
    let error = session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect_err("coverage cannot approve a rejected parent");
    assert!(
        error
            .to_string()
            .contains("every note map and hierarchy parent"),
        "{error}"
    );
}

#[test]
fn rejected_note_map_keeps_other_notes_reviewable_but_blocks_parents() {
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
    assert_eq!(remaining.len(), REFERENCE_NOTE_COUNT - 1);
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
        "a rejected note map blocks parent review after the remaining notes are gathered"
    );
    assert_eq!(
        session
            .decision_counts(&hierarchy, &approved)
            .expect("count grouped decisions"),
        (REFERENCE_NOTE_COUNT - 1, 1, REFERENCE_NOTE_COUNT + 4,)
    );
}

#[test]
fn changed_leaf_identifier_preserves_note_assignments_but_reopens_its_parent() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_complete_hierarchy(&mut session, &hierarchy, &approved);

    let mut revised = hierarchy.clone();
    revised.draft_id = "crec-116-reference-v2".to_owned();
    let software = revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "software")
        .expect("software leaf");
    software.node_id = "software-development".to_owned();
    let technology = revised
        .nodes
        .iter_mut()
        .find(|node| node.node_id == "technology")
        .expect("technology parent");
    let software_child = technology
        .children
        .iter_mut()
        .find(|child| child.as_str() == "software")
        .expect("software child");
    *software_child = "software-development".to_owned();
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
            "a hidden node identifier does not change displayed subject assignments"
        );
    }
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "all-subjects".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "life".to_owned(),
        }
    ));
    assert!(
        session.focus_coverage_is_approved(&revised, &approved),
        "a hidden node identifier does not change the displayed membership summary"
    );
    let next_targets = session
        .reviewable_targets(&revised, &approved)
        .expect("list reopened parent");
    assert_eq!(
        next_targets,
        vec![HierarchyReviewTarget::Parent {
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
fn changed_membership_invalidates_its_note_map_and_focus_but_not_parents() {
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
    for node_id in ["all-subjects", "technology", "life"] {
        assert!(session.is_approved(
            &revised,
            &approved,
            &HierarchyReviewTarget::Parent {
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
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "all-subjects".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(!session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
            node_id: "life".to_owned(),
        }
    ));
}

#[test]
fn changed_parent_label_reopens_its_own_and_its_parent_review() {
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
        .label = "Computing technology".to_owned();
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
            .expect("list reopened parent reviews"),
        vec![
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
            },
        ]
    );
    assert!(session.is_approved(
        &revised,
        &approved,
        &HierarchyReviewTarget::Parent {
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
    approve_all_parents(&mut session, &hierarchy, &approved);
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
fn hierarchy_publication_requires_each_current_parent() {
    let approved = approved_notes();
    let hierarchy = hierarchy(&approved);
    let mut session =
        HierarchyReviewSession::new(&hierarchy, &approved).expect("create hierarchy session");
    approve_all_note_maps(&mut session, &hierarchy, &approved);
    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "all-subjects".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve top-level parent");
    assert_eq!(
        session
            .reviewable_targets(&hierarchy, &approved)
            .expect("list remaining parents"),
        vec![
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
        ]
    );
    let error = session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect_err("coverage cannot bypass an unapproved parent");
    assert!(error.to_string().contains("hierarchy parent"), "{error}");

    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "technology".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve technology parent");
    session
        .record(
            &hierarchy,
            &approved,
            HierarchyReviewTarget::Parent {
                node_id: "life".to_owned(),
            },
            approved_hierarchy_decision(),
        )
        .expect("approve final parent");
    session
        .record_focus_coverage(&hierarchy, &approved, approved_hierarchy_decision())
        .expect("approve final coverage check");
    let frozen = ApprovedHierarchy::from_review(&hierarchy, &approved, &session)
        .expect("publish approved hierarchy");
    assert_eq!(frozen.notes.len(), REFERENCE_NOTE_COUNT);
    assert_eq!(frozen.nodes.len(), 7);
}

#[test]
fn changing_hidden_root_order_reopens_only_the_top_level_review() {
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
    root.children.reverse();
    revised
        .validate(&approved)
        .expect("hidden-root definition may change structurally");

    for parent_id in ["technology", "life"] {
        assert!(
            session.is_approved(
                &revised,
                &approved,
                &HierarchyReviewTarget::Parent {
                    node_id: parent_id.to_owned(),
                }
            ),
            "changing the top-level order must not invalidate {parent_id}'s child list"
        );
    }
    assert_eq!(
        session
            .reviewable_targets(&revised, &approved)
            .expect("list reopened top-level review"),
        vec![HierarchyReviewTarget::Parent {
            node_id: "all-subjects".to_owned(),
        }]
    );
    assert!(!session.review_is_complete(&revised, &approved));
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
        hierarchy.notes[12].note_id,
        "the added central multi-membership note leads the leaf"
    );
    let hardware = hierarchy
        .leaf_notes("hardware")
        .expect("resolve ordered hardware notes");
    assert!(
        hardware
            .iter()
            .any(|note| note.note_id == hierarchy.notes[12].note_id),
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

#[derive(Clone, serde::Deserialize, serde::Serialize)]
struct AtomicHierarchyRecordFixture {
    target: HierarchyReviewTarget,
    target_revision_sha256: String,
    decision: HierarchyReviewDecision,
}

#[derive(serde::Serialize)]
struct GroupedHierarchySessionFixture {
    schema_version: u32,
    history: Vec<AtomicHierarchyRecordFixture>,
    focus_coverage_history: Vec<LegacyFocusCoverageRecordFixture>,
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
fn hierarchy_runner_opens_a_deepest_parent_after_all_note_maps() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut actions = (0..REFERENCE_NOTE_COUNT)
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
        .expect("approve every note map, then pause"),
        ReviewRunOutcome::Paused
    );
    let parent = ui.screens.last().expect("first bottom-up parent screen");
    assert_eq!(parent.title, "Technology");
    assert_eq!(parent.scope, "Are these immediate child subjects correct?");
    assert_eq!(parent.approve_label, "No problems");
    assert_eq!(parent.reject_label, "Describe a problem");
    assert_eq!(parent.evidence[0].body, "[1] Software\n[2] Hardware");
}

#[test]
fn hierarchy_runner_reviews_one_parent_level_at_a_time() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);
    let mut actions = (0..REFERENCE_NOTE_COUNT + 1)
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
        .expect("approve the first bottom-up parent, then pause"),
        ReviewRunOutcome::Paused
    );
    let technology = &ui.screens[REFERENCE_NOTE_COUNT];
    assert_eq!(
        technology.heading,
        "Hierarchy review · Parent 1 of 3 · 48 note maps approved"
    );
    assert_eq!(technology.title, "Technology");
    assert_eq!(
        technology.scope,
        "Are these immediate child subjects correct?"
    );
    assert_eq!(technology.approve_label, "No problems");
    assert_eq!(technology.reject_label, "Describe a problem");
    assert_eq!(
        technology.rejection_help,
        "Examples:\n\
         [2] Title is unclear.\n\
         [3] Does not belong under this parent.\n\
         Missing \"Expected subject\"."
    );
    assert_eq!(technology.evidence.len(), 1);
    assert_eq!(technology.evidence[0].title, "Children · 2 subjects");
    assert_eq!(
        technology.evidence[0].annotation,
        "Approving accepts these titles, their order, and their direct placement under this parent.\n\
         Use the numbers when describing a problem."
    );
    assert!(technology
        .guidance
        .as_ref()
        .expect("parent decision is explained")
        .body
        .contains("Only this one level is being reviewed."));
    assert_eq!(technology.evidence[0].body, "[1] Software\n[2] Hardware");
    let everyday_life = &ui.screens[REFERENCE_NOTE_COUNT + 1];
    assert_eq!(
        everyday_life.title, "Everyday life",
        "one parent approval advances to the next internal parent"
    );
    assert_eq!(everyday_life.evidence[0].body, "[1] Food\n[2] Outdoors");
}

#[test]
fn hierarchy_runner_migrates_empty_prior_sessions_to_schema_five() {
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
        assert_eq!(migrated["session"]["schema_version"], 5);
        assert_eq!(migrated["session"]["history"], serde_json::json!([]));
        assert_eq!(
            migrated["session"]["focus_coverage_history"],
            serde_json::json!([])
        );
    }
}

#[test]
fn hierarchy_runner_migrates_schema_four_note_maps_without_repeating_them() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let mut initial_actions = (0..REFERENCE_NOTE_COUNT)
        .map(|_| approve_action())
        .collect::<Vec<_>>();
    initial_actions.push(ApprovalTuiAction::Pause);
    let mut initial_ui = ScriptedUi::new(initial_actions);
    run_hierarchy_review(
        &notes_path,
        &draft_path,
        &session_path,
        temp.path().join("unused-approved-hierarchy.json"),
        &mut initial_ui,
    )
    .expect("record all note-map approvals");

    let envelope: serde_json::Value =
        serde_json::from_slice(&fs::read(&session_path).expect("read schema-five session"))
            .expect("decode schema-five session");
    let prior_history: Vec<AtomicHierarchyRecordFixture> =
        serde_json::from_value(envelope["session"]["history"].clone())
            .expect("decode schema-five note-map history");
    write_review_session_value(
        &session_path,
        &GroupedHierarchySessionFixture {
            schema_version: 4,
            history: prior_history.clone(),
            focus_coverage_history: Vec::new(),
        },
    );

    let mut resumed_ui = ScriptedUi::new([ApprovalTuiAction::Pause]);
    assert_eq!(
        run_hierarchy_review(
            &notes_path,
            &draft_path,
            &session_path,
            temp.path().join("approved-hierarchy.json"),
            &mut resumed_ui,
        )
        .expect("migrate note-only schema-four session"),
        ReviewRunOutcome::Paused
    );
    assert_eq!(resumed_ui.screens.len(), 1);
    assert_eq!(resumed_ui.screens[0].title, "Technology");

    let migrated: serde_json::Value =
        serde_json::from_slice(&fs::read(&session_path).expect("read migrated session"))
            .expect("decode migrated session");
    assert_eq!(migrated["session"]["schema_version"], 5);
    assert_eq!(
        migrated["session"]["history"],
        serde_json::to_value(prior_history).expect("encode prior history")
    );
}

#[test]
fn hierarchy_runner_refuses_schema_four_branch_approvals() {
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
        &GroupedHierarchySessionFixture {
            schema_version: 4,
            history: vec![AtomicHierarchyRecordFixture {
                target: HierarchyReviewTarget::Branch {
                    node_id: "technology".to_owned(),
                },
                target_revision_sha256: "0".repeat(64),
                decision: approved_hierarchy_decision(),
            }],
            focus_coverage_history: Vec::new(),
        },
    );

    let mut ui = ScriptedUi::new([]);
    let error = run_hierarchy_review(
        &notes_path,
        &draft_path,
        &session_path,
        temp.path().join("approved-hierarchy.json"),
        &mut ui,
    )
    .expect_err("a whole-branch approval cannot become a parent approval");
    assert!(
        error
            .to_string()
            .contains("cannot be reinterpreted as parent reviews"),
        "{error}"
    );
    assert!(ui.screens.is_empty());
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
                .contains("cannot be reinterpreted as note-map and parent reviews"),
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
        "Is there a concrete reason this note should not be included in the 48-note reference set?"
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
fn sparse_source_slot_uses_its_review_position_in_the_candidate_counter() {
    let temp = tempfile::tempdir().expect("tempdir");
    let (proposal_path, _) = write_source_bound_proposal(temp.path());
    let mut actions = (0..40).map(|_| approve_action()).collect::<Vec<_>>();
    actions.push(ApprovalTuiAction::Pause);
    let mut ui = ScriptedUi::new(actions);

    assert_eq!(
        run_note_review(
            &proposal_path,
            temp.path().join("session.json"),
            temp.path().join("approved.json"),
            &mut ui,
        )
        .expect("reach the first sparse source slot"),
        ReviewRunOutcome::Paused
    );
    let screen = ui.screens.last().expect("sparse-slot review screen");
    assert_eq!(screen.title, "Slot 42");
    assert_eq!(
        screen.heading,
        "Candidate 41 of 48 · 40 approved · 0 rejected"
    );
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
fn hierarchy_runner_reviews_each_note_then_each_parent_then_coverage() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let parent_count = draft
        .nodes
        .iter()
        .filter(|node| !node.children.is_empty())
        .count();
    let decision_count = notes.notes.len() + parent_count + 1;
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

    for (note, screen) in notes.notes.iter().zip(&ui.screens[..REFERENCE_NOTE_COUNT]) {
        assert_eq!(screen.title, format!("Note map · Slot {:02}", note.slot));
        assert!(
            screen.evidence[0]
                .body
                .contains(&format!("Real diagnostic note number {}", note.slot - 1)),
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
        ui.screens[REFERENCE_NOTE_COUNT..REFERENCE_NOTE_COUNT + 3]
            .iter()
            .map(|screen| screen.title.as_str())
            .collect::<Vec<_>>(),
        vec!["Technology", "Everyday life", "Top-level subjects"],
        "each internal parent is loaded bottom-up"
    );
    assert_eq!(ui.screens[REFERENCE_NOTE_COUNT + 3].title, "Focus coverage");
    assert!(
        ui.screens[..REFERENCE_NOTE_COUNT]
            .iter()
            .all(|screen| screen.heading.contains("52 total")),
        "note-map review retains the complete interaction count"
    );
    assert_eq!(
        ui.screens[REFERENCE_NOTE_COUNT].heading,
        "Hierarchy review · Parent 1 of 3 · 48 note maps approved"
    );
    assert_eq!(
        ui.screens[REFERENCE_NOTE_COUNT + 1].heading,
        "Hierarchy review · Parent 2 of 3 · 48 note maps approved"
    );
    assert_eq!(
        ui.screens[REFERENCE_NOTE_COUNT + 2].heading,
        "Hierarchy review · Parent 3 of 3 · 48 note maps approved"
    );
    assert_eq!(
        ui.screens[REFERENCE_NOTE_COUNT + 2].evidence[0].body,
        "[1] Technology\n[2] Everyday life",
        "the top-level choices are reviewed only after their child structures"
    );
    assert!(approved_path.is_file());
}

#[test]
fn hierarchy_runner_audits_focus_coverage_after_note_maps_and_parents() {
    let temp = tempfile::tempdir().expect("tempdir");
    let notes = approved_notes();
    let draft = hierarchy(&notes);
    let notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("hierarchy-draft.json");
    let session_path = temp.path().join("hierarchy-session.json");
    let approved_path = temp.path().join("approved-hierarchy.json");
    write_json(&notes_path, &notes);
    write_json(&draft_path, &draft);

    let decisions_before_coverage = REFERENCE_NOTE_COUNT + 3;
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
        "Focus coverage"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].scope,
        "Do the 48 note maps include both narrow-focus and multi-focus notes?"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].approve_label,
        "Yes — both kinds are represented"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].reject_label,
        "No — describe what is missing"
    );
    let guidance = ui.screens[decisions_before_coverage]
        .guidance
        .as_ref()
        .expect("focus coverage explains its decision");
    assert_eq!(guidance.title, "Coverage check");
    assert!(guidance.body.contains("Narrow-focus"));
    assert!(guidance.body.contains("Multi-focus"));
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
        "the reviewer sees one summary instead of switching panels"
    );
    assert_eq!(
        ui.screens[decisions_before_coverage].evidence[0].title,
        "Coverage summary"
    );
    assert!(rendered_inventory.contains("Narrow-focus notes"));
    assert!(rendered_inventory.contains("Multi-focus notes"));
    assert!(rendered_inventory.contains("Example · Slot"));
    assert!(
        rendered_inventory.matches("Example · Slot").count() <= 6,
        "the summary uses a few examples instead of repeating all 48 maps"
    );
    assert!(!rendered_inventory.contains("ordinal signature"));
    assert!(!rendered_inventory.contains("membership ·"));
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
fn tracked_crec_116_proposal_is_complete_and_source_bound() {
    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
    assert_eq!(proposal.notes.len(), REFERENCE_NOTE_COUNT);
    assert_eq!(
        proposal
            .notes
            .iter()
            .map(|note| note.note_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        REFERENCE_NOTE_COUNT
    );
}

#[test]
fn tracked_crec_116_revision_uses_the_stratified_48_candidate_set() {
    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
    assert_eq!(
        proposal
            .notes
            .iter()
            .map(|note| note.slot)
            .collect::<Vec<_>>(),
        vec![
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
            25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36, 38, 39, 43, 45, 46, 48, 52, 53, 54, 55, 56,
            57, 60,
        ]
    );

    let prior: NoteProposal = serde_json::from_slice(
        &fs::read("reference_map/crec-115-note-proposal-v2.json")
            .expect("read prior 64-note proposal"),
    )
    .expect("decode prior proposal");
    for slot in 1..=33 {
        assert_eq!(
            proposal.note(slot),
            prior.note(slot),
            "existing review evidence changed in slot {slot}"
        );
    }
}

#[test]
fn tracked_crec_116_plan_matches_the_source_bound_proposal() {
    let plan: serde_json::Value = serde_json::from_slice(
        &fs::read("reference_map/crec-116-note-metadata-v3.json").expect("read selection plan"),
    )
    .expect("decode selection plan");
    let proposal: serde_json::Value = serde_json::from_slice(
        &fs::read("reference_map/crec-116-note-proposal-v3.json").expect("read note proposal"),
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
    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
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
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
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
        "the tracked review is 48 note maps, 24 internal parents, and one coverage check"
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

fn tracked_memberships_for_slot(
    proposal: &NoteProposal,
    draft: &HierarchyDraft,
    slot: u8,
) -> BTreeSet<(String, MembershipStrength)> {
    let note_id = &proposal.note(slot).expect("tracked note slot").note_id;
    draft
        .nodes
        .iter()
        .filter(|node| node.is_leaf())
        .flat_map(|node| {
            node.memberships
                .iter()
                .filter(move |membership| &membership.note_id == note_id)
                .map(move |membership| (node.label.clone(), membership.strength))
        })
        .collect()
}

fn tracked_maps_sha256(proposal: &NoteProposal, draft: &HierarchyDraft, slots: &[u8]) -> String {
    let mut snapshot = String::new();
    for slot in slots {
        for (label, strength) in tracked_memberships_for_slot(proposal, draft, *slot) {
            let strength = match strength {
                MembershipStrength::Incidental => "incidental",
                MembershipStrength::Substantive => "substantive",
                MembershipStrength::Central => "central",
            };
            snapshot.push_str(&format!("{slot}\t{label}\t{strength}\n"));
        }
    }
    format!("{:x}", Sha256::digest(snapshot.as_bytes()))
}

#[test]
fn tracked_crec_116_correction_pass_preserves_or_explicitly_revises_note_maps() {
    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let expected = |memberships: &[(&str, MembershipStrength)]| {
        memberships
            .iter()
            .map(|(label, strength)| ((*label).to_owned(), *strength))
            .collect::<BTreeSet<_>>()
    };

    let expected_maps = [
        (
            5,
            expected(&[(
                "Coffee roasting and personal taste",
                MembershipStrength::Central,
            )]),
        ),
        (
            2,
            expected(&[
                (
                    "Cryptographic security comparison",
                    MembershipStrength::Substantive,
                ),
                (
                    "Software signing and verification",
                    MembershipStrength::Central,
                ),
                (
                    "Using Nostr keys outside messaging",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            3,
            expected(&[
                (
                    "Digitizing and organizing personal notes",
                    MembershipStrength::Central,
                ),
                (
                    "PowerShell file-inventory automation",
                    MembershipStrength::Substantive,
                ),
            ]),
        ),
        (
            6,
            expected(&[
                (
                    "Aging and family role reversal",
                    MembershipStrength::Central,
                ),
                (
                    "Family and close relationships",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            7,
            expected(&[
                (
                    "Exercise and physical training",
                    MembershipStrength::Substantive,
                ),
                ("Language and word usage", MembershipStrength::Central),
            ]),
        ),
        (
            8,
            expected(&[
                ("Child cognitive development", MembershipStrength::Central),
                (
                    "Development of knowledge and reasoning",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            9,
            expected(&[
                ("Music search and discovery", MembershipStrength::Central),
                ("Music streaming services", MembershipStrength::Substantive),
            ]),
        ),
        (
            10,
            expected(&[
                (
                    "Exercise and physical training",
                    MembershipStrength::Central,
                ),
                ("Nutrition and health", MembershipStrength::Substantive),
            ]),
        ),
        (
            11,
            expected(&[
                (
                    "Coffee brewing and preparation",
                    MembershipStrength::Substantive,
                ),
                ("Coffee product comparison", MembershipStrength::Substantive),
                (
                    "Coffee taste and product quality",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            13,
            expected(&[
                (
                    "Creative practice and skill development",
                    MembershipStrength::Central,
                ),
                ("Learning a musical instrument", MembershipStrength::Central),
                (
                    "Persistence in learning a skill",
                    MembershipStrength::Substantive,
                ),
            ]),
        ),
        (
            16,
            expected(&[(
                "Artificial boundaries between scientific disciplines",
                MembershipStrength::Central,
            )]),
        ),
        (
            17,
            expected(&[
                ("Books and reading", MembershipStrength::Substantive),
                (
                    "Criticism of digital access restrictions",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            18,
            expected(&[
                ("Book recommendations", MembershipStrength::Central),
                ("Books and reading", MembershipStrength::Central),
            ]),
        ),
        (
            19,
            expected(&[
                ("Early Islamic history", MembershipStrength::Central),
                ("History", MembershipStrength::Central),
            ]),
        ),
        (
            22,
            expected(&[("AI cognition and reasoning", MembershipStrength::Central)]),
        ),
        (
            23,
            expected(&[
                ("Book recommendations", MembershipStrength::Central),
                ("Books and reading", MembershipStrength::Central),
                ("History", MembershipStrength::Central),
                ("Medieval history", MembershipStrength::Substantive),
            ]),
        ),
        (
            24,
            expected(&[
                (
                    "Linux and open-source software",
                    MembershipStrength::Central,
                ),
                ("Shell scripting", MembershipStrength::Central),
            ]),
        ),
        (
            25,
            expected(&[
                (
                    "Energy systems and renewable power",
                    MembershipStrength::Central,
                ),
                (
                    "Homesteading and self-sufficient living",
                    MembershipStrength::Substantive,
                ),
                ("Practical Bitcoin mining", MembershipStrength::Central),
                ("Resource conservation", MembershipStrength::Substantive),
                (
                    "Software development and automation",
                    MembershipStrength::Substantive,
                ),
            ]),
        ),
        (
            27,
            expected(&[
                ("Open communication", MembershipStrength::Central),
                (
                    "Open protocols and decentralized networks",
                    MembershipStrength::Substantive,
                ),
                (
                    "Resistance to online censorship",
                    MembershipStrength::Central,
                ),
            ]),
        ),
        (
            30,
            expected(&[
                ("AI privacy and security", MembershipStrength::Central),
                ("Cloud AI infrastructure", MembershipStrength::Central),
                ("Privacy and surveillance", MembershipStrength::Central),
            ]),
        ),
        (
            31,
            expected(&[
                ("AI privacy and security", MembershipStrength::Substantive),
                ("On-device AI", MembershipStrength::Central),
                ("Privacy and surveillance", MembershipStrength::Substantive),
            ]),
        ),
        (
            32,
            expected(&[
                (
                    "Developer stereotypes and interpersonal behavior",
                    MembershipStrength::Central,
                ),
                (
                    "Linux and open-source software",
                    MembershipStrength::Substantive,
                ),
            ]),
        ),
        (
            33,
            expected(&[
                (
                    "Algorithmic attention and echo chambers",
                    MembershipStrength::Incidental,
                ),
                (
                    "Creator funding and direct value exchange",
                    MembershipStrength::Incidental,
                ),
                ("Nostr platform and ecosystem", MembershipStrength::Central),
                ("Open communication", MembershipStrength::Substantive),
                ("Privacy and surveillance", MembershipStrength::Incidental),
            ]),
        ),
        (
            35,
            expected(&[
                ("Art and aesthetics", MembershipStrength::Substantive),
                ("Goods offered for sale", MembershipStrength::Central),
                ("Poetry", MembershipStrength::Incidental),
                ("Pottery", MembershipStrength::Central),
            ]),
        ),
        (
            36,
            expected(&[
                (
                    "Family and close relationships",
                    MembershipStrength::Incidental,
                ),
                (
                    "Geographic and jurisdictional autonomy",
                    MembershipStrength::Central,
                ),
                (
                    "Public journaling and self-documentation",
                    MembershipStrength::Substantive,
                ),
                ("Relocation and moving abroad", MembershipStrength::Central),
            ]),
        ),
        (
            46,
            expected(&[
                ("Composting", MembershipStrength::Central),
                (
                    "Family and close relationships",
                    MembershipStrength::Substantive,
                ),
                ("Gardening and growing plants", MembershipStrength::Central),
            ]),
        ),
        (
            53,
            expected(&[
                ("Art and aesthetics", MembershipStrength::Substantive),
                ("Photography", MembershipStrength::Central),
                ("Travel", MembershipStrength::Central),
                ("Visual storytelling", MembershipStrength::Substantive),
            ]),
        ),
        (
            60,
            expected(&[
                ("Coffee and memory", MembershipStrength::Substantive),
                ("Poetry", MembershipStrength::Central),
            ]),
        ),
    ];

    for (slot, expected_memberships) in expected_maps {
        assert_eq!(
            tracked_memberships_for_slot(&proposal, &draft, slot),
            expected_memberships,
            "corrected note map changed for slot {slot}"
        );
    }

    let approved_slots = [
        1, 4, 5, 12, 14, 15, 20, 21, 26, 28, 29, 38, 39, 43, 45, 48, 52, 54, 55, 56, 57, 60,
    ];
    assert_eq!(
        tracked_maps_sha256(&proposal, &draft, &approved_slots),
        "60de22f2fcdfa20f7ebf7abb770414330fd97ac37103275621418c6958f06226",
        "the 22 reviewed note maps must match the explicit correction pass"
    );

    let accepted_slots = [
        1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
        28, 29, 30, 31, 32, 33, 36, 38, 39, 43, 45, 46, 48, 52, 53, 54, 55, 56, 57, 60,
    ];
    assert_eq!(
        tracked_maps_sha256(&proposal, &draft, &accepted_slots),
        "df9a04e6c1f924ae35abf211a4be06b5cdd23c15017bc77e9946b350a4d4f594",
        "the 45 reviewed note maps must match the explicit correction pass"
    );
}

#[test]
fn tracked_crec_116_uses_bounded_grouping_nodes_without_duplicate_leaf_labels() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");

    for subject_id in [
        "book-topics",
        "history-topics",
        "software-security",
        "visual-art",
        "creative-learning",
        "personal-life",
        "resource-use",
        "freedom-expression",
        "digital-autonomy",
    ] {
        let subject = draft.node(subject_id).expect("tracked grouping subject");
        assert!(
            !subject.is_leaf(),
            "{subject_id} must organize its displayed subject choices"
        );
        assert!(subject.memberships.is_empty());
        assert!((2..=8).contains(&subject.children.len()));
    }

    let leaf_labels = draft
        .nodes
        .iter()
        .filter(|node| node.is_leaf())
        .map(|node| node.label.as_str())
        .collect::<Vec<_>>();
    assert_eq!(
        leaf_labels.iter().copied().collect::<BTreeSet<_>>().len(),
        leaf_labels.len(),
        "note-map revisions use visible labels, so every leaf label must be unique"
    );
}

#[test]
fn tracked_crec_116_hierarchy_applies_the_approved_parent_corrections() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let child_ids = |node_id: &str| {
        draft
            .node(node_id)
            .expect("tracked parent subject")
            .children
            .clone()
    };

    assert_eq!(
        child_ids("book-topics"),
        vec!["books-reading", "book-recommendations"]
    );
    assert!(child_ids("knowledge-written-culture").contains(&"digital-knowledge-access".to_owned()));
    assert!(child_ids("knowledge-written-culture")
        .contains(&"scientific-discipline-boundaries".to_owned()));
    assert_eq!(
        draft
            .node("scientific-discipline-boundaries")
            .expect("precise scientific subject")
            .label,
        "Artificial boundaries between scientific disciplines"
    );
    assert!(draft.node("scientific-thought").is_none());
    assert!(draft.node("philosophy-of-science").is_none());
    assert!(draft.node("unity-of-nature").is_none());

    assert!(!child_ids("software-systems").contains(&"developer-stereotypes".to_owned()));
    assert_eq!(
        child_ids("society"),
        vec![
            "freedom-expression",
            "digital-autonomy",
            "economy-exchange",
            "developer-stereotypes",
        ]
    );
    assert_eq!(
        child_ids("freedom-expression"),
        vec!["open-communication", "censorship-resistance"]
    );
    assert_eq!(
        child_ids("digital-autonomy"),
        vec![
            "privacy-surveillance",
            "technology-autonomy",
            "algorithmic-attention",
        ]
    );
    assert!(child_ids("computing").contains(&"decentralized-protocols".to_owned()));
    assert!(child_ids("nostr-technology").contains(&"nostr-platform-ecosystem".to_owned()));

    assert_eq!(
        draft.node("health-movement").expect("health parent").label,
        "Health and wellbeing"
    );
    assert_eq!(
        draft.node("personal-life").expect("personal parent").label,
        "Personal experiences and relationships"
    );
    assert_eq!(
        child_ids("coffee-topics"),
        vec![
            "coffee-roasting-personal-taste",
            "coffee-taste-quality",
            "coffee-brewing-preparation",
            "coffee-product-comparison",
            "coffee-memory",
        ]
    );
    assert!(draft.node("coffee").is_none());
    assert_eq!(
        child_ids("daily-life"),
        vec!["personal-life", "coffee-topics", "food-meals", "cooking",]
    );
    assert_eq!(
        child_ids("environment"),
        vec![
            "energy-systems",
            "climate-emissions",
            "resource-use",
            "nature-landscapes",
            "gardening",
            "homesteading",
        ]
    );
}

#[test]
fn tracked_crec_116_review_session_preserves_the_human_hierarchy_decisions() {
    let tracked_session = "reference_map/crec-116-hierarchy-note-branch-review-session-v1.json";
    let envelope: serde_json::Value = serde_json::from_slice(
        &fs::read(tracked_session).expect("read tracked CREC-116 review session"),
    )
    .expect("decode tracked CREC-116 review session");
    let parent_history = envelope["session"]["history"]
        .as_array()
        .expect("review history")
        .iter()
        .filter(|record| record["target"]["kind"] == "parent")
        .collect::<Vec<_>>();

    assert_eq!(
        envelope["state_sha256"],
        "5dcdae305ad4108be785440c37746d0712af4e813c1fbfca9c522ef9bc527da1"
    );
    assert_eq!(
        envelope["session"]["history"]
            .as_array()
            .expect("review history")
            .len(),
        120,
        "only recorded human decisions belong in the tracked checkpoint"
    );
    assert_eq!(parent_history.len(), 39);
    assert_eq!(
        parent_history
            .iter()
            .filter(|record| record["decision"]["outcome"] == "approved")
            .count(),
        30
    );
    assert_eq!(
        parent_history
            .iter()
            .filter(|record| record["decision"]["outcome"] == "rejected")
            .count(),
        9
    );
    assert!(parent_history.iter().any(|record| {
        record["target"]["node_id"] == "scientific-thought"
            && record["decision"]["outcome"] == "rejected"
            && record["decision"]["comment"] == "unity of nature does not belong"
    }));
    assert!(parent_history.iter().any(|record| {
        record["target"]["node_id"] == "root" && record["decision"]["outcome"] == "approved"
    }));
    assert!(parent_history.iter().any(|record| {
        record["target"]["node_id"] == "daily-life"
            && record["decision"]["outcome"] == "rejected"
            && record["decision"]["comment"] == "disagree w 5 & 6"
    }));
    assert_eq!(
        envelope["session"]["focus_coverage_history"][0]["decision"]["outcome"],
        "approved"
    );

    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
    let mut note_review = NoteReviewSession::new(&proposal).expect("create note review");
    for note in &proposal.notes {
        note_review
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("approve tracked note");
    }
    let approved_notes =
        ApprovedNoteSet::from_review(&proposal, &note_review).expect("derive approved notes");
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode tracked hierarchy draft");
    let temp = tempfile::tempdir().expect("tempdir");
    let approved_notes_path = temp.path().join("approved-notes.json");
    let draft_path = temp.path().join("draft.json");
    let session_path = temp.path().join("session.json");
    write_json(&approved_notes_path, &approved_notes);
    write_json(&draft_path, &draft);
    fs::copy(tracked_session, &session_path).expect("copy tracked session");
    let approved_hierarchy_path = temp.path().join("approved-hierarchy.json");
    let mut ui = ScriptedUi::default();

    assert_eq!(
        run_hierarchy_review(
            approved_notes_path,
            draft_path,
            session_path,
            &approved_hierarchy_path,
            &mut ui,
        )
        .expect("resume the production hierarchy review from tracked state"),
        ReviewRunOutcome::Approved
    );
    assert!(ui.screens.is_empty());
    assert!(approved_hierarchy_path.is_file());
}

#[test]
fn tracked_crec_116_approved_hierarchy_is_complete_and_source_bound() {
    let hierarchy: ApprovedHierarchy = serde_json::from_slice(
        &fs::read("reference_map/crec-116-approved-hierarchy-v1.json")
            .expect("read tracked CREC-116 approved hierarchy"),
    )
    .expect("decode tracked CREC-116 approved hierarchy");
    hierarchy
        .validate()
        .expect("tracked CREC-116 approved hierarchy");

    let proposal = load_verified_note_proposal("reference_map/crec-116-note-proposal-v3.json")
        .expect("tracked CREC-116 proposal");
    let mut note_review = NoteReviewSession::new(&proposal).expect("create note review");
    for note in &proposal.notes {
        note_review
            .record(
                &proposal,
                note.slot,
                NoteReviewDecision {
                    outcome: ReviewOutcome::Approved,
                    comment: String::new(),
                },
            )
            .expect("approve tracked note");
    }
    let approved_notes =
        ApprovedNoteSet::from_review(&proposal, &note_review).expect("derive approved notes");
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode tracked hierarchy draft");

    assert_eq!(
        hierarchy.approved_notes_sha256,
        approved_notes.identity().expect("approved-note identity")
    );
    assert_eq!(
        hierarchy.hierarchy_draft_sha256,
        draft.identity(&approved_notes).expect("hierarchy identity")
    );
    assert_eq!(hierarchy.notes.len(), REFERENCE_NOTE_COUNT);
    assert_eq!(hierarchy.nodes, draft.nodes);

    let meaningful_subjects = hierarchy
        .nodes
        .iter()
        .filter(|node| node.is_leaf())
        .flat_map(|node| &node.memberships)
        .filter(|membership| {
            matches!(
                membership.strength,
                MembershipStrength::Central | MembershipStrength::Substantive
            )
        })
        .fold(BTreeMap::<&str, usize>::new(), |mut counts, membership| {
            *counts.entry(membership.note_id.as_str()).or_default() += 1;
            counts
        });
    assert_eq!(
        hierarchy
            .notes
            .iter()
            .filter(|note| meaningful_subjects[note.note_id.as_str()] == 1)
            .count(),
        6
    );
    assert_eq!(
        hierarchy
            .notes
            .iter()
            .filter(|note| meaningful_subjects[note.note_id.as_str()] >= 2)
            .count(),
        42
    );
}

#[test]
fn tracked_nostr_technical_subject_uses_one_coherent_label() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let subject = draft
        .nodes
        .iter()
        .find(|node| node.node_id == "nostr-protocol-engineering")
        .expect("tracked Nostr technical subject");

    assert_eq!(subject.label, "Nostr technical design and implementation");
    assert!(
        draft
            .nodes
            .iter()
            .all(|node| node.label != "Nostr protocols and engineering"),
        "the misleading combined label is absent"
    );
}

#[test]
fn tracked_books_and_history_subjects_are_separate() {
    let draft: HierarchyDraft = serde_json::from_slice(
        &fs::read("reference_map/crec-116-hierarchy-draft-v3.json")
            .expect("read tracked hierarchy draft"),
    )
    .expect("decode hierarchy draft");
    let books = draft.node("books-reading").expect("books subject");
    let history = draft.node("history").expect("history subject");

    assert_eq!(books.label, "Books and reading");
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
        &HierarchyReviewTarget::Parent {
            node_id: "all-subjects".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Parent {
            node_id: "technology".to_owned(),
        }
    ));
    assert!(session.is_approved(
        &revised_draft,
        &revised_notes,
        &HierarchyReviewTarget::Parent {
            node_id: "life".to_owned(),
        }
    ));
    assert!(
        session.focus_coverage_is_approved(&revised_draft, &revised_notes),
        "unchanged membership evidence preserves the final coverage decision"
    );
    assert!(
        !session.review_is_complete(&revised_draft, &revised_notes),
        "preserved parent decisions must not hide an invalidated note map"
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
    let mut ui = ScriptedUi::new(
        (0..REFERENCE_NOTE_COUNT).map(|_| ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new(),
        }),
    );

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
