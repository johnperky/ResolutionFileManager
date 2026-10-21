# Resolution File Manager — project handover

Updated: 21 October 2026 (Europe/London). Read this first at the start of every Work session. Update it after substantial development, a confirmed bug, or a release. Record actual results and remaining work; never infer success from an interrupted session.

## Current versions and verification

- **Windows source/review build: 12.7.5.** `VERSION.txt`, release notes and build records agree. Versioned Desktop EXE exists; its SHA-256 matches the saved verification record: `3a06b1acde063400d51897908ac1a71fe00e45e75971ba5ef7295e568f590cf1`.
- **Linux binary: 12.6.1 x86_64**, present in `dist/linux`. Earlier records report successful Ubuntu build/smoke checks; 12.7.x changes have not been built or verified on Linux. Mint, laptop hardware, drivers, audio, desktop drag/drop and Trash remain unverified.
- Latest local **Store package: 12.6.2.0**. Submission 8 is recorded as a draft with the package saved/Validated, not submitted. Current live/certification status was not checked in this inspection; consult Partner Center before acting. A historical Submission 7 certification screenshot is not evidence of today's status.
- Existing 12.7.5 log: 86 tests run, one known Serbian expectation failure. Inspector regression and embedded-resource checks passed according to saved reports. No tests or builds were rerun for this handover.

## Completed functionality

- Dual-pane recursive media browsing, Details/thumbnails, metadata sorting/filtering/search, persistent layouts/workspaces and independent tick selections.
- Image/video previews and comparison, frame export/contact sheets, metadata inspector, ratings/tags/labels, smart collections and cache/performance controls.
- Duplicate and similar-image review, integrity checks, inventory export, folder comparison/synchronisation previews and organisation rules.
- Queued copy/move with conflict policies, pause/cancel/retry, safe deletion, batch rename and Undo; preview-first video conversion retaining originals.
- Recent 12.7.x work: transfer/selection improvements; asynchronous resumable Undo coordinating background readers; translated Copy/Move/Cancel drop prompt; populated Info metadata localised in 12.7.5.

## Outstanding work and known problems

- Correct the stale Serbian packaging-test expectation, then rerun appropriate checks. The manifest should remain Cyrillic to match the actual pack.
- German conversion conflict selector clips its default text. Broader visual layout/RTL/typography review remains incomplete; automated language checks do not establish visual quality everywhere.
- 12.7.5 Store screenshots: 12 native captures, four each for English, Arabic and German. **40 other language sets remain incomplete.** Capture tooling still needs inspected layout adjustments; it is not unattended.
- README says 12.6.2 and PROJECT_CONTEXT says 12.7.4; those summaries need reconciliation. Prefer VERSION.txt plus versioned verification records for current state.
- Linux validation/release and Windows/Store release preparation for the current source remain outstanding. Older Store notes/keywords require reconciliation before reuse.
- Unsaved editor buffers were not observable. Saved development is substantially uncommitted; do not reset, clean or overwrite this tree.

## Languages

43 locale files exist: `ar, bg, bn, ca, cs, da, de, el, en, es, et, fa, fi, fil, fr, he, hi, hr, hu, id, it, ja, ko, lt, lv, ms, nl, no, pl, pt-BR, pt-PT, ro, ru, sk, sr, sv, th, tr, uk, ur, vi, zh-CN, zh-TW`.

Saved checks report full interface/new-control translations and Help in all 43 languages (22 chapters, 134 paragraphs), with six additive inspector keys in 12.7.5. Existing Help/UI entries were preserved. Translation completeness is not professional human review of every language.

Serbian text is Cyrillic. `AppxManifest.template.xml` correctly declares `sr-cyrl-rs`; `test_packaging_assets.py` still expects `sr-latn-rs`. This is a test mismatch, not evidence that the Serbian application translation is missing.

## GitHub and source synchronisation

- Repository: https://github.com/johnperky/ResolutionFileManager ; development branch: `main`.
- Verified remote main before this documentation publication: `835ab63bab795cffde8f8db0804267796cfed397`, source version 12.3.0.
- Local development HEAD: `105bd9c87ecf42014e84471b1ab6f3c4b024f21b`, `release: prepare Resolution File Manager 12.4.0`; eight commits ahead of remote main.
- Source is **not fully synchronised**: inspection found 29 modified tracked files and 208 untracked entries before handover files were added. Later 12.7.5 work is saved locally, not captured by that HEAD.
- This handover is maintained on documentation-only branch `codex/project-status-handover`, based on remote main. That branch does not contain the current application source. Recheck branch tips before future integration; review and selectively commit development without publishing caches, binaries or private data.

## Important locations and evidence

- Authoritative project: `F:/Resolution File Manager project/ResolutionFileManager-Project-v6`. Desktop project folder is a junction to it, not an independent backup.
- Builds: `build_windows.ps1`, `build_windows_release.ps1`, `build_windows_english_review.ps1`, `build_windows_multilingual_review.ps1`, `build_linux.sh`; runtime helper `run_linux.sh`.
- Current review binary: `dist/multilingual-review-12.7.5/ResolutionFileManager-v12.7.5-Multilingual-Review.exe`, with a versioned Desktop copy. Do not assume root-level or generic dist EXEs are current.
- Releases: `release-output/12.6.1`; Linux handoff: `F:/ResolutionFileManager-Linux-Handoff-12.6.1`.
- Backups: `F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-inspector-localization/source` and `2026-10-21-12.7.5-inspector-verified/source`, with ZIPs. Hash comparison of 449 shared files found only a later screenshot-helper version-title correction; snapshot-only SOURCE_MANIFEST.json is expected. This handover and its AGENTS instructions postdate that snapshot.
- Help master: `docs/help/en.json`; manual: `docs/help/ENGLISH_MANUAL.md`; locales: `locales/`.
- Evidence: `docs/STORE_SCREENSHOTS_12.7.5_CHECKPOINT.md`, `docs/TEST_INSPECTOR_12.7.5_FINAL.txt`, `docs/EMBEDDED_REVIEW_12.7.5.json`, `docs/MULTILINGUAL_12.7.3_CHECKPOINT.md`, `docs/RECOVERY_EXPORT_VERIFICATION.json`, `DEVELOPMENT_WORKFLOW.md`.

## Microsoft Store handover

- Product ID: `9NZL6GF5JSJK`; package identity: `JohnPerky1.ResolutionFileManager`; Windows Desktop x64/full-trust, 43 manifest languages. Configuration lives in `packaging/microsoft-store/`; package builder is `Build-StorePackage.ps1`. Publisher configuration already exists; do not invent or replace it.
- `output/ResolutionFileManager-12.6.2.0-x64.msix` exists. Staged manifest is 12.6.2.0. This package predates current 12.7.5 source and must not be presented as containing it.
- `SUBMISSION-8-CHECKPOINT.md` records saved Arabic/Italian/Vietnamese listings and a prepared 45-column locale export incorporating 26 new-language entries; the bulk import was **not confirmed saved**. Ukrainian individual-save status was uncertain, although the later export contained two image URLs. Reinspect actual draft rather than repeat work blindly.
- Preparation folders: `F:/Resolution File Manager project/Store Preparation 12.6.2`, `Store Preparation 12.7.4`, `Store Preparation 12.7.5`. Latest captures and progress/validation/index are under `Store Preparation 12.7.5/Screenshots E Drive`.
- Always use the microsoft-store-submission skill. Preserve current export, translations and asset URLs. Default imports: disjoint folders of 10–11 Store listings, maximum 11; validate actual PNG content/references together, import sequentially and verify each save. Older all-language import folder is a baseline, not the default future upload unit.
- Before any authorised submission: reconcile package/version/text/screenshots, verify all intended listings Complete, package Validated and actual price/options. Publication requires current user authorisation. No Store changes were made for this handover.

## Prioritised next steps

1. Read this file and current Git status; preserve the complete dirty/untracked source with a new verified snapshot before development.
2. Fix Serbian test expectation and German selector clipping; verify relevant regressions and record actual results here.
3. Reconcile stale version summaries, finish visual language/RTL review and remaining screenshot sets without repeating completed captures.
4. Review and commit intended source changes, integrate the handover branch, and synchronise GitHub deliberately; preserve older releases.
5. When authorised, build/validate current Windows and Linux releases and create versioned exports/backups.
6. When authorised, inspect the current Store draft, prepare matching release materials, resume verified small-batch imports, and record the resulting actual submission status.

Maintenance: keep this document concise and free of credentials, account email addresses, local settings and private data. Distinguish direct checks from historical logs and unknown live state on every update.
