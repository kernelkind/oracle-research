# ASv6.84 general-heading permission clarification

Status: tested, confirmed failures; not adopted. ASv6.81 N096 trial 1 drops the named
recipe's easy/never-fail/serving-five restrictions from its complete sautéing
subject, and N100 trial 2 loses the enclosing sirloin source in the full trim.
These native saved answers are the production-path failing behavior.

ASv6.84 changes only R23's permission that a heading need not retell the post:
a broader heading can omit instance details, while the complete particular
subject retains them in its own heading. This resolves a possible instruction
interpretation; it does not prove that interpretation caused the observed
answers. The existing source-retention and level-of-generality rules already
require this distinction. C1's Salt versus Salt for food seasoning and its
counted complete ingredient/action subjects demonstrate it. All seven examples,
other clauses, five implications, schema and POST template stay unchanged from
ASv6.81. ASv6.83's collection edit is excluded to isolate this sentence.

## Frozen comparison before generation

Run N063/N074/N096/N100 in three fresh medium trials, inheriting exact native
same-trial ASv6.81 inputs, evidence, settings and saved outputs: twelve calls.
Use the unchanged bounded source, scope and compatible-copy criteria, recording
every answer with output-bound native agent reviews. Preserve uncertainties,
accept equivalent wording and exclude optional hierarchy/recorded ambiguities.
No quality reruns or early stopping. Extend the existing selection ordering to
this exact candidate only after all twelve answers are reviewed. If selected,
complete the same thirty minimized/repair checks before fresh validation.

Use subscription gpt-6.1-sol medium, WebSocket, timeout 1,800 seconds, no output
cap or paid fallback, native persistent history and 2,000 budget. Concurrency
is one per runner and six overall, waiting for active screens to free capacity.
Count every failure; only explicit provider-transient failures may retry once.
Together with the previously frozen 916 attempts, this adds twelve to reach
928; a selected-candidate regression would add thirty to reach 958 before the
48 fresh validation calls. No fresh validation answer has been generated or
inspected, and no production candidate is adopted.

## Completed screen, including the transport failure

All twelve first attempts are recorded: eleven valid answers and one failed
request, with no retries or reuse. Every valid answer has a current output-bound
native agent review: six accepts, four rejects and one uncertainty under the
unchanged bounded checks. The N100 trial-1 request ends with WebSocket closure
1011 before a terminal response; the native failure kind is `unknown`, so it
is preserved without retry. Its partial stream is not judged as a completed
answer or used to revise the prompt.

| Case | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| N063 | accept | uncertain | accept |
| N074 | accept | accept | accept |
| N096 | reject | reject | accept |
| N100 | request failed | reject | reject |

N096 trial 1 loses the enclosing recipe qualifications and compatible material
copies; trial 2 retains the full action but omits it below returned dish
occurrences 2.1/2.2.1. Trial 3 passes the bounded sauté/pair checks. Both valid
N100 answers omit the full joint trim. N063 trial 2 retains all fifteen members
under a role group without an explicit tuple; the frozen alternative-group
exclusion makes that uncertain rather than a confirmed failure.

This screen does not displace ASv6.81's complete 8/12 original screen. It has
the same four confirmed failures plus an uncertainty and unavailable answer;
neither the general-heading wording nor its hypothesized reading conflict is
established as a reliable correction or unique internal cause.
