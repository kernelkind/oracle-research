# LG01 — subject hierarchy merging: the original walkthrough

The step-by-step exchange from our September 29, 2026 conversation. Your questions and replies and my answers are reproduced verbatim and in order. The title, numbered section headings, speaker labels, navigation and editorial notes are added for this document.

This explains the original **SMv1** experiment. Statements such as “proposed” and “no merges yet” describe that point in the walkthrough, not today's implementation status. The later **SMv2** addition is noted at the end. This is **not** the later 3/5/10-neighbor proposal.

## Contents

- [1. Find the closest mask in another post](#1-find-the-closest-mask-in-another-post)
- [2. Convert those mask matches into post pairs](#2-convert-those-mask-matches-into-post-pairs)
- [3. Find the best match for each subject](#3-find-the-best-match-for-each-subject)
- [4. A best match for every subject](#4-a-best-match-for-every-subject)
- [5. Use the same table in the reverse direction](#5-use-the-same-table-in-the-reverse-direction)
- [6. Keep only mutual choices](#6-keep-only-mutual-choices)
- [7. Check both similarities](#7-check-both-similarities)
- [8. Combine a passing pair into one shared node](#8-combine-a-passing-pair-into-one-shared-node)
- [9. Combine overlapping passing pairs](#9-combine-overlapping-passing-pairs)
- [10. Check for loops](#10-check-for-loops)
- [11. Display the resulting hierarchy](#11-display-the-resulting-hierarchy)
- [12. Which posts were in the first test?](#12-which-posts-were-in-the-first-test)

## 1. Find the closest mask in another post

**You**

> "  Start with two posts already identified by our candidate search: N015 and N037.
> " wdym candidate search

**Assistant**

I meant the **nearest-vector comparisons from the last investigation**.

One concrete example:

1. Take **V0216**, the mask for **Bread** in **N015**.
2. Compare it against every mask vector from the other five posts.
3. Its closest match is **V0513**, the mask for **Bread** in **N037**: cosine **0.9848**.

That individual match gives us a reason to examine **N015 and N037 together**.

My proposal is to use those individual matches to choose which pairs of posts receive the fuller comparison. We are **not comparing whole-post vectors**.

“Candidate search” was shorthand for that first operation; I should have explained it explicitly.

## 2. Convert those mask matches into post pairs

**You**

> so we do N^2 comparisons, mask to mask. for each mask, find it's most related mask. then what? you need to frame it like this

**Assistant**

Yes—for this small test, roughly **N² mask-to-mask comparisons**, excluding masks from the same post.

**Then convert those closest-mask matches into pairs of posts.**

For example:

```text
V0216 in N015 → closest mask V0513 in N037
V0215 in N015 → closest mask V0514 in N037
```

Both matches point to the same post pair: **N015 + N037**. Put that pair on a list **once**.

Repeat for every mask. The result is a deduplicated list of **post pairs whose SP hierarchies we would compare next**.

Nothing has been merged or placed yet. We have only selected which posts to compare.

## 3. Find the best match for each subject

**You**

> gotcha. what's next

**Assistant**

**For each selected post pair, compare every SP subject in one post against every SP subject in the other.**

For **N015 + N037**:

- N015 has **9 SP entries**.
- N037 has **16 SP entries**.
- That gives a **9 × 16 table of subject-to-subject cosines**.

This uses **subject-text vectors**, not mask vectors.

From that table, find each subject’s closest subject in the other post. For example:

```text
N015: Sourdough bread
  → N037: Sourdough bread
  cosine: 1.0000

N015: Sourdough bread preparation
  → N037: Sourdough bread
  cosine: 0.9686
```

Do this in **both directions**: N015 → N037 and N037 → N015.

We now have each subject’s preferred match. **Still no merges.** The next check is whether those choices are mutual.

## 4. A best match for every subject

**You**

> this seems very wasteful, but that's fine bc this is an experiment. so we're finding the pair of subjects between these two notes which are most related. got it

**Assistant**

One important correction: **we find a best match for every subject—not one winning pair for the two posts.**

So the same two posts can produce:

```text
Bread          ↔ Bread
Sourdough bread ↔ Sourdough bread
```

Both pairs remain candidates. We don’t discard the Sourdough bread match just because the Bread match scores higher.

We’re trying to combine matching subjects at **multiple levels** of their SP hierarchies.

## 5. Use the same table in the reverse direction

**You**

> oh, for every subject in A we compute the best match in B

**Assistant**

Yes. For **every subject in A**, find its best match in B.

Then do the reverse: for **every subject in B**, find its best match in A—using the same cosine table, without recomputing it.

## 6. Keep only mutual choices

**You**

> ok, got it. what's next

**Assistant**

**Next, keep only pairs where both subjects chose each other.**

Example:

```text
A’s Sourdough bread → B’s Sourdough bread
B’s Sourdough bread → A’s Sourdough bread
```

That pair passes.

But:

```text
A’s Sourdough bread preparation → B’s Sourdough bread
B’s Sourdough bread → A’s Sourdough bread
```

The preparation pair does **not** pass: B preferred a different subject in A.

Only that proposed pairing is removed. **Sourdough bread preparation itself stays in A’s SP hierarchy.**

Tied best matches remain eligible. The surviving pairs are still candidates—not merges yet.

## 7. Check both similarities

**You**

> got it

**Assistant**

Next, the mutual pair must pass **both proposed similarity checks**:

- Subject-text cosine **≥ 0.90**
- Mask-to-mask cosine **≥ 0.80**

For example:

| Pair | Subject cosine | Mask cosine | Passes? |
|---|---:|---:|---|
| Cranberries / Cranberries | 1.0000 | 0.8112 | Yes |
| Rosemary / Fresh rosemary | 0.7514 | 0.9320 | No |

A high mask cosine cannot compensate for a low subject cosine, or vice versa.

These cutoffs are **provisional experiment settings**, not established semantic boundaries. If either subject has no mask, this rule leaves that pair unmerged.

**You**

> hm sounds arbitrary, but sounds fine for now

**Assistant**

Agreed: **0.90 for subject cosine and 0.80 for mask cosine**, provisionally—not validated or frozen.

Nothing has run or changed. Next is how to combine the pairs that pass while preserving their SP relationships.

## 8. Combine a passing pair into one shared node

**You**

> tell me next

**Assistant**

**Next: turn a passing subject pair into one shared node. Keep both masks and all existing SP links.**

For example, these Bread subjects passed:

```text
N015: Bread — mask V0216
N037: Bread — mask V0513
```

The shared **Bread** node would hold **both V0216 and V0513**, with their original post references.

Their existing relationships would become:

```text
Food — from N037
└─ Bread — shared by N015 and N037
   ├─ Sourdough bread — from N015
   └─ Sourdough bread — from N037
```

The two Sourdough bread subjects are still separate at this step. They combine only when we process **their own passing pair**.

We are combining subject entries—not blending their vectors or rewriting their masks. The original saved SP data remains unchanged.

## 9. Combine overlapping passing pairs

**You**

> sounds good. what's next

**Assistant**

**Next, handle passing pairs that overlap.**

For example:

```text
N015’s Bread ↔ N037’s Bread — passes
N037’s Bread ↔ N072’s Bread — passes
```

My proposal: combine all three into **one Bread node**, holding masks **V0216, V0513 and V1145**, and preserve their SP relationships.

There’s an important design choice here: **a chain of passing pairs would be enough**. We wouldn’t require every possible pair within the resulting node to pass directly.

That means A–B and B–C could join all three even if A–C failed. A mistaken match could therefore pull different subjects together.

I suggest treating this as another provisional rule for the experiment—not an assumption we hide.

## 10. Check for loops

**You**

> sounds good. what's next

**Assistant**

**Next, check whether the merges created any loops between distinct nodes.**

A loop would mean:

```text
A is above B
B is above C
C is above A
```

My proposed rule:

- Undo **all proposed merges involved in a loop**, leaving those subjects separate.
- Keep their original SP relationships.
- Check again until no loops remain.

We would **not** arbitrarily delete an SP relationship or force additional subjects to merge to remove the loop.

This is only a structural check. It doesn’t establish that every remaining merge is semantically correct.

## 11. Display the resulting hierarchy

**You**

> ok. what's next

**Assistant**

**Then we display the resulting hierarchy in the existing UI.** There is no additional parent-placement step.

- Each node represents an original SP subject or a group of merged subjects.
- Its masks come from those subjects, retaining their post references.
- Its parent–child relationships come from the original SP hierarchies.

Unmatched subjects and disconnected branches remain visible. We don’t force them into another node.

That completes the proposed process. Next would be an **isolated six-post experiment**, using the saved vectors, so we can judge the resulting hierarchy rather than individual cosine scores. No new model calls.

## 12. Which posts were in the first test?

**You**

> the same six posts?

**Assistant**

Yes—the same three bread posts and three coffee-shop posts: **N004, N015, N037, N038, N065 and N072**.

This would check the complete procedure on known inputs—not validate generalization. Since we chose the provisional rules after examining these examples, a promising result would need testing on different posts next.

## Current-version note

Added for this document; not part of the quoted walkthrough:

**LG01** names the current technique, independent of post count. The six-post
and 100-post runs use the same technique. Code and saved artifacts retain
`SMv2`; the original exchange above uses the names from that conversation.

- SMv2 first combines entries from the **same post** only when their subject wording and nonempty mask positions are identical.
- Its cycle handling preserves those exact same-post combinations when undoing conflicting cross-post merges. If the exact same-post combinations alone create a cycle, it stops.
- The cross-post search, mutual-best checks and provisional cutoffs described above remain unchanged in SMv2 and the 100-post run.

See [the current rule register, HD08–HD21](../docs/planning/release-decisions.md#sp-based-hierarchy-rules) and [the SMv2 procedure](subject-order-probe.md#smv2--exact-same-post-combination) for those additions and their status.

<details>
<summary>Transcript provenance</summary>

Message timestamps on **2026-09-29**, in UTC, corresponding to the sections above (your message → assistant answer):

- Section 1: `01:06:08.829` → `01:06:36.410`
- Section 2: `01:08:55.178` → `01:09:20.592`
- Section 3: `01:10:00.816` → `01:10:34.385`
- Section 4: `01:12:20.628` → `01:12:35.230`
- Section 5: `01:13:11.633` → `01:13:23.044`
- Section 6: `01:13:30.431` → `01:13:51.188`
- Section 7: `01:14:54.001` → `01:15:18.112`
- Section 7: `01:16:06.639` → `01:17:20.290`
- Section 8: `01:20:29.986` → `01:21:07.807`
- Section 9: `01:22:01.716` → `01:23:10.757`
- Section 10: `01:23:48.721` → `01:24:30.310`
- Section 11: `01:25:04.459` → `01:25:54.433`
- Section 12: `01:28:16.675` → `01:28:32.456`

No tool outputs, private analysis or later proposals are included.

</details>
