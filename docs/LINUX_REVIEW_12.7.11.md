# Linux 12.7.11 review candidate — 21 October 2026

**Target:** x86_64 Linux Mint 22.x / Ubuntu 24.04; built with Python 3.12 and PyInstaller 6.22.3 on Ubuntu 24.04 under WSL. Physical Mint desktop compatibility remains unverified. Windows remains the published 12.7.10 release.

## Completed

- Current application, 43 translations and complete Help built for Linux. Persistent hidden-files toggle, transfer/Undo and existing features preserved.
- Top toolbar actions wrap when Linux fonts exceed available width, returning to the compact layout after scaling down.
- At the user's request, Linux offers 100/125/150/175%; 200% is omitted and old saved 200% returns to 100%. Windows retains 200%. Translated button names were preserved.
- Final Linux unit suite: 91 tests, 89 pass, two Windows-only skips. Windows: all 91 pass. Native Linux Appearance regression checks highest supported scale, Cancel/custom widths, toolbar actions and removed-scale fallback; hidden-files regression passed before the scale-only change.
- Earlier 43-language real-Tk scan/Help/navigation suite passed on the pre-scale-limit 12.7.11 source. Final source-native visual/toolbar pilot covers English, German, Arabic and Japanese at 100/175%. Do not describe the earlier suite as an exhaustive final-binary visual review.
- Final binary verified against six exact embedded modules, all 43 locales and English Help. Four isolated launches of the actual packaged binary with populated Arabic media completed without startup failure; one native packaged Arabic view inspected. This does not establish all feature/device compatibility.
- Reviewer found a Windows Sandbox JSON BOM issue; corrected to BOM-free UTF-8 and verified generated script syntax/configuration XML. The kit has **not** run in Sandbox.

## Exact candidate

- EXE-style Linux executable: `dist/linux/ResolutionFileManager-v12.7.11-linux-x86_64` (ELF, not a Windows EXE).
- Binary SHA-256: `a57a1d66d535870cb5f0ff8b6f852e6fdd762814961dc86cbb294785bd2f9a31`.
- Package: `release-output/12.7.11-linux-final-review/ResolutionFileManager-12.7.11-Linux-x86_64-review.tar.gz`.
- Archive SHA-256: `41e362e80f8d55db8e9a7b57e221dadf6b8221df7c0b95b74245ac4e10174346`.
- Package preserves binary bytes, executable permissions, launcher, privacy/licensing, installed Python component notices and 189 Ubuntu package notices/source-version records. Install system FFmpeg and Noto fonts as documented in `LINUX_INSTALL.txt`; this is not a universally dependency-free Linux binary.
- Earlier Linux 12.6.1, 12.7.10 and pre-scale-limit 12.7.11 binaries/packages remain preserved. No Linux GitHub binary release or Store submission made.

## Outstanding / release gate

**readyForRelease: false (Linux)**. At 1300-pixel window width, some pane labels/buttons still clip at 175% (including English, German, Arabic and Japanese); Arabic/Japanese guide text also wraps excessively when action buttons leave too little space; removing 200% does not prove every remaining scale fits. The top toolbar itself fits. The final representative native images record this limitation; lower scales/wider windows may be preferable until addressed.

Test the candidate on the user's Mint 22.x computer: startup, video/audio, preview/Info, hidden-file persistence, resizing, Help, desktop drag/drop, Trash and hardware encoding if used. Test file operations only on disposable copies. A real Mint pass and resolution/review of remaining large-text clipping are required before calling it stable. Existing Help describes shared Windows scale choices; Linux's actual choices are recorded in installation/release notes.

## Efficient repeatable workflow

Reuse the existing Ubuntu build virtualenv and pinned dependencies; pilot English/German/Arabic/Japanese before a full language batch. Run each native visual locale in its own Xvfb process to avoid old Tk callback/font state carrying across applications. `tools/linux_visual_probe.py` saves native screenshots with isolated settings and synthetic images; it never operates on user media. `tools/package_linux_candidate.py` packages existing reviewed bytes without rebuilding. Preserve logs/images in the project-parent `Recovery Backups/Linux-12.7.11-evidence` folder. Rebuild invalidates prior binary hashes; do not relabel earlier evidence.
