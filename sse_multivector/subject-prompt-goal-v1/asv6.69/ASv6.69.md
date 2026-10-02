Build a hierarchy of this social-media post's subjects, like a book's subject index. Begin by understanding the complete post before dividing it into subjects.

Use the complete post to resolve references to the most specific descriptions it supports. General knowledge may clarify language, identify referents, and recognize subjects, but every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by the post.

Interpret names, labels, and hashtags by what they refer to; their component words alone do not establish a literal description. For an unresolved named subject, retain its name.

URLs and opaque encoded identifiers—including, but not limited to, Nostr public keys (`npub1…`), event IDs (`nevent1…`), and cryptographic hashes—provide no subject evidence. The surrounding prose may still establish subjects involving URLs or identifiers.

If ambiguity remains after understanding the complete post, give each supported interpretation its own directly stated subject, without uncertainty qualifiers. Co-mention or statement order alone does not establish relationships. Do not add commentary about plausibility or what is unclear or unstated.

For numbers in subject text, preserve what they refer to; any count or measurement interpretation and units must be supported by the post. Include calculated results only if explicitly stated.

With the post's meaning understood, first enumerate all specific subjects it expresses before deriving broader headings. Include subjects conveyed literally, nonliterally, or rhetorically by individual parts, multiple parts together, or the post as a whole, even when no phrase names them. Identify individual subjects and particular instances as well as the combinations expressed by the post; a description of an event does not replace the subjects involved.

Return only one JSON object with a `subjects` array containing the completed hierarchy. Present it broad-to-specific using section-style numbering (`1`, `1.1`, `1.1.1`), listing each heading before its subheadings. Return an object for each hierarchy entry with `number`, then `context`, then `subject`.

In `context`, identify the subject and the source context establishing its meaning. This may describe a particular instance supporting a general heading.

In `subject`, name the subject at that entry's level of generality. Keep details distinguishing a particular instance in its subheading, rather than importing them from `context` into the general heading. Each heading must be understandable without the post, its `context`, or other entries; it need not retell what the post says about the subject. Preserve the heading's meaning, negation, and relationships. For comparison entries, name both sides when provided. Make the wording concise.

<example>
<post>
Repair:
One tube.
Cutting it.
Separately, edible olive oil for cooking and inedible olive oil for a lamp.
</post>

<explanation>
"One tube" and "Cutting one tube" do not themselves establish repair; their repair-qualified subjects appear under every valid parent copy. Likewise, unqualified "Olive oil" includes both stated oils and cannot inherit edible or inedible quality. An edible oil is not necessarily for cooking, and an inedible oil is not necessarily for a lamp: those purposes remain in their qualified subjects. The stated combination of both oil uses remains a subject beneath every copy of each constituent; it does not replace either constituent.
</explanation>

<output>
{"subjects": [
  {"number": "1", "context": "The repair list names a tube.", "subject": "Tubes"},
  {"number": "1.1", "context": "The list gives a count of one tube; its heading supplies this instance's repair purpose.", "subject": "One tube"},
  {"number": "1.1.1", "context": "The list places one tube under the repair heading.", "subject": "One tube for repair"},
  {"number": "1.1.1.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "1.1.2", "context": "In Cutting it, it refers to the one tube.", "subject": "Cutting one tube"},
  {"number": "1.1.2.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "2", "context": "The heading establishes the repair purpose of the tube and cutting.", "subject": "Repair"},
  {"number": "2.1", "context": "The list places one tube under the repair heading.", "subject": "One tube for repair"},
  {"number": "2.1.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "2.2", "context": "The list heading gives the cutting its repair purpose.", "subject": "Cutting for repair"},
  {"number": "2.2.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "3", "context": "The list explicitly names cutting.", "subject": "Cutting"},
  {"number": "3.1", "context": "In Cutting it, it refers to the one tube.", "subject": "Cutting one tube"},
  {"number": "3.1.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "3.2", "context": "The list heading gives the cutting its repair purpose.", "subject": "Cutting for repair"},
  {"number": "3.2.1", "context": "It refers to the one tube; the list heading supplies the cutting's repair purpose.", "subject": "Cutting one tube for repair"},
  {"number": "4", "context": "The separate statement names edible and inedible olive oil.", "subject": "Oils"},
  {"number": "4.1", "context": "The separate statement calls both oils olive oil.", "subject": "Olive oil"},
  {"number": "4.1.1", "context": "The separate statement names edible olive oil.", "subject": "Edible olive oil"},
  {"number": "4.1.1.1", "context": "The separate statement gives the edible olive oil a cooking purpose.", "subject": "Edible olive oil for cooking"},
  {"number": "4.1.1.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"},
  {"number": "4.1.2", "context": "The separate statement names inedible olive oil.", "subject": "Inedible olive oil"},
  {"number": "4.1.2.1", "context": "The separate statement gives the inedible olive oil a lamp purpose.", "subject": "Inedible olive oil for a lamp"},
  {"number": "4.1.2.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"},
  {"number": "4.2", "context": "The separate statement explicitly calls one olive oil edible.", "subject": "Edible oils"},
  {"number": "4.2.1", "context": "The separate statement names edible olive oil.", "subject": "Edible olive oil"},
  {"number": "4.2.1.1", "context": "The separate statement gives the edible olive oil a cooking purpose.", "subject": "Edible olive oil for cooking"},
  {"number": "4.2.1.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"},
  {"number": "4.3", "context": "The separate statement explicitly calls one olive oil inedible.", "subject": "Inedible oils"},
  {"number": "4.3.1", "context": "The separate statement names inedible olive oil.", "subject": "Inedible olive oil"},
  {"number": "4.3.1.1", "context": "The separate statement gives the inedible olive oil a lamp purpose.", "subject": "Inedible olive oil for a lamp"},
  {"number": "4.3.1.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"},
  {"number": "5", "context": "Cooking is the explicit purpose of the edible olive oil.", "subject": "Cooking"},
  {"number": "5.1", "context": "The separate statement gives the edible olive oil a cooking purpose.", "subject": "Edible olive oil for cooking"},
  {"number": "5.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"},
  {"number": "6", "context": "A lamp is the explicit purpose of the inedible olive oil.", "subject": "Lamps"},
  {"number": "6.1", "context": "The separate statement gives the inedible olive oil a lamp purpose.", "subject": "Inedible olive oil for a lamp"},
  {"number": "6.1.1", "context": "The separate statement names both quality-and-purpose-qualified oils together.", "subject": "Edible olive oil for cooking and inedible olive oil for a lamp"}
]}
</output>
</example>

<example>
<post>
On my first use, the new app #RavenWorks was a lifesaver, figuratively speaking—how could I not appreciate it on that first use? Also: AmberLoop.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "The post explicitly names RavenWorks as an app.", "subject": "Apps"},
  {"number": "1.1", "context": "The hashtag names the app RavenWorks.", "subject": "RavenWorks app"},
  {"number": "1.1.1", "context": "The writer explicitly calls the app new.", "subject": "New RavenWorks app"},
  {"number": "1.1.1.1", "context": "The writer says this was their first use of the new app.", "subject": "First use of the new RavenWorks app"},
  {"number": "1.1.1.1.1", "context": "The writer places the figurative lifesaver help on their first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.1.2", "context": "The rhetorical question explicitly places appreciation on that first use of the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "1.1.1.2", "context": "The new RavenWorks app is the stated helpful referent.", "subject": "Help from the new RavenWorks app"},
  {"number": "1.1.1.2.1", "context": "The writer places the figurative lifesaver help on their first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.3", "context": "The rhetorical it refers to the stated new RavenWorks app.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "1.1.1.3.1", "context": "The rhetorical question explicitly places appreciation on that first use of the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "2", "context": "The figurative lifesaver description expresses help.", "subject": "Help"},
  {"number": "2.1", "context": "The new RavenWorks app is the stated helpful referent.", "subject": "Help from the new RavenWorks app"},
  {"number": "2.1.1", "context": "The writer places the figurative lifesaver help on their first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "3", "context": "The rhetorical question expresses appreciation.", "subject": "Appreciation"},
  {"number": "3.1", "context": "The rhetorical it refers to the stated new RavenWorks app.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "3.1.1", "context": "The rhetorical question explicitly places appreciation on that first use of the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "4", "context": "The writer explicitly identifies this as their first use.", "subject": "First use"},
  {"number": "4.1", "context": "The writer says this was their first use of the new app.", "subject": "First use of the new RavenWorks app"},
  {"number": "4.1.1", "context": "The writer places the figurative lifesaver help on their first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "4.1.2", "context": "The rhetorical question explicitly places appreciation on that first use of the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "5", "context": "The post independently names AmberLoop without establishing its type.", "subject": "AmberLoop"}
]}
</output>
</example>

<example>
<post>
https://birds.example/repair?count=12
8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{"subjects": []}
</output>
</example>

<example>
<post>
Profile URL: https://birds.example/repair?count=12
Event ID: 8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{"subjects": [
  {"number": "1", "context": "The prose explicitly labels a profile URL.", "subject": "URLs"},
  {"number": "1.1", "context": "The prose describes the supplied URL as a profile URL.", "subject": "Profile URLs"},
  {"number": "2", "context": "The URL is explicitly described as a profile URL.", "subject": "Profiles"},
  {"number": "2.1", "context": "The prose describes the supplied URL as a profile URL.", "subject": "Profile URLs"},
  {"number": "3", "context": "The prose explicitly labels an event ID.", "subject": "Identifiers"},
  {"number": "3.1", "context": "The prose describes the supplied identifier as an event ID.", "subject": "Event identifiers"},
  {"number": "4", "context": "The identifier is explicitly described as an event ID.", "subject": "Events"},
  {"number": "4.1", "context": "The prose describes the supplied identifier as an event ID.", "subject": "Event identifiers"}
]}
</output>
</example>

<example>
<post>
I saw her duck. I bought a notebook.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "The writer reports seeing a person's duck.", "subject": "Ducks"},
  {"number": "1.1", "context": "The duck seen by the writer belongs to a person.", "subject": "A person's duck"},
  {"number": "1.1.1", "context": "The writer reports seeing a duck belonging to a person.", "subject": "Observation of a person's duck"},
  {"number": "2", "context": "The writer reports seeing a person duck.", "subject": "Ducking"},
  {"number": "2.1", "context": "The person described by 'her' performs the ducking movement.", "subject": "A person ducking"},
  {"number": "2.1.1", "context": "The writer reports seeing a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "3", "context": "The pronoun 'her' refers to a person.", "subject": "People"},
  {"number": "3.1", "context": "The duck seen by the writer belongs to a person.", "subject": "A person's duck"},
  {"number": "3.1.1", "context": "The writer reports seeing a duck belonging to a person.", "subject": "Observation of a person's duck"},
  {"number": "3.2", "context": "The person described by 'her' performs the ducking movement.", "subject": "A person ducking"},
  {"number": "3.2.1", "context": "The writer reports seeing a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "4", "context": "The writer reports seeing.", "subject": "Observation"},
  {"number": "4.1", "context": "The writer reports seeing a duck belonging to a person.", "subject": "Observation of a person's duck"},
  {"number": "4.2", "context": "The writer reports seeing a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "5", "context": "The writer says they bought a notebook.", "subject": "Notebooks"},
  {"number": "5.1", "context": "The second sentence reports the writer's purchase of a notebook.", "subject": "Purchase of a notebook"},
  {"number": "6", "context": "The writer reports buying a notebook.", "subject": "Purchases"},
  {"number": "6.1", "context": "The second sentence reports the writer's purchase of a notebook.", "subject": "Purchase of a notebook"}
]}
</output>
</example>

<example>
<post>
2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "The post describes two cables.", "subject": "Cables"},
  {"number": "1.1", "context": "The post states the lengths of both cables.", "subject": "Cable lengths"},
  {"number": "1.1.1", "context": "Cable A is explicitly 2 m long.", "subject": "2 m cables"},
  {"number": "1.1.1.1", "context": "The post names cable A and gives its length as 2 m.", "subject": "2 m cable A"},
  {"number": "1.1.1.1.1", "context": "The two cables are A, 2 m long, and B, 3 m long.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.1.1.1.1", "context": "The post explicitly says A is not longer than B, having given both cable lengths.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.2", "context": "Cable B is explicitly 3 m long.", "subject": "3 m cables"},
  {"number": "1.1.2.1", "context": "The post names cable B and gives its length as 3 m.", "subject": "3 m cable B"},
  {"number": "1.1.2.1.1", "context": "The two cables are A, 2 m long, and B, 3 m long.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.2.1.1.1", "context": "The post explicitly says A is not longer than B, having given both cable lengths.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.3", "context": "The second sentence compares cable A's length with cable B's length.", "subject": "Cable length comparisons"},
  {"number": "1.1.3.1", "context": "The post explicitly says A is not longer than B, having given both cable lengths.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.2", "context": "The opening count is two cables.", "subject": "Pairs of cables"},
  {"number": "1.2.1", "context": "The two cables are A, 2 m long, and B, 3 m long.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.2.1.1", "context": "The post explicitly says A is not longer than B, having given both cable lengths.", "subject": "2 m cable A not longer than 3 m cable B"}
]}
</output>
</example>

<example>
<post>
2 + 3 = 5.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "The post states the arithmetic equality 2 + 3 = 5.", "subject": "Arithmetic"},
  {"number": "1.1", "context": "The plus sign specifies addition.", "subject": "Addition"},
  {"number": "1.1.1", "context": "The numbers 2 and 3 are the numbers being added.", "subject": "Addends"},
  {"number": "1.1.1.1", "context": "In 2 + 3 = 5, 2 is an addend.", "subject": "2 as an addend"},
  {"number": "1.1.1.1.1", "context": "The full stated calculation is 2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.1.2", "context": "In 2 + 3 = 5, 3 is an addend.", "subject": "3 as an addend"},
  {"number": "1.1.1.2.1", "context": "The full stated calculation is 2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.2", "context": "The equation explicitly states the result of addition.", "subject": "Addition results"},
  {"number": "1.1.2.1", "context": "The equation explicitly gives 5 as the result.", "subject": "5 as an addition result"},
  {"number": "1.1.2.1.1", "context": "The full stated calculation is 2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"}
]}
</output>
</example>

Every parent-child pair must be valid from its two `subject` strings alone. Read the child without the post or context: its wording must preserve the parent's type, purpose, modifier, action, negation and relationship. A parent's restriction cannot come from how this post happens to use the child. If another post in any domain could discuss that child without the parent's restriction, the pair is invalid. For a generic substance, object or action heading, consider a different use, recipient or situation, beyond the usual use here. Keep that generic heading broad in a separate branch; place the supported role-qualified heading under the restricted parent. Derive broader headings by generalizing without adding restrictions or assuming typical uses. General knowledge may establish actual type membership, but cannot change a generic heading into this post's instance. The post, `context` and other entries cannot repair a missing restriction.

Use the valid relationships to build the hierarchy upward, combining shared headings. Finish these relationships before assigning numbers. Repeating a heading repeats its enumerated descendants too: every copy must retain the same complete source-subject headings beneath it. Then check each enumerated subject against every returned heading: wherever its wording passes the same parent check, retain it beneath that heading, in every copy of that heading. A placement elsewhere does not satisfy a missing branch. Give every heading and subheading its own entry.
