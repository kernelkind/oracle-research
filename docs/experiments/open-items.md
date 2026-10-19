# Before publication

This is the inventory as of 2026-10-19. The file list is ready to review;
archives have not been assembled, uploaded or approved for release.

## Input versions

All nine official subject corpus hashes match located files. The 151 input
bindings to relocated storage were also checked against their recorded hashes.

There are **21 source bindings whose current contents differ from the recorded
hash**. [Exact alternatives](dependency-alternatives.csv) identify a matching
saved copy for nine of them. The other twelve still need the original bytes
located or their limitation documented. Keep the current and historical
versions distinguishable; do not change frozen plans to conceal a mismatch.
These counts describe bindings, not necessarily distinct files.

Some absent filenames are expected:

- **65 maintained-spec references** use `unused-source.json`. The hierarchy
  generator replaces that placeholder with a saved `source.json` before
  preparing each step; these are not missing corpora.
- **Four older comparison specs** point to an intermediate that was never
  created because the producer step was held before comparison. Those defaults
  cannot be run directly. The saved state and the reference-specific explanation
  are recorded in [reference resolutions](reference-resolutions.csv).

## Saved results and verification

- **3,173 native plans** have no `results.jsonl` at the recorded location or
  beside their saved plan. Some may be prepared jobs that never ran. Establish
  their status from the saved records before calling them failed experiments or
  missing results. They remain indexed as evidence of preparation.
- **42 large plans** are listed as files and as entries with metadata pending.
  They exceeded the inventory's 32 MiB JSON read limit. Their detailed settings
  and dependencies still need inspection with a bounded-memory reader.
- **15 large input bindings** have located files whose hashes were not checked.
  Another **9,541 code, prompt or configuration bindings** retain recorded hashes
  without a new hash check. See [dependencies](dependencies.csv). Encoder asset
  checks are recorded separately in [runtime inputs](runtime-inputs.csv).
- Adapter configurations identify pinned base-model revisions. Weight files,
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

Choose archive groups from the explicit file list, verify their contents and
checksums, then add download links. The listed archive members total about
534 GiB before compression; this includes intermediate evidence and files not
yet checked for identical contents. It is not a download-size estimate. Readers
should be able to obtain the collections they need without downloading all
research artifacts.

Next, turn the recorded inputs, source versions and settings into tested
instructions for inspecting saved evidence and rerunning experiments. Record
relocation instructions separately from frozen inputs. Finish history cleanup
and repeat the publication checks against the final release contents.
