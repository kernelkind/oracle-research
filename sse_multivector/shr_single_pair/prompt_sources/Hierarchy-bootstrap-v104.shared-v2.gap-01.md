Establish the explicit meaning of the selected entry in a social-media post.

# Input

A local hierarchy arranges entries from one post into layers of abstraction. Each entry has a `subject` naming a topic and a `context` helping interpret its scope.

The input is a JSON object with `local`:
- `local.post` is the full original post text.
- `local.hierarchy.entries` contains each entry once, with `number`, `subject` and `context`. It contains the complete original tree under the selected entry's root. Removing the final dot-separated component of a number gives its immediate parent's number; a number without a dot identifies the root.
- `local.hierarchy.selected` is the `number` of the entry whose meaning you must establish. Find that entry in `local.hierarchy.entries` and use its `subject` and `context`.

An ancestor is an entry above the selected entry on its original branch; a descendant is an entry below it.

# Establish the topic and factual evidence

The selected subject identifies the topic to define. Its context and the surrounding hierarchy guide interpretation. The full post is the definitive evidence for facts about what it describes; subject, context and hierarchy text cannot independently establish unsupported facts.

Read the post to identify what it says about the selected topic. Keep facts about different things distinct, and preserve uncertainty about facts the post leaves unknown.

The hierarchy indicates levels of abstraction and relationships among the topics illustrated in this post.

Use general knowledge to clarify language, identify known names and define an interpreted concept. 