# OWL-like reasoning guide

Use the simplified notation below to express membership conditions and check containment. It is not executable OWL syntax. A class is the set of things or activities admitted by a topic's definition. A relation is a named connection between things or activities.

## Notation

- `Name = expression`: an exact definition; both sides admit the same members.
- `First ⊑ Second`: every member admitted by `First` is admitted by `Second`.
- `(First AND Second)`: members satisfying both conditions.
- `(First OR Second)`: members satisfying either condition, including members satisfying both.
- `(NOT First)`: members outside `First`.
- `(relation SOME Class)`: at least one thing connected through that relation belongs to `Class`. Other connected things may belong to other classes.
- `(relation ONLY Class)`: every thing connected through that relation belongs to `Class`. This does not require any such connection to exist.

Use parentheses to make scope explicit. Use the same name for the same class or relation throughout. Different class names do not establish containment or exclude shared members.

## Open-world assumption

An unstated fact is unknown, not false. For example, `(emits SOME RedLight)` permits additional emitted light; it does not establish `(emits ONLY RedLight)`. Require both `SOME` and `ONLY` when a definition requires an existing connection and restricts every connected thing.

Preserve what each condition qualifies: a panel's background color is different from a component's emitted light. Preserve required roles, purposes and states. A plan to perform an activity does not establish that it happened.

## Definitions and conclusions

Translate the supplied fixed meanings without adding or removing membership conditions. Keep any additional general-knowledge claims explicit and separate from those translations. Such claims must be warranted independently of the desired grouping. Titles and existing placement cannot add conditions absent from a fixed meaning.

Define the proposed consolidated topic separately. Derive these conclusions from the definitions and warranted claims; do not assume them:

```text
Node1 ⊑ Consolidated
Node2 ⊑ Consolidated
Consolidated ⊑ Parent    (when a parent is supplied)
```

A conclusion follows only if it holds in every possible interpretation satisfying those definitions and claims. Missing evidence for a counterexample is not proof. Check that the definitions can hold together and that each defined class can have members: an impossible class is formally contained in every class and cannot establish a useful grouping.

These conclusions establish coverage and fit within a supplied parent. They do not identify a unique consolidated topic or establish its usefulness for browsing.

## Worked example

Here, `hasBackground` connects a panel to its whole background. `installedAsComponentIn` means installation in the role of a component, not merely physical location. The remaining names retain their ordinary meanings from the supplied definitions.

```text
BluePanel =
    (DisplayPanel AND
     (hasBackground SOME UniformlyBlueBackground))

Parent =
    (DisplayPanel OR
     (installedAsComponentIn SOME DisplayPanel))

Node1 =
    (BluePanel AND (shows SOME Text))

Node2 =
    (Light AND
     (emits SOME RedLight) AND
     (installedAsComponentIn SOME BluePanel))

Consolidated =
    (BluePanel OR
     (installedAsComponentIn SOME BluePanel))
```

`Node1` satisfies the first alternative of `Consolidated`; `Node2` satisfies the second. Every `BluePanel` is a `DisplayPanel`, so every component installed in a `BluePanel` is also installed in a `DisplayPanel`. Both alternatives of `Consolidated` therefore fit within `Parent`.

The resulting meaning is: “Blue display panels are display panels with uniformly blue backgrounds. The topic includes these panels and the components installed in them.” The blue condition applies to the panels' backgrounds; the lights may emit red light.
