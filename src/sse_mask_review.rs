//! Source-bound generation proposals and durable human review for SSE subjects and masks.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Padding, Paragraph, Wrap};
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::reference_map::ReviewOutcome;
use crate::reference_review::ApprovalUi;
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, border_style,
    centered, has_command_modifier, is_control_c_event, render_scrollable_panel, render_too_small,
    secondary_style, terminal_safe,
};
use crate::review_state::{
    acquire_session_lock, load_session, publish_json, save_session, value_sha256,
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
const TPV3_81_INSTRUCTION: &str = r#"Read this social-media post as a whole and determine everything the author communicates.

Using the complete post, resolve each context-dependent reference or expression to the most specific descriptive meaning clearly supported by the post. When an exact identity is unavailable, use a supported descriptive referent. Express relationships only at the specificity supported by the complete post.

Identify every substantive meaning the author communicates. Information the post merely leaves unidentified, unexplained, unstated, or unresolved is not itself a meaning to output.

Rewrite each identified meaning in your own words as a distinct, standalone takeaway. Omit exact user handles, URLs, and hashtag syntax. Preserve any substantive meaning they contribute using ordinary language.

Evaluate the final wording of each takeaway in isolation, assuming its reader cannot see the original post or any other takeaway. Revise it until it contains the referents, relationships, and context needed to preserve the same meaning without adding meaning.

Return only a JSON array of takeaway strings."#;
const MPV3_3_INSTRUCTION: &str = r#"Align one fixed takeaway to its source social-media post.

Read the complete post and takeaway first. Resolve context-dependent source expressions using the complete post.

Select exact source fragments that satisfy this criterion: when read together without any unselected text, they preserve the takeaway’s complete meaning—including its referents, relationships, and qualifications—without adding unrelated meaning. Complete the selection before minimizing it.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Before returning, verify that the selected fragments alone satisfy the criterion above.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<takeaway>
{TAKEAWAY}
</takeaway>"#;
const TPV3_82_INSTRUCTION: &str = r#"Read this social-media post as a whole and determine everything the author communicates.

Using the complete post, resolve each context-dependent reference or expression to the most specific descriptive meaning clearly supported by the post. When an exact identity is unavailable, use a supported descriptive referent. Express relationships only at the specificity supported by the complete post.

A URL, exact user handle, or hashtag syntax cannot by itself establish a destination, relationship, or activity that the surrounding text does not state. Hashtag words may supply subject context, but do not otherwise add a claim.

Identify every substantive meaning the author communicates. Information the post merely leaves unidentified, unexplained, unstated, or unresolved is not itself a meaning to output.

Rewrite each identified meaning in your own words as a distinct takeaway that stands alone as a separate document. Other takeaways do not provide context. A takeaway passes only when a reader who sees that one string and nothing else can identify every participant, event, claim, and relationship needed to recover its meaning. If a takeaway communicates a response to or evaluation of another meaning in the post, restate that meaning inside the takeaway. Repeat source-grounded context when necessary.

Before returning, test every takeaway against that success criterion and revise any item that does not pass without adding meaning.

Omit exact user handles, URLs, and hashtag syntax.

Return only a JSON array of takeaway strings."#;
const MPV3_4_INSTRUCTION: &str = r#"Align one fixed takeaway to its source social-media post.

Read the complete post and takeaway first. Treat the takeaway as the fixed target meaning.

The returned fragments will be read together as a standalone excerpt, without the complete post or the takeaway. Select exact source fragments so that this excerpt explicitly preserves the takeaway’s complete meaning—including its referents, relationships, and qualifications—without adding unrelated meaning.

Judge support only from meaning explicitly stated by the selected text. A name identifies an entity but does not supply its type, attributes, or relationships. Unselected text and external knowledge supply nothing.

Complete the evidence needed for the whole takeaway before minimizing. Then remove selected text whose meaning is not part of the takeaway.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Before returning, read only the selected fragments and verify that they explicitly support every part of the takeaway and no additional meaning.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<takeaway>
{TAKEAWAY}
</takeaway>"#;

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

#[derive(Clone, Debug)]
struct VerifiedAtomicSubjectReviewRun {
    identity_sha256: String,
    items: Vec<VerifiedPromptReviewItem>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PromptGenerationStage {
    prompt_registry_path: String,
    prompt_registry_sha256: String,
    prompt_version: String,
    prompt: String,
    prompt_sha256: String,
    model: String,
    reasoning_effort: String,
    response_schema: serde_json::Value,
    response_schema_sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectGenerationManifest {
    schema_version: u32,
    mode: String,
    wrapper_sha256: String,
    codex_binary: String,
    codex_version: String,
    codex_home: String,
    input_path: String,
    input_sha256: String,
    subject_envelope_version: String,
    subject_input_normalization_version: String,
    subject: PromptGenerationStage,
    isolation: serde_json::Value,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PromptGenerationInput {
    schema_version: u32,
    notes: Vec<PromptGenerationInputNote>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PromptGenerationInputNote {
    note_id: String,
    text: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectGenerationOutput {
    schema_version: u32,
    manifest_sha256: String,
    notes: Vec<AtomicSubjectGenerationOutputNote>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectGenerationOutputNote {
    note_id: String,
    text: String,
    subjects: Vec<AtomicSubjectGenerationOutputSubject>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectGenerationOutputSubject {
    source_index: usize,
    text: String,
}

#[derive(Clone, Debug, Deserialize)]
struct PromptGenerationResult {
    schema_version: u32,
    manifest_sha256: String,
    job_key: String,
    stage: String,
    note_id: String,
    attempt: u32,
    status: String,
    wrapper_sha256: String,
    codex_version: String,
    model: String,
    reasoning_effort: String,
    prompt_sha256: String,
    response_schema_sha256: String,
    final_output_raw: Option<String>,
    final_output_sha256: Option<String>,
    response: serde_json::Value,
}

#[derive(Serialize)]
struct PromptReviewRunIdentity<'a> {
    review_protocol: &'a str,
    manifest_sha256: &'a str,
    input_sha256: &'a str,
    results_sha256: &'a str,
    output_sha256: &'a str,
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum PromptReviewItemKind {
    Subject,
    SubjectList,
}

#[derive(Clone, Debug)]
struct VerifiedPromptReviewItem {
    item_id: String,
    item_sha256: String,
    presentation: PromptReviewItemPresentation,
}

#[derive(Clone, Debug)]
enum PromptReviewItemPresentation {
    Subject(AtomicSubjectPromptReviewScreen),
    SubjectList {
        note_index: usize,
        note_count: usize,
        note: String,
        subject_item_indices: Vec<usize>,
    },
}

impl PromptReviewItemPresentation {
    fn kind(&self) -> PromptReviewItemKind {
        match self {
            Self::Subject(_) => PromptReviewItemKind::Subject,
            Self::SubjectList { .. } => PromptReviewItemKind::SubjectList,
        }
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AtomicSubjectPromptReviewScreen {
    pub heading: String,
    pub subject: String,
    pub question: String,
    pub note: String,
    pub approve_label: String,
    pub reject_label: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AtomicSubjectListReviewScreen {
    pub heading: String,
    pub question: String,
    pub note: String,
    pub accepted_subjects: Vec<String>,
    pub approve_label: String,
    pub reject_label: String,
    pub guidance: ApprovalGuidance,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PromptReviewScreen {
    Subject {
        review: AtomicSubjectPromptReviewScreen,
        comment: String,
    },
    SubjectList {
        review: AtomicSubjectListReviewScreen,
        comment: String,
    },
}

impl PromptReviewScreen {
    pub fn approval_screen(&self) -> ApprovalScreen {
        match self {
            PromptReviewScreen::Subject { review, .. } => review.approval_screen(),
            PromptReviewScreen::SubjectList { review, .. } => review.approval_screen(),
        }
    }

    pub fn comment(&self) -> &str {
        match self {
            PromptReviewScreen::Subject { comment, .. }
            | PromptReviewScreen::SubjectList { comment, .. } => comment,
        }
    }
}

pub trait PromptReviewUi {
    fn review_prompt(&mut self, screen: PromptReviewScreen) -> io::Result<ApprovalTuiAction>;
}

impl PromptReviewUi for ReferenceTerminal {
    fn review_prompt(&mut self, screen: PromptReviewScreen) -> io::Result<ApprovalTuiAction> {
        self.review_prompt_iteration(screen.approval_screen(), screen.comment().to_owned())
    }
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PromptReviewRunOutcome {
    Paused,
    Completed {
        subjects: PromptReviewCounts,
        subject_lists: PromptReviewCounts,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PromptReviewCounts {
    pub approved: usize,
    pub rejected: usize,
    pub skipped: usize,
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

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum PromptReviewStatus {
    Pending,
    Approved,
    Rejected,
    Skipped,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PromptReviewItemState {
    item_id: String,
    item_sha256: String,
    status: PromptReviewStatus,
    comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PromptReviewSession {
    schema_version: u32,
    review_protocol: String,
    generation_run_sha256: String,
    items: Vec<PromptReviewItemState>,
}

const PROMPT_REVIEW_SESSION_SCHEMA_VERSION: u32 = 1;
const PROMPT_REVIEW_PROTOCOL: &str = "atomic-subject-review-v1";
const SUBJECT_RESPONSE_SCHEMA_SHA256: &str =
    "ffa0aa2d4a52a1b30f41f0a1761e455471a5127c0e20d74aaeea575a0df2226a";

pub fn load_verified_subject_mask_proposal(
    proposal_path: impl AsRef<Path>,
) -> Result<VerifiedSubjectMaskProposal> {
    let proposal_path = proposal_path.as_ref();
    let (proposal, _proposal_sha256): (SubjectMaskProposal, String) =
        load_json_snapshot(proposal_path)?;
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
    let (note_set, note_set_sha256): (FrozenNoteSet, String) = load_json_snapshot(&note_set_path)?;
    if note_set_sha256 != proposal.note_set.sha256 {
        return invalid(format!(
            "frozen note set `{}` does not match its proposal binding",
            note_set_path.display()
        ));
    }
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
        note_set_sha256,
        notes,
    })
}

fn uses_approved_generation_profile(subject_instruction: &str, mask_instruction: &str) -> bool {
    (subject_instruction == SUBJECT_INSTRUCTION && mask_instruction == MASK_INSTRUCTION)
        || (subject_instruction == TAKEAWAY_INSTRUCTION
            && mask_instruction == TAKEAWAY_MASK_INSTRUCTION)
        || (subject_instruction == TPV3_81_INSTRUCTION && mask_instruction == MPV3_3_INSTRUCTION)
        || (subject_instruction == TPV3_82_INSTRUCTION && mask_instruction == MPV3_4_INSTRUCTION)
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
            ApprovalTuiAction::SaveComment { .. } => {
                return invalid("production mask review cannot save a draft comment");
            }
            ApprovalTuiAction::Skip { .. } => {
                return invalid("production mask review cannot skip a decision");
            }
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

fn load_verified_atomic_subject_review_run(
    run_directory: &Path,
) -> Result<VerifiedAtomicSubjectReviewRun> {
    if run_directory.join("runner-upgrades.jsonl").exists() {
        return invalid(
            "subject prompt review requires a fresh generation run without runner upgrades",
        );
    }
    let manifest_path = run_directory.join("manifest.json");
    let (manifest, manifest_sha256): (AtomicSubjectGenerationManifest, String) =
        load_json_snapshot(&manifest_path)?;
    validate_atomic_subject_generation_manifest(&manifest)?;

    let input_path = resolve_relative(&manifest_path, &manifest.input_path);
    let (input, input_sha256): (PromptGenerationInput, String) = load_json_snapshot(&input_path)?;
    if input_sha256 != manifest.input_sha256 {
        return invalid(format!(
            "generation input `{}` does not match its manifest binding",
            input_path.display()
        ));
    }
    if input.schema_version != 1 || input.notes.is_empty() {
        return invalid("prompt generation input schema or note list is invalid");
    }

    let output_path = run_directory.join("output.json");
    let (output, output_sha256): (AtomicSubjectGenerationOutput, String) =
        load_json_snapshot(&output_path)?;
    if output.schema_version != 1 || output.manifest_sha256 != manifest_sha256 {
        return invalid("subject generation output does not match its manifest");
    }
    if output.notes.len() != input.notes.len() {
        return invalid("subject generation output does not match its input note count");
    }

    let results_path = run_directory.join("results.jsonl");
    let (results_bytes, results_sha256) = load_bytes_snapshot(&results_path)?;
    let mut results = latest_prompt_generation_results(
        &results_bytes,
        &results_path,
        &manifest,
        &manifest_sha256,
        &input,
    )?;

    let identity_sha256 = value_sha256(&PromptReviewRunIdentity {
        review_protocol: PROMPT_REVIEW_PROTOCOL,
        manifest_sha256: &manifest_sha256,
        input_sha256: &input_sha256,
        results_sha256: &results_sha256,
        output_sha256: &output_sha256,
    })?;
    let subject_count = output.notes.iter().map(|note| note.subjects.len()).sum();
    let mut seen_note_ids = BTreeSet::<String>::new();
    let mut seen_item_ids = BTreeSet::<String>::new();
    let mut items = Vec::with_capacity(subject_count + input.notes.len());
    let mut global_subject_index = 0;
    for (note_index, (input_note, output_note)) in input.notes.iter().zip(&output.notes).enumerate()
    {
        if input_note.note_id.trim().is_empty()
            || input_note.text.trim().is_empty()
            || !seen_note_ids.insert(input_note.note_id.clone())
        {
            return invalid(format!(
                "subject generation input note {} has an invalid or duplicate identity",
                note_index + 1
            ));
        }
        if output_note.note_id != input_note.note_id {
            return invalid(format!(
                "subject generation output note {} does not match the input order",
                note_index + 1
            ));
        }
        if output_note.text != input_note.text {
            return invalid(format!(
                "subject generation output note {} does not preserve its source text",
                note_index + 1
            ));
        }

        let labels = output_note
            .subjects
            .iter()
            .map(|subject| subject.text.clone())
            .collect::<Vec<_>>();
        let subject_key = format!("subject:{}", input_note.note_id);
        let subject_result = take_generation_result(&mut results, &subject_key)?;
        let rendered_subject_prompt =
            render_subject_prompt(&manifest.subject.prompt, &input_note.text);
        validate_generation_result(
            &subject_result,
            &manifest,
            &manifest_sha256,
            &subject_key,
            &input_note.note_id,
            &manifest.subject,
            &rendered_subject_prompt,
            &serde_json::to_value(&labels).map_err(|source| Error::Manifest {
                operation: "encode",
                path: output_path.clone(),
                source,
            })?,
        )?;

        let first_subject_item_index = items.len();
        for (subject_index, generated) in output_note.subjects.iter().enumerate() {
            if generated.text.trim().is_empty() {
                return invalid(format!(
                    "subject generation output note {} subject {} is empty",
                    input_note.note_id,
                    subject_index + 1
                ));
            }
            if generated.source_index != subject_index {
                return invalid(format!(
                    "subject generation output note {} has invalid source index {}",
                    input_note.note_id, generated.source_index
                ));
            }
            let item_id = format!("subject:{}:{subject_index}", input_note.note_id);
            if !seen_item_ids.insert(item_id.clone()) {
                return invalid("generated subject review item identities collided");
            }
            let item_sha256 = value_sha256(&(
                identity_sha256.as_str(),
                "subject",
                input_note.note_id.as_str(),
                input_note.text.as_str(),
                subject_index,
                generated.text.as_str(),
            ))?;
            items.push(VerifiedPromptReviewItem {
                item_id,
                item_sha256,
                presentation: PromptReviewItemPresentation::Subject(atomic_subject_screen(
                    note_index,
                    input.notes.len(),
                    global_subject_index,
                    subject_count,
                    &input_note.text,
                    &generated.text,
                )),
            });
            global_subject_index += 1;
        }
        let item_id = format!("subject-list:{}", input_note.note_id);
        if !seen_item_ids.insert(item_id.clone()) {
            return invalid("generated subject-list review item identities collided");
        }
        let item_sha256 = value_sha256(&(
            identity_sha256.as_str(),
            "subject_list",
            input_note.note_id.as_str(),
            input_note.text.as_str(),
            &labels,
        ))?;
        items.push(VerifiedPromptReviewItem {
            item_id,
            item_sha256,
            presentation: PromptReviewItemPresentation::SubjectList {
                note_index,
                note_count: input.notes.len(),
                note: input_note.text.clone(),
                subject_item_indices: (first_subject_item_index..items.len()).collect(),
            },
        });
    }
    if let Some(unexpected) = results.keys().next() {
        return invalid(format!(
            "subject generation ledger contains unexpected latest result `{unexpected}`"
        ));
    }
    Ok(VerifiedAtomicSubjectReviewRun {
        identity_sha256,
        items,
    })
}

fn validate_atomic_subject_generation_manifest(
    manifest: &AtomicSubjectGenerationManifest,
) -> Result<()> {
    if manifest.schema_version != 1 || manifest.mode != "atomic_subject_generation" {
        return invalid("subject prompt review requires an atomic-subject generation run");
    }
    let wrapper_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector")
        .join("codex_exec.py");
    let (_, wrapper_sha256) = load_bytes_snapshot(&wrapper_path)?;
    if !is_lower_hex(&manifest.input_sha256, 64)
        || manifest.wrapper_sha256 != wrapper_sha256
        || manifest.codex_binary.trim().is_empty()
        || manifest.codex_version.trim().is_empty()
        || manifest.codex_home.trim().is_empty()
        || manifest.input_path.trim().is_empty()
        || manifest.subject_envelope_version != "xml-post-v1"
        || manifest.subject_input_normalization_version != "remove-long-ascii-nip19-identifiers-v2"
    {
        return invalid("subject generation manifest is incomplete");
    }
    if manifest.isolation != expected_prompt_generation_isolation() {
        return invalid(
            "prompt generation did not use a fresh process and isolated context per job",
        );
    }
    validate_prompt_generation_stage(
        &manifest.subject,
        "subject",
        expected_subject_response_schema(),
        SUBJECT_RESPONSE_SCHEMA_SHA256,
    )?;
    Ok(())
}

fn validate_prompt_generation_stage(
    stage: &PromptGenerationStage,
    name: &str,
    expected_response_schema: serde_json::Value,
    expected_response_schema_sha256: &str,
) -> Result<()> {
    if stage.prompt_registry_path.trim().is_empty()
        || !is_lower_hex(&stage.prompt_registry_sha256, 64)
        || stage.prompt_version.trim().is_empty()
        || stage.prompt.trim().is_empty()
        || stage.prompt_sha256 != sha256_bytes(stage.prompt.as_bytes())
        || stage.model.trim().is_empty()
        || stage.reasoning_effort.trim().is_empty()
        || stage.response_schema != expected_response_schema
        || stage.response_schema_sha256 != expected_response_schema_sha256
    {
        return invalid(format!(
            "prompt generation manifest {name} stage is invalid"
        ));
    }
    Ok(())
}

fn expected_prompt_generation_isolation() -> serde_json::Value {
    serde_json::json!({
        "fresh_process_per_job": true,
        "ephemeral": true,
        "sterile_working_directory_per_job": true,
        "ignore_user_config": true,
        "ignore_rules": true,
        "approval_policy": "never",
        "sandbox": "read-only",
        "web_search": "disabled",
        "shell_environment_inherit": "none",
        "model_instructions": "Follow the user's instructions.\n",
        "model_instructions_sha256": "3d366e0253ede507e29be8ce00a9bd46ba2ebe7c01024bad45305bc0207fcfb1",
        "runtime_context_overrides": [
            "agents.enabled=false",
            "include_permissions_instructions=false",
            "include_apps_instructions=false",
            "include_collaboration_mode_instructions=false",
            "include_environment_context=false",
            "skills.include_instructions=false"
        ],
        "disabled_features": [
            "shell_tool",
            "unified_exec",
            "multi_agent",
            "apps",
            "plugins",
            "browser_use",
            "computer_use",
            "image_generation"
        ]
    })
}

fn expected_subject_response_schema() -> serde_json::Value {
    serde_json::json!({
        "type": "object",
        "properties": {
            "subjects": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["subjects"],
        "additionalProperties": false
    })
}

fn latest_prompt_generation_results(
    bytes: &[u8],
    path: &Path,
    manifest: &AtomicSubjectGenerationManifest,
    manifest_sha256: &str,
    input: &PromptGenerationInput,
) -> Result<BTreeMap<String, PromptGenerationResult>> {
    let mut note_texts = BTreeMap::<&str, &str>::new();
    for note in &input.notes {
        if note.note_id.trim().is_empty()
            || note.text.trim().is_empty()
            || note_texts
                .insert(note.note_id.as_str(), note.text.as_str())
                .is_some()
        {
            return invalid("prompt generation input contains an invalid or duplicate note");
        }
    }
    let mut latest = BTreeMap::<String, PromptGenerationResult>::new();
    let lines = bytes.split(|byte| *byte == b'\n').collect::<Vec<_>>();
    for (index, line) in lines.iter().enumerate() {
        if line.is_empty() {
            if index + 1 == lines.len() && bytes.ends_with(b"\n") {
                continue;
            }
            return invalid(format!(
                "prompt generation result line {} is empty",
                index + 1
            ));
        }
        let result: PromptGenerationResult =
            serde_json::from_slice(line).map_err(|source| Error::Manifest {
                operation: "decode generation result from",
                path: path.to_owned(),
                source,
            })?;
        if result.schema_version != 1
            || result.manifest_sha256 != manifest_sha256
            || result.attempt == 0
            || result.job_key.trim().is_empty()
        {
            return invalid(format!(
                "prompt generation result line {} has an invalid identity",
                index + 1
            ));
        }
        let expected_attempt = latest
            .get(&result.job_key)
            .map_or(1, |previous| previous.attempt + 1);
        if result.attempt != expected_attempt {
            return invalid(format!(
                "prompt generation result `{}` has a nonconsecutive attempt",
                result.job_key
            ));
        }

        let Some(note_text) = note_texts.get(result.note_id.as_str()).copied() else {
            return invalid(format!(
                "prompt generation result `{}` names an unknown note",
                result.job_key
            ));
        };
        if result.stage != "subject" || result.job_key != format!("subject:{}", result.note_id) {
            return invalid(format!(
                "prompt generation result `{}` has an invalid subject identity",
                result.job_key
            ));
        }
        let stage = &manifest.subject;
        let rendered_prompt = render_subject_prompt(&manifest.subject.prompt, note_text);
        if result.wrapper_sha256 != manifest.wrapper_sha256
            || result.codex_version != manifest.codex_version
            || result.model != stage.model
            || result.reasoning_effort != stage.reasoning_effort
            || result.prompt_sha256 != sha256_bytes(rendered_prompt.as_bytes())
            || result.response_schema_sha256 != stage.response_schema_sha256
            || !matches!(result.status.as_str(), "succeeded" | "failed")
        {
            return invalid(format!(
                "prompt generation result `{}` does not match its rendered prompt or generation contract",
                result.job_key
            ));
        }
        if result.status == "succeeded" {
            validate_result_output(&result, &result.response, &result.job_key)?;
            result
                .response
                .as_array()
                .ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "prompt generation result `{}` response is not an array",
                        result.job_key
                    ))
                })?
                .iter()
                .map(|item| {
                    item.as_str()
                        .filter(|value| !value.trim().is_empty())
                        .map(str::to_owned)
                        .ok_or_else(|| {
                            Error::ExperimentState(format!(
                                "prompt generation result `{}` contains an invalid response item",
                                result.job_key
                            ))
                        })
                })
                .collect::<Result<Vec<_>>>()?;
        } else {
            validate_failed_result_output(&result)?;
        }
        latest.insert(result.job_key.clone(), result);
    }
    if latest.is_empty() {
        return invalid("prompt generation result ledger is empty");
    }
    Ok(latest)
}

fn validate_failed_result_output(result: &PromptGenerationResult) -> Result<()> {
    if !result.response.is_null() {
        return invalid(format!(
            "failed prompt generation result `{}` contains a response",
            result.job_key
        ));
    }
    match (&result.final_output_raw, &result.final_output_sha256) {
        (None, None) => Ok(()),
        (Some(raw), Some(expected_sha256)) if sha256_bytes(raw.as_bytes()) == *expected_sha256 => {
            Ok(())
        }
        _ => invalid(format!(
            "failed prompt generation result `{}` has invalid final output provenance",
            result.job_key
        )),
    }
}

fn take_generation_result(
    results: &mut BTreeMap<String, PromptGenerationResult>,
    key: &str,
) -> Result<PromptGenerationResult> {
    results.remove(key).ok_or_else(|| {
        Error::ExperimentState(format!(
            "prompt generation output has no preserved result `{key}`"
        ))
    })
}

#[allow(clippy::too_many_arguments)]
fn validate_generation_result(
    result: &PromptGenerationResult,
    manifest: &AtomicSubjectGenerationManifest,
    manifest_sha256: &str,
    job_key: &str,
    note_id: &str,
    stage: &PromptGenerationStage,
    rendered_prompt: &str,
    expected_response: &serde_json::Value,
) -> Result<()> {
    if result.schema_version != 1
        || result.manifest_sha256 != manifest_sha256
        || result.job_key != job_key
        || result.stage != "subject"
        || result.note_id != note_id
        || result.status != "succeeded"
        || result.wrapper_sha256 != manifest.wrapper_sha256
        || result.codex_version != manifest.codex_version
        || result.model != stage.model
        || result.reasoning_effort != stage.reasoning_effort
        || result.prompt_sha256 != sha256_bytes(rendered_prompt.as_bytes())
        || result.response_schema_sha256 != stage.response_schema_sha256
        || &result.response != expected_response
    {
        return invalid(format!(
            "prompt generation output does not match preserved result or rendered prompt `{job_key}`"
        ));
    }
    validate_result_output(result, expected_response, job_key)?;
    Ok(())
}

fn validate_result_output(
    result: &PromptGenerationResult,
    expected_response: &serde_json::Value,
    job_key: &str,
) -> Result<()> {
    let raw = result.final_output_raw.as_deref().ok_or_else(|| {
        Error::ExperimentState(format!(
            "prompt generation result `{job_key}` has no final output"
        ))
    })?;
    let expected_sha256 = result.final_output_sha256.as_deref().ok_or_else(|| {
        Error::ExperimentState(format!(
            "prompt generation result `{job_key}` has no final output hash"
        ))
    })?;
    if sha256_bytes(raw.as_bytes()) != expected_sha256 {
        return invalid(format!(
            "prompt generation result `{job_key}` has invalid final output provenance"
        ));
    }
    let raw_response: serde_json::Value =
        serde_json::from_str(raw).map_err(|source| Error::Manifest {
            operation: "decode prompt generation final output from",
            path: PathBuf::from(job_key),
            source,
        })?;
    let expected_final_output = serde_json::json!({"subjects": expected_response});
    if raw_response != expected_final_output {
        return invalid(format!(
            "prompt generation result `{job_key}` final output does not match its response"
        ));
    }
    Ok(())
}

fn render_subject_prompt(prompt: &str, note: &str) -> String {
    format!(
        "{prompt}\n\n<post>\n{}\n</post>",
        normalize_subject_input(note)
    )
}
fn normalize_subject_input(note: &str) -> String {
    let mut normalized = String::with_capacity(note.len());
    let mut copied_until = 0;
    let mut cursor = 0;
    while cursor < note.len() {
        let previous_is_word = note[..cursor]
            .chars()
            .next_back()
            .is_some_and(is_ascii_regex_word_character);
        if !previous_is_word && let Some(length) = nip19_identifier_length(&note[cursor..]) {
            normalized.push_str(&note[copied_until..cursor]);
            cursor += length;
            copied_until = cursor;
            continue;
        }
        cursor += note[cursor..]
            .chars()
            .next()
            .expect("valid string cursor")
            .len_utf8();
    }
    normalized.push_str(&note[copied_until..]);
    normalized
}

fn nip19_identifier_length(value: &str) -> Option<usize> {
    let mut cursor = ascii_case_insensitive_prefix_length(value, "nostr:").unwrap_or(0);
    let prefix_length = [
        "nprofile", "nevent", "nrelay", "naddr", "npub", "nsec", "note",
    ]
    .into_iter()
    .find_map(|prefix| ascii_case_insensitive_prefix_length(&value[cursor..], prefix))?;
    cursor += prefix_length;
    if value.as_bytes().get(cursor) != Some(&b'1') {
        return None;
    }
    cursor += 1;
    let mut payload_characters = 0;
    while let Some(character) = value[cursor..].chars().next() {
        if !is_ascii_case_insensitive_bech32_payload(character) {
            break;
        }
        cursor += character.len_utf8();
        payload_characters += 1;
    }
    if payload_characters < 20 {
        return None;
    }
    if value
        .as_bytes()
        .get(cursor)
        .is_some_and(|byte| matches!(byte, b'?' | b'#'))
    {
        cursor += 1;
        while cursor < value.len() {
            let character = value[cursor..].chars().next()?;
            if is_python_whitespace(character) || matches!(character, '<' | '>' | '"' | '\'') {
                break;
            }
            cursor += character.len_utf8();
        }
    }
    if value[cursor..]
        .chars()
        .next()
        .is_some_and(is_ascii_regex_word_character)
    {
        return None;
    }
    Some(cursor)
}

fn ascii_case_insensitive_prefix_length(value: &str, expected: &str) -> Option<usize> {
    let mut length = 0;
    for expected_character in expected.bytes() {
        let character = value[length..].chars().next()?;
        if !character.is_ascii() || character.to_ascii_lowercase() != char::from(expected_character)
        {
            return None;
        }
        length += character.len_utf8();
    }
    Some(length)
}

fn is_ascii_case_insensitive_bech32_payload(character: char) -> bool {
    character.is_ascii()
        && matches!(
            character.to_ascii_lowercase(),
            '0' | '2'..='9' | 'a' | 'c'..='h' | 'j'..='n' | 'p'..='z'
        )
}

fn is_python_whitespace(character: char) -> bool {
    character.is_whitespace() || matches!(character, '\u{1c}'..='\u{1f}')
}

fn is_ascii_regex_word_character(character: char) -> bool {
    character.is_ascii_alphanumeric() || character == '_'
}

pub fn run_atomic_subject_prompt_review(
    generation_run_directory: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    ui: &mut impl PromptReviewUi,
) -> Result<PromptReviewRunOutcome> {
    let generation_run_directory = generation_run_directory.as_ref();
    let session_path = session_path.as_ref();
    let run = load_verified_atomic_subject_review_run(generation_run_directory)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = match load_session::<PromptReviewSession>(session_path)? {
        Some(session) => {
            session.validate(&run)?;
            session
        }
        None => PromptReviewSession::new(&run),
    };
    save_session(session_path, &session)?;

    while let Some(item_index) = session.next_pending_item() {
        let screen = prompt_review_item_screen(item_index, &run, &session)?;
        let action = ui.review_prompt(screen).map_err(|source| {
            io_error(
                "run SSE prompt review UI for",
                generation_run_directory,
                source,
            )
        })?;
        match action {
            ApprovalTuiAction::None => {
                return invalid("prompt review UI returned without a decision");
            }
            ApprovalTuiAction::Pause => return Ok(PromptReviewRunOutcome::Paused),
            ApprovalTuiAction::SaveComment { comment } => {
                session.record_comment(item_index, comment)?;
                save_session(session_path, &session)?;
            }
            ApprovalTuiAction::Submit { outcome, comment } => {
                let status = match outcome {
                    ReviewOutcome::Approved => PromptReviewStatus::Approved,
                    ReviewOutcome::Rejected => PromptReviewStatus::Rejected,
                };
                session.record(item_index, status, comment)?;
                save_session(session_path, &session)?;
            }
            ApprovalTuiAction::Skip { comment } => {
                session.record(item_index, PromptReviewStatus::Skipped, comment)?;
                save_session(session_path, &session)?;
            }
        }
    }

    let subjects = session.decision_counts(&run, PromptReviewItemKind::Subject);
    let subject_lists = session.decision_counts(&run, PromptReviewItemKind::SubjectList);
    Ok(PromptReviewRunOutcome::Completed {
        subjects,
        subject_lists,
    })
}

impl PromptReviewSession {
    fn new(run: &VerifiedAtomicSubjectReviewRun) -> Self {
        let items = run
            .items
            .iter()
            .map(|item| PromptReviewItemState {
                item_id: item.item_id.clone(),
                item_sha256: item.item_sha256.clone(),
                status: PromptReviewStatus::Pending,
                comment: String::new(),
            })
            .collect();
        Self {
            schema_version: PROMPT_REVIEW_SESSION_SCHEMA_VERSION,
            review_protocol: PROMPT_REVIEW_PROTOCOL.to_owned(),
            generation_run_sha256: run.identity_sha256.clone(),
            items,
        }
    }

    fn validate(&self, run: &VerifiedAtomicSubjectReviewRun) -> Result<()> {
        if self.schema_version != PROMPT_REVIEW_SESSION_SCHEMA_VERSION {
            return invalid(format!(
                "prompt review session schema {} is unsupported",
                self.schema_version
            ));
        }
        if self.review_protocol != PROMPT_REVIEW_PROTOCOL {
            return invalid("prompt review session uses a different review protocol");
        }
        if self.generation_run_sha256 != run.identity_sha256 {
            return invalid("prompt review session belongs to a different generation run");
        }
        if self.items.len() != run.items.len() {
            return invalid("prompt review session has a different item count");
        }
        for (stored, item) in self.items.iter().zip(&run.items) {
            if stored.item_id != item.item_id || stored.item_sha256 != item.item_sha256 {
                return invalid("prompt review item identity is invalid");
            }
        }
        Ok(())
    }

    fn next_pending_item(&self) -> Option<usize> {
        self.items
            .iter()
            .position(|item| item.status == PromptReviewStatus::Pending)
    }

    fn record(
        &mut self,
        item_index: usize,
        status: PromptReviewStatus,
        comment: String,
    ) -> Result<()> {
        if status == PromptReviewStatus::Pending {
            return invalid("cannot record a pending prompt-review decision");
        }
        let (current_status, current_comment) = self.item_mut(item_index)?;
        if *current_status != PromptReviewStatus::Pending {
            return invalid("prompt-review item was already decided");
        }
        *current_status = status;
        *current_comment = comment.trim().to_owned();
        Ok(())
    }

    fn record_comment(&mut self, item_index: usize, comment: String) -> Result<()> {
        let (status, current_comment) = self.item_mut(item_index)?;
        if *status != PromptReviewStatus::Pending {
            return invalid("cannot change the comment on a decided prompt-review item");
        }
        *current_comment = comment.trim().to_owned();
        Ok(())
    }

    fn comment(&self, item_index: usize) -> Result<&str> {
        self.items
            .get(item_index)
            .map(|item| item.comment.as_str())
            .ok_or_else(|| Error::ExperimentState("prompt-review item is absent".to_owned()))
    }

    fn item_mut(&mut self, item_index: usize) -> Result<(&mut PromptReviewStatus, &mut String)> {
        self.items
            .get_mut(item_index)
            .map(|item| (&mut item.status, &mut item.comment))
            .ok_or_else(|| Error::ExperimentState("prompt-review item is absent".to_owned()))
    }

    fn decision_counts(
        &self,
        run: &VerifiedAtomicSubjectReviewRun,
        kind: PromptReviewItemKind,
    ) -> PromptReviewCounts {
        prompt_review_counts(
            self.items
                .iter()
                .zip(&run.items)
                .filter(|(_, item)| item.presentation.kind() == kind)
                .map(|(stored, _)| stored.status),
        )
    }
}

fn prompt_review_counts(statuses: impl Iterator<Item = PromptReviewStatus>) -> PromptReviewCounts {
    statuses.fold(
        PromptReviewCounts {
            approved: 0,
            rejected: 0,
            skipped: 0,
        },
        |mut counts, status| {
            match status {
                PromptReviewStatus::Approved => counts.approved += 1,
                PromptReviewStatus::Rejected => counts.rejected += 1,
                PromptReviewStatus::Skipped => counts.skipped += 1,
                PromptReviewStatus::Pending => {}
            }
            counts
        },
    )
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
        title: Some(subject.proposal.label.clone()),
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
        evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
            title: "Note".to_owned(),
            annotation: String::new(),
            body: highlighted_note(&note.note.content, &subject.spans),
        }]),
    })
}

fn atomic_subject_screen(
    note_index: usize,
    note_count: usize,
    global_subject_index: usize,
    subject_count: usize,
    note: &str,
    subject: &str,
) -> AtomicSubjectPromptReviewScreen {
    AtomicSubjectPromptReviewScreen {
        heading: format!(
            "Atomic-subject prompt review · Subject {} of {} · Note {} of {}",
            global_subject_index + 1,
            subject_count,
            note_index + 1,
            note_count,
        ),
        subject: subject.to_owned(),
        question:
            "Is this a valid atomic subject explicitly and substantively discussed in this note?"
                .to_owned(),
        approve_label: "Approve".to_owned(),
        reject_label: "Disapprove".to_owned(),
        note: note.to_owned(),
    }
}

impl AtomicSubjectPromptReviewScreen {
    fn approval_screen(&self) -> ApprovalScreen {
        ApprovalScreen {
            heading: self.heading.clone(),
            title: Some(self.subject.clone()),
            scope: self.question.clone(),
            approve_label: self.approve_label.clone(),
            reject_label: self.reject_label.clone(),
            rejection_help: String::new(),
            guidance: None,
            evidence: ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
                title: "Note".to_owned(),
                annotation: String::new(),
                body: self.note.clone(),
            }]),
        }
    }
}

fn prompt_review_item_screen(
    item_index: usize,
    run: &VerifiedAtomicSubjectReviewRun,
    session: &PromptReviewSession,
) -> Result<PromptReviewScreen> {
    let item = run.items.get(item_index).ok_or_else(|| {
        Error::ExperimentState(format!("prompt-review item {item_index} is absent"))
    })?;
    match &item.presentation {
        PromptReviewItemPresentation::Subject(review) => Ok(PromptReviewScreen::Subject {
            review: review.clone(),
            comment: session.comment(item_index)?.to_owned(),
        }),
        PromptReviewItemPresentation::SubjectList {
            note_index,
            note_count,
            note,
            subject_item_indices,
        } => {
            let mut accepted_subjects = Vec::with_capacity(subject_item_indices.len());
            for &subject_item_index in subject_item_indices {
                let subject_item = run.items.get(subject_item_index).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "subject review item {subject_item_index} is absent"
                    ))
                })?;
                let PromptReviewItemPresentation::Subject(subject_screen) =
                    &subject_item.presentation
                else {
                    return invalid("subject-list review references a non-subject item");
                };
                let state = session.items.get(subject_item_index).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "subject review state {subject_item_index} is absent"
                    ))
                })?;
                if state.status == PromptReviewStatus::Pending {
                    return invalid(
                        "subject-list review was reached before its subjects were decided",
                    );
                }
                if state.status == PromptReviewStatus::Approved {
                    accepted_subjects.push(subject_screen.subject.clone());
                }
            }
            Ok(PromptReviewScreen::SubjectList {
                review: atomic_subject_list_screen(
                    *note_index,
                    *note_count,
                    note,
                    accepted_subjects,
                ),
                comment: session.comment(item_index)?.to_owned(),
            })
        }
    }
}

fn atomic_subject_list_screen(
    note_index: usize,
    note_count: usize,
    note: &str,
    accepted_subjects: Vec<String>,
) -> AtomicSubjectListReviewScreen {
    AtomicSubjectListReviewScreen {
        heading: format!(
            "Atomic-subject list review · Note {} of {}",
            note_index + 1,
            note_count
        ),
        question:
            "Are any atomic subjects missing, or do any accepted subjects express the same thing?"
                .to_owned(),
        note: note.to_owned(),
        accepted_subjects,
        approve_label: "No — complete and distinct".to_owned(),
        reject_label: "Yes — missing or repeated".to_owned(),
        guidance: ApprovalGuidance {
            title: "Decision scope".to_owned(),
            body: "This decision records only whether an atomic subject is missing or repeated. It does not change any earlier subject decision."
                .to_owned(),
        },
    }
}

impl AtomicSubjectListReviewScreen {
    fn approval_screen(&self) -> ApprovalScreen {
        let accepted_subjects = if self.accepted_subjects.is_empty() {
            "No accepted atomic subjects.".to_owned()
        } else {
            self.accepted_subjects
                .iter()
                .enumerate()
                .map(|(index, subject)| format!("{}. {subject}", index + 1))
                .collect::<Vec<_>>()
                .join("\n")
        };
        ApprovalScreen {
            heading: self.heading.clone(),
            title: None,
            scope: self.question.clone(),
            approve_label: self.approve_label.clone(),
            reject_label: self.reject_label.clone(),
            rejection_help: String::new(),
            guidance: Some(self.guidance.clone()),
            evidence: ApprovalEvidenceLayout::Stacked {
                top: ApprovalEvidence {
                    title: "Note".to_owned(),
                    annotation: String::new(),
                    body: self.note.clone(),
                },
                bottom: ApprovalEvidence {
                    title: "Accepted subjects".to_owned(),
                    annotation: String::new(),
                    body: accepted_subjects,
                },
            },
        }
    }
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
    let source_bytes =
        fs::read(&source_path).map_err(|source| io_error("read", &source_path, source))?;
    let source_sha256 = format!("{:x}", Sha256::digest(&source_bytes));
    if source_sha256 != note_set.source.sha256 {
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
    let reader = BufReader::new(source_bytes.as_slice());
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

fn load_json_snapshot<T: DeserializeOwned>(path: &Path) -> Result<(T, String)> {
    let (bytes, sha256) = load_bytes_snapshot(path)?;
    let value = serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })?;
    Ok((value, sha256))
}

fn load_bytes_snapshot(path: &Path) -> Result<(Vec<u8>, String)> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let sha256 = sha256_bytes(&bytes);
    Ok((bytes, sha256))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
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
