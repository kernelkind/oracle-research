# BCPv1 — SP branch comparison

Status: **draft, untested, not frozen**. The user authorized drafting this
prompt for review, not inference or changes to the saved hierarchy.

[BCPv1.md](BCPv1.md) is a new prompt, not a revision of the older mask-only
equivalence or placement prompts. It compares supplied SP subject branches
together, proposing missing parent links, semantic equivalences, or no change.
It does not minimize node count or collapse equal-post nodes.

## Input and output

Use the shared experiment runner's generic adapter with one `INPUT_JSON`
variable. Serialize the input as JSON; do not manually render batches.
Include:

- Stable node IDs and all original subject entries represented by each node.
- Each entry's post ID, SP number, exact subject wording and saved `context`.
- Its mask ID and complete source post with that individual mask marked inline.
  Preserve separate masks, including repeated posts. Represent an empty mask
  explicitly while retaining the subject and full post.
- Existing parent–child links between the supplied nodes. Reuse one node ID
  wherever a node is already shared across paths.

Supply source evidence, not expected answers, previous model decisions or
cosine scores. Existing links are inputs, not the model's proposed additions.
The proposed test output is a readable list of relationships, brief
justifications, unresolved comparisons and any conflicts. There is no graph
update parser or automatic application stage in this draft. Unmentioned pairs
are not negative labels.

## Proposed first review

After prompt approval, the proposed test is one call per saved case:

1. N037 / N072: Food ingredients and Baking ingredients above shared Cranberries.
2. N015: food-preparation and bread-type paths above Sourdough bread preparation.
3. N065: internet-access, network-equipment and retaliation paths above the
   contemplated disruption of coffee shop internet access through password changes.
4. N038: music, song and coffee-shop paths, including the distinction between
   Coffee shop playing Baby Got Back and Baby Got Back playing in a coffee shop.

These are diagnostic cases, not validated accuracy labels or examples embedded
in the prompt. Preserve the saved SMv2 graph and all earlier results. Any run,
input preparation and application policy remain separate work; this draft
does not authorize them or select a production placement algorithm.

## Design references

The draft follows the existing
[SP hierarchy rules](../../docs/planning/release-decisions.md#sp-based-hierarchy-rules),
particularly HD08–11 and the open placement question HD21. No rule-register or
existing prompt changes are made here.

The [official OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively)
informed the direct task statement, separated input and initial test without
worked examples. This is guidance for the draft, not evidence that it works.
