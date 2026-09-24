//! Review generated titles against their complete, unchanged member masks.

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

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TitleReviewBatch {
    schema_version: u32,
    batch_id: String,
    candidate_version: String,
    baseline_version: String,
    items: Vec<TitleReviewItem>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TitleReviewItem {
    item_id: String,
    candidate_title: String,
    baseline_title: String,
    instances: Vec<TitleReviewInstance>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    assessment: Option<String>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TitleReviewInstance {
    instance: String,
    fragments: Vec<String>,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum TitleDecision {
    Approved,
    Rejected,
    Skipped,
}

#[derive(Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TitleDecisionRecord {
    outcome: Option<TitleDecision>,
    comment: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TitleReviewSession {
    schema_version: u32,
    batch_sha256: String,
    current_item: Option<String>,
    decisions: BTreeMap<String, TitleDecisionRecord>,
}

/// Supplementary assistant text, separate from the reviewed batch and user decisions.
#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TitleReviewComment {
    pub assessment_summary: String,
    pub comment: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TitleReviewComments {
    schema_version: u32,
    batch_sha256: String,
    comments: BTreeMap<String, TitleReviewComment>,
}

#[derive(Debug, Eq, PartialEq)]
pub enum TitlePromptReviewOutcome {
    Paused,
    Completed {
        approved: usize,
        rejected: usize,
        skipped: usize,
    },
}

impl TitleReviewBatch {
    fn validate(&self) -> Result<BTreeSet<&str>> {
        if self.schema_version != 1
            || self.batch_id.trim().is_empty()
            || self.candidate_version.trim().is_empty()
            || self.baseline_version.trim().is_empty()
            || self.items.is_empty()
        {
            return Err(Error::ExperimentState("invalid title review batch".into()));
        }
        let mut ids = BTreeSet::new();
        for item in &self.items {
            if item.item_id.trim().is_empty()
                || item.candidate_title.trim().is_empty()
                || item.baseline_title.trim().is_empty()
                || item
                    .assessment
                    .as_ref()
                    .is_some_and(|text| text.trim().is_empty())
                || item.instances.is_empty()
                || !ids.insert(item.item_id.as_str())
            {
                return Err(Error::ExperimentState(
                    "empty title review field or duplicate item ID".into(),
                ));
            }
            let mut instances = BTreeSet::new();
            for instance in &item.instances {
                if instance.instance.trim().is_empty()
                    || !instances.insert(instance.instance.as_str())
                    || instance.fragments.is_empty()
                    || instance.fragments.iter().any(|text| text.trim().is_empty())
                {
                    return Err(Error::ExperimentState(
                        "empty title review mask or duplicate instance ID".into(),
                    ));
                }
            }
        }
        Ok(ids)
    }

    fn screen(&self, index: usize, decision: &TitleDecisionRecord) -> ApprovalScreen {
        let item = &self.items[index];
        let status = match decision.outcome {
            None => "Not reviewed",
            Some(TitleDecision::Approved) => "Approved",
            Some(TitleDecision::Rejected) => "Disapproved",
            Some(TitleDecision::Skipped) => "Skipped",
        };
        let masks = item
            .instances
            .iter()
            .map(|instance| {
                let fragments = instance
                    .fragments
                    .iter()
                    .map(|fragment| format!("⟦{fragment}⟧"))
                    .collect::<Vec<_>>()
                    .join(" ");
                format!("{}: {fragments}", instance.instance)
            })
            .collect::<Vec<_>>()
            .join(if item.assessment.is_some() {
                "\n\n"
            } else {
                "\n"
            });
        if let Some(assessment) = &item.assessment {
            return ApprovalScreen {
                heading: format!(
                    "{} of {} · {} · {} · {status}",
                    index + 1,
                    self.items.len(),
                    item.item_id,
                    self.candidate_version
                ),
                title: Some(item.candidate_title.clone()),
                scope: "Does this title fit every mask?".into(),
                approve_label: "Approve".into(),
                reject_label: "Reject".into(),
                rejection_help: String::new(),
                guidance: Some(ApprovalGuidance {
                    title: "Compare titles".into(),
                    body: format!(
                        "{} candidate — complete raw response:\n{}\n\n{} baseline — context only:\n{}\n\nMy assessment: {}\n\nOnly your A/R/S choice records a decision. B or Esc returns to the masks.",
                        self.candidate_version,
                        item.candidate_title,
                        self.baseline_version,
                        item.baseline_title,
                        assessment
                    ),
                }),
                evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
                    title: "Masks".into(),
                    annotation: format!("My assessment: {assessment}"),
                    body: masks,
                }]),
            };
        }
        ApprovalScreen {
            heading: format!(
                "Title review · {} of {} · {} · {status}",
                index + 1,
                self.items.len(),
                item.item_id
            ),
            // Keep both raw titles in the scrollable pane, including long responses.
            title: None,
            scope: format!(
                "Does the {} title describe the subject shared by every instance, with all its qualifying details supported? Judge only {}.",
                self.candidate_version, self.candidate_version
            ),
            approve_label: format!("Approve {} title", self.candidate_version),
            reject_label: format!("Disapprove {} title", self.candidate_version),
            rejection_help: String::new(),
            guidance: Some(ApprovalGuidance {
                title: "Title review".into(),
                body: format!(
                    "Review only the {} candidate title. The {} baseline is context, not a second question. Each V-ID identifies one original mask; brackets preserve its separate fragments. Repeated masks remain separate instances.\n\nA or R records or replaces the candidate title's decision. C edits an optional comment; Enter saves it. S records a skip. Left/right navigates all cards, including reviewed cards; up/down and Page Up/Down scroll the complete titles and masks. Ctrl-C exits with saved decisions, comments and the current card. Run the same command to resume; --start-at can reopen a completed card.",
                    self.candidate_version, self.baseline_version
                ),
            }),
            evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
                title: "Title and exact member masks".into(),
                annotation: String::new(),
                body: format!(
                    "{} title under review:\n{}\n\n{} baseline — context only, not being approved:\n{}\n\nExact member masks:\n{masks}",
                    self.candidate_version,
                    item.candidate_title,
                    self.baseline_version,
                    item.baseline_title
                ),
            }]),
        }
    }
}

/// Review candidate titles with durable decisions and baseline context.
/// `start_at` explicitly reopens any card, including an already reviewed card.
pub fn run_title_prompt_review(
    batch_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    start_at: Option<&str>,
    mut review: impl FnMut(ApprovalScreen, String) -> io::Result<ApprovalTuiAction>,
) -> Result<TitlePromptReviewOutcome> {
    run_title_prompt_review_with_comments(
        batch_path,
        session_path,
        start_at,
        None,
        |screen, comment, _| review(screen, comment),
    )
}

/// Load optional assistant comments without changing the batch identity or decisions.
/// Saved approval applies to the original reviewed batch, not supplementary comments.
pub fn run_title_prompt_review_with_comments(
    batch_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    start_at: Option<&str>,
    comments_path: Option<&Path>,
    mut review: impl FnMut(
        ApprovalScreen,
        String,
        Option<&TitleReviewComment>,
    ) -> io::Result<ApprovalTuiAction>,
) -> Result<TitlePromptReviewOutcome> {
    let batch_path = batch_path.as_ref();
    let session_path = session_path.as_ref();
    if std::fs::canonicalize(batch_path)
        .ok()
        .is_some_and(|path| std::fs::canonicalize(session_path).ok().as_ref() == Some(&path))
    {
        return Err(Error::ExperimentState(
            "title input and review session must be different files".into(),
        ));
    }
    let batch: TitleReviewBatch = load_json(batch_path)?;
    let ids = batch.validate()?;
    if let Some(id) = start_at
        && !ids.contains(id)
    {
        return Err(Error::ExperimentState(format!(
            "unknown title review item {id}"
        )));
    }
    let batch_sha256 = value_sha256(&batch)?;
    let comments = comments_path
        .map(load_json::<TitleReviewComments>)
        .transpose()?;
    if let Some(comments) = &comments
        && (comments.schema_version != 1
            || comments.batch_sha256 != batch_sha256
            || comments.comments.iter().any(|(id, comment)| {
                !ids.contains(id.as_str())
                    || comment.assessment_summary.trim().is_empty()
                    || comment.comment.trim().is_empty()
            }))
    {
        return Err(Error::ExperimentState(
            "invalid title review comments or comments belong to a different title batch".into(),
        ));
    }
    if let Some(comments) = &comments
        && let Some(item) = batch
            .items
            .iter()
            .find(|item| comments.comments.contains_key(&item.item_id) && item.assessment.is_none())
    {
        return Err(Error::ExperimentState(format!(
            "comments require an assessed title review item: {}",
            item.item_id
        )));
    }
    let _lock = acquire_session_lock(session_path)?;
    let mut session = match load_session::<TitleReviewSession>(session_path)? {
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
                    "review session belongs to a different title batch".into(),
                ));
            }
            if session
                .current_item
                .as_deref()
                .is_some_and(|id| !ids.contains(id))
                || (session.current_item.is_none()
                    && session
                        .decisions
                        .values()
                        .any(|record| record.outcome.is_none()))
            {
                return Err(Error::ExperimentState(
                    "title review session has an invalid current item".into(),
                ));
            }
            session
        }
        None => TitleReviewSession {
            schema_version: 1,
            batch_sha256,
            current_item: Some(batch.items[0].item_id.clone()),
            decisions: batch
                .items
                .iter()
                .map(|item| (item.item_id.clone(), TitleDecisionRecord::default()))
                .collect(),
        },
    };
    if let Some(id) = start_at {
        session.current_item = Some(id.to_owned());
    }
    save_session(session_path, &session)?;
    while let Some(id) = &session.current_item {
        let index = batch
            .items
            .iter()
            .position(|item| &item.item_id == id)
            .expect("validated item ID");
        let decision = &session.decisions[id];
        let action = review(
            batch.screen(index, decision),
            decision.comment.clone(),
            comments
                .as_ref()
                .and_then(|comments| comments.comments.get(id)),
        )
        .map_err(|source| io_error("review titles from", batch_path, source))?;
        let advance = matches!(
            action,
            ApprovalTuiAction::Submit { .. } | ApprovalTuiAction::Skip { .. }
        );
        let decision = session.decisions.get_mut(id).expect("validated item ID");
        match action {
            ApprovalTuiAction::Pause => return Ok(TitlePromptReviewOutcome::Paused),
            ApprovalTuiAction::PreviousItem => {
                session.current_item = Some(
                    batch.items[(index + batch.items.len() - 1) % batch.items.len()]
                        .item_id
                        .clone(),
                );
            }
            ApprovalTuiAction::NextItem => {
                session.current_item =
                    Some(batch.items[(index + 1) % batch.items.len()].item_id.clone());
            }
            ApprovalTuiAction::None => {
                return Err(Error::ExperimentState(
                    "title review returned without an action".into(),
                ));
            }
            ApprovalTuiAction::SaveComment { comment } => decision.comment = comment,
            ApprovalTuiAction::Submit { outcome, comment } => {
                decision.outcome = Some(match outcome {
                    ReviewOutcome::Approved => TitleDecision::Approved,
                    ReviewOutcome::Rejected => TitleDecision::Rejected,
                });
                decision.comment = comment;
            }
            ApprovalTuiAction::Skip { comment } => {
                decision.outcome = Some(TitleDecision::Skipped);
                decision.comment = comment;
            }
        }
        if advance {
            session.current_item = (1..=batch.items.len())
                .map(|offset| &batch.items[(index + offset) % batch.items.len()].item_id)
                .find(|id| session.decisions[*id].outcome.is_none())
                .cloned();
        }
        save_session(session_path, &session)?;
    }
    let (mut approved, mut rejected, mut skipped) = (0, 0, 0);
    for decision in session.decisions.values() {
        match decision.outcome {
            Some(TitleDecision::Approved) => approved += 1,
            Some(TitleDecision::Rejected) => rejected += 1,
            Some(TitleDecision::Skipped) => skipped += 1,
            None => unreachable!("all cards have decisions"),
        }
    }
    Ok(TitlePromptReviewOutcome::Completed {
        approved,
        rejected,
        skipped,
    })
}
