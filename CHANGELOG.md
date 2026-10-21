# Changelog

## 12.6.2 — 20 October 2026

- Use existing translated tick counters in both panes.
- Translate duplicate-output, same-source and skip-existing conversion-preview statuses.
- Fit translated column headings on language changes and width resets, while preserving later same-language custom widths and unrestricted mouse resizing.
- Preserve all existing Help content. Windows rebuild and 43-language GUI regression checks completed; no Linux binary rebuild or Store submission.

## 12.6.1 — 19 October 2026

- Restored the full 15-chapter English Help from the verified 12.3.0 repository and retained newer topics.
- Added detailed Smart Collections examples/limitations and a clickable topic index, bringing Help to 19 chapters.
- Added paragraph-level multilingual completeness checks and full-English fallback for incomplete Help.
- Improved RTL Help layout and scrolling for long chapter names.
- Repaired complete source snapshots, recoverable backups and cross-platform build/handoff verification; preserved older builds.

## 12.6.0 — 19 October 2026

- Expanded the fully localised interface and Help system to 43 selectable languages.
- Added Arabic, Vietnamese, Ukrainian, Norwegian, Finnish, Danish, Hungarian, Romanian, Czech, European Portuguese, Brazilian Portuguese, Turkish, Traditional Chinese, Malay, Hebrew, Bangla, Urdu, Persian, Slovak, Croatian, Serbian, Catalan, Estonian, Latvian and Lithuanian.
- Added regional operating-system language detection and Microsoft Store package declarations for every new language.

## 12.5.3 — 19 October 2026

- Added a complete Italian interface and Help language pack.
- Added automatic detection for Italian regional locales.
- Declared Italian support in the Microsoft Store package manifest and release validation.

## 12.5.2 — 16 October 2026

- Localised conversion presets, output resolution choices, automatic/software engine choices and queue states in all 17 interface languages.
- Localised option values in appearance, report export, integrity checking, similar-image search, folder rules and performance settings.
- Preserved stable internal option identifiers so translated choices do not alter saved settings or processing behaviour.

## 12.5.1 — 16 October 2026

- Localised every Advanced Filters control in all 17 supported languages.
- Reflowed filter controls and dynamically sized translated selectors to prevent clipping.
- Corrected visible Spanish and Filipino wording found during screenshot review.

## 12.5.0 — 16 October 2026

- Added complete Swedish, Bulgarian, Thai, Indonesian, Greek, Filipino, Hindi and Polish interface and Help translations.
- Added automatic regional-locale detection for all eight new languages.
- Expanded release validation and locale parity tests to cover every bundled language pack.

## 12.4.1 — 13 October 2026

- Corrected the Microsoft Store package so it contains the current multilingual executable.
- Added a build-time check that rejects stale executables before Store packaging.

## 12.4.0 — 13 October 2026

- Added automatic system-language detection and nine bundled interface/help languages.
- Added Tools > Language with a persistent override, System default restoration and safe English fallback.
- Added an optional Microsoft Store rating reminder after five launches across three dates; Later postpones it by ten launches.
- Added an optional Buy Me a Coffee reminder at launch 11 with an 11-launch Maybe later interval.
- Added Tools > Reminders to independently disable or re-enable both private, local-only reminders.
- Added build-time language-pack validation and bundled locale assets for Windows and Linux packages.

## 12.3.0 — 2 October 2026

- Added independent tick-box action groups to both browser panes.
- Details rows and thumbnail cards now expose clear ☐/☑ controls.
- Ticked files remain collected while other files are highlighted and previewed, and while sorting or filtering.
- The Details checkmark heading and the thumbnail “✓ All shown” control toggle the complete visible group.
- File actions use the ticked group when present and retain the established highlighted-row fallback when no files are ticked.
- Ticks are session-only, clear when their pane navigates to another folder, and are removed automatically when files disappear.

## 12.2.2 — 30 September 2026

- Added an optional “Buy John a coffee” entry to Help and the About window.
- The support page opens only following a direct user action.
- Added a copyable fallback address when the browser cannot be opened.
- Updated the searchable Help Centre with a Support the Project chapter.

## Earlier releases

The complete development history from version 6 through 12.3.0 is preserved in `PROJECT_CONTEXT.md` and the “What's new” chapters of `README.md`.
