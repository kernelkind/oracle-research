# Hierarchy serving protocol

Each author publishes one hierarchy. The hierarchy author and relay operator
are separate roles.

## Opening a hierarchy — proposal

The client starts with the hierarchy author's public key and a relay URL.

The author publishes a signed hierarchy entry event using a dedicated
**replaceable kind** in `10000–19999`; the kind number is not assigned yet.
Its author and kind select the current entry event, so no `d` tag is needed.
[NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds)

For example, connect to `wss://hierarchy.example` and request:

```text
["REQ","sid",{"authors":["npub1abc..abc"],"kinds":[K_ENTRY],"limit":1}]
```

`K_ENTRY` stands for the unassigned kind number. Examples abbreviate event IDs,
public keys and signatures; wire IDs and keys use full lowercase hex.
[NIP-19](https://github.com/nostr-protocol/nips/blob/master/19.md#bare-keys-and-ids)

## Entry event — proposed schema

The entry event's `e` tags list the root node event IDs in order.
The root nodes are served by the same relay. `content` is empty.

```text
{
  "id":"note1abc..abc", "pubkey":"npub1abc..abc",
  "created_at":1790683200, "kind":K_ENTRY,
  "tags":[["e","note1def..def"],["e","note1ghi..ghi"]],
  "content":"", "sig":"abc..abc"
}
```

Fetch the referenced root nodes from that relay:

```text
["REQ","sid",{"ids":["note1def..def","note1ghi..ghi"]}]
```

## Node event — proposed schema

`K_NODE` is an unassigned regular kind in `1000–9999`.
Node events are published by the hierarchy author and served by the same relay.

Each node MUST have exactly one `d` tag with a nonempty identifier, unique
within the author's hierarchy. The identifier MUST stay the same when the
node's title, children or notes change, and MUST NOT be reused for a
different node.

`title` names the node. Its `e` tags list immediate child node event IDs in
order. A node with no `e` tags has no children. `content` is empty.

```text
{
  "id":"note1def..def", "pubkey":"npub1abc..abc",
  "created_at":1790683199, "kind":K_NODE,
  "tags":[
    ["d","7602d719-2393-4fab-93b8-5df19d887eb0"],
    ["title","Cooking"],
    ["e","note1jkl..jkl"],
    ["e","note1mno..mno"],
    ["notes_index","note1pqr..pqr"]
  ],
  "content":"", "sig":"def..def"
}
```

## Note lists — proposed schema

`K_NOTES_INDEX` is an unassigned regular kind in `1000–9999`.

A node uses one `notes_index` tag to reference the index of its note IDs,
or omits the tag for an empty list.

In an index, `e` tags list note event IDs. All `e` tags precede all
`notes_index` tags, which reference further indexes:

```text
{
  "id":"note1pqr..pqr", "pubkey":"npub1abc..abc",
  "created_at":1790683198, "kind":K_NOTES_INDEX,
  "tags":[
    ["e","note1aaa..aaa"],
    ["e","note1bbb..bbb"],
    ["notes_index","note1vwx..vwx"]
  ],
  "content":"", "sig":"abc..abc"
}
```

List the `e` tag values in their tag order, then append each referenced
index's complete sequence in `notes_index` tag order. Apply this rule
recursively.
A missing referenced index makes the read incomplete.

An index must not reference itself directly or through other indexes. If
following `notes_index` references revisits an index on the current traversal
path, the list is invalid. Reusing an index in a separate branch is allowed.

Indexes are published by the hierarchy author and served by the same relay.
`content` is empty. The author chooses how many entries fit each event's
byte and tag limits. [NIP-11](https://github.com/nostr-protocol/nips/blob/master/11.md#server-limitations)
