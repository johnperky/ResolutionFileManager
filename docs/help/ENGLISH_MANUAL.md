# Resolution File Manager — authoritative English manual

## Quick Start

1. Choose a folder independently in each pane with Browse, the folder tree, or the path box.
2. Turn on Include subfolders only when you want the complete tree below that folder scanned.
3. Use Details for sortable technical information or Thumbnails for visual browsing.
4. Select files in one pane. Copy and Move use the folder displayed in the other pane as their destination.
5. Turn on Preview or Info only in the pane where you need them. Both default off to save processing power.
6. File-changing actions show confirmation or a preview where appropriate. Delete uses Recycle Bin/Trash, and Ctrl+Z reverses supported recent actions.

The chapters on the left explain every part of the program. Type any word or phrase in Search all chapters and press Enter. Matching chapters and the number of matches appear in the contents list; use Next match to step through each highlighted occurrence.

Choose a folder in either pane. Enable Videos, Images and Include subfolders as needed. Use Details or Thumbnails, select or tick files, preview them, then copy, move, analyse or convert them. Ticked files form the action group; highlighting remains available for browsing and preview.

## Topic Index and Chapter Links

Quick Start — [chapter:quick_start]

Getting Started — [chapter:getting_started]

Details And Thumbnails — [chapter:details_and_thumbnails]

Scanning And Filtering — [chapter:scanning_and_filtering]

Selecting And Previewing — [chapter:selecting_and_previewing]

Copying And Moving — [chapter:copying_and_moving]

Smart Collections: Saved Searches — [chapter:smart_collections]

Duplicates And Comparison — [chapter:duplicates_and_comparison]

Video Conversion — [chapter:video_conversion]

Exporting a Media Report — [chapter:media_reports]

Viewing Embedded Metadata — [chapter:embedded_metadata]

Checking Media Integrity — [chapter:media_integrity]

Creating a Video Contact Sheet — [chapter:video_contact_sheets]

Folder Synchronization — [chapter:folder_synchronization]

Folder Organization Rules — [chapter:folder_organization_rules]

Managing the Transfer Queue — [chapter:transfer_queue]

Safe File Actions — [chapter:safe_file_actions]

Workspaces And Cache — [chapter:workspaces_and_cache]

Language — [chapter:language]

Glossary — [chapter:glossary]

Support The Project — [chapter:support_the_project]

## Getting Started

Each side of the window is an independent folder browser. Use Browse, the folder tree, the path box, or Up to choose folders. Click inside a pane to make it active.

View > Appearance and text size offers System, Light, Dark, and High contrast themes plus 100%, 125%, 150%, 175%, and 200% interface scaling. Changes preview immediately throughout existing controls. Save keeps the choice for future launches, Cancel or closing the window restores the previous settings, and Restore system default returns to the operating-system theme at 100%. These settings change only presentation, never media or library data.

Each pane has its own compact Explorer-style navigation strip: ← goes Back, → goes Forward, ↑ opens the parent folder, and ↻ Refreshes the folder tree and current scan. Opening a different folder after going Back starts a new forward history from that point.

The folder tree always follows the pane's current location: it expands the parent folders, selects the exact scan starting folder, and scrolls that folder into view. The current folder remains closed until you expand it, preventing a temporary Loading placeholder from being displayed. This also happens after restoring a workspace or typing a path, so a drive root is not left highlighted while a deeper folder is being scanned. Include subfolders begins at the selected/current folder shown in that pane, not at the drive root above it.

Each pane has independent Back, Forward, Up and Refresh controls, filters, sorting, thumbnails, Info and Preview. Video preview starts at 4× speed. Comma and full stop move backward or forward ten percent. Preview and Info remain off until enabled to reduce background work.

The folder tree automatically aligns the currently visible branches to avoid wasted indentation. When you scroll down into deeper branches it shifts horizontally; scrolling back up to ancestors returns it left without requiring a click. The full hierarchy remains available, and the horizontal scrollbar beneath the tree permits manual horizontal viewing.

## Details And Thumbnails

Use the view selector at the top of either pane, or the View menu, to switch that pane between Details and Thumbnails. Both views show the same files and share their selection. Thumbnail mode respects Include subfolders, media switches, search, resolution, advanced filters, and sorting. Its Sort menu offers an exact direction for Name (A–Z/Z–A), Date modified (oldest/newest), File size, Length, Codec, Resolution, Type, Bitrate, Frame rate, and Rating. Each pane sorts independently, the button shows the active order, and saved workspaces and Smart Collections restore it. Details headings remain clickable for quick sorting. Relative paths appear beneath thumbnails during recursive scans. Use the thumbnail-size slider beside the view selector. Named size presets remain under View > Thumbnail size. Continuous is the default thumbnail browser: one scrollbar covers the complete filtered collection, while the program creates only visible cards plus a small buffer and recycles them during scrolling. This keeps widget and image memory bounded for very large libraries. Choose Paged beside it at any time to restore the established page grid; choose Auto, 200, 500, or 1,000 cards per page and use the compact ← and → controls. Auto uses 200 when videos are at least half the filtered results and 500 when images are the majority. Each pane and saved workspace remembers its browser choice.

The thumbnail grid measures the actual browser width before its first render and reflows automatically when a pane or the folder/browser divider is resized. In Paged mode, page 1 therefore uses the same column count as later pages for a given pane width and thumbnail size. In Continuous mode, resizing recalculates the virtual rows without constructing the whole collection. Roll the mouse wheel anywhere over a thumbnail pane—including over a card, image, or filename—to scroll that pane up and down; the two panes scroll independently.

In Details mode, the default order is Name, Codec, Resolution, Video length, File size, MB/min, FPS, Date modified, Type, Bitrate, Audio, HDR, Megapixels, Label, Tags, and Rating. Drag the divider between headers to resize a column by any amount; the horizontal-resize cursor shows when the divider is ready. Drag a header itself to reorder it—no keyboard modifier is required. A simple header click still sorts. Columns keep their chosen widths and the horizontal scrollbar reaches fields outside the pane. For precise control, choose View > Configure columns or right-click a header; the Columns window can move fields, set exact widths, and restore defaults. Existing personally arranged and saved column orders are preserved. Long recursive paths are shortened in the middle so the filename remains visible.

Video thumbnails are sampled 15% into the clip to avoid unrepresentative opening frames. If duration metadata is unavailable, the application uses a one-second fallback. Generated thumbnails are cached for faster repeat browsing.

Ordinary image thumbnails are decoded efficiently in-process with Pillow; FFmpeg is used for video frames and as a fallback for unusual image formats. Thumbnail decoding uses a small worker pool so a large folder cannot launch an excessive number of decoders. Cache images are written atomically and checked before display; incomplete or corrupt cached thumbnails are ignored and regenerated, while results belonging to an older grid are discarded safely.

Generated thumbnails remain available after the program closes, so revisiting an unchanged file normally uses its cached image immediately. Tools > Cache and scanning controls the maximum thumbnail-cache size as a percentage of the operating-system drive; the default is 1%. Reused thumbnails are marked as recent, and when the limit is exceeded the least recently used entries are removed first. The limit can be set from 0.1% to 10% and enforced immediately. Clear thumbnails reports the current count and size before confirmation, then removes only generated thumbnails—not original media or cached technical metadata. Clear all cache removes both thumbnails and metadata.

The thumbnail-size slider appears only in Thumbnails; Details hides it. Moving it adjusts thumbnail size continuously, and switching views retains its setting. Pause briefly after dragging it for the grid to reflow; the larger images keep their aspect ratio and the current size is saved with pane settings. Named size presets remain available in the View menu; there is no duplicate size dropdown in the pane heading.

## Scanning And Filtering

Enable Include subfolders to scan recursively. Use Find for filenames, Resolution for an exact resolution, and More filters for dimensions, file size, duration, codec, orientation, and date. Cancel stops a long scan. Cache and scanning settings under Tools control parallel workers and excluded patterns.

To save the scan results as a spreadsheet or document, see [chapter:media_reports].

Large recursive scans collect results without repeatedly rebuilding the growing browser. When scanning finishes, Details rows are added in short batches so Play/Pause, navigation, painting, and window controls remain responsive. Thumbnail grids likewise update at scan completion. Successful copy, move, and delete commands now update only affected in-memory entries instead of rescanning both folders; unfamiliar files dropped from outside the application still trigger a safety scan only in the affected pane. Metadata cache saving runs in the background, and stopped FFmpeg preview processes are cleaned up promptly. Tools > Cache and scanning provides Quiet, Balanced, and Fast performance profiles. Balanced retains the established behaviour. Quiet reduces scan and thumbnail concurrency and targets 8 preview frames per second; Fast increases concurrency and targets 15 frames per second. Quiet and Balanced pace new uncached probes and thumbnail decodes while a preview is playing or seeking, giving interactive work priority. Cached results are never deliberately delayed. The metadata-worker field remains adjustable after selecting a profile.

Each side has independent playback, timeline, speed, audio/mute, frame cache, and decoder processes. Scratch video playback is deliberately paced to real time at 12 frames per second. This keeps previews smooth while avoiding the heavy CPU use caused by decoding the rest of a clip faster than the preview can display it, especially while a large folder scan is running.

Click anywhere on either preview timeline to move its marker directly to that position and resume playback there. You can also press and drag the marker for continuous scrubbing. Scrubbing cancels an older frame request as soon as a newer position is requested, preventing several FFmpeg decoders from competing in the background. Recently visited positions are cached in quarter-second steps, so moving back to them is immediate. Release the slider to resume playback from the chosen position.

Video preview defaults to 4× speed for faster reviewing. Use the 1×, 2×, 4×, 6×, 8×, and 16× buttons beneath the timeline to change playback speed. The active speed button is disabled to make the current setting clear. Audio is muted by default; select 🔇 Muted to enable synchronized sound, and select 🔊 Audio to mute it again. Changing speed while playing restarts video and audio together at the current timeline position.

Use |◀ and ▶| beside the audio button to move backward or forward by one frame. The application uses the video's reported frame rate, with a 25 fps fallback when that metadata is unavailable, and performs a precise seek for the resulting still. Choose ⤓ PNG to export the current video position as a full-source-resolution PNG; playback pauses at that exact position, output is written through a temporary file, and the video is never altered.

With focus outside a typing field, press comma (,) to jump the active pane's video preview backward by 10% of its total duration, or full stop/period (.) to jump forward by 10%. The active pane is the side most recently clicked. A playing preview continues playing from the new position; a paused preview remains paused and displays the exact destination frame. The keys type normally in path, search, filter, and dialog fields.

Refresh active pane or Refresh both panes under View after folders or files are changed in File Explorer or another application. Refresh rebuilds the folder tree as well as rescanning media. It is also available through F5, the toolbar, and right-click menus in the browser and folder tree. Alternatively, enable Live independently in either pane to watch its current folder automatically. Live follows navigation and uses the same scope as Include subfolders. Bursts of creates, modifications, renames, and deletions are combined before refreshing; folder changes also update the tree. A Live marker appears in the completed scan status. Live defaults off, and clearing its checkbox immediately restores manual-refresh behaviour.

## Selecting And Previewing

Each pane has an independent tick-box action group. Click the ☐/☑ box beside a Details row or on a thumbnail card, or focus a Details row and press Space. Ticks remain collected while you highlight and preview other files, sort the pane, or change filters. The counter below the browser shows the total, including ticked files currently hidden by a filter. Click the ✓ Details heading or ✓ All shown in Thumbnails to tick every currently displayed file; repeat it to untick that displayed group. Clear ticks removes the complete group. Copy, move, drag, delete, rename, rating, tag, comparison, integrity and conversion actions use all ticked files when any exist; with no ticks they use the ordinary highlighted rows. Changing that pane to a different folder or drive clears its ticks, and ticks are not saved after closing the application.

Checkboxes change only when you click and release on the box without dragging. Empty space beside a box is not part of its clickable area. Moving more than a few pixels starts a highlight selection instead and leaves the ticks unchanged, even when the drag began on a checkbox. Use the explicit Tick selection and Untick selection controls to change an entire highlighted group.

Drag from empty browser space across rows or thumbnail cards to highlight a group with an outlined selection rectangle. This does not tick or untick any files. A plain drag starts a new highlighted group; hold Ctrl while starting the drag to add to existing highlights. Start on empty thumbnail space, not an image or filename, because dragging a thumbnail file starts a transfer instead. In Details you can also drag vertically across rows to highlight a group; drag towards the other pane for a transfer. Headers retain their normal resizing and reordering gestures. Use Tick selection to add the highlighted files to the existing ticked action group. Use Untick selection to remove only those highlighted files from that group. Both buttons are at the top of each browser beside Sort, Select all shown and Clear ticks; controls wrap on narrower panes. Both commands are also available in the right-click menus. Other ticks, including files hidden by filters, are retained. File actions continue to prefer all ticks when any exist, so use these explicit controls before copying or moving if you want to change the action group.

Each browser pane has its own large ▶ Preview toggle, which defaults off to avoid unnecessary decoding. Enable Preview on the left, right, or both sides to open separate aligned preview panels below the browsers. The button has a distinct selected state so enabled previews are easy to spot. When both toggles are off, the preview area collapses completely and the browsers use the full window height. Click a file to preview it on its own side. Highlighting is independent from ticks, so you can inspect or preview another file without losing the action group. Hold Ctrl while clicking thumbnails or detail rows to highlight several files. Select matching highlights every currently displayed result. Double-click opens the highlighted file in its normal application.

Images and video frames automatically use the largest size that fits their own preview panel while keeping the original width-to-height ratio. Resizing the main window or either preview divider updates the image after a short delay, avoiding repeated decoder restarts while the divider is being dragged.

Each pane also has a large independent ⓘ Info toggle. It defaults off and adds a collapsible inspector on that pane's right edge. If a file is already selected, enabling Info displays it immediately—there is no need to select it again. The inspector follows later selection in Details, Continuous thumbnails, and Paged thumbnails and shows the full path, dimensions, size, dates, duration, codec, frame rate, bitrate, pixel format, HDR, audio, unreadable reason, rating, colour, and tags. Copy path places the full path on the clipboard; Open and Reveal use the normal file actions. Turning Info off removes the inspector completely, and saved workspaces remember its state. Info opens at a compact starting width of about 180 pixels. The top Sort and selection controls are independent of the Info divider, so opening Info does not squeeze those buttons. Drag the divider beside the inspector to change its width; turning Info off and on restores that width, and saved pane/workspace settings retain it. On narrow windows the width is limited to leave some space for browsing.

Show in File Explorer/Reveal works with the complete selection. With up to five selected files it sends a separate reveal request for every path. Above five, a warning shows the exact count because the operation may open many file-manager windows. Choose Yes to reveal every selected file or No to reveal only the first. Windows and macOS select each exact file; Linux opens each file's containing folder through the system file manager.

For camera information, EXIF fields or video container/stream tags, see [chapter:embedded_metadata].

## Copying And Moving

Select files in one pane and use the toolbar, Edit menu, right-click menu, keyboard shortcuts, or drag-and-drop. To send several selected files to another application such as Shutter, drag the large ↗ Drag selected handle beside that pane's navigation controls with the left mouse button. It exports the complete selection using the normal operating-system file-list format and works in both Details and Thumbnails without interfering with column resizing. The other pane is the destination for in-app transfers. Transfers enter a queue with progress, speed, remaining time, pause, cancel, retry, and conflict choices. Pane transfers let you choose whether to preserve relative folders or copy just the files.

Edit > Batch rename selected opens a complete preview before changing any names. The preview updates automatically after you change the pattern, find/replace text, case sensitivity, start number or padding; Refresh preview is also available. Build names with {name} for the original stem, {n} for a padded sequence number, {ext} for the extension without a dot, and {dotext} for the extension including its dot. Optional find/replace can be case-sensitive or insensitive, and numbering has adjustable start and padding. Invalid Windows names, duplicate outputs, and conflicts with unselected files disable Apply. A confirmed batch uses temporary names internally so swaps and cycles cannot overwrite one another; an interrupted batch is rolled back where possible. The successful batch is one Ctrl+Z undo action, including ratings and tags. F2 or Rename on one file opens a live filename preview; Rename is enabled only for a valid, available new name.

For repeatable copy/move conditions with a review before applying, see [chapter:folder_organization_rules]. To pause, cancel or retry queued transfers, see [chapter:transfer_queue].

Right-click one or several selected files to assign a zero-to-five-star rating, a Red/Yellow/Green/Blue/Purple colour label, or comma-separated tags. Clear rating, None, and an empty tag list reverse those changes. These annotations are stored only in the application database; original media and embedded metadata are never altered. Details mode provides sortable Rating, Label, and Tags columns. Thumbnail captions show ratings/tags and use the colour label as their unselected outline. More filters can require a minimum rating, colour (including Unlabelled), or tag text. Internal rename, copy, move, and undo operations carry annotations to the resulting path. Clear all cache removes technical cache data but deliberately retains user annotations.

In Details mode, individual rows retain right-button file dragging; a normal right-click still opens the context menu. You can also drag a row or selected group with the left button into the opposite pane. A drop offers clearly labelled Copy, Move and Cancel buttons. Copy or Move opens the transfer preview; Cancel or closing the prompt leaves the files unchanged. Header resizing and reordering remain independent. For conventional left-button dragging into another program, use ↗ Drag selected. Thumbnail cards also support ordinary left-button file dragging.

Copy, move, rename, send files to the Recycle Bin or Trash, review duplicates, apply tags and ratings, export reports and create contact sheets. Conversion supports H.264, H.265 and AV1 with compatible hardware acceleration. Source files are retained and partial failed outputs are removed.

New folders: choose File > New folder…, press Ctrl+Shift+N, or right-click in a pane and choose New folder…. Enter the name of a single new folder. The folder is created inside the active pane's current folder and the browser refreshes; this does not move your selected files. Empty, reserved and invalid names are rejected, and an existing folder is never replaced.

Copy/move example: enable Include subfolders in the source pane, tick files in several subfolders, and click Copy selected → other pane or Move selected → other pane. In the preview choose Preserve folder structure to keep paths below the source folder, or Files only (no subfolders) to put files directly in the destination. The first default preserves folders; later transfers remember your last choice. Read the Source, Destination and Status columns before queuing. Browse… changes the destination; New folder… creates and selects a folder without abandoning the preview. Open destination when complete opens that folder only after a successful, uncancelled transfer. Click Queue copy or Queue move to proceed, or Cancel to leave files unchanged. Paste and dropped files use this preview too.

Conflicts: Ask for each conflict offers Keep both, Replace, Skip and Cancel, with Apply to all remaining conflicts. Alternatively choose a policy in the preview before queuing. Keep both finds an available numbered filename such as clip (2).mp4, including collisions between selected files from different subfolders. Replace explicitly allows replacement and keeps the previous destination in the session undo area. Skip leaves the existing destination unchanged. A destination that is one of the selected source files is blocked: choose another folder. The queue rechecks destinations, so a file appearing after preview is not silently overwritten. Undo is limited to the last 20 supported actions in this session and is not a permanent backup. Do not edit transferred files before using Undo; undoing a copy removes the copied file.

Selection basket: use the Selection basket toolbar button, File > Selection basket…, or right-click selected files and choose Add to selection basket. The basket is a collapsible panel above both browsers, not a separate window. Hide basket or the toolbar button hides it without clearing its references. Add pane selection gathers the pane's ticked action group, or its highlighted files when no ticks exist. Visit other folders and add more files; each original path appears only once. The basket contains references, not copies, and clears when the application closes. Remove references or Clear basket does not delete originals. Select basket rows and choose Copy to active pane or Move to active pane; when no basket rows are selected, all entries are used. Review the normal transfer preview. Basket files without a shared browsing root use their filenames rather than a combined folder tree. Missing originals are marked [missing] and cannot be transferred until available.

## Smart Collections: Saved Searches

WHAT SMART COLLECTIONS SAVE

A Smart Collection is a named, saved search and view for one browser pane. It remembers how to find and display files at a source folder. It references the original files; creating, opening, renaming or deleting a collection does not copy, move, rename, delete or annotate those media files. Use it when you repeatedly review the same library with particular filters and sorting, instead of re-entering those settings on every visit. A saved workspace restores both panes and their layout; a Smart Collection changes only the active pane.

Each collection has exactly one starting folder. Include subfolders searches all folders beneath that root. It cannot combine arbitrary unrelated folders, separate drives, or multiple starting roots into one collection. Choose their nearest common parent where practical, or save separate collections and open them in the two panes. Selecting a drive root with Include subfolders can scan the whole drive; choose the narrowest useful parent folder.

The saved settings are the folder path, Include subfolders, Videos and Images switches, Find text, Resolution selection, every More filters value, sort field and direction, Details or Thumbnails, thumbnail size, and Continuous or Paged mode. It does not save ticked files, highlighted selections, preview playback, live monitoring, the other pane, column widths/order, pane dividers or thumbnail page capacity. These remain independent settings. Collections are stored locally in smart_collections.json in the application settings directory.

CREATE A COLLECTION

1. Click inside the pane you want to configure. This makes it the active pane for Tools commands.
2. Use Browse… or the path box to open the intended source folder. Enable Include subfolders if nested folders belong in the search.
3. Tick Videos, Images, or both. Set Find for a case-insensitive filename or relative-path substring, and choose Resolution for an exact width × height where wanted. The display says Resolution: All when no exact resolution restriction is applied.
4. Open More filters… for orientation, codec substring, tag substring, minimum rating, colour label, minimum/maximum width and height, file size, duration and modification dates. Empty fields impose no limit; all non-empty restrictions must match. Enter Apply to use the filters. Clear resets the advanced filter values. This is not a separate arbitrary-extension filter; use the Videos/Images switches and, where suitable, a filename substring such as .mp4.
5. Wait for the scan and choose the required order. In Details, click a column heading; click again to reverse direction. In Thumbnails, use Sort and its field/direction submenu. Both views use the same filtered media and order.
6. Choose Tools > Save active smart collection… and enter a descriptive Collection name. Saving an existing name asks Replace smart collection; agree only if the current pane should replace that saved definition. Saving creates a preset, not a copy of the displayed files.

OPEN AND UPDATE A COLLECTION

Choose the destination pane first. Open Tools > Manage smart collections…, select a saved entry, and click Apply or double-click the row. The active pane navigates to the saved starting folder, restores the saved filters, sorting and presentation, then scans it. The opposite pane is unchanged. If the folder is disconnected, moved or no longer exists, Collection folder unavailable explains the saved path; reconnect it or save a replacement using a valid folder.

Results reflect files currently found when the pane scans, rather than a frozen list captured when the preset was saved. Use the pane's ↻ button, View > Refresh active pane, or F5 for both panes after external file changes. Live can watch the current folder, but Live is not part of a saved collection. Changes to filtering or sorting affect the current view immediately; changes to source scope require the corresponding scan. Cancel stops a scan. Large recursive collections use the same metadata cache and performance profiles as ordinary browsing.

There is no separate collection Edit button. To change an existing collection, Apply it, adjust the folder, scope, filters or ordering in that pane, then choose Tools > Save active smart collection… with the same name and confirm replacement. In the manager, Save current saves the current active-pane settings and asks for a name; it does not automatically edit the selected row. Renaming does not save any changes made to a pane's filters.

RENAME, DELETE AND RESTORE

In Tools > Manage smart collections…, choose an entry and click Rename. Enter New name: and confirm replacement if another collection already has that name. Delete asks for confirmation and removes only the preset. Undo delete restores the latest deleted preset while this manager window remains open. Closing the manager loses this temporary undo stack. If a same-name collection has subsequently been created, restoring the deleted entry replaces that name's preset, so use distinct names when preserving both. Close exits without applying a selected row. Ctrl+Z is for file operations, not collection-manager deletion.

EXAMPLE: SORT IMAGES ACROSS SUBFOLDERS BY RESOLUTION

1. In the left pane, Browse… to your Pictures parent folder, enable Include subfolders and Images, and turn Videos off.
2. Clear Find and set Resolution to All if you want to compare all dimensions. Open More filters… and Clear/Apply if old restrictions should be removed.
3. In Details, click Resolution until the desired ascending or descending order appears. Or choose Thumbnails and Sort > Resolution > Smallest first or Largest first. Resolution sorting uses pixel area (width × height), with width and height breaking equal-area ties; it is not a simple width-only sort. An exact Resolution filter restricts to one specific dimension pair instead.
4. Save the active pane as Images by resolution. Later Apply this entry in either pane to repeat the search, including newly added matching files after scanning.

EXAMPLE: REVIEW HIGH-RESOLUTION VIDEOS

1. Browse… to a Videos parent folder, enable Include subfolders and Videos, and turn Images off.
2. In More filters…, set Minimum width (pixels) to 1920 and Minimum height (pixels) to 1080 if you want videos meeting BOTH dimensions. This excludes portrait videos narrower than 1920, even when they have high pixel counts; adjust the limits or use Orientation according to your goal.
3. Leave Resolution at All to include different qualifying dimensions. Optionally set Codec contains to hevc to match the stored HEVC codec label, or H.264 for H.264. The filter matches the displayed codec label literally, ignoring letter case; h264 without the dot does not match H.264. Use Info to see a file's actual codec if a filter finds nothing.
4. Sort by Resolution in Details or Thumbnails. Other supported sort fields include Name, Date modified, File size, Length, Codec, Type, Bitrate, Frame rate and Rating. Save as High-resolution videos. Use Preview or Info when needed to review individual results; enabling them is independent of the collection definition.

LIMITATIONS AND FILE ACTIONS

A collection is a preset over accessible files, not an indexed library spanning disconnected drives, a background automatic rule, a playlist, a duplicate group or a physical folder. Changing a preset never reorganises files automatically. File copy/move/delete commands you deliberately run on its results still act on the original media. Existing ticks take precedence over highlighting and can include files hidden by filters; check the tick counter and Clear ticks before acting on an unintended group. Navigating to a different folder clears that pane's ticks. Collection application may leave existing ticks when the starting folder stays the same, so always review them before file actions.

See also: [chapter:scanning_and_filtering] · [chapter:details_and_thumbnails] · [chapter:workspaces_and_cache] · [chapter:safe_file_actions]

## Duplicates And Comparison

Tools > Find duplicates finds exact matches in stages. Same-size files receive a quick fingerprint sampled from the beginning, middle, and end; only matching candidates are then read completely and verified with SHA-256. Both fingerprints are retained in the SQLite cache while path, size, and modification time remain unchanged, making later searches much faster. Progress appears in the active pane status line. The review window shows two copies side by side with paths, dates, and retention labels. A strategy only selects proposed redundant files—it never deletes them automatically. Compare selected shows two chosen files and their technical metadata.

Tools > Find visually similar images detects resized, lightly recompressed, and otherwise visually close images even when their files are not byte-for-byte identical. Choose Visible or All scanned and a tolerance from 0–16; lower values are stricter and 6 is the default. The 64-bit difference hashes are cached against path, size, and modification date, and a BK-tree keeps matching practical on large collections. Results are estimates and open in a review-only window with previews and a Select this group action. The tool never deletes or changes files; review every proposed group before using normal file actions.

USING THE REVIEW TOOLS

For exact duplicates, open the source folder, enable Include subfolders if required, wait for scanning and choose Tools > Find duplicates…. It examines all media scanned in that pane, not only highlighted or filter-visible files. Review the grouped paths and side-by-side previews, then choose a keep strategy to highlight the proposed redundant copies in the source pane. This does not delete them. Clear existing ticks and inspect the proposed highlights before running a file action.

For visually similar images, choose Tools > Find visually similar images…, select Scope: Visible or All scanned, set Similarity tolerance (0–16), and click Start. Begin with 6; lower is stricter. Select a result to preview it; Select this group in source pane highlights the group, including the reference image. It is not an automatic selection of only unwanted copies.

To compare a pair directly, clear unwanted ticks, select exactly two files in one pane and choose Tools > Compare selected…. Check their previews, paths and properties. Keep left (recycle right) and Keep right (recycle left) request confirmation before sending the other file to the Recycle Bin / Trash. Closing without either action leaves both files unchanged.

## Video Conversion

Use Tools > Convert selected videos… to create new video files with a different codec, container or resolution. The originals are retained. Choose a small sample first so you can compare its quality, playback compatibility, file size and conversion time before processing a large group.

CONVERT ONE OR MORE VIDEOS

1. Open the source folder in either pane. Enable Include subfolders if the videos are spread across its subfolders, and wait for scanning to finish.
2. Tick the videos to convert. If there are no ticks, the command uses highlighted files instead. Clear unwanted ticks first: a ticked file hidden by a filter still belongs to the action group. Images in the group are ignored by this command.
3. Choose Tools > Convert selected videos….
4. Choose Preset, Resolution, Quality (CRF) and Encoding engine as described below.
5. Check Output folder. It initially points to the other pane's folder; use Browse… or enter a different destination if required. Check Preserve folders relative to the active pane to retain the source subfolder structure beneath that destination.
6. Choose Skip existing or Keep both. Click Refresh preview after changing the destination, folder preservation or existing-file policy. Read every Source and Output path and check the Status column. Only Ready rows will run.
7. Click Start conversion… and review the confirmation before agreeing. Watch the progress and per-file Result. When finished, open a converted file and check it before deciding what to do with the original.

CHOOSING A PRESET

H.264 MP4 (compatible): a useful choice when broad player/device compatibility matters.
H.265 MP4 (smaller): HEVC encoding, which can reduce file size but needs a compatible player.
AV1 MKV (smallest): AV1 encoding in an MKV container; check playback support and conversion speed on your computer.
720p H.264 proxy: a lower-resolution H.264 copy useful for quicker browsing or review. Selecting this preset sets Resolution to 720p; you can change it before starting.
Remux to MKV (no re-encoding): copies the existing streams into MKV. It does not change the video codec, resolution or quality, and is not a way to convert H.264 to H.265. Re-encoding preset names are not a guarantee that every output will be smaller than its source.

RESOLUTION AND QUALITY

Keep source resolution retains the original frame dimensions when re-encoding. 1080p and 720p set the output HEIGHT to 1080 or 720 pixels while preserving the aspect ratio; they are not maximum-width or automatic downscale-only settings. For example, a 3840 × 2160 video becomes 1920 × 1080 at 1080p. A smaller source can be enlarged, which does not restore missing detail. Portrait videos keep their proportions rather than becoming landscape.

Quality (CRF) accepts whole numbers from 18 to 35; the default is 23. Lower numbers request higher quality and usually larger files. Hardware engines map this value to their own quality control, so equal values need not produce identical results across engines. Try a sample. Remux ignores quality, resizing and acceleration.

ENCODING AND DECODING

Automatic (recommended) tries available hardware encoding options and falls back through alternatives to Software / CPU if necessary. Software / CPU uses the processor. NVIDIA NVENC, Intel Quick Sync, AMD AMF and Linux VA-API are offered where supported for the chosen preset. The detection summary reports FFmpeg support; the selected hardware and drivers must also work. An explicitly selected hardware engine reports failure instead of silently switching to a different encoder.

Use hardware decoding when available controls reading the source independently of the output encoder. If a requested hardware decoder cannot start, decoding is retried in software while keeping the chosen encoder. Uncheck it when you want software decoding. These settings do not change the original file.

OUTPUT NAMES, PROGRESS AND CANCELLATION

New filenames include a preset suffix and, when chosen, the output resolution. Skip existing leaves an existing target alone. Keep both uses a numbered filename instead of replacing it. Check the preview for skipped files, duplicate output names or other problems before starting.

Videos are processed one at a time. Cancel conversion stops the current conversion, removes its unfinished output and stops the remaining queue. Completed outputs remain. Closing this conversion window also requests cancellation. Its queue is separate from Tools > Transfer queue…, which manages copying and moving.

EXAMPLE: H.264 TO H.265 AT 1080p

Tick a few H.264 videos, open Tools > Convert selected videos…, choose H.265 MP4 (smaller), set Resolution to 1080p, leave Quality (CRF) at 23 for an initial trial, and choose Automatic (recommended). Choose an output folder, click Refresh preview, inspect the paths, then Start conversion…. Compare the finished copies with the originals; adjust quality or resolution and test again if needed.

## Exporting a Media Report

Tools > Export media report… saves an inventory of files already scanned in the active pane. It does not copy, convert or modify those media files. Use CSV for a spreadsheet, JSON for structured data, or HTML for a report you can open in a web browser.

CREATE A REPORT

1. Open the folder you want to catalogue. Enable Include subfolders if required and let the scan finish.
2. Apply filters if you want a report of a particular group, such as H.265 videos or high-resolution images. Click inside that pane to make it active.
3. Choose Tools > Export media report….
4. Set Scope to Selected, Visible or All scanned.
5. Choose Format: CSV, JSON or HTML.
6. Leave Include full file paths ticked to record complete locations, or untick it to use paths relative to the active folder where possible.
7. Click Export…, choose the report's filename and destination, then Save. Wait for Report exported. Open the saved file in the appropriate spreadsheet, browser or data viewer.

WHAT SCOPE MEANS

Selected uses the pane's ticked files when ticks exist; otherwise it uses highlighted files. Hidden ticks can therefore be included. Visible means ALL files matching the current pane filters, not just the rows or thumbnails currently on screen or the current thumbnail page. All scanned includes the pane's scanned media even if current filters hide them. None of these options scans another drive or folder automatically.

WHAT THE REPORT CONTAINS

Each item includes its name and path, media kind and extension, dimensions/resolution, size, modification date, duration, video codec, bitrate, frame rate, audio codec/channels, pixel format, HDR, rating, colour label, tags and readable/error status where available. Missing information remains missing; exporting does not run a full integrity check. JSON includes a summary and item list. HTML includes a summary and table. CSV contains the per-file table.

EXAMPLE AND CANCELLATION

To list large videos across subfolders, open their common parent folder, enable Videos and Include subfolders, set the size restriction in More filters…, then export with Scope: Visible and Format: CSV. Open the CSV in your spreadsheet and review the sizes and paths.

Cancel export stops an export in progress; Close also requests cancellation. A report is only placed at its final filename when writing completes, so cancellation does not leave a partly written final report. Review paths before sharing a report: full file paths can reveal folder names.

## Viewing Embedded Metadata

Tools > View embedded metadata… reads information stored inside one image or video. This is different from the application's own ratings, colour labels and tags, which do not change the media file.

1. Clear unwanted ticks, then select exactly one image or video in the active pane.
2. Choose Tools > View embedded metadata… and wait for the fields to appear.
3. Read the Section, Field and Value columns. Images may include camera/date EXIF information and GPS fields when present; videos may include container and stream tags. Not every file contains these fields.
4. Type in Find to narrow the displayed rows by their section, field or value.
5. Select rows and click Copy selected/all to copy them. With no row selected, it copies all currently displayed rows.
6. Click Export JSON… to save all extracted metadata, including rows hidden by Find. Choose a filename and Save.
7. Close the window when finished. Viewing, copying and exporting metadata do not edit embedded information in the original file.

## Checking Media Integrity

Tools > Verify media integrity… checks whether media can be decoded, rather than relying only on its filename or technical header. Use it to investigate unreadable files or check a batch before archiving. Reading entire videos can take considerable time. It never repairs or changes the originals.

1. Open the source folder, set Include subfolders as needed, and let scanning finish.
2. Choose Tools > Verify media integrity….
3. Set Scope: Selected for ticked/highlighted files, Visible for all filter-matching files, or All scanned to include files hidden by filters.
4. Tick Force recheck if you want a new check even when a previous result is cached.
5. Click Start. Review Status, Cached, Path and Details as results arrive. Passed means the decoder completed its check; Failed records a decoding or access problem. It is not a guarantee of visual quality, correct content or the absence of malware.
6. Use Cancel to stop further checking. Results already collected remain available.
7. Click Export CSV… to save the collected results, including when a check was cancelled. Select failed highlights failed files back in the source pane and closes the results window; it does not delete them.

Before acting on highlighted failures, inspect their details and check Clear ticks: existing ticks still take priority for subsequent file commands. A failure can reflect permissions, missing drives or decoder support as well as damaged data. Do not delete files solely because one check failed.

## Creating a Video Contact Sheet

A contact sheet is one PNG containing a grid of still frames from a video. It gives an overview without playing the whole clip. Tools > Create video contact sheet… does not change the source video.

1. Clear unwanted ticks and select one video in the active pane.
2. Choose Tools > Create video contact sheet….
3. Set Number of frames (4–48), Columns (2–8) and Frame width (pixels) (160–640). The defaults are 12 frames, 4 columns and 320 pixels.
4. Leave Show frame numbers and timestamps ticked if you want captions beneath the frames.
5. Click Create…, choose the PNG filename and destination, and Save.
6. Wait for Contact sheet complete, then open the saved PNG in an image viewer. Cancel stops extraction; Close also requests cancellation.

Frames are sampled evenly through the clip, avoiding its exact first and last frames. This is not scene detection, and the tool needs a readable video duration. Larger grids and frames take longer and create a larger image. For a quick overview, start with the default 12-frame sheet.

## Folder Synchronization

Open the folders to compare in the left and right panes, then choose Tools > Compare / synchronize folders. Review Left only, Right only, Newer, and Different entries before queuing a one-way synchronization.

1. Open the two folders in the left and right panes. Set Include subfolders independently for each side if required.
2. Choose Tools > Compare / synchronize folders….
3. Review Relative path and Status: Left only, Right only, Same, Left newer, Right newer or Different. This comparison uses supported media files, file sizes and modification times; Same is not a full-content hash check. It inventories the folders independently of the pane's Find/media display filters.
4. Highlight particular rows to limit the operation. If no rows are highlighted, the direction buttons consider the entire comparison.
5. Click Copy missing/newer → right or Copy missing/newer → left. Only applicable missing, newer or Different files in that direction are proposed. Read and confirm the file count before queuing.
6. Follow progress in Tools > Transfer queue…. This copies files in one direction; it does not remove extra destination files or perform automatic two-way mirroring. Run the comparison again after copying if you want an updated result list.

## Folder Organization Rules

Tools > Folder organization rules… saves repeatable Copy or Move rules. Unlike Smart Collections, applying these rules really changes file locations or creates copies. Rules do not run automatically in the background: review the preview and confirm Apply… each time.

WHAT YOU CAN ACHIEVE

Use rules to copy favourite photos into a sharing folder, move videos with a project name into a project folder, separate videos by their existing codec, or collect files you have tagged for "review". Each rule sends matching files to one fixed destination. The rule name is just a label for you; it is not a search condition. Copy leaves the source in place; Move relocates it. Neither action converts, renames or edits the media, assigns ratings/tags, or creates a live synchronised collection. Use Smart Collections instead when you only want a saved view without copying or moving files.

CREATE OR EDIT A RULE

1. Click the pane containing the files you want to organise, then choose Tools > Folder organization rules….
2. Click Add. Enter Rule name, choose Action: Copy or Move, and set Destination folder using Browse… if needed. Check Action carefully: a new rule initially uses Move.
3. Set Media kind to Any, Images or Videos. Optional conditions are Extensions (comma separated), Filename contains, Codec contains, Minimum rating (0–5), and Required exact tag. Leave unused conditions empty; 0 imposes no minimum rating restriction. All entered conditions must match. Filename and codec matching ignore letter case; the tag must match a whole assigned tag, not part of one.
4. Leave Rule enabled ticked if the rule should participate, then click Save rule.
5. Select an existing rule and Edit to change it. Use ↑ and ↓ to change precedence: the first enabled matching rule wins. Delete removes a rule after confirmation, not its media; Undo delete is available while this manager remains open.

HOW CONDITIONS WORK TOGETHER

All filled conditions in one rule mean AND: a Videos rule with Filename contains set to "holiday" and Minimum rating set to 4 needs a video whose filename contains "holiday" AND whose assigned rating is 4 or 5. A matching name alone is insufficient. Leave text conditions blank, Extensions blank, Media kind at Any and Minimum rating at 0 for no restriction from those fields. A rule with no restrictions matches every file in the chosen preview scope, so place a general catch-all rule last. For alternative words or tags, make separate rules with the same destination; entering a comma-separated list in Filename contains or Required exact tag does not mean OR.

MEDIA KIND AND EXTENSIONS

Media kind limits a rule to Images, Videos, or either kind (Any); it does not include arbitrary documents outside the application's supported media. Extensions checks the final filename suffix: mp4 matches .mp4 and .MP4, and jpg, jpeg, png accepts any of those three extensions. A leading dot is optional. Extensions is a list field; the other text conditions are not. MP4 and MKV are containers, not codecs: use Extensions for a file format and Codec contains for the encoding shown in the pane.

FILENAME CONTAINS: A PIECE OF THE ACTUAL NAME

Enter ordinary text without quotation marks. "holiday" matches "Beach_Holiday_2026.mp4" and "holiday-photo.jpg", ignoring letter case. It searches the whole filename, including its extension, but not parent folder names or the image/video content. A file called "clip.mp4" inside a "Holiday" folder does not match "holiday". Spaces and punctuation matter: "summer holiday" does not match "summer_holiday". There are no wildcards, regular expressions or exclusion expressions here; "*.mp4" is treated as literal text, so put mp4 in Extensions instead. To match "holiday" OR "birthday", create two rules.

CODEC CONTAINS: THE ENCODING ALREADY REPORTED

Look at the Codec column or Info first and enter part of that displayed codec label. HEVC matches H.265 / HEVC; H.264 matches H.264. Matching ignores letter case but keeps punctuation, so h264 without the dot does not match H.264. Do not use mp4 here when you mean an MP4 filename extension. This condition reads the item's Codec value, not every audio stream or embedded metadata tag. It neither converts a video nor changes its codec. If the codec is Unknown, an HEVC rule will not match; check that the scan completed and the file is readable.

MINIMUM RATING: STARS YOU ASSIGN IN THIS APP

Select or tick your files, right-click and use Rating to assign one to five stars before previewing the rule. With ticks present, rating actions use the ticked group; clear unrelated ticks first. The application does not judge quality or automatically award stars. Unrated files have rating 0. Minimum rating 4 accepts both 4-star and 5-star files, not just exactly 4; 5 accepts only 5-star files; 0 includes unrated and rated files. This field cannot select only unrated files, a maximum rating or an exact middle rating. Ratings are local application annotations, not ratings read from or written into the media's embedded metadata.

REQUIRED EXACT TAG: A LABEL YOU ASSIGN IN THIS APP

Select or tick files, right-click and choose Edit tags. Enter tags separated by commas, for example "holiday, family, review". Saving replaces the tag list on every file in that action group; include tags you want to keep. These are local application labels, not embedded EXIF/video tags or words detected in a picture. In the rule, enter one whole tag, for example "review", without quotes. Matching ignores letter case: "Review" matches "review", but "review" does not match "needs-review", and "family" does not match "family holiday". The rule field accepts one required tag; "review, family" is not a request for either or both tags. Make separate rules for either tag. One rule cannot require two separate exact tags.

PREVIEW AND APPLY

1. Set the source pane's filters if you want to restrict the files considered.
2. In the rules manager, click Preview active pane….
3. Choose Scope: Visible for the pane's filter-matching files or All scanned for its complete scanned set. This tool does not have a Selected scope.
4. Choose whether to Preserve folders relative to the active pane. Checked keeps relative subfolders beneath each rule's destination; unchecked uses just the filename.
5. Click Refresh preview after changing these controls. Review Rule, Action, Source, Destination and Status. Unmatched files are not queued. Resolve problems such as Duplicate target before applying.
6. Click Apply… and confirm the proposed action count. Copy/move work enters the normal transfer queue; existing targets use the normal conflict choices. Close leaves the preview without applying it.

EXAMPLE

To copy MP4 videos into a review folder, Add a rule named MP4 review copies, choose Copy, choose the review destination, set Media kind to Videos and Extensions to mp4, then Save rule. Preview active pane… with Scope: Visible, inspect the paths and Apply…. This creates copies; choose Move only when you intend to relocate originals.

MORE WORKED EXAMPLES

Project videos: choose Copy, destination Project copies, Media kind Videos and Filename contains "wedding". Leave the other text fields blank and Minimum rating at 0. "Wedding_ceremony.mp4" matches; "clip.mp4" in a "Wedding" folder does not.

Favourite "holiday" photos: choose Copy, destination "Holiday" favourites, Media kind Images, Minimum rating 4 and Required exact tag "holiday". First assign the "holiday" tag and 4 or 5 stars to the photos you want. A 5-star photo tagged "work" fails; a 3-star photo tagged "holiday" also fails. Nothing needs "holiday" in its filename.

HEVC "review" copies: choose Copy, destination HEVC "review", Media kind Videos and Codec contains HEVC. Leave Extensions empty to accept supported containers such as MP4 and MKV; add mp4 only if you also want to require MP4. Outputs keep the original encoding.

Approved project videos: choose Copy, destination Approved project, Media kind Videos, Extensions mp4, Filename contains "wedding", Codec contains H.264, Minimum rating 4 and Required exact tag "approved". Every condition must match. Begin with fewer conditions and add them one at a time if this finds no files.

RULE ORDER: FIRST MATCH ONLY

Suppose the first rule copies 5-star Images to Best photos and the second copies all Images to Photo archive. A 5-star image uses only the first rule; it is not copied to both destinations. Other images reach the second rule. Reverse the order and the general Images rule catches every image before the favourites rule. Move specific rules above general ones with the arrow buttons. Disabled rules are skipped. An unsuitable destination on the first matching rule does not make the file fall through to another rule; fix the preview problem or change the order.

DESTINATION FOLDERS AND PREVIEW SCOPE

With the active source folder Media and a file at Media/2026/Trip/"clip.mp4", destination "Review" plus Preserve folders relative to the active pane produces "Review"/2026/Trip/"clip.mp4". Without that option the target is "Review"/"clip.mp4". Enable Include subfolders in the pane to scan nested files in the first place. Keeping folders can prevent two same-named files from different subfolders collapsing onto one target; without it the preview can report Duplicate target. Each rule has a fixed destination: it does not invent date/tag/codec folder names from templates. To route more groups to different folders, create more rules. Visible respects the active pane's current filters; All scanned considers its scanned set, not unscanned folders or every drive. Ticks do not supply a Selected scope for this tool.

IF THE PREVIEW IS EMPTY OR UNEXPECTED

Check the active source pane, scanned files, Scope and pane filters first. Confirm the rule is enabled, then temporarily remove optional conditions and add them back one at a time. Compare the actual filename, Codec, Rating and Tags in Details/Info with what you typed. Check for a more general rule above yours. Click Refresh preview after changes. Unmatched files stay where they are; Already in destination needs no transfer. Target exists uses the normal conflict choices, while Duplicate target and other problem rows must be resolved before Apply becomes available. "Review" every destination before confirming Apply. Rules do not run automatically when new files arrive: preview and apply them again when wanted.

## Managing the Transfer Queue

Tools > Transfer queue… shows progress for queued copy and move work, including transfers started by folder synchronization and organization rules. Video conversion has its own separate progress window.

1. Start a copy or move using the pane controls or file commands. Open Tools > Transfer queue… if its progress window is not already visible.
2. Read the current operation, progress, queued count and transfer details.
3. Click Pause to suspend copying at a safe point; the button becomes Resume. Resume continues the transfer. A move already being performed may need to finish before responding.
4. Cancel current requests that the active job stop. It does not clear every pending job, and successfully completed files are not automatically undone.
5. Retry failed requeues files that failed in the most recent failed transfer. Check the reported error and destination first.
6. Close hides the progress window; it does not cancel copying or moving. Reopen it from Tools to check progress. Use Ctrl+Z separately to undo a supported completed file operation.

## Safe File Actions

Delete sends files to the operating-system Recycle Bin or Trash. After a delete or move, the file that follows the removed selection in the active sort order is automatically selected and revealed; if the removed files were at the end, the new final file is selected. Rename and refresh also retain a useful current file, and this behaviour is shared by Details and Thumbnails. Undo reverses recent copies, moves, replacements, single renames, and complete batch renames. Replacement conflicts offer Replace, Skip or Keep both, with a choice to apply the answer to all remaining conflicts.

Undo runs in the background so the window remains responsive. It temporarily stops the previews and pauses new metadata and thumbnail file reads while existing reads finish, then restores the files. You do not need to wait for a folder scan to finish first. Brief Windows file-sharing locks are retried automatically. If another program still holds a file, or a restored source would replace a newly created file, Undo stops and reports the problem rather than overwriting it. Completed recovery steps are retained; unfinished steps and original replacement backups remain available. Close the application using the affected file or resolve the reported conflict, then press Undo again to resume. Queued transfers wait while recovery is incomplete. Do not delete recovery backups or edit the affected files while recovery is incomplete. Preview toggles remain as chosen; select a file again after recovery to resume previewing.

## Workspaces And Cache

Saved workspaces remember folders, filters, view modes, columns, inspectors, and layout. Smart Collections under Tools are smaller one-pane presets: they save the folder, Include subfolders and media switches, filename and advanced filters, resolution, sorting, Details/Thumbnails view, thumbnail size, and Continuous/Paged choice. Applying one affects only the active pane. The manager can rename or delete presets; deletion requires confirmation and Undo delete restores it while the manager remains open. Smart Collections never move, delete, or annotate media. Cached metadata and thumbnails speed up future visits; Tools > Cache and scanning can inspect, prune, or clear them.

SAVE AND LOAD A WORKSPACE

1. Arrange both panes with the folders, filters, views and layout you want to reuse.
2. Choose Tools > Save workspace… and enter Workspace name. Reusing a name replaces that workspace without a separate replacement prompt; use a new name to preserve the earlier layout.
3. Later choose Tools > Load workspace…. The prompt lists saved names. Enter the exact name shown and confirm to restore both panes. Cancel leaves the current workspace unchanged.

Use [chapter:smart_collections] instead when you only want to restore one pane's search and view.

CACHE AND SCANNING CONTROLS

Open Tools > Cache and scanning… to see metadata entries and thumbnail storage. In Scan settings, choose Performance profile: Quiet for lower background load, Balanced for normal use, or Fast for higher throughput. Adjust Parallel metadata workers (1–16) if needed. Exclude patterns (semicolon separated) can omit matching paths; examples shown in the window include *.tmp; proxy/*; @eaDir/*. Click Apply to save the settings. Refresh the pane to run a scan using changed exclusions.

In Thumbnail storage, Maximum percentage of operating-system drive defaults to 1% and accepts 0.1%–10%. Apply saves the limit; Enforce limit now removes the least recently used cached thumbnails until the limit is met.

Remove stale entries prunes outdated metadata entries. Clear thumbnails asks for confirmation, then deletes generated thumbnail pictures only; they will be rebuilt as needed. Clear all cache confirms removal of technical cache data and thumbnails, so future visits need fresh scanning/decoding. These cache controls do not delete original media or user ratings, colour labels and tags.

## Language

On first launch the application follows the operating-system language when supported. Choose Tools > Language to override it or return to System default. Restart the application after changing language.

## Glossary

Active pane: The left or right browser that most recently received a click. Menu and keyboard actions normally apply there.

Codec: The method used to encode video or audio, such as H.264, H.265/HEVC, AV1, AAC, or Opus. A container such as MP4 or MKV can hold one or more encoded streams.

Remux: Copying existing video/audio streams into another container without re-encoding. It is fast and lossless but does not change the codec.

CRF/quality: A constant-quality target for re-encoding. Lower numbers request higher quality and larger files. Hardware encoders translate it to their closest quality control.

Metadata cache: Stored technical results that avoid repeatedly probing unchanged files. It is separate from ratings, labels, and tags.

Thumbnail cache: Generated preview pictures retained on disk for faster future visits and limited through Tools > Cache and scanning.

Recursive/Include subfolders: Scan the selected folder and every folder below it. It never means the entire drive unless the drive root itself is selected.

Smart Collection: A saved view definition containing a location, filters, sorting, and presentation settings. It does not copy or move files.

## Support The Project

Resolution File Manager is provided as a standalone application without requiring a subscription. If you find it useful and would like to support continued development, choose Help > If you like this, buy John a coffee. The same optional support button appears in Help > About and opens the public JohnPerky page in your normal web browser:

https://buymeacoffee.com/johnperky

Supporting the project is completely optional. The application does not open the page automatically, collect payment information, track whether you visit it, or change any feature based on support.

RATINGS AND OPTIONAL REMINDERS

After five launches across at least three days, the app may invite you to rate it in Microsoft Store. Later postpones the request by ten launches. The optional coffee reminder begins at launch 11 and repeats every 11 launches only after Maybe later. Don't ask again disables either reminder; Tools > Reminders can re-enable it. A page opens only after you press its explicit button.

Choose Tools > Reminders… to control the rating and support prompts separately. Tick a prompt to enable it or untick it to disable it, then Save. Cancel leaves the current choices unchanged.
