use std::env;
use std::io::{self, Write};

use oracle_mvp::english_corpus::{FrozenEnglishClassifier, build_english_corpus, glotlid_v3_lock};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let deduplicated = args.next().ok_or_else(usage)?;
    let output = args.next().ok_or_else(usage)?;
    let model = args.next().ok_or_else(usage)?;
    if args.next().is_some() {
        return Err(usage().into());
    }

    let classifier = FrozenEnglishClassifier::load(model, glotlid_v3_lock())?;
    let manifest = build_english_corpus(deduplicated, output, &classifier)?;
    serde_json::to_writer_pretty(io::stdout().lock(), &manifest)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}

fn usage() -> String {
    "usage: stage6_english_filter DEDUPLICATED_DIRECTORY OUTPUT_DIRECTORY GLOTLID_V3_MODEL"
        .to_owned()
}
