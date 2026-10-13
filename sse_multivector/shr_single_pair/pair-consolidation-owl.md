# Pair-consolidation-owl: experimental prompt line

`pair-consolidation-owl-v1` is a draft for review, not an activated prompt or a
replacement for the approved `Hierarchy-pair-consolidation-v6`. No model tests
have been run for this line.

The user approved proceeding with this separate experimental line and the
following contract:

- A supplied parent contains formal logic and English definitions for its
  named classes and relations, without a separate title or meaning. The model
  preserves those definitions instead of generating a parent translation.
- Both input nodes retain their fixed natural-language titles and meanings.
- Output first supplies the first node's formal definition and English
  definitions, then the second node's, then the consolidated topic's, followed
  by the consolidated natural-language title and meaning.
- Reused names preserve their supplied definitions. Required relationships
  must appear in the formal representation rather than being introduced as
  unstated English assumptions.

The exact JSON field names and the full v1 wording are draft implementation
choices for review, not independently approved decisions.

## Sources and assembly

The [v1 prompt](pair-consolidation-owl-v1.md) is built by its
[pinned assembly manifest](pair-consolidation-owl-v1.assembly.json). It includes
the reviewed [OWL-like guide v1](prompt_parts/owl-reasoning-guide-v1.md) and
[explicit-meaning rules v6](prompt_parts/explicit-meaning-rules-v6.md)
byte-for-byte. Its matching definition-writing reference is
[Bootstrap-v129](Hierarchy-bootstrap-v129.md). Neither shared fragment nor any
existing prompt is modified by this draft.

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
  sse_multivector/shr_single_pair/pair-consolidation-owl-v1.assembly.json
```

Assembly checks establish exact reconstruction and unchanged shared sources.
They do not establish faithful translation, valid containment or useful
consolidation. The next step is review of the draft before any separately
authorized model trial.
