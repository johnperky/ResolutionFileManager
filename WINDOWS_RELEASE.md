# Windows release and installation

## For users

1. Download the ZIP from the project's official Releases page.
2. Compare its SHA-256 value with `SHA256SUMS.txt` on that release page.
3. Extract the complete ZIP to a normal folder.
4. Open `ResolutionFileManager-12.2.2.exe`.

The application is portable: it does not need an installer and does not require a separately installed copy of FFmpeg. Windows may show a SmartScreen warning while the application remains unsigned. Only download it from the official project page and verify the checksum.

Settings and caches are stored in the user's local application-data folder, rather than beside the executable. Removing the application does not delete media files.

## For maintainers

Run `build_windows_release.ps1` from PowerShell. It performs a clean PyInstaller build, creates a versioned portable folder and ZIP, copies source and compliance documents, and writes SHA-256 checksums under `release-output/12.2.2/`.

Before publication:

1. Test the package on a clean Windows 10 or Windows 11 computer.
2. Scan the extracted executable with current security software.
3. If a code-signing certificate is available, sign the executable and rebuild the ZIP/checksums.
4. Create the matching `v12.2.2` source tag.
5. Upload the ZIP, standalone EXE, source archive, and `SHA256SUMS.txt` to the official release.
6. Replace the URL placeholders in the WinGet and Chocolatey templates only after the final files are public.
