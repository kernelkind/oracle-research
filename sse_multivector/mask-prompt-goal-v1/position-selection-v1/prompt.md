Convert an already specified mask into boundary positions in the original text.

The marked original shows exactly what to select using ⟦ and ⟧. These markers are not part of the original text. Keep those selections unchanged.

The indexed original is the same unmarked text with a numbered label at every character boundary. For each marked fragment, select the supplied boundary immediately before it and the supplied boundary immediately after it.

Return only a JSON array of objects with integer "start" and "end" fields, one per marked fragment, in source order.

<marked_original>
{MARKED}
</marked_original>

<indexed_original>
{INDEXED}
</indexed_original>
