# Experiment 2: exploratory nearby-subject segmentation

Status: **draft; every atomic-subject cohort, diagnostic annotation, and mask
requires human approval before encoding**.

## Purpose

> Nearby but meaningfully distinct fine subjects are resolved.

This experiment characterizes what one frozen fine-segmentation candidate does
inside several densely sampled semantic neighborhoods. It does not prescribe
one correct partition, one mandatory semantic boundary, or one required
hierarchy.

The primary question is:

> For each returned multi-vector segment, what is the narrowest recognizable
> subject for which every instance is a valid refinement?

If no such subject exists, the returned segment is a false merge. Coherent
broader grouping, coherent narrower splitting, overlapping segments, and
unassigned vectors are recorded rather than forced into a predetermined
verdict.

## Fixture

The fixture is one corpus containing 128 vectors. It has four annotated broad
areas, eight annotated atomic-subject cohorts per area, and four independently
worded instances per atomic-subject cohort. Every complete note is also its
complete mask. Every concept is ordinary and stated directly; no relationship
depends on obscure facts or compositional role ordering.

The diagnostic annotations are balanced by construction:

| Path depth | Annotated groups | Vectors per group |
|---|---:|---:|
| Complete corpus | 1 | 128 |
| First path term | 4 | 32 |
| First two path terms | 8 | 16 |
| First three path terms | 16 | 8 |
| Complete path | 32 | 4 |

This balances support among peer annotations. Unequal density and sparsity are
tested separately in Experiment 5. The candidate receives only opaque IDs and
vectors, not the annotations.

Each input table below has one complete diagnostic path in its title. Reading a
path from left to right gives progressively narrower human interpretations of
the masks. These paths help diagnose returned segments after their blind
review. They are not expected output and do not determine correctness.

## Complete corpus · 128 vectors

The complete input set is a non-semantic container, not a claim that every
vector shares one subject.

### Coffee activities > Coffee preparation > Roasting coffee > Light-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I roasted green coffee beans to a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦Heating transformed the raw coffee beans into a light roast.⟧ |
| `LIGHT-ROAST-3` | ⟦I stopped roasting the coffee beans at the light-roast stage.⟧ |
| `LIGHT-ROAST-4` | ⟦The coffee beans were roasted until they reached a light roast.⟧ |

### Coffee activities > Coffee preparation > Roasting coffee > Dark-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦I roasted green coffee beans to a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦Heating transformed the raw coffee beans into a dark roast.⟧ |
| `DARK-ROAST-3` | ⟦I continued roasting the coffee beans to the dark-roast stage.⟧ |
| `DARK-ROAST-4` | ⟦The coffee beans were roasted until they reached a dark roast.⟧ |

### Coffee activities > Coffee preparation > Brewing coffee > Pour-over brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `POUR-OVER-1` | ⟦I brewed coffee with a pour-over dripper.⟧ |
| `POUR-OVER-2` | ⟦I prepared a cup of pour-over coffee.⟧ |
| `POUR-OVER-3` | ⟦My coffee was brewed using the pour-over method.⟧ |
| `POUR-OVER-4` | ⟦I used pour-over brewing to make coffee.⟧ |

### Coffee activities > Coffee preparation > Brewing coffee > Espresso brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ESPRESSO-1` | ⟦I brewed a shot of espresso.⟧ |
| `ESPRESSO-2` | ⟦I used an espresso machine to prepare espresso.⟧ |
| `ESPRESSO-3` | ⟦My coffee preparation produced a shot of espresso.⟧ |
| `ESPRESSO-4` | ⟦I made espresso with an espresso brewer.⟧ |

### Coffee activities > Drinking coffee > Drinking hot coffee > Drinking hot black coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BLACK-HOT-1` | ⟦I drank a cup of hot black coffee.⟧ |
| `BLACK-HOT-2` | ⟦I sipped hot coffee without milk or cream.⟧ |
| `BLACK-HOT-3` | ⟦I drank hot coffee served black.⟧ |
| `BLACK-HOT-4` | ⟦I drank black coffee while it was hot.⟧ |

### Coffee activities > Drinking coffee > Drinking hot coffee > Drinking hot coffee with milk · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `MILK-HOT-1` | ⟦I drank hot coffee with milk.⟧ |
| `MILK-HOT-2` | ⟦I drank a hot coffee that contained milk.⟧ |
| `MILK-HOT-3` | ⟦I sipped a cup of hot coffee with milk.⟧ |
| `MILK-HOT-4` | ⟦I sipped a hot, milky coffee.⟧ |

### Coffee activities > Drinking coffee > Drinking cold coffee > Drinking iced coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ICED-COFFEE-1` | ⟦I drank coffee served over ice.⟧ |
| `ICED-COFFEE-2` | ⟦I sipped an iced coffee.⟧ |
| `ICED-COFFEE-3` | ⟦I drank cold coffee with ice cubes in it.⟧ |
| `ICED-COFFEE-4` | ⟦I drank a chilled cup of iced coffee.⟧ |

### Coffee activities > Drinking coffee > Drinking cold coffee > Drinking cold-brew coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLD-BREW-1` | ⟦I drank a cup of cold-brew coffee.⟧ |
| `COLD-BREW-2` | ⟦I drank cold-brew coffee as a cold drink.⟧ |
| `COLD-BREW-3` | ⟦I sipped a cold-brew coffee.⟧ |
| `COLD-BREW-4` | ⟦I finished drinking a cold-brew coffee.⟧ |

### Working with photos > Making and editing photos > Taking photos > Taking portraits · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PORTRAIT-1` | ⟦I took a portrait photograph of a person.⟧ |
| `PORTRAIT-2` | ⟦My camera captured a person's portrait.⟧ |
| `PORTRAIT-3` | ⟦I photographed someone for a portrait.⟧ |
| `PORTRAIT-4` | ⟦The photo I took was a portrait of a person.⟧ |

### Working with photos > Making and editing photos > Taking photos > Taking landscape photos · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LANDSCAPE-1` | ⟦I took a landscape photograph of the scenery.⟧ |
| `LANDSCAPE-2` | ⟦My camera captured a wide outdoor landscape.⟧ |
| `LANDSCAPE-3` | ⟦I photographed the natural scenery as a landscape.⟧ |
| `LANDSCAPE-4` | ⟦The photo I took showed a broad landscape.⟧ |

### Working with photos > Making and editing photos > Editing photos > Cropping photos · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CROP-PHOTO-1` | ⟦I cropped a photo to remove its outer edges.⟧ |
| `CROP-PHOTO-2` | ⟦I trimmed the borders from a photograph.⟧ |
| `CROP-PHOTO-3` | ⟦Cropping removed the unwanted edges of the picture.⟧ |
| `CROP-PHOTO-4` | ⟦I reframed an image by cutting away its outside area.⟧ |

### Working with photos > Making and editing photos > Editing photos > Adjusting photo colors · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLOR-ADJUST-1` | ⟦I adjusted the colors in a photo.⟧ |
| `COLOR-ADJUST-2` | ⟦I edited a photograph's color balance.⟧ |
| `COLOR-ADJUST-3` | ⟦Changing the color settings altered the picture's appearance.⟧ |
| `COLOR-ADJUST-4` | ⟦I corrected the colors while editing an image.⟧ |

### Working with photos > Storing and sharing photos > Backing up photos > Local photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I created a recovery backup of my photo library on a local external drive.⟧ |
| `LOCAL-BACKUP-2` | ⟦A drive connected to my computer holds a backup copy of my photos.⟧ |
| `LOCAL-BACKUP-3` | ⟦I copied my photo library to a locally attached disk for recovery.⟧ |
| `LOCAL-BACKUP-4` | ⟦A local USB storage device stores my photo backup.⟧ |

### Working with photos > Storing and sharing photos > Backing up photos > Cloud photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦I created a recovery backup of my photo library in remote cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦A cloud storage service holds a backup copy of my photos.⟧ |
| `CLOUD-BACKUP-3` | ⟦I copied my photo library to remote online storage for recovery.⟧ |
| `CLOUD-BACKUP-4` | ⟦An off-site cloud service stores my photo backup.⟧ |

### Working with photos > Storing and sharing photos > Sharing photos > Sharing photos by email · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `EMAIL-SHARE-1` | ⟦I shared a photo by attaching it to an email.⟧ |
| `EMAIL-SHARE-2` | ⟦I emailed a photograph to someone.⟧ |
| `EMAIL-SHARE-3` | ⟦An email attachment carried the photo I shared.⟧ |
| `EMAIL-SHARE-4` | ⟦I sent someone a picture through email.⟧ |

### Working with photos > Storing and sharing photos > Sharing photos > Sharing photos by link · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LINK-SHARE-1` | ⟦I shared a photo by sending its online link.⟧ |
| `LINK-SHARE-2` | ⟦I gave someone a web link to a photograph.⟧ |
| `LINK-SHARE-3` | ⟦A shared link opened the online photo.⟧ |
| `LINK-SHARE-4` | ⟦I sent someone a link for viewing my picture.⟧ |

### Eating produce > Eating fruit > Eating apples > Eating red apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RED-APPLE-1` | ⟦I ate a red apple.⟧ |
| `RED-APPLE-2` | ⟦I was eating an apple with red skin.⟧ |
| `RED-APPLE-3` | ⟦My snack was a red apple.⟧ |
| `RED-APPLE-4` | ⟦A red apple was what I ate.⟧ |

### Eating produce > Eating fruit > Eating apples > Eating green apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GREEN-APPLE-1` | ⟦I ate a green apple.⟧ |
| `GREEN-APPLE-2` | ⟦I was eating an apple with green skin.⟧ |
| `GREEN-APPLE-3` | ⟦My snack was a green apple.⟧ |
| `GREEN-APPLE-4` | ⟦A green apple was what I ate.⟧ |

### Eating produce > Eating fruit > Eating citrus fruit > Eating oranges · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ORANGE-1` | ⟦I ate an orange.⟧ |
| `ORANGE-2` | ⟦I was eating a fresh orange fruit.⟧ |
| `ORANGE-3` | ⟦My snack was an orange.⟧ |
| `ORANGE-4` | ⟦An orange was what I ate.⟧ |

### Eating produce > Eating fruit > Eating citrus fruit > Eating grapefruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GRAPEFRUIT-1` | ⟦I ate a grapefruit.⟧ |
| `GRAPEFRUIT-2` | ⟦I was eating fresh grapefruit.⟧ |
| `GRAPEFRUIT-3` | ⟦My snack was a grapefruit.⟧ |
| `GRAPEFRUIT-4` | ⟦A grapefruit was what I ate.⟧ |

### Eating produce > Eating vegetables > Eating carrots > Eating raw carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RAW-CARROT-1` | ⟦I ate a raw carrot.⟧ |
| `RAW-CARROT-2` | ⟦I snacked on an uncooked carrot.⟧ |
| `RAW-CARROT-3` | ⟦I crunched on a fresh raw carrot.⟧ |
| `RAW-CARROT-4` | ⟦I ate a carrot without cooking it.⟧ |

### Eating produce > Eating vegetables > Eating carrots > Eating cooked carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COOKED-CARROT-1` | ⟦I ate a cooked carrot.⟧ |
| `COOKED-CARROT-2` | ⟦I ate a carrot after cooking it.⟧ |
| `COOKED-CARROT-3` | ⟦I had a soft cooked carrot with my meal.⟧ |
| `COOKED-CARROT-4` | ⟦I ate a carrot that had been cooked.⟧ |

### Eating produce > Eating vegetables > Eating leafy greens > Eating lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LETTUCE-1` | ⟦I ate some lettuce.⟧ |
| `LETTUCE-2` | ⟦I was eating fresh lettuce leaves.⟧ |
| `LETTUCE-3` | ⟦My food included crisp lettuce.⟧ |
| `LETTUCE-4` | ⟦Lettuce leaves were what I ate.⟧ |

### Eating produce > Eating vegetables > Eating leafy greens > Eating spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `SPINACH-1` | ⟦I ate some spinach.⟧ |
| `SPINACH-2` | ⟦I was eating fresh spinach leaves.⟧ |
| `SPINACH-3` | ⟦My food included leafy spinach.⟧ |
| `SPINACH-4` | ⟦Spinach leaves were what I ate.⟧ |

### Consuming media > Reading > Reading books > Reading fiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-BOOK-1` | ⟦I read a fiction book.⟧ |
| `FICTION-BOOK-2` | ⟦I spent time reading a novel.⟧ |
| `FICTION-BOOK-3` | ⟦My reading was a fictional book.⟧ |
| `FICTION-BOOK-4` | ⟦I read a book that told an invented story.⟧ |

### Consuming media > Reading > Reading books > Reading nonfiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-BOOK-1` | ⟦I read a nonfiction book.⟧ |
| `NONFICTION-BOOK-2` | ⟦I spent time reading a factual book.⟧ |
| `NONFICTION-BOOK-3` | ⟦My reading was a work of nonfiction.⟧ |
| `NONFICTION-BOOK-4` | ⟦I read a book about real events and facts.⟧ |

### Consuming media > Reading > Reading magazines > Reading print magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PRINT-MAGAZINE-1` | ⟦I read a printed magazine.⟧ |
| `PRINT-MAGAZINE-2` | ⟦I turned the paper pages while reading a magazine.⟧ |
| `PRINT-MAGAZINE-3` | ⟦My reading was a physical magazine issue.⟧ |
| `PRINT-MAGAZINE-4` | ⟦I read articles in a magazine printed on paper.⟧ |

### Consuming media > Reading > Reading magazines > Reading digital magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIGITAL-MAGAZINE-1` | ⟦I read a digital magazine.⟧ |
| `DIGITAL-MAGAZINE-2` | ⟦I used a screen to read an electronic magazine issue.⟧ |
| `DIGITAL-MAGAZINE-3` | ⟦My reading was an online magazine edition.⟧ |
| `DIGITAL-MAGAZINE-4` | ⟦I read magazine articles in a digital publication.⟧ |

### Consuming media > Listening > Listening to podcasts > Listening to news podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NEWS-PODCAST-1` | ⟦I listened to a news podcast.⟧ |
| `NEWS-PODCAST-2` | ⟦I played a podcast episode about current news.⟧ |
| `NEWS-PODCAST-3` | ⟦My listening choice was a news podcast.⟧ |
| `NEWS-PODCAST-4` | ⟦I heard the latest news in a podcast episode.⟧ |

### Consuming media > Listening > Listening to podcasts > Listening to interview podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `INTERVIEW-PODCAST-1` | ⟦I listened to an interview podcast.⟧ |
| `INTERVIEW-PODCAST-2` | ⟦I played a podcast episode featuring an interview.⟧ |
| `INTERVIEW-PODCAST-3` | ⟦My listening choice was a podcast conversation with a guest.⟧ |
| `INTERVIEW-PODCAST-4` | ⟦I heard a host interview someone on a podcast.⟧ |

### Consuming media > Listening > Listening to audiobooks > Listening to fiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-AUDIOBOOK-1` | ⟦I listened to a fiction audiobook.⟧ |
| `FICTION-AUDIOBOOK-2` | ⟦I listened to a narrated audiobook telling a fictional story.⟧ |
| `FICTION-AUDIOBOOK-3` | ⟦My listening was an audiobook of a novel.⟧ |
| `FICTION-AUDIOBOOK-4` | ⟦I played an audiobook that told an invented story.⟧ |

### Consuming media > Listening > Listening to audiobooks > Listening to nonfiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-AUDIOBOOK-1` | ⟦I listened to a nonfiction audiobook.⟧ |
| `NONFICTION-AUDIOBOOK-2` | ⟦I listened to a narrated audiobook presenting factual material.⟧ |
| `NONFICTION-AUDIOBOOK-3` | ⟦My listening was an audiobook of nonfiction.⟧ |
| `NONFICTION-AUDIOBOOK-4` | ⟦I played an audiobook about real events and facts.⟧ |

## Reviewing the returned segments

Freeze and preserve the candidate's complete output before restoring fixture
identities. Review every returned segment containing at least two vectors.

The primary review is blind to the fixture IDs, cohort identities, and path
annotations. Give each vector a neutral temporary label, show all of the
segment's complete masks, and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

Record the proposed subject and whether every mask genuinely fits it. If no
precise recognizable subject covers every member, record a false merge and the
specific masks that make it false. Do not rescue a false merge with a vague
umbrella, a list of unrelated subjects, or the hidden diagnostic paths.

After the primary review is frozen, reveal the cohort and path annotations for
diagnosis. Record:

- every returned multi-vector segment and its complete masks;
- every proposed segment subject and review judgment;
- every false merge and the members responsible;
- where the four paraphrases of each annotated atomic subject appeared;
- singleton and unassigned vectors;
- overlapping memberships;
- memberships spanning diagnostic path prefixes;
- raw-vector cosine values as diagnostics only.

A split annotated cohort is not automatically a failure. A segment spanning
different diagnostic paths is not automatically a false merge. The masks and
the primary review determine whether one coherent fine subject exists.

This experiment has no mandatory semantic-boundary score, highest rung, or
binary pass/fail verdict. It characterizes a development candidate. Any
candidate or configuration changed after inspecting the result requires a new
unseen fixture for subsequent validation.

## Run

1. Approve and freeze every note, mask, atomic-subject cohort, and diagnostic
   path annotation.
2. Freeze one candidate, configuration, seed, fine-output selector, and opaque
   shuffled input order before encoding or exposing vector diagnostics.
3. Encode all 128 inputs once under the shared contract in README.md.
4. Run once and preserve the complete output before restoring fixture IDs.
5. Complete and freeze the blind segment review.
6. Reveal the diagnostic annotations and complete the diagnostic record.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, blind review judgments,
annotation-based diagnostics, and all generated artifact hashes.

## Scope

This is an exploratory test of the complete frozen SSE-plus-segmentation
system. A failure may originate in the SSE geometry, the candidate, or their
interaction; cosine diagnostics cannot conclusively attribute causation.

The diagnostic paths are human interpretations of this synthetic corpus, not
universal semantic-distance thresholds or a required hierarchy. Experiments
3–6 separately test lexical traps, unmasked context, unequal density, and
irrelevant changes.
