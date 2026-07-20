use std::collections::BTreeSet;
use std::io;

use oracle_mvp::adaptive_learning_runner::AdaptiveLearningRunnerOutcome;
use oracle_mvp::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RestOutcome, RestView,
};
use oracle_mvp::phase3_preview::run_phase3_preview;

#[test]
fn wrong_language_after_the_first_rest_reaches_a_real_replacement() {
    let workspace = tempfile::tempdir().expect("preview workspace");
    let mut evaluator = ReplacementProbe::default();

    let outcome = run_phase3_preview(workspace.path(), &mut evaluator)
        .expect("run production Phase 3 workflow over preview fixtures");

    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(evaluator.presentation_numbers, (1..=41).collect::<Vec<_>>());
    assert_eq!(evaluator.rests, [20, 40]);
    assert_eq!(evaluator.notes.len(), 41);
    assert_eq!(
        evaluator.notes.iter().collect::<BTreeSet<_>>().len(),
        41,
        "the replacement must be a newly presented note"
    );
    assert_eq!(evaluator.completions, 0);
}

#[test]
fn mixed_preferences_can_reach_production_completion() {
    let workspace = tempfile::tempdir().expect("preview workspace");
    let mut evaluator = CompletionProbe::default();

    let outcome = run_phase3_preview(workspace.path(), &mut evaluator)
        .expect("complete production Phase 3 workflow over preview fixtures");

    assert!(matches!(
        outcome,
        AdaptiveLearningRunnerOutcome::Complete(_)
    ));
    assert_eq!(evaluator.completions, 1);
    assert_eq!(
        evaluator.notes.iter().collect::<BTreeSet<_>>().len(),
        evaluator.notes.len(),
        "the complete preview must not repeat a presented note"
    );
}

#[derive(Default)]
struct ReplacementProbe {
    presentation_numbers: Vec<usize>,
    notes: Vec<String>,
    rests: Vec<usize>,
    completions: usize,
}

impl EvaluatorUi for ReplacementProbe {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presentation_numbers.push(view.presentation_number());
        self.notes.push(view.note().to_owned());
        let decision = if view.presentation_number() == 21 {
            EvaluatorDecision::WrongLanguage
        } else {
            EvaluatorDecision::Rating(7)
        };
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            decision,
            view.presentation_number() == 41,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("a fresh preview must not enter recovery")
    }

    fn rest(&mut self, view: RestView) -> io::Result<RestOutcome> {
        self.rests.push(view.presentations_stored());
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        self.completions += 1;
        Ok(())
    }
}

#[derive(Default)]
struct CompletionProbe {
    notes: Vec<String>,
    completions: usize,
}

impl EvaluatorUi for CompletionProbe {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.notes.push(view.note().to_owned());
        let rating = if view.note().contains("A deliberately long note")
            || view.note().contains("open-source program")
        {
            7
        } else {
            1
        };
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(rating),
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("a fresh preview must not enter recovery")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        self.completions += 1;
        Ok(())
    }
}
