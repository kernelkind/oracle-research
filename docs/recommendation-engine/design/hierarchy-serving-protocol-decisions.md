# Toy hierarchy snapshot protocol

`toy` `experimental`

This is a toy protocol. It is not recommended for widespread adoption.
Efficient hierarchy updates are out of scope.

The client starts with a hierarchy author's public key and a relay URL.
One author publishes one hierarchy. The author and relay operator are separate.
All hierarchy events come from that author and have empty `content`.
Source notes are fetched separately and need not be on the hierarchy relay.

| Kind | Event | Nostr behavior | Contains |
| --- | --- | --- | --- |
| 18680 | Starting event | Replaceable | Exact root node references |
| 8680 | Node | Regular | UUID, title, exact child references and direct note IDs |

These are experimental kind numbers, not registered allocations. Kind behavior
follows [NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds).
Examples abbreviate event IDs, public keys and signatures.

## Open the snapshot

Request the author's starting event:

```text
["REQ","sid",{"authors":["npub1abc..abc"],"kinds":[18680],"limit":1}]
```

Its `child` tags list all root nodes:

```text
{
  "id":"note1abc..abc", "pubkey":"npub1abc..abc",
  "created_at":1790683200, "kind":18680,
  "tags":[
    ["child","7602d719-2393-4fab-93b8-5df19d887eb0","note1def..def"]
  ],
  "content":"", "sig":"abc..abc"
}
```

Each `child` tag contains a node's UUID followed by its exact event ID.
Fetch that event:

```text
["REQ","sid",{"ids":["note1def..def"]}]
```

## Read a node

```text
{
  "id":"note1def..def", "pubkey":"npub1abc..abc",
  "created_at":1790683199, "kind":8680,
  "tags":[
    ["d","7602d719-2393-4fab-93b8-5df19d887eb0"],
    ["title","Root node"],
    ["child","d288321f-a49b-4dbd-9523-86337d7ad046","note1ghi..ghi"],
    ["e","note1jkl..jkl"],
    ["e","note1mno..mno"]
  ],
  "content":"", "sig":"def..def"
}
```

- `d` is the node's stable UUID.
- `title` is its title.
- Each `child` references an immediate child node by UUID and exact event ID.
- Each `e` references one source note directly assigned to this node.

The root list follows `child` tag order in the starting event. A node's child
list follows its `child` tag order; its notes follow its `e` tag order.
Descendant notes appear in this node only if their IDs are explicitly listed.

Root and immediate-child counts are small. Each node holds at most 500 direct
note IDs. All lists are complete in their containing event; there is no
pagination. Fetching a node for its title also transfers its note IDs.

## Follow the selected events

Clients MUST follow the exact event IDs in the selected starting event and
its referenced nodes. Read the title, children and note IDs from those node
events. The UUID identifies the logical node; it does not select a newer event.

A newer starting event can begin another snapshot read. It does not change an
existing read's references. Cached events with matching IDs remain reusable.

## Validity and missing data

- A node MUST contain exactly one `d` tag with its UUID and exactly one
  `title` tag with a nonempty value. Its UUID MUST NOT identify a different node.
- Every `child` MUST reference a kind 8680 event by the hierarchy author,
  with a `d` matching the UUID in the reference.
- A UUID MUST appear at most once in a root list or immediate-child list.
  A node MAY have multiple parents.
- A UUID MUST NOT repeat along a path through child references.
- A source note ID MUST appear at most once in one node. The same source note
  MAY appear in different nodes.

Malformed recognized tags and references violating these rules are invalid.
Missing referenced node events leave that part of the snapshot unresolved.
Clients MUST NOT replace them with newer events found by UUID.

| Available event | Empty list |
| --- | --- |
| Starting event with no `child` tags | No roots |
| Node with no `child` tags | No children |
| Node with no `e` tags | No direct notes |

A missing node is unresolved, not an empty node. A missing source note does not
change the complete list of IDs recorded in its node.

## Publish a snapshot

Construct children before their parents so their event IDs can be referenced.
Publish the snapshot's node events before its starting event. Readers select
that starting event and follow its exact references while those events remain
available.
