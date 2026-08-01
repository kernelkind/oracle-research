# Isolated Codex generation runner

`codex_exec.py` runs the takeaway and mask prompts through subscription-authenticated
`codex exec`. It is intended for batches larger than the manually orchestrated
32-note experiment.

The runner does not choose a model. Takeaway and mask model IDs and reasoning
efforts are required in every run configuration. This lets us compare configurations
without changing code or silently falling back to another model.

## One-time login

The runner never uses the normal `~/.codex` home. Authenticate the dedicated home
once:

```sh
python3 sse_multivector/codex_exec.py login \
  --codex-home ~/.local/state/oracle-mvp/codex-home
```

The directory is required to have mode `0700`. Login credentials are stored there
as `auth.json`, which Codex creates with mode `0600`, and must never be placed
inside the repository. The runner refuses to start generation if that file is
missing or has any other permission mode.

## Input

```json
{
  "schema_version": 1,
  "notes": [
    {
      "note_id": "a stable note identifier",
      "text": "The complete canonical note text."
    }
  ]
}
```

## Run configuration

Paths may be absolute or relative to the configuration file.

```json
{
  "schema_version": 1,
  "codex_binary": "codex",
  "codex_home": "~/.local/state/oracle-mvp/codex-home",
  "input_path": "notes.json",
  "run_directory": "run-model-probe-1",
  "takeaway": {
    "prompt_registry_path": "sse_multivector/takeaway-prompt-versions.json",
    "prompt_version": "TPv3.81",
    "model": "replace-with-model-id",
    "reasoning_effort": "replace-with-effort"
  },
  "mask": {
    "prompt_registry_path": "sse_multivector/mask-prompt-versions.json",
    "prompt_version": "MP3.2",
    "model": "replace-with-model-id",
    "reasoning_effort": "replace-with-effort"
  }
}
```

Run it with:

```sh
python3 sse_multivector/codex_exec.py run path/to/config.json
```

Each note receives one fresh takeaway process. Each resulting takeaway receives one
fresh mask process containing only its source note, fixed takeaway, and frozen mask
prompt. No Codex conversation is resumed or shared.

## Isolation

Every generation uses:

- the dedicated `CODEX_HOME`;
- a new empty working directory outside the repository;
- an ephemeral session;
- ignored user configuration and execution rules;
- a one-line replacement for Codex's built-in coding-agent instructions;
- disabled Codex agent orchestration, plus suppressed permissions, apps,
  collaboration, skills, and environment-context instruction blocks;
- read-only sandboxing with approvals disabled;
- disabled shell, multi-agent, apps, plugins, browser, computer-use, image, and web
  search tools;
- a subprocess environment with inherited `CODEX_*`, `OPENAI_*`, and `CHATGPT_*`
  variables removed.

The note is still untrusted model input. The isolation contract prevents it from
turning the generation job into a general Codex tool-using session.

## Results and resume behavior

The run directory contains:

- `manifest.json`: exact input, prompt, schema, model, effort, Codex-version, and
  wrapper hashes;
- `model-instructions.md`: the exact minimal replacement for Codex's built-in
  coding-agent instructions;
- `results.jsonl`: one auditable success or failure record per attempt, including
  token usage, duration, event stream, stderr, and raw final output;
- `output.json`: published atomically only after every takeaway and mask job
  succeeds.

Completed jobs are reused when the same command is run again. Failed jobs are not
retried automatically. After inspecting the failure, explicitly create a new
recorded attempt with:

```sh
python3 sse_multivector/codex_exec.py run path/to/config.json --retry-failed
```

Changing an input, prompt, model, effort, Codex version, or wrapper implementation
requires a new run directory. This prevents results from different experiments from
being mixed.

Running the command consumes Codex subscription allowance. The implementation and
tests use a fake executable and make no real model calls.
