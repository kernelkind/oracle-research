# HRC03 — Complete category descriptions and scores

These are every constructed model input, not original notes or masks. S = software, E = economics, P = political ideas, R = relationships, F = food control. Each ID is one case with two wordings, not two independent cases.

`Angle` is HierarCaps’ broader→narrower score: lower favors that parent. `Cosine` is ordinary similarity between this model’s embeddings: higher means more similar. Neither number is a probability. The intended parent was chosen before scoring. An unexpected ordering is evidence to inspect, not proof that every alternative is semantically invalid.

Direction is checked separately by comparing intended-parent→child with child→intended-parent. It depends on the two vectors’ distances from the empty-string root. Crossed-wording checks vary the three descriptions independently; they are eight combinations of the same case.

Some alternatives admit broader readings: in S04 file organization can include backup workflows; in F03 growing food may include handling the harvest; in S06 wording 2 the description intended to mean application software is not exclusive to it. These cases remain unchanged and their results remain reported. See [Findings](RESULTS.md) for interpretation.

## S01 — Software

Pre-score judgment: Blocking cross-site tracking is a valid topical refinement of Web browser privacy. Web browser appearance is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Blocking cross-site tracking

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Web browser privacy | 114.6285° | 0.860399 |
| Alternative: Web browser appearance | 110.3737° | 0.851995 |

Parent choice: alternative parent; margin -4.2549° (positive favors intended). Direction: intended parent→child 114.6285°, child→intended parent 121.4335°; declared direction favored.

**Wording 2**

Narrower category: Preventing tracking across different websites

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Protecting privacy while browsing the web | 112.9729° | 0.885155 |
| Alternative: How a web browser looks | 125.0467° | 0.797806 |

Parent choice: intended parent; margin 12.0738° (positive favors intended). Direction: intended parent→child 112.9729°, child→intended parent 113.8518°; declared direction favored.

Independent wording combinations favor the intended parent in 4/8 combinations of this same case.

## S02 — Software

Pre-score judgment: verifying downloaded program signatures refines software security, not software usability. Replaced release management because verifying distributed release artifacts can fall under it.

**Wording 1**

Narrower category: Verifying digital signatures on downloaded programs

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Software security | 96.7255° | 0.801275 |
| Alternative: Software usability | 105.9693° | 0.773697 |

Parent choice: intended parent; margin 9.2438° (positive favors intended). Direction: intended parent→child 96.7255°, child→intended parent 144.0032°; declared direction favored.

**Wording 2**

Narrower category: Checking downloaded software's digital signatures

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Keeping software secure | 103.5789° | 0.774074 |
| Alternative: Making software easy to use | 101.2969° | 0.774874 |

Parent choice: alternative parent; margin -2.2820° (positive favors intended). Direction: intended parent→child 103.5789°, child→intended parent 137.2279°; declared direction favored.

Independent wording combinations favor the intended parent in 6/8 combinations of this same case.

## S03 — Software

Pre-score judgment: Programs released under the GNU General Public License is a valid topical refinement of Open-source software. Closed-source software is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Programs released under the GNU General Public License

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Open-source software | 87.9191° | 0.775288 |
| Alternative: Closed-source software | 94.3780° | 0.738588 |

Parent choice: intended parent; margin 6.4590° (positive favors intended). Direction: intended parent→child 87.9191°, child→intended parent 146.5373°; declared direction favored.

**Wording 2**

Narrower category: Software distributed under the GPL

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Software whose source code users may inspect, modify, and redistribute | 120.7851° | 0.806405 |
| Alternative: Software with source code withheld from users | 107.3373° | 0.831282 |

Parent choice: alternative parent; margin -13.4478° (positive favors intended). Direction: intended parent→child 120.7851°, child→intended parent 114.9735°; declared direction reversed.

Independent wording combinations favor the intended parent in 4/8 combinations of this same case.

## S04 — Software

Pre-score judgment: Keeping backup copies of important files is a valid topical refinement of Preventing data loss. File organization is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Keeping backup copies of important files

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Preventing data loss | 107.0797° | 0.897941 |
| Alternative: File organization | 102.0372° | 0.872556 |

Parent choice: alternative parent; margin -5.0425° (positive favors intended). Direction: intended parent→child 107.0797°, child→intended parent 121.2691°; declared direction favored.

**Wording 2**

Narrower category: Making extra copies of important files for recovery

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Protecting against lost data | 108.3911° | 0.788384 |
| Alternative: Arranging and categorizing files | 117.3830° | 0.774133 |

Parent choice: intended parent; margin 8.9919° (positive favors intended). Direction: intended parent→child 108.3911°, child→intended parent 135.3715°; declared direction favored.

Independent wording combinations favor the intended parent in 4/8 combinations of this same case.

## S05 — Software

Pre-score judgment: Preventing access to freed memory is a valid topical refinement of Memory safety. Memory performance is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Preventing access to freed memory

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Memory safety | 97.2135° | 0.890358 |
| Alternative: Memory performance | 97.5807° | 0.885753 |

Parent choice: intended parent; margin 0.3672° (positive favors intended). Direction: intended parent→child 97.2135°, child→intended parent 131.6921°; declared direction favored.

**Wording 2**

Narrower category: Preventing a program from using memory after it has been freed

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Safe use of computer memory | 99.8676° | 0.863180 |
| Alternative: The speed and efficiency of computer memory use | 115.9058° | 0.843766 |

Parent choice: intended parent; margin 16.0381° (positive favors intended). Direction: intended parent→child 99.8676°, child→intended parent 128.7051°; declared direction favored.

Independent wording combinations favor the intended parent in 5/8 combinations of this same case.

## S06 — Software

Pre-score judgment: Linux distributions is a valid topical refinement of Operating systems. Application software is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Linux distributions

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Operating systems | 97.6920° | 0.879009 |
| Alternative: Application software | 94.8840° | 0.842295 |

Parent choice: alternative parent; margin -2.8080° (positive favors intended). Direction: intended parent→child 97.6920°, child→intended parent 133.0322°; declared direction favored.

**Wording 2**

Narrower category: Distributions of the Linux operating system

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: System software that manages a computer's hardware and programs | 108.6110° | 0.734075 |
| Alternative: Programs designed to carry out tasks for users | 107.4488° | 0.692672 |

Parent choice: alternative parent; margin -1.1621° (positive favors intended). Direction: intended parent→child 108.6110°, child→intended parent 127.9301°; declared direction favored.

Independent wording combinations favor the intended parent in 3/8 combinations of this same case.

## E01 — Economics

Pre-score judgment: Savings buying less as prices rise is a valid topical refinement of Changes in purchasing power. Bank transfers is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Savings buying less as prices rise

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Changes in purchasing power | 102.2571° | 0.836206 |
| Alternative: Bank transfers | 104.3907° | 0.733350 |

Parent choice: intended parent; margin 2.1336° (positive favors intended). Direction: intended parent→child 102.2571°, child→intended parent 126.2292°; declared direction favored.

**Wording 2**

Narrower category: Rising prices reducing the goods that savings can purchase

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Changes in what money can buy | 107.7194° | 0.788761 |
| Alternative: Moving money between bank accounts | 109.6908° | 0.785522 |

Parent choice: intended parent; margin 1.9714° (positive favors intended). Direction: intended parent→child 107.7194°, child→intended parent 132.3148°; declared direction favored.

Independent wording combinations favor the intended parent in 5/8 combinations of this same case.

## E02 — Economics

Pre-score judgment: A central bank raising interest rates is a valid topical refinement of Monetary policy. Fiscal policy is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: A central bank raising interest rates

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Monetary policy | 84.8441° | 0.898768 |
| Alternative: Fiscal policy | 93.3048° | 0.848944 |

Parent choice: intended parent; margin 8.4606° (positive favors intended). Direction: intended parent→child 84.8441°, child→intended parent 139.2339°; declared direction favored.

**Wording 2**

Narrower category: An increase in policy interest rates by the central bank

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Central-bank management of money and borrowing conditions | 97.4707° | 0.851866 |
| Alternative: Government decisions about taxation and spending | 98.9583° | 0.789446 |

Parent choice: intended parent; margin 1.4876° (positive favors intended). Direction: intended parent→child 97.4707°, child→intended parent 124.1675°; declared direction favored.

Independent wording combinations favor the intended parent in 5/8 combinations of this same case.

## E03 — Economics

Pre-score judgment: Tariffs on imported goods is a valid topical refinement of International trade. Domestic sales taxation is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Tariffs on imported goods

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: International trade | 88.0047° | 0.889494 |
| Alternative: Domestic sales taxation | 118.6420° | 0.851557 |

Parent choice: intended parent; margin 30.6373° (positive favors intended). Direction: intended parent→child 88.0047°, child→intended parent 146.1709°; declared direction favored.

**Wording 2**

Narrower category: Import duties charged on goods entering a country

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Commerce between countries | 104.2015° | 0.815500 |
| Alternative: Taxes charged on purchases within the domestic market | 112.9905° | 0.893515 |

Parent choice: intended parent; margin 8.7890° (positive favors intended). Direction: intended parent→child 104.2015°, child→intended parent 134.4478°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## E04 — Economics

Pre-score judgment: Setting aside money for emergencies is a valid topical refinement of Personal saving. Personal borrowing is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Setting aside money for emergencies

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Personal saving | 95.1783° | 0.891954 |
| Alternative: Personal borrowing | 110.4534° | 0.856014 |

Parent choice: intended parent; margin 15.2751° (positive favors intended). Direction: intended parent→child 95.1783°, child→intended parent 141.4007°; declared direction favored.

**Wording 2**

Narrower category: Building an emergency cash reserve

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Putting money aside for future needs | 106.1632° | 0.828619 |
| Alternative: Taking on debt to meet personal needs | 107.6813° | 0.851137 |

Parent choice: intended parent; margin 1.5180° (positive favors intended). Direction: intended parent→child 106.1632°, child→intended parent 135.0381°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## E05 — Economics

Pre-score judgment: Negotiating a higher salary is a valid topical refinement of Employment compensation. Working-time arrangements is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Negotiating a higher salary

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Employment compensation | 100.1968° | 0.863600 |
| Alternative: Working-time arrangements | 117.4108° | 0.809094 |

Parent choice: intended parent; margin 17.2139° (positive favors intended). Direction: intended parent→child 100.1968°, child→intended parent 140.5890°; declared direction favored.

**Wording 2**

Narrower category: Asking an employer for a pay rise

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Pay and benefits received for work | 109.2043° | 0.839230 |
| Alternative: Agreements about employees' working hours | 117.4800° | 0.803900 |

Parent choice: intended parent; margin 8.2758° (positive favors intended). Direction: intended parent→child 109.2043°, child→intended parent 125.5420°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## E06 — Economics

Pre-score judgment: Businesses competing by lowering prices is a valid topical refinement of Market competition. Price collusion is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Businesses competing by lowering prices

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Market competition | 95.7373° | 0.896017 |
| Alternative: Price collusion | 114.7593° | 0.847022 |

Parent choice: intended parent; margin 19.0220° (positive favors intended). Direction: intended parent→child 95.7373°, child→intended parent 136.5997°; declared direction favored.

**Wording 2**

Narrower category: Sellers undercutting each other's prices

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Rivalry between sellers | 104.0827° | 0.878722 |
| Alternative: Coordination between sellers to fix prices | 107.2003° | 0.887033 |

Parent choice: intended parent; margin 3.1175° (positive favors intended). Direction: intended parent→child 104.0827°, child→intended parent 119.3423°; declared direction favored.

Independent wording combinations favor the intended parent in 6/8 combinations of this same case.

## P01 — Political ideas

Pre-score judgment: The right to criticize the government is a valid topical refinement of Freedom of expression. Freedom of movement is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: The right to criticize the government

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Freedom of expression | 101.9380° | 0.858121 |
| Alternative: Freedom of movement | 111.4232° | 0.818604 |

Parent choice: intended parent; margin 9.4852° (positive favors intended). Direction: intended parent→child 101.9380°, child→intended parent 139.7402°; declared direction favored.

**Wording 2**

Narrower category: Being free to speak against government policies

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Freedom to voice opinions | 99.6159° | 0.910224 |
| Alternative: Freedom to travel and choose where to live | 114.4300° | 0.859719 |

Parent choice: intended parent; margin 14.8141° (positive favors intended). Direction: intended parent→child 99.6159°, child→intended parent 128.0616°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## P02 — Political ideas

Pre-score judgment: Voting in local elections is a valid topical refinement of Democratic participation. Public-sector employment is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Voting in local elections

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Democratic participation | 95.6270° | 0.903662 |
| Alternative: Public-sector employment | 111.7821° | 0.842910 |

Parent choice: intended parent; margin 16.1550° (positive favors intended). Direction: intended parent→child 95.6270°, child→intended parent 132.9719°; declared direction favored.

**Wording 2**

Narrower category: Citizens electing their local representatives

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Public participation in democratic government | 108.3748° | 0.860753 |
| Alternative: Working in jobs provided by government | 109.4423° | 0.815848 |

Parent choice: intended parent; margin 1.0675° (positive favors intended). Direction: intended parent→child 108.3748°, child→intended parent 121.8641°; declared direction favored.

Independent wording combinations favor the intended parent in 5/8 combinations of this same case.

## P03 — Political ideas

Pre-score judgment: Giving local councils more decision-making power instead of the national government is a valid topical refinement of Decentralization of government. Electoral representation is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Giving local councils more decision-making power instead of the national government

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Decentralization of government | 102.0719° | 0.813030 |
| Alternative: Electoral representation | 101.1645° | 0.751793 |

Parent choice: alternative parent; margin -0.9074° (positive favors intended). Direction: intended parent→child 102.0719°, child→intended parent 133.3962°; declared direction favored.

**Wording 2**

Narrower category: Transferring authority from national leaders to local councils

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Decentralizing government authority | 101.4839° | 0.863363 |
| Alternative: How elected officials represent voters | 107.4506° | 0.811219 |

Parent choice: intended parent; margin 5.9667° (positive favors intended). Direction: intended parent→child 101.4839°, child→intended parent 123.3456°; declared direction favored.

Independent wording combinations favor the intended parent in 4/8 combinations of this same case.

## P04 — Political ideas

Pre-score judgment: Organizing peaceful demonstrations for political change is a valid topical refinement of Political activism. Political journalism is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Organizing peaceful demonstrations for political change

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Political activism | 85.7967° | 0.876980 |
| Alternative: Political journalism | 108.4520° | 0.806299 |

Parent choice: intended parent; margin 22.6553° (positive favors intended). Direction: intended parent→child 85.7967°, child→intended parent 145.0580°; declared direction favored.

**Wording 2**

Narrower category: Arranging nonviolent public demonstrations to seek political change

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Taking action to bring about political change | 92.9916° | 0.857460 |
| Alternative: News reporting about politics | 108.3914° | 0.756305 |

Parent choice: intended parent; margin 15.3997° (positive favors intended). Direction: intended parent→child 92.9916°, child→intended parent 135.7391°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## P05 — Political ideas

Pre-score judgment: Legal protection against arbitrary detention is a valid topical refinement of Civil liberties. Criminal sentencing is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Legal protection against arbitrary detention

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Civil liberties | 102.6715° | 0.840315 |
| Alternative: Criminal sentencing | 105.2042° | 0.819175 |

Parent choice: intended parent; margin 2.5327° (positive favors intended). Direction: intended parent→child 102.6715°, child→intended parent 137.9280°; declared direction favored.

**Wording 2**

Narrower category: Safeguards against being detained without lawful justification

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Individual freedoms protected against government interference | 112.9013° | 0.856658 |
| Alternative: Deciding penalties following criminal convictions | 122.9519° | 0.804006 |

Parent choice: intended parent; margin 10.0505° (positive favors intended). Direction: intended parent→child 112.9013°, child→intended parent 119.8041°; declared direction favored.

Independent wording combinations favor the intended parent in 6/8 combinations of this same case.

## P06 — Political ideas

Pre-score judgment: Requiring elected officials to disclose their personal financial interests is a valid topical refinement of Political accountability. Election campaigning is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Requiring elected officials to disclose their personal financial interests

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Political accountability | 92.1307° | 0.853592 |
| Alternative: Election campaigning | 115.0748° | 0.773684 |

Parent choice: intended parent; margin 22.9441° (positive favors intended). Direction: intended parent→child 92.1307°, child→intended parent 143.2974°; declared direction favored.

**Wording 2**

Narrower category: Mandatory disclosure of elected officials' personal financial interests

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Making public officials answerable for their conduct | 112.2836° | 0.837389 |
| Alternative: Organized efforts to win elections | 113.6541° | 0.806256 |

Parent choice: intended parent; margin 1.3705° (positive favors intended). Direction: intended parent→child 112.2836°, child→intended parent 121.8138°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## R01 — Interpersonal relationships

Pre-score judgment: Relying on a partner to keep a confidence is a valid topical refinement of Trust in relationships. Shared leisure in relationships is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Relying on a partner to keep a confidence

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Trust in relationships | 106.5207° | 0.881433 |
| Alternative: Shared leisure in relationships | 110.4294° | 0.864444 |

Parent choice: intended parent; margin 3.9086° (positive favors intended). Direction: intended parent→child 106.5207°, child→intended parent 128.6328°; declared direction favored.

**Wording 2**

Narrower category: Trusting a partner to keep private information confidential

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Interpersonal trust | 98.6658° | 0.857456 |
| Alternative: Spending recreational time together in a relationship | 106.0017° | 0.861309 |

Parent choice: intended parent; margin 7.3359° (positive favors intended). Direction: intended parent→child 98.6658°, child→intended parent 137.9396°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## R02 — Interpersonal relationships

Pre-score judgment: Accepting a friend's refusal to discuss a private matter is a valid topical refinement of Respecting personal boundaries. Giving personal advice is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Accepting a friend's refusal to discuss a private matter

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Respecting personal boundaries | 111.9580° | 0.818556 |
| Alternative: Giving personal advice | 107.9472° | 0.811283 |

Parent choice: alternative parent; margin -4.0107° (positive favors intended). Direction: intended parent→child 111.9580°, child→intended parent 129.8908°; declared direction favored.

**Wording 2**

Narrower category: Letting a friend keep a sensitive topic private

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Respect for other people's personal limits | 115.5463° | 0.801357 |
| Alternative: Offering someone guidance about personal decisions | 117.5889° | 0.807668 |

Parent choice: intended parent; margin 2.0426° (positive favors intended). Direction: intended parent→child 115.5463°, child→intended parent 129.8418°; declared direction favored.

Independent wording combinations favor the intended parent in 4/8 combinations of this same case.

## R03 — Interpersonal relationships

Pre-score judgment: Listening compassionately to a grieving friend is a valid topical refinement of Emotional support. Financial support is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Listening compassionately to a grieving friend

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Emotional support | 104.6398° | 0.777792 |
| Alternative: Financial support | 104.6499° | 0.761412 |

Parent choice: intended parent; margin 0.0101° (positive favors intended). Direction: intended parent→child 104.6398°, child→intended parent 144.3987°; declared direction favored.

**Wording 2**

Narrower category: Offering a bereaved friend a sympathetic ear

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Helping someone cope emotionally | 95.7946° | 0.737241 |
| Alternative: Helping someone with money or expenses | 103.3140° | 0.679180 |

Parent choice: intended parent; margin 7.5194° (positive favors intended). Direction: intended parent→child 95.7946°, child→intended parent 142.8073°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## R04 — Interpersonal relationships

Pre-score judgment: Working through a disagreement with a partner is a valid topical refinement of Resolving interpersonal conflict. Interpersonal competition is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Working through a disagreement with a partner

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Resolving interpersonal conflict | 103.1440° | 0.904103 |
| Alternative: Interpersonal competition | 107.2417° | 0.865817 |

Parent choice: intended parent; margin 4.0977° (positive favors intended). Direction: intended parent→child 103.1440°, child→intended parent 126.2706°; declared direction favored.

**Wording 2**

Narrower category: Finding a resolution to an argument within a couple

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Settling disagreements between people | 109.7976° | 0.879746 |
| Alternative: Competing against other people | 115.7616° | 0.825619 |

Parent choice: intended parent; margin 5.9640° (positive favors intended). Direction: intended parent→child 109.7976°, child→intended parent 123.3671°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## R05 — Interpersonal relationships

Pre-score judgment: Accommodating a spouse's preferences despite different personal tastes is a valid topical refinement of Consideration for a partner. Persuasion in relationships is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Accommodating a spouse's preferences despite different personal tastes

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Consideration for a partner | 100.7102° | 0.784897 |
| Alternative: Persuasion in relationships | 99.8709° | 0.792995 |

Parent choice: alternative parent; margin -0.8393° (positive favors intended). Direction: intended parent→child 100.7102°, child→intended parent 140.2959°; declared direction favored.

**Wording 2**

Narrower category: Making room for what a spouse likes even when one's own preferences differ

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Being considerate toward one's partner | 100.9568° | 0.783572 |
| Alternative: Trying to change another person's views or preferences | 106.7829° | 0.738376 |

Parent choice: intended parent; margin 5.8261° (positive favors intended). Direction: intended parent→child 100.9568°, child→intended parent 136.4264°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## R06 — Interpersonal relationships

Pre-score judgment: Admitting a mistake to a friend is a valid topical refinement of Honesty in relationships. Maintaining personal privacy is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Admitting a mistake to a friend

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Honesty in relationships | 110.0120° | 0.880226 |
| Alternative: Maintaining personal privacy | 115.7683° | 0.833146 |

Parent choice: intended parent; margin 5.7563° (positive favors intended). Direction: intended parent→child 110.0120°, child→intended parent 126.0981°; declared direction favored.

**Wording 2**

Narrower category: Owning up to something one did wrong when speaking to a friend

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Being truthful with other people | 104.5038° | 0.864043 |
| Alternative: Keeping personal information private | 112.7159° | 0.828288 |

Parent choice: intended parent; margin 8.2121° (positive favors intended). Direction: intended parent→child 104.5038°, child→intended parent 131.9229°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## F01 — Food control

Pre-score judgment: Bagels with sesame seeds is a valid topical refinement of Bread. Crackers is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Bagels with sesame seeds

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Bread | 84.1434° | 0.689999 |
| Alternative: Crackers | 101.9936° | 0.649860 |

Parent choice: intended parent; margin 17.8502° (positive favors intended). Direction: intended parent→child 84.1434°, child→intended parent 158.4308°; declared direction favored.

**Wording 2**

Narrower category: Sesame-topped bagels

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Baked bread products | 91.2571° | 0.631049 |
| Alternative: Crisp, dry cracker products | 107.3020° | 0.578128 |

Parent choice: intended parent; margin 16.0448° (positive favors intended). Direction: intended parent→child 91.2571°, child→intended parent 150.0237°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## F02 — Food control

Pre-score judgment: yogurt made with live cultures refines fermented foods, not roasted foods. Replaced thickening food because milk fermentation also thickens it.

**Wording 1**

Narrower category: Yogurt made with live cultures

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Fermented foods | 109.7669° | 0.781539 |
| Alternative: Roasted foods | 113.7021° | 0.720780 |

Parent choice: intended parent; margin 3.9352° (positive favors intended). Direction: intended parent→child 109.7669°, child→intended parent 131.3642°; declared direction favored.

**Wording 2**

Narrower category: Milk fermented into yogurt using live bacteria

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Foods produced through fermentation | 101.4756° | 0.778050 |
| Alternative: Foods cooked by roasting | 114.5154° | 0.612058 |

Parent choice: intended parent; margin 13.0398° (positive favors intended). Direction: intended parent→child 101.4756°, child→intended parent 127.6347°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.

## F03 — Food control

Pre-score judgment: Freezing homegrown vegetables is a valid topical refinement of Preserving food. Growing food is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Freezing homegrown vegetables

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Preserving food | 100.0652° | 0.716494 |
| Alternative: Growing food | 87.6037° | 0.732856 |

Parent choice: alternative parent; margin -12.4615° (positive favors intended). Direction: intended parent→child 100.0652°, child→intended parent 144.1105°; declared direction favored.

**Wording 2**

Narrower category: Keeping garden vegetables in the freezer

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Preventing stored food from spoiling | 106.2879° | 0.749657 |
| Alternative: Cultivating plants for food | 98.9030° | 0.770340 |

Parent choice: alternative parent; margin -7.3849° (positive favors intended). Direction: intended parent→child 106.2879°, child→intended parent 131.0303°; declared direction favored.

Independent wording combinations favor the intended parent in 2/8 combinations of this same case.

## F04 — Food control

Pre-score judgment: Making a cake in the oven is a valid topical refinement of Baking. Food decoration is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Making a cake in the oven

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Baking | 80.1979° | 0.838585 |
| Alternative: Food decoration | 99.0126° | 0.712799 |

Parent choice: intended parent; margin 18.8147° (positive favors intended). Direction: intended parent→child 80.1979°, child→intended parent 145.5379°; declared direction favored.

**Wording 2**

Narrower category: Preparing an oven-baked cake

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Cooking food by baking | 99.0164° | 0.845128 |
| Alternative: Decorating food for presentation | 117.0665° | 0.761001 |

Parent choice: intended parent; margin 18.0501° (positive favors intended). Direction: intended parent→child 99.0164°, child→intended parent 132.0292°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## F05 — Food control

Pre-score judgment: Pan-frying vegetables is a valid topical refinement of Cooking methods. Cutting techniques in food preparation is a related category but does not encompass that narrower subject as described.

**Wording 1**

Narrower category: Pan-frying vegetables

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Cooking methods | 85.1806° | 0.775156 |
| Alternative: Cutting techniques in food preparation | 105.7701° | 0.732344 |

Parent choice: intended parent; margin 20.5895° (positive favors intended). Direction: intended parent→child 85.1806°, child→intended parent 149.6825°; declared direction favored.

**Wording 2**

Narrower category: Frying vegetables in a pan

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Techniques for cooking food | 98.8446° | 0.737350 |
| Alternative: Ways of slicing and chopping ingredients | 111.6648° | 0.700543 |

Parent choice: intended parent; margin 12.8202° (positive favors intended). Direction: intended parent→child 98.8446°, child→intended parent 138.5951°; declared direction favored.

Independent wording combinations favor the intended parent in 8/8 combinations of this same case.

## F06 — Food control

Pre-score judgment: a stew made entirely from plant ingredients is a valid refinement of vegetarian meals, but not meat dishes.

**Wording 1**

Narrower category: Lentil stew made entirely from plant ingredients

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Vegetarian meals | 91.8694° | 0.703183 |
| Alternative: Meat dishes | 98.4295° | 0.656376 |

Parent choice: intended parent; margin 6.5601° (positive favors intended). Direction: intended parent→child 91.8694°, child→intended parent 149.9431°; declared direction favored.

**Wording 2**

Narrower category: A lentil stew made entirely from plant ingredients

| Candidate parent | Angle ↓ | Cosine ↑ |
|---|---:|---:|
| Intended: Meals without meat or fish | 97.0000° | 0.686315 |
| Alternative: Dishes containing meat | 101.4401° | 0.639470 |

Parent choice: intended parent; margin 4.4402° (positive favors intended). Direction: intended parent→child 97.0000°, child→intended parent 143.4578°; declared direction favored.

Independent wording combinations favor the intended parent in 7/8 combinations of this same case.
