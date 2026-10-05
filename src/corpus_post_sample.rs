//! Bounded, read-only export of original events in deterministic sample order.
use crate::{
    english_corpus::{FrozenEnglishClassifier, glotlid_v3_lock},
    io_pressure::IoPressureController,
};
use lmdb::{Cursor, Environment, EnvironmentFlags, Transaction};
use nostrdb::{Note, NoteReply};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BinaryHeap,
    fs,
    io::{BufReader, BufWriter, Read, Write},
    path::{Path, PathBuf},
};

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CorpusPostSampleConfig {
    pub source_corpus_path: PathBuf,
    pub ordered_event_ids_path: PathBuf,
    pub ordered_event_ids_sha256: String,
    pub selection_domain: String,
    pub candidate_rows: usize,
    pub language_model_path: Option<PathBuf>,
}

pub fn export_corpus_post_sample(config: &CorpusPostSampleConfig, output: &Path) -> Result<Value> {
    if output.exists() || config.candidate_rows == 0 || config.selection_domain.is_empty() {
        return Err("output exists or sampling settings are empty".into());
    }
    let controller = IoPressureController::for_current_cgroup()?;
    let result = export(config, output, &controller);
    let shutdown = controller.shutdown();
    let value = result?;
    shutdown?;
    Ok(value)
}

fn export(
    config: &CorpusPostSampleConfig,
    output: &Path,
    controller: &IoPressureController,
) -> Result<Value> {
    let source_data = config.source_corpus_path.join("data.mdb");
    let before = fs::metadata(&source_data)?;
    let file = fs::File::open(&config.ordered_event_ids_path)?;
    let size = file.metadata()?.len();
    if size % 32 != 0 {
        return Err("partial event ID record".into());
    }
    let mut remaining = size;
    let mut input = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut heap = BinaryHeap::with_capacity(config.candidate_rows);
    let mut block = [0u8; 32 * 4096];
    let mut available = 0usize;
    while remaining > 0 {
        let permit = controller.wait_for_read()?;
        let count = remaining.min(block.len() as u64) as usize;
        input.read_exact(&mut block[..count])?;
        remaining -= count as u64;
        permit.complete()?;
        hasher.update(&block[..count]);
        for bytes in block[..count].chunks_exact(32) {
            let id: [u8; 32] = bytes.try_into()?;
            let mut rank = Sha256::new();
            rank.update(config.selection_domain.as_bytes());
            rank.update(id);
            let key: [u8; 32] = rank.finalize().into();
            let item = (key, id);
            if heap.len() < config.candidate_rows {
                heap.push(item);
            } else if heap.peek().is_some_and(|largest| &item < largest) {
                heap.pop();
                heap.push(item);
            }
            available += 1;
        }
    }
    if format!("{:x}", hasher.finalize()) != config.ordered_event_ids_sha256
        || heap.len() != config.candidate_rows
    {
        return Err("source event-ID checksum/count differs".into());
    }
    let mut builder = Environment::new();
    // The source is sealed. NO_LOCK avoids modifying its reader-table file.
    builder
        .set_max_dbs(32)
        .set_map_size(256usize << 30)
        .set_flags(
            EnvironmentFlags::READ_ONLY
                | EnvironmentFlags::NO_READAHEAD
                | EnvironmentFlags::NO_LOCK,
        );
    let db = builder.open(&config.source_corpus_path)?;
    let ids = db.open_db(Some("note_id"))?;
    let notes = db.open_db(Some("note"))?;
    let tx = db.begin_ro_txn()?;
    let classifier = config
        .language_model_path
        .as_ref()
        .map(|p| FrozenEnglishClassifier::load(p, glotlid_v3_lock()))
        .transpose()?;
    let stage = output.with_extension("partial");
    fs::create_dir(&stage)?;
    let mut writer = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(stage.join("candidates.jsonl"))?,
    );
    for (rank, id) in heap.into_sorted_vec() {
        let permit = controller.wait_for_read()?;
        let mut low = [0u8; 40];
        low[..32].copy_from_slice(&id);
        let cursor = tx.open_ro_cursor(ids)?;
        let (found, primary) = cursor.get(Some(&low), None, 17)?;
        let found = found.ok_or("missing stored event key")?;
        if found.len() != 40 || found[..32] != id || primary.len() != 8 {
            return Err("event lookup differs".into());
        }
        let raw = tx.get(notes, &primary)?;
        if raw.len() < 160 || raw[0] != 1 {
            return Err("invalid stored NostrDB note".into());
        }
        // Sealed NostrDB owns the validated note bytes for this read transaction.
        let note = Note::Unowned {
            ptr: unsafe { &*raw.as_ptr().cast() },
        };
        if note.id() != &id {
            return Err("stored event ID differs".into());
        }
        let event: Value =
            serde_json::from_str(&note.json_with_bufsize(raw.len().saturating_mul(4).max(16384))?)?;
        let canonical = serde_json::to_vec(&json!([
            0,
            event["pubkey"],
            event["created_at"],
            event["kind"],
            event["tags"],
            event["content"]
        ]))?;
        if hex(&id) != format!("{:x}", Sha256::digest(canonical)) {
            return Err("canonical event hash differs".into());
        }
        let relation = NoteReply::new(note.tags());
        let address_reply = note.tags().into_iter().any(|tag| {
            tag.get_str(0) == Some("a") && matches!(tag.get_str(3), Some("root" | "reply"))
        });
        let quote = note
            .tags()
            .into_iter()
            .any(|tag| tag.get_str(0) == Some("q"));
        let row = json!({"note_id":hex(&id),"pubkey":hex(note.pubkey()),"text":note.content(),
            "event":event,"selection_order_sha256":hex(&rank),
            "root_non_quote":note.kind()==1 && !relation.is_reply() && relation.mention().is_none() && !address_reply && !quote,
            "language_decision":classifier.as_ref().map(|c|c.classify_content(note.content())),
            "canonical_event_id_verified":true});
        serde_json::to_writer(&mut writer, &row)?;
        writer.write_all(b"\n")?;
        permit.complete()?;
    }
    writer.flush()?;
    writer.get_ref().sync_all()?;
    let after = fs::metadata(&source_data)?;
    if before.len() != after.len() || before.modified()? != after.modified()? {
        return Err("source changed during export".into());
    }
    let manifest = json!({"schema_version":1,"config":config,"available_ids":available,
        "candidate_rows":config.candidate_rows,"candidates_sha256":crate::artifact::hash_file(&stage.join("candidates.jsonl"))?,
        "source_data_bytes":before.len(),"source_access":"read-only-no-lock",
        "pressure_control":"current-cgroup-io-pressure-v1","canonical_event_ids_verified":true});
    fs::write(
        stage.join("manifest.json"),
        serde_json::to_vec_pretty(&manifest)?,
    )?;
    fs::rename(stage, output)?;
    Ok(manifest)
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
