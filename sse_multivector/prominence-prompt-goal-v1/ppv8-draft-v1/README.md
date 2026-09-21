# PPv8 — markers only in the full note

Status: draft, not model-tested, frozen or adopted in production.

Only PPv7's input-format paragraph changes. The marked full note still uses
`⟦` and `⟧` to identify selected occurrences. The separate mask instead presents
one quoted fragment per line, without added mask markers. Both views must still
be rendered from the same saved selections, retaining fragment boundaries,
source order and repeated selections. Quoting must preserve embedded quotes,
newlines and other source characters when a renderer is implemented.

All remaining prompt bytes are unchanged. The
[PPv7 task and limitations](../ppv7-draft-v1/README.md) still apply; this format
description replaces the older requirement to mark both views. No renderer,
production configuration or inference is changed by this draft.

`PPv8.md.revision.json` records the exact edit and source/output hashes. PPv7
and frozen PPv2 remain unchanged. Next suggested step after review: the small
saved-note ranking test, checking both rendered views before inference.
