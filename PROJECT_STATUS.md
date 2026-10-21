# Resolution File Manager — project handover

Updated: 21 October 2026 (Europe/London). Read this first at the start of every Work session. Update it after substantial development, a confirmed bug, or a release. Record actual results and remaining work; never infer success from an interrupted session.

## Screenshot workflow update

- **Complete: 172 final 12.7.8 PNG candidates / 43 languages × four views**, integrity checked and visually reviewed through gallery/control/preview sheets plus targeted full-size checks. Exact scope and hashes: `docs/STORE_SCREENSHOT_REVIEW_12.7.8.md`; local gallery/progress: `Store Preparation 12.7.8/Batch Candidates v2`. No new visible app layout defect identified in these four views.
- Default future method: retain/adapt `Capture Store Screenshots.cmd` and `tools/batch_store_screenshots.py`; review with `tools/review_batch_candidates.py`. Focus/notification handling and paused frame/time staging were repaired; six tool tests pass. Rejected/replaced originals are preserved. The old manual capture automation was deleted.
- These are matching-source native UI captures, separately identified from packaged-process captures. Six modules/43 locales match the exact EXE; binary checks include the saved Arabic four-view set and a fresh English packaged-process capture. Broader native release QA and matching release/package assets remain outstanding: `readyForRelease: false`, `readyForStoreImport: false`. No application code/build, Store submission or binary release changed.

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
- Screenshot capture/review is complete for the four latest-version Store views in all 43 languages; see the current workflow summary above. Older 12.7.5/12.7.6 screenshots and excluded diagnostics remain preserved. Wider native release QA remains incomplete.
- 12.7.8 Info metadata/action clipping fix passed all 43 short-browser regressions. Four-view image review is complete; resizing/dialog/theme/scaling coverage outside those views remains outstanding. Preserve existing app fixes and the exact reviewed binary.
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
- Earlier versioned review binaries remain available for rollback; use the exact 12.7.8 path below for current work.
- Current review binary: `dist/multilingual-review-12.7.8/ResolutionFileManager-v12.7.8-Multilingual-Review.exe`, plus versioned Desktop copy. The preceding 12.7.5 and 12.7.6 paths are retained for rollback only.
- Releases: `release-output/12.6.1`; Linux handoff: `F:/ResolutionFileManager-Linux-Handoff-12.6.1`.
- Backups: `F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-inspector-localization/source` and `2026-10-21-12.7.5-inspector-verified/source`, with ZIPs. Hash comparison of 449 shared files found only a later screenshot-helper version-title correction; snapshot-only SOURCE_MANIFEST.json is expected. This handover and its AGENTS instructions postdate that snapshot.
- Pre-GitHub-sync backup: `F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-github-sync/source` plus ZIP; 451 files verified before documentation/ignore updates.
- Help master: `docs/help/en.json`; manual: `docs/help/ENGLISH_MANUAL.md`; locales: `locales/`.
- Evidence: `docs/STORE_SCREENSHOTS_12.7.5_CHECKPOINT.md`, `docs/TEST_INSPECTOR_12.7.5_FINAL.txt`, `docs/EMBEDDED_REVIEW_12.7.5.json`, `docs/MULTILINGUAL_12.7.3_CHECKPOINT.md`, `docs/RECOVERY_EXPORT_VERIFICATION.json`, `DEVELOPMENT_WORKFLOW.md`.

## Microsoft Store handover

- Product ID: `9NZL6GF5JSJK`; package identity: `JohnPerky1.ResolutionFileManager`; Windows Desktop x64/full-trust, 43 manifest languages. Configuration lives in `packaging/microsoft-store/`; package builder is `Build-StorePackage.ps1`. Publisher configuration already exists; do not invent or replace it.
- `output/ResolutionFileManager-12.6.2.0-x64.msix` exists. Staged manifest is 12.6.2.0. This package predates current 12.7.8 source and must not be presented as containing it.
- `SUBMISSION-8-CHECKPOINT.md` records saved Arabic/Italian/Vietnamese listings and a prepared 45-column locale export incorporating 26 new-language entries; the bulk import was **not confirmed saved**. Ukrainian individual-save status was uncertain, although the later export contained two image URLs. Reinspect actual draft rather than repeat work blindly.
- Current screenshot preparation: `F:/Resolution File Manager project/Store Preparation 12.7.8/Batch Candidates v2` (172 reviewed source-native candidates); `Screenshots E Drive` retains four packaged-process Arabic captures. Older preparation folders remain preserved.
- Always use the microsoft-store-submission skill. Preserve current export, translations and asset URLs. Default imports: disjoint folders of 10–11 Store listings, maximum 11; validate actual PNG content/references together, import sequentially and verify each save. Older all-language import folder is a baseline, not the default future upload unit.
- Before any authorised submission: reconcile package/version/text/screenshots, verify all intended listings Complete, package Validated and actual price/options. Publication requires current user authorisation. No Store changes were made for this handover.

## Prioritised next steps

Publication authorisation (21 October 2026): the manual screenshot/layout one-offs are finished/obsolete and deleted. The conditional hourly publication follow-up checks readiness quietly. User authorises the newest Windows GitHub release only after full review and release gates pass; four-view screenshot completion alone is insufficient. No Store or Linux publication is authorised.

1. Read this file and current Git status; preserve the complete dirty/untracked source with a new verified snapshot before development.
2. Preserve the completed German selector and Serbian Cyrillic/test fixes. Do not repeat the completed 172-image capture/review.
3. Complete broader native release QA (resizing/dialogs/themes/scaling beyond the four Store views), then prepare matching release assets and final release checks.
4. Keep GitHub source and this handover current after subsequent fixes; preserve older releases and local-only Store preparation materials.
5. When authorised, build/validate current Windows and Linux releases and create versioned exports/backups.
6. When authorised, inspect the current Store draft, prepare matching release materials, resume verified small-batch imports, and record the resulting actual submission status.

Maintenance: keep this document concise and free of credentials, account email addresses, local settings and private data. Distinguish direct checks from historical logs and unknown live state on every update.
