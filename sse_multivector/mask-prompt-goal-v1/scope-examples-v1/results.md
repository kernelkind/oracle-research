# Scope examples: no observed change

Two calls used the unchanged baseline instructions plus two synthetic examples. Both masks are identical to the baseline and the direct-instruction revision. No broader calls were run.

M05’s original error judgment has been reopened, not converted into a pass. [The correction](../m05-scope-review/correction.json) applies to every identical output. The examples have not demonstrated an improvement.

## M05

Subject: A call for Salvadorans to make their presence known.

> ⟦Where are all
> My Salvadorans at?⟧
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Analysis: Identical to baseline and scope-v1. The initial rule treated My as extra affinity. A subsequent review found that My also helps express the familiar call; whether retaining it exceeds this fixed subject's scope needs clarification. It is not counted as a pass or a proven failure.

## M06

Subject: The poster's expressed affinity with Salvadorans.

> Where are all
> ⟦My Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Analysis: My Salvadorans captures the requested affinity and its addressees.

Both calls returned exact fragments in source order, with unique placements and separate fresh threads/workdirs. No tool calls occurred. Usage: 5,074 input tokens and 24 output tokens; 1,920 cached input tokens are included in the input total.

Raw outputs, settings, timing and resource records are in `probe/`. These two masks do not establish a general success rate or any SSE result.
