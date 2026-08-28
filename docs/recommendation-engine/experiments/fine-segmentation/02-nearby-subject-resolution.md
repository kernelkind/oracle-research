# Experiment 2: fine-subject resolution spectrum

Status: **draft; every subject identity, rung, and mask requires human approval
before encoding**.

## Assumption

> Nearby but meaningfully distinct fine subjects are resolved.

We do not yet know how fine the segmentation must be. The experiment therefore
defines five concrete rungs over one corpus:

- **Rung 0:** the complete unsegmented input set;
- **Rung 1:** four broad groups;
- **Rung 2:** eight narrower groups;
- **Rung 3:** sixteen still-narrower groups;
- **Rung 4:** thirty-two finest groups.

Rung 1 is the mandatory minimum. Its boundaries are deliberately coarse and
unambiguous. Rungs 2 through 4 measure progressively finer resolving power.

This sweeps semantic distinctions in the fixture. It does not tune or sweep an
algorithm-specific setting. One candidate and configuration remain frozen.

## Fixture

The fixture is one corpus containing 128 vectors. It has four broad branches,
eight finest-subject cohorts per branch, and four independently worded
instances per finest cohort. Every complete note is also its complete mask.
Every concept is ordinary and stated directly; no rung depends on obscure
facts or compositional role ordering.

The hierarchy is balanced by construction:

| Rung | Groups in the corpus | Vectors per group |
|---|---:|---:|
| 0 | 1 | 128 |
| 1 | 4 | 32 |
| 2 | 8 | 16 |
| 3 | 16 | 8 |
| 4 | 32 | 4 |

This controls sample-count density inside this experiment. Unequal density and
sparsity are tested separately in Experiment 5. The candidate receives only
opaque IDs and vectors, not the branch or rung information.

Read the fixture below from top to bottom. Each parent immediately names its
children, then the document shows everything inside the first child before
moving to the next. Each Rung 4 subject contains its four exact input masks.
Every higher group is the union of the Rung 4 inputs nested beneath it; later
rungs do not introduce new vectors.

## Rung 0 · Complete corpus · 128 vectors

Rung 0 is the unsegmented input set. It is a non-semantic root, not a claim
that every vector shares one subject.

Its immediate children are:

- Coffee activities · 32 vectors
- Working with photos · 32 vectors
- Eating produce · 32 vectors
- Consuming media · 32 vectors

### Rung 1 · Coffee activities · 32 vectors

Its immediate children are:

- Coffee preparation · 16 vectors
- Drinking coffee · 16 vectors

#### Rung 2 · Coffee preparation · 16 vectors

Its immediate children are:

- Roasting coffee · 8 vectors
- Brewing coffee · 8 vectors

##### Rung 3 · Roasting coffee · 8 vectors

Its immediate children are Light-roast preparation and Dark-roast
preparation, each containing four vectors.

###### Rung 4 · Light-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I roasted green coffee beans to a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦Heating transformed the raw coffee beans into a light roast.⟧ |
| `LIGHT-ROAST-3` | ⟦I stopped roasting the coffee beans at the light-roast stage.⟧ |
| `LIGHT-ROAST-4` | ⟦The coffee beans were roasted until they reached a light roast.⟧ |

###### Rung 4 · Dark-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦I roasted green coffee beans to a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦Heating transformed the raw coffee beans into a dark roast.⟧ |
| `DARK-ROAST-3` | ⟦I continued roasting the coffee beans to the dark-roast stage.⟧ |
| `DARK-ROAST-4` | ⟦The coffee beans were roasted until they reached a dark roast.⟧ |

##### Rung 3 · Brewing coffee · 8 vectors

Its immediate children are Pour-over brewing and Espresso brewing, each
containing four vectors.

###### Rung 4 · Pour-over brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `POUR-OVER-1` | ⟦I brewed coffee with a pour-over dripper.⟧ |
| `POUR-OVER-2` | ⟦I prepared a cup of pour-over coffee.⟧ |
| `POUR-OVER-3` | ⟦My coffee was brewed using the pour-over method.⟧ |
| `POUR-OVER-4` | ⟦I used pour-over brewing to make coffee.⟧ |

###### Rung 4 · Espresso brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ESPRESSO-1` | ⟦I brewed a shot of espresso.⟧ |
| `ESPRESSO-2` | ⟦I used an espresso machine to prepare espresso.⟧ |
| `ESPRESSO-3` | ⟦My coffee preparation produced a shot of espresso.⟧ |
| `ESPRESSO-4` | ⟦I made espresso with an espresso brewer.⟧ |

#### Rung 2 · Drinking coffee · 16 vectors

Its immediate children are:

- Drinking hot coffee · 8 vectors
- Drinking cold coffee · 8 vectors

##### Rung 3 · Drinking hot coffee · 8 vectors

Its immediate children are Drinking hot black coffee and Drinking hot coffee
with milk, each containing four vectors.

###### Rung 4 · Drinking hot black coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BLACK-HOT-1` | ⟦I drank a cup of hot black coffee.⟧ |
| `BLACK-HOT-2` | ⟦I sipped hot coffee without milk or cream.⟧ |
| `BLACK-HOT-3` | ⟦I drank hot coffee served black.⟧ |
| `BLACK-HOT-4` | ⟦I drank black coffee while it was hot.⟧ |

###### Rung 4 · Drinking hot coffee with milk · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `MILK-HOT-1` | ⟦I drank hot coffee with milk.⟧ |
| `MILK-HOT-2` | ⟦I drank a hot coffee that contained milk.⟧ |
| `MILK-HOT-3` | ⟦I sipped a cup of hot coffee with milk.⟧ |
| `MILK-HOT-4` | ⟦I sipped a hot, milky coffee.⟧ |

##### Rung 3 · Drinking cold coffee · 8 vectors

Its immediate children are Drinking iced coffee and Drinking cold-brew coffee,
each containing four vectors.

###### Rung 4 · Drinking iced coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ICED-COFFEE-1` | ⟦I drank coffee served over ice.⟧ |
| `ICED-COFFEE-2` | ⟦I sipped an iced coffee.⟧ |
| `ICED-COFFEE-3` | ⟦I drank cold coffee with ice cubes in it.⟧ |
| `ICED-COFFEE-4` | ⟦I drank a chilled cup of iced coffee.⟧ |

###### Rung 4 · Drinking cold-brew coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLD-BREW-1` | ⟦I drank a cup of cold-brew coffee.⟧ |
| `COLD-BREW-2` | ⟦I drank cold-brew coffee as a cold drink.⟧ |
| `COLD-BREW-3` | ⟦I sipped a cold-brew coffee.⟧ |
| `COLD-BREW-4` | ⟦I chose cold-brew coffee as my drink.⟧ |

### Rung 1 · Working with photos · 32 vectors

Its immediate children are:

- Making and editing photos · 16 vectors
- Storing and sharing photos · 16 vectors

#### Rung 2 · Making and editing photos · 16 vectors

Its immediate children are:

- Taking photos · 8 vectors
- Editing photos · 8 vectors

##### Rung 3 · Taking photos · 8 vectors

Its immediate children are Taking portraits and Taking landscape photos, each
containing four vectors.

###### Rung 4 · Taking portraits · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PORTRAIT-1` | ⟦I took a portrait photograph of a person.⟧ |
| `PORTRAIT-2` | ⟦My camera captured a person's portrait.⟧ |
| `PORTRAIT-3` | ⟦I photographed someone for a portrait.⟧ |
| `PORTRAIT-4` | ⟦The photo I took was a portrait of a person.⟧ |

###### Rung 4 · Taking landscape photos · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LANDSCAPE-1` | ⟦I took a landscape photograph of the scenery.⟧ |
| `LANDSCAPE-2` | ⟦My camera captured a wide outdoor landscape.⟧ |
| `LANDSCAPE-3` | ⟦I photographed the natural scenery as a landscape.⟧ |
| `LANDSCAPE-4` | ⟦The photo I took showed a broad landscape.⟧ |

##### Rung 3 · Editing photos · 8 vectors

Its immediate children are Cropping photos and Adjusting photo colors, each
containing four vectors.

###### Rung 4 · Cropping photos · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CROP-PHOTO-1` | ⟦I cropped a photo to remove its outer edges.⟧ |
| `CROP-PHOTO-2` | ⟦I trimmed the borders from a photograph.⟧ |
| `CROP-PHOTO-3` | ⟦Cropping removed the unwanted edges of the picture.⟧ |
| `CROP-PHOTO-4` | ⟦I reframed an image by cutting away its outside area.⟧ |

###### Rung 4 · Adjusting photo colors · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLOR-ADJUST-1` | ⟦I adjusted the colors in a photo.⟧ |
| `COLOR-ADJUST-2` | ⟦I edited a photograph's color balance.⟧ |
| `COLOR-ADJUST-3` | ⟦Changing the color settings altered the picture's appearance.⟧ |
| `COLOR-ADJUST-4` | ⟦I corrected the colors while editing an image.⟧ |

#### Rung 2 · Storing and sharing photos · 16 vectors

Its immediate children are:

- Backing up photos · 8 vectors
- Sharing photos · 8 vectors

##### Rung 3 · Backing up photos · 8 vectors

Its immediate children are Local photo backups and Cloud photo backups, each
containing four vectors.

###### Rung 4 · Local photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I created a recovery backup of my photo library on a local external drive.⟧ |
| `LOCAL-BACKUP-2` | ⟦A drive connected to my computer holds a backup copy of my photos.⟧ |
| `LOCAL-BACKUP-3` | ⟦I copied my photo library to a locally attached disk for recovery.⟧ |
| `LOCAL-BACKUP-4` | ⟦A local USB storage device stores my photo backup.⟧ |

###### Rung 4 · Cloud photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦I created a recovery backup of my photo library in remote cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦A cloud storage service holds a backup copy of my photos.⟧ |
| `CLOUD-BACKUP-3` | ⟦I copied my photo library to remote online storage for recovery.⟧ |
| `CLOUD-BACKUP-4` | ⟦An off-site cloud service stores my photo backup.⟧ |

##### Rung 3 · Sharing photos · 8 vectors

Its immediate children are Sharing photos by email and Sharing photos by link,
each containing four vectors.

###### Rung 4 · Sharing photos by email · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `EMAIL-SHARE-1` | ⟦I shared a photo by attaching it to an email.⟧ |
| `EMAIL-SHARE-2` | ⟦I emailed a photograph to someone.⟧ |
| `EMAIL-SHARE-3` | ⟦An email attachment carried the photo I shared.⟧ |
| `EMAIL-SHARE-4` | ⟦I sent someone a picture through email.⟧ |

###### Rung 4 · Sharing photos by link · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LINK-SHARE-1` | ⟦I shared a photo by sending its online link.⟧ |
| `LINK-SHARE-2` | ⟦I gave someone a web link to a photograph.⟧ |
| `LINK-SHARE-3` | ⟦A shared link opened the online photo.⟧ |
| `LINK-SHARE-4` | ⟦I sent someone a link for viewing my picture.⟧ |

### Rung 1 · Eating produce · 32 vectors

Its immediate children are:

- Eating fruit · 16 vectors
- Eating vegetables · 16 vectors

#### Rung 2 · Eating fruit · 16 vectors

Its immediate children are:

- Eating apples · 8 vectors
- Eating citrus fruit · 8 vectors

##### Rung 3 · Eating apples · 8 vectors

Its immediate children are Eating red apples and Eating green apples, each
containing four vectors.

###### Rung 4 · Eating red apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RED-APPLE-1` | ⟦I ate a red apple.⟧ |
| `RED-APPLE-2` | ⟦I was eating an apple with red skin.⟧ |
| `RED-APPLE-3` | ⟦My snack was a red apple.⟧ |
| `RED-APPLE-4` | ⟦A red apple was what I ate.⟧ |

###### Rung 4 · Eating green apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GREEN-APPLE-1` | ⟦I ate a green apple.⟧ |
| `GREEN-APPLE-2` | ⟦I was eating an apple with green skin.⟧ |
| `GREEN-APPLE-3` | ⟦My snack was a green apple.⟧ |
| `GREEN-APPLE-4` | ⟦A green apple was what I ate.⟧ |

##### Rung 3 · Eating citrus fruit · 8 vectors

Its immediate children are Eating oranges and Eating grapefruit, each
containing four vectors.

###### Rung 4 · Eating oranges · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ORANGE-1` | ⟦I ate an orange.⟧ |
| `ORANGE-2` | ⟦I was eating a fresh orange fruit.⟧ |
| `ORANGE-3` | ⟦My snack was an orange.⟧ |
| `ORANGE-4` | ⟦An orange was what I ate.⟧ |

###### Rung 4 · Eating grapefruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GRAPEFRUIT-1` | ⟦I ate a grapefruit.⟧ |
| `GRAPEFRUIT-2` | ⟦I was eating fresh grapefruit.⟧ |
| `GRAPEFRUIT-3` | ⟦My snack was a grapefruit.⟧ |
| `GRAPEFRUIT-4` | ⟦A grapefruit was what I ate.⟧ |

#### Rung 2 · Eating vegetables · 16 vectors

Its immediate children are:

- Eating carrots · 8 vectors
- Eating leafy greens · 8 vectors

##### Rung 3 · Eating carrots · 8 vectors

Its immediate children are Eating raw carrots and Eating cooked carrots, each
containing four vectors.

###### Rung 4 · Eating raw carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RAW-CARROT-1` | ⟦I ate a raw carrot.⟧ |
| `RAW-CARROT-2` | ⟦I snacked on an uncooked carrot.⟧ |
| `RAW-CARROT-3` | ⟦I crunched on a fresh raw carrot.⟧ |
| `RAW-CARROT-4` | ⟦I ate a carrot without cooking it.⟧ |

###### Rung 4 · Eating cooked carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COOKED-CARROT-1` | ⟦I ate a cooked carrot.⟧ |
| `COOKED-CARROT-2` | ⟦I ate a carrot after cooking it.⟧ |
| `COOKED-CARROT-3` | ⟦I had a soft cooked carrot with my meal.⟧ |
| `COOKED-CARROT-4` | ⟦I ate a carrot that had been cooked.⟧ |

##### Rung 3 · Eating leafy greens · 8 vectors

Its immediate children are Eating lettuce and Eating spinach, each containing
four vectors.

###### Rung 4 · Eating lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LETTUCE-1` | ⟦I ate some lettuce.⟧ |
| `LETTUCE-2` | ⟦I was eating fresh lettuce leaves.⟧ |
| `LETTUCE-3` | ⟦My food included crisp lettuce.⟧ |
| `LETTUCE-4` | ⟦Lettuce leaves were what I ate.⟧ |

###### Rung 4 · Eating spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `SPINACH-1` | ⟦I ate some spinach.⟧ |
| `SPINACH-2` | ⟦I was eating fresh spinach leaves.⟧ |
| `SPINACH-3` | ⟦My food included leafy spinach.⟧ |
| `SPINACH-4` | ⟦Spinach leaves were what I ate.⟧ |

### Rung 1 · Consuming media · 32 vectors

Its immediate children are:

- Reading · 16 vectors
- Listening · 16 vectors

#### Rung 2 · Reading · 16 vectors

Its immediate children are:

- Reading books · 8 vectors
- Reading magazines · 8 vectors

##### Rung 3 · Reading books · 8 vectors

Its immediate children are Reading fiction books and Reading nonfiction books,
each containing four vectors.

###### Rung 4 · Reading fiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-BOOK-1` | ⟦I read a fiction book.⟧ |
| `FICTION-BOOK-2` | ⟦I spent time reading a novel.⟧ |
| `FICTION-BOOK-3` | ⟦My reading was a fictional book.⟧ |
| `FICTION-BOOK-4` | ⟦I read a book that told an invented story.⟧ |

###### Rung 4 · Reading nonfiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-BOOK-1` | ⟦I read a nonfiction book.⟧ |
| `NONFICTION-BOOK-2` | ⟦I spent time reading a factual book.⟧ |
| `NONFICTION-BOOK-3` | ⟦My reading was a work of nonfiction.⟧ |
| `NONFICTION-BOOK-4` | ⟦I read a book about real events and facts.⟧ |

##### Rung 3 · Reading magazines · 8 vectors

Its immediate children are Reading print magazines and Reading digital
magazines, each containing four vectors.

###### Rung 4 · Reading print magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PRINT-MAGAZINE-1` | ⟦I read a printed magazine.⟧ |
| `PRINT-MAGAZINE-2` | ⟦I turned the paper pages while reading a magazine.⟧ |
| `PRINT-MAGAZINE-3` | ⟦My reading was a physical magazine issue.⟧ |
| `PRINT-MAGAZINE-4` | ⟦I read articles in a magazine printed on paper.⟧ |

###### Rung 4 · Reading digital magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIGITAL-MAGAZINE-1` | ⟦I read a digital magazine.⟧ |
| `DIGITAL-MAGAZINE-2` | ⟦I used a screen to read an electronic magazine issue.⟧ |
| `DIGITAL-MAGAZINE-3` | ⟦My reading was an online magazine edition.⟧ |
| `DIGITAL-MAGAZINE-4` | ⟦I read magazine articles in a digital publication.⟧ |

#### Rung 2 · Listening · 16 vectors

Its immediate children are:

- Listening to podcasts · 8 vectors
- Listening to audiobooks · 8 vectors

##### Rung 3 · Listening to podcasts · 8 vectors

Its immediate children are Listening to news podcasts and Listening to
interview podcasts, each containing four vectors.

###### Rung 4 · Listening to news podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NEWS-PODCAST-1` | ⟦I listened to a news podcast.⟧ |
| `NEWS-PODCAST-2` | ⟦I played a podcast episode about current news.⟧ |
| `NEWS-PODCAST-3` | ⟦My listening choice was a news podcast.⟧ |
| `NEWS-PODCAST-4` | ⟦I heard the latest news in a podcast episode.⟧ |

###### Rung 4 · Listening to interview podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `INTERVIEW-PODCAST-1` | ⟦I listened to an interview podcast.⟧ |
| `INTERVIEW-PODCAST-2` | ⟦I played a podcast episode featuring an interview.⟧ |
| `INTERVIEW-PODCAST-3` | ⟦My listening choice was a podcast conversation with a guest.⟧ |
| `INTERVIEW-PODCAST-4` | ⟦I heard a host interview someone on a podcast.⟧ |

##### Rung 3 · Listening to audiobooks · 8 vectors

Its immediate children are Listening to fiction audiobooks and Listening to
nonfiction audiobooks, each containing four vectors.

###### Rung 4 · Listening to fiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-AUDIOBOOK-1` | ⟦I listened to a fiction audiobook.⟧ |
| `FICTION-AUDIOBOOK-2` | ⟦I listened to a narrator tell a fictional story.⟧ |
| `FICTION-AUDIOBOOK-3` | ⟦My listening was an audiobook of a novel.⟧ |
| `FICTION-AUDIOBOOK-4` | ⟦I played an audiobook that told an invented story.⟧ |

###### Rung 4 · Listening to nonfiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-AUDIOBOOK-1` | ⟦I listened to a nonfiction audiobook.⟧ |
| `NONFICTION-AUDIOBOOK-2` | ⟦I listened to a narrator tell factual material.⟧ |
| `NONFICTION-AUDIOBOOK-3` | ⟦My listening was an audiobook of nonfiction.⟧ |
| `NONFICTION-AUDIOBOOK-4` | ⟦I played an audiobook about real events and facts.⟧ |

## Scoring the corpus

The nested structure above is the complete expected hierarchy. Every named
heading is one required group; its vectors are exactly the vectors beneath that
heading. Scoring uses those subject names directly rather than separate
aliases.

A returned segment **crosses** a boundary when it contains vectors from two
groups that the rung keeps separate.

A required group is **recovered** when either:

1. one returned segment equals that group exactly; or
2. all of its immediate child groups are recovered.

At Rung 4, a group is recovered only when one returned segment equals its four
vectors exactly. For example, the 16-vector Coffee preparation group is
recovered by any of these complete outputs:

- one exact Coffee preparation segment;
- exact Roasting coffee and Brewing coffee segments;
- exact Light-roast preparation, Dark-roast preparation, Pour-over brewing,
  and Espresso brewing segments.

A partial subset does not recover its parent group.

A result reaches a rung when every required group at that rung is recovered and
no returned segment crosses any boundary at that rung:

- **Rung 1:** all four 32-vector branches are recovered, and no segment mixes
  Coffee, Photos, Produce, or Media;
- **Rung 2:** all eight 16-vector groups are recovered, with no Rung 2 boundary
  crossed;
- **Rung 3:** all sixteen 8-vector groups are recovered, with no Rung 3
  boundary crossed;
- **Rung 4:** all thirty-two 4-vector finest cohorts are recovered, with no
  finest-cohort boundary crossed.

Additional segments contained inside one finest cohort are allowed. Segments
crossing a required boundary prevent that rung from passing even if valid
segments also exist. The verdict does not otherwise require every vector to
have only one membership.

## Overall result

The mandatory minimum is Rung 1 for the complete corpus. Rungs 2 through 4
measure additional resolving power and are not minimum requirements.

Report the highest verified rung for the complete corpus and separately for
each Rung 1 branch. A result that does not reach Rung 1 is reported as **below
minimum**; Rung 0 is the input state, not a successful segmentation result.

## Run

1. Approve and freeze every note, mask, cohort identity, and hierarchy rung.
2. Freeze one candidate, configuration, seed, fine-output selector, and opaque
   shuffled input order before encoding or exposing vector diagnostics.
3. Encode all 128 inputs once under the shared contract in README.md.
4. Run once and preserve the complete output before restoring fixture IDs.
5. Score the one corpus against Rungs 1 through 4.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, the highest verified global
rung, and the highest rung reached inside each Rung 1 branch. Preserve
raw-vector cosine values for diagnosis only.

## Scope

The rung labels refer only to the human-approved boundaries in this synthetic
hierarchy. They are not universal semantic-distance thresholds. Experiments
3–6 separately test lexical traps, unmasked context, unequal density, and
irrelevant changes.
