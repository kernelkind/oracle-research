# Bootstrap-v122: four original HR04 Food definitions

The user requested fresh explicit meanings for all four original HR04 Food
nodes, followed by assessment of whether their discrepancies are justified
against the posts. Historical definitions and labels are not expected answers.
Bootstrap-v122 remains unchanged; no Compare calls, hierarchy construction or
UI changes are part of this diagnostic.

## Input and execution identity

The [four-entry selection](hierarchy-bootstrap-hr04-four-foods-v1.json) uses
the original HR04 corpus, complete selected-root trees and full source posts.
All four selected entries are Food roots, number `1`:

| Historical node | Post | Original note ID | Tree entries |
|---|---|---|---:|
| C003 | Mushroom risotto with shrimp | a7475c940b50d31d115c9cea990b14b1c6c3b02232e9a005305e0257373fc5dc | 34 |
| C004 | Cranberry sourdough | ab52ebc67eed9ae6d8e8bd327073ff0ed4e80e267f2b76dfcb8a4468d136c895 | 24 |
| C009 | Matcha-cashew pie | 493f02481e0355200d3390369435cefc29bdeacce8f218771b35795971d82556 | 9 |
| C014 | Brisket on a homemade barrel smoker | c68026e7c9e1f97913aa4044eea86d60c22ce1d8469b315ebb8a124149235525 | 3 |

The corpus SHA-256 is
`18370b4772fee22c8d11f49a505f20f781f163e0512a8f32473d487ebdc8849a`.
The original ASv6.100 provenance and exact HR04 selected-entry mappings were
checked independently. Other trees for the same raw posts are not substituted.
Historical Food meanings and review criteria remain outside model input.

The [frozen specification](hierarchy-bootstrap-v122-hr04-four-foods-v1.spec.json)
uses GPT-6.1 Sol medium, subscription SSE and automatic prefix caching through
main's shared runner. Native `prepare --repeat` makes all four intentional fresh
draws; there are no answer reuses. The experiment is
`target/bootstrap-v122-hr04-four-foods-v1/draw1` in the retained
`oracle-mvp-shr-pair-correctness-v1` worktree. Original receipts and outputs
remain immutable.

Before dispatch, the user clarified that another agent had removed the earlier
20,000-attempt cap. The old counter still reads limit/used 20,000; it was not
reset or edited. This newly authorized four-case run omits that obsolete optional
counter. This record does not impose a replacement total allowance or authorize
additional experiments.

## Exact fresh meanings and evidence assessment

### C003: risotto

> Food is substances and preparations intended for human consumption by eating or drinking, encompassing finished dishes and culinary ingredients intended to be incorporated into food for preparation, flavoring or seasoning. Examples include, but are not limited to, mushroom risotto with shrimp and its ingredients.

The original post names mushroom risotto with shrimp and lists its ingredients,
including wine, broth, fats, herbs and seasonings. Those support prepared-food
and ingredient coverage in the human culinary sense. Nourishment is not a
membership condition in this definition. The diagnostics choose human
consumption without contrasting other consumers or nourishment-only scope.

Producer record SHA-256:
`a46284ea16ffa29382e229cfafd6b051358bda97d63a8b919a5e4dfa350f8d31`.

### C004: sourdough

> Food is material intended for human consumption as nourishment or as an edible ingredient in something eaten, including but not limited to prepared bread, cranberries, culinary rosemary, brown sugar and cinnamon.

The post names the bread and all four ingredients, then praises the bread:
"good lord it soo good". Prepared food and ingredient coverage are supported.
The post does not establish why a finished food needs a nourishment purpose,
while an ingredient qualifies through its edible-component role. This is a
chosen category boundary, not a source-established distinction from the pie or
risotto meanings. Its resolution contains that nourishment-or-component choice;
this is not merely a condition added while writing the final meaning.

Producer record SHA-256:
`88a6c0eef63d8019ad4f61a4bb295c2eded5c8e235dd20a12f697372e654e51e`.

### C009: pie

> Food is substances and preparations intended to be eaten for nourishment or enjoyment, including but not limited to finished dishes such as pies and edible ingredients consumed directly or incorporated into dishes.

The post describes making an Easter matcha-cashew pie, carrot decorations made
with real carrots and coconut butter, its dietary properties, and
"Addictive potential...". The particular pie's appeal supports an enjoyment
interpretation. It does not establish that enjoyment must be admitted here but
not under the sourdough or brisket categories. Human consumption is not an
explicit membership condition in this final meaning. The diagnostics do not
contrast that consumer boundary or nourishment-only scope.

Producer record SHA-256:
`ee7aee09611939f8360dcb7908e21ef6c7c5d1e702e04b3e48745a7d901ef054`.

### C014: brisket

> Food is edible material consumed or intended to be consumed for nourishment, including but not limited to meat such as brisket.

The full original post is "#foodstr brisket on a homemade barrel  smoker."
followed by an image URL. The Food hashtag, brisket and smoker support the
culinary interpretation. They do not establish compulsory nourishment or
exclusion of enjoyment. This definition does not explicitly restrict consumers
to humans. Its diagnostics examine broad-category scope and equipment membership,
not nourishment versus enjoyment or human versus other consumers.

Producer record SHA-256:
`187a40ea2f813b5c2dc1e5501001403be2eff97bf2ae3087df7eeedae23d5f39`.

## Finding and limits

Root and an independent read-only reviewer find that all four meanings fit the
source examples; no definite post contradiction is established. Material
consumer, purpose and eating/drinking differences remain. The posts do not
establish why these four categories must differ in those conditions.

These are individually permissible boundary choices under the present contract,
not evidence-required discrepancies. The source supports culinary interpretation
and food/ingredient examples; absence of an enjoyment statement does not make
nourishment mandatory. Conversely, praise of one food does not by itself dictate
the whole category's purpose boundary. Matching headings do not certify
equivalence, and no new pair label is established here.

The diagnostics never directly identify or resolve the consequential contrasts
between human and other consumers, nourishment and enjoyment, or eating and
drinking. Those choices nonetheless enter final membership conditions. No
definite resolution/final mismatch is established: the weak point is boundary
identification and selection before final expression. A single fresh draw per
source cannot establish repeatability or attribute these choices to a particular
prompt sentence. Old C003 poison judgments are not transferred to these strings.

The proposed next step is to review with the user whether this source-independent
boundary variation is acceptable, before another prompt edit. If it is not,
test a general requirement to explicitly examine each consequential condition
being introduced, rather than prescribing one Food definition or food-specific
exceptions. No such edit or further generation occurred.

## Native accounting and verification

Five attempts comprise four valid fresh definitions and one valid automatic
warmup. There are zero reuses, failures or retries. Three of four definition
requests report prefix cache hits. The native API-equivalent total is
$0.0533864 with complete usage; it is not an additional subscription charge.
The [native accounting source](hierarchy-bootstrap-v122-hr04-four-foods-usage-v1.json)
binds this draw separately from historical generation.

Exact case inputs, original AS source identity, evidence quotations and native
receipts were reviewed. Twenty-three existing prompt-revision and saved-comparison
checks pass after main synchronization. No implementation behavior or prompt
wording changed.
