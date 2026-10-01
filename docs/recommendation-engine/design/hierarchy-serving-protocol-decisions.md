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
    ["e","note1mno..mno"]
  ],
  "content":"", "sig":"def..def"
}
```
