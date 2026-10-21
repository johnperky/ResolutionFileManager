# Windows release and installation

## For users

1. Download the ZIP from the project's official Releases page.
2. Compare its SHA-256 value with `SHA256SUMS.txt` on that release page.
3. Extract the complete ZIP to a normal folder.
4. Open `ResolutionFileManager-12.7.10.exe`.

The application is portable: it does not need an installer and does not require a separately installed copy of FFmpeg. Windows may show a SmartScreen warning while the application remains unsigned. Only download it from the official project page and verify the checksum.

Settings and caches are stored in the user's local application-data folder, rather than beside the executable. Removing the application does not delete media files.

## For maintainers

For an already reviewed build, run `build_windows_release.ps1 -ReviewedExecutable <exact-reviewed-exe>` from PowerShell. This verifies all six embedded application modules and all 43 locales against maintained source, then packages those exact bytes without rebuilding. It creates the portable ZIP, standalone EXE, complete source archive, licence/notices and checksums under `release-output/<version>/`. Existing versioned folders are preserved. Without this argument the script builds first; that fresh binary requires review before publication.

Before publication:

1. Test the package on a clean Windows 10 or Windows 11 computer where available. Record the actual host and environment isolation used; an isolated run on an existing host is not a separate clean-machine test. Record untested systems explicitly in release notes.
2. Scan the extracted executable with current security software.
3. If a code-signing certificate is available, sign the executable and rebuild the ZIP/checksums.
4. Create the matching `v12.7.10` source tag.
5. Upload the ZIP, standalone EXE, source archive, and `SHA256SUMS.txt` to the official release.
6. Replace the URL placeholders in the WinGet and Chocolatey templates only after the final files are public.
