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
