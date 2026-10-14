# Music 50-note fixed-group epsilon review

Status: completed grouping probe; the candidate rule remains experimental.
No production HiGen policy, prompt, selected membership or canonical hierarchy
was changed. Native section naming was prepared by the existing adapter but
was not run: this task requested the numerical grouping and colored SVG.

## Inputs and controls

The first 50 notes in the saved 100-note Music corpus selection were used in
their existing order. Every complete post matched its original content hash.
Their note IDs are disjoint from HR21's 50-note food corpus. This is a curated
corpus subset, not a random sample.

Original selection source:
`sse_multivector/real-note-fine-segmentation-v1/music-corpus-selection-v1/notes.json`.
Its SHA256 is
`e4cc3d288231f69677bf1c8720132cf72d652bd23c2ca883b4528ff270e32b87`.
The experiment uses a separate frozen raw-post copy in its task worktree.
Deprecated ASv6.23 Music hierarchies were not reused.

- Local hierarchies: ASv6.100, GPT-6.1 Sol medium, subscription SSE.
- Original L1 titles and meanings: Bootstrap-v133, same teacher settings.
- SSE: the Bootstrap title followed by two newlines and its explicit meaning;
  only the title's contextual tokens are pooled. Same pinned CPU checkpoint,
  base model, 768 dimensions and batch size eight as HR21.
- HDBSCAN: exact angular distances, `min_samples=3`, `min_cluster_size=2`,
  excess-of-mass selection; same retained production executable as HR21.
- Cut: unchanged [10%-trimmed bend rule](hr21-epsilon-selection-v1.md), applied
  to the original selected-group ancestor tree. No six-section limit or
  corpus-specific adjustment was added.

Teacher preparation and execution used the shared stable runner launcher from
the isolated Music worktree. Its project source remains frozen at `2b0ce4f1`;
the isolated teacher worker source is `9575d04`. Provider scheduling remained
owned by the shared 30-request queue. There was no outer concurrency cap.

## Result

| Measure | Result |
|---|---:|
| Input notes | 50 |
| Original L1 entries | 392 |
| Null Bootstrap meanings | 2 |
| Encoded original entries | 390 |
| Selected HDBSCAN groups | 40 |
| Entries in selected groups | 192 |
| Unassigned encoded entries | 198 |
| Notes represented by selected groups | 50 |
| Automatically selected epsilon | 0.8284732141631335 |
| Colored sections | 30 |
| Largest section: fixed groups | 11 |
| Largest section: distinct notes | 42 |

Songstr and zapagirl returned null meanings and were skipped according to the
existing Bootstrap contract. Their saved answers remain intact. No selected
HDBSCAN group or represented note was removed by the epsilon fit or final cut.

The selected split distance is `0.8457376664459951`; the next smaller full-curve
distance is `0.8112087618802719`. Their midpoint gives the epsilon above.
All 40 groups occur in exactly one section.

The one combined section contains G01, G03, G04, G10, G12, G16, G17, G20, G21,
G26 and G40: songs, live music, recordings, bands, requests/listening,
music/listening/playback, performances, songwriting/lyrics, music searches and
playlists, musicians, and concerts. The remaining 29 groups are singleton
sections. Several fixed groups already mix different titles; numerical
coverage is not semantic validation of those groups or of the combined section.
Neither section names nor containment judgments were generated in this probe.

## Native accounting and verification

The native summary records 442 valid cases, 446 fresh provider attempts,
zero exact answer reuses, two automatic prefix warmups and two recovered failed
attempts. No case remains failed or unrun in the two executed teacher batches.
The two failed attempts have unknown usage, so full cost is unknown. The known
API-equivalent catalog subtotal is $4.319410; this is not a subscription cash
charge. Incremental cash charge was zero.

The offline tool independently reproduced HR21's exact reviewed 25-group,
15-section partition and epsilon `0.94062506360364`. Seventy relevant tool,
HDBSCAN adapter and hierarchy tests passed on combined main. Native state,
producer and vector receipts, request controls, full section coverage, SVG
labels and colors were verified. The generated PNG was visually inspected;
cutoff arrows remain outside the tree rather than drawing an overlapping line
through branches. No hierarchy review UI was refreshed.

## Retained evidence

Task worktree:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-music-fifty-epsilon-v1`.
All files below are ignored artifacts relative to that worktree:

- `target/music-fifty-epsilon-v1/selection.json`: original selection and hashes.
- `target/music-fifty-epsilon-v1/AS/`: native local-hierarchy inputs and receipts.
- `target/music-fifty-epsilon-v1/subject-collection/`: native collected subjects.
- `target/music-fifty-epsilon-v1/numeric-source/`: frozen Bootstrap answers,
  original vectors, native HDBSCAN request/result and stopped construction state.
- `target/music-fifty-epsilon-v1/review/analysis.json`: exact projection, full
  split curve, fitted points, selected interval and all memberships.
- `target/music-fifty-epsilon-v1/review/groups.svg` and `groups.png`: complete
  colored tree; `groups.md`: compact group and section tables.
- `target/music-fifty-epsilon-v1/hr21-control/`: independently reproduced
  numerical and visual control.
- `target/music-fifty-epsilon-v1/usage.json` and `result-summary.json`: native
  accounting and bounded result status.

The isolated runner worktree
`/home/dev/src/notedeck_worktrees/algos/experiment-runner-music-fifty-source-v1`
is also retained because native producer identities bind its absolute paths.
The reusable review tool is on main; the experiment remains in its frozen task
worktree. Review the Music grouping's concrete contents before treating this
transfer result as support for adopting the cut in construction.
