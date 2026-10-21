# Store screenshot review — 21 October 2026

**Complete: 172 native PNG candidates, 43 languages × four views, 1920×1032.** Final file/hash/dimension/duplicate/media-content checks pass. Visual inspection covered every gallery overview, main-control strips at original pixel size and every final dual-preview panel, with targeted full-size checks for Arabic, Bengali, German, Persian and Urdu. No new visible application layout defect was identified in these four views. This is not professional translation proofreading or exhaustive theme/scaling/dialog QA.

## Capture repairs and preservation

- Reacquire the capture window before saving; retry bounded focus loss and reject overlapping notifications. Strict class/size/position checks distinguish NVIDIA title-bar decorations from obstructing windows. Six capture-tool tests pass, including stale-image review invalidation.
- A Bengali preview containing a ChatGPT notification was rejected and preserved. Paused-preview staging was also corrected to synchronise frame, slider and displayed time at three seconds. All 43 preview originals were preserved and retaken; the other 129 images were retained.
- No application code or version changed, no rebuild occurred, and no copy/move/delete/conversion was executed to stage UI. Earlier approved captures and versioned binaries remain intact.

## Exact provenance and binary checks

- Version: **12.7.8 Windows review**. Binary SHA-256: `5b2c1270038627adb0d1c0525e82269359d2bd02a0611172cafc11c2af2c2718`.
- Six maintained application modules and all 43 locales match the frozen binary. These new captures are **verified-source native UI**, not 172 captures of the packaged process.
- Compared the saved exact-binary Arabic four-view set against source-native views. A fresh background capture from the existing packaged English process also showed the expected controls; this client-only diagnostic is not a Store screenshot. Its PNG SHA-256 is `0d2dda3d2e9f52628c19bf079adc27f4da0981e5bfefed8e9e4d1a67e5174997`.
- Exact reviewed image hashes, source hashes, binary evidence and review scope are saved locally in `Store Preparation 12.7.8/Batch Candidates v2/visual-review.json` (SHA-256 `aafb8f1ad8fe541dce769c2cbacba1db34c98a303ec9d68a785feee833fe4148`). Integrity/diagnostic sheets are under `review-evidence/`; `REVIEW.html` is the gallery. Existing packaged-process Arabic originals remain in `Screenshots E Drive`.

## Gates and remaining work

- `captureComplete: true`; `visualReviewComplete: true` **for the four screenshot views**.
- `fullNativeReleaseReviewComplete: false`; `readyForRelease: false`; `readyForStoreImport: false`.
- Broader native resizing/dialog/theme/scaling review recorded in the layout checkpoint is still incomplete. Prepare matching release/package assets and run final release gates before publication. The last local Store package is still 12.6.2.0 and must not be represented as 12.7.8.
- No Store import/upload/submission, GitHub binary release or Linux release occurred. Preserve Serbian's existing Cyrillic manifest/test correction.
