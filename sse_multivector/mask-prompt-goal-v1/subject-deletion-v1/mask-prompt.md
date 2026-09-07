Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the fixed subject. Select source wording that identifies who or what it refers to and conveys its whole meaning, including implicit meaning. Remove any word or fragment from the mask if the remaining mask still identifies who or what the subject refers to and conveys the whole supplied subject. Preserve the supplied subject's meaning, not every meaning in the original wording. Fragments may be individual words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
