Identify possible broader parents of hierarchy node A from the supplied candidates.

A contains subject/context entries from social-media posts. Each candidate identifies an existing hierarchy node and the subject wordings it represents.

Interpret subjects at their stated level of generality. Use A's context to resolve meaning and references, without narrowing its subject to the particular examples described.

Select candidates within whose scope A's whole subject is a more specific topic. A parent may be an ancestor, not necessarily an immediate parent. Equivalent, narrower or merely related subjects do not qualify.

Return only {"candidates":[{"id":"...","reason":"..."}]}, using supplied candidate IDs and one short reason per selection. If none qualify, return {"candidates":[]}.

<input>
{INPUT_JSON}
</input>
