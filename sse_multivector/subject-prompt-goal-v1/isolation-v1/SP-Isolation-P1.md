Collect supplied complete source subjects beneath supplied subject-index parent occurrences. Do not discover additional subjects, derive headings or build a tree. An action concerning an object can fit that object's subject-index topic.

Compare only the proposed subject strings across possible posts in any domain. A child heading must itself preserve every restriction of its parent: type, purpose, modifier, action, negation and relationship. Imagine another post that fits the child heading: if it could fail to fit the proposed parent heading, the child does not belong there. The post, context and other entries cannot supply a restriction missing from a heading.

For each supplied parent heading, collect every supplied source subject whose own wording passes this parent check. Use that complete collection beneath every numbered occurrence of the parent heading, even when another parent copy has the same heading. Return one entry for every supplied parent number, including an empty subject_ids array when no supplied subject fits. Order of subject IDs is immaterial. Keep the supplied IDs and numbers exactly. Return only {"placements": [{"parent_number": "number", "subject_ids": ["source ID"]}]}.

Complete source subjects:
{SUBJECTS}

Parent occurrences:
{PARENTS}
