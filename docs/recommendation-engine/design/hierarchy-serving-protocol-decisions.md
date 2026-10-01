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

`title` names the node. Its `e` tags list immediate child node event IDs in
order. A node with no `e` tags has no children. `content` is empty.

```text
{
  "id":"note1def..def", "pubkey":"npub1abc..abc",
  "created_at":1790683199, "kind":K_NODE,
  "tags":[
    ["title","Cooking"],
    ["e","note1jkl..jkl"],
    ["e","note1mno..mno"],
    ["notes_index","note1pqr..pqr"]
  ],
  "content":"", "sig":"def..def"
}
```

## Note lists — proposed schema

`K_NOTES` and `K_NOTES_INDEX` are unassigned regular kinds in `1000–9999`.

In nodes and indexes, `notes` references a `K_NOTES` page; `notes_index`
references a `K_NOTES_INDEX` index. A node uses exactly one of these tags,
or neither for an empty list.

In an index, all `notes` tags precede all `notes_index` tags:

```text
{
  "id":"note1pqr..pqr", "pubkey":"npub1abc..abc",
  "created_at":1790683198, "kind":K_NOTES_INDEX,
  "tags":[["notes","note1stu..stu"],["notes_index","note1vwx..vwx"]],
  "content":"", "sig":"abc..abc"
}
```

In `K_NOTES`, `e` tags contain note event IDs, in order:

```text
{
  "id":"note1stu..stu", "pubkey":"npub1abc..abc",
  "created_at":1790683197, "kind":K_NOTES,
  "tags":[["e","note1aaa..aaa"],["e","note1bbb..bbb"]],
  "content":"", "sig":"abc..abc"
}
```

Concatenate the pages' note IDs in `notes` tag order, then append each
referenced index's complete sequence in `notes_index` tag order. Apply this
rule recursively.
A missing referenced page or index makes the read incomplete.

An index must not reference itself directly or through other indexes. If
following `notes_index` references revisits an index on the current traversal
path, the list is invalid. Reusing an index in a separate branch is allowed.

Pages and indexes are published by the hierarchy author and served by the same
relay. `content` is empty. The author chooses how many entries fit each event's
byte and tag limits. [NIP-11](https://github.com/nostr-protocol/nips/blob/master/11.md#server-limitations)
