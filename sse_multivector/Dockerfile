FROM pytorch/pytorch@sha256:72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26bc469de4c8a28b427

ENV PATH=/opt/sse-venv/bin:$PATH

COPY sse_multivector/requirements.lock /tmp/requirements.lock
RUN uv venv --system-site-packages /opt/sse-venv \
    && uv pip install \
        --python /opt/sse-venv/bin/python \
        --no-cache \
        --no-deps \
        --only-binary :all: \
        --require-hashes \
        --requirement /tmp/requirements.lock \
    && python -m pip check \
    && rm /tmp/requirements.lock
