# Experiment 2: fine-subject resolution spectrum

Status: **draft; every subject identity, rung, and mask requires human approval
before encoding**.

## Assumption

> Nearby but meaningfully distinct fine subjects are resolved.

We do not yet know how fine the segmentation must be. Each ladder therefore
defines four concrete semantic rungs:

- **Rung 0:** all four cohorts remain under one broad subject;
- **Rung 1:** the most conservative boundary is resolved;
- **Rung 2:** an intermediate boundary is also resolved;
- **Rung 3:** the closest pair is resolved.

This sweeps semantic distinctions in the fixture. It does not tune or sweep an
algorithm-specific setting. One candidate and configuration remain frozen.

## Fixture

The fixture contains 64 vectors: four ladders, four subject cohorts per ladder,
and four independently worded instances per cohort. Every concept is ordinary
and stated directly in the note; no rung depends on obscure facts or
compositional role ordering.

| Ladder | Rung 0 | Rung 1 | Rung 2 | Rung 3 |
|---|---|---|---|---|
| Coffee | Coffee preparation | Preparing beans / brewing | Roasting / grinding / brewing | Light roast / dark roast / grinding / brewing |
| Photos | Working with photos | Replicating / cropping | Backup / synchronization / cropping | Local backup / cloud backup / synchronization / cropping |
| Produce | Eating produce | Fruit / carrots | Apples / oranges / carrots | Red apples / green apples / oranges / carrots |
| Media | Consuming published media | Reading publications / listening to podcasts | Books / magazines / podcasts | Fiction books / nonfiction books / magazines / podcasts |

Each complete note is also its complete mask. Density is balanced. The
candidate receives only opaque IDs and vectors, not the ladder or rung
information.

### Coffee

#### `LIGHT-ROAST`: roasting coffee beans to a light roast

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I roasted green coffee beans to a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦Heating transformed the raw coffee beans into a light roast.⟧ |
| `LIGHT-ROAST-3` | ⟦I stopped roasting the coffee beans at the light-roast stage.⟧ |
| `LIGHT-ROAST-4` | ⟦The coffee beans were roasted until they reached a light roast.⟧ |

#### `DARK-ROAST`: roasting coffee beans to a dark roast

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦I roasted green coffee beans to a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦Heating transformed the raw coffee beans into a dark roast.⟧ |
| `DARK-ROAST-3` | ⟦I continued roasting the coffee beans to the dark-roast stage.⟧ |
| `DARK-ROAST-4` | ⟦The coffee beans were roasted until they reached a dark roast.⟧ |

#### `GRIND`: grinding coffee beans

| ID | Complete note and exact mask |
|---|---|
| `GRIND-1` | ⟦I ground whole coffee beans into coffee grounds.⟧ |
| `GRIND-2` | ⟦Milling reduced whole coffee beans to small particles.⟧ |
| `GRIND-3` | ⟦I used a grinder to turn whole coffee beans into grounds.⟧ |
| `GRIND-4` | ⟦Mechanical crushing broke whole coffee beans down into coffee grounds.⟧ |

#### `BREW`: brewing coffee

| ID | Complete note and exact mask |
|---|---|
| `BREW-1` | ⟦I brewed coffee from grounds and hot water.⟧ |
| `BREW-2` | ⟦Hot water extracted a coffee drink from coffee grounds.⟧ |
| `BREW-3` | ⟦I prepared coffee by passing hot water through grounds.⟧ |
| `BREW-4` | ⟦Coffee grounds and hot water were used to brew coffee.⟧ |

### Photos

#### `LOCAL-BACKUP`: backing up photos to local storage

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I created a recovery backup of my photo library on a local external drive.⟧ |
| `LOCAL-BACKUP-2` | ⟦A drive connected to my computer holds a backup copy of my photos.⟧ |
| `LOCAL-BACKUP-3` | ⟦I copied my photo library to a locally attached disk for recovery.⟧ |
| `LOCAL-BACKUP-4` | ⟦A local USB storage device stores my photo backup.⟧ |

#### `CLOUD-BACKUP`: backing up photos to cloud storage

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦I created a recovery backup of my photo library in remote cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦A cloud storage service holds a backup copy of my photos.⟧ |
| `CLOUD-BACKUP-3` | ⟦I copied my photo library to remote online storage for recovery.⟧ |
| `CLOUD-BACKUP-4` | ⟦An off-site cloud service stores my photo backup.⟧ |

#### `PHOTO-SYNC`: synchronizing photos between devices

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-SYNC-1` | ⟦I synchronized photo-library changes between my phone and laptop.⟧ |
| `PHOTO-SYNC-2` | ⟦A photo-library change on either device is propagated to the other.⟧ |
| `PHOTO-SYNC-3` | ⟦My phone and tablet exchange photo updates to stay synchronized.⟧ |
| `PHOTO-SYNC-4` | ⟦Photo-library updates are synchronized across my personal devices.⟧ |

#### `CROP-PHOTO`: cropping photos

| ID | Complete note and exact mask |
|---|---|
| `CROP-PHOTO-1` | ⟦I cropped a photo to remove its outer edges.⟧ |
| `CROP-PHOTO-2` | ⟦I trimmed the borders from a photograph.⟧ |
| `CROP-PHOTO-3` | ⟦Cropping removed the unwanted edges of the picture.⟧ |
| `CROP-PHOTO-4` | ⟦I reframed an image by cutting away its outside area.⟧ |

### Produce

#### `RED-APPLE`: eating red apples

| ID | Complete note and exact mask |
|---|---|
| `RED-APPLE-1` | ⟦I ate a red apple.⟧ |
| `RED-APPLE-2` | ⟦I was eating an apple with red skin.⟧ |
| `RED-APPLE-3` | ⟦My snack was a red apple.⟧ |
| `RED-APPLE-4` | ⟦A red apple was what I ate.⟧ |

#### `GREEN-APPLE`: eating green apples

| ID | Complete note and exact mask |
|---|---|
| `GREEN-APPLE-1` | ⟦I ate a green apple.⟧ |
| `GREEN-APPLE-2` | ⟦I was eating an apple with green skin.⟧ |
| `GREEN-APPLE-3` | ⟦My snack was a green apple.⟧ |
| `GREEN-APPLE-4` | ⟦A green apple was what I ate.⟧ |

#### `ORANGE`: eating oranges

| ID | Complete note and exact mask |
|---|---|
| `ORANGE-1` | ⟦I ate an orange.⟧ |
| `ORANGE-2` | ⟦I was eating a fresh orange fruit.⟧ |
| `ORANGE-3` | ⟦My snack was an orange.⟧ |
| `ORANGE-4` | ⟦An orange was what I ate.⟧ |

#### `CARROT`: eating carrots

| ID | Complete note and exact mask |
|---|---|
| `CARROT-1` | ⟦I ate a carrot.⟧ |
| `CARROT-2` | ⟦I was eating a fresh carrot.⟧ |
| `CARROT-3` | ⟦My snack was a carrot.⟧ |
| `CARROT-4` | ⟦A carrot was what I ate.⟧ |

### Media

#### `FICTION-BOOK`: reading fiction books

| ID | Complete note and exact mask |
|---|---|
| `FICTION-BOOK-1` | ⟦I read a fiction book.⟧ |
| `FICTION-BOOK-2` | ⟦I spent time reading a novel.⟧ |
| `FICTION-BOOK-3` | ⟦My reading was a fictional book.⟧ |
| `FICTION-BOOK-4` | ⟦I read a book that told an invented story.⟧ |

#### `NONFICTION-BOOK`: reading nonfiction books

| ID | Complete note and exact mask |
|---|---|
| `NONFICTION-BOOK-1` | ⟦I read a nonfiction book.⟧ |
| `NONFICTION-BOOK-2` | ⟦I spent time reading a factual book.⟧ |
| `NONFICTION-BOOK-3` | ⟦My reading was a work of nonfiction.⟧ |
| `NONFICTION-BOOK-4` | ⟦I read a book about real events and facts.⟧ |

#### `MAGAZINE`: reading magazines

| ID | Complete note and exact mask |
|---|---|
| `MAGAZINE-1` | ⟦I read a magazine.⟧ |
| `MAGAZINE-2` | ⟦I spent time reading an issue of a magazine.⟧ |
| `MAGAZINE-3` | ⟦My reading was a printed magazine.⟧ |
| `MAGAZINE-4` | ⟦I read articles in a magazine.⟧ |

#### `PODCAST`: listening to podcasts

| ID | Complete note and exact mask |
|---|---|
| `PODCAST-1` | ⟦I listened to a podcast.⟧ |
| `PODCAST-2` | ⟦I spent time listening to a podcast episode.⟧ |
| `PODCAST-3` | ⟦My media choice was an audio podcast.⟧ |
| `PODCAST-4` | ⟦I played and listened to a podcast program.⟧ |

## Scoring one ladder

For scoring only, call the four cohorts `A`, `B`, `C`, and `D`:

| Ladder | `A` | `B` | `C` | `D` |
|---|---|---|---|---|
| Coffee | Light roast | Dark roast | Grinding | Brewing |
| Photos | Local backup | Cloud backup | Synchronization | Cropping |
| Produce | Red apples | Green apples | Oranges | Carrots |
| Media | Fiction books | Nonfiction books | Magazines | Podcasts |

The canonical grouping at each rung is:

```text
Rung 0: {A ∪ B ∪ C ∪ D}
Rung 1: {A ∪ B ∪ C}, {D}
Rung 2: {A ∪ B}, {C}, {D}
Rung 3: {A}, {B}, {C}, {D}
```

A returned segment **crosses** a boundary when it contains vectors from two
groups that the rung keeps separate.

A result reaches **Rung 1** when:

1. one returned fine segment equals exactly `D`;
2. the remaining cohorts appear as one of these complete refinements:
   - one segment equal to `A ∪ B ∪ C`;
   - segments equal to `A ∪ B` and `C`;
   - segments equal to `A`, `B`, and `C`;
3. no returned fine segment crosses the `(A ∪ B ∪ C) / D` boundary.

A result reaches **Rung 2** when:

1. one returned fine segment equals exactly `C`;
2. one returned fine segment equals exactly `D`;
3. either one segment equals exactly `A ∪ B`, or separate segments equal
   exactly `A` and exactly `B`;
4. no returned fine segment crosses the `(A ∪ B) / C / D` boundaries.

A result reaches **Rung 3** when:

1. separate returned fine segments equal exactly `A`, `B`, `C`, and `D`;
2. no returned fine segment crosses any of the four subject boundaries.

Additional segments contained inside one cohort are allowed. Segments mixing
different ladders are recorded separately and do not affect this experiment
unless they also cross a scored boundary inside one ladder. The verdict does
not require every vector globally to have only one membership.

## Overall result

The proposed conservative MVP requirement is Rung 1 on all four ladders. This
requirement still needs human approval before the experiment is frozen.

Report the highest verified rung for every ladder. A result that does not reach
Rung 1 is reported as **below Rung 1**; the experiment must not infer that its
output cleanly matches Rung 0. Rungs 2 and 3 measure additional resolving power
and are not MVP requirements.

## Run

1. Approve and freeze every note, mask, cohort identity, and ladder ordering.
2. Freeze one candidate, configuration, seed, fine-output selector, and opaque
   shuffled input order before encoding or exposing vector diagnostics.
3. Encode all 64 inputs once under the shared contract in README.md.
4. Run once and preserve the complete output before restoring fixture IDs.
5. Score each ladder independently.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, and highest verified rung per
ladder. Preserve raw-vector cosine values for diagnosis only.

## Scope

The rung labels refer only to the human-approved boundaries in these four
ladders. They are not universal semantic-distance thresholds. Experiments 3–6
separately test lexical traps, unmasked context, unequal density, and irrelevant
changes.
