# ASv6.26 compared with frozen ASv6.23

These pre-ASv6.100 results are retained as historical evidence.

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.26 adds useful broader subjects, but does not fix the motivating omission: none of its three coffee-shop outputs independently names Coffee shops. None of the three fresh ASv6.23 outputs does either. ASv6.23 remains frozen.

24 successful calls: four real posts, two prompts, three fresh trials each. Both prompts used Astra low through the same pi-ai subscription runner. ASv6.23 is the control; no intervening draft is treated as a baseline.

## What was tested

ASv6.26 adds two instructions to frozen ASv6.23: independently represent broader subjects that occur within detailed entries, and keep each subject at its intended level of detail when adding context. The evidence, ambiguity, number, reference-resolution, output-schema and model settings remain unchanged.

Each call received the exact approved prompt and original post, without added application instructions, conversation history or tools. The notes and review criteria are the same as the prior diagnostic. The baseline was generated afresh; historical outputs were not substituted.

## Findings

Counts below describe independent topic entries across three trials. “Narrower” means an independently named, valid narrower subject, not a factual error. A broad subject appearing only inside a particular claim is not counted as independently represented. Semantic equivalents are accepted; literal string matches are not required.

| Note | Subject checked | ASv6.23 | ASv6.26 |
| --- | --- | --- | --- |
| N065 | Coffee shops | 3 absent | 2 narrower; 1 absent |
| E0347 | Ad blocking in web browsers | 3 absent | 1 present; 2 narrower |
| E0347 | Tracker blocking | 1 narrower; 2 absent | 3 present |
| E0347 | Cookie-consent dialogs | 3 absent | 2 present; 1 absent |
| N022 | Beets | 2 narrower; 1 absent | 3 narrower |
| N022 | Raised-bed gardening | 3 absent | 3 narrower |
| N022 | Preserving food by vacuum sealing and freezing | 3 absent | 3 narrower |
| N067 | Cheesecake | 3 present | 3 present |
| N067 | Blueberry cheesecake | 3 present | 3 present |

An additional observation outside the fixed probes: all three ASv6.26 gardening outputs independently named **Home vegetable gardening**; none of the baseline outputs did. This is a useful broader subject, even though the specific Beets and Raised-bed gardening probes were not independently covered at their broad scopes.

All six short-note outputs independently named Cheesecake. The earlier diagnostic's difference on this topic did not repeat in the fresh baseline. That matters: three trials are not a stable estimate of reliability.

The candidate produced 149 subjects; the baseline produced 105. More subjects alone are not a quality gain. I reviewed every one of the 254 final subjects against its full note before revealing prompt identities. I identified no definite factual errors, and all checked specific source meanings were retained. Three baseline cheesecake outputs did not separately name Food, although it remained implicit in cheesecake/dessert. These are assistant judgments, not new user approvals or independent validation.

## Notes and evidence

### N065

> Coffee shop I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. Felt like changing their router/ap passwords so they could experience the true freedom from internet, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

Neither prompt independently names Coffee shops in any trial.

Candidate trial 1 begins:

> Restrictions on technology use in coffee shops.

Candidate trial 3 begins:

> A coffee shop's restrictions on laptop and tablet use.

Those are valid, narrower subjects. They do not supply the separate Coffee shops entry this experiment was designed to recover. The candidate also names subjects such as Freedom from the internet and Personal growth. It is capable of adding some broader subjects, but does not do so consistently for the one that motivated this comparison.

Both prompts retain the weekend ban, hipster criticism, contemplated network retaliation, decision to go elsewhere, plan to stop visiting, and humorous personal-growth framing.

Complete generated outputs:

- ASv6.23: trial 1 (`./N065-asv6.23-t1/run/output.json`), trial 2 (`./N065-asv6.23-t2/run/output.json`), trial 3 (`./N065-asv6.23-t3/run/output.json`).
- ASv6.26: trial 1 (`./N065-asv6.26-t1/run/output.json`), trial 2 (`./N065-asv6.26-t2/run/output.json`), trial 3 (`./N065-asv6.26-t3/run/output.json`).

### E0347

> fwiw, I'm on latest Vivaldi, default block setting just gets me the cookie dialog up on that page, in a new private window.
> 
> When I'm up-to-date and adblock doesn't work I usually just turn it down a notch to just "Block trackers" (shield icon left of padlock)

Candidate trial 2 independently names:

> Ad blocking in Vivaldi.

The other candidate trials name narrower subjects:

> Troubleshooting ad blocking in Vivaldi by changing the blocking setting.

> Ad blocking not working in Vivaldi.

All three candidate trials independently name tracker blocking or its named Vivaldi setting, without folding that entry into a factual comparison with ad blocking. Two name the cookie dialog independently. The baseline represents these meanings mainly through the author's specific observations and workaround; one baseline tracker-setting definition is recorded as partial coverage because it includes a contrast with ad blocking.

The browser version, default setting, private window, cookie dialog, usual workaround and shield-icon location remain represented in both prompts.

Complete generated outputs:

- ASv6.23: trial 1 (`./E0347-asv6.23-t1/run/output.json`), trial 2 (`./E0347-asv6.23-t2/run/output.json`), trial 3 (`./E0347-asv6.23-t3/run/output.json`).
- ASv6.26: trial 1 (`./E0347-asv6.26-t1/run/output.json`), trial 2 (`./E0347-asv6.26-t2/run/output.json`), trial 3 (`./E0347-asv6.26-t3/run/output.json`).

### N022

> This year’s beets. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town. https://image.nostr.build/b4349cc1251dccf78990620ee851ad0ae449327da16ac31391e3e71fafdbe65c.jpg https://image.nostr.build/5c7e4ba19bb3c2e98cb57753679d33be2bbad3a07900afc86315c85f80bc46e4.jpg 

All three candidate trials independently name:

> Home vegetable gardening.

They also contain valid narrower subjects such as:

> Growing beets in a 4x4 raised garden bed.

> Preserving homegrown beets for later use.

This is a broader-topic gain, not a failure merely because those subjects differ from our selected probes. However, it does not establish independent entries for Beets, Raised-bed gardening, or preservation at the specific broad scopes checked in the table.

Both prompts retain the harvested beets, vacuum sealing and preparation for freezing, favorable yield judgment, five meals, current town lot and desire for more space. No measurement units were invented.

Complete generated outputs:

- ASv6.23: trial 1 (`./N022-asv6.23-t1/run/output.json`), trial 2 (`./N022-asv6.23-t2/run/output.json`), trial 3 (`./N022-asv6.23-t3/run/output.json`).
- ASv6.26: trial 1 (`./N022-asv6.26-t1/run/output.json`), trial 2 (`./N022-asv6.26-t2/run/output.json`), trial 3 (`./N022-asv6.26-t3/run/output.json`).

### N067

> And my #Blueberry cheesecake!  #foodstr #nostr https://image.nostr.build/ffde1f0a6109f806b66beae798e610fa7d4055a8ca4b21565160ecf84de16753.jpg 

Both prompts independently name Cheesecake and Blueberry cheesecake in every trial. One baseline entry is “Cheesecake as a dessert,” which is accepted as equivalent broad-topic coverage rather than rejected for different wording.

The candidate additionally names Food and Desserts in all three trials. The baseline leaves Food implicit. All six outputs retain the author's blueberry cheesecake; none introduces subjects about the URL or bare Nostr identifier/hashtag metadata.

Complete generated outputs:

- ASv6.23: trial 1 (`./N067-asv6.23-t1/run/output.json`), trial 2 (`./N067-asv6.23-t2/run/output.json`), trial 3 (`./N067-asv6.23-t3/run/output.json`).
- ASv6.26: trial 1 (`./N067-asv6.26-t1/run/output.json`), trial 2 (`./N067-asv6.26-t2/run/output.json`), trial 3 (`./N067-asv6.26-t3/run/output.json`).

## Interpretation and next step

The revised instructions influence which levels of subject are returned. They add some independently named broader subjects while preserving the detailed source meanings checked here. They do not reliably fix the missing Coffee shops subject.

This does not establish why the omission occurs internally. The model demonstrably can produce broader subjects, so an inability to understand the concept is not supported. Nor does this comparison establish that the auxiliary context field causes the omission: both versions use it, and it was not independently varied.

I recommend keeping ASv6.23 frozen. A justified next candidate is one worked example, from a substantially unrelated domain, showing a broad subject independently of detailed subjects. That would test teaching the required distinction through an output example rather than relying on another abstract wording change. Any future comparison should still use ASv6.23 as the baseline. The example has not been written or run; it requires user review and approval.

This is a four-note reused diagnostic, not general validation. Both coverage and self-containment wording changed together. The selected broad topics are not a unique correct subject list. No masks, vectors, HDBSCAN groups or hierarchy changes were generated.

## Saved record

- Predeclared plan (`./plan.json`)
- Complete notes and all subjects under review IDs (`./review-input.json`)
- Judgments saved before revealing versions (`./review-judgments.json`)
- Version and trial mapping (`./review-key.json`)
- Machine-readable comparison (`./summary.json`)
- Execution verification (`./verification.json`)

All 24 calls succeeded on their first attempts and returned unique response IDs. Reported usage: 24,107 tokens, comprising 13,230 input and 10,877 output; output includes 1,436 reasoning tokens. These were subscription calls, not paid API calls. The lowest sampled available memory was 103.29 GiB; sampled memory and I/O pressure stayed at zero. No owned jobs remain active. Prior prompts, outputs and the frozen package remain unchanged.

**Selected data:** Posts, final answers, recorded assessments, measurements and parameters are selected for release as `prompt-studies/asv6.26-comparison-v1-85a6037dcd1c` in the [publication catalog](../../../docs/experiments/publications.csv). The compact files use a different layout from the original local artifacts cited above.
