# Official hierarchy runs and experimental parameters

This Markdown file is the register of official hierarchy runs and their
experimental parameters. **HR05** is the approved 24-note rerun being prepared.
**HR04** is the completed 12-note run; **HR03** is the completed 50-note baseline.
Each run's raw build, browsing menu and export share its ID.

## HR05 — ASv6.100 24-note hierarchy

Approved as a rerun of HR04 with 24 notes. Execution has not started. The
[run definition](../../sse_multivector/hierarchy-runs/hr05/traversal.spec.json)
records complete note IDs in their original selection order. A review UI using
the existing terminal hierarchy viewer will be prepared after the run.

### Inputs and construction

| Parameter | Selected value |
| --- | --- |
| Notes | First 24 notes in HR03's frozen 50-note selection, in the same order |
| Subject prompt | ASv6.100; reuse HR03's saved subject trees |
| Local subject entries | 832, including 150 local roots |
| Bootstrap prompt | [Hierarchy-bootstrap-v109](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v109.md) |
| Compare prompt | [Hierarchy-compare-v179](../../sse_multivector/shr_single_pair/Hierarchy-compare-v179.md), symmetric A/B fixed meanings |
| Consolidation prompt | [Hierarchy-consolidation-v4](../../sse_multivector/hierarchy-runs/hr05/Hierarchy-consolidation-v4.md), unchanged from the three-note trial |
| Constructor | `traversal-v24`, including landed refinement change `c5cc28d31455403292dd012e862aa871d06e0241` |
| Local schema version | 4 |
| Initial graph | Empty |
| Selection | L1 roots first, then deeper levels; rotate one local entry per note per pass in saved order |
| Refinement after coverage | Deeper entries only from notes represented in leaves containing multiple notes |
| Active local searches | At most 3; placements in selection order |
| Consolidation trigger | An addition leaves 6 or more siblings, including roots; best effort |
| Redundant browsing steps | Bypass equal-note-set parents, retaining deeper headings and preserving the raw graph |
| Completion | All notes individually accessible, one note per browsing leaf, strictly smaller note sets on downward edges |

The selected notes reuse the exact HR03 ASv6.100 corpus. Construction starts
from an empty graph with native meanings and comparisons, retaining any exact
answer reuse with its producer receipts.

### Model execution and attempt allowance

| Parameter | Selected value |
| --- | --- |
| Provider | `openai-codex`, subscription |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prompt cache | Enabled, with automatic warming |
| Shared provider queue | Maximum 30 requests across experiments |
| Bootstrap timeout | 600 seconds |
| Compare/consolidation timeout | 1,800 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unspecified; no overrides |
| Persistent attempt ceiling | 500 total, including warmups, retries and every resume |

The exact Bootstrap, Compare and consolidation settings are saved alongside the
run definition. The same persistent allowance is used throughout. Reaching its
ceiling preserves partial work and reports unfinished construction.

### Git provenance and retained artifacts

Before execution, record the full Oracle generation commit and clean source
status in the frozen preparation record. The hierarchy source and prompts
match HR04. The retained isolated runner remains at
`e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7`. Run artifacts stay under
`oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hierarchy-hr05-twenty-four-note-v1/`.
The subject corpus SHA-256 remains
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`.

## HR04 — ASv6.100 12-note hierarchy

Approved and completed October 11, 2026. The run uses the current
standalone constructor, including restricted refinement, single-note leaves and
deeper-heading retention. The
[run definition](../../sse_multivector/hierarchy-runs/hr04/traversal.spec.json)
records the complete note IDs in their selection order.

### Result

| Measurement | Saved result |
| --- | --- |
| Construction / execution status | complete / complete |
| Notes represented and individually accessible | 12 of 12 |
| Raw graph and browsing menu | 14 nodes, 9 edges, 5 roots |
| Maximum child choices | 6 |
| Structural audit | Passed; all 9 edges strictly narrow note sets, every leaf contains one note, no violations |
| Selected local entries | 14, all L1 roots; two searches retained without placement after stopping |
| Consolidation proposals | 3: two placed, one held because required containment was not established |
| Held local entries | 0 |
| Native attempts | 153 of 500: 45 warmups and 108 ordinary attempts |
| Valid model answers | 107; one provider failure recovered by retry, no terminal failures |
| Exact answer reuses | 0 |
| Known API-equivalent cost subtotal | $0.7431476; complete total unknown because the recovered failed attempt has no usage |

The run stopped during L1. It did not need deeper refinement or removal of
equal-note-set steps, so it does not establish their behavior with live model
judgments. The structural audit does not grade meanings or relationships; its
`done` field deliberately remains false. Saved teacher judgments and the held
proposal remain unchanged.

### Inputs and construction

| Parameter | Selected value |
| --- | --- |
| Notes | First 12 notes in HR03's frozen 50-note selection, in the same order |
| Subject prompt | ASv6.100; reuse HR03's saved subject trees |
| Local subject entries | 416, including 72 local roots |
| Bootstrap prompt | [Hierarchy-bootstrap-v109](../../sse_multivector/shr_single_pair/Hierarchy-bootstrap-v109.md) |
| Compare prompt | [Hierarchy-compare-v179](../../sse_multivector/shr_single_pair/Hierarchy-compare-v179.md), symmetric A/B fixed meanings |
| Consolidation prompt | [Hierarchy-consolidation-v4](../../sse_multivector/hierarchy-runs/hr04/Hierarchy-consolidation-v4.md), unchanged from the three-note trial |
| Constructor | `traversal-v24`, including landed refinement change `c5cc28d31455403292dd012e862aa871d06e0241` |
| Local schema version | 4 |
| Initial graph | Empty |
| Selection | L1 roots first, then deeper levels; rotate one local entry per note per pass in saved order |
| Refinement after coverage | Deeper entries only from notes represented in leaves containing multiple notes |
| Active local searches | At most 3; placements in selection order |
| Consolidation trigger | An addition leaves 6 or more siblings, including roots; best effort |
| Redundant browsing steps | Bypass equal-note-set parents, retaining deeper headings and preserving the raw graph |
| Completion | All notes individually accessible, one note per browsing leaf, strictly smaller note sets on downward edges |

The selected notes cover rocket-stove cooking, lamb dinner, shrimp risotto,
cranberry sourdough, cast-iron cookware, chicken stock, preserved beets,
matcha-cashew pie, meal planning, beef stew, sourdough preparation and smoked
brisket. Their saved AS outputs are reused; meanings and comparisons use the
native runner and retain any exact answer reuse with its original receipt.

### Model execution and attempt allowance

| Parameter | Selected value |
| --- | --- |
| Provider | `openai-codex`, subscription |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prompt cache | Enabled, with automatic warming |
| Shared provider queue | Maximum 30 requests across experiments |
| Bootstrap timeout | 600 seconds |
| Compare/consolidation timeout | 1,800 seconds |
| Output-token limit | No explicit limit |
| Seed / temperature | Unspecified; no overrides |
| Persistent attempt ceiling | 500 total, including warmups, retries and every resume |

The exact Bootstrap, Compare and consolidation settings are saved alongside the
run definition. The same persistent allowance is used throughout. Reaching its
ceiling preserves partial work and reports unfinished construction.

### Git provenance and retained artifacts

| Generation provenance | Recorded value |
| --- | --- |
| Oracle generation commit | `17ea0b74959106090de110d2971e6797eff73c11` |
| Shared-runner generation commit | `e19592f9a6b0b3a2b3ac0bc63220156d86a0f1a7` |
| Uncommitted source changes at generation | None in either isolated worktree |

The [frozen preparation record](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/prepared-provenance.json)
contains the commits, selected note IDs, complete settings, frozen constructor
hashes and initial native plan bindings. Later documentation commits do not
change these generation commits. Resume from the retained task worktree with
the same attempt-budget path; its frozen source remains unchanged.

The run worktree is `oracle-mvp-hierarchy-hr04-twelve-note-v1`; artifacts remain
under `target/hierarchy-hr04-twelve-note-v1/`. Its saved AS corpus SHA-256 is
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`, identical to
HR03's bound subject corpus. The prepared definition separately binds the exact
12-note selection. Preserve the raw graph, menu, execution summary, attempt
ledger, native receipts and source provenance there. The final graph and menu
are copied into `final/` and bound by immutable output hashes in the official
register. Retain both the Oracle and runner worktrees for native frozen paths.

| Saved artifact | File |
| --- | --- |
| Raw hierarchy | [HR04 raw state](../../target/hierarchy-catalogue/outputs/HR04.json) |
| Browsing menu | [HR04 menu](../../target/hierarchy-catalogue/outputs/HR04-related-1.json) |
| Complete parameters and evidence | [HR04 record](../../target/hierarchy-catalogue/records/HR04.json) |
| Structural audit | [Saved audit](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/audit.json) |
| Native usage and allowance reconciliation | [Saved usage](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/usage.json) |
| Final source and output provenance | [Saved provenance](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/final/code-provenance.json) |
| Exact generator source snapshots | [43-file source archive](../../../oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hierarchy-hr04-twelve-note-v1/code-snapshot/manifest.json) |

### SHA-256 bindings

| Input, source or output | SHA-256 |
| --- | --- |
| Run definition and note order | `a83792329bcd13ca6598ad32c0144bba6c915baa634254cc392659642c1848ad` |
| Bootstrap-v109 prompt | `caa77221193ce816c6112ea20ea81fcf4bf4739994fa06102e4b41f132128cd1` |
| Compare-v179 prompt | `49d936bd6d5e251bcc1317f34a87fd71c25eb1e63f972e5ec8824b81f73eb9ed` |
| Consolidation-v4 prompt | `144e23d89c65910f0851d4163ac7dff1baee248ebf5dab5c8779c843f9aae7c6` |
| Bootstrap response schema | `5806c8c66ce8a8a9b13fb9f5ff6445eb79bb918cf15925a17fd9354a1877809c` |
| Compare response schema | `9bdea40731448a9ef7b73372743cc258c5f6dc9419377c1d6c563d9dd12bc522` |
| Shared-runner fingerprint | `67a3688360b285fa4de34c08f2009df12708246143163e7a35d7ea04301cc0b8` |
| Request-code fingerprint | `15429b548cf904622a33bdad86c20d523da097c1956cc736ebbb2a513ded9018` |
| Source archive manifest | `182ed08a12b76ac6dcb5e8ebcbfc113e938b14a8851aec0fb86f76cdc9790099` |
| Raw hierarchy | `f482553bd90d76b9b4eeac77ec0662419dd3387465d1dbc67d046c034cce19b7` |
| Browsing menu | `86bd1e43fe30aafbbfdb1c1f0b87f9bebe7b6cd81f6f608c5524d6a2cc95599a` |

## HR03 — ASv6.100 50-note hierarchy

Generated October 10, 2026, using Bootstrap-v96 and Compare-v48. The latest
saved execution start is `2026-10-10T19:29:26.716124Z`.

### Inputs and construction

| Parameter | Recorded value |
| --- | --- |
| Notes | 50 |
| Note selection | [Frozen 50-note subject-generation specification](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-subjects-v1.spec.json) |
| Initial construction | [20 local roots from 20 notes](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-prefix-v1.json), before extending to the selected 50 notes |
| Subject prompt | [ASv6.100, frozen run template](../../target/hierarchy-catalogue/code/0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f.txt) |
| Subject entries | 1,510 |
| Bootstrap prompt | [Hierarchy-bootstrap-v96, frozen run copy](../../target/hierarchy-catalogue/code/599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845.md) |
| Compare prompt | [Hierarchy-compare-v48, frozen run copy](../../target/hierarchy-catalogue/code/b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af.md) |
| Comparison policy | guarded16 |
| Comparison limit | 16 |
| Local candidate limit | 32 |
| Maximum entries | 200 |
| Maximum choices setting | 6 |
| Independent meanings | true |
| Local schema version | 4 |

### Model execution

These are the saved settings, including the historical concurrency of 32.

| Parameter | Recorded value |
| --- | --- |
| Provider | `openai-codex` |
| Model | `gpt-6.1-sol` |
| Reasoning effort | medium |
| Transport | SSE |
| Prepared concurrency | 32 |
| Execution concurrency | 32 |
| Prompt cache | enabled in the frozen Bootstrap/Compare specifications |
| Warm cache | true |
| Subject-generation timeout | 1,800 seconds |
| Bootstrap/Compare timeout | 600 seconds |
| Output-token limit | No explicit limit; `null` in saved manifests |
| Seed | Unknown; not recorded |
| Temperature | Unknown; not recorded |

### Subject vectors

| Parameter | Recorded value |
| --- | --- |
| Model | `sentence-transformers/sentence-t5-base` |
| Device | CPU |
| Note batch size | 8 |
| Unique subject texts | 693 |
| Dimensions | 768 |
| Maximum length | 512 |
| Pooling | `selected-contextual-token-mean-linear-relu-linear-v1` |
| Python | `3.13.12` |
| PyTorch | `2.13.0+cpu` |
| Transformers | `4.57.1` |
| Tokenizers | `0.22.2` |

### Browsing menu

The run uses the saved
[shape-v2 recipe](../../sse_multivector/shr_single_pair/hierarchy-as100-fifty-note-shape-v2.json)
to select roots and child links from the raw hierarchy. The maximum-choices
setting was 6; the resulting menu has 7 roots, with 13 choices under Food.
The saved recipe and assessment retain those actual choices.

### Generator code and Git commits

| Code provenance | Recorded value |
| --- | --- |
| Oracle generation commit | Unknown; not recorded |
| Shared-runner generation commit | Unknown; not recorded |
| Uncommitted source changes at generation | Unknown; not recorded |
| Preserved Oracle source commit | `7f0a54b9e2fc9dcd47e62b7da0ac901056087904` |
| Preserved shared-runner source commit | `e27660d98798facf959d4661000b885e2dcd298f` |

The preserved Oracle commit was made after generation. Its source matches all
53 recorded project Python files. The preserved runner commit matches eight
recorded Python files and the saved seven-file runner fingerprint. These checks
identify matching source; they do not recover the execution-time Git HEAD or
uncommitted changes. Exact source-file snapshots and their hashes are listed in
the [complete HR03 record](../../target/hierarchy-catalogue/records/HR03.json).

### Outputs and complete evidence

| Output | Saved file |
| --- | --- |
| Raw hierarchy (`regrouping-roots-v1`) | [HR03 raw state](../../target/hierarchy-catalogue/outputs/HR03.json) |
| Browsing menu (`menu-v2`) | [HR03 menu](../../target/hierarchy-catalogue/outputs/HR03-related-1.json) |
| Browser export (`review-ui-v1`) | [HR03 browser export](../../target/hierarchy-catalogue/outputs/HR03-related-2.json) |

The [complete HR03 record](../../target/hierarchy-catalogue/records/HR03.json)
contains the frozen construction settings, response schemas, source bindings,
menu recipe and references to saved parameter evidence. The original native
[plan and code hashes](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/step-123/experiment/experiment.json)
and [execution settings](../../../oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/regrouping-roots-v1/step-123/experiment/execution-settings.jsonl)
remain available. Unrecorded historical settings stay unknown.

### SHA-256 bindings

| Input, source or output | SHA-256 |
| --- | --- |
| Source corpus | `581e465d9a4c3ac5e6e2067a2edb9e9711acb3fd68982909394c9c704151dbf3` |
| 50-note selection specification | `452add80668e785462e01c8a8840e2547108e47212d2d33d344d549639a5ac99` |
| Initial 20-root construction definition | `3e3922c1c9dc9c5356fbff871d7ed0695f8c7caaa9eed0521483a54adb03d54b` |
| Subjects | `18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a` |
| ASv6.100 template | `0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f` |
| Bootstrap-v96 prompt | `599e811307cfd3feac290ec91b0c763f1900cc244fccc4756d8255027a050845` |
| Compare-v48 prompt | `b225da8653af04dfbe41fc8ff9e4f9d8bf780df527e27ee3e2d088c0e7eb23af` |
| Subject-vector checkpoint | `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d` |
| Subject-vector model tree | `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d` |
| Subject-vector container image | `a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa` |
| Subject-vector worker source | `eccf48810ca4f43724f7e197d71c25e456d62ed510ba13f8cf40e90127a580fc` |
| Subject-vector receipt | `c35d1d37279c164a4e628be9c12e769667b8b3a8166be7ee686a2726881b80a1` |
| Subject-vector data | `d2012833be298658fe6686c8e9ea3233279d806a5d4061be7071059da0f7d429` |
| Menu recipe | `bd576d8e2617940bb7dfb9bb37ce5692654bcc8e2dee4c7d53cbdd256a5dacfe` |
| Shared-runner fingerprint | `5fa694dce385a2579286bae5a637625bfe14818ca6511de8cbec014724c44888` |
| Raw hierarchy | `853343330cac7db7c2cc9c5a2a333b590c05ca79c8563df0b7261850789a3aae` |
| Browsing menu | `4fd0a99ed797b57f94a79d8c1c90ba5d81df72de071bec73d1372a0922e1dc8c` |
| Browser export | `763ddd9c614581529653dcd1dcd342a3145ccd9beb9f194655448ee5f4f69060` |

## Registering future runs

Register a run only when the human explicitly designates it as official.
Completing a diagnostic, approving its execution or generating a browsing output
does not make it official. Checkpoints and derived outputs remain attached to
their run; they do not receive separate run IDs. The previous `H0001`–`H0701`
diagnostic inventory is withdrawn, and those IDs must not be reused.

The [catalogue source](../../sse_multivector/hierarchy-catalogue-source-v1.json)
contains the explicit `official_runs` list. Each entry records `version_id`,
`name`, `root`, `artifact_path` and `sha256`, with optional `related_outputs` for
the run's other saved outputs. The
[version registry](../../sse_multivector/hierarchy-versions.json) binds the ID to
its preserved output and parameter evidence. The existing-run cutoff remains
October 8, 2026 at midnight America/New_York (`2026-10-08T04:00:00Z`). Older bound
inputs remain provenance.

Keep this Markdown register and the explicit source list synchronized when
registering an official run. Before a new run, record the full commits of Oracle
and the shared runner, plus any uncommitted source changes, alongside their
frozen code hashes. Generator source is accepted only when its bytes match a
saved hash. An exact Git blob identifies file contents, not the run's overall
commit.

Regenerate the catalogue after updating the explicit official-run list, from a
task worktree:

```bash
/home/dev/src/notedeck_worktrees/algos/experiment-runner/bin/experiment-runner \
  --project-root "$PWD" catalogue-hierarchies \
  --source sse_multivector/hierarchy-catalogue-source-v1.json \
  --registry sse_multivector/hierarchy-versions.json \
  --output /home/dev/src/notedeck_worktrees/algos/oracle-mvp/target/hierarchy-catalogue
```

This offline command makes no model calls and preserves original experiments.
Use `--saved-only` to regenerate from retained records. Generated pages, parameter
evidence and output snapshots stay ignored under `target/`; preserve them with
the original runs. The registry alone is not a backup. Experiment preparation,
execution and resumption still use task worktrees and the shared launcher.
The [HTML viewer](../../target/hierarchy-catalogue/index.html) also supports
side-by-side comparison of official runs.
