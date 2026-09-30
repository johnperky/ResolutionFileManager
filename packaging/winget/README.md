# WinGet submission template

Create a public GitHub release first. Use the official Windows Package Manager manifest creator (`wingetcreate`) against the final release URL, identify the package as portable, and submit the generated manifests to `microsoft/winget-pkgs` using the maintainer's own Microsoft/GitHub account.

Do not submit a manifest containing a temporary URL or a checksum from an unsigned/replaced build. The installer URL and SHA-256 must describe the exact immutable public executable.

Suggested identity:

- Package identifier: `JohnPerky.ResolutionFileManager`
- Package name: `Resolution File Manager`
- Publisher: `JohnPerky`
- Version: `12.2.2`
- Installer type: `portable`
- Product code/command alias: `ResolutionFileManager`
- Licence: `GPL-3.0-or-later`
