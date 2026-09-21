Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed.

A fragment is one continuous range of text from the post. It may contain part of a word, one word, or multiple words. A mask is the complete set of fragments which together make up the exact semantic meaning for the supplied subject.

Use the complete post to interpret the fixed subject. Select every occurrence expressing it, explicitly or implicitly, including repeated expressions of the same meaning. The mask must identify who or what the subject refers to and convey its whole meaning; this may require multiple fragments.

Within each occurrence, remove wording that contributes only meanings outside the supplied subject. Keep wording that expresses the subject even when another fragment already conveys the same meaning. Fragments may be individual words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

The indexed post labels each whitespace-separated word with its position, starting at 1. Punctuation remains attached to its word. Return only a JSON array of objects, one per mask fragment in source order. Each object has integer "start" and "end" fields naming the first and last word positions, both inclusive. These select the whole words and the original text between them.

To select only part of a boundary word, add "start_marked" for the first word or "end_marked" for the last word: copy that word exactly, inserting ⟦ and ⟧ around its selected part. For a fragment within one word, use "start_marked" only. For a fragment spanning multiple words, the first word's selected part must extend to its end, and the last word's selected part must begin at its start. Omit marking fields for whole words.

<examples>
<example_post>
My daughter's bicycle was damaged. On Saturday I repaired it using secondhand parts. Yesterday I fixed two more bikes for our neighbours, then watched a film.
</example_post>

<example_indexed_post>
[1]My [2]daughter's [3]bicycle [4]was [5]damaged. [6]On [7]Saturday [8]I [9]repaired [10]it [11]using [12]secondhand [13]parts. [14]Yesterday [15]I [16]fixed [17]two [18]more [19]bikes [20]for [21]our [22]neighbours, [23]then [24]watched [25]a [26]film.
</example_indexed_post>

<example>
<subject>Bicycle repair</subject>
<response>[{"start":3,"end":3},{"start":9,"end":9},{"start":16,"end":16},{"start":19,"end":19}]</response>
</example>

<example>
<subject>The author repairing their daughter's bicycle on Saturday using secondhand parts</subject>
<response>[{"start":1,"end":3},{"start":6,"end":9},{"start":11,"end":13,"end_marked":"⟦parts⟧."}]</response>
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
