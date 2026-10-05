# Paid relays for the flagship hierarchy

Investigated and provisionally decided October 5, 2026.

## Provisional decision

Use **`wss://cellar.nostr.wine` as the provisional paid relay** for publishing
the flagship hierarchy once it is generated. The user prefers Cellar's metered
payment model because our expected upload is larger than an average person's
Nostr history. A price that grows with stored events is a better fit for this
use than relying on a flat-price promise of unlimited storage.

This selects a candidate; it does not approve spending or publication. Paid
writes of our custom kinds, upload pacing, the actual event count and the
operating period remain to be verified. Protocol agreement and Notedeck
integration remain separate work.

The hierarchy relay needs to store hierarchy events and references to original
posts. **It does not need to retain the original posts.** Clients fetch those
separately. Kind numbers remain experimental, so the provider must accept
custom kinds from funded authors rather than restrict them to a social-post
allowlist. Public hierarchy reads must also work through the queries the
protocol uses.

## Cellar: published policy

[Cellar's documentation](https://docs.nostr.wine/cellar/readme), last updated
November 21, 2023, describes a long-term storage relay funded by a balance
attached to the publishing public key. Its
[current payment page](https://cellar.nostr.wine/) advertises **1 sat per
event/year and a 1,000-sat minimum deposit**.

The documented annual charge is prorated. Duplicates are not charged; kinds
`0`, `3` and `10002` are free for paid users. Authorized deletion requests are
honored without charge. The service advertises indexing, automatic backups,
import/export and public historical queries, with low-balance and renewal
reminders. Exact billing for replaced events and treatment of an exhausted
balance are not explained.

The documentation rejects `4`, `6`, `7`, `1064`, `1984`, `9735` and all
ephemeral events. The live metadata instead advertises zero retention for
`4`, `6`, `7`, `9734`, `9735`, `30311` and `30315`. Zero advertised retention
does not itself prove write rejection. These lists disagree; avoid both sets
when choosing hierarchy kinds, or resolve a relevant conflict before using one.

The operator's [terms](https://nostr.wine/terms) cover the relay and supporting
services. They prohibit flooding and abuse and permit throttling or restricting
access. No numerical bulk-upload rate, total event/byte quota, or requirement
for special approval solely because of a large archive was found. Meeting the
published requirements appears sufficient to use the service; paying does not
establish an unrestricted upload rate or a retention guarantee.

## Cellar: live relay metadata

The following values were read on October 5 from
[the relay endpoint](https://cellar.nostr.wine/) using the HTTP header
`Accept: application/nostr+json`. These are advertised limits, not boundary
tests of paid writes.

| Field | Observed value | Consequence for the hierarchy |
| --- | --- | --- |
| `max_message_length` | `196608` bytes, 192 KiB | Fit the entire serialized incoming JSON message, including the `EVENT` wrapper. |
| `max_event_tags` | `2000` | Fit every event to both this limit and the byte limit. |
| `max_limit` | `1000` | Bound queries and resolve omitted event IDs with further requests. |
| `max_subscriptions` | `50` per connection | Bound simultaneous subscriptions. |
| `max_subid_length` | `71` | Short subscription IDs fit. |
| `min_pow_difficulty` | `0` | No proof-of-work requirement advertised. |
| `auth_required` | `false` | Ordinary public reads worked without authentication. |
| `payment_required`, `restricted_writes` | `true` | Fund the publishing public key before testing writes. |
| `created_at_lower_limit`, `created_at_upper_limit` | `0`, `300` | Documentation explicitly permits historical imports; the precise timestamp boundary was not write-tested. |
| Default `retention.time` | `31536000` seconds, 365 days | Read alongside the recurring annual storage charge; renewal and expiry details remain open. |
| `fees.publication` | `1000` msats | Equals 1 sat; this metadata omits the annual period supplied by the documentation. |

[NIP-11](https://github.com/nostr-protocol/nips/blob/master/11.md#server-limitations)
defines the message limit in serialized UTF-8 bytes and the tag limit as the
number of tag arrays. A tag-heavy event can reach the byte limit before the tag
limit. The draft already allows further pages when items or page references
do not fit; measure the actual encoded events rather than impose one fixed
item count for every page.

## Compatibility with the complete protocol draft

The complete draft supplied by the user for review on October 5 proposes these
experimental kind numbers. This compatibility check does not register the
numbers or approve the protocol.

| Kind | Draft event | Nostr behavior |
| --- | --- | --- |
| `18680` | Hierarchy entry | Replaceable |
| `8680` | Node event | Regular |
| `8681` | Node list page | Regular |
| `38680` | First notes page | Addressable |
| `8682` | Notes page | Regular |

**None is ephemeral, and none appears in either Cellar exclusion list.**
[NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds)
defines ephemeral events as kinds `20000–29999`, which are not expected to be
stored. A new `18680` entry can replace the previous entry for its author. A
new `38680` first notes page can replace the previous page for that author and
`d`. Referenced `8680`, `8681` and `8682` events are regular events fetched by
their exact IDs. Replaceability is compatible with storage and is separate
from ephemeral behavior.

All draft events have empty `content`. Tag-based data and these exact five
kinds still need a funded write test. Existing reads of a different
addressable kind support the choice but do not prove that all custom kinds
will be accepted.

## Read-only checks performed

Bounded queries with `nak 0.16.2` against Cellar confirmed:

- An unauthenticated kind `1` historical read returned an event dated
  December 31, 2023. Storage is not simply limited to events created within
  the preceding year.
- An unauthenticated kind `30078` read returned an addressable event with a
  `d` tag.
- Fetching that same event by its exact ID succeeded.
- Fetching it by author, kind and `#d` succeeded.

The last two queries exercise the forms needed to fetch referenced nodes/pages
and a node's current first notes page. No funds were deposited, events
published, imports triggered, or operators contacted. Bulk-write behavior,
renewals, exports and maximum-size events were not tested.

## Other paid relays considered

Prices and live limits below were checked October 5. Message limits include
the surrounding JSON; they are not promises of equally large event bodies.

| Relay | Advertised payment | Evidence and tradeoff |
| --- | --- | --- |
| [nostr.wine](https://nostr.wine/) | 18,888 sats, one-time admission | Live metadata: 512 KiB messages, 4,000 tags. Public reads, including kind `30078` and the ID/author/kind/`d` queries, worked without authentication. Flat admission pricing is less aligned with the user's preference for paying in proportion to this archive. |
| [nostr.land](https://nostr.land/subscribe) | Plus: 60,000 sats for one year | Personal archive/import advertised. Live metadata: 65,535-byte messages, 2,000 tags. Corresponding public reads worked. Its [fair-use terms](https://nostr.land/terms) allow restrictions for disruptive use; archive volume is not priced per event. |
| [relay.nostr.build](https://relay.nostr.build/) | Included in paid plans, starting at $18/year | Advertises no event-count or retention cap and continued storage after subscription expiry. Website event cap: 64 KB; live incoming-message cap: 96 KiB, 2,500 tags. Public reads required NIP-42 authentication; a fresh unpaid signer could read. The current Notedeck relay handler records AUTH challenges without answering them, so integration would require additional work. |

The nostr.build authentication observation is grounded in
`nd-oracle-mvp/crates/enostr/src/relay/outbox/service/mod.rs`, in the
`RelayMessage::Auth` branch, as inspected October 5. Its website and live
metadata also disagree about pricing: metadata advertises 69,000 sats admission
while the website offers the $18/year plan. The table reports the current
website offer, not a resolved explanation of that discrepancy.

[nostrbtc](https://nostrbtc.com/guide) advertises 21,000 sats/year and free
reads, but its documented custom kind `9999` serves a specific schema rather
than proving arbitrary hierarchy-kind acceptance. Live relay access failed
from the investigation environment; this does not establish a general outage.
[relay.tools managed feeds](https://feeds.relay.tools/) were also considered.
Configurable kind policies are possible in its
[public example configuration](https://code.relay.tools/api/v4/projects/opensauce%2Fnewlay/repository/files/docs%2Fnewlay.example.toml/raw?ref=main),
but that example is not a deployed-service commitment. Neither displaced Cellar.

## Verification before publishing the hierarchy

1. Agree the event kinds and protocol. Count billable events and measure the
   largest encoded message and tag count. Include regular events retained
   across hierarchy updates when estimating ongoing cost.
2. Estimate the total charge for the intended operating period and obtain
   spending approval within the project's $1,000 lifetime paid-resource cap.
   Hosting estimates and accounting follow
   [release planning](../../planning/release-decisions.md#compute-hosting-and-budget).
3. After an approved deposit, publish a minimal hierarchy using every selected
   kind, including an empty first notes page. Confirm accepted writes, exact-ID
   reads, author/kind/`#d` reads, and replacement of the entry and first notes
   page while referenced regular events remain readable.
4. Pace the full upload, handle throttling and verify that every referenced
   hierarchy event can be retrieved. Recheck policy if actual kinds or limits
   differ from this investigation.

The advertised base rate would make 100,000 billable stored events cost
100,000 sats for one year. This is an illustrative calculation, not our
measured hierarchy size or an approved allocation. Original post IDs within
one hierarchy event are references, not separately uploaded original posts.

The most useful next step is the small funded compatibility test once the
protocol and spending are approved. Contacting the operator is warranted only
for a requirement that remains unclear and affects the actual upload; special
permission for high total volume is not a published prerequisite found here.
