//! Serialized binding between verified public artifacts and one Phase 3 session.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::adaptive_learning_runner::{AdaptiveLearningRunnerConfig, AdaptiveLearningSeed};
use crate::candidate_order::B16Boundary;
use crate::personalizer_learning::{CompactLearningSettings, RbfLearningSettings, ScaleLevel};
use crate::quota_resolution::PriorPresentation;
use crate::representation::EventId;
use crate::representation_geometry::RepresentationGeometryArtifact;

/// Stable schema shared by the Phase 3 preflight, capacity run, and evaluator.
pub const PHASE3_RUNNER_BINDING_SCHEMA_VERSION: u32 = 1;

/// One seed as represented in a durable Phase 3 binding.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Phase3SeedBinding {
    event_id: String,
    rating: u8,
}

/// One screening-only event retained solely in the exact-ID no-repeat ledger.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Phase3InitialPresentationBinding {
    event_id: String,
    state: PriorPresentation,
}

impl Phase3InitialPresentationBinding {
    pub fn new(event_id: impl Into<String>, state: PriorPresentation) -> Result<Self, String> {
        if matches!(state, PriorPresentation::Rated { .. }) {
            return Err("initial screening presentation cannot contain rated evidence".to_owned());
        }
        let binding = Self {
            event_id: event_id.into(),
            state,
        };
        binding.event_id()?;
        Ok(binding)
    }

    pub fn event_id(&self) -> Result<EventId, String> {
        parse_event_id(&self.event_id)
    }

    pub fn state(&self) -> &PriorPresentation {
        &self.state
    }
}

impl Phase3SeedBinding {
    pub fn new(event_id: impl Into<String>, rating: u8) -> Self {
        Self {
            event_id: event_id.into(),
            rating,
        }
    }

    pub fn event_id_hex(&self) -> &str {
        &self.event_id
    }

    pub const fn rating(&self) -> u8 {
        self.rating
    }

    pub fn event_id(&self) -> Result<EventId, String> {
        parse_event_id(&self.event_id)
    }
}

/// Immutable public geometry, corpus identity, and seeds for one Phase 3 run.
///
/// Field order and names are the original CREC-88/90 JSON contract.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Phase3RunnerBinding {
    schema_version: u32,
    corpus_path: PathBuf,
    corpus_identity: String,
    session_path: PathBuf,
    representation_version: String,
    geometry_version: String,
    b16_bits: String,
    h16_bits: String,
    h64_bits: String,
    h256_bits: String,
    s16_bits: String,
    s64_bits: String,
    s256_bits: String,
    seeds: Vec<Phase3SeedBinding>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    initial_presentations: Vec<Phase3InitialPresentationBinding>,
}

impl Phase3RunnerBinding {
    /// Bind one verified geometry artifact to its disposable corpus, durable
    /// session, and ordered seeds without decimal round-tripping.
    pub fn from_geometry(
        geometry: &RepresentationGeometryArtifact,
        corpus_path: PathBuf,
        session_path: PathBuf,
        seeds: Vec<Phase3SeedBinding>,
    ) -> Self {
        Self::from_geometry_with_initial_presentations(
            geometry,
            corpus_path,
            session_path,
            seeds,
            Vec::new(),
        )
    }

    pub fn from_geometry_with_initial_presentations(
        geometry: &RepresentationGeometryArtifact,
        corpus_path: PathBuf,
        session_path: PathBuf,
        seeds: Vec<Phase3SeedBinding>,
        initial_presentations: Vec<Phase3InitialPresentationBinding>,
    ) -> Self {
        let manifest = geometry.manifest();
        let values = &manifest.values;
        Self {
            schema_version: PHASE3_RUNNER_BINDING_SCHEMA_VERSION,
            corpus_path,
            corpus_identity: format!("sha256:{}", manifest.representation.corpus_data_sha256),
            session_path,
            representation_version: manifest.representation.representation_version.clone(),
            geometry_version: geometry.geometry_version().to_owned(),
            b16_bits: values.b16.bits.clone(),
            h16_bits: values.h16.bits.clone(),
            h64_bits: values.h64.bits.clone(),
            h256_bits: values.h256.bits.clone(),
            s16_bits: values.s16.bits.clone(),
            s64_bits: values.s64.bits.clone(),
            s256_bits: values.s256.bits.clone(),
            seeds,
            initial_presentations,
        }
    }

    pub const fn schema_version(&self) -> u32 {
        self.schema_version
    }

    pub fn corpus_path(&self) -> &Path {
        &self.corpus_path
    }

    pub fn corpus_identity(&self) -> &str {
        &self.corpus_identity
    }

    pub fn session_path(&self) -> &Path {
        &self.session_path
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn geometry_version(&self) -> &str {
        &self.geometry_version
    }

    pub fn seeds(&self) -> &[Phase3SeedBinding] {
        &self.seeds
    }

    pub fn initial_presentations(&self) -> Result<BTreeMap<EventId, PriorPresentation>, String> {
        let seed_ids = self
            .seeds
            .iter()
            .map(Phase3SeedBinding::event_id)
            .collect::<Result<std::collections::BTreeSet<_>, _>>()?;
        let mut presentations = BTreeMap::new();
        for binding in &self.initial_presentations {
            let event_id = binding.event_id()?;
            if seed_ids.contains(&event_id) {
                return Err("initial screening presentation overlaps a positive seed".to_owned());
            }
            if matches!(binding.state, PriorPresentation::Rated { .. }) {
                return Err("initial screening presentation contains rated evidence".to_owned());
            }
            if presentations
                .insert(event_id, binding.state.clone())
                .is_some()
            {
                return Err("initial screening presentation IDs must be unique".to_owned());
            }
        }
        Ok(presentations)
    }

    /// Reconstruct the runner at the paths serialized in this binding.
    pub fn runner_config(&self) -> Result<AdaptiveLearningRunnerConfig, String> {
        self.runner_config_at(&self.corpus_path, &self.session_path)
    }

    /// Reconstruct the same immutable experiment while relocating only its
    /// disposable corpus and private session paths.
    pub fn runner_config_at(
        &self,
        corpus_path: impl AsRef<Path>,
        session_path: impl AsRef<Path>,
    ) -> Result<AdaptiveLearningRunnerConfig, String> {
        if self.schema_version != PHASE3_RUNNER_BINDING_SCHEMA_VERSION {
            return Err("runner binding has the wrong schema".to_owned());
        }
        let compact_settings = CompactLearningSettings::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.h16_bits, "h16")?,
            decode_f64_bits(&self.h64_bits, "h64")?,
            decode_f64_bits(&self.h256_bits, "h256")?,
            ScaleLevel::Mass64,
        )
        .map_err(|error| error.to_string())?;
        let rbf_settings = RbfLearningSettings::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.s16_bits, "s16")?,
            decode_f64_bits(&self.s64_bits, "s64")?,
            decode_f64_bits(&self.s256_bits, "s256")?,
        )
        .map_err(|error| error.to_string())?;
        let b16 = B16Boundary::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.b16_bits, "b16")?,
        )
        .map_err(|error| error.to_string())?;
        let seeds = self
            .seeds
            .iter()
            .map(|seed| {
                AdaptiveLearningSeed::new(seed.event_id()?, seed.rating)
                    .map_err(|error| error.to_string())
            })
            .collect::<Result<Vec<_>, _>>()?;
        self.initial_presentations()?;
        Ok(AdaptiveLearningRunnerConfig {
            corpus_path: corpus_path.as_ref().to_owned(),
            corpus_identity: self.corpus_identity.clone(),
            session_path: session_path.as_ref().to_owned(),
            compact_settings,
            rbf_settings,
            b16,
            seeds,
        })
    }
}

fn parse_event_id(value: &str) -> Result<EventId, String> {
    if value.len() != 64 {
        return Err("event ID must contain 64 lowercase hexadecimal digits".to_owned());
    }
    let mut event_id = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        event_id[index] = (decode_hex(pair[0])? << 4) | decode_hex(pair[1])?;
    }
    Ok(event_id)
}

fn decode_hex(byte: u8) -> Result<u8, String> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        _ => Err("event ID must use lowercase hexadecimal".to_owned()),
    }
}

fn decode_f64_bits(bits: &str, label: &str) -> Result<f64, String> {
    if bits.len() != 16
        || !bits
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(format!(
            "{label} is not a lowercase 16-digit f64 bit pattern"
        ));
    }
    let value = f64::from_bits(
        u64::from_str_radix(bits, 16).map_err(|error| format!("invalid {label}: {error}"))?,
    );
    if !value.is_finite() || value < 0.0 {
        return Err(format!("{label} is not a finite nonnegative f64"));
    }
    Ok(value)
}
