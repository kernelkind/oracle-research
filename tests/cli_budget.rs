use std::process::Command;

#[test]
fn ordinary_cli_embedding_refuses_cuda_before_loading_a_model() {
    for arguments in [
        vec![
            "embed-corpus",
            "/unused",
            "/missing-model",
            "/missing-runtime",
            "cuda",
            "1",
        ],
        vec![
            "embed-stage",
            "/unused",
            "stage",
            "/missing-model",
            "/missing-runtime",
            "cuda",
            "1",
        ],
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_oracle-mvp"))
            .args(arguments)
            .output()
            .expect("run command");
        assert!(!output.status.success());
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(stderr.contains("refuses unadmitted CUDA"), "{stderr}");
        assert!(!stderr.contains("missing-model"), "{stderr}");
    }
}

#[test]
fn cli_exposes_the_capped_gpu_workflow() {
    let output = Command::new(env!("CARGO_BIN_EXE_oracle-mvp"))
        .arg("--help")
        .output()
        .expect("run help");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    for command in [
        "audit-stage-token-lengths",
        "benchmark-stage",
        "plan-admission",
        "execute-admission",
    ] {
        assert!(stdout.contains(command), "missing {command}: {stdout}");
    }
}
