Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to understand what each passage means. Select every occurrence expressing the supplied subject, explicitly or implicitly, including repeated expressions of the same meaning. Combine fragments from different parts of the post when needed to convey the whole meaning of the supplied subject.

Within each occurrence, keep only the wording needed to express the supplied subject at its stated level of detail. A detail belongs in the mask when the subject requires it, not merely because it is true of the particular occurrence. Fragments may be individual words or parts of words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

The indexed post labels each whitespace-separated word with its position, starting at 1. Punctuation remains attached to its word. Return only a JSON array of objects, one per mask fragment in source order. Each object has integer "start" and "end" fields naming the first and last word positions, both inclusive. These select the whole words and the original text between them.

To select only part of a boundary word, add "start_marked" for the first word or "end_marked" for the last word: copy that word exactly, inserting ⟦ and ⟧ around its selected part. For a fragment within one word, use "start_marked" only. For a fragment spanning multiple words, the first word's selected part must extend to its end, and the last word's selected part must begin at its start. Omit marking fields for whole words.

<post>
{POST}
</post>

<indexed_post>
{INDEXED_POST}
</indexed_post>

<subject>
{SUBJECT}
</subject>
