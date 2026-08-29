//! Durable approval runners for the selected notes and reference hierarchy.

use std::collections::BTreeMap;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::Path;

use serde::Deserialize;
use sha2::{Digest, Sha256};

use crate::reference_map::{
    ApprovedHierarchy, ApprovedNoteSet, BroadNarrowRole, HierarchyDraft, HierarchyReviewDecision,
    HierarchyReviewSession, HierarchyReviewTarget, MembershipStrength, NoteProposal,
    NoteReviewDecision, NoteReviewSession, PairMembership, ProposedNote, ReviewOutcome,
    SelectionSource,
};
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    ReferenceTerminal,
};
use crate::review_state::{
    acquire_session_lock, load_json, load_session, publish_json, replace_json, save_session,
};
use crate::snapshot::{Error, Result, io_error};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReviewRunOutcome {
    Paused,
    NeedsRevision { approved: usize, rejected: usize },
    Approved,
}

pub trait ApprovalUi {
    fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction>;
}

impl ApprovalUi for ReferenceTerminal {
    fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction> {
        ReferenceTerminal::review(self, screen)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct NoteSelectionPlan {
    schema_version: u32,
    proposal_id: String,
    source: SelectionSource,
    notes: Vec<PlannedNote>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PlannedNote {
    slot: u8,
    note_id: String,
    contrast_pair: Option<PairMembership>,
    broad_narrow_pair: Option<PairMembership>,
    niche_or_sparse_case: Option<String>,
}

pub fn prepare_note_proposal(
    plan_path: impl AsRef<Path>,
    proposal_path: impl AsRef<Path>,
) -> Result<NoteProposal> {
    let plan_path = plan_path.as_ref();
    let proposal_path = proposal_path.as_ref();
    if plan_path.parent() != proposal_path.parent() {
        return Err(Error::ExperimentState(
            "the generated proposal must be stored beside its selection plan so relative source provenance remains valid"
                .to_owned(),
        ));
    }
    let plan: NoteSelectionPlan = load_json(plan_path)?;
    if plan.schema_version != 3
        || plan.proposal_id.trim().is_empty()
        || plan.notes.len() != crate::reference_map::REFERENCE_NOTE_COUNT
    {
        return Err(Error::ExperimentState(
            "note selection plan schema, ID, or note count is invalid".to_owned(),
        ));
    }
    let sample = load_source_sample(&plan.source, plan_path)?;
    let notes = plan
        .notes
        .into_iter()
        .map(|planned| {
            let row = sample.get(planned.note_id.as_str()).ok_or_else(|| {
                Error::ExperimentState(format!(
                    "planned note {} is absent from the bound source sample and split",
                    planned.note_id
                ))
            })?;
            Ok(ProposedNote {
                slot: planned.slot,
                note_id: planned.note_id,
                pubkey: row.pubkey.clone(),
                content: row.content.clone(),
                contrast_pair: planned.contrast_pair,
                broad_narrow_pair: planned.broad_narrow_pair,
                niche_or_sparse_case: planned.niche_or_sparse_case,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let proposal = NoteProposal {
        schema_version: 3,
        proposal_id: plan.proposal_id,
        source: plan.source,
        notes,
    };
    proposal.validate()?;
    replace_json(proposal_path, &proposal)?;
    Ok(proposal)
}

pub fn load_verified_note_proposal(path: impl AsRef<Path>) -> Result<NoteProposal> {
    let path = path.as_ref();
    let proposal: NoteProposal = load_json(path)?;
    proposal.validate()?;
    let sample = load_source_sample(&proposal.source, path)?;
    for note in &proposal.notes {
        let Some(row) = sample.get(note.note_id.as_str()) else {
            return Err(Error::ExperimentState(format!(
                "proposed note {} does not exactly match the bound source sample",
                note.note_id
            )));
        };
        if row.pubkey != note.pubkey || row.content != note.content {
            return Err(Error::ExperimentState(format!(
                "proposed note {} does not exactly match the bound source sample",
                note.note_id
            )));
        }
    }
    Ok(proposal)
}

fn load_source_sample(
    source: &SelectionSource,
    anchor_path: &Path,
) -> Result<BTreeMap<String, SourceSampleRow>> {
    let sample_path = if Path::new(&source.sample_path).is_absolute() {
        Path::new(&source.sample_path).to_owned()
    } else {
        anchor_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join(&source.sample_path)
    };
    let file = File::open(&sample_path)
        .map_err(|source| io_error("open source sample", &sample_path, source))?;
    let mut reader = BufReader::new(file);
    let mut rows = BTreeMap::new();
    let mut digest = Sha256::new();
    let mut line = Vec::new();
    loop {
        line.clear();
        let read = reader
            .read_until(b'\n', &mut line)
            .map_err(|source| io_error("read source sample", &sample_path, source))?;
        if read == 0 {
            break;
        }
        digest.update(&line);
        let row: SourceSampleRow =
            serde_json::from_slice(&line).map_err(|source| Error::Manifest {
                operation: "decode source sample row from",
                path: sample_path.clone(),
                source,
            })?;
        if row.split != source.split {
            continue;
        }
        if rows.insert(row.note_id.clone(), row).is_some() {
            return Err(Error::ExperimentState(format!(
                "source sample `{}` repeats a note ID in split {}",
                sample_path.display(),
                source.split
            )));
        }
    }
    let actual_sha256 = format!("{:x}", digest.finalize());
    if actual_sha256 != source.sample_sha256 {
        return Err(Error::ExperimentState(format!(
            "source sample `{}` has SHA-256 {actual_sha256}, expected {}",
            sample_path.display(),
            source.sample_sha256
        )));
    }
    Ok(rows)
}

#[derive(Deserialize)]
struct SourceSampleRow {
    split: String,
    note_id: String,
    pubkey: String,
    content: String,
}

pub fn run_note_review(
    proposal_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    approved_path: impl AsRef<Path>,
    ui: &mut impl ApprovalUi,
) -> Result<ReviewRunOutcome> {
    let proposal_path = proposal_path.as_ref();
    let session_path = session_path.as_ref();
    let approved_path = approved_path.as_ref();
    let proposal = load_verified_note_proposal(proposal_path)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = load_session::<NoteReviewSession>(session_path)?
        .unwrap_or(NoteReviewSession::new(&proposal)?);
    session.reconcile(&proposal)?;
    save_session(session_path, &session)?;

    while let Some(slot) = session.pending_slots(&proposal).first().copied() {
        let screen = note_screen(&proposal, &session, slot)?;
        match ui
            .review(screen)
            .map_err(|source| io_error("run review UI for", proposal_path, source))?
        {
            ApprovalTuiAction::None => {
                return Err(Error::ExperimentState(
                    "approval UI returned without a decision".to_owned(),
                ));
            }
            ApprovalTuiAction::Pause => return Ok(ReviewRunOutcome::Paused),
            ApprovalTuiAction::SaveComment { .. } => {
                return Err(Error::ExperimentState(
                    "production note review cannot save a draft comment".to_owned(),
                ));
            }
            ApprovalTuiAction::Skip { .. } => {
                return Err(Error::ExperimentState(
                    "production note review cannot skip a decision".to_owned(),
                ));
            }
            ApprovalTuiAction::Submit { outcome, comment } => {
                session.record(&proposal, slot, NoteReviewDecision { outcome, comment })?;
                save_session(session_path, &session)?;
            }
        }
    }

    let approved = session.approved_count(&proposal);
    let rejected = proposal
        .notes
        .iter()
        .filter(|note| {
            session
                .decision_for(&proposal, note.slot)
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
        })
        .count();
    if rejected != 0 {
        return Ok(ReviewRunOutcome::NeedsRevision { approved, rejected });
    }
    let artifact = ApprovedNoteSet::from_review(&proposal, &session)?;
    publish_json(approved_path, &artifact)?;
    Ok(ReviewRunOutcome::Approved)
}

pub fn run_hierarchy_review(
    approved_notes_path: impl AsRef<Path>,
    draft_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    approved_hierarchy_path: impl AsRef<Path>,
    ui: &mut impl ApprovalUi,
) -> Result<ReviewRunOutcome> {
    let approved_notes_path = approved_notes_path.as_ref();
    let draft_path = draft_path.as_ref();
    let session_path = session_path.as_ref();
    let approved_hierarchy_path = approved_hierarchy_path.as_ref();
    let approved_notes: ApprovedNoteSet = load_json(approved_notes_path)?;
    approved_notes.validate()?;
    let draft: HierarchyDraft = load_json(draft_path)?;
    draft.validate(&approved_notes)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = load_session::<HierarchyReviewSession>(session_path)?
        .unwrap_or(HierarchyReviewSession::new(&draft, &approved_notes)?);
    session.reconcile_legacy_empty()?;
    save_session(session_path, &session)?;

    loop {
        if let Some(target) = session
            .reviewable_targets(&draft, &approved_notes)?
            .first()
            .cloned()
        {
            let screen = hierarchy_target_screen(&draft, &approved_notes, &session, &target)?;
            match ui
                .review(screen)
                .map_err(|source| io_error("run hierarchy review UI for", draft_path, source))?
            {
                ApprovalTuiAction::None => {
                    return Err(Error::ExperimentState(
                        "approval UI returned without a decision".to_owned(),
                    ));
                }
                ApprovalTuiAction::Pause => return Ok(ReviewRunOutcome::Paused),
                ApprovalTuiAction::SaveComment { .. } => {
                    return Err(Error::ExperimentState(
                        "production hierarchy review cannot save a draft comment".to_owned(),
                    ));
                }
                ApprovalTuiAction::Skip { .. } => {
                    return Err(Error::ExperimentState(
                        "production hierarchy review cannot skip a decision".to_owned(),
                    ));
                }
                ApprovalTuiAction::Submit { outcome, comment } => {
                    session.record(
                        &draft,
                        &approved_notes,
                        target,
                        HierarchyReviewDecision { outcome, comment },
                    )?;
                    save_session(session_path, &session)?;
                }
            }
            continue;
        }

        if session.all_note_maps_approved(&draft, &approved_notes)
            && session.all_parents_approved(&draft, &approved_notes)
            && session
                .current_focus_coverage_decision(&draft, &approved_notes)
                .is_none()
        {
            let screen = focus_coverage_screen(&draft, &approved_notes, &session)?;
            match ui
                .review(screen)
                .map_err(|source| io_error("run hierarchy review UI for", draft_path, source))?
            {
                ApprovalTuiAction::None => {
                    return Err(Error::ExperimentState(
                        "approval UI returned without a decision".to_owned(),
                    ));
                }
                ApprovalTuiAction::Pause => return Ok(ReviewRunOutcome::Paused),
                ApprovalTuiAction::SaveComment { .. } => {
                    return Err(Error::ExperimentState(
                        "production hierarchy review cannot save a draft comment".to_owned(),
                    ));
                }
                ApprovalTuiAction::Skip { .. } => {
                    return Err(Error::ExperimentState(
                        "production hierarchy review cannot skip a decision".to_owned(),
                    ));
                }
                ApprovalTuiAction::Submit { outcome, comment } => {
                    session.record_focus_coverage(
                        &draft,
                        &approved_notes,
                        HierarchyReviewDecision { outcome, comment },
                    )?;
                    save_session(session_path, &session)?;
                }
            }
            continue;
        }

        break;
    }

    let (approved, rejected, _) = session.decision_counts(&draft, &approved_notes)?;
    if !session.review_is_complete(&draft, &approved_notes) {
        return Ok(ReviewRunOutcome::NeedsRevision { approved, rejected });
    }
    let artifact = ApprovedHierarchy::from_review(&draft, &approved_notes, &session)?;
    publish_json(approved_hierarchy_path, &artifact)?;
    Ok(ReviewRunOutcome::Approved)
}

fn focus_coverage_screen(
    draft: &HierarchyDraft,
    approved_notes: &ApprovedNoteSet,
    session: &HierarchyReviewSession,
) -> Result<ApprovalScreen> {
    let (approved, rejected, total) = session.decision_counts(draft, approved_notes)?;
    let membership_inventory = note_membership_inventory(draft);
    let mut narrow_focus = Vec::new();
    let mut multi_focus = Vec::new();
    let mut notes = approved_notes.notes.iter().collect::<Vec<_>>();
    notes.sort_unstable_by_key(|note| note.slot);
    for note in notes {
        let memberships = &membership_inventory[note.note_id.as_str()];
        let meaningful_subject_count = memberships
            .iter()
            .filter(|(_, strength)| {
                matches!(
                    strength,
                    MembershipStrength::Central | MembershipStrength::Substantive
                )
            })
            .count();
        let example = format!(
            "Example · Slot {:02}\n{}",
            note.slot,
            format_note_memberships(memberships)
        );
        if meaningful_subject_count <= 1 {
            narrow_focus.push(example);
        } else {
            multi_focus.push(example);
        }
    }
    let format_examples = |examples: &[String]| {
        if examples.is_empty() {
            "No examples".to_owned()
        } else {
            examples
                .iter()
                .take(3)
                .cloned()
                .collect::<Vec<_>>()
                .join("\n\n────────────────────────────────────────\n\n")
        }
    };
    let summary = format!(
        "Narrow-focus notes · {}\n\
         At most one subject is Central or Substantive.\n\n\
         {}\n\n\
         ════════════════════════════════════════\n\n\
         Multi-focus notes · {}\n\
         Two or more subjects are Central or Substantive.\n\n\
         {}",
        narrow_focus.len(),
        format_examples(&narrow_focus),
        multi_focus.len(),
        format_examples(&multi_focus),
    );
    Ok(ApprovalScreen {
        heading: format!(
            "Hierarchy review · {approved} approved · {rejected} rejected · {total} total"
        ),
        title: Some("Focus coverage".to_owned()),
        scope: format!(
            "Do the {} note maps include both narrow-focus and multi-focus notes?",
            approved_notes.notes.len()
        ),
        approve_label: "Yes — both kinds are represented".to_owned(),
        reject_label: "No — describe what is missing".to_owned(),
        rejection_help:
            "State whether narrow-focus or multi-focus notes are missing or too sparse.".to_owned(),
        guidance: Some(focus_coverage_guidance()),
        evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
            title: "Coverage summary".to_owned(),
            annotation:
                "Each note map was already reviewed. This screen only checks the mix of focus patterns."
                    .to_owned(),
            body: summary,
        }]),
    })
}

fn note_screen(
    proposal: &NoteProposal,
    session: &NoteReviewSession,
    slot: u8,
) -> Result<ApprovalScreen> {
    let note = proposal
        .note(slot)
        .ok_or_else(|| Error::ExperimentState(format!("note slot {slot} is missing")))?;
    let ordinal = proposal
        .notes
        .iter()
        .position(|candidate| candidate.slot == slot)
        .expect("the reviewed slot belongs to the validated proposal")
        + 1;
    let approved = session.approved_count(proposal);
    let rejected = proposal
        .notes
        .iter()
        .filter(|note| {
            session
                .decision_for(proposal, note.slot)
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
        })
        .count();
    let mut categories = Vec::new();
    if let Some(pair) = &note.contrast_pair {
        categories.push(format!("Related-but-different pair · {}", pair.pair_id));
    }
    if let Some(pair) = &note.broad_narrow_pair {
        let role = match pair
            .broad_narrow_role
            .expect("validated broad/narrow pair has a role")
        {
            BroadNarrowRole::Broad => "broad",
            BroadNarrowRole::Narrow => "narrow",
        };
        categories.push(format!("Broad/narrow pair · {role} · {}", pair.pair_id));
    }
    if let Some(case) = &note.niche_or_sparse_case {
        categories.push(format!("Niche/sparse coverage case · {case}"));
    }
    let mut evidence = vec![ApprovalEvidence {
        title: "Candidate note".to_owned(),
        annotation: categories.join(" · "),
        body: note.content.clone(),
    }];
    let mut partner_slots = Vec::new();
    if let Some(pair) = &note.contrast_pair {
        partner_slots.push((
            pair.partner_slot,
            format!("Related-but-different pair · {}", pair.pair_id),
        ));
    }
    if let Some(pair) = &note.broad_narrow_pair {
        partner_slots.push((
            pair.partner_slot,
            format!("Broad/narrow partner · {}", pair.pair_id),
        ));
    }
    partner_slots.sort_unstable_by_key(|(partner_slot, _)| *partner_slot);
    partner_slots.dedup_by_key(|(partner_slot, _)| *partner_slot);
    for (partner_slot, annotation) in partner_slots {
        let partner = proposal.note(partner_slot).ok_or_else(|| {
            Error::ExperimentState(format!(
                "note slot {slot} names missing partner slot {partner_slot}"
            ))
        })?;
        evidence.push(ApprovalEvidence {
            title: format!("Comparison note · Slot {partner_slot:02}"),
            annotation: format!(
                "{annotation}\n\
                 Shown only to judge this relationship; reviewed separately at its own slot."
            ),
            body: partner.content.clone(),
        });
    }
    Ok(ApprovalScreen {
        heading: format!(
            "Candidate {ordinal} of {} · {approved} approved · {rejected} rejected",
            proposal.notes.len()
        ),
        title: Some(format!("Slot {slot:02}")),
        scope: format!(
            "Is there a concrete reason this note should not be included in the {}-note reference set?",
            proposal.notes.len()
        ),
        approve_label: "Approve — no disqualifying problem".to_owned(),
        reject_label: "Reject — explain the problem".to_owned(),
        rejection_help: "Explain the concrete disqualifying problem.".to_owned(),
        guidance: Some(ApprovalGuidance {
            title: "Rejection guide".to_owned(),
            body: "Reject only when:\n\n\
                   • Text is corrupt, truncated, or effectively empty.\n\
                   • The note is in a language you cannot judge.\n\
                   • Essential meaning depends on missing context.\n\
                   • It duplicates or nearly duplicates another selected note.\n\
                   • A diagnostic annotation is wrong.\n\n\
                   Do not reject merely because:\n\n\
                   • You disagree with it.\n\
                   • It has several subjects.\n\
                   • It is niche, ambiguous, old, or personally uninteresting.\n\n\
                   A URL is only a problem when its contents are necessary to understand the note."
                .to_owned(),
        }),
        evidence: ApprovalEvidenceLayout::Paged(evidence),
    })
}

fn hierarchy_target_screen(
    draft: &HierarchyDraft,
    approved_notes: &ApprovedNoteSet,
    session: &HierarchyReviewSession,
    target: &HierarchyReviewTarget,
) -> Result<ApprovalScreen> {
    let (approved, rejected, total) = session.decision_counts(draft, approved_notes)?;
    let heading =
        format!("Hierarchy review · {approved} approved · {rejected} rejected · {total} total");
    match target {
        HierarchyReviewTarget::NoteMap { note_id } => {
            let note = approved_notes
                .notes
                .iter()
                .find(|note| note.note_id == *note_id)
                .ok_or_else(|| {
                    Error::ExperimentState(format!("approved reference note {note_id} is missing"))
                })?;
            let memberships = note_map_memberships(draft, note_id);
            Ok(ApprovalScreen {
                heading,
                title: Some(format!("Note map · Slot {:02}", note.slot)),
                scope: "Are these subject assignments correct?".to_owned(),
                approve_label: "Approve these assignments".to_owned(),
                reject_label: "Reject — name the exact correction".to_owned(),
                rejection_help:
                    "Name the incorrect subject or strength and state the exact correction."
                        .to_owned(),
                guidance: Some(note_map_guidance()),
                evidence: ApprovalEvidenceLayout::Stacked {
                    top: ApprovalEvidence {
                        title: "Note".to_owned(),
                        annotation: String::new(),
                        body: note.content.clone(),
                    },
                    bottom: ApprovalEvidence {
                        title: "Proposed subject map".to_owned(),
                        annotation: String::new(),
                        body: format_note_assignments(&memberships),
                    },
                },
            })
        }
        HierarchyReviewTarget::Parent { node_id } => {
            let parent = draft.node(node_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy parent {node_id} is missing"))
            })?;
            let parent_targets = HierarchyReviewSession::parent_targets(draft);
            let parent_index = parent_targets
                .iter()
                .position(|target| {
                    target
                        == &HierarchyReviewTarget::Parent {
                            node_id: node_id.clone(),
                        }
                })
                .ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "hierarchy parent {node_id} has no review target"
                    ))
                })?
                + 1;
            let child_list = format_immediate_children(draft, node_id)?;
            let child_count = parent.children.len();
            Ok(ApprovalScreen {
                heading: format!(
                    "Hierarchy review · Parent {parent_index} of {} · {} note maps approved",
                    parent_targets.len(),
                    approved_notes.notes.len()
                ),
                title: Some(if node_id == &draft.root_node_id {
                    "Top-level subjects".to_owned()
                } else {
                    parent.label.clone()
                }),
                scope: "Are these immediate child subjects correct?".to_owned(),
                approve_label: "No problems".to_owned(),
                reject_label: "Describe a problem".to_owned(),
                rejection_help: "Examples:\n\
                                 [2] Title is unclear.\n\
                                 [3] Does not belong under this parent.\n\
                                 Missing \"Expected subject\"."
                    .to_owned(),
                guidance: Some(ApprovalGuidance {
                    title: "Parent review".to_owned(),
                    body: "Approving accepts the displayed child titles, their order, and their direct placement under this parent.\n\n\
                           Only this one level is being reviewed.\n\n\
                           Reject when:\n\n\
                           • A child title is unclear or combines unrelated meanings.\n\
                           • A child does not genuinely belong under this parent.\n\
                           • A necessary immediate child is missing.\n\n\
                           Name the numbered child. For something missing, name it."
                        .to_owned(),
                }),
                evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
                    title: format!(
                        "Children · {child_count} subject{}",
                        if child_count == 1 { "" } else { "s" }
                    ),
                    annotation:
                        "Approving accepts these titles, their order, and their direct placement under this parent.\n\
                         Use the numbers when describing a problem."
                            .to_owned(),
                    body: child_list,
                }]),
            })
        }
        HierarchyReviewTarget::Branch { .. }
        | HierarchyReviewTarget::Membership { .. }
        | HierarchyReviewTarget::Subject { .. }
        | HierarchyReviewTarget::ParentChild { .. } => Err(Error::ExperimentState(
            "a legacy hierarchy target reached the parent review UI".to_owned(),
        )),
    }
}

fn note_map_memberships<'a>(
    draft: &'a HierarchyDraft,
    note_id: &str,
) -> Vec<(&'a crate::reference_map::SubjectNode, MembershipStrength)> {
    let mut memberships = draft
        .nodes
        .iter()
        .filter(|node| node.is_leaf())
        .flat_map(|node| {
            node.memberships
                .iter()
                .filter(move |membership| membership.note_id == note_id)
                .map(move |membership| (node, membership.strength))
        })
        .collect::<Vec<_>>();
    memberships.sort_unstable_by(|left, right| {
        right
            .1
            .rank()
            .cmp(&left.1.rank())
            .then_with(|| left.0.label.cmp(&right.0.label))
    });
    memberships
}

fn format_note_assignments(
    memberships: &[(&crate::reference_map::SubjectNode, MembershipStrength)],
) -> String {
    memberships
        .iter()
        .map(|(subject, strength)| format!("{} — {}", subject.label, strength_label(*strength)))
        .collect::<Vec<_>>()
        .join("\n")
}

fn format_immediate_children(draft: &HierarchyDraft, node_id: &str) -> Result<String> {
    let parent = draft
        .node(node_id)
        .ok_or_else(|| Error::ExperimentState(format!("hierarchy parent {node_id} is missing")))?;
    parent
        .children
        .iter()
        .enumerate()
        .map(|(index, child_id)| {
            let child = draft.node(child_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy child {child_id} is missing"))
            })?;
            Ok(format!("[{}] {}", index + 1, child.label))
        })
        .collect::<Result<Vec<_>>>()
        .map(|lines| lines.join("\n"))
}

fn focus_coverage_guidance() -> ApprovalGuidance {
    ApprovalGuidance {
        title: "Coverage check".to_owned(),
        body: "Narrow-focus: at most one subject is Central or Substantive.\n\n\
               Multi-focus: two or more subjects are Central or Substantive.\n\n\
               Incidental subjects are minor details and do not make a note multi-focus.\n\n\
               You already approved each note’s subject assignments. This check only confirms that the set contains both kinds.\n\n\
               Central: the subject is one of the note’s main points.\n\n\
               Substantive: the subject materially matters to the note, but is not a main point.\n\n\
               Incidental: the subject appears only as a minor or supporting detail."
            .to_owned(),
    }
}

fn note_map_guidance() -> ApprovalGuidance {
    ApprovalGuidance {
        title: "Note-map review".to_owned(),
        body: "Approving accepts each listed subject and strength.\n\n\
               Reject only when:\n\n\
               • A listed subject is not actually expressed.\n\
               • A membership strength is wrong.\n\
               • A subject label makes the assignment impossible to judge.\n\n\
               Name the subject and exact correction in the rejection comment.\n\n\
               Strength scale:\n\n\
               Central: one of the note’s main points.\n\
               Substantive: materially matters, but is not a main point.\n\
               Incidental: only a minor or supporting detail."
            .to_owned(),
    }
}

fn note_membership_inventory(
    draft: &HierarchyDraft,
) -> BTreeMap<&str, Vec<(&str, MembershipStrength)>> {
    let mut memberships = BTreeMap::<&str, Vec<(&str, MembershipStrength)>>::new();
    for node in draft.nodes.iter().filter(|node| node.is_leaf()) {
        for membership in &node.memberships {
            memberships
                .entry(membership.note_id.as_str())
                .or_default()
                .push((node.label.as_str(), membership.strength));
        }
    }
    for note_memberships in memberships.values_mut() {
        note_memberships.sort_unstable_by(|left, right| {
            right
                .1
                .rank()
                .cmp(&left.1.rank())
                .then_with(|| left.0.cmp(right.0))
        });
    }
    memberships
}

fn format_note_memberships(memberships: &[(&str, MembershipStrength)]) -> String {
    memberships
        .iter()
        .map(|(label, strength)| format!("• {label} — {}", strength_label(*strength)))
        .collect::<Vec<_>>()
        .join("\n")
}

fn strength_label(strength: MembershipStrength) -> &'static str {
    match strength {
        MembershipStrength::Incidental => "Incidental",
        MembershipStrength::Substantive => "Substantive",
        MembershipStrength::Central => "Central",
    }
}
