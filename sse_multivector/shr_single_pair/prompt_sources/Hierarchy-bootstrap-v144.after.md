
If a material ambiguity remains unresolved or the choices cannot form one coherent meaning, return a null meaning.

# Output

Return only one JSON object with exactly five fields:
- `ambiguities`: an array of category-boundary questions. Each record has exactly these fields:
  - `id`: a short identifier, unique within this response.
  - `question`: a question identifying competing category boundaries for the selected subject, including material choices introduced by the proposed definition.
- `resolutions`: an array with exactly one record for each ambiguity, with no additional records. Each record has exactly these fields:
  - `ambiguity_id`: the `id` of the ambiguity being resolved.
  - `answer`: the chosen membership condition, or JSON `null` if no coherent condition can be justified.
  - `justification`: a brief explanation of why that condition fits the selected subject and its evidence, including why competing interpretations were rejected, or why the ambiguity cannot be resolved.
- `meaning`: a concise standalone description incorporating the chosen boundaries, or JSON `null` if one meaning cannot be established. State the meaning directly without referring to the post or explaining how you derived it.
- `title`: a concise topic label derived solely from `meaning`, or JSON `null` exactly when `meaning` is null.
- `evidence`: an array of records supporting the meaning. Each record has exactly these fields:
  - `quote`: an exact, contiguous excerpt from `local.post`, without inserted words or ellipses.
  - `supports`: the part of the meaning that the excerpt supports, or the unresolved issue when `meaning` is null.
  - `inference`: a brief interpretation connecting the excerpt to the supported meaning; use JSON `null` when the support is direct. Keep category-boundary choices in `resolutions`.

Use empty `ambiguities` and `resolutions` arrays when there are no material category ambiguities. If any resolution's `answer` is null, `meaning` must be null.

Account for every kind, role and restriction included in the meaning, including purpose and required state. Do not use subject, context or local hierarchy text as a quote unless the same text appears in the post. If `meaning` is null, identify the unresolved issue through the evidence records; use an empty array only when the post supplies no relevant text. Give concise boundary decisions and evidence interpretations, not a step-by-step reasoning trace.

# Examples

## Define a broad category without treating its illustrated responses as exhaustive

<example>
<input>
{
  "local": {
    "post": "Saturday's paper-circuit workshop is over, and I'm trying to improve the next one. We asked participants what was clear, what was confusing, and what they would change about the workshop.\n\nWe tried two ways of collecting feedback. Participants could leave comment slips in a box by the exit. The slips were anonymous; we didn't ask for names. Several comments asked for larger diagrams and more time with the switches. In the closing discussion, people spoke under their own names and suggested changes to the next workshop. That conversation also helped us understand why the diagrams had been difficult to follow.\n\nThese methods reached different people, and I'd like to try another way of gathering feedback next month. The batteries and spare components are packed away now. I still need to return the borrowed table before the hall opens tomorrow.",
    "hierarchy": {
      "selected": "2",
      "entries": [
        {
          "number": "2",
          "context": "The post describes asking participants questions and trying two feedback methods.",
          "subject": "Feedback"
        },
        {
          "number": "2.1",
          "context": "All feedback questions and methods concern the paper-circuit workshops.",
          "subject": "Feedback about paper-circuit workshops"
        },
        {
          "number": "2.1.1",
          "context": "Participants were asked what was clear about the workshop.",
          "subject": "Asking participants what was clear about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.1.1",
          "context": "The organizers asked participants what was clear, confusing, and worth changing.",
          "subject": "Asking participants what was clear, what was confusing, and what they would change about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.2",
          "context": "Participants were asked what was confusing about the workshop.",
          "subject": "Asking participants what was confusing about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.2.1",
          "context": "The organizers asked participants what was clear, confusing, and worth changing.",
          "subject": "Asking participants what was clear, what was confusing, and what they would change about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.3",
          "context": "Participants were asked what they would change about the workshop.",
          "subject": "Asking participants what they would change about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.3.1",
          "context": "The organizers asked participants what was clear, confusing, and worth changing.",
          "subject": "Asking participants what was clear, what was confusing, and what they would change about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.4",
          "context": "Participants could leave anonymous comment slips without names in a box by the exit.",
          "subject": "Anonymous comment slips, with no names requested, for feedback about Saturday's completed paper-circuit workshop, which participants could leave in a box by the exit"
        },
        {
          "number": "2.1.4.1",
          "context": "The anonymous-slip method and named closing discussion were the two feedback methods tried.",
          "subject": "Two feedback methods tried for Saturday's completed paper-circuit workshop: anonymous comment slips with no names requested, left in a box by the exit, and a closing discussion in which participants spoke under their own names"
        },
        {
          "number": "2.1.4.1.1",
          "context": "These methods reached different people.",
          "subject": "Anonymous comment slips with no names requested, left in a box by the exit, and a closing discussion with participants speaking under their own names reached different people for feedback about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.5",
          "context": "Several comments asked for larger diagrams.",
          "subject": "Several anonymous comments about Saturday's completed paper-circuit workshop requesting larger diagrams"
        },
        {
          "number": "2.1.5.1",
          "context": "Several comments asked for larger diagrams and more time with the switches.",
          "subject": "Several anonymous comments about Saturday's completed paper-circuit workshop requesting larger diagrams and more time with the switches"
        },
        {
          "number": "2.1.6",
          "context": "Several comments asked for more time with the switches.",
          "subject": "Several anonymous comments about Saturday's completed paper-circuit workshop requesting more time with the switches"
        },
        {
          "number": "2.1.6.1",
          "context": "Several comments asked for larger diagrams and more time with the switches.",
          "subject": "Several anonymous comments about Saturday's completed paper-circuit workshop requesting larger diagrams and more time with the switches"
        },
        {
          "number": "2.1.7",
          "context": "The closing discussion was the second feedback method.",
          "subject": "Closing discussion of Saturday's completed paper-circuit workshop with participants speaking under their own names"
        },
        {
          "number": "2.1.7.1",
          "context": "People in the discussion suggested changes to the next workshop.",
          "subject": "Participants speaking under their own names in the closing discussion of Saturday's completed paper-circuit workshop and suggesting changes to the next paper-circuit workshop"
        },
        {
          "number": "2.1.7.2",
          "context": "That conversation helped the organizers understand why the diagrams had been difficult to follow.",
          "subject": "The closing discussion of Saturday's completed paper-circuit workshop, with participants speaking under their own names, helping organizers understand why that workshop's diagrams were difficult to follow"
        },
        {
          "number": "2.1.7.3",
          "context": "The anonymous-slip method and named closing discussion were the two feedback methods tried.",
          "subject": "Two feedback methods tried for Saturday's completed paper-circuit workshop: anonymous comment slips with no names requested, left in a box by the exit, and a closing discussion in which participants spoke under their own names"
        },
        {
          "number": "2.1.7.3.1",
          "context": "These methods reached different people.",
          "subject": "Anonymous comment slips with no names requested, left in a box by the exit, and a closing discussion with participants speaking under their own names reached different people for feedback about Saturday's completed paper-circuit workshop"
        },
        {
          "number": "2.1.8",
          "context": "The author would like another way of gathering feedback next month.",
          "subject": "Author's desire to try another method of gathering paper-circuit workshop feedback next month"
        }
      ]
    }
  }
}
</input>
<output>
{
  "ambiguities": [
    {
      "id": "a1",
      "question": "Is Feedback limited to the workshop comments and discussion shown here, or does it name a broader category of communicated views, evaluations and suggestions?"
    },
    {
      "id": "a2",
      "question": "Must feedback be anonymous?"
    }
  ],
  "resolutions": [
    {
      "ambiguity_id": "a1",
      "answer": "Communicated views, evaluations or suggestions about an activity or experience.",
      "justification": "The selected subject is Feedback. Its child Feedback about paper-circuit workshops supplies a narrower category, and the more specific descendants describe the illustrated responses."
    },
    {
      "ambiguity_id": "a2",
      "answer": "Feedback may be anonymous or identified. In either form, it consists of views, evaluations or suggestions communicated about an activity or experience.",
      "justification": "The anonymous comments and named discussion both communicate evaluations or suggestions about the workshop. A comment slip or spoken remark qualifies through that content, rather than its form alone."
    }
  ],
  "meaning": "Feedback consists of views, evaluations or suggestions communicated about an activity or experience.",
  "title": "Feedback",
  "evidence": [
    {
      "quote": "We asked participants what was clear, what was confusing, and what they would change about the workshop.",
      "supports": "Communicated views, evaluations or suggestions about an activity or experience.",
      "inference": "The questions solicit participants' evaluations and suggestions about their workshop experience."
    },
    {
      "quote": "The slips were anonymous; we didn't ask for names.",
      "supports": "Anonymous responses.",
      "inference": null
    },
    {
      "quote": "In the closing discussion, people spoke under their own names and suggested changes to the next workshop.",
      "supports": "Identified responses.",
      "inference": null
    }
  ]
}
</output>
</example>

## Resolve a grouped descendant while preserving the selected subject's restrictions

<example>
<input>
{
  "local": {
    "post": "At the neighborhood history room today, I sorted the queue for digitally scanning photographs. The plates in that queue are glass photographic negatives, and none has been scanned yet. Some show studio portraits; others show shop fronts before the street was widened. The envelopes give approximate dates, but we haven't checked those dates.\n\nA separate box holds glass negatives that were scanned last month. Those are finished and aren't in this queue. The paper photographs waiting on the next shelf still need scanning too.\n\nWe also found two aluminum mounting plates for the scanner stand. They're hardware, not photographic negatives, and they aren't part of the scanning queue. I labelled the trays so we can keep these things separate. Tomorrow we'll test the machine on a modern print before handling the old glass.",
    "hierarchy": {
      "selected": "3.1",
      "entries": [
        {
          "number": "3",
          "context": "Some of the glass negatives show studio portraits.",
          "subject": "Studio portraits"
        },
        {
          "number": "3.1",
          "context": "The studio portraits occur on some of the old, unscanned glass negatives in the queue.",
          "subject": "Old, as-yet-unscanned glass photographic negatives in the photograph-scanning queue showing studio portraits"
        },
        {
          "number": "3.1.1",
          "context": "The post distinguishes queued negatives showing studio portraits from others showing pre-widening shop fronts.",
          "subject": "Groups of old, as-yet-unscanned glass photographic negatives in the photograph-scanning queue showing studio portraits and shop fronts before street widening"
        }
      ]
    }
  }
}
</input>
<output>
{
  "ambiguities": [
    {
      "id": "a1",
      "question": "Do shop-front-only negatives belong under the selected topic because its descendant names a group containing both portrait and shop-front negatives?"
    }
  ],
  "resolutions": [
    {
      "ambiguity_id": "a1",
      "answer": "Negatives must depict studio portraits.",
      "justification": "The selected subject expressly requires studio portraits. The post distinguishes negatives showing portraits from others showing shop fronts; the combined group in the descendant does not remove that requirement."
    }
  ],
  "meaning": "Old, unscanned glass photographic negatives queued for digital scanning and depicting studio portraits.",
  "title": "Studio portrait negatives",
  "evidence": [
    {
      "quote": "I sorted the queue for digitally scanning photographs. The plates in that queue are glass photographic negatives, and none has been scanned yet.",
      "supports": "Unscanned glass photographic negatives queued for digital scanning.",
      "inference": null
    },
    {
      "quote": "Some show studio portraits; others show shop fronts before the street was widened.",
      "supports": "Depicting studio portraits.",
      "inference": "Some refers to the glass photographic negatives in the scanning queue; the selected subject identifies the portrait-bearing group."
    },
    {
      "quote": "Tomorrow we'll test the machine on a modern print before handling the old glass.",
      "supports": "Old glass photographic negatives.",
      "inference": "The old glass refers to the queued glass photographic negatives."
    }
  ]
}
</output>
</example>

<example>
<input>
{
  "local": {
    "post": "Transportation update: buses carried passengers and trains carried freight today.",
    "hierarchy": {
      "selected": "1",
      "entries": [
        {
          "number": "1",
          "subject": "Transportation",
          "context": "The post reports transportation of people and goods."
        },
        {
          "number": "1.1",
          "subject": "Transportation by bus",
          "context": "Buses carried passengers."
        },
        {
          "number": "1.1.1",
          "subject": "Buses carrying passengers today",
          "context": "The post reports this passenger transport today."
        },
        {
          "number": "1.2",
          "subject": "Transportation by train",
          "context": "Trains carried freight."
        },
        {
          "number": "1.2.1",
          "subject": "Trains carrying freight today",
          "context": "The post reports this freight transport today."
        }
      ]
    }
  }
}
</input>
<output>
{
  "ambiguities": [
    {
      "id": "a1",
      "question": "Does Transportation identify the general activity, or only the bus and train services reported today?"
    }
  ],
  "resolutions": [
    {
      "ambiguity_id": "a1",
      "answer": "Transportation is the movement of people or goods from one place to another.",
      "justification": "The selected subject names the general activity. Its descendants identify particular modes and services rather than exhausting the category. The definition states the process itself without listing ways of carrying it out."
    }
  ],
  "meaning": "Transportation is the movement of people or goods from one place to another.",
  "title": "Transportation",
  "evidence": [
    {
      "quote": "buses carried passengers and trains carried freight today.",
      "supports": "The movement of people or goods.",
      "inference": "Carrying passengers and freight identifies transportation as the general activity. The vehicles and particular journeys illustrate it rather than define it."
    }
  ]
}
</output>
</example>

<example>
<input>
{
  "local": {
    "post": "I wore 18-karat gold earrings today. I like their rose color.",
    "hierarchy": {
      "selected": "1.1",
      "entries": [
        {
          "number": "1",
          "subject": "Gold alloys",
          "context": "The post names a gold alloy used for jewelry."
        },
        {
          "number": "1.1",
          "subject": "18-karat gold",
          "context": "18-karat gold is the material named in the post."
        },
        {
          "number": "1.1.1",
          "subject": "18-karat gold earrings worn by the author today",
          "context": "The author reports wearing these earrings today."
        },
        {
          "number": "1.1.1.1",
          "subject": "Author liking the rose color of the 18-karat gold earrings worn today",
          "context": "The author likes the rose color of these particular earrings."
        }
      ]
    }
  }
}
</input>
<output>
{
  "ambiguities": [
    {
      "id": "a1",
      "question": "Does 18-karat gold identify the alloy kind, or only the author's rose-colored earrings worn today?"
    },
    {
      "id": "a2",
      "question": "Does any gold alloy qualify, or is a particular gold content required?"
    }
  ],
  "resolutions": [
    {
      "ambiguity_id": "a1",
      "answer": "The topic is the gold alloy kind defined by 18-karat fineness.",
      "justification": "The selected material is broader than the particular earrings, their rose color and the reported use."
    },
    {
      "ambiguity_id": "a2",
      "answer": "The alloy must have a nominal gold content of 18 parts out of 24 by mass, or 75%.",
      "justification": "Karat fineness measures the gold proportion. General knowledge supplies the composition required by the selected name; the name alone or a generic gold-alloy description does not state it."
    }
  ],
  "meaning": "18-karat gold is a gold alloy with a nominal gold content of 75% by mass.",
  "title": "18-karat gold",
  "evidence": [
    {
      "quote": "18-karat gold earrings",
      "supports": "18-karat gold as the selected material.",
      "inference": "The phrase identifies the alloy kind. General knowledge supplies its defining composition; the earring form and rose color do not define that kind."
    }
  ]
}
</output>
</example>

# Write the title

`title` is a short topic label for a list, derived solely from finalized `meaning`. Use the topic's ordinary name or a simple noun phrase. The requirement to state all defining conditions applies to `meaning`, not to the title. Do not compress the definition into a title or enumerate its steps, parts or conditions. Leave those details in `meaning`. Do not change `meaning` to fit the title. If `meaning` is null, `title` must be null.

Examples of titles from finalized meanings:
- Meaning: The author's plan to replace cracked roof tiles, renew the flashing and clear the gutters before autumn rains.
  Title: Roof maintenance plan
- Meaning: A student's preference to study regularly, seek feedback and revise their work to improve academic performance.
  Title: Preferred study approach

# Input

<input>
{INPUT_JSON}
</input>
