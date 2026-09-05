Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the subject and resolve references in the source text, including when the subject is conveyed implicitly. The mask must capture the supplied subject's whole meaning and match its scope, without including additional meanings from the post. Include the source words that identify who or what the subject refers to and express its relationships and qualifications; a context-dependent expression alone is insufficient when the post provides wording that identifies what it refers to.

The mask may contain one or more fragments, including individual words. The fragments need not form grammatical prose: include words because they carry the supplied subject's meaning, not merely to keep a source sentence or clause intact. Prefer fewer words only when they preserve the same meaning.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return only a JSON array of exact substrings copied from the post, in source order.

<examples>
<example>
<post>
At the river festival, volunteers painted the rescue boat bright yellow. It can carry six passengers.
</post>
<subject>
The rescue boat can carry six passengers.
</subject>
<response>
["rescue boat", "can carry six passengers."]
</response>
</example>

<example>
<post>
At the river festival, volunteers painted the rescue boat bright yellow. It can carry six passengers.
</post>
<subject>
Volunteers painted the rescue boat bright yellow at the river festival.
</subject>
<response>
["At the river festival, volunteers painted the rescue boat bright yellow."]
</response>
</example>

<example>
<post>
Our ceramics studio, which is run by volunteers, offers evening classes for beginners.
</post>
<subject>
The ceramics studio offers evening classes for beginners.
</subject>
<response>
["ceramics studio", "offers evening classes for beginners."]
</response>
</example>

<example>
<post>
Our ceramics studio, which is run by volunteers, offers evening classes for beginners.
</post>
<subject>
The ceramics studio is run by volunteers and offers evening classes for beginners.
</subject>
<response>
["ceramics studio, which is run by volunteers, offers evening classes for beginners."]
</response>
</example>

<example>
<post>
The theater announced the cast during a celebration. Two performers quit. Their departure delayed rehearsals.
</post>
<subject>
Two performers quitting delayed rehearsals.
</subject>
<response>
["Two performers quit.", "delayed rehearsals."]
</response>
</example>

<example>
<post>
The theater announced the cast during a celebration. Two performers quit. Their departure delayed rehearsals.
</post>
<subject>
Two performers quit.
</subject>
<response>
["Two performers quit."]
</response>
</example>
</examples>

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
