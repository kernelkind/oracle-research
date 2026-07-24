use std::path::Path;

use oracle_mvp::evaluator::RepetitionAnswer;
use oracle_mvp::static_exposure_probe_launch::{
    STATIC_EXPOSURE_PROBE_PURPOSE, calibrate_full_pool_exposure_ceiling,
    read_full_pool_escape_probe_launch_config,
};
use oracle_mvp::static_exposure_probe_runner::{
    CREC_109_EXPOSURE_CEILING, FULL_POOL_ESCAPE_PROBE_PURPOSE,
};

#[test]
fn full_pool_outputs_cannot_overwrite_source_probe_outputs_outside_the_config_directory() {
    let temp = tempfile::tempdir().expect("temporary launch fixture");
    let root = temp.path().canonicalize().expect("canonical fixture root");
    let source_config_root = root.join("source-config");
    let phase3_root = root.join("phase3");
    let phase4_root = root.join("phase4");
    let source_output_root = root.join("source-output");
    let source_corpus = root.join("source-corpus.ndb");
    let destination_root = root.join("destination");
    let destination_corpus = destination_root.join("corpus.ndb");
    for directory in [
        &source_config_root,
        &phase3_root,
        &phase4_root,
        &source_output_root,
        &source_corpus,
        &destination_root,
        &destination_corpus,
    ] {
        std::fs::create_dir_all(directory).expect("create launch fixture directory");
    }
    let binding = phase3_root.join("runner-binding.json");
    let phase4_session = phase4_root.join("session.json");
    let frozen_orders = phase4_root.join("orders.json");
    let launch_receipt = phase4_root.join("launch.json");
    let oracle_cache = phase4_root.join("oracle-cache");
    std::fs::create_dir(&oracle_cache).expect("create oracle cache");
    let source_session = source_output_root.join("probe-session.json");
    let source_report = source_output_root.join("probe-report.json");
    for path in [
        &binding,
        &phase4_session,
        &frozen_orders,
        &launch_receipt,
        &source_session,
        &source_report,
    ] {
        std::fs::write(path, b"{}\n").expect("create source artifact");
    }
    std::fs::write(destination_corpus.join("data.mdb"), b"copied corpus")
        .expect("create copied corpus");

    let source_config_path = source_config_root.join("config.json");
    write_json(
        &source_config_path,
        &serde_json::json!({
            "schema_version": 1,
            "purpose": STATIC_EXPOSURE_PROBE_PURPOSE,
            "source_phase3_runner_binding_path": binding,
            "source_phase4_session_path": phase4_session,
            "source_phase4_frozen_orders_path": frozen_orders,
            "source_phase4_oracle_cache_path": oracle_cache,
            "source_phase4_launch_receipt_path": launch_receipt,
            "corpus_path": source_corpus,
            "session_path": source_session,
            "report_path": source_report,
        }),
    );
    let full_config_path = destination_root.join("config.json");
    write_json(
        &full_config_path,
        &serde_json::json!({
            "schema_version": 1,
            "purpose": FULL_POOL_ESCAPE_PROBE_PURPOSE,
            "source_static_exposure_probe_config_path": source_config_path,
            "corpus_path": destination_corpus,
            "session_path": source_output_root.join("probe-session.json"),
            "report_path": destination_root.join("probe-report.json"),
        }),
    );

    let error = read_full_pool_escape_probe_launch_config(&full_config_path)
        .expect_err("full-pool outputs must not overwrite source probe outputs");

    assert!(error.to_string().contains("frozen source"));
}

#[test]
fn crec_108_labels_reproduce_the_frozen_full_pool_ceiling() {
    let observations = [
        (0.0, "no"),
        (0.0, "no"),
        (0.0, "no"),
        (0.013550516313995717, "no"),
        (0.08163404909290403, "no"),
        (0.09940665524126625, "no"),
        (0.11154769026942651, "no"),
        (0.16769210694162784, "no"),
        (0.22899426585096402, "no"),
        (0.2668236673047218, "no"),
        (0.3053102170037677, "no"),
        (0.31672780161040404, "no"),
        (0.3470250797985881, "yes"),
        (0.462930271898372, "yes"),
        (0.4769958691356003, "no"),
        (0.5492640426368693, "yes"),
        (0.6249100368437072, "yes"),
        (0.6192205691090205, "no"),
        (0.45251444936636254, "yes"),
        (0.5295529890744451, "yes"),
        (0.3370049676073291, "yes"),
        (0.6567645194322198, "yes"),
        (0.7214689083350501, "no"),
        (0.7937729890492767, "no"),
        (0.09305429439491571, "yes"),
        (0.892508958334928, "no"),
        (0.38806139791378536, "no"),
        (0.8150584252263323, "no"),
        (0.9270552970257029, "yes"),
        (0.9123157285210586, "yes"),
        (0.9119919469568286, "yes"),
        (0.9671056124817665, "yes"),
        (1.0746700928427289, "yes"),
        (0.8191207956780557, "yes"),
        (0.8009989145977553, "yes"),
        (0.944679391578729, "yes"),
        (1.0455630978924058, "yes"),
        (0.9599538672957817, "yes"),
        (1.2145260848427564, "yes"),
        (1.3618072854769887, "yes"),
    ]
    .map(|(exposure, answer)| {
        (
            exposure,
            if answer == "yes" {
                RepetitionAnswer::Yes
            } else {
                RepetitionAnswer::No
            },
        )
    });

    let calibration =
        calibrate_full_pool_exposure_ceiling(&observations).expect("calibrate exact source labels");

    assert_eq!(
        calibration.ceiling().to_bits(),
        CREC_109_EXPOSURE_CEILING.to_bits()
    );
    assert_eq!(calibration.true_positives(), 20);
    assert_eq!(calibration.false_negatives(), 1);
    assert_eq!(calibration.true_negatives(), 12);
    assert_eq!(calibration.false_positives(), 7);
}

fn write_json(path: &Path, value: &serde_json::Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode launch fixture");
    bytes.push(b'\n');
    std::fs::write(path, bytes).expect("write launch fixture");
}
