# Current capture checkpoint — 21 October 2026

## Completed software fix

- Version 12.7.5. Dynamic populated Info metadata uses existing localized interface terminology, with six additive keys translated in all 43 locales. Original Help, literals and existing UI strings verified unchanged against pre-edit backup.
- Desktop build: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.5-Multilingual-Review.exe`
- SHA256: `3a06b1acde063400d51897908ac1a71fe00e45e75971ba5ef7295e568f590cf1`
- Build succeeded. Embedded main/transfer modules and 43 locale files match maintained source. English Help unchanged. Real EXE launches and displays translated inspector metadata in Arabic and German.
- Inspector all-language regression passes. Full unit suite: 86 tests, one known unrelated failure `test_store_manifest_declares_12_6_language_expansion` expecting Serbian Latin, whereas package intentionally declares Serbian Cyrillic. Do not claim a fully green suite or change correct manifest to mask this.
- Logs: `docs/BUILD_MULTILINGUAL_12.7.5.txt`, `docs/TEST_INSPECTOR_12.7.5_FINAL.txt`, `docs/EMBEDDED_REVIEW_12.7.5.json`.

## Backups

- Before edits: `F:\Resolution File Manager project\Recovery Backups\2026-10-21-before-inspector-localization\source` (+ verified ZIP), 440 files.
- Verified post-fix source: `F:\Resolution File Manager project\Recovery Backups\2026-10-21-12.7.5-inspector-verified\source` (+ verified ZIP), 449 files. Subsequent review-index title-only helper adjustment is in maintained source, not this snapshot.

## Screenshot progress — NOT complete

Root: `F:\Resolution File Manager project\Store Preparation 12.7.5\Screenshots E Drive`

12 genuine native screenshots: FOUR each in `en`, `ar`, `de`. PNG copies verified identical decoded pixels and 1920 × 1032 original resolution. Native JPEG originals preserved. Maximized window, no taskbar. Only E: sample directories visible; C:/F: collapsed. No conversion/copy/move/deletion performed. All other 40 languages still need capture; do not claim all 43 screenshot sets are finished.

Layouts: `01-details-info`, `02-dual-previews`, `03-thumbnails`, `04-video-conversion`. Arabic uses nature/architecture demo thumbnails from `E:\Resolution File Manager Demo Media`; English/German show varied actual videos, not sample variants. Previews are two distinct wildlife/landscape clips in all three sets. Conversion uses three selected actual videos; German demonstrates Keep both (default Skip existing text is clipped in its fixed-width selector).

`capture-progress.json` is authoritative for saved captures; `validation.json` lists exact missing layouts/languages; `REVIEW.html` displays completed sets. No upload or submission, no Git push/commit, no Linux work.

## Capture tooling and efficiency limitation

`tools/store_capture_session.mjs`: supported native Sky API, persistent capture/save manifest, no overwrites, native screenshots only. `tools/launch_store_review.ps1`: current EXE, isolated review settings, E: sample paths, language and view presets. `tools/validate_store_captures.py`: batch real PNG normalization, unchanged pixel verification, 43-language completeness/index.

The Tk accessibility tree exposes menus but not named individual controls. Capture tool is NOT a fully unattended all-language UI robot: currently each state-derived input is inspected, layout width differs by locale, so blindly replaying English coordinates is unsafe/unreliable. Do not pretend remaining sets are running automatically. Preserve these completed sets instead of repeating.

## Resume

German isolated 12.7.5 review app is currently open, no conversion dialog. Close only that isolated app before restarting settings. Run launcher with `pwsh -NoProfile -File tools/launch_store_review.ps1 -Language <code> -View Details -Sort duration -Info`.

Native node helper: import `tools/store_capture_session.mjs`, `createCaptureSession(captureRoot,'12.7.5')`. `select()` gets returned current window (localized title may vary). `act(method,args)` does one native action and refresh; inspect latest screenshot before next coordinates. `save(code,layout,{reviewed:true})` preserves earlier captures.

Maximize by double-click title bar. If left tree is collapsed at startup, its sash is at x10; drag to x212 if desired. Right tree shows E: expanded by default, C:/F: closed. Main Details/Info: right fourth row is cattle clip, x~1370,y404 for current tested languages, but inspect the current state before using coordinates. Left snowy wildlife clip is duration-sorted row at y924 before previews, file `19784079-hd_1080_1918_60fps.mp4`. Enable each preview and balance divider at x965 (initial divider varies by locale). Pause each for stable final capture.

Thumbnail view via left selector; for conservative universally suitable imagery select E: Demo Media and enable Images. Conversion: highlight right first three rows, Tick selection (localized toolbar position varies), Tools > localized Convert selected videos. Center dialog; never Start conversion. Check every visible selector/label for clipping. Save primary full main-window screenshot including owned modal, not the smaller standalone dialog snapshot.

After more captures: `python tools/validate_store_captures.py "F:/Resolution File Manager project/Store Preparation 12.7.5/Screenshots E Drive"`.

Existing release notes/keywords remain in Store Preparation 12.7.4; reconcile version and fresh Store export later. Do not upload older-package material or label this new set upload-ready. Standing import preference remains max 11 Store listings per folder.
