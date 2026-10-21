# Store UI fixes — 20 October 2026

Authoritative source: `F:/Resolution File Manager project/ResolutionFileManager-Project-v6`.

## Changes and causes

- Tick-counter resources already existed in all 43 languages. The initial value and updates used English literals instead of `pane.checked`; both now use the resource.
- Conversion plans correctly detected duplicate output paths, but their internal status was absent from the displayed-label mapping. The mapping now covers Duplicate output, Same as source and Skip existing without altering planning or conversion behaviour. Only the two missing resource keys were added to every language.
- Table widths were based on fixed English sizes. New-language/migrated layouts and Reset widths now measure the real heading font. The pane records the language associated with saved widths; subsequent same-language manual widths are kept, including deliberately narrow columns. Mouse resizing minimum and maximum are unchanged.

## Verification

- New regressions reproduced the old English counters and unmapped statuses before the fixes; all four targeted tests pass afterward.
- Full unit/regression suite: **66 passed** (`TEST_STORE_UI_FIXES_2026-10-20.txt`). The old release test hard-coded 12.6.1; it now checks version format, source agreement and the release notes for the actual version.
- Real Tk GUI checks: **43/43 passed** (`GUI_SMOKE_STORE_UI_ALL_LANGUAGES_2026-10-20.json`), covering initial and updated counters, measured headings, saved/manual width retention, language migration, scanning, Smart Collections, Help navigation/search and filter dialogs.
- The GUI test was extended to restore pane state; an initial run exposed a test timing error (sorting while that restore's asynchronous scan was still running). The test now waits for scan completion. The final full 43-language run passed.
- Windows 12.6.2 build completed. Its Desktop copy matches the maintained dist build.
- Packaged launch/liveness test: passed for 30 seconds with Italian disposable settings and empty stderr (`BINARY_SMOKE_STORE_UI_FIXES_2026-10-20.json`). This is not claimed as exhaustive binary feature testing.
- All **43 embedded locale files** match source byte-for-byte.
- Native visual check of the rebuilt Arabic app: localized zero/four counters and the formerly English duplicate-output warning displayed correctly; visible column headings fitted. Evidence: `STORE_UI_FIXES_ARABIC_2026-10-20.png`. No conversion was started.
- All 43 Help objects match the pre-fix snapshot. The current English master file matches its pre-fix SHA-256: `4b10b7ae5bc8116a3880de904eb644d8c4514b6aa776c819ea1c75a70096c5c8`.

## Build

Desktop: `C:/Users/johnp/Desktop/ResolutionFileManager-v12.6.2.exe`.

SHA-256: `7c740a91739da8b46bc39888384d93e94c728b692ad7b0a2f6eda53b082bd236`.

Pre-fix labelled source snapshot and ZIP: `F:/Resolution File Manager project/Recovery Backups/2026-10-20-before-store-ui-fixes`.

## Screenshot preparation checkpoint

The user's UI-fix decision is resolved: fixes approved and implemented. Do not ask for that approval again.

- Retain the 26 prepared listing drafts and reviewed keyword overrides under `packaging/microsoft-store/prepared-12.6.1`; the folder name records their preparation baseline, not an instruction to upload an old executable. Do not regenerate translations unnecessarily.
- Retain all older captures. The seven 12.6.1 review captures are historical, not newly approved final Store images.
- Completed: **80 selected native captures across all 26 remaining languages**, in `F:/Resolution File Manager project/Store Preparation 12.6.2`. Each set contains details/resolution sorting without previews, thumbnails/codec sorting, and the conversion window with two selected neutral clips. Italian and Arabic also have dual-preview captures.
- `tools/launch_store_review.ps1` starts the built executable with isolated, persisted review settings and the real `F:/free to use videos` folder. It does not modify application code or control the UI. Close its review instance before changing those settings. Capture and operate the native window with the Computer Use tool.
- Use 3–4 varied, unaltered, original-resolution native-window images per language, no taskbar. Include details without previews, thumbnails/sorting, useful previews and the conversion window with selected files. Prefer neutral `sample*` woodland/seascape clips for all languages. Do not start conversions.
- The latest existing Store package remains 12.5.2.0 and is **not** the rebuilt 12.6.2 release. A new validated package is required before any later authorized upload.
- No Store upload/submission, public release, Git commit/push or Linux rebuild occurred. The older user-open Desktop app and user preferences were left untouched.

## Screenshot review handoff

- `REVIEW.html` in the capture root links to the original PNGs and displays the reused localized listing drafts. `submission-preparation.json` records dimensions, hashes, per-language review notes and exact selected files for the later Store workflow.
- All 80 selected PNGs passed integrity checks. Images were not cropped, translated, resized or otherwise altered; native window capture excludes the taskbar. Source folder: `F:/free to use videos`. Conversion was never started.
- Two superseded thumbnail captures remain recoverable in their language folders but are excluded from the selected manifest: Arabic `02-thumbnails.png` and Portugal `02-thumbnails-codec-sorting.png` (use its wider replacement).
- Visual checks found that a few closed option selectors still truncate long localized values, notably in Finnish, Norwegian, Ukrainian, Romanian, Malay, Bengali, Slovak and Serbian. These are recorded for review; the screenshot task does not claim a perfect layout or native-speaker approval. Widening conversion windows and adjusting pane dividers resolved the larger guidance/toolbar clipping in selected captures without changing source code.
- All 26 listing drafts are included beside their screenshots. No translations were regenerated. User approval and a matching validated MSIX remain necessary before upload; `uploadReady` is false.
