# Microsoft Store submission kit

This folder contains the repeatable MSIX build and prepared Microsoft Store listings for Resolution File Manager 12.6.0. The base listing is English (United Kingdom), with additional multilingual Store listings maintained in Partner Center.

Version 12.6.0 ships 43 complete interface and Help choices, including separate European and Brazilian Portuguese packs and separate Simplified and Traditional Chinese packs. Store-listing translations remain separate marketing assets.

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

- `STORE_LISTING.md` contains the base English (United Kingdom) description, feature list, URLs, recommended questionnaire answers and certification notes.
- `STORE_LISTING.<locale>.md` contains the localised customer-facing fields for each additional Store language. The brand name and URLs remain unchanged, and non-English listings disclose that the current application interface is in English.
- `AppxManifest.template.xml` declares an x64 full-trust Windows desktop app.
- `Build-StorePackage.ps1` creates all package tile assets and the MSIX using the Windows SDK.
- At least one real in-app screenshot is still required by Partner Center; four or more are recommended.

Do not upload a package made with placeholder identity values. Microsoft validates those values against the reserved product identity.
