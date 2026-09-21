Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed.

A fragment is one continuous range of text from the post. It may contain part of a word, one word, or multiple words. A mask is the complete set of fragments which together make up the exact semantic meaning for the supplied subject.

Use the complete post to interpret the fixed subject and the source wording, including idioms and implied meanings. Select expressions of the supplied meaning, not descriptions of particular examples that merely demonstrate it. Match the subject's level of generality: keep the details it specifies and exclude details that make the mask more specific. Select every occurrence expressing it at that level, including repeated expressions of the same meaning. The mask must convey the supplied subject's whole meaning; this may require multiple fragments.

Within each occurrence, remove any word or fragment if the remaining wording still conveys the supplied subject's whole meaning. Keep wording that expresses the subject even when another fragment already conveys the same meaning. Preserve the supplied subject's meaning, not every meaning in the original wording. Fragments may be individual words and need not form grammatical prose.

If no combination of exact fragments can express the supplied subject at its level of generality, return {"mask": []} rather than a mask for a broader or narrower subject.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

The indexed post labels each whitespace-separated word with its position, starting at 1. Punctuation remains attached to its word. Return only a JSON object with a "mask" array of selections in source order, without overlaps.

Use [start, end] to select whole words from the first position through the last, both inclusive. Both positions are integers. Use [n, n] for one whole word.

To select part of a word, use {"word": n, "text": "selected text"}, where n is the word's position. Copy only the selected text exactly from that word; do not insert markers or copy the unselected characters.

For a fragment containing whole words and parts of words, list the whole-word range and each partial-word selection separately. A partially selected word must not also be included in a whole-word range.

<examples>
<example_post>
My daughter's bicycle was damaged. On Saturday I repaired it using secondhand parts. Yesterday I fixed two more bikes for our neighbours, then watched a film.
</example_post>

<example_indexed_post>
[1]My [2]daughter's [3]bicycle [4]was [5]damaged. [6]On [7]Saturday [8]I [9]repaired [10]it [11]using [12]secondhand [13]parts. [14]Yesterday [15]I [16]fixed [17]two [18]more [19]bikes [20]for [21]our [22]neighbours, [23]then [24]watched [25]a [26]film.
</example_indexed_post>

<example>
<subject>Bicycle repair</subject>
<response>{"mask":[[3,3],[9,9],[16,16],[19,19]]}</response>
</example>

<example>
<subject>The author repairing their daughter's bicycle on Saturday using secondhand parts</subject>
<response>{"mask":[[1,3],[6,9],[11,12],{"word":13,"text":"parts"}]}</response>
</example>

<example>
<example_post>
I donated furniture to the shelter: a table and two chairs.
</example_post>

<example_indexed_post>
[1]I [2]donated [3]furniture [4]to [5]the [6]shelter: [7]a [8]table [9]and [10]two [11]chairs.
</example_indexed_post>

<subject>Furniture</subject>
<response>{"mask":[[3,3]]}</response>
</example>

<example>
<example_post>
I donated a table and two chairs to the shelter.
</example_post>

<example_indexed_post>
[1]I [2]donated [3]a [4]table [5]and [6]two [7]chairs [8]to [9]the [10]shelter.
</example_indexed_post>

<subject>Furniture</subject>
<response>{"mask":[]}</response>
</example>

<example>
<example_post>
The pilot flew a small aircraft while a mechanic repaired a radio.
</example_post>

<example_indexed_post>
[1]The [2]pilot [3]flew [4]a [5]small [6]aircraft [7]while [8]a [9]mechanic [10]repaired [11]a [12]radio.
</example_indexed_post>

<subject>Flying</subject>
<response>{"mask":[[3,3]]}</response>
</example>

<example>
<example_post>
The pilot flew a small aircraft while a mechanic repaired a radio.
</example_post>

<example_indexed_post>
[1]The [2]pilot [3]flew [4]a [5]small [6]aircraft [7]while [8]a [9]mechanic [10]repaired [11]a [12]radio.
</example_indexed_post>

<subject>Pilots flying aircraft</subject>
<response>{"mask":[[2,3],[6,6]]}</response>
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
