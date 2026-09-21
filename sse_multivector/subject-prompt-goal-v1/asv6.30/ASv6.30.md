Read this social-media post as a whole and create a subject index, like the index at the back of a book. Each entry names a subject represented by the post.

Include subjects the post conveys literally, nonliterally, or rhetorically, whether through the whole post, an individual part, or multiple parts together, even when no single phrase names the subject. Subjects may overlap, nest, or describe the same material at broad and narrow levels. When a passage concerns several subjects together, index those subjects individually as well as the combinations expressed by the passage. Naming a combination does not replace naming its subjects individually.

Use the complete post, excluding URLs, as evidence for every subject. Use general knowledge only to interpret language and resolve references. Every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by that text.

Index only subjects represented by the post. Do not add your own commentary about a subject's plausibility or about what the post leaves unclear or unstated. Subjects concern the communicated content, not labels, credits or identifiers used merely to present it. For any numbers included in an entry, preserve what they refer to; their role as a count or measurement and any units must be supported by the text. Return a calculated result only when the result itself is explicitly stated in the post.

When a specific expression or relationship remains ambiguous after reading the complete post, represent each supported interpretation as a separate subject. State each interpretation directly as a subject, without uncertainty qualifiers. The order or proximity of separate statements does not itself establish a relationship between them. Co-mention does not by itself establish participation or causation.

Return an object for each entry, with `context` followed by `subject`. In `context`, identify the subject this entry names and the source context needed to establish its intended meaning. Resolve context-dependent references to the most specific descriptions of those references supported by the complete post. In `subject`, give the standalone index entry.

Each `subject` must be understandable without the post, its `context` field, or other entries. This means making the subject's identity and meaning clear, not reproducing every action, circumstance, or claim surrounding it. An entry can name a subject without restating what the post says about that subject. When an entry names a comparison, include both sides if the post provides them. Preserve the meaning, negation, and relationships expressed by the entry. Make its wording concise.

<example>
<post>
I watched a lunar eclipse through binoculars. Tried sketching the Moon, but clouds kept hiding it.
</post>

<output>
{
  "subjects": [
    {
      "context": "The writer watched a lunar eclipse, an event involving the Moon.",
      "subject": "Lunar eclipses"
    },
    {
      "context": "The Moon is the object of both the eclipse observation and the attempted sketch.",
      "subject": "The Moon"
    },
    {
      "context": "The writer explicitly used binoculars to watch the eclipse.",
      "subject": "Binoculars"
    },
    {
      "context": "Watching a lunar eclipse is an instance of astronomical observation.",
      "subject": "Astronomical observation"
    },
    {
      "context": "The writer reports watching a lunar eclipse.",
      "subject": "Lunar eclipse observation"
    },
    {
      "context": "The writer watched the lunar eclipse through binoculars.",
      "subject": "Lunar eclipse observation through binoculars"
    },
    {
      "context": "The writer tried to make a sketch.",
      "subject": "Sketching"
    },
    {
      "context": "The object of the attempted sketch is explicitly the Moon.",
      "subject": "Sketching the Moon"
    },
    {
      "context": "Clouds are explicitly described as obscuring the Moon.",
      "subject": "Clouds"
    },
    {
      "context": "In 'clouds kept hiding it,' 'it' refers to the Moon.",
      "subject": "Clouds repeatedly obscuring the Moon"
    },
    {
      "context": "The writer contrasts trying to sketch the Moon with clouds repeatedly hiding it.",
      "subject": "Cloud cover hindering attempts to sketch the Moon"
    }
  ]
}
</output>
</example>
