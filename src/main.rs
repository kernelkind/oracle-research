//! Command-line entrypoint for the recommendation oracle MVP.

use std::env;
use std::ffi::OsString;
use std::fs::File;
use std::io::{self, Write};
use std::path::PathBuf;
use std::process::ExitCode;

use oracle_mvp::benchmark::BenchmarkStageConfig;
use oracle_mvp::budget::{AdmittedExecutionConfig, BudgetAdmissionConfig};
use oracle_mvp::embedding::EmbeddingBuildConfig;
use oracle_mvp::pplx::{
    ExecutionProvider, PREFLIGHT_ARTIFACT_NAME, PplxOnnxConfig, PplxOnnxEncoder,
    PplxTokenLengthCounter,
};
use oracle_mvp::preflight::PreflightConfig;
use oracle_mvp::snapshot::DamusSnapshot;
use oracle_mvp::stage::CorpusStageConfig;
use oracle_mvp::token_audit::TokenAuditConfig;
use serde::{Serialize, de::DeserializeOwned};

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
        Command::AuditTokenLengths {
            root,
            artifact_name,
            model_dir,
            shard_rows,
        } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!(
                "auditing raw token lengths for {}",
                pipeline.layout().canonical_rows().display()
            );
            let mut counter =
                PplxTokenLengthCounter::load(model_dir).map_err(|error| error.to_string())?;
            let manifest = pipeline
                .audit_canonical_token_lengths(
                    &TokenAuditConfig {
                        artifact_name,
                        shard_rows,
                    },
                    &mut counter,
                )
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::AuditStageTokenLengths {
            root,
            stage_name,
            artifact_name,
            model_dir,
            shard_rows,
        } => {
            let pipeline = DamusSnapshot::new(root);
            let mut counter =
                PplxTokenLengthCounter::load(model_dir).map_err(|error| error.to_string())?;
            let manifest = pipeline
                .audit_corpus_stage_token_lengths(
                    &stage_name,
                    &TokenAuditConfig {
                        artifact_name,
                        shard_rows,
                    },
                    &mut counter,
                )
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
            require_unadmitted_cpu(execution_provider, "embed-corpus")?;
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
        Command::MaterializeStage {
            root,
            stage_name,
            rows,
        } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!("materializing corpus stage {stage_name} with {rows} rows");
            let manifest = pipeline
                .materialize_corpus_stage(&CorpusStageConfig {
                    name: stage_name,
                    rows,
                })
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::BenchmarkStage {
            root,
            config_path,
            model_dir,
            runtime_library,
        } => {
            let config: BenchmarkStageConfig = read_json(&config_path)?;
            let pipeline = DamusSnapshot::new(root);
            let mut encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
                model_dir,
                runtime_library,
                execution_provider: ExecutionProvider::Cuda,
            })
            .map_err(|error| error.to_string())?;
            let manifest = pipeline
                .benchmark_corpus_stage(&config, &mut encoder)
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::PlanAdmission {
            root,
            name,
            config_path,
        } => {
            let config: BudgetAdmissionConfig = read_json(&config_path)?;
            let pipeline = DamusSnapshot::new(root);
            let admission = pipeline
                .plan_and_publish_budget_admission(&name, &config)
                .map_err(|error| error.to_string())?;
            print_json(&admission)
        }
        Command::ExecuteAdmission {
            root,
            name,
            execution_path,
            model_dir,
            runtime_library,
        } => {
            let execution: AdmittedExecutionConfig = read_json(&execution_path)?;
            let pipeline = DamusSnapshot::new(root);
            let mut encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
                model_dir,
                runtime_library,
                execution_provider: ExecutionProvider::Cuda,
            })
            .map_err(|error| error.to_string())?;
            let manifest = pipeline
                .execute_budget_admission(&name, &execution, &mut encoder)
                .map_err(|error| error.to_string())?;
            print_json(&manifest)
        }
        Command::EmbedStage {
            root,
            stage_name,
            model_dir,
            runtime_library,
            execution_provider,
            batch_size,
            shard_rows,
        } => {
            require_unadmitted_cpu(execution_provider, "embed-stage")?;
            let pipeline = DamusSnapshot::new(root);
            eprintln!("embedding corpus stage {stage_name}");
            let mut encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
                model_dir,
                runtime_library,
                execution_provider,
            })
            .map_err(|error| error.to_string())?;
            let manifest = pipeline
                .embed_corpus_stage(
                    &stage_name,
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
        Command::ExecutePreflight {
            root,
            name,
            stage_name,
            expected_rows,
            model_dir,
            runtime_library,
            execution_provider,
            candidate_depth,
            topic,
        } => {
            let pipeline = DamusSnapshot::new(root);
            eprintln!("executing preflight {name}");
            let encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
                model_dir,
                runtime_library,
                execution_provider,
            })
            .map_err(|error| error.to_string())?;
            let manifest = pipeline
                .execute_preflight(
                    &PreflightConfig {
                        name,
                        stage_name,
                        embedding_artifact: PREFLIGHT_ARTIFACT_NAME.to_owned(),
                        expected_rows,
                        topic,
                        candidate_depth,
                    },
                    encoder,
                )
                .map_err(|error| error.to_string())?;
            print_json(&manifest)?;
            if manifest.failures.is_empty() {
                Ok(())
            } else {
                Err(format!(
                    "preflight recorded {} failed correctness checks",
                    manifest.failures.len()
                ))
            }
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
    AuditTokenLengths {
        root: PathBuf,
        artifact_name: String,
        model_dir: PathBuf,
        shard_rows: u64,
    },
    AuditStageTokenLengths {
        root: PathBuf,
        stage_name: String,
        artifact_name: String,
        model_dir: PathBuf,
        shard_rows: u64,
    },
    EmbedCorpus {
        root: PathBuf,
        model_dir: PathBuf,
        runtime_library: PathBuf,
        execution_provider: ExecutionProvider,
        batch_size: usize,
        shard_rows: u64,
    },
    MaterializeStage {
        root: PathBuf,
        stage_name: String,
        rows: u64,
    },
    EmbedStage {
        root: PathBuf,
        stage_name: String,
        model_dir: PathBuf,
        runtime_library: PathBuf,
        execution_provider: ExecutionProvider,
        batch_size: usize,
        shard_rows: u64,
    },
    BenchmarkStage {
        root: PathBuf,
        config_path: PathBuf,
        model_dir: PathBuf,
        runtime_library: PathBuf,
    },
    PlanAdmission {
        root: PathBuf,
        name: String,
        config_path: PathBuf,
    },
    ExecuteAdmission {
        root: PathBuf,
        name: String,
        execution_path: PathBuf,
        model_dir: PathBuf,
        runtime_library: PathBuf,
    },
    ExecutePreflight {
        root: PathBuf,
        name: String,
        stage_name: String,
        expected_rows: u64,
        model_dir: PathBuf,
        runtime_library: PathBuf,
        execution_provider: ExecutionProvider,
        candidate_depth: usize,
        topic: String,
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
            "audit-token-lengths" => {
                let artifact_name = required_utf8(&mut args, command, "AUDIT_NAME")?;
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let shard_rows = match args.next() {
                    Some(value) => parse_positive_u64(value, command, "SHARD_ROWS")?,
                    None => 100_000,
                };
                ensure_finished(args)?;
                Ok(Some(Self::AuditTokenLengths {
                    root,
                    artifact_name,
                    model_dir,
                    shard_rows,
                }))
            }
            "audit-stage-token-lengths" => {
                let stage_name = required_utf8(&mut args, command, "STAGE_NAME")?;
                let artifact_name = required_utf8(&mut args, command, "AUDIT_NAME")?;
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let shard_rows = match args.next() {
                    Some(value) => parse_positive_u64(value, command, "SHARD_ROWS")?,
                    None => 100_000,
                };
                ensure_finished(args)?;
                Ok(Some(Self::AuditStageTokenLengths {
                    root,
                    stage_name,
                    artifact_name,
                    model_dir,
                    shard_rows,
                }))
            }
            "embed-corpus" => {
                let embedding = required_embedding_args(&mut args, command)?;
                Ok(Some(Self::EmbedCorpus {
                    root,
                    model_dir: embedding.model_dir,
                    runtime_library: embedding.runtime_library,
                    execution_provider: embedding.execution_provider,
                    batch_size: embedding.batch_size,
                    shard_rows: embedding.shard_rows,
                }))
            }
            "materialize-stage" => {
                let stage_name = required_utf8(&mut args, command, "STAGE_NAME")?;
                let rows = required_positive_u64(&mut args, command, "ROWS")?;
                ensure_finished(args)?;
                Ok(Some(Self::MaterializeStage {
                    root,
                    stage_name,
                    rows,
                }))
            }
            "embed-stage" => {
                let stage_name = required_utf8(&mut args, command, "STAGE_NAME")?;
                let embedding = required_embedding_args(&mut args, command)?;
                Ok(Some(Self::EmbedStage {
                    root,
                    stage_name,
                    model_dir: embedding.model_dir,
                    runtime_library: embedding.runtime_library,
                    execution_provider: embedding.execution_provider,
                    batch_size: embedding.batch_size,
                    shard_rows: embedding.shard_rows,
                }))
            }
            "benchmark-stage" => {
                let config_path = required_path(&mut args, command, "CONFIG_JSON")?;
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let runtime_library = required_path(&mut args, command, "ONNX_RUNTIME")?;
                ensure_finished(args)?;
                Ok(Some(Self::BenchmarkStage {
                    root,
                    config_path,
                    model_dir,
                    runtime_library,
                }))
            }
            "plan-admission" => {
                let name = required_utf8(&mut args, command, "ADMISSION_NAME")?;
                let config_path = required_path(&mut args, command, "CONFIG_JSON")?;
                ensure_finished(args)?;
                Ok(Some(Self::PlanAdmission {
                    root,
                    name,
                    config_path,
                }))
            }
            "execute-admission" => {
                let name = required_utf8(&mut args, command, "ADMISSION_NAME")?;
                let execution_path = required_path(&mut args, command, "EXECUTION_JSON")?;
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let runtime_library = required_path(&mut args, command, "ONNX_RUNTIME")?;
                ensure_finished(args)?;
                Ok(Some(Self::ExecuteAdmission {
                    root,
                    name,
                    execution_path,
                    model_dir,
                    runtime_library,
                }))
            }
            "execute-preflight" => {
                let name = required_utf8(&mut args, command, "RECORD_NAME")?;
                let stage_name = required_utf8(&mut args, command, "STAGE_NAME")?;
                let expected_rows = required_positive_u64(&mut args, command, "EXPECTED_ROWS")?;
                let model_dir = required_path(&mut args, command, "MODEL_DIR")?;
                let runtime_library = required_path(&mut args, command, "ONNX_RUNTIME")?;
                let execution_provider = required_execution_provider(&mut args, command)?;
                let candidate_depth =
                    required_positive_usize(&mut args, command, "CANDIDATE_DEPTH")?;
                let topic = required_utf8(&mut args, command, "TOPIC")?;
                ensure_finished(args)?;
                Ok(Some(Self::ExecutePreflight {
                    root,
                    name,
                    stage_name,
                    expected_rows,
                    model_dir,
                    runtime_library,
                    execution_provider,
                    candidate_depth,
                    topic,
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

struct EmbeddingArgs {
    model_dir: PathBuf,
    runtime_library: PathBuf,
    execution_provider: ExecutionProvider,
    batch_size: usize,
    shard_rows: u64,
}

fn required_embedding_args(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
) -> Result<EmbeddingArgs, String> {
    let model_dir = required_path(args, command, "MODEL_DIR")?;
    let runtime_library = required_path(args, command, "ONNX_RUNTIME")?;
    let execution_provider = required_execution_provider(args, command)?;
    let batch_size = required_positive_usize(args, command, "BATCH_SIZE")?;
    let shard_rows = match args.next() {
        Some(value) => parse_positive_u64(value, command, "SHARD_ROWS")?,
        None => 100_000,
    };
    ensure_finished(args)?;
    Ok(EmbeddingArgs {
        model_dir,
        runtime_library,
        execution_provider,
        batch_size,
        shard_rows,
    })
}

fn required_execution_provider(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
) -> Result<ExecutionProvider, String> {
    let provider = required_utf8(args, command, "PROVIDER")?;
    match provider.as_str() {
        "cpu" => Ok(ExecutionProvider::Cpu),
        "cuda" => Ok(ExecutionProvider::Cuda),
        _ => Err(format!(
            "{command} PROVIDER must be `cpu` or `cuda`, not `{provider}`\n\n{}",
            usage()
        )),
    }
}

fn require_unadmitted_cpu(
    execution_provider: ExecutionProvider,
    command: &str,
) -> Result<(), String> {
    if execution_provider == ExecutionProvider::Cuda {
        Err(format!(
            "{command} refuses unadmitted CUDA work; use benchmark-stage or execute-admission"
        ))
    } else {
        Ok(())
    }
}

fn read_json<T: DeserializeOwned>(path: &std::path::Path) -> Result<T, String> {
    let file = File::open(path)
        .map_err(|error| format!("failed to open `{}`: {error}", path.display()))?;
    serde_json::from_reader(file)
        .map_err(|error| format!("failed to decode `{}`: {error}", path.display()))
}

fn required_positive_usize(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
    name: &str,
) -> Result<usize, String> {
    let value = required_utf8(args, command, name)?;
    let parsed = value
        .parse::<usize>()
        .map_err(|_| format!("{command} {name} must be a positive integer\n\n{}", usage()))?;
    if parsed == 0 {
        Err(format!(
            "{command} {name} must be a positive integer\n\n{}",
            usage()
        ))
    } else {
        Ok(parsed)
    }
}

fn required_positive_u64(
    args: &mut impl Iterator<Item = OsString>,
    command: &str,
    name: &str,
) -> Result<u64, String> {
    let value = args
        .next()
        .ok_or_else(|| format!("{command} requires {name}\n\n{}", usage()))?;
    parse_positive_u64(value, command, name)
}

fn parse_positive_u64(value: OsString, command: &str, name: &str) -> Result<u64, String> {
    let parsed = value
        .to_str()
        .ok_or_else(|| format!("{name} is not valid UTF-8\n\n{}", usage()))?
        .parse::<u64>()
        .map_err(|_| format!("{command} {name} must be a positive integer\n\n{}", usage()))?;
    if parsed == 0 {
        Err(format!(
            "{command} {name} must be a positive integer\n\n{}",
            usage()
        ))
    } else {
        Ok(parsed)
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
    "Usage:\n  oracle-mvp import-source DATA_ROOT\n  oracle-mvp derive-corpus DATA_ROOT\n  oracle-mvp canonicalize-corpus DATA_ROOT\n  oracle-mvp audit-token-lengths DATA_ROOT AUDIT_NAME MODEL_DIR [SHARD_ROWS]\n  oracle-mvp audit-stage-token-lengths DATA_ROOT STAGE_NAME AUDIT_NAME MODEL_DIR [SHARD_ROWS]\n  oracle-mvp embed-corpus DATA_ROOT MODEL_DIR ONNX_RUNTIME PROVIDER BATCH_SIZE [SHARD_ROWS]\n  oracle-mvp materialize-stage DATA_ROOT STAGE_NAME ROWS\n  oracle-mvp embed-stage DATA_ROOT STAGE_NAME MODEL_DIR ONNX_RUNTIME PROVIDER BATCH_SIZE [SHARD_ROWS]\n  oracle-mvp benchmark-stage DATA_ROOT CONFIG_JSON MODEL_DIR ONNX_RUNTIME\n  oracle-mvp plan-admission DATA_ROOT ADMISSION_NAME CONFIG_JSON\n  oracle-mvp execute-admission DATA_ROOT ADMISSION_NAME EXECUTION_JSON MODEL_DIR ONNX_RUNTIME\n  oracle-mvp execute-preflight DATA_ROOT RECORD_NAME STAGE_NAME EXPECTED_ROWS MODEL_DIR ONNX_RUNTIME PROVIDER CANDIDATE_DEPTH TOPIC\n  oracle-mvp build DATA_ROOT"
}
