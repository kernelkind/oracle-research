use std::env;
use std::io::{self, Write};
use std::path::Path;

use oracle_mvp::ordered_embedding::{OrderedEmbeddingBuildConfig, build_ordered_embeddings};
use oracle_mvp::pplx::{ExecutionProvider, PplxOnnxConfig, PplxOnnxEncoder};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let deduplicated = args.next().ok_or(usage())?;
    let output = args.next().ok_or(usage())?;
    let rows = parse_u64(args.next(), "ROWS")?;
    let model_dir = args.next().ok_or(usage())?;
    let runtime_library = args.next().ok_or(usage())?;
    let batch_size = parse_usize(args.next(), "BATCH_SIZE")?;
    let shard_rows = parse_u64(args.next(), "SHARD_ROWS")?;
    if args.next().is_some() {
        return Err(usage().into());
    }

    let deduplicated = Path::new(&deduplicated);
    let mut encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
        model_dir: model_dir.into(),
        runtime_library: runtime_library.into(),
        execution_provider: ExecutionProvider::Cpu,
    })?;
    let result = build_ordered_embeddings(
        deduplicated.join("ndb"),
        deduplicated.join("ordered-event-ids.bin"),
        output,
        &OrderedEmbeddingBuildConfig {
            rows,
            batch_size,
            shard_rows,
        },
        &mut encoder,
    )?;
    serde_json::to_writer_pretty(io::stdout().lock(), &result)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}

fn parse_u64(value: Option<std::ffi::OsString>, name: &str) -> Result<u64, String> {
    let value = value.ok_or_else(usage)?;
    let value = value
        .to_str()
        .ok_or_else(|| format!("{name} is not valid UTF-8\n\n{}", usage()))?;
    value
        .parse::<u64>()
        .ok()
        .filter(|value| *value > 0)
        .ok_or_else(|| format!("{name} must be a positive integer\n\n{}", usage()))
}

fn parse_usize(value: Option<std::ffi::OsString>, name: &str) -> Result<usize, String> {
    let value = parse_u64(value, name)?;
    usize::try_from(value).map_err(|_| format!("{name} does not fit usize"))
}

fn usage() -> String {
    "usage: stage5_embed_prefix DEDUPLICATED_DIRECTORY OUTPUT_DIRECTORY ROWS MODEL_DIRECTORY ONNX_RUNTIME BATCH_SIZE SHARD_ROWS".to_owned()
}
