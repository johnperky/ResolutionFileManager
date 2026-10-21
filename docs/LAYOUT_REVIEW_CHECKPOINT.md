# Layout review checkpoint — 21 October 2026

readyForScreenshots: true
readyForRelease: false

Screenshot update: **172 final candidates / 43 complete sets** now pass integrity checks and four-view visual review. See `STORE_SCREENSHOT_REVIEW_12.7.8.md` for exact hashes and scope. New captures use matching source native UI; packaged-binary checks include the existing Arabic four views and a fresh English process diagnostic. Broader native release QA beyond these four views remains incomplete, so `readyForRelease` stays false. The manual screenshot automation was deleted; retain the local batch workflow.

Version: 12.7.8 Windows review build. Screenshot-view review is complete; exhaustive native resizing/dialog/theme/scaling review and release packaging remain outstanding.

## Exact reviewed baseline

- Binary: `dist/multilingual-review-12.7.8/ResolutionFileManager-v12.7.8-Multilingual-Review.exe` (versioned Desktop copy also exists).
- Binary SHA-256: `5b2c1270038627adb0d1c0525e82269359d2bd02a0611172cafc11c2af2c2718`.
- `media_sorter.py`: `6f46e06c9ce89b4f7cf3bc26555bfbb33a37353a86b5be4ba4f010a1577b4998`.
- `transfer_engine.py`: `b78097df216c7cae9cb89b072361289022dbfb561717e2e0900345ee7c856568`.
- `transfer_ui.py`: `52809db9282d7b49fcef005a7682ff7e8421e6011bc606914a5de98cde6db04b`.
- Exact embedded modules and all 43 locale files match source: `EMBEDDED_REVIEW_12.7.8.json`.

## Verified fixes and checks

- Native German 12.7.5 reproduced clipped conversion conflict text; real-Tk measurements also found clipped preset/resolution/engine options. Pixel-measured selector sizing passed all 43 languages in `CONVERSION_LAYOUT_REVIEW_12.7.6.json`. Conversion function remains AST-identical in 12.7.8. Native German/Arabic intermediate binaries confirmed visible controls; native final Arabic conversion dialog checked too.
- Initial 12.7.6 screenshot work exposed Info metadata/action clipping when previews shorten browsers. Added read-only scrollable metadata and reserved the action row. Intermediate 12.7.7 tests found wrapped rows still exceeded the bottom in some locales; 12.7.8 reserves actions before variable-height headings.
- Final short-browser Info regression: **43/43 pass**, `INSPECTOR_LAYOUT_REVIEW_12.7.8.json`. Earlier failing reports are diagnostic history, not final results.
- Final unit suite: **86/86 pass**, `TEST_LAYOUT_12.7.8.txt`. Mouse/resizing/selection/Info/basket checks pass without callback errors: `LAYOUT_MOUSE_12.7.8.txt`.
- Upgrade toolbar/Info/transfer/rename/basket checks passed all 43 languages before the final Info correction: `LAYOUT_UPGRADE_REVIEW.json`; full rerun of that broader suite after the correction has not been performed.
- Complete Help validation passes. Existing locale/Help content was preserved. Serbian manifest/test correction remains intact. No media operation or conversion was executed.

## Actual native coverage and remaining review

- Final 12.7.8 Arabic main, populated Info, preview-shortened Info (actions visible), scroll to final metadata, and conversion dialog inspected through native UI. Intermediate 12.7.6 German main/Info/conversion inspected. This is not full native review of every language, screen, theme or scaling level.
- Four-view screenshot review is complete for all 43 source-native locales; automated completeness was supplemented by actual image review. Professional translation proofreading and broader release QA are not implied. The separate packaged-process set contains four Arabic views.
- Preserve all older native captures. 12.7.5 has 12 captures/three sets; 12.7.6 has one selected Info capture and an excluded dual-preview diagnostic original. Do not relabel old images as current.
- Batch children have finished. The earlier isolated English packaged review app remains open; do not change personal settings or confuse it with a batch child.

## Resume and publication gates

- Final candidate root: `F:/Resolution File Manager project/Store Preparation 12.7.8/Batch Candidates v2`; exact reviewed images in `visual-review.json`, gallery in `REVIEW.html`.
- Use `Capture Store Screenshots.cmd` / `batch_store_screenshots.py` and `review_batch_candidates.py`; preserve the older manual capture tools for binary spot checks. No remaining scheduled manual capture run.
- All 172 screenshot candidates are captured and reviewed. Capture-tool failures and replacements are recorded in the screenshot review document; no application edits/rebuild were needed for that work.
- No GitHub binary release, Store upload/submission, Linux build or publication. Conditional release follow-up must wait for finished native review, validated captures and matching release assets.
- Verified pre-edit source snapshots/ZIPs: `Recovery Backups/2026-10-21-before-layout-review/source` (294 files) and `2026-10-21-before-info-height-fix/source` (307 files), beneath the F: project parent. Earlier versioned binaries retained.
