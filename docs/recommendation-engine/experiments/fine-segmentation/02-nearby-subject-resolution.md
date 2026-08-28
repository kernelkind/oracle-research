# Experiment 2: nearby fine-subject resolution

Status: **draft; every subject identity, sibling boundary, and mask requires
human approval before encoding**.

## Assumption

> Nearby but meaningfully distinct fine subjects are resolved.

## Fixture

The fixture contains 48 vectors: six sibling pairs with four independently
worded instances per fine subject. Each pair tests a different boundary:

| Pair | Boundary |
|---|---|
| Coffee | Different operations on the same material |
| Photo backup | Different storage destinations |
| Cooking lesson | Reversed teacher and learner roles |
| Greenhouse miner | Different resource relationships among shared entities |
| File cryptography | Opposite transformation directions |
| Bird photography | Different purposes for the same activity |

Each complete note is also its complete mask. Density is balanced. The
candidate receives only opaque IDs and vectors, not the pair names, subject
names, or expected groups.

### Coffee: different operations

#### `ROAST`: roasting coffee beans

| ID | Complete note and exact mask |
|---|---|
| `ROAST-1` | ⟦I heated green coffee beans until they were roasted.⟧ |
| `ROAST-2` | ⟦Applying heat transformed my raw coffee beans into roasted beans.⟧ |
| `ROAST-3` | ⟦I used heat to roast a batch of unroasted coffee beans.⟧ |
| `ROAST-4` | ⟦My green coffee beans became roasted coffee through heating.⟧ |

#### `GRIND`: grinding coffee beans

| ID | Complete note and exact mask |
|---|---|
| `GRIND-1` | ⟦I mechanically ground whole coffee beans into small particles.⟧ |
| `GRIND-2` | ⟦Milling reduced my whole coffee beans to coffee grounds.⟧ |
| `GRIND-3` | ⟦I used a grinder to turn whole coffee beans into grounds.⟧ |
| `GRIND-4` | ⟦Mechanical crushing broke the whole coffee beans into coffee grounds.⟧ |

### Photo backup: different destinations

#### `LOCAL-BACKUP`: backing up photos to local storage

| ID | Complete note and exact mask |
|---|---|
| `LOCAL-BACKUP-1` | ⟦I created a backup of my photo library on an external drive attached to my computer.⟧ |
| `LOCAL-BACKUP-2` | ⟦A locally connected disk now stores a recovery copy of my photo collection.⟧ |
| `LOCAL-BACKUP-3` | ⟦I duplicated my photo library onto a local storage drive for recovery.⟧ |
| `LOCAL-BACKUP-4` | ⟦An external drive at home holds an offline backup of all my photos.⟧ |

#### `CLOUD-BACKUP`: backing up photos to cloud storage

| ID | Complete note and exact mask |
|---|---|
| `CLOUD-BACKUP-1` | ⟦I created a backup of my photo library in remote cloud storage.⟧ |
| `CLOUD-BACKUP-2` | ⟦An online storage service now holds a recovery copy of my photo collection.⟧ |
| `CLOUD-BACKUP-3` | ⟦I uploaded a recovery copy of my photo library to remote internet storage.⟧ |
| `CLOUD-BACKUP-4` | ⟦An off-site cloud account holds an online backup of all my photos.⟧ |

### Cooking lesson: reversed participant roles

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

### Greenhouse miner: different resource relationships

#### `MINER-HEAT`: using Bitcoin-miner waste heat to warm a greenhouse

| ID | Complete note and exact mask |
|---|---|
| `MINER-HEAT-1` | ⟦Waste heat from a running Bitcoin miner warmed the greenhouse.⟧ |
| `MINER-HEAT-2` | ⟦The greenhouse was heated by excess thermal output from Bitcoin mining hardware.⟧ |
| `MINER-HEAT-3` | ⟦Thermal energy released during Bitcoin mining maintained the greenhouse temperature.⟧ |
| `MINER-HEAT-4` | ⟦Discarded heat from the Bitcoin miner supplied warmth to the greenhouse.⟧ |

#### `SOLAR-MINER`: using greenhouse solar infrastructure to power a Bitcoin miner

| ID | Complete note and exact mask |
|---|---|
| `SOLAR-MINER-1` | ⟦Solar panels installed for the greenhouse supplied surplus electricity to a Bitcoin miner.⟧ |
| `SOLAR-MINER-2` | ⟦A Bitcoin miner ran on excess power from the solar installation serving the greenhouse.⟧ |
| `SOLAR-MINER-3` | ⟦Unused output from solar panels serving the greenhouse supplied electricity to Bitcoin mining hardware.⟧ |
| `SOLAR-MINER-4` | ⟦Extra power from the greenhouse's solar array operated a Bitcoin miner.⟧ |

### File cryptography: opposite transformations

#### `ENCRYPT`: encrypting a file

| ID | Complete note and exact mask |
|---|---|
| `ENCRYPT-1` | ⟦I encrypted a plaintext file into ciphertext.⟧ |
| `ENCRYPT-2` | ⟦A cryptographic key transformed the readable file into encrypted data.⟧ |
| `ENCRYPT-3` | ⟦I used encryption to make the document's contents unreadable.⟧ |
| `ENCRYPT-4` | ⟦The file was converted from plaintext to ciphertext with encryption.⟧ |

#### `DECRYPT`: decrypting a file

| ID | Complete note and exact mask |
|---|---|
| `DECRYPT-1` | ⟦I decrypted a ciphertext file into plaintext.⟧ |
| `DECRYPT-2` | ⟦A cryptographic key transformed the encrypted file into readable data.⟧ |
| `DECRYPT-3` | ⟦I used decryption to recover the document's readable contents.⟧ |
| `DECRYPT-4` | ⟦The file was converted from ciphertext to plaintext with decryption.⟧ |

### Bird photography: different purposes

#### `BIRD-SURVEY`: photographing birds for scientific research

| ID | Complete note and exact mask |
|---|---|
| `BIRD-SURVEY-1` | ⟦I photographed birds to document species for a scientific survey.⟧ |
| `BIRD-SURVEY-2` | ⟦Bird pictures were taken as observations for an ecological field study.⟧ |
| `BIRD-SURVEY-3` | ⟦I recorded birds with a camera to contribute data to a wildlife census.⟧ |
| `BIRD-SURVEY-4` | ⟦The purpose of my bird photography was collecting scientific evidence for wildlife research.⟧ |

#### `BIRD-ART`: photographing birds to create art

| ID | Complete note and exact mask |
|---|---|
| `BIRD-ART-1` | ⟦I photographed birds to create artistic images.⟧ |
| `BIRD-ART-2` | ⟦Bird pictures were taken for their visual composition and beauty.⟧ |
| `BIRD-ART-3` | ⟦I used bird photography as a form of artistic expression.⟧ |
| `BIRD-ART-4` | ⟦The purpose of my bird photography was producing aesthetic photographs.⟧ |

## Pass rule

The candidate's predeclared fine-segment output must contain one segment equal
to each of the 12 four-vector subject sets above.

The six sibling boundaries are also frozen before encoding. A boundary is
crossed when one returned fine segment contains at least one vector from each
subject in that pair. The experiment requires zero crossings across all 96
forbidden sibling-vector pairs.

Additional segments contained within one expected subject are allowed.
Cross-family segments are recorded but do not affect this assumption's
verdict. A universal or indiscriminate segment still fails because it crosses
all six sibling boundaries.

## Run

1. Approve and freeze every note, mask, subject identity, and sibling boundary.
2. Encode all 48 inputs once under the shared contract in README.md.
3. Freeze the candidate, configuration, seed, fine-output selector, and one
   shuffled opaque-ID order.
4. Run the candidate and preserve its complete output before restoring the
   fixture identities.
5. Score all 12 expected groups and six sibling boundaries.

Record the frozen inputs and hashes, raw vectors, input order, candidate
configuration, complete returned memberships, missing expected groups, and
every crossed boundary. Preserve the raw-vector cosine matrix for diagnosis;
it does not determine the verdict.

## Scope

A pass supports only these 12 human-approved fine subjects and six sibling
boundaries. It does not define a universal boundary for every possible subject
pair. Experiments 3–6 separately test lexical traps, unmasked context, unequal
density, and irrelevant changes.
