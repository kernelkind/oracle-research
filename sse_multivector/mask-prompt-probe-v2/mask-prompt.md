Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the subject and resolve references, including when the subject is conveyed implicitly. The mask must capture the supplied subject's whole meaning and match its scope, without including additional meanings from the post. Include the source words that identify who or what the subject refers to and express its relationships and qualifications.

The mask may contain one or more fragments. Prefer fewer words only when they preserve the same meaning.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
