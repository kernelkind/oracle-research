# S10 group definitions and second synthetic replacement

Status: completed authorized experiment, following the
[original-grouped-only S05 run](food-drink-s05-synthetic-grouped-v1.md).
This is a numerical replacement experiment, not an activated hierarchy policy.

## Two consolidation stages

The selected S10 contains 39 original entries in G04, G12, G16, G22 and G42,
representing 27 distinct notes. Each group supplies its own consolidation result;
the five resulting titles and fixed meanings then supply the section call.
No parent is supplied in either stage.

Four exact original group results are reused from native HR22 producers:
Positive feelings and attitudes, Greetings and good wishes, Wishing for Outcomes,
and Human aims. The current seven-entry G04 differs from the original group,
so it receives one fresh call, yielding **Positive attitudes and behaviors**.
The subsequent five-definition call yields **Psychological and social life**.
The native section evidence freezes each group's original input IDs, exact input
bytes, producer directory and result receipt. The four reused group results are
source references rather than four new cases or four new samples.

## Inclusion rule and result

Original HR22 assignment decides inclusion throughout this experiment. Keep
originally grouped inputs even when later unassigned; omit the 361 originally
unassigned inputs. Synthetic nodes retain their original support associations.

Replace the 39 selected inputs with R00002. All six previously unassigned inputs
remain, including R00001, Food and domestic animals. The new pool has
`255 - 39 + 1 = 217` inputs. Its support is still exactly the original 367 grouped
entries and 94 distinct notes. The R00001 title, meaning, associations and vector
are unchanged. Only R00002 requires encoding: 768 dimensions, 140 total tokens,
with the five title tokens selected and its meaning supplied as context.

| Measure | Before S10 replacement | After |
|---|---:|---:|
| Input vectors | 255 | 217 |
| Assigned inputs | 249 | 211 |
| Selected HDBSCAN groups | 44 | 39 |
| Epsilon sections | 33 | 32 |
| Distinct eligible notes | 94 | 94 |
| Distinct notes in selected groups | 80 | 80 |
| Currently unassigned inputs | 6 | 6 |

Angular HDBSCAN still uses min_samples=3, min_cluster_size=2 and EOM. The
unchanged middle-80% bend rule again selects epsilon 0.9425191168536686.
R00002 joins Mental states, Physical and mental stagnation, Mental alertness and
Brain fog and mental clarity in G12, the sole group in S07. That section now
represents 30 notes, including the synthetic node's original 27. R00001 remains
unassigned. Assignment is not forced, and numerical grouping is not itself a
semantic containment judgment.

The largest other sections are Nostr/GrowNostr (S04, 24 notes), coffee and coffee
businesses/hashtags (S13, 19), breakfast/mornings/sleep (S19, 13), and chicken/eggs
(S18, 10). The exact six unassigned input IDs are unchanged from the source run.

## Native accounting and verification

Both fresh calls use unchanged Hierarchy-consolidated-grouped-v1,
GPT-6.1 Sol medium, subscription SSE. There are two actual attempts, no failures,
retries or warmups. The native usage summary reports 3,590 input tokens, zero
cache reads/writes, and 1,002 output tokens including 766 reasoning tokens.
Fresh API-equivalent cost is **$0.0172**; incremental subscription cash charge is
zero. Historical costs of the four reused group definitions are not included.
One new SSE vector is encoded; the remaining 216 input vectors are reused.