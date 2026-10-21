# ASv6.23: small OpenRouter diagnostic

Muse Spark is the most promising alternative in this sample. It is not yet an established Astra replacement. All three models sometimes failed to make each subject understandable by itself; DeepSeek and GLM also made clearer content errors.

## View the results

From `oracle-mvp`, run:

```bash
./sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/run-review.sh
```

Left/right changes the note; 1–4 switches models. Tab selects the note, output or separate assistant-comment pane; up/down scrolls. Press `i` to switch between the original note and the prepared model input where they differ. Press `q` to exit. The viewer is read-only and makes no model calls.

## What ran

Twelve notes with existing ASv6.23 Astra-low outputs: four short, four medium, four long. Selection covered headlines, an opinion, a numeric comparison, gardening, a product launch, a reading app, court reporting and sports. Notes were selected for variety before reading the alternative models' outputs. The first archived Astra trial was used consistently—not whichever trial looked best.

Each alternative received the exact archived user prompt and schema, with low reasoning requested. The saved request bodies confirm one user message, no tools/search, and one HTTP attempt per note/model. No new Astra or mask calls were made. The earlier unexecuted v1 selection was superseded.

Astra's historical calls used a different Codex harness, including the extra instruction “Follow the user's instructions.” Its outputs are useful reference material, not ground truth or a controlled fresh baseline. This diagnostic cannot isolate the effects of model, provider, reasoning implementation or harness.

| Model | Responses | Actual charge | Median request time | Rough subject cost per 1,000 notes |
|---|---:|---:|---:|---:|
| Muse Spark 1.3 Contributor | 12/12 | $0.0068003 | 28.3 seconds | $0.57 |
| DeepSeek V4.1 Flash | 12/12 | $0.003497976 | 22.3 seconds | $0.29 |
| GLM 5.3 Flash | 10/12 | $0.001619675 | 25.3 seconds | $0.16 |

Total: **$0.011917951**, about 1.2 cents. GLM's H06 and H21 requests received provider HTTP 429 errors before generation; neither was retried. Request times and per-1,000 estimates use successful calls. GLM therefore has a different denominator. These are small-sample extrapolations at the observed routes/prices, not production quotes or total subject-plus-mask costs.

DeepSeek reported 4,608 cached input tokens; Muse and GLM reported none. Completion counts include reasoning: Muse reported 26,125 reasoning tokens, GLM 482, DeepSeek zero. The same requested “low” setting does not establish equal reasoning across models; zero reported reasoning does not prove that no internal reasoning occurred.

## Concrete findings

**H06 — URL-derived additions from DeepSeek.** The visible headline says “Google Pixel Satellite Texting Expands to a New Market.” Its URL contains the publication domain and `/2025/11/`. DeepSeek generated “Google Pixel satellite texting expansion occurring in November 2025” and “Android Headlines reporting on Google Pixel satellite texting expanding to a new market.” Both use information found only in the URL, contrary to the prompt. Muse and saved Astra did not add these claims. GLM had no output.

**H15 — preserving what the prices mean.** The complete note is:

> Best Value:
>
> LightningPay:
> 64,638 sats = $100
>
> Other NZ options:
> 63,655 sats - Easy Crypto
> 54,394 sats - Swyftx
> 45,224 sats - Independent Reserve

Muse and saved Astra preserved the $100 basis in the individual offers. DeepSeek's “Easy Crypto is an other New Zealand option: 63,655 sats” omits what the amount measures. GLM's “63,655 sats are required for $100 through Easy Crypto” likely reverses the intended exchange direction: the highest number is advertised as best value, suggesting sats received for $100, not sats required to obtain $100. That last judgment is an interpretation of the complete comparison, not an explicit direction stated in the equation.

**H48 — context omissions affect all three alternatives.** The note announces Mempool Intelligence Broker, offering Bitcoin mempool analysis and priced services. Muse and DeepSeek both generated “Block data ... 10 sats” without identifying Bitcoin or the service in that subject. GLM repeatedly used “the service” without naming it. Saved Astra included Mempool Intelligence Broker and Bitcoin in those subjects. This matters because the final subject must work without its separate context field or neighboring subjects.

DeepSeek and GLM also made the raw onion address into a subject; Muse did not. The address was copied, not hallucinated, but it is a pointer rather than the substantive content this prompt is meant to extract.

**H49 — GLM changes who built the app.** The model input says “So  made me a library app for my book!” The original Nostr identifier had already been removed by the historical input preparation; the same resulting text was used for all four models. GLM returned “The author made a library app for their book.” The input says someone made it for the author, not that the author built it. Muse and saved Astra correctly used passive wording. DeepSeek also produced context-dependent subjects such as “A fully immersive experience for the reader,” which leaves the actual reading experience unidentified.

**H54 — attribution and context in court reporting.** The note says “His argument is he invested in a nonprofit that was converted into a $350 billion for-profit without his consent.” DeepSeek and GLM produced standalone subjects presenting that disputed account as fact, without Musk's attribution. Muse preserved “Elon Musk argues...” but left the nonprofit unnamed; saved Astra identified OpenAI. DeepSeek also generated “Two claims remain from the original 26 claims” and “The trial continues this week” without identifying the case. This review concerns fidelity to the post, not whether its reporting is factually true.

**H59 — standalone sports subjects.** DeepSeek and GLM generated subjects about “the first practice session” or “the field” without identifying the 2026 Miami Formula 1 Grand Prix. Muse and saved Astra generally retained that context. DeepSeek added “Ferrari looking fast or competitive” to a passage ending “Ferrari looked ...”; because the post also says Leclerc set the fastest time, that is a plausible implication, not an unequivocal hallucination.

**Other notes.** No clear substantive error was identified in the alternatives' available H27, H45, H02 or H11 final subjects. Different numbers of overlapping subjects are not failures. H21 DeepSeek added “An image attached to the social-media post,” drawing a subject from attachment metadata; Muse preserved the gardening content. H25 DeepSeek's “The people addressed by the post are fools” loses the connection to belief in a Lord of the Rings extended-extended edition; Muse, GLM and saved Astra retained it. Quoting rhetorical language, including broad subjects, or producing fewer duplicates than Astra was not penalized.

## What this justifies

Keep Muse as the leading candidate for the next controlled comparison once the subject prompt is settled. Its price is encouraging and its outputs were cleaner here, but its context omissions prevent claiming Astra-equivalent quality. DeepSeek and GLM remain inexpensive alternatives with demonstrated weaknesses—not models conclusively ruled out by twelve notes.

Do not tune the old prompt around this diagnostic or infer a corpus-wide accuracy percentage. No mask quality was tested. Further runs require approval.

## Saved evidence

- `selection.json`: full original notes, exact model inputs, prompts, schemas, archived Astra outputs and provenance hashes.
- `muse/results.jsonl` and `deepseek/results.jsonl`: unedited outputs, complete request bodies, usage and timing.
- `glm/results.jsonl`: initial H06 failure; `glm-remaining/H*/results.jsonl`: the other eleven once-only attempts.
- `summary.json`: verified request counts and per-model statistics.
- `billing.json`: individual OpenRouter generation charges and cumulative-key reconciliation. Generation records, not catalog estimates, determine actual spend.

## Publication files

Selected saved answers, failed attempts, exact inputs, settings and reviews cover the initial and retry records together. Reused Astra answers remain references to their existing publication.

`historical-studies/frontier-asv6.23-diagnostic-v2` appears in the
[catalog](../../../docs/experiments/publications.csv) and [dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest).
These files are prepared locally for Hugging Face Datasets; downloads are not
available yet. Recorded pre-ASv6.100 derivatives remain deprecated historical evidence.
