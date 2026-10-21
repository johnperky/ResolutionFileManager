# Folder organisation rules Help update — 21 October 2026

Windows version stays **12.7.10**, as requested. No app behaviour, UI labels or layouts changed; no Store screenshots regenerated. The existing published Windows EXE and GitHub assets remain intact. Store preparation was paused before uploads or submission.

## Expanded guidance

The chapter now explains the purpose and limits of rules, AND conditions, literal filename matching (including extensions, excluding parent folders), displayed codec labels and punctuation, manually assigned minimum star ratings, exact case-insensitive local tags, tag-list replacement, first-match precedence, preview scope, fixed destinations, preserved subfolders and troubleshooting. It retains the original instructions/MP4 example and adds four worked examples: project videos, favourite holiday photos, HEVC copies and a combined approved-project rule.

Only 11 added paragraphs were translated into the other 42 languages using the existing glossary/cache. Literal example values are protected from translation so the suggested search still matches its filename/tag. All UI dictionaries, the other 21 Help chapters and four original rule paragraphs were verified unchanged. Total: 22 chapters / 145 paragraphs in all 43 languages. Translations still need human linguistic proofreading; structural validation is not that review.

## Verified checks

- 43-language Help validation: zero errors and zero review flags.
- 18 Help integrity/translation/validator tests pass, including quoted-example preservation.
- 19 actual rule-matching/order/destination assertions pass without executing transfers.
- English/German/Arabic/Japanese source-native Help/navigation/search checks pass.
- A separate Windows build was made from tag `v12.7.10` plus the updated Help resources; this deliberately excludes Linux 12.7.11 application changes. All six application modules match the published Windows binary after ignoring compile-time source paths. All 43 embedded locale resources match this revision, and their UI/other chapters match the published binary.
- Actual revised packaged process stayed alive for 15 seconds with isolated settings and no stderr. This is startup evidence, not a claim of exhaustive binary visual review.

## Files and next use

- English chapter: `docs/help/ENGLISH_MANUAL.md`, “Folder Organization Rules”; authoritative structured master: `docs/help/en.json`.
- Retained updater: `tools/expand_folder_rules_help.py`; incremental translation helper: `tools/translate_help.py`.
- New candidate: `dist/help-review-12.7.10/ResolutionFileManager-v12.7.10-Help-Review.exe`.
- Candidate SHA-256: `ecc2b624c556aa923bcb132e937b3600abb11bdcc8b6a94a5d2e8f997f004419`.
- Published original remains `f1424ea2b42efb8586886d8721ea2864e40bb9df1cdafe8aef1ec7ae3ac6d22f`.
- Evidence: `docs/FOLDER_RULES_HELP_REVISION_12.7.10.json` and `docs/HELP_FOLDER_RULES_VALIDATION.json`.
- Isolated build source: project-parent `Store Preparation 12.7.10/Help Revision Source`; backups/logs: `Recovery Backups/2026-10-21-before-folder-rules-help` and `folder-rules-help-*`.

When Store preparation resumes, use this Help revision, retaining the same 12.7.10 application version and approved 172 screenshots. It still needs its own MSIX packaging/content verification; never substitute the original hash or claim the old readiness record covers different bytes. Do not replace published GitHub assets silently. The Linux candidate has not been rebuilt with this Help update.

Partner Center inspection before the pause showed Submission 8 available in Store and a Start update button, rather than the previously recorded draft. No new update was started; the exact live package version was not established.
