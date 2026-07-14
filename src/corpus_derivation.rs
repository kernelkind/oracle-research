//! Bounded-memory derivation of the root kind-1 corpus from NostrDB.

use std::ops::ControlFlow;
use std::thread;
use std::time::Duration;

use nostrdb::{Error as NdbError, Filter, Ndb, Note, NoteReply, Transaction};
use thiserror::Error;

const INGEST_RETRY_DELAY: Duration = Duration::from_millis(100);

/// A root kind-1 corpus derivation failure.
#[derive(Debug, Error)]
pub enum CorpusDerivationError {
    /// A NostrDB operation failed.
    #[error("NostrDB operation failed: {0}")]
    Ndb(#[from] NdbError),

    /// NostrDB's C API represents event and output-buffer lengths as signed integers.
    #[error("stored event is too large for NostrDB's signed length")]
    EventTooLarge,
}

/// Stream root, non-quote kind-1 events from `source` into `corpus`.
///
/// The source query stays cursor-driven: the current note is classified and
/// either discarded or accepted by the destination before the cursor advances.
/// NostrDB handles duplicate events when an interrupted derivation is replayed.
pub fn derive_corpus(source: &Ndb, corpus: &Ndb) -> Result<(), CorpusDerivationError> {
    let txn = Transaction::new(source)?;
    let kind_one = Filter::new().kinds([1]).build();

    source.try_fold(&txn, &[kind_one], Ok(()), |state, note| {
        derive_note(state, note, corpus)
    })?
}

fn derive_note(
    state: Result<(), CorpusDerivationError>,
    note: Note<'_>,
    corpus: &Ndb,
) -> ControlFlow<Result<(), CorpusDerivationError>, Result<(), CorpusDerivationError>> {
    let Ok(()) = state else {
        return ControlFlow::Break(state);
    };

    if !is_root_non_quote(&note) {
        return ControlFlow::Continue(Ok(()));
    }

    let json = match note_json(&note) {
        Ok(json) => json,
        Err(error) => return ControlFlow::Break(Err(error)),
    };
    match submit_with_retry(corpus, &json) {
        Ok(()) => ControlFlow::Continue(Ok(())),
        Err(error) => ControlFlow::Break(Err(error)),
    }
}

fn is_root_non_quote(note: &Note<'_>) -> bool {
    let relation = NoteReply::new(note.tags());
    !relation.is_reply()
        && relation.mention().is_none()
        && !note
            .tags()
            .into_iter()
            .any(|tag| tag.get_str(0) == Some("q"))
}

fn note_json(note: &Note<'_>) -> Result<String, CorpusDerivationError> {
    let mut capacity = note.size().saturating_mul(2).max(1_024);
    loop {
        if capacity > i32::MAX as usize {
            return Err(CorpusDerivationError::EventTooLarge);
        }
        match note.json_with_bufsize(capacity) {
            Ok(json) if json.len() <= i32::MAX as usize => return Ok(json),
            Ok(_) => return Err(CorpusDerivationError::EventTooLarge),
            Err(NdbError::BufferOverflow) => {
                capacity = capacity
                    .checked_mul(2)
                    .ok_or(CorpusDerivationError::EventTooLarge)?;
            }
            Err(error) => return Err(error.into()),
        }
    }
}

fn submit_with_retry(corpus: &Ndb, event: &str) -> Result<(), CorpusDerivationError> {
    loop {
        match corpus.process_event(event) {
            Ok(()) => return Ok(()),
            Err(NdbError::NoteProcessFailed) => thread::sleep(INGEST_RETRY_DELAY),
            Err(error) => return Err(error.into()),
        }
    }
}
