FROM pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427 AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server openssh-client util-linux \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*

ENV PATH=/opt/distillation-venv/bin:$PATH \
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
    --requirement /tmp/requirements-gpu.lock \
    && PYTHONPATH=/opt/distillation-gpu python -m pip check

WORKDIR /work
FROM runtime
COPY gte/full_build_package.py gte/calibration_package.py gte/vast_private_create.py /work/gte/
COPY sse_multivector/distillation/requirements.lock sse_multivector/distillation/Dockerfile \
    sse_multivector/distillation/requirements-gpu.lock \
    sse_multivector/distillation/vast-launch.json \
    /work/sse_multivector/distillation/
COPY sse_multivector/distillation_run.py sse_multivector/distillation_data.py \
    sse_multivector/extraction_pipeline.py sse_multivector/mask_positions.py \
    sse_multivector/test_distillation_run.py sse_multivector/test_distillation_data.py \
    sse_multivector/distillation_deploy.py sse_multivector/test_distillation_deploy.py \
    sse_multivector/distillation_cache.py sse_multivector/test_distillation_cache.py \
    sse_multivector/test_distillation_candidates.py \
    sse_multivector/distillation_vast.py sse_multivector/test_distillation_vast.py \
    /work/sse_multivector/
COPY vast/runner.py vast/package.py /work/vast/
EXPOSE 22
# Vast replaces the image entrypoint with managed SSH and runs the frozen onstart.
ENTRYPOINT ["/bin/bash"]
