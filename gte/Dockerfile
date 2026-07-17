FROM docker.io/library/rust@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc AS rust-builder

RUN apt-get update \
    && apt-get install --yes --no-install-recommends clang cmake libclang-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /source
COPY Cargo.toml Cargo.lock ./
COPY models ./models
COPY src ./src
RUN cargo build --locked --release --bin gte-oracle

FROM docker.io/pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427

ARG ORACLE_MVP_SOURCE_COMMIT
RUN test -n "$ORACLE_MVP_SOURCE_COMMIT"
LABEL org.opencontainers.image.revision="$ORACLE_MVP_SOURCE_COMMIT"

ENV CUBLAS_WORKSPACE_CONFIG=:4096:8 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_OFFLINE=1 \
    NVIDIA_TF32_OVERRIDE=0 \
    PATH=/opt/gte-venv/bin:$PATH \
    PYTHONHASHSEED=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TOKENIZERS_PARALLELISM=false \
    TRANSFORMERS_OFFLINE=1 \
    UV_SYSTEM_PYTHON=1

COPY gte/requirements.lock /tmp/gte-locks/requirements.lock

RUN uv venv --system-site-packages /opt/gte-venv \
    && uv pip install \
        --python /opt/gte-venv/bin/python \
        --no-cache \
        --no-deps \
        --only-binary :all: \
        --require-hashes \
        --requirement /tmp/gte-locks/requirements.lock \
    && python -m pip check \
    && python -c 'import importlib.metadata as metadata, sys, torch; assert sys.version_info[:2] == (3, 12); assert metadata.version("torch") == "2.12.1+cu130"; assert torch.version.cuda == "13.0"; assert metadata.version("cuda-toolkit") == "13.0.2"; assert metadata.version("transformers") == "4.41.2"'

COPY --from=rust-builder /source/target/release/gte-oracle /usr/local/bin/gte-oracle
COPY gte/worker.py /opt/oracle-mvp/gte/worker.py
COPY gte/model_bundle.py /opt/oracle-mvp/gte/model_bundle.py
COPY gte/calibration_package.py /opt/oracle-mvp/gte/calibration_package.py

ENTRYPOINT ["/usr/local/bin/gte-oracle"]
