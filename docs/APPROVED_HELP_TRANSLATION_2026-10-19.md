# Approved Help translation — scheduled 19:41, 19 October 2026

Authoritative project: F:\Resolution File Manager project\ResolutionFileManager-Project-v6.
Approved English: docs/help/en.json, SHA-256 2b303fa46c4e5dc0dc0f1e8939cc9ce176d81de08fb98206e1d6aaab2c2965b7.
22 chapters; Topic Index second; Glossary second-last; Support the Project last with merged reminder guidance. Removed developer/legal/troubleshooting chapters must not return.

Pre-change verified 167-file snapshot and ZIP: F:\Resolution File Manager project\Recovery Backups\2026-10-19-1941-before-approved-help-translations. This protects the approved English, all interface dictionaries and previous Help translations.

Execution: Help-only translator uses Bing and six workers. Current locale paragraphs with matching source hashes override older machine caches, including moved paragraphs, preserving previous review corrections. No interface translation or English rewrite is authorised. All new paragraphs must be fully translated; no summaries.

Ruling: the historical guide remains archived, but the live manual follows the user's approved removals/order, not the original 12.3.0 chapter positions. The obsolete historical-order assertion was removed; archive checksum, current-master completeness and real chapter navigation remain tested. Fixed validator language-subset handling after a regression test failed with 42 unwanted language errors and passed after the fix.

## Verified final results

- All 42 other languages updated; all 43 packs contain the approved 22 chapters and 125 paragraphs in the approved order. No deleted chapters returned.
- Approved English master, readable manual and runtime English are byte-identical to the protected snapshot. media_sorter.py, localization.py and rtl_display.py are also byte-identical. All 43 UI strings/literals dictionaries remain logically identical.
- Full validator: 43 languages, zero errors, zero review flags. It now rejects missing/reordered numbered instructions as well as missing paragraphs, links, stale hashes, English residue and bidi problems. Native Bengali/Persian/Urdu numerals and Urdu punctuation are allowed.
- Regression suite: 62 tests passed. New tests reproduce service-caused joined glossary labels/steps, protect decimals and codec names, retain natural inflections/compounds, and prove requested language subsets are respected. The approved historical archive remains intact; removed developer/legal chapters are not requirements for the current live guide.
- Source application: all 43 language selections passed real-Tk scanning, sorting, Smart Collections, all Help chapter navigation, clickable index, search/highlights and RTL-alignment tests. French, German, Arabic, Finnish, Thai and Greek were rechecked after final text/formatting corrections.
- Targeted Finnish synchronization and Thai contact-sheet paragraphs were translated one instruction at a time after the service dropped step numbers. Arabic conversion steps and representative French/Greek wording received additional corrections. UI dictionaries were not changed. Arrow-button symbols were restored where the service damaged them.
- Windows build succeeded from maintained F: source. The packaged archive was compared with every current locale JSON: exact matches for all 43. The isolated executable startup check ran 30 seconds with no stderr or early exit.
- No Linux rebuild, Store work/screenshots, public release, Git commit or push. Older/open executables remain untouched.

**Use this final Desktop review build:**
`C:\Users\johnp\Desktop\ResolutionFileManager-v12.6.1-Updated-Help-43-Languages-Final.exe`

SHA-256: `b77c08f2c65f1ecbe3743d553acec45e18b24266923457c5196c409bd11b6a67`.

Reports: HELP_VALIDATION_APPROVED_2026-10-19.json, GUI_SMOKE_APPROVED_HELP_WINDOWS_2026-10-19.json, GUI_SMOKE_APPROVED_HELP_FINAL_QA.json and BINARY_SMOKE_APPROVED_HELP_FINAL_WINDOWS.json. Canonical HELP_VALIDATION.json is current too.

## Review scope and limitations

Translations use machine translation, the existing UI terminology and targeted corrections, not professional native-speaker proofreading in all languages. Automated completeness/format checks cannot certify every nuance. Arabic was visually checked for connected text, a right-hand chapter pane and separate numbered instructions. The existing Windows Tk bidi renderer was preserved; long mixed RTL/LTR wrapping and native-language typography remain review items rather than a claim of perfect presentation on every screen/font. No Store-ready linguistic or universal RTL certification is claimed.

Source backup/snapshot: `F:\Resolution File Manager project\Recovery Backups\2026-10-19-approved-help-43-languages-final` and its ZIP. Final snapshot verification and independent C: archive hash comparison must succeed before reporting backup completion. Existing before/after snapshots are never overwritten.
