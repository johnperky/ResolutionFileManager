# Screenshot continuation — 21 October 2026

- Current Windows review version: 12.7.8. Read `LAYOUT_REVIEW_CHECKPOINT.md` and verify its exact hashes/readiness first.
- Capture root: `F:/Resolution File Manager project/Store Preparation 12.7.8/Screenshots E Drive`.
- Completed: **one Arabic `01-details-info` capture**, visually reviewed, genuine maximized 1920 x 1032 native image, actual PNG/pixel/dimension validation passed. Zero complete language sets. **171 of 172 views remain.**
- `capture-progress.json` records selected originals; `validation.json` gives exact missing views; `REVIEW.html` shows selected captures. Original JPEG and identical-pixel PNG are both retained.
- Old 12.7.5 English/Arabic/German sets remain untouched. The 12.7.6 diagnostic dual-preview image is excluded because it exposed Info clipping; its bytes remain preserved. New UI fixes/version titles require final-version captures; never relabel old screenshots.
- 11:10 work was delayed by additional layout fixes and verification. Continuation is scheduled for **11:45 Europe/London today**. No upload/submission/public release yet.

## Exact resume state

An isolated Arabic 12.7.8 review app is open, maximized, main Details/Info view, no modal or conversion running. Right wildlife/landscape video is selected and populated Info is visible. Left list is duration sorted; snowy wildlife clip `19784079-hd_1080_1918_60fps.mp4` is visible near row y924. Coordinate hints are not permission to replay blindly: inspect each fresh native screenshot.

In a Computer Use node session, import `tools/store_capture_session.mjs`; create the session with the root above and version `12.7.8`. `select()` observes the current binary; `act(method,args)` performs one observed action then refreshes, passing its current screenshot ID. `save(code,layout,{reviewed:true})` preserves earlier captures. Do not overwrite the completed Arabic Info shot.

Four required views per language: Details/Info, two distinct previews, varied suitable thumbnails, conversion options with selected actual videos (never Start). Use only E: sample folders. UI control positions vary by language. Existing helper is not an unattended all-language robot. Stop and checkpoint any new clipping instead of saving it as reviewed.

Before changing language settings, close only the isolated review app; then run the established launcher with the requested language. Choose E: Demo Media for conservative nature/architecture thumbnail content where appropriate. Do not modify sample files.

Run `python tools/validate_store_captures.py "F:/Resolution File Manager project/Store Preparation 12.7.8/Screenshots E Drive"` to normalise/validate native images in a batch. It preserves original pixels/resolution and writes completeness/index files. Capture count is not native linguistic sign-off; inspect every actual view.

Release remains blocked until native visual review, screenshot sets, tests and matching release assets are complete. No Store work is authorised beyond local preparation.
