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
20,000-attempt cap. This newly authorized four-case run omits that obsolete
optional counter. The user subsequently explicitly required permanent removal.
The active artifact path was retired to
`target/hierarchy-selective-sprint-v1/attempt-budget.json.retired`, preserving
its exact historical bytes and used count. Its SHA-256 is
`d0199c9f595afd646f501be8f74689c8f616e857e926abf8e542b500a689847b`.
No replacement global attempt cap is established; native attempts and usage
continue to be recorded without that optional counter.

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

## Compare counterexamples: reassessment of the exact fresh meanings

The first review checked source-example fit and called the differences
individually permissible. The user explicitly corrected that standard:
"regarding the results, you MUST consider the counterexamples presented by
COmpare." Root and the independent reviewer reassessed the same unchanged
outputs using the actual saved HR04 witnesses. Fitting the particular post
does not establish that a definition preserves the chosen category's scope.

The witness hypotheses are tested against fresh final wording, without silently
adding conditions or transferring historical pair labels. This is read-only
Bootstrap review; no new Compare calls or relation labels were generated.

| Saved Compare witness | Fresh risotto Food | Fresh sourdough Food | Fresh pie Food | Fresh brisket Food |
|---|---|---|---|---|
| Lethal, non-edible chemical intended as a component of a human-consumed poisoned drink | Admitted by unrestricted human eating/drinking condition | Excluded: no nourishment or edible ingredient role | Excluded: no nourishment or enjoyment purpose | Excluded: no nourishment, not edible |
| Barium sulfate in a human-consumed drink solely for diagnostic imaging | Admitted by human drinking condition | Excluded: no nourishment or edible ingredient in something eaten | Excluded: no nourishment or enjoyment purpose | Excluded: no nourishment purpose |
| Edible, nonnutritive wafer eaten solely to measure intestinal transit | Admitted by human eating condition | Excluded: neither nourishment nor an ingredient role | Excluded: neither nourishment nor enjoyment | Excluded: no nourishment |
| Food-grade edible gold swallowed alone solely for ceremony, without nourishment or a component role | Admission depends on whether the stated swallowing counts as eating | Excluded: neither nourishment nor an ingredient role | Uncertain: the witness does not explicitly resolve enjoyment as a purpose | Excluded: no nourishment |
| Cattle or horse feed intended exclusively for those animals to eat as nourishment | Excluded by human-consumer condition | Excluded by human-consumer condition | Admitted: nourishment and intended eating, with no human condition | Admitted when edible for the relevant consumer; human edibility cannot be added silently |
| Pure nonnutritive mineral oil intended to be drunk solely as a laxative, with no food-ingredient or accompanying-beverage use | Admitted by human drinking condition | Excluded: no nourishment or qualifying ingredient role | Excluded: no nourishment or enjoyment | Excluded: no nourishment |
| Bacterium eaten as nourishment by a wild amoeba, with no intended consumption, preparation use or meal connection | Excluded: no intended human consumption | Excluded: no intended human consumption | Excluded: no intended eating | Conditional: actual consumption is admitted, but the intended consumer of "edible" is unsettled |

These are semantic hypotheses as stated by Compare, not assertions that a
source post contains any of them. Qualified admissions stay qualified. In
particular, the gold witness cannot acquire an unstated enjoyment purpose or
an automatic equivalence between swallowing and eating.

### Source-bound witness provenance

All experiments below are under the original HR04
`target/hierarchy-hr04-twelve-note-v1/trial` directory in
`oracle-mvp-hierarchy-hr04-twelve-note-v1`. Saved historical meanings remain
unchanged, and the fresh four-output cohort is separate.

| Native experiment / case | Witnesses | Compare record SHA-256 |
|---|---|---|
| batch-00010/experiment / C003 | Poison; ceremonial gold | a2915d0c6c644180cf821a7de56c504703e0d785bd3f4254f0376e7c9e0f2039 |
| batch-00017/experiment / C003 | Diagnostic contrast drink; cattle feed | 9df0b81b836352f5222c6d5d4455b750e317f896e4335b91595b3fe711cba548 |
| batch-00017/experiment / C004 | Diagnostic wafer; horse feed | fa0844207cbe59c95afa6b9c5d270e8312a6d9d16c126b41b87522e414396a4b |
| batch-00039/experiment / C007 | Medicinal mineral oil; wild amoeba eating a bacterium | 2ee768406f3a7d410ef03417dd10db2f2659832ca556ea5f3e4beb05424152c3 |

The [earlier user-reviewed poison admission](bootstrap-hr04-food-boundaries-v1.md#historical-distinction)
is bound to the old C003 string. Here the same hypothesis is independently
admitted by the fresh risotto string's broader head clause. Other witnesses are
saved Compare proposals assessed by agents; their existence is not human gold.

## Corrected finding and limits

**Risotto's fresh meaning has a concrete scope-quality defect.** Its unrestricted
head clause admits toxic and medicinal human ingestion. Naming finished dishes
and culinary ingredients afterward does not make culinary or edible status a
shared condition on all substances admitted by that clause. The chosen culinary
Food identity is therefore broader in its expressed membership than the source
interpretation supports. The native agent review is revised to reject on that
ground, rather than claiming a false fact about the particular risotto.

Sourdough excludes the specified non-nourishing, non-ingredient ingestion
witnesses through its own stated conditions. Its nourishment-or-ingredient
boundary is still a choice, not a distinction uniquely required by the bread
post. Pie admits animal feed; that is a real broader consumer scope, not by
itself proof that animal Food is an invalid category choice. Brisket additionally
leaves whether edibility is human-relative or consumer-relative unclear for
the amoeba witness. Original human-culinary context cannot silently supply a
human restriction missing from either final meaning. The assessments are one
reject, two qualified accepts and one uncertain meaning; they are agent reviews,
not a human accuracy score or certification of pair relationships.

The posts do not establish why nourishment, enjoyment or consumer conditions
must differ. The diagnostics fail to directly examine those consequential
contrasts. The producer weakness includes both choosing the category boundary
and carrying its identity and conditions into every admitted alternative. A
single fresh draw cannot establish recurrence or identify a responsible prompt
sentence. Matching Food headings do not certify equivalence.

The next proposed focus is the risotto head-clause gap: examine how the producer
can state a category's qualifying kind for every alternative, rather than add
exceptions for poisons or medicines. Review the unresolved consumer/edibility
boundaries separately. No prompt edit or additional generation was performed
in this reassessment.

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
