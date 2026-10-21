# Clean Windows test

This means running the published download in a fresh Windows environment without the project's Python, FFmpeg, caches or development settings. Windows Sandbox provides that environment on supported Windows editions. It tests the Windows version supplied by the host; a Windows11 Sandbox does not establish Windows10 compatibility.

1. Open **Turn Windows features on or off**, select **Windows Sandbox**, then OK. This requires administrator approval; restart only when convenient if Windows requests it. Nothing in this kit enables features or restarts the PC.
2. Run the retained **Prepare Clean Windows Test.cmd** once. It creates a versioned test folder beside the project and preserves any existing kit.
3. Open **Run Clean Windows Test.wsb** in that folder. The published EXE is checksum checked and launched with disposable media/settings. Host app files are read-only; only the kit's Results folder accepts test logs. Networking is disabled.
4. Tick the checks below in the host Results/CHECKLIST.md. Startup.txt records the actual guest OS and environment. Closing Sandbox deletes its temporary workspace; host results remain.

- [ ] App opens without separately installing Python or FFmpeg.
- [ ] Both panes show normal.jpg and sample.mp4 (if supplied); preview image/video, thumbnails and Info work.
- [ ] Tools > Show hidden files reveals hidden.jpg and .dot-hidden.jpg in both panes; off hides them again; layout stays fixed.
- [ ] Resize, open Help, and check System/Dark/High contrast at100%,150%,200%; toolbar, Info and dialog actions remain usable.
- [ ] Close/reopen the app during this Sandbox session; saved choices restore.
- [ ] Any file-operation/conversion tests use only C:/RFM-Clean-Test/Media copies, never host originals.
- [ ] Record pass/fail and any error, OS build, display size and steps before closing Sandbox.

Windows10 requires a separate Windows10 PC or virtual machine with legitimate installation media/licensing. This kit does not download an OS, create a VM or claim that test has passed.

Microsoft instructions: https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install

Sandbox environment/supported editions: https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/
