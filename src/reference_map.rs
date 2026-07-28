//! Auditable artifacts for the small semantic-map reference example.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::snapshot::{Error, Result};

pub const REFERENCE_NOTE_COUNT: usize = 64;
pub const MIN_INTERPRETIVE_AMBIGUITY_COUNT: usize = 8;
pub const CONTRAST_PAIR_COUNT: usize = 8;
pub const BROAD_NARROW_PAIR_COUNT: usize = 8;
pub const NICHE_OR_SPARSE_CASE_COUNT: usize = 8;

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BroadNarrowRole {
    Broad,
    Narrow,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PairMembership {
    pub pair_id: String,
    pub partner_slot: u8,
    pub broad_narrow_role: Option<BroadNarrowRole>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedNote {
    pub slot: u8,
    pub note_id: String,
    pub pubkey: String,
    pub content: String,
    pub interpretive_ambiguity: bool,
    pub contrast_pair: Option<PairMembership>,
    pub broad_narrow_pair: Option<PairMembership>,
    pub niche_or_sparse_case: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SelectionSource {
    pub sample_path: String,
    pub sample_sha256: String,
    pub split: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteProposal {
    pub schema_version: u32,
    pub proposal_id: String,
    pub source: SelectionSource,
    pub notes: Vec<ProposedNote>,
}

impl NoteProposal {
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != 2 {
            return invalid("note proposal schema_version must be 2");
        }
        if self.proposal_id.trim().is_empty() {
            return invalid("note proposal_id must not be empty");
        }
        if self.source.sample_path.trim().is_empty()
            || !is_lower_hex(&self.source.sample_sha256, 64)
            || self.source.split != "learning"
        {
            return invalid(
                "selection source must name the verified sample, its SHA-256, and learning split",
            );
        }
        if self.notes.len() != REFERENCE_NOTE_COUNT {
            return invalid(format!(
                "note proposal must contain exactly {REFERENCE_NOTE_COUNT} notes"
            ));
        }

        let mut slots = BTreeSet::new();
        let mut note_ids = BTreeSet::new();
        let mut interpretively_ambiguous = 0;
        let mut niche_or_sparse_cases = BTreeSet::new();
        let mut contrast = BTreeMap::<&str, Vec<&ProposedNote>>::new();
        let mut broad_narrow = BTreeMap::<&str, Vec<&ProposedNote>>::new();

        for note in &self.notes {
            if !slots.insert(note.slot) {
                return invalid(format!("note slot {} is duplicated", note.slot));
            }
            if !note_ids.insert(note.note_id.as_str()) {
                return invalid(format!("note_id {} is duplicated", note.note_id));
            }
            if !is_lower_hex(&note.note_id, 64) || !is_lower_hex(&note.pubkey, 64) {
                return invalid(format!(
                    "note slot {} must contain lowercase 32-byte note and author IDs",
                    note.slot
                ));
            }
            if note.content.trim().is_empty() {
                return invalid(format!("note slot {} must contain text", note.slot));
            }
            if note.interpretive_ambiguity {
                interpretively_ambiguous += 1;
            }
            if let Some(pair) = &note.contrast_pair {
                validate_pair_fields(note, pair, false)?;
                contrast
                    .entry(pair.pair_id.as_str())
                    .or_default()
                    .push(note);
            }
            if let Some(pair) = &note.broad_narrow_pair {
                validate_pair_fields(note, pair, true)?;
                broad_narrow
                    .entry(pair.pair_id.as_str())
                    .or_default()
                    .push(note);
            }
            if let Some(case) = &note.niche_or_sparse_case {
                if case.trim().is_empty() || !niche_or_sparse_cases.insert(case.as_str()) {
                    return invalid(
                        "every niche or sparse case marker must be nonempty and distinct",
                    );
                }
            }
        }

        let expected_slots = (1..=REFERENCE_NOTE_COUNT)
            .map(|slot| u8::try_from(slot).expect("64 slots fit u8"))
            .collect::<BTreeSet<_>>();
        if slots != expected_slots {
            return invalid("note slots must be exactly 1 through 64");
        }
        if interpretively_ambiguous < MIN_INTERPRETIVE_AMBIGUITY_COUNT {
            return invalid(format!(
                "note proposal must mark at least {MIN_INTERPRETIVE_AMBIGUITY_COUNT} \
                 interpretively ambiguous notes"
            ));
        }
        validate_pair_groups("contrast", &contrast, CONTRAST_PAIR_COUNT, false)?;
        validate_pair_groups("broad/narrow", &broad_narrow, BROAD_NARROW_PAIR_COUNT, true)?;
        if niche_or_sparse_cases.len() != NICHE_OR_SPARSE_CASE_COUNT {
            return invalid(format!(
                "note proposal must mark exactly {NICHE_OR_SPARSE_CASE_COUNT} distinct niche or sparse cases"
            ));
        }
        Ok(())
    }

    pub fn note(&self, slot: u8) -> Option<&ProposedNote> {
        self.notes.iter().find(|note| note.slot == slot)
    }

    pub fn identity(&self) -> Result<String> {
        self.validate()?;
        canonical_sha256(&(&self.source, &self.notes))
    }
}

fn validate_pair_fields(
    note: &ProposedNote,
    pair: &PairMembership,
    broad_narrow: bool,
) -> Result<()> {
    if pair.pair_id.trim().is_empty() || pair.partner_slot == note.slot {
        return invalid(format!(
            "note slot {} has an invalid {} pair",
            note.slot,
            if broad_narrow {
                "broad/narrow"
            } else {
                "contrast"
            }
        ));
    }
    if broad_narrow != pair.broad_narrow_role.is_some() {
        return invalid(format!(
            "note slot {} has an invalid {} pair role",
            note.slot,
            if broad_narrow {
                "broad/narrow"
            } else {
                "contrast"
            }
        ));
    }
    Ok(())
}

fn validate_pair_groups(
    name: &str,
    groups: &BTreeMap<&str, Vec<&ProposedNote>>,
    expected_groups: usize,
    broad_narrow: bool,
) -> Result<()> {
    if groups.len() != expected_groups {
        return invalid(format!(
            "note proposal must contain exactly {expected_groups} {name} pairs"
        ));
    }
    for (pair_id, notes) in groups {
        if notes.len() != 2 {
            return invalid(format!(
                "{name} pair {pair_id} must contain exactly two notes"
            ));
        }
        let left_pair = if broad_narrow {
            notes[0].broad_narrow_pair.as_ref()
        } else {
            notes[0].contrast_pair.as_ref()
        }
        .expect("grouped note has the requested pair");
        let right_pair = if broad_narrow {
            notes[1].broad_narrow_pair.as_ref()
        } else {
            notes[1].contrast_pair.as_ref()
        }
        .expect("grouped note has the requested pair");
        if left_pair.partner_slot != notes[1].slot || right_pair.partner_slot != notes[0].slot {
            return invalid(format!("{name} pair {pair_id} is not reciprocal"));
        }
        if broad_narrow {
            let roles = [left_pair.broad_narrow_role, right_pair.broad_narrow_role]
                .into_iter()
                .collect::<BTreeSet<_>>();
            if roles
                != [Some(BroadNarrowRole::Broad), Some(BroadNarrowRole::Narrow)]
                    .into_iter()
                    .collect()
            {
                return invalid(format!(
                    "broad/narrow pair {pair_id} must contain one broad and one narrow note"
                ));
            }
        }
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewOutcome {
    Approved,
    Rejected,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteReviewDecision {
    pub outcome: ReviewOutcome,
    pub comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredNoteDecision {
    note_sha256: String,
    decision: NoteReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteReviewSession {
    schema_version: u32,
    decisions: BTreeMap<u8, StoredNoteDecision>,
}

impl NoteReviewSession {
    pub fn new(proposal: &NoteProposal) -> Result<Self> {
        proposal.validate()?;
        Ok(Self {
            schema_version: 1,
            decisions: BTreeMap::new(),
        })
    }

    pub fn record(
        &mut self,
        proposal: &NoteProposal,
        slot: u8,
        decision: NoteReviewDecision,
    ) -> Result<()> {
        proposal.validate()?;
        validate_review_decision(decision.outcome, &decision.comment)?;
        let note = proposal
            .note(slot)
            .ok_or_else(|| Error::ExperimentState(format!("note slot {slot} does not exist")))?;
        self.decisions.insert(
            slot,
            StoredNoteDecision {
                note_sha256: canonical_sha256(note)?,
                decision,
            },
        );
        Ok(())
    }

    pub fn reconcile(&mut self, proposal: &NoteProposal) -> Result<()> {
        proposal.validate()?;
        self.decisions.retain(|slot, stored| {
            proposal.note(*slot).is_some_and(|note| {
                canonical_sha256(note).is_ok_and(|identity| identity == stored.note_sha256)
            })
        });
        Ok(())
    }

    pub fn decision_for(&self, proposal: &NoteProposal, slot: u8) -> Option<&NoteReviewDecision> {
        let note = proposal.note(slot)?;
        let identity = canonical_sha256(note).ok()?;
        self.decisions
            .get(&slot)
            .filter(|stored| stored.note_sha256 == identity)
            .map(|stored| &stored.decision)
    }

    pub fn approved_count(&self, proposal: &NoteProposal) -> usize {
        proposal
            .notes
            .iter()
            .filter(|note| {
                self.decision_for(proposal, note.slot)
                    .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
            })
            .count()
    }

    pub fn pending_slots(&self, proposal: &NoteProposal) -> Vec<u8> {
        proposal
            .notes
            .iter()
            .filter(|note| self.decision_for(proposal, note.slot).is_none())
            .map(|note| note.slot)
            .collect()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ApprovedNoteSet {
    pub schema_version: u32,
    pub proposal_sha256: String,
    pub source: SelectionSource,
    pub notes: Vec<ProposedNote>,
}

impl ApprovedNoteSet {
    pub fn from_review(proposal: &NoteProposal, session: &NoteReviewSession) -> Result<Self> {
        proposal.validate()?;
        let approved = session.approved_count(proposal);
        if approved != REFERENCE_NOTE_COUNT {
            return invalid(format!(
                "cannot publish approved note set: {approved} of {REFERENCE_NOTE_COUNT} current notes are approved"
            ));
        }
        Ok(Self {
            schema_version: 2,
            proposal_sha256: proposal.identity()?,
            source: proposal.source.clone(),
            notes: proposal.notes.clone(),
        })
    }

    pub fn validate(&self) -> Result<()> {
        if self.schema_version != 2 || !is_lower_hex(&self.proposal_sha256, 64) {
            return invalid("approved note set identity is invalid");
        }
        let proposal = NoteProposal {
            schema_version: 2,
            proposal_id: "approved-note-set-validation".to_owned(),
            source: self.source.clone(),
            notes: self.notes.clone(),
        };
        proposal.validate()?;
        if proposal.identity()? != self.proposal_sha256 {
            return invalid("approved note set proposal SHA-256 does not match its content");
        }
        Ok(())
    }

    pub fn identity(&self) -> Result<String> {
        self.validate()?;
        canonical_sha256(self)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MembershipStrength {
    Incidental,
    Substantive,
    Central,
}

impl MembershipStrength {
    pub const fn rank(self) -> u8 {
        match self {
            Self::Incidental => 1,
            Self::Substantive => 2,
            Self::Central => 3,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LeafMembership {
    pub note_id: String,
    pub strength: MembershipStrength,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SubjectNode {
    pub node_id: String,
    pub label: String,
    pub scope: String,
    pub children: Vec<String>,
    pub memberships: Vec<LeafMembership>,
}

impl SubjectNode {
    pub fn is_leaf(&self) -> bool {
        self.children.is_empty()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyDraft {
    pub schema_version: u32,
    pub draft_id: String,
    pub approved_notes_sha256: String,
    pub root_node_id: String,
    pub nodes: Vec<SubjectNode>,
}

impl HierarchyDraft {
    pub fn validate(&self, approved_notes: &ApprovedNoteSet) -> Result<()> {
        approved_notes.validate()?;
        if self.schema_version != 1 || self.draft_id.trim().is_empty() {
            return invalid("hierarchy draft schema and ID are invalid");
        }
        if self.approved_notes_sha256 != approved_notes.identity()? {
            return invalid("hierarchy draft is not bound to the approved note set");
        }
        if self.nodes.is_empty() {
            return invalid("hierarchy draft contains no nodes");
        }

        let mut nodes = BTreeMap::new();
        for node in &self.nodes {
            if node.node_id.trim().is_empty()
                || node.label.trim().is_empty()
                || node.scope.trim().is_empty()
            {
                return invalid("every hierarchy node must have an ID, label, and scope");
            }
            if nodes.insert(node.node_id.as_str(), node).is_some() {
                return invalid(format!("hierarchy node {} is duplicated", node.node_id));
            }
            if node.is_leaf() {
                if node.memberships.is_empty() {
                    return invalid(format!(
                        "leaf hierarchy node {} contains no notes",
                        node.node_id
                    ));
                }
            } else {
                if !node.memberships.is_empty() {
                    return invalid(format!(
                        "internal hierarchy node {} must not contain direct note memberships",
                        node.node_id
                    ));
                }
                if !(2..=8).contains(&node.children.len()) {
                    return invalid(format!(
                        "internal hierarchy node {} must contain 2 through at most 8 children",
                        node.node_id
                    ));
                }
                let unique_children = node.children.iter().collect::<BTreeSet<_>>();
                if unique_children.len() != node.children.len() {
                    return invalid(format!(
                        "internal hierarchy node {} repeats a child",
                        node.node_id
                    ));
                }
            }
        }
        if !nodes.contains_key(self.root_node_id.as_str()) {
            return invalid("hierarchy hidden root does not exist");
        }
        if nodes[self.root_node_id.as_str()].is_leaf() {
            return invalid("hierarchy hidden root must be internal");
        }

        let mut parent_counts = BTreeMap::<&str, usize>::new();
        for node in &self.nodes {
            for child in &node.children {
                if !nodes.contains_key(child.as_str()) {
                    return invalid(format!(
                        "hierarchy node {} names missing child {child}",
                        node.node_id
                    ));
                }
                *parent_counts.entry(child.as_str()).or_default() += 1;
            }
        }
        for node in &self.nodes {
            let parent_count = parent_counts
                .get(node.node_id.as_str())
                .copied()
                .unwrap_or(0);
            if node.node_id == self.root_node_id {
                if parent_count != 0 {
                    return invalid("hierarchy hidden root must not have a parent");
                }
            } else if parent_count != 1 {
                return invalid(format!(
                    "hierarchy node {} must have exactly one parent",
                    node.node_id
                ));
            }
        }

        let mut visiting = BTreeSet::new();
        let mut visited = BTreeSet::new();
        visit_node(
            self.root_node_id.as_str(),
            &nodes,
            &mut visiting,
            &mut visited,
        )?;
        if visited.len() != nodes.len() {
            return invalid("every hierarchy node must be reachable from the hidden root");
        }

        let approved_ids = approved_notes
            .notes
            .iter()
            .map(|note| note.note_id.as_str())
            .collect::<BTreeSet<_>>();
        let mut covered = BTreeSet::new();
        for node in self.nodes.iter().filter(|node| node.is_leaf()) {
            let mut local = BTreeSet::new();
            for membership in &node.memberships {
                if !approved_ids.contains(membership.note_id.as_str()) {
                    return invalid(format!(
                        "leaf {} references a note outside the approved set",
                        node.node_id
                    ));
                }
                if !local.insert(membership.note_id.as_str()) {
                    return invalid(format!(
                        "leaf {} repeats note {}",
                        node.node_id, membership.note_id
                    ));
                }
                covered.insert(membership.note_id.as_str());
            }
        }
        if covered != approved_ids {
            return invalid("every approved note must belong to at least one leaf subject");
        }
        Ok(())
    }

    pub fn node(&self, node_id: &str) -> Option<&SubjectNode> {
        self.nodes.iter().find(|node| node.node_id == node_id)
    }

    pub fn identity(&self, approved_notes: &ApprovedNoteSet) -> Result<String> {
        self.validate(approved_notes)?;
        canonical_sha256(self)
    }

    fn leaf_map_revision(&self, approved_notes: &ApprovedNoteSet) -> Result<String> {
        self.validate(approved_notes)?;
        let mut leaves = self
            .nodes
            .iter()
            .filter(|node| node.is_leaf())
            .collect::<Vec<_>>();
        leaves.sort_unstable_by(|left, right| left.node_id.cmp(&right.node_id));
        canonical_sha256(&(approved_notes.identity()?, leaves))
    }

    pub fn node_revision(&self, approved_notes: &ApprovedNoteSet, node_id: &str) -> Result<String> {
        self.validate(approved_notes)?;
        let nodes = self
            .nodes
            .iter()
            .map(|node| (node.node_id.as_str(), node))
            .collect::<BTreeMap<_, _>>();
        let notes = approved_notes
            .notes
            .iter()
            .map(|note| (note.note_id.as_str(), note))
            .collect::<BTreeMap<_, _>>();
        node_revision_unchecked(node_id, &nodes, &notes, &mut BTreeMap::new())
    }
}

fn visit_node<'a>(
    node_id: &'a str,
    nodes: &BTreeMap<&'a str, &'a SubjectNode>,
    visiting: &mut BTreeSet<&'a str>,
    visited: &mut BTreeSet<&'a str>,
) -> Result<()> {
    if visited.contains(node_id) {
        return Ok(());
    }
    if !visiting.insert(node_id) {
        return invalid(format!("hierarchy contains a cycle at node {node_id}"));
    }
    let node = nodes
        .get(node_id)
        .ok_or_else(|| Error::ExperimentState(format!("hierarchy node {node_id} is missing")))?;
    for child in &node.children {
        visit_node(child, nodes, visiting, visited)?;
    }
    visiting.remove(node_id);
    visited.insert(node_id);
    Ok(())
}

fn node_revision_unchecked(
    node_id: &str,
    nodes: &BTreeMap<&str, &SubjectNode>,
    notes: &BTreeMap<&str, &ProposedNote>,
    memo: &mut BTreeMap<String, String>,
) -> Result<String> {
    if let Some(revision) = memo.get(node_id) {
        return Ok(revision.clone());
    }
    let node = nodes
        .get(node_id)
        .ok_or_else(|| Error::ExperimentState(format!("hierarchy node {node_id} is missing")))?;
    let children = node
        .children
        .iter()
        .map(|child| {
            Ok((
                child.clone(),
                node_revision_unchecked(child, nodes, notes, memo)?,
            ))
        })
        .collect::<Result<Vec<_>>>()?;
    let memberships = node
        .memberships
        .iter()
        .map(|membership| {
            let note = notes.get(membership.note_id.as_str()).ok_or_else(|| {
                Error::ExperimentState(format!(
                    "hierarchy membership names missing note {}",
                    membership.note_id
                ))
            })?;
            Ok((membership, note.content.as_str()))
        })
        .collect::<Result<Vec<_>>>()?;
    let revision = canonical_sha256(&(
        node.node_id.as_str(),
        node.label.as_str(),
        node.scope.as_str(),
        memberships,
        children,
    ))?;
    memo.insert(node_id.to_owned(), revision.clone());
    Ok(revision)
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyReviewDecision {
    pub outcome: ReviewOutcome,
    pub comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyReviewRecord {
    pub node_id: String,
    pub node_revision_sha256: String,
    pub decision: HierarchyReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FocusCoverageReviewRecord {
    pub leaf_map_revision_sha256: String,
    pub decision: HierarchyReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyReviewSession {
    schema_version: u32,
    history: Vec<HierarchyReviewRecord>,
    focus_coverage_history: Vec<FocusCoverageReviewRecord>,
}

impl HierarchyReviewSession {
    pub fn new(draft: &HierarchyDraft, approved_notes: &ApprovedNoteSet) -> Result<Self> {
        draft.validate(approved_notes)?;
        Ok(Self {
            schema_version: 2,
            history: Vec::new(),
            focus_coverage_history: Vec::new(),
        })
    }

    pub fn record(
        &mut self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
        node_id: &str,
        decision: HierarchyReviewDecision,
    ) -> Result<()> {
        draft.validate(approved_notes)?;
        validate_review_decision(decision.outcome, &decision.comment)?;
        draft.node(node_id).ok_or_else(|| {
            Error::ExperimentState(format!("hierarchy node {node_id} does not exist"))
        })?;
        if !self
            .reviewable_node_ids(draft, approved_notes)
            .iter()
            .any(|reviewable| reviewable == node_id)
        {
            return invalid(format!(
                "hierarchy node {node_id} cannot be reviewed until all lower levels are approved"
            ));
        }
        self.history.push(HierarchyReviewRecord {
            node_id: node_id.to_owned(),
            node_revision_sha256: draft.node_revision(approved_notes, node_id)?,
            decision,
        });
        Ok(())
    }

    pub fn record_focus_coverage(
        &mut self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
        decision: HierarchyReviewDecision,
    ) -> Result<()> {
        draft.validate(approved_notes)?;
        validate_review_decision(decision.outcome, &decision.comment)?;
        if !self.all_leaves_approved(draft, approved_notes) {
            return invalid(
                "focus-concentration coverage cannot be reviewed until every leaf mapping is approved",
            );
        }
        if self
            .current_focus_coverage_decision(draft, approved_notes)
            .is_some()
        {
            return invalid(
                "focus-concentration coverage already has a decision for the current leaf map",
            );
        }
        self.focus_coverage_history.push(FocusCoverageReviewRecord {
            leaf_map_revision_sha256: draft.leaf_map_revision(approved_notes)?,
            decision,
        });
        Ok(())
    }

    pub fn current_decision(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
        node_id: &str,
    ) -> Option<&HierarchyReviewDecision> {
        let revision = draft.node_revision(approved_notes, node_id).ok()?;
        self.history
            .iter()
            .rev()
            .find(|record| record.node_id == node_id && record.node_revision_sha256 == revision)
            .map(|record| &record.decision)
    }

    pub fn is_approved(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
        node_id: &str,
    ) -> bool {
        self.current_decision(draft, approved_notes, node_id)
            .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
    }

    pub fn current_focus_coverage_decision(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
    ) -> Option<&HierarchyReviewDecision> {
        let revision = draft.leaf_map_revision(approved_notes).ok()?;
        self.focus_coverage_history
            .iter()
            .rev()
            .find(|record| record.leaf_map_revision_sha256 == revision)
            .map(|record| &record.decision)
    }

    pub fn focus_coverage_is_approved(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
    ) -> bool {
        self.current_focus_coverage_decision(draft, approved_notes)
            .is_some_and(|decision| decision.outcome == ReviewOutcome::Approved)
    }

    pub fn all_leaves_approved(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
    ) -> bool {
        draft
            .nodes
            .iter()
            .filter(|node| node.is_leaf())
            .all(|node| self.is_approved(draft, approved_notes, node.node_id.as_str()))
    }

    pub fn reviewable_node_ids(
        &self,
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
    ) -> Vec<String> {
        if self.all_leaves_approved(draft, approved_notes)
            && !self.focus_coverage_is_approved(draft, approved_notes)
        {
            return Vec::new();
        }
        let eligible = draft
            .nodes
            .iter()
            .filter(|node| {
                self.current_decision(draft, approved_notes, &node.node_id)
                    .is_none()
                    && node
                        .children
                        .iter()
                        .all(|child| self.is_approved(draft, approved_notes, child))
            })
            .map(|node| {
                (
                    node.node_id.clone(),
                    node_height(draft, node.node_id.as_str()),
                )
            })
            .collect::<Vec<_>>();
        let Some(minimum_height) = eligible.iter().map(|(_, height)| *height).min() else {
            return Vec::new();
        };
        let reviewable_ids = eligible
            .iter()
            .filter(|(_, height)| *height == minimum_height)
            .map(|(node_id, _)| node_id.as_str())
            .collect::<BTreeSet<_>>();
        let mut reviewable = Vec::with_capacity(reviewable_ids.len());
        collect_node_ids_in_tree_order(
            draft,
            draft.root_node_id.as_str(),
            &reviewable_ids,
            &mut reviewable,
        );
        reviewable
    }

    pub fn history(&self) -> &[HierarchyReviewRecord] {
        &self.history
    }
}

fn validate_review_decision(outcome: ReviewOutcome, comment: &str) -> Result<()> {
    if outcome == ReviewOutcome::Rejected && comment.trim().is_empty() {
        return invalid("a rejection comment must explain what needs to change");
    }
    Ok(())
}

fn node_height(draft: &HierarchyDraft, node_id: &str) -> usize {
    let node = draft
        .node(node_id)
        .expect("validated hierarchy contains every child");
    node.children
        .iter()
        .map(|child| node_height(draft, child))
        .max()
        .map_or(0, |height| height + 1)
}

fn collect_node_ids_in_tree_order(
    draft: &HierarchyDraft,
    node_id: &str,
    selected: &BTreeSet<&str>,
    ordered: &mut Vec<String>,
) {
    if selected.contains(node_id) {
        ordered.push(node_id.to_owned());
    }
    let node = draft
        .node(node_id)
        .expect("validated hierarchy contains every child");
    for child in &node.children {
        collect_node_ids_in_tree_order(draft, child, selected, ordered);
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyNote {
    pub note_id: String,
    pub content: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ApprovedHierarchy {
    pub schema_version: u32,
    pub approved_notes_sha256: String,
    pub hierarchy_draft_sha256: String,
    pub artifact_sha256: String,
    pub root_node_id: String,
    pub notes: Vec<HierarchyNote>,
    pub nodes: Vec<SubjectNode>,
}

impl ApprovedHierarchy {
    pub fn from_review(
        draft: &HierarchyDraft,
        approved_notes: &ApprovedNoteSet,
        session: &HierarchyReviewSession,
    ) -> Result<Self> {
        draft.validate(approved_notes)?;
        if !session.focus_coverage_is_approved(draft, approved_notes) {
            return invalid(
                "cannot publish hierarchy until focus-concentration coverage is approved",
            );
        }
        if !session.is_approved(draft, approved_notes, &draft.root_node_id) {
            return invalid("cannot publish hierarchy until the current hidden root is approved");
        }
        let unresolved = draft
            .nodes
            .iter()
            .filter(|node| !session.is_approved(draft, approved_notes, node.node_id.as_str()))
            .map(|node| node.node_id.as_str())
            .collect::<Vec<_>>();
        if !unresolved.is_empty() {
            return invalid(format!(
                "cannot publish hierarchy while nodes remain unapproved: {}",
                unresolved.join(", ")
            ));
        }
        let notes = approved_notes
            .notes
            .iter()
            .map(|note| HierarchyNote {
                note_id: note.note_id.clone(),
                content: note.content.clone(),
            })
            .collect::<Vec<_>>();
        let approved_notes_sha256 = approved_notes.identity()?;
        let hierarchy_draft_sha256 = draft.identity(approved_notes)?;
        let artifact_sha256 = canonical_sha256(&(
            1_u32,
            approved_notes_sha256.as_str(),
            hierarchy_draft_sha256.as_str(),
            draft.root_node_id.as_str(),
            notes.as_slice(),
            draft.nodes.as_slice(),
        ))?;
        Ok(Self {
            schema_version: 1,
            approved_notes_sha256,
            hierarchy_draft_sha256,
            artifact_sha256,
            root_node_id: draft.root_node_id.clone(),
            notes,
            nodes: draft.nodes.clone(),
        })
    }

    pub fn validate(&self) -> Result<()> {
        if self.schema_version != 1
            || !is_lower_hex(&self.approved_notes_sha256, 64)
            || !is_lower_hex(&self.hierarchy_draft_sha256, 64)
            || !is_lower_hex(&self.artifact_sha256, 64)
        {
            return invalid("approved hierarchy identity is invalid");
        }
        if self.notes.len() != REFERENCE_NOTE_COUNT {
            return invalid(format!(
                "approved hierarchy must contain exactly {REFERENCE_NOTE_COUNT} notes"
            ));
        }
        if canonical_sha256(&(
            self.schema_version,
            self.approved_notes_sha256.as_str(),
            self.hierarchy_draft_sha256.as_str(),
            self.root_node_id.as_str(),
            self.notes.as_slice(),
            self.nodes.as_slice(),
        ))? != self.artifact_sha256
        {
            return invalid("approved hierarchy artifact SHA-256 does not match its content");
        }
        let mut note_ids = BTreeSet::new();
        for note in &self.notes {
            if !is_lower_hex(&note.note_id, 64)
                || note.content.trim().is_empty()
                || !note_ids.insert(note.note_id.as_str())
            {
                return invalid("approved hierarchy notes must be unique, valid, and nonempty");
            }
        }

        let mut nodes = BTreeMap::new();
        for node in &self.nodes {
            if node.node_id.trim().is_empty()
                || node.label.trim().is_empty()
                || node.scope.trim().is_empty()
                || nodes.insert(node.node_id.as_str(), node).is_some()
            {
                return invalid("approved hierarchy contains an invalid or duplicate node");
            }
            if node.is_leaf() {
                if node.memberships.is_empty() {
                    return invalid(format!("leaf {} contains no notes", node.node_id));
                }
            } else if !(2..=8).contains(&node.children.len()) || !node.memberships.is_empty() {
                return invalid(format!(
                    "internal node {} must have 2 through at most 8 children and no direct notes",
                    node.node_id
                ));
            }
        }
        if !nodes.contains_key(self.root_node_id.as_str()) {
            return invalid("approved hierarchy hidden root does not exist");
        }
        if nodes[self.root_node_id.as_str()].is_leaf() {
            return invalid("approved hierarchy hidden root must be internal");
        }
        let mut parent_counts = BTreeMap::<&str, usize>::new();
        for node in &self.nodes {
            let unique = node.children.iter().collect::<BTreeSet<_>>();
            if unique.len() != node.children.len() {
                return invalid(format!("node {} repeats a child", node.node_id));
            }
            for child in &node.children {
                if !nodes.contains_key(child.as_str()) {
                    return invalid(format!("node {} names missing child {child}", node.node_id));
                }
                *parent_counts.entry(child.as_str()).or_default() += 1;
            }
        }
        for node in &self.nodes {
            let parents = parent_counts
                .get(node.node_id.as_str())
                .copied()
                .unwrap_or(0);
            if (node.node_id == self.root_node_id && parents != 0)
                || (node.node_id != self.root_node_id && parents != 1)
            {
                return invalid(format!(
                    "node {} does not have the required parent count",
                    node.node_id
                ));
            }
        }
        let mut visiting = BTreeSet::new();
        let mut visited = BTreeSet::new();
        visit_node(
            self.root_node_id.as_str(),
            &nodes,
            &mut visiting,
            &mut visited,
        )?;
        if visited.len() != nodes.len() {
            return invalid("every approved hierarchy node must be reachable");
        }
        let mut covered = BTreeSet::new();
        for leaf in self.nodes.iter().filter(|node| node.is_leaf()) {
            let mut local = BTreeSet::new();
            for membership in &leaf.memberships {
                if !note_ids.contains(membership.note_id.as_str())
                    || !local.insert(membership.note_id.as_str())
                {
                    return invalid(format!(
                        "leaf {} contains an invalid or duplicate membership",
                        leaf.node_id
                    ));
                }
                covered.insert(membership.note_id.as_str());
            }
        }
        if covered != note_ids {
            return invalid("every approved hierarchy note must belong to a leaf");
        }
        Ok(())
    }

    pub fn node(&self, node_id: &str) -> Option<&SubjectNode> {
        self.nodes.iter().find(|node| node.node_id == node_id)
    }

    pub fn leaf_notes(&self, node_id: &str) -> Result<Vec<&HierarchyNote>> {
        self.validate()?;
        let node = self
            .node(node_id)
            .ok_or_else(|| Error::ExperimentState(format!("subject node {node_id} is missing")))?;
        if !node.is_leaf() {
            return invalid(format!("subject node {node_id} is not a leaf"));
        }
        let notes = self
            .notes
            .iter()
            .map(|note| (note.note_id.as_str(), note))
            .collect::<BTreeMap<_, _>>();
        let mut memberships = node.memberships.iter().collect::<Vec<_>>();
        memberships.sort_by(|left, right| {
            right
                .strength
                .rank()
                .cmp(&left.strength.rank())
                .then_with(|| left.note_id.cmp(&right.note_id))
        });
        Ok(memberships
            .into_iter()
            .map(|membership| notes[membership.note_id.as_str()])
            .collect())
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct NavigationFrame {
    node_id: String,
    cursor: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReferenceNavigation {
    frames: Vec<NavigationFrame>,
}

impl ReferenceNavigation {
    pub fn new(hierarchy: &ApprovedHierarchy) -> Result<Self> {
        hierarchy.validate()?;
        Ok(Self {
            frames: vec![NavigationFrame {
                node_id: hierarchy.root_node_id.clone(),
                cursor: 0,
            }],
        })
    }

    pub fn current_node_id(&self) -> &str {
        &self
            .frames
            .last()
            .expect("navigation always contains its hidden root")
            .node_id
    }

    pub fn selected_index(&self) -> usize {
        self.frames
            .last()
            .expect("navigation always contains its hidden root")
            .cursor
    }

    pub fn move_next(&mut self, hierarchy: &ApprovedHierarchy) {
        let count = self.current_item_count(hierarchy);
        if count == 0 {
            return;
        }
        let frame = self
            .frames
            .last_mut()
            .expect("navigation always contains its hidden root");
        frame.cursor = (frame.cursor + 1).min(count - 1);
    }

    pub fn move_previous(&mut self) {
        let frame = self
            .frames
            .last_mut()
            .expect("navigation always contains its hidden root");
        frame.cursor = frame.cursor.saturating_sub(1);
    }

    pub fn enter(&mut self, hierarchy: &ApprovedHierarchy) -> Result<()> {
        hierarchy.validate()?;
        let node = hierarchy.node(self.current_node_id()).ok_or_else(|| {
            Error::ExperimentState(format!(
                "current subject node {} is missing",
                self.current_node_id()
            ))
        })?;
        if node.is_leaf() {
            return Ok(());
        }
        let child = node
            .children
            .get(self.selected_index())
            .ok_or_else(|| Error::ExperimentState("subject cursor is invalid".to_owned()))?;
        self.frames.push(NavigationFrame {
            node_id: child.clone(),
            cursor: 0,
        });
        Ok(())
    }

    pub fn back(&mut self) {
        if self.frames.len() > 1 {
            self.frames.pop();
        }
    }

    pub fn breadcrumb<'a>(&self, hierarchy: &'a ApprovedHierarchy) -> Result<Vec<&'a str>> {
        self.frames
            .iter()
            .skip(1)
            .map(|frame| {
                hierarchy
                    .node(&frame.node_id)
                    .map(|node| node.label.as_str())
                    .ok_or_else(|| {
                        Error::ExperimentState(format!(
                            "breadcrumb subject {} is missing",
                            frame.node_id
                        ))
                    })
            })
            .collect()
    }

    pub fn selected_note<'a>(
        &self,
        hierarchy: &'a ApprovedHierarchy,
    ) -> Result<Option<&'a HierarchyNote>> {
        let node = hierarchy.node(self.current_node_id()).ok_or_else(|| {
            Error::ExperimentState(format!(
                "current subject node {} is missing",
                self.current_node_id()
            ))
        })?;
        if !node.is_leaf() {
            return Ok(None);
        }
        Ok(hierarchy
            .leaf_notes(&node.node_id)?
            .get(self.selected_index())
            .copied())
    }

    fn current_item_count(&self, hierarchy: &ApprovedHierarchy) -> usize {
        let Some(node) = hierarchy.node(self.current_node_id()) else {
            return 0;
        };
        if node.is_leaf() {
            hierarchy
                .leaf_notes(&node.node_id)
                .map_or(0, |notes| notes.len())
        } else {
            node.children.len()
        }
    }
}

fn canonical_sha256<T: Serialize>(value: &T) -> Result<String> {
    let bytes = serde_json::to_vec(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: "<reference-map-identity>".into(),
        source,
    })?;
    Ok(format!("{:x}", Sha256::digest(bytes)))
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
