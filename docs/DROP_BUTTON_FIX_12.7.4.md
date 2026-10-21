# Explicit drag/drop action buttons — 12.7.4

Replaces the misleading Yes/No/Cancel prompt with Copy/Move/Cancel buttons using
existing translations in all 43 languages. RTL button order is supported. Cancel
is initially focused; Escape or closing the prompt cancels. Enter invokes the
focused action. The existing boolean Copy/Move contract and transfer workflow
are preserved; no file operation begins before the existing transfer preview.

Backup before edits: `F:\Resolution File Manager project\Recovery Backups\2026-10-21-before-drop-button-fix\source`
(327 source/resource files verified plus ZIP). Older Desktop builds preserved.

Tests: actual Tk dialog checks exercise all 43 languages and all four outcomes
(172 actions: Copy, Move, Cancel, close). Relevant app upgrade regression passes
28 checks, including drag-group retention, Copy/Move mapping, cancellation and
existing selection/Info/basket/rename/Undo features. Full discovery: 85 tests,
one existing Serbian Store-manifest mismatch only. Help validator: 43 languages,
zero errors and review flags. No validator or Store test was weakened.

The only changed Help text is copying_and_moving.p005 in each language. All other
paragraphs, chapter ordering/titles and every existing UI translation are
unchanged; DROP_CHANGE_PRESERVATION_12.7.4.json records the checks.

No Store changes, Git commit/push, public release or Linux build was performed.

Final build: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.4-Multilingual-Review-20261021-061556.exe`.
SHA256 `773300870db66604b8b582da5f76b8fb361a59416537de7c1654c7217da24f50`.
Frozen main/transfer code and all43 locale resources match maintained source.
Packaged startup passed15 seconds with empty stderr. Source Help/navigation/
search smoke passed in English, German and Arabic. The exact-scope check caught
unwanted general-helper formatting changes; all unrelated paragraphs were
restored from the verified baseline before final packaging. Only the intended
transfer paragraph differs in each language.

Final source snapshot target:
`F:\Resolution File Manager project\Recovery Backups\2026-10-21-12.7.4-drop-buttons-verified\source`.
