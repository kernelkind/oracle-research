//! Durable approval runners for the 64-note selection and reference hierarchy.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::path::Path;

use serde::de::DeserializeOwned;
use serde::Deserialize;
use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::reference_map::{
    ApprovedHierarchy, ApprovedNoteSet, BroadNarrowRole, HierarchyDraft, HierarchyReviewDecision,
    HierarchyReviewSession, HierarchyReviewTarget, MembershipStrength, NoteProposal,
    NoteReviewDecision, NoteReviewSession, PairMembership, ProposedNote, ReviewOutcome,
    SelectionSource,
};
use crate::reference_tui::{
    ApprovalEvidence, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction, ReferenceTerminal,
};
use crate::snapshot::{io_error, Error, Result};

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

        if session.all_leaves_approved(&draft, &approved_notes)
            && session
                .current_focus_coverage_decision(&draft, &approved_notes)
                .is_none()
        {
            let screen = focus_coverage_screen(&draft, &approved_notes);
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
) -> ApprovalScreen {
    let membership_inventory = note_membership_inventory(draft);
    let mut groups = BTreeMap::<Vec<MembershipStrength>, Vec<String>>::new();
    for note in &approved_notes.notes {
        let memberships = &membership_inventory[note.note_id.as_str()];
        let mut signature = memberships
            .iter()
            .map(|(_, strength)| *strength)
            .collect::<Vec<_>>();
        signature.sort_unstable_by(|left, right| right.rank().cmp(&left.rank()));
        groups.entry(signature).or_default().push(format!(
            "Slot {:02}\n{}\n\n{}",
            note.slot,
            format_note_memberships(memberships),
            note.content
        ));
    }
    let evidence = groups
        .into_iter()
        .map(|(signature, notes)| {
            let note_count = notes.len();
            let membership_count = signature.len();
            ApprovalEvidence {
                title: format!(
                    "{membership_count} membership{} · {}",
                    if membership_count == 1 { "" } else { "s" },
                    format_membership_signature(&signature)
                ),
                annotation: format!(
                    "{note_count} note{} · exact ordinal signature",
                    if note_count == 1 { "" } else { "s" }
                ),
                body: notes.join("\n\n────────────────────────────────────────\n\n"),
            }
        })
        .collect();
    ApprovalScreen {
        heading: "Hierarchy review · all leaf mappings approved".to_owned(),
        title: "Focus-concentration coverage".to_owned(),
        scope:
            "Is any part of the focus-concentration spectrum missing from this 64-note reference set?"
                .to_owned(),
        approve_label: "Approve — no known coverage gap".to_owned(),
        reject_label: "Reject — describe the gap".to_owned(),
        guidance: Some(membership_strength_guidance()),
        evidence,
    }
}

fn note_screen(
    proposal: &NoteProposal,
    session: &NoteReviewSession,
    slot: u8,
) -> Result<ApprovalScreen> {
    let note = proposal
        .note(slot)
        .ok_or_else(|| Error::ExperimentState(format!("note slot {slot} is missing")))?;
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
        heading: format!("Candidate {slot} of 64 · {approved} approved · {rejected} rejected"),
        title: format!("Slot {slot:02}"),
        scope:
            "Is there a concrete reason this note should not be included in the 64-note reference set?"
                .to_owned(),
        approve_label: "Approve — no disqualifying problem".to_owned(),
        reject_label: "Reject — explain the problem".to_owned(),
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
        evidence,
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
        HierarchyReviewTarget::Membership {
            subject_id,
            note_id,
        } => {
            let subject = draft.node(subject_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy subject {subject_id} is missing"))
            })?;
            let membership = subject
                .memberships
                .iter()
                .find(|membership| membership.note_id == *note_id)
                .ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "hierarchy subject {subject_id} does not contain note {note_id}"
                    ))
                })?;
            let note = approved_notes
                .notes
                .iter()
                .find(|note| note.note_id == *note_id)
                .ok_or_else(|| {
                    Error::ExperimentState(format!("approved reference note {note_id} is missing"))
                })?;
            let strength = strength_label(membership.strength);
            Ok(ApprovalScreen {
                heading,
                title: format!("Membership · {} · {strength}", subject.label),
                scope: format!(
                    "Does this note express “{}” at {strength} strength?",
                    subject.label
                ),
                approve_label: "Approve — yes".to_owned(),
                reject_label: "Reject — no, explain".to_owned(),
                guidance: Some(membership_strength_guidance()),
                evidence: vec![ApprovalEvidence {
                    title: "Candidate note".to_owned(),
                    annotation: format!(
                        "Subject: {}\nDescription: {}\n\nThis action decides only this note’s {strength} membership.",
                        subject.label, subject.scope
                    ),
                    body: note.content.clone(),
                }],
            })
        }
        HierarchyReviewTarget::Subject { node_id } => {
            let subject = draft.node(node_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy subject {node_id} is missing"))
            })?;
            if subject.node_id == draft.root_node_id {
                return Err(Error::ExperimentState(
                    "the hidden root is not a reviewable subject".to_owned(),
                ));
            }
            if subject.is_leaf() {
                let counts = membership_strength_counts(subject);
                Ok(ApprovalScreen {
                    heading,
                    title: format!("Leaf subject · {}", subject.label),
                    scope: format!(
                        "Should “{}” remain as a leaf navigation choice?",
                        subject.label
                    ),
                    approve_label: "Approve — keep this leaf".to_owned(),
                    reject_label: "Reject — explain what should change".to_owned(),
                    guidance: None,
                    evidence: vec![ApprovalEvidence {
                        title: "Subject definition".to_owned(),
                        annotation:
                            "This action approves only this subject’s label and description."
                                .to_owned(),
                        body: format!(
                            "Label: {}\nDescription: {}\n\nApproved memberships: {}\n• Central: {}\n• Substantive: {}\n• Incidental: {}",
                            subject.label,
                            subject.scope,
                            subject.memberships.len(),
                            counts[0],
                            counts[1],
                            counts[2]
                        ),
                    }],
                })
            } else {
                let children = subject
                    .children
                    .iter()
                    .map(|child_id| {
                        let child = draft.node(child_id).ok_or_else(|| {
                            Error::ExperimentState(format!(
                                "hierarchy subject {} names missing child {child_id}",
                                subject.node_id
                            ))
                        })?;
                        Ok(format!("• {}\n  {}", child.label, child.scope))
                    })
                    .collect::<Result<Vec<_>>>()?
                    .join("\n\n");
                Ok(ApprovalScreen {
                    heading,
                    title: format!("Parent subject · {}", subject.label),
                    scope: format!(
                        "Should “{}” remain as a parent navigation choice for these approved children?",
                        subject.label
                    ),
                    approve_label: "Approve — keep this parent".to_owned(),
                    reject_label: "Reject — explain what should change".to_owned(),
                    guidance: None,
                    evidence: vec![ApprovalEvidence {
                        title: "Subject definition".to_owned(),
                        annotation:
                            "This action approves only this parent’s label and description."
                                .to_owned(),
                        body: format!(
                            "Label: {}\nDescription: {}\n\nApproved direct children:\n\n{children}",
                            subject.label, subject.scope
                        ),
                    }],
                })
            }
        }
        HierarchyReviewTarget::ParentChild {
            parent_id,
            child_id,
        } => {
            let parent = draft.node(parent_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy parent {parent_id} is missing"))
            })?;
            let child = draft.node(child_id).ok_or_else(|| {
                Error::ExperimentState(format!("hierarchy child {child_id} is missing"))
            })?;
            let top_level = parent.node_id == draft.root_node_id;
            Ok(ApprovalScreen {
                heading,
                title: if top_level {
                    format!("Top-level choice · {}", child.label)
                } else {
                    format!("Relationship · {} → {}", parent.label, child.label)
                },
                scope: if top_level {
                    format!(
                        "Should “{}” appear as a top-level navigation choice?",
                        child.label
                    )
                } else {
                    format!(
                        "Does “{}” belong directly under “{}”?",
                        child.label, parent.label
                    )
                },
                approve_label: if top_level {
                    "Approve — keep this top-level choice".to_owned()
                } else {
                    "Approve — keep this relationship".to_owned()
                },
                reject_label: "Reject — explain where it belongs".to_owned(),
                guidance: None,
                evidence: vec![ApprovalEvidence {
                    title: if top_level {
                        "Top-level choice".to_owned()
                    } else {
                        "Parent–child relationship".to_owned()
                    },
                    annotation: "This action approves only this relationship.".to_owned(),
                    body: if top_level {
                        format!("Choice: {}\nDescription: {}", child.label, child.scope)
                    } else {
                        format!(
                            "Parent: {}\nDescription: {}\n\nChild: {}\nDescription: {}",
                            parent.label, parent.scope, child.label, child.scope
                        )
                    },
                }],
            })
        }
    }
}

fn membership_strength_counts(subject: &crate::reference_map::SubjectNode) -> [usize; 3] {
    let mut counts = [0; 3];
    for membership in &subject.memberships {
        match membership.strength {
            MembershipStrength::Central => counts[0] += 1,
            MembershipStrength::Substantive => counts[1] += 1,
            MembershipStrength::Incidental => counts[2] += 1,
        }
    }
    counts
}

fn membership_strength_guidance() -> ApprovalGuidance {
    ApprovalGuidance {
        title: "Membership scale".to_owned(),
        body: "Central: the subject is one of the note’s main points.\n\n\
               Substantive: the subject materially matters to the note, but is not a main point.\n\n\
               Incidental: the subject appears only as a minor or supporting detail.\n\n\
               These are ordered categories, not percentages."
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

fn format_membership_signature(signature: &[MembershipStrength]) -> String {
    signature
        .iter()
        .map(|strength| strength_label(*strength))
        .collect::<Vec<_>>()
        .join(" + ")
}

fn strength_label(strength: MembershipStrength) -> &'static str {
    match strength {
        MembershipStrength::Incidental => "Incidental",
        MembershipStrength::Substantive => "Substantive",
        MembershipStrength::Central => "Central",
    }
}

#[derive(serde::Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SessionEnvelope<T> {
    schema_version: u32,
    state_sha256: String,
    session: T,
}

fn load_session<T>(path: &Path) -> Result<Option<T>>
where
    T: DeserializeOwned + Serialize,
{
    if !path.exists() {
        return Ok(None);
    }
    let envelope: SessionEnvelope<T> = load_json(path)?;
    if envelope.schema_version != 1 {
        return Err(Error::ExperimentState(format!(
            "review session `{}` has an unsupported schema",
            path.display()
        )));
    }
    let expected = value_sha256(&envelope.session)?;
    if envelope.state_sha256 != expected {
        return Err(Error::ExperimentState(format!(
            "review session `{}` failed its state hash",
            path.display()
        )));
    }
    Ok(Some(envelope.session))
}

fn save_session<T: Serialize>(path: &Path, session: &T) -> Result<()> {
    let envelope = SessionEnvelope {
        schema_version: 1,
        state_sha256: value_sha256(session)?,
        session,
    };
    replace_json(path, &envelope)
}

fn load_json<T: DeserializeOwned>(path: &Path) -> Result<T> {
    let mut bytes = Vec::new();
    File::open(path)
        .and_then(|mut file| file.read_to_end(&mut bytes))
        .map_err(|source| io_error("read", path, source))?;
    serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })
}

fn value_sha256<T: Serialize>(value: &T) -> Result<String> {
    let bytes = serde_json::to_vec(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: "<reference-review-state-identity>".into(),
        source,
    })?;
    Ok(format!("{:x}", Sha256::digest(bytes)))
}

fn publish_json<T>(path: &Path, value: &T) -> Result<()>
where
    T: DeserializeOwned + Serialize + PartialEq,
{
    if path.exists() {
        let existing: T = load_json(path)?;
        if &existing == value {
            return Ok(());
        }
        return Err(Error::ArtifactExists(path.to_owned()));
    }
    write_json_atomic(path, value, false)
}

fn replace_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    write_json_atomic(path, value, true)
}

fn write_json_atomic<T: Serialize>(path: &Path, value: &T, replace: bool) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    prepare_directory(parent)?;
    if !replace && path.exists() {
        return Err(Error::ArtifactExists(path.to_owned()));
    }
    let filename = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = parent.join(format!(".{filename}.{}.tmp", std::process::id()));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    let mut options = OpenOptions::new();
    options.create_new(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    let mut writer = BufWriter::new(file);
    let result = (|| {
        serde_json::to_writer_pretty(&mut writer, value).map_err(|source| Error::Manifest {
            operation: "encode",
            path: temporary.clone(),
            source,
        })?;
        writer
            .write_all(b"\n")
            .and_then(|()| writer.flush())
            .map_err(|source| io_error("write", &temporary, source))?;
        writer
            .get_ref()
            .sync_all()
            .map_err(|source| io_error("sync", &temporary, source))?;
        if replace {
            fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
        } else {
            match fs::hard_link(&temporary, path) {
                Ok(()) => {
                    fs::remove_file(&temporary)
                        .map_err(|source| io_error("remove", &temporary, source))?;
                }
                Err(source) if source.kind() == io::ErrorKind::AlreadyExists => {
                    return Err(Error::ArtifactExists(path.to_owned()));
                }
                Err(source) => return Err(io_error("publish", path, source)),
            }
        }
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", parent, source))
    })();
    if result.is_err() && temporary.exists() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

fn prepare_directory(path: &Path) -> Result<()> {
    let mut builder = fs::DirBuilder::new();
    builder.recursive(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::DirBuilderExt as _;
        builder.mode(0o700);
    }
    builder
        .create(path)
        .map_err(|source| io_error("create", path, source))
}

fn acquire_session_lock(session_path: &Path) -> Result<File> {
    let parent = session_path.parent().unwrap_or_else(|| Path::new("."));
    prepare_directory(parent)?;
    let filename = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    let lock_path = parent.join(format!(".{filename}.lock"));
    let mut options = OpenOptions::new();
    options.create(true).read(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(&lock_path)
        .map_err(|source| io_error("open", &lock_path, source))?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "review session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &lock_path, source)),
    }
}
