# NMP-Jev-v1 — mask-based node merging

Status: tested in the approved Sleep and diverse-pair comparisons; not frozen or adopted.
The unchanged title-only NSP-Jev-v3 remains the saved comparison baseline.

This separate prompt asks whether two groups express the same topic at the same
level of generality. It replaces generated title inputs with the masks in each
group. It does not generate titles, place parents or change the saved tree.

## Input and output

- `A_MASKS_JSON` and `B_MASKS_JSON`: JSON-serialized arrays of masks, each mask
  represented by its ordered array of exact fragment strings. Preserve the
  existing title adapter's exact same-post mask deduplication and instance order.
  The placeholders are unquoted because the values are arrays, not JSON strings.
- Supply the two groups separately. Do not combine them, flatten fragments
  across masks, or add titles, source-post text, IDs or tree positions.
- Use the shared generic adapter's literal variable substitution; serialize
  arrays with a JSON encoder. Never concatenate unescaped source text into JSON.
- Intended transport: `typesafe/jev-1.13` through the existing System One runner,
  with `provider-default` reasoning. No model change is proposed.
- Native choice question: `same_topic`, with `yes`, `no`, or `uncertain`.
  This is one symmetric equivalence question, not a directed containment answer.
  Do not relabel it as two native `contains` answers or feed it unchanged to the
  old directional-result validator.

## Scope and review

The initial comparison used the same ten saved Sleep group pairs from
HR02-NT02-C01, tested separately as HR02-NT02-C02. The user then approved a
small diverse sample, tested as HR02-NMP02 with twelve other saved pairs.
Both use the shared experiment runner without baseline reruns. Only a direct
Yes permits a collapse; No and Uncertain remain distinct. HR02-NMP02 examines
pairwise decisions only and performs no contraction. Saved groups and masks
stay fixed. No new titles, parent placement or production adoption.

`merge_tree_nesting.mask_pair_cases` prepares the mask inputs through the
existing title adapter. `validate_equivalence_decisions` checks the exact
question, inputs, native choice and receipt-backed report;
`contract_equivalence` preserves direct answers separately from containment
answers. Both decision types reuse the same reversible edge-contraction code.
The original title-only results still replay exactly.

This changes both evidence (titles to masks) and question framing (two directed
containment answers to one equivalence answer). It is a comparison of those
complete approaches, not an isolation of the effect of adding masks alone.

The criterion is semantic scope, not identical masks, common words, group size
or a merely shared broader topic. Differing examples need not create different
topics; a genuinely narrower topic must remain distinguishable.

## Sleep comparison result

All ten requests completed with valid native answers: nine Yes, one No, no
retries or reused answers. Direct equivalence collapses eleven original groups
to two, versus six with the saved title-only approach. All twelve masks and
eleven original-group mappings remain recoverable. Input hashes are unchanged,
and both prior title-only consolidation results still replay exactly.

The two surviving groups retain their saved titles, **Sleep and tiredness**
(twelve masks) and **Sleep** (three masks). Their nesting comes from the saved
mask sets; this test did not validate semantic parent placement or generate titles.

Agent review accepts nine decisions and flags one as uncertain, not as a
user-approved error: the five-mask combined group was judged equivalent to the
two-mask group containing `[tired, 😴]` and `[fell asleep, very tired]`. The added
masks concern adequate/good sleep and sleep alone, so the merge may erase a useful
sleepiness distinction. Native probabilities were Yes 0.52, No 0.47, Uncertain
0.01; no threshold or output override was applied. Removing redundant levels is
encouraging, but this possible loss prevents claiming overall success or accuracy.

Receipts and separate agent assessments are in
`sse_multivector/experiments/hr02-sleep-mask-merge-jev-v1/`.
Derived consolidation and verification are in
`target/hierarchy-build-v1/hr02-sleep-mask-merge-v1/`.
Provider-reported cost was $0.000287994.
Subsequent read-only inspection judged this an incorrect merge: the two masks
express tiredness, while the added sleep-only masks do not require tiredness.
That is an agent assessment, not a user verdict; the saved run-time uncertainty
and native answer remain intact. The user approved the diverse test below.

## Diverse comparison result — HR02-NMP02

Twelve original saved edges were selected before inference: six expected to
merge and six expected to remain separate. Seven pairs come from the earlier
food/nonfood diagnostics, five from the saved M06 tree. Their grouping/title
provenance differs; all model inputs contain only the exact grouped masks.
The purposive sample covers Dinner, Recipes, Coffee, Art, Children, Tea, Food,
Animals, Emotions and Morning greetings. It is not a representative accuracy
estimate, and pre-run expectations are agent judgments, not human ground truth.

All twelve fresh requests completed successfully, with no reuse or retries.
Nine matched pre-run expectations. Agent review accepts nine decisions, rejects
two and flags one as uncertain:

- **Art: missed merge.** Both groups retain explicit art masks; adding painting
  supplies another art example, not a different overall topic. Jev answered No.
- **Dinner: incorrect merge.** The smaller group always expresses dinner;
  added standalone grilling out and Barbecue Chain do not require dinner.
  Jev answered Yes, losing the narrower distinction if applied.
- **Children: uncertain missed merge.** Adding baby to kid/kids/son masks was
  expected to preserve the overall children topic. Jev answered No. The agent
  still leans toward merging, but colloquial age boundaries make this less clear.

The five other narrower distinctions were preserved: Hot tea, Processed food,
Dogs, Happiness and Morning greetings. Four repetition/example additions also
received the expected Yes. This tests scope preservation, not just node-count
reduction. The saved title-only decisions agreed with the agent's expectations
on the three disputed pairs; the mask approach is not uniformly better.

Receipts and separate agent assessments:
`sse_multivector/experiments/hr02-diverse-mask-merge-jev-v1/`.
Pre-run selection, exact input provenance, results and verification:
`target/hierarchy-build-v1/hr02-diverse-mask-merge-v1/`.
Provider-reported cost was $0.000293118.
All source hashes and the prompt are unchanged; 83 regression tests pass.

The subsequent read-only audit found that NMP-Jev-v1 already states the relevant
scope and example distinctions; these outputs do not establish a missing
instruction or a contradiction. The recommendation was to leave it unchanged
and inspect the saved merge decisions in the hierarchy UI. The user approved
that comparison, not a revision, additional inference or adoption.

## Saved hierarchy comparison

The existing category browser now exposes Original groups, Title-based merges
and Mask-based merges for each tested topic. Sleep, Dinner, Art and Children
appear first; seven further topics are under Other tested topics. These are
navigation menus, not newly generated hierarchy nodes.

Both methods apply only the same **22 tested original pairs**. All **33 other
links** in the displayed branches remain separate in both views, even where
title-only answers already exist. Thus the title view is a matched-coverage
comparison, not the fully consolidated historical title result. View labels
show tested/total counts; `?` exposes native answers, untested links and saved
agent concerns. Native mask answers are never relabeled as containment answers.

All original groups remain in the Original view. Surviving groups retain their
saved titles and masks; no renamed nodes, inferred memberships, semantic parent
repairs or model calls are involved. Links show saved mask-set nesting, not a
validated semantic hierarchy. Browser equal-note and single-child collapsing
are disabled here so they cannot conceal differences between the methods.

```bash
cd /home/dev/src/notedeck_worktrees/algos && \
bash oracle-mvp/sse_multivector/run-merge-comparison.sh
```

Enter/l opens a topic, view or node; Backspace returns. N shows posts, D shows
direct posts, and O shows masks outside the children, individually with IDs;
`[` and `]` switch masks. `?` shows analysis. The UI is read-only: nothing is
approved, edited or merged by browsing.

The reusable offline exporter is [merge_tree_comparison.py](../merge_tree_comparison.py),
configured by [merge-comparison-hr02-v1.json](../merge-comparison-hr02-v1.json).
It validates the saved title/mask experiment receipts through the shared runner,
reuses existing contraction and mask rendering, and refuses to overwrite an
export. Generated categories, source hashes and reversible mappings are ignored
under `target/hierarchy-build-v1/hr02-merge-comparison-v2/`.

Verification: the new test suite first failed because the exporter did not yet
exist; a further test caught ambiguous attribution of agent comments, now fixed.
All five new tests and 83 related tests pass. The browser accepts the export
with `--check`; interactive inspection confirms the three-view menu and full
post display with original mask IDs. Canonical HR02 is unchanged.

Next: review Sleep first to see the reduction in repeated levels, then Dinner
to assess the cost of losing a narrower group. This is a browsing comparison,
not a decision to adopt either merge method.

The full delta against NSP-Jev-v3 and its exact edits are reproducible from
`prompt.txt.revision.json`, generated by `experiment.py revise`. The prompt is
versioned separately because its input and question contracts materially differ.

Drafting follows the general principles of concise instructions, separated
inputs and starting without examples from the official OpenAI
[prompting guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).
That guidance is not evidence of effectiveness for Jev; no OpenAI-model-specific
parameters or reasoning instructions were transferred to this prompt.
