# Recovery and full Help implementation plan

**Goal:** preserve current 43-language Windows development, restore full documentation and establish verifiable Windows/Linux releases from the maintained F: source.

**Architecture:** retain the established project path and shared application. Extract the verified 12.3.0 English guide into a version-controlled paragraph-addressable master; preserve later topics and add implementation-verified Smart Collections instructions. Translate Help only, with stable chapter/paragraph identifiers and master hashes. Keep UI dictionaries unchanged. Export complete manifests and source bundles rather than maintaining divergent Linux source.

**Spec:** user's phased recovery request; evidence in docs/RECOVERY_AUDIT_2026-10-19.md.

## Ordered stages and checks

- [x] Read-only location/Git/platform audit, report conflicts, separate backups before edits.
- [x] Verify complete snapshot hashes and document all important missing export files.
- [x] Restore the 15 original English chapters selectively; retain all six later topics as appropriate; add complete Smart Collections chapter and searchable navigation/index.
- [x] Test actual Smart Collections save/apply/filter/sort/rename/delete/restore behaviour with isolated fixture media and settings.
- [x] Update only Help for 42 non-English languages, preserving every paragraph ID, formatting, references and existing UI terminology. Validate every language for coverage, length, English residue, broken references and RTL control balance. Keep translation-service limitations explicit.
- [x] Repair source export/backup/release workflows so all imports, help, locales, tests and both builders are included; preserve old releases and prevent clobbering snapshots.
- [x] Run Windows tests and isolated UI smoke tests; build new versioned Windows EXE and Desktop copy.
- [x] Build/test shared code and executable on local Ubuntu; export a fresh versioned Linux handoff without overwriting 12.3.0. Check packaging dependencies; report Mint/desktop tests not performed.
- [x] Verify source/release manifests and final backups; prepare clean candidate Git file list without committing/pushing; record checkpoint and final results. Evidence: docs/RECOVERY_EXPORT_VERIFICATION.json and project_snapshot.py candidates. Completed-source archive also retains the final report/checkpoint.

## Constraints and review focus

No downgrade, unrelated changes, Store operations or screenshots. Preserve current UI values byte-for-byte logically. Backups/releases use new paths. Tests must catch summary substitution, missing master paragraphs, stale source ZIPs, Smart Collections accidentally moving media, and platform-specific desktop integration assumptions. User has authorised inline execution of these phases; continue without another approval gate.
