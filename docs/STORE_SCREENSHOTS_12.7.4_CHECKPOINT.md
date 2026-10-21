# E: Store screenshot checkpoint — 21 October 2026

Nothing uploaded or submitted. No application source or translations changed.

## Captured and verified

Root: `F:\Resolution File Manager project\Store Preparation 12.7.4\Screenshots E Drive`

English: four genuine screenshots, original 1920 × 1032 maximized application window, taskbar excluded:

1. Details + populated right Info inspector (width adjusted to show full metadata).
2. Dual previews: `19784079-hd_1080_1918_60fps.mp4` wildlife in snow and `9894607-uhd_4096_2160_25fps.mp4` cattle/landscape. Preview panes balanced.
3. Thumbnails, varied videos and resolutions.
4. Centered conversion dialog with three different ticked files; conversion NOT started.

Both panes use `E:\free to use videos`; C: and F: remain collapsed. Originals are preserved as native JPEG capture bytes. `validate_store_captures.py` encoded real PNG copies and verified unchanged dimensions and decoded pixels. `validation.json` and `REVIEW.html` are in the root. Four English captures pass format/pixel checks; the other 42 languages are incomplete.

## Blocker found before mass capture

Arabic app launches and localized menus/columns display, but populated Info metadata labels remain English (`Type`, `Codec`, `Resolution`, `File size`, `Modified`, `Duration`, `Frame rate`, `Bitrate`, `Pixel format`, `Dynamic range`, `Audio`, `Rating`, `Colour label`, `Tags`, plus values such as `Unrated` and `None`).

Confirmed in `media_sorter.py` around lines 2127–2140: these are hard-coded dynamic inspector strings. Do not duplicate this issue across 42 languages or claim their screenshot sets are complete. Diagnostic only: `Excluded diagnostics/ar-info-untranslated.jpg`, NOT an upload candidate.

The Arabic capture session also initially displays no left folder tree (right tree remains visible). Check splitter positioning before any accepted Arabic capture. Do not repair app code silently as part of screenshot-only preparation; obtain direction for the needed fix and rebuilt executable first.

Arabic isolated review app is currently open on E:, maximized; Info enabled on the right. No files were converted, copied, moved or deleted.

## Reusable tooling added

- `tools/launch_store_review.ps1`: closed isolated review settings only; explicit E: sample path, Info preset, balanced panes, current versioned EXE. Uses `pwsh`, not Windows PowerShell 5. No personal app settings touched.
- `tools/store_capture_session.mjs`: load in Computer Use node session; `select`, `observe`, `act`, `save`. One input and refreshed state per call; inspect returned screenshot before next action. Native screenshots only, no blind coordinate loop, no image alteration. Preserves existing captures.
- `tools/validate_store_captures.py`: real PNG encoding without pixel changes, original preservation, all-43-language/four-layout completeness and HTML review index.

## Next steps

1. Resolve inspector localization and splitter issue with approval; rebuild current version preserving all other work.
2. Verify English and Arabic four-layout captures with rebuilt app before remaining languages.
3. Complete missing languages using E: only, maximize each instance, avoid taskbar/personal paths, inspect RTL and long labels. Use genuinely different clips and broadly suitable imagery.
4. Run PNG/pixel/completeness validation; visually review originals.
5. Reconcile with fresh Store draft export and existing five batches (max 11 listings each) before any later authorized import. No Store action is authorized by this checkpoint.
