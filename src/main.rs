//! Command-line entrypoint for the recommendation oracle MVP.

use std::env;
use std::ffi::OsString;
use std::io::{self, Write};
use std::path::PathBuf;
use std::process::ExitCode;

use oracle_mvp::embedding::EmbeddingBuildConfig;
use oracle_mvp::pplx::{
    ExecutionProvider, PREFLIGHT_ARTIFACT_NAME, PplxOnnxConfig, PplxOnnxEncoder,
};
use oracle_mvp::snapshot::DamusSnapshot;
use serde::Serialize;

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let Some(command) = Command::parse(env::args_os().skip(1))? else {
        print_usage();
        return Ok(());
    };

    match command {
        Command::ImportSource { root } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "importing {}",
                pipeline.layout().snapshot().as_path().display()
            );
            let manifest = pipeline
                .import_source()
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::DeriveCorpus { root } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "deriving {}",
                pipeline.layout().corpus_db().as_path().display()
            );
            let manifest = pipeline
                .derive_corpus()
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::CanonicalizeCorpus { root } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "canonicalizing {}",
                pipeline.layout().corpus_db().as_path().display()
            );
            let manifest = pipeline
                .canonicalize_corpus()
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::EmbedCorpus {
            root,
            model_dir,
            runtime_library,
            execution_provider,
            batch_size,
            shard_rows,
        } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "verifying model and embedding {}",
                pipeline.layout().canonical_rows().display()
            );
            let mut encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
                model_dir,
                runtime_library,
                execution_provider,
            })
            .map_err(|error| error.to_string())?;
            let manifest = pipeline
                .embed_canonical_corpus(
                    &EmbeddingBuildConfig {
                        artifact_name: PREFLIGHT_ARTIFACT_NAME.to_owned(),
                        batch_size,
                        shard_rows,
                    },
                    &mut encoder,
                )
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::Build { root } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "importing {}",
                pipeline.layout().snapshot().as_path().display()
            );
            let source = pipeline
                .import_source()
                .map_err(|error| error.to_string())?;
            eprintln!(
                "deriving {}",
                pipeline.layout().corpus_db().as_path().display()
            );
            let corpus = pipeline
                .derive_corpus()
                .map_err(|error| error.to_string())?;
            eprintln!(
                "canonicalizing {}",
                pipeline.layout().corpus_db().as_path().display()
            );
            let canonical = pipeline
                .canonicalize_corpus()
                .map_err(|error| error.to_string())?;
            print_json(&BuildResult {
                source,
                corpus,
                canonical,
            })
        }
    }
}

#[derive(Debug)]
enum Command {
    ImportSource {
        root: PathBuf,
    },
    DeriveCorpus {
        root: PathBuf,
    },
    CanonicalizeCorpus {
        root: PathBuf,
    },
    EmbedCorpus {
        root: PathBuf,
        model_dir: PathBuf,
        runtime_library: PathBuf,
        execution_provider: ExecutionProvider,
        batch_size: usize,
        shard_rows: u64,
    },
    Build {
        root: PathBuf,
    },
}

impl Command {
    fn parse(mut args: impl Iterator<Item = OsString>) -> Result<Option<Self>, String> {
        let Some(command) = args.next() else {
            return Ok(None);
        };
        if command == "--help" || command == "-h" {
            ensure_finished(args)?;
            return Ok(None);
        }
        let command = command
            .to_str()
            .ok_or_else(|| "command is not valid UTF-8".to_owned())?;
        let root = args
            .next()
            .map(PathBuf::from)
            .ok_or_else(|| format!("{command} requires DATA_ROOT\n\n{}", usage()))?;

        match command {
            "import-source" => {
                ensure_finished(args)?;
                Ok(Some(Self::ImportSource { root }))
            }
            "derive-corpus" => {
                ensure_finished(args)?;
                Ok(Some(Self::DeriveCorpus { root }))
            }
            "canonicalize-corpus" => {
                ensure_finished(args)?;
                Ok(Some(Self::CanonicalizeCorpus { root }))
            }
            "embed-corpus" => {
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let runtime_library = required_path(&mut args, command, "ONNX_RUNTIME")?;
                let provider = required_utf8(&mut args, command, "PROVIDER")?;
                let execution_provider = match provider.as_str() {
                    "cpu" => ExecutionProvider::Cpu,
                    "cuda" => ExecutionProvider::Cuda,
                    _ => {
                        return Err(format!(
                            "embed-corpus PROVIDER must be `cpu` or `cuda`, not `{provider}`\n\n{}",
                            usage()
                        ));
                    }
                };
                let batch_size = required_utf8(&mut args, command, "BATCH_SIZE")?
                    .parse::<usize>()
                    .map_err(|_| {
                        format!(
                            "embed-corpus BATCH_SIZE must be a positive integer\n\n{}",
                            usage()
                        )
                    })?;
                if batch_size == 0 {
                    return Err(format!(
                        "embed-corpus BATCH_SIZE must be a positive integer\n\n{}",
                        usage()
                    ));
                }
                let shard_rows = match args.next() {
                    Some(value) => value
                        .to_str()
                        .ok_or_else(|| "SHARD_ROWS is not valid UTF-8".to_owned())?
                        .parse::<u64>()
                        .map_err(|_| {
                            format!(
                                "embed-corpus SHARD_ROWS must be a positive integer\n\n{}",
                                usage()
                            )
                        })?,
                    None => 100_000,
                };
                if shard_rows == 0 {
                    return Err(format!(
                        "embed-corpus SHARD_ROWS must be a positive integer\n\n{}",
                        usage()
                    ));
                }
                ensure_finished(args)?;
                Ok(Some(Self::EmbedCorpus {
                    root,
                    model_dir,
                    runtime_library,
                    execution_provider,
                    batch_size,
                    shard_rows,
                }))
            }
            "build" => {
                ensure_finished(args)?;
                Ok(Some(Self::Build { root }))
            }
            _ => Err(format!("unknown command `{command}`\n\n{}", usage())),
        }
    }
}

fn required_path(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
    name: &str,
) -> Result<PathBuf, String> {
    args.next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("{command} requires {name}\n\n{}", usage()))
}

fn required_utf8(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
    name: &str,
) -> Result<String, String> {
    let value = args
        .next()
        .ok_or_else(|| format!("{command} requires {name}\n\n{}", usage()))?;
    value
        .into_string()
        .map_err(|_| format!("{name} is not valid UTF-8\n\n{}", usage()))
}

#[derive(Serialize)]
struct BuildResult {
    source: oracle_mvp::snapshot::SourceManifest,
    corpus: oracle_mvp::snapshot::CorpusManifest,
    canonical: oracle_mvp::snapshot::CanonicalManifest,
}

fn ensure_finished(mut args: impl Iterator<Item = OsString>) -> Result<(), String> {
    match args.next() {
        Some(argument) => Err(format!(
            "unexpected argument `{}`\n\n{}",
            argument.to_string_lossy(),
            usage()
        )),
        None => Ok(()),
    }
}

fn print_json(value: &impl Serialize) -> Result<(), String> {
    let stdout = io::stdout();
    let mut output = stdout.lock();
    serde_json::to_writer_pretty(&mut output, value).map_err(|error| error.to_string())?;
    writeln!(output).map_err(|error| error.to_string())
}

fn print_usage() {
    println!("{}", usage());
}

fn usage() -> &'static str {
    "Usage:\n  oracle-mvp import-source DATA_ROOT\n  oracle-mvp derive-corpus DATA_ROOT\n  oracle-mvp canonicalize-corpus DATA_ROOT\n  oracle-mvp embed-corpus DATA_ROOT MODEL_DIR ONNX_RUNTIME PROVIDER BATCH_SIZE [SHARD_ROWS]\n  oracle-mvp build DATA_ROOT"
}
