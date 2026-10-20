# Public repository cleanup and validation

## Basis and policy

Input: the user-provided final LaZer normal-proof-path code archive dated 2026-10-19. The original archive is **not** edited. This cleaned copy is meant to be a repository of one paper, not a chronological archive of development deliveries. Algorithms, recorded experiment observations, parameter headers and upstream source contents are not rewritten. Changes to repository-facing reproduction code are limited to neutral naming, a filtered SHA manifest, publication-table dependency removal, and system-font discovery. Three runtime/specification JSON metadata files have only machine-local absolute paths redacted; the original measurement JSONL and associated receipts remain byte-identical.

## Retained

1. Actual LaZer native/Python sources, variant patches, build infrastructure, third-party source/dependency archives, pinned-upstream identity and license.
2. Complete `full` raw JSONL data, task receipts, batch plans/configuration, archived finite verification records and model assumptions.
3. Per-variant source and parameter snapshots used by numerical/model checks; source-byte hashes still match their original archive's fingerprints.
4. Full-batch summary, security audit and paper figure/table scripts. Original run-script bytes are retained separately for trustworthy source-fingerprint checks.
5. The 7 manuscript figures × 2 languages × PNG/PDF/SVG, final numeric table mappings and existing human-readable table outputs.

## Excluded

- Repeated pilot/smoke full archives and redundant `.tar.gz` files; historical E3 prototype and older paper deliveries.
- Native `.a`, `.so`, `.o`, Python CFFI extensions and variant build-cache copies; all must be locally regenerated for new cryptographic measurements.
- Environment-specific `.deps`, `.compat-bin`, logs, temporary/cached state, reference-user bundles and legacy version/audit-delivery snapshots.
- Outdated Word publication drafts and unrelated paper PDF files.
- Bundled fonts and all font binaries. Regeneration uses an installed operating-system CJK font.

## Provenance guardrail

Because compiled artifacts were omitted, each variant's `SHA256.json` is a **reduced manifest** containing only original source-file SHA-256 entries. Retained hashes were carried forward exactly from the original per-variant manifests; the original manifest's binary entries were omitted, not silently claimed to pass. The batch configuration still retains the original full-run source-script fingerprints. The system does **not** claim to have re-executed the original native trials.

## Validation after cleanup

- `python project/verify_baseline.py`: `SOURCE_INTEGRITY_OK` (341 pristine file hashes; 9 documented modified files).
- `python check_regressions.py`: 11 regression tests passed. This checks archived evidence/guard conditions; it does not reexecute 7,200 proof sessions.
- `python reproduce_final.py`: original full data yielded 7,200 formal benchmark samples, 13,972 records including warmups and extra runs, 42 figure exports, 327 original display-cell checks and 256 final-paper number checks (`PASSED`). One documented final-digit rounding note remains.
- A fresh native rebuild of all seven variants has **not** been performed as part of this repo-only cleanup. It should be smoke-tested on the target Ubuntu environment before representing it as fully native-reproducible.

## Posting to GitHub

1. Unzip repository and inspect the text/LICENSE notices.
2. Add the author-approved license for original contributions, set an actual repository URL when created.
3. Run `python verify_repository.py` and, if desired, the data-only reproduction commands above.
4. Publish only this cleaned root (not the original ZIP). Avoid `git add` on generated build/log outputs.
5. Use the GitHub URL in the manuscript only **after the repository is live, publicly accessible and tagged/frozen**.
