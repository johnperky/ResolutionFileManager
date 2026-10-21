# Resolution File Manager — project handover

Updated: 21 October 2026 (Europe/London). Read this and AGENTS.md before development; update after significant changes. Record verified outcomes, preserve unrelated work, and keep public documentation free of secrets.

## Current versions and release state

- **Windows: 12.7.10 — published as GitHub Latest**, with review and asset gates complete. Exact EXE: `dist/multilingual-review-12.7.10/ResolutionFileManager-v12.7.10-Multilingual-Review.exe`; SHA-256 `f1424ea2b42efb8586886d8721ea2864e40bb9df1cdafe8aef1ec7ae3ac6d22f`. Six modules and all 43 locales match source (`docs/EMBEDDED_REVIEW_12.7.10.json`). Older candidates/binaries preserved.
- Final 89 unit tests and Defender custom scan pass. Complete Help validation has zero errors/review warnings. Native packaged checks pass System 100%, Dark 200% and High contrast 150%, with isolated settings and system-only PATH. Actual populated binary views inspected. A separate clean OS/Windows 10 was not tested; no claim of exhaustive device/scale/language coverage.
- **Linux: 12.6.1 x86_64**, retained in `dist/linux`; current Windows changes have not been built/tested on Linux. Earlier Ubuntu checks do not establish Mint/laptop/driver/audio/drag/drop/Trash compatibility.
- **Latest local Microsoft Store package: 12.6.2.0.** Submission 8 previously recorded as draft/package Validated, not submitted. Current live certification status remains unverified; no Store action in this release task.
- **GitHub Windows release: [12.7.10](https://github.com/johnperky/ResolutionFileManager/releases/tag/v12.7.10)**, tag `v12.7.10`, released source commit `a6046d88a3c87524acba61b09e362a0665da49dd`. Portable ZIP, standalone EXE, full source ZIP and checksums uploaded; server SHA-256 values match, anonymous downloads return 200 with correct filenames/sizes, checksum download and public Latest page verified. `readyForRelease: true`; evidence: `docs/RELEASE_PUBLICATION_12.7.10.json`. Previous releases preserved. Publication monitor is paused; future releases require a new request.

## Completed functionality and latest fixes

- Dual-pane recursive media browsing, Details/thumbnails, sorting/filtering/search, folder trees, tick selections, selection basket, layouts/workspaces, metadata inspector, ratings/tags/labels and smart collections.
- Image/video previews and comparison, frame export/contact sheets, duplicates/similar-image review, integrity/inventory/folder comparison and organisation rules.
- Queued copy/move with conflict previews, pause/cancel/retry, safe deletion, rename/Undo and preview-first video conversion retaining originals; asynchronous resumable Undo coordinates background readers.
- **Tools > Show hidden files** persists, defaults off and applies to both pane scans, folder trees and inventory. Recognises dot names and Windows hidden attributes; normal media filters still apply. Native toggle pilot covers recursion, Details/Thumbnails, saved preference and unchanged window geometry. Label translated in all 43 languages; capture runners explicitly keep it off.
- Current layout fixes: measured conversion choices; scrollable Info metadata with reserved actions; scaled rows/headings and settled Japanese fallback fonts; readable dark/high-contrast dropdowns; scrollable enlarged conversion settings; preserved toolbar/scan Cancel actions; Appearance Cancel restores custom column widths.
- Representative review includes 160 theme/scale/resize states with explicitly recorded earlier source scope, plus a final 40-state English scan-footer regression. Fresh exact-binary checks supplement matching-source native review. See `docs/APPEARANCE_REVIEW_12.7.10.json` and `docs/PACKAGED_REVIEW_12.7.10.json`.

## Languages and Serbian

43 locale packs: `ar, bg, bn, ca, cs, da, de, el, en, es, et, fa, fi, fil, fr, he, hi, hr, hu, id, it, ja, ko, lt, lv, ms, nl, no, pl, pt-BR, pt-PT, ro, ru, sk, sr, sv, th, tr, uk, ur, vi, zh-CN, zh-TW`.

All have interface translations and 22 Help chapters/134 paragraphs. Existing content was retained; completeness and native layout checks are not professional proofreading. Serbian is Cyrillic: manifest, listing mapping and packaging test consistently use `sr-cyrl-rs`. Earlier mismatch fixed/pushed as `83d1ad0`; no repeat translation/manifest change needed. Live Store acceptance remains unverified.

## Screenshots and efficient automation

- Default retained launcher: `Capture Store Screenshots.cmd`, runner `tools/batch_store_screenshots.py`; resume per-language manifests with isolated settings, E: sample media and read-only SQLite cache backup. No file operation or conversion is performed to stage UI.
- **Final 12.7.10 capture/review is complete: 172 validated/reviewed PNGs in all 43 languages** under `F:/Resolution File Manager project/Store Preparation 12.7.10/Batch Candidates v3`. Source-native candidates are distinguished from packaged-process checks; version/hash provenance is mandatory.
- Preserve reviewed 12.7.8 172-image set and 12.7.10 pre-footer candidates in `Batch Candidates v2`; never relabel these as final. New final captures use the corrected source/binary.
- Reuse exact unchanged reviewed regions through decoded-pixel equality (`tools/compare_capture_regions.py`); validate PNGs, dimensions, hashes, references, duplicates and media content in batches (`review_batch_candidates.py`). Review combined galleries/new action strips rather than repeating remote clicks or every unchanged translation. See `docs/BATCH_SCREENSHOTS.md`.
- Pilot English/German/Arabic before all 43 languages; avoid concurrent native UI changes/capture batches. Reuse passing tests unless source changes or failures justify more. Do not trade correctness for lower usage.

## GitHub, packaging and important files

- Repository: https://github.com/johnperky/ResolutionFileManager ; branch `main`. Released source/tag: `a6046d88a3c87524acba61b09e362a0665da49dd` / `v12.7.10`; final publication handover is synchronised on `main`. Use `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` for the latest documentation commit without a self-referential hash here.
- Main folder: `F:/Resolution File Manager project/ResolutionFileManager-Project-v6`; Desktop project is a junction, not an independent backup. Versioned Desktop review EXEs are retained.
- Builds: `build_windows_multilingual_review.ps1`, `build_windows_release.ps1`, `build_linux.sh`, `run_linux.sh`. Release package: `release-output/12.7.10`; pre-footer package preserved separately. `-ReviewedExecutable` packages exact reviewed bytes without rebuilding and validates six modules/43 locales.
- Finalise committed source/docs with `tools/finalize_release_archives.py`, verify ZIPs/licences/media tools/checksums with `verify_windows_package.py`, then publish with `publish_reviewed_release.py`. The external ignored release readiness gate binds all four asset hashes, the source commit and public review evidence; it avoids a self-referential source ZIP hash inside its own archive. Do not regenerate the binary after review.
- Verified backups: project-parent `Recovery Backups/2026-10-21-before-release-gates/source` (+ZIP, 331 files) and `2026-10-21-before-toolbar-release-fix/source` (+ZIP, 345 files); earlier recovery/layout snapshots retained. Initial 12.7.10 candidate EXEs are preserved in their versioned dist subfolders.
- Help master/manual: `docs/help/en.json`, `docs/help/ENGLISH_MANUAL.md`; app translations: `locales/`; Store manifest: `packaging/microsoft-store/AppxManifest.template.xml` (x64/full-trust desktop configuration, existing assigned identity supplied during packaging).

## Prioritised next work

Windows GitHub release is complete; no remaining blocker in its recorded review scope.

1. A future Store update requires the `microsoft-store-submission` skill: inspect/resume the actual draft, package the approved binary, preserve existing languages/English (India), reconcile stale listing text, and import CSV/image batches of 10–11 listings (maximum 11), saving/verifying each. Final screenshots have not been uploaded; live certification remains unverified. No Store submission was made here.
2. Separately plan the Linux rebuild and Ubuntu/Mint/hardware checks. Linux remains 12.6.1 and was not released in this task.
3. Broaden Windows 10/clean-machine/device coverage, professional translation checks, and signing if a certificate becomes available. These limits are disclosed; do not describe untested systems as passing. Unsaved editor buffers cannot be established from disk inspection.
