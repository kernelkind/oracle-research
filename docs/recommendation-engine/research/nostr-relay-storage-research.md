# Nostr Relay Storage Research

## Scope

This note estimates the storage required to capture the kind `1` corpus of one large public Nostr relay. It uses direct relay-operator disclosures, with Damus as the primary case and nos.lol and nostr21.com as comparisons.

The central distinction is between:

- The events currently available from a live relay.
- A historical archive exported before the relay was pruned or rebuilt.
- Compact event storage such as NostrDB.
- A relay database such as Strfry, which also stores retrieval indices and may contain fragmentation.

## Conclusion

The best direct historical Damus measurement is the snapshot exported in April 2025:

- **46,338,991 total events.**
- **14,183,529 kind `1` events.**
- **14,632,472,076 bytes, or 13.63 GiB, for the zstd-compressed all-kind snapshot.**

For those 14.18 million kind `1` events, the evidence supports these working estimates:

| Storage form | Estimated size |
|---|---:|
| Compact NostrDB-style event store | 9–13 GB |
| Raw kind `1` JSONL | 10–25 GB |
| Compact indexed Strfry database | 28–43 GB |
| Fragmented or migration-heavy Strfry database | Up to approximately 75 GB |
| Staged capture with temporary files removed promptly | 100 GB provisioned |
| Comfortable workspace retaining the archive, extraction, database, and compaction headroom | 200 GB provisioned |

A Negentropy sync against the current Damus relay does **not** recover this historical corpus. Damus is operated as a short-term, high-availability relay and has been rebuilt repeatedly. In April 2026, jb55 reported that an all-kind-`1` Negentropy sync returned approximately 100,000 notes covering only the preceding three days.

## Damus Relay History

### April 2023: 80 million events and a 243 GB Strfry database

On April 18, 2023, jb55 reported that the [Damus relay was approximately 243 GB](https://nostr.at/nevent1qqsd0um09e0gktcvj0aumekzfdkqag0hpheyae3cxegwdlr3qqukz9sd9q65x). Five days later, he reported [80 million events](https://nostr.at/nevent1qqsprzruh5n52fm6swu89l5hdet4pxqy3deavcv2qmc76j62j5nf0gsknzrkq) and clarified that the [event data occupied 60 GB, its indices occupied hundreds of gigabytes, and a zstd-compressed export occupied 13 GB](https://nostr.at/nevent1qqspakpuvlqtp3q47qxmyx6udphpt3ty9xkdq6wa7tsk6kghrrtgrss72zzgn).

Normalized across the reported 80 million events:

| Representation | Bytes per event |
|---|---:|
| Raw event data | 750 |
| Zstd-compressed export | 163 |
| Indexed relay database | 3,038 |

The indexed database was approximately four times the raw event data. This is consistent with a large Strfry installation whose retrieval indices dominate its event payload.

### November 2023: first documented reset

jb55 described Damus as a fast relay for day-to-day use with [no guarantee of long-term storage](https://nostr.at/nevent1qqsrlrzm2uswrw5kvrdekzpcsap5p968es7486sutwfvfk72c56737g8lvq7k). During the same maintenance episode, he reported the relay database going from [300 GB to 8 MB](https://nostr.at/nevent1qqsrr2mzuv2nms7wvf5wq3kltuyq2fwprqm99yex9gfccvl2usvl2vsull0jx).

The reset explains why later queries against the live relay do not expose its full 2023 corpus.

### April 2025: second reset and historical snapshot

On April 24, 2025, jb55 [announced another relay rebuild](https://nostr.at/nevent1qqsv2037l4ksw3kwp34qkzfcayzhe4wuq4vavwvqput5dza9sumsqsgr7eqgf), retaining profiles and contact lists. Two days later, he published a [snapshot of the preceding two to three years](https://nostr.at/nevent1qqsgz75mtzefxe4jw9ewn3gyxucdytlhdrpnlapw5u9d3teu0csyzhsgahkxx):

```text
https://damus.io/snapshots/damus-relay-2025-04-24.json.zst
```

An HTTP `HEAD` request reports a `Content-Length` of 14,632,472,076 bytes, or 13.63 GiB. This is the entire all-kind snapshot, not just kind `1`.

jb55 also published the snapshot's [complete per-kind counts](https://nostr.at/nevent1qqs87s5dn0wdc77f0skvm7cupp8fltd9zz5rvsx4tu5qhkj73ejhaxgzukl4d). Summing the 905 disclosed kind rows produces 46,338,991 total events. The largest categories were:

| Kind | Events | Share of events |
|---:|---:|---:|
| `7` | 15,383,120 | 33.2% |
| `1` | 14,183,529 | 30.6% |
| `5` | 3,137,859 | 6.8% |
| `4` | 2,112,570 | 4.6% |
| `9735` | 1,879,346 | 4.1% |
| `6` | 1,685,790 | 3.6% |

Kind `1` accounts for 30.6% of the events but likely more than 30.6% of the event bytes because reactions and deletion requests are generally smaller than text notes. The compressed snapshot cannot be allocated precisely by kind without scanning it.

### 2026: current kind `1` is a short rolling window

On April 3, 2026, jb55 reported that a Negentropy sync of [all kind `1` events on Damus returned approximately 100,000 notes from the preceding three days](https://nostr.at/nevent1qqsdxz387cac83z8tdyhlw3dxkk0frxjqscl5he2uvq2s3mrvz2jc5gfply3z).

On April 20, he separately reported a [137 GB Strfry database](https://nostr.at/nevent1qqsdqeg8k2g5jft3wtu62hf8k6w784gwx98funpnk2zh8rswy2yjv3sgr7j9g). That number covers the relay database as a whole. It cannot be converted into a continuous kind `1` history because:

- The relay was reset in November 2023.
- It was reset again in April 2025 while retaining selected replaceable kinds.
- The April 2026 kind `1` sync covered only three days.
- Strfry database size includes indices, retained non-kind-`1` events, and potentially fragmentation.

## Comparable Relay Disclosures

### nos.lol

The nos.lol operator reported:

- [25,295,340 events in a 54 GB database](https://nostr.at/nevent1qqsq3xpp5dyx3n9upkqutk4tf9hzwetwupvxm9q2wkzm44ylnyqes7sq7jqzw) in October 2023: 2,135 bytes per event.
- [More than 70 million events in a 183 GB Strfry database before an upgrade and 138 GB afterward](https://nostr.at/nevent1qqstwf8737g0s3qpxfelkthca65cdjd7rgsmpmjtrh244p2mxqrahysw3whdf) in March 2025: 1,971–2,614 bytes per event.
- A [242 GB database with no operator-initiated pruning up to that point](https://nostr.at/nevent1qqsrgr5w8dkdsgdau6s3urhzjflcgpscxcegkjpj7smtpx4ht36ms0ckrj96z) in March 2026. No contemporaneous event count was disclosed, so this point cannot supply a bytes-per-event ratio.

### nostr21.com

The nostr21.com operator reported:

- [Five million events using approximately 12 GB](https://nostr.at/nevent1qqsqpetz0dhmwe85sa94fuup592pwrp8eg4tkpuzjhyfhyy487qzf8qzl44kf) in August 2023: 2,400 bytes per event.
- [Eleven million events](https://nostr.at/nevent1qqsz2g5jslfg68alyskfklh3nmnhha22g32vxqu4ndqquj99d7w926q4x8ujr) in May 2024.
- At approximately the same time, a [59 GB database whose export was only 9 GB](https://nostr.at/nevent1qqs8mytp40dewtxfw4dhanhj06zug0q6h4x4wuu8f9rr8npfdmsp78s2dck2r). The operator attributed the gap to deleted records and planned compaction or rebuilding.

At 11 million events, those figures correspond to 818 bytes per event in the export but 5,364 bytes per event in the fragmented database. This is direct evidence that an old LMDB file can require more than twice the storage suggested by a compact Strfry ratio.

## Normalized Storage Ratios

Operator-reported `GB` values are treated as decimal gigabytes for normalization. The source values are informal operational disclosures, so the derived ratios should not be interpreted as byte-exact benchmarks.

| Source | Reported state | Bytes/event | Size at 14,183,529 events |
|---|---|---:|---:|
| Damus, 2023 | Indexed Strfry DB | 3,038 | 43.08 GB / 40.12 GiB |
| nos.lol, 2023 | Indexed Strfry DB | 2,135 | 30.28 GB / 28.20 GiB |
| nos.lol, 2025 after upgrade | Indexed Strfry DB | 1,971 | 27.96 GB / 26.04 GiB |
| nostr21.com, 2023 | Indexed relay DB | 2,400 | 34.04 GB / 31.70 GiB |
| nostr21.com, 2024 | Fragmented relay DB | 5,364 | 76.08 GB / 70.85 GiB |

The compact indexed-relay cluster is approximately 2–3 KB per event. Kind mix, tag density, content length, Strfry version, compression dictionaries, and configured indices all affect the actual result.

Strfry documents that it stores data in LMDB, stores event JSON uncompressed by default, and supports optional zstd dictionaries that compress only event JSON rather than retrieval indices. It also documents compaction specifically for reclaiming fragmentation. See the [Strfry storage, compaction, and compression documentation](https://github.com/hoytech/strfry#db-compaction).

## Compact Event-Store Evidence

Two additional jb55 disclosures describe local NostrDB-sized stores rather than relay databases:

- [One million notes occupied 644 MB](https://nostr.at/nevent1qqsx8u3xj6fqkg8s0lvdwz5c8rv5ljl4wj7wvx4h8ckhmcxnz2wpqdqeqzhrs), or 644 bytes per event. Applied to 14,183,529 events, that is 9.13 GB or 8.51 GiB.
- A Negentropy sync of [600,000 notes and 200,000 zaps occupied approximately 700 MB](https://nostr.at/nevent1qqs2kx02v0wzaaqhh3hn86n8nv3h5upja9flnenry9jcsxpny76zpes5wwuth), or 875 bytes per event. Applied to 14,183,529 events, that is 12.41 GB or 11.56 GiB.

These measurements support approximately 9–13 GB for a compact event store at the historical Damus kind `1` count. They should not be used to size a full relay database because they do not include Strfry's retrieval indices.

## Negentropy Storage Implications

[NIP-77](https://github.com/nostr-protocol/nips/blob/master/77.md) reconciles the client's and relay's event-ID sets. It identifies IDs missing on either side but does not transfer the corresponding event bodies. Missing events are subsequently downloaded with ordinary `REQ` messages.

Consequently:

- Negentropy substantially reduces reconciliation traffic when the client already holds most of the relay's set.
- An empty client still downloads every matching event body.
- Negentropy does not reduce the final steady-state storage required for those events.
- A sync is bounded by the relay's current retained set; it cannot recover events removed by a prior reset.

For Damus specifically, a current Negentropy sync and the April 2025 historical snapshot answer different questions. The current sync captures the live rolling set. The snapshot captures the earlier two-to-three-year corpus.

## Recommended Provisioning

### Current live Damus kind `1`

The April 2026 operator measurement was approximately 100,000 events over three days. That set is comfortably below 1 GB in either a compact event store or indexed relay database. Its retention window may change without notice.

### April 2025 historical Damus kind `1`

For extracting and retaining only the 14.18 million kind `1` events:

- **25 GB** is adequate for a compact event store when no full JSON export or relay index is retained.
- **50 GB** is a reasonable target for a freshly built, compact indexed relay containing only kind `1`.
- **100 GB** is the minimum practical workspace when staging the compressed snapshot, extraction, and database sequentially and deleting intermediates promptly.
- **200 GB** is the safer operational allocation when retaining the original archive, extracted data, indexed database, and enough free space for rebuilding or compaction.

These figures exclude media referenced by event URLs. Nostr relay event storage contains the event JSON and signatures, not the referenced images, video, audio, or webpages.

## Research Method

The operator statements were located through bounded, author-scoped searches using the [nostr.wine search API](https://docs.nostr.wine/api), which returns at most 100 events per request. Event IDs, pubkeys, timestamps, contents, and signatures were preserved in the returned Nostr events.

No full relay request, historical event enumeration, or snapshot download was performed. The snapshot byte size came from an HTTP `HEAD` request, and its event totals came from jb55's published per-kind count table.
