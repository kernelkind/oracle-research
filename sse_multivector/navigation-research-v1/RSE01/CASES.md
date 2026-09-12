# RSE01 — Every category comparison

These are the exact constructed category descriptions from HRC03, not original notes or masks. S/E/P/R/F identify software, economics, political ideas, relationships and food cases. Each case has two wordings. “Intended” records the frozen pre-score judgment; it is not a model output.

RSE entailment: higher favors the proposed parent. RSE cosine: higher means more similar, without direction. HierarCaps angle: lower favors the proposed parent. Do not compare numerical scales between models. All columns use the exact child and candidate text shown.

The eight-combination table also mixes the two wordings of the child, intended parent and alternative. Its numbers identify wording 1 or 2 immediately above it. These are wording checks, not independent examples.

Qualified interpretations remain in [the HRC03 review](../HRC03/RESULTS.md#all-unexpected-matched-choices). RSE01 does not silently rewrite those judgments.

## S01

Pre-score judgment: Blocking cross-site tracking is a valid topical refinement of Web browser privacy. Web browser appearance is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Blocking cross-site tracking

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Web browser privacy | 0.381531 | 0.438012 | 114.6285° |
| Web browser appearance | 0.421560 | 0.425764 | 110.3737° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: -0.019580.

### Wording 2

**Child:** Preventing tracking across different websites

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Protecting privacy while browsing the web | 0.500349 | 0.501077 | 112.9729° |
| How a web browser looks | 0.398132 | 0.370082 | 125.0467° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.062931.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.381531 | 0.421560 | alternative |
| 1 | 1 | 2 | 0.381531 | 0.385416 | alternative |
| 2 | 1 | 1 | 0.426692 | 0.433145 | alternative |
| 2 | 1 | 2 | 0.426692 | 0.398132 | intended |
| 1 | 2 | 1 | 0.421933 | 0.421560 | intended |
| 1 | 2 | 2 | 0.421933 | 0.385416 | intended |
| 2 | 2 | 1 | 0.500349 | 0.433145 | intended |
| 2 | 2 | 2 | 0.500349 | 0.398132 | intended |

## S02

Pre-score judgment: verifying downloaded program signatures refines software security, not software usability. Replaced release management because verifying distributed release artifacts can fall under it.

### Wording 1

**Child:** Verifying digital signatures on downloaded programs

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Software security | 0.420213 | 0.458927 | 96.7255° |
| Software usability | 0.410331 | 0.352621 | 105.9693° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.051004.

### Wording 2

**Child:** Checking downloaded software's digital signatures

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Keeping software secure | 0.655927 | 0.606097 | 103.5789° |
| Making software easy to use | 0.538087 | 0.448046 | 101.2969° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.173265.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.420213 | 0.410331 | intended |
| 1 | 1 | 2 | 0.420213 | 0.484443 | alternative |
| 2 | 1 | 1 | 0.455465 | 0.475224 | alternative |
| 2 | 1 | 2 | 0.455465 | 0.538087 | alternative |
| 1 | 2 | 1 | 0.596907 | 0.410331 | intended |
| 1 | 2 | 2 | 0.596907 | 0.484443 | intended |
| 2 | 2 | 1 | 0.655927 | 0.475224 | intended |
| 2 | 2 | 2 | 0.655927 | 0.538087 | intended |

## S03

Pre-score judgment: Programs released under the GNU General Public License is a valid topical refinement of Open-source software. Closed-source software is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Programs released under the GNU General Public License

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Open-source software | 0.726371 | 0.778149 | 87.9191° |
| Closed-source software | 0.578604 | 0.676036 | 94.3780° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.091564.

### Wording 2

**Child:** Software distributed under the GPL

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Software whose source code users may inspect, modify, and redistribute | 0.580560 | 0.701568 | 120.7851° |
| Software with source code withheld from users | 0.464226 | 0.643181 | 107.3373° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.062918.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.726371 | 0.578604 | intended |
| 1 | 1 | 2 | 0.726371 | 0.421537 | intended |
| 2 | 1 | 1 | 0.770344 | 0.614176 | intended |
| 2 | 1 | 2 | 0.770344 | 0.464226 | intended |
| 1 | 2 | 1 | 0.563498 | 0.578604 | alternative |
| 1 | 2 | 2 | 0.563498 | 0.421537 | intended |
| 2 | 2 | 1 | 0.580560 | 0.614176 | alternative |
| 2 | 2 | 2 | 0.580560 | 0.464226 | intended |

## S04

Pre-score judgment: Keeping backup copies of important files is a valid topical refinement of Preventing data loss. File organization is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Keeping backup copies of important files

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Preventing data loss | 0.587013 | 0.612615 | 107.0797° |
| File organization | 0.574655 | 0.631210 | 102.0372° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.005486.

### Wording 2

**Child:** Making extra copies of important files for recovery

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Protecting against lost data | 0.666730 | 0.651784 | 108.3911° |
| Arranging and categorizing files | 0.595105 | 0.614380 | 117.3830° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.120140.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.587013 | 0.574655 | intended |
| 1 | 1 | 2 | 0.587013 | 0.581446 | intended |
| 2 | 1 | 1 | 0.621847 | 0.538043 | intended |
| 2 | 1 | 2 | 0.621847 | 0.595105 | intended |
| 1 | 2 | 1 | 0.676309 | 0.574655 | intended |
| 1 | 2 | 2 | 0.676309 | 0.581446 | intended |
| 2 | 2 | 1 | 0.666730 | 0.538043 | intended |
| 2 | 2 | 2 | 0.666730 | 0.595105 | intended |

## S05

Pre-score judgment: Preventing access to freed memory is a valid topical refinement of Memory safety. Memory performance is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Preventing access to freed memory

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Memory safety | 0.549383 | 0.544222 | 97.2135° |
| Memory performance | 0.499885 | 0.479906 | 97.5807° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.116122.

### Wording 2

**Child:** Preventing a program from using memory after it has been freed

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Safe use of computer memory | 0.587479 | 0.626099 | 99.8676° |
| The speed and efficiency of computer memory use | 0.611087 | 0.620131 | 115.9058° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.022066.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.549383 | 0.499885 | intended |
| 1 | 1 | 2 | 0.549383 | 0.533524 | intended |
| 2 | 1 | 1 | 0.422128 | 0.425473 | alternative |
| 2 | 1 | 2 | 0.422128 | 0.611087 | alternative |
| 1 | 2 | 1 | 0.604998 | 0.499885 | intended |
| 1 | 2 | 2 | 0.604998 | 0.533524 | intended |
| 2 | 2 | 1 | 0.587479 | 0.425473 | intended |
| 2 | 2 | 2 | 0.587479 | 0.611087 | alternative |

## S06

Pre-score judgment: Linux distributions is a valid topical refinement of Operating systems. Application software is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Linux distributions

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Operating systems | 0.438947 | 0.457775 | 97.6920° |
| Application software | 0.467591 | 0.481784 | 94.8840° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.005445.

### Wording 2

**Child:** Distributions of the Linux operating system

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| System software that manages a computer's hardware and programs | 0.532792 | 0.573717 | 108.6110° |
| Programs designed to carry out tasks for users | 0.460594 | 0.397277 | 107.4488° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.035459.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.438947 | 0.467591 | alternative |
| 1 | 1 | 2 | 0.438947 | 0.435135 | intended |
| 2 | 1 | 1 | 0.498262 | 0.482721 | intended |
| 2 | 1 | 2 | 0.498262 | 0.460594 | intended |
| 1 | 2 | 1 | 0.489889 | 0.467591 | intended |
| 1 | 2 | 2 | 0.489889 | 0.435135 | intended |
| 2 | 2 | 1 | 0.532792 | 0.482721 | intended |
| 2 | 2 | 2 | 0.532792 | 0.460594 | intended |

## E01

Pre-score judgment: Savings buying less as prices rise is a valid topical refinement of Changes in purchasing power. Bank transfers is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Savings buying less as prices rise

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Changes in purchasing power | 0.631231 | 0.592714 | 102.2571° |
| Bank transfers | 0.315235 | 0.275816 | 104.3907° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.162089.

### Wording 2

**Child:** Rising prices reducing the goods that savings can purchase

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Changes in what money can buy | 0.610592 | 0.536329 | 107.7194° |
| Moving money between bank accounts | 0.376112 | 0.248775 | 109.6908° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.189671.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.631231 | 0.315235 | intended |
| 1 | 1 | 2 | 0.631231 | 0.473125 | intended |
| 2 | 1 | 1 | 0.608045 | 0.219373 | intended |
| 2 | 1 | 2 | 0.608045 | 0.376112 | intended |
| 1 | 2 | 1 | 0.618357 | 0.315235 | intended |
| 1 | 2 | 2 | 0.618357 | 0.473125 | intended |
| 2 | 2 | 1 | 0.610592 | 0.219373 | intended |
| 2 | 2 | 2 | 0.610592 | 0.376112 | intended |

## E02

Pre-score judgment: A central bank raising interest rates is a valid topical refinement of Monetary policy. Fiscal policy is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** A central bank raising interest rates

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Monetary policy | 0.428858 | 0.449205 | 84.8441° |
| Fiscal policy | 0.340600 | 0.338046 | 93.3048° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.001864.

### Wording 2

**Child:** An increase in policy interest rates by the central bank

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Central-bank management of money and borrowing conditions | 0.554598 | 0.607819 | 97.4707° |
| Government decisions about taxation and spending | 0.404065 | 0.319193 | 98.9583° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.002760.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.428858 | 0.340600 | intended |
| 1 | 1 | 2 | 0.428858 | 0.366321 | intended |
| 2 | 1 | 1 | 0.476666 | 0.409654 | intended |
| 2 | 1 | 2 | 0.476666 | 0.404065 | intended |
| 1 | 2 | 1 | 0.577087 | 0.340600 | intended |
| 1 | 2 | 2 | 0.577087 | 0.366321 | intended |
| 2 | 2 | 1 | 0.554598 | 0.409654 | intended |
| 2 | 2 | 2 | 0.554598 | 0.404065 | intended |

## E03

Pre-score judgment: Tariffs on imported goods is a valid topical refinement of International trade. Domestic sales taxation is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Tariffs on imported goods

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| International trade | 0.634753 | 0.680280 | 88.0047° |
| Domestic sales taxation | 0.639548 | 0.753429 | 118.6420° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.022963.

### Wording 2

**Child:** Import duties charged on goods entering a country

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Commerce between countries | 0.592409 | 0.609358 | 104.2015° |
| Taxes charged on purchases within the domestic market | 0.588069 | 0.727534 | 112.9905° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.028552.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.634753 | 0.639548 | alternative |
| 1 | 1 | 2 | 0.634753 | 0.635672 | alternative |
| 2 | 1 | 1 | 0.488672 | 0.505479 | alternative |
| 2 | 1 | 2 | 0.488672 | 0.588069 | alternative |
| 1 | 2 | 1 | 0.658074 | 0.639548 | intended |
| 1 | 2 | 2 | 0.658074 | 0.635672 | intended |
| 2 | 2 | 1 | 0.592409 | 0.505479 | intended |
| 2 | 2 | 2 | 0.592409 | 0.588069 | intended |

## E04

Pre-score judgment: Setting aside money for emergencies is a valid topical refinement of Personal saving. Personal borrowing is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Setting aside money for emergencies

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Personal saving | 0.546617 | 0.601435 | 95.1783° |
| Personal borrowing | 0.342327 | 0.409676 | 110.4534° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.082288.

### Wording 2

**Child:** Building an emergency cash reserve

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Putting money aside for future needs | 0.780272 | 0.827299 | 106.1632° |
| Taking on debt to meet personal needs | 0.660923 | 0.666904 | 107.6813° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.013421.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.546617 | 0.342327 | intended |
| 1 | 1 | 2 | 0.546617 | 0.623204 | alternative |
| 2 | 1 | 1 | 0.568026 | 0.398431 | intended |
| 2 | 1 | 2 | 0.568026 | 0.660923 | alternative |
| 1 | 2 | 1 | 0.813643 | 0.342327 | intended |
| 1 | 2 | 2 | 0.813643 | 0.623204 | intended |
| 2 | 2 | 1 | 0.780272 | 0.398431 | intended |
| 2 | 2 | 2 | 0.780272 | 0.660923 | intended |

## E05

Pre-score judgment: Negotiating a higher salary is a valid topical refinement of Employment compensation. Working-time arrangements is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Negotiating a higher salary

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Employment compensation | 0.554587 | 0.595669 | 100.1968° |
| Working-time arrangements | 0.474869 | 0.503990 | 117.4108° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.037077.

### Wording 2

**Child:** Asking an employer for a pay rise

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Pay and benefits received for work | 0.467972 | 0.475773 | 109.2043° |
| Agreements about employees' working hours | 0.508769 | 0.498586 | 117.4800° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.010814.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.554587 | 0.474869 | intended |
| 1 | 1 | 2 | 0.554587 | 0.575553 | alternative |
| 2 | 1 | 1 | 0.556172 | 0.417895 | intended |
| 2 | 1 | 2 | 0.556172 | 0.508769 | intended |
| 1 | 2 | 1 | 0.463772 | 0.474869 | alternative |
| 1 | 2 | 2 | 0.463772 | 0.575553 | alternative |
| 2 | 2 | 1 | 0.467972 | 0.417895 | intended |
| 2 | 2 | 2 | 0.467972 | 0.508769 | alternative |

## E06

Pre-score judgment: Businesses competing by lowering prices is a valid topical refinement of Market competition. Price collusion is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Businesses competing by lowering prices

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Market competition | 0.582528 | 0.660219 | 95.7373° |
| Price collusion | 0.585706 | 0.628394 | 114.7593° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: -0.013229.

### Wording 2

**Child:** Sellers undercutting each other's prices

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Rivalry between sellers | 0.693969 | 0.712697 | 104.0827° |
| Coordination between sellers to fix prices | 0.574642 | 0.494712 | 107.2003° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.140358.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.582528 | 0.585706 | alternative |
| 1 | 1 | 2 | 0.582528 | 0.580941 | intended |
| 2 | 1 | 1 | 0.424718 | 0.542909 | alternative |
| 2 | 1 | 2 | 0.424718 | 0.574642 | alternative |
| 1 | 2 | 1 | 0.549678 | 0.585706 | alternative |
| 1 | 2 | 2 | 0.549678 | 0.580941 | alternative |
| 2 | 2 | 1 | 0.693969 | 0.542909 | intended |
| 2 | 2 | 2 | 0.693969 | 0.574642 | intended |

## P01

Pre-score judgment: The right to criticize the government is a valid topical refinement of Freedom of expression. Freedom of movement is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** The right to criticize the government

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Freedom of expression | 0.671364 | 0.733041 | 101.9380° |
| Freedom of movement | 0.543277 | 0.530854 | 111.4232° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.019063.

### Wording 2

**Child:** Being free to speak against government policies

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Freedom to voice opinions | 0.765130 | 0.820414 | 99.6159° |
| Freedom to travel and choose where to live | 0.562625 | 0.596397 | 114.4300° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.005973.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.671364 | 0.543277 | intended |
| 1 | 1 | 2 | 0.671364 | 0.508105 | intended |
| 2 | 1 | 1 | 0.679178 | 0.592442 | intended |
| 2 | 1 | 2 | 0.679178 | 0.562625 | intended |
| 1 | 2 | 1 | 0.729824 | 0.543277 | intended |
| 1 | 2 | 2 | 0.729824 | 0.508105 | intended |
| 2 | 2 | 1 | 0.765130 | 0.592442 | intended |
| 2 | 2 | 2 | 0.765130 | 0.562625 | intended |

## P02

Pre-score judgment: Voting in local elections is a valid topical refinement of Democratic participation. Public-sector employment is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Voting in local elections

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Democratic participation | 0.513828 | 0.584157 | 95.6270° |
| Public-sector employment | 0.326813 | 0.348890 | 111.7821° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.047604.

### Wording 2

**Child:** Citizens electing their local representatives

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Public participation in democratic government | 0.512892 | 0.589545 | 108.3748° |
| Working in jobs provided by government | 0.382545 | 0.284232 | 109.4423° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.072927.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.513828 | 0.326813 | intended |
| 1 | 1 | 2 | 0.513828 | 0.398645 | intended |
| 2 | 1 | 1 | 0.432210 | 0.247742 | intended |
| 2 | 1 | 2 | 0.432210 | 0.382545 | intended |
| 1 | 2 | 1 | 0.508407 | 0.326813 | intended |
| 1 | 2 | 2 | 0.508407 | 0.398645 | intended |
| 2 | 2 | 1 | 0.512892 | 0.247742 | intended |
| 2 | 2 | 2 | 0.512892 | 0.382545 | intended |

## P03

Pre-score judgment: Giving local councils more decision-making power instead of the national government is a valid topical refinement of Decentralization of government. Electoral representation is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Giving local councils more decision-making power instead of the national government

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Decentralization of government | 0.700881 | 0.717561 | 102.0719° |
| Electoral representation | 0.559910 | 0.511243 | 101.1645° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.102552.

### Wording 2

**Child:** Transferring authority from national leaders to local councils

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Decentralizing government authority | 0.746315 | 0.806581 | 101.4839° |
| How elected officials represent voters | 0.586210 | 0.559202 | 107.4506° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.033045.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.700881 | 0.559910 | intended |
| 1 | 1 | 2 | 0.700881 | 0.568543 | intended |
| 2 | 1 | 1 | 0.674024 | 0.600512 | intended |
| 2 | 1 | 2 | 0.674024 | 0.586210 | intended |
| 1 | 2 | 1 | 0.728326 | 0.559910 | intended |
| 1 | 2 | 2 | 0.728326 | 0.568543 | intended |
| 2 | 2 | 1 | 0.746315 | 0.600512 | intended |
| 2 | 2 | 2 | 0.746315 | 0.586210 | intended |

## P04

Pre-score judgment: Organizing peaceful demonstrations for political change is a valid topical refinement of Political activism. Political journalism is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Organizing peaceful demonstrations for political change

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Political activism | 0.622217 | 0.654715 | 85.7967° |
| Political journalism | 0.334974 | 0.358120 | 108.4520° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.062647.

### Wording 2

**Child:** Arranging nonviolent public demonstrations to seek political change

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Taking action to bring about political change | 0.764324 | 0.785705 | 92.9916° |
| News reporting about politics | 0.349041 | 0.346064 | 108.3914° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.119092.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.622217 | 0.334974 | intended |
| 1 | 1 | 2 | 0.622217 | 0.339833 | intended |
| 2 | 1 | 1 | 0.630380 | 0.365738 | intended |
| 2 | 1 | 2 | 0.630380 | 0.349041 | intended |
| 1 | 2 | 1 | 0.735913 | 0.334974 | intended |
| 1 | 2 | 2 | 0.735913 | 0.339833 | intended |
| 2 | 2 | 1 | 0.764324 | 0.365738 | intended |
| 2 | 2 | 2 | 0.764324 | 0.349041 | intended |

## P05

Pre-score judgment: Legal protection against arbitrary detention is a valid topical refinement of Civil liberties. Criminal sentencing is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Legal protection against arbitrary detention

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Civil liberties | 0.521565 | 0.556831 | 102.6715° |
| Criminal sentencing | 0.518669 | 0.554442 | 105.2042° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.003404.

### Wording 2

**Child:** Safeguards against being detained without lawful justification

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Individual freedoms protected against government interference | 0.528714 | 0.487900 | 112.9013° |
| Deciding penalties following criminal convictions | 0.410398 | 0.364915 | 122.9519° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.066732.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.521565 | 0.518669 | intended |
| 1 | 1 | 2 | 0.521565 | 0.475382 | intended |
| 2 | 1 | 1 | 0.393704 | 0.434875 | alternative |
| 2 | 1 | 2 | 0.393704 | 0.410398 | alternative |
| 1 | 2 | 1 | 0.633783 | 0.518669 | intended |
| 1 | 2 | 2 | 0.633783 | 0.475382 | intended |
| 2 | 2 | 1 | 0.528714 | 0.434875 | intended |
| 2 | 2 | 2 | 0.528714 | 0.410398 | intended |

## P06

Pre-score judgment: Requiring elected officials to disclose their personal financial interests is a valid topical refinement of Political accountability. Election campaigning is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Requiring elected officials to disclose their personal financial interests

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Political accountability | 0.600302 | 0.641497 | 92.1307° |
| Election campaigning | 0.431553 | 0.389373 | 115.0748° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.008412.

### Wording 2

**Child:** Mandatory disclosure of elected officials' personal financial interests

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Making public officials answerable for their conduct | 0.716918 | 0.730462 | 112.2836° |
| Organized efforts to win elections | 0.490539 | 0.439857 | 113.6541° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.087809.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.600302 | 0.431553 | intended |
| 1 | 1 | 2 | 0.600302 | 0.512627 | intended |
| 2 | 1 | 1 | 0.573450 | 0.429331 | intended |
| 2 | 1 | 2 | 0.573450 | 0.490539 | intended |
| 1 | 2 | 1 | 0.771991 | 0.431553 | intended |
| 1 | 2 | 2 | 0.771991 | 0.512627 | intended |
| 2 | 2 | 1 | 0.716918 | 0.429331 | intended |
| 2 | 2 | 2 | 0.716918 | 0.490539 | intended |

## R01

Pre-score judgment: Relying on a partner to keep a confidence is a valid topical refinement of Trust in relationships. Shared leisure in relationships is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Relying on a partner to keep a confidence

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Trust in relationships | 0.647101 | 0.716547 | 106.5207° |
| Shared leisure in relationships | 0.504143 | 0.517786 | 110.4294° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.083017.

### Wording 2

**Child:** Trusting a partner to keep private information confidential

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Interpersonal trust | 0.687591 | 0.756606 | 98.6658° |
| Spending recreational time together in a relationship | 0.526121 | 0.493751 | 106.0017° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.026512.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.647101 | 0.504143 | intended |
| 1 | 1 | 2 | 0.647101 | 0.514196 | intended |
| 2 | 1 | 1 | 0.700500 | 0.522612 | intended |
| 2 | 1 | 2 | 0.700500 | 0.526121 | intended |
| 1 | 2 | 1 | 0.604061 | 0.504143 | intended |
| 1 | 2 | 2 | 0.604061 | 0.514196 | intended |
| 2 | 2 | 1 | 0.687591 | 0.522612 | intended |
| 2 | 2 | 2 | 0.687591 | 0.526121 | intended |

## R02

Pre-score judgment: Accepting a friend's refusal to discuss a private matter is a valid topical refinement of Respecting personal boundaries. Giving personal advice is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Accepting a friend's refusal to discuss a private matter

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Respecting personal boundaries | 0.427838 | 0.323904 | 111.9580° |
| Giving personal advice | 0.402604 | 0.392354 | 107.9472° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.112575.

### Wording 2

**Child:** Letting a friend keep a sensitive topic private

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Respect for other people's personal limits | 0.416689 | 0.299584 | 115.5463° |
| Offering someone guidance about personal decisions | 0.429292 | 0.342697 | 117.5889° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.103267.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.427838 | 0.402604 | intended |
| 1 | 1 | 2 | 0.427838 | 0.404673 | intended |
| 2 | 1 | 1 | 0.465600 | 0.413764 | intended |
| 2 | 1 | 2 | 0.465600 | 0.429292 | intended |
| 1 | 2 | 1 | 0.449782 | 0.402604 | intended |
| 1 | 2 | 2 | 0.449782 | 0.404673 | intended |
| 2 | 2 | 1 | 0.416689 | 0.413764 | intended |
| 2 | 2 | 2 | 0.416689 | 0.429292 | alternative |

## R03

Pre-score judgment: Listening compassionately to a grieving friend is a valid topical refinement of Emotional support. Financial support is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Listening compassionately to a grieving friend

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Emotional support | 0.301514 | 0.221595 | 104.6398° |
| Financial support | 0.146597 | 0.066730 | 104.6499° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.093538.

### Wording 2

**Child:** Offering a bereaved friend a sympathetic ear

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Helping someone cope emotionally | 0.633179 | 0.581978 | 95.7946° |
| Helping someone with money or expenses | 0.448726 | 0.393763 | 103.3140° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.122493.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.301514 | 0.146597 | intended |
| 1 | 1 | 2 | 0.301514 | 0.304120 | alternative |
| 2 | 1 | 1 | 0.400313 | 0.259052 | intended |
| 2 | 1 | 2 | 0.400313 | 0.448726 | alternative |
| 1 | 2 | 1 | 0.592099 | 0.146597 | intended |
| 1 | 2 | 2 | 0.592099 | 0.304120 | intended |
| 2 | 2 | 1 | 0.633179 | 0.259052 | intended |
| 2 | 2 | 2 | 0.633179 | 0.448726 | intended |

## R04

Pre-score judgment: Working through a disagreement with a partner is a valid topical refinement of Resolving interpersonal conflict. Interpersonal competition is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Working through a disagreement with a partner

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Resolving interpersonal conflict | 0.546245 | 0.546910 | 103.1440° |
| Interpersonal competition | 0.270978 | 0.202037 | 107.2417° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.004778.

### Wording 2

**Child:** Finding a resolution to an argument within a couple

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Settling disagreements between people | 0.711956 | 0.759393 | 109.7976° |
| Competing against other people | 0.409801 | 0.290152 | 115.7616° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.046929.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.546245 | 0.270978 | intended |
| 1 | 1 | 2 | 0.546245 | 0.362036 | intended |
| 2 | 1 | 1 | 0.597238 | 0.350197 | intended |
| 2 | 1 | 2 | 0.597238 | 0.409801 | intended |
| 1 | 2 | 1 | 0.649351 | 0.270978 | intended |
| 1 | 2 | 2 | 0.649351 | 0.362036 | intended |
| 2 | 2 | 1 | 0.711956 | 0.350197 | intended |
| 2 | 2 | 2 | 0.711956 | 0.409801 | intended |

## R05

Pre-score judgment: Accommodating a spouse's preferences despite different personal tastes is a valid topical refinement of Consideration for a partner. Persuasion in relationships is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Accommodating a spouse's preferences despite different personal tastes

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Consideration for a partner | 0.598034 | 0.576749 | 100.7102° |
| Persuasion in relationships | 0.492496 | 0.460709 | 99.8709° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.029217.

### Wording 2

**Child:** Making room for what a spouse likes even when one's own preferences differ

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Being considerate toward one's partner | 0.784546 | 0.744078 | 100.9568° |
| Trying to change another person's views or preferences | 0.480806 | 0.487889 | 106.7829° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.114869.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.598034 | 0.492496 | intended |
| 1 | 1 | 2 | 0.598034 | 0.479100 | intended |
| 2 | 1 | 1 | 0.624298 | 0.470299 | intended |
| 2 | 1 | 2 | 0.624298 | 0.480806 | intended |
| 1 | 2 | 1 | 0.761108 | 0.492496 | intended |
| 1 | 2 | 2 | 0.761108 | 0.479100 | intended |
| 2 | 2 | 1 | 0.784546 | 0.470299 | intended |
| 2 | 2 | 2 | 0.784546 | 0.480806 | intended |

## R06

Pre-score judgment: Admitting a mistake to a friend is a valid topical refinement of Honesty in relationships. Maintaining personal privacy is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Admitting a mistake to a friend

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Honesty in relationships | 0.430122 | 0.412651 | 110.0120° |
| Maintaining personal privacy | 0.306433 | 0.238503 | 115.7683° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.020522.

### Wording 2

**Child:** Owning up to something one did wrong when speaking to a friend

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Being truthful with other people | 0.707178 | 0.674474 | 104.5038° |
| Keeping personal information private | 0.289520 | 0.318757 | 112.7159° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.087022.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.430122 | 0.306433 | intended |
| 1 | 1 | 2 | 0.430122 | 0.230292 | intended |
| 2 | 1 | 1 | 0.513593 | 0.416896 | intended |
| 2 | 1 | 2 | 0.513593 | 0.289520 | intended |
| 1 | 2 | 1 | 0.561945 | 0.306433 | intended |
| 1 | 2 | 2 | 0.561945 | 0.230292 | intended |
| 2 | 2 | 1 | 0.707178 | 0.416896 | intended |
| 2 | 2 | 2 | 0.707178 | 0.289520 | intended |

## F01

Pre-score judgment: Bagels with sesame seeds is a valid topical refinement of Bread. Crackers is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Bagels with sesame seeds

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Bread | 0.419707 | 0.495959 | 84.1434° |
| Crackers | 0.387491 | 0.492691 | 101.9936° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: -0.043938.

### Wording 2

**Child:** Sesame-topped bagels

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Baked bread products | 0.696035 | 0.650255 | 91.2571° |
| Crisp, dry cracker products | 0.525817 | 0.551068 | 107.3020° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.199015.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.419707 | 0.387491 | intended |
| 1 | 1 | 2 | 0.419707 | 0.445041 | alternative |
| 2 | 1 | 1 | 0.597575 | 0.501022 | intended |
| 2 | 1 | 2 | 0.597575 | 0.525817 | intended |
| 1 | 2 | 1 | 0.609276 | 0.387491 | intended |
| 1 | 2 | 2 | 0.609276 | 0.445041 | intended |
| 2 | 2 | 1 | 0.696035 | 0.501022 | intended |
| 2 | 2 | 2 | 0.696035 | 0.525817 | intended |

## F02

Pre-score judgment: yogurt made with live cultures refines fermented foods, not roasted foods. Replaced thickening food because milk fermentation also thickens it.

### Wording 1

**Child:** Yogurt made with live cultures

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Fermented foods | 0.510820 | 0.531631 | 109.7669° |
| Roasted foods | 0.492545 | 0.479081 | 113.7021° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.042076.

### Wording 2

**Child:** Milk fermented into yogurt using live bacteria

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Foods produced through fermentation | 0.637644 | 0.636959 | 101.4756° |
| Foods cooked by roasting | 0.363635 | 0.317346 | 114.5154° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.121030.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.510820 | 0.492545 | intended |
| 1 | 1 | 2 | 0.510820 | 0.475470 | intended |
| 2 | 1 | 1 | 0.455354 | 0.342643 | intended |
| 2 | 1 | 2 | 0.455354 | 0.363635 | intended |
| 1 | 2 | 1 | 0.555353 | 0.492545 | intended |
| 1 | 2 | 2 | 0.555353 | 0.475470 | intended |
| 2 | 2 | 1 | 0.637644 | 0.342643 | intended |
| 2 | 2 | 2 | 0.637644 | 0.363635 | intended |

## F03

Pre-score judgment: Freezing homegrown vegetables is a valid topical refinement of Preserving food. Growing food is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Freezing homegrown vegetables

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Preserving food | 0.764519 | 0.710677 | 100.0652° |
| Growing food | 0.716089 | 0.691438 | 87.6037° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.228741.

### Wording 2

**Child:** Keeping garden vegetables in the freezer

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Preventing stored food from spoiling | 0.682956 | 0.614238 | 106.2879° |
| Cultivating plants for food | 0.648203 | 0.568368 | 98.9030° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.249190.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.764519 | 0.716089 | intended |
| 1 | 1 | 2 | 0.764519 | 0.664738 | intended |
| 2 | 1 | 1 | 0.741162 | 0.738533 | intended |
| 2 | 1 | 2 | 0.741162 | 0.648203 | intended |
| 1 | 2 | 1 | 0.655521 | 0.716089 | alternative |
| 1 | 2 | 2 | 0.655521 | 0.664738 | alternative |
| 2 | 2 | 1 | 0.682956 | 0.738533 | alternative |
| 2 | 2 | 2 | 0.682956 | 0.648203 | intended |

## F04

Pre-score judgment: Making a cake in the oven is a valid topical refinement of Baking. Food decoration is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Making a cake in the oven

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Baking | 0.664326 | 0.709757 | 80.1979° |
| Food decoration | 0.436716 | 0.317750 | 99.0126° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.107712.

### Wording 2

**Child:** Preparing an oven-baked cake

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Cooking food by baking | 0.651442 | 0.687666 | 99.0164° |
| Decorating food for presentation | 0.663345 | 0.699244 | 117.0665° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.121145.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.664326 | 0.436716 | intended |
| 1 | 1 | 2 | 0.664326 | 0.563932 | intended |
| 2 | 1 | 1 | 0.583372 | 0.468232 | intended |
| 2 | 1 | 2 | 0.583372 | 0.663345 | alternative |
| 1 | 2 | 1 | 0.732805 | 0.436716 | intended |
| 1 | 2 | 2 | 0.732805 | 0.563932 | intended |
| 2 | 2 | 1 | 0.651442 | 0.468232 | intended |
| 2 | 2 | 2 | 0.651442 | 0.663345 | alternative |

## F05

Pre-score judgment: Pan-frying vegetables is a valid topical refinement of Cooking methods. Cutting techniques in food preparation is a related category but does not encompass that narrower subject as described.

### Wording 1

**Child:** Pan-frying vegetables

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Cooking methods | 0.491021 | 0.439439 | 85.1806° |
| Cutting techniques in food preparation | 0.569106 | 0.460681 | 105.7701° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.188328.

### Wording 2

**Child:** Frying vegetables in a pan

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Techniques for cooking food | 0.541264 | 0.490970 | 98.8446° |
| Ways of slicing and chopping ingredients | 0.449660 | 0.389614 | 111.6648° |

RSE selected the **intended** candidate. Forward-minus-reverse entailment: +0.200313.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.491021 | 0.569106 | alternative |
| 1 | 1 | 2 | 0.491021 | 0.484611 | intended |
| 2 | 1 | 1 | 0.479687 | 0.543014 | alternative |
| 2 | 1 | 2 | 0.479687 | 0.449660 | intended |
| 1 | 2 | 1 | 0.549768 | 0.569106 | alternative |
| 1 | 2 | 2 | 0.549768 | 0.484611 | intended |
| 2 | 2 | 1 | 0.541264 | 0.543014 | alternative |
| 2 | 2 | 2 | 0.541264 | 0.449660 | intended |

## F06

Pre-score judgment: a stew made entirely from plant ingredients is a valid refinement of vegetarian meals, but not meat dishes.

### Wording 1

**Child:** Lentil stew made entirely from plant ingredients

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Vegetarian meals | 0.555008 | 0.579526 | 91.8694° |
| Meat dishes | 0.625868 | 0.608987 | 98.4295° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.159554.

### Wording 2

**Child:** A lentil stew made entirely from plant ingredients

| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |
| --- | ---: | ---: | ---: |
| Meals without meat or fish | 0.459323 | 0.528851 | 97.0000° |
| Dishes containing meat | 0.636504 | 0.476989 | 101.4401° |

RSE selected the **alternative** candidate. Forward-minus-reverse entailment: +0.072394.

### Changing the wording independently

| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 1 | 0.555008 | 0.625868 | alternative |
| 1 | 1 | 2 | 0.555008 | 0.632205 | alternative |
| 2 | 1 | 1 | 0.544116 | 0.608298 | alternative |
| 2 | 1 | 2 | 0.544116 | 0.636504 | alternative |
| 1 | 2 | 1 | 0.484039 | 0.625868 | alternative |
| 1 | 2 | 2 | 0.484039 | 0.632205 | alternative |
| 2 | 2 | 1 | 0.459323 | 0.608298 | alternative |
| 2 | 2 | 2 | 0.459323 | 0.636504 | alternative |
