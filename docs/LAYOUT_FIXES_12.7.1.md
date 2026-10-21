# 12.7.1 English layout/selection corrections

Supersedes the layout and direct-handler test claims of the first 12.7.0 review.

## Changes

- Moved inspector to its own nested divider, separate from the folder/browser divider. Restore and sash-release clamp keep file space available; oversized saved folder/inspector widths no longer consume the browser.
- Removed the heading Small/Medium/Large dropdown; retained the continuous thumbnail slider and existing View-menu presets.
- Selection basket now docks above the browsers and can be hidden/reopened without losing references. No floating basket window.
- Vertical mouse drags across Details rows form an action group; blank-space rectangle selection continues. A dedicated first bindtag keeps thumbnail drags/release routing to selection when the pointer crosses child image/filename widgets. This was the failure missed by earlier direct-handler tests.
- English instructions corrected, same 22 chapters. Other 42 locale files unchanged pending review.

## Verification

Native Windows mouse interaction using the computer-use skill on an isolated disposable-media source instance:

- Dragged over six Details files: six visible ticks and highlights.
- Resized Info, toggled off/on: file list remained visible, adjusted width restored.
- Opened docked basket above browsers; Add pane selection populated references.
- Reproduced thumbnail failure before child-bindtag fix; repeated native blank-space drag across image widgets afterwards: four visible selected/ticked cards, four-ticked counter, completed release.
- Dragged slider: thumbnails visibly enlarged/reflowed; no size dropdown remained.
- Closed only the isolated diagnostic instance; no user media was touched.

Automated: 17 real-binding/layout checks, 20 upgrade GUI checks, English scan/sort/Smart Collections/22-chapter Help navigation suite pass; no callback exceptions. 13 focused unit tests include an actual-sash clamp regression that failed before the fix. Full discovery: 79 tests, 44 known failure entries limited to deliberately deferred language Help/literal parity (42 locale subtests plus full-help test) and the pre-existing Serbian Store-manifest test expectation. No tests were weakened to suppress those failures.

The inspector GUI assertion was updated from an unconditional 280px to a balanced available-width requirement plus visible file space, matching the corrected independent split. No translation or Store checks were bypassed for a public release. This remains an English-only review build.

## Recovery and delivery

Pre-edit verified source snapshot: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-before-12.7.1-layout-fixes\source` (265 files plus ZIP). The previous Desktop EXE is preserved. An intermediate 12.7.1 EXE was moved into this backup folder; it is not the final review build.

Final Desktop: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.1-English-Review.exe`. Frozen-module/resource verification: `docs/EMBEDDED_REVIEW_12.7.1.json`; packaged startup check: `docs/BINARY_SMOKE_12.7.1_ENGLISH.json`. Final verified source snapshot: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-12.7.1-layout-fixed\source`.

Final EXE SHA-256: `9f88afc4c889f2af0dc718fd09733daecfa2e597988cdd462b4ef90a08e91051`. All three frozen application/transfer modules and 43 embedded locale resources match maintained source exactly.

GitHub, Linux releases, other language packs and Store submissions remain deferred until user approval. Not an exhaustive large-media or cross-platform test.
