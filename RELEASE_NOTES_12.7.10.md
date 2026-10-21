# Resolution File Manager 12.7.10 — Windows

## Accessibility and layout corrections

- Added Tools > Show hidden files, a persistent toggle for hidden media/files and folders in both panes. Normal filters still apply; the Store capture runner keeps hidden files off without adding a main-window control.

- Scan status and Cancel retain their own row and space when text is enlarged or the window narrows.
- Enlarged text wraps the top guide while preserving full toolbar action buttons.
- File rows and column headings follow interface text scaling without cutting off enlarged text.
- Read-only dropdowns use readable colours in Dark and High contrast themes.
- Enlarged conversion settings retain full selector widths in a scrollable area; conversion actions remain visible. The appearance dialog fits its controls after changing text size.
- Retains pixel-measured translated conversion choices and scrollable Info metadata with reserved action buttons in short browsers.

## Changes since the previous public Windows release, 12.3.0

- Expanded interface and Help to 43 languages, including RTL presentation and regional language detection. Serbian uses Cyrillic.
- Added and improved the selection basket, tick/highlight separation, drag/drop Copy/Move/Cancel prompt and transfer previews.
- Improved queued transfers and asynchronous, resumable Undo coordination with background media readers.
- Preserved and expanded Help to 22 chapters and 134 paragraphs per language, with navigation, search and a clickable topic index.
- Localised conversion choices/statuses, tick counters and new controls; fitted translated headings while retaining manual column resizing.

The Windows portable package includes the executable, source archive, licence/notices and SHA-256 checksums. Settings and caches stay local; media remains on the computer. Existing media operations retain their review/confirmation workflows.

Linux's latest verified binary remains 12.6.1; this Windows release does not update Linux. No Microsoft Store submission is included. The Windows executable is unsigned; verify its checksum against the official release assets.

Validation used the current Windows 11 host with isolated settings and a system-only PATH, plus matching-source native UI checks. A separate clean OS and Windows 10 were not tested.
