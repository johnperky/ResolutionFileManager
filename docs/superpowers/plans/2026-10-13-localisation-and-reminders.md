# Localisation and Reminders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release Resolution File Manager 12.4.0 with automatic OS-language detection, nine complete interface/help languages, and private locally scheduled Microsoft Store rating and Buy Me a Coffee reminders.

**Architecture:** Add two independently testable modules: `localization.py` owns locale selection, pack loading and English fallback; `reminder_policy.py` owns launch history and reminder eligibility without importing Tk. `media_sorter.py` consumes both modules for translated widgets/dialogs/help and schedules at most one post-startup reminder. UTF-8 JSON packs remain editable assets bundled into both one-file builds.

**Tech Stack:** Python 3, Tkinter/ttk, JSON, `unittest`, PyInstaller, PowerShell and POSIX shell build scripts.

**Spec:** `docs/superpowers/specs/2026-10-13-localisation-and-reminders-design.md`

## Global Constraints

- Preserve all version 12.3.0 behaviour; its executable remains the rollback.
- Supported interface languages are English, Simplified Chinese, Dutch, French, German, Japanese, Korean, Russian and Spanish.
- English (India) uses English; unsupported, missing or malformed locales fall back to English.
- A language change takes effect after restart; do not partially rebuild the live interface.
- Rating eligibility begins at five successful launches across three distinct dates; Later postpones ten launches.
- Support eligibility begins at launch 11; Maybe later postpones 11 launches.
- Display at most one reminder per launch, with rating priority and preserved support eligibility.
- All counters and preferences remain local; no analytics or completion tracking may be added.
- All new production behaviour is developed test-first.
- Every behaviour change must be reflected in the in-app Help Centre.
- A successful Windows build must copy `ResolutionFileManager-v12.4.0.exe` to the user's Desktop.

## Review Focus

- Corrupt or partially written settings and locale files must not prevent startup; tests in Tasks 1 and 3 pin the fallback.
- Regional locale formats (`de_AT`, `zh-Hans-CN`, Windows locale aliases, absent locale) must resolve deterministically; Task 1 tests each class.
- Translation placeholders must neither crash nor silently substitute the wrong named value; Task 1 tests missing and extra arguments.
- Closing a reminder must postpone it, and simultaneous eligibility must not discard the support reminder; Task 3 tests both paths.
- PyInstaller one-file execution must find all locale assets outside the source checkout; Task 5 adds packaging assertions and Task 6 exercises the built executable.

---

### Task 1: Localisation Core and Canonical English Pack

**Files:**
- Create: `localization.py`
- Create: `locales/en.json`
- Create: `test_localization.py`

**Interfaces:**
- Produces: `SUPPORTED_LANGUAGES: dict[str, str]`
- Produces: `normalise_locale(value: str | None) -> str`
- Produces: `select_language(saved: str | None, system_locale: str | None) -> str`
- Produces: `class Translator` with `Translator(locale_dir: Path, language: str)`, `text(key: str, **values) -> str`, `language`, `diagnostics`, and `help_chapters() -> list[tuple[str, str]]`
- Consumes later: `media_sorter.MediaSorterApp` creates one translator before constructing widgets.

- [ ] **Step 1: Write failing locale-selection tests**

Add tests for base and regional forms (`de-AT`, `de_AT`, `es-MX`, `zh-Hans-CN`, `en-IN`), an unsupported locale, an empty locale and a saved override including `system`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest -v test_localization.LocalizationSelectionTests`

Expected: FAIL because `localization` and its public functions do not exist.

- [ ] **Step 3: Implement locale normalisation and selection**

Implement only the mapping and override rules required by the tests. Use canonical codes `en`, `zh-CN`, `nl`, `fr`, `de`, `ja`, `ko`, `ru`, and `es`.

- [ ] **Step 4: Run selection tests and verify GREEN**

Run: `python -m unittest -v test_localization.LocalizationSelectionTests`

Expected: all selection tests pass.

- [ ] **Step 5: Write failing pack/fallback/interpolation tests**

Test valid pack loading, absent and malformed non-English packs, blank/missing translated values, missing English keys, named interpolation, missing required placeholders, extra values, diagnostics, and ordered help chapters.

- [ ] **Step 6: Run pack tests and verify RED**

Run: `python -m unittest -v test_localization.TranslatorTests`

Expected: FAIL because `Translator` and the canonical pack behaviour are incomplete.

- [ ] **Step 7: Implement `Translator` and the canonical English structure**

Store flat UI keys plus a `help.chapters` ordered array in `locales/en.json`. Load English first, overlay the selected pack, and catch file, decode, type and formatting failures into `diagnostics` while returning a safe English value.

- [ ] **Step 8: Run localisation tests and the existing suite**

Run: `python -m unittest -v test_localization && python -m unittest discover -v`

Expected: all tests pass.

- [ ] **Step 9: Commit Task 1**

Commit: `feat: add localisation core and English pack`

### Task 2: Complete Nine-Language Pack Set

**Files:**
- Create: `locales/zh-CN.json`
- Create: `locales/nl.json`
- Create: `locales/fr.json`
- Create: `locales/de.json`
- Create: `locales/ja.json`
- Create: `locales/ko.json`
- Create: `locales/ru.json`
- Create: `locales/es.json`
- Create: `test_locale_packs.py`
- Modify: `locales/en.json`

**Interfaces:**
- Consumes: canonical keys and `help.chapters` schema from Task 1.
- Produces: complete UTF-8 packs with identical required keys and named placeholders.

- [ ] **Step 1: Write failing pack-parity tests**

Assert all nine files load as JSON objects, every required English UI key is present and nonblank, help chapter identifiers and order match English, named placeholder sets match the English value, and no pack contains unknown top-level structures.

- [ ] **Step 2: Run parity tests and verify RED**

Run: `python -m unittest -v test_locale_packs`

Expected: FAIL listing the eight absent packs and untranslated keys.

- [ ] **Step 3: Add all translated UI and Help content**

Translate user-facing prose while retaining codec names, extensions, paths, keyboard keys, URLs, placeholder names and user-authored values. Include the Language and Reminders guidance required by the specification.

- [ ] **Step 4: Run parity and localisation tests**

Run: `python -m unittest -v test_locale_packs test_localization`

Expected: all tests pass with valid UTF-8 and exact key/placeholder parity.

- [ ] **Step 5: Perform human-readable translation checks**

Inspect every pack for accidental English UI prose (excluding approved technical terms), mojibake, mistranslated product/codec names, overlong menu labels and inconsistent terminology.

- [ ] **Step 6: Commit Task 2**

Commit: `feat: add nine complete language packs`

### Task 3: Reminder Policy and Persistent State

**Files:**
- Create: `reminder_policy.py`
- Create: `test_reminder_policy.py`

**Interfaces:**
- Produces: `record_successful_launch(state: dict, today: date) -> dict`
- Produces: `eligible_reminder(state: dict) -> Literal["rating", "support"] | None`
- Produces: `apply_reminder_choice(state: dict, reminder: str, choice: str) -> dict`
- Produces: `set_reminder_enabled(state: dict, reminder: str, enabled: bool) -> dict`
- State keys are namespaced under `reminders` when merged into application settings.

- [ ] **Step 1: Write failing launch-history and migration tests**

Cover one increment per successful launch, repeated same-day launches, three distinct dates, malformed values, bounded date history, preservation of unrelated settings and fresh defaults for older settings.

- [ ] **Step 2: Run history tests and verify RED**

Run: `python -m unittest -v test_reminder_policy.ReminderHistoryTests`

Expected: FAIL because the reminder module does not exist.

- [ ] **Step 3: Implement state normalisation and launch recording**

Return new dictionaries rather than mutating callers. Preserve only the dates needed to establish the three-day threshold.

- [ ] **Step 4: Run history tests and verify GREEN**

Run: `python -m unittest -v test_reminder_policy.ReminderHistoryTests`

Expected: all history tests pass.

- [ ] **Step 5: Write failing eligibility and choice tests**

Cover rating launch/date thresholds, support launch 11, rating priority, preserved support eligibility, ten/11-launch postponement, closing-as-later, button completion, permanent dismissal and re-enable scheduling.

- [ ] **Step 6: Run policy tests and verify RED**

Run: `python -m unittest -v test_reminder_policy.ReminderPolicyTests`

Expected: FAIL on missing eligibility and choice behaviour.

- [ ] **Step 7: Implement the minimal reminder state machine**

Use explicit integer next-launch thresholds and disabled booleans. Re-enabling schedules from the current count and never fabricates distinct dates.

- [ ] **Step 8: Run reminder tests and the whole suite**

Run: `python -m unittest -v test_reminder_policy && python -m unittest discover -v`

Expected: all tests pass.

- [ ] **Step 9: Commit Task 3**

Commit: `feat: add private reminder scheduling policy`

### Task 4: Integrate Localisation Throughout the Tk Application

**Files:**
- Modify: `media_sorter.py`
- Create: `test_app_integration.py`
- Modify: `locales/*.json`

**Interfaces:**
- Consumes: `Translator`, `select_language`, and all reminder-policy functions.
- Produces: `MediaSorterApp.tr(key: str, **values) -> str`
- Produces: `MediaSorterApp.language_controls()`, `reminder_controls()`, `schedule_startup_reminder()`, `show_rating_reminder()`, and `show_support_reminder()`.

- [ ] **Step 1: Write failing non-GUI integration tests**

Extract/test helpers for merging localisation/reminder settings without dropping geometry, panes or performance keys; selecting the packaged locale directory under source and PyInstaller `_MEIPASS`; and generating the Windows Store URI plus HTTPS fallback.

- [ ] **Step 2: Run integration tests and verify RED**

Run: `python -m unittest -v test_app_integration`

Expected: FAIL because application integration helpers are absent.

- [ ] **Step 3: Initialise translation and reminder state before widget creation**

Determine the effective locale from `settings["language"]` and the system locale, create `Translator`, record one successful launch only after the main UI is initialised, and preserve the complete pre-existing settings dictionary when saving new state.

- [ ] **Step 4: Route all visible interface text through stable translation keys**

Cover top-level menus, toolbar, both `FilePane` instances, `PreviewPane`, columns, thumbnail controls, context menus, every tool/dialog, progress/status/error text, About, shortcuts and Help Centre. Pass the translator or a callable into child components rather than importing global mutable language state.

- [ ] **Step 5: Add Tools > Language and Tools > Reminders**

Language offers System default and all nine language names, saves the override, and explains the restart requirement in the current language. Reminders independently reports, disables and re-enables rating/support prompts using the policy module.

- [ ] **Step 6: Add post-startup reminder dialogs and safe link opening**

Schedule evaluation with `after` once startup layout work is complete. Each custom modal has the exact three choices from the spec; window close maps to postponement. Use `ms-windows-store://pdp/?productid=9NZL6GF5JSJK`, HTTPS fallback, and existing browser behaviour for Buy Me a Coffee. Persist each choice immediately and never show both prompts in one launch.

- [ ] **Step 7: Replace embedded English Help prose with active-pack chapters**

Keep the established searchable contents, chapter navigation and highlighting UI. Ensure the new language/reminder/privacy guidance is present in every pack.

- [ ] **Step 8: Run focused and full automated tests**

Run: `python -m unittest -v test_app_integration test_localization test_locale_packs test_reminder_policy && python -m unittest discover -v`

Expected: all tests pass without Tk tracebacks.

- [ ] **Step 9: Manually smoke-test source mode**

Launch with English, German, Japanese and an unsupported locale; change language and restart; search translated Help; open Reminders; simulate eligible states using an isolated temporary settings directory; verify only one translated prompt appears and each link requires an explicit click.

- [ ] **Step 10: Commit Task 4**

Commit: `feat: localise interface and add reminder controls`

### Task 5: Package Locale Assets and Advance Release Metadata

**Files:**
- Modify: `build_windows.ps1`
- Modify: `build_linux.sh`
- Create: `test_packaging_assets.py`
- Modify: `media_sorter.py`
- Modify: `VERSION.txt`
- Create: `RELEASE_NOTES_12.4.0.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `packaging/microsoft-store/README.md`

**Interfaces:**
- Consumes: complete `locales` directory from Tasks 1–2.
- Produces: PyInstaller builds containing `locales` and a consistent version `12.4.0` everywhere.

- [ ] **Step 1: Write failing packaging/version tests**

Assert both build scripts include the complete locale directory, require `locales/en.json`, and source/version/release documents consistently report 12.4.0.

- [ ] **Step 2: Run packaging tests and verify RED**

Run: `python -m unittest -v test_packaging_assets`

Expected: FAIL because builds do not include locales and the project still reports 12.3.0.

- [ ] **Step 3: Bundle and validate locale assets in both builds**

Add platform-correct PyInstaller `--add-data` arguments for the `locales` directory. Fail clearly before building if English or any declared supported pack is missing.

- [ ] **Step 4: Update version and documentation**

Set `APP_VERSION` and `VERSION.txt` to `12.4.0`; add release notes and document detection, overrides, restart, exact prompt schedules, controls, privacy, URLs, packaging and 12.3.0 rollback.

- [ ] **Step 5: Run packaging and full tests**

Run: `python -m unittest -v test_packaging_assets && python -m unittest discover -v`

Expected: all tests pass.

- [ ] **Step 6: Commit Task 5**

Commit: `release: prepare Resolution File Manager 12.4.0`

### Task 6: Full Verification and Windows Delivery

**Files:**
- Verify only unless a failing check requires a scoped fix.
- Output: `dist/ResolutionFileManager.exe`
- Output: `%USERPROFILE%\Desktop\ResolutionFileManager-12.4.0.exe`

**Interfaces:**
- Consumes: all completed tasks.
- Produces: verified source and packaged Windows application plus the required Desktop copy.

- [ ] **Step 1: Run syntax and complete automated verification**

Run: `python -m py_compile localization.py reminder_policy.py media_sorter.py && python -m unittest discover -v`

Expected: exit 0 with every test passing.

- [ ] **Step 2: Run clean Windows build**

Run: `powershell -ExecutionPolicy Bypass -File .\build_windows.ps1`

Expected: dependency and PyInstaller steps succeed, the output has a fresh timestamp, and the script reports both build and Desktop paths.

- [ ] **Step 3: Verify packaged assets and identity**

Confirm the executable starts without the source checkout, reports version 12.4.0, uses the application icon, loads a non-English locale, opens translated Help and retains all bundled FFmpeg tools.

- [ ] **Step 4: Verify reminder behaviour in an isolated packaged profile**

Exercise launch 5 across three dates, launch 11, Later/Maybe later, Don't ask again, re-enable controls, simultaneous eligibility and failure fallbacks without altering the user's normal settings.

- [ ] **Step 5: Verify preserved media workflows**

Smoke-test recursive scanning, Details/Thumbnails, previews, ticks, filters, copy/move/delete/undo, duplicate review and one short conversion. Confirm normal settings survive restart.

- [ ] **Step 6: Confirm deliverables and working-tree scope**

Check `VERSION.txt`, executable hashes/timestamps, Desktop filename, `git diff --check`, and `git status --short`. Report unrelated pre-existing Store/WinGet assets separately without modifying or committing them.

- [ ] **Step 7: Commit any verification-only corrections and tag the handoff state**

Commit only scoped corrections with an explanatory message; do not submit the Microsoft Store draft or publish externally without a separate explicit request.
