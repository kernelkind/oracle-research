# ASv6.49

Status: superseded, untested.
[ASv6.51 (approved candidate, tested on Sol xhigh)](../asv6.51/ASv6.51.md) is the latest
approved subject prompt. ASv6.49 repeated existing instructions about refinement
and independently understandable headings; ASv6.50 clarified the existing
hierarchy paragraph instead. ASv6.48 remains the frozen subject baseline.
MPv3.43 remains the frozen mask working baseline.

## Change and prompt audit

[ASv6.49.md](ASv6.49.md) adds one paragraph to the hierarchy instructions in
[ASv6.48](../asv6.48/ASv6.48.md). Each child heading must refine its parent's
meaning without borrowing restrictions from the source post or `context`.
The question is whether every post about the child would also be about the
parent.

The initial lunar-eclipse and railway-museum audit missed one qualifier loss:
the railway example's 7.1.1 names Bracken as a steam locomotive, while its
7.1.1.1 child omits that type. The [subsequent ASv6.51 audit](../asv6.50/README.md#worked-example-finding)
records this inconsistency. The examples' source posts, headings, contexts and
numbering remain byte-identical in ASv6.49. The separately authorized
[ASv6.53 (draft, untested)](../asv6.53/ASv6.53.md) corrects this loss and the
missing placements in both worked examples. ASv6.52's initial audit missed the
every-applicable-branch requirement. The corrected wording and model test
remain open. The current [ASv6.54 (draft, untested on models)](../asv6.54/ASv6.54.md)
uses focused cases to cover the remaining rules; its
[rule-to-case map](../asv6.50/README.md#example-correctness-and-rule-coverage)
records their instruction basis and review status.
The existing instructions retain individual subjects, combinations and broader
headings. This revision preserves those coverage requirements.

The shared `experiment.py revise` command generated the draft and revision
receipt against ASv6.48 SHA-256
`e1d5740e68b5f5c29e139ad3fbb37839f91784784aaa31b3bdbdc4a829a4bacc`.
No model calls were made. Mechanical checks of the revision do not establish
semantic improvement.

## Agreed regression set

On October 1, 2026, the user chose N063, N074, N096 and N100 from the saved
100-post ASv6.48 collection as the regression set for this failure pattern.
Use the complete original posts and saved outputs from
`../../hierarchy-refresh-v1/subjects.json`; do not shorten the posts or regenerate
the saved baseline.

| Post | Saved relationship illustrating the failure | Required meaning |
| --- | --- | --- |
| N063 | 2.1 Ingredients for mushroom risotto with shrimp → 2.1.8 Cooking fats | A child in the dish-specific branch must retain that scope. Preserve supported general ingredients and their broader headings elsewhere. The other general ingredient children require the same check. |
| N074 | 6.1 Eating real food in moderation, mostly plants → 6.1.1 Eating real food | A child of the combined recommendation must preserve all its restrictions. Preserve the individual recommendations and their combination. Also inspect 6.1.2 and 6.1.3. |
| N096 | 4.1 Bolognaise sauce preparation → 4.1.4 Gently frying ground beef without browning | A step in this branch must retain its Bolognaise preparation meaning. Preserve the supported preparation steps and inspect the other children of 4.1. |
| N100 | 4 Use of meat-processing byproducts → 4.1 Beef fat | A child in this branch must retain the byproduct-use meaning. Preserve the supported general material subjects and particular uses. Also inspect 4.2, 4.3 and 4.5. |

Judge complete returned hierarchies, including coverage and newly introduced
errors. Different faithful wording, numbering and organization are acceptable;
matching saved strings is not the acceptance rule. Removing supported general
subjects or their particular instances does not satisfy the regression.

## Approved comparison

On October 1, 2026, the user approved the ASv6.50 delta and requested testing on
GPT-6.1 Sol xhigh. The [candidate comparison](../asv6.50/README.md#approved-candidate-comparison-on-gpt-61-sol-xhigh)
uses the shared experiment workflow for three independent ASv6.50 outputs per
regression post, compared with saved Sol ASv6.48 answers. Independent trials
disable request reuse through `--repeat`. All twelve answers completed; two
contain the parent-scope failure pattern. The linked comparison records the
complete-output reviews and separate grounding uncertainties. The user has
authorized the [ASv6.51 comparison](../asv6.50/README.md#asv651-comparison-on-gpt-61-sol-xhigh),
with a fresh transfer check outside food conditional on a passing regression set.
All twelve initial ASv6.51 requests were interrupted by a local service interruption. No candidate answer completed in that attempt. The user
subsequently authorized the identical twelve-request retry set on GPT-6.1 Sol
xhigh. All twelve answers completed; N096 trials 1 and 3 contain new instances
of the same failure pattern. The linked comparison records all twelve agent
reviews, coverage findings and separate grounding uncertainties. The conditional
non-food check was not started because the regression set did not pass.
