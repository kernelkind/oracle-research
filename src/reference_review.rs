//! Durable approval runners for the 64-note selection and reference hierarchy.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::path::Path;

use serde::de::DeserializeOwned;
use serde::Deserialize;
use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::reference_map::{
    ApprovedHierarchy, ApprovedNoteSet, BroadNarrowRole, HierarchyDraft, HierarchyReviewDecision,
    HierarchyReviewSession, MembershipStrength, NoteProposal, NoteReviewDecision,
    NoteReviewSession, PairMembership, ProposedNote, ReviewOutcome, SelectionSource, SubjectNode,
};
use crate::reference_tui::{
    ApprovalEvidence, ApprovalScreen, ApprovalTuiAction, ReferenceTerminal,
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
    interpretive_ambiguity: bool,
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
    if plan.schema_version != 2
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
                interpretive_ambiguity: planned.interpretive_ambiguity,
                contrast_pair: planned.contrast_pair,
                broad_narrow_pair: planned.broad_narrow_pair,
                niche_or_sparse_case: planned.niche_or_sparse_case,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let proposal = NoteProposal {
        schema_version: 2,
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
    save_session(session_path, &session)?;

    loop {
        if let Some(node_id) = session
            .reviewable_node_ids(&draft, &approved_notes)
            .first()
            .cloned()
        {
            let screen = hierarchy_screen(&draft, &approved_notes, &session, &node_id)?;
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
                        &node_id,
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

    let approved = draft
        .nodes
        .iter()
        .filter(|node| session.is_approved(&draft, &approved_notes, node.node_id.as_str()))
        .count();
    let rejected = draft
        .nodes
        .iter()
        .filter(|node| {
            session
                .current_decision(&draft, &approved_notes, node.node_id.as_str())
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
        })
        .count()
        + usize::from(
            session
                .current_focus_coverage_decision(&draft, &approved_notes)
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected),
        );
    if approved != draft.nodes.len() || !session.focus_coverage_is_approved(&draft, &approved_notes)
    {
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
    if note.interpretive_ambiguity {
        categories.push("Interpretive-ambiguity coverage case".to_owned());
    }
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
            annotation,
            body: format!(
                "Shown only to judge this relationship; reviewed separately at its own slot.\n\n{}",
                partner.content
            ),
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
        evidence,
    })
}

fn hierarchy_screen(
    draft: &HierarchyDraft,
    approved_notes: &ApprovedNoteSet,
    session: &HierarchyReviewSession,
    node_id: &str,
) -> Result<ApprovalScreen> {
    let node = draft
        .node(node_id)
        .ok_or_else(|| Error::ExperimentState(format!("hierarchy node {node_id} is missing")))?;
    let approved = draft
        .nodes
        .iter()
        .filter(|candidate| session.is_approved(draft, approved_notes, candidate.node_id.as_str()))
        .count();
    let rejected = draft
        .nodes
        .iter()
        .filter(|candidate| {
            session
                .current_decision(draft, approved_notes, candidate.node_id.as_str())
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
        })
        .count();
    let note_by_id = approved_notes
        .notes
        .iter()
        .map(|note| (note.note_id.as_str(), note.content.as_str()))
        .collect::<BTreeMap<_, _>>();
    let membership_inventory = note_membership_inventory(draft);
    let evidence = if node.is_leaf() {
        let mut memberships = node.memberships.iter().collect::<Vec<_>>();
        memberships.sort_by(|left, right| {
            right
                .strength
                .rank()
                .cmp(&left.strength.rank())
                .then_with(|| left.note_id.cmp(&right.note_id))
        });
        memberships
            .into_iter()
            .map(|membership| ApprovalEvidence {
                title: format!("Member note · {}", strength_label(membership.strength)),
                annotation: format!(
                    "Current leaf membership: {}",
                    strength_label(membership.strength)
                ),
                body: format!(
                    "Complete proposed map:\n{}\n\nNote:\n{}",
                    format_note_memberships(&membership_inventory[membership.note_id.as_str()]),
                    note_by_id[membership.note_id.as_str()]
                ),
            })
            .collect()
    } else {
        let children = node
            .children
            .iter()
            .map(|child_id| {
                draft.node(child_id).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "hierarchy node {} names missing child {child_id}",
                        node.node_id
                    ))
                })
            })
            .collect::<Result<Vec<_>>>()?;
        let overview = children
            .iter()
            .map(|child| format!("• {}\n  {}", child.label, child.scope))
            .collect::<Vec<_>>()
            .join("\n\n");
        let mut evidence = Vec::with_capacity(children.len() + 1);
        evidence.push(ApprovalEvidence {
            title: "All child subjects".to_owned(),
            annotation: format!(
                "{} choices · review the complete sibling set first",
                children.len()
            ),
            body: overview,
        });
        evidence.extend(
            children
                .into_iter()
                .map(|child| {
                    let note_ids = representative_note_ids(draft, child, 3)?;
                    let examples = note_ids
                        .into_iter()
                        .filter_map(|note_id| note_by_id.get(note_id.as_str()).copied())
                        .map(|content| format!("• {content}"))
                        .collect::<Vec<_>>()
                        .join("\n\n");
                    Ok(ApprovalEvidence {
                        title: format!("Child subject · {}", child.label),
                        annotation: child.scope.clone(),
                        body: if examples.is_empty() {
                            child.scope.clone()
                        } else {
                            format!(
                                "{}\n\nRepresentative member notes:\n\n{examples}",
                                child.scope
                            )
                        },
                    })
                })
                .collect::<Result<Vec<_>>>()?,
        );
        evidence
    };
    let title = if node.node_id == draft.root_node_id {
        "Root choices".to_owned()
    } else if node.is_leaf() {
        format!("Leaf subject · {}", node.label)
    } else {
        format!("Parent subject · {}", node.label)
    };
    Ok(ApprovalScreen {
        heading: format!(
            "Hierarchy review · {approved} approved · {rejected} rejected · {} total",
            draft.nodes.len()
        ),
        title,
        scope: node.scope.clone(),
        approve_label: "Approve — no concrete problem".to_owned(),
        reject_label: "Reject — explain the problem".to_owned(),
        evidence,
    })
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

fn representative_note_ids(
    draft: &HierarchyDraft,
    node: &SubjectNode,
    limit: usize,
) -> Result<Vec<String>> {
    if node.is_leaf() {
        let mut memberships = node.memberships.iter().collect::<Vec<_>>();
        memberships.sort_by(|left, right| {
            right
                .strength
                .rank()
                .cmp(&left.strength.rank())
                .then_with(|| left.note_id.cmp(&right.note_id))
        });
        return Ok(memberships
            .into_iter()
            .take(limit)
            .map(|membership| membership.note_id.clone())
            .collect());
    }

    let mut child_representatives = Vec::with_capacity(node.children.len());
    for child_id in &node.children {
        let child = draft.node(child_id).ok_or_else(|| {
            Error::ExperimentState(format!(
                "hierarchy node {} names missing child {child_id}",
                node.node_id
            ))
        })?;
        child_representatives.push(representative_note_ids(draft, child, limit)?);
    }

    let mut note_ids = Vec::with_capacity(limit);
    let mut seen = BTreeSet::new();
    let maximum_child_notes = child_representatives
        .iter()
        .map(Vec::len)
        .max()
        .unwrap_or(0);
    for index in 0..maximum_child_notes {
        for representatives in &child_representatives {
            let Some(note_id) = representatives.get(index) else {
                continue;
            };
            if seen.insert(note_id.as_str()) {
                note_ids.push(note_id.clone());
                if note_ids.len() == limit {
                    return Ok(note_ids);
                }
            }
        }
    }
    Ok(note_ids)
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
