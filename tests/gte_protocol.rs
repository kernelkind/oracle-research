use std::fs;
use std::path::PathBuf;

use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig, TokenRole};
use oracle_mvp::representation::RepresentationEncoder;
use sha2::{Digest, Sha256};

#[test]
fn rust_client_verifies_the_attested_worker_handshake_and_reports_worker_errors() {
    let identity = tempfile::tempdir().expect("identity directory");
    let model_dir = identity.path().join("model");
    fs::create_dir(&model_dir).expect("empty model directory");
    let model_lock_path = identity.path().join("model-lock.json");
    let dependency_lock_path = identity.path().join("requirements.lock");
    fs::write(&model_lock_path, b"model lock\n").expect("model lock");
    fs::write(&dependency_lock_path, b"dependency lock\n").expect("dependency lock");
    let worker_path = identity.path().join("attested_worker.py");
    fs::write(&worker_path, FAKE_ATTESTED_WORKER).expect("fake attested worker");
    let config = GteWorkerConfig {
        program: PathBuf::from("python3"),
        prefix_arguments: Vec::new(),
        worker_path: Some(worker_path.clone()),
        model_dir,
        model_lock_path: model_lock_path.clone(),
        dependency_lock_path: dependency_lock_path.clone(),
        device: "cpu".to_owned(),
        model_lock_sha256: hash(&model_lock_path),
        worker_sha256: hash(&worker_path),
        dependency_lock_sha256: hash(&dependency_lock_path),
        container_image: "local-test@sha256:".to_owned() + &"4".repeat(64),
        torch_version: "2.12.1".to_owned(),
        transformers_version: "4.41.2".to_owned(),
        cuda_version: "13.0.2".to_owned(),
    };
    let mut worker = GteProcessEncoder::start(config.clone()).expect("start real worker");

    assert_eq!(
        worker.descriptor().model_id,
        "Alibaba-NLP/gte-Qwen2-7B-instruct"
    );
    assert_eq!(worker.descriptor().dimensions, 3_584);
    assert_eq!(worker.descriptor().numeric_format, "f32le");
    assert_eq!(worker.descriptor().execution_device, "cpu");
    assert_eq!(worker.descriptor().torch_version, "2.12.1");
    assert_eq!(worker.descriptor().transformers_version, "4.41.2");
    assert_eq!(worker.descriptor().cuda_version, "13.0.2");

    let error = worker
        .token_lengths(TokenRole::Document, &["real request"])
        .expect_err("missing model must be a worker error");
    assert!(error.to_string().contains("fixture has no tokenizer"));
    drop(worker);

    let mut mislabeled = config.clone();
    mislabeled.worker_sha256 = "0".repeat(64);
    let error = GteProcessEncoder::start(mislabeled)
        .err()
        .expect("worker identity mismatch must be rejected");
    assert!(
        error
            .to_string()
            .contains("incompatible protocol or representation")
    );

    let mut false_runtime = config;
    false_runtime.torch_version = "0.0.0".to_owned();
    let error = GteProcessEncoder::start(false_runtime)
        .err()
        .expect("runtime identity mismatch must be rejected");
    assert!(
        error
            .to_string()
            .contains("incompatible protocol or representation")
    );
}

const FAKE_ATTESTED_WORKER: &str = r#"
import argparse, hashlib, json, struct, sys

frame_length = struct.Struct('<Q')
metadata_length = struct.Struct('<I')

def read_exact(length):
    output = b''
    while len(output) < length:
        chunk = sys.stdin.buffer.read(length - len(output))
        if not chunk:
            raise SystemExit(0)
        output += chunk
    return output

def read_frame():
    length = frame_length.unpack(read_exact(8))[0]
    body = read_exact(length)
    metadata_bytes = metadata_length.unpack(body[:4])[0]
    return json.loads(body[4:4 + metadata_bytes]), body[4 + metadata_bytes:]

def write_frame(metadata, payload=b''):
    encoded = json.dumps(metadata, separators=(',', ':')).encode()
    body = metadata_length.pack(len(encoded)) + encoded + payload
    sys.stdout.buffer.write(frame_length.pack(len(body)) + body)
    sys.stdout.buffer.flush()

def sha256(path):
    with open(path, 'rb') as source:
        return hashlib.sha256(source.read()).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--model-dir')
parser.add_argument('--model-lock-path')
parser.add_argument('--dependency-lock-path')
parser.add_argument('--device')
args = parser.parse_args()
write_frame({
    'type': 'hello',
    'protocol': 'nd-gte-framed-stdio',
    'protocol_version': 1,
    'model_id': 'Alibaba-NLP/gte-Qwen2-7B-instruct',
    'model_revision': 'a8d08b36ada9cacfe34c4d6f80957772a025daf2',
    'dimensions': 3584,
    'model_token_ceiling': 32768,
    'scalar_type': 'float32',
    'byte_order': 'little',
    'execution_device': args.device,
    'worker_sha256': sha256(__file__),
    'model_lock_sha256': sha256(args.model_lock_path),
    'dependency_lock_sha256': sha256(args.dependency_lock_path),
    'python_version': '3.12.3',
    'torch_version': '2.12.1',
    'torch_build_version': '2.12.1+cu130',
    'torch_cuda_version': '13.0',
    'transformers_version': '4.41.2',
    'cuda_version': '13.0.2',
})
while True:
    request, payload = read_frame()
    if request['type'] == 'shutdown':
        write_frame({'type': 'ok', 'request_id': request['request_id'], 'operation': 'shutdown'})
        raise SystemExit(0)
    write_frame({
        'type': 'error',
        'request_id': request['request_id'],
        'code': 'tokenizer_load_failed',
        'message': 'fixture has no tokenizer',
    })
"#;

fn hash(path: &std::path::Path) -> String {
    let bytes = fs::read(path).expect("hash input");
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}
