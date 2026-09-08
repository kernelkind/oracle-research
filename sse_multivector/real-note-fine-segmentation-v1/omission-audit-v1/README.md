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

## Your review

You completed the 11-pair disputed set: **6 Valid, 5 Invalid**, with no comments. These decisions are separate from the 28 pairs accepted by all three assistant assessments; those 28 were not part of this user review.

| Your decision | Pair IDs |
|---|---|
| Valid | S3b9fb504a2, Sc6d6292a20, S6e277fa61a, S0e8e49606a, S7628431582, Sf55c1ca00b |
| Invalid | Se0df9826e1, S8af5fbe0c7, S77651f1c45, S9c51988975, S793247713b |

This confirms that the baseline missed relationships you consider valid. It does not establish how many distinct fine subjects were missed or why HDBSCAN separated these masks. The rejected pairs are not user-confirmed omissions. No reasons are inferred from the empty comments, and no original assistant judgments are overwritten.

## What remains unsettled

The eleven disputed pairs originally received at least one Valid judgment but were not unanimously accepted. Your decisions above now resolve that review set for this experiment. The earlier assistant disagreements concern the breadth of the shared subject and how much the masks actually identify. The model rounds used the same model in separate clean contexts, so their agreement on the other 28 pairs is not independent human ground truth. My judgments remain separate as well.

The other pairs are preserved with every assessment, including Uncertain judgments. We have not measured all omissions or proved that rejected pairs could never form useful groups. The random sample is too small to certify the remaining population. The protocol does not estimate an overall recall percentage.

This audit examines masks lacking a baseline multi-note segment. It does not examine every possible split between masks that already have such segments. Sampling was by vector ID; the 795 vectors include 23 exact-source aliases. The 44 demonstrated affected masks happen to be distinct source masks.

## Review

The existing reviewer displays only exact bracketed masks. No titles, scores, proposal methods, or assistant verdicts appear on screen. These are proposed two-mask groups, not a new HDBSCAN partition. The original baseline decisions remain untouched.

Reopen your completed 11-pair review:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
R=sse_multivector/real-note-fine-segmentation-v1/omission-audit-v1/report/disagreements
./target/debug/fine-segmentation-review "$R/review.json" "$R/user-session.json" "$R/user-response.json"
```

For the 28 pairs unanimously accepted by the assistant assessments, change the last directory to `report/agreements`. The complete mixed 128-pair set is in `sample/review.json`. All support partial review and resume. Only your saved decisions populate the completed disputed-pair session; no assistant judgments have been copied into user answers.

[All 128 pairs and their separate assessments](report/assessments.md) · [Counts and input hashes](report/summary.json) · [Protocol](../omission-audit-protocol.md) · [Sampling record](sample/sampling-manifest.json).

## Integrity and resources

The completed user review binds to review set `RN1a389ae36016` and artifact SHA-256 `9790b8e1f1635c6d91432316dd967fb6ba8aa0cef8f69ec1aa055511b9f64db5`. The saved response SHA-256 is `bf4767d4c19928d1a16121110d8dfa06af3f5f8dce5fd19387d92c30c85d0372`; the session SHA-256 is `821db7a8c90302777a9d0405e90d4857e33509af4204838c2fe4b111b25da095`. The first pair has a pending same-value Valid reselection with a prior confirmed Valid verdict; the exported response correctly retains that prior verdict. Session and response files remain local, untracked, and unmodified by this documentation update.

No subjects, masks, vectors, original HDBSCAN results, or existing user decisions changed. All 20 model calls succeeded once with 20 distinct recorded threads and isolated workspaces, using the existing Astra-low subscription runner. Four calls proposed text partners; sixteen calls supplied two assessments for each sampled pair. Exact prompts, responses, and isolation receipts are saved under `text/` and `assessments/`.

Nine same-note suggestions were mechanically excluded with reasons; one repeated-other-note suggestion was retained because it was still an eligible pair. Nothing was silently rewritten or retried. Full target coverage and the proposal-file hash were checked before sampling; see [admission checks](admission.json).

Usage: 178,766 input tokens (3,840 cached) and 19,781 output tokens. The 75 guard samples showed at least 103.29 GiB available memory, zero sampled memory pressure, and at most 0.12% I/O pressure. No guard interruption, new encoding, rented compute, or new paid API resource was needed. The new records occupied about 8 MiB before report packaging.
