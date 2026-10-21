# Resolution File Manager

A dual-pane media file manager with shared Windows/Linux source that scans images and videos, displays technical metadata, sorts and filters large collections, previews content, and performs reviewable file-management and conversion workflows. Linux binaries require a compatible Linux environment; see LINUX_INSTALL.txt for dependencies and test limitations.

Current Windows version: 12.7.10. Linux 12.7.11 is a Mint 22.x / Ubuntu 24.04 review candidate; physical Mint desktop checks remain outstanding. Read PROJECT_STATUS.md first for current verification, release status and remaining work.

The maintained development source is the established F: project directory. See DEVELOPMENT_WORKFLOW.md for complete verified snapshots, Git preparation, shared-source builds and preservation of older releases. The authoritative detailed English manual is docs/help/ENGLISH_MANUAL.md; Help completeness is checked before builds. See docs/RECOVERY_REPORT_2026-10-19.md for actual verification status.

## Download and support

Use the project's official Releases page for Windows downloads. Each release includes a portable package, source archive, SHA-256 checksums, licensing information and installation instructions. Avoid executable copies hosted by unknown third parties.

Resolution File Manager is free software licensed under GNU GPL version 3 or later. If it is useful to you, optional support is available at https://buymeacoffee.com/johnperky.

## Features

- Dual folder panes
- Persistent Tools > Show hidden files toggle for hidden media and folders
- Automatic operating-system language detection with 43 complete interface/help choices, including separate European and Brazilian Portuguese packs, Simplified and Traditional Chinese, and broad European and Asian language coverage
- Optional private local reminders for Microsoft Store ratings and Buy Me a Coffee support, with independent controls under Tools
- Independent per-pane tick boxes that collect an action group while ordinary highlighting remains free for previewing
- Expandable folder tree in each pane
- Video support: MP4, MKV, MOV, AVI, WebM, M4V, WMV, MPG, MPEG
- Image support: JPG and JPEG
- Sort by name, type, resolution, megapixels, or file size
- Per-pane thumbnail Sort menu with explicit ascending/descending choices for name, date, size, length, codec, resolution, type, bitrate, frame rate, and rating
- Filter to one resolution and select the whole visible group
- Tick/untick all shown files, preserve ticks through sorting and filtering, and clear the group in one click
- Right-click one file or a multi-file selection to copy or move it
- Optional recursive scanning of all subfolders (folder structure is preserved on transfer)
- Independent Videos and Images visibility toggles
- Sortable resolution, file size, date modified, and video length columns
- Drag-and-drop column header reordering
- Slim, flat draggable divider between the left and right browsers
- Sortable MB/min data-rate column and automatic selection of unusually large videos relative to their duration
- Adjustable Moderate, Large, and Extreme size-outlier sensitivity
- Persistent folders, filters, column order/widths, sorting, window size, and pane layout
- Metadata cache for substantially faster repeat scans
- Scan progress and cancellation
- Copy/move progress counts
- Open, reveal in the operating-system file manager, and rename actions
- Additional PNG, WebP, TIFF, BMP, GIF, HEIC/HEIF, and AVIF image support
- Matching slim divider between the browser and scratch-preview areas
- Native drag-out of selected files to the Windows desktop, File Explorer, and compatible applications
- Right-button dragging requests the destination's native Copy/Move/shortcut action menu
- Drag-and-drop copying between the two browser panes and onto folders in their folder trees
- Scratch preview panel with silent video autoplay, looping, Play/Pause, a live timeline, and responsive drag-to-skim frames
- Copy or move selections to the folder open in the other pane
- Background scanning so the interface stays responsive
- Sortable video codec, bitrate, frame-rate, audio, pixel-format, and HDR metadata
- Filename search and advanced resolution, size, duration, codec, orientation, and date filters
- Exact SHA-256 duplicate detection with first/newest/smallest retention choices
- Dedicated duplicate-review window with side-by-side previews, paths, dates, decision labels, and First/Newest/Oldest/Smallest/Largest retention proposals
- Side-by-side visual and technical comparison with keep-left/keep-right actions
- Integrated per-pane Details and cached Thumbnail browser modes with Small, Medium, and Large sizes
- Thumbnail mode uses the complete filtered recursive result set and shares selection, preview, context actions, and drag-and-drop with Details mode
- Video thumbnails are sampled 15% into each clip instead of near the opening frame
- Folder comparison and one-way synchronization previews
- Named workspaces for folders, filters, columns, and layout
- Configurable parallel scan workers and excluded path patterns
- Metadata/thumbnail cache inspection, pruning, and clearing
- Transfer queue with progress, speed, remaining time, pause/resume, cancellation, retry, and conflict policies
- Undo for recent copies, moves, replacements, and renames
- Keyboard copy/cut/paste, select-all, refresh, navigation, rename, delete, and undo
- Safe deletion through the operating system Recycle Bin or Trash
- Conventional File, Edit, View, Tools, and Help menus with a complete in-app usage guide
- Read-only, cancellable full media-integrity verification with cached results, failed-file selection, and CSV reporting
- Cancellable video contact-sheet export with evenly spaced frames, configurable layout, and optional timestamps
- Frame-accurate previous/next preview controls and full-resolution current-frame PNG export
- Review-only perceptual image matching with adjustable tolerance, cached hashes, and scalable BK-tree lookup
- Preview-first batch renaming with templates, find/replace, numbering, collision checks, transactional swaps, and whole-batch undo
- Cancellable Selected/Visible/All-scanned media inventory export to CSV, structured JSON, or self-contained HTML
- On-demand searchable image EXIF and video container/stream metadata viewer with clipboard and JSON export
- Persistent System, Light, Dark, and High contrast themes with live 100–200% interface scaling and cancel rollback
- Persistent preview-first folder organization rules with ordered conditions and safe transfer-queue execution
- Preview-first sequential H.264/H.265/AV1/proxy/remux conversion with progress, cancellation, atomic outputs, and retained originals
- Full folder-tree and media refresh from View, F5, the toolbar, and browser/folder-tree right-click menus
- Optional independent live filesystem updates in each pane, with recursive scope matching Include subfolders
- Quiet, Balanced, and Fast performance profiles with interactive preview priority
- Virtualised continuous thumbnail scrolling, with the original paged grid retained per pane
- Persistent database-only star ratings, colour labels, and tags with sorting and filtering
- Named one-pane smart collections with apply, rename, delete, and undo-delete management
- Optional independent file-information inspectors that collapse completely when disabled
- Reliable column edge resizing, with Shift+drag reserved for column reordering
- Stable non-stretching column widths plus a Columns dialog for ordering and exact width control
- Unrestricted Details-view header resizing by separating left-button headers from right-button file dragging
- Direct divider-drag resizing and modifier-free header-drag reordering inside the browser
- Responsive bounded scan-result processing and background cache saving during large recursive scans
- Scan-safe preview pausing and filename-preserving recursive path compaction

## What's new in 9.0.0

Version 9 turns the file browser into a broader media-management workspace. Technical metadata and advanced filters help locate files; duplicate, thumbnail, comparison, and synchronization tools help decide what to keep; and all internal transfers now share a safer queued workflow with conflict handling and undo.

## What's new in 9.1.0

Duplicate detection now opens a visual review workspace instead of immediately asking for a retention rule. Each exact duplicate group lists full locations, file sizes, timestamps, and decision labels while previewing two copies side by side. Choosing a strategy only selects proposed redundant files in the main pane for further review.

## What's new in 9.2.0

Thumbnails are now a full browser mode inside each pane rather than a separate window limited to 60 files. Details and Thumbnail modes share the complete recursive scan, filters, sorting, selections, preview, file actions, and cached media. Version 9.2 also adds a standard desktop menu bar and an in-app help guide.

## What's new in 9.2.1

Video thumbnails are now generated at 15% of the clip duration. Files without readable duration metadata continue to use a one-second fallback. Existing cached thumbnails regenerate automatically under the new sampling rule.

## What's new in 9.2.2

Refresh now rebuilds folder trees as well as rescanning media, reflecting folders created, renamed, moved, or deleted outside the application. Refresh active pane and Refresh both panes are available from View and relevant right-click menus; F5 and the toolbar refresh both panes.

## What's new in 9.2.3

Column edges now resize normally; hold Shift while dragging a header to reorder columns. Scan updates no longer restart a manually paused preview of the same file. Long recursive paths keep the first folder and full filename visible where space permits, using a compact `first/…/filename` form.

## What's new in 9.2.4

Columns no longer stretch and collapse to fill the pane. Legacy layouts where nearly every column was saved at minimum width reset automatically. Use View > Configure columns or right-click a header to move columns, set exact widths, or restore defaults; Shift+drag header reordering remains available.

## What's new in 9.2.5

Details-view file dragging now uses the right mouse button so the drag-and-drop layer cannot interrupt left-button column resizing or Shift+drag reordering. Thumbnail cards continue to support ordinary left-button dragging.

## What's new in 9.2.6

Column manipulation is handled directly inside the browser rather than relying on theme-dependent Treeview behavior. Drag dividers to resize continuously and drag header faces to reorder without Shift; click headers normally to sort. The pointer changes over resizable dividers.

## What's new in 9.2.7

Large recursive scans no longer monopolize the Tkinter UI while cached results arrive. Result processing is bounded per UI turn, detail refreshes are throttled, thumbnails rebuild after completion, and cache writing occurs in the background. Preview stills return through a main-thread queue and stopped FFmpeg processes are cleaned up, keeping scratch-preview controls responsive even while scanning large libraries.

## Requirements

- Python 3.10 or newer (Tkinter included)
- FFmpeg/ffprobe on `PATH` for video dimensions
- Python packages from `requirements.txt` when running from source

Windows: `winget install Gyan.FFmpeg`

Ubuntu/Debian: `sudo apt install python3-tk ffmpeg`

Fedora: `sudo dnf install python3-tkinter ffmpeg`

## Run

```text
python -m pip install -r requirements.txt
python media_sorter.py
```

Click a pane to make it active. Selected files are copied or moved from that pane into the folder shown in the other pane.

## Optional standalone builds

Install PyInstaller, then build separately on each operating system:

```text
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ResolutionFileManager media_sorter.py
```

The executable appears under `dist`. The supplied Windows and Linux build scripts bundle FFmpeg, FFprobe, and FFplay, so their finished applications do not require a separate FFmpeg installation on the destination computer.

## Continue developing the project

Keep this whole folder as the project. The main source is `media_sorter.py`. On Windows, install FFmpeg and then run:

```text
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

This recreates the standalone executable in `dist`. Build Linux packages on Linux from the same Python source; platform executables should always be compiled on their target operating system.

For every release, update the in-app Help guide alongside the source documentation. After a successful Windows build, place a fresh versioned copy on the Desktop, for example `ResolutionFileManager-v9.2.3.exe`.

Version 9.2.8 improves large recursive-folder responsiveness by deferring the full browser refresh until scanning completes, inserting final Details rows in short UI batches, and pacing scratch video decoding to real time at 12 fps so preview playback does not consume unnecessary CPU during scans.

Version 9.2.9 adds Back, Forward, Up, and Refresh controls beneath each pane heading, with separate Explorer-style navigation history for the two panes.

Version 9.3.0 keeps each folder tree expanded and selected at the pane's current folder, including after navigation, workspace restoration, and refresh. Folder-tree expansion no longer probes every sibling directory in advance.

Version 9.3.1 uses compact standard symbols for the per-pane Back, Forward, Up, and Refresh buttons.

Version 9.3.2 makes scratch-preview seeking faster by cancelling obsolete decoder processes during scrubbing and caching recently visited timeline frames.

Version 9.4 adds 1×–16× scratch-preview playback speeds and optional synchronized audio, muted by default. Windows builds bundle FFplay for audio output, while high-speed previews reduce decoded frame density to control CPU use.

Version 9.4.1 prevents the synchronized current folder from showing a lingering Loading placeholder before it is expanded.

Version 9.4.2 stabilizes image-thumbnail loading with bounded decoder concurrency, atomic validated PNG cache writes, stale-result rejection, and short UI callback batches.

Version 9.5 uses Pillow instead of a separate FFmpeg process for ordinary image thumbnails and pages each pane's thumbnail grid in groups of 200. FFmpeg remains the fallback for unusual image formats and the decoder for video thumbnails.

Version 9.5.1 waits for the real thumbnail-canvas width before the first grid render and automatically reflows columns when a pane is resized.

Version 9.5.2 offers per-pane thumbnail page sizes of 200, 500, or 1,000, defaults to 500, and remembers the chosen capacity.

Version 9.6 provides separate left/right scratch previews. Each pane has an off-by-default Preview toggle, and the entire lower preview area collapses while neither side is enabled to maximize browser space and eliminate preview overhead.

Version 9.6.1 scales each image or video preview to fill as much of its own panel as possible while retaining the original aspect ratio, including after divider and window resizing.

Version 9.6.2 defaults thumbnail page capacity to Auto: 200 for video-majority results and 500 for image-majority results. Manual capacities remain available.

Version 9.7 retains thumbnail files across restarts and applies an adjustable least-recently-used storage limit, defaulting to 1% of the operating-system drive and configurable from 0.1% to 10% under Tools.

Version 9.7.1 adds a dedicated, confirmed Clear thumbnails command that leaves source media and cached metadata untouched.

Version 9.7.2 allows mouse-wheel scrolling from anywhere inside either thumbnail grid, including directly over thumbnail cards, images, and filenames.

Version 10.0 replaces the all-in-memory JSON metadata cache with an indexed SQLite database. Existing cached metadata migrates automatically on first launch, while new and changed records are committed incrementally in batches. This reduces cache memory usage and eliminates full-file JSON rewrites as large libraries grow.

Version 10.1 makes exact duplicate searches staged and persistent. Same-size files are sampled with a fast beginning/middle/end fingerprint before whole-file SHA-256 verification, and both hashes are cached in SQLite for near-instant reuse when files remain unchanged.

Version 10.2 adds an optional Live checkbox to each pane. Native folder notifications merge bursts of external creates, changes, renames, and deletions into one refresh, and recursive monitoring follows Include subfolders. Live mode defaults off and can be disabled instantly to restore manual-refresh behaviour.

Version 10.3 adds a central background-work controller and performance profiles. Balanced retains the previous concurrency and preview rate, Quiet reduces system load, and Fast favours throughput. During playback or seeking, Quiet and Balanced pace new uncached metadata and thumbnail jobs so interactive previews receive priority; cached results remain immediate.

Version 10.4 adds Continuous thumbnail browsing. Only cards in and just beyond the visible viewport exist, keeping memory and Tk widget use bounded while a single scrollbar covers the complete filtered collection. Each pane can switch back to the original Paged mode at any time; workspaces remember the choice.

Version 10.5 adds reversible ratings, colour labels, and tags without changing media files. They appear in Details and Thumbnails, participate in sorting and advanced filtering, survive technical cache clearing, support multi-file assignment, and follow internal file operations.

Version 10.6 adds saved Smart Collections for reusable one-pane folders, searches, filters, sorting, and browser modes. It also adds an optional Info inspector to each pane with technical and annotation details plus Copy path, Open, and Reveal actions. Inspectors default off and collapse completely; smart collections can be renamed, deleted with confirmation, and immediately restored after deletion.

Version 10.7 adds a read-only media-integrity verifier for Selected, Visible, or All scanned files. It fully decodes image frames in-process and video/audio streams through bundled FFmpeg, supports cancellation and forced rechecks, caches unchanged results in SQLite, selects failures in the source pane, and exports CSV reports. Source media is never modified, and the separate version 10.6 executable remains available for rollback.

Version 10.8 adds PNG video contact sheets for a single selected clip. It extracts 4–48 evenly spaced frames away from the endpoints, supports 2–8 columns and 160–640-pixel frame widths, optionally labels frames with numbers and timestamps, reports progress, and can be cancelled. Output is written atomically and source video remains untouched; version 10.7 remains available for rollback.

Version 10.9 adds previous-frame and next-frame controls to both scratch previews using each video's reported frame rate, with a 25 fps fallback. Stepped stills use precise seeking and exact-position cache keys. The current position can also be exported as a full-source-resolution PNG through an atomic temporary output, without modifying the video; version 10.8 remains available for rollback.

Version 11.0 adds review-only visual similarity search for images. A cached 64-bit difference hash detects many resized or lightly recompressed copies, while an adjustable 0–16 tolerance controls strictness. BK-tree lookup avoids quadratic comparison across large collections. Results provide previews and source-pane group selection but no deletion action, and version 10.9 remains available for rollback.

Version 11.1 adds preview-first batch renaming for selected files. Templates support original names, padded sequence numbers, and extensions, alongside optional case-sensitive or insensitive find/replace. Validation blocks forbidden names, duplicate outputs, and collisions before Apply. A two-stage temporary-name transaction safely handles swaps and rolls back failed batches where possible; successful batches and their annotations are restored together by one Ctrl+Z, while version 11.0 remains available for rollback.

Version 11.2 adds cancellable media inventory reports for Selected, Visible, or All scanned files. CSV supports spreadsheet workflows, JSON contains a structured library summary and item records, and HTML provides a self-contained readable table. Reports cover paths, technical metadata, annotations, and unreadable status, with optional active-folder-relative paths. Output is atomic and incomplete temporary reports are removed; version 11.1 remains available for rollback.

Version 11.3 adds an on-demand, read-only embedded-metadata viewer for one selected file. Images expose format information, EXIF camera/date/GPS fields, and safe binary-value summaries; videos expose container and per-stream tags through FFprobe. Results can be searched live, copied as tab-separated rows, or exported atomically as JSON. Ordinary scans remain unaffected, and version 11.2 remains available for rollback.

Version 11.4 adds persistent System, Light, Dark, and High contrast themes and live 100%, 125%, 150%, 175%, or 200% interface scaling. Existing widgets recalculate their named-font metrics immediately, including when returning to 100%. The appearance window previews changes, Save persists them, and Cancel restores the exact previous theme and scale; version 11.3 remains available for executable rollback.

Version 11.5 adds persistent ordered folder-organization rules. Rules can Copy or Move the first matching media based on kind, extensions, filename text, codec text, minimum rating, and exact tag. A dry-run preview covers Visible or All scanned files, optionally preserves recursive relative folders, and flags existing or duplicate targets before confirmation. Apply delegates to the established conflict-aware, cancellable, retryable, undo-capable transfer queue; rule deletion is confirmed and immediately undoable, while version 11.4 remains available for rollback.

Version 11.6 adds preview-first batch video conversion with H.264 MP4, H.265 MP4, AV1 MKV, 720p H.264 proxy, and stream-copy MKV remux presets. The opposite pane is the default destination, recursive relative folders can be preserved, CRF is adjustable, and existing outputs can be skipped or given numbered Keep both names. Conversion is sequential with per-file/overall progress and cancellation; partial files are removed, completed outputs are atomic, originals are always retained, and version 11.5 remains available for rollback.

Version 11.6.1 hardens Windows release packaging. The build script now checks the dependency-install and PyInstaller process exit codes, requires the executable to exist, and verifies that its timestamp belongs to the current build. A locked or otherwise failed build can no longer print a misleading success message or be copied as a fresh release; version 11.6 remains available for rollback.

Version 11.6.2 fixes the in-app Help guide's batch-rename token examples. Literal template braces are now escaped inside the version-formatted guide, so Help opens normally and displays `{name}`, `{n}`, `{ext}`, and `{dotext}` exactly as users must enter them. A complete Help-window regression check covers every researched feature section; version 11.6.1 remains available for rollback.

Version 11.7 adds a visible Sort menu to each thumbnail browser. Name, date modified, file size, length, codec, resolution, type, bitrate, frame rate, and rating provide explicit ascending and descending choices with plain-language directions such as Newest first and Longest first. The button displays the current order, both panes remain independent, Details header sorting is unchanged, and workspace restoration now reapplies the saved sort order; version 11.6.2 remains available for rollback.

Version 11.7.1 makes the per-pane Preview and Info toggles larger, bold, icon-labelled buttons with a clear selected state. Enabling Info now captures and displays an existing selection before the inspector changes the pane layout, then confirms it after layout completes, so users no longer need to select the file again. Version 11.7 remains available for rollback.

Version 11.7.2 makes Linux releases copyable as one versioned file. The Linux build now bundles FFmpeg, FFprobe, and FFplay, verifies its output, marks it executable, and names it with the application version and processor architecture. It must still be built on Linux Mint and is intended for compatible machines of the same architecture; building on the oldest supported Mint release provides the broadest compatibility. Version 11.7.1 remains available for rollback.

Version 11.8 changes the factory Details layout to Name, Codec, Resolution, Video length, File size, MB/min, FPS, Date modified, Type, Bitrate, Audio, HDR, Megapixels, Label, Tags, and Rating. Existing saved or manually reordered layouts remain unchanged, while new panes and layouts without a saved order use the more useful technical-first sequence. Version 11.7.2 remains available for rollback.

Version 11.8.1 replaces PyInstaller's generic Windows floppy-disk icon with an original blue dual-folder media-transfer icon. A multi-resolution ICO is embedded into the executable for File Explorer and shortcuts, while the matching PNG is bundled and applied to the live application window and taskbar. Linux builds also bundle the window icon. Version 11.8 remains available for rollback.

Version 11.9 adds a dedicated left-button `Drag selected` source to each pane, exporting the complete multi-file selection as the native file-list drop type for programs such as Shutter without reintroducing the Details-header drag conflict. Completed copy and move jobs now clone known metadata into affected panes and remove moved sources in memory; delete removes successful paths directly. Full rescans are avoided for ordinary internal operations and retained only when an externally dropped file has no safe in-memory metadata source. Version 11.8.1 remains available for rollback.

Version 11.9.1 extends Show in File Explorer/Reveal to multi-file selections. Up to five files are revealed individually without another prompt. Larger selections display the exact count and warn that many file-manager windows may open; Yes reveals every selected file and No reveals only the first. Windows and macOS request selection of each exact file, while Linux opens each containing folder through the system file manager. Version 11.9 remains available for rollback.

Version 12.0 adds selectable conversion acceleration. The conversion dialog detects encoders and decode methods advertised by bundled FFmpeg and offers Automatic, CPU/software, NVIDIA NVENC, Intel Quick Sync, AMD AMF, and Linux VA-API when compatible with the preset. Hardware decoding is independently selectable. Automatic verifies engines through real conversion attempts and falls back through alternatives to CPU; an unsupported hardware decoder retries with software decode, while an explicitly selected hardware encoder never silently changes. The 18–35 quality value maps to each engine's constant-quality controls, results identify the engine/decode path used, and remux remains a direct stream copy. Version 11.9.1 remains available for rollback.

Version 12.0.1 keeps the browser anchored after file-changing commands. Deleting or moving selected files automatically selects and reveals the next visible file in the current sort order, falling back to the previous final file when the removed selection was at the end. Rename, batch rename, comparison deletion, live/manual rescans, and both Details and Thumbnail views preserve a useful current item instead of jumping back to the beginning. Version 12.0 remains available for rollback.

Version 12.1 replaces the single scrolling help page with a professional built-in help centre. A chapter contents panel, Previous/Next navigation, full-book case-insensitive search, per-chapter match counts, highlighted results, F3 match stepping, Quick Start, detailed feature chapters, troubleshooting, glossary, status feedback, and keyboard navigation make the complete guide practical to browse while using the program. Version 12.0.1 remains available for rollback.

Version 12.1.1 adds active-preview percentage seeking: comma jumps backward by 10% of the clip and full stop/period jumps forward by 10%. Playback continues when it was running, paused video remains paused on a precise destination frame, the active pane determines which of the two previews responds, and typing fields retain normal punctuation input. New preview panes default to 4× playback for faster review while all 1×–16× controls remain available. The Shortcuts window and searchable Help Centre document the behaviour; version 12.1 remains available for rollback.

Version 12.2 adds Keep source resolution, 1080p, and 720p choices to the video-conversion preview. Resolution is independent of codec and works with CPU/software, NVIDIA NVENC, Intel Quick Sync, AMD AMF, Linux VA-API, and Automatic fallback paths. Resizing sets the selected output height, preserves aspect ratio, and labels output filenames with 1080p or 720p. The 720p proxy selects 720p automatically, while stream-copy remux retains the source resolution; version 12.1.1 remains available for rollback.

Version 12.2.1 lets either preview timeline jump directly to a clicked position. Clicking the track moves the marker to that percentage and resumes playback there; ordinary click-and-drag scrubbing and the comma/full-stop ten-percent shortcuts remain available. Version 12.2 remains available for rollback.

Version 12.2.2 adds an optional support link for the application's creator. Help contains “If you like this, buy John a coffee,” and the redesigned About window repeats the button, displays the public address, and clearly states that support is optional. Activation opens `https://buymeacoffee.com/johnperky` in the normal web browser; the application never opens it automatically or handles payment information. Version 12.2.1 remains available for rollback.

Version 12.3.0 adds independent tick-box action groups to both panes. Details rows and thumbnail cards have visible ☐/☑ controls, while the Details checkmark heading and thumbnail ✓ All shown control toggle every displayed file. Ticks persist through sorting, filtering, paging, and thumbnail recycling so another file can be highlighted and previewed without losing the collected group. Existing commands use ticks when present and ordinary highlighted rows otherwise. Ticks are session-only and changing a pane's folder clears only that pane. Version 12.2.2 remains available for rollback.

On Linux, install Python Tk and FFmpeg as described above, then run:

```text
chmod +x build_linux.sh
./build_linux.sh
```

The resulting `dist/ResolutionFileManager-vVERSION-linux-ARCH` file can be copied to another compatible Linux Mint computer. On that computer, run `chmod +x` on the copied file once and then open it; Python and FFmpeg do not need to be installed there.
