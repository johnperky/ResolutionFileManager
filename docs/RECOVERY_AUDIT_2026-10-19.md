# Development and recovery audit — 19 October 2026

## Authoritative source and evidence before edits

`F:\Resolution File Manager project\ResolutionFileManager-Project-v6` is the working directory and authoritative Windows 12.6.0 source. It contains 43 locale JSON files, localisation/reminder modules, tests, icons and Windows/Linux builders. `C:\Users\johnp\Desktop\ResolutionFileManager-Project-v6` is a junction to this exact directory. Both media_sorter.py hashes were C5177E0A72F66CA2BB38B742228ADE60E09AD9927D21CD6522D557B93AAFE487. There is no evidence of newer source in the searched Codex worktrees or Temp locations. The misleading v6 folder name is historical; retain its established path.

The separate F: ChatGPT handoff and `F:\ResolutionFileManager-Linux-Handoff-12.3.0` both contain 12.3.0 media_sorter.py (FB846D1B515E8AD027953AABC0118ACED4C4A97E28C850C3473957A553C02395) with no locale packs. The old Linux workspace and Desktop relocation backup are 12.1.1. The explicitly labelled old F: backup is 11.7.2. Preserve all of them.

Additional source/release audit: the real C: `Desktop/project backup/Resolution File Manager project/ResolutionFileManager-Project-v6` copy is also 12.6.0 with the exact same pre-edit main-source hash as F:. Its Linux/ChatGPT handoffs are 12.3.0. Both C: and F: release-output folders retain 12.2.2 and 12.3.0 source distributions; their main files match their respective public versions. No newer source was found in the inspected staging/release directories. This C: backup provides an independent original copy; it was not overwritten.

Local main is 105bd9c (12.4.0 commit), eight commits ahead of origin/main. The remote HEAD was independently checked with git ls-remote: 835ab63bab795cffde8f8db0804267796cfed397, release 12.3.0. Branch codex/localisation-reminders-12-4 is c946ec0. All 12.4.1–12.6.0 development is present as modified/untracked files, including 33 additional locale files, tools and tests. No push, commit or history replacement is authorised during this repair.

## Established causes

- F: source **has** been maintained; stale copies/handoffs and executables obscure that fact. The root ResolutionFileManager.exe is dated 30 September, while dist and Desktop have the new 12.6.0 build. Do not replace old files silently.
- GitHub lacks local commits and later uncommitted files. This is a publishing/checkpoint gap, not proof of missing Windows source.
- Linux handoff is a manually copied snapshot. No automatic export validates it against current source.
- build_windows_release.ps1 uses an obsolete fixed source list that omits localisation.py, reminder_policy.py, verify_release_assets.py, locales, tests and help resources. Its old behaviour also deletes an existing versioned release directory.
- .gitignore hides run_linux.sh (untracked) and states Linux is intentionally outside the Windows release. Windows and Linux otherwise use the same Python application.
- The full English guide in current media_sorter.py is byte-for-byte equal to GitHub 12.3.0's guide: 30,849 characters, 15 chapters. Translator.help_chapters() replaces it with six very short locale summaries. Thus documentation was hidden by the localisation overlay, not destroyed.
- The old translation generator checks only chapter count, which cannot detect summarisation or omitted paragraphs.

## Backups completed before source edits

Sibling folder `F:\Resolution File Manager project\Recovery Backups\2026-10-19-before-help-recovery` contains separately labelled Latest-Windows-Source-12.6.0, Existing-F-Project-12.6.0, Existing-Linux-Source-12.3.0, and Help-and-Translations-12.6.0 snapshots. Windows/F snapshots include .git and all source/resources, excluding regenerable build, dist, venv, cache and smoke/test-state directories. Existing compiled releases remain in their original locations; root historic executables were copied with source. The two Windows source snapshots intentionally duplicate the same physical source because Desktop and F: resolve to one project. Main-source hashes verified equal after copying. Full file verification is recorded separately by the backup tooling.

## Build/testing environment

Windows Python 3.14/PyInstaller and FFmpeg are installed. Local WSL Ubuntu x86_64 with Python 3.12 is available. Linux dependencies and isolated build environment may be installed locally; no laptop connection is involved. Ubuntu/WSL success does not prove compatibility with every Mint release or standalone PC: document the tested environment and shared-library limits.

## Store work

No RFM Store-preparation automation was created: the earlier scheduling call failed validation. Only unrelated RapidClips automations exist. This task must perform no Store changes, screenshots or publication.
