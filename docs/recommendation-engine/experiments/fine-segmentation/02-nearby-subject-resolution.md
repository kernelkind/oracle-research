# Experiment 2: exploratory nearby-subject segmentation

Status: **draft; every atomic-subject cohort, diagnostic annotation, and mask
requires human approval before encoding**.

## Purpose

> Nearby but meaningfully distinct fine subjects are resolved.

This experiment characterizes what one frozen fine-segmentation candidate does
inside several densely sampled semantic neighborhoods and whether surrounding
semantic material changes those results. It does not prescribe one correct
partition, one mandatory semantic boundary, or one required hierarchy.

The primary question is:

> For each returned multi-vector segment, what is the narrowest recognizable
> subject for which every instance is a valid refinement?

If no such subject exists, the returned segment is a false merge. Coherent
broader grouping, coherent narrower splitting, overlapping segments, and
unassigned vectors are recorded rather than forced into a predetermined
verdict.

## Probe fixture

The probe fixture contains 128 vectors. It has four annotated broad areas,
eight annotated atomic-subject cohorts per area, and four controlled
formulations per atomic-subject cohort. Every complete note is also its complete
mask. Every concept is ordinary and stated directly; no relationship depends
on obscure facts or compositional role ordering.

The diagnostic annotations are balanced by construction:

| Path depth | Annotated groups | Vectors per group |
|---|---:|---:|
| Complete corpus | 1 | 128 |
| First path term | 4 | 32 |
| First two path terms | 8 | 16 |
| First three path terms | 16 | 8 |
| Complete path | 32 | 4 |

This balances support among peer annotations. Unequal density and sparsity are
tested separately in Experiment 5.

Three synthetic background layers add 32 vectors each:

| Layer | Purpose | Cohorts | Vectors |
|---|---|---:|---:|
| `D` | Subjects deliberately distant from the four probe areas | 8 | 32 |
| `A` | New subjects adjacent to the probe neighborhoods | 8 | 32 |
| `B` | Precise subjects connecting attributes from existing neighborhoods | 8 | 32 |

Equal layer sizes prevent the intervention type from being confused with the
number of added vectors. All 224 inputs are encoded once. The candidate
receives only opaque IDs and vectors, not the probe identities, layer roles,
cohort identities, or annotations.

Each input table below has one complete diagnostic path in its title. Reading a
path from left to right gives progressively narrower human interpretations of
the masks. These paths help diagnose returned segments after their blind
review. They are not expected output and do not determine correctness.

## Probe corpus · 128 vectors

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

## Synthetic background layers · 96 vectors

The three layer roles are human-defined interventions, not claims about where
SSE must place the vectors. Layer membership is frozen before encoding and is
not changed after inspecting vector geometry.

### Layer `D` · distant subjects · 32 vectors

These eight subjects are deliberately outside coffee, photos, eating produce,
and consuming media. They test whether adding semantically remote material
changes the probe result.

#### Replacing a faucet washer to stop a drip · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-FAUCET-1` | ⟦The bathroom faucet kept dripping, so I replaced its worn washer.⟧ |
| `DIST-FAUCET-2` | ⟦A fresh washer stopped the slow leak from the sink tap.⟧ |
| `DIST-FAUCET-3` | ⟦I changed the damaged washer that was causing my faucet to drip.⟧ |
| `DIST-FAUCET-4` | ⟦The tap finally quit leaking after I fitted it with a new washer.⟧ |

#### Renewing a passport · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-PASSPORT-1` | ⟦My passport expires this autumn, so I submitted a renewal application.⟧ |
| `DIST-PASSPORT-2` | ⟦I mailed the forms and my old passport in for renewal.⟧ |
| `DIST-PASSPORT-3` | ⟦Before my current passport lapses, I filed the paperwork to renew it.⟧ |
| `DIST-PASSPORT-4` | ⟦I sent in my expiring passport to have it renewed.⟧ |

#### Training a dog to sit on command · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-DOG-SIT-1` | ⟦I am teaching my dog to sit when I give the command.⟧ |
| `DIST-DOG-SIT-2` | ⟦We practiced until the dog would sit whenever it heard the cue.⟧ |
| `DIST-DOG-SIT-3` | ⟦At training today, my dog got a treat each time it sat after hearing “sit.”⟧ |
| `DIST-DOG-SIT-4` | ⟦My dog is learning to sit in response to the signal without any help.⟧ |

#### Receiving a professional teeth cleaning · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-DENTAL-CLEAN-1` | ⟦I went to the dentist for a routine teeth cleaning.⟧ |
| `DIST-DENTAL-CLEAN-2` | ⟦At my checkup, the dental hygienist removed plaque and polished my teeth.⟧ |
| `DIST-DENTAL-CLEAN-3` | ⟦Today’s dental appointment was for a professional cleaning.⟧ |
| `DIST-DENTAL-CLEAN-4` | ⟦I had my teeth cleaned by the hygienist this morning.⟧ |

#### Waiting at a station for a delayed train · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-DELAYED-TRAIN-1` | ⟦My train was running late, so I waited on the platform.⟧ |
| `DIST-DELAYED-TRAIN-2` | ⟦The train’s scheduled departure time passed while I was still waiting at the station.⟧ |
| `DIST-DELAYED-TRAIN-3` | ⟦A station announcement said my train was delayed, so I stayed on the platform.⟧ |
| `DIST-DELAYED-TRAIN-4` | ⟦I waited well past the timetable before the late train finally arrived.⟧ |

#### Clearing snow from a driveway · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-SNOW-DRIVEWAY-1` | ⟦After the overnight snowfall, I shoveled the driveway clear.⟧ |
| `DIST-SNOW-DRIVEWAY-2` | ⟦I used a snow shovel to open the driveway again.⟧ |
| `DIST-SNOW-DRIVEWAY-3` | ⟦The driveway was buried, so I spent the morning clearing off the snow.⟧ |
| `DIST-SNOW-DRIVEWAY-4` | ⟦I pushed the fresh snow aside until the whole driveway was passable.⟧ |

#### Swimming laps in a pool · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-POOL-LAPS-1` | ⟦I swam several laps in the pool before work.⟧ |
| `DIST-POOL-LAPS-2` | ⟦At the aquatic center, I swam back and forth along one lane.⟧ |
| `DIST-POOL-LAPS-3` | ⟦My workout was a steady series of lengths across the pool.⟧ |
| `DIST-POOL-LAPS-4` | ⟦I spent half an hour swimming laps without leaving my lane.⟧ |

#### Participating in a workplace fire drill · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIST-FIRE-DRILL-1` | ⟦When the fire drill alarm sounded, everyone in our office evacuated.⟧ |
| `DIST-FIRE-DRILL-2` | ⟦Our workplace ran a scheduled drill, and we followed the fire exit route outside.⟧ |
| `DIST-FIRE-DRILL-3` | ⟦During the practice evacuation, staff left the building and met at the fire assembly point.⟧ |
| `DIST-FIRE-DRILL-4` | ⟦We rehearsed getting out of the office safely as though there were a fire.⟧ |

### Layer `A` · adjacent subjects · 32 vectors

These subjects belong near the four probe areas without intentionally joining
two existing probe cohorts. They test the effect of adding local semantic
density.

#### Cleaning a burr coffee grinder · adjacent to coffee preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-GRINDER-CLEAN-1` | ⟦I brushed old coffee grounds out of my burr grinder.⟧ |
| `ADJ-GRINDER-CLEAN-2` | ⟦After unplugging the grinder, I cleaned the coffee residue from its burrs.⟧ |
| `ADJ-GRINDER-CLEAN-3` | ⟦Trapped grounds had collected around the burrs, so I cleaned the coffee grinder.⟧ |
| `ADJ-GRINDER-CLEAN-4` | ⟦I opened my burr coffee grinder and cleared away the stale dust inside.⟧ |

#### Descaling an automatic drip coffee maker · adjacent to coffee preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-DRIP-DESCALE-1` | ⟦Mineral buildup had slowed my automatic drip coffee maker, so I ran a descaling cycle.⟧ |
| `ADJ-DRIP-DESCALE-2` | ⟦I flushed limescale from the drip coffee machine with a descaling solution.⟧ |
| `ADJ-DRIP-DESCALE-3` | ⟦Cleaning out the mineral deposits left my automatic drip coffee brewer free of scale.⟧ |
| `ADJ-DRIP-DESCALE-4` | ⟦I descaled the automatic drip coffee brewer to clear the chalky buildup inside it.⟧ |

#### Straightening a tilted photograph · adjacent to photo editing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-PHOTO-STRAIGHTEN-1` | ⟦I straightened a tilted photo until its edges sat level.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-2` | ⟦The picture looked crooked, so I rotated it slightly to square it up.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-3` | ⟦A small rotation corrected the slant in the photograph.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-4` | ⟦I leveled a photo that had been tilted noticeably to one side.⟧ |

#### Adding descriptive keyword tags to photos · adjacent to photo-library organization · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-PHOTO-TAG-1` | ⟦I added descriptive tags to the photos in my library.⟧ |
| `ADJ-PHOTO-TAG-2` | ⟦I labeled each picture with searchable keywords so I could find it later.⟧ |
| `ADJ-PHOTO-TAG-3` | ⟦Going through the folder, I tagged every photograph with words describing its contents.⟧ |
| `ADJ-PHOTO-TAG-4` | ⟦The photo collection became easier to search after I assigned keyword labels to its images.⟧ |

#### Eating blueberries · adjacent to eating fruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-BLUEBERRY-1` | ⟦I ate a handful of blueberries with breakfast.⟧ |
| `ADJ-BLUEBERRY-2` | ⟦I snacked on a small bowl of ripe blueberries.⟧ |
| `ADJ-BLUEBERRY-3` | ⟦One by one, I finished the blueberries I had packed for lunch.⟧ |
| `ADJ-BLUEBERRY-4` | ⟦After dinner, I ate the fresh blueberries left in the bowl.⟧ |

#### Eating steamed broccoli · adjacent to eating vegetables · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-STEAMED-BROCCOLI-1` | ⟦I ate a serving of steamed broccoli with dinner.⟧ |
| `ADJ-STEAMED-BROCCOLI-2` | ⟦The broccoli florets had been steamed, and I finished them with lunch.⟧ |
| `ADJ-STEAMED-BROCCOLI-3` | ⟦I ate broccoli that had just come out of the steamer basket.⟧ |
| `ADJ-STEAMED-BROCCOLI-4` | ⟦I finished a bowl of steamed broccoli as my vegetable side.⟧ |

#### Watching a feature-length film · adjacent to consuming media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-FEATURE-FILM-1` | ⟦I watched a feature film from beginning to end.⟧ |
| `ADJ-FEATURE-FILM-2` | ⟦Last night I settled in and watched a full-length movie.⟧ |
| `ADJ-FEATURE-FILM-3` | ⟦The feature-length movie kept me watching all the way through the closing credits.⟧ |
| `ADJ-FEATURE-FILM-4` | ⟦I put on a feature-length film and watched the whole thing.⟧ |

#### Watching a live sports broadcast · adjacent to consuming media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-LIVE-SPORTS-1` | ⟦I watched a sporting event as it unfolded in a live television broadcast.⟧ |
| `ADJ-LIVE-SPORTS-2` | ⟦The match was televised as it happened, and I followed it on screen.⟧ |
| `ADJ-LIVE-SPORTS-3` | ⟦I tuned in to watch the live broadcast of the sports game.⟧ |
| `ADJ-LIVE-SPORTS-4` | ⟦Watching the live sports coverage let me see every play in real time.⟧ |

### Layer `B` · bridging subjects · 32 vectors

Each subject is one precise intersection of attributes already present in the
probe neighborhoods. These are not expected to occupy any predetermined
geometric position. They test how legitimate semantic connections affect the
probe segments.

#### Drinking iced cold-brew coffee · bridges iced coffee and cold-brew coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-ICED-COLD-BREW-1` | ⟦I drank cold-brew coffee poured over ice.⟧ |
| `BRIDGE-ICED-COLD-BREW-2` | ⟦I sipped cold-brew coffee from a glass filled with ice.⟧ |
| `BRIDGE-ICED-COLD-BREW-3` | ⟦The iced coffee I drank had been prepared by cold brewing.⟧ |
| `BRIDGE-ICED-COLD-BREW-4` | ⟦The coffee I finished was cold-brewed and chilled with ice cubes.⟧ |

#### Pour-over brewing with dark-roast beans · bridges dark roast and pour-over · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-DARK-POUR-OVER-1` | ⟦I brewed dark-roast coffee with a pour-over dripper.⟧ |
| `BRIDGE-DARK-POUR-OVER-2` | ⟦My pour-over used dark-roasted beans.⟧ |
| `BRIDGE-DARK-POUR-OVER-3` | ⟦I made a pour-over using dark-roasted coffee beans.⟧ |
| `BRIDGE-DARK-POUR-OVER-4` | ⟦My pour-over was brewed from dark-roast coffee grounds.⟧ |

#### Cropping a portrait photograph · bridges portraits and cropping · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-CROPPED-PORTRAIT-1` | ⟦I cropped the portrait to remove empty space around the person.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-2` | ⟦To tighten its framing, I trimmed the edges of a portrait photo.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-3` | ⟦I reframed the person’s portrait by cutting away the outer parts of the image.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-4` | ⟦The portrait was cropped so the person filled more of the frame.⟧ |

#### Sharing a photo link by email · bridges email and link sharing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-EMAILED-PHOTO-LINK-1` | ⟦I emailed someone a web link to the photo.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-2` | ⟦I shared the picture by putting its viewing link in an email.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-3` | ⟦The email I sent contained a link that opened the photograph.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-4` | ⟦I shared the online photo through an emailed link.⟧ |

#### Eating raw spinach · bridges raw produce and spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-RAW-SPINACH-1` | ⟦I ate raw spinach leaves in a salad.⟧ |
| `BRIDGE-RAW-SPINACH-2` | ⟦The spinach I ate was fresh and uncooked.⟧ |
| `BRIDGE-RAW-SPINACH-3` | ⟦I snacked on spinach without cooking it.⟧ |
| `BRIDGE-RAW-SPINACH-4` | ⟦I ate spinach served raw with my meal.⟧ |

#### Eating cooked lettuce · bridges cooked produce and lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-COOKED-LETTUCE-1` | ⟦I ate lettuce after grilling it.⟧ |
| `BRIDGE-COOKED-LETTUCE-2` | ⟦The lettuce I ate had been cooked until wilted.⟧ |
| `BRIDGE-COOKED-LETTUCE-3` | ⟦I ate cooked lettuce as a dinner side.⟧ |
| `BRIDGE-COOKED-LETTUCE-4` | ⟦I braised lettuce before eating it.⟧ |

#### Listening to a news-interview podcast · bridges news and interview podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-NEWS-INTERVIEW-PODCAST-1` | ⟦I listened to a news podcast built around an interview with a reporter.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-2` | ⟦The podcast episode covered current news through a guest interview.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-3` | ⟦I heard a host interview an expert about the day’s news on a podcast.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-4` | ⟦My news podcast featured a conversation with a guest about current events.⟧ |

#### Reading a digital nonfiction book · bridges nonfiction books and digital media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-DIGITAL-NONFICTION-BOOK-1` | ⟦I read a nonfiction book in digital form.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-2` | ⟦I read a nonfiction ebook on my e-reader.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-3` | ⟦I read a factual book on a screen rather than on paper.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-4` | ⟦The nonfiction book I was reading was an electronic edition.⟧ |

## Reviewing the returned segments

Freeze and preserve every run's complete output before restoring fixture
identities.

For the probe-only run, review every returned segment containing at least two
probe vectors. For each background intervention, review every returned segment
that contains at least one probe and at least two total vectors. Background-only
segments are preserved but are outside this composition comparison.

The primary review is blind to the fixture IDs, cohort identities, and path
annotations. Give each vector a neutral temporary label, show all of the
segment's complete masks, and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

Record the proposed subject and whether every mask genuinely fits it. If no
precise recognizable subject covers every member, record a false merge and the
specific masks that make it false. Do not rescue a false merge with a vague
umbrella, a list of unrelated subjects, or the hidden diagnostic paths.

After the primary review is frozen, reveal the probe paths, cohort identities,
and background-layer roles for diagnosis. Record:

- every returned probe-containing segment and its complete masks;
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

### Comparing background interventions

Let `P` be the 128 probe IDs. For each returned segment in each run:

1. intersect its members with `P`;
2. discard an empty intersection;
3. retain one-probe intersections because a probe may share the full segment
   with background vectors;
4. remove duplicate projected member sets.

Compare each intervention with the probe-only result. Record:

- projected probe-member sets added or removed from the complete collection;
- probe pairs that begin sharing a segment;
- probe pairs that stop sharing a segment;
- probes that become assigned or unassigned;
- background vectors added to every probe-containing segment;
- changes in overlapping memberships;
- the complete masks and semantic review for every changed segment.

The exact projected member-set collection is the primary structural
comparison. Pairwise and assignment summaries diagnose that comparison but do
not replace it, because different overlapping segment collections can produce
the same probe-pair relationships.

Also compare the three equal-count intervention runs directly:

- `P+A` against `P+D` contrasts adjacent additions with an equal number of
  distant additions;
- `P+B` against `P+D` contrasts bridging additions with an equal number of
  distant additions;
- `P+B` against `P+A` contrasts cross-cutting bridges with ordinary local
  additions at equal count.

A change shared by `P+D`, `P+A`, and `P+B` cannot be attributed to one layer's
semantic role; it may be a generic collection-size or composition effect.
Differences between these runs apply to the exact frozen layer fixtures. Count
is controlled, but wording and subject content necessarily differ, so the
contrasts do not establish a universal effect for “distant,” “adjacent,” or
“bridging” material.

A change is not automatically a failure. Added context can expose an artificial
probe-only grouping, connect valid additional instances, create a false merge,
or fragment a coherent segment. The masks and frozen review establish which
occurred.

This experiment has no mandatory semantic-boundary score, highest rung, or
binary pass/fail verdict. It characterizes a development candidate. Any
candidate or configuration changed after inspecting the result requires a new
unseen fixture for subsequent validation.

## Run

1. Approve and freeze all 224 notes and masks, atomic-subject cohorts, probe
   paths, and background-layer roles.
2. Freeze one candidate, configuration, seed, fine-output selector, and all
   opaque input orders before encoding or exposing vector diagnostics.
3. Encode all 224 inputs once under the shared contract in README.md.
4. Run these five fixed collections without retuning or re-encoding:

   | Run | Inputs | Count | Purpose |
   |---|---|---:|---|
   | `P` | probes | 128 | probe-only baseline |
   | `P+D` | probes plus distant layer | 160 | distant composition |
   | `P+A` | probes plus adjacent layer | 160 | local semantic density |
   | `P+B` | probes plus bridging layer | 160 | legitimate semantic connections |
   | `P+D+A+B` | probes plus all layers | 224 | combined background composition |

5. Preserve every complete output before restoring fixture identities.
6. Complete and freeze the blind segment reviews and intervention comparisons.
7. Reveal the diagnostic annotations and complete the diagnostic record.

One frozen shuffled probe order occupies the first 128 positions in every run.
Each added layer has its own frozen shuffled order after the probes. The
combined run appends `D`, then `A`, then `B`. This preserves every probe's input
ordinal across runs; Experiment 6 separately tests order sensitivity.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, all five complete returned memberships, blind review judgments,
projected probe comparisons, annotation-based diagnostics, and all generated
artifact hashes.

## Scope

This is an exploratory test of the complete frozen SSE-plus-segmentation
system. A failure may originate in the SSE geometry, the candidate, or their
interaction; cosine diagnostics cannot conclusively attribute causation.

The diagnostic paths and background roles are human interpretations of this
synthetic corpus, not universal semantic-distance thresholds or a required
hierarchy. The interventions establish sensitivity only to these three
32-vector additions; they do not reproduce production-scale corpus
composition. Experiments 3–6 separately test lexical traps, unmasked context,
unequal density, and broader irrelevant-change stability.
