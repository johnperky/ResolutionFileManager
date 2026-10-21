# Local screenshot batch

Standing user preference: keep this launcher and runner as the default capture method for future Store work. Adapt versions, scenes, language lists and app-specific setup when needed instead of recreating a manual remote-control workflow. Preserve versioned originals and rerun verification after adaptations.

Run `Capture Store Screenshots.cmd` in the main project folder. It generates all 43 languages × four views without remote control or per-click assistant calls. Leave the desktop free while it runs; it needs an unlocked Windows desktop at the reviewed display size. Close the window or press Ctrl+C to stop; completed candidates are retained.

For a smaller run: `python tools/batch_store_screenshots.py --languages en,de,ar`. Repeat the same command to resume. A Windows file lock prevents overlapping batches in the same output folder. Failures stop the batch and preserve completed images. Changed application source/build/resources require a new output folder (`--output`). Capture-only repairs can resume unchanged application provenance; earlier script provenance is preserved and new captures record their runner hash.

Output: the project parent's `Store Preparation 12.7.8/Batch Candidates v2` folder. `REVIEW.html` provides a combined gallery; `candidate-progress.json`, per-language `captures.json`, `provenance.json` and `run-status.json` record progress and hashes. The double-click launcher's log is `%TEMP%/rfm-screenshot-batch.log`.

The runner verifies maintained application modules and all 43 locales against the frozen review EXE, checks the saved layout gate/binary hash, then runs the matching source's real native Tk widgets in a separate process per locale. These are **verified-source native UI candidates, not captures of the packaged EXE process**. Runtime/packaging differences still require binary spot checks. Every candidate starts `reviewed: false`; no approved capture manifest or release gate is changed.

The runner opens real sample media from E:, populates Info, renders two video frames, shows image thumbnails and opens a conversion plan. It never presses Start or invokes copy/move/delete. Settings and caches are isolated. Actual window pixels are saved directly as PNG without resizing, overlays or reconstructed UI; foreground ownership is checked before capture. Existing manually approved Arabic screenshots and all older versions remain untouched.

Focus loss is retried locally before each capture. Visible overlapping windows/notifications delay capture; a small NVIDIA nView title-bar decoration is excluded using class and strict size/position checks. Persistent obstruction stops rather than saves a contaminated image. One older Bengali preview with a ChatGPT toast was rejected and preserved under `rejected/`, then retaken. `tools/review_batch_candidates.py` verifies PNGs, dimensions, hashes, duplicates and media variation, and creates diagnostic overview/control sheets without changing originals.

Paused preview staging synchronises the actual three-second frame, slider position and displayed time before saving. Earlier preview originals are retained under `rejected/preview-timing-originals`; a preview-only resume skips the unrelated thumbnail/conversion staging.

Review the gallery together for clipped controls, empty media, dialogs and RTL typography. Approve only views actually inspected. Candidate completeness alone does not authorise Store import or release publication. No Store upload, build or release is performed by this tool.
