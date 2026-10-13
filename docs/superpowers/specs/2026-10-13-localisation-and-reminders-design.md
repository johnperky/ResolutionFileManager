# Resolution File Manager 12.4.0 Localisation and Reminders Design

## Goal

Release Resolution File Manager 12.4.0 with a maintainable multilingual interface and two respectful, private, locally scheduled prompts: one inviting a Microsoft Store rating and one inviting optional support through Buy Me a Coffee.

The release must preserve all version 12.3.0 behaviour and remain reversible through the existing 12.3.0 executable.

## Supported languages

The application will ship with these interface languages:

- English
- Chinese (Simplified)
- Dutch
- French
- German
- Japanese
- Korean
- Russian
- Spanish

English (India) uses the English interface. On the first launch of 12.4.0, the application detects the operating-system display locale and selects the closest supported language. Regional variants map to their base supported language, for example `de-AT` to German and `es-MX` to Spanish. Unsupported and unreadable locales fall back to English.

The selected language is stored in the existing local settings file. A manual choice under **Tools > Language** overrides automatic detection on future launches. Selecting **System default** removes the override and restores locale detection. A language change displays a translated explanation and takes effect after the application is restarted; the running interface is not partially rebuilt.

## Localisation architecture

Translations will live in separate bundled UTF-8 JSON language packs under a dedicated `locales` directory. English defines the complete canonical key set. Other packs contain the same stable keys and may omit a value only when English fallback is acceptable.

A focused localisation module will:

- normalise operating-system locale identifiers;
- choose the effective language from a saved override or system locale;
- load and validate bundled language packs;
- return translated strings by stable key;
- interpolate named placeholders without evaluating arbitrary expressions;
- fall back to the English value for a missing, blank or invalid translation;
- fall back to the key only when the English pack itself is missing that key;
- expose supported-language names for the Language menu.

The main application will request user-visible text through this module. This includes menus, pane controls, column headings, context menus, dialogs, validation and error messages, status/progress text, conversion and analysis windows, About, and the complete Help Centre. Codec names, extensions, file paths, tag values, technical metadata values and user-authored content are not translated.

The Help Centre keeps its searchable chapter model. Each language pack provides translated chapter titles and bodies, including new chapters or sections for language selection, reminder controls, Store ratings and optional support. Search operates on the active translated content.

Pack loading must never prevent the application from starting. Malformed or absent non-English packs produce an English interface and a diagnostic entry suitable for troubleshooting, without exposing a blocking error during startup.

## Reminder state and privacy

Reminder scheduling is implemented in a focused module independent of Tk widgets. It reads and writes only local state in the existing settings file:

- total successful application launches;
- distinct local calendar dates on which the application was launched, bounded to the minimum history needed by the policy;
- the next eligible rating launch;
- rating-reminder disabled state;
- the next eligible support launch;
- support-reminder disabled state.

No reminder state, launch count, date, file information or other usage data is transmitted. The application contains no analytics and does not attempt to determine whether a rating or donation was completed.

A launch is counted once after the main window has initialised successfully. Development tests and failed startup attempts do not increment the count.

Only one reminder may be displayed during a launch. A Store rating reminder has priority. When both are eligible, the support reminder remains eligible and may appear on the next successful launch.

## Microsoft Store rating reminder

The first rating reminder becomes eligible when both conditions are true:

- at least five successful launches have been recorded; and
- those launches span at least three distinct local calendar dates.

The reminder offers:

- **Rate in Microsoft Store** — records the rating reminder as permanently disabled, then opens product `9NZL6GF5JSJK` using the Windows Store URI. If that launch fails, it tries the product's HTTPS Microsoft Store page. If both fail, it shows the copyable destination and the error.
- **Later** — schedules the next rating reminder for ten launches after the current launch count.
- **Don't ask again** — permanently disables automatic rating reminders without opening a destination.

The application cannot know whether the user submits a rating. Pressing the explicit Store button is treated as completion so the user is not asked again.

## Buy Me a Coffee reminder

The first support reminder becomes eligible on successful launch 11. Choosing **Maybe later** schedules it for 11 launches after the current launch count, so it may recur at 22, 33 and subsequent 11-launch intervals when no higher-priority reminder is shown.

The reminder offers:

- **Buy me a coffee** — opens `https://buymeacoffee.com/johnperky` through the operating system's normal browser and schedules no further automatic support reminders;
- **Maybe later** — postpones the prompt by 11 successful launches;
- **Don't ask again** — permanently disables automatic support reminders.

Opening failures show the copyable address and error. The page never opens automatically, and no feature is restricted based on the user's choice.

## Reminder controls

**Tools > Reminders** opens a small settings dialog showing whether each reminder is enabled and when it can next become eligible. It provides independent controls to re-enable or disable Store rating and Buy Me a Coffee reminders.

Re-enabling the rating reminder schedules it no earlier than ten launches after the current launch and still requires three distinct use dates. Re-enabling the support reminder schedules it 11 launches after the current launch. The dialog does not provide a way to fabricate historical usage.

## User experience

Reminder dialogs use the active interface language, clearly identify the destination, and use neutral wording. Closing a reminder window is equivalent to choosing its postponement option, not permanent refusal.

Prompts are evaluated only after normal startup work is complete and are deferred while another modal startup dialog is active. They do not interrupt scans, conversions, transfers or shutdown.

## Compatibility and packaging

Version identifiers in source, `VERSION.txt`, release notes and project context will advance to 12.4.0. The Windows and Linux build definitions will bundle every language pack. Missing required English localisation assets cause a build failure; a missing optional translation pack is reported clearly during verification.

Settings written by older releases remain valid. Existing installations without localisation or reminder keys receive automatic language detection and fresh reminder counters without losing pane, workspace, cache, appearance or performance settings. Version 12.3.0 remains the rollback executable.

After verification, the Windows build pipeline will produce a fresh versioned executable and copy `ResolutionFileManager-v12.4.0.exe` to the user's Desktop, following the established project rule.

## Testing and verification

Development follows test-first implementation. Automated tests cover:

- locale normalisation, regional mapping and unsupported-locale fallback;
- saved manual overrides and System default restoration;
- missing, blank, malformed and incomplete language packs;
- named placeholder interpolation and English fallback;
- parity of required keys across all nine packs;
- launch counting and distinct-date handling;
- the five-launch/three-day rating threshold;
- ten-launch rating postponement and permanent dismissal;
- the launch-11 support threshold, 11-launch recurrence and permanent dismissal;
- collision handling that shows only the rating reminder and preserves support eligibility;
- re-enabling each reminder from current state;
- Store URI, web fallback and Buy Me a Coffee browser-opening failure paths;
- settings migration without loss of unrelated existing values;
- packaging inclusion of all locale files.

The complete existing test suite must remain green. Manual verification covers first launch under representative supported and unsupported system locales, changing language and restarting, translated Help search, both reminder dialogs, the Reminders settings dialog, Microsoft Store launch, browser launch, and a packaged Windows executable running without a source checkout.

## Documentation

The in-app Help Centre, `PROJECT_CONTEXT.md`, `CHANGELOG.md`, `README.md`, release notes and packaging guidance will document:

- supported languages and automatic detection;
- how to override or restore the system language;
- why restart is required;
- the exact rating and support schedules;
- how to disable and re-enable reminders;
- the local-only reminder state and absence of tracking;
- direct destination URLs and failure recovery.
