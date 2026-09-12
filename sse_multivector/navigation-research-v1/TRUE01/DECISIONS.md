# TRUE01 — Every category decision

Each row asks **A contains B?** In other words: does belonging to B warrant belonging to A?

Expected answers were recorded before inference. Scores in parentheses are the probability of the first output token being `1`, not cosine, complete-label probability, or calibrated category confidence. Answers come from complete native greedy output with EOS, not a score cutoff. “Topic sentence” uses `This text is about …`; “Bare text” uses the unchanged category strings. Both are inside the released `premise: … hypothesis: …` format, with B as premise.

| ID | A | B | Expected | Topic sentence | Bare text |
|---|---|---|---|---|---|
| F02-w1-forward | Fermented foods | Yogurt made with live cultures | Yes | No (0.391975) | No (0.268394) |
| F02-w1-reverse | Yogurt made with live cultures | Fermented foods | No | No (0.004501) | No (0.012795) |
| F02-w1-alternative | Roasted foods | Yogurt made with live cultures | No | No (0.000311) | No (0.001476) |
| F02-w1-alternative-reverse | Yogurt made with live cultures | Roasted foods | No | No (0.000469) | No (0.002195) |
| F02-w2-forward | Foods produced through fermentation | Milk fermented into yogurt using live bacteria | Yes | Yes (0.725585) | Yes (0.892174) |
| F02-w2-reverse | Milk fermented into yogurt using live bacteria | Foods produced through fermentation | No | No (0.006244) | No (0.012078) |
| F02-w2-alternative | Foods cooked by roasting | Milk fermented into yogurt using live bacteria | No | No (0.000886) | No (0.001899) |
| F02-w2-alternative-reverse | Milk fermented into yogurt using live bacteria | Foods cooked by roasting | No | No (0.000234) | No (0.002438) |
| F06-w1-forward | Vegetarian meals | Lentil stew made entirely from plant ingredients | Yes | No (0.434810) | No (0.458776) |
| F06-w1-reverse | Lentil stew made entirely from plant ingredients | Vegetarian meals | No | No (0.040109) | No (0.058855) |
| F06-w1-alternative | Meat dishes | Lentil stew made entirely from plant ingredients | No | No (0.000855) | No (0.000850) |
| F06-w1-alternative-reverse | Lentil stew made entirely from plant ingredients | Meat dishes | No | No (0.000163) | No (0.000405) |
| F06-w2-forward | Meals without meat or fish | A lentil stew made entirely from plant ingredients | Yes | No (0.458879) | Yes (0.511558) |
| F06-w2-reverse | A lentil stew made entirely from plant ingredients | Meals without meat or fish | No | No (0.006572) | No (0.013812) |
| F06-w2-alternative | Dishes containing meat | A lentil stew made entirely from plant ingredients | No | No (0.000367) | No (0.000779) |
| F06-w2-alternative-reverse | A lentil stew made entirely from plant ingredients | Dishes containing meat | No | No (0.000179) | No (0.000453) |
| S03-w1-forward | Open-source software | Programs released under the GNU General Public License | Yes | Yes (0.671306) | Yes (0.649335) |
| S03-w1-reverse | Programs released under the GNU General Public License | Open-source software | No | No (0.039221) | No (0.032225) |
| S03-w1-alternative | Closed-source software | Programs released under the GNU General Public License | No | No (0.000801) | No (0.000457) |
| S03-w1-alternative-reverse | Programs released under the GNU General Public License | Closed-source software | No | No (0.000537) | No (0.001472) |
| S03-w2-forward | Software whose source code users may inspect, modify, and redistribute | Software distributed under the GPL | Yes | No (0.144155) | No (0.048672) |
| S03-w2-reverse | Software distributed under the GPL | Software whose source code users may inspect, modify, and redistribute | No | No (0.098581) | No (0.048849) |
| S03-w2-alternative | Software with source code withheld from users | Software distributed under the GPL | No | No (0.000590) | No (0.000353) |
| S03-w2-alternative-reverse | Software distributed under the GPL | Software with source code withheld from users | No | No (0.000576) | No (0.001243) |
| S05-w1-forward | Memory safety | Preventing access to freed memory | Yes | Yes (0.752024) | No (0.467457) |
| S05-w1-reverse | Preventing access to freed memory | Memory safety | No | No (0.054204) | No (0.038576) |
| S05-w1-alternative | Memory performance | Preventing access to freed memory | No | No (0.140235) | No (0.031007) |
| S05-w1-alternative-reverse | Preventing access to freed memory | Memory performance | No | No (0.002445) | No (0.001246) |
| S05-w2-forward | Safe use of computer memory | Preventing a program from using memory after it has been freed | Yes | Yes (0.509001) | No (0.203902) |
| S05-w2-reverse | Preventing a program from using memory after it has been freed | Safe use of computer memory | No | No (0.007740) | No (0.004090) |
| S05-w2-alternative | The speed and efficiency of computer memory use | Preventing a program from using memory after it has been freed | No | No (0.015232) | No (0.011363) |
| S05-w2-alternative-reverse | Preventing a program from using memory after it has been freed | The speed and efficiency of computer memory use | No | No (0.000905) | No (0.001163) |
| E02-w1-forward | Monetary policy | A central bank raising interest rates | Yes | No (0.445237) | Yes (0.500502) |
| E02-w1-reverse | A central bank raising interest rates | Monetary policy | No | No (0.003236) | No (0.002549) |
| E02-w1-alternative | Fiscal policy | A central bank raising interest rates | No | No (0.018869) | No (0.011137) |
| E02-w1-alternative-reverse | A central bank raising interest rates | Fiscal policy | No | No (0.000980) | No (0.000842) |
| E02-w2-forward | Central-bank management of money and borrowing conditions | An increase in policy interest rates by the central bank | Yes | Yes (0.578411) | No (0.469192) |
| E02-w2-reverse | An increase in policy interest rates by the central bank | Central-bank management of money and borrowing conditions | No | No (0.003140) | No (0.002928) |
| E02-w2-alternative | Government decisions about taxation and spending | An increase in policy interest rates by the central bank | No | No (0.000664) | No (0.001473) |
| E02-w2-alternative-reverse | An increase in policy interest rates by the central bank | Government decisions about taxation and spending | No | No (0.000292) | No (0.000648) |
| E06-w1-forward | Market competition | Businesses competing by lowering prices | Yes | Yes (0.597608) | No (0.446741) |
| E06-w1-reverse | Businesses competing by lowering prices | Market competition | No | No (0.001928) | No (0.001564) |
| E06-w1-alternative | Price collusion | Businesses competing by lowering prices | No | No (0.094988) | No (0.006979) |
| E06-w1-alternative-reverse | Businesses competing by lowering prices | Price collusion | No | No (0.015004) | No (0.009415) |
| E06-w2-forward | Rivalry between sellers | Sellers undercutting each other's prices | Yes | Yes (0.642473) | No (0.498149) |
| E06-w2-reverse | Sellers undercutting each other's prices | Rivalry between sellers | No | No (0.009199) | No (0.009406) |
| E06-w2-alternative | Coordination between sellers to fix prices | Sellers undercutting each other's prices | No | No (0.003641) | No (0.002059) |
| E06-w2-alternative-reverse | Sellers undercutting each other's prices | Coordination between sellers to fix prices | No | No (0.001576) | No (0.002912) |
| P01-w1-forward | Freedom of expression | The right to criticize the government | Yes | No (0.376392) | No (0.445877) |
| P01-w1-reverse | The right to criticize the government | Freedom of expression | No | No (0.021086) | No (0.011260) |
| P01-w1-alternative | Freedom of movement | The right to criticize the government | No | No (0.001279) | No (0.003412) |
| P01-w1-alternative-reverse | The right to criticize the government | Freedom of movement | No | No (0.000903) | No (0.000887) |
| P01-w2-forward | Freedom to voice opinions | Being free to speak against government policies | Yes | Yes (0.859314) | Yes (0.778918) |
| P01-w2-reverse | Being free to speak against government policies | Freedom to voice opinions | No | No (0.006482) | No (0.005643) |
| P01-w2-alternative | Freedom to travel and choose where to live | Being free to speak against government policies | No | No (0.000442) | No (0.000868) |
| P01-w2-alternative-reverse | Being free to speak against government policies | Freedom to travel and choose where to live | No | No (0.000622) | No (0.000828) |
| P03-w1-forward | Decentralization of government | Giving local councils more decision-making power instead of the national government | Yes | Yes (0.656283) | No (0.129578) |
| P03-w1-reverse | Giving local councils more decision-making power instead of the national government | Decentralization of government | No | No (0.041161) | No (0.048059) |
| P03-w1-alternative | Electoral representation | Giving local councils more decision-making power instead of the national government | No | No (0.013593) | No (0.011347) |
| P03-w1-alternative-reverse | Giving local councils more decision-making power instead of the national government | Electoral representation | No | No (0.001214) | No (0.001477) |
| P03-w2-forward | Decentralizing government authority | Transferring authority from national leaders to local councils | Yes | Yes (0.914144) | Yes (0.746455) |
| P03-w2-reverse | Transferring authority from national leaders to local councils | Decentralizing government authority | No | No (0.109992) | No (0.138809) |
| P03-w2-alternative | How elected officials represent voters | Transferring authority from national leaders to local councils | No | No (0.006251) | No (0.009558) |
| P03-w2-alternative-reverse | Transferring authority from national leaders to local councils | How elected officials represent voters | No | No (0.000467) | No (0.001261) |
| R02-w1-forward | Respecting personal boundaries | Accepting a friend's refusal to discuss a private matter | Yes | Yes (0.682570) | Yes (0.646557) |
| R02-w1-reverse | Accepting a friend's refusal to discuss a private matter | Respecting personal boundaries | No | No (0.029274) | No (0.074031) |
| R02-w1-alternative | Giving personal advice | Accepting a friend's refusal to discuss a private matter | No | No (0.002077) | No (0.000869) |
| R02-w1-alternative-reverse | Accepting a friend's refusal to discuss a private matter | Giving personal advice | No | No (0.000188) | No (0.000521) |
| R02-w2-forward | Respect for other people's personal limits | Letting a friend keep a sensitive topic private | Yes | Yes (0.540976) | No (0.388025) |
| R02-w2-reverse | Letting a friend keep a sensitive topic private | Respect for other people's personal limits | No | No (0.022919) | No (0.034214) |
| R02-w2-alternative | Offering someone guidance about personal decisions | Letting a friend keep a sensitive topic private | No | No (0.000989) | No (0.000808) |
| R02-w2-alternative-reverse | Letting a friend keep a sensitive topic private | Offering someone guidance about personal decisions | No | No (0.001079) | No (0.002249) |
| R03-w1-forward | Emotional support | Listening compassionately to a grieving friend | Yes | Yes (0.588673) | Yes (0.676361) |
| R03-w1-reverse | Listening compassionately to a grieving friend | Emotional support | No | No (0.014531) | No (0.018131) |
| R03-w1-alternative | Financial support | Listening compassionately to a grieving friend | No | No (0.000911) | No (0.000813) |
| R03-w1-alternative-reverse | Listening compassionately to a grieving friend | Financial support | No | No (0.000403) | No (0.000446) |
| R03-w2-forward | Helping someone cope emotionally | Offering a bereaved friend a sympathetic ear | Yes | Yes (0.775747) | Yes (0.729463) |
| R03-w2-reverse | Offering a bereaved friend a sympathetic ear | Helping someone cope emotionally | No | No (0.045519) | No (0.099325) |
| R03-w2-alternative | Helping someone with money or expenses | Offering a bereaved friend a sympathetic ear | No | No (0.000781) | No (0.002354) |
| R03-w2-alternative-reverse | Offering a bereaved friend a sympathetic ear | Helping someone with money or expenses | No | No (0.000497) | No (0.002352) |
| F02-equivalent-1-2 | Fermented foods | Foods produced through fermentation | Yes | Yes (0.989598) | Yes (0.950123) |
| F02-equivalent-2-1 | Foods produced through fermentation | Fermented foods | Yes | Yes (0.984193) | Yes (0.957280) |
| S05-equivalent-1-2 | Preventing access to freed memory | Preventing a program from using memory after it has been freed | Yes | Yes (0.975220) | Yes (0.972189) |
| S05-equivalent-2-1 | Preventing a program from using memory after it has been freed | Preventing access to freed memory | Yes | No (0.412917) | Yes (0.723546) |
| E02-equivalent-1-2 | Fiscal policy | Government decisions about taxation and spending | Yes | Yes (0.802983) | No (0.296772) |
| E02-equivalent-2-1 | Government decisions about taxation and spending | Fiscal policy | Yes | No (0.168097) | No (0.103767) |
| P03-equivalent-1-2 | Decentralization of government | Decentralizing government authority | Yes | Yes (0.991183) | Yes (0.872645) |
| P03-equivalent-2-1 | Decentralizing government authority | Decentralization of government | Yes | Yes (0.899894) | Yes (0.678423) |
| R03-equivalent-1-2 | Financial support | Helping someone with money or expenses | Yes | Yes (0.947598) | Yes (0.920942) |
| R03-equivalent-2-1 | Helping someone with money or expenses | Financial support | Yes | Yes (0.746392) | Yes (0.736780) |
