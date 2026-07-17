//! Persistent framed-stdio client for the pinned Python GTE worker.

use std::ffi::OsString;
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};

use serde_json::{Value, json};

use crate::representation::{RepresentationDescriptor, RepresentationEncoder};
use crate::snapshot::{Error, Result};

pub const MODEL_ID: &str = "Alibaba-NLP/gte-Qwen2-7B-instruct";
pub const MODEL_REVISION: &str = "a8d08b36ada9cacfe34c4d6f80957772a025daf2";
pub const DIMENSIONS: u32 = 3_584;
pub const MODEL_TOKEN_CEILING: u32 = 32_768;
pub const QUERY_INSTRUCTION: &str = "Instruct: Given a note, retrieve other notes related to the interests it expresses\nQuery: {raw note content}";

const PROTOCOL: &str = "nd-gte-framed-stdio";
const PROTOCOL_VERSION: u64 = 1;
const MAX_FRAME_BYTES: u64 = 256 * 1024 * 1024;
const PYTHON_VERSION_PREFIX: &str = "3.12.";
const TORCH_BUILD_VERSION: &str = "2.12.1+cu130";
const TORCH_CUDA_VERSION: &str = "13.0";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TokenRole {
    Document,
    Query,
}

impl TokenRole {
    fn as_str(self) -> &'static str {
        match self {
            Self::Document => "document",
            Self::Query => "query",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GteWorkerConfig {
    pub program: PathBuf,
    pub prefix_arguments: Vec<OsString>,
    pub worker_path: Option<PathBuf>,
    pub model_dir: PathBuf,
    pub model_lock_path: PathBuf,
    pub dependency_lock_path: PathBuf,
    pub device: String,
    pub model_lock_sha256: String,
    pub worker_sha256: String,
    pub dependency_lock_sha256: String,
    pub container_image: String,
    pub torch_version: String,
    pub transformers_version: String,
    pub cuda_version: String,
}

pub struct GteProcessEncoder {
    child: Child,
    input: BufWriter<ChildStdin>,
    output: BufReader<ChildStdout>,
    descriptor: RepresentationDescriptor,
    next_request: u64,
}

impl GteProcessEncoder {
    pub fn start(config: GteWorkerConfig) -> Result<Self> {
        validate_config(&config)?;
        let mut command = Command::new(&config.program);
        command.args(&config.prefix_arguments);
        if let Some(worker_path) = &config.worker_path {
            command.arg(worker_path);
        }
        let mut child = command
            .arg("--model-dir")
            .arg(&config.model_dir)
            .arg("--model-lock-path")
            .arg(&config.model_lock_path)
            .arg("--dependency-lock-path")
            .arg(&config.dependency_lock_path)
            .arg("--device")
            .arg(&config.device)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|error| worker_error("start worker", error.to_string()))?;
        let input = child
            .stdin
            .take()
            .ok_or_else(|| worker_error("start worker", "worker stdin is unavailable"))?;
        let output = child
            .stdout
            .take()
            .ok_or_else(|| worker_error("start worker", "worker stdout is unavailable"))?;
        let mut output = BufReader::new(output);
        let (hello, payload) = read_frame(&mut output)?;
        let actual_torch_version = hello
            .get("torch_version")
            .and_then(Value::as_str)
            .map(str::to_owned);
        let actual_transformers_version = hello
            .get("transformers_version")
            .and_then(Value::as_str)
            .map(str::to_owned);
        let actual_cuda_version = hello
            .get("cuda_version")
            .and_then(Value::as_str)
            .map(str::to_owned);
        if !payload.is_empty()
            || hello.get("type").and_then(Value::as_str) != Some("hello")
            || hello.get("protocol").and_then(Value::as_str) != Some(PROTOCOL)
            || hello.get("protocol_version").and_then(Value::as_u64) != Some(PROTOCOL_VERSION)
            || hello.get("model_id").and_then(Value::as_str) != Some(MODEL_ID)
            || hello.get("model_revision").and_then(Value::as_str) != Some(MODEL_REVISION)
            || hello.get("dimensions").and_then(Value::as_u64) != Some(u64::from(DIMENSIONS))
            || hello.get("model_token_ceiling").and_then(Value::as_u64)
                != Some(u64::from(MODEL_TOKEN_CEILING))
            || hello.get("scalar_type").and_then(Value::as_str) != Some("float32")
            || hello.get("byte_order").and_then(Value::as_str) != Some("little")
            || hello.get("execution_device").and_then(Value::as_str) != Some(config.device.as_str())
            || hello.get("worker_sha256").and_then(Value::as_str)
                != Some(config.worker_sha256.as_str())
            || hello.get("model_lock_sha256").and_then(Value::as_str)
                != Some(config.model_lock_sha256.as_str())
            || hello.get("dependency_lock_sha256").and_then(Value::as_str)
                != Some(config.dependency_lock_sha256.as_str())
            || !hello
                .get("python_version")
                .and_then(Value::as_str)
                .is_some_and(|version| version.starts_with(PYTHON_VERSION_PREFIX))
            || actual_torch_version.as_deref() != Some(config.torch_version.as_str())
            || hello.get("torch_build_version").and_then(Value::as_str) != Some(TORCH_BUILD_VERSION)
            || hello.get("torch_cuda_version").and_then(Value::as_str) != Some(TORCH_CUDA_VERSION)
            || actual_transformers_version.as_deref() != Some(config.transformers_version.as_str())
            || actual_cuda_version.as_deref() != Some(config.cuda_version.as_str())
        {
            let _ = child.kill();
            let _ = child.wait();
            return Err(worker_error(
                "verify worker handshake",
                "worker reported an incompatible protocol or representation",
            ));
        }
        Ok(Self {
            child,
            input: BufWriter::new(input),
            output,
            descriptor: RepresentationDescriptor {
                model_id: MODEL_ID.to_owned(),
                model_revision: MODEL_REVISION.to_owned(),
                model_lock_sha256: config.model_lock_sha256,
                worker_sha256: config.worker_sha256,
                dependency_lock_sha256: config.dependency_lock_sha256,
                container_image: config.container_image,
                torch_version: actual_torch_version.expect("verified worker torch version"),
                transformers_version: actual_transformers_version
                    .expect("verified worker Transformers version"),
                cuda_version: actual_cuda_version.expect("verified worker CUDA version"),
                execution_device: config.device,
                dimensions: DIMENSIONS,
                model_token_ceiling: MODEL_TOKEN_CEILING,
                document_input: "raw-note-content".to_owned(),
                query_instruction: QUERY_INSTRUCTION.to_owned(),
                pooling: "last-token".to_owned(),
                normalization: "l2".to_owned(),
                numeric_format: "f32le".to_owned(),
            },
            next_request: 0,
        })
    }

    pub fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        let (metadata, payload) = self.request("token_lengths", role, texts)?;
        if metadata.get("type").and_then(Value::as_str) != Some("token_lengths")
            || metadata.get("rows").and_then(Value::as_u64) != Some(texts.len() as u64)
            || metadata.get("payload_format").and_then(Value::as_str) != Some("uint32-le")
            || payload.len() != texts.len() * size_of::<u32>()
        {
            return Err(worker_error(
                "decode token lengths",
                "worker returned an incompatible token-length response",
            ));
        }
        Ok(payload
            .chunks_exact(size_of::<u32>())
            .map(|bytes| u32::from_le_bytes(bytes.try_into().expect("u32 width")))
            .collect())
    }

    fn encode(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<f32>> {
        let (metadata, payload) = self.request("encode", role, texts)?;
        let expected_values = texts
            .len()
            .checked_mul(DIMENSIONS as usize)
            .ok_or_else(|| worker_error("decode embeddings", "response width overflowed"))?;
        if metadata.get("type").and_then(Value::as_str) != Some("embeddings")
            || metadata.get("rows").and_then(Value::as_u64) != Some(texts.len() as u64)
            || metadata.get("dimensions").and_then(Value::as_u64) != Some(u64::from(DIMENSIONS))
            || metadata.get("payload_format").and_then(Value::as_str)
                != Some("float32-le-row-major")
            || payload.len() != expected_values * size_of::<f32>()
        {
            return Err(worker_error(
                "decode embeddings",
                "worker returned an incompatible embedding response",
            ));
        }
        let vectors = payload
            .chunks_exact(size_of::<f32>())
            .map(|bytes| f32::from_le_bytes(bytes.try_into().expect("f32 width")))
            .collect::<Vec<_>>();
        if vectors.iter().any(|value| !value.is_finite()) {
            return Err(worker_error(
                "decode embeddings",
                "worker returned a non-finite FP32 value",
            ));
        }
        Ok(vectors)
    }

    fn request(
        &mut self,
        operation: &'static str,
        role: TokenRole,
        texts: &[&str],
    ) -> Result<(Value, Vec<u8>)> {
        if texts.is_empty() {
            return Err(worker_error(operation, "request batch is empty"));
        }
        self.next_request = self
            .next_request
            .checked_add(1)
            .ok_or_else(|| worker_error(operation, "request counter overflowed"))?;
        let request_id = format!("rust-{}", self.next_request);
        let lengths = texts.iter().map(|text| text.len()).collect::<Vec<_>>();
        let payload = texts
            .iter()
            .flat_map(|text| text.as_bytes().iter().copied())
            .collect::<Vec<_>>();
        let metadata = json!({
            "type": operation,
            "request_id": request_id,
            "role": role.as_str(),
            "text_lengths": lengths,
        });
        write_frame(&mut self.input, &metadata, &payload)?;
        let (response, payload) = read_frame(&mut self.output)?;
        if response.get("request_id").and_then(Value::as_str) != Some(request_id.as_str()) {
            return Err(worker_error(
                operation,
                "worker response has a different request ID",
            ));
        }
        if response.get("type").and_then(Value::as_str) == Some("error") {
            let code = response
                .get("code")
                .and_then(Value::as_str)
                .unwrap_or("unknown_error");
            let message = response
                .get("message")
                .and_then(Value::as_str)
                .unwrap_or("worker returned no error message");
            return Err(worker_error(operation, format!("{code}: {message}")));
        }
        Ok((response, payload))
    }

    fn shutdown(&mut self) -> Result<()> {
        self.next_request = self.next_request.saturating_add(1);
        let request_id = format!("rust-{}", self.next_request);
        write_frame(
            &mut self.input,
            &json!({"type": "shutdown", "request_id": request_id}),
            &[],
        )?;
        let (response, payload) = read_frame(&mut self.output)?;
        if !payload.is_empty()
            || response.get("type").and_then(Value::as_str) != Some("ok")
            || response.get("request_id").and_then(Value::as_str) != Some(request_id.as_str())
            || response.get("operation").and_then(Value::as_str) != Some("shutdown")
        {
            return Err(worker_error(
                "shutdown worker",
                "worker returned an incompatible shutdown response",
            ));
        }
        Ok(())
    }
}

impl RepresentationEncoder for GteProcessEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        self.encode(TokenRole::Document, texts)
    }

    fn encode_queries(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        self.encode(TokenRole::Query, texts)
    }
}

impl Drop for GteProcessEncoder {
    fn drop(&mut self) {
        if self.child.try_wait().ok().flatten().is_none() && self.shutdown().is_err() {
            let _ = self.child.kill();
        }
        let _ = self.child.wait();
    }
}

fn write_frame(writer: &mut impl Write, metadata: &Value, payload: &[u8]) -> Result<()> {
    let metadata = serde_json::to_vec(metadata)
        .map_err(|error| worker_error("encode request", error.to_string()))?;
    let body_length = size_of::<u32>()
        .checked_add(metadata.len())
        .and_then(|length| length.checked_add(payload.len()))
        .ok_or_else(|| worker_error("encode request", "frame length overflowed"))?;
    if body_length as u64 > MAX_FRAME_BYTES || metadata.len() > u32::MAX as usize {
        return Err(worker_error("encode request", "request frame is too large"));
    }
    writer
        .write_all(&(body_length as u64).to_le_bytes())
        .and_then(|()| writer.write_all(&(metadata.len() as u32).to_le_bytes()))
        .and_then(|()| writer.write_all(&metadata))
        .and_then(|()| writer.write_all(payload))
        .and_then(|()| writer.flush())
        .map_err(|error| worker_error("write request", error.to_string()))
}

fn read_frame(reader: &mut impl Read) -> Result<(Value, Vec<u8>)> {
    let mut length = [0_u8; size_of::<u64>()];
    reader
        .read_exact(&mut length)
        .map_err(|error| worker_error("read response", error.to_string()))?;
    let body_length = u64::from_le_bytes(length);
    if body_length < size_of::<u32>() as u64 || body_length > MAX_FRAME_BYTES {
        return Err(worker_error(
            "read response",
            format!("invalid frame length {body_length}"),
        ));
    }
    let mut body = vec![0_u8; body_length as usize];
    reader
        .read_exact(&mut body)
        .map_err(|error| worker_error("read response", error.to_string()))?;
    let metadata_length = u32::from_le_bytes(
        body[..size_of::<u32>()]
            .try_into()
            .expect("metadata length width"),
    ) as usize;
    let metadata_end = size_of::<u32>() + metadata_length;
    if metadata_end > body.len() {
        return Err(worker_error(
            "read response",
            "metadata length exceeds the frame",
        ));
    }
    let metadata = serde_json::from_slice(&body[size_of::<u32>()..metadata_end])
        .map_err(|error| worker_error("decode response", error.to_string()))?;
    Ok((metadata, body[metadata_end..].to_vec()))
}

fn validate_config(config: &GteWorkerConfig) -> Result<()> {
    if config.device != "cpu" && config.device != "cuda" {
        return Err(worker_error(
            "start worker",
            "device must be `cpu` or `cuda`",
        ));
    }
    for hash in [
        &config.model_lock_sha256,
        &config.worker_sha256,
        &config.dependency_lock_sha256,
    ] {
        if hash.len() != 64 || !hash.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(worker_error("start worker", "runtime hash is not SHA-256"));
        }
    }
    Ok(())
}

fn worker_error(operation: &'static str, message: impl Into<String>) -> Error {
    Error::Encoder {
        operation,
        message: message.into(),
    }
}
