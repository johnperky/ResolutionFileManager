# Undo safety fix — 20 October 2026

Authoritative source remains `F:\Resolution File Manager project\ResolutionFileManager-Project-v6`.
Verified pre-edit snapshot: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-before-undo-fix\source` (286 files plus ZIP). Earlier versions remain preserved.

## Cause and repair

Previous Undo could collide with FFprobe/FFmpeg/Pillow reads and popped the entire
Undo history entry even after an error. Repeated replacements could consequently
restore sources but strand a previous destination backup.

MetadataCache.inspect and thumbnail workers now share a concurrent-reader gate.
Undo prevents new readers, drains existing readers, and performs restoration off
the Tk thread. Preview decoders are stopped first, and new preview selection is
suspended until recovery completes. Windows sharing violations 32/33 retry for up
to two seconds. Other failures are not blindly retried.

Each record checkpoints its completed move/copy removal before backup restoration.
Failed recovery retains the current and earlier records plus replacement backups;
a second Undo resumes unfinished steps. Recovery stops at the first failure, so
earlier replacements of the same destination cannot be undone out of order.
Queued transfers wait until incomplete recovery is resolved. Existing source or
destination files and modified transfer outputs are not silently overwritten.
Recovery remains session-based, not durable across application exit; do not
discard backups or close the app during incomplete recovery.

English instructions are in Safe File Actions, beside the existing Undo safety
material. Approved chapter order and detailed English content remain intact.
Other language packs are unchanged until the authorised overnight task.

## Tests

- New tests first failed for missing coordination/recovery APIs, then passed.
- `test_undo_busy`: concurrent reader/exclusive restoration, actual Windows sharing
  handle released after a delay, failed backup restoration resumed safely, and
  app-level conflict retaining its record and restoring on retry.
- Targeted transfer/Undo unit tests: 17 passed.
- Real Tk upgrade regression: 25 checks passed, no callback exceptions. Includes
  a generated video actively playing, a held reader during Undo while UI callbacks
  continue, active scans, repeated flattened replacement moves and original bytes
  restored for both sources and the original destination.
- Layout/pointer regression: 50 checks passed. English scan/sort/Smart Collections
  and 22-chapter Help navigation/search smoke passed.
- Full unit discovery results and frozen EXE verification recorded separately.
  Deferred translation parity/full-help failures and the pre-existing Serbian
  Store-manifest expectation must not be presented as passing.

Full discovery: 83 tests executed, 44 failure entries: 42 deferred non-English
locale parity subtests, all-language Help completeness, and the existing Serbian
manifest test expecting Latin rather than the current Cyrillic locale. The release
version consistency check passes. No new Undo/transfer regression failed.

Final Windows build: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.3-English-Review.exe`.
SHA256 `53448a9e491e2f96011e3ea6e13892da055ba5642cc47a894be2053181a286ae`.
Frozen main/transfer modules match maintained source exactly, and all43 embedded
locale bytes (including the updated English Help) match maintained resources.

## Scheduled continuation

Automation `rfm-translate-latest-english-changes-and-verify` runs once at 00:01
Europe/London on 21 October 2026. It updates all 42 other existing languages from
the current English UI/help masters, validates completeness, links, placeholders,
RTL and layout, runs regressions, then produces a multilingual Windows review EXE.
No GitHub, Linux, Store or publication work is authorised by that continuation.
The task must delete its own automation after running.
