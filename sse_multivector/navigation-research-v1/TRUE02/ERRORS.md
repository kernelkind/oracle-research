# TRUE02 — All errors, with the actual categories

Each row asks **Does A contain B?** Both full category strings are shown. The exact input is `premise: This text is about {B}. hypothesis: This text is about {A}.` No note text, mask, explanation, or expected answer was given to the model.

Score means the full-vocabulary probability of the first output token being `1`. Native is the complete generated answer. Cutoff accepts when score > 0.142. None of the expectations were changed after inference.

## Three invalid relationships accepted by the cutoff

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---:|---|
| F6-contains-F2 | Bread baking | Sourdough bread | No | Yes | 0.5380854792535511 | Yes |
| F6-contains-F4 | Bread baking | Gluten-free bread | No | No | 0.17845554844592706 | Yes |
| F6-contains-F5 | Bread baking | Bread made without gluten | No | Yes | 0.5091760385618475 | Yes |

**Why No:** eating, storing, or discussing the nutritional properties of either variety belongs to that bread topic without necessarily belonging to baking. Bread baking is an appropriate narrower topic under Bread, not a parent containing every discussion of these varieties. The last two descriptions are equivalent, so these are one recurring error pattern across two varieties and two phrasings for one of them.

The native model already makes two of the three errors. Lowering the decision boundary adds only the Gluten-free bread error; it does not create the whole pattern.

## Eleven valid relationships missed by the native answer, recovered by the cutoff

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---:|---|
| S1-contains-S2 | Software testing | Testing web applications | Yes | No | 0.3579706389767548 | Yes |
| S1-contains-S4 | Software testing | Security testing of web applications | Yes | No | 0.1574639227098067 | Yes |
| S1-contains-S5 | Software testing | Testing the security of web applications | Yes | No | 0.35769393086777107 | Yes |
| S3-contains-S4 | Software security testing | Security testing of web applications | Yes | No | 0.39494610331706076 | Yes |
| S3-contains-S5 | Software security testing | Testing the security of web applications | Yes | No | 0.44173951011910384 | Yes |
| E3-contains-E4 | Environmental policy | Carbon taxes | Yes | No | 0.2529240445333169 | Yes |
| E3-contains-E5 | Environmental policy | Taxes on carbon emissions | Yes | No | 0.23918733838272774 | Yes |
| E3-contains-E6 | Environmental policy | Carbon emissions trading | Yes | No | 0.19387817385622083 | Yes |
| P1-contains-P2 | Political campaigning | Election fundraising | Yes | No | 0.2921858687948083 | Yes |
| P3-contains-P5 | Online political campaigning | Raising money online for election campaigns | Yes | No | 0.49567884433331794 | Yes |
| R3-contains-R5 | Workplace relationships | Workplace mentoring | Yes | No | 0.46653531691823674 | Yes |

**Software:** web applications are software. Testing their security is a narrower kind of software testing and software security testing. The broader topics also include other software targets and testing purposes.

**Economics:** carbon taxes and carbon-emissions trading are environmental-policy instruments. They need not be the same instrument, and their effectiveness is irrelevant to this categorical relationship. Environmental policy also encompasses other instruments.

**Politics:** election fundraising is a political-campaigning activity. Raising election funds online is a narrower online political-campaigning activity. Campaigning is not restricted to persuasion alone.

**Interpersonal:** workplace mentoring is a workplace relationship. Other workplace relationships need not be mentoring.

These explanations reflect judgments recorded before model scores, not rationalizations chosen to agree with the classifier. A literal object/process taxonomy would be a different task from the topical hierarchy evaluated here.

There are 14 distinct error rows across the two decision rules: 13 native errors, three cutoff errors, two shared. Every correct and incorrect decision (`03bd9e45:sse_multivector/navigation-research-v1/TRUE02/DECISIONS.md`).
