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

`K_NODE` is an unassigned integer kind; event IDs, keys and signatures are
abbreviated. The logical node IDs below are examples, not a required format.

```text
{
  "id":"C2", "pubkey":"P", "created_at":1790683200, "kind":K_NODE,
  "tags":[
    ["d","8fc3492dd2094adf96a858c67e1b0394"], ["title","Cooking"],
    ["child","cda491245f344c9286e5dd497d840d52"],
    ["child","243e868f11f9431795e6d3f0fd85a4ae"],
    ["notes_list","cooking-7"],
    ["notes_events","2"], ["notes_per_page","800"]
  ],
  "content":"",
  "sig":"S"
}
```

## Open decisions

- Logical node identity across rebuilds; provider, manifest and root discovery.
- Event kinds, storage and retention; empty lists and oversized events.
- Complete-list download cost; overlap duration and behavior after retirement.
