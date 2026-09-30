# Hierarchy serving protocol

Decision baseline reconstructed from discussion; wording awaiting review.

## Agreed behavior

- One hierarchy per endpoint; nodes expose ordered immediate children.
- Notes queries return ordered, deduplicated direct note event IDs.
- Notes may belong to several nodes; nodes may have several parents.
- Clients fetch actual note events from other relays. Masks are not involved.
- Updates preserve browsing: older and newer completed data overlap before retirement.
- Node creation, removal and metadata changes are independent of notes changes.

## Direct-note lists

| Node metadata | Meaning |
| --- | --- |
| `notes_list` | Identity of a completed ordered list |
| `notes_events` | Number of pagination events |
| `notes_per_page` | Provider-chosen IDs per full page; last page may be smaller |

Pages have `d = <notes_list>/<zero-based index>`. Providers choose capacity
to fit relay limits; there is no protocol-wide cap. Page count establishes
the end; a missing page is an incomplete read.

Publish all pages of a modified list before changing the node's reference.
Use a fresh list ID and retain earlier pages during overlap. Reuse unchanged
lists when only node metadata changes.

## Current node list — provisional

The manifest names `nodes_list` and `nodes_events`. Its pages form a complete
mapping of logical node IDs to exact node-record event IDs. Clients reuse
unchanged cached records and fetch changed or needed records.
Absence establishes removal only after the complete mapping is received.

## Node record — proposed schema

Providers assign opaque node IDs unique within the hierarchy; titles may repeat.
`d` carries the node ID; ordered `child` tags carry child IDs. The node-list
mapping uses those same IDs as keys. Put notes-list settings in tags; leave
`content` empty.

`K_NODE` is an unassigned integer kind. Examples display shortened `note1…` IDs
and `npub1…` keys; [wire values are hex](https://github.com/nostr-protocol/nips/blob/master/19.md#bare-keys-and-ids).
Signatures are abbreviated. Logical node IDs are examples, not a required format.

```text
{
  "id":"note1abc..abc", "pubkey":"npub1abc..abc", "created_at":1790683200, "kind":K_NODE,
  "tags":[
    ["d","8fc3492dd2094adf96a858c67e1b0394"], ["title","Cooking"],
    ["child","cda491245f344c9286e5dd497d840d52"],
    ["child","243e868f11f9431795e6d3f0fd85a4ae"],
    ["notes_list","cooking-7"],
    ["notes_events","2"], ["notes_per_page","800"]
  ],
  "content":"",
  "sig":"abc..abc"
}
```

## Node-record kind and retention — proposed

- `K_NODE` uses a regular kind in `1000–9999`; its final number is open.
- `d` identifies the logical node without replacing older signed records.
- Updates create new event IDs with the same logical node ID. Reuse unchanged
  signed records.
- Keep every record referenced by a current or overlapping node list queryable,
  together with its notes pages. Retiring an older list must not remove data
  still referenced by a served list.

Regular kinds avoid addressable replacement discarding an earlier record
during overlap. [NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds)

## Notes page — proposed schema

`K_NOTES` uses a regular kind in `1000–9999`; its number remains open.
[NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds)

The page is signed by the same provider as its referencing node record.
Example: final page `1`; page `0` contains 800 IDs. Values use the notation above.

```text
{
  "id":"note1def..def", "pubkey":"npub1abc..abc", "created_at":1790683199, "kind":K_NOTES,
  "tags":[["d","cooking-7/1"],["e","note1aaa..aaa"],["e","note1ddd..ddd"]],
  "content":"",
  "sig":"def..def"
}
```

`e` tags contain note event IDs in served order. Read pages by index.
Never overwrite published pages or reuse list IDs under the provider's public key.

## Open decisions

- Logical node identity across rebuilds; provider, manifest and root discovery.
- Event kinds, storage and retention; empty lists and oversized events.
- Complete-list download cost; overlap duration and behavior after retirement.
