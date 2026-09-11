# SSE context counterfactual result

The immutable formal result is reported below. The subsequent review of what
the three failed comparisons scientifically establish is recorded in
[`scientific-interpretation.md`](scientific-interpretation.md).

## Question

Can SSE use surrounding text when that text is necessary to interpret a selected meaning, while preventing unrelated surrounding text from taking over the selected meaning?

The frozen experiment used 24 target vectors and 19 three-example reference groups. Each target passed only when the median cosine for its intended group was strictly greater than every declared alternative. There was no absolute cosine threshold.

## Frozen result

**Overall: fail.** Twenty-one of 24 target predictions passed.

| Verdict | Result | Direct targets |
|---|---:|---:|
| Self-contained baseline | Pass | 3/3 |
| Unrelated-context resistance | Pass | 6/6 |
| Context grounding | Fail | 4/6 |
| Mixed-note separation | Fail | 8/9 |
| Not blended | Fail | Composite |
| Overall | Fail | Composite |

All 1,368 target-to-reference cosines, 456 group medians, and 56 predeclared comparisons are retained in `analysis.json`.

## What passed

- All three meanings were recognizable when presented alone.
- Adding unrelated coffee or GPL text never displaced the unchanged selected meaning. The six winning margins ranged from `+0.600` to `+0.834`.
- All five meanings in the untouched Saturday note won their comparisons, including meanings that were legitimately related to one another.
- Three of four meanings in the untouched miner-control note won. The temperature-maintenance, temperature/day-night-control, and solar-use-measurement meanings remained distinguishable.
- Changing technology-surveillance context to financial-control context changed the winning interpretation of the same selected phrase in both directions. The financial-control direction was close: `0.4754` versus `0.4411`.

These are strong results for resistance to obviously unrelated context and promising results for separating several meanings inside a real mixed note.

## What failed

### Greenhouse retirement

Target:

> Flexicables installed for our geothermal solar powered greenhouse.  
> ⟦This will be the first steps to my non consumption based retirement.⟧

| Reference group | Three cosines | Median |
|---|---|---:|
| Greenhouse-enabled retirement, intended | `0.6213`, `0.7998`, `0.5929` | `0.6213` |
| Minimalism-enabled retirement | `0.7402`, `0.5971`, `0.6598` | `0.6598` |

The alternative won by `0.0385`. SSE represented low-consumption retirement strongly, but the greenhouse antecedent did not determine the result. The paired minimalism target passed clearly, so the pair was asymmetric. This result alone cannot distinguish weak context resolution from sensitivity to the reference wording.

### Rooftop panels

Target:

> There are six extra panels out back and ⟦four that are working up top on the roof⟧.

| Reference group | Three cosines | Median |
|---|---|---:|
| Four rooftop solar panels, intended | `0.7761`, `0.7907`, `0.6935` | `0.7761` |
| Four roof workers | `0.8455`, `0.8390`, `0.8483` | `0.8455` |

The alternative won by `0.0694`; every worker reference beat every panel reference. This is the largest context-grounding miss under the frozen metric. It is not a clean solar-versus-worker test, however: the experiment shortened away the original note's earlier explicit mention of solar panels, leaving only “panels,” while the intended references explicitly say solar or photovoltaic. The preceding word “panels” still affected the vector—the panel group was second-highest—but the fixture cannot tell us how SSE would behave with the complete resolving context. The paired roof-worker target passed, so this pair was also asymmetric.

### Solar startup versus solar-use measurement

Selected meaning inside the untouched miner note:

> Meanwhile I do a bit of programming to ⟦start up the miner when I have #solar #energy left⟧. And to have statistics how much solar energy is used for the miner.

| Reference group | Three cosines | Median |
|---|---|---:|
| Surplus-solar startup, intended | `0.8808`, `0.7789`, `0.8310` | `0.8310` |
| Solar-use measurement | `0.8463`, `0.6538`, `0.8433` | `0.8433` |

The alternative won by `0.0123`. The target still beat both temperature-related meanings by large margins. This is a narrow failure to distinguish two closely related miner-and-solar meanings, not a nonsensical vector. The reverse solar-use-measurement target passed. The result does not isolate whether the cause was context leakage, shared meaning, or reference wording.

## Interpretation

The frozen assumption does not pass as stated. SSE was not reliable on all controlled cases.

The evidence also does **not** support saying that SSE generally blends whole notes or loses selected meanings. It resisted every unrelated-context intervention, separated 8/9 meanings in two untouched mixed notes, and usually kept the intended group near the top even when it lost.

The weakest demonstrated capability is resolving an ambiguous selected phrase from nearby context: only one of the three paired context tests succeeded in both directions. Fine separation between closely related meanings is promising but not yet reliable.

Two diagnostic conclusions are sensitive to the three hand-written references. Greenhouse retirement and solar startup fail under the frozen median rule but would narrowly pass if the three cosines were averaged. That does not change the predeclared result; it means those two failures cannot, by themselves, establish a general model defect.

The experiment tests SSE conditional on hand-supplied masks. It does not test automatic takeaway or mask generation, corpus-wide coverage, or the eventual subject hierarchy.

Under the frozen contract, Stage 2 did not run because Stage 1 failed. This
directory records that result; the current interpretation and work order are
indexed in
[`../../docs/notes/SSE-EXPERIMENTS.md`](../../docs/notes/SSE-EXPERIMENTS.md).

## Reproduction and audit

The committed result directory contains the raw 81-by-768 `f32` matrix, worker receipt, complete analysis, readable table, and integrity manifest. Replay it with:

```text
nix develop -c cargo run --release --bin sse-context-counterfactual -- verify \
  sse_multivector/context-counterfactual-v1.json \
  sse_multivector/context-counterfactual-result-v1
```

Inference ran locally with networking disabled and the immutable image ID `sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa`. The command invoked that ID directly after `docker image inspect` returned the same ID. The worker receipt binds the request, checkpoint, model tree, worker source, output rows, and raw-vector hash. As with any local run, the committed files cannot independently prove which container runtime command the operator executed.
