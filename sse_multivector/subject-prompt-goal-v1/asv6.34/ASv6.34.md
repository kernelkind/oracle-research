Read this social-media post as a whole and create a subject index, like the index at the back of a book. Each subject heading or subheading names a subject represented by the post.

Include subjects the post conveys literally, nonliterally, or rhetorically, whether through the whole post, an individual part, or multiple parts together, even when no single phrase names the subject. Subjects may overlap, nest, or describe the same material at broad and narrow levels. When a passage concerns several subjects together, index those subjects individually as well as the combinations expressed by the passage. Include headings for general subjects as well as for the specific people, things, actions, and situations the post discusses. A subject named within a more specific heading still needs its own heading.

Use the complete post, excluding URLs, as evidence for every subject. Use general knowledge only to interpret language and resolve references. Every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by that text.

Index only subjects represented by the post. Do not add your own commentary about a subject's plausibility or about what the post leaves unclear or unstated. Subjects concern the communicated content, not labels, credits or identifiers used merely to present it. For numbers included in the subject text, preserve what they refer to; their role as a count or measurement and any units must be supported by the text. Return a calculated result only when the result itself is explicitly stated in the post.

When a specific expression or relationship remains ambiguous after reading the complete post, represent each supported interpretation as a separate subject. State each interpretation directly as a subject, without uncertainty qualifiers. The order or proximity of separate statements does not itself establish a relationship between them. Co-mention does not by itself establish participation or causation.

Organize the index into subject headings and subheadings. Place more specific subjects under the broader subjects they refine. Give each heading and subheading its own entry. Use section-style numbering such as `1`, `1.1`, and `1.1.1` to show this structure, listing each heading before its subheadings.

Return an object for each heading or subheading, with `number`, then `context`, then `subject`. In `context`, identify the subject this entry names and the source context needed to establish its intended meaning. Resolve context-dependent references to the most specific descriptions of those references supported by the complete post. In `subject`, give the standalone subject heading or subheading.

Each `subject` must be understandable without the post, its `context` field, or other entries. This means making the subject's identity and meaning clear, not reproducing every action, circumstance, or claim surrounding it. When an entry names a comparison, include both sides if the post provides them. Preserve the meaning, negation, and relationships expressed by the entry. Make its wording concise.

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
Mira, a volunteer, is helping restore Bracken, our railway museum's steam locomotive, which needs a replacement boiler. I'm photographing the restoration for an exhibition, and the museum's guided tours will continue while the work is underway.
</post>

<output>
{
  "subjects": [
    {
      "number": "1",
      "context": "The post discusses a museum's steam locomotive and guided tours.",
      "subject": "Museums"
    },
    {
      "number": "1.1",
      "context": "The museum is explicitly described as a railway museum.",
      "subject": "Railway museums"
    },
    {
      "number": "2",
      "context": "The museum's railway focus and steam locomotive establish railways as a subject.",
      "subject": "Railways"
    },
    {
      "number": "3",
      "context": "Mira is explicitly described as a volunteer.",
      "subject": "Volunteers"
    },
    {
      "number": "3.1",
      "context": "Mira is the volunteer helping restore the steam locomotive Bracken.",
      "subject": "Mira, a volunteer helping restore a steam locomotive"
    },
    {
      "number": "4",
      "context": "A volunteer is contributing to the restoration work.",
      "subject": "Volunteering"
    },
    {
      "number": "4.1",
      "context": "Mira's volunteer contribution is to restoring the steam locomotive Bracken.",
      "subject": "Volunteering in steam locomotive restoration"
    },
    {
      "number": "5",
      "context": "Bracken is identified as a locomotive.",
      "subject": "Locomotives"
    },
    {
      "number": "5.1",
      "context": "Bracken is explicitly described as a steam locomotive.",
      "subject": "Steam locomotives"
    },
    {
      "number": "5.1.1",
      "context": "Bracken is the name of the railway museum's steam locomotive.",
      "subject": "Bracken, a railway museum's steam locomotive"
    },
    {
      "number": "6",
      "context": "The locomotive needs a replacement boiler.",
      "subject": "Boilers"
    },
    {
      "number": "6.1",
      "context": "Bracken needs a replacement boiler.",
      "subject": "Boiler replacement"
    },
    {
      "number": "6.1.1",
      "context": "The steam locomotive Bracken is the locomotive needing the replacement boiler.",
      "subject": "The steam locomotive Bracken's need for a replacement boiler"
    },
    {
      "number": "7",
      "context": "The post explicitly describes restoration work underway.",
      "subject": "Restoration"
    },
    {
      "number": "7.1",
      "context": "The object being restored is a steam locomotive.",
      "subject": "Steam locomotive restoration"
    },
    {
      "number": "7.1.1",
      "context": "Bracken is the railway museum's steam locomotive that Mira is helping restore.",
      "subject": "Restoration of the steam locomotive Bracken"
    },
    {
      "number": "7.1.1.1",
      "context": "Mira is helping with the restoration of the steam locomotive Bracken.",
      "subject": "Mira's contribution to restoring the steam locomotive Bracken"
    },
    {
      "number": "8",
      "context": "The writer is photographing the restoration.",
      "subject": "Photography"
    },
    {
      "number": "8.1",
      "context": "The photographs document restoration work.",
      "subject": "Restoration photography"
    },
    {
      "number": "8.1.1",
      "context": "The restoration being photographed is that of the steam locomotive Bracken.",
      "subject": "Photography of the steam locomotive Bracken's restoration"
    },
    {
      "number": "8.1.1.1",
      "context": "The writer is taking the restoration photographs for an exhibition.",
      "subject": "Photographing the steam locomotive Bracken's restoration for an exhibition"
    },
    {
      "number": "9",
      "context": "The photographs are being taken for an exhibition.",
      "subject": "Exhibitions"
    },
    {
      "number": "9.1",
      "context": "The writer's photographs of Bracken's restoration are intended for an exhibition.",
      "subject": "Exhibition photographs of the steam locomotive Bracken's restoration"
    },
    {
      "number": "10",
      "context": "Guided tours of the museum are explicitly mentioned.",
      "subject": "Guided tours"
    },
    {
      "number": "10.1",
      "context": "The guided tours are those of the railway museum.",
      "subject": "Guided tours of a railway museum"
    },
    {
      "number": "10.1.1",
      "context": "The museum's tours will continue while Bracken's restoration is underway.",
      "subject": "Continuation of a railway museum's guided tours during steam locomotive restoration"
    }
  ]
}
</output>
</example>
