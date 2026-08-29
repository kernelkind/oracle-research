# Experiment 2: exploratory nearby-subject segmentation

Status: **draft; every atomic proposition and mask requires human approval
before encoding**.

## Purpose

The motivating assumption is:

> Nearby but meaningfully distinct fine subjects are resolved.

This experiment does not pass or fail that assumption. It exposes how one
frozen fine-segmentation candidate organizes a controlled collection of nearby
atomic subjects so a human can judge whether the result is useful, too coarse,
too fragmented, or otherwise revealing.

For each returned multi-vector segment, the primary review asks:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

No partition, mandatory boundary, segment count, or hierarchy is prescribed.

## Fixture

The fixture contains 160 vectors: forty atomic subjects with four formulations
each. Ten subjects concern coffee, ten concern photos, ten concern produce, and
ten concern media. These four neighborhoods organize this document for human
review; neither the candidate nor the blind reviewer receives them.

There are no bridge cohorts or different fixture roles. Every subject has four
formulations. Deliberately varying cohort support, irrelevant corpus changes,
and subjects that combine attributes from multiple regions belong to separate
experiments.

Each subject heading states its frozen atomic proposition. Every formulation
must be semantically equivalent to that proposition:

1. the complete mask must imply the proposition;
2. the proposition must imply the complete meaning of the mask.

This mutual-entailment requirement excludes both missing evidence and added
details such as time, place, motivation, quantity, meal context, or a narrower
method. Every complete note is also its complete mask.

Within each cohort, one formulation may use the canonical subject wording. The
others use ordinary alternative wording where possible. Repeated words are
allowed when they directly express the atomic subject.

The candidate receives one frozen shuffled collection of opaque IDs and raw
vectors. It does not receive the notes, masks, atomic propositions, or fixture
neighborhoods.

## Lexical-only diagnostic

Record how easily surface words alone recover the forty cohorts. This does not
score the candidate; it shows how much lexical shortcut information the
fixture contains.

Before SSE encoding:

1. lowercase each complete mask and tokenize contiguous Unicode letters and
   numbers;
2. build binary unigram vectors with inverse-document-frequency weight
   `ln((1 + 160) / (1 + document_frequency)) + 1`;
3. L2-normalize every vector;
4. for each mask, build every cohort centroid while excluding that mask from
   its own cohort, average the remaining normalized vectors, and L2-normalize
   each centroid;
5. assign the mask only when one centroid has the unique highest cosine;
   preserve exact ties as unresolved;
6. preserve the complete cosine matrix, predicted cohort for every mask,
   confusion matrix, and leave-one-out accuracy.

A high lexical-only accuracy does not invalidate the exploration. It prevents
us from attributing a similar segmentation result uniquely to semantic
geometry.

## Coffee subjects · 40 vectors

### The author roasted coffee beans to a light roast · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I roasted coffee beans to a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦My coffee-bean roasting produced light-roast beans.⟧ |
| `LIGHT-ROAST-3` | ⟦The beans I roasted received a light roast.⟧ |
| `LIGHT-ROAST-4` | ⟦I made light-roast coffee beans by roasting them.⟧ |

### The author roasted coffee beans to a dark roast · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦I gave coffee beans a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦Dark-roast beans were the result of my coffee roasting.⟧ |
| `DARK-ROAST-3` | ⟦The coffee beans I roasted came out dark-roasted.⟧ |
| `DARK-ROAST-4` | ⟦By roasting coffee beans, I made them into a dark roast.⟧ |

### The author brewed coffee using the pour-over method · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `POUR-OVER-1` | ⟦I brewed coffee by the pour-over method.⟧ |
| `POUR-OVER-2` | ⟦Pour-over was how I made the coffee.⟧ |
| `POUR-OVER-3` | ⟦The coffee I prepared was a pour-over brew.⟧ |
| `POUR-OVER-4` | ⟦I made coffee by pouring water through grounds in a filter.⟧ |

### The author brewed espresso · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ESPRESSO-1` | ⟦I brewed espresso.⟧ |
| `ESPRESSO-2` | ⟦The coffee I brewed was espresso.⟧ |
| `ESPRESSO-3` | ⟦Espresso was the kind of coffee I brewed.⟧ |
| `ESPRESSO-4` | ⟦What I produced by brewing the coffee was espresso.⟧ |

### The author drank coffee that was hot and black · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BLACK-HOT-1` | ⟦I drank hot black coffee.⟧ |
| `BLACK-HOT-2` | ⟦The black coffee I drank was hot.⟧ |
| `BLACK-HOT-3` | ⟦Hot coffee taken black was what I drank.⟧ |
| `BLACK-HOT-4` | ⟦What I drank was coffee that was both hot and black.⟧ |

### The author drank coffee that was hot and contained milk · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `MILK-HOT-1` | ⟦Milk was in the hot coffee I drank.⟧ |
| `MILK-HOT-2` | ⟦I drank a hot mixture of coffee and milk.⟧ |
| `MILK-HOT-3` | ⟦The coffee I drank had milk in it and was hot.⟧ |
| `MILK-HOT-4` | ⟦Hot coffee containing milk was what I drank.⟧ |

### The author drank coffee that had been chilled with ice · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ICED-COFFEE-1` | ⟦I drank iced coffee.⟧ |
| `ICED-COFFEE-2` | ⟦Ice had chilled the coffee I drank.⟧ |
| `ICED-COFFEE-3` | ⟦The coffee I drank was cold from ice.⟧ |
| `ICED-COFFEE-4` | ⟦Coffee chilled with ice was what I drank.⟧ |

### The author drank coffee prepared by the cold-brew method · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLD-BREW-1` | ⟦I drank cold-brew coffee.⟧ |
| `COLD-BREW-2` | ⟦Cold brew was the coffee I drank.⟧ |
| `COLD-BREW-3` | ⟦The coffee I drank had been made by cold brewing.⟧ |
| `COLD-BREW-4` | ⟦Coffee prepared by the cold-brew method was what I drank.⟧ |

### The author cleaned a burr coffee grinder · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GRINDER-CLEAN-1` | ⟦I cleaned a burr coffee grinder.⟧ |
| `GRINDER-CLEAN-2` | ⟦The coffee grinder I cleaned was a burr grinder.⟧ |
| `GRINDER-CLEAN-3` | ⟦A coffee grinder that uses burrs was what I cleaned.⟧ |
| `GRINDER-CLEAN-4` | ⟦I gave a burr coffee grinder a cleaning.⟧ |

### The author descaled an automatic drip coffee maker · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DRIP-DESCALE-1` | ⟦I descaled an automatic drip coffee maker.⟧ |
| `DRIP-DESCALE-2` | ⟦Scale was what I removed from an automatic drip coffee machine.⟧ |
| `DRIP-DESCALE-3` | ⟦The coffee brewer I descaled was an automatic drip model.⟧ |
| `DRIP-DESCALE-4` | ⟦I cleared an automatic drip coffee machine of scale.⟧ |

## Photo subjects · 40 vectors

### The author took a portrait photograph · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PORTRAIT-1` | ⟦I took a portrait photograph.⟧ |
| `PORTRAIT-2` | ⟦The picture I shot was a portrait.⟧ |
| `PORTRAIT-3` | ⟦A photographic portrait was what I captured.⟧ |
| `PORTRAIT-4` | ⟦I photographed a subject as a portrait.⟧ |

### The author took a photograph of a landscape · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LANDSCAPE-1` | ⟦I took a photograph of a landscape.⟧ |
| `LANDSCAPE-2` | ⟦I photographed a landscape.⟧ |
| `LANDSCAPE-3` | ⟦A landscape was the subject of the picture I took.⟧ |
| `LANDSCAPE-4` | ⟦The photo I captured depicted a landscape.⟧ |

### The author cropped a photograph · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CROP-PHOTO-1` | ⟦I cropped a photograph.⟧ |
| `CROP-PHOTO-2` | ⟦A crop was the edit I made to a photo.⟧ |
| `CROP-PHOTO-3` | ⟦I trimmed the edges of the picture.⟧ |
| `CROP-PHOTO-4` | ⟦The photograph was cropped by me.⟧ |

### The author adjusted the colors in a photograph · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COLOR-ADJUST-1` | ⟦I adjusted the colors in a photograph.⟧ |
| `COLOR-ADJUST-2` | ⟦The photo's colors were what I changed.⟧ |
| `COLOR-ADJUST-3` | ⟦I made color adjustments to the picture.⟧ |
| `COLOR-ADJUST-4` | ⟦My edit altered the photograph's colors.⟧ |

### The author created a backup of photographs in local storage · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I backed up the photos to local storage.⟧ |
| `LOCAL-BACKUP-2` | ⟦Backup copies of the photographs were kept in local storage by me.⟧ |
| `LOCAL-BACKUP-3` | ⟦I made a local backup of the pictures.⟧ |
| `LOCAL-BACKUP-4` | ⟦Local storage held the photo backup I created.⟧ |

### The author created a backup of photographs in cloud storage · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦A cloud backup was what I made of the photos.⟧ |
| `CLOUD-BACKUP-2` | ⟦I stored backup copies of the pictures in the cloud.⟧ |
| `CLOUD-BACKUP-3` | ⟦The photographs were backed up to cloud storage by me.⟧ |
| `CLOUD-BACKUP-4` | ⟦I created a backup of the photos in cloud storage.⟧ |

### The author sent a photo file as an email attachment · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `EMAIL-SHARE-1` | ⟦I sent a photo file as an email attachment.⟧ |
| `EMAIL-SHARE-2` | ⟦The photograph I emailed was attached as a file.⟧ |
| `EMAIL-SHARE-3` | ⟦I sent an email with the picture file attached.⟧ |
| `EMAIL-SHARE-4` | ⟦The email I sent included the photo as an attached file.⟧ |

### The author shared a photograph by sending a viewing link · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LINK-SHARE-1` | ⟦I sent a viewing link to share a photograph.⟧ |
| `LINK-SHARE-2` | ⟦The link I sent let someone view the photo.⟧ |
| `LINK-SHARE-3` | ⟦I gave another person a link to view the picture.⟧ |
| `LINK-SHARE-4` | ⟦I shared the photograph by sending its viewing link.⟧ |

### The author straightened a tilted photograph · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-STRAIGHTEN-1` | ⟦I straightened a tilted photograph.⟧ |
| `PHOTO-STRAIGHTEN-2` | ⟦The tilted photo was made straight by me.⟧ |
| `PHOTO-STRAIGHTEN-3` | ⟦I corrected the tilt in a picture.⟧ |
| `PHOTO-STRAIGHTEN-4` | ⟦I leveled a photograph that was slanted.⟧ |

### The author assigned descriptive tags to photographs · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-TAG-1` | ⟦I added descriptive tags to photographs.⟧ |
| `PHOTO-TAG-2` | ⟦The tags I assigned to the photos described them.⟧ |
| `PHOTO-TAG-3` | ⟦I labeled the pictures with descriptive tags.⟧ |
| `PHOTO-TAG-4` | ⟦Descriptive terms were what I used to tag the photographs.⟧ |

## Produce subjects · 40 vectors

### The author ate a red apple · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RED-APPLE-1` | ⟦I ate a red apple.⟧ |
| `RED-APPLE-2` | ⟦The apple I ate was red.⟧ |
| `RED-APPLE-3` | ⟦I ate an apple with red skin.⟧ |
| `RED-APPLE-4` | ⟦I consumed an apple that was red.⟧ |

### The author ate a green apple · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GREEN-APPLE-1` | ⟦Green was the color of the apple I ate.⟧ |
| `GREEN-APPLE-2` | ⟦I ate a green-skinned apple.⟧ |
| `GREEN-APPLE-3` | ⟦The apple was green when I ate it.⟧ |
| `GREEN-APPLE-4` | ⟦I ate a green apple.⟧ |

### The author ate an orange · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `ORANGE-1` | ⟦An orange was the fruit I ate.⟧ |
| `ORANGE-2` | ⟦I consumed an orange.⟧ |
| `ORANGE-3` | ⟦I ate an orange.⟧ |
| `ORANGE-4` | ⟦It was an orange that I ate.⟧ |

### The author ate a grapefruit · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `GRAPEFRUIT-1` | ⟦I consumed a grapefruit.⟧ |
| `GRAPEFRUIT-2` | ⟦I ate a grapefruit.⟧ |
| `GRAPEFRUIT-3` | ⟦A grapefruit was what I ate.⟧ |
| `GRAPEFRUIT-4` | ⟦The fruit I ate was a grapefruit.⟧ |

### The author ate a raw carrot · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `RAW-CARROT-1` | ⟦I ate a raw carrot.⟧ |
| `RAW-CARROT-2` | ⟦The carrot I ate was uncooked.⟧ |
| `RAW-CARROT-3` | ⟦I consumed a carrot in its raw state.⟧ |
| `RAW-CARROT-4` | ⟦An uncooked carrot was what I ate.⟧ |

### The author ate a cooked carrot · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `COOKED-CARROT-1` | ⟦A cooked carrot was what I consumed.⟧ |
| `COOKED-CARROT-2` | ⟦The carrot had been cooked before I ate it.⟧ |
| `COOKED-CARROT-3` | ⟦I ate a carrot that had been cooked.⟧ |
| `COOKED-CARROT-4` | ⟦I ate a cooked carrot.⟧ |

### The author ate lettuce · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LETTUCE-1` | ⟦Lettuce was what I consumed.⟧ |
| `LETTUCE-2` | ⟦I ate lettuce.⟧ |
| `LETTUCE-3` | ⟦What I ate was lettuce.⟧ |
| `LETTUCE-4` | ⟦It was lettuce that I ate.⟧ |

### The author ate spinach · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `SPINACH-1` | ⟦The greens I ate were spinach.⟧ |
| `SPINACH-2` | ⟦Spinach was what I ate.⟧ |
| `SPINACH-3` | ⟦I ate spinach.⟧ |
| `SPINACH-4` | ⟦It was spinach that I consumed.⟧ |

### The author ate blueberries · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `BLUEBERRY-1` | ⟦I ate blueberries.⟧ |
| `BLUEBERRY-2` | ⟦Blueberries were what I consumed.⟧ |
| `BLUEBERRY-3` | ⟦The berries I ate were blueberries.⟧ |
| `BLUEBERRY-4` | ⟦It was blueberries that I ate.⟧ |

### The author ate steamed broccoli · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `STEAMED-BROCCOLI-1` | ⟦The broccoli I ate had been steamed.⟧ |
| `STEAMED-BROCCOLI-2` | ⟦I ate broccoli cooked by steaming.⟧ |
| `STEAMED-BROCCOLI-3` | ⟦Steaming was how the broccoli I ate was prepared.⟧ |
| `STEAMED-BROCCOLI-4` | ⟦I ate steamed broccoli.⟧ |

## Media subjects · 40 vectors

### The author read a fiction book · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-BOOK-1` | ⟦I read a fiction book.⟧ |
| `FICTION-BOOK-2` | ⟦The book I read was a work of fiction.⟧ |
| `FICTION-BOOK-3` | ⟦A book containing a fictional story was what I read.⟧ |
| `FICTION-BOOK-4` | ⟦I spent time reading a book of fiction.⟧ |

### The author read a nonfiction book · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-BOOK-1` | ⟦I read a nonfiction book.⟧ |
| `NONFICTION-BOOK-2` | ⟦The book I read was a work of nonfiction.⟧ |
| `NONFICTION-BOOK-3` | ⟦A book of nonfiction was what I read.⟧ |
| `NONFICTION-BOOK-4` | ⟦I spent time reading a book written as nonfiction.⟧ |

### The author read a print magazine · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `PRINT-MAGAZINE-1` | ⟦I read a magazine printed on paper.⟧ |
| `PRINT-MAGAZINE-2` | ⟦The magazine issue I read was a physical print edition.⟧ |
| `PRINT-MAGAZINE-3` | ⟦A paper copy of a magazine was what I read.⟧ |
| `PRINT-MAGAZINE-4` | ⟦A printed magazine issue was what I read.⟧ |

### The author read a digital magazine · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `DIGITAL-MAGAZINE-1` | ⟦I read a digital magazine.⟧ |
| `DIGITAL-MAGAZINE-2` | ⟦The magazine issue I read was electronic.⟧ |
| `DIGITAL-MAGAZINE-3` | ⟦A digital edition of a magazine was what I read.⟧ |
| `DIGITAL-MAGAZINE-4` | ⟦I read a magazine in digital form.⟧ |

### The author listened to a news podcast · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NEWS-PODCAST-1` | ⟦I listened to a news podcast.⟧ |
| `NEWS-PODCAST-2` | ⟦The podcast episode I heard presented news.⟧ |
| `NEWS-PODCAST-3` | ⟦A podcast about news was what I listened to.⟧ |
| `NEWS-PODCAST-4` | ⟦I heard news presented in podcast form.⟧ |

### The author listened to an interview podcast · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `INTERVIEW-PODCAST-1` | ⟦I listened to an interview podcast.⟧ |
| `INTERVIEW-PODCAST-2` | ⟦The podcast episode I heard consisted of a host interviewing a guest.⟧ |
| `INTERVIEW-PODCAST-3` | ⟦A podcast conversation between interviewer and guest was what I heard.⟧ |
| `INTERVIEW-PODCAST-4` | ⟦I listened to a podcast built around an interview.⟧ |

### The author listened to a fiction audiobook · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FICTION-AUDIOBOOK-1` | ⟦I listened to a fiction audiobook.⟧ |
| `FICTION-AUDIOBOOK-2` | ⟦The audiobook I heard narrated a work of fiction.⟧ |
| `FICTION-AUDIOBOOK-3` | ⟦An audio recording of a book of fiction was what I listened to.⟧ |
| `FICTION-AUDIOBOOK-4` | ⟦I listened to a fiction book read aloud in audiobook form.⟧ |

### The author listened to a nonfiction audiobook · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-AUDIOBOOK-1` | ⟦I listened to a nonfiction audiobook.⟧ |
| `NONFICTION-AUDIOBOOK-2` | ⟦The audiobook I heard narrated a work of nonfiction.⟧ |
| `NONFICTION-AUDIOBOOK-3` | ⟦An audio recording of a nonfiction book was what I listened to.⟧ |
| `NONFICTION-AUDIOBOOK-4` | ⟦I listened to a nonfiction book read aloud in audiobook form.⟧ |

### The author watched a feature-length film · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `FEATURE-FILM-1` | ⟦I watched a feature-length film.⟧ |
| `FEATURE-FILM-2` | ⟦A full-length movie was what I viewed.⟧ |
| `FEATURE-FILM-3` | ⟦The film I watched was feature length.⟧ |
| `FEATURE-FILM-4` | ⟦I viewed a movie of feature length.⟧ |

### The author watched a live sports broadcast · 4 vectors

| ID | Complete note and exact mask |
|---|---|
| `LIVE-SPORTS-1` | ⟦I watched a live sports broadcast.⟧ |
| `LIVE-SPORTS-2` | ⟦A sporting event unfolded live in the broadcast I viewed.⟧ |
| `LIVE-SPORTS-3` | ⟦I viewed a sporting event through a live broadcast.⟧ |
| `LIVE-SPORTS-4` | ⟦The program I viewed was live coverage of a sporting event.⟧ |

## Reviewing the returned segments

Freeze and preserve the candidate's complete output before restoring fixture
identities. Give every vector a neutral temporary label, freeze one shuffled
segment-review order, and review every returned segment containing at least two
vectors.

For each segment, show every complete mask and ask:

> What is the narrowest recognizable subject for which every instance is a
> valid refinement?

Record the proposed subject and whether every mask genuinely fits it. If no
precise recognizable subject covers every member, record a suspected false
merge and the specific masks responsible. Do not rescue it with a vague
umbrella or a list of unrelated subjects.

The segment-by-segment review is not enough. Before revealing fixture
identities, also record the complete output shape:

- number and size distribution of all returned segments, including
  one-vector segments;
- number of vectors assigned zero, one, and multiple times;
- duplicate member sets;
- containment relationships among returned segments;
- every vector's complete memberships.

Then reveal the atomic propositions and fixture neighborhoods. Record:

- where the four formulations of every atomic proposition appeared;
- same-cohort pairs that do and do not share a segment;
- cross-cohort pairs that share a segment;
- cohorts represented only by singletons or unassigned vectors;
- candidate behavior beside the lexical-only diagnostic and raw-vector cosine
  matrix.

Finally, make one explicit human judgment of the complete result: useful, too
coarse, too fragmented, dominated by redundant overlap, or another stated
description. Support that judgment with the complete counts above rather than
only selected examples.

A split cohort, broad grouping, overlap, singleton, or unassigned vector is not
automatically a failure. This experiment has no score, preferred resolution,
or pass/fail verdict.

## Run

1. Approve and freeze all forty atomic propositions, all 160 equivalent masks,
   the four fixture neighborhoods, and the lexical-only diagnostic.
2. Freeze one candidate, configuration, seed, fine-output selector, shuffled
   opaque input order, and shuffled segment-review order.
3. Run and preserve the lexical-only diagnostic.
4. Encode all 160 inputs once under the shared contract in README.md.
5. Run the frozen candidate once without retuning.
6. Preserve the complete output before restoring fixture identities.
7. Complete and freeze the blind segment and output-shape reviews.
8. Reveal the atomic propositions, neighborhoods, lexical diagnostic, and raw
   cosine matrix; then complete the diagnostic record and overall human
   judgment.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, blind review judgments,
lexical-only result, annotation-based diagnostics, and all generated artifact
hashes.

## Scope

This is an exploratory observation of the complete frozen
SSE-plus-segmentation system. It does not validate, rank, or pass the candidate.
Any undesirable behavior may originate in the SSE geometry, the candidate, or
their interaction; neither the lexical diagnostic nor cosine values identify
the internal cause.

The fixture contains direct synthetic English statements in four semantic
neighborhoods. It does not cover automatic atomic-subject generation,
cross-cutting subjects, corpus scale, hierarchy construction, or natural note
noise. Experiments 3–6 separately examine lexical traps, unmasked context,
unequal density, and irrelevant-change stability.

If the result influences a candidate or configuration, later validation
requires a new frozen fixture.
