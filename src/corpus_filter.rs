//! Streaming token-length filtering from the root kind-1 corpus into NostrDB.

use std::collections::BTreeSet;
use std::fs::{self, File};
use std::io::{BufReader, Read};
use std::ops::ControlFlow;
use std::path::{Path, PathBuf};
use std::thread;
use std::time::Duration;

use nostrdb::{Error as NdbError, Filter, Ndb, Note, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;
use tokenizers::Tokenizer;

const TOKEN_LIMIT: u32 = 512;
const FILTER_BATCH_EVENTS: usize = 1_024;
const FILTER_BATCH_CONTENT_BYTES: usize = 8 * 1_024 * 1_024;
const INGEST_RETRY_DELAY: Duration = Duration::from_millis(100);
const TOKENIZER_LOCK_SCHEMA_VERSION: u32 = 1;
const RAW_TOKEN_LENGTH_RULE: &str = "tokenizer-output-ids-before-model-truncation-v1";
const PPLX_TOKENIZER_LOCK_JSON: &str = include_str!("../models/pplx-embed-v1-tokenizer.lock.json");
const GTE_TOKENIZER_LOCK_JSON: &str =
    include_str!("../models/gte-multilingual-base-tokenizer.lock.json");

/// A Stage 3 corpus-filtering failure.
#[derive(Debug, Error)]
pub enum CorpusFilterError {
    /// A NostrDB operation failed.
    #[error("NostrDB operation failed: {0}")]
    Ndb(#[from] NdbError),

    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },

    /// A frozen tokenizer lock or its files are invalid.
    #[error("invalid frozen tokenizer: {0}")]
    FrozenTokenizer(String),

    /// The tokenizer runtime failed.
    #[error("tokenizer failed while {operation}: {message}")]
    Tokenizer {
        operation: &'static str,
        message: String,
    },

    /// A tokenizer did not return one length for every input row.
    #[error("{tokenizer} returned {actual} lengths for {expected} events")]
    LengthCount {
        tokenizer: &'static str,
        expected: usize,
        actual: usize,
    },

    /// The configured token limit differs from the fixed MVP policy.
    #[error("{tokenizer} is configured for {actual} tokens; Stage 3 requires 512")]
    TokenLimit {
        tokenizer: &'static str,
        actual: u32,
    },

    /// A NostrDB event cannot be serialized through its signed-size interface.
    #[error("stored event is too large for NostrDB's signed length")]
    EventTooLarge,

    /// A corpus counter overflowed.
    #[error("corpus filter count overflowed u64")]
    CountOverflow,
}

/// Counts produced by one complete pass over `corpus.ndb`.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct CorpusFilterSummary {
    /// Events read from the Stage 2 corpus.
    pub scanned_events: u64,
    /// Events submitted unchanged to `filtered.ndb`.
    pub retained_events: u64,
    /// Events rejected for exceeding 512 tokens under either tokenizer.
    pub excluded_events: u64,
}

/// Versioned handling of empty event content.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(tag = "strategy", rename_all = "snake_case")]
enum EmptyInputRule {
    Unchanged,
    ReplaceWithToken { token: String, token_id: u32 },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct TokenizerFileLock {
    path: String,
    bytes: u64,
    sha256: String,
}

#[derive(Deserialize)]
struct FrozenTokenizerLockDocument {
    schema_version: u32,
    tokenizer_id: String,
    configured_input_tokens: u32,
    input_rule: String,
    token_length_rule: String,
    empty_input: EmptyInputRule,
    files: Vec<TokenizerFileLock>,
}

/// Parsed immutable tokenizer identity used by Stage 3.
#[derive(Clone, Debug)]
pub struct FrozenTokenizerLock {
    tokenizer_id: String,
    configured_input_tokens: u32,
    empty_input: EmptyInputRule,
    files: Vec<TokenizerFileLock>,
}

impl FrozenTokenizerLock {
    /// Parse and validate one frozen tokenizer lock.
    pub fn from_json(json: &str) -> Result<Self, CorpusFilterError> {
        let document: FrozenTokenizerLockDocument =
            serde_json::from_str(json).map_err(|error| {
                CorpusFilterError::FrozenTokenizer(format!("cannot decode lock JSON: {error}"))
            })?;
        validate_lock(&document)?;
        Ok(Self {
            tokenizer_id: document.tokenizer_id,
            configured_input_tokens: document.configured_input_tokens,
            empty_input: document.empty_input,
            files: document.files,
        })
    }
}

/// Return the exact checked-in Perplexity tokenizer lock.
pub fn pplx_tokenizer_lock() -> Result<FrozenTokenizerLock, CorpusFilterError> {
    FrozenTokenizerLock::from_json(PPLX_TOKENIZER_LOCK_JSON)
}

/// Return the exact checked-in GTE tokenizer lock.
pub fn gte_tokenizer_lock() -> Result<FrozenTokenizerLock, CorpusFilterError> {
    FrozenTokenizerLock::from_json(GTE_TOKENIZER_LOCK_JSON)
}

/// Raw counter loaded only after every frozen tokenizer file is verified.
pub struct FrozenTokenizer {
    tokenizer: Tokenizer,
    lock: FrozenTokenizerLock,
}

impl std::fmt::Debug for FrozenTokenizer {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("FrozenTokenizer")
            .field("tokenizer_id", &self.lock.tokenizer_id)
            .field(
                "configured_input_tokens",
                &self.lock.configured_input_tokens,
            )
            .finish_non_exhaustive()
    }
}

impl FrozenTokenizer {
    /// Verify all locked files and load the tokenizer without truncation or padding.
    pub fn load(
        tokenizer_dir: impl AsRef<Path>,
        lock: FrozenTokenizerLock,
    ) -> Result<Self, CorpusFilterError> {
        let tokenizer_dir =
            fs::canonicalize(tokenizer_dir.as_ref()).map_err(|source| CorpusFilterError::Io {
                operation: "resolve",
                path: tokenizer_dir.as_ref().to_owned(),
                source,
            })?;
        verify_locked_files(&tokenizer_dir, &lock)?;
        let tokenizer_file = lock
            .files
            .iter()
            .find(|file| file.path == "tokenizer.json")
            .expect("validated lock contains tokenizer.json");
        let mut tokenizer = Tokenizer::from_file(tokenizer_dir.join(&tokenizer_file.path))
            .map_err(|error| CorpusFilterError::Tokenizer {
                operation: "loading frozen tokenizer",
                message: error.to_string(),
            })?;
        tokenizer
            .with_truncation(None)
            .map_err(|error| CorpusFilterError::Tokenizer {
                operation: "disabling truncation",
                message: error.to_string(),
            })?;
        tokenizer.with_padding(None);
        if let EmptyInputRule::ReplaceWithToken { token, token_id } = &lock.empty_input
            && tokenizer.token_to_id(token) != Some(*token_id)
        {
            return Err(CorpusFilterError::FrozenTokenizer(format!(
                "{} does not map empty-input token `{token}` to {token_id}",
                lock.tokenizer_id
            )));
        }
        Ok(Self { tokenizer, lock })
    }

    fn configured_input_tokens(&self) -> u32 {
        self.lock.configured_input_tokens
    }

    /// Count tokens after normal special tokens and before truncation or padding.
    fn raw_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>, CorpusFilterError> {
        if texts.is_empty() {
            return Ok(Vec::new());
        }
        let inputs = texts
            .iter()
            .map(|text| match (&self.lock.empty_input, *text) {
                (EmptyInputRule::ReplaceWithToken { token, .. }, "") => token.as_str(),
                _ => *text,
            })
            .collect::<Vec<_>>();
        self.tokenizer
            .encode_batch(inputs, true)
            .map_err(|error| CorpusFilterError::Tokenizer {
                operation: "measuring raw token lengths",
                message: error.to_string(),
            })?
            .iter()
            .map(|encoding| {
                u32::try_from(encoding.get_ids().len()).map_err(|_| {
                    CorpusFilterError::FrozenTokenizer(
                        "raw token length does not fit u32".to_owned(),
                    )
                })
            })
            .collect()
    }
}

/// Stream all Stage 2 events and copy only rows within both 512-token limits.
///
/// NostrDB owns replay deduplication. A retry after partial progress therefore
/// produces the same destination event set.
pub fn filter_corpus(
    source: &Ndb,
    filtered: &Ndb,
    pplx: &mut FrozenTokenizer,
    gte: &mut FrozenTokenizer,
) -> Result<CorpusFilterSummary, CorpusFilterError> {
    require_token_limit("Perplexity tokenizer", pplx.configured_input_tokens())?;
    require_token_limit("GTE tokenizer", gte.configured_input_tokens())?;

    let txn = Transaction::new(source)?;
    let all = Filter::new().build();
    let mut state = source.try_fold(&txn, &[all], Ok(FilterState::new()), |state, note| {
        queue_note(state, note, filtered, pplx, gte)
    })??;
    flush_batch(&mut state, filtered, pplx, gte)?;
    Ok(state.summary)
}

struct FilterState<'txn> {
    pending: Vec<Note<'txn>>,
    pending_content_bytes: usize,
    summary: CorpusFilterSummary,
}

impl FilterState<'_> {
    fn new() -> Self {
        Self {
            pending: Vec::with_capacity(FILTER_BATCH_EVENTS),
            pending_content_bytes: 0,
            summary: CorpusFilterSummary {
                scanned_events: 0,
                retained_events: 0,
                excluded_events: 0,
            },
        }
    }
}

fn queue_note<'txn>(
    state: Result<FilterState<'txn>, CorpusFilterError>,
    note: Note<'txn>,
    filtered: &Ndb,
    pplx: &mut FrozenTokenizer,
    gte: &mut FrozenTokenizer,
) -> ControlFlow<
    Result<FilterState<'txn>, CorpusFilterError>,
    Result<FilterState<'txn>, CorpusFilterError>,
> {
    let Ok(mut state) = state else {
        return ControlFlow::Break(state);
    };
    let content_bytes = note.content().len();
    if !state.pending.is_empty()
        && state.pending_content_bytes.saturating_add(content_bytes) > FILTER_BATCH_CONTENT_BYTES
        && let Err(error) = flush_batch(&mut state, filtered, pplx, gte)
    {
        return ControlFlow::Break(Err(error));
    }
    state.summary.scanned_events = match increment(state.summary.scanned_events) {
        Ok(count) => count,
        Err(error) => return ControlFlow::Break(Err(error)),
    };
    state.pending_content_bytes = state.pending_content_bytes.saturating_add(content_bytes);
    state.pending.push(note);
    if (state.pending.len() == FILTER_BATCH_EVENTS
        || state.pending_content_bytes >= FILTER_BATCH_CONTENT_BYTES)
        && let Err(error) = flush_batch(&mut state, filtered, pplx, gte)
    {
        return ControlFlow::Break(Err(error));
    }
    ControlFlow::Continue(Ok(state))
}

fn flush_batch(
    state: &mut FilterState<'_>,
    filtered: &Ndb,
    pplx: &mut FrozenTokenizer,
    gte: &mut FrozenTokenizer,
) -> Result<(), CorpusFilterError> {
    if state.pending.is_empty() {
        return Ok(());
    }
    let texts = state.pending.iter().map(Note::content).collect::<Vec<_>>();
    let pplx_lengths = pplx.raw_token_lengths(&texts)?;
    require_length_count("Perplexity tokenizer", texts.len(), pplx_lengths.len())?;
    let gte_lengths = gte.raw_token_lengths(&texts)?;
    require_length_count("GTE tokenizer", texts.len(), gte_lengths.len())?;

    for ((note, pplx_length), gte_length) in state.pending.iter().zip(pplx_lengths).zip(gte_lengths)
    {
        if pplx_length <= TOKEN_LIMIT && gte_length <= TOKEN_LIMIT {
            submit_with_retry(filtered, &note_json(note)?)?;
            state.summary.retained_events = increment(state.summary.retained_events)?;
        } else {
            state.summary.excluded_events = increment(state.summary.excluded_events)?;
        }
    }
    state.pending.clear();
    state.pending_content_bytes = 0;
    Ok(())
}

fn require_token_limit(tokenizer: &'static str, actual: u32) -> Result<(), CorpusFilterError> {
    if actual == TOKEN_LIMIT {
        Ok(())
    } else {
        Err(CorpusFilterError::TokenLimit { tokenizer, actual })
    }
}

fn require_length_count(
    tokenizer: &'static str,
    expected: usize,
    actual: usize,
) -> Result<(), CorpusFilterError> {
    if actual == expected {
        Ok(())
    } else {
        Err(CorpusFilterError::LengthCount {
            tokenizer,
            expected,
            actual,
        })
    }
}

fn increment(count: u64) -> Result<u64, CorpusFilterError> {
    count.checked_add(1).ok_or(CorpusFilterError::CountOverflow)
}

fn note_json(note: &Note<'_>) -> Result<String, CorpusFilterError> {
    let mut capacity = note.size().saturating_mul(2).max(1_024);
    loop {
        if capacity > i32::MAX as usize {
            return Err(CorpusFilterError::EventTooLarge);
        }
        match note.json_with_bufsize(capacity) {
            Ok(json) if json.len() <= i32::MAX as usize => return Ok(json),
            Ok(_) => return Err(CorpusFilterError::EventTooLarge),
            Err(NdbError::BufferOverflow) => {
                capacity = capacity
                    .checked_mul(2)
                    .ok_or(CorpusFilterError::EventTooLarge)?;
            }
            Err(error) => return Err(error.into()),
        }
    }
}

fn submit_with_retry(filtered: &Ndb, event: &str) -> Result<(), CorpusFilterError> {
    loop {
        match filtered.process_event(event) {
            Ok(()) => return Ok(()),
            Err(NdbError::NoteProcessFailed) => thread::sleep(INGEST_RETRY_DELAY),
            Err(error) => return Err(error.into()),
        }
    }
}

fn validate_lock(document: &FrozenTokenizerLockDocument) -> Result<(), CorpusFilterError> {
    if document.schema_version != TOKENIZER_LOCK_SCHEMA_VERSION
        || document.tokenizer_id.is_empty()
        || document.configured_input_tokens == 0
        || document.input_rule.is_empty()
        || document.token_length_rule != RAW_TOKEN_LENGTH_RULE
        || document.files.is_empty()
    {
        return Err(CorpusFilterError::FrozenTokenizer(
            "lock identity or tokenization rules are incomplete".to_owned(),
        ));
    }
    if let EmptyInputRule::ReplaceWithToken { token, .. } = &document.empty_input
        && token.is_empty()
    {
        return Err(CorpusFilterError::FrozenTokenizer(
            "empty-input replacement token is empty".to_owned(),
        ));
    }
    let mut paths = BTreeSet::new();
    for file in &document.files {
        if !safe_file_name(&file.path)
            || file.bytes == 0
            || !valid_sha256(&file.sha256)
            || !paths.insert(file.path.as_str())
        {
            return Err(CorpusFilterError::FrozenTokenizer(
                "locked file metadata is invalid".to_owned(),
            ));
        }
    }
    if !paths.contains("tokenizer.json") {
        return Err(CorpusFilterError::FrozenTokenizer(
            "lock does not contain tokenizer.json".to_owned(),
        ));
    }
    Ok(())
}

fn verify_locked_files(
    tokenizer_dir: &Path,
    lock: &FrozenTokenizerLock,
) -> Result<(), CorpusFilterError> {
    for file in &lock.files {
        let path = tokenizer_dir.join(&file.path);
        let actual_bytes = fs::metadata(&path)
            .map_err(|source| CorpusFilterError::Io {
                operation: "read metadata for",
                path: path.clone(),
                source,
            })?
            .len();
        if actual_bytes != file.bytes {
            return Err(CorpusFilterError::FrozenTokenizer(format!(
                "`{}` has {actual_bytes} bytes; lock records {}",
                path.display(),
                file.bytes
            )));
        }
        if sha256_file(&path)? != file.sha256 {
            return Err(CorpusFilterError::FrozenTokenizer(format!(
                "`{}` checksum does not match its lock",
                path.display()
            )));
        }
    }
    Ok(())
}

fn sha256_file(path: &Path) -> Result<String, CorpusFilterError> {
    let file = File::open(path).map_err(|source| CorpusFilterError::Io {
        operation: "open",
        path: path.to_owned(),
        source,
    })?;
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1_024];
    loop {
        let bytes = reader
            .read(&mut buffer)
            .map_err(|source| CorpusFilterError::Io {
                operation: "read",
                path: path.to_owned(),
                source,
            })?;
        if bytes == 0 {
            break;
        }
        hasher.update(&buffer[..bytes]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn safe_file_name(name: &str) -> bool {
    !name.is_empty()
        && name != "."
        && name != ".."
        && name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}
