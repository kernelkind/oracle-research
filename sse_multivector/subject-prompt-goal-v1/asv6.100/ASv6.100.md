Build a hierarchy of this social-media post's subjects, like a book's subject index. Understand the complete post before dividing it into subjects.

Resolve each reference or local description to the complete supported description of its referent for that occurrence, using the whole post, including titles, enclosing headings, lists and shared predicates. Before deriving broader headings, enumerate all specific subjects expressed literally, nonliterally or rhetorically by individual parts, combined parts or the whole post, even when unnamed. Retain individual subjects, particular instances and every expressed combination with their complete supported referents, amounts, modifiers, negation, enclosing relationships—including list membership—and local roles or purposes in `subject`; event descriptions do not replace the subjects involved. General knowledge may clarify language, identify referents and recognize subjects; every entity, modifier, action and relationship must be stated or reasonably implied by the post.

Interpret names, labels and hashtags by what they refer to; their component words alone do not establish literal descriptions. Retain the name of an unresolved named subject.

URLs and opaque encoded identifiers, including Nostr public keys (`npub1…`), event IDs (`nevent1…`) and cryptographic hashes, provide no subject evidence. Surrounding prose may establish subjects involving them.

If ambiguity remains after understanding the complete post, give every supported interpretation its own directly stated subject without uncertainty qualifiers. Co-mention or statement order alone does not establish relationships. Add no commentary about plausibility or what is unclear or unstated.

Preserve what numbers refer to; count or measurement interpretations and units must be supported by the post. Include calculated results only when explicitly stated.

Make each `subject` concise, understandable without the post, `context` or other entries, and faithful to its meaning, negation and relationships. Name both comparison sides when provided. A heading names its subject at its level of generality; it need not retell the post's assertion about it. Broader headings may omit instance details; complete source subjects retain those details in their own specific headings.

Derive broader headings by generalizing source meanings without adding restrictions. Judge each parent-child pair using only its `subject` strings across possible posts in any domain. The child itself must preserve every parent restriction: type, purpose, modifier, action, negation and relationship. If another post could fit the child but fail to fit the parent, broaden the parent or preserve the supported restriction in the child. A usual purpose does not restrict every instance; a purpose-qualified heading cannot contain an unrestricted item heading. The post's domain, `context` and other entries cannot supply a missing heading restriction.

Determine valid relationships before numbering, combine shared headings, and give every heading and subheading its own entry. For each complete source subject, compare its own wording with every returned heading using the parent check. An equal-meaning heading's own entry already represents the source subject; include it among the descendants of every more-general compatible heading, independently at every numbered occurrence even when surrounding branches differ. Placement elsewhere cannot repair a missing branch.

Return only one JSON object with a `subjects` array. Each entry has `number`, then `context`, then `subject`. Use section-style numbering (`1`, `1.1`, `1.1.1`), broad to specific, listing every heading before its subheadings. In `context`, identify the subject and the source establishing its meaning; this may describe a particular instance supporting a general heading.

<example>
<post>
Food seasoning: sea salt.

Food ingredients for the dog:
One piece of connective tissue and two meat scraps.
Cutting it and them with a knife when a bowl is empty.

Separately, connective tissue for the dog.
</post>

<explanation>
The post expressly gives sea salt a food-seasoning purpose, so its complete source subject retains "for food seasoning". Sea salt also belongs under Food: nonfood uses do not disqualify a food substance from that class. Both Sea salt occurrences retain the complete purpose-qualified subject. The ingredients heading makes the counted tissue and scraps food ingredients for the dog; "it" and "them" resolve to that piece and those two scraps. Cutting with the knife applies to each part and to both together: keep each partial cutting subject and the complete shared action. The Knife branch and the named bowl condition each retain both individual actions and their shared action; copying only the shared action there would omit the individual sources. The bowl is neither the cutting object nor the knife: its empty state conditions each action and their combination. Every complete action names the knife and the bowl condition, so its own wording supports both relationships without borrowing context. The condition subject names the topic without asserting that a bowl is actually empty. The partial actions do not replace their expressed combination. The complete cutting subject belongs below each partial action and below the complete ingredient group; the reverse directions lose a material or action restriction. Each complete source subject appears beneath every compatible parent copy, including both Dog food branches. An entry already represents a source subject with the same meaning; the complete shared cutting action has no identical descendant, but still appears beneath every compatible group and partial-action occurrence. The separate tissue "for the dog" clause specifies a recipient without stating an ingredient relationship. Separate Sea salt, Connective tissue, Meat scraps and Dogs subjects remain alongside the actions. Their optional general headings need not repeat a particular use.
</explanation>

<output>
{"subjects": [
  {"number": "2", "context": "Connective tissue in the ingredients list and separate dog-recipient clause.", "subject": "Connective tissue"},
  {"number": "3", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Meat scraps"},
  {"number": "4", "context": "Food ingredients for the dog and the separate tissue for the dog.", "subject": "Dogs"},
  {"number": "2.1", "context": "Separately, connective tissue for the dog.", "subject": "Connective tissue for the dog"},
  {"number": "4.2", "context": "Separately, connective tissue for the dog.", "subject": "Connective tissue for the dog"},
  {"number": "5", "context": "Food seasoning and the Food ingredients for the dog list.", "subject": "Food"},
  {"number": "1", "context": "Food seasoning: sea salt.", "subject": "Sea salt"},
  {"number": "5.3", "context": "Food seasoning: sea salt. Sea salt is a food substance.", "subject": "Sea salt"},
  {"number": "4.1", "context": "The Food ingredients for the dog list and its cutting action.", "subject": "Dog food"},
  {"number": "5.2", "context": "The Food ingredients for the dog list and its cutting action.", "subject": "Dog food"},
  {"number": "4.1.1", "context": "The Food ingredients for the dog list.", "subject": "Dog-food ingredients"},
  {"number": "5.2.1", "context": "The Food ingredients for the dog list.", "subject": "Dog-food ingredients"},
  {"number": "2.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "4.1.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "4.2.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "5.2.1.1", "context": "One piece of connective tissue in the Food ingredients for the dog list.", "subject": "One piece of connective tissue as a food ingredient for the dog"},
  {"number": "3.1", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.2", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.2", "context": "Two meat scraps in the Food ingredients for the dog list.", "subject": "Two meat scraps as food ingredients for the dog"},
  {"number": "2.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "3.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.1.1.2.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "4.2.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.1.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "5.2.1.2.1", "context": "Food ingredients for the dog: one piece of connective tissue and two meat scraps.", "subject": "One piece of connective tissue and two meat scraps as food ingredients for the dog"},
  {"number": "5.1", "context": "Food seasoning: sea salt.", "subject": "Food seasoning"},
  {"number": "1.1", "context": "Food seasoning: sea salt.", "subject": "Sea salt for food seasoning"},
  {"number": "5.1.1", "context": "Food seasoning: sea salt.", "subject": "Sea salt for food seasoning"},
  {"number": "5.3.1", "context": "Food seasoning: sea salt.", "subject": "Sea salt for food seasoning"},
  {"number": "6", "context": "Cutting it and them with a knife when a bowl is empty.", "subject": "Cutting"},
  {"number": "7", "context": "Cutting it and them with a knife when a bowl is empty.", "subject": "Knife"},
  {"number": "8", "context": "When a bowl is empty names the cutting condition, without asserting actual emptiness.", "subject": "A bowl being empty"},
  {"number": "2.1.1.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.1.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "4.2.1.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.1.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "6.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "7.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "8.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = the counted tissue piece.", "subject": "Cutting one piece of connective tissue as a food ingredient for the dog with a knife when a bowl is empty"},
  {"number": "3.1.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.2.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.2.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "6.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "7.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "8.2", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; them = the two meat scraps.", "subject": "Cutting two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "2.1.1.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "2.1.1.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "3.1.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "3.1.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.1.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.1.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.2.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.1.1.2.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.2.1.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "4.2.1.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.1.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.1.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.2.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "5.2.1.2.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "6.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "6.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "7.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "7.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "8.1.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"},
  {"number": "8.2.1", "context": "Cutting it and them with a knife when a bowl is empty under the ingredient heading; it = one tissue piece, them = two meat scraps.", "subject": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog with a knife when a bowl is empty"}
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
  {"number": "2", "context": "Lifesaver, figuratively speaking.", "subject": "Help"},
  {"number": "1.1.1.2", "context": "The new app was a figurative lifesaver.", "subject": "Help from the new RavenWorks app"},
  {"number": "2.1", "context": "The new app was a figurative lifesaver.", "subject": "Help from the new RavenWorks app"},
  {"number": "3", "context": "How could I not appreciate it?", "subject": "Appreciation"},
  {"number": "1.1.1.3", "context": "Appreciate it; it = the new app #RavenWorks.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "3.1", "context": "Appreciate it; it = the new app #RavenWorks.", "subject": "Appreciation for the new RavenWorks app"},
  {"number": "4", "context": "On my first use.", "subject": "First use"},
  {"number": "1.1.1.1", "context": "My first use of the new app #RavenWorks.", "subject": "First use of the new RavenWorks app"},
  {"number": "4.1", "context": "My first use of the new app #RavenWorks.", "subject": "First use of the new RavenWorks app"},
  {"number": "1.1.1.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.2.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "2.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "4.1.1", "context": "The new app was a figurative lifesaver on first use.", "subject": "Help from the new RavenWorks app on first use"},
  {"number": "1.1.1.1.2", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "1.1.1.3.1", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "3.1.1", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "4.1.2", "context": "Appreciate it on that first use; it = the new app.", "subject": "Appreciation for the new RavenWorks app on first use"},
  {"number": "5", "context": "AmberLoop names the blocker; its type is unresolved.", "subject": "AmberLoop"},
  {"number": "6", "context": "The conditional clause names blocking.", "subject": "Blocking"},
  {"number": "1.1.1.4", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "5.1", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "6.1", "context": "Unless AmberLoop blocked it; it = the new app.", "subject": "AmberLoop blocking the new RavenWorks app"},
  {"number": "1.1.1.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "1.1.1.2.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "1.1.1.4.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "2.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "4.1.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
  {"number": "5.1.1", "context": "First-use figurative help, unless AmberLoop blocked it; it = new app.", "subject": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app"},
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
  {"number": "2", "context": "Profile URL labels the URL.", "subject": "Profiles"},
  {"number": "1.1", "context": "Profile URL labels the URL.", "subject": "Profile URLs"},
  {"number": "2.1", "context": "Profile URL labels the URL.", "subject": "Profile URLs"},
  {"number": "3", "context": "Event ID labels the identifier.", "subject": "Identifiers"},
  {"number": "4", "context": "Event ID labels the identifier.", "subject": "Events"},
  {"number": "3.1", "context": "Event ID labels the identifier.", "subject": "Event identifiers"},
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
  {"number": "2", "context": "Her duck, read as an action.", "subject": "Ducking"},
  {"number": "3", "context": "Her refers to a person.", "subject": "People"},
  {"number": "1.1", "context": "Her duck, read as her animal.", "subject": "A person's duck"},
  {"number": "3.1", "context": "Her duck, read as her animal.", "subject": "A person's duck"},
  {"number": "2.1", "context": "Her duck, read as a person ducking.", "subject": "A person ducking"},
  {"number": "3.2", "context": "Her duck, read as a person ducking.", "subject": "A person ducking"},
  {"number": "4", "context": "I saw her duck.", "subject": "Observation"},
  {"number": "1.1.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "3.1.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "4.1", "context": "I saw her duck, read as her animal.", "subject": "Observation of a person's duck"},
  {"number": "2.1.1", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "3.2.1", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "4.2", "context": "I saw her duck, read as a person ducking.", "subject": "Observation of a person ducking"},
  {"number": "5", "context": "I bought a notebook.", "subject": "Notebooks"},
  {"number": "6", "context": "I bought a notebook.", "subject": "Purchases"},
  {"number": "5.1", "context": "I bought a notebook.", "subject": "Purchase of a notebook"},
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
  {"number": "1.1.2", "context": "Cable B is 3 m long.", "subject": "3 m cables"},
  {"number": "1.1.2.1", "context": "Cable B is 3 m long.", "subject": "3 m cable B"},
  {"number": "1.1.3", "context": "A is not longer than B.", "subject": "Cable length comparisons"},
  {"number": "1.2", "context": "2 cables: A and B.", "subject": "Pairs of cables"},
  {"number": "1.1.1.1.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.2.1.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.2.1", "context": "2 cables: A is 2 m; B is 3 m.", "subject": "Pair consisting of 2 m cable A and 3 m cable B"},
  {"number": "1.1.1.1.1.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.2.1.1.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
  {"number": "1.1.3.1", "context": "A is not longer than B; A = 2 m, B = 3 m.", "subject": "2 m cable A not longer than 3 m cable B"},
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
  {"number": "1.1.1.2", "context": "3 is added to 2.", "subject": "3 as an addend"},
  {"number": "1.1.2", "context": "The stated sum is 5.", "subject": "Addition results"},
  {"number": "1.1.2.1", "context": "The stated sum is 5.", "subject": "5 as an addition result"},
  {"number": "1.1.1.1.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.1.2.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"},
  {"number": "1.1.2.1.1", "context": "2 + 3 = 5.", "subject": "Addition of 2 and 3 yielding 5"}
]}
</output>
</example>

<example>
<post>
My reliable lentil soup recipe serving four people.
Cumin for seasoning food, to taste.
</post>

<explanation>
The opening sentence introduces the recipe whose seasoning is described on the next line. The complete cumin subject retains its purpose, to-taste amount and relationship to the author's reliable lentil soup recipe serving four people. The recipe's separate subject and the cumin subject's placement cannot supply details missing from the cumin wording. General Cumin and Food seasoning headings remain broader; their complete source descendant retains the recipe relationship. The full cumin subject appears beneath both recipe copies and every other compatible returned heading.
</explanation>

<output>
{"subjects": [
  {"number": "1", "context": "The opening sentence introduces a recipe.", "subject": "Recipes"},
  {"number": "1.1", "context": "My reliable lentil soup recipe serving four people.", "subject": "Author's reliable lentil soup recipe serving four people"},
  {"number": "1.1.1", "context": "Cumin for seasoning food, to taste, in the recipe introduced by the opening sentence.", "subject": "Cumin to taste for seasoning food in the author's reliable lentil soup recipe serving four people"},
  {"number": "2", "context": "The recipe is for lentil soup.", "subject": "Lentil soup"},
  {"number": "2.1", "context": "My reliable lentil soup recipe serving four people.", "subject": "Author's reliable lentil soup recipe serving four people"},
  {"number": "2.1.1", "context": "Cumin for seasoning food, to taste, in the recipe introduced by the opening sentence.", "subject": "Cumin to taste for seasoning food in the author's reliable lentil soup recipe serving four people"},
  {"number": "3", "context": "The seasoning line names cumin.", "subject": "Cumin"},
  {"number": "3.1", "context": "Cumin for seasoning food, to taste, in the recipe introduced by the opening sentence.", "subject": "Cumin to taste for seasoning food in the author's reliable lentil soup recipe serving four people"},
  {"number": "4", "context": "Cumin is expressly for seasoning food.", "subject": "Food seasoning"},
  {"number": "4.1", "context": "Cumin for seasoning food, to taste, in the recipe introduced by the opening sentence.", "subject": "Cumin to taste for seasoning food in the author's reliable lentil soup recipe serving four people"}
]}
</output>
</example>
