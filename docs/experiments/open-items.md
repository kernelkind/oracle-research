# Before publication

This is the inventory as of 2026-10-19. The file list is ready to review;
archives have not been assembled, uploaded or approved for release.

## Input versions

All nine official subject corpus hashes match located files. The 151 input
bindings to relocated storage were also checked against their recorded hashes.

There are **26 source bindings whose current contents differ from the recorded
hash**. [Exact alternatives](dependency-alternatives.csv) identify a matching
saved or recovered copy for **23** of them. The remaining **three versions of
one hierarchy state file** were not located in the recovery check below.
Keep the current and historical versions distinguishable; do not change frozen
plans to conceal a mismatch. These counts describe bindings, not necessarily
distinct files.

Some absent filenames are expected:

- **65 maintained-spec references** use `unused-source.json`. The hierarchy
  generator replaces that placeholder with a saved `source.json` before
  preparing each step; these are not missing corpora.
- **Four older comparison specs** point to an intermediate that was never
  created because the producer step was held before comparison. Those defaults
  cannot be run directly. The saved state and the reference-specific explanation
  are recorded in [reference resolutions](reference-resolutions.csv).

### Historical input recovery

The first recovery check on 2026-10-19 recovered nine additional input versions,
totaling 1,424,669 bytes. Each complete recovered file matches the SHA-256
recorded by its original experiment:

- **Eight review logs:** the required version is an exact prefix of the current
  log, ending at a complete JSON line. Later reviews had been appended. The
  alternatives list records the source, full-source hash and exact prefix length.
  Both the complete current logs and the recovered earlier versions are retained.
- **One qualification configuration:** `qualification-20261007` preserved its
  case definitions in its plan. Replacing only the one-line Q06 and Q08 case
  objects in Git blob `91b0a023d8dd9969f91a1394906bed97336b19f7` with those
  saved definitions recovers the exact file. The alternatives list records the
  plan location and hash, serialization and resulting hash. This is a verified
  recovery, not a separately discovered backup.

These nine files are saved under the publication checkout's ignored
`target/publication-inputs/` directory and included in [part-1251.csv](files/part-1251.csv)
for delivery under `datasets/`. Their contents are not committed to Git.
Original files, plans and receipts were not modified.

Three earlier versions of
`oracle-mvp-shr-pair-correctness-v1:target/hierarchy-nine-note-children-v3/state.json`
remain unlocated. They affect these eight saved experiments beneath
`target/hierarchy-iteration-v1/` in that source root:

| Expected SHA-256 | Affected experiment directories |
| --- | --- |
| `8170a1ada66e1a95d7a22a3ba5171f96bc36647bf3c998b722b49359034200a1` | `ingredient-heat-guards-v32-baseline`, `ingredient-heat-guards-v34-draw1` |
| `3c684cdbedb8f8aeec8894267ca009e0ae4fba8fc20dcf7cc3f678dce5a90c0b` | `ingredient-heat-v32-baseline`, `ingredient-heat-v34-draw1`, `ingredient-heat-v34-draw2` |
| `0e7eaab5e9f7154ace1478c6998f2164fde65e58c3e63b946ec398456a9541c6` | `preparation-storage-v32-baseline`, `preparation-storage-v35-draw1`, `preparation-storage-v35-draw2` |

All eight retain prepared cases and saved responses. Their missing state
versions prevent complete source verification and regeneration of those cases
from the original state. Preserve the available evidence with this limitation;
the current state file is not a substitute. The affected entries are marked in
[experiments](experiments.csv) and [issues](issues.csv).

The search checked 658 indexed state/configuration files, 167 additional direct
copies under known source roots, indexed historical hashes, the configuration's
Git path history and 18,285 Git blobs within bounded size ranges. It included
inventoried files on relocated storage. [Inventory metadata](inventory.json)
records the search bounds. This establishes that these versions were not found
in those locations, not that no copy exists anywhere.

### Remaining input hash checks

The subsequent check completed all **9,556 previously unchecked input bindings**:
9,551 match their current files, including all 15 large inputs. Five require
older versions of these files under `research-main:sse_multivector/experiment_specs/`:

| File | Exact historical version |
| --- | --- |
| `hr02-m06-muse-titles-v1.json` | Two versions: one in Git; the other recovered by changing only `max_output_tokens` from 6500 to the saved plan's 8192 in that Git version. |
| `luna-complete-note-masks-v1.json` | Found in Git history. |
| `lg01-bcpv4-six-pairs-astra-low-v1.json` | Found in Git history. |
| `asv6.100-hr01-post-template.txt` | Recovered by UTF-8 encoding the exact `plan.prompt.text` saved in the `asv6.100-context-draft/V1` experiment. |

All five match their original recorded hashes. The three Git blobs and their
commits are present in the publication clone. The two recovered files are saved
under ignored `target/publication-inputs/` and listed in
[part-1252.csv](files/part-1252.csv). [Exact alternatives](dependency-alternatives.csv)
records each source, hash and recovery procedure. No additional unresolved
versions were found; the three state versions above remain unlocated.

All **62 recorded encoder bindings** also match: two checkpoint copies and two
configuration/tokenizer directory copies shared by the hierarchy runs. Directory
hashes use the production worker's `canonical_tree_sha256` function. Measured
hashes are recorded in [runtime inputs](runtime-inputs.csv) and the file lists.

Files were hashed in 1 MiB chunks, with size and modification checks to detect
concurrent edits. No concurrent changes were detected. This completes checking
the recorded input hashes already indexed. The large-plan follow-up below also
checks their newly indexed inputs. Verification of all saved responses remains
unfinished.

### Large experiment plans

All **42 plans** that exceeded the initial 32 MiB read limit are now indexed as
native experiments. Their entries contain prompt versions, provider/model
settings, case counts, saved plan and manifest identities, code-provenance
references and located result files. Complete frozen settings remain in each
original plan.

Their **34,091 source references** resolve to **6,092 input files**, all matching
the recorded hashes. Of these, 6,067 had measured hashes and unchanged file
metadata; the remaining 25 were hashed in 1 MiB chunks. This adds 25 dependency
rows and one previously unlisted file: a saved **DSLv2** relationship prompt in
[part-1253.csv](files/part-1253.csv). No new source mismatches or missing inputs
were found.

**33 plans have located result files.** The other nine have no result file at
their recorded or adjacent locations. They remain evidence of preparation;
absence of that file alone does not establish a failed run or lost results.
Their individual entries are included in [issues](issues.csv).

The streaming JSON pass read 8,200,509,108 bytes with a peak parser memory use
of about 24 MiB. Raw plan-file hashes were also measured. This checked metadata
and source bindings; it did not perform inference, assess answers or verify all
response receipts. Saved case counts do not represent independent trials.
Original plans and results were not modified.

## Saved results and verification

- **3,182 native plans** have no `results.jsonl` at the recorded location or
  beside their saved plan. Some may be prepared jobs that never ran. Establish
  their status from the saved records before calling them failed experiments or
  missing results. They remain indexed as evidence of preparation.
- Indexed input and encoder hashes have been checked as described above. The
  three unlocated state versions remain a source-verification limitation.
- Adapter configurations identify pinned base-model revisions. Adapter weights,
  other unmeasured evidence and the eventual archives still need checksums.
  Having a saved file is not a completed reproduction test.

[Detailed issues](issues.csv) retain the individual findings. Duplicate native
jobs, warmups and reused answers must not be counted as independent trials.

## Preserve the source history

Of 41 recorded generation commits, 40 are present in the publication clones.
HR34's Oracle construction commit,
`bf7801bc1d92491b20eab8d075fb8d57b83d6b3e`, exists in the original repository
but is absent from the publication clone. Preserve that history before release.
[Code versions](code-versions.csv) records the check and affected run.

The inventory also identifies **294 artifact blobs present in Git history but
absent from the current Git index**, with measured SHA-256 hashes and their
original commit associations.
Preserve these files before removing historical data from Git. No history has
been rewritten by this inventory work.

## Assemble and test the release

Review the actual selected contents for credentials and personal information
before packaging. Known credential containers were excluded from discovery;
that is not a completed privacy review of the evidence.

The [publication proposal](downloads.md) records the agreed GitHub/Hugging Face
hosting division and inclusion of all 17 evaluated adapters, with measured sizes.
The remaining evidence selection is open, including the large clustering files.
The existing bundle tables still describe the broad inventory;
they do not select every listed file for publication.

Finish source and original-producer selection from frozen plans and receipts,
retaining required exceptions to proposed omissions, then verify the staged
packages. Known shared-download requirements are incomplete, and the
consolidated dependency index retains only example consumers. Check unused
candidate posts embedded in larger frozen inputs before selecting whole files.
The nine official subject corpora have passed this used-ID check; other frozen
inputs require their own selection review.

The size audit measured **534.71 GiB** of candidate source files before
compression. That is neither the approved publication size nor a fully
deduplicated total. Verify the final contents and checksums before adding exact
Hugging Face versions and download links. Readers should be able to obtain
the experiments they need without downloading all research artifacts.

The [reproduction guide](reproduce.md) now provides concrete commands and records
their validation limits. Before calling the release reproducible end to end:

- Test the downloaded archives in a clean environment, including a complete
  hierarchy run with public authentication.
- Prepare the verification metadata below and include it in each evidence
  package. One local HR39 archive has passed after extraction elsewhere using
  `verify` without extra options; the full collection has not been verified.
- Provide a maintained, tested command for the L1 analysis from saved judgments;
  the saved scores and original verification exist, but that CLI does not.
- Validate portable training and adapter-inference instructions with the exact
  datasets, base-model revisions and runtime versions.

Finish history cleanup last and repeat publication checks against the final
release contents, updating any affected checksums and commit references.

## Prepare verification metadata

This is a publisher step. Readers extract the package and run `verify`; they
do not supply paths from the research machine.

Stage the selected native experiments and their required files under one
extraction root. Include each plan, prepared configuration, run manifest,
results and any runner/worker upgrade ledgers, all bound source versions, and
the producer receipts needed by reused answers. Resolve historical input
versions using the inventory before staging. Use copies of the frozen bytes.
The file list remains the basis for selecting archive contents; this command
does not select files, copy evidence or build an archive.

An original path can require different historical contents in different plans.
The current location file maps each original path to one destination, so a
single shared mapping cannot verify conflicting versions. Resolve that packaging
limitation before preparing a shared package for those experiments.

Use the private original-to-staged locations from file selection and copying.
For the HR39 example, with the setup variables from the reproduction guide and
that private file saved outside the staging root:

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
python sse_multivector/experiment.py prepare-release "$RELEASE_ROOT" \
  --locations target/reproduction/private-locations.json \
  --experiment evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1/HR39-resumed-1/batch-00025/experiment
```

Repeat `--experiment` for all selected native experiments sharing that extraction
root. Preparation verifies them and writes `experiment-locations.json` only
after they pass. The generated file contains relative destinations for only the
locations those checks use, including original producers of reused responses.
Shared sources are hashed once per invocation. No model calls are made.
The private location format is documented in the runner's publisher instructions.

Preparation rejects dependencies outside the staging root and does not overwrite
an existing locations file. Missing files, changed source bytes and invalid
receipts must be resolved before packaging. A successful integrity check may
still include failed or unrun cases; preserve their recorded status.

Include the generated file at the extraction root and add it to the final
archive file list and checksums. Keep the private staging locations outside the
archive. When splitting a collection into several archives, preserve the common
extraction layout and supply the same complete metadata with the pieces. Do not
overwrite it with independently generated partial mappings. Check the required
downloads together after extraction elsewhere, with original storage unavailable,
using the reader command without `--locations`.
