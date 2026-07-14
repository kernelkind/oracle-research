use std::env;
use std::io::{self, Write};

use oracle_mvp::corpus_dedup::build_deduplicated_corpus;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let filtered_path = args
        .next()
        .ok_or("usage: stage4_deduplicate FILTERED_NDB_PATH OUTPUT_DIRECTORY")?;
    let output_path = args
        .next()
        .ok_or("usage: stage4_deduplicate FILTERED_NDB_PATH OUTPUT_DIRECTORY")?;
    if args.next().is_some() {
        return Err("usage: stage4_deduplicate FILTERED_NDB_PATH OUTPUT_DIRECTORY".into());
    }

    let summary = build_deduplicated_corpus(filtered_path, output_path)?;
    serde_json::to_writer(io::stdout().lock(), &summary)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}
