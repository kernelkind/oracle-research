use nostrdb::{Config, Ndb};
use oracle_mvp::corpus_derivation::derive_corpus;
use std::env;
use std::fs;
use std::path::Path;
use std::thread;
use std::time::Duration;

const DRAIN_DELAY: Duration = Duration::from_secs(60);

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let source_path = args
        .next()
        .ok_or("usage: stage2_corpus SOURCE_NDB_PATH CORPUS_NDB_PATH")?;
    let corpus_path = args
        .next()
        .ok_or("usage: stage2_corpus SOURCE_NDB_PATH CORPUS_NDB_PATH")?;
    if args.next().is_some() {
        return Err("usage: stage2_corpus SOURCE_NDB_PATH CORPUS_NDB_PATH".into());
    }
    if source_path == corpus_path {
        return Err("source and corpus NostrDB paths must differ".into());
    }

    let source_path = Path::new(&source_path);
    let corpus_path = Path::new(&corpus_path);
    if !source_path.is_dir() {
        return Err(format!("source NostrDB does not exist: {}", source_path.display()).into());
    }
    if let Some(parent) = corpus_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let source_path = source_path
        .to_str()
        .ok_or("source NostrDB path is not valid UTF-8")?;
    let corpus_path = corpus_path
        .to_str()
        .ok_or("corpus NostrDB path is not valid UTF-8")?;
    let no_fulltext = 1 << 2;
    let no_note_blocks = 1 << 3;
    let no_stats = 1 << 4;
    let source_config = Config::new()
        .set_flags(no_fulltext | no_note_blocks | no_stats)
        .set_mapsize(256 * 1024 * 1024 * 1024);
    let corpus_config = source_config.skip_validation(true).set_ingester_threads(1);
    let source = Ndb::new(source_path, &source_config)?;
    let corpus = Ndb::new(corpus_path, &corpus_config)?;

    derive_corpus(&source, &corpus)?;
    thread::sleep(DRAIN_DELAY);
    drop(corpus);
    drop(source);
    Ok(())
}
