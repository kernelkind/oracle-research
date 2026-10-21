# Bootstrap-v127: direct consumption and ingredient roles

## Controlled change and status

Experimental [Bootstrap-v127](Hierarchy-bootstrap-v127.md) extends one sentence
in v126's `Resolve category ambiguities` paragraph. After specifying a qualifying
kind and its role/use/component relationship, it asks whether that relationship
suffices or requires a particular function or purpose, and whether the required
role is intended or actual. The [edit source] (`sse_multivector/shr_single_pair/hierarchy-bootstrap-v127-role-function.edits.json` at `03bd9e45`)
and native revision receipt preserve all other bytes. No Food-specific condition,
medical example, validation witness, input field or output-schema change occurs.

| Prompt | SHA256 |
|---|---|
| v126, unchanged base | `85dbf0b23de1dd085cdd7519650d0e9bcf9bd7264e4d517b1a1f461c436e3f30` |
| v127, tested candidate | `b178df05f67c12fc7af108d43ce4c8fda1f23e7b5f1d62a6a6543c8fd544323a` |

V127 remains tested experimental evidence, without an activation recommendation.
V126 remains the working experimental baseline, not a generally qualified
production prompt. This result does not establish that extra instructions improve
boundary identification. Integration of either prompt does not activate it.

## Frozen evidence and execution

The first draw regenerates the same four original ASv6.100 Food inputs as
[v125/v126](bootstrap-v125-v126-food-kind-features-v1.md); their full posts and
complete selected-root trees remain fixed. The input strings match the actual
HR09 Food producer inputs byte-for-byte. Case IDs remain the earlier HR04 selection
IDs, not model-input identities or newly substituted notes. No old answer,
counterexample, expectation or graph identity enters Bootstrap input.

Native experiments in `oracle-mvp-shr-pair-correctness-v1`:

- `target/bootstrap-v127-hr04-four-foods-v1/draw1`: four fresh definitions.
- `target/bootstrap-v127-hr04-four-foods-v1/repeat`: fresh risotto and sourdough
  definitions with identical prompt, inputs and non-prompt settings.

Both use the isolated shared runner at `experiment-runner-hr08-hr10-source-v1`,
commit `e19592f`, matching current runner main. GPT-6.1 Sol medium, SSE, automatic
prefix warming, concurrency 30 and timeout 600 seconds stay fixed. No attempt cap,
Compare inference, hierarchy construction or UI refresh occurs. Different draws
are separate definitions; no output is spliced or retrospectively repaired.

## What the saved counterexamples establish

All six final meanings retain a shared physical condition: edible material or
material suitable for eating directly or after preparation. They therefore exclude
the explicitly non-edible poison and already poisonous death-cap dish even when
intended for nourishment. Source ingredients remain covered. No definite invented
particular fact or lost ingredient was found by two independent read-only reviews.

The [saved witnesses](bootstrap-v125-v126-food-kind-features-v1.md#saved-counterexamples-as-bootstrap-regressions)
test each exact meaning; medical admission is not automatic negative gold.
Direct consumption and incorporation must be assessed separately:

| Cohort / Food source | Standalone edible diagnostic wafer | Diagnostic beads mixed into porridge |
|---|---|---|
| First risotto | Admitted through direct human eating. | Qualified: make/season and culinary-role wording must be interpreted; standalone consumption cannot silently replace an incorporated role. |
| First sourdough | Admitted through intended human eating. | Admitted through an edible ingredient in prepared food; no separate culinary-purpose condition is supplied. |
| First pie | Solely diagnostic purpose does not meet nourishment intention. | Incorporation alone does not establish the required nourishment intention. |
| First brisket | Diagnostic purpose alone establishes neither nourishment nor meal/snack setting. | Conditional on a meal/snack setting, absent from the saved porridge hypothesis. |
| Repeated risotto | Admitted through direct human eating. | Qualified by the explicit incorporation **as culinary ingredients** condition. |
| Repeated sourdough | Admitted through own consumption. | Admitted through an edible ingredient in something eaten; culinary purpose is not required. |

The repeated risotto's exact head is:

> Food is edible material intended for human consumption, either eaten or drunk directly or incorporated into dishes as culinary ingredients.

Its first resolution permits direct human consumption; its second says edible
substances intended as culinary ingredients qualify. The standalone wafer fits
the direct alternative. The beads are mixed into porridge, so that direct
alternative cannot automatically bypass their culinary-ingredient condition.
Whether their solely diagnostic function satisfies that condition remains
unresolved. This is a local improvement in explicit ingredient qualification,
not evidence of a reliable causal prompt effect.

The repeated sourdough instead permits edible material intended for human
consumption on its own or as an ingredient in something eaten. Both clinical
examples fit that broader wording, consistently with its resolutions. A
nourishment or culinary-purpose condition cannot be borrowed from another draw.

Medical drinks and medicinal oil remain conditional where the hypothesis does
not establish edibility. Swallowing ceremonial gold does not automatically
establish eating/drinking when those routes are required. Animal-feed exclusion
applies only to meanings that require human consumption. These witness details
cannot be silently changed to obtain a convenient label.

## Diagnostic result and next qualification

None of the six ambiguity lists directly contrasts relationship-only membership
with a required functional purpose. Most still contrast the broad category with
the illustrated dish, or finished dishes with ingredients. One repeat's clearer
culinary qualification does not demonstrate systematic benefit from v127's extra
instruction. No definite final-meaning/resolution mismatch was established.
Qualified native agent accepts preserve these findings and unresolved cases;
they are not user semantic approvals or full-branch passes.

Keep v127 as tested evidence rather than adding restrictions to force clinical
negatives. The user subsequently prioritizes the four Food definitions directly.
The [v128 breadth diagnostic](bootstrap-v128-food-breadth-qualification-v1.md)
tests that objective before further branch qualification. Complete original
Food-branch qualification remains unperformed: independently established children
would need assessment against their exact pinned parent meanings, preserving
qualifying-kind, purpose and consumer conditions. Do not optimize isolated
counterexamples toward an unstated preferred category.

## Native accounting and verification

The [native usage source] (`sse_multivector/shr_single_pair/hierarchy-bootstrap-v127-food-role-usage-v1.json` at `03bd9e45`)
produces `target/bootstrap-v127-hr04-four-foods-v1/usage-native-v1.json`.
Six definitions are valid, nonnull and fresh. Eight attempts include two warmups,
with zero failures, retries or answer reuses. All six definition requests report
cached input. Complete native usage reports **$0.0769484 API-equivalent cost**,
not subscription cash spending; reasoning is already included in output.

Forty-four focused checks pass: twenty-three prompt-revision/saved-comparison
checks and twenty-one prompt-assembly checks. Native validation and
two independent reviewers verify exact inputs, prompt/settings identities,
receipt/output hashes and evidence quotations. Each producer record remains in
its cohort's `run/results.jsonl`:

| Cohort | Case suffix | Producer record SHA256 |
|---|---|---|
| draw1 | risotto | `ca1f19569a97b5b832b25b8b03b7c2b4fb3174f58ea9ce3cb2c6dacda5f3ad66` |
| draw1 | sourdough | `d1a512cfb17e132653ba1a33bf68e2ccf37250eba00ffc5289a4bdd736b8cbe6` |
| draw1 | pie | `bb5d9345a03d7ab0bd048c8f38c8bb569778463621748513ef6ae43370f0a4c5` |
| draw1 | brisket | `6323a09e5d9b2216f32e7ff4503a42e960c2c3ac17dc2857a792f70c9c18fc42` |
| repeat | risotto | `d3ae0a64cb72b44fb5235314c57ddbfdc212e935155a115a1bb79bfb116fbf13` |
| repeat | sourdough | `38ef29bd2116b973942ff7239ed1476b66bd9fbad9badd860cda0cf769ea700d` |

Full case IDs have prefix `hr04-food-`. Saved outputs, receipts and earlier
reviews remain unchanged. No general reliability, category equivalence,
completed hierarchy or comprehensive legacy-suite pass is claimed.
