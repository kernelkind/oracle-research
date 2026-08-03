# Fine-segment hierarchy pilot

This artifact preserves geometry only. No generated title influenced a segment or hierarchy merge.

- Input: 194 vectors in 768 dimensions
- Reviewed boundary: 30 passes through `0.453216`, then first failure at `0.446687`
- Partition cutoff between those decisions: `0.449951`
- Fine-segment selection: `MaximalCrossNoteSets`
- Cross-note candidates before maximal filtering: 24
- Strict-subset candidates excluded: 2
- Fine segments selected: 22
- Source notes represented: 36
- Vectors represented: 72
- Singleton fine segments selected: 0
- Unreviewed same-note groups retained only in the source artifact: 32 groups containing 83 vectors
- Higher merges: 21

## Fine segments

- `F000000`: V001 V102 V103 V104
- `F000001`: V003 V004 V023 V099 V101
- `F000002`: V005 V113 V116
- `F000003`: V007 V008 V009 V105 V106 V107
- `F000004`: V010 V028
- `F000005`: V011 V012 V014 V015 V090 V091
- `F000006`: V013 V152
- `F000007`: V035 V051 V060
- `F000008`: V042 V159
- `F000009`: V062 V186
- `F000010`: V063 V170
- `F000011`: V071 V086 V087
- `F000012`: V075 V076 V095 V096 V097
- `F000013`: V078 V092
- `F000014`: V088 V122
- `F000015`: V094 V119
- `F000016`: V100 V114
- `F000017`: V109 V123
- `F000018`: V111 V112 V128
- `F000019`: V117 V118 V127 V133 V136
- `F000020`: V120 V121 V132 V134 V135
- `F000021`: V174 V175 V192 V193

## Complete higher-level merge tree

- `H000000` · cosine `0.505072` · 2 fine segments: `F000002` + `F000003`
- `H000001` · cosine `0.496276` · 2 fine segments: `F000019` + `F000020`
- `H000002` · cosine `0.479633` · 2 fine segments: `F000007` + `F000010`
- `H000003` · cosine `0.419252` · 3 fine segments: `F000018` + `H000001`
- `H000004` · cosine `0.407400` · 2 fine segments: `F000001` + `F000005`
- `H000005` · cosine `0.381002` · 4 fine segments: `F000017` + `H000003`
- `H000006` · cosine `0.380998` · 3 fine segments: `H000000` + `F000004`
- `H000007` · cosine `0.344678` · 5 fine segments: `F000014` + `H000005`
- `H000008` · cosine `0.289317` · 3 fine segments: `F000000` + `H000004`
- `H000009` · cosine `0.287877` · 4 fine segments: `H000006` + `F000011`
- `H000010` · cosine `0.279206` · 2 fine segments: `F000013` + `F000015`
- `H000011` · cosine `0.255925` · 4 fine segments: `H000008` + `F000006`
- `H000012` · cosine `0.254617` · 3 fine segments: `H000002` + `F000021`
- `H000013` · cosine `0.204703` · 4 fine segments: `H000012` + `F000009`
- `H000014` · cosine `0.185290` · 5 fine segments: `H000009` + `F000008`
- `H000015` · cosine `0.175478` · 5 fine segments: `H000011` + `F000012`
- `H000016` · cosine `0.143866` · 7 fine segments: `H000010` + `H000007`
- `H000017` · cosine `0.137602` · 6 fine segments: `H000014` + `F000016`
- `H000018` · cosine `0.096473` · 11 fine segments: `H000013` + `H000016`
- `H000019` · cosine `0.041588` · 11 fine segments: `H000015` + `H000017`
- `H000020` · cosine `0.027366` · 22 fine segments: `H000019` + `H000018`
