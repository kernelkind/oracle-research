//! Source-bound proposal validation and durable human review for SSE masks.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::artifact::hash_file;
use crate::reference_map::ReviewOutcome;
use crate::reference_review::ApprovalUi;
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
};
use crate::review_state::{
    acquire_session_lock, load_json, load_session, publish_json, save_session, value_sha256,
};
use crate::snapshot::{Error, Result, io_error};

const NOTE_SET_SCHEMA_VERSION: u32 = 1;
const MASK_PROPOSAL_SCHEMA_VERSION: u32 = 1;
const MASK_SESSION_SCHEMA_VERSION: u32 = 1;
const APPROVED_MASK_SCHEMA_VERSION: u32 = 1;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BoundFile {
    path: String,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FrozenSubject {
    id: String,
    label: String,
    reference_note_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FrozenMixedNote {
    note_id: String,
    subject_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FrozenNoteSetInvariants {
    subject_count: usize,
    reference_notes_per_subject: usize,
    reference_note_count: usize,
    mixed_note_count: usize,
    subjects_per_mixed_note: usize,
    mixed_masks_per_subject: usize,
    total_note_count: usize,
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
    subjects: Vec<FrozenSubject>,
    mixed_notes: Vec<FrozenMixedNote>,
    invariants: FrozenNoteSetInvariants,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedSubjectMask {
    pub note_id: String,
    pub subject_id: String,
    pub fragments: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskProposal {
    schema_version: u32,
    proposal_id: String,
    note_set: BoundFile,
    masks: Vec<ProposedSubjectMask>,
}

#[derive(Clone, Debug)]
struct SourceNote {
    pubkey: String,
    content: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum MaskRole {
    Reference,
    MixedFirst,
    MixedSecond,
}

#[derive(Clone, Debug)]
struct VerifiedSubjectMask {
    proposal: ProposedSubjectMask,
    subject_label: String,
    note: SourceNote,
    spans: Vec<(usize, usize)>,
    role: MaskRole,
}

#[derive(Clone, Debug)]
pub struct VerifiedMaskProposal {
    proposal: MaskProposal,
    note_set_sha256: String,
    masks: Vec<VerifiedSubjectMask>,
}

impl VerifiedMaskProposal {
    pub fn mask_count(&self) -> usize {
        self.masks.len()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaskReviewDecision {
    pub outcome: ReviewOutcome,
    pub comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredMaskDecision {
    mask_sha256: String,
    decision: MaskReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct MaskReviewSession {
    schema_version: u32,
    decisions: BTreeMap<String, StoredMaskDecision>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ApprovedMaskSet {
    pub schema_version: u32,
    pub proposal_sha256: String,
    pub note_set_sha256: String,
    pub masks: Vec<ProposedSubjectMask>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MaskReviewRunOutcome {
    Paused,
    NeedsRevision { approved: usize, rejected: usize },
    Approved,
}

pub fn load_verified_mask_proposal(
    proposal_path: impl AsRef<Path>,
) -> Result<VerifiedMaskProposal> {
    let proposal_path = proposal_path.as_ref();
    let proposal: MaskProposal = load_json(proposal_path)?;
    if proposal.schema_version != MASK_PROPOSAL_SCHEMA_VERSION
        || proposal.proposal_id.trim().is_empty()
        || !is_lower_hex(&proposal.note_set.sha256, 64)
    {
        return invalid("mask proposal schema, ID, or note-set identity is invalid");
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
    let notes = load_source_notes(&note_set, &note_set_path)?;
    let expected = expected_masks(&note_set);
    if proposal.masks.len() != expected.len() {
        return invalid(format!(
            "mask proposal has {} masks, expected {} from the frozen note-set review order",
            proposal.masks.len(),
            expected.len()
        ));
    }

    let labels = note_set
        .subjects
        .iter()
        .map(|subject| (subject.id.as_str(), subject.label.as_str()))
        .collect::<BTreeMap<_, _>>();
    let mut masks = Vec::with_capacity(proposal.masks.len());
    for (index, (mask, expected)) in proposal.masks.iter().zip(expected.iter()).enumerate() {
        if mask.note_id != expected.note_id || mask.subject_id != expected.subject_id {
            return invalid(format!(
                "mask {} does not match the frozen note-set review order",
                index + 1
            ));
        }
        let note = notes
            .get(mask.note_id.as_str())
            .expect("all expected frozen note IDs were source-verified")
            .clone();
        let spans = resolve_fragments(mask, &note.content)?;
        masks.push(VerifiedSubjectMask {
            proposal: mask.clone(),
            subject_label: labels[mask.subject_id.as_str()].to_owned(),
            note,
            spans,
            role: expected.role,
        });
    }

    Ok(VerifiedMaskProposal {
        proposal,
        note_set_sha256: hash_file(&note_set_path)?,
        masks,
    })
}

pub fn run_mask_review(
    proposal_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    approved_path: impl AsRef<Path>,
    ui: &mut impl ApprovalUi,
) -> Result<MaskReviewRunOutcome> {
    let proposal_path = proposal_path.as_ref();
    let session_path = session_path.as_ref();
    let approved_path = approved_path.as_ref();
    let proposal = load_verified_mask_proposal(proposal_path)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session = load_session::<MaskReviewSession>(session_path)?.unwrap_or_default();
    session.reconcile(&proposal)?;
    save_session(session_path, &session)?;

    while let Some(index) = session.pending_indices(&proposal).first().copied() {
        let screen = mask_screen(&proposal, &session, index)?;
        match ui
            .review(screen)
            .map_err(|source| io_error("run SSE mask review UI for", proposal_path, source))?
        {
            ApprovalTuiAction::None => {
                return invalid("approval UI returned without a mask decision");
            }
            ApprovalTuiAction::Pause => return Ok(MaskReviewRunOutcome::Paused),
            ApprovalTuiAction::Submit { outcome, comment } => {
                session.record(&proposal, index, MaskReviewDecision { outcome, comment })?;
                save_session(session_path, &session)?;
            }
        }
    }

    let (approved, rejected) = session.decision_counts(&proposal);
    if rejected != 0 {
        return Ok(MaskReviewRunOutcome::NeedsRevision { approved, rejected });
    }
    let artifact = ApprovedMaskSet::from_review(&proposal, &session)?;
    publish_json(approved_path, &artifact)?;
    Ok(MaskReviewRunOutcome::Approved)
}

impl Default for MaskReviewSession {
    fn default() -> Self {
        Self {
            schema_version: MASK_SESSION_SCHEMA_VERSION,
            decisions: BTreeMap::new(),
        }
    }
}

impl MaskReviewSession {
    fn reconcile(&mut self, proposal: &VerifiedMaskProposal) -> Result<()> {
        if self.schema_version != MASK_SESSION_SCHEMA_VERSION {
            return invalid(format!(
                "mask review session schema {} is unsupported",
                self.schema_version
            ));
        }
        let identities = proposal
            .masks
            .iter()
            .map(|mask| Ok((mask_key(mask), mask_identity(mask)?)))
            .collect::<Result<BTreeMap<_, _>>>()?;
        self.decisions.retain(|key, stored| {
            identities
                .get(key)
                .is_some_and(|identity| identity == &stored.mask_sha256)
        });
        Ok(())
    }

    fn record(
        &mut self,
        proposal: &VerifiedMaskProposal,
        index: usize,
        decision: MaskReviewDecision,
    ) -> Result<()> {
        validate_decision(&decision)?;
        let mask = proposal
            .masks
            .get(index)
            .ok_or_else(|| Error::ExperimentState(format!("mask index {index} is absent")))?;
        self.decisions.insert(
            mask_key(mask),
            StoredMaskDecision {
                mask_sha256: mask_identity(mask)?,
                decision,
            },
        );
        Ok(())
    }

    fn decision_for<'a>(&'a self, mask: &VerifiedSubjectMask) -> Option<&'a MaskReviewDecision> {
        let identity = mask_identity(mask).ok()?;
        self.decisions
            .get(&mask_key(mask))
            .filter(|stored| stored.mask_sha256 == identity)
            .map(|stored| &stored.decision)
    }

    fn pending_indices(&self, proposal: &VerifiedMaskProposal) -> Vec<usize> {
        proposal
            .masks
            .iter()
            .enumerate()
            .filter(|(_, mask)| self.decision_for(mask).is_none())
            .map(|(index, _)| index)
            .collect()
    }

    fn decision_counts(&self, proposal: &VerifiedMaskProposal) -> (usize, usize) {
        proposal
            .masks
            .iter()
            .filter_map(|mask| self.decision_for(mask))
            .fold((0, 0), |(approved, rejected), decision| {
                match decision.outcome {
                    ReviewOutcome::Approved => (approved + 1, rejected),
                    ReviewOutcome::Rejected => (approved, rejected + 1),
                }
            })
    }
}

impl ApprovedMaskSet {
    fn from_review(proposal: &VerifiedMaskProposal, session: &MaskReviewSession) -> Result<Self> {
        let (approved, rejected) = session.decision_counts(proposal);
        if approved != proposal.masks.len() || rejected != 0 {
            return invalid(format!(
                "cannot publish approved masks: {approved} approved and {rejected} rejected out of {}",
                proposal.masks.len()
            ));
        }
        Ok(Self {
            schema_version: APPROVED_MASK_SCHEMA_VERSION,
            proposal_sha256: value_sha256(&proposal.proposal)?,
            note_set_sha256: proposal.note_set_sha256.clone(),
            masks: proposal
                .masks
                .iter()
                .map(|mask| mask.proposal.clone())
                .collect(),
        })
    }
}

#[derive(Clone, Debug)]
struct ExpectedMask {
    note_id: String,
    subject_id: String,
    role: MaskRole,
}

fn expected_masks(note_set: &FrozenNoteSet) -> Vec<ExpectedMask> {
    let references = note_set.subjects.iter().flat_map(|subject| {
        subject
            .reference_note_ids
            .iter()
            .map(|note_id| ExpectedMask {
                note_id: note_id.clone(),
                subject_id: subject.id.clone(),
                role: MaskRole::Reference,
            })
    });
    let mixed = note_set.mixed_notes.iter().flat_map(|note| {
        note.subject_ids
            .iter()
            .enumerate()
            .map(|(index, subject_id)| ExpectedMask {
                note_id: note.note_id.clone(),
                subject_id: subject_id.clone(),
                role: if index == 0 {
                    MaskRole::MixedFirst
                } else {
                    MaskRole::MixedSecond
                },
            })
    });
    references.chain(mixed).collect()
}

fn validate_note_set(note_set: &FrozenNoteSet) -> Result<()> {
    if note_set.schema_version != NOTE_SET_SCHEMA_VERSION
        || note_set.status != "approved"
        || !is_lower_hex(&note_set.source.sha256, 64)
        || note_set.invariants.required_split.trim().is_empty()
    {
        return invalid("frozen note-set schema, status, source, or split is invalid");
    }
    let invariants = &note_set.invariants;
    if note_set.subjects.len() != invariants.subject_count
        || note_set.mixed_notes.len() != invariants.mixed_note_count
        || note_set.subjects.iter().any(|subject| {
            subject.reference_note_ids.len() != invariants.reference_notes_per_subject
        })
        || note_set
            .mixed_notes
            .iter()
            .any(|note| note.subject_ids.len() != invariants.subjects_per_mixed_note)
    {
        return invalid("frozen note-set counts do not match its invariants");
    }
    let subject_ids = note_set
        .subjects
        .iter()
        .map(|subject| subject.id.as_str())
        .collect::<BTreeSet<_>>();
    if subject_ids.len() != note_set.subjects.len()
        || note_set
            .subjects
            .iter()
            .any(|subject| subject.id.trim().is_empty() || subject.label.trim().is_empty())
    {
        return invalid("frozen note-set subject IDs and labels must be unique and nonempty");
    }
    let reference_ids = note_set
        .subjects
        .iter()
        .flat_map(|subject| subject.reference_note_ids.iter())
        .collect::<Vec<_>>();
    let mixed_ids = note_set
        .mixed_notes
        .iter()
        .map(|note| &note.note_id)
        .collect::<Vec<_>>();
    let all_ids = reference_ids
        .iter()
        .copied()
        .chain(mixed_ids.iter().copied())
        .collect::<Vec<_>>();
    if reference_ids.len() != invariants.reference_note_count
        || all_ids.len() != invariants.total_note_count
        || all_ids.iter().collect::<BTreeSet<_>>().len() != invariants.unique_note_count
        || all_ids.iter().any(|note_id| !is_lower_hex(note_id, 64))
    {
        return invalid("frozen note-set note IDs or counts are invalid");
    }
    let mut mixed_counts = BTreeMap::<&str, usize>::new();
    for mixed in &note_set.mixed_notes {
        for subject_id in &mixed.subject_ids {
            if !subject_ids.contains(subject_id.as_str()) {
                return invalid(format!(
                    "mixed note {} names unknown subject {}",
                    mixed.note_id, subject_id
                ));
            }
            *mixed_counts.entry(subject_id.as_str()).or_default() += 1;
        }
    }
    if subject_ids.iter().any(|subject_id| {
        mixed_counts.get(subject_id).copied().unwrap_or(0) != invariants.mixed_masks_per_subject
    }) {
        return invalid("frozen note-set mixed-mask coverage does not match its invariants");
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
        .subjects
        .iter()
        .flat_map(|subject| subject.reference_note_ids.iter())
        .chain(note_set.mixed_notes.iter().map(|note| &note.note_id))
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
        if row.split == note_set.invariants.required_split
            && expected_ids.contains(row.note_id.as_str())
        {
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
    }
    let missing = expected_ids
        .iter()
        .filter(|note_id| !notes.contains_key(**note_id))
        .copied()
        .collect::<Vec<_>>();
    if !missing.is_empty() {
        return invalid(format!(
            "source sample is missing {} frozen note IDs",
            missing.len()
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

fn resolve_fragments(mask: &ProposedSubjectMask, content: &str) -> Result<Vec<(usize, usize)>> {
    if mask.fragments.is_empty() {
        return invalid(format!(
            "mask {} / {} contains no fragments",
            mask.note_id, mask.subject_id
        ));
    }
    let mut spans = Vec::with_capacity(mask.fragments.len());
    for fragment in &mask.fragments {
        if fragment.trim().is_empty() {
            return invalid(format!(
                "mask {} / {} contains an empty fragment",
                mask.note_id, mask.subject_id
            ));
        }
        let matches = content.match_indices(fragment).collect::<Vec<_>>();
        let [(start, _)] = matches.as_slice() else {
            return if matches.is_empty() {
                invalid(format!(
                    "mask fragment `{fragment}` is absent from note {}",
                    mask.note_id
                ))
            } else {
                invalid(format!(
                    "mask fragment `{fragment}` is not unique in note {}",
                    mask.note_id
                ))
            };
        };
        spans.push((*start, start + fragment.len()));
    }
    for pair in spans.windows(2) {
        if pair[0].0 > pair[1].0 {
            return invalid(format!(
                "mask fragments for note {} are not in source order",
                mask.note_id
            ));
        }
        if pair[0].1 > pair[1].0 {
            return invalid(format!("mask fragments for note {} overlap", mask.note_id));
        }
    }
    Ok(spans)
}

fn mask_screen(
    proposal: &VerifiedMaskProposal,
    session: &MaskReviewSession,
    index: usize,
) -> Result<ApprovalScreen> {
    let mask = proposal
        .masks
        .get(index)
        .ok_or_else(|| Error::ExperimentState(format!("mask index {index} is absent")))?;
    let (approved, rejected) = session.decision_counts(proposal);
    let title = match mask.role {
        MaskRole::Reference => "Reference note · only mask",
        MaskRole::MixedFirst => "Mixed note · first of two masks",
        MaskRole::MixedSecond => "Mixed note · second of two masks",
    };
    Ok(ApprovalScreen {
        heading: format!(
            "SSE mask review · Primary mask {} of {} · {approved} approved · {rejected} rejected",
            index + 1,
            proposal.masks.len()
        ),
        title: title.to_owned(),
        scope: format!(
            "Subject: {}\n\n\
             Does the highlight faithfully isolate “{}”?\n\n\
             Approve only if it includes the necessary evidence and excludes text belonging only to another subject.",
            mask.subject_label, mask.subject_label
        ),
        approve_label: "No problem".to_owned(),
        reject_label: "Needs revision".to_owned(),
        rejection_help: "State exactly what text must be added, removed, or changed.".to_owned(),
        guidance: Some(ApprovalGuidance {
            title: "Mask help".to_owned(),
            body: "Text between ⟦ and ⟧ is selected for this mask.\n\n\
                   The complete note remains visible to the encoder as context. Only the selected text is pooled into this subject vector.\n\n\
                   This decision approves one subject mask only. A mixed note’s other subject appears on the next screen.\n\n\
                   Reject when necessary evidence is missing or selected text belongs only to another subject."
                .to_owned(),
        }),
        evidence: vec![ApprovalEvidence {
            title: "Note".to_owned(),
            annotation: String::new(),
            body: highlighted_note(&mask.note.content, &mask.spans),
        }],
        evidence_layout: ApprovalEvidenceLayout::Paged,
    })
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

fn mask_key(mask: &VerifiedSubjectMask) -> String {
    format!("{}:{}", mask.proposal.note_id, mask.proposal.subject_id)
}

#[derive(Serialize)]
struct MaskIdentity<'a> {
    note_id: &'a str,
    subject_id: &'a str,
    subject_label: &'a str,
    fragments: &'a [String],
    note_content: &'a str,
    role: MaskRole,
}

fn mask_identity(mask: &VerifiedSubjectMask) -> Result<String> {
    value_sha256(&MaskIdentity {
        note_id: &mask.proposal.note_id,
        subject_id: &mask.proposal.subject_id,
        subject_label: &mask.subject_label,
        fragments: &mask.proposal.fragments,
        note_content: &mask.note.content,
        role: mask.role,
    })
}

fn validate_decision(decision: &MaskReviewDecision) -> Result<()> {
    if decision.outcome == ReviewOutcome::Rejected && decision.comment.trim().is_empty() {
        return invalid("a mask rejection requires an actionable comment");
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
