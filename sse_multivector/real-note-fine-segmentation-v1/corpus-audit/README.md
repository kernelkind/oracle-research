# Text-only corpus audit

Status: complete for area choice; **the final 100 notes have not been selected**.

Recommendation: food and drink, covering preparation, eating experiences and
preferences. The affirmative manual audit contains 117 distinct complete notes
from 109 authors, with at most two notes per author. It provides an everyday
language alternative to the technical areas and enough recurrence and variation
to attempt the experiment without prespecifying fine segments.

After that choice, a separate short-note audit corrected the unnecessary
18-word convenience floor. It reviewed a bounded domain-hash-ordered prefix of
120 candidates containing 5–17 visible words and retained 77 notes from 73
authors. The original 280 complete notes were not rereviewed. The combined
eligibility artifact is now `food-combined-manually-eligible-v2.json`: **194 notes
from 176 authors**, sorted by the same content-independent domain hash. The
original 117-note artifact is preserved unchanged. There is no final short-note
quota and no final 100-note selection in this audit.

## Evidence

| Broad area | Keyword hits in 51,200 notes | Length-eligible | Copy-screened, author-capped candidates | Candidate authors | Complete notes inspected |
| --- | ---: | ---: | ---: | ---: | ---: |
| Food/drink | 1,220 | 807 | 607 | 510 | 280; 117 affirmatively eligible |
| Bitcoin | 9,640 | 5,826 | 1,923 | 1,487 | 45 |
| AI | 724 | 564 | 357 | 304 | 35 |

Counts outside the food manual audit are retrieval counts, not a claim that
every candidate is useful or that 100 have been semantically certified.
Bitcoin has substantial depth but its first 45 notes also contain many block,
fee and trading bots. Its usable examples include payment experiences, custody
choices, full-node hardware and mining. AI has useful personal software-building
experiences, arguments about surveillance/authenticity, and reporting on products
and employment; it also contains promotional posts and images described only by
tags. These are plausible alternatives but are less directly audited than food.

Additional preliminary screens found Nostr 1,201 candidates / 964 authors and
gardening 124 / 106. Gardening's small surplus above 100 is vulnerable to false
positives and was not selected for detailed comparison. No predicted fine
segments, target memberships or per-subject quotas were used.

The initial frozen 500-note input contains only 85 Bitcoin, 43 Nostr, 35 AI,
10 food and 2 gardening keyword hits even before length filtering. It also lacks
pubkeys, making it inadequate by itself for this concentrated 100-note task.

## Files

- `audit-summary.json`: provenance, retrieval rules and all automated counts.
- `manual-audit-summary.json`: exact manual coverage and limitations.
- `food-manual-audit.json`: affirmative broad-area decisions and reasons.
- `food-manually-eligible.json`: the 117 complete notes, event IDs, pubkeys,
  original content hashes, source rows and reasons; **not a frozen selection**.
- `food-combined-manually-eligible-v2.json`: the current 194-note combined pool,
  with per-note audit provenance and ordering hashes. Reapply author and copy
  controls across the combined selection; combining separately capped pools
  produces a maximum of three candidates for one author before final filtering.
- `short-note-audit-v1/food-manual-audit.json`: affirmative and negative reasons
  for every one of the 120 complete short notes, including missing-image-context
  exclusions. `short-note-audit-v1/manual-audit-summary.json` gives exact counts.
- `prior-text-familiarity-notes.json`: possible prior coffee-roasting and decaf
  text familiarity flagged by the parent, not independently verified or
  automatically excluded. This is development, not strict unseen validation.
- `representative-complete-notes.md` and `.json`: complete illustrative notes
  from the three compared broad areas.
- `*-candidates.jsonl`: reusable complete candidate pools, with deterministic
  ranks and original source rows.

## Provenance and resource use

The broader sample was already materialized before this goal:

```text
topic_map/crec-113-formal-sample.json
  -> /dev/shm/oracle-mvp-crec113-granite-r2-v1/formal-v1/sample/sample.jsonl
  -> target/crec-113-formal-v1/sample/sample.jsonl (durable historical copy)
```

The 21,813,509-byte tmpfs sample was read and its complete SHA-256 verified as
`8edb8a51246201100e6ba7cf7bf1bbf9cd501881d7c70b8a9cfc7a380d1b168e`.
Its manifest declares source NostrDB identity
`8c6e8b7798a52639f78bd4a0ba4276d72784e4d1f149e3d5925d95289ae62bad`,
3,530,455 available eligible notes, 53,402 source-order rows examined, and 51,200
retained notes. This is the older public English corpus, not the newer CREC-120
fresh corpus. No source database was opened, scanned or rehashed, and no corpus
was rebuilt. The existing sampler config identifies the original corpus and
ordered-ID paths. The durable 21 MB copy was not rehashed during this audit.

The audit script limits its source to at most 32 MB and preserves complete raw
content. It screens 18–300 words after ignoring URLs/NIP-19 references, with a
2,500-codepoint bound on the complete text. Hash order is independent of content
and vectors. It rejects normalized exact text copies and strong four-word-shingle
near copies, then caps each author's candidate contribution at two. This is a
conservative mechanical copy screen, not proof that all retained prose was
independently written.

The 18-word floor was a convenience retrieval screen, not a requirement for
meaningful notes. The follow-up read the same bounded tmpfs source once more,
found 347 length-eligible food keyword hits at 5–17 words, and inspected only the
first 120 copy-screened, author-capped candidates in domain-hash order. It
retained explicit short preparation, ingredient, preference and experience
statements. Images do not need to be viewed when the complete text itself gives
the meaning; essential missing image context, not brevity, grounds exclusions.

The host admission controller used a 20% I/O-pressure backoff threshold. A
separate operational check at original implementation commit `aca6142` observed
22.5% workload I/O pressure: admission paused, accepted writes drained, and
admission resumed after about 12 seconds of low pressure. This corpus audit
needed only the bounded 21 MB tmpfs read;
there was no sustained storage workload or pressure interruption. Output files
are small audit artifacts. No model calls, Cargo invocation, external writes,
or commits were made by this audit task.

## Selection cautions

The next stage must verify the actual SSE tokenizer/input limit on complete
original notes. Character and word bounds are not token-limit verification,
especially for long encoded image URLs. Keep unsupported nutrition assertions
as source content, not endorsed advice; broad-area eligibility does not assert
their truth. Some eligible notes are mixed-topic, truncated *by their original
publisher*, promotional, short, or otherwise weaker; their individual reasons
make these limitations explicit. Read them before final selection. There are
327 further food candidates available if more usable notes are needed.

A provenance search accidentally returned nine prior mask-fidelity example IDs
and their expected comparisons, without actual vector/grouping outcomes. Those
nine are explicitly quarantined by the retrieval script. A mixed coffee note
already visible in documentation is additionally quarantined as food candidate
99. None of these ten belong to the 117-note affirmative pool. No vectors or
prior clustering results were inspected or used to choose an area.

## Reproduce

From the repository root, with the existing tmpfs source still present:

The first command reconstructs candidate pools from original source text; the
second applies the separately stored manual audit and packages its evidence.
Both overwrite only the new audit's own generated files. Do not run them on
large database artifacts or substitute a different source under the same audit.

To reproduce the separate short-note extension and combined eligibility:
