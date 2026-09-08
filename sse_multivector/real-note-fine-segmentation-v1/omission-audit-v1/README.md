# Missing cross-note partners: results

The baseline left some masks without a multi-note segment even though suitable partners existed in the same frozen collection.

Two fresh model assessments and my separate inspection agreed on **28 valid pairs**. They involve **44 previously unserved masks from 36 notes**. Ten were HDBSCAN noise; 34 belonged to one-note segments. These are 28 observed relationships, **not 28 distinct missing subjects**. A note may already have other masks in multi-note segments.

## What we inspected

All 795 mask vectors without a baseline multi-note segment were considered for partner suggestions. Saved alternative configurations and cosine neighbors proposed 2,485 distinct pairs. The separate text-only pass proposed 425 eligible pairs, adding 278 new ones. Their union contained 2,763 pairs.

We sampled 64 pairs from that union and 64 from the remaining 425,323 eligible pairs. The sample and sampling probabilities were frozen before any new judgments. Each pair contains masks from two different notes.

| Source of the sampled pair | Pairs inspected | All three assessments said Valid |
|---|---:|---:|
| At least one method suggested it | 64 | 27 |
| No method suggested it | 64 | 1 |

The unsuggested agreement was:

V788: ⟦morning⟧ ⟦Brisket⟧ ⟦smoker⟧

V767: ⟦Beef⟧ ⟦with mash tatoes and avocados⟧

All three assessments accepted the shared beef-food meaning. V788 lacked a multi-note segment. This shows that even the combined suggestion methods missed a recognizable relationship.

## What remains unsettled

Eleven pairs received at least one Valid judgment but were not unanimously accepted. Some disagreements concern the breadth of the shared subject; others concern how much the masks actually identify. The model rounds used the same model in separate clean contexts, so agreement is not independent human ground truth. My judgments remain separate as well.

The other pairs are preserved with every assessment, including Uncertain judgments. We have not measured all omissions or proved that rejected pairs could never form useful groups. The random sample is too small to certify the remaining population. The protocol does not estimate an overall recall percentage.

This audit examines masks lacking a baseline multi-note segment. It does not examine every possible split between masks that already have such segments. Sampling was by vector ID; the 795 vectors include 23 exact-source aliases. The 44 demonstrated affected masks happen to be distinct source masks.

## Review

The existing reviewer displays only exact bracketed masks. No titles, scores, proposal methods, or assistant verdicts appear on screen. These are proposed two-mask groups, not a new HDBSCAN partition. The original baseline decisions remain untouched.

Start with the 11 disputed pairs:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/omission-audit-v1/report/disagreements
./target/debug/fine-segmentation-review "$R/review.json" "$R/user-session.json" "$R/user-response.json"
```

For the 28 unanimously accepted pairs, change the last directory to `report/agreements`. The complete mixed 128-pair set is in `sample/review.json`. All support partial review and resume; no user answers have been filled in.

[All 128 pairs and their separate assessments](report/assessments.md) · [Counts and input hashes](report/summary.json) · [Protocol](../omission-audit-protocol.md) · [Sampling record](sample/sampling-manifest.json).

## Integrity and resources

No subjects, masks, vectors, original HDBSCAN results, or existing user decisions changed. All 20 model calls succeeded once with 20 distinct recorded threads and isolated workspaces, using the existing Astra-low subscription runner. Four calls proposed text partners; sixteen calls supplied two assessments for each sampled pair. Exact prompts, responses, and isolation receipts are saved under `text/` and `assessments/`.

Nine same-note suggestions were mechanically excluded with reasons; one repeated-other-note suggestion was retained because it was still an eligible pair. Nothing was silently rewritten or retried. Full target coverage and the proposal-file hash were checked before sampling; see [admission checks](admission.json).

Usage: 178,766 input tokens (3,840 cached) and 19,781 output tokens. The 75 guard samples showed at least 103.29 GiB available memory, zero sampled memory pressure, and at most 0.12% I/O pressure. No guard interruption, new encoding, rented compute, or new paid API resource was needed. The new records occupied about 8 MiB before report packaging.
