# TRUE02 — Every frozen holdout decision

Each row asks **A contains B?** B is the premise; A is the hypothesis. All inputs use the unchanged TRUE01 topic sentence wrapper.

Native answers are complete greedy labels with EOS required. Score is full-vocabulary probability of the first output token being `1`, not calibrated category confidence. The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.

| ID | A | B | Expected | Native | Score | Cutoff |
|---|---|---|---|---|---|---|
| F1-contains-F2 | Bread | Sourdough bread | Yes | Yes | 0.863123 | Yes |
| F1-contains-F3 | Bread | Gluten-free food | No | No | 0.008023 | No |
| F1-contains-F4 | Bread | Gluten-free bread | Yes | Yes | 0.796678 | Yes |
| F1-contains-F5 | Bread | Bread made without gluten | Yes | Yes | 0.959889 | Yes |
| F1-contains-F6 | Bread | Bread baking | Yes | Yes | 0.928326 | Yes |
| F2-contains-F1 | Sourdough bread | Bread | No | No | 0.006518 | No |
| F2-contains-F3 | Sourdough bread | Gluten-free food | No | No | 0.000445 | No |
| F2-contains-F4 | Sourdough bread | Gluten-free bread | No | No | 0.001220 | No |
| F2-contains-F5 | Sourdough bread | Bread made without gluten | No | No | 0.002622 | No |
| F2-contains-F6 | Sourdough bread | Bread baking | No | No | 0.006361 | No |
| F3-contains-F1 | Gluten-free food | Bread | No | No | 0.001926 | No |
| F3-contains-F2 | Gluten-free food | Sourdough bread | No | No | 0.006725 | No |
| F3-contains-F4 | Gluten-free food | Gluten-free bread | Yes | Yes | 0.868542 | Yes |
| F3-contains-F5 | Gluten-free food | Bread made without gluten | Yes | Yes | 0.740384 | Yes |
| F3-contains-F6 | Gluten-free food | Bread baking | No | No | 0.000724 | No |
| F4-contains-F1 | Gluten-free bread | Bread | No | No | 0.003915 | No |
| F4-contains-F2 | Gluten-free bread | Sourdough bread | No | No | 0.003117 | No |
| F4-contains-F3 | Gluten-free bread | Gluten-free food | No | No | 0.047346 | No |
| F4-contains-F5 | Gluten-free bread | Bread made without gluten | Yes | Yes | 0.971428 | Yes |
| F4-contains-F6 | Gluten-free bread | Bread baking | No | No | 0.002974 | No |
| F5-contains-F1 | Bread made without gluten | Bread | No | No | 0.002163 | No |
| F5-contains-F2 | Bread made without gluten | Sourdough bread | No | No | 0.004722 | No |
| F5-contains-F3 | Bread made without gluten | Gluten-free food | No | No | 0.031765 | No |
| F5-contains-F4 | Bread made without gluten | Gluten-free bread | Yes | Yes | 0.954654 | Yes |
| F5-contains-F6 | Bread made without gluten | Bread baking | No | No | 0.001272 | No |
| F6-contains-F1 | Bread baking | Bread | No | No | 0.027619 | No |
| F6-contains-F2 | Bread baking | Sourdough bread | No | Yes | 0.538085 | Yes |
| F6-contains-F3 | Bread baking | Gluten-free food | No | No | 0.001348 | No |
| F6-contains-F4 | Bread baking | Gluten-free bread | No | No | 0.178456 | Yes |
| F6-contains-F5 | Bread baking | Bread made without gluten | No | Yes | 0.509176 | Yes |
| S1-contains-S2 | Software testing | Testing web applications | Yes | No | 0.357971 | Yes |
| S1-contains-S3 | Software testing | Software security testing | Yes | Yes | 0.823308 | Yes |
| S1-contains-S4 | Software testing | Security testing of web applications | Yes | No | 0.157464 | Yes |
| S1-contains-S5 | Software testing | Testing the security of web applications | Yes | No | 0.357694 | Yes |
| S1-contains-S6 | Software testing | Automated software testing | Yes | Yes | 0.709454 | Yes |
| S2-contains-S1 | Testing web applications | Software testing | No | No | 0.014899 | No |
| S2-contains-S3 | Testing web applications | Software security testing | No | No | 0.016933 | No |
| S2-contains-S4 | Testing web applications | Security testing of web applications | Yes | Yes | 0.780689 | Yes |
| S2-contains-S5 | Testing web applications | Testing the security of web applications | Yes | Yes | 0.892745 | Yes |
| S2-contains-S6 | Testing web applications | Automated software testing | No | No | 0.014295 | No |
| S3-contains-S1 | Software security testing | Software testing | No | No | 0.009033 | No |
| S3-contains-S2 | Software security testing | Testing web applications | No | No | 0.004838 | No |
| S3-contains-S4 | Software security testing | Security testing of web applications | Yes | No | 0.394946 | Yes |
| S3-contains-S5 | Software security testing | Testing the security of web applications | Yes | No | 0.441740 | Yes |
| S3-contains-S6 | Software security testing | Automated software testing | No | No | 0.009697 | No |
| S4-contains-S1 | Security testing of web applications | Software testing | No | No | 0.003365 | No |
| S4-contains-S2 | Security testing of web applications | Testing web applications | No | No | 0.006883 | No |
| S4-contains-S3 | Security testing of web applications | Software security testing | No | No | 0.016412 | No |
| S4-contains-S5 | Security testing of web applications | Testing the security of web applications | Yes | Yes | 0.995652 | Yes |
| S4-contains-S6 | Security testing of web applications | Automated software testing | No | No | 0.002810 | No |
| S5-contains-S1 | Testing the security of web applications | Software testing | No | No | 0.003741 | No |
| S5-contains-S2 | Testing the security of web applications | Testing web applications | No | No | 0.003027 | No |
| S5-contains-S3 | Testing the security of web applications | Software security testing | No | No | 0.037221 | No |
| S5-contains-S4 | Testing the security of web applications | Security testing of web applications | Yes | Yes | 0.995426 | Yes |
| S5-contains-S6 | Testing the security of web applications | Automated software testing | No | No | 0.004305 | No |
| S6-contains-S1 | Automated software testing | Software testing | No | No | 0.011937 | No |
| S6-contains-S2 | Automated software testing | Testing web applications | No | No | 0.008357 | No |
| S6-contains-S3 | Automated software testing | Software security testing | No | No | 0.010632 | No |
| S6-contains-S4 | Automated software testing | Security testing of web applications | No | No | 0.006970 | No |
| S6-contains-S5 | Automated software testing | Testing the security of web applications | No | No | 0.008034 | No |
| E1-contains-E2 | Taxes | Taxes on corporate profits | Yes | Yes | 0.973949 | Yes |
| E1-contains-E3 | Taxes | Environmental policy | No | No | 0.000580 | No |
| E1-contains-E4 | Taxes | Carbon taxes | Yes | Yes | 0.553967 | Yes |
| E1-contains-E5 | Taxes | Taxes on carbon emissions | Yes | Yes | 0.953095 | Yes |
| E1-contains-E6 | Taxes | Carbon emissions trading | No | No | 0.001263 | No |
| E2-contains-E1 | Taxes on corporate profits | Taxes | No | No | 0.003078 | No |
| E2-contains-E3 | Taxes on corporate profits | Environmental policy | No | No | 0.000332 | No |
| E2-contains-E4 | Taxes on corporate profits | Carbon taxes | No | No | 0.001283 | No |
| E2-contains-E5 | Taxes on corporate profits | Taxes on carbon emissions | No | No | 0.000622 | No |
| E2-contains-E6 | Taxes on corporate profits | Carbon emissions trading | No | No | 0.000240 | No |
| E3-contains-E1 | Environmental policy | Taxes | No | No | 0.000391 | No |
| E3-contains-E2 | Environmental policy | Taxes on corporate profits | No | No | 0.000599 | No |
| E3-contains-E4 | Environmental policy | Carbon taxes | Yes | No | 0.252924 | Yes |
| E3-contains-E5 | Environmental policy | Taxes on carbon emissions | Yes | No | 0.239187 | Yes |
| E3-contains-E6 | Environmental policy | Carbon emissions trading | Yes | No | 0.193878 | Yes |
| E4-contains-E1 | Carbon taxes | Taxes | No | No | 0.005767 | No |
| E4-contains-E2 | Carbon taxes | Taxes on corporate profits | No | No | 0.001416 | No |
| E4-contains-E3 | Carbon taxes | Environmental policy | No | No | 0.004814 | No |
| E4-contains-E5 | Carbon taxes | Taxes on carbon emissions | Yes | Yes | 0.977043 | Yes |
| E4-contains-E6 | Carbon taxes | Carbon emissions trading | No | No | 0.013346 | No |
| E5-contains-E1 | Taxes on carbon emissions | Taxes | No | No | 0.002715 | No |
| E5-contains-E2 | Taxes on carbon emissions | Taxes on corporate profits | No | No | 0.000443 | No |
| E5-contains-E3 | Taxes on carbon emissions | Environmental policy | No | No | 0.002509 | No |
| E5-contains-E4 | Taxes on carbon emissions | Carbon taxes | Yes | Yes | 0.911335 | Yes |
| E5-contains-E6 | Taxes on carbon emissions | Carbon emissions trading | No | No | 0.008175 | No |
| E6-contains-E1 | Carbon emissions trading | Taxes | No | No | 0.000383 | No |
| E6-contains-E2 | Carbon emissions trading | Taxes on corporate profits | No | No | 0.000429 | No |
| E6-contains-E3 | Carbon emissions trading | Environmental policy | No | No | 0.002360 | No |
| E6-contains-E4 | Carbon emissions trading | Carbon taxes | No | No | 0.002229 | No |
| E6-contains-E5 | Carbon emissions trading | Taxes on carbon emissions | No | No | 0.003998 | No |
| P1-contains-P2 | Political campaigning | Election fundraising | Yes | No | 0.292186 | Yes |
| P1-contains-P3 | Political campaigning | Online political campaigning | Yes | Yes | 0.534411 | Yes |
| P1-contains-P4 | Political campaigning | Online fundraising for election campaigns | Yes | Yes | 0.516954 | Yes |
| P1-contains-P5 | Political campaigning | Raising money online for election campaigns | Yes | Yes | 0.619948 | Yes |
| P1-contains-P6 | Political campaigning | Door-to-door election canvassing | Yes | Yes | 0.777410 | Yes |
| P2-contains-P1 | Election fundraising | Political campaigning | No | No | 0.019411 | No |
| P2-contains-P3 | Election fundraising | Online political campaigning | No | No | 0.012703 | No |
| P2-contains-P4 | Election fundraising | Online fundraising for election campaigns | Yes | Yes | 0.903569 | Yes |
| P2-contains-P5 | Election fundraising | Raising money online for election campaigns | Yes | Yes | 0.926785 | Yes |
| P2-contains-P6 | Election fundraising | Door-to-door election canvassing | No | No | 0.087392 | No |
| P3-contains-P1 | Online political campaigning | Political campaigning | No | No | 0.007539 | No |
| P3-contains-P2 | Online political campaigning | Election fundraising | No | No | 0.006723 | No |
| P3-contains-P4 | Online political campaigning | Online fundraising for election campaigns | Yes | Yes | 0.520837 | Yes |
| P3-contains-P5 | Online political campaigning | Raising money online for election campaigns | Yes | No | 0.495679 | Yes |
| P3-contains-P6 | Online political campaigning | Door-to-door election canvassing | No | No | 0.000864 | No |
| P4-contains-P1 | Online fundraising for election campaigns | Political campaigning | No | No | 0.001616 | No |
| P4-contains-P2 | Online fundraising for election campaigns | Election fundraising | No | No | 0.012794 | No |
| P4-contains-P3 | Online fundraising for election campaigns | Online political campaigning | No | No | 0.013439 | No |
| P4-contains-P5 | Online fundraising for election campaigns | Raising money online for election campaigns | Yes | Yes | 0.987197 | Yes |
| P4-contains-P6 | Online fundraising for election campaigns | Door-to-door election canvassing | No | No | 0.000317 | No |
| P5-contains-P1 | Raising money online for election campaigns | Political campaigning | No | No | 0.002076 | No |
| P5-contains-P2 | Raising money online for election campaigns | Election fundraising | No | No | 0.016494 | No |
| P5-contains-P3 | Raising money online for election campaigns | Online political campaigning | No | No | 0.009832 | No |
| P5-contains-P4 | Raising money online for election campaigns | Online fundraising for election campaigns | Yes | Yes | 0.988963 | Yes |
| P5-contains-P6 | Raising money online for election campaigns | Door-to-door election canvassing | No | No | 0.000228 | No |
| P6-contains-P1 | Door-to-door election canvassing | Political campaigning | No | No | 0.008381 | No |
| P6-contains-P2 | Door-to-door election canvassing | Election fundraising | No | No | 0.000832 | No |
| P6-contains-P3 | Door-to-door election canvassing | Online political campaigning | No | No | 0.000417 | No |
| P6-contains-P4 | Door-to-door election canvassing | Online fundraising for election campaigns | No | No | 0.000199 | No |
| P6-contains-P5 | Door-to-door election canvassing | Raising money online for election campaigns | No | No | 0.000196 | No |
| R1-contains-R2 | Friendship | Friendships between coworkers | Yes | Yes | 0.903120 | Yes |
| R1-contains-R3 | Friendship | Workplace relationships | No | No | 0.001379 | No |
| R1-contains-R4 | Friendship | Mentoring at work | No | No | 0.002200 | No |
| R1-contains-R5 | Friendship | Workplace mentoring | No | No | 0.001604 | No |
| R1-contains-R6 | Friendship | Long-distance friendships | Yes | Yes | 0.694237 | Yes |
| R2-contains-R1 | Friendships between coworkers | Friendship | No | No | 0.004490 | No |
| R2-contains-R3 | Friendships between coworkers | Workplace relationships | No | No | 0.036581 | No |
| R2-contains-R4 | Friendships between coworkers | Mentoring at work | No | No | 0.005944 | No |
| R2-contains-R5 | Friendships between coworkers | Workplace mentoring | No | No | 0.006839 | No |
| R2-contains-R6 | Friendships between coworkers | Long-distance friendships | No | No | 0.000775 | No |
| R3-contains-R1 | Workplace relationships | Friendship | No | No | 0.000820 | No |
| R3-contains-R2 | Workplace relationships | Friendships between coworkers | Yes | Yes | 0.560847 | Yes |
| R3-contains-R4 | Workplace relationships | Mentoring at work | Yes | Yes | 0.506243 | Yes |
| R3-contains-R5 | Workplace relationships | Workplace mentoring | Yes | No | 0.466535 | Yes |
| R3-contains-R6 | Workplace relationships | Long-distance friendships | No | No | 0.000514 | No |
| R4-contains-R1 | Mentoring at work | Friendship | No | No | 0.000662 | No |
| R4-contains-R2 | Mentoring at work | Friendships between coworkers | No | No | 0.007882 | No |
| R4-contains-R3 | Mentoring at work | Workplace relationships | No | No | 0.010197 | No |
| R4-contains-R5 | Mentoring at work | Workplace mentoring | Yes | Yes | 0.985006 | Yes |
| R4-contains-R6 | Mentoring at work | Long-distance friendships | No | No | 0.000502 | No |
| R5-contains-R1 | Workplace mentoring | Friendship | No | No | 0.001022 | No |
| R5-contains-R2 | Workplace mentoring | Friendships between coworkers | No | No | 0.009673 | No |
| R5-contains-R3 | Workplace mentoring | Workplace relationships | No | No | 0.013724 | No |
| R5-contains-R4 | Workplace mentoring | Mentoring at work | Yes | Yes | 0.954510 | Yes |
| R5-contains-R6 | Workplace mentoring | Long-distance friendships | No | No | 0.000571 | No |
| R6-contains-R1 | Long-distance friendships | Friendship | No | No | 0.003443 | No |
| R6-contains-R2 | Long-distance friendships | Friendships between coworkers | No | No | 0.000906 | No |
| R6-contains-R3 | Long-distance friendships | Workplace relationships | No | No | 0.000324 | No |
| R6-contains-R4 | Long-distance friendships | Mentoring at work | No | No | 0.000526 | No |
| R6-contains-R5 | Long-distance friendships | Workplace mentoring | No | No | 0.000430 | No |

## Native errors (13)

- F6-contains-F2: expected No; got Yes; score 0.538085.
- F6-contains-F5: expected No; got Yes; score 0.509176.
- S1-contains-S2: expected Yes; got No; score 0.357971.
- S1-contains-S4: expected Yes; got No; score 0.157464.
- S1-contains-S5: expected Yes; got No; score 0.357694.
- S3-contains-S4: expected Yes; got No; score 0.394946.
- S3-contains-S5: expected Yes; got No; score 0.441740.
- E3-contains-E4: expected Yes; got No; score 0.252924.
- E3-contains-E5: expected Yes; got No; score 0.239187.
- E3-contains-E6: expected Yes; got No; score 0.193878.
- P1-contains-P2: expected Yes; got No; score 0.292186.
- P3-contains-P5: expected Yes; got No; score 0.495679.
- R3-contains-R5: expected Yes; got No; score 0.466535.

## Cutoff errors (3)

- F6-contains-F2: expected No; got Yes; score 0.538085.
- F6-contains-F4: expected No; got Yes; score 0.178456.
- F6-contains-F5: expected No; got Yes; score 0.509176.
