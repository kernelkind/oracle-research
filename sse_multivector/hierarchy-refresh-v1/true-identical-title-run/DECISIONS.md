# HRv1-identical-titles — Every frozen title decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

No answer key is attached; these are model verdicts, not measured accuracy.

| ID | A | B | Native | Score | Cutoff |
|---|---|---|---|---|---|
| S1fe681cb8e-contains-S8e972c2c30 | Bitcoin | Bitcoin | Yes | 0.985914 | Yes |
| S3fc1daec3e-contains-Sb5cc79557f | Nostr decentralized communication protocol | Nostr decentralized communication protocol | Yes | 0.989958 | Yes |
| S64fcf6c1d7-contains-S54b2843dd5 | Coffee | Coffee | Yes | 0.985560 | Yes |
