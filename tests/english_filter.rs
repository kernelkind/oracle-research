use std::collections::BTreeSet;
use std::fs;

use bech32::{Bech32, Hrp};
use oracle_mvp::english_filter::{classifier_input, select_sampled_event_ids};
use oracle_mvp::english_filter_pilot::{
    BlindRecord, ClassifierDecision, JudgmentRecord, LanguagePrediction, ManualJudgment,
    PredictionRecord, calculate_report,
};

#[test]
fn removes_web_urls_without_merging_surrounding_words() {
    let content = concat!(
        "alpha(https://example.com/a_(b)?q=1#part),beta ",
        "www.example.org:8443/path; gamma example.net/path?x=1#y delta ",
        "https://\u{4f8b}\u{3048}.\u{30c6}\u{30b9}\u{30c8}/\u{9053} omega"
    );

    assert_eq!(classifier_input(content), "alpha beta gamma delta omega");
}

#[test]
fn removes_nested_and_opaque_url_schemes_without_leaving_payload_fragments() {
    let content = concat!(
        "before blob:https://gifbuddy.lol/f024ac63-2161-468c-b2b8-c7df0fd89ef2 ",
        "vmess://eyJ2IjogIjIiLCAiaWQiOiAiNzAyMiJ9== after"
    );

    assert_eq!(classifier_input(content), "before after");
}

#[test]
fn preserves_dotted_code_identifiers_next_to_real_urls() {
    let content = concat!(
        "runtime.OnPerformanceWarningCategory\n",
        "https://developer.mozilla.org/en-US/docs/example"
    );

    assert_eq!(
        classifier_input(content),
        "runtime.OnPerformanceWarningCategory"
    );
}

#[test]
fn removes_every_nip19_entity_in_bare_and_nostr_uri_forms() {
    let npub = encode("npub", &[1; 32]);
    let nsec = encode("nsec", &[2; 32]);
    let note = encode("note", &[3; 32]);
    let nprofile = encode("nprofile", &tlv(&[(0, &[4; 32])]));
    let nevent = encode("nevent", &tlv(&[(0, &[5; 32])]));
    let nrelay = encode("nrelay", &tlv(&[(0, b"wss://relay.example.com")]));
    let naddr = encode(
        "naddr",
        &tlv(&[
            (0, b"oracle"),
            (2, &[6; 32]),
            (3, &30_023_u32.to_be_bytes()),
        ]),
    );
    let content = format!(
        "start ({npub}) {nsec}, {note}; {nprofile}! nostr:{nevent}?relay=wss%3A%2F%2Frelay.example#thread <{nrelay}> NOSTR:{} end",
        naddr.to_uppercase()
    );

    assert_eq!(classifier_input(&content), "start end");
}

#[test]
fn preserves_malformed_nip19_lookalikes_and_ordinary_prefix_words() {
    let valid = encode("npub", &[7; 32]);
    let mut bad_checksum = valid.clone();
    bad_checksum.pop();
    bad_checksum.push(if valid.ends_with('q') { 'p' } else { 'q' });
    let mixed_case = format!("N{}", &valid[1..]);
    let content =
        format!("noteworthy npub1friend {bad_checksum} {mixed_case} nostr:npub1broken remains");

    assert_eq!(classifier_input(&content), content);
}

#[test]
fn preserves_valid_nip19_payloads_embedded_in_larger_tokens() {
    let valid = encode("npub", &[9; 32]);
    let content = format!("prefix{valid} {valid}suffix {valid}_suffix");

    assert_eq!(classifier_input(&content), content);
}

#[test]
fn preserves_checksum_valid_but_structurally_invalid_nip19_values() {
    let wrong_npub_length = encode("npub", &[1; 31]);
    let duplicate_profile_key = encode("nprofile", &tlv(&[(0, &[2; 32]), (0, &[3; 32])]));
    let profile_with_invalid_relay = encode(
        "nprofile",
        &tlv(&[(0, &[4; 32]), (1, b"https://relay.example.com")]),
    );
    let event_with_invalid_author = encode("nevent", &tlv(&[(0, &[5; 32]), (2, &[6; 31])]));
    let address_with_invalid_kind = encode(
        "naddr",
        &tlv(&[(0, b"oracle"), (2, &[7; 32]), (3, &[0; 3])]),
    );
    let relay_with_duplicate_url = encode(
        "nrelay",
        &tlv(&[(0, b"wss://one.example"), (0, b"wss://two.example")]),
    );
    let content = [
        wrong_npub_length,
        duplicate_profile_key,
        profile_with_invalid_relay,
        event_with_invalid_author,
        address_with_invalid_kind,
        relay_with_duplicate_url,
    ]
    .join(" ");

    assert_eq!(classifier_input(&content), content);
}

#[test]
fn url_and_identifier_only_input_becomes_empty() {
    let note = encode("note", &[8; 32]);
    assert_eq!(
        classifier_input(&format!("https://example.com nostr:{note}")),
        ""
    );
}

#[test]
fn uniformly_samples_the_complete_ordered_id_file_deterministically() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let path = temp.path().join("ordered-event-ids.bin");
    let source = (0_u64..10_000).map(event_id).collect::<Vec<[u8; 32]>>();
    fs::write(&path, source.iter().flatten().copied().collect::<Vec<_>>()).expect("ordered IDs");

    let first = select_sampled_event_ids(&path, 1_000, b"crec-59-pilot-v1").expect("first sample");
    let repeated =
        select_sampled_event_ids(&path, 1_000, b"crec-59-pilot-v1").expect("repeated sample");
    let other = select_sampled_event_ids(&path, 1_000, b"different-seed").expect("other sample");

    assert_eq!(first, repeated);
    assert_ne!(first, other);
    assert_eq!(first.len(), 1_000);
    assert_eq!(first.iter().copied().collect::<BTreeSet<_>>().len(), 1_000);
    assert!(first.iter().all(|id| source.contains(id)));
    assert_ne!(first, source[..1_000]);
}

#[test]
fn reports_retained_precision_recall_accuracy_and_ambiguous_rows_separately() {
    let blind = [
        blind_record(1, "a", "English text"),
        blind_record(2, "b", "More English"),
        blind_record(3, "c", "Texto en español"),
        blind_record(4, "d", "Mixed"),
    ];
    let predictions = [
        prediction_record(1, "a", ClassifierDecision::KeepEnglish, 0.99),
        prediction_record(2, "b", ClassifierDecision::Exclude, 0.55),
        prediction_record(3, "c", ClassifierDecision::KeepEnglish, 0.60),
        prediction_record(4, "d", ClassifierDecision::Exclude, 0.40),
    ];
    let judgments = [
        judgment("a", ManualJudgment::English),
        judgment("b", ManualJudgment::English),
        judgment("c", ManualJudgment::PrimarilyNonEnglish),
        judgment("d", ManualJudgment::Ambiguous),
    ];

    let report = calculate_report("manifest", "judgments", &blind, &predictions, &judgments)
        .expect("report");

    assert_eq!(report.sample_size, 4);
    assert_eq!(report.evaluated_rows, 3);
    assert_eq!(report.confusion.true_positive, 1);
    assert_eq!(report.confusion.false_positive, 1);
    assert_eq!(report.confusion.false_negative, 1);
    assert_eq!(report.confusion.true_negative, 0);
    assert_eq!(report.confusion.ambiguous, 1);
    assert_eq!(report.retained_precision.successes, 1);
    assert_eq!(report.retained_precision.total, 2);
    assert_eq!(report.eligible_recall.successes, 1);
    assert_eq!(report.eligible_recall.total, 2);
    assert_eq!(report.overall_accuracy.successes, 1);
    assert_eq!(report.overall_accuracy.total, 3);
    assert_eq!(report.disagreement_event_ids, ["b", "c"]);
}

fn encode(hrp: &str, payload: &[u8]) -> String {
    bech32::encode::<Bech32>(Hrp::parse(hrp).expect("HRP"), payload).expect("bech32")
}

fn tlv(fields: &[(u8, &[u8])]) -> Vec<u8> {
    let mut output = Vec::new();
    for (kind, value) in fields {
        output.push(*kind);
        output.push(u8::try_from(value.len()).expect("TLV length"));
        output.extend_from_slice(value);
    }
    output
}

fn event_id(index: u64) -> [u8; 32] {
    let mut id = [0_u8; 32];
    id[24..].copy_from_slice(&index.to_be_bytes());
    id
}

fn blind_record(ordinal: u32, id: &str, input: &str) -> BlindRecord {
    BlindRecord {
        sample_ordinal: ordinal,
        event_id: id.to_owned(),
        original_content: input.to_owned(),
        classifier_input: input.to_owned(),
    }
}

fn prediction_record(
    ordinal: u32,
    id: &str,
    decision: ClassifierDecision,
    confidence: f32,
) -> PredictionRecord {
    PredictionRecord {
        sample_ordinal: ordinal,
        event_id: id.to_owned(),
        predictions: vec![LanguagePrediction {
            label: "__label__eng_Latn".to_owned(),
            confidence,
        }],
        decision,
    }
}

fn judgment(id: &str, judgment: ManualJudgment) -> JudgmentRecord {
    JudgmentRecord {
        event_id: id.to_owned(),
        judgment,
    }
}
