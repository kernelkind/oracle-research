# Scope examples: no observed change

Two calls used the unchanged baseline instructions plus two synthetic examples. Both masks are identical to the baseline and the direct-instruction revision. No broader calls were run.

The user resolved the reopened M05 judgment: “my would add unwanted meaning.” [The decision history](../m05-scope-review/correction.json) applies to every identical output. The examples have not demonstrated an improvement: one mask is accepted and one has a scope error.

## M05

Subject: A call for Salvadorans to make their presence known.

> ⟦Where are all
> My Salvadorans at?⟧
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Analysis: Identical to baseline and scope-v1. “My” adds affinity beyond the supplied call-for-presence subject. The user confirmed this is unwanted meaning; the mask fails the scope requirement.

## M06

Subject: The poster's expressed affinity with Salvadorans.

> Where are all
> ⟦My Salvadorans⟧ at?
> https://blossom.primal.net/2b5ac7389e0863fcc843a67abf667a024f4e8f79310cbe048a3e3141bfecedca.jpg

Analysis: My Salvadorans captures the requested affinity and its addressees.

Both calls returned exact fragments in source order, with unique placements and separate fresh threads/workdirs. No tool calls occurred. Usage: 5,074 input tokens and 24 output tokens; 1,920 cached input tokens are included in the input total.

Raw outputs, settings, timing and resource records are in `probe/`. These two masks do not establish a general success rate or any SSE result.
