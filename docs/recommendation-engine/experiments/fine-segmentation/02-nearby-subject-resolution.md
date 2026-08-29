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

The fixture contains 192 vectors in 48 annotated atomic-subject cohorts, with
four controlled formulations per cohort. Every complete note is also its
complete mask. Every concept is ordinary and stated directly; no relationship
depends on obscure facts or compositional role ordering.

The first 128 vectors form four densely structured neighborhoods. Another 32
vectors add nearby subjects, and the final 32 add precise subjects that combine
attributes already represented in those neighborhoods. Together, these inputs
provide varied nearby-subject relationships for one segmentation run.

The four formulations of each subject are independently worded. Sibling
subjects do not reuse aligned sentence templates. Repeated words remain only
where they directly express the subject being tested.

The diagnostic annotations are balanced by construction:

| Path depth | Annotated groups | Vectors per group |
|---|---:|---:|
| Structured core | 1 | 128 |
| First path term | 4 | 32 |
| First two path terms | 8 | 16 |
| First three path terms | 16 | 8 |
| Complete path | 32 | 4 |

This balances support among peer annotations in the structured core. Unequal
density and sparsity are tested separately in Experiment 5. Stability under
irrelevant corpus changes is tested separately in Experiment 6.

The candidate receives only opaque IDs and vectors, not the cohort identities
or diagnostic annotations.

Each structured-neighborhood table has one complete diagnostic path in its
title. Reading a path from left to right gives progressively narrower human
interpretations of the masks. The additional table titles identify adjacent or
cross-cutting relationships. These annotations help diagnose returned segments
after their blind review. They are not expected output and do not determine
correctness.

## Structured subject neighborhoods · 128 vectors

The structured core is a diagnostic collection, not a claim that every vector
shares one subject.

### Coffee activities > Coffee preparation > Roasting coffee > Light-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I pulled the coffee beans from the roaster at the light-roast stage.⟧ |
| `LIGHT-ROAST-2` | ⟦A batch of green coffee beans came out lightly roasted.⟧ |
| `LIGHT-ROAST-3` | ⟦I kept this coffee-bean roast light.⟧ |
| `LIGHT-ROAST-4` | ⟦These green coffee beans were prepared as a light roast.⟧ |

### Coffee activities > Coffee preparation > Roasting coffee > Dark-roast preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦The coffee beans stayed in the roaster until they reached a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦I turned a batch of green coffee beans into dark-roast coffee.⟧ |
| `DARK-ROAST-3` | ⟦This batch of coffee was roasted dark.⟧ |
| `DARK-ROAST-4` | ⟦The finished coffee beans had a dark roast.⟧ |

### Coffee activities > Coffee preparation > Brewing coffee > Pour-over brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `POUR-OVER-1` | ⟦Hot water passed through the coffee grounds in my pour-over dripper.⟧ |
| `POUR-OVER-2` | ⟦A pour-over cone was how I brewed this cup of coffee.⟧ |
| `POUR-OVER-3` | ⟦I made coffee by hand-pouring water through a filter.⟧ |
| `POUR-OVER-4` | ⟦The coffee in my cup came from a pour-over brew.⟧ |

### Coffee activities > Coffee preparation > Brewing coffee > Espresso brewing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ESPRESSO-1` | ⟦I pulled an espresso shot from the machine.⟧ |
| `ESPRESSO-2` | ⟦The coffee I prepared was espresso.⟧ |
| `ESPRESSO-3` | ⟦An espresso brewer produced my shot.⟧ |
| `ESPRESSO-4` | ⟦A small shot of espresso came out of the pressurized brewer.⟧ |

### Coffee activities > Drinking coffee > Drinking hot coffee > Drinking hot black coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BLACK-HOT-1` | ⟦Steam rose from the black coffee as I drank it.⟧ |
| `BLACK-HOT-2` | ⟦I finished a hot cup of coffee with no milk or cream.⟧ |
| `BLACK-HOT-3` | ⟦The coffee I was sipping was served hot and black.⟧ |
| `BLACK-HOT-4` | ⟦The black coffee was still hot when I drank it.⟧ |

### Coffee activities > Drinking coffee > Drinking hot coffee > Drinking hot coffee with milk · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `MILK-HOT-1` | ⟦I added milk to the hot coffee before drinking it.⟧ |
| `MILK-HOT-2` | ⟦A steaming cup of milky coffee was what I sipped.⟧ |
| `MILK-HOT-3` | ⟦The coffee I finished was served hot with milk.⟧ |
| `MILK-HOT-4` | ⟦I drank a mixture of hot coffee and milk.⟧ |

### Coffee activities > Drinking coffee > Drinking cold coffee > Drinking iced coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ICED-COFFEE-1` | ⟦The coffee I drank was chilled by ice cubes.⟧ |
| `ICED-COFFEE-2` | ⟦I poured coffee over ice and drank it cold.⟧ |
| `ICED-COFFEE-3` | ⟦My cup held iced coffee when I took a sip.⟧ |
| `ICED-COFFEE-4` | ⟦I drank a cold coffee served on ice.⟧ |

### Coffee activities > Drinking coffee > Drinking cold coffee > Drinking cold-brew coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLD-BREW-1` | ⟦Cold-brew coffee was what I drank.⟧ |
| `COLD-BREW-2` | ⟦The coffee I sipped had been made by cold brewing.⟧ |
| `COLD-BREW-3` | ⟦I finished a cup of cold brew.⟧ |
| `COLD-BREW-4` | ⟦I was drinking coffee prepared as cold brew.⟧ |

### Working with photos > Making and editing photos > Taking photos > Taking portraits · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PORTRAIT-1` | ⟦A person posed while I made their portrait photograph.⟧ |
| `PORTRAIT-2` | ⟦Someone was the subject of the portrait my camera captured.⟧ |
| `PORTRAIT-3` | ⟦The image I made was a person’s portrait.⟧ |
| `PORTRAIT-4` | ⟦The photograph I took presented one person as a portrait.⟧ |

### Working with photos > Making and editing photos > Taking photos > Taking landscape photos · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LANDSCAPE-1` | ⟦I photographed the scenery as a landscape.⟧ |
| `LANDSCAPE-2` | ⟦A wide outdoor view became my landscape photo.⟧ |
| `LANDSCAPE-3` | ⟦My camera captured the natural surroundings in a landscape image.⟧ |
| `LANDSCAPE-4` | ⟦The shot I took showed a broad landscape.⟧ |

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
| `COLOR-ADJUST-3` | ⟦Adjusting the photograph's color settings changed how the image looked.⟧ |
| `COLOR-ADJUST-4` | ⟦I corrected the colors while editing an image.⟧ |

### Working with photos > Storing and sharing photos > Backing up photos > Local photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦For recovery, I keep a copy of my photo library on an external drive connected to my computer.⟧ |
| `LOCAL-BACKUP-2` | ⟦My pictures are backed up to a USB disk beside my computer.⟧ |
| `LOCAL-BACKUP-3` | ⟦I copied every photo onto locally attached storage in case the originals are lost.⟧ |
| `LOCAL-BACKUP-4` | ⟦An external hard drive stores the photo backup locally.⟧ |

### Working with photos > Storing and sharing photos > Backing up photos > Cloud photo backups · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦My photo library has a recovery copy in online cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦A remote storage service backs up my pictures.⟧ |
| `CLOUD-BACKUP-3` | ⟦I uploaded all my photos to the cloud so they could be restored if needed.⟧ |
| `CLOUD-BACKUP-4` | ⟦The backup of my photograph collection lives on off-site cloud servers.⟧ |

### Working with photos > Storing and sharing photos > Sharing photos > Sharing photos by email · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `EMAIL-SHARE-1` | ⟦I attached the photograph to a message and sent it by email.⟧ |
| `EMAIL-SHARE-2` | ⟦I sent the picture as an email attachment.⟧ |
| `EMAIL-SHARE-3` | ⟦Email was how I delivered a photo to another person.⟧ |
| `EMAIL-SHARE-4` | ⟦Someone received the image file in an email from me.⟧ |

### Working with photos > Storing and sharing photos > Sharing photos > Sharing photos by link · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LINK-SHARE-1` | ⟦I gave someone the web address where my photo could be viewed.⟧ |
| `LINK-SHARE-2` | ⟦A link I shared opened the photograph online.⟧ |
| `LINK-SHARE-3` | ⟦The picture was available through a viewing URL I sent to another person.⟧ |
| `LINK-SHARE-4` | ⟦I sent someone an online link to my image.⟧ |

### Eating produce > Eating fruit > Eating apples > Eating red apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RED-APPLE-1` | ⟦I ate an apple with red skin.⟧ |
| `RED-APPLE-2` | ⟦I ate a red apple down to its core.⟧ |
| `RED-APPLE-3` | ⟦I finished eating a red-skinned apple.⟧ |
| `RED-APPLE-4` | ⟦The apple I ate was red.⟧ |

### Eating produce > Eating fruit > Eating apples > Eating green apples · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GREEN-APPLE-1` | ⟦A green apple was what I ate.⟧ |
| `GREEN-APPLE-2` | ⟦Green skin covered the apple I was eating.⟧ |
| `GREEN-APPLE-3` | ⟦I ate an apple that was green.⟧ |
| `GREEN-APPLE-4` | ⟦The fruit I finished eating was a green apple.⟧ |

### Eating produce > Eating fruit > Eating citrus fruit > Eating oranges · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ORANGE-1` | ⟦I ate an orange.⟧ |
| `ORANGE-2` | ⟦The fruit I was eating was an orange.⟧ |
| `ORANGE-3` | ⟦An orange was what I finished eating.⟧ |
| `ORANGE-4` | ⟦I consumed an orange.⟧ |

### Eating produce > Eating fruit > Eating citrus fruit > Eating grapefruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GRAPEFRUIT-1` | ⟦Some grapefruit was what I ate.⟧ |
| `GRAPEFRUIT-2` | ⟦I finished eating a grapefruit.⟧ |
| `GRAPEFRUIT-3` | ⟦I ate grapefruit as my citrus fruit.⟧ |
| `GRAPEFRUIT-4` | ⟦I ate my way through some grapefruit.⟧ |

### Eating produce > Eating vegetables > Eating carrots > Eating raw carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RAW-CARROT-1` | ⟦The carrot I ate was raw.⟧ |
| `RAW-CARROT-2` | ⟦I snacked on an uncooked carrot.⟧ |
| `RAW-CARROT-3` | ⟦A raw carrot crunched between my teeth as I ate it.⟧ |
| `RAW-CARROT-4` | ⟦I ate a carrot without cooking it.⟧ |

### Eating produce > Eating vegetables > Eating carrots > Eating cooked carrots · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COOKED-CARROT-1` | ⟦I ate a carrot that had been cooked.⟧ |
| `COOKED-CARROT-2` | ⟦A cooked carrot was part of what I ate.⟧ |
| `COOKED-CARROT-3` | ⟦The carrot on my plate had been cooked before I ate it.⟧ |
| `COOKED-CARROT-4` | ⟦I finished eating a cooked carrot.⟧ |

### Eating produce > Eating vegetables > Eating leafy greens > Eating lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LETTUCE-1` | ⟦I ate some lettuce.⟧ |
| `LETTUCE-2` | ⟦Lettuce leaves were part of what I ate.⟧ |
| `LETTUCE-3` | ⟦I finished the lettuce I was eating.⟧ |
| `LETTUCE-4` | ⟦The leafy food I ate was lettuce.⟧ |

### Eating produce > Eating vegetables > Eating leafy greens > Eating spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `SPINACH-1` | ⟦A serving of spinach was what I ate.⟧ |
| `SPINACH-2` | ⟦I consumed a portion of spinach.⟧ |
| `SPINACH-3` | ⟦I ate the spinach in front of me.⟧ |
| `SPINACH-4` | ⟦The greens I finished eating were spinach.⟧ |

### Consuming media > Reading > Reading books > Reading fiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-BOOK-1` | ⟦I read a novel.⟧ |
| `FICTION-BOOK-2` | ⟦The book I finished told a fictional story.⟧ |
| `FICTION-BOOK-3` | ⟦A fictional book occupied my reading time.⟧ |
| `FICTION-BOOK-4` | ⟦My latest reading was an invented narrative in book form.⟧ |

### Consuming media > Reading > Reading books > Reading nonfiction books · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-BOOK-1` | ⟦I read a nonfiction book.⟧ |
| `NONFICTION-BOOK-2` | ⟦Factual material filled the book I was reading.⟧ |
| `NONFICTION-BOOK-3` | ⟦A book of nonfiction was what I finished reading.⟧ |
| `NONFICTION-BOOK-4` | ⟦My reading time went to a book of nonfiction.⟧ |

### Consuming media > Reading > Reading magazines > Reading print magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PRINT-MAGAZINE-1` | ⟦I read a magazine printed on paper.⟧ |
| `PRINT-MAGAZINE-2` | ⟦Turning physical pages, I worked through a magazine issue.⟧ |
| `PRINT-MAGAZINE-3` | ⟦I read the print magazine I held in my hands.⟧ |
| `PRINT-MAGAZINE-4` | ⟦My magazine reading came from a paper copy.⟧ |

### Consuming media > Reading > Reading magazines > Reading digital magazines · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIGITAL-MAGAZINE-1` | ⟦A digital magazine was what I read.⟧ |
| `DIGITAL-MAGAZINE-2` | ⟦The magazine issue appeared on a screen while I read it.⟧ |
| `DIGITAL-MAGAZINE-3` | ⟦My screen displayed the digital magazine I was reading.⟧ |
| `DIGITAL-MAGAZINE-4` | ⟦I read a magazine that had been published digitally.⟧ |

### Consuming media > Listening > Listening to podcasts > Listening to news podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NEWS-PODCAST-1` | ⟦I listened to a news podcast.⟧ |
| `NEWS-PODCAST-2` | ⟦Current events were the subject of the podcast episode I heard.⟧ |
| `NEWS-PODCAST-3` | ⟦A podcast supplied the news I was listening to.⟧ |
| `NEWS-PODCAST-4` | ⟦The audio program I played covered recent news in podcast form.⟧ |

### Consuming media > Listening > Listening to podcasts > Listening to interview podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `INTERVIEW-PODCAST-1` | ⟦A guest interview filled the podcast I listened to.⟧ |
| `INTERVIEW-PODCAST-2` | ⟦I played a podcast built around a host interviewing a guest.⟧ |
| `INTERVIEW-PODCAST-3` | ⟦The episode I heard featured a conversation with an interviewee.⟧ |
| `INTERVIEW-PODCAST-4` | ⟦My podcast listening centered on an interview.⟧ |

### Consuming media > Listening > Listening to audiobooks > Listening to fiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-AUDIOBOOK-1` | ⟦I listened to a novel in audiobook form.⟧ |
| `FICTION-AUDIOBOOK-2` | ⟦The audiobook I heard contained a narrator’s performance of a fictional story.⟧ |
| `FICTION-AUDIOBOOK-3` | ⟦A work of fiction was playing as an audiobook for me.⟧ |
| `FICTION-AUDIOBOOK-4` | ⟦My listening was an audio edition of a fictional book.⟧ |

### Consuming media > Listening > Listening to audiobooks > Listening to nonfiction audiobooks · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-AUDIOBOOK-1` | ⟦My audiobook was a work of nonfiction.⟧ |
| `NONFICTION-AUDIOBOOK-2` | ⟦I listened to factual material narrated from a book.⟧ |
| `NONFICTION-AUDIOBOOK-3` | ⟦The audio edition I played presented real events as fact.⟧ |
| `NONFICTION-AUDIOBOOK-4` | ⟦A nonfiction book was read aloud in the recording I heard.⟧ |

## Additional adjacent subjects · 32 vectors

These subjects belong near the four structured areas without intentionally
joining two existing cohorts. They add further nearby distinctions to the same
corpus.

### Cleaning a burr coffee grinder · adjacent to coffee preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-GRINDER-CLEAN-1` | ⟦I brushed old coffee grounds out of my burr grinder.⟧ |
| `ADJ-GRINDER-CLEAN-2` | ⟦I cleaned the coffee residue from the burrs inside my grinder.⟧ |
| `ADJ-GRINDER-CLEAN-3` | ⟦Trapped grounds had collected around the burrs, so I cleaned the coffee grinder.⟧ |
| `ADJ-GRINDER-CLEAN-4` | ⟦I opened my burr coffee grinder and cleared away the stale dust inside.⟧ |

### Descaling an automatic drip coffee maker · adjacent to coffee preparation · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-DRIP-DESCALE-1` | ⟦I ran a descaling cycle to remove mineral buildup from my automatic drip coffee maker.⟧ |
| `ADJ-DRIP-DESCALE-2` | ⟦I flushed limescale from the drip coffee machine with a descaling solution.⟧ |
| `ADJ-DRIP-DESCALE-3` | ⟦Cleaning out the mineral deposits left my automatic drip coffee brewer free of scale.⟧ |
| `ADJ-DRIP-DESCALE-4` | ⟦I descaled the automatic drip coffee brewer to clear the chalky buildup inside it.⟧ |

### Straightening a tilted photograph · adjacent to photo editing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-PHOTO-STRAIGHTEN-1` | ⟦I straightened a tilted photo until its edges sat level.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-2` | ⟦The picture looked crooked, so I rotated it slightly to square it up.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-3` | ⟦A small rotation corrected the slant in the photograph.⟧ |
| `ADJ-PHOTO-STRAIGHTEN-4` | ⟦I leveled a photo that had been tilted noticeably to one side.⟧ |

### Adding descriptive keyword tags to photos · adjacent to photo-library organization · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-PHOTO-TAG-1` | ⟦I added descriptive tags to the photos in my library.⟧ |
| `ADJ-PHOTO-TAG-2` | ⟦I labeled each picture with searchable keywords so I could find it later.⟧ |
| `ADJ-PHOTO-TAG-3` | ⟦Going through the folder, I tagged every photograph with words describing its contents.⟧ |
| `ADJ-PHOTO-TAG-4` | ⟦The photo collection became easier to search after I assigned keyword labels to its images.⟧ |

### Eating blueberries · adjacent to eating fruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-BLUEBERRY-1` | ⟦I ate a handful of blueberries with breakfast.⟧ |
| `ADJ-BLUEBERRY-2` | ⟦I snacked on a small bowl of ripe blueberries.⟧ |
| `ADJ-BLUEBERRY-3` | ⟦One by one, I finished the blueberries I had packed for lunch.⟧ |
| `ADJ-BLUEBERRY-4` | ⟦After dinner, I ate the fresh blueberries left in the bowl.⟧ |

### Eating steamed broccoli · adjacent to eating vegetables · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-STEAMED-BROCCOLI-1` | ⟦I ate a serving of steamed broccoli with dinner.⟧ |
| `ADJ-STEAMED-BROCCOLI-2` | ⟦The broccoli florets had been steamed, and I finished them with lunch.⟧ |
| `ADJ-STEAMED-BROCCOLI-3` | ⟦I ate broccoli that had just come out of the steamer basket.⟧ |
| `ADJ-STEAMED-BROCCOLI-4` | ⟦I finished a bowl of steamed broccoli as my vegetable side.⟧ |

### Watching a feature-length film · adjacent to consuming media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-FEATURE-FILM-1` | ⟦I watched a feature-length film.⟧ |
| `ADJ-FEATURE-FILM-2` | ⟦A full-length movie was what I viewed.⟧ |
| `ADJ-FEATURE-FILM-3` | ⟦I settled in to watch a feature film.⟧ |
| `ADJ-FEATURE-FILM-4` | ⟦The movie I viewed on my screen was feature length.⟧ |

### Watching a live sports broadcast · adjacent to consuming media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ADJ-LIVE-SPORTS-1` | ⟦I watched a sporting event as it unfolded in a live television broadcast.⟧ |
| `ADJ-LIVE-SPORTS-2` | ⟦The match was televised as it happened, and I followed it on screen.⟧ |
| `ADJ-LIVE-SPORTS-3` | ⟦I tuned in to watch the live broadcast of the sports game.⟧ |
| `ADJ-LIVE-SPORTS-4` | ⟦Watching the live sports coverage let me see every play in real time.⟧ |

## Cross-cutting subjects · 32 vectors

Each subject is one precise intersection of attributes already present in the
structured neighborhoods. These are not expected to occupy any predetermined
geometric position. They expose relationships that a useful fine segmentation
may represent through broader, narrower, or overlapping segments.

### Drinking iced cold-brew coffee · bridges iced coffee and cold-brew coffee · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-ICED-COLD-BREW-1` | ⟦Ice chilled the cold-brew coffee I drank.⟧ |
| `BRIDGE-ICED-COLD-BREW-2` | ⟦I poured cold brew over ice before sipping it.⟧ |
| `BRIDGE-ICED-COLD-BREW-3` | ⟦The iced coffee I drank had been prepared by cold brewing.⟧ |
| `BRIDGE-ICED-COLD-BREW-4` | ⟦The coffee I finished was cold-brewed and chilled with ice cubes.⟧ |

### Pour-over brewing with dark-roast beans · bridges dark roast and pour-over · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-DARK-POUR-OVER-1` | ⟦Dark-roasted beans went into the pour-over I brewed.⟧ |
| `BRIDGE-DARK-POUR-OVER-2` | ⟦My pour-over used dark-roasted beans.⟧ |
| `BRIDGE-DARK-POUR-OVER-3` | ⟦The coffee from my pour-over had a dark roast.⟧ |
| `BRIDGE-DARK-POUR-OVER-4` | ⟦My pour-over was brewed from dark-roast coffee grounds.⟧ |

### Cropping a portrait photograph · bridges portraits and cropping · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-CROPPED-PORTRAIT-1` | ⟦I cropped the portrait to remove empty space around the person.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-2` | ⟦To tighten its framing, I trimmed the edges of a portrait photo.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-3` | ⟦I reframed the person’s portrait by cutting away the outer parts of the image.⟧ |
| `BRIDGE-CROPPED-PORTRAIT-4` | ⟦The portrait was cropped so the person filled more of the frame.⟧ |

### Sharing a photo link by email · bridges email and link sharing · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-EMAILED-PHOTO-LINK-1` | ⟦I emailed someone a web link to the photo.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-2` | ⟦I shared the picture by putting its viewing link in an email.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-3` | ⟦The email I sent contained a link that opened the photograph.⟧ |
| `BRIDGE-EMAILED-PHOTO-LINK-4` | ⟦I shared the online photo through an emailed link.⟧ |

### Eating raw spinach · bridges raw produce and spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-RAW-SPINACH-1` | ⟦I ate raw spinach leaves in a salad.⟧ |
| `BRIDGE-RAW-SPINACH-2` | ⟦The spinach I ate was fresh and uncooked.⟧ |
| `BRIDGE-RAW-SPINACH-3` | ⟦I snacked on spinach without cooking it.⟧ |
| `BRIDGE-RAW-SPINACH-4` | ⟦I ate spinach served raw with my meal.⟧ |

### Eating cooked lettuce · bridges cooked produce and lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-COOKED-LETTUCE-1` | ⟦I ate lettuce after grilling it.⟧ |
| `BRIDGE-COOKED-LETTUCE-2` | ⟦The lettuce I ate had been cooked until wilted.⟧ |
| `BRIDGE-COOKED-LETTUCE-3` | ⟦I ate cooked lettuce as a dinner side.⟧ |
| `BRIDGE-COOKED-LETTUCE-4` | ⟦I braised lettuce before eating it.⟧ |

### Listening to a news-interview podcast · bridges news and interview podcasts · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-NEWS-INTERVIEW-PODCAST-1` | ⟦I listened to a news podcast built around an interview with a reporter.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-2` | ⟦The podcast episode covered current news through a guest interview.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-3` | ⟦I heard a host interview an expert about the day’s news on a podcast.⟧ |
| `BRIDGE-NEWS-INTERVIEW-PODCAST-4` | ⟦My news podcast featured a conversation with a guest about current events.⟧ |

### Reading a digital nonfiction book · bridges nonfiction books and digital media · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BRIDGE-DIGITAL-NONFICTION-BOOK-1` | ⟦I read a nonfiction book in digital form.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-2` | ⟦I read a nonfiction ebook on my e-reader.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-3` | ⟦I read a factual book on a screen rather than on paper.⟧ |
| `BRIDGE-DIGITAL-NONFICTION-BOOK-4` | ⟦The nonfiction book I was reading was an electronic edition.⟧ |

## Reviewing the returned segments

Freeze and preserve the complete output before restoring fixture identities.
Review every returned segment containing at least two vectors.

The primary review is blind to the fixture IDs, cohort identities, and path
annotations. Give each vector a neutral temporary label, show all of the
segment's complete masks, and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

Record the proposed subject and whether every mask genuinely fits it. If no
precise recognizable subject covers every member, record a false merge and the
specific masks that make it false. Do not rescue a false merge with a vague
umbrella, a list of unrelated subjects, or the hidden diagnostic paths.

After the primary review is frozen, reveal the diagnostic paths and cohort
identities. Record:

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

1. Approve and freeze all 192 notes and masks, atomic-subject cohorts,
   diagnostic paths, and the wording-independence control above.
2. Freeze one candidate, configuration, seed, fine-output selector, and one
   shuffled opaque input order before encoding or exposing vector diagnostics.
3. Encode all 192 inputs once under the shared contract in README.md.
4. Run the frozen candidate once without retuning.
5. Preserve the complete output before restoring fixture identities.
6. Complete and freeze the blind segment review.
7. Reveal the diagnostic annotations and complete the diagnostic record.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, blind review judgments,
annotation-based diagnostics, and all generated artifact hashes.

## Scope

This is an exploratory test of the complete frozen SSE-plus-segmentation
system. A failure may originate in the SSE geometry, the candidate, or their
interaction; cosine diagnostics cannot conclusively attribute causation.

The diagnostic paths and cohort identities are human interpretations of this
synthetic corpus, not universal semantic-distance thresholds or a required
hierarchy. Experiments 3–6 separately test lexical traps, unmasked context,
unequal density, and irrelevant-change stability.
