# LaZer Anonymous Credential Implementation Optimization

**Research artifact for:** *Optimizing LaZer Anonymous Credentials for Repeated Presentation and Selective Disclosure*.

This repository contains the **second-paper implementation artifact** for optimizing a fixed BLNS23/LaZer anonymous-credential path. It does **not** implement or evaluate bounded-response offset repair from a different study.

## Scope

- Reuse static statement preparation and associated SHAKE128 prefix / CRT representations across suitable presentation and verification calls.
- Simplify proof-path computation, with guarded fixed-width arithmetic and the **original MPFR rejection decisions** retained in the main configurations.
- Remove redundant disclosed-attribute witness coordinates together with their related constraints in the compact implementation.
- Compare the corrected baseline, padded optimization, and compact optimization for repeated presentation and session reconstruction, in default and strict verification modes.

**What the paper measured:** 7,200 formal benchmark sessions in three randomly interleaved batches (600 samples per variant–lifecycle–verification-mode combination). Local presentation time means **local proof generation + local verification**; it excludes issuance, initialization, and network transfer. This is not a complete networked anonymous-authentication product, a new credential protocol, or a whole-protocol security proof.

## Repository map

| Path | Purpose |
| --- | --- |
| `project/` | BLNS/LaZer C/Python source, variant switches, patches, build and test scripts, dependency source archives. Source derived from the pinned upstream snapshot. |
| `results/full/raw/` | Immutable per-task JSONL observations and receipts from the measured full batch. |
| `results/full/{specs,verification,security,derived}/` | Batch specifications, original native regression receipts, security-model evidence and derived data. |
| `results/full/artifacts/<variant>/` | Archived source/parameter snapshots for the original measured variants; compiled libraries are deliberately omitted. |
| `figures/{en,zh}/{svg,pdf,png}/` | All seven existing paper figures per language in the three formats; no fonts are bundled. |
| `tables/` and `publication/final_tables.json` | Convenient tables and the manuscript's frozen table transcriptions. |
| `reproduce_final.py` | **Primary entry point**: verify existing full-batch evidence, recompute tables, redraw all seven figures. |
| `check_regressions.py` | 11 archived-source and parameter negative/consistency regressions (Python only). |
| `original_audit_scripts/` | Exact original scripts matched by the run's embedded SHA-256 source fingerprints. |
| `paper_reference/` | Original table-recomputation mappings and source provenance, retained for verification. |
| `MANIFEST_SHA256.txt` | SHA-256 of all shipped repository files except this manifest. |

Older internal run IDs (e.g. B1, G3, C3, E4) are retained *inside code and records* because they are part of the experiment's genuine provenance, not multiple competing release versions.

## Rebuild figures and statistical tables (without native compilation)

Ubuntu 22.04 / Python 3.10+ recommended. On Ubuntu, install a CJK font via your operating system for Chinese figures (for example `sudo apt install fonts-noto-cjk`); this repository redistributes **no font binaries**. A system CJK font is only needed if generating the Chinese figure set.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-plots.txt
python verify_repository.py
python reproduce_final.py --output reproduced
```

Expected final marker: `FINAL_PAPER_REPRODUCTION_COMPLETE`, `numeric cells 256`, `status PASSED`. This rebuild **does not rerun native proofs or any benchmark**. It compares the saved full run to the manuscript's published table entries. The package was tested after cleanup with 42 generated figure files, 327 underlying displayed-cell checks and 256 final-manuscript numerical comparisons passing; one pre-existing rounding note remains disclosed by the verification output.

Archive evidence and parametric source tests:

```bash
python check_regressions.py --output regression_checks.json
python project/verify_baseline.py
```

## Native build and new measurements

The complete upstream source and experiment variants remain in `project/`. The cleaned repository deliberately omits native `.so`, `.a`, `.o` libraries and build caches: **you must compile before executing fresh proofs**. Build behavior depends on installed GMP/MPFR, C/C++ compiler, CMake and Python/CFFI versions. The recorded machine used Intel i5-13400F, AVX2 and no AVX-512. Native builds on a new machine have not been re-executed during this packaging operation.

```bash
cd project
bash 01_build.sh
bash 02_run_smoke.sh
bash 03_run_pilot.sh 30
# only after smoke and pilot succeed, consider full runs
cd ..
python run_e4.py --help
```

**Do not** present any newly collected measurements as though they were the original paper's batch. Do not edit recorded raw JSONL files. A new batch should get its own path and an explicit new measurement record. The `original_audit_scripts/` files are **provenance**, not the recommended active experiment entry points.

## Evidence and scientific boundaries

- Some historical results in related-work/legacy tables are transcribed and **cannot be recomputed from the included full batch**; see the generated table-provenance CSV. In particular, historical E3 raw full archives are not present.
- Figures 1–2 are conceptual schematics; Figures 3–7 come from recorded data. Error ranges in Figures 6–7 are observed min–max ranges, not confidence intervals.
- The compaction argument establishes application-relation witness correspondence under stated constraints, **not a complete protocol security reduction**. Recorded generic MSIS/MLWE attack-cost models are not whole-protocol security certifications.
- The tested source snapshots and negative/regression checks are finite; they do not establish constant-time behavior or complete concurrent-cache correctness.
- Fixed-seed and archived verification checks must not be confused with newly executed cryptographic testing.

## Provenance and rights

The upstream LaZer library license is preserved in `project/lazer/LICENSE`; bundled third-party material retains its own notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No blanket new license is asserted for all new author-authored experiment scripts. **Before making a public GitHub release, the owners should choose an explicit license for their contributions** and verify third-party subcomponents' notices.

See [README_zh.md](README_zh.md) for a Chinese guide and [CLEANUP_REPORT.md](CLEANUP_REPORT.md) for cleaning decisions and validation.
