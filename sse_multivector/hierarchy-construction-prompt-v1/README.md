# HCPv1: multi-node hierarchy construction diagnostic

Status: **draft; no model calls or hierarchy changes**. This is not an adopted
HG rule. [HCPv1](HCPv1.md) asks for equivalent-node combinations and missing
ancestor links involving several existing hierarchy nodes in one request.

## Proposed input and scope

- **SP subject entry:** a subject in one post's local hierarchy.
- **Hierarchy node:** a node in the combined global hierarchy representing one
  or more SP subject entries. Every query and catalogue item is such a node.

The shared `hierarchy_construction` input adapter reads saved SP inputs and a
saved global hierarchy. It assigns each hierarchy node to the earliest
represented `note_short_id` in lexical order, **for scheduling only**. This
neither changes its membership nor limits its evidence to that post. Each node
appears in exactly one query set. Removing `dataset.select` would prepare every
set; it would not perform inference.

Every request contains the same complete catalogue: stable node IDs derived
from the minimum represented SP index, all distinct original subject/context
pairs within each node, and all saved underlying links (not just the reduced
browsing links). Duplicate subject/context pairs are sent once; all original
SP entries, masks and posts remain in review evidence. Empty masks do not remove
subject entries. No subject-vector shortlist or manual case assembly is used.

The draft restricts each proposed equivalent group or ancestor link to include
at least one query node. Catalogue-only changes are outside that request's
scope. This restriction, scheduling and full-catalogue input are experimental
choices for review, not approved production architecture.

## N100 preparation

[n100-selection.json](n100-selection.json) selects the existing separate
ten-root test hierarchy as its frozen source, including its saved diagnostic
links. [n100-spec.json](n100-spec.json) prepares only N100's scheduling set using
Astra low through the existing subscription provider. It does not rerun older
decisions. The full catalogue is intentionally available for this 100-post
diagnostic; this is not a proposed million-post input format.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare \
  target/hierarchy-construction-v1/hcpv1-n100-v1 \
  --spec sse_multivector/hierarchy-construction-prompt-v1/n100-spec.json \
  --history-root target/hierarchy-construction-v1
```

Inspect the complete real rendered request through the runner:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py show \
  target/hierarchy-construction-v1/hcpv1-n100-v1 \
  --case N100
```

Only a separately authorized `run` sends requests. Model behavior, catalogue
size suitability and joint proposal quality remain untested. Preparation is
offline. JSON validation checks supplied IDs, query involvement, duplicate
proposals and field types; it does not establish semantic correctness. No
application or conflict-repair stage for this output has been implemented.

## Prompting reference

The draft separates task definitions, JSON output and delimited input, without
requesting hidden reasoning. The reusable catalogue precedes the variable query,
following the [official prompting guidance](https://developers.openai.com/api/docs/guides/prompt-engineering).
This organization does not establish that the prompt works; the first model
test still requires review and authorization.
