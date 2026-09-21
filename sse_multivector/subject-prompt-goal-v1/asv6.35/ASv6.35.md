Read this social-media post as a whole and create a subject index, like the index at the back of a book. Each subject heading or subheading names a subject represented by the post.

Include subjects the post conveys literally, nonliterally, or rhetorically, whether through the whole post, an individual part, or multiple parts together, even when no single phrase names the subject. Subjects may overlap, nest, or describe the same material at broad and narrow levels. When a passage concerns several subjects together, index those subjects individually as well as the combinations expressed by the passage. Naming a combination does not replace naming its subjects individually.

Use the complete post, excluding URLs, as evidence for every subject. Use general knowledge only to interpret language and resolve references. Every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by that text.

Index only subjects represented by the post. Do not add your own commentary about a subject's plausibility or about what the post leaves unclear or unstated. Subjects concern the communicated content, not labels, credits or identifiers used merely to present it. For numbers included in the subject text, preserve what they refer to; their role as a count or measurement and any units must be supported by the text. Return a calculated result only when the result itself is explicitly stated in the post.

When a specific expression or relationship remains ambiguous after reading the complete post, represent each supported interpretation as a separate subject. State each interpretation directly as a subject, without uncertainty qualifiers. The order or proximity of separate statements does not itself establish a relationship between them. Co-mention does not by itself establish participation or causation.

Organize the index into subject headings and subheadings. Place more specific subjects under the broader subjects they refine. Give each heading and subheading its own entry. Use section-style numbering such as `1`, `1.1`, and `1.1.1` to show this structure, listing each heading before its subheadings.

Return an object for each heading or subheading, with `number`, then `context`, then `subject`. In `context`, identify the subject this entry names and the source context needed to establish its intended meaning. Resolve context-dependent references to the most specific descriptions of those references supported by the complete post. In `subject`, give the standalone subject heading or subheading.

Each `subject` must be understandable without the post, its `context` field, or other entries. This means making the subject's identity and meaning clear, not reproducing every action, circumstance, or claim surrounding it. An entry can name a subject without restating what the post says about that subject. When an entry names a comparison, include both sides if the post provides them. Preserve the meaning, negation, and relationships expressed by the entry. Make its wording concise.

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
      "subject": "Photography of Bracken's restoration for an exhibition"
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
    }
  ]
}
</output>
</example>
