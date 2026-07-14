use std::env;
use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::thread;
use std::time::Duration;

use nostrdb::{Config, Ndb};
use oracle_mvp::corpus_filter::{
    FrozenTokenizer, filter_corpus, gte_tokenizer_lock, pplx_tokenizer_lock,
};

const DRAIN_DELAY: Duration = Duration::from_secs(60);

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let source_path = args.next().ok_or(
        "usage: stage3_filter CORPUS_NDB_PATH FILTERED_NDB_PATH PPLX_TOKENIZER_DIR GTE_TOKENIZER_DIR",
    )?;
    let filtered_path = args.next().ok_or(
        "usage: stage3_filter CORPUS_NDB_PATH FILTERED_NDB_PATH PPLX_TOKENIZER_DIR GTE_TOKENIZER_DIR",
    )?;
    let pplx_tokenizer_dir = args.next().ok_or(
        "usage: stage3_filter CORPUS_NDB_PATH FILTERED_NDB_PATH PPLX_TOKENIZER_DIR GTE_TOKENIZER_DIR",
    )?;
    let gte_tokenizer_dir = args.next().ok_or(
        "usage: stage3_filter CORPUS_NDB_PATH FILTERED_NDB_PATH PPLX_TOKENIZER_DIR GTE_TOKENIZER_DIR",
    )?;
    if args.next().is_some() {
        return Err(
            "usage: stage3_filter CORPUS_NDB_PATH FILTERED_NDB_PATH PPLX_TOKENIZER_DIR GTE_TOKENIZER_DIR"
                .into(),
        );
    }
    if source_path == filtered_path {
        return Err("source and filtered NostrDB paths must differ".into());
    }

    let source_path = Path::new(&source_path);
    let filtered_path = Path::new(&filtered_path);
    if !source_path.is_dir() {
        return Err(format!("source NostrDB does not exist: {}", source_path.display()).into());
    }
    if filtered_path.exists() && fs::canonicalize(source_path)? == fs::canonicalize(filtered_path)?
    {
        return Err("source and filtered NostrDB paths must differ".into());
    }
    if let Some(parent) = filtered_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let mut pplx = FrozenTokenizer::load(pplx_tokenizer_dir, pplx_tokenizer_lock()?)?;
    let mut gte = FrozenTokenizer::load(gte_tokenizer_dir, gte_tokenizer_lock()?)?;
    let source_path = source_path
        .to_str()
        .ok_or("source NostrDB path is not valid UTF-8")?;
    let filtered_path = filtered_path
        .to_str()
        .ok_or("filtered NostrDB path is not valid UTF-8")?;
    let no_fulltext = 1 << 2;
    let no_note_blocks = 1 << 3;
    let no_stats = 1 << 4;
    let source_config = Config::new()
        .set_flags(no_fulltext | no_note_blocks | no_stats)
        .set_mapsize(256 * 1_024 * 1_024 * 1_024);
    let filtered_config = source_config.skip_validation(true).set_ingester_threads(1);
    let source = Ndb::new(source_path, &source_config)?;
    let filtered = Ndb::new(filtered_path, &filtered_config)?;

    let summary = filter_corpus(&source, &filtered, &mut pplx, &mut gte)?;
    thread::sleep(DRAIN_DELAY);
    drop(filtered);
    drop(source);
    serde_json::to_writer(io::stdout().lock(), &summary)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}
