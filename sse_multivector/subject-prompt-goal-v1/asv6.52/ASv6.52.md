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
I watched a lunar eclipse through binoculars. Tried sketching the Moon, but clouds kept hiding it.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "Watching a lunar eclipse is an instance of astronomical observation.",
      "subject": "Astronomical observation"
    },
    {
      "number": "1.1",
      "context": "The writer reports watching a lunar eclipse.",
      "subject": "Lunar eclipse observation"
    },
    {
      "number": "1.1.1",
      "context": "The writer watched the lunar eclipse through binoculars.",
      "subject": "Lunar eclipse observation through binoculars"
    },
    {
      "number": "2",
      "context": "The Moon is the object of both the eclipse observation and the attempted sketch.",
      "subject": "The Moon"
    },
    {
      "number": "2.1",
      "context": "The writer watched a lunar eclipse, an event involving the Moon.",
      "subject": "Lunar eclipses"
    },
    {
      "number": "3",
      "context": "The writer explicitly used binoculars to watch the eclipse.",
      "subject": "Binoculars"
    },
    {
      "number": "4",
      "context": "The writer tried to make a sketch.",
      "subject": "Sketching"
    },
    {
      "number": "4.1",
      "context": "The object of the attempted sketch is explicitly the Moon.",
      "subject": "Sketching the Moon"
    },
    {
      "number": "4.1.1",
      "context": "The writer contrasts trying to sketch the Moon with clouds repeatedly hiding it.",
      "subject": "Cloud cover hindering attempts to sketch the Moon"
    },
    {
      "number": "5",
      "context": "Clouds are explicitly described as obscuring the Moon.",
      "subject": "Clouds"
    },
    {
      "number": "5.1",
      "context": "In 'clouds kept hiding it,' 'it' refers to the Moon.",
      "subject": "Clouds repeatedly obscuring the Moon"
    }
  ]
}
</output>
</example>

<example>
<post>
Mira, a volunteer, is helping restore Bracken, our railway museum's steam locomotive, which needs a replacement boiler. I'm photographing the restoration for an exhibition, and the museum's guided tours will continue while the work is underway. Advice for museum visitors: book your visit ahead and stay on the marked visitor route.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post identifies a railway museum with a steam locomotive and guided tours.",
      "subject": "Museums"
    },
    {
      "number": "1.1",
      "context": "The writer describes a railway museum as 'our railway museum'; it owns Bracken and offers guided tours.",
      "subject": "Railway museum"
    },
    {
      "number": "1.1.1",
      "context": "Bracken is explicitly identified as the railway museum's steam locomotive.",
      "subject": "Railway museum's steam locomotive Bracken"
    },
    {
      "number": "2",
      "context": "Bracken is explicitly identified as a steam locomotive.",
      "subject": "Locomotives"
    },
    {
      "number": "2.1",
      "context": "Bracken, the locomotive being restored, is explicitly a steam locomotive.",
      "subject": "Steam locomotives"
    },
    {
      "number": "2.1.1",
      "context": "The post names the railway museum's steam locomotive Bracken.",
      "subject": "Bracken the steam locomotive"
    },
    {
      "number": "2.1.1.1",
      "context": "Bracken is being restored, with help from Mira.",
      "subject": "Restoration of Bracken the steam locomotive"
    },
    {
      "number": "2.1.1.2",
      "context": "The relative clause 'which needs a replacement boiler' refers to Bracken.",
      "subject": "Bracken the steam locomotive's need for a replacement boiler"
    },
    {
      "number": "3",
      "context": "Mira is helping restore Bracken, and the writer is photographing the restoration.",
      "subject": "Restoration"
    },
    {
      "number": "3.1",
      "context": "Helping restore the museum's steam locomotive is the central work described in the post.",
      "subject": "Steam locomotive restoration"
    },
    {
      "number": "3.1.1",
      "context": "Mira is a volunteer helping restore Bracken, the railway museum's steam locomotive.",
      "subject": "Volunteer participation in steam locomotive restoration"
    },
    {
      "number": "3.1.1.1",
      "context": "The named volunteer Mira is explicitly helping restore Bracken.",
      "subject": "Mira's volunteer work restoring Bracken the steam locomotive"
    },
    {
      "number": "4",
      "context": "Mira is introduced as a volunteer and described as helping with the restoration.",
      "subject": "Volunteering"
    },
    {
      "number": "4.1",
      "context": "Mira's volunteer activity consists of helping restore a railway museum's locomotive.",
      "subject": "Volunteering in railway museum locomotive restoration"
    },
    {
      "number": "5",
      "context": "Mira is explicitly described as a volunteer.",
      "subject": "Volunteers"
    },
    {
      "number": "5.1",
      "context": "Mira is the person identified as a volunteer helping restore Bracken.",
      "subject": "Mira, the railway locomotive restoration volunteer"
    },
    {
      "number": "6",
      "context": "Bracken needs a replacement boiler.",
      "subject": "Boilers"
    },
    {
      "number": "6.1",
      "context": "Bracken needs a replacement boiler.",
      "subject": "Steam locomotive boilers"
    },
    {
      "number": "6.1.1",
      "context": "The post identifies a replacement boiler as a requirement for Bracken.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "6.2",
      "context": "A replacement boiler is needed for Bracken.",
      "subject": "Boiler replacement"
    },
    {
      "number": "6.2.1",
      "context": "Bracken, the locomotive needing a replacement boiler, is explicitly a steam locomotive.",
      "subject": "Steam locomotive boiler replacement"
    },
    {
      "number": "7",
      "context": "The writer states, 'I'm photographing the restoration.'",
      "subject": "Photography"
    },
    {
      "number": "7.1",
      "context": "The writer is photographing the restoration of Bracken.",
      "subject": "Restoration photography"
    },
    {
      "number": "7.1.1",
      "context": "The restoration being photographed is that of Bracken, the railway museum's steam locomotive.",
      "subject": "Photography of Bracken the steam locomotive's restoration"
    },
    {
      "number": "7.1.1.1",
      "context": "The writer is photographing Bracken's restoration specifically for an exhibition.",
      "subject": "Photography of Bracken the steam locomotive's restoration for an exhibition"
    },
    {
      "number": "7.2",
      "context": "The writer is taking photographs for an exhibition.",
      "subject": "Photography for an exhibition"
    },
    {
      "number": "8",
      "context": "An exhibition is the stated purpose of the writer's restoration photography.",
      "subject": "Exhibitions"
    },
    {
      "number": "8.1",
      "context": "Photographs of Bracken's restoration are being made for an exhibition.",
      "subject": "Exhibition of photographs of Bracken the steam locomotive's restoration"
    },
    {
      "number": "9",
      "context": "The museum's guided tours will continue while the restoration work is underway.",
      "subject": "Guided tours"
    },
    {
      "number": "9.1",
      "context": "The museum's guided tours will continue during the restoration work on Bracken.",
      "subject": "Railway museum's guided tours"
    },
    {
      "number": "9.1.1",
      "context": "The post states that guided tours will continue while work on restoring Bracken is underway.",
      "subject": "Railway museum's guided tours continuing during Bracken's restoration"
    },
    {
      "number": "10",
      "context": "Bracken needs a replacement boiler, which is a replacement part.",
      "subject": "Replacement parts"
    },
    {
      "number": "10.1",
      "context": "The replacement part needed for Bracken is a boiler.",
      "subject": "Replacement boilers"
    },
    {
      "number": "10.1.1",
      "context": "Bracken, explicitly identified as a steam locomotive, needs a replacement boiler.",
      "subject": "Replacement boiler for Bracken the steam locomotive"
    },
    {
      "number": "11",
      "context": "The post explicitly gives advice to museum visitors.",
      "subject": "Advice"
    },
    {
      "number": "11.1",
      "context": "The advice is addressed to visitors to the railway museum.",
      "subject": "Advice for railway museum visitors"
    },
    {
      "number": "11.1.1",
      "context": "The first instruction advises museum visitors to book their visit ahead.",
      "subject": "Advice for railway museum visitors to book visits in advance"
    },
    {
      "number": "11.1.1.1",
      "context": "The full advice combines booking the visit ahead with staying on the marked visitor route.",
      "subject": "Advice for railway museum visitors to book visits in advance and stay on the marked visitor route"
    },
    {
      "number": "11.1.2",
      "context": "The second instruction advises museum visitors to stay on the marked visitor route.",
      "subject": "Advice for railway museum visitors to stay on the marked visitor route"
    },
    {
      "number": "11.1.2.1",
      "context": "The full advice combines staying on the marked visitor route with booking the visit ahead.",
      "subject": "Advice for railway museum visitors to book visits in advance and stay on the marked visitor route"
    },
    {
      "number": "12",
      "context": "Booking a visit ahead is one of the actions recommended to museum visitors.",
      "subject": "Advance booking"
    },
    {
      "number": "12.1",
      "context": "The advance booking recommended in the advice concerns visits to the railway museum.",
      "subject": "Advance booking for railway museum visits"
    },
    {
      "number": "13",
      "context": "The visitor advice explicitly names a marked visitor route.",
      "subject": "Marked routes"
    },
    {
      "number": "13.1",
      "context": "The marked visitor route is the one museum visitors are advised to stay on.",
      "subject": "Railway museum's marked visitor route"
    },
    {
      "number": "14",
      "context": "Staying on the marked visitor route is one of the actions recommended to museum visitors.",
      "subject": "Staying on marked routes"
    },
    {
      "number": "14.1",
      "context": "The recommended action is staying on the railway museum's marked visitor route.",
      "subject": "Staying on a railway museum's marked visitor route"
    },
    {
      "number": "15",
      "context": "The advice is explicitly addressed to museum visitors.",
      "subject": "Visitors"
    },
    {
      "number": "15.1",
      "context": "The visitors addressed by the advice are visitors to the railway museum.",
      "subject": "Railway museum visitors"
    }
  ]
}
</output>
</example>
