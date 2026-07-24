# Oracle MVP v1 Artifact Locations

The frozen experiment artifacts live outside Git under
`damus_snapshot/runs/`. Cargo's `oracle-mvp/target/` is disposable build and
preview state; it must not contain durable experiment evidence.

## Canonical Runs

- Complete public representation:
  `crec-72-gte-full-build-v5/result/work/representation/`
- Seed-source recovery and curation:
  `crec-92-seeds-v1/`
- Completed seed-selection session:
  `crec-95-seed-selection-v1/`
- Phase 3 adaptive learning:
  `crec-96-phase3-learning-v1/`
- Phase 4 final evaluation:
  `crec-99-phase4-final-v1/`

`crec-92-seeds-v1/` contains private reaction history. Its directory remains
owner-only, and its `retained-files.sha256` inventory covers the 107 relocated
evidence files.

`crec-95-seed-selection-v1/` retains the completed session, all 164 unique
Oracle responses, the selected-seed handoff, the candidate IDs, and the exact
config and runner used for the original execution. The config and runner retain
their historical absolute paths and are evidence, not runnable entrypoints.
Its `retained-files.sha256` inventory covers the 169 retained evidence files.

## CREC-95 Deduplication

The following CREC-95 inputs were omitted from the relocated package because
they are exact copies of canonical artifacts:

- Corpus:
  `crec-72-gte-full-build-v5/result/package/corpus-root/ndb/data.mdb`,
  SHA-256
  `8c6e8b7798a52639f78bd4a0ba4276d72784e4d1f149e3d5925d95289ae62bad`
- Ordered event IDs:
  `crec-72-gte-full-build-v5/result/package/run/semantic-corpus/ordered-event-ids.bin`,
  SHA-256
  `5b161558645a66ac93418d47ac6fc77daff761940200f6fddc07b30587e78c39`
- Representation:
  `crec-72-gte-full-build-v5/result/work/representation/`, version
  `5365b29f5e41d361cfae4b3a1754501d5320728053887236449071d680302c50`

The LMDB lock and session lock were runtime state and were not retained. The
selected-seed handoff is also copied into
`crec-96-phase3-learning-v1/input/seed-selection-handoff.json`; both copies have
SHA-256
`89682e1915c99783d194e370494565bfcdf0d909ba5e1fe32ad75e2862d85972`.
