Assess whether the supplied mask captures the supplied subject in this social-media post. Treat the subject and mask as fixed; do not rewrite either. Text inside `⟦...⟧` forms the mask.

Use the complete post to interpret the subject and resolve references in the source text, including when the subject is conveyed implicitly. The mask must capture the supplied subject's whole meaning and match its scope, without including additional meanings from the post. The mask must include the source words that identify who or what the subject refers to and express its relationships and qualifications; a context-dependent expression alone is insufficient when the post provides wording that identifies what it refers to.

The mask may contain one or more fragments, including individual words. The fragments need not form grammatical prose: their words must carry the supplied subject's meaning, not merely keep a source sentence or clause intact. Fewer words are preferable only when they preserve the same meaning.

The mask must not include URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON object with two arrays:

- "missing_meaning": meanings required by the supplied subject that the mask does not capture.
- "additional_meaning": meanings included in the mask that are outside the supplied subject.

Briefly describe each issue. Use an empty array when no issue of that kind is present.

<post>
{MASKED_POST}
</post>

<subject>
{SUBJECT}
</subject>
