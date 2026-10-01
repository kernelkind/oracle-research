# Saved posts in prompt experiments

Use `experiment.py` with `dataset.adapter: "posts"` to read an existing
`{"schema_version":1,"notes":[...]}` extraction file directly. Each note supplies
`note_id` and complete `text`; only the text fills `{POST}`. Saved subjects and
masks are not model inputs. Review evidence retains the post, ID and origin.

The case ID is `origin.prompt_id` when present, otherwise `note_id`. Duplicate
post IDs or case IDs are rejected. Optional `dataset.select` names case IDs;
unknown selections are rejected. The existing workflow hashes the source and
freezes exact rendered prompts, settings and schema.

Historical imports still require every saved job to match the rendered input
exactly. `experiment_specs/asv6.48-hr01-subjects-baseline-v1.json` describes the
88 saved Astra jobs in `hierarchy-refresh-v1/subject-config.json`; the other
twelve corpus notes came from separate historical runs. Importing is read-only,
not permission to run Astra. Prepare a candidate from the import with `--only`
and explicit model overrides to reuse inputs and baseline outputs without
regenerating them. This does not make the baseline ground truth.
