# PPv10 mixed-note follow-up

PPv10 remains unchanged. `plan.json` records selection and expectations before
inference. The previous study's offline renderer and receipt collector are reused
without modifying them; inference goes through the canonical saved batch runner.
No subject descriptions or assessment labels enter the model input.

Prepare once (refuses to overwrite evidence):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
PYTHONPATH=sse_multivector/prominence-prompt-goal-v1/ppv10-ranking-v1 \
python3 -c 'import study; study.ROOT = study.ROOT.parent / "ppv10-mixed-notes-v1"; study.prepare()'
```

Run or resume the saved batch:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/extraction_pipeline.py prompt \
  sse_multivector/prominence-prompt-goal-v1/ppv10-mixed-notes-v1/config.json
```

Collect once (validates pinned inputs and actual receipts):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
PYTHONPATH=sse_multivector/prominence-prompt-goal-v1/ppv10-ranking-v1 \
python3 -c 'import study; study.ROOT = study.ROOT.parent / "ppv10-mixed-notes-v1"; study.collect()'
```

`results.json` contains automatically collected measurements. `assessment.md`
contains the assistant's separate interpretation, not model-generated rationale
or user-approved correctness labels.
