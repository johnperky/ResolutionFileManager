# 12.7.2 English review checkpoint

Includes all requested follow-up corrections after 12.7.1:

- Dragging selects highlights only, never replacing or changing persistent ticks. Ctrl-drag adds highlights. Tick selection / Untick selection add/remove only the highlighted paths; Clear ticks clears the persistent action group.
- Sort, Select all shown, Tick selection, Untick selection and Clear ticks share a full-pane top toolbar outside the folder/file/Info dividers. No redundant “Highlighted files” label. Responsive placement wraps controls only when the whole pane narrows, not when Info opens.
- Info starts at 180px instead of 330px. Oversized old review settings reset once; a layout-version flag preserves later explicitly saved user widths.
- Outline-only rectangle; motion and release route across thumbnail image children and across the opposite pane. No solid overlay hiding files.
- Precise checkbox hit areas follow the glyph bounds, not the whole first column or thumbnail-label padding. A click toggles on release; movement beyond 4px becomes highlight selection and leaves ticks unchanged. Space keyboard ticking remains available.
- Tree alignment uses the least-indented currently visible nodes, not a fixed selected-folder offset. Vertical scrolling back to ancestors automatically returns horizontal alignment left without a click. Horizontal scrollbar still permits manual ancestor viewing.
- Thumbnail slider is hidden in Details and restored only in Thumbnails, retaining its setting. Compact Info labels wrap to the available width and its Copy path/Open/Reveal controls wrap rather than disappearing.

## Verification

English Help placement reviewed: checkbox accuracy and rubber-band highlighting now follow the existing tick-selection explanation; Info sizing is in the Info paragraph; thumbnail-slider instructions are in Details And Thumbnails. New folder, transfer preview/conflicts, live rename preview and the basket remain in Copying And Moving. The existing 22-chapter order and full detailed contents are preserved. English Help navigation/search smoke passed after this reorganisation.

`tools/test_layout_mouse_1271.py` now tests the current version through actual Tk binding dispatch, including child-widget/cross-pane release, preserving existing ticks, explicit tick/untick, exact checkbox click vs padding vs drag, both Info layouts, compact Info button fit, slider visibility, top-control fit and vertical/horizontal tree-scroll interaction. `tools/test_upgrade_gui.py` checks the retained upgrade features. English scan/sort/Smart Collections/Help suite passes. Details are in GUI_LAYOUT_12.7.2.json, GUI_UPGRADE_12.7.2_ENGLISH.json and GUI_SMOKE_12.7.2_ENGLISH.json. No claim of a completed native mouse retest after the user's physical Escape interruption is made; final accuracy checks are Tk event-binding tests. Focused read-only review found no important new defects in the pointer/selection/tree-scroll changes.

Full discovery retains known expected failures for the deliberately deferred 42 non-English help/literal packs plus the pre-existing Serbian Store-manifest test expectation. No validation rules were weakened to hide those. No translations, GitHub, Linux release or Store changes were made.

An unrelated existing timing issue was reproduced: immediate repeated-replacement Undo while metadata scanning/FFprobe holds the destination can report WinError 32 and leave the earlier destination in place; backups remain in the undo area. The completed-operation GUI regression now explicitly waits until metadata scans settle before Undo and passes in that supported test condition. This UI/selection change does not claim to fix concurrent-scan Undo. Wait for scans to finish before Undo pending a separate fix.

## Preservation

Final Desktop review: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.7.2-English-Review-20261020-212650.exe`. SHA256 `c8d9f7197ff33a126d8b5a517f28f949bd042fcc82cce370f79f124c538d4b10`. Frozen main/transfer modules match maintained source exactly; all 43 embedded locale files match, including reorganised English Help. Isolated packaged startup stayed alive for 15 seconds with empty stderr. GUI layout suite: 50 checks; upgrade suite: 21 checks; English Help/scan/sort/Smart Collections smoke passed. See JSON reports for precise scope. Final source snapshot target: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-12.7.2-final\source` (verification result must be checked separately).

Verified baseline before 12.7.2: `F:\Resolution File Manager project\Recovery Backups\2026-10-20-before-12.7.2-selection\source`. Additional verified working-source snapshot before checkbox changes: `...\2026-10-20-before-12.7.2-checkbox-accuracy\source-stable`. The earlier sibling `source` snapshot in that second folder was rejected because a derived manual changed while copying; do not treat it as verified. Older Desktop versions and intermediate builds are preserved. Final verified snapshot/build evidence will be saved after packaging completes.
