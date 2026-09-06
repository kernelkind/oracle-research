//! Source-bound generation proposals and durable human review for SSE subjects and masks.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span, Text};
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
    acquire_session_lock, load_session, publish_json, publish_session, save_session, value_sha256,
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
    kind: PromptReviewKind,
    identity_sha256: String,
    items: Vec<VerifiedPromptReviewItem>,
}

#[derive(Clone, Debug)]
struct VerifiedAtomicSubjectNoteReviewNote {
    note_id: String,
    note: String,
    subjects: Vec<VerifiedAtomicSubjectNoteReviewSubject>,
    list_item_id: String,
    list_item_sha256: String,
}

#[derive(Clone, Debug)]
struct VerifiedAtomicSubjectNoteReviewSubject {
    item_id: String,
    item_sha256: String,
    label: String,
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
struct ClaimGenerationManifest {
    schema_version: u32,
    mode: String,
    wrapper_sha256: String,
    engine_sha256: String,
    codex_binary: String,
    codex_version: String,
    codex_home: String,
    input_path: String,
    input_sha256: String,
    claim_envelope_version: String,
    claim_input_normalization_version: String,
    claim: PromptGenerationStage,
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
#[serde(deny_unknown_fields)]
struct ClaimGenerationOutput {
    schema_version: u32,
    manifest_sha256: String,
    notes: Vec<ClaimGenerationOutputNote>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ClaimGenerationOutputNote {
    note_id: String,
    text: String,
    claims: Vec<ClaimGenerationOutputClaim>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ClaimGenerationOutputClaim {
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

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AtomicSubjectCoverageDecision {
    Complete,
    Missing,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AtomicSubjectDistinctnessDecision {
    Distinct,
    Repeated,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AtomicSubjectNoteReviewChoice {
    pub label: String,
    pub outcome: Option<ReviewOutcome>,
    pub comment: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AtomicSubjectNoteReviewScreen {
    pub kind: PromptReviewKind,
    pub note_index: usize,
    pub note_count: usize,
    pub note: String,
    pub subjects: Vec<AtomicSubjectNoteReviewChoice>,
    pub coverage: Option<AtomicSubjectCoverageDecision>,
    pub coverage_comment: String,
    pub distinctness: Option<AtomicSubjectDistinctnessDecision>,
    pub distinctness_comment: String,
    pub selected_index: usize,
    pub finished: bool,
    pub finished_note_count: usize,
    pub decided_review_count: usize,
    pub total_review_count: usize,
    pub prior_combined_check: Option<String>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PromptReviewKind {
    AtomicSubject,
    Claim,
}

impl PromptReviewKind {
    fn note_review_protocol(self) -> &'static str {
        match self {
            Self::AtomicSubject => ATOMIC_SUBJECT_NOTE_REVIEW_PROTOCOL,
            Self::Claim => CLAIM_NOTE_REVIEW_PROTOCOL,
        }
    }

    fn list_item_prefix(self) -> &'static str {
        match self {
            Self::AtomicSubject => "subject-list:",
            Self::Claim => "claim-list:",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AtomicSubjectNoteReviewAction {
    None,
    DecideSubject {
        subject_index: usize,
        outcome: ReviewOutcome,
    },
    ClearSubject {
        subject_index: usize,
    },
    SaveSubjectComment {
        subject_index: usize,
        comment: String,
    },
    DecideCoverage {
        decision: AtomicSubjectCoverageDecision,
    },
    ClearCoverage,
    SaveCoverageComment {
        comment: String,
    },
    DecideDistinctness {
        decision: AtomicSubjectDistinctnessDecision,
    },
    ClearDistinctness,
    SaveDistinctnessComment {
        comment: String,
    },
    FinishNote,
    PreviousNote,
    NextNote,
    Pause,
}

pub trait AtomicSubjectNoteReviewUi {
    fn review_note(
        &mut self,
        model: &mut AtomicSubjectNoteReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<AtomicSubjectNoteReviewAction>;
}

impl PromptReviewUi for ReferenceTerminal {
    fn review_prompt(&mut self, screen: PromptReviewScreen) -> io::Result<ApprovalTuiAction> {
        self.review_prompt_iteration(screen.approval_screen(), screen.comment().to_owned())
    }
}

impl AtomicSubjectNoteReviewUi for ReferenceTerminal {
    fn review_note(
        &mut self,
        model: &mut AtomicSubjectNoteReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<AtomicSubjectNoteReviewAction> {
        self.run_review_model_stateful(model, drain_stale_input)
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
pub enum AtomicSubjectNoteReviewRunOutcome {
    Paused,
    Completed {
        subjects: PromptReviewCounts,
        notes_missing_subjects: usize,
        notes_with_repeated_subjects: usize,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ClaimNoteReviewRunOutcome {
    Paused,
    Completed {
        claims: PromptReviewCounts,
        notes_missing_claims: usize,
        notes_with_repeated_claims: usize,
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

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectNoteReviewSubjectState {
    item_id: String,
    item_sha256: String,
    outcome: Option<ReviewOutcome>,
    comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PriorCombinedPromptReviewCheck {
    status: PromptReviewStatus,
    comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectNoteReviewState {
    note_id: String,
    list_item_id: String,
    list_item_sha256: String,
    subjects: Vec<AtomicSubjectNoteReviewSubjectState>,
    coverage: Option<AtomicSubjectCoverageDecision>,
    coverage_comment: String,
    distinctness: Option<AtomicSubjectDistinctnessDecision>,
    distinctness_comment: String,
    prior_combined_check: Option<PriorCombinedPromptReviewCheck>,
    selected_index: usize,
    finished: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct AtomicSubjectNoteReviewSession {
    schema_version: u32,
    review_protocol: String,
    generation_run_sha256: String,
    current_note_index: usize,
    notes: Vec<AtomicSubjectNoteReviewState>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ClaimNoteReviewState {
    note_id: String,
    list_item_id: String,
    list_item_sha256: String,
    claims: Vec<AtomicSubjectNoteReviewSubjectState>,
    coverage: Option<AtomicSubjectCoverageDecision>,
    coverage_comment: String,
    distinctness: Option<AtomicSubjectDistinctnessDecision>,
    distinctness_comment: String,
    prior_combined_check: Option<PriorCombinedPromptReviewCheck>,
    selected_index: usize,
    finished: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ClaimNoteReviewSession {
    schema_version: u32,
    review_protocol: String,
    generation_run_sha256: String,
    current_note_index: usize,
    notes: Vec<ClaimNoteReviewState>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(untagged)]
enum StoredAtomicSubjectNoteReviewSession {
    V2(AtomicSubjectNoteReviewSession),
    V1(PromptReviewSession),
}

const PROMPT_REVIEW_SESSION_SCHEMA_VERSION: u32 = 1;
const PROMPT_REVIEW_PROTOCOL: &str = "atomic-subject-review-v1";
const ATOMIC_SUBJECT_NOTE_REVIEW_SESSION_SCHEMA_VERSION: u32 = 2;
const ATOMIC_SUBJECT_NOTE_REVIEW_PROTOCOL: &str = "atomic-subject-review-v2";
const CLAIM_NOTE_REVIEW_SESSION_SCHEMA_VERSION: u32 = 1;
const CLAIM_NOTE_REVIEW_PROTOCOL: &str = "claim-review-v1";
const SUBJECT_RESPONSE_SCHEMA_SHA256: &str =
    "ffa0aa2d4a52a1b30f41f0a1761e455471a5127c0e20d74aaeea575a0df2226a";
const CLAIM_RESPONSE_SCHEMA_SHA256: &str =
    "1365a3d239f08657226fb771b8e7db48974882b8d580005de6e651d288be53a3";

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
            let spans = resolve_fragments(
                &subject.fragments,
                &note.content,
                &proposed.note_id,
                &subject.subject_id,
            )?;
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
            ApprovalTuiAction::None | ApprovalTuiAction::PreviousItem | ApprovalTuiAction::NextItem => {
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
        kind: PromptReviewKind::AtomicSubject,
        identity_sha256,
        items,
    })
}

fn load_verified_claim_review_run(run_directory: &Path) -> Result<VerifiedAtomicSubjectReviewRun> {
    if run_directory.join("runner-upgrades.jsonl").exists() {
        return invalid("claim review requires a fresh generation run without runner upgrades");
    }
    let manifest_path = run_directory.join("manifest.json");
    let (manifest, manifest_sha256): (ClaimGenerationManifest, String) =
        load_json_snapshot(&manifest_path)?;
    validate_claim_generation_manifest(&manifest)?;

    let input_path = resolve_relative(&manifest_path, &manifest.input_path);
    let (input, input_sha256): (PromptGenerationInput, String) = load_json_snapshot(&input_path)?;
    if input_sha256 != manifest.input_sha256 {
        return invalid(format!(
            "claim generation input `{}` does not match its manifest binding",
            input_path.display()
        ));
    }
    if input.schema_version != 1 || input.notes.is_empty() {
        return invalid("claim generation input schema or note list is invalid");
    }

    let output_path = run_directory.join("output.json");
    let (output, output_sha256): (ClaimGenerationOutput, String) =
        load_json_snapshot(&output_path)?;
    if output.schema_version != 1 || output.manifest_sha256 != manifest_sha256 {
        return invalid("claim generation output does not match its manifest");
    }
    if output.notes.len() != input.notes.len() {
        return invalid("claim generation output does not match its input note count");
    }

    let results_path = run_directory.join("results.jsonl");
    let (results_bytes, results_sha256) = load_bytes_snapshot(&results_path)?;
    let mut results = latest_claim_generation_results(
        &results_bytes,
        &results_path,
        &manifest,
        &manifest_sha256,
        &input,
    )?;
    let identity_sha256 = value_sha256(&PromptReviewRunIdentity {
        review_protocol: CLAIM_NOTE_REVIEW_PROTOCOL,
        manifest_sha256: &manifest_sha256,
        input_sha256: &input_sha256,
        results_sha256: &results_sha256,
        output_sha256: &output_sha256,
    })?;
    let claim_count = output.notes.iter().map(|note| note.claims.len()).sum();
    let mut seen_note_ids = BTreeSet::<String>::new();
    let mut seen_item_ids = BTreeSet::<String>::new();
    let mut items = Vec::with_capacity(claim_count + input.notes.len());
    let mut global_claim_index = 0;
    for (note_index, (input_note, output_note)) in input.notes.iter().zip(&output.notes).enumerate()
    {
        if input_note.note_id.trim().is_empty()
            || input_note.text.trim().is_empty()
            || !seen_note_ids.insert(input_note.note_id.clone())
        {
            return invalid(format!(
                "claim generation input note {} has an invalid or duplicate identity",
                note_index + 1
            ));
        }
        if output_note.note_id != input_note.note_id || output_note.text != input_note.text {
            return invalid(format!(
                "claim generation output note {} does not preserve the input note",
                note_index + 1
            ));
        }
        let labels = output_note
            .claims
            .iter()
            .map(|claim| claim.text.clone())
            .collect::<Vec<_>>();
        let claim_key = format!("claim:{}", input_note.note_id);
        let claim_result = take_generation_result(&mut results, &claim_key)?;
        let rendered_prompt = render_claim_prompt(&manifest.claim.prompt, &input_note.text);
        validate_claim_generation_result(
            &claim_result,
            &manifest,
            &manifest_sha256,
            &claim_key,
            &input_note.note_id,
            &rendered_prompt,
            &serde_json::to_value(&labels).map_err(|source| Error::Manifest {
                operation: "encode",
                path: output_path.clone(),
                source,
            })?,
        )?;

        let first_claim_item_index = items.len();
        for (claim_index, generated) in output_note.claims.iter().enumerate() {
            if generated.text.trim().is_empty() || generated.source_index != claim_index {
                return invalid(format!(
                    "claim generation output note {} has an invalid claim {}",
                    input_note.note_id,
                    claim_index + 1
                ));
            }
            let item_id = format!("claim:{}:{claim_index}", input_note.note_id);
            if !seen_item_ids.insert(item_id.clone()) {
                return invalid("generated claim review item identities collided");
            }
            let item_sha256 = value_sha256(&(
                identity_sha256.as_str(),
                "claim",
                input_note.note_id.as_str(),
                input_note.text.as_str(),
                claim_index,
                generated.text.as_str(),
            ))?;
            items.push(VerifiedPromptReviewItem {
                item_id,
                item_sha256,
                presentation: PromptReviewItemPresentation::Subject(atomic_subject_screen(
                    note_index,
                    input.notes.len(),
                    global_claim_index,
                    claim_count,
                    &input_note.text,
                    &generated.text,
                )),
            });
            global_claim_index += 1;
        }
        let item_id = format!("claim-list:{}", input_note.note_id);
        if !seen_item_ids.insert(item_id.clone()) {
            return invalid("generated claim-list review item identities collided");
        }
        let item_sha256 = value_sha256(&(
            identity_sha256.as_str(),
            "claim_list",
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
                subject_item_indices: (first_claim_item_index..items.len()).collect(),
            },
        });
    }
    if let Some(unexpected) = results.keys().next() {
        return invalid(format!(
            "claim generation ledger contains unexpected latest result `{unexpected}`"
        ));
    }
    Ok(VerifiedAtomicSubjectReviewRun {
        kind: PromptReviewKind::Claim,
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

fn validate_claim_generation_manifest(manifest: &ClaimGenerationManifest) -> Result<()> {
    if manifest.schema_version != 1 || manifest.mode != "claim_generation" {
        return invalid("claim review requires a claim generation run");
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("sse_multivector");
    let (_, wrapper_sha256) = load_bytes_snapshot(&root.join("claim_exec.py"))?;
    let (_, engine_sha256) = load_bytes_snapshot(&root.join("codex_exec.py"))?;
    if !is_lower_hex(&manifest.input_sha256, 64)
        || manifest.wrapper_sha256 != wrapper_sha256
        || manifest.engine_sha256 != engine_sha256
        || manifest.codex_binary.trim().is_empty()
        || manifest.codex_version.trim().is_empty()
        || manifest.codex_home.trim().is_empty()
        || manifest.input_path.trim().is_empty()
        || manifest.claim_envelope_version != "exact-note-text-v1"
        || manifest.claim_input_normalization_version != "none-v1"
    {
        return invalid("claim generation manifest is incomplete");
    }
    if manifest.isolation != expected_prompt_generation_isolation() {
        return invalid("claim generation did not use a fresh isolated process per job");
    }
    validate_prompt_generation_stage(
        &manifest.claim,
        "claim",
        expected_claim_response_schema(),
        CLAIM_RESPONSE_SCHEMA_SHA256,
    )
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

fn expected_claim_response_schema() -> serde_json::Value {
    serde_json::json!({
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {"type": "string", "minLength": 1}
            }
        },
        "required": ["claims"],
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

fn latest_claim_generation_results(
    bytes: &[u8],
    path: &Path,
    manifest: &ClaimGenerationManifest,
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
            return invalid("claim generation input contains an invalid or duplicate note");
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
                "claim generation result line {} is empty",
                index + 1
            ));
        }
        let result: PromptGenerationResult =
            serde_json::from_slice(line).map_err(|source| Error::Manifest {
                operation: "decode claim generation result from",
                path: path.to_owned(),
                source,
            })?;
        if result.schema_version != 1
            || result.manifest_sha256 != manifest_sha256
            || result.attempt == 0
            || result.job_key.trim().is_empty()
        {
            return invalid(format!(
                "claim generation result line {} has an invalid identity",
                index + 1
            ));
        }
        let expected_attempt = latest
            .get(&result.job_key)
            .map_or(1, |previous| previous.attempt + 1);
        if result.attempt != expected_attempt {
            return invalid(format!(
                "claim generation result `{}` has a nonconsecutive attempt",
                result.job_key
            ));
        }
        let Some(note_text) = note_texts.get(result.note_id.as_str()).copied() else {
            return invalid(format!(
                "claim generation result `{}` names an unknown note",
                result.job_key
            ));
        };
        if result.stage != "claim" || result.job_key != format!("claim:{}", result.note_id) {
            return invalid(format!(
                "claim generation result `{}` has an invalid claim identity",
                result.job_key
            ));
        }
        let rendered_prompt = render_claim_prompt(&manifest.claim.prompt, note_text);
        if result.wrapper_sha256 != manifest.wrapper_sha256
            || result.codex_version != manifest.codex_version
            || result.model != manifest.claim.model
            || result.reasoning_effort != manifest.claim.reasoning_effort
            || result.prompt_sha256 != sha256_bytes(rendered_prompt.as_bytes())
            || result.response_schema_sha256 != manifest.claim.response_schema_sha256
            || !matches!(result.status.as_str(), "succeeded" | "failed")
        {
            return invalid(format!(
                "claim generation result `{}` does not match its rendered prompt or generation contract",
                result.job_key
            ));
        }
        if result.status == "succeeded" {
            validate_claim_result_output(&result, &result.response, &result.job_key)?;
            result
                .response
                .as_array()
                .ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "claim generation result `{}` response is not an array",
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
                                "claim generation result `{}` contains an invalid response item",
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
        return invalid("claim generation result ledger is empty");
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

#[allow(clippy::too_many_arguments)]
fn validate_claim_generation_result(
    result: &PromptGenerationResult,
    manifest: &ClaimGenerationManifest,
    manifest_sha256: &str,
    job_key: &str,
    note_id: &str,
    rendered_prompt: &str,
    expected_response: &serde_json::Value,
) -> Result<()> {
    if result.schema_version != 1
        || result.manifest_sha256 != manifest_sha256
        || result.job_key != job_key
        || result.stage != "claim"
        || result.note_id != note_id
        || result.status != "succeeded"
        || result.wrapper_sha256 != manifest.wrapper_sha256
        || result.codex_version != manifest.codex_version
        || result.model != manifest.claim.model
        || result.reasoning_effort != manifest.claim.reasoning_effort
        || result.prompt_sha256 != sha256_bytes(rendered_prompt.as_bytes())
        || result.response_schema_sha256 != manifest.claim.response_schema_sha256
        || &result.response != expected_response
    {
        return invalid(format!(
            "claim generation output does not match preserved result or rendered prompt `{job_key}`"
        ));
    }
    validate_claim_result_output(result, expected_response, job_key)
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

fn validate_claim_result_output(
    result: &PromptGenerationResult,
    expected_response: &serde_json::Value,
    job_key: &str,
) -> Result<()> {
    let raw = result.final_output_raw.as_deref().ok_or_else(|| {
        Error::ExperimentState(format!(
            "claim generation result `{job_key}` has no final output"
        ))
    })?;
    let expected_sha256 = result.final_output_sha256.as_deref().ok_or_else(|| {
        Error::ExperimentState(format!(
            "claim generation result `{job_key}` has no final output hash"
        ))
    })?;
    if sha256_bytes(raw.as_bytes()) != expected_sha256 {
        return invalid(format!(
            "claim generation result `{job_key}` has invalid final output provenance"
        ));
    }
    let raw_response: serde_json::Value =
        serde_json::from_str(raw).map_err(|source| Error::Manifest {
            operation: "decode claim generation final output from",
            path: PathBuf::from(job_key),
            source,
        })?;
    if raw_response != serde_json::json!({"claims": expected_response}) {
        return invalid(format!(
            "claim generation result `{job_key}` final output does not match its response"
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

fn render_claim_prompt(prompt: &str, note: &str) -> String {
    format!("{prompt}\n\nText:\n{note}")
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
            ApprovalTuiAction::None | ApprovalTuiAction::PreviousItem | ApprovalTuiAction::NextItem => {
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

pub fn run_atomic_subject_note_review(
    generation_run_directory: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    ui: &mut impl AtomicSubjectNoteReviewUi,
) -> Result<AtomicSubjectNoteReviewRunOutcome> {
    let generation_run_directory = generation_run_directory.as_ref();
    let session_path = session_path.as_ref();
    let run = load_verified_atomic_subject_review_run(generation_run_directory)?;
    let notes = run.note_review_notes()?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = match load_session::<StoredAtomicSubjectNoteReviewSession>(session_path)? {
        Some(StoredAtomicSubjectNoteReviewSession::V2(session)) => {
            session.validate(&run, &notes)?;
            session
        }
        Some(StoredAtomicSubjectNoteReviewSession::V1(legacy)) => {
            legacy.validate(&run)?;
            preserve_legacy_prompt_review_session(session_path, &legacy)?;
            AtomicSubjectNoteReviewSession::migrate(legacy, &run, &notes)?
        }
        None => AtomicSubjectNoteReviewSession::new(&run, &notes),
    };
    save_session(session_path, &session)?;

    let mut model = AtomicSubjectNoteReviewTuiModel::new(session.screen(&notes)?);
    let mut drain_stale_input = true;
    loop {
        let action = ui
            .review_note(&mut model, drain_stale_input)
            .map_err(|source| {
                io_error(
                    "run SSE atomic-subject note review UI for",
                    generation_run_directory,
                    source,
                )
            })?;
        drain_stale_input = false;
        session.set_selected_index(model.selected_index())?;
        match action {
            AtomicSubjectNoteReviewAction::None => {
                return invalid("atomic-subject note review UI returned without an action");
            }
            AtomicSubjectNoteReviewAction::Pause => {
                save_session(session_path, &session)?;
                return Ok(if session.all_finished() {
                    session.completed_outcome()
                } else {
                    AtomicSubjectNoteReviewRunOutcome::Paused
                });
            }
            AtomicSubjectNoteReviewAction::DecideSubject {
                subject_index,
                outcome,
            } => session.decide_subject(subject_index, outcome)?,
            AtomicSubjectNoteReviewAction::ClearSubject { subject_index } => {
                session.clear_subject(subject_index)?
            }
            AtomicSubjectNoteReviewAction::SaveSubjectComment {
                subject_index,
                comment,
            } => session.save_subject_comment(subject_index, comment)?,
            AtomicSubjectNoteReviewAction::DecideCoverage { decision } => {
                session.decide_coverage(decision)?
            }
            AtomicSubjectNoteReviewAction::ClearCoverage => session.clear_coverage()?,
            AtomicSubjectNoteReviewAction::SaveCoverageComment { comment } => {
                session.save_coverage_comment(comment)?
            }
            AtomicSubjectNoteReviewAction::DecideDistinctness { decision } => {
                session.decide_distinctness(decision)?
            }
            AtomicSubjectNoteReviewAction::ClearDistinctness => session.clear_distinctness()?,
            AtomicSubjectNoteReviewAction::SaveDistinctnessComment { comment } => {
                session.save_distinctness_comment(comment)?
            }
            AtomicSubjectNoteReviewAction::FinishNote => {
                session.finish_current_note()?;
                if !session.all_finished() {
                    session.move_to_next_unfinished()?;
                }
            }
            AtomicSubjectNoteReviewAction::PreviousNote => session.move_previous()?,
            AtomicSubjectNoteReviewAction::NextNote => session.move_next()?,
        }
        save_session(session_path, &session)?;
        model.replace_screen(session.screen(&notes)?);
    }
}

pub fn run_claim_note_review(
    generation_run_directory: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    ui: &mut impl AtomicSubjectNoteReviewUi,
) -> Result<AtomicSubjectNoteReviewRunOutcome> {
    let generation_run_directory = generation_run_directory.as_ref();
    let session_path = session_path.as_ref();
    let run = load_verified_claim_review_run(generation_run_directory)?;
    let notes = run.note_review_notes()?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = match load_session::<ClaimNoteReviewSession>(session_path)? {
        Some(session) => session.into_atomic(),
        None => AtomicSubjectNoteReviewSession::new(&run, &notes),
    };
    session.validate(&run, &notes)?;
    save_claim_note_review_session(session_path, &session)?;

    let mut model = AtomicSubjectNoteReviewTuiModel::new(session.screen(&notes)?);
    let mut drain_stale_input = true;
    loop {
        let action = ui
            .review_note(&mut model, drain_stale_input)
            .map_err(|source| {
                io_error(
                    "run SSE claim note review UI for",
                    generation_run_directory,
                    source,
                )
            })?;
        drain_stale_input = false;
        session.set_selected_index(model.selected_index())?;
        match action {
            AtomicSubjectNoteReviewAction::None => {
                return invalid("claim note review UI returned without an action");
            }
            AtomicSubjectNoteReviewAction::Pause => {
                save_claim_note_review_session(session_path, &session)?;
                return Ok(if session.all_finished() {
                    session.completed_outcome()
                } else {
                    AtomicSubjectNoteReviewRunOutcome::Paused
                });
            }
            AtomicSubjectNoteReviewAction::DecideSubject {
                subject_index,
                outcome,
            } => session.decide_subject(subject_index, outcome)?,
            AtomicSubjectNoteReviewAction::ClearSubject { subject_index } => {
                session.clear_subject(subject_index)?
            }
            AtomicSubjectNoteReviewAction::SaveSubjectComment {
                subject_index,
                comment,
            } => session.save_subject_comment(subject_index, comment)?,
            AtomicSubjectNoteReviewAction::DecideCoverage { decision } => {
                session.decide_coverage(decision)?
            }
            AtomicSubjectNoteReviewAction::ClearCoverage => session.clear_coverage()?,
            AtomicSubjectNoteReviewAction::SaveCoverageComment { comment } => {
                session.save_coverage_comment(comment)?
            }
            AtomicSubjectNoteReviewAction::DecideDistinctness { decision } => {
                session.decide_distinctness(decision)?
            }
            AtomicSubjectNoteReviewAction::ClearDistinctness => session.clear_distinctness()?,
            AtomicSubjectNoteReviewAction::SaveDistinctnessComment { comment } => {
                session.save_distinctness_comment(comment)?
            }
            AtomicSubjectNoteReviewAction::FinishNote => {
                session.finish_current_note()?;
                if !session.all_finished() {
                    session.move_to_next_unfinished()?;
                }
            }
            AtomicSubjectNoteReviewAction::PreviousNote => session.move_previous()?,
            AtomicSubjectNoteReviewAction::NextNote => session.move_next()?,
        }
        save_claim_note_review_session(session_path, &session)?;
        model.replace_screen(session.screen(&notes)?);
    }
}

fn save_claim_note_review_session(
    session_path: &Path,
    session: &AtomicSubjectNoteReviewSession,
) -> Result<()> {
    save_session(session_path, &ClaimNoteReviewSession::from_atomic(session))
}

impl ClaimNoteReviewSession {
    fn from_atomic(session: &AtomicSubjectNoteReviewSession) -> Self {
        Self {
            schema_version: CLAIM_NOTE_REVIEW_SESSION_SCHEMA_VERSION,
            review_protocol: session.review_protocol.clone(),
            generation_run_sha256: session.generation_run_sha256.clone(),
            current_note_index: session.current_note_index,
            notes: session
                .notes
                .iter()
                .map(|note| ClaimNoteReviewState {
                    note_id: note.note_id.clone(),
                    list_item_id: note.list_item_id.clone(),
                    list_item_sha256: note.list_item_sha256.clone(),
                    claims: note.subjects.clone(),
                    coverage: note.coverage,
                    coverage_comment: note.coverage_comment.clone(),
                    distinctness: note.distinctness,
                    distinctness_comment: note.distinctness_comment.clone(),
                    prior_combined_check: note.prior_combined_check.clone(),
                    selected_index: note.selected_index,
                    finished: note.finished,
                })
                .collect(),
        }
    }

    fn into_atomic(self) -> AtomicSubjectNoteReviewSession {
        AtomicSubjectNoteReviewSession {
            schema_version: ATOMIC_SUBJECT_NOTE_REVIEW_SESSION_SCHEMA_VERSION,
            review_protocol: self.review_protocol,
            generation_run_sha256: self.generation_run_sha256,
            current_note_index: self.current_note_index,
            notes: self
                .notes
                .into_iter()
                .map(|note| AtomicSubjectNoteReviewState {
                    note_id: note.note_id,
                    list_item_id: note.list_item_id,
                    list_item_sha256: note.list_item_sha256,
                    subjects: note.claims,
                    coverage: note.coverage,
                    coverage_comment: note.coverage_comment,
                    distinctness: note.distinctness,
                    distinctness_comment: note.distinctness_comment,
                    prior_combined_check: note.prior_combined_check,
                    selected_index: note.selected_index,
                    finished: note.finished,
                })
                .collect(),
        }
    }
}

fn preserve_legacy_prompt_review_session(
    session_path: &Path,
    legacy: &PromptReviewSession,
) -> Result<()> {
    let mut backup_name = session_path.as_os_str().to_os_string();
    backup_name.push(".v1-backup");
    let backup_path = PathBuf::from(backup_name);
    if let Some(existing) = load_session::<PromptReviewSession>(&backup_path)? {
        if &existing == legacy {
            return Ok(());
        }
        return invalid(format!(
            "legacy prompt-review backup `{}` differs from the session being migrated",
            backup_path.display()
        ));
    }
    publish_session(&backup_path, legacy)
}

impl VerifiedAtomicSubjectReviewRun {
    fn note_review_notes(&self) -> Result<Vec<VerifiedAtomicSubjectNoteReviewNote>> {
        let mut notes = Vec::new();
        for item in &self.items {
            let PromptReviewItemPresentation::SubjectList {
                note_index,
                note_count,
                note,
                subject_item_indices,
            } = &item.presentation
            else {
                continue;
            };
            if *note_index != notes.len() || *note_count == 0 {
                return invalid("prompt-review note ordering is invalid");
            }
            let note_id = item
                .item_id
                .strip_prefix(self.kind.list_item_prefix())
                .filter(|value| !value.is_empty())
                .ok_or_else(|| {
                    Error::ExperimentState("prompt-review note identity is invalid".to_owned())
                })?
                .to_owned();
            let mut subjects = Vec::with_capacity(subject_item_indices.len());
            for &subject_item_index in subject_item_indices {
                let subject_item = self.items.get(subject_item_index).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "subject review item {subject_item_index} is absent"
                    ))
                })?;
                let PromptReviewItemPresentation::Subject(subject_screen) =
                    &subject_item.presentation
                else {
                    return invalid("subject-list review references a non-subject item");
                };
                subjects.push(VerifiedAtomicSubjectNoteReviewSubject {
                    item_id: subject_item.item_id.clone(),
                    item_sha256: subject_item.item_sha256.clone(),
                    label: subject_screen.subject.clone(),
                });
            }
            notes.push(VerifiedAtomicSubjectNoteReviewNote {
                note_id,
                note: note.clone(),
                subjects,
                list_item_id: item.item_id.clone(),
                list_item_sha256: item.item_sha256.clone(),
            });
        }
        if notes.is_empty() || notes.iter().any(|note| note.note.trim().is_empty()) {
            return invalid("prompt-review run contains no valid notes");
        }
        Ok(notes)
    }
}

impl AtomicSubjectNoteReviewSession {
    fn new(
        run: &VerifiedAtomicSubjectReviewRun,
        notes: &[VerifiedAtomicSubjectNoteReviewNote],
    ) -> Self {
        Self {
            schema_version: ATOMIC_SUBJECT_NOTE_REVIEW_SESSION_SCHEMA_VERSION,
            review_protocol: run.kind.note_review_protocol().to_owned(),
            generation_run_sha256: run.identity_sha256.clone(),
            current_note_index: 0,
            notes: notes
                .iter()
                .map(|note| AtomicSubjectNoteReviewState {
                    note_id: note.note_id.clone(),
                    list_item_id: note.list_item_id.clone(),
                    list_item_sha256: note.list_item_sha256.clone(),
                    subjects: note
                        .subjects
                        .iter()
                        .map(|subject| AtomicSubjectNoteReviewSubjectState {
                            item_id: subject.item_id.clone(),
                            item_sha256: subject.item_sha256.clone(),
                            outcome: None,
                            comment: String::new(),
                        })
                        .collect(),
                    coverage: None,
                    coverage_comment: String::new(),
                    distinctness: None,
                    distinctness_comment: String::new(),
                    prior_combined_check: None,
                    selected_index: 0,
                    finished: false,
                })
                .collect(),
        }
    }

    fn migrate(
        legacy: PromptReviewSession,
        run: &VerifiedAtomicSubjectReviewRun,
        notes: &[VerifiedAtomicSubjectNoteReviewNote],
    ) -> Result<Self> {
        let first_pending_item_id = legacy
            .items
            .iter()
            .find(|item| item.status == PromptReviewStatus::Pending)
            .map(|item| item.item_id.clone());
        let legacy_by_id = legacy
            .items
            .into_iter()
            .map(|item| (item.item_id.clone(), item))
            .collect::<BTreeMap<_, _>>();
        let mut session = Self::new(run, notes);
        for (note_state, note) in session.notes.iter_mut().zip(notes) {
            for (subject_state, subject) in note_state.subjects.iter_mut().zip(&note.subjects) {
                let legacy_state = legacy_by_id.get(&subject.item_id).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "legacy prompt-review subject `{}` is absent",
                        subject.item_id
                    ))
                })?;
                subject_state.comment = legacy_state.comment.clone();
                subject_state.outcome = match legacy_state.status {
                    PromptReviewStatus::Approved => Some(ReviewOutcome::Approved),
                    PromptReviewStatus::Rejected => Some(ReviewOutcome::Rejected),
                    PromptReviewStatus::Pending | PromptReviewStatus::Skipped => None,
                };
            }
            let all_subjects_decided = note_state
                .subjects
                .iter()
                .all(|subject| subject.outcome.is_some());
            let legacy_list = legacy_by_id.get(&note.list_item_id).ok_or_else(|| {
                Error::ExperimentState(format!(
                    "legacy prompt-review list `{}` is absent",
                    note.list_item_id
                ))
            })?;
            let mapped_approved =
                legacy_list.status == PromptReviewStatus::Approved && all_subjects_decided;
            if mapped_approved {
                note_state.coverage = Some(AtomicSubjectCoverageDecision::Complete);
                note_state.distinctness = Some(AtomicSubjectDistinctnessDecision::Distinct);
                note_state.finished = true;
            }
            if (!mapped_approved && legacy_list.status != PromptReviewStatus::Pending)
                || !legacy_list.comment.is_empty()
            {
                note_state.prior_combined_check = Some(PriorCombinedPromptReviewCheck {
                    status: legacy_list.status,
                    comment: legacy_list.comment.clone(),
                });
            }
            note_state.selected_index = note_state
                .subjects
                .iter()
                .position(|subject| subject.outcome.is_none())
                .unwrap_or(note_state.subjects.len());
        }
        session.current_note_index = first_pending_item_id
            .as_deref()
            .and_then(|item_id| {
                notes.iter().position(|note| {
                    note.list_item_id == item_id
                        || note
                            .subjects
                            .iter()
                            .any(|subject| subject.item_id == item_id)
                })
            })
            .or_else(|| session.notes.iter().position(|note| !note.finished))
            .unwrap_or(0);
        if let Some(item_id) = first_pending_item_id.as_deref()
            && let Some(subject_index) = notes[session.current_note_index]
                .subjects
                .iter()
                .position(|subject| subject.item_id == item_id)
        {
            session.notes[session.current_note_index].selected_index = subject_index;
        } else if first_pending_item_id.as_deref()
            == Some(notes[session.current_note_index].list_item_id.as_str())
        {
            session.notes[session.current_note_index].selected_index =
                notes[session.current_note_index].subjects.len();
        }
        session.validate(run, notes)?;
        Ok(session)
    }

    fn validate(
        &self,
        run: &VerifiedAtomicSubjectReviewRun,
        notes: &[VerifiedAtomicSubjectNoteReviewNote],
    ) -> Result<()> {
        if self.schema_version != ATOMIC_SUBJECT_NOTE_REVIEW_SESSION_SCHEMA_VERSION {
            return invalid(format!(
                "atomic-subject note review session schema {} is unsupported",
                self.schema_version
            ));
        }
        if self.review_protocol != run.kind.note_review_protocol() {
            return invalid("atomic-subject note review session uses a different protocol");
        }
        if self.generation_run_sha256 != run.identity_sha256 {
            return invalid(
                "atomic-subject note review session belongs to a different generation run",
            );
        }
        if self.notes.len() != notes.len() || self.current_note_index >= notes.len() {
            return invalid(
                "atomic-subject note review session has an invalid note count or position",
            );
        }
        for (stored, note) in self.notes.iter().zip(notes) {
            if stored.note_id != note.note_id
                || stored.list_item_id != note.list_item_id
                || stored.list_item_sha256 != note.list_item_sha256
                || stored.subjects.len() != note.subjects.len()
            {
                return invalid("atomic-subject note review note identity is invalid");
            }
            for (stored_subject, subject) in stored.subjects.iter().zip(&note.subjects) {
                if stored_subject.item_id != subject.item_id
                    || stored_subject.item_sha256 != subject.item_sha256
                {
                    return invalid("atomic-subject note review subject identity is invalid");
                }
            }
            if stored.selected_index >= atomic_subject_review_item_count(stored) {
                return invalid("atomic-subject note review selection is invalid");
            }
            if stored.finished
                && (stored
                    .subjects
                    .iter()
                    .any(|subject| subject.outcome.is_none())
                    || stored.coverage.is_none()
                    || stored.distinctness.is_none())
            {
                return invalid("finished atomic-subject note review is incomplete");
            }
        }
        Ok(())
    }

    fn screen(
        &self,
        notes: &[VerifiedAtomicSubjectNoteReviewNote],
    ) -> Result<AtomicSubjectNoteReviewScreen> {
        let state = self.notes.get(self.current_note_index).ok_or_else(|| {
            Error::ExperimentState("current atomic-subject review note is absent".to_owned())
        })?;
        let note = notes.get(self.current_note_index).ok_or_else(|| {
            Error::ExperimentState("current verified atomic-subject note is absent".to_owned())
        })?;
        let subjects = state
            .subjects
            .iter()
            .zip(&note.subjects)
            .map(|(stored, subject)| AtomicSubjectNoteReviewChoice {
                label: subject.label.clone(),
                outcome: stored.outcome,
                comment: stored.comment.clone(),
            })
            .collect();
        let prior_combined_check = state.prior_combined_check.as_ref().map(|prior| {
            let status = match prior.status {
                PromptReviewStatus::Pending => "pending",
                PromptReviewStatus::Approved => "approved",
                PromptReviewStatus::Rejected => "rejected",
                PromptReviewStatus::Skipped => "skipped",
            };
            if prior.comment.is_empty() {
                format!("Previous combined list check: {status}. Review Coverage and Distinctness separately.")
            } else {
                format!(
                    "Previous combined list check: {status} — {}. Review Coverage and Distinctness separately.",
                    prior.comment
                )
            }
        });
        Ok(AtomicSubjectNoteReviewScreen {
            kind: if self.review_protocol == CLAIM_NOTE_REVIEW_PROTOCOL {
                PromptReviewKind::Claim
            } else {
                PromptReviewKind::AtomicSubject
            },
            note_index: self.current_note_index,
            note_count: notes.len(),
            note: note.note.clone(),
            subjects,
            coverage: state.coverage,
            coverage_comment: state.coverage_comment.clone(),
            distinctness: state.distinctness,
            distinctness_comment: state.distinctness_comment.clone(),
            selected_index: state.selected_index,
            finished: state.finished,
            finished_note_count: self.notes.iter().filter(|note| note.finished).count(),
            decided_review_count: self
                .notes
                .iter()
                .map(atomic_subject_note_decided_count)
                .sum(),
            total_review_count: self
                .notes
                .iter()
                .map(atomic_subject_review_item_count)
                .sum(),
            prior_combined_check,
        })
    }

    fn current_note_mut(&mut self) -> Result<&mut AtomicSubjectNoteReviewState> {
        self.notes.get_mut(self.current_note_index).ok_or_else(|| {
            Error::ExperimentState("current atomic-subject review note is absent".to_owned())
        })
    }

    fn set_selected_index(&mut self, selected_index: usize) -> Result<()> {
        let note = self.current_note_mut()?;
        note.selected_index = selected_index.min(atomic_subject_review_item_count(note) - 1);
        Ok(())
    }

    fn decide_subject(&mut self, subject_index: usize, outcome: ReviewOutcome) -> Result<()> {
        let note = self.current_note_mut()?;
        let subject = note.subjects.get_mut(subject_index).ok_or_else(|| {
            Error::ExperimentState(format!("atomic-subject proposal {subject_index} is absent"))
        })?;
        let was_pending = subject.outcome.is_none();
        if subject.outcome != Some(outcome) {
            subject.outcome = Some(outcome);
            note.finished = false;
            invalidate_note_checks(note);
        }
        if was_pending && outcome == ReviewOutcome::Approved {
            note.selected_index =
                next_pending_review_item(note, subject_index).unwrap_or(subject_index);
        } else {
            note.selected_index = subject_index;
        }
        Ok(())
    }

    fn clear_subject(&mut self, subject_index: usize) -> Result<()> {
        let note = self.current_note_mut()?;
        let subject = note.subjects.get_mut(subject_index).ok_or_else(|| {
            Error::ExperimentState(format!("atomic-subject proposal {subject_index} is absent"))
        })?;
        subject.outcome = None;
        note.selected_index = subject_index;
        note.finished = false;
        invalidate_note_checks(note);
        Ok(())
    }

    fn save_subject_comment(&mut self, subject_index: usize, comment: String) -> Result<()> {
        let note = self.current_note_mut()?;
        let subject = note.subjects.get_mut(subject_index).ok_or_else(|| {
            Error::ExperimentState(format!("atomic-subject proposal {subject_index} is absent"))
        })?;
        subject.comment = comment.trim().to_owned();
        note.selected_index = subject_index;
        Ok(())
    }

    fn decide_coverage(&mut self, decision: AtomicSubjectCoverageDecision) -> Result<()> {
        let note = self.current_note_mut()?;
        let row = note.subjects.len();
        let was_pending = note.coverage.is_none();
        if note.coverage != Some(decision) {
            note.coverage = Some(decision);
            note.finished = false;
        }
        note.selected_index = if was_pending && decision == AtomicSubjectCoverageDecision::Complete
        {
            next_pending_review_item(note, row).unwrap_or(row)
        } else {
            row
        };
        Ok(())
    }

    fn clear_coverage(&mut self) -> Result<()> {
        let note = self.current_note_mut()?;
        note.coverage = None;
        note.finished = false;
        note.selected_index = note.subjects.len();
        Ok(())
    }

    fn save_coverage_comment(&mut self, comment: String) -> Result<()> {
        let note = self.current_note_mut()?;
        note.coverage_comment = comment.trim().to_owned();
        note.selected_index = note.subjects.len();
        Ok(())
    }

    fn decide_distinctness(&mut self, decision: AtomicSubjectDistinctnessDecision) -> Result<()> {
        let note = self.current_note_mut()?;
        let row = note.subjects.len() + 1;
        if note.distinctness != Some(decision) {
            note.distinctness = Some(decision);
            note.finished = false;
        }
        note.selected_index = row;
        Ok(())
    }

    fn clear_distinctness(&mut self) -> Result<()> {
        let note = self.current_note_mut()?;
        note.distinctness = None;
        note.finished = false;
        note.selected_index = note.subjects.len() + 1;
        Ok(())
    }

    fn save_distinctness_comment(&mut self, comment: String) -> Result<()> {
        let note = self.current_note_mut()?;
        note.distinctness_comment = comment.trim().to_owned();
        note.selected_index = note.subjects.len() + 1;
        Ok(())
    }

    fn finish_current_note(&mut self) -> Result<()> {
        let note = self.current_note_mut()?;
        if note
            .subjects
            .iter()
            .any(|subject| subject.outcome.is_none())
        {
            return invalid(
                "every proposed atomic subject must be decided before finishing the note",
            );
        }
        if note.coverage.is_none() {
            return invalid("coverage must be decided before finishing the note");
        }
        if note.distinctness.is_none() {
            return invalid("distinctness must be decided before finishing the note");
        }
        note.finished = true;
        Ok(())
    }

    fn move_previous(&mut self) -> Result<()> {
        if self.notes.is_empty() {
            return invalid("atomic-subject note review contains no notes");
        }
        self.current_note_index = if self.current_note_index == 0 {
            self.notes.len() - 1
        } else {
            self.current_note_index - 1
        };
        Ok(())
    }

    fn move_next(&mut self) -> Result<()> {
        if self.notes.is_empty() {
            return invalid("atomic-subject note review contains no notes");
        }
        self.current_note_index = (self.current_note_index + 1) % self.notes.len();
        Ok(())
    }

    fn move_to_next_unfinished(&mut self) -> Result<()> {
        let note_count = self.notes.len();
        for offset in 1..=note_count {
            let candidate = (self.current_note_index + offset) % note_count;
            if !self.notes[candidate].finished {
                self.current_note_index = candidate;
                return Ok(());
            }
        }
        invalid("atomic-subject note review has no unfinished note")
    }

    fn all_finished(&self) -> bool {
        self.notes.iter().all(|note| note.finished)
    }

    fn completed_outcome(&self) -> AtomicSubjectNoteReviewRunOutcome {
        let approved = self
            .notes
            .iter()
            .flat_map(|note| &note.subjects)
            .filter(|subject| subject.outcome == Some(ReviewOutcome::Approved))
            .count();
        let rejected = self
            .notes
            .iter()
            .flat_map(|note| &note.subjects)
            .filter(|subject| subject.outcome == Some(ReviewOutcome::Rejected))
            .count();
        AtomicSubjectNoteReviewRunOutcome::Completed {
            subjects: PromptReviewCounts {
                approved,
                rejected,
                skipped: 0,
            },
            notes_missing_subjects: self
                .notes
                .iter()
                .filter(|note| note.coverage == Some(AtomicSubjectCoverageDecision::Missing))
                .count(),
            notes_with_repeated_subjects: self
                .notes
                .iter()
                .filter(|note| {
                    note.distinctness == Some(AtomicSubjectDistinctnessDecision::Repeated)
                })
                .count(),
        }
    }
}

fn atomic_subject_review_item_count(note: &AtomicSubjectNoteReviewState) -> usize {
    note.subjects.len() + 2
}

fn atomic_subject_note_decided_count(note: &AtomicSubjectNoteReviewState) -> usize {
    note.subjects
        .iter()
        .filter(|subject| subject.outcome.is_some())
        .count()
        + usize::from(note.coverage.is_some())
        + usize::from(note.distinctness.is_some())
}

fn next_pending_review_item(note: &AtomicSubjectNoteReviewState, current: usize) -> Option<usize> {
    let item_count = atomic_subject_review_item_count(note);
    (1..=item_count)
        .map(|offset| (current + offset) % item_count)
        .find(|&index| {
            if let Some(subject) = note.subjects.get(index) {
                subject.outcome.is_none()
            } else if index == note.subjects.len() {
                note.coverage.is_none()
            } else {
                note.distinctness.is_none()
            }
        })
}

fn invalidate_note_checks(note: &mut AtomicSubjectNoteReviewState) {
    note.coverage = None;
    note.distinctness = None;
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum AtomicSubjectCommentTarget {
    Subject(usize),
    Coverage,
    Distinctness,
}

#[derive(Clone, Debug)]
pub struct AtomicSubjectNoteReviewTuiModel {
    screen: AtomicSubjectNoteReviewScreen,
    selected_index: usize,
    note_scroll: u16,
    help_scroll: u16,
    half_page_lines: u16,
    help_visible: bool,
    comment_target: Option<AtomicSubjectCommentTarget>,
    comment: String,
    comment_cursor: usize,
    interaction_enabled: bool,
}

impl AtomicSubjectNoteReviewTuiModel {
    pub fn new(screen: AtomicSubjectNoteReviewScreen) -> Self {
        let mut model = Self {
            screen: sanitize_atomic_subject_note_screen(screen),
            selected_index: 0,
            note_scroll: 0,
            help_scroll: 0,
            half_page_lines: 1,
            help_visible: false,
            comment_target: None,
            comment: String::new(),
            comment_cursor: 0,
            interaction_enabled: true,
        };
        model.selected_index = model
            .screen
            .selected_index
            .min(model.review_item_count() - 1);
        model
    }

    pub fn screen(&self) -> &AtomicSubjectNoteReviewScreen {
        &self.screen
    }

    pub fn selected_index(&self) -> usize {
        self.selected_index
    }

    pub fn replace_screen(&mut self, screen: AtomicSubjectNoteReviewScreen) {
        let note_changed = self.screen.note_index != screen.note_index;
        self.screen = sanitize_atomic_subject_note_screen(screen);
        self.selected_index = self.screen.selected_index.min(self.review_item_count() - 1);
        if note_changed {
            self.note_scroll = 0;
            self.help_scroll = 0;
            self.help_visible = false;
        }
    }

    fn review_item_count(&self) -> usize {
        self.screen.subjects.len() + 2
    }

    fn coverage_index(&self) -> usize {
        self.screen.subjects.len()
    }

    pub fn handle_event(&mut self, event: Event) -> AtomicSubjectNoteReviewAction {
        if is_control_c_event(&event) {
            self.comment_target = None;
            return AtomicSubjectNoteReviewAction::Pause;
        }
        if !self.interaction_enabled {
            return AtomicSubjectNoteReviewAction::None;
        }
        if self.comment_target.is_some() {
            return self.handle_comment_event(event);
        }
        let Event::Key(key) = event else {
            return AtomicSubjectNoteReviewAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return AtomicSubjectNoteReviewAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D') => {
                    if self.help_visible {
                        self.help_scroll = self.help_scroll.saturating_add(self.half_page_lines);
                    } else {
                        self.note_scroll = self.note_scroll.saturating_add(self.half_page_lines);
                    }
                }
                KeyCode::Char('u' | 'U') => {
                    if self.help_visible {
                        self.help_scroll = self.help_scroll.saturating_sub(self.half_page_lines);
                    } else {
                        self.note_scroll = self.note_scroll.saturating_sub(self.half_page_lines);
                    }
                }
                _ => {}
            }
            return AtomicSubjectNoteReviewAction::None;
        }
        if has_command_modifier(key.modifiers) {
            return AtomicSubjectNoteReviewAction::None;
        }
        if self.help_visible {
            match key.code {
                KeyCode::Char('?') | KeyCode::Esc => {
                    self.help_visible = false;
                    self.help_scroll = 0;
                }
                KeyCode::Down | KeyCode::Char('j' | 'J') => {
                    self.help_scroll = self.help_scroll.saturating_add(1);
                }
                KeyCode::Up | KeyCode::Char('k' | 'K') => {
                    self.help_scroll = self.help_scroll.saturating_sub(1);
                }
                KeyCode::PageDown => {
                    self.help_scroll = self.help_scroll.saturating_add(PAGE_LINES);
                }
                KeyCode::PageUp => {
                    self.help_scroll = self.help_scroll.saturating_sub(PAGE_LINES);
                }
                KeyCode::Home => self.help_scroll = 0,
                _ => {}
            }
            return AtomicSubjectNoteReviewAction::None;
        }
        match key.code {
            KeyCode::Down | KeyCode::Char('j' | 'J') => {
                self.selected_index = (self.selected_index + 1) % self.review_item_count();
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') => {
                self.selected_index = if self.selected_index == 0 {
                    self.review_item_count() - 1
                } else {
                    self.selected_index - 1
                };
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::Char('a' | 'A') => self.affirm_selected_item(),
            KeyCode::Char('r' | 'R') => self.reject_selected_item(),
            KeyCode::Char('u' | 'U') => self.clear_selected_item(),
            KeyCode::Char('c' | 'C') => {
                self.begin_comment(self.selected_comment_target());
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::Char('p' | 'P') | KeyCode::Left => AtomicSubjectNoteReviewAction::PreviousNote,
            KeyCode::Char('n' | 'N') | KeyCode::Right => AtomicSubjectNoteReviewAction::NextNote,
            KeyCode::Enter if self.all_review_items_decided() => {
                AtomicSubjectNoteReviewAction::FinishNote
            }
            KeyCode::Char('?') => {
                self.help_visible = true;
                self.help_scroll = 0;
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::PageDown => {
                self.note_scroll = self.note_scroll.saturating_add(PAGE_LINES);
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::PageUp => {
                self.note_scroll = self.note_scroll.saturating_sub(PAGE_LINES);
                AtomicSubjectNoteReviewAction::None
            }
            KeyCode::Home => {
                self.note_scroll = 0;
                AtomicSubjectNoteReviewAction::None
            }
            _ => AtomicSubjectNoteReviewAction::None,
        }
    }

    fn affirm_selected_item(&self) -> AtomicSubjectNoteReviewAction {
        if self.selected_index < self.coverage_index() {
            AtomicSubjectNoteReviewAction::DecideSubject {
                subject_index: self.selected_index,
                outcome: ReviewOutcome::Approved,
            }
        } else if self.selected_index == self.coverage_index() {
            AtomicSubjectNoteReviewAction::DecideCoverage {
                decision: AtomicSubjectCoverageDecision::Complete,
            }
        } else {
            AtomicSubjectNoteReviewAction::DecideDistinctness {
                decision: AtomicSubjectDistinctnessDecision::Distinct,
            }
        }
    }

    fn reject_selected_item(&self) -> AtomicSubjectNoteReviewAction {
        if self.selected_index < self.coverage_index() {
            AtomicSubjectNoteReviewAction::DecideSubject {
                subject_index: self.selected_index,
                outcome: ReviewOutcome::Rejected,
            }
        } else if self.selected_index == self.coverage_index() {
            AtomicSubjectNoteReviewAction::DecideCoverage {
                decision: AtomicSubjectCoverageDecision::Missing,
            }
        } else {
            AtomicSubjectNoteReviewAction::DecideDistinctness {
                decision: AtomicSubjectDistinctnessDecision::Repeated,
            }
        }
    }

    fn clear_selected_item(&self) -> AtomicSubjectNoteReviewAction {
        if self.selected_index < self.coverage_index() {
            AtomicSubjectNoteReviewAction::ClearSubject {
                subject_index: self.selected_index,
            }
        } else if self.selected_index == self.coverage_index() {
            AtomicSubjectNoteReviewAction::ClearCoverage
        } else {
            AtomicSubjectNoteReviewAction::ClearDistinctness
        }
    }

    fn selected_comment_target(&self) -> AtomicSubjectCommentTarget {
        if self.selected_index < self.coverage_index() {
            AtomicSubjectCommentTarget::Subject(self.selected_index)
        } else if self.selected_index == self.coverage_index() {
            AtomicSubjectCommentTarget::Coverage
        } else {
            AtomicSubjectCommentTarget::Distinctness
        }
    }

    fn begin_comment(&mut self, target: AtomicSubjectCommentTarget) {
        self.comment = match target {
            AtomicSubjectCommentTarget::Subject(index) => self
                .screen
                .subjects
                .get(index)
                .map(|subject| subject.comment.clone())
                .unwrap_or_default(),
            AtomicSubjectCommentTarget::Coverage => self.screen.coverage_comment.clone(),
            AtomicSubjectCommentTarget::Distinctness => self.screen.distinctness_comment.clone(),
        };
        self.comment_cursor = self.comment.chars().count();
        self.comment_target = Some(target);
    }

    fn handle_comment_event(&mut self, event: Event) -> AtomicSubjectNoteReviewAction {
        match event {
            Event::Paste(text) => {
                let text = terminal_safe(&text).replace('\n', " ");
                insert_at_character(&mut self.comment, self.comment_cursor, &text);
                self.comment_cursor += text.chars().count();
            }
            Event::Key(key) if key.kind == KeyEventKind::Press => {
                if key.modifiers == KeyModifiers::CONTROL
                    && matches!(key.code, KeyCode::Char('k' | 'K'))
                {
                    let target = self
                        .comment_target
                        .take()
                        .expect("comment editor always has a target");
                    return clear_atomic_subject_comment(target);
                }
                if has_command_modifier(key.modifiers) {
                    return AtomicSubjectNoteReviewAction::None;
                }
                match key.code {
                    KeyCode::Enter => {
                        let target = self
                            .comment_target
                            .take()
                            .expect("comment editor always has a target");
                        let comment = self.comment.trim().to_owned();
                        return match target {
                            AtomicSubjectCommentTarget::Subject(subject_index) => {
                                AtomicSubjectNoteReviewAction::SaveSubjectComment {
                                    subject_index,
                                    comment,
                                }
                            }
                            AtomicSubjectCommentTarget::Coverage => {
                                AtomicSubjectNoteReviewAction::SaveCoverageComment { comment }
                            }
                            AtomicSubjectCommentTarget::Distinctness => {
                                AtomicSubjectNoteReviewAction::SaveDistinctnessComment { comment }
                            }
                        };
                    }
                    KeyCode::Esc => {
                        self.comment_target = None;
                        self.comment.clear();
                        self.comment_cursor = 0;
                    }
                    KeyCode::Left => {
                        self.comment_cursor = self.comment_cursor.saturating_sub(1);
                    }
                    KeyCode::Right => {
                        self.comment_cursor =
                            (self.comment_cursor + 1).min(self.comment.chars().count());
                    }
                    KeyCode::Home => self.comment_cursor = 0,
                    KeyCode::End => self.comment_cursor = self.comment.chars().count(),
                    KeyCode::Backspace if self.comment_cursor > 0 => {
                        remove_character(&mut self.comment, self.comment_cursor - 1);
                        self.comment_cursor -= 1;
                    }
                    KeyCode::Delete if self.comment_cursor < self.comment.chars().count() => {
                        remove_character(&mut self.comment, self.comment_cursor);
                    }
                    KeyCode::Char(character) => {
                        let mut text = String::new();
                        text.push(character);
                        insert_at_character(&mut self.comment, self.comment_cursor, &text);
                        self.comment_cursor += 1;
                    }
                    _ => {}
                }
            }
            _ => {}
        }
        AtomicSubjectNoteReviewAction::None
    }

    fn all_review_items_decided(&self) -> bool {
        self.screen
            .subjects
            .iter()
            .all(|subject| subject.outcome.is_some())
            && self.screen.coverage.is_some()
            && self.screen.distinctness.is_some()
    }

    fn local_decided_count(&self) -> usize {
        self.screen
            .subjects
            .iter()
            .filter(|subject| subject.outcome.is_some())
            .count()
            + usize::from(self.screen.coverage.is_some())
            + usize::from(self.screen.distinctness.is_some())
    }

    fn selected_question(&self) -> &'static str {
        if self.screen.kind == PromptReviewKind::Claim
            && self.selected_index < self.coverage_index()
        {
            "Is this one self-contained claim made by the note without added information?"
        } else if self.screen.kind == PromptReviewKind::Claim
            && self.selected_index == self.coverage_index()
        {
            "Do the approved claims include every claim made by the note?"
        } else if self.screen.kind == PromptReviewKind::Claim {
            "Do the approved claims express different claims?"
        } else if self.selected_index < self.coverage_index() {
            "Is this subject supported by the note?"
        } else if self.selected_index == self.coverage_index() {
            "Do the approved subjects cover every atomic subject in the note?"
        } else {
            "Do the approved subjects express different meanings? Repeats are OK."
        }
    }

    fn selected_control_labels(&self) -> (&'static str, &'static str) {
        if self.selected_index < self.coverage_index() {
            ("Approve", "Disapprove")
        } else if self.selected_index == self.coverage_index() {
            ("Complete", "Missing")
        } else {
            ("Distinct", "Repeated")
        }
    }

    fn selected_status(&self) -> String {
        if let Some(subject) = self.screen.subjects.get(self.selected_index) {
            let decision = match subject.outcome {
                None => "Pending",
                Some(ReviewOutcome::Approved) => "Approved",
                Some(ReviewOutcome::Rejected) => "Disapproved",
            };
            return selected_review_status(
                &format!(
                    "{} {}",
                    if self.screen.kind == PromptReviewKind::Claim {
                        "Claim"
                    } else {
                        "Subject"
                    },
                    self.selected_index + 1
                ),
                decision,
                &subject.comment,
            );
        }
        if self.selected_index == self.coverage_index() {
            let decision = match self.screen.coverage {
                None => "Pending",
                Some(AtomicSubjectCoverageDecision::Complete) => "Complete",
                Some(AtomicSubjectCoverageDecision::Missing) => {
                    if self.screen.kind == PromptReviewKind::Claim {
                        "Missing claim(s)"
                    } else {
                        "Missing subject(s)"
                    }
                }
            };
            return selected_review_status("Coverage", decision, &self.screen.coverage_comment);
        }
        let decision = match self.screen.distinctness {
            None => "Pending",
            Some(AtomicSubjectDistinctnessDecision::Distinct) => "Distinct",
            Some(AtomicSubjectDistinctnessDecision::Repeated) => {
                if self.screen.kind == PromptReviewKind::Claim {
                    "Repeated claim(s)"
                } else {
                    "Repeated subject(s)"
                }
            }
        };
        selected_review_status("Distinctness", decision, &self.screen.distinctness_comment)
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let terminal_area = frame.area();
        self.interaction_enabled =
            terminal_area.width >= MIN_WIDTH && terminal_area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            render_too_small(frame, terminal_area);
            return;
        }
        let area = centered(terminal_area);
        let inner_width = area.width.saturating_sub(4).max(1);
        let note_lines = Paragraph::new(self.screen.note.as_str())
            .wrap(Wrap { trim: false })
            .line_count(inner_width);
        let note_height = u16::try_from(note_lines.saturating_add(2))
            .unwrap_or(u16::MAX)
            .clamp(4, 9);
        let note_height = if self.help_visible { 9 } else { note_height };
        let status_height = if self.screen.prior_combined_check.is_some() {
            2
        } else {
            1
        };
        let footer_height = 4;
        let question_height = if self.screen.kind == PromptReviewKind::Claim {
            2
        } else {
            1
        };
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(note_height),
                Constraint::Length(question_height),
                Constraint::Min(6),
                Constraint::Length(status_height),
                Constraint::Length(footer_height),
            ])
            .split(area);

        let local_decided = self.local_decided_count();
        let finished = if self.screen.finished {
            " · Finished"
        } else {
            ""
        };
        frame.render_widget(
            Paragraph::new(format!(
                "Note {}/{} · {local_decided}/{} here · {}/{} overall · {}/{} finished{finished}",
                self.screen.note_index + 1,
                self.screen.note_count,
                self.review_item_count(),
                self.screen.decided_review_count,
                self.screen.total_review_count,
                self.screen.finished_note_count,
                self.screen.note_count,
            ))
            .style(secondary_style()),
            rows[0],
        );

        if self.help_visible {
            let (help_title, mut help) = if self.screen.kind == PromptReviewKind::Claim {
                (
                    "Claim review help",
                    "Each note has three kinds of review row.\n\nA claim cannot depend on another proposed claim.\n\nClaim proposal: approve when the note makes it, it expresses only one claim, adds no information, and supplies the event, action, or situation being claimed. Descriptive entities such as “the player” or “the fire” may remain unidentified.\n\nCoverage: decide whether the approved claims include every claim made by the note.\n\nDistinctness: decide whether the approved claims express different claims. Only approved claims count.\n\nA records the positive answer shown for the selected row. R records the negative answer. U clears that decision. C edits an optional comment.\n\nP and N move between notes without deciding anything. Enter marks the note finished only after every row has an explicit decision. Finished notes remain editable."
                        .to_owned(),
                )
            } else {
                (
                    "Atomic-subject review help",
                    "Review the subjects against the complete note.\n\nSubject proposal: approve when the note states or reasonably implies the meaning. Disapprove when the subject adds unsupported meaning or changes what the note communicates.\n\nBroad, narrow, nested, overlapping and duplicate subjects are allowed. A brief mention is not, by itself, a reason to disapprove a subject.\n\nCoverage: decide whether any meaning communicated by the note is missing from the approved subjects. Different wording for an already covered meaning is not a missing subject.\n\nDistinctness records whether approved subjects repeat a meaning. Repetition is allowed; choosing Repeated does not reject any subject.\n\nA and R record the answer shown for the selected row. U clears that decision. C edits an optional comment.\n\nP and N move between notes without deciding anything. Ctrl-C saves and exits; you do not need to finish every row or note. Enter marks the note finished only after every row has an explicit decision. Finished notes remain editable."
                        .to_owned(),
                )
            };
            if let Some(prior) = &self.screen.prior_combined_check {
                help.push_str("\n\nMigrated prior combined check:\n");
                help.push_str(prior);
            }
            render_scrollable_panel(
                frame,
                rows[1],
                help_title,
                &help,
                &mut self.help_scroll,
                &mut self.half_page_lines,
                false,
            );
        } else {
            render_scrollable_panel(
                frame,
                rows[1],
                "Note",
                &self.screen.note,
                &mut self.note_scroll,
                &mut self.half_page_lines,
                false,
            );
        }

        frame.render_widget(
            Paragraph::new(self.selected_question())
                .style(accent_style())
                .wrap(Wrap { trim: false }),
            rows[2],
        );
        self.render_review_items(frame, rows[3], local_decided);
        self.render_status(frame, rows[4]);
        if self.comment_target.is_some() {
            self.render_comment_editor(frame, rows[5]);
        } else if self.help_visible {
            self.render_help_controls(frame, rows[5]);
        } else {
            self.render_controls(frame, rows[5]);
        }
    }

    fn render_review_items(&mut self, frame: &mut Frame<'_>, area: Rect, local_decided: usize) {
        let label_width = usize::from(area.width.saturating_sub(12).max(12));
        let mut items = self
            .screen
            .subjects
            .iter()
            .enumerate()
            .map(|(index, subject)| {
                let (symbol, style) = match subject.outcome {
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
                let prefix = format!("{symbol} {}. ", index + 1);
                let continuation = " ".repeat(prefix.chars().count());
                let wrapped = wrap_terminal_text(&subject.label, label_width);
                let lines = wrapped
                    .into_iter()
                    .enumerate()
                    .map(|(line_index, text)| {
                        Line::from(vec![
                            Span::styled(
                                if line_index == 0 {
                                    prefix.clone()
                                } else {
                                    continuation.clone()
                                },
                                style,
                            ),
                            Span::raw(text),
                        ])
                    })
                    .collect::<Vec<_>>();
                ListItem::new(Text::from(lines))
            })
            .collect::<Vec<_>>();

        let (coverage_symbol, coverage_style, coverage_status) = match self.screen.coverage {
            None => ("?", secondary_style(), "Pending"),
            Some(AtomicSubjectCoverageDecision::Complete) => (
                "✓",
                Style::default()
                    .fg(Color::Green)
                    .add_modifier(Modifier::BOLD),
                "Complete",
            ),
            Some(AtomicSubjectCoverageDecision::Missing) => (
                "✗",
                Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
                if self.screen.kind == PromptReviewKind::Claim {
                    "Missing claim(s)"
                } else {
                    "Missing subject(s)"
                },
            ),
        };
        items.push(ListItem::new(Line::from(vec![
            Span::styled(format!("{coverage_symbol} Coverage · "), coverage_style),
            Span::raw(coverage_status),
        ])));

        let (distinctness_symbol, distinctness_style, distinctness_status) =
            match self.screen.distinctness {
                None => ("?", secondary_style(), "Pending"),
                Some(AtomicSubjectDistinctnessDecision::Distinct) => (
                    "✓",
                    Style::default()
                        .fg(Color::Green)
                        .add_modifier(Modifier::BOLD),
                    "Distinct",
                ),
                Some(AtomicSubjectDistinctnessDecision::Repeated) => (
                    "✗",
                    Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
                    if self.screen.kind == PromptReviewKind::Claim {
                        "Repeated claim(s)"
                    } else {
                        "Repeated subject(s)"
                    },
                ),
            };
        items.push(ListItem::new(Line::from(vec![
            Span::styled(
                format!("{distinctness_symbol} Distinctness · "),
                distinctness_style,
            ),
            Span::raw(distinctness_status),
        ])));

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
                        .title(format!(
                            "Review items · {local_decided}/{} decided",
                            self.review_item_count()
                        ))
                        .title_style(accent_style()),
                ),
            area,
            &mut state,
        );
    }

    fn render_status(&self, frame: &mut Frame<'_>, area: Rect) {
        let width = usize::from(area.width);
        let mut lines = vec![Line::raw(truncate_terminal_line(
            &self.selected_status(),
            width,
        ))];
        if let Some(prior) = &self.screen.prior_combined_check {
            lines.push(Line::styled(
                truncate_terminal_line(prior, width),
                secondary_style(),
            ));
        }
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn render_controls(&self, frame: &mut Frame<'_>, area: Rect) {
        let (affirm, reject) = self.selected_control_labels();
        let finish_line =
            if self.screen.finished && self.screen.finished_note_count == self.screen.note_count {
                Line::from(vec![
                    Span::styled(
                        "All notes finished  ",
                        Style::default()
                            .fg(Color::Green)
                            .add_modifier(Modifier::BOLD),
                    ),
                    Span::styled("[?]", accent_style()),
                    Span::styled(" Help", secondary_style()),
                ])
            } else {
                let action = if self.screen.finished {
                    "Next unfinished"
                } else if self.all_review_items_decided() {
                    "Finish note"
                } else {
                    "Finish (decide all first)"
                };
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(format!(" {action}  "), secondary_style()),
                    Span::styled("[?]", accent_style()),
                    Span::styled(" Help", secondary_style()),
                ])
            };
        let lines = vec![
            Line::from(vec![
                Span::styled("[A]", accent_style()),
                Span::styled(format!(" {affirm}  "), secondary_style()),
                Span::styled("[R]", accent_style()),
                Span::styled(format!(" {reject}  "), secondary_style()),
                Span::styled("[U]", accent_style()),
                Span::styled(" Undecide  ", secondary_style()),
                Span::styled("[C]", accent_style()),
                Span::styled(" Comment", secondary_style()),
            ]),
            Line::from(vec![
                Span::styled("[↑/↓]", accent_style()),
                Span::styled(" Select  ", secondary_style()),
                Span::styled("[P/N]", accent_style()),
                Span::styled(" Note", secondary_style()),
            ]),
            finish_line,
            Line::from(vec![
                Span::styled("[Ctrl-D/U]", accent_style()),
                Span::styled(" Note  ", secondary_style()),
                Span::styled("[Ctrl-C]", accent_style()),
                Span::styled(" Save/exit", secondary_style()),
            ]),
        ];
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn render_help_controls(&self, frame: &mut Frame<'_>, area: Rect) {
        let lines = vec![
            Line::from(vec![
                Span::styled("[?/Esc]", accent_style()),
                Span::styled(" Close help  ", secondary_style()),
                Span::styled("[↑/↓]", accent_style()),
                Span::styled(" Scroll", secondary_style()),
            ]),
            Line::from(vec![
                Span::styled("[Ctrl-D/U]", accent_style()),
                Span::styled(" Half-page  ", secondary_style()),
                Span::styled("[Home]", accent_style()),
                Span::styled(" Top", secondary_style()),
            ]),
            Line::from(vec![
                Span::styled("[Ctrl-C]", accent_style()),
                Span::styled(" Save/exit", secondary_style()),
            ]),
        ];
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn render_comment_editor(&self, frame: &mut Frame<'_>, area: Rect) {
        let target = self
            .comment_target
            .expect("comment editor always has a target");
        let title = match target {
            AtomicSubjectCommentTarget::Subject(index) => {
                format!(
                    "Comment for {} {} (optional)",
                    if self.screen.kind == PromptReviewKind::Claim {
                        "claim"
                    } else {
                        "subject"
                    },
                    index + 1
                )
            }
            AtomicSubjectCommentTarget::Coverage => "Coverage comment (optional)".to_owned(),
            AtomicSubjectCommentTarget::Distinctness => {
                "Distinctness comment (optional)".to_owned()
            }
        };
        let available = usize::from(area.width.saturating_sub(2).max(1));
        let (visible, cursor_x) = comment_window(&self.comment, self.comment_cursor, available);
        frame.render_widget(
            Paragraph::new(vec![
                Line::styled(title, accent_style()),
                Line::raw(format!("> {visible}")),
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" Save  ", secondary_style()),
                    Span::styled("[Ctrl-K]", accent_style()),
                    Span::styled(" Clear  ", secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[←/→]", accent_style()),
                    Span::styled(" Move  ", secondary_style()),
                    Span::styled("[Home/End]", accent_style()),
                    Span::styled(" Ends", secondary_style()),
                ]),
            ]),
            area,
        );
        frame.set_cursor_position((
            area.x.saturating_add(2).saturating_add(cursor_x),
            area.y.saturating_add(1),
        ));
    }
}

impl InteractiveReviewModel for AtomicSubjectNoteReviewTuiModel {
    type Action = AtomicSubjectNoteReviewAction;

    fn none_action() -> Self::Action {
        AtomicSubjectNoteReviewAction::None
    }

    fn pause_action() -> Self::Action {
        AtomicSubjectNoteReviewAction::Pause
    }

    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }

    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

fn sanitize_atomic_subject_note_screen(
    mut screen: AtomicSubjectNoteReviewScreen,
) -> AtomicSubjectNoteReviewScreen {
    screen.note = terminal_safe(&screen.note);
    screen.coverage_comment = terminal_safe(&screen.coverage_comment).replace('\n', " ");
    screen.distinctness_comment = terminal_safe(&screen.distinctness_comment).replace('\n', " ");
    screen.prior_combined_check = screen
        .prior_combined_check
        .map(|message| terminal_safe(&message).replace('\n', " "));
    for subject in &mut screen.subjects {
        subject.label = terminal_safe(&subject.label).replace('\n', " ");
        subject.comment = terminal_safe(&subject.comment).replace('\n', " ");
    }
    screen
}

fn clear_atomic_subject_comment(
    target: AtomicSubjectCommentTarget,
) -> AtomicSubjectNoteReviewAction {
    match target {
        AtomicSubjectCommentTarget::Subject(subject_index) => {
            AtomicSubjectNoteReviewAction::SaveSubjectComment {
                subject_index,
                comment: String::new(),
            }
        }
        AtomicSubjectCommentTarget::Coverage => {
            AtomicSubjectNoteReviewAction::SaveCoverageComment {
                comment: String::new(),
            }
        }
        AtomicSubjectCommentTarget::Distinctness => {
            AtomicSubjectNoteReviewAction::SaveDistinctnessComment {
                comment: String::new(),
            }
        }
    }
}

fn selected_review_status(label: &str, decision: &str, comment: &str) -> String {
    if comment.is_empty() {
        format!("{label} · {decision} · no comment")
    } else {
        format!("{label} · {decision} · comment: {comment}")
    }
}

fn truncate_terminal_line(value: &str, maximum_width: usize) -> String {
    if unicode_width::UnicodeWidthStr::width(value) <= maximum_width {
        return value.to_owned();
    }
    if maximum_width == 0 {
        return String::new();
    }
    let content_width = maximum_width.saturating_sub(1);
    let mut truncated = String::new();
    let mut width = 0;
    for character in value.chars() {
        let character_width = unicode_width::UnicodeWidthChar::width(character).unwrap_or(0);
        if width + character_width > content_width {
            break;
        }
        truncated.push(character);
        width += character_width;
    }
    truncated.push('…');
    truncated
}

fn insert_at_character(value: &mut String, character_index: usize, text: &str) {
    let byte_index = value
        .char_indices()
        .nth(character_index)
        .map_or(value.len(), |(index, _)| index);
    value.insert_str(byte_index, text);
}

fn remove_character(value: &mut String, character_index: usize) {
    let Some((start, character)) = value.char_indices().nth(character_index) else {
        return;
    };
    value.drain(start..start + character.len_utf8());
}

fn wrap_terminal_text(value: &str, maximum_width: usize) -> Vec<String> {
    let maximum_width = maximum_width.max(1);
    let mut lines = Vec::new();
    let mut current = String::new();
    let mut current_width = 0;
    for word in value.split_whitespace() {
        let word_width = unicode_width::UnicodeWidthStr::width(word);
        if current_width != 0 && current_width + 1 + word_width > maximum_width {
            lines.push(current);
            current = String::new();
            current_width = 0;
        }
        if !current.is_empty() {
            current.push(' ');
            current_width += 1;
        }
        if word_width <= maximum_width {
            current.push_str(word);
            current_width += word_width;
            continue;
        }
        for character in word.chars() {
            let width = unicode_width::UnicodeWidthChar::width(character).unwrap_or(0);
            if current_width != 0 && current_width + width > maximum_width {
                lines.push(current);
                current = String::new();
                current_width = 0;
            }
            current.push(character);
            current_width += width;
        }
    }
    if !current.is_empty() || lines.is_empty() {
        lines.push(current);
    }
    lines
}

fn comment_window(value: &str, cursor: usize, maximum_width: usize) -> (String, u16) {
    let characters = value.chars().collect::<Vec<_>>();
    let cursor = cursor.min(characters.len());
    let mut start = 0;
    while display_width(&characters[start..cursor]) >= maximum_width && start < cursor {
        start += 1;
    }
    let mut end = start;
    while end < characters.len() && display_width(&characters[start..=end]) <= maximum_width {
        end += 1;
    }
    let visible = characters[start..end].iter().collect::<String>();
    let cursor_width = display_width(&characters[start..cursor]);
    (visible, u16::try_from(cursor_width).unwrap_or(u16::MAX))
}

fn display_width(characters: &[char]) -> usize {
    characters
        .iter()
        .map(|character| unicode_width::UnicodeWidthChar::width(*character).unwrap_or(0))
        .sum()
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

pub(crate) fn resolve_fragments(
    fragments: &[ProposedMaskFragment],
    content: &str,
    note_id: &str,
    subject_id: &str,
) -> Result<Vec<(usize, usize)>> {
    if fragments.is_empty() {
        return invalid(format!(
            "mask {note_id} / {subject_id} contains no fragments"
        ));
    }
    let mut spans = Vec::with_capacity(fragments.len());
    for fragment in fragments {
        if fragment.text.trim().is_empty() || fragment.occurrence == 0 {
            return invalid(format!(
                "mask {note_id} / {subject_id} contains an empty fragment or zero occurrence"
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

pub(crate) fn highlighted_note(content: &str, spans: &[(usize, usize)]) -> String {
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
