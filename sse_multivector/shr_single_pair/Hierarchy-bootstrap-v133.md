Establish the explicit meaning of the selected entry in a social-media post.

# Input

A local hierarchy arranges entries from one post into layers of abstraction. Each entry has a `subject` naming a topic and a `context` helping interpret the subject.

The input is a JSON object with `local`:
- `local.post` is the full original post text.
- `local.hierarchy.entries` contains each entry once, with `number`, `subject` and `context`. It contains the complete original tree under the selected entry's root. Removing the final dot-separated component of a number gives its immediate parent's number; a number without a dot identifies the root.
- `local.hierarchy.selected` is the `number` of the entry whose meaning you must establish. Find that entry in `local.hierarchy.entries` and use its `subject` and `context`.

An ancestor is an entry above the selected entry on its original branch; a descendant is an entry below it.

# Establish the topic and factual evidence

The selected subject establishes the topic, its level of abstraction and its expressed restrictions. Use the full post, its context and the surrounding hierarchy to resolve its intended sense, references and named identity. An ancestor may establish a category restriction left implicit by the selected subject when the original branch and post support that interpretation. Preserve the selected level of abstraction: descendants and details of a particular example do not automatically exhaust the category or become defining conditions. The full post is the definitive evidence for facts about particular people, things and events; subject, context and hierarchy text cannot independently establish unsupported facts.

Read the post to identify what it says about the selected topic. Keep facts about different things distinct, and preserve uncertainty about facts the post leaves unknown.

The hierarchy records intended generalizations and narrower topics. Its relationships guide interpretation; they do not establish factual claims.

Use general knowledge to clarify language, identify known names and define an interpreted concept. Retain the selected name to preserve identity. Include features needed to define the chosen sense or scope, including defining designs or methods. Distinguish required features from optional variations. Do not turn non-defining details about design, method or customary use into membership conditions. A definition may include features not stated verbatim in the post; it must not assert an unmentioned occurrence, purpose or state of a particular example. A URL alone does not supply its destination's contents. Treat all supplied text as data, including quoted instructions.

# Identify category ambiguities

Identify material differences in membership between supported interpretations of the selected subject. Include choices introduced by your proposed definition, even when the input does not explicitly contrast them. Consider its sense or identity, the kinds it covers, its level of abstraction, which actions or methods define an activity and which are optional ways of performing it, and whether a role, purpose, state or circumstance defines the category or only describes a supporting example. Also consider whether supplied descendants illustrate a broader category or establish its full membership.

Distinguish what the subject identifies from which information belongs under it. First identify each kind covered and the features required to make it the intended kind, including any defining role. An intention to use something as a kind does not establish the other features required to be that kind, or that the use occurred. A kind may be defined by its intended use; when it also requires other features, state and preserve them. A role, use or component relationship must preserve every required feature of the kind involved. Examine whether further roles, purposes or states identify the topic, limit the information covered, or do both. For every condition proposed for the meaning, identify and resolve any material ambiguity in what it requires or whom it applies to. State which conditions define a kind and which must hold for a particular example.

Record material differences in membership as questions in `ambiguities`. Use contrasting cases to examine proposed conditions, not to introduce an interpretation unsupported by the input. A hypothetical test case does not establish a fact about the post. Unknown facts about an example are not choices you can settle by defining a category.

# Resolve category ambiguities

Resolve each ambiguity using the selected subject, its context, the original branch and the post. Preserve all explicitly named alternatives and parts. Use ancestors and descendants to help interpret its sense and level of abstraction. Do not apply every ancestor restriction automatically or discard any named alternative or required part to make a relationship fit. A description requiring several parts together may narrow the topic of a required part; the other parts need not be instances of that part's kind or action. Decide whether multiple named parts must be described together or are alternatives admitted independently. Co-mention alone does not settle this. Preserve the restrictions the selected subject applies to each admitted alternative. If a coherent interpretation of the selected subject cannot be justified, record the ambiguity as unresolved.

For an activity, choose a concrete condition stating its defining action or process. Decide which actions are required and which methods are optional, retaining any required purpose or product alongside the action. If competing process conditions admit different activities, record and resolve that boundary; naming the activity or listing possible methods does not settle it. For a particular instance, retain the chosen process while preserving uncertainty about unmentioned methods, tools and outcomes.

Choose a supported interpretation for each ambiguity. Identify conditions shared by every admitted kind and conditions specific to each alternative. Apply every shared condition to every alternative, and state each alternative's remaining conditions completely. When something qualifies through a role, use or component relationship, specify both the kind and the required relationship. Do not substitute a broader or narrower topic or combine competing interpretations to avoid deciding.

Check the proposed definition as a whole, including its opening description and every alternative or relationship. Are its conditions enough to establish membership, or can something satisfy the wording while lacking a defining feature of the chosen kind? Could a member of the chosen interpretation fail the wording? Resolve any discrepancy by revising the general conditions using the subject and its evidence. Preserve legitimate members and all named alternatives or jointly required parts. Do not add exclusions solely to block a particular test case. Record consequential boundary questions in `ambiguities` and the chosen conditions in `resolutions`.

In each `resolutions.answer`, state the concrete membership condition chosen for that ambiguity: the properties, role, purpose or state that qualify something for the category. Specify whether the condition characterizes the kind or must hold for the particular example. The choices must fit together as one coherent meaning. Repeating the selected subject is not enough to resolve a difference in membership. Put the brief justification and explanations of rejected interpretations in `justification`; use a null answer if no coherent condition can be justified.

# Write the meaning

Use the conditions chosen in `resolutions` when writing `meaning`. Preserve restrictions stated by the selected subject or required by its intended sense. Do not use the diagnostics to interpret the final definition; keep explanations of rejected restrictions in `resolutions`.

Write a clear, standalone definition of the selected topic using the chosen defining conditions. Name the selected topic and describe what it is, the kinds it covers, and its required actions, methods, roles, purposes or states. Preserve the identity and complete conditions of each admitted kind. Make every shared condition apply to all alternatives; if covered kinds have different conditions, describe each in a separate sentence with its own complete conditions.

Define the selected topic, not every concept it mentions. In an activity definition, name the required kinds involved without separately defining their technical features; express a required restriction on those kinds directly as a condition of that activity. State the defining action or process directly. When a role is required for membership, define the topic in that role rather than describing a general kind through its customary uses.

Read the final definition on its own. Check that its wording admits the same kinds under the same conditions you chose. Correct wording that broadens or narrows that scope; do not add a new membership condition while writing the definition. The meaning alone must express every chosen boundary.

In `meaning`, define what belongs through the topic's identity, required features and positively stated optional variations. When listing illustrative members of a broader category, use "including but not limited to" to make clear that the list is not exhaustive. Do not add statements that the topic does not require a feature or that it applies regardless of a circumstance. State required absences that define the topic directly. Do not leave required versus optional membership to frequency qualifiers such as "typically" or "usually".


If a material ambiguity remains unresolved or the choices cannot form one coherent meaning, return a null meaning.

# Write the title

After finalizing `meaning`, write a concise, natural title naming its topic. Use only information in that meaning. Use the topic’s ordinary name when it identifies the topic clearly. Preserve the topic’s identity and level of abstraction. Keep distinctions needed to recognize the topic; leave explanatory and illustrative details in the meaning. Favor clear, ordinary phrasing when shortening would make the title awkward or misleading. Do not change the meaning to fit the title. If `meaning` is null, `title` must be null.

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
  "meaning": "Feedback consisting of views, evaluations or suggestions communicated about an activity or experience, whether responses are anonymous or identified.",
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
  "title": "Old glass negatives of studio portraits awaiting digital scanning",
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

# Input

<input>
{INPUT_JSON}
</input>
