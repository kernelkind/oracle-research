Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the fixed subject. Select every occurrence expressing it, explicitly or implicitly, including repeated expressions of the same meaning. The mask must identify who or what the subject refers to and convey its whole meaning; this may require multiple fragments.

Within each occurrence, keep only the wording needed to express the supplied subject. Preserve the supplied subject's meaning, not every meaning in the original wording. Fragments may be individual words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
