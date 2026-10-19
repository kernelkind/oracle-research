Establish the selected entry's explicit `meaning` in the supplied post, then give that topic a brief `title`.

# Input

A local hierarchy arranges entries from one post into layers of abstraction. Each entry has a `subject` naming a topic and a `context` helping interpret the subject.

The input is a JSON object with `local`:
- `local.post` is the full original post text.
- `local.hierarchy.entries` contains each entry once, with `number`, `subject` and `context`. It contains the complete original tree under the selected entry's root. Removing the final dot-separated component of a number gives its immediate parent's number; a number without a dot identifies the root.
- `local.hierarchy.selected` is the `number` of the entry whose meaning you must establish. Find that entry in `local.hierarchy.entries` and use its `subject` and `context`.

An ancestor is an entry above the selected entry on its original branch; a descendant is an entry below it.

# Establish the topic and factual evidence

The selected subject identifies the topic to define in `meaning` and its level of abstraction. Use the full post, its context and the surrounding hierarchy to resolve its intended sense, references, named identity and defining restrictions. An ancestor may establish a category restriction left implicit by the selected subject when the original branch and post support that interpretation. Preserve the selected level of abstraction: descendants and details of a particular example do not automatically exhaust the category or become defining conditions. The full post is the definitive evidence for facts about particular people, things and events; subject, context and hierarchy text cannot independently establish unsupported facts.

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

Use the conditions chosen in `resolutions` when writing `meaning`. Keep explanations of rejected restrictions in `resolutions`.
