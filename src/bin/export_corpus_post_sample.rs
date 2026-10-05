use oracle_mvp::corpus_post_sample::{CorpusPostSampleConfig, export_corpus_post_sample};
use std::{env, fs, path::Path};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 2 {
        return Err("usage: export-corpus-post-sample CONFIG.json OUTPUT".into());
    }
    let config: CorpusPostSampleConfig = serde_json::from_slice(&fs::read(&args[0])?)?;
    println!(
        "{}",
        export_corpus_post_sample(&config, Path::new(&args[1]))?
    );
    Ok(())
}
