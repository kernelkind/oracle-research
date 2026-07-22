use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::representation::{
    RepresentationBuildConfig, RepresentationBuildResult, RepresentationDescriptor,
    RepresentationEncoder, build_representation_shards,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::representation_geometry::{
    derive_representation_geometry, open_representation_geometry, verify_representation_geometry,
};
use oracle_mvp::snapshot::{Error, Result};
use serde::Deserialize;
use sha2::{Digest, Sha256};

const ROWS: usize = 513;
const ANCHORS: usize = 512;
const DERIVATION_VERSION: &str = "exact-direct-f64-chord-geometry-v1";
const ANCHOR_DOMAIN: &[u8] = b"oracle-mvp-representation-geometry-anchor-v1\0";

#[test]
fn derives_replayable_geometry_without_mutating_the_representation() {
    let fixture = Fixture::new();
    let (representation, built) =
        fixture.build_representation("representation", ROWS as u64, vec![0]);
    assert!(built.manifest.complete);
    assert_eq!(built.manifest.total_rows, ROWS as u64);

    let pristine_representation = snapshot_tree(&representation);
    let first_output = fixture.temp.path().join("geometry-a");
    derive_representation_geometry(&fixture.ordered_path, &representation, &first_output)
        .expect("derive exact representation geometry");
    assert_eq!(snapshot_tree(&representation), pristine_representation);
    open_representation_geometry(&fixture.ordered_path, &representation, &first_output)
        .expect("open and verify published geometry");
    verify_representation_geometry(&fixture.ordered_path, &representation, &first_output)
        .expect("deeply replay and verify published geometry");

    let manifest: GeometryManifest = read_json(&first_output.join("manifest.json"));
    assert_eq!(manifest.schema_version, 1);
    assert_eq!(manifest.derivation_version, DERIVATION_VERSION);
    assert!(manifest.rules.is_object());
    assert_eq!(
        manifest.rules["b16"],
        "order-direct-squared-distance-then-event-id-report-square-root-v1"
    );
    assert_eq!(manifest.targets, [16, 64, 256]);
    assert_eq!(
        manifest.representation.representation_version,
        built.representation_version
    );
    assert_eq!(
        manifest.representation.corpus_data_sha256,
        built.manifest.corpus_data_sha256
    );
    assert_eq!(
        manifest.representation.ordered_event_ids_sha256,
        built.manifest.ordered_event_ids_sha256
    );
    assert_eq!(manifest.representation.total_rows, ROWS as u64);
    assert_eq!(manifest.representation.completed_rows, ROWS as u64);
    assert_eq!(manifest.representation.dimensions, 2);
    assert!(manifest.representation.complete);
    assert_eq!(
        manifest.representation.descriptor_sha256,
        built.manifest.descriptor_sha256
    );
    assert_eq!(
        manifest.representation.build_identity_sha256,
        built.manifest.build_identity_sha256
    );
    assert_eq!(
        manifest.representation.index_manifest_sha256,
        built.manifest.index_manifest_sha256
    );
    assert_eq!(
        manifest.representation.matrix_format,
        built.manifest.matrix_format
    );
    assert_eq!(manifest.representation.vector_shards.len(), 1);
    let shard = &manifest.representation.vector_shards[0];
    let built_shard = &built.manifest.shards[0];
    assert_eq!(shard.ordinal, built_shard.ordinal);
    assert_eq!(shard.start_row, built_shard.start_row);
    assert_eq!(shard.rows, built_shard.rows);
    assert_eq!(shard.file, built_shard.vectors.file);
    assert_eq!(shard.bytes, built_shard.vectors.bytes);
    assert_eq!(shard.sha256, built_shard.vectors.sha256);
    assert_eq!(manifest.anchor_measurements.records, ANCHORS as u64);
    assert_eq!(
        manifest.anchor_measurements.file,
        "anchor-measurements.json"
    );

    let measurement_path = first_output.join(&manifest.anchor_measurements.file);
    let measurement_bytes = fs::read(&measurement_path).expect("read anchor measurements");
    assert_eq!(
        manifest.anchor_measurements.bytes,
        measurement_bytes.len() as u64
    );
    assert_eq!(
        manifest.anchor_measurements.sha256,
        hash_bytes(&measurement_bytes)
    );
    let measurements: Vec<AnchorMeasurement> =
        serde_json::from_slice(&measurement_bytes).expect("decode anchor measurements");
    assert_eq!(measurements.len(), ANCHORS);

    let expected_anchors = expected_anchors(&built.representation_version, &fixture.ids);
    let vectors = (0..ROWS).map(document_vector).collect::<Vec<_>>();
    for (ordinal, (measurement, expected)) in measurements.iter().zip(&expected_anchors).enumerate()
    {
        assert_eq!(measurement.anchor_ordinal, ordinal as u64);
        assert_eq!(
            measurement.selection_sha256,
            hex(&expected.selection_sha256)
        );
        assert_eq!(measurement.row, expected.row as u64);
        assert_eq!(measurement.event_id, hex(&expected.event_id));

        let mut neighbors = fixture
            .ids
            .iter()
            .enumerate()
            .filter(|(row, _)| *row != expected.row)
            .map(|(row, event_id)| Neighbor {
                event_id: *event_id,
                distance: squared_chord_distance(&vectors[expected.row], &vectors[row]).sqrt(),
            })
            .collect::<Vec<_>>();
        neighbors.sort_unstable_by(|left, right| {
            left.distance
                .total_cmp(&right.distance)
                .then_with(|| left.event_id.cmp(&right.event_id))
        });
        let sixteenth = &neighbors[15];
        assert_ne!(measurement.event_id, measurement.b16_neighbor_event_id);
        assert_eq!(measurement.b16_neighbor_event_id, hex(&sixteenth.event_id));
        assert_eq!(
            parse_bits(&measurement.b16.bits).to_bits(),
            sixteenth.distance.to_bits()
        );

        let squared_distances = fixture
            .ids
            .iter()
            .enumerate()
            .filter(|(row, _)| *row != expected.row)
            .map(|(row, _)| squared_chord_distance(&vectors[expected.row], &vectors[row]))
            .collect::<Vec<_>>();
        let distances = squared_distances
            .iter()
            .map(|squared| squared.sqrt())
            .collect::<Vec<_>>();
        for (target, bits) in [
            (16.0, &measurement.h16.bits),
            (64.0, &measurement.h64.bits),
            (256.0, &measurement.h256.bits),
        ] {
            assert_minimum_scale(bits, target, |scale| compact_mass(&distances, scale));
        }
        for (target, bits) in [
            (16.0, &measurement.s16.bits),
            (64.0, &measurement.s64.bits),
            (256.0, &measurement.s256.bits),
        ] {
            assert_minimum_scale(bits, target, |scale| rbf_mass(&squared_distances, scale));
        }
    }

    assert_eq!(
        manifest.values.b16.bits,
        median_bits(&measurements, |entry| &entry.b16.bits)
    );
    assert_eq!(
        manifest.values.h16.bits,
        median_bits(&measurements, |entry| &entry.h16.bits)
    );
    assert_eq!(
        manifest.values.h64.bits,
        median_bits(&measurements, |entry| &entry.h64.bits)
    );
    assert_eq!(
        manifest.values.h256.bits,
        median_bits(&measurements, |entry| &entry.h256.bits)
    );
    assert_eq!(
        manifest.values.s16.bits,
        median_bits(&measurements, |entry| &entry.s16.bits)
    );
    assert_eq!(
        manifest.values.s64.bits,
        median_bits(&measurements, |entry| &entry.s64.bits)
    );
    assert_eq!(
        manifest.values.s256.bits,
        median_bits(&measurements, |entry| &entry.s256.bits)
    );

    let first_manifest = fs::read(first_output.join("manifest.json")).expect("read first manifest");
    derive_representation_geometry(&fixture.ordered_path, &representation, &first_output)
        .expect("reuse and verify existing exact geometry");
    assert_eq!(
        fs::read(first_output.join("manifest.json")).expect("read replay manifest"),
        first_manifest
    );
    assert_eq!(
        fs::read(first_output.join("anchor-measurements.json")).expect("read replay measurements"),
        measurement_bytes
    );
    assert_eq!(snapshot_tree(&representation), pristine_representation);
    assert!(
        fs::read_dir(fixture.temp.path())
            .expect("read artifact parent")
            .all(|entry| {
                !entry
                    .expect("artifact entry")
                    .file_name()
                    .to_string_lossy()
                    .starts_with(".geometry-")
            }),
        "successful atomic publication must leave no geometry stage"
    );
}

#[test]
fn rejects_output_inside_representation_without_creating_it() {
    let fixture = Fixture::new();
    let (representation, _) = fixture.build_representation("representation", ROWS as u64, vec![0]);
    let before = snapshot_tree(&representation);
    let output = representation.join("nested/geometry");

    let error = derive_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect_err("output inside the representation must be rejected");

    assert_invariant_contains(error, "outside the representation directory");
    assert!(!output.exists());
    assert!(!representation.join("nested").exists());
    assert_eq!(snapshot_tree(&representation), before);
}

#[test]
fn rejects_corrupted_measurements() {
    let fixture = Fixture::new();
    let (representation, _) = fixture.build_representation("representation", ROWS as u64, vec![0]);
    let output = fixture.temp.path().join("geometry");
    derive_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect("derive fixture geometry");
    let measurements = output.join("anchor-measurements.json");
    let mut corrupted = fs::read(&measurements).expect("read measurements to corrupt");
    corrupted.push(b' ');
    fs::write(&measurements, corrupted).expect("corrupt measurements");

    let error = open_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect_err("corrupted measurements must be rejected");

    assert_invariant_contains(error, "measurement file does not match its manifest");
}

#[test]
fn rejects_a_self_consistent_measurement_with_an_unknown_b16_neighbor() {
    let fixture = Fixture::new();
    let (representation, _) = fixture.build_representation("representation", ROWS as u64, vec![0]);
    let output = fixture.temp.path().join("geometry");
    derive_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect("derive fixture geometry");
    let measurements_path = output.join("anchor-measurements.json");
    let mut measurements: serde_json::Value = read_json(&measurements_path);
    measurements[0]["b16_neighbor_event_id"] = serde_json::Value::String("f".repeat(64));
    write_json(&measurements_path, &measurements);
    let measurement_bytes = fs::read(&measurements_path).expect("read rewritten measurements");
    let manifest_path = output.join("manifest.json");
    let mut manifest: serde_json::Value = read_json(&manifest_path);
    manifest["anchor_measurements"]["bytes"] = measurement_bytes.len().into();
    manifest["anchor_measurements"]["sha256"] = hash_bytes(&measurement_bytes).into();
    write_json(&manifest_path, &manifest);

    let error = open_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect_err("an unknown B16 neighbor must be rejected");

    assert_invariant_contains(error, "B16 neighbor is not in the representation");
}

#[test]
fn deep_verification_rejects_a_self_consistent_but_incorrect_b16_neighbor() {
    let fixture = Fixture::new();
    let (representation, _) = fixture.build_representation("representation", ROWS as u64, vec![0]);
    let output = fixture.temp.path().join("geometry");
    derive_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect("derive fixture geometry");
    let measurements_path = output.join("anchor-measurements.json");
    let mut measurements: serde_json::Value = read_json(&measurements_path);
    let anchor = measurements[0]["event_id"]
        .as_str()
        .expect("first anchor event ID");
    let actual_neighbor = measurements[0]["b16_neighbor_event_id"]
        .as_str()
        .expect("first anchor B16 neighbor");
    let replacement = measurements
        .as_array()
        .expect("measurement array")
        .iter()
        .filter_map(|measurement| measurement["event_id"].as_str())
        .find(|event_id| *event_id != anchor && *event_id != actual_neighbor)
        .expect("different represented event ID")
        .to_owned();
    measurements[0]["b16_neighbor_event_id"] = serde_json::Value::String(replacement);
    write_json(&measurements_path, &measurements);
    let measurement_bytes = fs::read(&measurements_path).expect("read rewritten measurements");
    let manifest_path = output.join("manifest.json");
    let mut manifest: serde_json::Value = read_json(&manifest_path);
    manifest["anchor_measurements"]["bytes"] = measurement_bytes.len().into();
    manifest["anchor_measurements"]["sha256"] = hash_bytes(&measurement_bytes).into();
    write_json(&manifest_path, &manifest);

    open_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect("structurally self-consistent geometry should open");
    let error = verify_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect_err("deep replay must reject an incorrect known B16 neighbor");

    assert_invariant_contains(error, "deep verification did not reproduce");
    assert!(
        !fixture
            .temp
            .path()
            .join(".geometry.verify.partial")
            .exists()
    );
}

#[test]
fn rejects_incomplete_and_unsealed_representations() {
    let fixture = Fixture::new();
    let (representation, built) =
        fixture.build_representation("incomplete-representation", 257, vec![0]);
    assert!(!built.manifest.complete);

    let incomplete_output = fixture.temp.path().join("incomplete-geometry");
    let error =
        derive_representation_geometry(&fixture.ordered_path, &representation, &incomplete_output)
            .expect_err("incomplete representation must be rejected");
    assert_invariant_contains(error, "requires a complete representation");
    assert_unpublished(&incomplete_output);

    fs::remove_file(representation.join("verification.json"))
        .expect("remove representation verification receipt");
    let unsealed_output = fixture.temp.path().join("unsealed-geometry");
    let error =
        derive_representation_geometry(&fixture.ordered_path, &representation, &unsealed_output)
            .expect_err("unsealed representation must be rejected");
    assert_invariant_contains(error, "representation is not sealed");
    assert_unpublished(&unsealed_output);
}

#[test]
fn derivation_failure_removes_target_and_partial_stage() {
    let fixture = Fixture::new();
    let representation = fixture.build_repeated_representation("repeated-representation");
    let output = fixture.temp.path().join("failed-geometry");

    let error = derive_representation_geometry(&fixture.ordered_path, &representation, &output)
        .expect_err("degenerate zero-distance geometry must fail derivation");

    assert_invariant_contains(error, "already reached at zero bandwidth");
    assert_unpublished(&output);
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GeometryManifest {
    schema_version: u32,
    derivation_version: String,
    representation: RepresentationBinding,
    rules: serde_json::Value,
    targets: [u64; 3],
    anchor_measurements: FileIdentity,
    values: GeometryValues,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RepresentationBinding {
    representation_version: String,
    corpus_data_sha256: String,
    ordered_event_ids_sha256: String,
    descriptor_sha256: String,
    build_identity_sha256: String,
    index_manifest_sha256: String,
    matrix_format: String,
    total_rows: u64,
    completed_rows: u64,
    dimensions: u32,
    complete: bool,
    vector_shards: Vec<VectorShardBinding>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct VectorShardBinding {
    ordinal: u32,
    start_row: u64,
    rows: u64,
    file: String,
    bytes: u64,
    sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FileIdentity {
    file: String,
    bytes: u64,
    records: u64,
    sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GeometryValues {
    b16: F64Bits,
    h16: F64Bits,
    h64: F64Bits,
    h256: F64Bits,
    s16: F64Bits,
    s64: F64Bits,
    s256: F64Bits,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct F64Bits {
    bits: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct AnchorMeasurement {
    anchor_ordinal: u64,
    selection_sha256: String,
    row: u64,
    event_id: String,
    b16_neighbor_event_id: String,
    b16: F64Bits,
    h16: F64Bits,
    h64: F64Bits,
    h256: F64Bits,
    s16: F64Bits,
    s64: F64Bits,
    s256: F64Bits,
}

struct ExpectedAnchor {
    selection_sha256: [u8; 32],
    row: usize,
    event_id: [u8; 32],
}

struct Neighbor {
    event_id: [u8; 32],
    distance: f64,
}

fn expected_anchors(representation_version: &str, ids: &[[u8; 32]]) -> Vec<ExpectedAnchor> {
    let mut anchors = ids
        .iter()
        .enumerate()
        .map(|(row, event_id)| {
            let mut hasher = Sha256::new();
            hasher.update(ANCHOR_DOMAIN);
            hasher.update(
                u64::try_from(representation_version.len())
                    .expect("version length")
                    .to_le_bytes(),
            );
            hasher.update(representation_version.as_bytes());
            hasher.update(event_id);
            ExpectedAnchor {
                selection_sha256: hasher.finalize().into(),
                row,
                event_id: *event_id,
            }
        })
        .collect::<Vec<_>>();
    anchors.sort_unstable_by(|left, right| {
        left.selection_sha256
            .cmp(&right.selection_sha256)
            .then_with(|| left.event_id.cmp(&right.event_id))
    });
    anchors.truncate(ANCHORS);
    anchors
}

fn assert_minimum_scale(bits: &str, target: f64, mass: impl Fn(f64) -> f64) {
    let scale = parse_bits(bits);
    assert!(scale.is_finite() && scale > 0.0, "invalid scale {scale}");
    assert!(
        mass(scale) >= target,
        "scale {scale} does not reach mass {target}"
    );
    let previous = f64::from_bits(scale.to_bits() - 1);
    assert!(
        mass(previous) < target,
        "scale {scale} is not the smallest f64 reaching mass {target}"
    );
}

fn compact_mass(distances: &[f64], radius: f64) -> f64 {
    distances
        .iter()
        .filter(|distance| **distance < radius)
        .map(|distance| (1.0 - (distance / radius).powi(3)).powi(3))
        .sum()
}

fn rbf_mass(squared_distances: &[f64], scale: f64) -> f64 {
    let denominator = 2.0 * scale * scale;
    squared_distances
        .iter()
        .map(|squared| (-squared / denominator).exp())
        .sum()
}

fn squared_chord_distance(left: &[f32], right: &[f32]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(left, right)| {
            let difference = f64::from(*left) - f64::from(*right);
            difference * difference
        })
        .sum()
}

fn median_bits(
    measurements: &[AnchorMeasurement],
    value: impl Fn(&AnchorMeasurement) -> &str,
) -> String {
    let mut values = measurements
        .iter()
        .map(|measurement| parse_bits(value(measurement)))
        .collect::<Vec<_>>();
    values.sort_unstable_by(f64::total_cmp);
    let median = values[255] / 2.0 + values[256] / 2.0;
    format!("{:016x}", median.to_bits())
}

fn parse_bits(bits: &str) -> f64 {
    assert_eq!(
        bits.len(),
        16,
        "f64 bit patterns use 16 lowercase hex digits"
    );
    assert!(
        bits.bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
        "f64 bit patterns use lowercase hex"
    );
    f64::from_bits(u64::from_str_radix(bits, 16).expect("f64 bits"))
}

fn snapshot_tree(root: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    fn walk(root: &Path, directory: &Path, output: &mut Vec<(PathBuf, Vec<u8>)>) {
        let mut entries = fs::read_dir(directory)
            .expect("read artifact directory")
            .collect::<std::io::Result<Vec<_>>>()
            .expect("artifact entries");
        entries.sort_unstable_by_key(|entry| entry.file_name());
        for entry in entries {
            let path = entry.path();
            if path.is_dir() {
                walk(root, &path, output);
            } else {
                output.push((
                    path.strip_prefix(root)
                        .expect("relative artifact path")
                        .to_owned(),
                    fs::read(&path).expect("read artifact file"),
                ));
            }
        }
    }

    let mut output = Vec::new();
    walk(root, root, &mut output);
    output
}

fn assert_invariant_contains(error: Error, expected: &str) {
    match error {
        Error::Invariant(message) => assert!(
            message.contains(expected),
            "expected invariant containing `{expected}`, got `{message}`"
        ),
        other => panic!("expected invariant containing `{expected}`, got {other}"),
    }
}

fn assert_unpublished(output: &Path) {
    let name = output.file_name().expect("geometry output file name");
    let partial = output.with_file_name(format!(".{}.partial", name.to_string_lossy()));
    assert!(!output.exists(), "failed derivation published its target");
    assert!(
        !partial.exists(),
        "failed derivation left its partial stage"
    );
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> T {
    let mut bytes = Vec::new();
    File::open(path)
        .and_then(|mut file| file.read_to_end(&mut bytes))
        .expect("read JSON artifact");
    serde_json::from_slice(&bytes).expect("decode JSON artifact")
}

fn write_json(path: &Path, value: &serde_json::Value) {
    let mut encoded = serde_json::to_vec_pretty(value).expect("encode JSON artifact");
    encoded.push(b'\n');
    fs::write(path, encoded).expect("write JSON artifact");
}

fn hash_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

struct Fixture {
    temp: tempfile::TempDir,
    ndb_path: PathBuf,
    ordered_path: PathBuf,
    token_audit_path: PathBuf,
    ids: Vec<[u8; 32]>,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let ndb_path = temp.path().join("corpus.ndb");
        let ndb = Ndb::new(
            ndb_path.to_str().expect("UTF-8 NDB path"),
            &Config::new().set_mapsize(512 * 1024 * 1024),
        )
        .expect("open fixture NDB");
        let events = (0..ROWS)
            .map(|index| signed_event(&format!("note-{index}"), index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit fixture event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);

        let ids = events
            .iter()
            .map(|event| event_id(event))
            .collect::<Vec<_>>();
        let ordered_path = temp.path().join("ordered-event-ids.bin");
        write_ids(&ordered_path, &ids);
        let token_audit_path = temp.path().join("token-audit");
        let mut counter = FixtureLengthCounter {
            descriptor: fixture_descriptor(),
        };
        audit_ordered_gte_tokens(
            &ndb_path,
            &ordered_path,
            &token_audit_path,
            &OrderedGteTokenAuditConfig {
                batch_size: 64,
                shard_rows: ROWS as u64,
            },
            &mut counter,
        )
        .expect("audit fixture token lengths");
        Self {
            temp,
            ndb_path,
            ordered_path,
            token_audit_path,
            ids,
        }
    }

    fn build_representation(
        &self,
        name: &str,
        shard_rows: u64,
        shard_ordinals: Vec<u32>,
    ) -> (PathBuf, RepresentationBuildResult) {
        let output = self.temp.path().join(name);
        let mut encoder = FixtureEncoder {
            descriptor: fixture_descriptor(),
        };
        let result = build_representation_shards(
            &self.ndb_path,
            &self.ordered_path,
            &output,
            &self.build_config(name, shard_rows, shard_ordinals),
            &mut encoder,
        )
        .expect("build and seal fixture representation");
        (output, result)
    }

    fn build_repeated_representation(&self, name: &str) -> PathBuf {
        let output = self.temp.path().join(name);
        let mut encoder = RepeatedFixtureEncoder {
            descriptor: fixture_descriptor(),
        };
        build_representation_shards(
            &self.ndb_path,
            &self.ordered_path,
            &output,
            &self.build_config(name, ROWS as u64, vec![0]),
            &mut encoder,
        )
        .expect("build and seal repeated-vector representation");
        output
    }

    fn build_config(
        &self,
        name: &str,
        shard_rows: u64,
        shard_ordinals: Vec<u32>,
    ) -> RepresentationBuildConfig {
        let batch_plan_path = self.temp.path().join(format!("{name}-batch-plan"));
        create_representation_batch_plan(
            &self.ordered_path,
            &self.token_audit_path,
            &batch_plan_path,
            &RepresentationBatchPlanConfig {
                shard_rows,
                batch_rows: 64,
            },
        )
        .expect("create fixture batch plan");
        RepresentationBuildConfig {
            token_audit_path: self.token_audit_path.clone(),
            batch_plan_path,
            shard_ordinals,
        }
    }
}

struct FixtureLengthCounter {
    descriptor: RepresentationDescriptor,
}

impl OrderedGteTokenCounter for FixtureLengthCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, _role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        Ok(vec![1; texts.len()])
    }
}

struct FixtureEncoder {
    descriptor: RepresentationDescriptor,
}

struct RepeatedFixtureEncoder {
    descriptor: RepresentationDescriptor,
}

impl RepresentationEncoder for RepeatedFixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        Ok(texts.iter().flat_map(|_| [1.0_f32, 0.0_f32]).collect())
    }

    fn encode_queries(&mut self, _texts: &[&str]) -> Result<Vec<f32>> {
        Err(Error::Encoder {
            operation: "encode query",
            message: "geometry fixture never query-encodes".to_owned(),
        })
    }
}

impl RepresentationEncoder for FixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        let mut vectors = Vec::with_capacity(texts.len() * 2);
        for text in texts {
            let index = note_index(text)?;
            vectors.extend(document_vector(index));
        }
        Ok(vectors)
    }

    fn encode_queries(&mut self, _texts: &[&str]) -> Result<Vec<f32>> {
        Err(Error::Encoder {
            operation: "encode query",
            message: "geometry fixture never query-encodes".to_owned(),
        })
    }
}

fn fixture_descriptor() -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/geometry".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: "2".repeat(64),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:5".to_owned() + &"5".repeat(63),
        torch_version: "fixture".to_owned(),
        transformers_version: "fixture".to_owned(),
        cuda_version: "fixture".to_owned(),
        execution_device: "cpu".to_owned(),
        dimensions: 2,
        model_token_ceiling: 32_768,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture-query-instruction".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn document_vector(index: usize) -> Vec<f32> {
    let angle = std::f64::consts::TAU * index as f64 / ROWS as f64;
    vec![angle.cos() as f32, angle.sin() as f32]
}

fn note_index(text: &str) -> Result<usize> {
    text.strip_prefix("note-")
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|index| *index < ROWS)
        .ok_or_else(|| Error::Invariant("unexpected fixture note".to_owned()))
}

fn signed_event(content: &str, offset: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + offset)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign fixture event")
        .json()
        .expect("fixture event JSON")
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let transaction = Transaction::new(ndb).expect("read fixture transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count fixture events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "NDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("fixture event value");
    let encoded = value["id"].as_str().expect("fixture event ID");
    let mut output = [0_u8; 32];
    for (index, chunk) in encoded.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_hex(chunk[0]) << 4) | decode_hex(chunk[1]);
    }
    output
}

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn write_ids(path: &Path, ids: &[[u8; 32]]) {
    let mut file = File::create(path).expect("create ordered ID file");
    for id in ids {
        file.write_all(id).expect("write ordered event ID");
    }
    file.sync_all().expect("sync ordered event IDs");
}
