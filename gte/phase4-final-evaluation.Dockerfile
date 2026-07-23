FROM docker.io/library/rust@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc AS rust-builder

RUN apt-get update \
    && apt-get install --yes --no-install-recommends clang cmake libclang-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /source
COPY Cargo.toml Cargo.lock ./
COPY models ./models
COPY src ./src
RUN cargo build --locked --release --bin phase4-final-evaluation

FROM docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a

ARG ORACLE_MVP_SOURCE_COMMIT
RUN test -n "$ORACLE_MVP_SOURCE_COMMIT"
LABEL org.opencontainers.image.revision="$ORACLE_MVP_SOURCE_COMMIT"

COPY --from=rust-builder /source/target/release/phase4-final-evaluation /usr/local/bin/phase4-final-evaluation

ENTRYPOINT ["/usr/local/bin/phase4-final-evaluation"]
