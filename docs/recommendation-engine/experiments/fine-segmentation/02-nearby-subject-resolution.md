# Experiment 2: fine-subject resolution spectrum

Status: **draft; every subject identity, boundary, and mask requires human
approval before encoding**.

## Assumption

> Nearby but meaningfully distinct fine subjects are resolved.

We do not yet know how fine the segmentation must be. This experiment therefore
measures resolution at two predeclared levels instead of requiring every
distinction:

- **Minimum:** separate a conservatively different subject from two very close
  subjects.
- **Fine:** also separate the two very close subjects from each other.

This is a semantic sweep over fixed inputs. It does not tune or sweep any
algorithm-specific setting. The candidate and its configuration remain frozen.

## Fixture

The fixture contains 48 vectors: four resolution ladders, three subject cohorts
per ladder, and four independently worded instances per cohort.

| Ladder | Close pair | Conservatively different subject |
|---|---|---|
| Coffee | Light roast / dark roast | Grinding coffee beans |
| Photos | Local backup / cloud backup | Synchronizing photos |
| Kitchen | Parent teaches child / child teaches parent | Washing dishes together |
| Files | AES encryption / ChaCha20 encryption | File compression |

Each complete note is also its complete mask. Density is balanced. The
candidate receives only opaque IDs and vectors, not the ladder, subject, or
boundary information.

### Coffee

#### `LIGHT-ROAST`: lightly roasting coffee beans

| ID | Complete note and exact mask |
|---|---|
| `LIGHT-ROAST-1` | ⟦I gave green coffee beans a light roast.⟧ |
| `LIGHT-ROAST-2` | ⟦I heated raw coffee beans only to a light-roast level.⟧ |
| `LIGHT-ROAST-3` | ⟦A batch of green coffee beans was roasted until lightly browned.⟧ |
| `LIGHT-ROAST-4` | ⟦I stopped roasting the coffee beans at the light stage.⟧ |

#### `DARK-ROAST`: darkly roasting coffee beans

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

### Kitchen

#### `PARENT-TEACHES`: a parent teaching a child to cook

| ID | Complete note and exact mask |
|---|---|
| `PARENT-TEACHES-1` | ⟦A parent taught their child how to prepare a meal.⟧ |
| `PARENT-TEACHES-2` | ⟦A child learned how to cook through instruction from their parent.⟧ |
| `PARENT-TEACHES-3` | ⟦Cooking instruction passed from a parent to their child.⟧ |
| `PARENT-TEACHES-4` | ⟦The parent gave the child a lesson in meal preparation.⟧ |

#### `CHILD-TEACHES`: a child teaching a parent to cook

| ID | Complete note and exact mask |
|---|---|
| `CHILD-TEACHES-1` | ⟦A child taught their parent how to prepare a meal.⟧ |
| `CHILD-TEACHES-2` | ⟦A parent learned how to cook through instruction from their child.⟧ |
| `CHILD-TEACHES-3` | ⟦Cooking instruction passed from a child to their parent.⟧ |
| `CHILD-TEACHES-4` | ⟦The child gave the parent a lesson in meal preparation.⟧ |

#### `WASH-DISHES`: a parent and child washing dishes together

| ID | Complete note and exact mask |
|---|---|
| `WASH-DISHES-1` | ⟦A parent and child washed the dishes together.⟧ |
| `WASH-DISHES-2` | ⟦A parent and child jointly cleaned the dirty dishes.⟧ |
| `WASH-DISHES-3` | ⟦Dishwashing was shared between a parent and child.⟧ |
| `WASH-DISHES-4` | ⟦The parent and child worked together to clean the dishes.⟧ |

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

Call the two close four-vector cohorts `A` and `B`, and the conservatively
different four-vector cohort `C`.

The ladder meets **minimum resolution** when:

1. one returned fine segment `R` satisfies `A ⊆ R ⊆ A ∪ B`;
2. one returned fine segment `R` satisfies `B ⊆ R ⊆ A ∪ B`;
3. one returned fine segment equals exactly `C`;
4. no returned fine segment contains both a `C` vector and an `A` or `B`
   vector.

`A` and `B` may share one segment at minimum resolution.

The ladder reaches **fine resolution** when it meets minimum resolution and:

1. one returned fine segment equals exactly `A`;
2. one returned fine segment equals exactly `B`;
3. no returned fine segment contains both an `A` vector and a `B` vector.

Additional segments contained inside one cohort are allowed. The verdict does
not require every vector globally to have only one membership.

## Overall result

The proposed conservative MVP requirement is minimum resolution on all four
ladders. This requirement still needs human approval before the experiment is
frozen. Failure on any ladder places the candidate below that proposed minimum.

Fine resolution is reported separately as `0/4` through `4/4` ladders. It is
not required to pass this experiment.

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
