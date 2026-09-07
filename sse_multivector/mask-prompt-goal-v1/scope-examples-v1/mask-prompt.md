Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the subject and resolve references in the source text, including when the subject is conveyed implicitly. The mask must capture the supplied subject's whole meaning and match its scope, without including additional meanings from the post. Include the source words that identify who or what the subject refers to and express its relationships and qualifications; a context-dependent expression alone is insufficient when the post provides wording that identifies what it refers to.

The mask may contain one or more fragments, including individual words. The fragments need not form grammatical prose: include words because they carry the supplied subject's meaning, not merely to keep a source sentence or clause intact. Prefer fewer words only when they preserve the same meaning.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Examples:

Post: The overnight train was waiting at platform four. The impatient conductor waved the sleepy passengers aboard.
Subject: The conductor signaled passengers to board the overnight train.
Mask: ["The overnight train", "conductor waved the", "passengers aboard."]

Post: The overnight train was waiting at platform four. The impatient conductor waved the sleepy passengers aboard.
Subject: The conductor was impatient.
Mask: ["impatient conductor"]

Return only a JSON array of exact substrings copied from the post, in source order.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
