Select exact text from this social-media post for the supplied subject. Treat the supplied subject as fixed. The selected fragments form its mask.

Use the complete post to interpret the fixed subject. Select every occurrence expressing it, explicitly or implicitly, including repeated expressions of the same meaning. The mask must identify who or what the subject refers to and convey its whole meaning; this may require multiple fragments.

Within each occurrence, remove any word or fragment if the remaining wording still identifies who or what the supplied subject refers to and conveys its whole meaning. Preserve the supplied subject's meaning, not every meaning in the original wording. Fragments may be individual words and need not form grammatical prose.

Do not select URLs, exact user handles, or long encoded Nostr identifiers beginning with prefixes such as `npub1…`, `nprofile1…`, `note1…`, `nevent1…`, `naddr1…`, or `nsec1…`. These identifiers may be prefixed by `nostr:`, the Nostr URI scheme, as in `nostr:npub1…`.

Return the complete original post, inserting ⟦ immediately before each mask fragment and ⟧ immediately after it. Preserve every original character, including whitespace, exactly. Add nothing else.

<post>
{POST}
</post>

<subject>
{SUBJECT}
</subject>
