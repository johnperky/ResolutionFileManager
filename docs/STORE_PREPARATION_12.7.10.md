# Microsoft Store 12.7.10 preparation — 21 October 2026

Prepared using the `microsoft-store-submission` skill and the established **Import listings > Upload folder** workflow. Application code was not rebuilt: the exact separately reviewed 12.7.10 Help-revision executable was packaged.

## Exact package

- `packaging/microsoft-store/output/ResolutionFileManager-12.7.10.0-x64.msix`
- SHA-256: `21a6f8fdd5c3665ef6e172298b5da088c322363c3e7ab73a12a5f640ef611aa8`.
- Embedded EXE SHA-256: `ecc2b624c556aa923bcb132e937b3600abb11bdcc8b6a94a5d2e8f997f004419`.
- Existing assigned identity/publisher, x64 Desktop target, 43 resource languages including `sr-cyrl-rs`, and existing `runFullTrust` capability retained. Licence texts included. MakeAppx schema/package validation, ZIP integrity, manifest identity/language and exact embedded-EXE checks pass locally. Remote upload/save status is recorded separately below.
- Builder now accepts explicit reviewed source/executable/licence paths, verifies embedded modules/resources, and uses a new versioned stage without deleting earlier packages. Never package the newer Linux source under the Windows version.

## Upload folders

Project-parent location: **`Store Preparation 12.7.10/Submission Folders Preserved`**.

| Folder | Store listings | PNGs |
|---|---:|---:|
| RFM-12.7.10-Import-Part-1 | 11 | 44 |
| RFM-12.7.10-Import-Part-2 | 11 | 44 |
| RFM-12.7.10-Import-Part-3 | 11 | 44 |
| RFM-12.7.10-Import-Part-4 | 11 | 44 |
| RFM-12.7.10-Import-Part-5 | 1 | 4 |

45 existing Store locale entries cover 43 application languages, retaining English (India), both existing Simplified Chinese entries and Cyrillic Serbian. Each folder contains exactly one UTF-8 CSV plus its referenced new PNGs. All 172 approved source-native PNGs were decoded/format/dimension/hash checked, then copied byte-identically into 180 upload references including the English/Chinese aliases. No screenshots regenerated.

Release notes, DesktopScreenshot1–4 and their captions are the intended changes. **Always include the complete original export rows for each batch locale.** Actual partial-import evidence showed omitted Feature/SearchTerm lists were cleared and a logo flag reset even though descriptions survived. The corrected CSVs explicitly carry forward descriptions, every feature/search term, logo flags, icons, trailers, optional fields, existing unrelated URLs and later screenshot slots. Full fresh Submission 9 export is preserved under `Baseline`; baseline SHA-256: `6d8de1d05335d39ab3cf63df9ddc2620a83af4821fa1a2a53074c831d567fce5`. It supersedes the old 12.6.2 export for preparation.

Release notes cover hidden files, expanded organisation-rules Help, transfer/Undo improvements, layout changes and 43-language Help. They and captions are translated into all 43 languages; individual text files cover all 45 Store entries. Review gallery: `Release Notes Review.html`. Public reusable copy: `packaging/microsoft-store/RELEASE_NOTES_12.7.10.json`. Translation is machine-assisted; native-speaker proofreading is not claimed.

Pilot English/German/Arabic before the full batch. Short UI-glossary substitutions damaged longer release-note words in the initial pilot; final prose translations preserve technical version/count without those substitutions. Older intermediate folders are marked superseded; use **Submission Folders Preserved** only. Generator: `packaging/microsoft-store/prepare_12710_import.py`; unchanged inputs/cache/results can be reused safely, and differing existing outputs are preserved rather than overwritten.

## Partner Center and next steps

Product `9NZL6GF5JSJK`; **Submission 9**: `1152921505702194214`, created as a draft from live Submission 8. Live package inspected as 12.6.2.0. Fresh draft export downloaded successfully. New 12.7.10.0 MSIX uploaded, analysed and saved; Partner Center overview verified **Validated / Updated**. The older package was automatically superseded in this draft. All 45 Store language rows show **Complete**. Price remains **GBP 0**, public/discoverable, all 240 markets. Submission options retain automatic publication after certification; existing full-trust explanation is present. None of these settings was changed.

Original Parts 1–3 saved, but export verification found the missing-list-field reset. Restore folders 1–3 carry complete baseline fields and reuse already saved screenshot URLs, without reuploading PNGs. First full-field restore pilot saved and verified against a fresh export: 11 listings, 99 intended changed cells, all other fields equal baseline, zero errors (`Verified-restore-pilot.json`). All three restore batches and corrected Parts 4–5 are now saved. **Final fresh export verification passes for all 45 listings: 405 intended changed cells, every unrelated baseline field preserved, 132 saved screenshot/caption pairs preserved through restoration, zero errors.** Final export SHA-256: `4638361bde4b8bf8f19a845af2b9b279fea7a30a5cba005a661f5bd7d0106aae`. Local evidence: `FINAL_EXPORT_VERIFICATION.json`, `Baseline/final-saved-export.csv` and `IMPORT_PROGRESS.md`. Do not reimport completed folders. Microsoft also reorders some screenshot/caption pairs; all four translated captions were present in every imported locale, so verification compares caption sets rather than assumed slots. Corrected original Parts 4–5 include complete baseline rows. Import sequentially through Import listings > Upload folder; verify each saves and record progress in the local `IMPORT_PROGRESS.md`. Never select the parent preparation folder or upload CSV/images individually by default. No certification submission is authorised by this preparation task. Full listing saves/readiness are separate from local folder validation.

Final status: **draft prepared, not submitted for certification**. The overview remains open. Package and listing changes are saved; do not repeat imports. Verification tooling: packaging/microsoft-store/verify_import_export.py compares a new export with baseline, changed fields, and saved screenshot/caption pairs for restored batches.
