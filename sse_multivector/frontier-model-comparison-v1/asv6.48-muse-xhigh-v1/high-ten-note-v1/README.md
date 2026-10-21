# ASv6.48 — Muse high, ten-note completion test

Status: completed 2026-09-21 UTC. ASv6.48 remained unchanged.

All 10 notes completed normally and passed the requested JSON schema: nine new calls and the existing N031 high result. Each note has one high attempt in this sample, with no retries. Hierarchy quality has **not** been assessed against Astra.

| Note | Seconds | Subjects | Result source |
| --- | ---: | ---: | --- |
| N004 | 165.103 | 15 | New |
| N038 | 174.433 | 16 | New |
| N065 | 236.098 | 43 | New |
| N031 | 239.702 | 45 | Reused `../high-uncapped-v1/result.json` |
| N080 | 370.055 | 137 | New |
| N094 | 177.012 | 30 | New |
| N096 | 383.559 | 94 | New |
| N061 | 270.340 | 37 | New |
| N029 | 100.011 | 7 | New |
| N052 | 206.642 | 11 | New |

## Conditions and execution

- Same saved rendered ASv6.48 prompts, checked against `../cases.json` hashes; same schema and uncapped high request as the saved N031 diagnostic.
- OpenRouter through the existing local credential service and diagnostic HTTP replay. No direct Meta requests or proxy changes.
- No caller token cap. The provider independently inserted `max_output_tokens: 65536`, as in the preceding uncapped diagnostics. Returned debug settings confirm `high` and the same schema on every note.
- The first six new requests started sequentially. After the user rejected that constraint, N061, N029 and N052 were launched together while N096 remained active. Four was the number of unfinished notes at that point, not an established provider limit.
- Exclusive per-note directory creation prevented duplicate sends during the handoff. The original process saved N096 successfully, then exited when N061 was already claimed. Its nonzero exit is not a model failure.
- Final receipt: `summary.json`; per-note requests, full event traces, outputs and mechanical assessments are retained in each note directory. `parallel-attempt.json` records the concurrent handoff. Collection makes no inference calls.
- Fourteen diagnostic tests passed, including real mock HTTP calls checking concurrent dispatch, exact inputs, failure accounting and duplicate refusal. All outputs also have unique hierarchy numbers and no missing numbered parents.

## Interpretation and next step

High is a promising workaround on this sample, not a demonstrated upstream fix or a guarantee of reliability. N080 survived a 272.122-second gap between model events, close to the approximately 300-second gaps preceding prior failures. Successful calls took 100–384 seconds.

New customer spend: $0.0374322, recorded as 4 cents in the ledger. The previously settled N031 charge is not counted again. No requests remain active.

Next: compare these saved hierarchies with the saved Astra ASv6.48 outputs named in `../cases.json`. No additional inference is required. Do not substitute Muse low for the requested Astra comparison.

## Publication files

Selected final answers, assessments, measurements, inputs and settings retain N031 as a reference to its saved answer in the earlier variant study.

`historical-studies/frontier-asv6.48-muse-high-ten-note-v1` appears in the
[catalog](../../../../docs/experiments/publications.csv) and [dataset manifest](../../../../docs/experiments/downloads.md#dataset-manifest).
These files are prepared locally for Hugging Face Datasets; downloads are not
available yet. Recorded pre-ASv6.100 derivatives remain deprecated historical evidence.
