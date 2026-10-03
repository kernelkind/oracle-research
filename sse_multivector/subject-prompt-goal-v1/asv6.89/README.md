# ASv6.89 complete-source collection demonstration

Status: tested with failures; not adopted.
[ASv6.89](ASv6.89.md) replaces only C1's explanation in
[ASv6.87](../asv6.87/ASv6.87.md). It keeps the six complete specific source
subjects, then demonstrates one complete collection before numbering:
the ingredient-group heading has the full mixing action as its only distinct
compatible source subheading. The group already labels the heading; either
individual ingredient lacks the other. The unchanged output places that full
action beneath all seven occurrences of the group, including both Dog food
branches. The other heading collections remain demonstrated by the output.

The hypothesis is that one concrete collection can help the model preserve
complete actions beneath every compatible group copy. ASv6.87's J001 trial 2
retained its complete actions elsewhere but left material-group occurrences
empty. Stating the collection procedure and enumerating subjects did not
reliably prevent that failure. This revision demonstrates the missing step;
it does not establish an internal model cause or guarantee improvement.

C1's post and 42-row JSON, the six other examples, all instructions and the
schema are byte-identical to ASv6.87. All 34 primary clause and five implication
mappings remain unchanged. R22 gains a concrete collection demonstration;
no production rule, output field or additional inference pass is introduced.
The explanation grows from 160 to 235 whitespace-separated words. Every
request carries those additional words, and one collection may not generalize
to other relationships or repair source construction and later attributes.
The semantic fixture is an agent judgment, not independent gold.

The minimal production-path check first validated ASv6.87's C1 through the
subjects adapter, then failed because its explanation contained no explicit
complete group collection. The same check now verifies the demonstrated
collection against the reviewed source relationships and every group copy
in the production-parsed output. Additional checks preserve the original
examples, source enumeration, scope, relationships, copies and exact POST
template. The frozen 24-attempt screen now finishes: 23 valid answers, fourteen
bounded accepts, nine rejects and one unknown S006 trial-3 error. All five
available minimized answers pass, but originals remain 6 accepts/6 rejects
and later-property cases 3 accepts/3 rejects. Source, independent copies and
actual scope failures persist. The [completed comparison](../isolation-v1/source-completion-phase-v1.md)
preserves the unavailable answer without retry and establishes no reliable fix.

The native `experiment.py revise` command applied the single exact edit in
[prompt-edits.json](prompt-edits.json). Its automatic
[revision receipt](ASv6.89.md.revision.json) pins the ASv6.87 base and records
the authored prompt. The reusable
[POST template](../../experiment_specs/asv6.89-hr01-post-template.txt) is the
exact prompt followed by `\n<post>\n{POST}\n</post>`.
