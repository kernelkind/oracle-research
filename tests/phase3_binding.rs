use std::path::PathBuf;

use oracle_mvp::phase3_binding::Phase3RunnerBinding;
use oracle_mvp::quota_resolution::PriorPresentation;

const LEGACY_BINDING_JSON: &str = r#"{
  "schema_version": 1,
  "corpus_path": "/legacy/corpus.ndb",
  "corpus_identity": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "session_path": "/legacy/phase3-session.json",
  "representation_version": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "geometry_version": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "b16_bits": "3ff0000000000000",
  "h16_bits": "3ff0000000000000",
  "h64_bits": "4000000000000000",
  "h256_bits": "4008000000000000",
  "s16_bits": "3ff0000000000000",
  "s64_bits": "4000000000000000",
  "s256_bits": "4008000000000000",
  "seeds": [
    {
      "event_id": "0101010101010101010101010101010101010101010101010101010101010101",
      "rating": 5
    },
    {
      "event_id": "0202020202020202020202020202020202020202020202020202020202020202",
      "rating": 6
    },
    {
      "event_id": "0303030303030303030303030303030303030303030303030303030303030303",
      "rating": 7
    },
    {
      "event_id": "0404040404040404040404040404040404040404040404040404040404040404",
      "rating": 5
    },
    {
      "event_id": "0505050505050505050505050505050505050505050505050505050505050505",
      "rating": 6
    }
  ]
}"#;

#[test]
fn shared_binding_serializes_byte_compatibly_with_the_legacy_schema() {
    let binding: Phase3RunnerBinding =
        serde_json::from_str(LEGACY_BINDING_JSON).expect("decode legacy runner binding");

    let serialized = serde_json::to_string_pretty(&binding).expect("encode shared runner binding");

    assert_eq!(serialized, LEGACY_BINDING_JSON);
}

#[test]
fn shared_binding_can_relocate_only_the_fresh_corpus_and_session_paths() {
    let binding: Phase3RunnerBinding =
        serde_json::from_str(LEGACY_BINDING_JSON).expect("decode legacy runner binding");
    let fresh_corpus = PathBuf::from("/fresh/corpus.ndb");
    let fresh_session = PathBuf::from("/fresh/phase3-session.json");

    let config = binding
        .runner_config_at(&fresh_corpus, &fresh_session)
        .expect("build relocated runner config");

    assert_eq!(config.corpus_path, fresh_corpus);
    assert_eq!(config.session_path, fresh_session);
    assert_eq!(
        config.corpus_identity,
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    );
    assert_eq!(
        config.compact_settings.representation_version(),
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    );
    assert_eq!(
        config.rbf_settings.representation_version(),
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    );
    assert_eq!(
        config.b16.representation_version(),
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    );
    assert_eq!(
        config
            .seeds
            .iter()
            .map(|seed| (seed.event_id(), seed.rating()))
            .collect::<Vec<_>>(),
        vec![
            ([1_u8; 32], 5),
            ([2_u8; 32], 6),
            ([3_u8; 32], 7),
            ([4_u8; 32], 5),
            ([5_u8; 32], 6),
        ]
    );
}

#[test]
fn shared_binding_carries_screening_no_repeat_state_separately_from_seeds() {
    let mut json: serde_json::Value =
        serde_json::from_str(LEGACY_BINDING_JSON).expect("decode binding JSON");
    json["initial_presentations"] = serde_json::json!([
        {
            "event_id": "0606060606060606060606060606060606060606060606060606060606060606",
            "state": { "kind": "eligible_unrated" }
        },
        {
            "event_id": "0707070707070707070707070707070707070707070707070707070707070707",
            "state": { "kind": "wrong_language" }
        }
    ]);
    let binding: Phase3RunnerBinding =
        serde_json::from_value(json).expect("decode binding with screening ledger");

    assert_eq!(binding.seeds().len(), 5);
    assert_eq!(
        binding
            .initial_presentations()
            .expect("decode screening ledger"),
        std::collections::BTreeMap::from([
            ([6_u8; 32], PriorPresentation::EligibleUnrated),
            ([7_u8; 32], PriorPresentation::WrongLanguage),
        ])
    );
}
