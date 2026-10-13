# Microsoft Store submission kit

This folder contains the repeatable MSIX build and prepared Store-listing material for Resolution File Manager 12.4.0.

Version 12.4.0 ships English, Simplified Chinese, Dutch, French, German, Japanese, Korean, Russian and Spanish interface/help packs. Store listing translations remain separate marketing assets and must continue to disclose English fallback where appropriate.

## Before the final package can be built

1. Register or sign in at Microsoft Partner Center.
2. Create a new **MSIX or PWA app** and reserve **Resolution File Manager**.
3. Open **Product management > Product identity** and copy the exact **Package/Identity/Name**, **Package/Identity/Publisher**, and **Package/Properties/PublisherDisplayName** values.
4. Run `Build-StorePackage.ps1` with those values. They are case-sensitive and must exactly match Partner Center.

Example:

```powershell
.\Build-StorePackage.ps1 `
  -IdentityName "12345Publisher.ResolutionFileManager" `
  -Publisher "CN=00000000-0000-0000-0000-000000000000" `
  -PublisherDisplayName "John Perky"
```

The finished package is written under `output`. The fourth version component remains zero because Microsoft Store reserves it.

## Submission material

- `STORE_LISTING.md` contains the description, feature list, URLs, recommended questionnaire answers and certification notes.
- `AppxManifest.template.xml` declares an x64 full-trust Windows desktop app.
- `Build-StorePackage.ps1` creates all package tile assets and the MSIX using the Windows SDK.
- At least one real in-app screenshot is still required by Partner Center; four or more are recommended.

Do not upload a package made with placeholder identity values. Microsoft validates those values against the reserved product identity.
