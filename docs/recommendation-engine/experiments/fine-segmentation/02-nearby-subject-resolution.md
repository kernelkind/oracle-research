# Experiment 2: fine-subject resolution spectrum

Status: **draft; every subject identity, boundary, and mask requires human
approval before encoding**.

## Assumption

> Nearby but meaningfully distinct fine subjects are resolved.

We do not yet know how fine the segmentation must be. This experiment therefore
defines three concrete rungs for each semantic ladder:

- **Rung 0:** all three cohorts remain under one broad subject;
- **Rung 1:** a conservative boundary is resolved;
- **Rung 2:** a narrower boundary is also resolved.

This is a semantic sweep over fixed inputs. It does not tune or sweep any
algorithm-specific setting. The candidate and its configuration remain frozen.

## Fixture

The fixture contains 48 vectors: four resolution ladders, three subject cohorts
per ladder, and four independently worded instances per cohort. These are the
actual ladder rungs:

| Ladder | Rung 0 | Rung 1 | Rung 2 |
|---|---|---|---|
| Coffee | Coffee-bean processing | Roasting / grinding | Light roast / dark roast / grinding |
| Photos | Photo-library replication | Backup / synchronization | Local backup / cloud backup / synchronization |
| Raptors | Observing birds of prey | Eagles / hawks | Bald eagles / golden eagles / red-tailed hawks |
| Files | File-data transformation | Encryption / compression | AES encryption / ChaCha20 encryption / compression |

Each complete note is also its complete mask. Density is balanced. The
candidate receives only opaque IDs and vectors, not the ladder, subject, or
boundary information. No ladder depends on preserving actor/recipient order or
other compositional structure.

### Coffee

#### `LIGHT-ROAST`: lightly roasting coffee beans

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I gave green coffee beans a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦I heated raw coffee beans only to a light-roast level.⟧ |
| `LIGHT-ROAST-3` | ⟦A batch of green coffee beans was roasted until lightly browned.⟧ |
| `LIGHT-ROAST-4` | ⟦I stopped roasting the coffee beans at the light stage.⟧ |

#### `DARK-ROAST`: roasting coffee beans to a dark roast

| ID | Complete note and exact mask |
|---|---|
| `DARK-ROAST-1` | ⟦I gave green coffee beans a dark roast.⟧ |
| `DARK-ROAST-2` | ⟦I heated raw coffee beans until they reached a dark-roast level.⟧ |
| `DARK-ROAST-3` | ⟦A batch of green coffee beans was roasted until deeply browned.⟧ |
| `DARK-ROAST-4` | ⟦I continued roasting the coffee beans to the dark stage.⟧ |

#### `GRIND`: grinding coffee beans

| ID | Complete note and exact mask |
|---|---|
| `GRIND-1` | ⟦I mechanically ground whole coffee beans into small particles.⟧ |
| `GRIND-2` | ⟦Milling reduced my whole coffee beans to coffee grounds.⟧ |
| `GRIND-3` | ⟦I used a grinder to turn whole coffee beans into grounds.⟧ |
| `GRIND-4` | ⟦Mechanical crushing broke whole coffee beans into coffee grounds.⟧ |

### Photos

#### `LOCAL-BACKUP`: backing up photos to local storage

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I created a recovery backup of my photo library on an external drive connected to my computer.⟧ |
| `LOCAL-BACKUP-2` | ⟦A locally attached storage drive holds a backup copy of my photo collection.⟧ |
| `LOCAL-BACKUP-3` | ⟦I copied my photo library to a local external disk for recovery.⟧ |
| `LOCAL-BACKUP-4` | ⟦A USB storage device connected to my computer stores my photo backup.⟧ |

#### `CLOUD-BACKUP`: backing up photos to cloud storage

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦I created a recovery backup of my photo library in remote cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦A cloud storage service holds a backup copy of my photo collection.⟧ |
| `CLOUD-BACKUP-3` | ⟦I copied my photo library to remote online storage for recovery.⟧ |
| `CLOUD-BACKUP-4` | ⟦An off-site cloud service stores my photo backup.⟧ |

#### `PHOTO-SYNC`: synchronizing photos between devices

| ID | Complete note and exact mask |
|---|---|
| `PHOTO-SYNC-1` | ⟦I synchronized photo-library changes between my phone and laptop in both directions.⟧ |
| `PHOTO-SYNC-2` | ⟦Photo additions and edits on either of my devices now propagate to the other.⟧ |
| `PHOTO-SYNC-3` | ⟦My phone and tablet exchange photo-library updates so both stay synchronized.⟧ |
| `PHOTO-SYNC-4` | ⟦A photo-library change made on either device is copied to the other device.⟧ |

### Raptors

#### `BALD-EAGLE`: observing bald eagles

| ID | Complete note and exact mask |
|---|---|
| `BALD-EAGLE-1` | ⟦I observed a bald eagle.⟧ |
| `BALD-EAGLE-2` | ⟦I watched a bald eagle.⟧ |
| `BALD-EAGLE-3` | ⟦I spent time viewing a bald eagle.⟧ |
| `BALD-EAGLE-4` | ⟦My birdwatching focused on a bald eagle.⟧ |

#### `GOLDEN-EAGLE`: observing golden eagles

| ID | Complete note and exact mask |
|---|---|
| `GOLDEN-EAGLE-1` | ⟦I observed a golden eagle.⟧ |
| `GOLDEN-EAGLE-2` | ⟦I watched a golden eagle.⟧ |
| `GOLDEN-EAGLE-3` | ⟦I spent time viewing a golden eagle.⟧ |
| `GOLDEN-EAGLE-4` | ⟦My birdwatching focused on a golden eagle.⟧ |

#### `REDTAIL-HAWK`: observing red-tailed hawks

| ID | Complete note and exact mask |
|---|---|
| `REDTAIL-HAWK-1` | ⟦I observed a red-tailed hawk.⟧ |
| `REDTAIL-HAWK-2` | ⟦I watched a red-tailed hawk.⟧ |
| `REDTAIL-HAWK-3` | ⟦I spent time viewing a red-tailed hawk.⟧ |
| `REDTAIL-HAWK-4` | ⟦My birdwatching focused on a red-tailed hawk.⟧ |

### Files

#### `AES-ENCRYPT`: encrypting a file with AES

| ID | Complete note and exact mask |
|---|---|
| `AES-ENCRYPT-1` | ⟦I encrypted a file with AES.⟧ |
| `AES-ENCRYPT-2` | ⟦AES encryption converted a plaintext file into ciphertext.⟧ |
| `AES-ENCRYPT-3` | ⟦I applied AES to encrypt the readable contents of a file.⟧ |
| `AES-ENCRYPT-4` | ⟦The file became AES ciphertext through encryption.⟧ |

#### `CHACHA-ENCRYPT`: encrypting a file with ChaCha20

| ID | Complete note and exact mask |
|---|---|
| `CHACHA-ENCRYPT-1` | ⟦I encrypted a file with ChaCha20.⟧ |
| `CHACHA-ENCRYPT-2` | ⟦ChaCha20 encryption converted a plaintext file into ciphertext.⟧ |
| `CHACHA-ENCRYPT-3` | ⟦I applied ChaCha20 to encrypt the readable contents of a file.⟧ |
| `CHACHA-ENCRYPT-4` | ⟦The file became ChaCha20 ciphertext through encryption.⟧ |

#### `COMPRESS`: compressing a file

| ID | Complete note and exact mask |
|---|---|
| `COMPRESS-1` | ⟦I compressed a file to reduce its size.⟧ |
| `COMPRESS-2` | ⟦Data compression converted the file into a smaller representation.⟧ |
| `COMPRESS-3` | ⟦I applied compression so the file would occupy fewer bytes.⟧ |
| `COMPRESS-4` | ⟦The file's storage size was reduced through compression.⟧ |

## Scoring one ladder

For scoring only, call the two closest four-vector cohorts `A` and `B`, and the
other four-vector cohort `C`. Their meanings in each ladder are:

| Ladder | `A` | `B` | `C` |
|---|---|---|---|
| Coffee | Light roast | Dark roast | Grinding |
| Photos | Local backup | Cloud backup | Synchronization |
| Raptors | Bald eagles | Golden eagles | Red-tailed hawks |
| Files | AES encryption | ChaCha20 encryption | Compression |

The canonical grouping at each rung is:

```text
Rung 0: {A ∪ B ∪ C}
Rung 1: {A ∪ B}, {C}
Rung 2: {A}, {B}, {C}
```

A result reaches **Rung 1** when:

1. one returned fine segment equals exactly `C`;
2. either one segment equals exactly `A ∪ B`, or separate segments equal
   exactly `A` and exactly `B`;
3. no returned fine segment crosses the `(A ∪ B) / C` boundary.

A result reaches **Rung 2** when:

1. one returned fine segment equals exactly `A`;
2. one returned fine segment equals exactly `B`;
3. one returned fine segment equals exactly `C`;
4. no returned fine segment crosses any of the three subject boundaries.

Additional segments contained inside one cohort are allowed. Segments mixing
different ladders are recorded separately and do not affect this experiment
unless they also cross a scored boundary inside one ladder. The verdict does
not require every vector globally to have only one membership.

## Overall result

The proposed conservative MVP requirement is Rung 1 on all four ladders. This
requirement still needs human approval before the experiment is frozen.

Report the highest verified rung for every ladder. A result that does not reach
Rung 1 is reported as **below Rung 1**; the experiment must not infer that its
output cleanly matches Rung 0. Rung 2 is additional resolving power, not an MVP
requirement.

## Run

1. Approve and freeze every note, mask, cohort identity, and ladder ordering.
2. Freeze one candidate, configuration, seed, fine-output selector, and opaque
   shuffled input order before encoding or exposing vector diagnostics.
3. Encode all 48 inputs once under the shared contract in README.md.
4. Run once and preserve the complete output before restoring fixture IDs.
5. Score each ladder independently.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, and both resolution verdicts per
ladder. Preserve raw-vector cosine values for diagnosis only.

## Scope

The words “minimum” and “fine” refer only to the human-approved boundaries in
these four ladders. They are not universal semantic-distance thresholds.
Experiments 3–6 separately test lexical traps, unmasked context, unequal
density, and irrelevant changes.
