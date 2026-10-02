Build a hierarchy of this social-media post's subjects, like a book's subject index. Begin by understanding the complete post before dividing it into subjects.

Use the complete post to resolve references to the most specific descriptions it supports. General knowledge may clarify language, identify referents, and recognize subjects, but every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by the post.

Interpret names, labels, and hashtags by what they refer to; their component words alone do not establish a literal description. For an unresolved named subject, retain its name.

URLs and opaque encoded identifiers—including, but not limited to, Nostr public keys (`npub1…`), event IDs (`nevent1…`), and cryptographic hashes—provide no subject evidence. The surrounding prose may still establish subjects involving URLs or identifiers.

If ambiguity remains after understanding the complete post, give each supported interpretation its own directly stated subject, without uncertainty qualifiers. Co-mention or statement order alone does not establish relationships. Do not add commentary about plausibility or what is unclear or unstated.

For numbers in subject text, preserve what they refer to; any count or measurement interpretation and units must be supported by the post. Include calculated results only if explicitly stated.

With the post's meaning understood, first enumerate all specific subjects it expresses before deriving broader headings. Include subjects conveyed literally, nonliterally, or rhetorically by individual parts, multiple parts together, or the post as a whole, even when no phrase names them. Identify individual subjects and particular instances as well as the combinations expressed by the post; a description of an event does not replace the subjects involved.

For each enumerated subject, identify broader subjects by comparing their `subject` headings alone. Imagine another post that fits the child heading: if it could fail to fit the proposed parent heading, use a broader parent. Use these relationships to build the hierarchy upward, combining shared headings. Retain every enumerated subject as an entry, including it in each branch that passes this check. Give every heading and subheading its own entry.

Return only one JSON object with a `subjects` array containing the completed hierarchy. Present it broad-to-specific using section-style numbering (`1`, `1.1`, `1.1.1`), listing each heading before its subheadings. Return an object for each hierarchy entry with `number`, then `context`, then `subject`.

In `context`, identify the subject and the source context establishing its meaning. This may describe a particular instance supporting a general heading.

In `subject`, name the subject at that entry's level of generality. Keep details distinguishing a particular instance in its subheading, rather than importing them from `context` into the general heading. Each heading must be understandable without the post, its `context`, or other entries; it need not retell what the post says about the subject. Preserve the heading's meaning, negation, and relationships. For comparison entries, name both sides when provided. Make the wording concise.

<example>
<post>
Replacement boiler for Bracken. Bracken is a steam locomotive.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post names a replacement boiler.",
      "subject": "Boilers"
    },
    {
      "number": "1.1",
      "context": "The boiler is for Bracken, identified in the next sentence as a steam locomotive.",
      "subject": "Steam locomotive boilers"
    },
    {
      "number": "1.1.1",
      "context": "The replacement boiler is for Bracken, a steam locomotive.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "1.2",
      "context": "The post explicitly describes the boiler as a replacement boiler.",
      "subject": "Replacement boilers"
    },
    {
      "number": "1.2.1",
      "context": "The replacement boiler is for Bracken, a steam locomotive.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "2",
      "context": "The post identifies Bracken as a steam locomotive.",
      "subject": "Locomotives"
    },
    {
      "number": "2.1",
      "context": "Bracken is explicitly a steam locomotive.",
      "subject": "Steam locomotives"
    },
    {
      "number": "2.1.1",
      "context": "The boiler is for Bracken, identified in the next sentence as a steam locomotive.",
      "subject": "Steam locomotive boilers"
    },
    {
      "number": "2.1.1.1",
      "context": "The replacement boiler is for Bracken, a steam locomotive.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "2.1.2",
      "context": "The second sentence identifies the named Bracken as a steam locomotive.",
      "subject": "Bracken the steam locomotive"
    },
    {
      "number": "2.1.2.1",
      "context": "The replacement boiler is for Bracken, a steam locomotive.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "3",
      "context": "The boiler described as a replacement boiler is a replacement part.",
      "subject": "Replacement parts"
    },
    {
      "number": "3.1",
      "context": "The post explicitly describes the boiler as a replacement boiler.",
      "subject": "Replacement boilers"
    },
    {
      "number": "3.1.1",
      "context": "The replacement boiler is for Bracken, a steam locomotive.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    }
  ]
}
</output>
</example>

<example>
<post>
The app #RavenWorks is a lifesaver, figuratively speaking—how could I not appreciate it? Also: AmberLoop.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post explicitly calls RavenWorks an app.",
      "subject": "Apps"
    },
    {
      "number": "1.1",
      "context": "The hashtag #RavenWorks names the app described by the writer.",
      "subject": "RavenWorks app"
    },
    {
      "number": "1.1.1",
      "context": "The app called a 'lifesaver' is RavenWorks.",
      "subject": "Help from the RavenWorks app"
    },
    {
      "number": "1.1.2",
      "context": "In the rhetorical question, 'it' refers to the RavenWorks app.",
      "subject": "Appreciation for the RavenWorks app"
    },
    {
      "number": "1.2",
      "context": "The writer credits an app with being helpful by calling it a 'lifesaver'.",
      "subject": "Help from apps"
    },
    {
      "number": "1.2.1",
      "context": "The app called a 'lifesaver' is RavenWorks.",
      "subject": "Help from the RavenWorks app"
    },
    {
      "number": "1.3",
      "context": "The writer expresses appreciation for an app through the rhetorical question.",
      "subject": "Appreciation for apps"
    },
    {
      "number": "1.3.1",
      "context": "In the rhetorical question, 'it' refers to the RavenWorks app.",
      "subject": "Appreciation for the RavenWorks app"
    },
    {
      "number": "2",
      "context": "Calling the app a 'lifesaver' credits it with being helpful.",
      "subject": "Help"
    },
    {
      "number": "2.1",
      "context": "The writer credits an app with being helpful by calling it a 'lifesaver'.",
      "subject": "Help from apps"
    },
    {
      "number": "2.1.1",
      "context": "The app called a 'lifesaver' is RavenWorks.",
      "subject": "Help from the RavenWorks app"
    },
    {
      "number": "3",
      "context": "The writer's rhetorical question expresses appreciation.",
      "subject": "Appreciation"
    },
    {
      "number": "3.1",
      "context": "The writer expresses appreciation for an app through the rhetorical question.",
      "subject": "Appreciation for apps"
    },
    {
      "number": "3.1.1",
      "context": "In the rhetorical question, 'it' refers to the RavenWorks app.",
      "subject": "Appreciation for the RavenWorks app"
    },
    {
      "number": "4",
      "context": "The writer also mentions AmberLoop.",
      "subject": "AmberLoop"
    }
  ]
}
</output>
</example>

<example>
<post>
https://birds.example/repair?count=12
8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{
  "subjects": []
}
</output>
</example>

<example>
<post>
Profile URL: https://birds.example/repair?count=12
Event ID: 8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The prose explicitly labels a profile URL.",
      "subject": "URLs"
    },
    {
      "number": "1.1",
      "context": "The prose describes the supplied URL as a profile URL.",
      "subject": "Profile URLs"
    },
    {
      "number": "2",
      "context": "The URL is explicitly described as a profile URL.",
      "subject": "Profiles"
    },
    {
      "number": "2.1",
      "context": "The prose describes the supplied URL as a profile URL.",
      "subject": "Profile URLs"
    },
    {
      "number": "3",
      "context": "The prose explicitly labels an event ID.",
      "subject": "Identifiers"
    },
    {
      "number": "3.1",
      "context": "The prose describes the supplied identifier as an event ID.",
      "subject": "Event identifiers"
    },
    {
      "number": "4",
      "context": "The identifier is explicitly described as an event ID.",
      "subject": "Events"
    },
    {
      "number": "4.1",
      "context": "The prose describes the supplied identifier as an event ID.",
      "subject": "Event identifiers"
    }
  ]
}
</output>
</example>

<example>
<post>
I saw her duck. I bought a notebook.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The writer reports seeing a person's duck.",
      "subject": "Ducks"
    },
    {
      "number": "1.1",
      "context": "The duck seen by the writer belongs to a person.",
      "subject": "A person's duck"
    },
    {
      "number": "1.1.1",
      "context": "The writer reports seeing a duck belonging to a person.",
      "subject": "Observation of a person's duck"
    },
    {
      "number": "2",
      "context": "The writer reports seeing a person duck.",
      "subject": "Ducking"
    },
    {
      "number": "2.1",
      "context": "The person described by 'her' performs the ducking movement.",
      "subject": "A person ducking"
    },
    {
      "number": "2.1.1",
      "context": "The writer reports seeing a person ducking.",
      "subject": "Observation of a person ducking"
    },
    {
      "number": "3",
      "context": "The pronoun 'her' refers to a person.",
      "subject": "People"
    },
    {
      "number": "3.1",
      "context": "The duck seen by the writer belongs to a person.",
      "subject": "A person's duck"
    },
    {
      "number": "3.1.1",
      "context": "The writer reports seeing a duck belonging to a person.",
      "subject": "Observation of a person's duck"
    },
    {
      "number": "3.2",
      "context": "The person described by 'her' performs the ducking movement.",
      "subject": "A person ducking"
    },
    {
      "number": "3.2.1",
      "context": "The writer reports seeing a person ducking.",
      "subject": "Observation of a person ducking"
    },
    {
      "number": "4",
      "context": "The writer reports seeing.",
      "subject": "Observation"
    },
    {
      "number": "4.1",
      "context": "The writer reports seeing a duck belonging to a person.",
      "subject": "Observation of a person's duck"
    },
    {
      "number": "4.2",
      "context": "The writer reports seeing a person ducking.",
      "subject": "Observation of a person ducking"
    },
    {
      "number": "5",
      "context": "The writer says they bought a notebook.",
      "subject": "Notebooks"
    },
    {
      "number": "5.1",
      "context": "The second sentence reports the writer's purchase of a notebook.",
      "subject": "Purchase of a notebook"
    },
    {
      "number": "6",
      "context": "The writer reports buying a notebook.",
      "subject": "Purchases"
    },
    {
      "number": "6.1",
      "context": "The second sentence reports the writer's purchase of a notebook.",
      "subject": "Purchase of a notebook"
    }
  ]
}
</output>
</example>

<example>
<post>
2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post describes two cables.",
      "subject": "Cables"
    },
    {
      "number": "1.1",
      "context": "The post states the lengths of both cables.",
      "subject": "Cable lengths"
    },
    {
      "number": "1.1.1",
      "context": "Cable A is explicitly 2 m long.",
      "subject": "2 m cables"
    },
    {
      "number": "1.1.1.1",
      "context": "The post names cable A and gives its length as 2 m.",
      "subject": "2 m cable A"
    },
    {
      "number": "1.1.1.1.1",
      "context": "The two cables are A, 2 m long, and B, 3 m long.",
      "subject": "Pair consisting of 2 m cable A and 3 m cable B"
    },
    {
      "number": "1.1.1.1.1.1",
      "context": "The post explicitly says A is not longer than B, having given both cable lengths.",
      "subject": "2 m cable A not longer than 3 m cable B"
    },
    {
      "number": "1.1.2",
      "context": "Cable B is explicitly 3 m long.",
      "subject": "3 m cables"
    },
    {
      "number": "1.1.2.1",
      "context": "The post names cable B and gives its length as 3 m.",
      "subject": "3 m cable B"
    },
    {
      "number": "1.1.2.1.1",
      "context": "The two cables are A, 2 m long, and B, 3 m long.",
      "subject": "Pair consisting of 2 m cable A and 3 m cable B"
    },
    {
      "number": "1.1.2.1.1.1",
      "context": "The post explicitly says A is not longer than B, having given both cable lengths.",
      "subject": "2 m cable A not longer than 3 m cable B"
    },
    {
      "number": "1.1.3",
      "context": "The second sentence compares cable A's length with cable B's length.",
      "subject": "Cable length comparisons"
    },
    {
      "number": "1.1.3.1",
      "context": "The post explicitly says A is not longer than B, having given both cable lengths.",
      "subject": "2 m cable A not longer than 3 m cable B"
    },
    {
      "number": "1.2",
      "context": "The opening count is two cables.",
      "subject": "Pairs of cables"
    },
    {
      "number": "1.2.1",
      "context": "The two cables are A, 2 m long, and B, 3 m long.",
      "subject": "Pair consisting of 2 m cable A and 3 m cable B"
    },
    {
      "number": "1.2.1.1",
      "context": "The post explicitly says A is not longer than B, having given both cable lengths.",
      "subject": "2 m cable A not longer than 3 m cable B"
    }
  ]
}
</output>
</example>

<example>
<post>
2 + 3 = 5.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post states the arithmetic equality 2 + 3 = 5.",
      "subject": "Arithmetic"
    },
    {
      "number": "1.1",
      "context": "The plus sign specifies addition.",
      "subject": "Addition"
    },
    {
      "number": "1.1.1",
      "context": "The numbers 2 and 3 are the numbers being added.",
      "subject": "Addends"
    },
    {
      "number": "1.1.1.1",
      "context": "In 2 + 3 = 5, 2 is an addend.",
      "subject": "2 as an addend"
    },
    {
      "number": "1.1.1.1.1",
      "context": "The full stated calculation is 2 + 3 = 5.",
      "subject": "Addition of 2 and 3 yielding 5"
    },
    {
      "number": "1.1.1.2",
      "context": "In 2 + 3 = 5, 3 is an addend.",
      "subject": "3 as an addend"
    },
    {
      "number": "1.1.1.2.1",
      "context": "The full stated calculation is 2 + 3 = 5.",
      "subject": "Addition of 2 and 3 yielding 5"
    },
    {
      "number": "1.1.2",
      "context": "The equation explicitly states the result of addition.",
      "subject": "Addition results"
    },
    {
      "number": "1.1.2.1",
      "context": "The equation explicitly gives 5 as the result.",
      "subject": "5 as an addition result"
    },
    {
      "number": "1.1.2.1.1",
      "context": "The full stated calculation is 2 + 3 = 5.",
      "subject": "Addition of 2 and 3 yielding 5"
    }
  ]
}
</output>
</example>
