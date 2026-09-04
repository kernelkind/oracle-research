Identify the exact text supporting the supplied subject in this social-media post. Treat the supplied subject as fixed. The fragments selected for the subject form its mask.

Use the complete post to interpret the subject and resolve references. Select fragments that jointly express the whole supplied subject as conveyed by the post, including when it is conveyed implicitly. Include the source wording needed to preserve its referents, relationships, and qualifications. Use multiple fragments when the supporting text is separated.

Keep the mask focused on the subject. Prefer fewer words only when they preserve the same meaning.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
