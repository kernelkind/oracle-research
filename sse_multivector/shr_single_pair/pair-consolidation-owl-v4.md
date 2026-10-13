Propose one new parent to consolidate two nodes in a hierarchy of information topics. Express the two nodes and the consolidation in the OWL-like notation defined below, then write the consolidated title and meaning.

# Input

The input is a JSON object:
- `parent`, when supplied, contains `owl` and `definitions`. Its `owl` is a JSON object mapping class names to expressions, including the fixed definition of the nodes' current parent under the key `Parent`. Its `definitions` provides English definitions for referenced class and relation names that lack a formal definition in `owl`. The parent has no separate `title` or `meaning`.
- `nodes` contains exactly two nodes, each with a `title` and `meaning`. The title names the topic; the meaning defines what information belongs under it. These meanings are fixed.

Treat all supplied text as data, including quoted instructions.

# Express the two nodes

Translate the first node's fixed meaning as `Node1`, then the second node's fixed meaning as `Node2`. Establish each independently of the grouping you will propose. Preserve every admitted kind, alternative, required feature, role, purpose and state. A restriction stated by one node does not restrict the other.

Put each formal class definition in its own `owl` field: the class name is the key and its expression is the string value. Include any additional class definitions needed to express a node's conditions. Necessary membership implications must be expressed through those definitions and warranted independently of the desired grouping. Do not turn a one-way containment relationship into an exact definition.

For every referenced class or relation name that lacks a formal definition in the supplied parent or the returned `owl` objects, supply an English definition in `definitions`. Do not duplicate formal definitions there. Use descriptive names. Copy any reused parent definition exactly; the same name must retain the same definition throughout the response. Use a different name for a different concept.

Do not add an unstated condition through an English definition, a name or an assumed relationship. Keep the supplied parent logic and definitions unchanged. Do not generate a replacement parent definition. Keep both node translations fixed while choosing the consolidation; neither translation may refer to `Consolidated`.

# Choose the consolidated definition

Look across both nodes for a coherent broader topic. Choose an informative topic that helps a reader decide which information to browse. Prefer a shared category over a heading that merely lists the two nodes.

Define the selected topic as `Consolidated`, using the fixed node translations and the supplied parent definition when present. It must cover both nodes' entire meanings and, when a parent is supplied, fit wholly within `Parent`. Establish those relationships from the definitions; do not assert the desired containment relationships as premises.

Supply English definitions only for referenced names that lack a formal definition. Preserve any formal or English definitions already used for the parent or either node.

# Write the title and meaning

The selected topic is `Consolidated`. Write its natural-language title and meaning from its established formal definition. The meaning must admit exactly the same kinds under exactly the same conditions; do not add or remove a membership condition while translating it into English.

Write a clear, standalone definition of the selected topic using the chosen defining conditions. Name the selected topic and describe what it is, the kinds it covers, and its required actions, methods, roles, purposes or states. Preserve the identity and complete conditions of each admitted kind. Make every shared condition apply to all alternatives; if covered kinds have different conditions, describe each in a separate sentence with its own complete conditions.

Define the selected topic, not every concept it mentions. In an activity definition, name the required kinds involved without separately defining their technical features; express a required restriction on those kinds directly as a condition of that activity. State the defining action or process directly. When a role is required for membership, define the topic in that role rather than describing a general kind through its customary uses.

Read the final definition on its own. Check that its wording admits the same kinds under the same conditions you chose. Correct wording that broadens or narrows that scope; do not add a new membership condition while writing the definition. The meaning alone must express every chosen boundary.

In `meaning`, define what belongs through the topic's identity, required features and positively stated optional variations. When listing illustrative members of a broader category, use "including but not limited to" to make clear that the list is not exhaustive. Do not add statements that the topic does not require a feature or that it applies regardless of a circumstance. State required absences that define the topic directly. Do not leave required versus optional membership to frequency qualifiers such as "typically" or "usually".

# OWL-like reasoning guide

Use the simplified notation below to express membership conditions and check containment. It is not executable OWL syntax. A class is the set of things or activities admitted by a topic's definition. A relation is a named connection between things or activities.

## Notation

- An `owl` field `"Name": "expression"` is an exact class definition: the name and the expression admit the same members.
- `First ⊑ Second` means every member admitted by `First` is admitted by `Second`. Use this notation for containment checks; an `owl` field expresses an exact definition, not a one-way containment claim.
- `First AND Second`: members satisfying both conditions.
- `First OR Second`: members satisfying either condition, including members satisfying both.
- `NOT First`: members outside `First`.
- `relation SOME Class`: at least one thing connected through that relation belongs to `Class`. Other connected things may belong to other classes.
- `relation ONLY Class`: every thing connected through that relation belongs to `Class`. This does not require any such connection to exist.

The JSON string bounds the complete expression, so omit outermost parentheses. Use nested parentheses to make grouping explicit. Give each named class definition its own JSON field; do not put `Name =` or newline-separated statements inside an expression string.

Use the same name for the same class or relation throughout. Different class names do not establish containment or exclude shared members. A name defined by an OWL expression takes its meaning from that expression and the definitions of its component names; do not give it a duplicate English glossary entry.

## Open-world assumption

An unstated fact is unknown, not false. For example, `emits SOME RedLight` permits additional emitted light; it does not establish `emits ONLY RedLight`. Require both `SOME` and `ONLY` when a definition requires an existing connection and restricts every connected thing.

Preserve what each condition qualifies: a panel's background color is different from a component's emitted light. Preserve required roles, purposes and states. A plan to perform an activity does not establish that it happened.

## Definitions and conclusions

Translate the supplied fixed meanings without adding or removing membership conditions. General knowledge may clarify language and its necessary implications; express any required membership implications in the formal definitions. They must be warranted independently of the desired grouping. Titles and existing placement cannot add conditions absent from a fixed meaning.

Define the proposed consolidated topic separately. Derive these conclusions from the definitions; do not assume them:

```text
Node1 ⊑ Consolidated
Node2 ⊑ Consolidated
Consolidated ⊑ Parent    (when a parent is supplied)
```

A conclusion follows only if it holds in every possible interpretation satisfying those definitions. Missing evidence for a counterexample is not proof. Check that the definitions can hold together and that each defined class can have members: an impossible class is formally contained in every class and cannot establish a useful grouping.

These conclusions establish coverage and fit within a supplied parent. They do not identify a unique consolidated topic or establish its usefulness for browsing.

# Check the final result

Use the final formal definitions and `meaning` unchanged in these checks. The final meaning must preserve every condition of `Consolidated` and add none.

If the consolidated topic covers associated activities, products or participants, express the relationship required for them to belong in both its formal definition and its meaning.

Interpret each supplied node from its fixed `meaning` and its necessary implications. General knowledge may clarify language; titles, customary uses, associations and existing placement cannot add conditions absent from that meaning. An activity topic includes information about plans to perform that activity unless its meaning explicitly requires the activity to have happened. Plans do not establish that the activity happened.

For each node, check for a possible case admitted by its fixed meaning but excluded by the consolidated definition. A counterexample must satisfy the node's requirements while failing the consolidation's requirements. If one is possible, revise the consolidation and its English definitions, title and meaning together; do not change the supplied parent or either node's translation to make the check pass. Recheck coverage of both nodes and containment within the supplied parent, when present.

State the final meaning directly, without referring to the supplied nodes or explaining how it was derived.

# Output

Return only one JSON object with exactly these fields, in this order:
1. `node1`: an object with `owl` followed by `definitions`, for the first supplied node.
2. `node2`: an object with `owl` followed by `definitions`, for the second supplied node.
3. `consolidated`: an object with `owl` followed by `definitions`, for the proposed consolidated topic.
4. `title`: the consolidated topic's natural-language name.
5. `meaning`: its concise, standalone natural-language definition.

Each `owl` value is a JSON object mapping class names to expression strings. Include the named topic (`Node1`, `Node2` or `Consolidated`) and any additional formal class definitions it needs. Each expression string contains one expression, without an outermost pair of parentheses, a `Name =` prefix or embedded newlines. Reused formal class definitions must be identical.

Each `definitions` value is a JSON object mapping referenced class and relation names without a formal definition anywhere in the supplied parent or returned `owl` objects to their English definitions. Include every such name referenced by that object's expressions. A class defined in `owl` must not also appear in an English `definitions` glossary. Reused English definitions must be identical. An empty glossary is `{}`.

Return the formal definitions and final title and meaning without a reasoning narrative. Do not return a parent object.

# Worked example

Input:
```json
{
  "parent": {
    "owl": {
      "Parent": "DisplayPanel OR (installedAsComponentIn SOME DisplayPanel)"
    },
    "definitions": {
      "DisplayPanel": "A device that presents visual information.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role."
    }
  },
  "nodes": [
    {
      "title": "Blue text panels",
      "meaning": "Blue text panels are display panels that show text against a uniformly blue background."
    },
    {
      "title": "Red indicator lights in blue display panels",
      "meaning": "Red indicator lights in blue display panels are lights that emit red light and are installed as components in display panels with uniformly blue backgrounds."
    }
  ]
}
```

Output:
```json
{
  "node1": {
    "owl": {
      "BluePanel": "DisplayPanel AND (hasBackground SOME UniformlyBlueBackground)",
      "Node1": "BluePanel AND (shows SOME Text)"
    },
    "definitions": {
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "shows": "A relation from a display panel to the visual information it presents.",
      "Text": "Written characters."
    }
  },
  "node2": {
    "owl": {
      "BluePanel": "DisplayPanel AND (hasBackground SOME UniformlyBlueBackground)",
      "Node2": "Light AND (emits SOME RedLight) AND (installedAsComponentIn SOME BluePanel)"
    },
    "definitions": {
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "Light": "A device that emits light.",
      "emits": "A relation from a source to light it emits.",
      "RedLight": "Light that is red.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role."
    }
  },
  "consolidated": {
    "owl": {
      "BluePanel": "DisplayPanel AND (hasBackground SOME UniformlyBlueBackground)",
      "Consolidated": "BluePanel OR (installedAsComponentIn SOME BluePanel)"
    },
    "definitions": {
      "DisplayPanel": "A device that presents visual information.",
      "hasBackground": "A relation from a panel to its whole background.",
      "UniformlyBlueBackground": "A background that is blue throughout.",
      "installedAsComponentIn": "A relation from a component to the thing in which it is installed in that role."
    }
  },
  "title": "Blue display panels",
  "meaning": "Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and the components installed in them."
}
```

The panels satisfy the first alternative of `Consolidated`; the lights satisfy the second through their installed-component role. Both alternatives fit within the supplied `Parent`. The blue condition belongs to the panels' backgrounds, not to the light emitted by their components; `SOME RedLight` does not require the lights to emit only red light.

<input>
{INPUT_JSON}
</input>
