# Resolution File Manager recovery report — 19 October 2026

## Authoritative project and audit findings

`F:\Resolution File Manager project\ResolutionFileManager-Project-v6` is the maintained shared Windows/Linux project, now **12.6.1**. The historical folder name is retained to preserve working paths. Desktop source is a junction to this location.

Pre-edit F: source was already 12.6.0 with all 43 languages. An independent real C: Desktop/project backup copy contained identical main source. No newer source was found in the inspected Codex worktrees, temporary, release or staging locations. The audit records paths, dates, versions and hashes; it does not claim every file on every drive was searched.

The apparent missing updates had identifiable causes:

- Separate Linux/ChatGPT handoffs remained 12.3.0; old root EXEs and release folders obscured the current development version.
- Release source exports used an obsolete fixed file list, omitting localisation/reminder modules, locales, validators, tests and documentation. Linux exports were manual, and run_linux.sh was ignored.
- GitHub lacked local commits and later uncommitted files. Local main 105bd9c is eight commits ahead of origin/main; the other localisation branch remains intact. This was a checkpoint/publishing gap, not absent Windows source.
- The original detailed English guide still existed in media_sorter.py. Six short localised summaries overrode its presentation. Chapter-count-only checks could not detect missing detail.

## Preservation and maintenance repairs

Before edits, separate labelled Windows development, F: project, Linux 12.3.0 and Help/translation snapshots were created under `F:\Resolution File Manager project\Recovery Backups\2026-10-19-before-help-recovery`. Verification hashed **1,314 files**, checked Git history availability, identical Windows/F source and all 43 locale packs. Original old releases, handoffs, version-11-era backup and independent C: backup remain preserved.

The established source layout is retained. Source exports now include tracked and untracked non-ignored source plus essential-file checks, SHA-256 manifests, post-copy verification and detection of source changes during copying. Snapshot/release destinations cannot be silently overwritten. Both builders validate full Help. Platform build/output directories are separated. Every Windows build makes a fresh versioned Desktop EXE.

`DEVELOPMENT_WORKFLOW.md` records: develop here; test; verify an F: snapshot; review/commit with approval; build both platforms; prepare releases; publish only after approval. Git bundles protect history; separate snapshots protect uncommitted files. No older directory was copied wholesale over the current source.

## English Help and Smart Collections

Recovery source: verified GitHub/origin commit `835ab63bab795cffde8f8db0804267796cfed397` (12.3.0). Its **30,849-character, 15-chapter** guide was recovered selectively. Version 11 was not needed. Application code was not replaced with 12.3.0.

`docs/help/recovered-12.3.0-en.txt` preserves the original. `docs/help/en.json` is the authoritative paragraph-addressable master; `docs/help/ENGLISH_MANUAL.md` is readable. The restored guide now has **19 chapters / 114 paragraphs**, preserving original detailed instructions/examples, newer language/reminder/tick functionality and current compatibility clarifications. Chapter navigation, clickable topic index, full-text search, highlights and Next match work.

Smart Collections instructions now explain saved searches versus folders, references to originals, choosing one root/recursive subfolders, stored settings, creating/saving/applying/editing/renaming/deleting/restoring, results and refresh. Examples use actual image/video resolution sorting and codec filters.

Limitations are explicit: no combining unrelated roots/drives; no automatic file movement; no frozen results; ticks/highlight/preview/live state, column layout and page capacity are not collection settings. Resolution sorting uses pixel area; width/height minima both apply; codec search uses the displayed label (H.264). Delete undo lasts only while the manager stays open; same-name replacement behaviour is explained. Actual methods and missing-folder handling were tested with disposable media; originals were unchanged.

Schema/hash/paragraph checks prevent stale chapters or summaries from hiding full English. The locale generator cannot replace schema-2 Help wholesale; builders fail on incomplete Help. Future changes must edit the English master, preserving IDs and full instructions.

## All 43 languages

Every supported language now contains all 19 chapters and 114 paragraphs, with detailed examples and expanded Smart Collections. Existing UI strings/literals were compared with pre-edit backups: **43 unchanged; zero changed**. The UI was not retranslated.

`HELP_VALIDATION.json`: **43 languages, 0 errors, 0 review flags**. Checks cover IDs/order, hashes, empty entries, suspicious length, English residue, references/placeholders, chapter links, direction and balanced bidi controls. Compact languages use appropriate thresholds. Mutation tests reject missing, empty, summarised, English, broken-link and broken-bidi examples.

Translations are machine translated with terminology alignment and targeted corrections, not professionally proofread in every language. Structural completeness cannot guarantee perfect meaning/fluency; native-speaker review remains desirable.

Linux Tk 8.6 initially showed disconnected/backwards Arabic. A Linux-only display adapter now shapes/orders RTL while preserving logical dictionary text. Wrapping precedes bidi conversion; character mappings preserve Help search highlights and links. Windows native rendering is unchanged. RTL Help has right alignment, a right-hand chapter pane and horizontally scrollable long titles. Arabic Help and the Linux packaged interface were visually reviewed. Hebrew/Urdu/Persian also passed automated tests; every screen in all languages was not visually certified. Editable RTL fields and desktop integration need further real-user review.

## Verification

| Check | Windows | Local Ubuntu Linux |
|---|---|---|
| Regression tests | 51 passed | 51 passed |
| Source GUI language selections | 43/43 passed | 43/43 passed |
| Recursive media, image/video sorting, collections | Passed fixtures | Passed fixtures |
| All Help chapters, index links, search | Passed per-language checks | Passed per-language checks |
| Real probe, integrity, software conversion/remux/cancel | Passed | Passed |
| Packaged 12.6.1 build | Successful | Successful |
| Packaged startup | 120 seconds, no stderr; visible window | 120 seconds, no stderr; visible Arabic window |
| Embedded resources | 43 locales and RTL modules | 43 locales and RTL modules |

Windows: Python 3.14.3 / PyInstaller 6.22.2. Linux: local WSL Ubuntu 24.04 x86_64, Python 3.12.3 / PyInstaller 6.22.3, glibc 2.39, FFmpeg 6.1.1-3ubuntu5. Both build from the same F: source. Linux uses an isolated venv, not system pip/--break-system-packages. No laptop was accessed.

Reports: GUI_SMOKE_WINDOWS.json, GUI_SMOKE_LINUX.json, BINARY_SMOKE_WINDOWS.json and BINARY_SMOKE_LINUX.json. Source integration tests exercise functionality; packaged tests establish startup/liveness/resource inclusion, not a second full 43-language run inside each binary. `git diff --check` passed with ordinary line-ending conversion warnings.

Windows: `dist/ResolutionFileManager.exe`, SHA-256 `3e098402a965c8a071ec97fe99813a15b8a34028351fe7516589cd90d752aed1`. Fresh Desktop copy: `C:\Users\johnp\Desktop\ResolutionFileManager-v12.6.1.exe`.

Linux: `dist/linux/ResolutionFileManager-v12.6.1-linux-x86_64`, SHA-256 `a291fc2eb208ffd56790f68c525fcc6bff7771af2be3e166f0a11dcfb393777f`.

### Untested / remaining limitations

Mint itself, Vostro/laptop, older glibc, another architecture, desktop drag/drop, audio, Trash/file-manager integration and GPU encoding/decoding were not tested. Build on the oldest target Linux baseline and test its real desktop/drivers. Bundled FFmpeg/system shared-library and licence/source obligations require review before public Linux redistribution. Linux is current and tested on the stated Ubuntu environment, not certified for every Mint PC. No claim of universally portable Linux binaries is made.

## Git and publication

GitHub remains 12.3.0. No commit, push, public release, Store screenshot, listing change or Store submission occurred. All pre-existing modified/untracked work was preserved. `python tools/project_snapshot.py candidates` gives the complete source set for future review; caches, environments, generated specs/builds/dist/releases are excluded. Existing marketing/Store assets are preserved, not republished. Review unrelated pre-existing changes separately; do not stage everything blindly.

## Final export record

Source/release/handoff manifests and independent backup verification are recorded in `RECOVERY_EXPORT_VERIFICATION.json` after packaging. If absent, use RECOVERY_CHECKPOINT.md to finish the final stage; a folder alone does not prove successful export.

The Windows source release and Linux handoff contain identical 165-file source manifests, including all application modules, 43 locales, English master, tests and both builders. The subsequent final-source snapshot includes the added export-verification helper. The completed-source snapshot additionally retains final reporting/checkpoint updates. They are separately labelled checkpoints, not silent replacements of older snapshots. The independently copied completed-source ZIP and Git bundle are under `C:\Users\johnp\Desktop\project backup\RFM-recovery-2026-10-19-v12.6.1`. The generated verification report is necessarily written after the snapshots it verifies and is also copied beside the recovery archives.
