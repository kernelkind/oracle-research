//! Deterministic public geometry derived from one sealed FP32 representation.

use std::cmp::Ordering;
use std::collections::{BTreeSet, BinaryHeap};
use std::ffi::OsString;
use std::fs::{self, File, OpenOptions};
use std::path::{Component, Path, PathBuf};
use std::thread;

use memmap2::{MmapMut, MmapOptions};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::artifact::hash_file;
use crate::representation::{EventId, RepresentationStore, open_verified_representation};
use crate::snapshot::{Error, Result, io_error, read_manifest, require_file, write_manifest};

const SCHEMA_VERSION: u32 = 1;
const ANCHOR_COUNT: usize = 512;
const TARGETS: [u64; 3] = [16, 64, 256];
const MEASUREMENTS_FILE: &str = "anchor-measurements.json";
const MANIFEST_FILE: &str = "manifest.json";
const DISTANCE_SCRATCH_FILE: &str = ".squared-distances.f64.tmp";
const VECTOR_BLOCK_ROWS: usize = 4_096;
const INITIAL_LOCAL_NEIGHBORS: usize = 4_096;

/// Frozen implementation identity for this one-time public diagnostic.
pub const REPRESENTATION_GEOMETRY_DERIVATION_VERSION: &str = "exact-direct-f64-chord-geometry-v1";
/// Domain separating public-anchor hashes from every other deterministic hash.
pub const REPRESENTATION_GEOMETRY_ANCHOR_DOMAIN: &[u8] =
    b"oracle-mvp-representation-geometry-anchor-v1\0";

const ANCHOR_SELECTION_RULE: &str =
    "smallest-512-sha256-domain-length-prefixed-version-event-id-v1";
const DISTANCE_RULE: &str =
    "stored-f32-to-f64-coordinate-difference-square-sum-in-dimension-order-v1";
const B16_RULE: &str = "order-direct-squared-distance-then-event-id-report-square-root-v1";
const COMPACT_KERNEL_RULE: &str = "tricube-effective-mass-strict-radius-v1";
const RBF_KERNEL_RULE: &str = "gaussian-effective-mass-all-other-rows-v1";
const ROOT_RULE: &str = "smallest-positive-f64-reaching-row-order-mass-v1";
const MEDIAN_RULE: &str = "total-order-middle-255-half-plus-middle-256-half-v1";

/// One authoritative finite `f64`, serialized without decimal round-tripping.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct F64Bits {
    /// Lowercase, sixteen-digit IEEE-754 bit pattern.
    pub bits: String,
}

impl F64Bits {
    fn new(value: f64, label: &str, allow_zero: bool) -> Result<Self> {
        if !value.is_finite() || value < 0.0 || (!allow_zero && value == 0.0) {
            return Err(Error::Invariant(format!(
                "geometry {label} must be {}finite",
                if allow_zero {
                    "nonnegative and "
                } else {
                    "positive and "
                }
            )));
        }
        Ok(Self {
            bits: format!("{:016x}", value.to_bits()),
        })
    }

    /// Decode and validate the authoritative bit pattern.
    pub fn value(&self) -> Result<f64> {
        if self.bits.len() != 16
            || !self
                .bits
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(Error::Invariant(
                "geometry f64 bits must be sixteen lowercase hexadecimal digits".to_owned(),
            ));
        }
        let bits = u64::from_str_radix(&self.bits, 16)
            .map_err(|_| Error::Invariant("geometry f64 bits are invalid".to_owned()))?;
        Ok(f64::from_bits(bits))
    }
}

/// Exact identity of one vector shard consumed by the derivation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryVectorShardBinding {
    pub ordinal: u32,
    pub start_row: u64,
    pub rows: u64,
    pub file: String,
    pub bytes: u64,
    pub sha256: String,
}

/// Complete representation identity to which the geometry belongs.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryRepresentationBinding {
    pub representation_version: String,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub descriptor_sha256: String,
    pub build_identity_sha256: String,
    pub index_manifest_sha256: String,
    pub matrix_format: String,
    pub total_rows: u64,
    pub completed_rows: u64,
    pub dimensions: u32,
    pub complete: bool,
    pub vector_shards: Vec<GeometryVectorShardBinding>,
}

impl GeometryRepresentationBinding {
    fn from_store(store: &RepresentationStore) -> Self {
        let manifest = store.manifest();
        Self {
            representation_version: store.representation_version().to_owned(),
            corpus_data_sha256: manifest.corpus_data_sha256.clone(),
            ordered_event_ids_sha256: manifest.ordered_event_ids_sha256.clone(),
            descriptor_sha256: manifest.descriptor_sha256.clone(),
            build_identity_sha256: manifest.build_identity_sha256.clone(),
            index_manifest_sha256: manifest.index_manifest_sha256.clone(),
            matrix_format: manifest.matrix_format.clone(),
            total_rows: manifest.total_rows,
            completed_rows: manifest.completed_rows,
            dimensions: manifest.descriptor.dimensions,
            complete: manifest.complete,
            vector_shards: manifest
                .shards
                .iter()
                .map(|shard| GeometryVectorShardBinding {
                    ordinal: shard.ordinal,
                    start_row: shard.start_row,
                    rows: shard.rows,
                    file: shard.vectors.file.clone(),
                    bytes: shard.vectors.bytes,
                    sha256: shard.vectors.sha256.clone(),
                })
                .collect(),
        }
    }
}

/// Frozen rules needed to interpret or reproduce the measurements.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryRules {
    pub anchor_selection: String,
    pub distance: String,
    pub b16: String,
    pub compact_kernel: String,
    pub rbf_kernel: String,
    pub root: String,
    pub median: String,
}

impl Default for GeometryRules {
    fn default() -> Self {
        Self {
            anchor_selection: ANCHOR_SELECTION_RULE.to_owned(),
            distance: DISTANCE_RULE.to_owned(),
            b16: B16_RULE.to_owned(),
            compact_kernel: COMPACT_KERNEL_RULE.to_owned(),
            rbf_kernel: RBF_KERNEL_RULE.to_owned(),
            root: ROOT_RULE.to_owned(),
            median: MEDIAN_RULE.to_owned(),
        }
    }
}

/// Integrity description for the variable-width JSON measurement file.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryFileIdentity {
    pub file: String,
    pub records: u64,
    pub bytes: u64,
    pub sha256: String,
}

/// The seven representation-specific values consumed by Phase 3.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RepresentationGeometryValues {
    pub b16: F64Bits,
    pub h16: F64Bits,
    pub h64: F64Bits,
    pub h256: F64Bits,
    pub s16: F64Bits,
    pub s64: F64Bits,
    pub s256: F64Bits,
}

/// One anchor's complete deterministic measurements.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AnchorGeometryMeasurement {
    pub anchor_ordinal: u64,
    pub selection_sha256: String,
    pub row: u64,
    pub event_id: String,
    pub b16_neighbor_event_id: String,
    pub b16: F64Bits,
    pub h16: F64Bits,
    pub h64: F64Bits,
    pub h256: F64Bits,
    pub s16: F64Bits,
    pub s64: F64Bits,
    pub s256: F64Bits,
}

/// Durable identity and final values for one geometry artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RepresentationGeometryManifest {
    pub schema_version: u32,
    pub derivation_version: String,
    pub representation: GeometryRepresentationBinding,
    pub rules: GeometryRules,
    pub targets: [u64; 3],
    pub anchor_measurements: GeometryFileIdentity,
    pub values: RepresentationGeometryValues,
}

/// A fully verified geometry artifact.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationGeometryArtifact {
    manifest: RepresentationGeometryManifest,
    measurements: Vec<AnchorGeometryMeasurement>,
    geometry_version: String,
}

impl RepresentationGeometryArtifact {
    pub fn manifest(&self) -> &RepresentationGeometryManifest {
        &self.manifest
    }

    pub fn measurements(&self) -> &[AnchorGeometryMeasurement] {
        &self.measurements
    }

    pub fn geometry_version(&self) -> &str {
        &self.geometry_version
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct SelectedAnchor {
    selection_sha256: [u8; 32],
    row: u64,
    event_id: EventId,
}

impl Ord for SelectedAnchor {
    fn cmp(&self, other: &Self) -> Ordering {
        self.selection_sha256
            .cmp(&other.selection_sha256)
            .then_with(|| self.event_id.cmp(&other.event_id))
            .then_with(|| self.row.cmp(&other.row))
    }
}

impl PartialOrd for SelectedAnchor {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Derive and atomically publish the exact geometry, or verify an existing result.
pub fn derive_representation_geometry(
    ordered_event_ids_path: impl AsRef<Path>,
    representation_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationGeometryArtifact> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let representation_path = representation_path.as_ref();
    let output_path = output_path.as_ref();
    reject_output_inside_representation(representation_path, output_path)?;
    if output_path.exists() {
        return open_representation_geometry(ordered_path, representation_path, output_path);
    }

    let store = open_verified_representation(ordered_path, representation_path)?;
    validate_source(&store)?;
    let parent = output_path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    reject_output_inside_representation(representation_path, output_path)?;
    let stage = stage_path(output_path)?;
    match fs::create_dir(&stage) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            return Err(Error::IncompleteStage(stage));
        }
        Err(source) => return Err(io_error("create", &stage, source)),
    }

    let staged_artifact = match derive_in_stage(ordered_path, &store, &stage)
        .and_then(|()| open_representation_geometry(ordered_path, representation_path, &stage))
    {
        Ok(artifact) => artifact,
        Err(error) => return Err(error_after_stage_cleanup(&stage, error)),
    };
    if output_path.exists() {
        return Err(error_after_stage_cleanup(
            &stage,
            Error::ArtifactExists(output_path.to_owned()),
        ));
    }
    if let Err(source) = fs::rename(&stage, output_path) {
        return Err(error_after_stage_cleanup(
            &stage,
            io_error("publish", output_path, source),
        ));
    }
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))?;
    Ok(staged_artifact)
}

/// Open and structurally verify a previously published geometry artifact.
pub fn open_representation_geometry(
    ordered_event_ids_path: impl AsRef<Path>,
    representation_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationGeometryArtifact> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let representation_path = representation_path.as_ref();
    let output_path = output_path.as_ref();
    reject_output_inside_representation(representation_path, output_path)?;
    let store = open_verified_representation(ordered_path, representation_path)?;
    validate_source(&store)?;
    let manifest_path = output_path.join(MANIFEST_FILE);
    let measurements_path = output_path.join(MEASUREMENTS_FILE);
    require_file(&manifest_path)?;
    require_file(&measurements_path)?;
    let manifest: RepresentationGeometryManifest = read_manifest(&manifest_path)?;
    validate_manifest_shape(&manifest, &store)?;
    validate_measurement_file(&manifest.anchor_measurements, &measurements_path)?;
    let measurements: Vec<AnchorGeometryMeasurement> = read_manifest(&measurements_path)?;
    validate_measurements(ordered_path, &store, &manifest, &measurements)?;
    Ok(RepresentationGeometryArtifact {
        manifest,
        measurements,
        geometry_version: hash_file(&manifest_path)?,
    })
}

/// Recompute the complete derivation in a temporary sibling and require a byte-identical replay.
pub fn verify_representation_geometry(
    ordered_event_ids_path: impl AsRef<Path>,
    representation_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationGeometryArtifact> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let representation_path = representation_path.as_ref();
    let output_path = output_path.as_ref();
    let artifact = open_representation_geometry(ordered_path, representation_path, output_path)?;
    let store = open_verified_representation(ordered_path, representation_path)?;
    validate_source(&store)?;
    let stage = verification_stage_path(output_path)?;
    match fs::create_dir(&stage) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            return Err(Error::IncompleteStage(stage));
        }
        Err(source) => return Err(io_error("create", &stage, source)),
    }
    let verification = (|| {
        derive_in_stage(ordered_path, &store, &stage)?;
        for file in [MEASUREMENTS_FILE, MANIFEST_FILE] {
            let expected = fs::read(output_path.join(file))
                .map_err(|source| io_error("read", output_path.join(file), source))?;
            let replayed = fs::read(stage.join(file))
                .map_err(|source| io_error("read", stage.join(file), source))?;
            if replayed != expected {
                return Err(Error::Invariant(format!(
                    "geometry deep verification did not reproduce `{file}`"
                )));
            }
        }
        Ok(())
    })();
    remove_stage(&stage, verification)?;
    Ok(artifact)
}

fn derive_in_stage(ordered_path: &Path, store: &RepresentationStore, stage: &Path) -> Result<()> {
    let event_ids = load_event_ids(ordered_path, store)?;
    let anchors = select_anchors(store.representation_version(), &event_ids)?;
    let anchor_vectors = anchors
        .iter()
        .map(|anchor| store.vector_for_row(anchor.row))
        .collect::<Result<Vec<_>>>()?;
    let scratch_path = stage.join(DISTANCE_SCRATCH_FILE);
    let mut scratch = create_distance_scratch(
        &scratch_path,
        ANCHOR_COUNT,
        usize::try_from(store.manifest().total_rows)
            .map_err(|_| Error::Invariant("geometry row count does not fit usize".to_owned()))?,
    )?;
    fill_squared_distances(store, &anchors, &anchor_vectors, &mut scratch)?;
    let measurements = derive_anchor_measurements(&anchors, &event_ids, &scratch)?;
    drop(scratch);
    fs::remove_file(&scratch_path).map_err(|source| io_error("remove", &scratch_path, source))?;

    let measurements_path = stage.join(MEASUREMENTS_FILE);
    write_manifest(&measurements_path, &measurements)?;
    let measurement_metadata = fs::metadata(&measurements_path)
        .map_err(|source| io_error("read metadata for", &measurements_path, source))?;
    let values = median_values(&measurements)?;
    let manifest = RepresentationGeometryManifest {
        schema_version: SCHEMA_VERSION,
        derivation_version: REPRESENTATION_GEOMETRY_DERIVATION_VERSION.to_owned(),
        representation: GeometryRepresentationBinding::from_store(store),
        rules: GeometryRules::default(),
        targets: TARGETS,
        anchor_measurements: GeometryFileIdentity {
            file: MEASUREMENTS_FILE.to_owned(),
            records: ANCHOR_COUNT as u64,
            bytes: measurement_metadata.len(),
            sha256: hash_file(&measurements_path)?,
        },
        values,
    };
    write_manifest(&stage.join(MANIFEST_FILE), &manifest)?;
    File::open(stage)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", stage, source))
}

fn validate_source(store: &RepresentationStore) -> Result<()> {
    let manifest = store.manifest();
    if !manifest.complete || manifest.completed_rows != manifest.total_rows {
        return Err(Error::Invariant(
            "geometry requires a complete representation".to_owned(),
        ));
    }
    if manifest.total_rows <= ANCHOR_COUNT as u64 || manifest.total_rows <= TARGETS[2] {
        return Err(Error::Invariant(format!(
            "geometry requires more than {ANCHOR_COUNT} represented rows"
        )));
    }
    if manifest.descriptor.dimensions == 0 {
        return Err(Error::Invariant(
            "geometry requires at least one vector dimension".to_owned(),
        ));
    }
    if manifest.descriptor.numeric_format != "f32le" {
        return Err(Error::Invariant(
            "geometry requires stored f32le vectors".to_owned(),
        ));
    }
    Ok(())
}

fn load_event_ids(ordered_path: &Path, store: &RepresentationStore) -> Result<Vec<EventId>> {
    (0..store.manifest().total_rows)
        .map(|row| store.event_for_row(ordered_path, row))
        .collect()
}

fn select_anchors(version: &str, event_ids: &[EventId]) -> Result<Vec<SelectedAnchor>> {
    if event_ids.len() <= ANCHOR_COUNT {
        return Err(Error::Invariant(format!(
            "geometry requires more than {ANCHOR_COUNT} ordered event IDs"
        )));
    }
    let version_length = u64::try_from(version.len())
        .map_err(|_| Error::Invariant("representation version is too long".to_owned()))?;
    let mut selected = BinaryHeap::with_capacity(ANCHOR_COUNT + 1);
    for (row, event_id) in event_ids.iter().enumerate() {
        let mut hasher = Sha256::new();
        hasher.update(REPRESENTATION_GEOMETRY_ANCHOR_DOMAIN);
        hasher.update(version_length.to_le_bytes());
        hasher.update(version.as_bytes());
        hasher.update(event_id);
        let candidate = SelectedAnchor {
            selection_sha256: hasher.finalize().into(),
            row: row as u64,
            event_id: *event_id,
        };
        if selected.len() < ANCHOR_COUNT {
            selected.push(candidate);
        } else if selected.peek().is_some_and(|largest| candidate < *largest) {
            selected.pop();
            selected.push(candidate);
        }
    }
    let mut selected = selected.into_vec();
    selected.sort_unstable();
    Ok(selected)
}

fn create_distance_scratch(path: &Path, anchors: usize, rows: usize) -> Result<MmapMut> {
    let bytes = anchors
        .checked_mul(rows)
        .and_then(|values| values.checked_mul(size_of::<f64>()))
        .ok_or_else(|| Error::Invariant("geometry distance scratch size overflowed".to_owned()))?;
    let file = OpenOptions::new()
        .create_new(true)
        .read(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    file.set_len(bytes as u64)
        .map_err(|source| io_error("size", path, source))?;
    // SAFETY: the new file remains open for the mapping, has exactly `bytes`
    // bytes, and this derivation owns the only writable mapping.
    unsafe { MmapOptions::new().map_mut(&file) }.map_err(|source| io_error("map", path, source))
}

fn fill_squared_distances(
    store: &RepresentationStore,
    anchors: &[SelectedAnchor],
    anchor_vectors: &[Vec<f32>],
    scratch: &mut MmapMut,
) -> Result<()> {
    let rows = usize::try_from(store.manifest().total_rows)
        .map_err(|_| Error::Invariant("geometry row count does not fit usize".to_owned()))?;
    let dimensions = usize::try_from(store.manifest().descriptor.dimensions)
        .map_err(|_| Error::Invariant("geometry dimensions do not fit usize".to_owned()))?;
    let expected_values = anchors
        .len()
        .checked_mul(rows)
        .ok_or_else(|| Error::Invariant("geometry distance count overflowed".to_owned()))?;
    if scratch.len() != expected_values * size_of::<f64>() {
        return Err(Error::Invariant(
            "geometry distance scratch has the wrong length".to_owned(),
        ));
    }
    let pointer = scratch.as_mut_ptr();
    if pointer.align_offset(std::mem::align_of::<f64>()) != 0 {
        return Err(Error::Invariant(
            "geometry distance scratch is not f64-aligned".to_owned(),
        ));
    }
    // SAFETY: the mmap is aligned, has exactly `expected_values * 8` bytes,
    // and remains exclusively borrowed for the lifetime of this slice.
    let distances =
        unsafe { std::slice::from_raw_parts_mut(pointer.cast::<f64>(), expected_values) };
    let workers = thread::available_parallelism()
        .map(usize::from)
        .unwrap_or(1)
        .min(anchors.len());
    let anchors_per_worker = anchors.len().div_ceil(workers);
    store.scan_vector_blocks(VECTOR_BLOCK_ROWS, |start_row, encoded| {
        if encoded.len() % dimensions != 0 {
            return Err(Error::Invariant(
                "geometry vector block has a partial row".to_owned(),
            ));
        }
        let block_rows = encoded.len() / dimensions;
        let start = usize::try_from(start_row)
            .map_err(|_| Error::Invariant("geometry block row does not fit usize".to_owned()))?;
        let end = start
            .checked_add(block_rows)
            .ok_or_else(|| Error::Invariant("geometry block end overflowed".to_owned()))?;
        if end > rows {
            return Err(Error::Invariant(
                "geometry vector block extends beyond the representation".to_owned(),
            ));
        }
        thread::scope(|scope| -> Result<()> {
            let mut handles = Vec::new();
            for ((anchor_chunk, vector_chunk), output_chunk) in anchors
                .chunks(anchors_per_worker)
                .zip(anchor_vectors.chunks(anchors_per_worker))
                .zip(distances.chunks_mut(anchors_per_worker * rows))
            {
                handles.push(scope.spawn(move || -> Result<()> {
                    for ((anchor, anchor_vector), output) in anchor_chunk
                        .iter()
                        .zip(vector_chunk)
                        .zip(output_chunk.chunks_mut(rows))
                    {
                        let target = &mut output[start..end];
                        for (local_row, (candidate, destination)) in
                            encoded.chunks_exact(dimensions).zip(target).enumerate()
                        {
                            let row = start + local_row;
                            *destination = if row as u64 == anchor.row {
                                f64::INFINITY
                            } else {
                                squared_chord_distance(anchor_vector, candidate)?
                            };
                        }
                    }
                    Ok(())
                }));
            }
            for handle in handles {
                handle.join().map_err(|_| {
                    Error::Invariant("geometry distance worker panicked".to_owned())
                })??;
            }
            Ok(())
        })
    })?;
    if distances.iter().filter(|value| value.is_infinite()).count() != ANCHOR_COUNT {
        return Err(Error::Invariant(
            "geometry distance scan did not exclude exactly one row per anchor".to_owned(),
        ));
    }
    Ok(())
}

fn squared_chord_distance(left: &[f32], right: &[f32]) -> Result<f64> {
    if left.len() != right.len() || left.is_empty() {
        return Err(Error::Invariant(
            "geometry distance received incompatible vectors".to_owned(),
        ));
    }
    let mut squared = 0.0_f64;
    for (left, right) in left.iter().zip(right) {
        let difference = f64::from(*left) - f64::from(*right);
        squared += difference * difference;
    }
    if !squared.is_finite() || squared < 0.0 {
        return Err(Error::Invariant(
            "geometry distance is non-finite".to_owned(),
        ));
    }
    Ok(squared)
}

fn derive_anchor_measurements(
    anchors: &[SelectedAnchor],
    event_ids: &[EventId],
    scratch: &MmapMut,
) -> Result<Vec<AnchorGeometryMeasurement>> {
    let rows = event_ids.len();
    let expected_values = anchors
        .len()
        .checked_mul(rows)
        .ok_or_else(|| Error::Invariant("geometry distance count overflowed".to_owned()))?;
    if scratch.len() != expected_values * size_of::<f64>() {
        return Err(Error::Invariant(
            "geometry distance scratch has the wrong length".to_owned(),
        ));
    }
    let pointer = scratch.as_ptr();
    if pointer.align_offset(std::mem::align_of::<f64>()) != 0 {
        return Err(Error::Invariant(
            "geometry distance scratch is not f64-aligned".to_owned(),
        ));
    }
    // SAFETY: this is the same aligned, initialized mapping filled above and
    // remains immutably borrowed while the slice is used.
    let distances = unsafe { std::slice::from_raw_parts(pointer.cast::<f64>(), expected_values) };
    let workers = thread::available_parallelism()
        .map(usize::from)
        .unwrap_or(1)
        .min(anchors.len());
    let anchors_per_worker = anchors.len().div_ceil(workers);
    let mut chunks = thread::scope(|scope| {
        let mut handles = Vec::new();
        for (chunk_index, (anchor_chunk, distance_chunk)) in anchors
            .chunks(anchors_per_worker)
            .zip(distances.chunks(anchors_per_worker * rows))
            .enumerate()
        {
            let ordinal_start = chunk_index * anchors_per_worker;
            handles.push(scope.spawn(move || {
                anchor_chunk
                    .iter()
                    .zip(distance_chunk.chunks(rows))
                    .enumerate()
                    .map(|(local, (anchor, squared_distances))| {
                        derive_anchor_measurement(
                            ordinal_start + local,
                            anchor,
                            event_ids,
                            squared_distances,
                        )
                    })
                    .collect::<Result<Vec<_>>>()
            }));
        }
        handles
            .into_iter()
            .map(|handle| {
                handle.join().map_err(|_| {
                    Error::Invariant("geometry measurement worker panicked".to_owned())
                })?
            })
            .collect::<Result<Vec<_>>>()
    })?;
    let mut measurements = Vec::with_capacity(ANCHOR_COUNT);
    for chunk in &mut chunks {
        measurements.append(chunk);
    }
    Ok(measurements)
}

fn derive_anchor_measurement(
    ordinal: usize,
    anchor: &SelectedAnchor,
    event_ids: &[EventId],
    squared_distances: &[f64],
) -> Result<AnchorGeometryMeasurement> {
    if squared_distances.len() != event_ids.len() {
        return Err(Error::Invariant(
            "geometry anchor distance row count does not match the corpus".to_owned(),
        ));
    }
    let mut finite = squared_distances
        .iter()
        .copied()
        .filter(|value| value.is_finite())
        .collect::<Vec<_>>();
    if finite.len() + 1 != event_ids.len() || finite.len() < TARGETS[2] as usize {
        return Err(Error::Invariant(
            "geometry anchor did not retain every other finite distance".to_owned(),
        ));
    }
    let (_, b16_squared, _) = finite.select_nth_unstable_by(15, f64::total_cmp);
    let b16_squared = *b16_squared;
    let closer = squared_distances
        .iter()
        .filter(|value| value.is_finite() && **value < b16_squared)
        .count();
    let mut tied_ids = squared_distances
        .iter()
        .zip(event_ids)
        .filter(|(value, _)| value.is_finite() && **value == b16_squared)
        .map(|(_, event_id)| *event_id)
        .collect::<Vec<_>>();
    tied_ids.sort_unstable();
    let tied_index = 15_usize
        .checked_sub(closer)
        .ok_or_else(|| Error::Invariant("geometry B16 tie accounting underflowed".to_owned()))?;
    let b16_neighbor = *tied_ids
        .get(tied_index)
        .ok_or_else(|| Error::Invariant("geometry B16 tie accounting is incomplete".to_owned()))?;

    let compact_neighbors = compact_neighbor_set(squared_distances)?;
    let h16 = minimal_compact_scale(&compact_neighbors, 16.0)?;
    let h64 = minimal_compact_scale(&compact_neighbors, 64.0)?;
    let h256 = minimal_compact_scale(&compact_neighbors, 256.0)?;
    let s16 = minimal_rbf_scale(squared_distances, &compact_neighbors, 16.0)?;
    let s64 = minimal_rbf_scale(squared_distances, &compact_neighbors, 64.0)?;
    let s256 = minimal_rbf_scale(squared_distances, &compact_neighbors, 256.0)?;

    Ok(AnchorGeometryMeasurement {
        anchor_ordinal: ordinal as u64,
        selection_sha256: hex(&anchor.selection_sha256),
        row: anchor.row,
        event_id: hex(&anchor.event_id),
        b16_neighbor_event_id: hex(&b16_neighbor),
        b16: F64Bits::new(b16_squared.sqrt(), "B16", true)?,
        h16: F64Bits::new(h16, "H16", false)?,
        h64: F64Bits::new(h64, "H64", false)?,
        h256: F64Bits::new(h256, "H256", false)?,
        s16: F64Bits::new(s16, "S16", false)?,
        s64: F64Bits::new(s64, "S64", false)?,
        s256: F64Bits::new(s256, "S256", false)?,
    })
}

fn compact_neighbor_set(squared_distances: &[f64]) -> Result<Vec<f64>> {
    let available = squared_distances
        .iter()
        .filter(|value| value.is_finite())
        .count();
    let mut count = INITIAL_LOCAL_NEIGHBORS.min(available);
    loop {
        let mut values = squared_distances
            .iter()
            .copied()
            .filter(|value| value.is_finite())
            .collect::<Vec<_>>();
        let cutoff = if count < values.len() {
            let (_, selected, _) = values.select_nth_unstable_by(count - 1, f64::total_cmp);
            *selected
        } else {
            values
                .iter()
                .copied()
                .max_by(f64::total_cmp)
                .expect("nonempty neighbors")
        };
        let selected = squared_distances
            .iter()
            .copied()
            .filter(|value| value.is_finite() && *value <= cutoff)
            .collect::<Vec<_>>();
        let h256 = minimal_compact_scale(&selected, 256.0)?;
        if count == available || h256 * h256 < cutoff {
            return Ok(selected);
        }
        count = count.saturating_mul(2).min(available);
    }
}

fn minimal_compact_scale(squared_distances: &[f64], target: f64) -> Result<f64> {
    let zeros = squared_distances
        .iter()
        .filter(|value| **value == 0.0)
        .count();
    if zeros as f64 >= target {
        return Err(Error::Invariant(format!(
            "geometry compact target {target} is already reached at zero bandwidth"
        )));
    }
    let mut upper = squared_distances
        .iter()
        .copied()
        .max_by(f64::total_cmp)
        .expect("nonempty neighbors")
        .sqrt();
    if upper == 0.0 {
        upper = f64::MIN_POSITIVE;
    }
    while compact_mass(squared_distances, upper)? < target {
        upper *= 2.0;
        if !upper.is_finite() {
            return Err(Error::Invariant(
                "geometry compact root could not be bracketed".to_owned(),
            ));
        }
    }
    minimal_reaching_f64(
        upper,
        |scale| compact_mass(squared_distances, scale),
        target,
    )
}

fn compact_mass(squared_distances: &[f64], radius: f64) -> Result<f64> {
    if radius == 0.0 {
        return Ok(squared_distances
            .iter()
            .filter(|value| **value == 0.0)
            .count() as f64);
    }
    let mut mass = 0.0_f64;
    for squared in squared_distances {
        let distance = squared.sqrt();
        if distance < radius {
            let ratio_cubed = (distance / radius).powi(3);
            mass += (1.0 - ratio_cubed).powi(3);
        }
    }
    if !mass.is_finite() {
        return Err(Error::Invariant(
            "geometry compact mass is non-finite".to_owned(),
        ));
    }
    Ok(mass)
}

fn minimal_rbf_scale(
    all_squared_distances: &[f64],
    nearest_squared_distances: &[f64],
    target: f64,
) -> Result<f64> {
    let zeros = all_squared_distances
        .iter()
        .filter(|value| value.is_finite() && **value == 0.0)
        .count();
    if zeros as f64 >= target {
        return Err(Error::Invariant(format!(
            "geometry RBF target {target} is already reached at zero scale"
        )));
    }
    let mut upper = nearest_squared_distances
        .iter()
        .copied()
        .max_by(f64::total_cmp)
        .expect("nonempty neighbors")
        .sqrt();
    if upper == 0.0 {
        upper = f64::MIN_POSITIVE;
    }
    while rbf_mass(nearest_squared_distances, upper)? < target {
        upper *= 2.0;
        if !upper.is_finite() {
            return Err(Error::Invariant(
                "geometry RBF initial root could not be bracketed".to_owned(),
            ));
        }
    }
    let retained_root = minimal_reaching_f64(
        upper,
        |scale| rbf_mass(nearest_squared_distances, scale),
        target,
    )?;
    let mut high = retained_root;
    while rbf_mass(all_squared_distances, high)? < target {
        high *= 2.0;
        if !high.is_finite() {
            return Err(Error::Invariant(
                "geometry full RBF root could not be bracketed".to_owned(),
            ));
        }
    }
    let mut low = high / 2.0;
    while low > 0.0 && rbf_mass(all_squared_distances, low)? >= target {
        high = low;
        low /= 2.0;
    }
    for _ in 0..80 {
        let (mass, derivative) = rbf_mass_and_derivative(all_squared_distances, high)?;
        if mass < target {
            return Err(Error::Invariant(
                "geometry RBF upper bracket does not reach its target".to_owned(),
            ));
        }
        let previous = previous_positive_f64(high);
        if rbf_mass(all_squared_distances, previous)? < target {
            return Ok(high);
        }
        let mut next = high - (mass - target) / derivative;
        if !next.is_finite() || next <= low || next >= high {
            next = low / 2.0 + high / 2.0;
        }
        let next_mass = rbf_mass(all_squared_distances, next)?;
        if next_mass >= target {
            high = next;
        } else {
            low = next;
        }
        if next_up(low) == high {
            return Ok(high);
        }
    }
    Err(Error::Invariant(
        "geometry RBF root did not converge to the smallest f64".to_owned(),
    ))
}

fn rbf_mass(squared_distances: &[f64], scale: f64) -> Result<f64> {
    if scale < 0.0 || !scale.is_finite() {
        return Err(Error::Invariant(
            "geometry RBF mass requires a nonnegative finite scale".to_owned(),
        ));
    }
    if scale == 0.0 {
        return Ok(squared_distances
            .iter()
            .filter(|value| value.is_finite() && **value == 0.0)
            .count() as f64);
    }
    let denominator = 2.0 * scale * scale;
    if denominator == 0.0 {
        return Ok(squared_distances
            .iter()
            .filter(|value| value.is_finite() && **value == 0.0)
            .count() as f64);
    }
    let mut mass = 0.0_f64;
    for squared in squared_distances {
        if squared.is_infinite() {
            continue;
        }
        let weight = (-*squared / denominator).exp();
        mass += weight;
    }
    if !mass.is_finite() {
        return Err(Error::Invariant(
            "geometry RBF mass is non-finite".to_owned(),
        ));
    }
    Ok(mass)
}

fn rbf_mass_and_derivative(squared_distances: &[f64], scale: f64) -> Result<(f64, f64)> {
    if scale <= 0.0 || !scale.is_finite() {
        return Err(Error::Invariant(
            "geometry RBF mass requires a positive finite scale".to_owned(),
        ));
    }
    let denominator = 2.0 * scale * scale;
    let scale_cubed = scale * scale * scale;
    let mut mass = 0.0_f64;
    let mut derivative = 0.0_f64;
    for squared in squared_distances {
        if squared.is_infinite() {
            continue;
        }
        let weight = (-*squared / denominator).exp();
        mass += weight;
        derivative += weight * *squared / scale_cubed;
    }
    if !mass.is_finite() || !derivative.is_finite() || derivative <= 0.0 {
        return Err(Error::Invariant(
            "geometry RBF mass or derivative is invalid".to_owned(),
        ));
    }
    Ok((mass, derivative))
}

fn minimal_reaching_f64(upper: f64, mass: impl Fn(f64) -> Result<f64>, target: f64) -> Result<f64> {
    if !upper.is_finite() || upper <= 0.0 || mass(upper)? < target {
        return Err(Error::Invariant(
            "geometry root upper bracket is invalid".to_owned(),
        ));
    }
    let mut low_bits = 0_u64;
    let mut high_bits = upper.to_bits();
    while low_bits + 1 < high_bits {
        let middle_bits = low_bits + (high_bits - low_bits) / 2;
        let middle = f64::from_bits(middle_bits);
        if mass(middle)? >= target {
            high_bits = middle_bits;
        } else {
            low_bits = middle_bits;
        }
    }
    Ok(f64::from_bits(high_bits))
}

fn previous_positive_f64(value: f64) -> f64 {
    f64::from_bits(value.to_bits() - 1)
}

fn next_up(value: f64) -> f64 {
    if value == 0.0 {
        f64::from_bits(1)
    } else {
        f64::from_bits(value.to_bits() + 1)
    }
}

fn median_values(
    measurements: &[AnchorGeometryMeasurement],
) -> Result<RepresentationGeometryValues> {
    Ok(RepresentationGeometryValues {
        b16: median(measurements, |entry| &entry.b16, "B16", true)?,
        h16: median(measurements, |entry| &entry.h16, "H16", false)?,
        h64: median(measurements, |entry| &entry.h64, "H64", false)?,
        h256: median(measurements, |entry| &entry.h256, "H256", false)?,
        s16: median(measurements, |entry| &entry.s16, "S16", false)?,
        s64: median(measurements, |entry| &entry.s64, "S64", false)?,
        s256: median(measurements, |entry| &entry.s256, "S256", false)?,
    })
}

fn median(
    measurements: &[AnchorGeometryMeasurement],
    select: impl Fn(&AnchorGeometryMeasurement) -> &F64Bits,
    label: &str,
    allow_zero: bool,
) -> Result<F64Bits> {
    if measurements.len() != ANCHOR_COUNT {
        return Err(Error::Invariant(format!(
            "geometry median requires exactly {ANCHOR_COUNT} anchors"
        )));
    }
    let mut values = measurements
        .iter()
        .map(|measurement| select(measurement).value())
        .collect::<Result<Vec<_>>>()?;
    values.sort_unstable_by(f64::total_cmp);
    F64Bits::new(values[255] / 2.0 + values[256] / 2.0, label, allow_zero)
}

fn validate_manifest_shape(
    manifest: &RepresentationGeometryManifest,
    store: &RepresentationStore,
) -> Result<()> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.derivation_version != REPRESENTATION_GEOMETRY_DERIVATION_VERSION
        || manifest.rules != GeometryRules::default()
        || manifest.targets != TARGETS
    {
        return Err(Error::Invariant(
            "geometry manifest uses an unsupported derivation contract".to_owned(),
        ));
    }
    if manifest.representation != GeometryRepresentationBinding::from_store(store) {
        return Err(Error::Invariant(
            "geometry manifest does not match the sealed representation".to_owned(),
        ));
    }
    if manifest.anchor_measurements.file != MEASUREMENTS_FILE
        || manifest.anchor_measurements.records != ANCHOR_COUNT as u64
    {
        return Err(Error::Invariant(
            "geometry measurement identity has the wrong shape".to_owned(),
        ));
    }
    Ok(())
}

fn validate_measurement_file(identity: &GeometryFileIdentity, path: &Path) -> Result<()> {
    let metadata =
        fs::metadata(path).map_err(|source| io_error("read metadata for", path, source))?;
    if metadata.len() != identity.bytes || hash_file(path)? != identity.sha256 {
        return Err(Error::Invariant(
            "geometry measurement file does not match its manifest".to_owned(),
        ));
    }
    Ok(())
}

fn validate_measurements(
    ordered_path: &Path,
    store: &RepresentationStore,
    manifest: &RepresentationGeometryManifest,
    measurements: &[AnchorGeometryMeasurement],
) -> Result<()> {
    if measurements.len() != ANCHOR_COUNT {
        return Err(Error::Invariant(format!(
            "geometry artifact contains {} anchors instead of {ANCHOR_COUNT}",
            measurements.len()
        )));
    }
    let event_ids = load_event_ids(ordered_path, store)?;
    let expected = select_anchors(store.representation_version(), &event_ids)?;
    let mut unique_rows = BTreeSet::new();
    let mut unique_ids = BTreeSet::new();
    for (ordinal, ((measurement, anchor), expected_ordinal)) in
        measurements.iter().zip(expected).zip(0_u64..).enumerate()
    {
        let _ = ordinal;
        if measurement.anchor_ordinal != expected_ordinal
            || measurement.selection_sha256 != hex(&anchor.selection_sha256)
            || measurement.row != anchor.row
            || measurement.event_id != hex(&anchor.event_id)
        {
            return Err(Error::Invariant(
                "geometry anchor selection is not reproducible".to_owned(),
            ));
        }
        if !unique_rows.insert(measurement.row) || !unique_ids.insert(&measurement.event_id) {
            return Err(Error::Invariant(
                "geometry artifact repeats an anchor".to_owned(),
            ));
        }
        let neighbor_event_id = decode_event_id(
            &measurement.b16_neighbor_event_id,
            "geometry B16 neighbor event ID",
        )?;
        let neighbor_row = store.row_for_event(neighbor_event_id)?.ok_or_else(|| {
            Error::Invariant("geometry B16 neighbor is not in the representation".to_owned())
        })?;
        if neighbor_row == measurement.row {
            return Err(Error::Invariant(
                "geometry B16 neighbor is the anchor itself".to_owned(),
            ));
        }
        validate_measurement_values(measurement)?;
    }
    if median_values(measurements)? != manifest.values {
        return Err(Error::Invariant(
            "geometry final values do not match the anchor medians".to_owned(),
        ));
    }
    Ok(())
}

fn validate_measurement_values(measurement: &AnchorGeometryMeasurement) -> Result<()> {
    let b16 = measurement.b16.value()?;
    let compact = [
        measurement.h16.value()?,
        measurement.h64.value()?,
        measurement.h256.value()?,
    ];
    let rbf = [
        measurement.s16.value()?,
        measurement.s64.value()?,
        measurement.s256.value()?,
    ];
    if !b16.is_finite()
        || b16 < 0.0
        || compact
            .iter()
            .any(|value| !value.is_finite() || *value <= 0.0)
        || rbf.iter().any(|value| !value.is_finite() || *value <= 0.0)
        || !(compact[0] <= compact[1] && compact[1] <= compact[2])
        || !(rbf[0] <= rbf[1] && rbf[1] <= rbf[2])
    {
        return Err(Error::Invariant(
            "geometry anchor contains invalid or unordered values".to_owned(),
        ));
    }
    Ok(())
}

fn reject_output_inside_representation(representation: &Path, output: &Path) -> Result<()> {
    let representation = fs::canonicalize(representation)
        .map_err(|source| io_error("canonicalize", representation, source))?;
    let resolved_output = resolve_without_creating(output)?;
    if resolved_output == representation || resolved_output.starts_with(&representation) {
        return Err(Error::Invariant(
            "geometry output must be outside the representation directory".to_owned(),
        ));
    }
    Ok(())
}

fn resolve_without_creating(path: &Path) -> Result<PathBuf> {
    let absolute = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir()
            .map_err(|source| io_error("read current directory for", path, source))?
            .join(path)
    };
    let mut existing = absolute.as_path();
    let mut missing = Vec::<OsString>::new();
    while !existing.exists() {
        let name = existing.file_name().ok_or_else(|| {
            Error::Invariant("geometry output has no existing ancestor".to_owned())
        })?;
        missing.push(name.to_owned());
        existing = existing.parent().ok_or_else(|| {
            Error::Invariant("geometry output has no existing ancestor".to_owned())
        })?;
    }
    let mut resolved =
        fs::canonicalize(existing).map_err(|source| io_error("canonicalize", existing, source))?;
    for component in missing.into_iter().rev() {
        if component == "." || component == ".." {
            return Err(Error::Invariant(
                "geometry output contains an unsafe path component".to_owned(),
            ));
        }
        resolved.push(component);
    }
    if resolved
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err(Error::Invariant(
            "geometry output contains an unresolved parent component".to_owned(),
        ));
    }
    Ok(resolved)
}

fn stage_path(output: &Path) -> Result<PathBuf> {
    let name = output
        .file_name()
        .ok_or_else(|| Error::Invariant("geometry output path has no file name".to_owned()))?;
    let mut stage_name = OsString::from(".");
    stage_name.push(name);
    stage_name.push(".partial");
    Ok(output.with_file_name(stage_name))
}

fn verification_stage_path(output: &Path) -> Result<PathBuf> {
    let name = output
        .file_name()
        .ok_or_else(|| Error::Invariant("geometry output path has no file name".to_owned()))?;
    let mut stage_name = OsString::from(".");
    stage_name.push(name);
    stage_name.push(".verify.partial");
    Ok(output.with_file_name(stage_name))
}

fn remove_stage(stage: &Path, result: Result<()>) -> Result<()> {
    match result {
        Ok(()) => fs::remove_dir_all(stage).map_err(|source| io_error("remove", stage, source)),
        Err(error) => Err(error_after_stage_cleanup(stage, error)),
    }
}

fn error_after_stage_cleanup(stage: &Path, error: Error) -> Error {
    match fs::remove_dir_all(stage) {
        Ok(()) => error,
        Err(source) => Error::Invariant(format!(
            "{error}; additionally failed to remove `{}`: {source}",
            stage.display()
        )),
    }
}

fn hex(bytes: &[u8]) -> String {
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        write!(&mut encoded, "{byte:02x}").expect("writing to String cannot fail");
    }
    encoded
}

fn decode_event_id(encoded: &str, label: &str) -> Result<EventId> {
    if encoded.len() != 64
        || !encoded
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(Error::Invariant(format!(
            "{label} must be sixty-four lowercase hexadecimal digits"
        )));
    }
    let mut event_id = [0_u8; 32];
    for (destination, pair) in event_id.iter_mut().zip(encoded.as_bytes().chunks_exact(2)) {
        let pair = std::str::from_utf8(pair)
            .map_err(|_| Error::Invariant(format!("{label} is invalid")))?;
        *destination = u8::from_str_radix(pair, 16)
            .map_err(|_| Error::Invariant(format!("{label} is invalid")))?;
    }
    Ok(event_id)
}
