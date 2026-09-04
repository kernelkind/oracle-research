//! Mask-only prompt review: present fixed input and record human decisions.

use std::collections::{BTreeMap, BTreeSet};
use std::io;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::reference_map::ReviewOutcome;
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
};
use crate::review_state::{
    acquire_session_lock, load_json, load_session, save_session, value_sha256,
};
use crate::snapshot::{Error, Result, io_error};
use crate::sse_mask_review::{ProposedMaskFragment, highlighted_note, resolve_fragments};

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskReviewBatch {
    schema_version: u32,
    batch_id: String,
    items: Vec<MaskReviewItem>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskReviewItem {
    item_id: String,
    note_id: String,
    subject: String,
    note: String,
    fragments: Vec<ProposedMaskFragment>,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum MaskDecision {
    Approved,
    Rejected,
    Skipped,
}

#[derive(Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskDecisionRecord {
    outcome: Option<MaskDecision>,
    comment: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskReviewSession {
    schema_version: u32,
    batch_sha256: String,
    decisions: BTreeMap<String, MaskDecisionRecord>,
}

#[derive(Debug, Eq, PartialEq)]
pub enum MaskPromptReviewOutcome {
    Paused,
    Completed {
        approved: usize,
        rejected: usize,
        skipped: usize,
    },
}

/// Review masks independently of generation, subject approval, or downstream encoding.
pub fn run_mask_prompt_review(
    batch_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    mut review: impl FnMut(ApprovalScreen, String) -> io::Result<ApprovalTuiAction>,
) -> Result<MaskPromptReviewOutcome> {
    let batch_path = batch_path.as_ref();
    let session_path = session_path.as_ref();
    if std::fs::canonicalize(batch_path)
        .ok()
        .is_some_and(|path| std::fs::canonicalize(session_path).ok().as_ref() == Some(&path))
    {
        return Err(Error::ExperimentState(
            "mask input and review session must be different files".into(),
        ));
    }
    let batch: MaskReviewBatch = load_json(batch_path)?;
    if batch.schema_version != 1 || batch.batch_id.trim().is_empty() || batch.items.is_empty() {
        return Err(Error::ExperimentState("invalid mask review batch".into()));
    }
    let mut ids = BTreeSet::new();
    let mut notes = BTreeMap::new();
    let mut highlights = Vec::with_capacity(batch.items.len());
    for item in &batch.items {
        if item.item_id.trim().is_empty()
            || item.note_id.trim().is_empty()
            || item.subject.trim().is_empty()
            || item.note.trim().is_empty()
            || !ids.insert(item.item_id.as_str())
        {
            return Err(Error::ExperimentState(
                "empty mask review field or duplicate item ID".into(),
            ));
        }
        if notes
            .insert(&item.note_id, &item.note)
            .is_some_and(|note| note != &item.note)
        {
            return Err(Error::ExperimentState(
                "conflicting source text for one note ID".into(),
            ));
        }
        let spans = resolve_fragments(&item.fragments, &item.note, &item.note_id, &item.item_id)?;
        highlights.push(highlighted_note(&item.note, &spans));
    }
    let batch_sha256 = value_sha256(&batch)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = match load_session::<MaskReviewSession>(session_path)? {
        Some(session) => {
            if session.schema_version != 1
                || session.batch_sha256 != batch_sha256
                || session
                    .decisions
                    .keys()
                    .map(String::as_str)
                    .collect::<BTreeSet<_>>()
                    != ids
            {
                return Err(Error::ExperimentState(
                    "review session belongs to a different mask batch".into(),
                ));
            }
            session
        }
        None => MaskReviewSession {
            schema_version: 1,
            batch_sha256,
            decisions: batch
                .items
                .iter()
                .map(|item| (item.item_id.clone(), MaskDecisionRecord::default()))
                .collect(),
        },
    };
    save_session(session_path, &session)?;
    for (index, item) in batch.items.iter().enumerate() {
        while session.decisions[&item.item_id].outcome.is_none() {
            let screen = ApprovalScreen {
                heading: format!("Mask review · {} of {} · {}", index + 1, batch.items.len(), item.item_id),
                title: Some(item.subject.clone()),
                scope: "Does this mask express the whole subject without including text belonging only to something else?".into(),
                approve_label: "Approve".into(),
                reject_label: "Disapprove".into(),
                rejection_help: String::new(),
                guidance: Some(ApprovalGuidance {
                    title: "Mask review".into(),
                    body: "Review only the highlighted mask; the subject is fixed. The complete note supplies context.\n\nCheck for missing subject-bearing text and text belonging only to another subject. More than one mask can be reasonable; the shortest possible selection is not required.\n\nA or R records a decision. C edits an optional comment. S skips this mask. Ctrl-C saves and exits; you do not need to finish the batch.".into(),
                }),
                evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
                    title: "Note".into(),
                    annotation: String::new(),
                    body: highlights[index].clone(),
                }]),
            };
            let action = review(screen, session.decisions[&item.item_id].comment.clone())
                .map_err(|source| io_error("review masks from", batch_path, source))?;
            let decision = session
                .decisions
                .get_mut(&item.item_id)
                .expect("validated item ID");
            match action {
                ApprovalTuiAction::Pause => return Ok(MaskPromptReviewOutcome::Paused),
                ApprovalTuiAction::None => {
                    return Err(Error::ExperimentState(
                        "mask review returned without an action".into(),
                    ));
                }
                ApprovalTuiAction::SaveComment { comment } => decision.comment = comment,
                ApprovalTuiAction::Submit { outcome, comment } => {
                    decision.outcome = Some(match outcome {
                        ReviewOutcome::Approved => MaskDecision::Approved,
                        ReviewOutcome::Rejected => MaskDecision::Rejected,
                    });
                    decision.comment = comment;
                }
                ApprovalTuiAction::Skip { comment } => {
                    decision.outcome = Some(MaskDecision::Skipped);
                    decision.comment = comment;
                }
            }
            save_session(session_path, &session)?;
        }
    }
    let (mut approved, mut rejected, mut skipped) = (0, 0, 0);
    for decision in session.decisions.values() {
        match decision.outcome {
            Some(MaskDecision::Approved) => approved += 1,
            Some(MaskDecision::Rejected) => rejected += 1,
            Some(MaskDecision::Skipped) => skipped += 1,
            None => unreachable!("all items were reviewed"),
        }
    }
    Ok(MaskPromptReviewOutcome::Completed {
        approved,
        rejected,
        skipped,
    })
}
