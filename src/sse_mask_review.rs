//! Source-bound generation proposals and durable human review for SSE subjects and masks.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Padding, Paragraph, Wrap};
use serde::{Deserialize, Serialize};

use crate::artifact::hash_file;
use crate::reference_map::ReviewOutcome;
use crate::reference_review::ApprovalUi;
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, border_style,
    centered, has_command_modifier, is_control_c_event, render_scrollable_panel, render_too_small,
    secondary_style, terminal_safe,
};
use crate::review_state::{
    acquire_session_lock, load_json, load_session, publish_json, save_session, value_sha256,
};
use crate::snapshot::{Error, Result, io_error};

const NOTE_SET_SCHEMA_VERSION: u32 = 2;
const PROPOSAL_SCHEMA_VERSION: u32 = 2;
const REVIEW_SESSION_SCHEMA_VERSION: u32 = 2;
const APPROVED_SCHEMA_VERSION: u32 = 2;
const PAGE_LINES: u16 = 10;
const SUBJECT_INSTRUCTION: &str = "Enumerate every atomic subject explicitly and substantively discussed in the provided text.\n\nAn atomic subject is the smallest coherent semantic idea that remains meaningful as a distinct focus.\n\n<RAW NOTE>\n\nReturn only a JSON array of subject strings.";
const MASK_INSTRUCTION: &str = "Mask only the narrowest portion or portions of the provided text that directly express the provided atomic subject.\n\nAtomic subject:\n<SUBJECT>\n\nText:\n<RAW NOTE>\n\nReturn only a JSON array of exact substrings copied from the text, in source order. If the subject is not expressed, return \"unsupported\".";
const TAKEAWAY_INSTRUCTION: &str = "This text is a social media post. Identify each substantive point the user communicates. Summarize every independent point as a separate, concise takeaway in your own words. Combine details when they jointly express one point. Ground each takeaway in the text itself.\n\nReturn only a JSON array of strings.";
const TAKEAWAY_MASK_INSTRUCTION: &str = "Mask only the narrowest portion or portions of the provided text that directly express the provided takeaway.\n\nTakeaway:\n<TAKEAWAY>\n\nText:\n<RAW NOTE>\n\nReturn only a JSON array of exact substrings copied from the text, in source order. If the takeaway is not expressed, return \"unsupported\".";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BoundFile {
    path: String,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FrozenNoteSetInvariants {
    note_count: usize,
    unique_note_count: usize,
    unique_author_count: usize,
    required_split: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FrozenNoteSet {
    schema_version: u32,
    status: String,
    source: BoundFile,
    note_ids: Vec<String>,
    invariants: FrozenNoteSetInvariants,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum MaskGenerationStatus {
    Masked,
    Unsupported,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedMaskFragment {
    pub text: String,
    pub occurrence: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedSubjectMask {
    pub subject_id: String,
    pub label: String,
    status: MaskGenerationStatus,
    pub fragments: Vec<ProposedMaskFragment>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedNoteSubjects {
    pub note_id: String,
    pub subjects: Vec<ProposedSubjectMask>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct SubjectMaskProposal {
    schema_version: u32,
    proposal_id: String,
    note_set: BoundFile,
    subject_instruction: String,
    mask_instruction: String,
    notes: Vec<ProposedNoteSubjects>,
}

#[derive(Clone, Debug)]
struct SourceNote {
    pubkey: String,
    content: String,
}

#[derive(Clone, Debug)]
struct VerifiedSubjectMask {
    proposal: ProposedSubjectMask,
    spans: Vec<(usize, usize)>,
}

#[derive(Clone, Debug)]
struct VerifiedNoteSubjects {
    note_id: String,
    note: SourceNote,
    subjects: Vec<VerifiedSubjectMask>,
}

#[derive(Clone, Debug)]
pub struct VerifiedSubjectMaskProposal {
    proposal: SubjectMaskProposal,
    note_set_sha256: String,
    notes: Vec<VerifiedNoteSubjects>,
}

/// One verified subject mask ready for model input preparation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedSubjectEncodingMask {
    pub subject_id: String,
    pub label: String,
    pub fragments: Vec<ProposedMaskFragment>,
    pub byte_spans: Vec<(usize, usize)>,
}

/// One source-bound note and all of its ordered verified subject masks.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedSubjectEncodingNote {
    pub note_id: String,
    pub content: String,
    pub subjects: Vec<VerifiedSubjectEncodingMask>,
}

impl VerifiedSubjectMaskProposal {
    pub fn note_count(&self) -> usize {
        self.notes.len()
    }

    pub fn subject_count(&self) -> usize {
        self.notes.iter().map(|note| note.subjects.len()).sum()
    }

    /// SHA-256 of the frozen note set bound by this verified proposal.
    pub fn note_set_sha256(&self) -> &str {
        &self.note_set_sha256
    }

    /// Return the complete source text and ordered masks needed by an encoder.
    pub fn encoding_notes(&self) -> Vec<VerifiedSubjectEncodingNote> {
        self.notes
            .iter()
            .map(|note| VerifiedSubjectEncodingNote {
                note_id: note.note_id.clone(),
                content: note.note.content.clone(),
                subjects: note
                    .subjects
                    .iter()
                    .map(|subject| VerifiedSubjectEncodingMask {
                        subject_id: subject.proposal.subject_id.clone(),
                        label: subject.proposal.label.clone(),
                        fragments: subject.proposal.fragments.clone(),
                        byte_spans: subject.spans.clone(),
                    })
                    .collect(),
            })
            .collect()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SubjectReviewChoice {
    pub subject_id: String,
    pub label: String,
    pub outcome: Option<ReviewOutcome>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SubjectReviewScreen {
    pub heading: String,
    pub note: String,
    pub choices: Vec<SubjectReviewChoice>,
    pub selected_index: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SubjectReviewAction {
    None,
    Decide {
        subject_id: String,
        outcome: ReviewOutcome,
        comment: String,
    },
    Complete,
    Missing {
        comment: String,
    },
    Pause,
}

pub trait SubjectMaskReviewUi: ApprovalUi {
    fn review_subjects(&mut self, screen: SubjectReviewScreen) -> io::Result<SubjectReviewAction>;
}

impl SubjectMaskReviewUi for ReferenceTerminal {
    fn review_subjects(&mut self, screen: SubjectReviewScreen) -> io::Result<SubjectReviewAction> {
        self.run_review_model(SubjectReviewTuiModel::new(screen))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReviewStage {
    Subjects,
    Masks,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SubjectMaskReviewRunOutcome {
    Paused,
    NeedsRevision {
        stage: ReviewStage,
        approved: usize,
        rejected: usize,
        missing_subject_notes: usize,
    },
    Approved,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewDecision {
    outcome: ReviewOutcome,
    comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredDecision {
    item_sha256: String,
    decision: ReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct SubjectMaskReviewSession {
    schema_version: u32,
    subject_decisions: BTreeMap<String, StoredDecision>,
    completeness_decisions: BTreeMap<String, StoredDecision>,
    mask_decisions: BTreeMap<String, StoredDecision>,
}

impl Default for SubjectMaskReviewSession {
    fn default() -> Self {
        Self {
            schema_version: REVIEW_SESSION_SCHEMA_VERSION,
            subject_decisions: BTreeMap::new(),
            completeness_decisions: BTreeMap::new(),
            mask_decisions: BTreeMap::new(),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ApprovedSubjectMaskSet {
    pub schema_version: u32,
    pub proposal_sha256: String,
    pub note_set_sha256: String,
    pub notes: Vec<ProposedNoteSubjects>,
}

pub fn load_verified_subject_mask_proposal(
    proposal_path: impl AsRef<Path>,
) -> Result<VerifiedSubjectMaskProposal> {
    let proposal_path = proposal_path.as_ref();
    let proposal: SubjectMaskProposal = load_json(proposal_path)?;
    if proposal.schema_version != PROPOSAL_SCHEMA_VERSION
        || proposal.proposal_id.trim().is_empty()
        || !is_lower_hex(&proposal.note_set.sha256, 64)
    {
        return invalid("subject-mask proposal schema, ID, or note-set identity is invalid");
    }
    if !uses_approved_generation_profile(&proposal.subject_instruction, &proposal.mask_instruction)
    {
        return invalid("subject-mask proposal does not use the approved generation prompts");
    }

    let note_set_path = resolve_relative(proposal_path, &proposal.note_set.path);
    if hash_file(&note_set_path)? != proposal.note_set.sha256 {
        return invalid(format!(
            "frozen note set `{}` does not match its proposal binding",
            note_set_path.display()
        ));
    }
    let note_set: FrozenNoteSet = load_json(&note_set_path)?;
    validate_note_set(&note_set)?;
    let source_notes = load_source_notes(&note_set, &note_set_path)?;
    if proposal.notes.len() != note_set.note_ids.len() {
        return invalid(format!(
            "proposal has {} notes, expected {}",
            proposal.notes.len(),
            note_set.note_ids.len()
        ));
    }

    let mut all_subject_ids = BTreeSet::new();
    let mut notes = Vec::with_capacity(proposal.notes.len());
    for (index, (proposed, expected_note_id)) in proposal
        .notes
        .iter()
        .zip(note_set.note_ids.iter())
        .enumerate()
    {
        if &proposed.note_id != expected_note_id {
            return invalid(format!(
                "proposal note {} does not match the frozen note order",
                index + 1
            ));
        }
        if proposed.subjects.is_empty() {
            return invalid(format!(
                "proposal note {} contains no generated subjects",
                proposed.note_id
            ));
        }
        let note = source_notes
            .get(proposed.note_id.as_str())
            .expect("validated note set IDs were loaded")
            .clone();
        let mut labels = BTreeSet::new();
        let mut subjects = Vec::with_capacity(proposed.subjects.len());
        for subject in &proposed.subjects {
            if !is_lower_hex(&subject.subject_id, 16)
                || subject.label.trim().is_empty()
                || !all_subject_ids.insert(subject.subject_id.as_str())
                || !labels.insert(subject.label.as_str())
            {
                return invalid(format!(
                    "proposal note {} has invalid or duplicate subject IDs or labels",
                    proposed.note_id
                ));
            }
            if subject.status == MaskGenerationStatus::Unsupported {
                return invalid(format!(
                    "mask agent returned unsupported for note {} subject `{}`",
                    proposed.note_id, subject.label
                ));
            }
            let spans = resolve_fragments(subject, &note.content, &proposed.note_id)?;
            subjects.push(VerifiedSubjectMask {
                proposal: subject.clone(),
                spans,
            });
        }
        notes.push(VerifiedNoteSubjects {
            note_id: proposed.note_id.clone(),
            note,
            subjects,
        });
    }

    Ok(VerifiedSubjectMaskProposal {
        proposal,
        note_set_sha256: hash_file(&note_set_path)?,
        notes,
    })
}

fn uses_approved_generation_profile(subject_instruction: &str, mask_instruction: &str) -> bool {
    (subject_instruction == SUBJECT_INSTRUCTION && mask_instruction == MASK_INSTRUCTION)
        || (subject_instruction == TAKEAWAY_INSTRUCTION
            && mask_instruction == TAKEAWAY_MASK_INSTRUCTION)
}

pub fn run_subject_mask_review(
    proposal_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    approved_path: impl AsRef<Path>,
    ui: &mut impl SubjectMaskReviewUi,
) -> Result<SubjectMaskReviewRunOutcome> {
    let proposal_path = proposal_path.as_ref();
    let session_path = session_path.as_ref();
    let approved_path = approved_path.as_ref();
    let proposal = load_verified_subject_mask_proposal(proposal_path)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = load_session::<SubjectMaskReviewSession>(session_path)?.unwrap_or_default();
    session.reconcile(&proposal)?;
    save_session(session_path, &session)?;

    while let Some(note_index) = session.next_subject_note(&proposal) {
        let screen = subject_screen(&proposal, &session, note_index)?;
        match ui
            .review_subjects(screen)
            .map_err(|source| io_error("run SSE subject review UI for", proposal_path, source))?
        {
            SubjectReviewAction::None => {
                return invalid("subject review UI returned without a decision");
            }
            SubjectReviewAction::Pause => return Ok(SubjectMaskReviewRunOutcome::Paused),
            SubjectReviewAction::Decide {
                subject_id,
                outcome,
                comment,
            } => {
                session.record_subject(
                    &proposal,
                    note_index,
                    &subject_id,
                    ReviewDecision { outcome, comment },
                )?;
                save_session(session_path, &session)?;
            }
            SubjectReviewAction::Complete => {
                session.record_completeness(
                    &proposal,
                    note_index,
                    ReviewDecision {
                        outcome: ReviewOutcome::Approved,
                        comment: String::new(),
                    },
                )?;
                save_session(session_path, &session)?;
            }
            SubjectReviewAction::Missing { comment } => {
                session.record_completeness(
                    &proposal,
                    note_index,
                    ReviewDecision {
                        outcome: ReviewOutcome::Rejected,
                        comment,
                    },
                )?;
                save_session(session_path, &session)?;
            }
        }
    }

    let (approved_subjects, rejected_subjects) = session.subject_decision_counts(&proposal);
    let missing_notes = session.rejected_completeness_count(&proposal);
    if rejected_subjects + missing_notes != 0 {
        return Ok(SubjectMaskReviewRunOutcome::NeedsRevision {
            stage: ReviewStage::Subjects,
            approved: approved_subjects,
            rejected: rejected_subjects,
            missing_subject_notes: missing_notes,
        });
    }
    if !session.all_subjects_complete(&proposal) {
        return invalid("subject review ended without complete approved subject lists");
    }

    while let Some((note_index, subject_index, global_index)) = session.next_mask(&proposal) {
        let screen = mask_screen(&proposal, &session, note_index, subject_index, global_index)?;
        match ui
            .review(screen)
            .map_err(|source| io_error("run SSE mask review UI for", proposal_path, source))?
        {
            ApprovalTuiAction::None => {
                return invalid("mask review UI returned without a decision");
            }
            ApprovalTuiAction::Pause => return Ok(SubjectMaskReviewRunOutcome::Paused),
            ApprovalTuiAction::Submit { outcome, comment } => {
                session.record_mask(
                    &proposal,
                    note_index,
                    subject_index,
                    ReviewDecision { outcome, comment },
                )?;
                save_session(session_path, &session)?;
            }
        }
    }

    let (approved_masks, rejected_masks) = session.mask_decision_counts(&proposal);
    if rejected_masks != 0 {
        return Ok(SubjectMaskReviewRunOutcome::NeedsRevision {
            stage: ReviewStage::Masks,
            approved: approved_masks,
            rejected: rejected_masks,
            missing_subject_notes: 0,
        });
    }
    let artifact = ApprovedSubjectMaskSet::from_review(&proposal, &session)?;
    publish_json(approved_path, &artifact)?;
    Ok(SubjectMaskReviewRunOutcome::Approved)
}

impl SubjectMaskReviewSession {
    fn reconcile(&mut self, proposal: &VerifiedSubjectMaskProposal) -> Result<()> {
        if self.schema_version != REVIEW_SESSION_SCHEMA_VERSION {
            return invalid(format!(
                "subject-mask review session schema {} is unsupported",
                self.schema_version
            ));
        }
        let subject_identities = proposal
            .notes
            .iter()
            .flat_map(|note| {
                note.subjects.iter().map(move |subject| {
                    Ok((subject_key(note, subject), subject_identity(note, subject)?))
                })
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        let completeness_identities = proposal
            .notes
            .iter()
            .map(|note| Ok((note.note_id.clone(), completeness_identity(note)?)))
            .collect::<Result<BTreeMap<_, _>>>()?;
        let mask_identities = proposal
            .notes
            .iter()
            .flat_map(|note| {
                note.subjects.iter().map(move |subject| {
                    Ok((subject_key(note, subject), mask_identity(note, subject)?))
                })
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        retain_current(&mut self.subject_decisions, &subject_identities);
        retain_current(&mut self.completeness_decisions, &completeness_identities);
        retain_current(&mut self.mask_decisions, &mask_identities);
        Ok(())
    }

    fn subject_decision<'a>(
        &'a self,
        note: &VerifiedNoteSubjects,
        subject: &VerifiedSubjectMask,
    ) -> Option<&'a ReviewDecision> {
        decision_for(
            &self.subject_decisions,
            &subject_key(note, subject),
            subject_identity(note, subject).ok()?.as_str(),
        )
    }

    fn completeness_decision<'a>(
        &'a self,
        note: &VerifiedNoteSubjects,
    ) -> Option<&'a ReviewDecision> {
        decision_for(
            &self.completeness_decisions,
            &note.note_id,
            completeness_identity(note).ok()?.as_str(),
        )
    }

    fn mask_decision<'a>(
        &'a self,
        note: &VerifiedNoteSubjects,
        subject: &VerifiedSubjectMask,
    ) -> Option<&'a ReviewDecision> {
        decision_for(
            &self.mask_decisions,
            &subject_key(note, subject),
            mask_identity(note, subject).ok()?.as_str(),
        )
    }

    fn next_subject_note(&self, proposal: &VerifiedSubjectMaskProposal) -> Option<usize> {
        proposal.notes.iter().enumerate().find_map(|(index, note)| {
            if note
                .subjects
                .iter()
                .any(|subject| self.subject_decision(note, subject).is_none())
            {
                return Some(index);
            }
            if note.subjects.iter().any(|subject| {
                self.subject_decision(note, subject)
                    .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
            }) {
                return None;
            }
            self.completeness_decision(note).is_none().then_some(index)
        })
    }

    fn record_subject(
        &mut self,
        proposal: &VerifiedSubjectMaskProposal,
        note_index: usize,
        subject_id: &str,
        decision: ReviewDecision,
    ) -> Result<()> {
        validate_decision(&decision, "a subject rejection")?;
        let note = proposal
            .notes
            .get(note_index)
            .ok_or_else(|| Error::ExperimentState(format!("note index {note_index} is absent")))?;
        let subject = note
            .subjects
            .iter()
            .find(|subject| subject.proposal.subject_id == subject_id)
            .ok_or_else(|| {
                Error::ExperimentState(format!(
                    "subject {subject_id} is absent from note {}",
                    note.note_id
                ))
            })?;
        self.subject_decisions.insert(
            subject_key(note, subject),
            StoredDecision {
                item_sha256: subject_identity(note, subject)?,
                decision,
            },
        );
        self.completeness_decisions.remove(&note.note_id);
        Ok(())
    }

    fn record_completeness(
        &mut self,
        proposal: &VerifiedSubjectMaskProposal,
        note_index: usize,
        decision: ReviewDecision,
    ) -> Result<()> {
        validate_decision(&decision, "a missing-subject report")?;
        let note = proposal
            .notes
            .get(note_index)
            .ok_or_else(|| Error::ExperimentState(format!("note index {note_index} is absent")))?;
        if !note.subjects.iter().all(|subject| {
            self.subject_decision(note, subject)
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
        }) {
            return invalid(
                "note completeness may be decided only after every subject is approved",
            );
        }
        self.completeness_decisions.insert(
            note.note_id.clone(),
            StoredDecision {
                item_sha256: completeness_identity(note)?,
                decision,
            },
        );
        Ok(())
    }

    fn record_mask(
        &mut self,
        proposal: &VerifiedSubjectMaskProposal,
        note_index: usize,
        subject_index: usize,
        decision: ReviewDecision,
    ) -> Result<()> {
        validate_decision(&decision, "a mask rejection")?;
        let note = proposal
            .notes
            .get(note_index)
            .ok_or_else(|| Error::ExperimentState(format!("note index {note_index} is absent")))?;
        let subject = note.subjects.get(subject_index).ok_or_else(|| {
            Error::ExperimentState(format!(
                "subject index {subject_index} is absent from note {}",
                note.note_id
            ))
        })?;
        self.mask_decisions.insert(
            subject_key(note, subject),
            StoredDecision {
                item_sha256: mask_identity(note, subject)?,
                decision,
            },
        );
        Ok(())
    }

    fn subject_decision_counts(&self, proposal: &VerifiedSubjectMaskProposal) -> (usize, usize) {
        proposal
            .notes
            .iter()
            .flat_map(|note| {
                note.subjects
                    .iter()
                    .filter_map(|subject| self.subject_decision(note, subject))
            })
            .fold((0, 0), count_decision)
    }

    fn rejected_completeness_count(&self, proposal: &VerifiedSubjectMaskProposal) -> usize {
        proposal
            .notes
            .iter()
            .filter(|note| {
                self.completeness_decision(note)
                    .is_some_and(|decision| decision.outcome == ReviewOutcome::Rejected)
            })
            .count()
    }

    fn all_subjects_complete(&self, proposal: &VerifiedSubjectMaskProposal) -> bool {
        proposal.notes.iter().all(|note| {
            note.subjects.iter().all(|subject| {
                self.subject_decision(note, subject)
                    .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
            }) && self
                .completeness_decision(note)
                .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
        })
    }

    fn next_mask(&self, proposal: &VerifiedSubjectMaskProposal) -> Option<(usize, usize, usize)> {
        let mut global_index = 0;
        for (note_index, note) in proposal.notes.iter().enumerate() {
            for (subject_index, subject) in note.subjects.iter().enumerate() {
                if self.mask_decision(note, subject).is_none() {
                    return Some((note_index, subject_index, global_index));
                }
                global_index += 1;
            }
        }
        None
    }

    fn mask_decision_counts(&self, proposal: &VerifiedSubjectMaskProposal) -> (usize, usize) {
        proposal
            .notes
            .iter()
            .flat_map(|note| {
                note.subjects
                    .iter()
                    .filter_map(|subject| self.mask_decision(note, subject))
            })
            .fold((0, 0), count_decision)
    }
}

impl ApprovedSubjectMaskSet {
    fn from_review(
        proposal: &VerifiedSubjectMaskProposal,
        session: &SubjectMaskReviewSession,
    ) -> Result<Self> {
        if !session.all_subjects_complete(proposal) {
            return invalid("cannot publish before every subject list is approved as complete");
        }
        let (approved, rejected) = session.mask_decision_counts(proposal);
        if approved != proposal.subject_count() || rejected != 0 {
            return invalid(format!(
                "cannot publish approved subject masks: {approved} approved and {rejected} rejected out of {}",
                proposal.subject_count()
            ));
        }
        Ok(Self {
            schema_version: APPROVED_SCHEMA_VERSION,
            proposal_sha256: value_sha256(&proposal.proposal)?,
            note_set_sha256: proposal.note_set_sha256.clone(),
            notes: proposal.proposal.notes.clone(),
        })
    }
}

fn subject_screen(
    proposal: &VerifiedSubjectMaskProposal,
    session: &SubjectMaskReviewSession,
    note_index: usize,
) -> Result<SubjectReviewScreen> {
    let note = proposal
        .notes
        .get(note_index)
        .ok_or_else(|| Error::ExperimentState(format!("note index {note_index} is absent")))?;
    let choices = note
        .subjects
        .iter()
        .map(|subject| SubjectReviewChoice {
            subject_id: subject.proposal.subject_id.clone(),
            label: subject.proposal.label.clone(),
            outcome: session
                .subject_decision(note, subject)
                .map(|decision| decision.outcome),
        })
        .collect::<Vec<_>>();
    let decided = choices
        .iter()
        .filter(|choice| choice.outcome.is_some())
        .count();
    let selected_index = choices
        .iter()
        .position(|choice| choice.outcome.is_none())
        .unwrap_or(0);
    Ok(SubjectReviewScreen {
        heading: format!(
            "SSE subject review · Note {} of {} · {decided} of {} decided",
            note_index + 1,
            proposal.note_count(),
            choices.len()
        ),
        note: note.note.content.clone(),
        choices,
        selected_index,
    })
}

fn mask_screen(
    proposal: &VerifiedSubjectMaskProposal,
    session: &SubjectMaskReviewSession,
    note_index: usize,
    subject_index: usize,
    global_index: usize,
) -> Result<ApprovalScreen> {
    let note = &proposal.notes[note_index];
    let subject = &note.subjects[subject_index];
    let (approved, rejected) = session.mask_decision_counts(proposal);
    Ok(ApprovalScreen {
        heading: format!(
            "SSE mask review · Subject {} of {} · {approved} approved · {rejected} rejected",
            global_index + 1,
            proposal.subject_count()
        ),
        title: subject.proposal.label.clone(),
        scope: "Does the highlight contain only the smallest text span or spans that directly express this subject?"
            .to_owned(),
        approve_label: "Correct".to_owned(),
        reject_label: "Incorrect — explain".to_owned(),
        rejection_help: "State exactly what text must be added, removed, or changed.".to_owned(),
        guidance: Some(ApprovalGuidance {
            title: "Masking rules".to_owned(),
            body: "The complete note remains visible to the encoder as context.\n\n\
                   Only text between ⟦ and ⟧ is pooled into this subject vector.\n\n\
                   The selected text must directly express this one subject. Correlated context and text belonging only to another subject stay unmasked.\n\n\
                   Discontinuous spans are allowed when every selected span directly expresses the same subject."
                .to_owned(),
        }),
        evidence: vec![ApprovalEvidence {
            title: "Note".to_owned(),
            annotation: String::new(),
            body: highlighted_note(&note.note.content, &subject.spans),
        }],
        evidence_layout: ApprovalEvidenceLayout::Paged,
    })
}

#[derive(Clone, Debug)]
enum PendingSubjectComment {
    Reject(String),
    Missing,
}

#[derive(Clone, Debug)]
pub struct SubjectReviewTuiModel {
    screen: SubjectReviewScreen,
    selected_index: usize,
    note_scroll: u16,
    guidance_scroll: u16,
    half_page_lines: u16,
    guidance_visible: bool,
    pending_comment: Option<PendingSubjectComment>,
    comment: String,
    interaction_enabled: bool,
}

impl SubjectReviewTuiModel {
    pub fn new(mut screen: SubjectReviewScreen) -> Self {
        screen.heading = terminal_safe(&screen.heading);
        screen.note = terminal_safe(&screen.note);
        for choice in &mut screen.choices {
            choice.label = terminal_safe(&choice.label);
        }
        let selected_index = screen
            .selected_index
            .min(screen.choices.len().saturating_sub(1));
        Self {
            screen,
            selected_index,
            note_scroll: 0,
            guidance_scroll: 0,
            half_page_lines: 1,
            guidance_visible: false,
            pending_comment: None,
            comment: String::new(),
            interaction_enabled: true,
        }
    }

    pub fn handle_event(&mut self, event: Event) -> SubjectReviewAction {
        if is_control_c_event(&event) {
            return SubjectReviewAction::Pause;
        }
        if !self.interaction_enabled {
            return SubjectReviewAction::None;
        }
        if self.pending_comment.is_some() {
            return self.handle_comment_event(event);
        }
        let Event::Key(key) = event else {
            return SubjectReviewAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return SubjectReviewAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D') => {
                    if self.guidance_visible {
                        self.guidance_scroll =
                            self.guidance_scroll.saturating_add(self.half_page_lines);
                    } else {
                        self.note_scroll = self.note_scroll.saturating_add(self.half_page_lines);
                    }
                }
                KeyCode::Char('u' | 'U') => {
                    if self.guidance_visible {
                        self.guidance_scroll =
                            self.guidance_scroll.saturating_sub(self.half_page_lines);
                    } else {
                        self.note_scroll = self.note_scroll.saturating_sub(self.half_page_lines);
                    }
                }
                _ => {}
            }
            return SubjectReviewAction::None;
        }
        if has_command_modifier(key.modifiers) {
            return SubjectReviewAction::None;
        }
        if self.guidance_visible {
            match key.code {
                KeyCode::Char('?') | KeyCode::Esc => {
                    self.guidance_visible = false;
                    self.guidance_scroll = 0;
                }
                KeyCode::Down | KeyCode::Char('j' | 'J') => {
                    self.guidance_scroll = self.guidance_scroll.saturating_add(1);
                }
                KeyCode::Up | KeyCode::Char('k' | 'K') => {
                    self.guidance_scroll = self.guidance_scroll.saturating_sub(1);
                }
                KeyCode::PageDown => {
                    self.guidance_scroll = self.guidance_scroll.saturating_add(PAGE_LINES);
                }
                KeyCode::PageUp => {
                    self.guidance_scroll = self.guidance_scroll.saturating_sub(PAGE_LINES);
                }
                KeyCode::Home => self.guidance_scroll = 0,
                _ => {}
            }
            return SubjectReviewAction::None;
        }
        match key.code {
            KeyCode::Down | KeyCode::Char('j' | 'J') => {
                if !self.screen.choices.is_empty() {
                    self.selected_index = (self.selected_index + 1) % self.screen.choices.len();
                }
                SubjectReviewAction::None
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') => {
                if !self.screen.choices.is_empty() {
                    self.selected_index = if self.selected_index == 0 {
                        self.screen.choices.len() - 1
                    } else {
                        self.selected_index - 1
                    };
                }
                SubjectReviewAction::None
            }
            KeyCode::Char('a' | 'A') => {
                self.selected_choice()
                    .map_or(SubjectReviewAction::None, |choice| {
                        SubjectReviewAction::Decide {
                            subject_id: choice.subject_id.clone(),
                            outcome: ReviewOutcome::Approved,
                            comment: String::new(),
                        }
                    })
            }
            KeyCode::Char('r' | 'R') => {
                if let Some(choice) = self.selected_choice() {
                    self.pending_comment =
                        Some(PendingSubjectComment::Reject(choice.subject_id.clone()));
                    self.comment.clear();
                }
                SubjectReviewAction::None
            }
            KeyCode::Enter if self.all_approved() => SubjectReviewAction::Complete,
            KeyCode::Char('m' | 'M') if self.all_approved() => {
                self.pending_comment = Some(PendingSubjectComment::Missing);
                self.comment.clear();
                SubjectReviewAction::None
            }
            KeyCode::Char('?') => {
                self.guidance_visible = true;
                self.guidance_scroll = 0;
                SubjectReviewAction::None
            }
            KeyCode::PageDown => {
                self.note_scroll = self.note_scroll.saturating_add(PAGE_LINES);
                SubjectReviewAction::None
            }
            KeyCode::PageUp => {
                self.note_scroll = self.note_scroll.saturating_sub(PAGE_LINES);
                SubjectReviewAction::None
            }
            KeyCode::Home => {
                self.note_scroll = 0;
                SubjectReviewAction::None
            }
            _ => SubjectReviewAction::None,
        }
    }

    fn handle_comment_event(&mut self, event: Event) -> SubjectReviewAction {
        match event {
            Event::Paste(text) => {
                self.comment.push_str(&terminal_safe(&text));
                SubjectReviewAction::None
            }
            Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
                KeyCode::Enter if self.comment.trim().is_empty() => SubjectReviewAction::None,
                KeyCode::Enter => match self
                    .pending_comment
                    .take()
                    .expect("comment entry has a pending decision")
                {
                    PendingSubjectComment::Reject(subject_id) => SubjectReviewAction::Decide {
                        subject_id,
                        outcome: ReviewOutcome::Rejected,
                        comment: self.comment.trim().to_owned(),
                    },
                    PendingSubjectComment::Missing => SubjectReviewAction::Missing {
                        comment: self.comment.trim().to_owned(),
                    },
                },
                KeyCode::Esc => {
                    self.pending_comment = None;
                    self.comment.clear();
                    SubjectReviewAction::None
                }
                KeyCode::Backspace if !has_command_modifier(key.modifiers) => {
                    self.comment.pop();
                    SubjectReviewAction::None
                }
                KeyCode::Char(character) if !has_command_modifier(key.modifiers) => {
                    self.comment.push(character);
                    SubjectReviewAction::None
                }
                _ => SubjectReviewAction::None,
            },
            _ => SubjectReviewAction::None,
        }
    }

    fn selected_choice(&self) -> Option<&SubjectReviewChoice> {
        self.screen.choices.get(self.selected_index)
    }

    fn all_approved(&self) -> bool {
        self.screen
            .choices
            .iter()
            .all(|choice| choice.outcome == Some(ReviewOutcome::Approved))
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            render_too_small(frame, area);
            return;
        }
        let area = centered(area);
        let footer_height = if self.pending_comment.is_some() { 7 } else { 4 };
        let subject_height = u16::try_from(self.screen.choices.len() + 2)
            .unwrap_or(u16::MAX)
            .clamp(4, 11);
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(3),
                Constraint::Min(6),
                Constraint::Length(subject_height),
                Constraint::Length(footer_height),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(self.screen.heading.as_str()).style(secondary_style()),
            rows[0],
        );
        let question = if self.all_approved() {
            "Does this list include every narrow, independent subject explicitly discussed by this note?"
        } else {
            "Is the selected proposal one narrow, independent subject explicitly discussed by this note?"
        };
        frame.render_widget(
            Paragraph::new(question)
                .style(accent_style())
                .wrap(Wrap { trim: false }),
            rows[1],
        );

        if self.guidance_visible {
            render_scrollable_panel(
                frame,
                rows[2],
                "Subject review help",
                "Approve when the selected label names one narrow, independently meaningful subject explicitly discussed by the note.\n\n\
                 Reject when it combines independent subjects, names a broader ancestor, describes only rhetoric or sentiment, invents unsupported meaning, or treats an incidental mention as a discussed subject.\n\n\
                 After every proposal is approved, press Enter only if no explicitly discussed subject is missing. Press M to report a missing subject.",
                &mut self.guidance_scroll,
                &mut self.half_page_lines,
                false,
            );
        } else {
            render_scrollable_panel(
                frame,
                rows[2],
                "Note",
                &self.screen.note,
                &mut self.note_scroll,
                &mut self.half_page_lines,
                false,
            );
        }

        let items = self
            .screen
            .choices
            .iter()
            .map(|choice| {
                let (symbol, style) = match choice.outcome {
                    None => ("?", secondary_style()),
                    Some(ReviewOutcome::Approved) => (
                        "✓",
                        Style::default()
                            .fg(Color::Green)
                            .add_modifier(Modifier::BOLD),
                    ),
                    Some(ReviewOutcome::Rejected) => (
                        "✗",
                        Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
                    ),
                };
                ListItem::new(Line::from(vec![
                    Span::styled(format!("{symbol} "), style),
                    Span::raw(choice.label.as_str()),
                ]))
            })
            .collect::<Vec<_>>();
        let mut state = ListState::default().with_selected(Some(self.selected_index));
        frame.render_stateful_widget(
            List::new(items)
                .highlight_symbol("▶ ")
                .highlight_style(accent_style())
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(border_style())
                        .padding(Padding::horizontal(1))
                        .title(if self.all_approved() {
                            "Approved subjects"
                        } else {
                            "Proposed subjects"
                        })
                        .title_style(accent_style()),
                ),
            rows[3],
            &mut state,
        );

        let footer = if let Some(pending) = &self.pending_comment {
            let title = match pending {
                PendingSubjectComment::Reject(_) => "Reject subject comment (required)",
                PendingSubjectComment::Missing => "Missing subject comment (required)",
            };
            vec![
                Line::styled(title, accent_style()),
                Line::styled(
                    "Explain exactly what the generation proposal must change.",
                    secondary_style(),
                ),
                Line::raw(""),
                Line::raw(format!("> {}", self.comment)),
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" Confirm  ", secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel", secondary_style()),
                ]),
            ]
        } else if self.guidance_visible {
            vec![
                Line::from(vec![
                    Span::styled("[?]/[Esc]", accent_style()),
                    Span::styled(" Back to note", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[Ctrl-D/U]", accent_style()),
                    Span::styled(" Half-page  ", secondary_style()),
                    Span::styled("[Ctrl-C]", accent_style()),
                    Span::styled(" Pause", secondary_style()),
                ]),
            ]
        } else if self.all_approved() {
            vec![
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" List complete  ", secondary_style()),
                    Span::styled("[M]", accent_style()),
                    Span::styled(" Report missing subject", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[R]", accent_style()),
                    Span::styled(" Reject selected  ", secondary_style()),
                    Span::styled("[↑/↓]", accent_style()),
                    Span::styled(" Select  ", secondary_style()),
                    Span::styled("[Ctrl-D/U]", accent_style()),
                    Span::styled(" Scroll note  ", secondary_style()),
                    Span::styled("[?]", accent_style()),
                    Span::styled(" Help  ", secondary_style()),
                    Span::styled("[Ctrl-C]", accent_style()),
                    Span::styled(" Pause", secondary_style()),
                ]),
            ]
        } else {
            vec![
                Line::from(vec![
                    Span::styled("[A]", accent_style()),
                    Span::styled(" Approve selected  ", secondary_style()),
                    Span::styled("[R]", accent_style()),
                    Span::styled(" Reject and explain  ", secondary_style()),
                    Span::styled("[↑/↓]", accent_style()),
                    Span::styled(" Select", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[Ctrl-D/U]", accent_style()),
                    Span::styled(" Scroll note  ", secondary_style()),
                    Span::styled("[?]", accent_style()),
                    Span::styled(" Help  ", secondary_style()),
                    Span::styled("[Ctrl-C]", accent_style()),
                    Span::styled(" Pause", secondary_style()),
                ]),
            ]
        };
        frame.render_widget(Paragraph::new(footer).wrap(Wrap { trim: false }), rows[4]);
    }
}

impl InteractiveReviewModel for SubjectReviewTuiModel {
    type Action = SubjectReviewAction;

    fn none_action() -> Self::Action {
        SubjectReviewAction::None
    }

    fn pause_action() -> Self::Action {
        SubjectReviewAction::Pause
    }

    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }

    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

fn validate_note_set(note_set: &FrozenNoteSet) -> Result<()> {
    let invariants = &note_set.invariants;
    if note_set.schema_version != NOTE_SET_SCHEMA_VERSION
        || note_set.status != "approved"
        || !is_lower_hex(&note_set.source.sha256, 64)
        || invariants.required_split.trim().is_empty()
        || note_set.note_ids.len() != invariants.note_count
        || note_set.note_ids.len() != invariants.unique_note_count
        || note_set.note_ids.iter().collect::<BTreeSet<_>>().len() != invariants.unique_note_count
        || note_set.note_ids.iter().any(|id| !is_lower_hex(id, 64))
    {
        return invalid("frozen note-set schema, source, note IDs, or invariants are invalid");
    }
    Ok(())
}

fn load_source_notes(
    note_set: &FrozenNoteSet,
    note_set_path: &Path,
) -> Result<BTreeMap<String, SourceNote>> {
    let source_path = resolve_relative(note_set_path, &note_set.source.path);
    if hash_file(&source_path)? != note_set.source.sha256 {
        return invalid(format!(
            "source sample `{}` does not match the frozen note set",
            source_path.display()
        ));
    }
    let expected_ids = note_set
        .note_ids
        .iter()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    let file = File::open(&source_path).map_err(|source| io_error("open", &source_path, source))?;
    let reader = BufReader::new(file);
    let mut notes = BTreeMap::new();
    for line in reader.lines() {
        let line = line.map_err(|source| io_error("read", &source_path, source))?;
        let row: SourceSampleRow =
            serde_json::from_str(&line).map_err(|source| Error::Manifest {
                operation: "decode source row from",
                path: source_path.clone(),
                source,
            })?;
        if row.split != note_set.invariants.required_split
            || !expected_ids.contains(row.note_id.as_str())
        {
            continue;
        }
        if notes
            .insert(
                row.note_id.clone(),
                SourceNote {
                    pubkey: row.pubkey,
                    content: row.content,
                },
            )
            .is_some()
        {
            return invalid(format!("source sample repeats note {}", row.note_id));
        }
    }
    if notes.len() != expected_ids.len() {
        return invalid(format!(
            "source sample contains {} of {} frozen note IDs",
            notes.len(),
            expected_ids.len()
        ));
    }
    let authors = notes
        .values()
        .map(|note| note.pubkey.as_str())
        .collect::<BTreeSet<_>>();
    if authors.len() != note_set.invariants.unique_author_count {
        return invalid(format!(
            "source sample contains {} unique frozen-note authors, expected {}",
            authors.len(),
            note_set.invariants.unique_author_count
        ));
    }
    Ok(notes)
}

#[derive(Deserialize)]
struct SourceSampleRow {
    split: String,
    note_id: String,
    pubkey: String,
    content: String,
}

fn resolve_fragments(
    subject: &ProposedSubjectMask,
    content: &str,
    note_id: &str,
) -> Result<Vec<(usize, usize)>> {
    if subject.fragments.is_empty() {
        return invalid(format!(
            "mask {note_id} / {} contains no fragments",
            subject.subject_id
        ));
    }
    let mut spans = Vec::with_capacity(subject.fragments.len());
    for fragment in &subject.fragments {
        if fragment.text.trim().is_empty() || fragment.occurrence == 0 {
            return invalid(format!(
                "mask {note_id} / {} contains an empty fragment or zero occurrence",
                subject.subject_id
            ));
        }
        let Some((start, _)) = content
            .match_indices(&fragment.text)
            .nth(fragment.occurrence - 1)
        else {
            return invalid(format!(
                "mask fragment `{}` occurrence {} is absent from note {note_id}",
                fragment.text, fragment.occurrence
            ));
        };
        spans.push((start, start + fragment.text.len()));
    }
    for pair in spans.windows(2) {
        if pair[0].0 > pair[1].0 {
            return invalid(format!(
                "mask fragments for note {note_id} are not in source order"
            ));
        }
        if pair[0].1 > pair[1].0 {
            return invalid(format!("mask fragments for note {note_id} overlap"));
        }
    }
    Ok(spans)
}

fn highlighted_note(content: &str, spans: &[(usize, usize)]) -> String {
    let mut rendered = String::with_capacity(content.len() + spans.len() * 6);
    let mut cursor = 0;
    for &(start, end) in spans {
        rendered.push_str(&content[cursor..start]);
        rendered.push('⟦');
        rendered.push_str(&content[start..end]);
        rendered.push('⟧');
        cursor = end;
    }
    rendered.push_str(&content[cursor..]);
    rendered
}

fn subject_key(note: &VerifiedNoteSubjects, subject: &VerifiedSubjectMask) -> String {
    format!("{}:{}", note.note_id, subject.proposal.subject_id)
}

#[derive(Serialize)]
struct SubjectIdentity<'a> {
    note_id: &'a str,
    note_content: &'a str,
    subject_id: &'a str,
    label: &'a str,
}

fn subject_identity(note: &VerifiedNoteSubjects, subject: &VerifiedSubjectMask) -> Result<String> {
    value_sha256(&SubjectIdentity {
        note_id: &note.note_id,
        note_content: &note.note.content,
        subject_id: &subject.proposal.subject_id,
        label: &subject.proposal.label,
    })
}

#[derive(Serialize)]
struct CompletenessIdentity<'a> {
    note_id: &'a str,
    note_content: &'a str,
    subjects: Vec<(&'a str, &'a str)>,
}

fn completeness_identity(note: &VerifiedNoteSubjects) -> Result<String> {
    value_sha256(&CompletenessIdentity {
        note_id: &note.note_id,
        note_content: &note.note.content,
        subjects: note
            .subjects
            .iter()
            .map(|subject| {
                (
                    subject.proposal.subject_id.as_str(),
                    subject.proposal.label.as_str(),
                )
            })
            .collect(),
    })
}

#[derive(Serialize)]
struct MaskIdentity<'a> {
    subject: SubjectIdentity<'a>,
    fragments: &'a [ProposedMaskFragment],
}

fn mask_identity(note: &VerifiedNoteSubjects, subject: &VerifiedSubjectMask) -> Result<String> {
    value_sha256(&MaskIdentity {
        subject: SubjectIdentity {
            note_id: &note.note_id,
            note_content: &note.note.content,
            subject_id: &subject.proposal.subject_id,
            label: &subject.proposal.label,
        },
        fragments: &subject.proposal.fragments,
    })
}

fn decision_for<'a>(
    decisions: &'a BTreeMap<String, StoredDecision>,
    key: &str,
    identity: &str,
) -> Option<&'a ReviewDecision> {
    decisions
        .get(key)
        .filter(|stored| stored.item_sha256 == identity)
        .map(|stored| &stored.decision)
}

fn retain_current(
    decisions: &mut BTreeMap<String, StoredDecision>,
    identities: &BTreeMap<String, String>,
) {
    decisions.retain(|key, stored| {
        identities
            .get(key)
            .is_some_and(|identity| identity == &stored.item_sha256)
    });
}

fn count_decision(
    (approved, rejected): (usize, usize),
    decision: &ReviewDecision,
) -> (usize, usize) {
    match decision.outcome {
        ReviewOutcome::Approved => (approved + 1, rejected),
        ReviewOutcome::Rejected => (approved, rejected + 1),
    }
}

fn validate_decision(decision: &ReviewDecision, context: &str) -> Result<()> {
    if decision.outcome == ReviewOutcome::Rejected && decision.comment.trim().is_empty() {
        return invalid(format!("{context} requires an actionable comment"));
    }
    Ok(())
}

fn resolve_relative(anchor: &Path, declared: &str) -> PathBuf {
    let declared = Path::new(declared);
    if declared.is_absolute() {
        declared.to_owned()
    } else {
        anchor
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join(declared)
    }
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn invalid<T>(message: impl Into<String>) -> Result<T> {
    Err(Error::ExperimentState(message.into()))
}
