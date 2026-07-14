use std::io;
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::manual_workflow::{ManualWorkflowConfig, run_manual_workflow};
use oracle_mvp::pplx::{ExecutionProvider, PplxOnnxConfig, PplxOnnxEncoder};

const RUN_DIRECTORY: &str = "crec-9-complete-cpu-audit-v6";
const MODEL_REVISION: &str = "2c4d510dd4a732063c31a0f70193e35067b51fd8";
const EMBEDDING_ARTIFACT: &str = "pplx-embed-v1-0.6b-int8-1024d-final-10k-v1";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let repository = Path::new(env!("CARGO_MANIFEST_DIR"));
    let workspace = repository
        .parent()
        .ok_or("oracle-mvp repository has no workspace parent")?;
    let snapshot = workspace.join("damus_snapshot");
    let work = snapshot.join("runs").join(RUN_DIRECTORY).join("work");
    let deduplicated = work.join("deduplicated");
    let config = ManualWorkflowConfig {
        corpus_path: deduplicated.join("ndb"),
        ordered_event_ids_path: deduplicated.join("ordered-event-ids.bin"),
        embedding_artifact_path: work.join("embeddings").join(EMBEDDING_ARTIFACT),
        session_path: work.join("manual-workflow").join("crec-43-session.json"),
        onboarding_depth: 20,
        neighbor_depth: 50,
        recommendation_limit: 20,
    };
    let encoder = PplxOnnxEncoder::load(PplxOnnxConfig {
        model_dir: snapshot
            .join("models")
            .join("perplexity-ai")
            .join("pplx-embed-v1-0.6b")
            .join(MODEL_REVISION),
        runtime_library: snapshot
            .join("runtimes")
            .join("onnxruntime")
            .join("1.24.4")
            .join("cpu-linux-x64")
            .join("lib")
            .join("libonnxruntime.so.1.24.4"),
        execution_provider: ExecutionProvider::Cpu,
    })?;
    let stdin = io::stdin();
    let stdout = io::stdout();
    run_manual_workflow(&config, encoder, stdin.lock(), &mut stdout.lock())?;
    Ok(())
}
