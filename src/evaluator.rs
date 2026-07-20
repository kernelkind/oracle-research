//! Evaluator-facing protocol shared by Phase 3 learning and frozen evaluation.

use std::io;

/// The frozen question asked for every numeric judgment.
pub const RATING_QUESTION: &str =
    "Considering the attention it required, how glad are you that you saw this note?";

/// The frozen, equally weighted meanings of the seven accepted ratings.
pub const RATING_ANCHORS: [&str; 7] = [
    "1: Actively wish it had not been shown.",
    "2: Clearly not worth seeing.",
    "3: Little personal value.",
    "4: Indifferent.",
    "5: Mildly glad to have seen it.",
    "6: Clearly glad; personally valuable.",
    "7: Exceptionally valuable.",
];

/// The frozen rule for removing a presented note from numeric evaluation.
pub const WRONG_LANGUAGE_RULE: &str = "Use wrong_language only when the note is clearly primarily non-English. Mixed-language, code-heavy, and ambiguous notes remain eligible and must be rated.";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EvaluatorDecision {
    Rating(u8),
    WrongLanguage,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EvaluatorSubmission {
    decision: EvaluatorDecision,
    pause_after: bool,
}

impl EvaluatorSubmission {
    pub const fn new(decision: EvaluatorDecision, pause_after: bool) -> Self {
        Self {
            decision,
            pause_after,
        }
    }

    pub const fn decision(self) -> EvaluatorDecision {
        self.decision
    }

    pub const fn pause_after(self) -> bool {
        self.pause_after
    }
}

/// Only the information required to render one rating presentation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RatingView<'a> {
    note: &'a str,
    presentation_number: usize,
    break_in: usize,
}

impl<'a> RatingView<'a> {
    pub const fn new(note: &'a str, presentation_number: usize, break_in: usize) -> Self {
        Self {
            note,
            presentation_number,
            break_in,
        }
    }

    pub const fn note(self) -> &'a str {
        self.note
    }

    pub const fn presentation_number(self) -> usize {
        self.presentation_number
    }

    pub const fn break_in(self) -> usize {
        self.break_in
    }
}

/// A pending presentation is deliberately recovered without its note content.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RecoveryView {
    presentation_number: usize,
    break_in: usize,
}

impl RecoveryView {
    pub const fn new(presentation_number: usize, break_in: usize) -> Self {
        Self {
            presentation_number,
            break_in,
        }
    }

    pub const fn presentation_number(self) -> usize {
        self.presentation_number
    }

    pub const fn break_in(self) -> usize {
        self.break_in
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RestView {
    presentations_stored: usize,
}

impl RestView {
    pub const fn new(presentations_stored: usize) -> Self {
        Self {
            presentations_stored,
        }
    }

    pub const fn presentations_stored(self) -> usize {
        self.presentations_stored
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CompletionView {
    presentations_stored: usize,
}

impl CompletionView {
    pub const fn new(presentations_stored: usize) -> Self {
        Self {
            presentations_stored,
        }
    }

    pub const fn presentations_stored(self) -> usize {
        self.presentations_stored
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RatingOutcome {
    Submitted(EvaluatorSubmission),
    Paused,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RecoveryOutcome {
    Submitted(EvaluatorSubmission),
    Redisplay,
    Paused,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RestOutcome {
    Continue,
    Paused,
}

/// The evaluator interface used by both adaptive learning and frozen evaluation.
///
/// Its views intentionally contain no candidate provenance, personalizer identity,
/// score, rank, or experiment phase.
///
/// Implementations used for a real experiment must present the exact constants
/// in this module and enforce the frozen single-key, recovery, pause, and rest
/// behavior. The runner records that behavioral contract and trusts the
/// implementation to honor it; [`crate::evaluator_tui::FullScreenEvaluator`] is
/// the shipped implementation.
pub trait EvaluatorUi {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome>;

    fn recover(&mut self, view: RecoveryView) -> io::Result<RecoveryOutcome>;

    fn rest(&mut self, view: RestView) -> io::Result<RestOutcome>;

    fn preparing(&mut self) -> io::Result<()>;

    fn complete(&mut self, view: CompletionView) -> io::Result<()>;
}
