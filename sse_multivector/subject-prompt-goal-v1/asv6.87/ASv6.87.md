Build a hierarchy of this social-media post's subjects, like a book's subject index. Begin by understanding the complete post before dividing it into subjects.

Use the complete post to resolve each reference and local description to its most specific supported referent, including meaning established by a title, enclosing heading, list or shared predicate. A local role or purpose does not replace a supported enclosing relationship: retain both in the complete specific subject and expressed combination. General knowledge may clarify language, identify referents, and recognize subjects, but every entity, modifier, action, and relationship in an entry must be stated or reasonably implied by the post.

Interpret names, labels, and hashtags by what they refer to; their component words alone do not establish a literal description. For an unresolved named subject, retain its name.

URLs and opaque encoded identifiers—including, but not limited to, Nostr public keys (`npub1…`), event IDs (`nevent1…`), and cryptographic hashes—provide no subject evidence. The surrounding prose may still establish subjects involving URLs or identifiers.

If ambiguity remains after understanding the complete post, give each supported interpretation its own directly stated subject, without uncertainty qualifiers. Co-mention or statement order alone does not establish relationships. Do not add commentary about plausibility or what is unclear or unstated.

For numbers in subject text, preserve what they refer to; any count or measurement interpretation and units must be supported by the post. Include calculated results only if explicitly stated.

Return only one JSON object with a `subjects` array containing the completed hierarchy. Present it broad-to-specific using section-style numbering (`1`, `1.1`, `1.1.1`), listing each heading before its subheadings. Return an object for each hierarchy entry with `number`, then `context`, then `subject`.

In `context`, identify the subject and the source context establishing its meaning. This may describe a particular instance supporting a general heading.

In `subject`, name the subject at that entry's level of generality. Keep details distinguishing a particular instance in its subheading, rather than importing them from `context` into the general heading. Each heading must be understandable without the post, its `context`, or other entries; it need not retell what the post says about the subject. Preserve the heading's meaning, negation, and relationships. For comparison entries, name both sides when provided. Make the wording concise.

<example>
<post>
Food seasoning: salt.

Food ingredients for the dog:
One piece of connective tissue and two meat scraps.
Mixing it with them.

Separately, connective tissue for the dog.
</post>

<explanation>
Before deriving headings, resolve "it" and "them" and enumerate the complete specific source subjects: "Salt for food seasoning"; "Connective tissue for the dog"; "One piece of connective tissue as a food ingredient for the dog"; "Two meat scraps as food ingredients for the dog"; "One piece of connective tissue and two meat scraps as food ingredients for the dog"; and "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps". Then derive the displayed broader material, recipient, food-role and mixing headings. Salt and connective tissue can have nonfood uses; tissue merely "for the dog" could be for a training scent. Those unrestricted headings stay outside Food and Dog food. After checking the heading meanings, collect both ingredient subjects, their complete group and full mixing action beneath every compatible parent copy, including both Dog food branches. Keep individual materials and Dogs alongside the action. The separate recipient clause adds no ingredient relationship. Number the completed hierarchy.
</explanation>

<output>
{"subjects": [
  {"number": "1", "context": "Food seasoning: salt.", "subject": "Salt"},
  {"number": "1.1", "context": "Food seasoning: salt.", "subject": "Salt for food seasoning"},
  {"number": "2", "context": "Connective tissue in the ingredients list and separate dog-recipient clause.", "subject": "Connective tissue"},
  {"number": "2.1", "context": "Separately, connective tissue for the dog.", "subject": "Connective tissue for the dog"},
  {"number": "2.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "2.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "2.1.1.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "3", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Meat scraps"},
  {"number": "3.1", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "3.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "3.1.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "4", "context": "Food ingredients for the dog and the separate tissue for the dog.", "subject": "Dogs"},
  {"number": "4.1", "context": "The Food ingredients for the dog list and its mixing action.", "subject": "Dog food"},
  {"number": "4.1.1", "context": "The Food ingredients for the dog list.", "subject": "Dog-food ingredients"},
  {"number": "4.1.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "4.1.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.1.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "4.1.1.2", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.2.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.2.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "4.1.1.3", "context": "Mixing it with them under the Food ingredients for the dog heading.", "subject": "Mixing food ingredients for the dog"},
  {"number": "4.1.1.3.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "4.2", "context": "Separately, connective tissue for the dog.", "subject": "Connective tissue for the dog"},
  {"number": "4.2.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "4.2.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.2.1.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "5", "context": "Food seasoning and the Food ingredients for the dog list.", "subject": "Food"},
  {"number": "5.1", "context": "Food seasoning: salt.", "subject": "Food seasoning"},
  {"number": "5.1.1", "context": "Food seasoning: salt.", "subject": "Salt for food seasoning"},
  {"number": "5.2", "context": "The Food ingredients for the dog list and its mixing action.", "subject": "Dog food"},
  {"number": "5.2.1", "context": "The Food ingredients for the dog list.", "subject": "Dog-food ingredients"},
  {"number": "5.2.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "5.2.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.1.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "5.2.1.2", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.2.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.2.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "5.2.1.3", "context": "Mixing it with them under the Food ingredients for the dog heading.", "subject": "Mixing food ingredients for the dog"},
  {"number": "5.2.1.3.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"},
  {"number": "6", "context": "Mixing it with them.", "subject": "Mixing"},
  {"number": "6.1", "context": "Mixing it with them under the Food ingredients for the dog heading.", "subject": "Mixing food ingredients for the dog"},
  {"number": "6.1.1", "context": "Food ingredients for the dog list; it = the tissue piece, them = two meat scraps.", "subject": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps"}
]}
</output>
</example>

<example>
<post>
On my first use, the new app #RavenWorks was a lifesaver, figuratively speaking, unless AmberLoop blocked it—how could I not appreciate the app on that first use?
</post>

<explanation>
The unless clause qualifies the first-use help and names its blocker. Its complete subject retains the new app, first use and AmberLoop relationship beneath every copy of both component headings. The blocking heading names the same new app; the unresolved name AmberLoop does not establish an app or any other type for the blocker. Conditional subjects name the topics without asserting that the blocking occurred.
</explanation>

<output>
{"subjects": [
  {"number": "1", "context": "The app #RavenWorks.", "subject": "Apps"},
  {"number": "1.1", "context": "The app named #RavenWorks.", "subject": "RavenWorks app"},
  {"number": "1.1.1", "context": "The new app #RavenWorks.", "subject": "New RavenWorks app"},
  {"number": "1.1.1.1", "context": "My first use of the new app #RavenWorks.", "subject": "First use of the new RavenWorks app"},
  {"number": "1.1.1.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "1.1.1.1.2", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "1.1.1.2", "context": "The new app was a figurative lifesaver.", "subject": "Help from the new RavenWorks app"},
  {"number": "1.1.1.2.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.2.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "1.1.1.3", "context": "Appreciate it; it = the new app #RavenWorks.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "1.1.1.3.1", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "1.1.1.4", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "1.1.1.4.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "2", "context": "Lifesaver, figuratively speaking.", "subject": "Help"},
  {"number": "2.1", "context": "The new app was a figurative lifesaver.", "subject": "Help from the new RavenWorks app"},
  {"number": "2.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "2.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "3", "context": "How could I not appreciate it?", "subject": "Appreciation"},
  {"number": "3.1", "context": "Appreciate it; it = the new app #RavenWorks.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "3.1.1", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "4", "context": "On my first use.", "subject": "First use"},
  {"number": "4.1", "context": "My first use of the new app #RavenWorks.", "subject": "First use of the new RavenWorks app"},
  {"number": "4.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "4.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "4.1.2", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "5", "context": "AmberLoop names the blocker; its type is unresolved.", "subject": "AmberLoop"},
  {"number": "5.1", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "5.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "6", "context": "The conditional clause names blocking.", "subject": "Blocking"},
  {"number": "6.1", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "6.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"}
]}
</output>
</example>

<example>
<post>
https://birds.example/repair?count=12
8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{"subjects": []}
</output>
</example>

<example>
<post>
Profile URL: https://birds.example/repair?count=12
Event ID: 8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f
</post>

<output>
{"subjects": [
  {"number": "1", "context": "Profile URL labels the URL.", "subject": "URLs"},
  {"number": "1.1", "context": "Profile URL labels the URL.", "subject": "Profile URLs"},
  {"number": "2", "context": "Profile URL labels the URL.", "subject": "Profiles"},
  {"number": "2.1", "context": "Profile URL labels the URL.", "subject": "Profile URLs"},
  {"number": "3", "context": "Event ID labels the identifier.", "subject": "Identifiers"},
  {"number": "3.1", "context": "Event ID labels the identifier.", "subject": "Event identifiers"},
  {"number": "4", "context": "Event ID labels the identifier.", "subject": "Events"},
  {"number": "4.1", "context": "Event ID labels the identifier.", "subject": "Event identifiers"}
]}
</output>
</example>

<example>
<post>
I saw her duck. I bought a notebook.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "Her duck, read as a noun.", "subject": "Ducks"},
  {"number": "1.1", "context": "Her duck, read as her animal.", "subject": "A person's duck"},
  {"number": "1.1.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "2", "context": "Her duck, read as an action.", "subject": "Ducking"},
  {"number": "2.1", "context": "Her duck, read as a person ducking.", "subject": "A person ducking"},
  {"number": "2.1.1", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "3", "context": "Her refers to a person.", "subject": "People"},
  {"number": "3.1", "context": "Her duck, read as her animal.", "subject": "A person's duck"},
  {"number": "3.1.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "3.2", "context": "Her duck, read as a person ducking.", "subject": "A person ducking"},
  {"number": "3.2.1", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "4", "context": "I saw her duck.", "subject": "Observation"},
  {"number": "4.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "4.2", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "5", "context": "I bought a notebook.", "subject": "Notebooks"},
  {"number": "5.1", "context": "I bought a notebook.", "subject": "Purchase of a notebook"},
  {"number": "6", "context": "I bought a notebook.", "subject": "Purchases"},
  {"number": "6.1", "context": "I bought a notebook.", "subject": "Purchase of a notebook"}
]}
</output>
</example>

<example>
<post>
2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "2 cables: A and B.", "subject": "Cables"},
  {"number": "1.1", "context": "A is 2 m long; B is 3 m long.", "subject": "Cable lengths"},
  {"number": "1.1.1", "context": "Cable A is 2 m long.", "subject": "2 m cables"},
  {"number": "1.1.1.1", "context": "Cable A is 2 m long.", "subject": "2 m cable A"},
  {"number": "1.1.1.1.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.1.1.1.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.2", "context": "Cable B is 3 m long.", "subject": "3 m cables"},
  {"number": "1.1.2.1", "context": "Cable B is 3 m long.", "subject": "3 m cable B"},
  {"number": "1.1.2.1.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.2.1.1.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.3", "context": "A is not longer than B.", "subject": "Cable length comparisons"},
  {"number": "1.1.3.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.2", "context": "2 cables: A and B.", "subject": "Pairs of cables"},
  {"number": "1.2.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.2.1.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"}
]}
</output>
</example>

<example>
<post>
2 + 3 = 5.
</post>

<output>
{"subjects": [
  {"number": "1", "context": "2 + 3 = 5.", "subject": "Arithmetic"},
  {"number": "1.1", "context": "2 + 3 = 5.", "subject": "Addition"},
  {"number": "1.1.1", "context": "2 and 3 are added.", "subject": "Addends"},
  {"number": "1.1.1.1", "context": "2 is added to 3.", "subject": "2 as an addend"},
  {"number": "1.1.1.1.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.1.2", "context": "3 is added to 2.", "subject": "3 as an addend"},
  {"number": "1.1.1.2.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.2", "context": "The stated sum is 5.", "subject": "Addition results"},
  {"number": "1.1.2.1", "context": "The stated sum is 5.", "subject": "5 as an addition result"},
  {"number": "1.1.2.1.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"}
]}
</output>
</example>

For each enumerated subject, derive broader headings by generalizing its meaning without adding restrictions. An item's usual purpose is not a property of every instance: a purpose-qualified heading cannot contain an unrestricted item heading. Compare only the proposed `subject` strings across possible posts in any domain, including uses unlike the one described here. Classify what each heading necessarily means; the domain of this post cannot narrow an unrestricted heading. A child heading must itself preserve every restriction of its parent: type, purpose, modifier, action, negation and relationship. Imagine another post that fits the child heading: if it could fail to fit the proposed parent heading, broaden the parent or keep the supported restriction in the child wording. The post, `context` and other entries cannot supply a restriction missing from a heading.

Determine the valid relationships before numbering. For each returned heading, collect every enumerated source subject whose own wording passes the parent check. Use that complete collection beneath every numbered occurrence of the heading, even when its surrounding branch differs. Combine shared headings and give every heading and subheading its own entry. Before returning JSON, check each completed parent-child pair using only its two heading strings; broaden the parent or preserve the supported restriction in the child if needed, while retaining the source subject. Read every source clause again: its specific referents, amounts, modifiers, negation and expressed relationships must still be present in subject headings, not only contexts. Finally, check every numbered parent occurrence for its complete collection of source subjects. A placement elsewhere cannot repair a missing branch.

With the post's meaning understood, first enumerate all specific subjects it expresses before deriving broader headings. Include subjects conveyed literally, nonliterally, or rhetorically by individual parts, multiple parts together, or the post as a whole, even when no phrase names them. Retain individual subjects, their particular instances and every expressed combination, with their complete supported referents, amounts, modifiers, negation and relationships in the subject strings; a description of an event does not replace the subjects involved.
