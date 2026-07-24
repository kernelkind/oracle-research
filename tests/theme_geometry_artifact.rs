use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::theme_geometry_artifact::{
    BlindSourceNote, build_blind_packet, derive_analysis_label_set,
};
use oracle_mvp::theme_geometry_diagnostic::{Theme, ThemeLabelSet};

#[test]
fn blind_packet_conceals_phase4_identity_and_order() {
    let notes = vec![
        BlindSourceNote::new(1, [0x11; 32], "first note".to_owned())
            .expect("construct first source note"),
        BlindSourceNote::new(2, [0x22; 32], "second note".to_owned())
            .expect("construct second source note"),
        BlindSourceNote::new(3, [0x33; 32], "third note".to_owned())
            .expect("construct third source note"),
    ];

    let packet = build_blind_packet(notes, "blind-packet-test-v1").expect("build blind packet");
    let encoded_blind =
        serde_json::to_string(packet.blind_records()).expect("encode blind records");

    assert!(!encoded_blind.contains("presentation_ordinal"));
    assert!(!encoded_blind.contains(&"11".repeat(32)));
    assert!(!encoded_blind.contains(&"22".repeat(32)));
    assert!(!encoded_blind.contains(&"33".repeat(32)));
    assert_eq!(packet.blind_records().len(), 3);
    assert_eq!(packet.key_records().len(), 3);
    assert!(
        packet
            .blind_records()
            .iter()
            .zip(packet.key_records())
            .all(|(blind, key)| blind.record_id() == key.record_id())
    );
}

#[test]
fn analysis_derives_one_cryptocurrency_family_from_raw_labels() {
    let raw = ThemeLabelSet::new(
        "labeler-a",
        BTreeMap::from([
            ("T001".to_owned(), BTreeSet::from([Theme::Bitcoin])),
            ("T002".to_owned(), BTreeSet::from([Theme::Monero])),
            (
                "T003".to_owned(),
                BTreeSet::from([Theme::Bitcoin, Theme::Monero, Theme::Nostr]),
            ),
        ]),
    )
    .expect("construct raw labels");

    let analyzed = derive_analysis_label_set(&raw).expect("derive analysis families");

    assert_eq!(
        analyzed.labels()["T001"],
        BTreeSet::from([Theme::Cryptocurrency])
    );
    assert_eq!(
        analyzed.labels()["T002"],
        BTreeSet::from([Theme::Cryptocurrency])
    );
    assert_eq!(
        analyzed.labels()["T003"],
        BTreeSet::from([Theme::Cryptocurrency, Theme::Nostr])
    );
}
