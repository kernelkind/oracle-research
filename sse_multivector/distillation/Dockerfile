FROM pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server openssh-client \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*

ENV PATH=/opt/distillation-venv/bin:$PATH \
    DISTILLATION_GPU_PACKAGES=/opt/distillation-gpu \
    HF_HUB_DISABLE_TELEMETRY=1 \
    TOKENIZERS_PARALLELISM=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY sse_multivector/distillation/requirements.lock /tmp/requirements.lock
RUN uv venv --system-site-packages /opt/distillation-venv \
    && uv pip install --python /opt/distillation-venv/bin/python \
        --no-cache --no-deps --only-binary :all: --require-hashes \
        --requirement /tmp/requirements.lock \
    && python -m pip check \
    && python -c 'import torch, transformers, peft; assert torch.__version__ == "2.12.1+cu130"'

COPY sse_multivector/distillation/requirements-gpu.lock /tmp/requirements-gpu.lock
RUN uv pip install --python /opt/distillation-venv/bin/python --target /opt/distillation-gpu \
    --no-cache --no-deps --only-binary :all: --require-hashes \
    --requirement /tmp/requirements-gpu.lock

WORKDIR /work
COPY gte/full_build_package.py /work/gte/
COPY sse_multivector/distillation/requirements.lock sse_multivector/distillation/Dockerfile \
    sse_multivector/distillation/requirements-gpu.lock \
    sse_multivector/distillation/vast-launch.json \
    /work/sse_multivector/distillation/
COPY sse_multivector/distillation_run.py sse_multivector/distillation_data.py \
    sse_multivector/extraction_pipeline.py sse_multivector/mask_positions.py \
    sse_multivector/test_distillation_run.py sse_multivector/test_distillation_data.py \
    sse_multivector/distillation_deploy.py sse_multivector/test_distillation_deploy.py \
    sse_multivector/test_distillation_candidates.py \
    /work/sse_multivector/
CMD ["python", "-m", "sse_multivector.distillation_run", "--help"]
