use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::process::Command;

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::embedding::{
    EmbeddingBuildConfig, EmbeddingEncoder, EmbeddingManifest, EncoderDescriptor,
};
use oracle_mvp::event::EventId;
use oracle_mvp::oracle::{OfflineOracle, Oracle};
use oracle_mvp::preflight::PreflightConfig;
use oracle_mvp::retrieval::ExactRetriever;
use oracle_mvp::snapshot::{CanonicalManifest, CorpusManifest, DamusSnapshot, SourceManifest};
use oracle_mvp::stage::CorpusStageConfig;
use sha2::{Digest, Sha256};

#[test]
fn imports_validated_source_and_derives_eligible_corpus() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");

    let eligible_url = signed_note(1, "read https://example.com", &[]);
    let eligible_plain = signed_note(1, "plain root note", &[]);
    let reply = signed_note(1, "reply", &[["e", &"11".repeat(32), "", "reply"]]);
    let quote = signed_note(1, "quote", &[["q", &"22".repeat(32), "", ""]]);
    let legacy_quote = signed_note(1, "legacy quote", &[["e", &"33".repeat(32), "", "mention"]]);
    let metadata = signed_note(0, "{}", &[]);
    let embedded_root = signed_note(1, "root recovered from repost content", &[]);
    let nested_repost = signed_note(6, &embedded_root, &[]);
    let nested_envelope = format!(r#"["EVENT","nested",{nested_repost}]"#);
    let repost = signed_note(6, &nested_envelope, &[]);
    let tampered = eligible_plain.replace("plain root note", "invalid signature");

    write_snapshot(
        pipeline.layout().snapshot(),
        &[
            &eligible_url,
            &eligible_plain,
            &reply,
            &quote,
            &legacy_quote,
            &metadata,
            &repost,
            &eligible_url,
            &tampered,
        ],
    );

    let source = pipeline.import_source().expect("source import");
    assert_eq!(
        source.counts,
        oracle_mvp::snapshot::SourceCounts {
            snapshot_records: 9,
            stored_events: 9,
        }
    );
    assert_manifest::<SourceManifest>(pipeline.layout().source_manifest(), &source);

    let corpus = pipeline.derive_corpus().expect("corpus derivation");
    assert_eq!(
        corpus,
        CorpusManifest {
            schema_version: 1,
            source_snapshot_sha256: source.snapshot_sha256,
            rejections: oracle_mvp::snapshot::EligibilityRejections {
                non_kind_1: 3,
                replies: 1,
                quotes: 2,
            },
            eligible_events: 3,
        }
    );
    assert_manifest::<CorpusManifest>(pipeline.layout().corpus_manifest(), &corpus);

    let ndb = open_ndb(pipeline.layout().corpus_db());
    let txn = Transaction::new(&ndb).expect("corpus transaction");
    let kind_one = Filter::new().kinds([1]).build();
    let contents = ndb
        .fold(&txn, &[kind_one], Vec::new(), |mut contents, note| {
            contents.push(note.content().to_owned());
            contents
        })
        .expect("query corpus");
    assert_eq!(contents.len(), 3);
    assert!(contents.iter().any(|content| content == "plain root note"));
    assert!(
        contents
            .iter()
            .any(|content| content == "read https://example.com")
    );
    assert!(
        contents
            .iter()
            .any(|content| content == "root recovered from repost content")
    );
}

#[test]
fn imports_lax_numeric_kind_without_losing_embedded_content() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let child = signed_note(1, "embedded root", &[]);
    let kind_six = signed_note(6, &child, &[]);
    let lax_kind = kind_six.replacen(r#""kind":6"#, r#""kind":6.0"#, 1);
    assert_ne!(lax_kind, kind_six);
    write_snapshot(pipeline.layout().snapshot(), &[&lax_kind]);

    let source = pipeline.import_source().expect("source import");
    assert_eq!(source.counts.stored_events, 2);
}

#[test]
fn does_not_store_non_string_kind_six_content() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let child = signed_note(1, "embedded root", &[]);
    let kind_six = signed_note(6, &child, &[]);
    let encoded_child = serde_json::to_string(&child).expect("encoded child content");
    let lax_content = kind_six.replacen(
        &format!(r#""content":{encoded_child}"#),
        &format!(r#""content":{child}"#),
        1,
    );
    assert_ne!(lax_content, kind_six);
    write_snapshot(pipeline.layout().snapshot(), &[&lax_content]);

    let source = pipeline.import_source().expect("source import");
    assert_eq!(source.counts.stored_events, 0);
}

#[test]
fn build_command_publishes_all_pipeline_artifacts() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let eligible = signed_note(1, "one eligible event", &[]);
    write_snapshot(pipeline.layout().snapshot(), &[&eligible]);

    let output = Command::new(env!("CARGO_BIN_EXE_oracle-mvp"))
        .arg("build")
        .arg(&root)
        .output()
        .expect("run oracle-mvp");

    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let result: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("command result JSON");
    assert_eq!(result["source"]["counts"]["stored_events"], 1);
    assert_eq!(result["corpus"]["eligible_events"], 1);
    assert_eq!(result["canonical"]["counts"]["canonical_rows"], 1);
    assert!(pipeline.layout().source_db().is_dir());
    assert!(pipeline.layout().corpus_db().is_dir());
    assert!(pipeline.layout().canonical_rows().is_file());
    assert!(pipeline.layout().canonical_aliases().is_file());
}

#[test]
fn canonicalizes_exact_content_and_orders_rows_independently_of_ingestion_order() {
    let duplicate_a = signed_note_at(1, "same content", &[], 1_700_000_101, 1);
    let duplicate_b = signed_note_at(1, "same content", &[], 1_700_000_102, 2);
    let unique_a = signed_note_at(1, "unique alpha", &[], 1_700_000_103, 3);
    let unique_b = signed_note_at(1, "unique beta", &[], 1_700_000_104, 4);
    let events = [&duplicate_a, &duplicate_b, &unique_a, &unique_b];

    let first = canonicalize_fixture(&events);
    let reversed = canonicalize_fixture(&events.into_iter().rev().collect::<Vec<_>>());

    assert_ne!(
        first.manifest.source_snapshot_sha256,
        reversed.manifest.source_snapshot_sha256
    );
    assert_eq!(first.manifest.counts, reversed.manifest.counts);
    assert_eq!(first.manifest.rows, reversed.manifest.rows);
    assert_eq!(first.manifest.aliases, reversed.manifest.aliases);
    assert_eq!(first.rows, reversed.rows);
    assert_eq!(first.aliases, reversed.aliases);
    assert_eq!(
        first.manifest,
        CanonicalManifest {
            schema_version: 1,
            source_snapshot_sha256: first.manifest.source_snapshot_sha256.clone(),
            content_rule: "byte-identical-utf8-v1".to_owned(),
            canonical_event_rule: "lowest-event-id-v1".to_owned(),
            row_order_rule: "sha256-domain-separated-event-id-v1".to_owned(),
            counts: oracle_mvp::snapshot::CanonicalCounts {
                eligible_events: 4,
                canonical_rows: 3,
                duplicate_events: 1,
            },
            rows: first.manifest.rows.clone(),
            aliases: first.manifest.aliases.clone(),
        }
    );
    assert_eq!(first.manifest.rows.record_bytes, 32);
    assert_eq!(first.manifest.rows.records, 3);
    assert_eq!(first.manifest.rows.bytes, 96);
    assert_eq!(first.manifest.aliases.record_bytes, 64);
    assert_eq!(first.manifest.aliases.records, 4);
    assert_eq!(first.manifest.aliases.bytes, 256);

    let duplicate_ids = [event_id(&duplicate_a), event_id(&duplicate_b)];
    let canonical_duplicate = *duplicate_ids.iter().min().expect("duplicate ID");
    let mut expected_aliases = vec![
        (duplicate_ids[0], canonical_duplicate),
        (duplicate_ids[1], canonical_duplicate),
        (event_id(&unique_a), event_id(&unique_a)),
        (event_id(&unique_b), event_id(&unique_b)),
    ];
    expected_aliases.sort_unstable();
    assert_eq!(decode_aliases(&first.aliases), expected_aliases);

    let mut expected_rows = vec![
        canonical_duplicate,
        event_id(&unique_a),
        event_id(&unique_b),
    ];
    expected_rows.sort_unstable_by_key(row_order_key);
    assert_eq!(decode_rows(&first.rows), expected_rows);
}

#[test]
fn embeds_canonical_rows_into_versioned_int8_shards() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let duplicate_a = signed_note_at(1, "same content", &[], 1_700_000_201, 11);
    let duplicate_b = signed_note_at(1, "same content", &[], 1_700_000_202, 12);
    let url = signed_note_at(1, "read https://example.com", &[], 1_700_000_203, 13);
    let plain = signed_note_at(1, "plain content", &[], 1_700_000_204, 14);
    write_snapshot(
        pipeline.layout().snapshot(),
        &[&duplicate_a, &duplicate_b, &url, &plain],
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");

    let mut encoder = DeterministicEncoder::new();
    let config = EmbeddingBuildConfig {
        artifact_name: "test-native-int8".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let manifest = pipeline
        .embed_canonical_corpus(&config, &mut encoder)
        .expect("embedding artifacts");

    assert_manifest::<EmbeddingManifest>(
        pipeline.layout().embedding_manifest(&config.artifact_name),
        &manifest,
    );
    assert_eq!(manifest.total_rows, 3);
    assert_eq!(manifest.shards.len(), 2);
    assert_eq!(manifest.shards[0].start_row, 0);
    assert_eq!(manifest.shards[0].rows, 2);
    assert_eq!(manifest.shards[1].start_row, 2);
    assert_eq!(manifest.shards[1].rows, 1);
    assert_eq!(encoder.batch_sizes, vec![2, 1]);
    assert!(
        encoder
            .seen
            .iter()
            .any(|content| content == "read https://example.com")
    );

    let embedding_root = pipeline.layout().embedding_dir(&config.artifact_name);
    let mut embedded_ids = Vec::new();
    for shard in &manifest.shards {
        let row_ids = fs::read(embedding_root.join(&shard.row_ids.file)).expect("shard row IDs");
        let vectors = fs::read(embedding_root.join(&shard.vectors.file)).expect("shard vectors");
        let norms = fs::read(embedding_root.join(&shard.norms.file)).expect("shard norms");
        assert_eq!(vectors.len(), usize::try_from(shard.rows).unwrap() * 4);
        assert_eq!(norms.len(), usize::try_from(shard.rows).unwrap() * 4);
        for (vector, norm) in vectors.chunks_exact(4).zip(norms.chunks_exact(4)) {
            let expected = vector
                .iter()
                .map(|byte| f32::from(*byte as i8).powi(2))
                .sum::<f32>()
                .sqrt();
            assert_eq!(f32::from_le_bytes(norm.try_into().unwrap()), expected);
        }
        embedded_ids.extend(decode_rows(&row_ids));
    }
    let canonical_ids =
        decode_rows(&fs::read(pipeline.layout().canonical_rows()).expect("canonical row IDs"));
    assert_eq!(embedded_ids, canonical_ids);

    encoder.batch_sizes.clear();
    encoder.seen.clear();
    let reopened = pipeline
        .embed_canonical_corpus(&config, &mut encoder)
        .expect("reopen compatible embedding artifacts");
    assert_eq!(reopened, manifest);
    assert!(encoder.batch_sizes.is_empty());
    assert!(encoder.seen.is_empty());

    encoder.descriptor.model_revision = "fixture-v2".to_owned();
    let error = pipeline
        .embed_canonical_corpus(&config, &mut encoder)
        .expect_err("reject incompatible encoder identity");
    assert!(error.to_string().contains("encoder identity"));
}

#[test]
fn exact_sharded_int8_search_matches_the_reference_order() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let alpha = signed_note_at(1, "alpha", &[], 1_700_000_301, 21);
    let beta = signed_note_at(1, "beta", &[], 1_700_000_302, 22);
    let diagonal = signed_note_at(1, "diagonal", &[], 1_700_000_303, 23);
    let opposite = signed_note_at(1, "opposite", &[], 1_700_000_304, 24);
    write_snapshot(
        pipeline.layout().snapshot(),
        &[&alpha, &beta, &diagonal, &opposite],
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");

    let vectors = [
        ("alpha", [2_i8, 0_i8]),
        ("beta", [1, 0]),
        ("diagonal", [1, 1]),
        ("opposite", [-1, 0]),
    ];
    let mut encoder = LookupEncoder::new(&vectors);
    let config = EmbeddingBuildConfig {
        artifact_name: "exact-search-one-row-shards".to_owned(),
        batch_size: 2,
        shard_rows: 1,
    };
    pipeline
        .embed_canonical_corpus(&config, &mut encoder)
        .expect("embedding artifacts");

    let retriever =
        ExactRetriever::open(&pipeline, &config.artifact_name).expect("open exact retriever");
    let actual = retriever
        .search(&[1, 0], 4, None)
        .expect("exact full-matrix search");

    let mut expected = vec![
        (event_id(&alpha), cosine(&[1, 0], &[2, 0])),
        (event_id(&beta), cosine(&[1, 0], &[1, 0])),
        (event_id(&diagonal), cosine(&[1, 0], &[1, 1])),
        (event_id(&opposite), cosine(&[1, 0], &[-1, 0])),
    ];
    expected.sort_by(|left, right| {
        right
            .1
            .total_cmp(&left.1)
            .then_with(|| left.0.cmp(&right.0))
    });
    assert_eq!(actual.len(), expected.len());
    for (candidate, (expected_id, expected_score)) in actual.iter().zip(&expected) {
        assert_eq!(candidate.event_id, *expected_id);
        assert_eq!(candidate.cosine_score, *expected_score);
    }

    let repeated = retriever
        .search(&[1, 0], 4, None)
        .expect("repeated exact search");
    assert_eq!(repeated, actual);
    let excluded = retriever
        .search(&[1, 0], 2, Some(expected[0].0))
        .expect("exact search with exclusion");
    assert_eq!(
        excluded
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        expected
            .iter()
            .skip(1)
            .take(2)
            .map(|(event_id, _)| *event_id)
            .collect::<Vec<_>>()
    );
}

#[test]
fn text_and_note_queries_return_independent_versioned_evidence() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let duplicate_a = signed_note_at(1, "alpha", &[], 1_700_000_401, 31);
    let duplicate_b = signed_note_at(1, "alpha", &[], 1_700_000_402, 32);
    let beta = signed_note_at(1, "beta", &[], 1_700_000_403, 33);
    let diagonal = signed_note_at(1, "diagonal", &[], 1_700_000_404, 34);
    write_snapshot(
        pipeline.layout().snapshot(),
        &[&duplicate_a, &duplicate_b, &beta, &diagonal],
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");

    let vectors = [
        ("alpha", [2_i8, 0_i8]),
        ("beta", [1, 0]),
        ("diagonal", [1, 1]),
        ("query about alpha", [1, 0]),
    ];
    let mut build_encoder = LookupEncoder::new(&vectors);
    let config = EmbeddingBuildConfig {
        artifact_name: "oracle-entrypoints".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    pipeline
        .embed_canonical_corpus(&config, &mut build_encoder)
        .expect("embedding artifacts");

    let mut oracle = OfflineOracle::open(
        &pipeline,
        &config.artifact_name,
        LookupEncoder::new(&vectors),
    )
    .expect("open offline oracle");
    let text = oracle
        .search_text("query about alpha", 3)
        .expect("text search");
    assert_eq!(
        text.candidates
            .iter()
            .map(|candidate| candidate.rank)
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert!(!text.versions.corpus.is_empty());
    assert!(text.versions.retriever.starts_with("exact-int8-cosine-v1:"));
    assert_eq!(
        oracle
            .search_text("query about alpha", 3)
            .expect("repeated text search"),
        text
    );

    let duplicate_ids = [event_id(&duplicate_a), event_id(&duplicate_b)];
    let canonical = *duplicate_ids.iter().min().expect("canonical duplicate");
    let alias = *duplicate_ids.iter().max().expect("noncanonical duplicate");
    let neighbors = oracle
        .similar_notes(EventId::from(alias), 3)
        .expect("note-neighbor search through alias");
    assert_eq!(neighbors.versions, text.versions);
    assert!(
        neighbors
            .candidates
            .iter()
            .all(|candidate| candidate.event_id != EventId::from(canonical))
    );
    assert_eq!(neighbors.candidates.len(), 2);

    let error = oracle
        .similar_notes(EventId::from([0xff; 32]), 3)
        .expect_err("unknown event is rejected");
    assert!(error.to_string().contains("not present"));
    let error = oracle
        .search_text("query about alpha", 0)
        .expect_err("zero candidate depth is rejected");
    assert!(error.to_string().contains("candidate depth"));

    let mut incompatible = LookupEncoder::new(&vectors);
    incompatible.descriptor.model_revision = "fixture-v2".to_owned();
    let error = OfflineOracle::open(&pipeline, &config.artifact_name, incompatible)
        .err()
        .expect("incompatible text encoder is rejected");
    assert!(error.to_string().contains("encoder identity"));
}

#[test]
fn corpus_stage_selects_and_embeds_exactly_the_requested_stable_rows() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let alpha = signed_note_at(1, "alpha", &[], 1_700_000_501, 41);
    let beta = signed_note_at(1, "beta", &[], 1_700_000_502, 42);
    let gamma = signed_note_at(1, "gamma", &[], 1_700_000_503, 43);
    let delta = signed_note_at(1, "delta", &[], 1_700_000_504, 44);
    write_snapshot(
        pipeline.layout().snapshot(),
        &[&alpha, &beta, &gamma, &delta],
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");

    let stage_config = CorpusStageConfig {
        name: "three-row-preflight".to_owned(),
        rows: 3,
    };
    let stage = pipeline
        .materialize_corpus_stage(&stage_config)
        .expect("materialize corpus stage");
    assert_eq!(stage.available_canonical_rows, 4);
    assert_eq!(stage.selected_rows, 3);
    assert_eq!(stage.rows.records, 3);
    let canonical_rows = fs::read(pipeline.layout().canonical_rows()).expect("canonical rows");
    let stage_rows =
        fs::read(pipeline.layout().corpus_stage_rows(&stage_config.name)).expect("stage rows");
    assert_eq!(stage_rows, canonical_rows[..3 * 32]);
    assert_eq!(
        pipeline
            .materialize_corpus_stage(&stage_config)
            .expect("reopen corpus stage"),
        stage
    );
    let error = pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "too-large".to_owned(),
            rows: 5,
        })
        .expect_err("insufficient canonical rows are rejected");
    assert!(error.to_string().contains("only 4"));

    let vectors = [
        ("alpha", [4_i8, 0_i8]),
        ("beta", [3, 1]),
        ("gamma", [2, 2]),
        ("delta", [1, 3]),
        ("query", [1, 0]),
    ];
    let embedding_config = EmbeddingBuildConfig {
        artifact_name: "three-row-stage-embedding".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let mut build_encoder = LookupEncoder::new(&vectors);
    let embedding = pipeline
        .embed_corpus_stage(&stage_config.name, &embedding_config, &mut build_encoder)
        .expect("embed selected corpus stage");
    assert_eq!(embedding.total_rows, 3);
    assert_eq!(
        embedding
            .corpus_stage
            .as_ref()
            .expect("embedding stage identity")
            .name,
        stage_config.name
    );

    let mut oracle = OfflineOracle::open(
        &pipeline,
        &embedding_config.artifact_name,
        LookupEncoder::new(&vectors),
    )
    .expect("open staged oracle");
    assert_eq!(
        oracle
            .search_text("query", 10)
            .expect("search staged matrix")
            .candidates
            .len(),
        3
    );
    let selected = decode_rows(&stage_rows);
    let outside = decode_rows(&canonical_rows)
        .into_iter()
        .find(|event_id| !selected.contains(event_id))
        .expect("event outside selected stage");
    let error = oracle
        .similar_notes(EventId::from(outside), 3)
        .expect_err("out-of-stage event is rejected");
    assert!(error.to_string().contains("not present"));

    drop(oracle);
    let preflight_config = PreflightConfig {
        name: "three-row-codepath-check".to_owned(),
        stage_name: stage_config.name.clone(),
        embedding_artifact: embedding_config.artifact_name,
        expected_rows: 3,
        topic: "query".to_owned(),
        candidate_depth: 1,
    };
    let preflight = pipeline
        .execute_preflight(&preflight_config, LookupEncoder::new(&vectors))
        .expect("execute production-shaped preflight");
    assert!(preflight.failures.is_empty());
    assert!(preflight.checks.text_query_deterministic);
    assert!(preflight.checks.runner_state_deterministic);
    assert!(preflight.checks.local_order_deterministic);
    assert!(preflight.checks.onboarding_filtered);
    assert!(preflight.checks.source_excluded);
    assert_eq!(preflight.selected_rows, 3);
    assert_eq!(preflight.bootstrap_candidates, 1);
    assert_eq!(preflight.local_candidates, 1);
    assert_eq!(
        pipeline
            .execute_preflight(&preflight_config, LookupEncoder::new(&vectors))
            .expect("reopen preflight record"),
        preflight
    );

    for unsafe_name in [".", ".."] {
        let error = pipeline
            .materialize_corpus_stage(&CorpusStageConfig {
                name: unsafe_name.to_owned(),
                rows: 3,
            })
            .expect_err("path component stage name is rejected");
        assert!(error.to_string().contains("filesystem-safe"));
    }
    let mut unsafe_preflight = preflight_config.clone();
    unsafe_preflight.name = "..".to_owned();
    let error = pipeline
        .execute_preflight(&unsafe_preflight, LookupEncoder::new(&vectors))
        .expect_err("path component preflight name is rejected");
    assert!(error.to_string().contains("filesystem-safe"));
    let mut unsafe_embedding_encoder = LookupEncoder::new(&vectors);
    let error = pipeline
        .embed_corpus_stage(
            &stage_config.name,
            &EmbeddingBuildConfig {
                artifact_name: ".".to_owned(),
                batch_size: 1,
                shard_rows: 1,
            },
            &mut unsafe_embedding_encoder,
        )
        .expect_err("path component embedding name is rejected");
    assert!(error.to_string().contains("filesystem-safe"));

    let alternate_stage = pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "same-rows-other-stage".to_owned(),
            rows: 3,
        })
        .expect("materialize alternate stage identity");
    let preflight_path = pipeline.layout().preflight_manifest(&preflight_config.name);
    let original_preflight = fs::read(&preflight_path).expect("original preflight record");
    let mut mismatched_stage = preflight.clone();
    mismatched_stage.stage_name = alternate_stage.name.clone();
    mismatched_stage.stage_manifest_sha256 = sha256_file(
        &pipeline
            .layout()
            .corpus_stage_manifest(&alternate_stage.name),
    );
    fs::write(
        &preflight_path,
        serde_json::to_vec_pretty(&mismatched_stage).expect("serialize mismatched stage record"),
    )
    .expect("write mismatched stage record");
    let error = pipeline
        .open_preflight(&preflight_config.name)
        .expect_err("embedding bound to another stage is rejected");
    assert!(error.to_string().contains("embedding"));

    fs::write(&preflight_path, &original_preflight).expect("restore preflight record");
    let mut mismatched_versions = preflight.clone();
    mismatched_versions.oracle_versions.corpus = "00".repeat(32);
    fs::write(
        &preflight_path,
        serde_json::to_vec_pretty(&mismatched_versions)
            .expect("serialize mismatched version record"),
    )
    .expect("write mismatched version record");
    let error = pipeline
        .open_preflight(&preflight_config.name)
        .expect_err("unrelated oracle versions are rejected");
    assert!(error.to_string().contains("oracle versions"));

    fs::write(&preflight_path, &original_preflight).expect("restore preflight record");
    let mut inconsistent_failures = preflight.clone();
    inconsistent_failures.checks.unseen_neighbor_returned = false;
    fs::write(
        &preflight_path,
        serde_json::to_vec_pretty(&inconsistent_failures)
            .expect("serialize inconsistent failure record"),
    )
    .expect("write inconsistent failure record");
    let error = pipeline
        .open_preflight(&preflight_config.name)
        .expect_err("checks and failures must agree");
    assert!(error.to_string().contains("failures"));
    fs::write(&preflight_path, &original_preflight).expect("restore preflight record");

    let canonical_manifest_path = pipeline.layout().canonical_manifest();
    let original_canonical_manifest =
        fs::read(&canonical_manifest_path).expect("original canonical manifest");
    let stage_manifest_path = pipeline.layout().corpus_stage_manifest(&stage_config.name);
    let original_stage_manifest =
        fs::read(&stage_manifest_path).expect("original corpus stage manifest");
    let mut incompatible_canonical: CanonicalManifest =
        serde_json::from_slice(&original_canonical_manifest).expect("canonical manifest JSON");
    incompatible_canonical.row_order_rule = "unapproved-row-order".to_owned();
    fs::write(
        &canonical_manifest_path,
        serde_json::to_vec_pretty(&incompatible_canonical)
            .expect("serialize incompatible canonical manifest"),
    )
    .expect("write incompatible canonical manifest");
    let mut rebound_stage = stage.clone();
    rebound_stage.canonical_manifest_sha256 = sha256_file(&canonical_manifest_path);
    fs::write(
        &stage_manifest_path,
        serde_json::to_vec_pretty(&rebound_stage).expect("serialize rebound corpus stage"),
    )
    .expect("write rebound corpus stage");
    let error = pipeline
        .open_corpus_stage(&stage_config.name)
        .expect_err("unapproved canonical rules are rejected");
    assert!(error.to_string().contains("canonical manifest"));

    fs::write(&canonical_manifest_path, original_canonical_manifest)
        .expect("restore canonical manifest");
    fs::write(&stage_manifest_path, &original_stage_manifest).expect("restore stage manifest");
    let mut non_prefix_rows = stage_rows;
    non_prefix_rows[..32].copy_from_slice(&outside);
    fs::write(
        pipeline.layout().corpus_stage_rows(&stage_config.name),
        &non_prefix_rows,
    )
    .expect("write non-prefix stage rows");
    let mut non_prefix_stage = stage;
    non_prefix_stage.rows.sha256 = sha256_bytes(&non_prefix_rows);
    fs::write(
        &stage_manifest_path,
        serde_json::to_vec_pretty(&non_prefix_stage).expect("serialize non-prefix stage"),
    )
    .expect("write non-prefix stage manifest");
    let error = pipeline
        .open_corpus_stage(&stage_config.name)
        .expect_err("self-consistent non-prefix stage is rejected");
    assert!(error.to_string().contains("canonical prefix"));
}

fn cosine(left: &[i8], right: &[i8]) -> f32 {
    let dot = left
        .iter()
        .zip(right)
        .map(|(left, right)| i64::from(*left) * i64::from(*right))
        .sum::<i64>();
    let left_norm = left
        .iter()
        .map(|value| f32::from(*value).powi(2))
        .sum::<f32>()
        .sqrt();
    let right_norm = right
        .iter()
        .map(|value| f32::from(*value).powi(2))
        .sum::<f32>()
        .sqrt();
    dot as f32 / (left_norm * right_norm)
}

struct LookupEncoder {
    descriptor: EncoderDescriptor,
    vectors: std::collections::BTreeMap<String, Vec<i8>>,
}

impl LookupEncoder {
    fn new(vectors: &[(&str, [i8; 2])]) -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "test/lookup".to_owned(),
                model_revision: "fixture-v1".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "test".to_owned(),
                runtime_version: "1".to_owned(),
                runtime_sha256: "fixture-runtime".to_owned(),
                execution_provider: "test".to_owned(),
                output_name: "native_int8".to_owned(),
                dimensions: 2,
                max_tokens: 32,
                input_rule: "fixture-raw-text-v1".to_owned(),
                pooling: "fixture".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            vectors: vectors
                .iter()
                .map(|(text, vector)| ((*text).to_owned(), vector.to_vec()))
                .collect(),
        }
    }
}

impl EmbeddingEncoder for LookupEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn encode(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<i8>> {
        let mut encoded = Vec::with_capacity(texts.len() * 2);
        for text in texts {
            let vector =
                self.vectors
                    .get(*text)
                    .ok_or_else(|| oracle_mvp::snapshot::Error::Encoder {
                        operation: "encoding lookup fixture",
                        message: format!("missing vector for `{text}`"),
                    })?;
            encoded.extend(vector);
        }
        Ok(encoded)
    }
}

struct DeterministicEncoder {
    descriptor: EncoderDescriptor,
    batch_sizes: Vec<usize>,
    seen: Vec<String>,
}

impl DeterministicEncoder {
    fn new() -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "test/deterministic".to_owned(),
                model_revision: "fixture-v1".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "test".to_owned(),
                runtime_version: "1".to_owned(),
                runtime_sha256: "fixture-runtime".to_owned(),
                execution_provider: "test".to_owned(),
                output_name: "native_int8".to_owned(),
                dimensions: 4,
                max_tokens: 32,
                input_rule: "fixture-raw-text-v1".to_owned(),
                pooling: "fixture".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            batch_sizes: Vec::new(),
            seen: Vec::new(),
        }
    }
}

impl EmbeddingEncoder for DeterministicEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn encode(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<i8>> {
        self.batch_sizes.push(texts.len());
        let mut vectors = Vec::with_capacity(texts.len() * 4);
        for text in texts {
            self.seen.push((*text).to_owned());
            let sum = text.bytes().fold(0_u8, u8::wrapping_add);
            vectors.extend([
                i8::try_from(text.len().min(127)).unwrap(),
                (sum % 127) as i8,
                text.as_bytes().first().copied().unwrap_or(0).min(127) as i8,
                1,
            ]);
        }
        Ok(vectors)
    }
}

struct CanonicalFixture {
    manifest: CanonicalManifest,
    rows: Vec<u8>,
    aliases: Vec<u8>,
}

fn canonicalize_fixture(events: &[&String]) -> CanonicalFixture {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    write_snapshot(
        pipeline.layout().snapshot(),
        &events
            .iter()
            .map(|event| event.as_str())
            .collect::<Vec<_>>(),
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    let manifest = pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");
    assert_manifest::<CanonicalManifest>(pipeline.layout().canonical_manifest(), &manifest);
    CanonicalFixture {
        rows: fs::read(pipeline.layout().canonical_rows()).expect("canonical rows"),
        aliases: fs::read(pipeline.layout().canonical_aliases()).expect("canonical aliases"),
        manifest,
    }
}

fn signed_note(kind: u32, content: &str, tags: &[[&str; 4]]) -> String {
    signed_note_at(kind, content, tags, 1_700_000_000 + u64::from(kind), 7)
}

fn signed_note_at(
    kind: u32,
    content: &str,
    tags: &[[&str; 4]],
    created_at: u64,
    secret_byte: u8,
) -> String {
    let secret = [secret_byte; 32];
    let mut builder = NoteBuilder::new()
        .kind(kind)
        .content(content)
        .created_at(created_at);
    for tag in tags {
        builder = builder
            .start_tag()
            .tag_str(tag[0])
            .tag_str(tag[1])
            .tag_str(tag[2])
            .tag_str(tag[3]);
    }
    builder
        .sign(&secret)
        .build()
        .expect("signed note")
        .json()
        .expect("note JSON")
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
    let hex = value["id"].as_str().expect("event ID");
    let mut id = [0_u8; 32];
    for (index, byte) in id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&hex[index * 2..index * 2 + 2], 16).expect("hex event ID");
    }
    id
}

fn row_order_key(id: &[u8; 32]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"oracle-mvp/canonical-row-order/v1\0");
    hasher.update(id);
    hasher.finalize().into()
}

fn sha256_file(path: &std::path::Path) -> String {
    sha256_bytes(&fs::read(path).expect("artifact bytes"))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn decode_rows(bytes: &[u8]) -> Vec<[u8; 32]> {
    bytes
        .chunks_exact(32)
        .map(|record| record.try_into().expect("row record"))
        .collect()
}

fn decode_aliases(bytes: &[u8]) -> Vec<([u8; 32], [u8; 32])> {
    bytes
        .chunks_exact(64)
        .map(|record| {
            (
                record[..32].try_into().expect("alias ID"),
                record[32..].try_into().expect("canonical ID"),
            )
        })
        .collect()
}

fn write_snapshot(path: impl AsRef<std::path::Path>, events: &[&str]) {
    let file = File::create(path).expect("snapshot file");
    let encoder =
        zstd::stream::write::Encoder::new(BufWriter::new(file), 1).expect("zstd snapshot encoder");
    let mut writer = encoder.auto_finish();
    for event in events {
        writeln!(writer, "{event}").expect("write snapshot event");
    }
    writer.flush().expect("flush snapshot");
}

fn assert_manifest<T>(path: impl AsRef<std::path::Path>, expected: &T)
where
    T: serde::de::DeserializeOwned + PartialEq + std::fmt::Debug,
{
    let manifest = fs::read(path).expect("manifest file");
    let actual = serde_json::from_slice::<T>(&manifest).expect("manifest JSON");
    assert_eq!(&actual, expected);
}

fn open_ndb(path: impl AsRef<std::path::Path>) -> Ndb {
    Ndb::new(
        path.as_ref().to_str().expect("UTF-8 NostrDB path"),
        &Config::new().set_mapsize(512 * 1024 * 1024),
    )
    .expect("open NostrDB")
}
