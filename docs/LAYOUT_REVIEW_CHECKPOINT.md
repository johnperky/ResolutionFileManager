# Windows layout review — 21 October 2026

Version: 12.7.10
readyForScreenshots: true
readyForRelease: true

## Exact final candidate

- Binary: `dist/multilingual-review-12.7.10/ResolutionFileManager-v12.7.10-Multilingual-Review.exe`
- SHA-256: `f1424ea2b42efb8586886d8721ea2864e40bb9df1cdafe8aef1ec7ae3ac6d22f`
- Six embedded application modules and all 43 locales match maintained source: `EMBEDDED_REVIEW_12.7.10.json`.
- Earlier candidate binaries, portable packages and screenshots are preserved; final capture root is `Store Preparation 12.7.10/Batch Candidates v3`.

## Demonstrated fixes and evidence

- Scaled Treeview row heights/headings; Japanese fallback-font measurements settled before sizing.
- Readable Dark/High contrast readonly dropdown colours; conversion settings scroll at enlarged text size, with action buttons reserved.
- Top guide wraps to preserve toolbar actions. Scan status is reserved vertically and Cancel/progress/count before expandable status text horizontally. Regressions failed before fixes and pass after.
- Appearance Cancel restores exact prior custom column widths; hidden-files toggle updates both panes/trees/inventory, persists and leaves geometry unchanged. Translated into 43 languages; screenshot setting forced off.
- Current final source: English 40-state theme/scale/resize suite passes, including scan Cancel visibility/width. Japanese 40-state font suite passed immediately before the scan-footer-only correction. Earlier English/German/Arabic appearance matrices (120 states) are retained with their exact scope. Do not claim exhaustive every-language/theme/scale coverage.
- Final packaged binary: System 100%, Dark 200%, High contrast 150% main/Appearance and menu-toggle persistence checks pass with isolated settings and system-only PATH. Actual populated binary views inspected, including corrected enlarged toolbar and scan footer.
- Final 89 unit tests pass; complete Help validation has zero errors/review warnings. Earlier 43-language upgrade/Help checks are retained; unchanged logic evidence reused.
- Defender scan of this exact binary reports no threats. `TEST_RELEASE_12.7.10.txt`, `DEFENDER_SCAN_12.7.10.txt`, `PACKAGED_REVIEW_12.7.10.json`, `APPEARANCE_REVIEW_12.7.10.json`.

## Review complete and publication requirements

- **172/172 final PNGs across 43 languages pass validation and scoped visual review.** See `STORE_SCREENSHOT_REVIEW_12.7.10.md`; exact-image approval and pixel comparison are saved with the candidate root.
- No unresolved release-blocking layout issue in the reviewed scope. Code/screenshot review is complete for this exact source/binary. Current 89 tests, full Help, source/embedded locales and Defender checks pass; initial package content checks pass.
- `RELEASE_READINESS_12.7.10.json` records public review evidence. Before publication, freeze committed source/docs and require the external `release-output/12.7.10/RELEASE_READINESS.json` produced by `finalize_release_archives.py`; it binds final ZIP/EXE/checksum hashes, exact source commit and this review. Use `publish_reviewed_release.py`; never publish from a stale archive or unreviewed rebuild.
- Tested on the current Windows11 host in isolated settings/system-only PATH; no separate clean-OS or Windows10 claim. Linux remains12.6.1, Store package/submission unchanged. No Store upload/submission or Linux release.
