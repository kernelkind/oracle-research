//! Reproducible blind evaluation of GlotLID on a Nostr corpus sample.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::path::{Path, PathBuf};

use fasttext::FastText;
use nostrdb::Transaction;
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::hash_file;
use crate::english_filter::{self, classifier_input, select_sampled_event_ids};
use crate::snapshot::{Validation, ndb_error, open_ndb};

/// Fixed number of corpus notes in the approved CREC-59 pilot.
pub const PILOT_SAMPLE_SIZE: usize = 1_000;
/// Fixed sample seed recorded by the pilot artifact.
pub const PILOT_SAMPLE_SEED: &str = "crec-59-english-eligibility-pilot-v1";
/// Pinned GlotLID v3 model file SHA-256.
pub const GLOTLID_V3_SHA256: &str =
    "a818b6bd42a628ab47d3dfc1578c7ea615c45381f3494c42535e31e8c4cafc9e";
/// Hugging Face repository commit that owns the pinned model.
pub const GLOTLID_V3_REPOSITORY_COMMIT: &str = "85cd6716494360367b75f642b5bc78667605d0b4";

const SCHEMA_VERSION: u32 = 1;
const SELECTION_RULE: &str = "bottom-sha256-over-all-ordered-event-ids-v1";
const NORMALIZATION_POLICY: &str =
    "remove-urls-and-structurally-valid-nip19-references-collapse-whitespace-v2";
const CLASSIFICATION_POLICY: &str = "empty-is-neutral-otherwise-glotlid-v3-top1-eng-or-zxx-v1";
const TOP_PREDICTIONS: usize = 5;

/// A CREC-59 pilot failure.
#[derive(Debug, Error)]
pub enum Error {
    /// Core English-filter preparation failed.
    #[error(transparent)]
    EnglishFilter(#[from] english_filter::Error),

    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        /// Operation being attempted.
        operation: &'static str,
        /// Affected path.
        path: PathBuf,
        /// Filesystem failure.
        #[source]
        source: std::io::Error,
    },

    /// JSON serialization or deserialization failed.
    #[error("failed to {operation} JSON `{path}`: {source}")]
    Json {
        /// Operation being attempted.
        operation: &'static str,
        /// Affected path.
        path: PathBuf,
        /// JSON failure.
        #[source]
        source: serde_json::Error,
    },

    /// NostrDB access failed.
    #[error("NostrDB operation failed: {0}")]
    Ndb(#[from] crate::snapshot::Error),

    /// The pinned GlotLID model could not be loaded.
    #[error("failed to load GlotLID model `{path}`: {message}")]
    Model {
        /// Model path.
        path: PathBuf,
        /// Loader detail.
        message: String,
    },

    /// The output directory already exists.
    #[error("pilot output already exists: `{0}`")]
    OutputExists(PathBuf),

    /// A required pilot invariant was violated.
    #[error("English-filter pilot invariant failed: {0}")]
    Invariant(String),
}

/// One sample row safe to expose to a blind evaluator.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BlindRecord {
    /// Stable position in the sampled set.
    pub sample_ordinal: u32,
    /// Lowercase hexadecimal event ID.
    pub event_id: String,
    /// Original event content, preserved exactly.
    pub original_content: String,
    /// Derived language-classifier input.
    pub classifier_input: String,
}

/// One ranked GlotLID label.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct LanguagePrediction {
    /// GlotLID label including its `__label__` prefix.
    pub label: String,
    /// FastText model score.
    pub confidence: f32,
}

/// Eligibility decision made without private recommendation information.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ClassifierDecision {
    /// The top model label is English.
    KeepEnglish,
    /// No linguistic input remains or the top model label is `zxx`.
    KeepLanguageNeutral,
    /// The top label is neither English nor language-neutral.
    Exclude,
}

/// Classifier result kept separate from blind evaluation input.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct PredictionRecord {
    /// Stable position in the sampled set.
    pub sample_ordinal: u32,
    /// Lowercase hexadecimal event ID.
    pub event_id: String,
    /// Ranked model output, empty only for empty classifier input.
    pub predictions: Vec<LanguagePrediction>,
    /// Frozen initial eligibility decision.
    pub decision: ClassifierDecision,
}

/// Durable identity of a completed blind pilot.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PilotManifest {
    /// Manifest format version.
    pub schema_version: u32,
    /// Exact sample size.
    pub sample_size: u32,
    /// Exact deterministic seed.
    pub sample_seed: String,
    /// Algorithm selecting rows from the complete source order.
    pub selection_rule: String,
    /// SHA-256 of the complete ordered corpus IDs.
    pub ordered_event_ids_sha256: String,
    /// Rule used to derive classifier input.
    pub normalization_policy: String,
    /// Rule mapping model output to eligibility.
    pub classification_policy: String,
    /// Exact GlotLID model SHA-256.
    pub model_sha256: String,
    /// Exact upstream model repository commit.
    pub model_repository_commit: String,
    /// SHA-256 of the blind rows.
    pub blind_records_sha256: String,
    /// SHA-256 of the separately stored predictions.
    pub prediction_records_sha256: String,
}

/// Manual truth category assigned without classifier output.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ManualJudgment {
    /// Primarily English natural-language content.
    English,
    /// Content without a natural language, such as code or identifiers.
    LanguageNeutral,
    /// Primarily non-English natural-language content.
    PrimarilyNonEnglish,
    /// The evaluator cannot confidently apply the approved rule.
    Ambiguous,
}

impl ManualJudgment {
    fn eligible(self) -> Option<bool> {
        match self {
            Self::English | Self::LanguageNeutral => Some(true),
            Self::PrimarilyNonEnglish => Some(false),
            Self::Ambiguous => None,
        }
    }
}

/// One blind manual judgment.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct JudgmentRecord {
    /// Event being judged.
    pub event_id: String,
    /// Human-applied truth category.
    pub judgment: ManualJudgment,
}

/// Counts and Wilson interval for one binary metric.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BinomialMetric {
    /// Successful cases.
    pub successes: u64,
    /// Cases in the metric denominator.
    pub total: u64,
    /// Point estimate, or null when the denominator is zero.
    pub proportion: Option<f64>,
    /// Lower 95% Wilson bound, or null when the denominator is zero.
    pub confidence_95_low: Option<f64>,
    /// Upper 95% Wilson bound, or null when the denominator is zero.
    pub confidence_95_high: Option<f64>,
}

/// Confusion counts for an evaluated subset.
#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct ConfusionCounts {
    /// Eligible notes retained.
    pub true_positive: u64,
    /// Ineligible notes retained.
    pub false_positive: u64,
    /// Eligible notes excluded.
    pub false_negative: u64,
    /// Ineligible notes excluded.
    pub true_negative: u64,
    /// Notes whose manual judgment was ambiguous.
    pub ambiguous: u64,
}

/// Report derived only after all blind judgments are complete.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct PilotReport {
    /// Report format version.
    pub schema_version: u32,
    /// SHA-256 of the pilot manifest being evaluated.
    pub pilot_manifest_sha256: String,
    /// SHA-256 of the complete manual judgment file.
    pub judgments_sha256: String,
    /// Total rows in the pilot.
    pub sample_size: u64,
    /// Rows with a non-ambiguous manual judgment.
    pub evaluated_rows: u64,
    /// Overall confusion counts.
    pub confusion: ConfusionCounts,
    /// Among retained notes, the fraction manually eligible.
    pub retained_precision: BinomialMetric,
    /// Among manually eligible notes, the fraction retained.
    pub eligible_recall: BinomialMetric,
    /// Fraction of non-ambiguous decisions matching manual truth.
    pub overall_accuracy: BinomialMetric,
    /// Confusion grouped by derived classifier-input length.
    pub by_length: BTreeMap<String, ConfusionCounts>,
    /// Confusion grouped by top model confidence.
    pub by_confidence: BTreeMap<String, ConfusionCounts>,
    /// IDs for every non-ambiguous disagreement.
    pub disagreement_event_ids: Vec<String>,
}

/// Build and atomically publish the fixed blind pilot artifact.
pub fn build_pilot(
    deduplicated_directory: impl AsRef<Path>,
    output_directory: impl AsRef<Path>,
    model_path: impl AsRef<Path>,
) -> Result<PilotManifest, Error> {
    let deduplicated_directory = deduplicated_directory.as_ref();
    let output_directory = output_directory.as_ref();
    let model_path = model_path.as_ref();
    if output_directory.exists() {
        return Err(Error::OutputExists(output_directory.to_owned()));
    }

    let ordered_path = deduplicated_directory.join("ordered-event-ids.bin");
    let corpus_path = deduplicated_directory.join("ndb");
    let model_sha256 = hash_file(model_path)?;
    if model_sha256 != GLOTLID_V3_SHA256 {
        return Err(Error::Invariant(format!(
            "GlotLID model SHA-256 is {model_sha256}; expected pinned v3 {GLOTLID_V3_SHA256}"
        )));
    }
    let selected = select_sampled_event_ids(
        &ordered_path,
        PILOT_SAMPLE_SIZE,
        PILOT_SAMPLE_SEED.as_bytes(),
    )?;
    let model = FastText::load_model(model_path).map_err(|source| Error::Model {
        path: model_path.to_owned(),
        message: source.to_string(),
    })?;
    validate_model(&model)?;

    let parent = output_directory.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage = output_directory.with_extension(format!("partial-{}", std::process::id()));
    if stage.exists() {
        return Err(Error::OutputExists(stage));
    }
    fs::create_dir(&stage).map_err(|source| io_error("create", &stage, source))?;
    let result = build_in_stage(
        &corpus_path,
        &ordered_path,
        model_sha256,
        selected,
        &model,
        &stage,
    );
    let manifest = match result {
        Ok(manifest) => manifest,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage);
            return Err(error);
        }
    };
    if output_directory.exists() {
        let _ = fs::remove_dir_all(&stage);
        return Err(Error::OutputExists(output_directory.to_owned()));
    }
    fs::rename(&stage, output_directory)
        .map_err(|source| io_error("publish", output_directory, source))?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))?;
    Ok(manifest)
}

fn build_in_stage(
    corpus_path: &Path,
    ordered_path: &Path,
    model_sha256: String,
    selected: Vec<[u8; 32]>,
    model: &FastText,
    stage: &Path,
) -> Result<PilotManifest, Error> {
    let corpus = open_ndb(corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let blind_path = stage.join("blind.jsonl");
    let predictions_path = stage.join("predictions.jsonl");
    let mut blind = BufWriter::new(
        File::create(&blind_path).map_err(|source| io_error("create", &blind_path, source))?,
    );
    let mut predictions = BufWriter::new(
        File::create(&predictions_path)
            .map_err(|source| io_error("create", &predictions_path, source))?,
    );

    for (index, id) in selected.into_iter().enumerate() {
        let note = corpus
            .get_note_by_id(&transaction, &id)
            .map_err(|source| ndb_error("load event from", corpus_path, source))?;
        let original_content = note.content().to_owned();
        let classifier_input = classifier_input(&original_content);
        let event_id = encode_hex(&id);
        let sample_ordinal = u32::try_from(index + 1)
            .map_err(|_| Error::Invariant("sample ordinal does not fit u32".to_owned()))?;
        write_json_line(
            &mut blind,
            &blind_path,
            &BlindRecord {
                sample_ordinal,
                event_id: event_id.clone(),
                original_content,
                classifier_input: classifier_input.clone(),
            },
        )?;

        let ranked = if classifier_input.is_empty() {
            Vec::new()
        } else {
            model
                .predict(&classifier_input, TOP_PREDICTIONS, 0.0)
                .into_iter()
                .map(|prediction| LanguagePrediction {
                    label: prediction.label,
                    confidence: prediction.prob,
                })
                .collect::<Vec<_>>()
        };
        write_json_line(
            &mut predictions,
            &predictions_path,
            &PredictionRecord {
                sample_ordinal,
                event_id,
                decision: classify(&classifier_input, &ranked),
                predictions: ranked,
            },
        )?;
    }
    blind
        .flush()
        .map_err(|source| io_error("flush", &blind_path, source))?;
    blind
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &blind_path, source))?;
    predictions
        .flush()
        .map_err(|source| io_error("flush", &predictions_path, source))?;
    predictions
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &predictions_path, source))?;
    drop(transaction);
    drop(corpus);

    let manifest = PilotManifest {
        schema_version: SCHEMA_VERSION,
        sample_size: PILOT_SAMPLE_SIZE as u32,
        sample_seed: PILOT_SAMPLE_SEED.to_owned(),
        selection_rule: SELECTION_RULE.to_owned(),
        ordered_event_ids_sha256: hash_file(ordered_path)?,
        normalization_policy: NORMALIZATION_POLICY.to_owned(),
        classification_policy: CLASSIFICATION_POLICY.to_owned(),
        model_sha256,
        model_repository_commit: GLOTLID_V3_REPOSITORY_COMMIT.to_owned(),
        blind_records_sha256: hash_file(&blind_path)?,
        prediction_records_sha256: hash_file(&predictions_path)?,
    };
    write_json_file(&stage.join("manifest.json"), &manifest)?;
    Ok(manifest)
}

fn validate_model(model: &FastText) -> Result<(), Error> {
    let (labels, _) = model.get_labels();
    if !labels.iter().any(|label| label == "__label__eng_Latn") {
        return Err(Error::Invariant(
            "pinned model does not contain __label__eng_Latn".to_owned(),
        ));
    }
    if !labels.iter().any(|label| is_zxx_label(label)) {
        return Err(Error::Invariant(
            "pinned model does not contain a zxx language-neutral label".to_owned(),
        ));
    }
    Ok(())
}

fn classify(input: &str, predictions: &[LanguagePrediction]) -> ClassifierDecision {
    if input.is_empty() {
        return ClassifierDecision::KeepLanguageNeutral;
    }
    match predictions
        .first()
        .map(|prediction| prediction.label.as_str())
    {
        Some("__label__eng_Latn") => ClassifierDecision::KeepEnglish,
        Some(label) if is_zxx_label(label) => ClassifierDecision::KeepLanguageNeutral,
        Some(_) | None => ClassifierDecision::Exclude,
    }
}

fn is_zxx_label(label: &str) -> bool {
    label == "__label__zxx" || label.starts_with("__label__zxx_")
}

fn write_json_line<T: Serialize>(
    writer: &mut BufWriter<File>,
    path: &Path,
    value: &T,
) -> Result<(), Error> {
    serde_json::to_writer(&mut *writer, value).map_err(|source| Error::Json {
        operation: "write",
        path: path.to_owned(),
        source,
    })?;
    writer
        .write_all(b"\n")
        .map_err(|source| io_error("write", path, source))
}

fn write_json_file<T: Serialize>(path: &Path, value: &T) -> Result<(), Error> {
    let file = File::create(path).map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, value).map_err(|source| Error::Json {
        operation: "write",
        path: path.to_owned(),
        source,
    })?;
    writer
        .write_all(b"\n")
        .map_err(|source| io_error("write", path, source))?;
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn read_json_lines<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<Vec<T>, Error> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    BufReader::new(file)
        .lines()
        .enumerate()
        .map(|(index, line)| {
            let line = line.map_err(|source| io_error("read", path, source))?;
            serde_json::from_str(&line).map_err(|source| Error::Json {
                operation: "read",
                path: path.to_owned(),
                source: serde_json::Error::io(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    format!("line {}: {source}", index + 1),
                )),
            })
        })
        .collect()
}

fn encode_hex(id: &[u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in id {
        use std::fmt::Write as _;
        write!(output, "{byte:02x}").expect("write to String");
    }
    output
}

fn io_error(operation: &'static str, path: &Path, source: std::io::Error) -> Error {
    Error::Io {
        operation,
        path: path.to_owned(),
        source,
    }
}

/// Collect resumable manual judgments while never opening classifier predictions.
pub fn label_pilot(
    pilot_directory: impl AsRef<Path>,
    input: &mut impl BufRead,
    output: &mut impl Write,
    page_size: usize,
) -> Result<usize, Error> {
    let pilot_directory = pilot_directory.as_ref();
    if !(1..=50).contains(&page_size) {
        return Err(Error::Invariant(
            "blind-label page size must be between 1 and 50".to_owned(),
        ));
    }
    let manifest_path = pilot_directory.join("manifest.json");
    let blind_path = pilot_directory.join("blind.jsonl");
    let judgments_path = pilot_directory.join("judgments.jsonl");
    let manifest: PilotManifest = read_json_file(&manifest_path)?;
    if hash_file(&blind_path)? != manifest.blind_records_sha256 {
        return Err(Error::Invariant(
            "blind records do not match the pilot manifest".to_owned(),
        ));
    }
    let blind: Vec<BlindRecord> = read_json_lines(&blind_path)?;
    validate_blind_records(&manifest, &blind)?;
    let existing: Vec<JudgmentRecord> = if judgments_path.exists() {
        read_json_lines(&judgments_path)?
    } else {
        Vec::new()
    };
    let known_ids = blind
        .iter()
        .map(|record| record.event_id.as_str())
        .collect::<BTreeSet<_>>();
    let mut judged = BTreeSet::new();
    for judgment in existing {
        if !known_ids.contains(judgment.event_id.as_str()) {
            return Err(Error::Invariant(format!(
                "judgment names event {} outside the pilot",
                judgment.event_id
            )));
        }
        if !judged.insert(judgment.event_id) {
            return Err(Error::Invariant(
                "judgment file contains a duplicate event ID".to_owned(),
            ));
        }
    }

    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&judgments_path)
        .map_err(|source| io_error("open", &judgments_path, source))?;
    let mut writer = BufWriter::new(file);
    loop {
        let page = blind
            .iter()
            .filter(|record| !judged.contains(&record.event_id))
            .take(page_size)
            .collect::<Vec<_>>();
        if page.is_empty() {
            writeln!(output, "All {} blind judgments are complete.", judged.len())
                .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
            return Ok(judged.len());
        }

        writeln!(
            output,
            "\nBlind rows {}–{} of {}",
            judged.len() + 1,
            judged.len() + page.len(),
            blind.len()
        )
        .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
        for (page_index, record) in page.iter().enumerate() {
            writeln!(
                output,
                "\n[{}] {}/{} {}\noriginal: {}\nclassifier input: {}",
                page_index + 1,
                record.sample_ordinal,
                blind.len(),
                record.event_id,
                serde_json::to_string(&record.original_content).expect("serialize String"),
                serde_json::to_string(&record.classifier_input).expect("serialize String")
            )
            .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
        }
        writeln!(
            output,
            "\nEnter {} labels in order: e=English, z=language-neutral, n=primarily non-English, u=ambiguous; q=quit",
            page.len()
        )
        .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
        output
            .flush()
            .map_err(|source| io_error("flush terminal output for", &judgments_path, source))?;

        let mut response = String::new();
        let bytes = input
            .read_line(&mut response)
            .map_err(|source| io_error("read terminal input for", &judgments_path, source))?;
        if bytes == 0 {
            return Err(Error::Invariant(
                "terminal input ended before blind labeling completed".to_owned(),
            ));
        }
        if response.trim().eq_ignore_ascii_case("q") {
            return Ok(judged.len());
        }
        let labels = response
            .chars()
            .filter(|character| !character.is_whitespace())
            .map(parse_manual_label)
            .collect::<Result<Vec<_>, _>>();
        let Ok(labels) = labels else {
            writeln!(output, "Invalid label. Use only e, z, n, or u.")
                .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
            continue;
        };
        if labels.len() != page.len() {
            writeln!(
                output,
                "Expected {} labels; received {}.",
                page.len(),
                labels.len()
            )
            .map_err(|source| io_error("write terminal output for", &judgments_path, source))?;
            continue;
        }
        for (record, judgment) in page.into_iter().zip(labels) {
            write_json_line(
                &mut writer,
                &judgments_path,
                &JudgmentRecord {
                    event_id: record.event_id.clone(),
                    judgment,
                },
            )?;
            judged.insert(record.event_id.clone());
        }
        writer
            .flush()
            .map_err(|source| io_error("flush", &judgments_path, source))?;
        writer
            .get_ref()
            .sync_all()
            .map_err(|source| io_error("sync", &judgments_path, source))?;
    }
}

/// Calculate the complete report from already separated blind data and predictions.
pub fn calculate_report(
    pilot_manifest_sha256: &str,
    judgments_sha256: &str,
    blind: &[BlindRecord],
    predictions: &[PredictionRecord],
    judgments: &[JudgmentRecord],
) -> Result<PilotReport, Error> {
    if blind.len() != predictions.len() || blind.len() != judgments.len() {
        return Err(Error::Invariant(format!(
            "pilot has {} blind rows, {} predictions, and {} judgments",
            blind.len(),
            predictions.len(),
            judgments.len()
        )));
    }
    let mut truth = BTreeMap::new();
    for judgment in judgments {
        if truth
            .insert(judgment.event_id.as_str(), judgment.judgment)
            .is_some()
        {
            return Err(Error::Invariant(format!(
                "duplicate judgment for event {}",
                judgment.event_id
            )));
        }
    }

    let mut confusion = ConfusionCounts::default();
    let mut by_length = BTreeMap::<String, ConfusionCounts>::new();
    let mut by_confidence = BTreeMap::<String, ConfusionCounts>::new();
    let mut disagreements = Vec::new();
    for (blind_record, prediction) in blind.iter().zip(predictions) {
        if blind_record.sample_ordinal != prediction.sample_ordinal
            || blind_record.event_id != prediction.event_id
        {
            return Err(Error::Invariant(
                "blind and prediction rows are not identically ordered".to_owned(),
            ));
        }
        let judgment = truth.get(blind_record.event_id.as_str()).ok_or_else(|| {
            Error::Invariant(format!(
                "missing judgment for event {}",
                blind_record.event_id
            ))
        })?;
        let kept = prediction.decision != ClassifierDecision::Exclude;
        add_confusion(&mut confusion, kept, judgment.eligible());
        add_confusion(
            by_length
                .entry(length_bucket(&blind_record.classifier_input).to_owned())
                .or_default(),
            kept,
            judgment.eligible(),
        );
        add_confusion(
            by_confidence
                .entry(confidence_bucket(prediction).to_owned())
                .or_default(),
            kept,
            judgment.eligible(),
        );
        if judgment.eligible().is_some_and(|eligible| eligible != kept) {
            disagreements.push(blind_record.event_id.clone());
        }
    }
    if truth
        .keys()
        .any(|id| !blind.iter().any(|row| row.event_id == *id))
    {
        return Err(Error::Invariant(
            "judgment file contains an event outside the blind pilot".to_owned(),
        ));
    }

    let evaluated_rows = confusion.true_positive
        + confusion.false_positive
        + confusion.false_negative
        + confusion.true_negative;
    Ok(PilotReport {
        schema_version: SCHEMA_VERSION,
        pilot_manifest_sha256: pilot_manifest_sha256.to_owned(),
        judgments_sha256: judgments_sha256.to_owned(),
        sample_size: blind.len() as u64,
        evaluated_rows,
        retained_precision: binomial(
            confusion.true_positive,
            confusion.true_positive + confusion.false_positive,
        ),
        eligible_recall: binomial(
            confusion.true_positive,
            confusion.true_positive + confusion.false_negative,
        ),
        overall_accuracy: binomial(
            confusion.true_positive + confusion.true_negative,
            evaluated_rows,
        ),
        confusion,
        by_length,
        by_confidence,
        disagreement_event_ids: disagreements,
    })
}

/// Verify a completed blind pilot, score all judgments, and publish the report.
pub fn score_pilot(pilot_directory: impl AsRef<Path>) -> Result<PilotReport, Error> {
    let pilot_directory = pilot_directory.as_ref();
    let manifest_path = pilot_directory.join("manifest.json");
    let blind_path = pilot_directory.join("blind.jsonl");
    let predictions_path = pilot_directory.join("predictions.jsonl");
    let judgments_path = pilot_directory.join("judgments.jsonl");
    let report_path = pilot_directory.join("report.json");
    if report_path.exists() {
        return Err(Error::OutputExists(report_path));
    }
    let manifest: PilotManifest = read_json_file(&manifest_path)?;
    if hash_file(&blind_path)? != manifest.blind_records_sha256
        || hash_file(&predictions_path)? != manifest.prediction_records_sha256
    {
        return Err(Error::Invariant(
            "pilot rows do not match the manifest".to_owned(),
        ));
    }
    let blind: Vec<BlindRecord> = read_json_lines(&blind_path)?;
    validate_blind_records(&manifest, &blind)?;
    let predictions: Vec<PredictionRecord> = read_json_lines(&predictions_path)?;
    let judgments: Vec<JudgmentRecord> = read_json_lines(&judgments_path)?;
    let report = calculate_report(
        &hash_file(&manifest_path)?,
        &hash_file(&judgments_path)?,
        &blind,
        &predictions,
        &judgments,
    )?;
    write_json_file(&report_path, &report)?;
    let checksum_path = pilot_directory.join("report.sha256");
    let checksum = format!("{}  report.json\n", hash_file(&report_path)?);
    fs::write(&checksum_path, checksum)
        .map_err(|source| io_error("write", &checksum_path, source))?;
    File::open(&checksum_path)
        .and_then(|file| file.sync_all())
        .map_err(|source| io_error("sync", &checksum_path, source))?;
    Ok(report)
}

fn validate_blind_records(manifest: &PilotManifest, blind: &[BlindRecord]) -> Result<(), Error> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.sample_size as usize != PILOT_SAMPLE_SIZE
        || manifest.sample_seed != PILOT_SAMPLE_SEED
        || manifest.selection_rule != SELECTION_RULE
        || manifest.normalization_policy != NORMALIZATION_POLICY
        || manifest.classification_policy != CLASSIFICATION_POLICY
        || manifest.model_sha256 != GLOTLID_V3_SHA256
        || manifest.model_repository_commit != GLOTLID_V3_REPOSITORY_COMMIT
        || blind.len() != PILOT_SAMPLE_SIZE
    {
        return Err(Error::Invariant(
            "pilot manifest or blind row count is incompatible".to_owned(),
        ));
    }
    let mut ids = BTreeSet::new();
    for (index, record) in blind.iter().enumerate() {
        if record.sample_ordinal as usize != index + 1 || !ids.insert(&record.event_id) {
            return Err(Error::Invariant(
                "blind rows have invalid ordinals or duplicate IDs".to_owned(),
            ));
        }
        if classifier_input(&record.original_content) != record.classifier_input {
            return Err(Error::Invariant(format!(
                "stored classifier input disagrees for event {}",
                record.event_id
            )));
        }
    }
    Ok(())
}

fn parse_manual_label(label: char) -> Result<ManualJudgment, ()> {
    match label.to_ascii_lowercase() {
        'e' => Ok(ManualJudgment::English),
        'z' => Ok(ManualJudgment::LanguageNeutral),
        'n' => Ok(ManualJudgment::PrimarilyNonEnglish),
        'u' => Ok(ManualJudgment::Ambiguous),
        _ => Err(()),
    }
}

fn add_confusion(counts: &mut ConfusionCounts, kept: bool, eligible: Option<bool>) {
    match (kept, eligible) {
        (true, Some(true)) => counts.true_positive += 1,
        (true, Some(false)) => counts.false_positive += 1,
        (false, Some(true)) => counts.false_negative += 1,
        (false, Some(false)) => counts.true_negative += 1,
        (_, None) => counts.ambiguous += 1,
    }
}

fn length_bucket(input: &str) -> &'static str {
    match input.chars().count() {
        0 => "000-empty",
        1..=20 => "001-020",
        21..=50 => "021-050",
        51..=100 => "051-100",
        101..=280 => "101-280",
        _ => "281-plus",
    }
}

fn confidence_bucket(prediction: &PredictionRecord) -> &'static str {
    let Some(confidence) = prediction
        .predictions
        .first()
        .map(|prediction| prediction.confidence)
    else {
        return "empty-input";
    };
    if confidence < 0.50 {
        "0.00-0.49"
    } else if confidence < 0.80 {
        "0.50-0.79"
    } else if confidence < 0.95 {
        "0.80-0.94"
    } else {
        "0.95-1.00"
    }
}

fn binomial(successes: u64, total: u64) -> BinomialMetric {
    if total == 0 {
        return BinomialMetric {
            successes,
            total,
            proportion: None,
            confidence_95_low: None,
            confidence_95_high: None,
        };
    }
    let n = total as f64;
    let proportion = successes as f64 / n;
    let z = 1.959_963_984_540_054_f64;
    let denominator = 1.0 + z * z / n;
    let center = (proportion + z * z / (2.0 * n)) / denominator;
    let radius =
        z * ((proportion * (1.0 - proportion) / n + z * z / (4.0 * n * n)).sqrt()) / denominator;
    BinomialMetric {
        successes,
        total,
        proportion: Some(proportion),
        confidence_95_low: Some((center - radius).max(0.0)),
        confidence_95_high: Some((center + radius).min(1.0)),
    }
}

fn read_json_file<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, Error> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    serde_json::from_reader(BufReader::new(file)).map_err(|source| Error::Json {
        operation: "read",
        path: path.to_owned(),
        source,
    })
}
