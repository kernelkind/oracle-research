use std::collections::BTreeSet;
use std::fs;
use std::os::unix::fs::{PermissionsExt, symlink};
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::english_filter::{
    CLASSIFICATION_POLICY, GLOTLID_V3_REPOSITORY_COMMIT, GLOTLID_V3_SHA256, NORMALIZATION_POLICY,
};
use oracle_mvp::semantic_map_sample::{
    INITIAL_SAMPLE_ROWS, SAMPLE_ROWS, SemanticMapSampleConfig, SemanticMapSampleManifest,
    freeze_semantic_map_sample,
};
use sha2::{Digest, Sha256};

const VALID_NOTE_REFERENCE: &str =
    "nostr:note1rss6chekdfhvk8lhsmznxu4suv8ajlhralmelkp5cegrlunu49sqel9fuv";

#[test]
fn freezes_one_uniform_order_with_a_fixed_prefix_and_extension() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let source_path = root.path().join("fresh-corpus.ndb");
    let source = open_ndb(&source_path);
    let mut events = (0..SAMPLE_ROWS + 64)
        .map(|index| {
            signed_test_event(
                &format!(
                    "Eligible note {index} discusses a distinct real subject for the semantic map."
                ),
                index as u64,
            )
        })
        .collect::<Vec<_>>();
    events.push(signed_test_event("https://example.com/only-a-link", 10_001));
    events.push(signed_test_event(VALID_NOTE_REFERENCE, 10_002));
    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());
    drop(source);

    let source_data = source_path.join("data.mdb");
    let source_lock = source_path.join("lock.mdb");
    let source_hash_before = sha256_file(&source_data);
    let source_lock_hash_before = sha256_file(&source_lock);
    let mut permissions = fs::metadata(&source_data)
        .expect("source metadata")
        .permissions();
    permissions.set_mode(0o444);
    fs::set_permissions(&source_data, permissions).expect("make source data read-only");

    let ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let unusable_ids = BTreeSet::from([ids[SAMPLE_ROWS + 64], ids[SAMPLE_ROWS + 65]]);
    let forward_order = root.path().join("forward-ordered-event-ids.bin");
    write_ids(&forward_order, &ids);
    let forward_manifest = root.path().join("forward-english-manifest.json");
    write_source_manifest(
        &forward_manifest,
        &forward_order,
        &source_hash_before,
        ids.len(),
    );

    let first_output = root.path().join("sample-first");
    let first = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forward_manifest.clone(),
        output_path: first_output.clone(),
    })
    .expect("freeze first sample");

    assert_eq!(SAMPLE_ROWS as u64, first.selected_events);
    assert_eq!(
        b"oracle-mvp/scaled-semantic-map-sample/v1\0",
        first.selection_domain.as_bytes(),
        "the manifest must record every byte supplied to SHA-256"
    );
    assert!(
        first.selection_rule.contains("then-event-id"),
        "the manifest must record the deterministic tie-break"
    );
    assert_eq!(INITIAL_SAMPLE_ROWS as u64, first.initial_rows);
    assert_eq!(INITIAL_SAMPLE_ROWS as u64, first.extension_rows);
    assert_eq!(2, first.excluded_no_usable_text);
    assert_eq!((SAMPLE_ROWS * 32) as u64, first.ordered_event_ids.bytes);
    let selected = read_ids(&first_output.join("ordered-event-ids.bin"));
    assert_eq!(SAMPLE_ROWS, selected.len());
    assert_eq!(
        SAMPLE_ROWS,
        selected.iter().copied().collect::<BTreeSet<_>>().len()
    );
    assert!(selected.iter().all(|id| !unusable_ids.contains(id)));
    assert_ne!(&ids[..SAMPLE_ROWS], selected.as_slice());
    let mut expected = ids[..SAMPLE_ROWS + 64]
        .iter()
        .copied()
        .map(|id| {
            let mut hasher = Sha256::new();
            hasher.update(b"oracle-mvp/scaled-semantic-map-sample/v1\0");
            hasher.update(id);
            (<[u8; 32]>::from(hasher.finalize()), id)
        })
        .collect::<Vec<_>>();
    expected.sort_unstable();
    let expected = expected
        .into_iter()
        .take(SAMPLE_ROWS)
        .map(|(_, id)| id)
        .collect::<Vec<_>>();
    assert_eq!(
        expected, selected,
        "selection must be the frozen bottom-k rule"
    );

    let forged_manifest = root.path().join("forged-english-manifest.json");
    let mut forged: serde_json::Value = serde_json::from_slice(
        &fs::read(&forward_manifest).expect("read source manifest for forgery"),
    )
    .expect("decode source manifest for forgery");
    forged["source_ndb_data_sha256"] = serde_json::Value::String("0".repeat(64));
    fs::write(
        &forged_manifest,
        serde_json::to_vec_pretty(&forged).expect("encode forged source manifest"),
    )
    .expect("write forged source manifest");
    let error = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forged_manifest,
        output_path: root.path().join("forged-source-output"),
    })
    .expect_err("a manifest for different NostrDB bytes must be rejected");
    assert!(
        error.to_string().contains("source NostrDB data SHA-256"),
        "{error}"
    );

    let forged_model_manifest = root.path().join("forged-model-manifest.json");
    let mut forged_model: serde_json::Value = serde_json::from_slice(
        &fs::read(&forward_manifest).expect("read source manifest for model forgery"),
    )
    .expect("decode source manifest for model forgery");
    forged_model["model_sha256"] = serde_json::Value::String("4".repeat(64));
    fs::write(
        &forged_model_manifest,
        serde_json::to_vec_pretty(&forged_model).expect("encode forged model manifest"),
    )
    .expect("write forged model manifest");
    let error = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forged_model_manifest,
        output_path: root.path().join("forged-model-output"),
    })
    .expect_err("a different English-classifier model must be rejected");
    assert!(error.to_string().contains("classifier model"), "{error}");

    let error = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forward_manifest.clone(),
        output_path: source_path.join("forbidden-output"),
    })
    .expect_err("sample output must not be placed inside the source corpus");
    assert!(error.to_string().contains("overlaps a source"), "{error}");

    assert_eq!(
        first,
        freeze_semantic_map_sample(&SemanticMapSampleConfig {
            source_corpus_path: source_path.clone(),
            source_ordered_event_ids_path: forward_order.clone(),
            source_manifest_path: forward_manifest.clone(),
            output_path: first_output.clone(),
        })
        .expect("deeply verify existing sample")
    );

    fs::write(
        first_output.join("unexpected.txt"),
        b"not part of the artifact",
    )
    .expect("write unexpected output file");
    let error = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forward_manifest.clone(),
        output_path: first_output.clone(),
    })
    .expect_err("an extra output file must invalidate replay");
    assert!(
        error.to_string().contains("exactly its three frozen files"),
        "{error}"
    );
    fs::remove_file(first_output.join("unexpected.txt")).expect("remove unexpected output file");

    let external_sidecar = root.path().join("external-ordered-event-ids.sha256");
    fs::rename(
        first_output.join("ordered-event-ids.sha256"),
        &external_sidecar,
    )
    .expect("move sidecar outside the artifact");
    symlink(
        &external_sidecar,
        first_output.join("ordered-event-ids.sha256"),
    )
    .expect("replace sidecar with a symlink");
    let error = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forward_manifest.clone(),
        output_path: first_output.clone(),
    })
    .expect_err("a symlinked output file must invalidate replay");
    assert!(error.to_string().contains("regular files"), "{error}");
    fs::remove_file(first_output.join("ordered-event-ids.sha256"))
        .expect("remove symlinked sidecar");
    fs::rename(
        &external_sidecar,
        first_output.join("ordered-event-ids.sha256"),
    )
    .expect("restore sidecar inside the artifact");

    let second_output = root.path().join("sample-second");
    let second = freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: forward_order.clone(),
        source_manifest_path: forward_manifest,
        output_path: second_output.clone(),
    })
    .expect("freeze repeated sample");
    assert_eq!(first, second);
    assert_eq!(
        fs::read(first_output.join("ordered-event-ids.bin")).expect("first ordered IDs"),
        fs::read(second_output.join("ordered-event-ids.bin")).expect("second ordered IDs")
    );
    assert_eq!(
        fs::read(first_output.join("ordered-event-ids.sha256")).expect("first checksum"),
        fs::read(second_output.join("ordered-event-ids.sha256")).expect("second checksum")
    );
    assert_eq!(
        fs::read(first_output.join("manifest.json")).expect("first manifest"),
        fs::read(second_output.join("manifest.json")).expect("second manifest")
    );

    let mut reverse_ids = ids.clone();
    reverse_ids.reverse();
    let reverse_order = root.path().join("reverse-ordered-event-ids.bin");
    write_ids(&reverse_order, &reverse_ids);
    let reverse_manifest = root.path().join("reverse-english-manifest.json");
    write_source_manifest(
        &reverse_manifest,
        &reverse_order,
        &source_hash_before,
        reverse_ids.len(),
    );
    let reverse_output = root.path().join("sample-reverse");
    freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: reverse_order,
        source_manifest_path: reverse_manifest,
        output_path: reverse_output.clone(),
    })
    .expect("freeze reverse-order sample");
    assert_eq!(
        selected,
        read_ids(&reverse_output.join("ordered-event-ids.bin")),
        "source newest-first order must not determine sample membership or order"
    );

    assert_eq!(source_hash_before, sha256_file(&source_data));
    assert_eq!(source_lock_hash_before, sha256_file(&source_lock));
    assert_eq!(
        first,
        serde_json::from_slice::<SemanticMapSampleManifest>(
            &fs::read(first_output.join("manifest.json")).expect("stored manifest")
        )
        .expect("decode stored manifest")
    );
    assert_eq!(
        BTreeSet::from([
            "manifest.json".to_owned(),
            "ordered-event-ids.bin".to_owned(),
            "ordered-event-ids.sha256".to_owned(),
        ]),
        fs::read_dir(&first_output)
            .expect("sample directory")
            .map(|entry| {
                entry
                    .expect("sample directory entry")
                    .file_name()
                    .into_string()
                    .expect("UTF-8 sample filename")
            })
            .collect()
    );
}

fn write_source_manifest(path: &Path, ordered_path: &Path, data_sha256: &str, rows: usize) {
    fs::write(
        path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 2,
            "source_ordered_event_ids_sha256": "1".repeat(64),
            "source_ndb_data_sha256": data_sha256,
            "source_derivation_ledger_sha256": "2".repeat(64),
            "source_dedup_manifest_sha256": "3".repeat(64),
            "model_sha256": GLOTLID_V3_SHA256,
            "model_repository_commit": GLOTLID_V3_REPOSITORY_COMMIT,
            "normalization_policy": NORMALIZATION_POLICY,
            "classification_policy": CLASSIFICATION_POLICY,
            "input_events": rows,
            "retained_events": rows,
            "excluded_events": 0,
            "output_ordered_event_ids_sha256": sha256_file(ordered_path)
        }))
        .expect("encode source manifest"),
    )
    .expect("write source manifest");
}

fn open_ndb(path: &Path) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new()
            .set_flags((1 << 2) | (1 << 3) | (1 << 4))
            .set_mapsize(512 * 1_024 * 1_024)
            .set_ingester_threads(1),
    )
    .expect("open NostrDB")
}

fn submit(ndb: &Ndb, event: &str) {
    loop {
        match ndb.process_event(event) {
            Ok(()) => return,
            Err(NdbError::NoteProcessFailed) => thread::sleep(Duration::from_millis(10)),
            Err(error) => panic!("submit event: {error}"),
        }
    }
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let transaction = Transaction::new(ndb).expect("transaction");
        let count = ndb
            .count(&transaction, &[Filter::new().build()])
            .expect("count events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "timed out waiting for notes");
        thread::sleep(Duration::from_millis(10));
    }
}

fn signed_test_event(content: &str, seed: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + seed)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign test event")
        .json()
        .expect("serialize test event")
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
    let encoded = value["id"].as_str().expect("event ID").as_bytes();
    let mut id = [0_u8; 32];
    for (index, bytes) in encoded.chunks_exact(2).enumerate() {
        id[index] = decode_hex(bytes[0]) << 4 | decode_hex(bytes[1]);
    }
    id
}

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hexadecimal event ID"),
    }
}

fn write_ids(path: &Path, ids: &[[u8; 32]]) {
    fs::write(path, ids.iter().flatten().copied().collect::<Vec<_>>()).expect("write ordered IDs");
}

fn read_ids(path: &Path) -> Vec<[u8; 32]> {
    let bytes = fs::read(path).expect("read ordered IDs");
    let mut records = bytes.chunks_exact(32);
    let ids = records
        .by_ref()
        .map(|record| record.try_into().expect("event ID width"))
        .collect();
    assert!(records.remainder().is_empty());
    ids
}

fn sha256_file(path: &Path) -> String {
    let bytes = fs::read(path).expect("hash input");
    format!("{:x}", Sha256::digest(bytes))
}
