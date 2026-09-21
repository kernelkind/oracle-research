Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed.

A fragment is one continuous range of text from the post. It may contain part of a word, one word, or multiple words. A mask is the complete set of fragments selected for the supplied subject.

Use the complete post to interpret the fixed subject. Select every occurrence expressing it, explicitly or implicitly, including repeated expressions of the same meaning. The mask must identify who or what the subject refers to and convey its whole meaning; this may require multiple fragments.

Within each occurrence, remove any word or fragment if the remaining wording still identifies who or what the supplied subject refers to and conveys its whole meaning. Preserve the supplied subject's meaning, not every meaning in the original wording. Fragments may be individual words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

The indexed post labels each whitespace-separated word with its position, starting at 1. Punctuation remains attached to its word. Return only a JSON array of objects, one per mask fragment in source order. Each object has integer "start" and "end" fields naming the first and last word positions, both inclusive. These select the whole words and the original text between them.

To select only part of a boundary word, add "start_marked" for the first word or "end_marked" for the last word: copy that word exactly, inserting ⟦ and ⟧ around its selected part. For a fragment within one word, use "start_marked" only. For a fragment spanning multiple words, the first word's selected part must extend to its end, and the last word's selected part must begin at its start. Omit marking fields for whole words.

<examples>
Each example is a separate request using this same post and indexed post:

<example_post>
My train arrived twenty minutes behind schedule. The next train was late too. I also finished a detective novel today.
</example_post>

<example_indexed_post>
[1]My [2]train [3]arrived [4]twenty [5]minutes [6]behind [7]schedule. [8]The [9]next [10]train [11]was [12]late [13]too. [14]I [15]also [16]finished [17]a [18]detective [19]novel [20]today.
</example_indexed_post>

<example>
<subject>Trains</subject>
<response>[{"start":2,"end":2},{"start":10,"end":10}]</response>
</example>

<example>
<subject>Transport</subject>
<response>[{"start":2,"end":2},{"start":10,"end":10}]</response>
</example>

<example>
<subject>Train delays</subject>
<response>[{"start":2,"end":2},{"start":6,"end":7,"end_marked":"⟦schedule⟧."},{"start":10,"end":10},{"start":12,"end":12}]</response>
</example>

<example>
<subject>The author's train arriving twenty minutes late</subject>
<response>[{"start":1,"end":7,"end_marked":"⟦schedule⟧."}]</response>
</example>
</examples>

<post>
{POST}
</post>

<indexed_post>
{INDEXED_POST}
</indexed_post>

<subject>
{SUBJECT}
</subject>
