# 12.7.0 English-only review — 20 October 2026

Authoritative maintained source: `F:\Resolution File Manager project\ResolutionFileManager-Project-v6`.

The latest user request supersedes the scheduled multilingual/GitHub/Linux phase: implement and test English first, then wait for approval before translating, updating GitHub/Linux releases or preparing Store submissions. No Git commit/push or Store work was performed.

## Recoverability

Verified baseline: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-1900-before-transfer-upgrade\source` (250 source files, manifest and ZIP); full Git history in a verified repository.bundle; original 12.6.2 Windows EXE preserved with matching hash; existing 12.6.1 Linux binary and a separately verified 165-file Linux handoff source preserved. See that folder's RESTORE.md. All 42 non-English locale files remain byte-for-byte identical to baseline. No user-open EXE was closed. Intermediate, never-launched review executables were moved off Desktop into this backup folder rather than leaving stale candidates beside the final build.

An early post-edit snapshot under `2026-10-20-12.7.0-English-review/source` failed verification because its build log was still being written. Do NOT treat that particular snapshot as valid. Use the separately verified final snapshot recorded after all build/test logs finish.

## Implemented for review

New Folder (File, pane menus, Ctrl+Shift+N); shared transfer preview for pane copy/move, paste and drops; remembered preserve-folders/files-only setting; destination creation and optional open; per-conflict Keep both/Replace/Skip/Cancel and apply-to-all; reserved numbered names; staged cancellable transfer with source-change checks and replacement rollback; queue Undo guards and repeated-replacement restoration; rectangle selection/ticks in Details and Thumbnails with Ctrl-add; internal drop Copy/Move choice; retained external drag registration; live single/batch rename previews; remembered useful Info width; debounced continuous thumbnail-size slider; temporary reference-only selection basket.

English Help retains its 22 chapters/order and adds accurate instructions in existing relevant chapters. Other languages deliberately await user approval. The English-review builder validates English alone and uses a separate dist directory; the normal release builder continues to require complete translations.

## Verification and limits

- `test_transfer_upgrade`: 12 tests pass for planning, numbered-name reservations, per-conflict apply-all, same-file safety, skip/keep-both/replace, cancellation, source changes, publication failure/recovery, undo fingerprint protection and Windows publication without a second full copy.
- Real-Tk upgrade suite: 20 checks pass with no callback exceptions, including Info width, live previews, basket references, Details/thumbnail rubber selection, ordinary selection click, internal drag preserving multiple files, folder creation, queue copy/undo and repeated replacement move/undo restoring every original.
- Existing English real-Tk scan/sort/Smart Collections/Help navigation/search suite passes with 22 help chapters. Geometry checked programmatically; no completed visual screenshot review is claimed.
- Full discovery: 78 tests run, 44 failure entries confined to deliberately deferred non-English Help/literal parity (42 locale subtests plus full Help check) and the pre-existing Serbian Store manifest expectation (`sr-latn-rs` test versus corrected `sr-cyrl-rs` manifest). No tests were weakened to hide these. All other discovered tests pass. See TEST_12.7.0_ENGLISH.txt.
- Frozen main/transfer modules exactly match maintained source, and all 43 embedded language files match disk. Desktop EXE: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.0-English-Review.exe`, SHA-256 `d52b0f9c60336239b834e2a8902371a554b8d9b9f600b60f8e9685272e00cf78`. See EMBEDDED_REVIEW_12.7.0.json and BINARY_SMOKE_12.7.0_ENGLISH.json for packaged startup results.
- Native dragging into another external application, large-drive stress, and Linux build/GUI compatibility are not newly manually tested. Existing external-drag registrations are retained. All tests use disposable files; no user media was changed.

Before any public release: user reviews English build; address feedback; translate new UI/Help fully into the existing 42 other languages; restore full parity checks; test RTL and all languages; build/test Linux; then update GitHub and prepare Store work only as approved. Do not publish this English prototype.

Final source snapshot destination: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-12.7.0-English-review\source-verified-final`. The one-time scheduled automation was deleted after execution so it cannot repeat the superseded multilingual/GitHub phase.
