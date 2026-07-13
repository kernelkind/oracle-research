//! Frozen `pplx-embed-v1-0.6b` tokenizer and ONNX inference path.

use std::fs;
use std::path::{Path, PathBuf};

use ort::session::{HasSelectedOutputs, OutputSelector, RunOptions, Session};
use ort::value::Tensor;
use serde::Deserialize;
use tokenizers::{
    PaddingDirection, PaddingParams, PaddingStrategy, Tokenizer, TruncationDirection,
    TruncationParams, TruncationStrategy,
};

use crate::artifact::{hash_bytes, hash_file};
use crate::embedding::{EmbeddingEncoder, EncoderDescriptor};
use crate::snapshot::{Error, Result, io_error, require_file};

const MODEL_ID: &str = "perplexity-ai/pplx-embed-v1-0.6b";
const MODEL_REVISION: &str = "2c4d510dd4a732063c31a0f70193e35067b51fd8";
const MODEL_LOCK_JSON: &str = include_str!("../models/pplx-embed-v1-0.6b.lock.json");
const DIMENSIONS: usize = 1_024;
const MAX_TOKENS: usize = 512;
const OUTPUT_NAME: &str = "pooler_output_int8";
const END_OF_TEXT: &str = "<|endoftext|>";
const END_OF_TEXT_ID: u32 = 151_643;
const INPUT_RULE: &str = "raw-utf8-url-text-empty-as-eot-add-special-tokens-right-truncate-512-v1";

/// Stable directory name for the CREC-4 preflight artifact.
pub const PREFLIGHT_ARTIFACT_NAME: &str = "pplx-embed-v1-0.6b-int8-1024d-preflight-v1";

/// ONNX Runtime execution provider selected for one artifact build.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExecutionProvider {
    /// Run inference on the CPU provider.
    Cpu,
    /// Run inference on the CUDA provider.
    Cuda,
}

impl ExecutionProvider {
    /// Stable value recorded in the embedding manifest.
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Cpu => "cpu",
            Self::Cuda => "cuda",
        }
    }
}

/// Filesystem and runtime inputs required to construct the frozen encoder.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PplxOnnxConfig {
    /// Directory containing the exact locked Hugging Face model files.
    pub model_dir: PathBuf,
    /// ONNX Runtime shared library to load.
    pub runtime_library: PathBuf,
    /// Runtime provider used for inference.
    pub execution_provider: ExecutionProvider,
}

/// Real native-INT8 encoder used by the oracle preflight.
pub struct PplxOnnxEncoder {
    config: PplxOnnxConfig,
    backend: Option<PplxOnnxBackend>,
    descriptor: EncoderDescriptor,
}

struct PplxOnnxBackend {
    tokenizer: Tokenizer,
    session: Session,
    run_options: RunOptions<HasSelectedOutputs>,
}

impl PplxOnnxEncoder {
    /// Verify the frozen files and prepare a lazily loaded ONNX encoder.
    pub fn load(mut config: PplxOnnxConfig) -> Result<Self> {
        config.model_dir = fs::canonicalize(&config.model_dir)
            .map_err(|source| io_error("resolve", &config.model_dir, source))?;
        config.runtime_library = fs::canonicalize(&config.runtime_library)
            .map_err(|source| io_error("resolve", &config.runtime_library, source))?;
        let lock = verify_model_files(&config.model_dir)?;
        require_file(&config.runtime_library)?;
        let runtime_sha256 = hash_file(&config.runtime_library)?;
        let descriptor = EncoderDescriptor {
            model_id: lock.model_id,
            model_revision: lock.revision,
            model_lock_sha256: hash_bytes(MODEL_LOCK_JSON.as_bytes()),
            runtime: "onnxruntime".to_owned(),
            runtime_version: format!("ort-2.0.0-rc.12/api-{}", ort::MINOR_VERSION),
            runtime_sha256,
            execution_provider: config.execution_provider.as_str().to_owned(),
            output_name: OUTPUT_NAME.to_owned(),
            dimensions: u32::try_from(DIMENSIONS).expect("dimensions fit u32"),
            max_tokens: u32::try_from(MAX_TOKENS).expect("token ceiling fits u32"),
            input_rule: INPUT_RULE.to_owned(),
            pooling: "model-native-mean".to_owned(),
            quantization: "native-int8".to_owned(),
            instruction: None,
        };
        Ok(Self {
            config,
            backend: None,
            descriptor,
        })
    }

    fn backend(&mut self) -> Result<&mut PplxOnnxBackend> {
        if self.backend.is_none() {
            self.backend = Some(PplxOnnxBackend::load(&self.config)?);
        }
        self.backend
            .as_mut()
            .ok_or_else(|| Error::Invariant("ONNX backend did not initialize".to_owned()))
    }
}

impl PplxOnnxBackend {
    fn load(config: &PplxOnnxConfig) -> Result<Self> {
        let tokenizer_path = config.model_dir.join("tokenizer.json");
        let mut tokenizer = Tokenizer::from_file(&tokenizer_path)
            .map_err(|source| encoder_error("loading tokenizer", source))?;
        if tokenizer.token_to_id(END_OF_TEXT) != Some(END_OF_TEXT_ID) {
            return Err(Error::Invariant(format!(
                "tokenizer does not map `{END_OF_TEXT}` to {END_OF_TEXT_ID}"
            )));
        }
        tokenizer
            .with_truncation(Some(TruncationParams {
                direction: TruncationDirection::Right,
                max_length: MAX_TOKENS,
                strategy: TruncationStrategy::LongestFirst,
                stride: 0,
            }))
            .map_err(|source| encoder_error("configuring tokenizer truncation", source))?;
        tokenizer.with_padding(Some(PaddingParams {
            strategy: PaddingStrategy::BatchLongest,
            direction: PaddingDirection::Right,
            pad_to_multiple_of: None,
            pad_id: END_OF_TEXT_ID,
            pad_type_id: 0,
            pad_token: END_OF_TEXT.to_owned(),
        }));

        let committed = ort::init_from(&config.runtime_library)
            .map_err(|source| encoder_error("loading ONNX Runtime", source))?
            .commit();
        if !committed {
            return Err(Error::Encoder {
                operation: "loading ONNX Runtime",
                message: "an ONNX Runtime environment was already initialized in this process"
                    .to_owned(),
            });
        }
        let mut builder = Session::builder()
            .map_err(|source| encoder_error("creating ONNX session options", source))?;
        if config.execution_provider == ExecutionProvider::Cuda {
            builder = builder
                .with_execution_providers([ort::ep::CUDA::default().build().error_on_failure()])
                .map_err(|source| encoder_error("configuring CUDA execution", source))?;
        }
        let model_path = config.model_dir.join("onnx/model.onnx");
        let session = builder
            .commit_from_file(&model_path)
            .map_err(|source| encoder_error("loading ONNX model", source))?;
        if !session
            .outputs()
            .iter()
            .any(|output| output.name() == OUTPUT_NAME)
        {
            return Err(Error::Encoder {
                operation: "loading ONNX model",
                message: format!("model does not expose `{OUTPUT_NAME}`"),
            });
        }
        let run_options = RunOptions::new()
            .map_err(|source| encoder_error("creating ONNX run options", source))?
            .with_outputs(OutputSelector::no_default().with(OUTPUT_NAME));
        Ok(Self {
            tokenizer,
            session,
            run_options,
        })
    }
}

impl EmbeddingEncoder for PplxOnnxEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn encode(&mut self, texts: &[&str]) -> Result<Vec<i8>> {
        if texts.is_empty() {
            return Ok(Vec::new());
        }
        let inputs = texts
            .iter()
            .map(|text| if text.is_empty() { END_OF_TEXT } else { *text })
            .collect::<Vec<_>>();
        let backend = self.backend()?;
        let encodings = backend
            .tokenizer
            .encode_batch(inputs, true)
            .map_err(|source| encoder_error("tokenizing input batch", source))?;
        let sequence_length = encodings
            .first()
            .map(|encoding| encoding.get_ids().len())
            .ok_or_else(|| Error::Invariant("tokenizer returned an empty batch".to_owned()))?;
        if sequence_length == 0
            || encodings
                .iter()
                .any(|encoding| encoding.get_ids().len() != sequence_length)
        {
            return Err(Error::Invariant(
                "tokenizer did not return a nonempty rectangular batch".to_owned(),
            ));
        }

        let elements = texts.len().checked_mul(sequence_length).ok_or_else(|| {
            Error::Invariant("tokenized batch element count overflowed usize".to_owned())
        })?;
        let mut input_ids = Vec::with_capacity(elements);
        let mut attention_mask = Vec::with_capacity(elements);
        for encoding in &encodings {
            input_ids.extend(encoding.get_ids().iter().map(|value| i64::from(*value)));
            attention_mask.extend(
                encoding
                    .get_attention_mask()
                    .iter()
                    .map(|value| i64::from(*value)),
            );
        }
        let shape = [texts.len(), sequence_length];
        let input_ids = Tensor::from_array((shape, input_ids))
            .map_err(|source| encoder_error("constructing input-ID tensor", source))?;
        let attention_mask = Tensor::from_array((shape, attention_mask))
            .map_err(|source| encoder_error("constructing attention-mask tensor", source))?;
        let outputs = backend
            .session
            .run_with_options(
                ort::inputs! {
                    "input_ids" => input_ids,
                    "attention_mask" => attention_mask,
                },
                &backend.run_options,
            )
            .map_err(|source| encoder_error("running ONNX inference", source))?;
        let output = outputs.get(OUTPUT_NAME).ok_or_else(|| Error::Encoder {
            operation: "reading ONNX output",
            message: format!("inference did not return `{OUTPUT_NAME}`"),
        })?;
        let (output_shape, vectors) = output
            .try_extract_tensor::<i8>()
            .map_err(|source| encoder_error("reading native-INT8 output", source))?;
        let expected_shape = [
            i64::try_from(texts.len())
                .map_err(|_| Error::Invariant("batch size does not fit i64".to_owned()))?,
            i64::try_from(DIMENSIONS)
                .map_err(|_| Error::Invariant("dimensions do not fit i64".to_owned()))?,
        ];
        if output_shape.as_ref() != expected_shape {
            return Err(Error::Invariant(format!(
                "ONNX output shape {output_shape} does not match {:?}",
                expected_shape
            )));
        }
        Ok(vectors.to_vec())
    }
}

#[derive(Debug, Deserialize, Eq, PartialEq)]
struct ModelLock {
    schema_version: u32,
    model_id: String,
    revision: String,
    files: Vec<ModelFile>,
}

#[derive(Debug, Deserialize, Eq, PartialEq)]
struct ModelFile {
    path: String,
    bytes: u64,
    sha256: String,
}

fn verify_model_files(model_dir: &Path) -> Result<ModelLock> {
    let lock: ModelLock =
        serde_json::from_str(MODEL_LOCK_JSON).map_err(|source| Error::Manifest {
            operation: "decode embedded model lock",
            path: PathBuf::from("models/pplx-embed-v1-0.6b.lock.json"),
            source,
        })?;
    if lock.schema_version != 1 || lock.model_id != MODEL_ID || lock.revision != MODEL_REVISION {
        return Err(Error::Invariant(
            "embedded pplx model lock has an unsupported identity".to_owned(),
        ));
    }
    for file in &lock.files {
        let path = model_dir.join(&file.path);
        require_file(&path)?;
        let bytes = fs::metadata(&path)
            .map_err(|source| io_error("read metadata for", &path, source))?
            .len();
        if bytes != file.bytes {
            return Err(Error::Invariant(format!(
                "model file `{}` has {bytes} bytes but lock records {}",
                path.display(),
                file.bytes
            )));
        }
        let sha256 = hash_file(&path)?;
        if sha256 != file.sha256 {
            return Err(Error::Invariant(format!(
                "model file `{}` checksum does not match the lock",
                path.display()
            )));
        }
    }
    Ok(lock)
}

fn encoder_error(operation: &'static str, source: impl std::fmt::Display) -> Error {
    Error::Encoder {
        operation,
        message: source.to_string(),
    }
}
