# WinGet package

This folder contains the multi-file WinGet manifest for Resolution File Manager.

## Package identity

- Identifier: `JohnPerky.ResolutionFileManager`
- Version: `12.2.2`
- Installer type: portable Windows x64 executable
- Release asset: `ResolutionFileManager-12.2.2.exe`

The installer URL is version-specific and the SHA-256 value matches the published
`SHA256SUMS.txt` file in the GitHub v12.2.2 release.

## Validate locally

From an elevated PowerShell window, enable local manifests once:

```powershell
winget settings --enable LocalManifestFiles
```

Then validate and test the manifest:

```powershell
winget validate .\packaging\winget\manifests\j\JohnPerky\ResolutionFileManager\12.2.2
winget install --manifest .\packaging\winget\manifests\j\JohnPerky\ResolutionFileManager\12.2.2
```

Run the install test in Windows Sandbox or another disposable Windows account so
it does not disturb the normal desktop copy of the application.

## Submit

Copy the `manifests\j\JohnPerky\ResolutionFileManager\12.2.2` directory into a
fork of `microsoft/winget-pkgs` at the same path. Validate it, commit it on a new
branch, and open one pull request containing only this package version.

The Store build should also become installable through WinGet's `msstore` source
after Microsoft publishes it. The community manifest here covers the standalone
portable GitHub release and can be maintained independently.
