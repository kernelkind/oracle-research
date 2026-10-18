# Meaning example probe v1 — experimental diagnostic

Status: reusable preparation/collection adapter tested; numerical outcome pending.
This is a local frozen-SSE diagnostic, not a new hierarchy/admission policy,
meaning rewrite or prompt experiment. The selected group and outsiders stay fixed.

Compare three views of each original meaning in a saved reference group:

1. Pool the entire meaning in its original `title + "\n\n" + meaning` context.
2. Pool only the prefix preceding the exact `, including but not limited to `
   suffix, leaving that suffix in the encoder context.
3. Pool that identical prefix in a context with the suffix removed.

Meanings without that explicit optional suffix are unchanged controls. Other
forms of inclusion are not shortened. Original meanings, IDs, note identities,
accepted memberships and historical vectors are preserved. This narrow text
operation is a diagnostic intervention, not a generally valid meaning-cleaning
rule. It does not remove purposes, states, restrictive clauses or alternatives.

[meaning_example_probe.py](../meaning_example_probe.py) reads the saved group
and source plan directly, deduplicates exact context/span requests, pins source
hashes, and prepares the existing native
[worker.py](../worker.py). It adds no inference implementation or provider path.
The worker retains the source model descriptor, checkpoint, base artifact,
contextual pooling, dimensions, device and batching. Collection validates the
native receipt, raw vector hash, source identities and row bindings, then saves
three normalized arrays with the original group-member order. Changed sources
or incompatible existing results fail rather than silently overwriting evidence.

Run from the isolated task worktree. Preparation and collection are offline;
the middle command uses the existing CPU SSE worker and its pinned environment:

```bash
python -m sse_multivector.meaning_example_probe prepare \
  <completed-study> <new-probe-directory> \
  --root <saved-root-id> --group <saved-group-id>
python -m sse_multivector.worker <new-probe-directory>/worker-config.json
python -m sse_multivector.meaning_example_probe collect <new-probe-directory>
```

Use original full-meaning replay to validate numerical compatibility before
interpreting differences. Hold groups, outsider meanings, semantic review labels
and the admission algorithm fixed when inspecting scores and consistently
recomputed boundaries. This is a post-result mechanism test using already
reviewed HR38 cases, not another held-out accuracy estimate. No LLMs, training,
paid resources, hierarchy changes or prompt changes are involved.
