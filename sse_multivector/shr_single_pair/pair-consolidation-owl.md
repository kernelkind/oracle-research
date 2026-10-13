# Pair-consolidation-owl: experimental prompt line

`pair-consolidation-owl-v4` is a draft for review, not an activated prompt or a
replacement for the approved `Hierarchy-pair-consolidation-v6`. No model tests
have been run for this line.

The user approved proceeding with this separate experimental line and the
following contract:

- A supplied parent contains formal logic and English definitions for names
  that lack a formal definition, without a separate title or meaning. The
  model preserves those definitions instead of generating a parent translation.
- Both input nodes retain their fixed natural-language titles and meanings.
- Output first supplies the first node's formal definition and English
  definitions, then the second node's, then the consolidated topic's, followed
  by the consolidated natural-language title and meaning.
- Reused names preserve their supplied definitions. Required relationships
  must appear in the formal representation rather than being introduced as
  unstated English assumptions.
- `owl` is a JSON object mapping class names to expression strings. Expressions
  retain the OWL-like operators; definitions are separate JSON fields rather
  than newline-separated `Name = expression` statements in one string.
- English glossaries cover referenced names that lack a formal definition.
  They do not duplicate formal definitions of `Parent`, `Node1`, `Node2`,
  `Consolidated` or helper classes. The consolidated natural-language title
  and meaning remain separate final outputs.

The full v4 wording remains a draft for review. Outermost parentheses are
omitted from expression strings; nested parentheses preserve grouping.

## Sources and assembly

The [v4 prompt](pair-consolidation-owl-v4.md) is built by its
[pinned assembly manifest](pair-consolidation-owl-v4.assembly.json). It includes
[OWL-like guide v4](prompt_parts/owl-reasoning-guide-v4.md) and
[explicit-meaning rules v6](prompt_parts/explicit-meaning-rules-v6.md)
byte-for-byte. Its matching definition-writing reference is
[Bootstrap-v129](Hierarchy-bootstrap-v129.md).

V4 keeps one [complete input/output example](prompt_parts/pair-consolidation-owl-example-v2.md)
using the same display-panel case, updated to the JSON format and reduced
English glossaries. The guide distinguishes exact class definitions from
one-way containment checks; required membership implications are expressed in
the formal definitions. It does not encode a containment claim as an exact
equivalence. The shared meaning-writing rules and consolidated natural-language
meaning are unchanged. All earlier published prompt and guide files retain
their original bytes.

The notation is the simplified OWL-like notation described in the guide. The
model supplies formal definitions, not an executable OWL document or a
mechanically verified proof. There is no parser, reasoner, constructor change,
experiment adapter or activated configuration in this task.

Only two input nodes and an optional parent are supplied per call. The shared
guide adds fixed input text; formal definitions and their English definitions
add output tokens. No call reduction, token saving or correctness gain has yet
been measured.

## Offline checks

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 sse_multivector/prompt_assembly.py check \
  sse_multivector/shr_single_pair/pair-consolidation-owl-v4.assembly.json
```

Assembly checks establish exact reconstruction and unchanged shared sources.
They do not establish faithful translation, valid containment or useful
consolidation. The next step is review of the draft before any separately
authorized model trial.
