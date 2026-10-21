# English test-build plan

Scope approved in chat: new-folder commands, previewed transfers with optional folder preservation, explicit collision decisions, rubber-band selection/internal drag, live rename preview, remembered Info width, thumbnail slider and a temporary selection basket. English testing comes before translations, GitHub, Linux releases or Store work.

- [x] Snapshot all current tracked/untracked source and preserve Git history and 12.6.2 executable.
- [x] Test-first transfer planning/execution helpers using disposable files: duplicate input names, same paths, replacement recovery, cancellation, source preservation.
- [x] Reuse the existing transfer queue/undo with a shared preview dialog and per-conflict decisions. Keep external drag-out.
- [x] Add pane New Folder and browser selection controls without disturbing header gestures.
- [x] Add live batch rename, remembered Info width, debounced thumbnail sizing and session-only basket references.
- [x] Update English instructions only; retain all other language resources unchanged.
- [x] Run regressions and GUI checks; build a uniquely named English review EXE on Desktop. Record untested cases honestly.

Safety: never overlay older source, silently overwrite a collision, delete a move source before a complete copy, push unreviewed work, or publish anything. Preserve the existing queue/undo record format. Verify input/output aliases and reserve outputs within a batch.
