# Image and video enhancement — quick guide

These instructions describe the latest 13.0.0 Windows enhancement review build. The older Linux review archive has not been rebuilt with the new direct 2× choice. Earlier published versions may not have these controls. For the full instructions, open the app's Help and select **Image Conversion and Enhancement** or **Video Conversion**, or read the [English manual](help/ENGLISH_MANUAL.md).

## Enhance photographs and illustrations

1. Select or tick the images in the active pane. Open **Tools > Convert / enhance images**.
2. Choose an **Enhancement method** using the table below.
3. Choose **Output size**. Use **Original size** to enhance without enlarging the finished picture, or choose a percentage, long-edge preset or custom long edge to resize it. Check the final dimensions in the preview.
4. Leave **AI processing hardware** on **Automatic** initially. You can select a detected GPU or **CPU (slower)** if needed.
5. Choose JPEG, PNG or WebP, the output folder and the filename prefix/suffix. PNG retains transparency and avoids lossy output compression; JPEG flattens transparency onto white. JPEG/WebP quality defaults to 92.
6. Optionally choose standard effects and their strength. Start with Light and compare a sample before applying several effects to a batch.
7. Check the preview, hardware and space information, then start conversion. Compare the result with the original at 100% before processing more files.

| Method | When to try it |
|---|---|
| Ordinary resizing | Change dimensions or apply standard effects without AI. |
| AI Photo fast 2× / 4× | A quicker AI option for photographs, including large phone/camera photos. Compare fine detail for smoothing or changed textures. |
| AI Photo restore/detail 2× / 4× | Try the existing larger photo model when you want a different reconstruction result and can allow more processing time. |
| AI Illustration 2× / 4× | Drawings, cartoons and illustrations. |

The 2×/4× label describes the AI intermediate. **Output size controls the finished dimensions.** For example, Photo fast 2× with Original size still produces an image at its original dimensions. A 4× choice generally needs more time and working space; it is not a promise of a better result.

Standard effects are Denoise, Smooth, Sharpen, Auto contrast and Colour boost. These adjust existing pixels and also work without AI. Colour boost does not colourise black-and-white pictures. Dedicated scratch removal and face-repair tools are not included. AI can change faces, lettering and fine patterns, so keep the originals and compare results.

This is an 8-bit image workflow, not a RAW/HDR editor. Compatible RGB ICC profiles are retained, but other EXIF metadata, including location, is not copied.

## Enhance or convert video

1. Select or tick videos and open **Tools > Convert selected videos**.
2. Choose a preset for the **final height**, codec and container. H.264 is a useful compatibility starting point. Choose MKV when you need subtitle formats that MP4 cannot carry.
3. Choose the processing method below. Start with a short clip.
4. Choose the output folder and filename prefix/suffix. **Preserve folders** starts unticked; enable it only if you want source subfolder paths retained below the destination.
5. Leave hardware selection on Automatic initially. For AI, check both **AI processing hardware** and **Encoding engine**: these control different stages.
6. For AI, choose a spacious, fast **AI working folder**, review the temporary-space estimate and confirm conversion.
7. Check picture quality, motion/flicker, sound synchronisation, subtitles, chapters and the start/end before processing a long video.

| Video method | What it does |
|---|---|
| Ordinary resizing | Converts and resizes without AI reconstruction. |
| Fast enhancement (no AI) | Uses streaming Lanczos scaling and light sharpening. A useful first option for speed; it does not reconstruct missing detail and needs no temporary frame images or AI working folder. |
| AI Photo fast 2× / 4× | Uses the compact photo model on video frames; compare moving detail for flicker or smoothing. |
| AI Video 2× | Uses a trained native 2× model: a 360p frame becomes 720p, or 1080p becomes 2160p, without making 4× frames first. |
| AI Video 2× High quality (slower) | Retains the previous method: processes at 4×, then reduces to 2× before final encoding. Uses more resources and can look different; compare a sample rather than assuming it is always better. |
| AI Video 4× | Uses the existing larger model for genuine 4× enlargement. Allow substantially more processing time than ordinary/Fast conversion. |
| AI Animation 2× | Uses a native 2× model trained on compressed animation. Fine lines and textures can change; compare a short sample. |
| AI Animation 2× High quality (slower) | Retains the previous animation method: processes at 4×, then reduces to 2×. Uses more resources; the label does not guarantee better quality. |
| AI Animation 4× | Uses the existing 4× animation model for drawn or animated footage. |

The preset sets the final height; the AI multiplier is an intermediate enlargement. A 540p source with AI Video 2× and a 720p preset finishes at 720p. Files already at or above the requested height use ordinary resizing. Keep source and remux do not apply AI. AI video currently requires supported SDR 8-bit material with known frame timing; use ordinary conversion for HDR/high-bit-depth sources.

Fast enhancement uses the bundled FFmpeg scaler and sharpening filter. It does not require libplacebo. Audio tracks, subtitles and chapters are mapped to the output; unsupported subtitle/container combinations fail rather than being silently dropped. Remux copies compatible streams without changing their codec, resolution or quality.

## Hardware, working space and progress

**Automatic AI hardware** tries a compatible GPU and can fall back to CPU. CPU is available for systems without suitable GPU acceleration, but large AI jobs can be slow. An explicitly selected unavailable GPU reports failure. For video, an automatic GPU inference failure can restart the source on CPU to keep one backend throughout the result.

**Encoding engine** controls the final video compression. GPU encoding does not mean that AI inference is using that GPU, and a detected device may not support every output codec. Lower CRF values generally request higher quality/larger files; hardware encoder quality settings are not necessarily identical.

**AI working folder** and **Output folder** are independent. For example, use a fast C: working folder while saving finished files to F:. A blank AI working field uses the system temporary folder. Ordinary conversion and Fast video do not use the AI working folder.

AI video now prepares CPU frames directly and handles GPU frames in bounded batches that are removed as processing advances. It still keeps a complete lossless intermediate until the job finishes. Long or high-resolution videos can therefore need substantial temporary space. The preview/confirmation estimate is approximate, free space is checked during processing, and the output drive also needs room for the encoded file.

The current file shows activity immediately while preparation or model loading is underway. **Preparing video frames** and **Loading AI model** identify these stages; activity is indeterminate while progress is unknown. GPU progress counts actual saved frames before the whole batch finishes. Unknown work has no invented percentage or completion time. Preparation/AI processing and encoding are reported separately; their FPS values measure different work. A faster model or compatible GPU may help, but timings vary with input size, output settings and hardware; no fixed speed increase is guaranteed. Activity stops when cancellation or cleanup finishes.

## Cancel safely and retain originals

Use Cancel and allow cleanup to finish. Closing an active conversion window asks first. Quit or closing the main app also asks while a conversion is active; No leaves it running, while Yes cancels and waits for owned processes and temporary files to be cleared.

Originals, previously completed outputs and unrelated working-folder files remain. Jobs clean only their own temporary subfolders and unfinished output. Use Skip existing to retain an existing target or Keep both to create a numbered filename. The default suffix is ` - converted`.

The packaged app runs enhancement completely offline with its bundled engines/models. No separate Python installation, paid enhancement service or runtime model download is needed.

### Conversion display

Click **Display** in image or video conversion to open a separate view; click the same button again to close it. It retains the full-resolution completed image or sampled enhanced AI-video frame, without a reduced JPEG preview. Still images use the actual encoded output file; GPU video copies its completed frame and CPU video saves a lossless full-resolution snapshot. Only the most recent snapshot is retained, updating at most about once a second for AI video while open. Full-resolution copying/encoding adds some work while the display is open; closing it stops snapshot generation.

**Fit to window** resizes the on-screen presentation as the window changes size, preserving proportions. **100%** shows native pixels with scrollbars for detailed inspection. **Full screen**, F11 or double-click toggles full screen; Escape leaves it. The source frame stays at full resolution in all views. The dimensions appear beneath the picture.

The window opens beside conversion controls when screen space permits; otherwise it opens near the top to keep progress bars visible below. Before the first result it shows Loading preview. AI snapshots show progress before final encoding/effects; ordinary/Fast video does not currently supply live frames. The conversion table updates automatically; Refresh preview is no longer needed.

### Optional video effects

Video conversion now offers Denoise, Sharpen, Smooth, Contrast boost and Colour boost, with Light / Medium / Strong. All are off by default. They use the bundled FFmpeg filters, not AI reconstruction. They work with ordinary conversion, Fast enhancement and AI upscaling, and are applied during final encoding. Contrast boost is a fixed adjustment, avoiding frame-to-frame automatic contrast changes. Selecting Sharpen replaces Fast's existing light sharpening rather than adding a second sharpening pass.

Effects require re-encoding and are disabled for remux presets. Processing can take longer; hardware encoding can still be used, while these filters run on CPU. On Linux VA-API, filtering uses software-decoded frames before hardware upload. AI Display snapshots show the AI stage before final encoding effects; review the finished video for the combined result. Output audio/subtitle/metadata handling remains as described above.

### Existing output filenames

Conflicting output names are highlighted, with a visible File already exists notice. Start opens the conflict choices instead of silently remaining disabled. Choose **Rename**, **Replace**, **Folder** (change destination), or **Skip** for each conflict. Existing Keep both also provides automatic numbered names. The table reflects each choice before conversion starts.

Replace requires explicit confirmation for that existing output. Original input files, including other selected inputs and hard-linked aliases, cannot be overwritten. The old output remains until a new conversion succeeds. If the destination changes after confirmation, replacement stops; a competing new file is retained. Recovery backups are kept and identified if an unexpected conflict prevents restoration. Cancel or failure before publication leaves the existing output intact. Changes to the planned destination invalidate earlier filename choices.

### Conversion controls and main-pane columns

Both conversion windows grow initially to fit their options when the screen permits. Unnecessary settings scrollbars are hidden. On smaller screens or after making a window smaller, use the mouse wheel over the options (including closed drop-downs) to scroll vertically; hold Shift while using the wheel to scroll sideways. Scrolling the page does not change the selected drop-down option. The file list, progress bars and action buttons remain outside the settings scroller. An open drop-down retains its normal list behaviour.

The default Details order in both main panes is **Name / relative path → Resolution → Video length → Codec**, followed by the remaining fields. Relative paths appear with the filename rather than as a separate column. The previous untouched default order migrates automatically; personally arranged saved column orders and widths remain intact.

All 43 languages include the current conversion instructions in searchable Help. These are local review builds; human linguistic review and physical Linux hardware checks remain separate from the automated validation.

## Video compression and audio

**Automatic compression** is the default. It calculates a separate video bitrate
for each file from the final dimensions and frame rate, using the same bitrate
calculation as Shutter's Auto mode. A 1920×1080,25fps,8-bit H.265 output targets
2500kb/s; H.264 targets5000kb/s. The displayed target is not a guarantee of final
size or equivalent quality for every source. Constant quality remains available;
its number is not directly comparable across different encoders/rate-control modes.

**Max. Quality** defaults on. It uses slower quality-oriented encoder settings,
including NVIDIA p7/HQ/lookahead/AQ where supported. CPU maximum quality can take
considerably longer. Optional NVIDIA quality settings have a labelled compatibility
retry using the same encoder. Two-pass encoding is not enabled.

Audio defaults to **192kb/s per track**, with **128kb/s** also available (plus256
and320). All mapped audio tracks and original channels remain unless you explicitly
choose Stereo or Mono. Remux copies streams and ignores the encoding controls.
These choices are remembered. Review the target/audio summary before Start and
compare a short finished sample before converting long batches.
