# Resolution File Manager — project handover

Updated: 21 October 2026 (Europe/London). Read this first at the start of every Work session. Update it after substantial development, a confirmed bug, or a release. Record actual results and remaining work; never infer success from an interrupted session.

## Current versions and verification

- **Windows source/review build: 12.7.8.** Pixel-measured conversion selectors plus scrollable Info metadata/pinned actions for short browsers. Build and exact embedded-source/43-locale verification passed. Versioned Desktop EXE SHA-256: `5b2c1270038627adb0d1c0525e82269359d2bd02a0611172cafc11c2af2c2718`. Older 12.7.5/12.7.6/12.7.7 binaries retained.
- **Linux binary: 12.6.1 x86_64**, present in `dist/linux`. Earlier records report successful Ubuntu build/smoke checks; 12.7.x changes have not been built or verified on Linux. Mint, laptop hardware, drivers, audio, desktop drag/drop and Trash remain unverified.
- Latest local **Store package: 12.6.2.0**. Submission 8 is recorded as a draft with the package saved/Validated, not submitted. Current live/certification status was not checked in this inspection; consult Partner Center before acting. A historical Submission 7 certification screenshot is not evidence of today's status.
- Fresh verification after the Serbian test correction on 21 October: **all 86 tests pass** (`python -m unittest discover -q`). Inspector and embedded-resource checks also have saved reports. No application rebuild was needed.

## Completed functionality

- Dual-pane recursive media browsing, Details/thumbnails, metadata sorting/filtering/search, persistent layouts/workspaces and independent tick selections.
- Image/video previews and comparison, frame export/contact sheets, metadata inspector, ratings/tags/labels, smart collections and cache/performance controls.
- Duplicate and similar-image review, integrity checks, inventory export, folder comparison/synchronisation previews and organisation rules.
- Queued copy/move with conflict policies, pause/cancel/retry, safe deletion, batch rename and Undo; preview-first video conversion retaining originals.
- Recent 12.7.x work: transfer/selection improvements; asynchronous resumable Undo coordinating background readers; translated Copy/Move/Cancel drop prompt; populated Info metadata localised in 12.7.5.

## Outstanding work and known problems

- Serbian packaging-test mismatch resolved on 21 October: expectation now uses `sr-cyrl-rs`, matching the existing Cyrillic manifest and translation. All 86 tests pass. Live Store state remains unverified.
- German conversion conflict selector clipping fixed in 12.7.6, along with longer preset/resolution/engine choices. Final real-Tk conversion geometry and upgrade-control checks pass all 43 languages; 86 unit tests pass. Native new-binary German/Arabic main, Info and conversion views inspected. Broader native visual/scaling review remains incomplete; see `docs/LAYOUT_REVIEW_CHECKPOINT.md` for exact hashes and capture/release gates.
- 12.7.5 Store screenshots: 12 native captures, four each for English/Arabic/German, preserved. The new Info/conversion UI invalidates their use as the final latest-build set: capture 43 updated sets under the new version, without overwriting old originals. Initial 12.7.6 capture has one selected Arabic Info image; a dual-preview image exposed clipped Info fields/actions and is excluded with originals retained. No complete latest-build screenshot set exists yet. Capture tooling requires inspected inputs and is not unattended.
- Initial screenshot work found Info actions/metadata disappear when previews reduce browser height. 12.7.8 fixes this with a priority-reserved action row and read-only scrollable metadata. Fresh 86-test suite and mouse/selection/Info regression pass; final short-browser regression passes all 43 languages. Final native Arabic main/Info/scrolling/preview/conversion review passed; remaining native locale/view/scaling review is incomplete. Screenshot baseline is ready, release gate remains false. One final-version Arabic Info capture is validated; 171 views remain. Screenshot continuation requeued for 11:45 London time today.
- README and PROJECT_CONTEXT version summaries were reconciled to 12.7.5 during the GitHub update.
- Linux validation/release and Windows/Store release preparation for the current source remain outstanding. Older Store notes/keywords require reconciliation before reuse.
- Unsaved editor buffers were not observable. Preserve local generated materials and older releases; do not reset, clean or overwrite this tree.

## Languages

43 locale files exist: `ar, bg, bn, ca, cs, da, de, el, en, es, et, fa, fi, fil, fr, he, hi, hr, hu, id, it, ja, ko, lt, lv, ms, nl, no, pl, pt-BR, pt-PT, ro, ru, sk, sr, sv, th, tr, uk, ur, vi, zh-CN, zh-TW`.

Saved checks report full interface/new-control translations and Help in all 43 languages (22 chapters, 134 paragraphs), with six additive inspector keys in 12.7.5. Existing Help/UI entries were preserved. Translation completeness is not professional human review of every language.

Serbian text is Cyrillic. `AppxManifest.template.xml`, listing-preparation mapping and `test_packaging_assets.py` now consistently use `sr-cyrl-rs`. The stale Latin test expectation was corrected; translation and manifest needed no changes. No Store upload/submission was performed.

## GitHub and source synchronisation

- Repository: https://github.com/johnperky/ResolutionFileManager ; development branch: `main`.
- GitHub update authorised on 21 October: publish the eight previously local commits through `105bd9c` (12.4.0), plus a source/handover checkpoint for 12.7.5 on `main`. Verify `git rev-parse HEAD` against `git ls-remote origin refs/heads/main` after publication; those commands identify the exact final commit without a self-referential hash in this document.
- The checkpoint includes maintained source, 43 locale packs, Help, tests, builders and handover instructions. Generated packages/caches, local prepared Store materials and unreviewed evidence images remain local and are not part of source synchronisation. This is a source update, not a binary release or Store submission.
- Earlier documentation-only branch `codex/project-status-handover` is historical; the current handover is now included directly in the main source checkpoint.

## Important locations and evidence

- Authoritative project: `F:/Resolution File Manager project/ResolutionFileManager-Project-v6`. Desktop project folder is a junction to it, not an independent backup.
- Builds: `build_windows.ps1`, `build_windows_release.ps1`, `build_windows_english_review.ps1`, `build_windows_multilingual_review.ps1`, `build_linux.sh`; runtime helper `run_linux.sh`.
- Current review binary: `dist/multilingual-review-12.7.5/ResolutionFileManager-v12.7.5-Multilingual-Review.exe`, with a versioned Desktop copy. Do not assume root-level or generic dist EXEs are current.
- Current review binary: `dist/multilingual-review-12.7.8/ResolutionFileManager-v12.7.8-Multilingual-Review.exe`, plus versioned Desktop copy. The preceding 12.7.5 and 12.7.6 paths are retained for rollback only.
- Releases: `release-output/12.6.1`; Linux handoff: `F:/ResolutionFileManager-Linux-Handoff-12.6.1`.
- Backups: `F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-inspector-localization/source` and `2026-10-21-12.7.5-inspector-verified/source`, with ZIPs. Hash comparison of 449 shared files found only a later screenshot-helper version-title correction; snapshot-only SOURCE_MANIFEST.json is expected. This handover and its AGENTS instructions postdate that snapshot.
- Pre-GitHub-sync backup: `F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-github-sync/source` plus ZIP; 451 files verified before documentation/ignore updates.
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

Scheduling and publication authorisation (21 October 2026, Europe/London): layout review at 10:40, followed by screenshots at 11:10 only when the exact source/binary has passed layout review. A conditional hourly follow-up at half past the hour checks release readiness quietly. User authorises publishing the newest Windows build to GitHub **after** review is complete, with validated screenshots, tests, matching release assets and checksums; do not publish the current review build prematurely. No Store or Linux publication is authorised. Record actual completion and release URL here; pause the publication follow-up after success.

1. Read this file and current Git status; preserve the complete dirty/untracked source with a new verified snapshot before development.
2. German selector clipping and Serbian test correction are complete. Preserve these fixes; verify each remaining native language/view during screenshot capture and record any new issues.
3. Finish visual language/RTL review and remaining screenshot sets without repeating completed captures.
4. Keep GitHub source and this handover current after subsequent fixes; preserve older releases and local-only Store preparation materials.
5. When authorised, build/validate current Windows and Linux releases and create versioned exports/backups.
6. When authorised, inspect the current Store draft, prepare matching release materials, resume verified small-batch imports, and record the resulting actual submission status.

Maintenance: keep this document concise and free of credentials, account email addresses, local settings and private data. Distinguish direct checks from historical logs and unknown live state on every update.
