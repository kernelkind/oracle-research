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

`title` names the node. Its `child` tags list immediate children in tag order.
Each tag contains the child's `d` value followed by its node event ID.
The event ID selects the child version. The referenced event MUST be a
`K_NODE` event by the hierarchy author, and its `d` value MUST match the
tag's identifier.
A node with no `child` tags has no children. `content` is empty.

```text
{
  "id":"note1def..def", "pubkey":"npub1abc..abc",
  "created_at":1790683199, "kind":K_NODE,
  "tags":[
    ["d","7602d719-2393-4fab-93b8-5df19d887eb0"],
    ["title","Cooking"],
    ["child","d288321f-a49b-4dbd-9523-86337d7ad046","note1jkl..jkl"],
    ["child","74286a9a-5768-44ce-8a1a-c4af2f1a2255","note1mno..mno"]
  ],
  "content":"", "sig":"def..def"
}
```

## Note lists — proposed schema

`K_NOTES_LIST` is an unassigned addressable kind in `30000–39999`.
[NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md#kinds)

Each node has a note-list event with exactly one `d` tag matching the node's.
Request the current list from the hierarchy author:

```text
["REQ","sid",{"authors":["npub1abc..abc"],"kinds":[K_NOTES_LIST],"#d":["7602d719-2393-4fab-93b8-5df19d887eb0"],"limit":1}]
```

Clients use the current note list independently of the selected node version.
An empty list has no `e` or `notes_index` tags. A missing list event makes
the read incomplete.

Child nodes do not automatically contribute notes. A child's note is
included only if the author also lists its ID in this node's note list.

In both lists and indexes, `e` tags list note event IDs and `notes_index`
tags reference indexes. All `e` tags precede all `notes_index` tags.

```text
{
  "id":"note1xyz..xyz", "pubkey":"npub1abc..abc",
  "created_at":1790683201, "kind":K_NOTES_LIST,
  "tags":[
    ["d","7602d719-2393-4fab-93b8-5df19d887eb0"],
    ["e","note1ccc..ccc"],
    ["notes_index","note1pqr..pqr"],
    ["notes_index","note1stu..stu"]
  ],
  "content":"", "sig":"abc..abc"
}
```

## Note indexes — proposed schema

`K_NOTES_INDEX` is an unassigned regular kind in `1000–9999`.

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

For both lists and indexes, list the `e` tag values in their tag order, then
append each referenced index's complete sequence in `notes_index` tag order.
Apply this rule recursively.
A missing referenced index makes the read incomplete.

Within a node's note list, each note event ID MUST appear at most once,
whether listed directly or through an index. Indexes MUST NOT overlap,
including nested indexes. The same note ID MAY appear in different nodes' lists.

An index must not reference itself directly or through other indexes. If
following `notes_index` references revisits an index on the current traversal
path, the list is invalid.

Lists and indexes are published by the hierarchy author and served by the
same relay.
`content` is empty. The author chooses how many entries fit each event's
byte and tag limits. [NIP-11](https://github.com/nostr-protocol/nips/blob/master/11.md#server-limitations)
