# Hierarchy serving protocol — decision record

Status: records the design discussion for task **13 · Define Nostr hierarchy
protocol**, as of 2026-09-27. Every point under Decisions was ruled by the user;
proposals appear only under "Awaiting ruling" and "Open points" and are not
decisions. Terminology is defined before it is used. The user makes the design
decisions; the agent proposes. Nothing here authorizes implementation.

## Terminology (approved)

| Term | Meaning |
| --- | --- |
| **hierarchy node** | One position in the hierarchy. *(existing approved vocabulary)* |
| **node record** | The addressable event carrying a hierarchy node's display data: its title and its ordered children (each child's address and title). |
| **node address** | The `d` value identifying a hierarchy node's record; stable across hierarchy changes. |
| **notes page** | The addressable event carrying one ordered page of a node's notes: note event IDs sorted by relevance to the node's title. |
| **hierarchy manifest** | The one event naming the hierarchy and its top node address. |

Retired: "place record" (undefined coinage), "chunk container" (renamed to
*notes page*), "map version" (meant only *hierarchy snapshot*; the static
world-version scheme behind it was rejected).

## What the service is

- A **Nostr API endpoint**: a read-only service speaking Nostr protocol
  messages (`REQ` / `EVENT` / `EOSE` / `CLOSE`), answering queries as a person
  browses.
- It serves completed hierarchy data. It does not build hierarchy data and
  does not run models.
- Existing Nostr standards are used unless it is actually necessary to add
  something new.

## Browsing model (decided)

- The person begins with the top level options, selects one node, and sees
  that node's connections; at any point they can select to see the notes at
  that level. The notes are sorted by relevance to the node's title.
- Navigation is **always downward**.
- **connections** = the direct children of a node, only.
- **notes** = the node's direct notes plus the notes of its children
  recursively, each note once (deduplication rule from
  [User-Directed Subject Navigation](semantic-region-navigation.md)).
- The ordering is served data, computed at build time; the client does not
  rank.

The protocol therefore answers two questions about a hierarchy node — its
connections and its notes — plus the entry point.

## Data model (decided)

- Substrate: **addressable events** (kinds 30000–39999). Stable identifiers
  are maintained for the things that need to be stable; contents change in
  place at the same addresses.
- **hierarchy manifest** — the entry. Found by a plain kind filter; no address
  or discovery round trip needed. It names the hierarchy and its top node
  address. Precedent: nsites root manifests (kind `15128`), NIP-89 handler
  info.
- **node record** — `d` = node address. Content: its title and its ordered
  children as (address, title) pairs. A breadth count per child is **optional**.
- **notes page** — `d` = `<node address>/notes/<number>`. Content: just the
  sorted note IDs of that slice of the node's list.
  - Each node has one list: its level's notes in relevance order. It is split
    into notes pages **only because Nostr events have hard size limits**.
  - Pages are consecutive slices, numbered in their addresses: page 0, 1, 2…
    together they are the whole list, in order.
  - Entries are `e` tags in list order (NIP-01's own reference form), each
    optionally carrying a relay hint as its third element; `content` is empty.
  - Fixed capacity: exactly **N ids per page except the last**, with N budgeted
    so a full page's worst-case encoding fits the smallest event-size cap we
    target (e.g. 256 ids ≈ 18 KB as `e` tags). Relay hints are opportunistic
    and trimmed first; ids are never trimmed.
  - End of list: **a page with fewer than N ids is the end** — read from data,
    never inferred from an empty lookup.
- The client reads the notes themselves with a regular `ids` filter from
  relays. The service stores **no note content**. Optional relay hints are the
  most we do for note availability; we do not mirror kind-1 events.
- Retrieval otherwise uses standard Nostr filter semantics (`kinds`, `#d`,
  `limit`).

## Update model (decided)

- The hierarchy must **not** be assumed static. It is static for the launch
  deliverable, but the protocol must not depend on that.
- Plan for **continuous per-node change**: an update rewrites the records of
  the nodes that changed, at their stable addresses, with new contents.
  Nothing else is republished; there is no world-version scheme.

## Kind numbers (decided, provisional)

- `33001` hierarchy manifest, `33002` node record, `33003` notes page. To be
  checked against the registry-of-kinds before publication.

## Awaiting ruling

- **One-subscription reads.** Because notes pages are only physical
  packaging, a level's list is read with one `REQ` naming that node's notes
  pages. The whole list then arrives as one consistent set from one store
  state, so a client can never mix old and new contents: no stamps, no resync.
  The client renders as pages stream in and sends `CLOSE` when the person
  moves on. Proposed after the earlier reader-side coherence machinery was
  rejected.

## Open points

- **Saved links under continuous change**: whether a shared node address must
  reproduce what the sender saw, or only keep its meaning ("this node") while
  contents drift. This is the design doc's open question "how versions and
  corpus updates affect saved paths"; it is a product decision.
- Exact value of N and the target event-size cap.
- Final kind numbers, after the registry check.

## Rejected directions (do not re-propose)

- **Whole-hierarchy download** ("map bundle") — turns the endpoint into a file
  host; the endpoint answers queries as a person browses.
- **Parent relations as indexed tags** (query `#parent` to find children) —
  inverted lookups that lose the parent's own ordered, curated children list.
- **Global hierarchy version stamp in every record** — any change would bust
  every client cache and force a full republish; incompatible with continuous
  per-node change.
- **Reader-side list-hash stamps with resync-and-skip** — machinery to repair
  reads that the protocol can prevent.
- **Undefined coinages** ("place record", "map version") — terminology must be
  defined and approved before use.
