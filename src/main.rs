//! Command-line entrypoint for the recommendation oracle MVP.

use std::env;
use std::ffi::OsString;
use std::io::{self, Write};
use std::path::PathBuf;
use std::process::ExitCode;

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
            print_json(&BuildResult { source, corpus })
        }
    }
}

#[derive(Debug)]
enum Command {
    ImportSource { root: PathBuf },
    DeriveCorpus { root: PathBuf },
    Build { root: PathBuf },
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
        ensure_finished(args)?;

        match command {
            "import-source" => Ok(Some(Self::ImportSource { root })),
            "derive-corpus" => Ok(Some(Self::DeriveCorpus { root })),
            "build" => Ok(Some(Self::Build { root })),
            _ => Err(format!("unknown command `{command}`\n\n{}", usage())),
        }
    }
}

#[derive(Serialize)]
struct BuildResult {
    source: oracle_mvp::snapshot::SourceManifest,
    corpus: oracle_mvp::snapshot::CorpusManifest,
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
    "Usage:\n  oracle-mvp import-source DATA_ROOT\n  oracle-mvp derive-corpus DATA_ROOT\n  oracle-mvp build DATA_ROOT"
}
