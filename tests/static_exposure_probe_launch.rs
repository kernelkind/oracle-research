use std::path::Path;

use oracle_mvp::static_exposure_probe_launch::{
    STATIC_EXPOSURE_PROBE_PURPOSE, read_static_exposure_probe_launch_config,
};

#[test]
fn launch_config_binds_read_only_frozen_sources_to_separate_probe_outputs() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config(
        fixture.root.join("probe-session.json"),
        fixture.root.join("probe-report.json"),
    );

    let config =
        read_static_exposure_probe_launch_config(&config_path).expect("read valid launch config");

    assert_eq!(config.source_phase3_runner_binding_path(), fixture.binding);
    assert_eq!(config.source_phase4_session_path(), fixture.phase4_session);
    assert_eq!(config.source_phase4_frozen_orders_path(), fixture.orders);
    assert_eq!(config.source_phase4_oracle_cache_path(), fixture.cache);
    assert_eq!(config.source_phase4_launch_receipt_path(), fixture.launch);
    assert_eq!(config.corpus_path(), fixture.corpus);
    assert_eq!(
        config.session_path(),
        fixture.root.join("probe-session.json")
    );
    assert_eq!(config.report_path(), fixture.root.join("probe-report.json"));
}

#[test]
fn launch_config_rejects_outputs_inside_the_display_corpus() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config(
        fixture.corpus.join("probe-session.json"),
        fixture.root.join("probe-report.json"),
    );

    let error = read_static_exposure_probe_launch_config(&config_path)
        .expect_err("probe output must not be able to mutate its display corpus");

    assert!(error.to_string().contains("outside"));
}

#[test]
fn launch_config_rejects_a_symlinked_output_inside_frozen_sources() {
    use std::os::unix::fs::symlink;

    let fixture = Fixture::new();
    let alias = fixture.root.join("source-alias");
    symlink(
        fixture
            .binding
            .parent()
            .expect("source binding has a parent"),
        &alias,
    )
    .expect("create source alias");
    let config_path = fixture.write_config(
        alias.join("probe-session.json"),
        fixture.root.join("probe-report.json"),
    );

    let error = read_static_exposure_probe_launch_config(&config_path)
        .expect_err("resolved probe outputs must remain outside frozen sources");

    assert!(error.to_string().contains("outside"));
}

struct Fixture {
    _temp: tempfile::TempDir,
    root: std::path::PathBuf,
    binding: std::path::PathBuf,
    phase4_session: std::path::PathBuf,
    orders: std::path::PathBuf,
    cache: std::path::PathBuf,
    launch: std::path::PathBuf,
    corpus: std::path::PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary launch fixture");
        let root = temp.path().canonicalize().expect("canonical fixture root");
        let source = root.join("source");
        let cache = source.join("oracle-cache");
        let corpus = root.join("display-corpus.ndb");
        std::fs::create_dir_all(&cache).expect("create source cache");
        std::fs::create_dir(&corpus).expect("create display corpus");
        let binding = source.join("runner-binding.json");
        let phase4_session = source.join("phase4-session.json");
        let orders = source.join("frozen-orders.json");
        let launch = source.join("launch.json");
        for path in [&binding, &phase4_session, &orders, &launch] {
            std::fs::write(path, b"{}\n").expect("create source fixture");
        }
        Self {
            _temp: temp,
            root,
            binding,
            phase4_session,
            orders,
            cache,
            launch,
            corpus,
        }
    }

    fn write_config(
        &self,
        session_path: impl AsRef<Path>,
        report_path: impl AsRef<Path>,
    ) -> std::path::PathBuf {
        let config_path = self.root.join("config.json");
        let value = serde_json::json!({
            "schema_version": 1,
            "purpose": STATIC_EXPOSURE_PROBE_PURPOSE,
            "source_phase3_runner_binding_path": self.binding,
            "source_phase4_session_path": self.phase4_session,
            "source_phase4_frozen_orders_path": self.orders,
            "source_phase4_oracle_cache_path": self.cache,
            "source_phase4_launch_receipt_path": self.launch,
            "corpus_path": self.corpus,
            "session_path": session_path.as_ref(),
            "report_path": report_path.as_ref(),
        });
        std::fs::write(
            &config_path,
            serde_json::to_vec_pretty(&value).expect("encode launch config"),
        )
        .expect("write launch config");
        config_path
    }
}
