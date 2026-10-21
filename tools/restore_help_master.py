"""Selectively recover the public 12.3.0 guide; never copy old application code."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_COMMIT = "835ab63bab795cffde8f8db0804267796cfed397"

SMART = """WHAT SMART COLLECTIONS SAVE

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
"""

def recover():
    if (ROOT/"docs/help/en.json").exists():
        raise FileExistsError("English Help master already exists. Edit that master and synchronise it; never regenerate it from short locale summaries.")
    original = subprocess.check_output(["git", "show", f"{RECOVERY_COMMIT}:media_sorter.py"], cwd=ROOT).decode("utf-8")
    tree = ast.parse(original)
    function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "show_help")
    guide_node = next(n for n in ast.walk(function) if isinstance(n, ast.JoinedStr) and any(isinstance(v, ast.Constant) and "QUICK START" in str(v.value) for v in n.values))
    guide = "".join(v.value if isinstance(v, ast.Constant) else "{version}" for v in guide_node.values)
    target = ROOT / "docs" / "help"
    target.mkdir(parents=True, exist_ok=True)
    (target / "recovered-12.3.0-en.txt").write_text(guide, encoding="utf-8")
    matches = list(re.finditer(r"(?m)^([A-Z][A-Z /&-]{2,})$", guide))
    chapters = []
    for index, match in enumerate(matches):
        title = match.group(1).title()
        body = guide[match.end():matches[index+1].start() if index+1 < len(matches) else len(guide)].strip()
        chapter_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        chapters.append({"id": chapter_id, "title": title, "body": body})
    english_path = ROOT / "locales" / "en.json"
    english = json.loads(english_path.read_text(encoding="utf-8"))
    old = english["help"]["chapters"]
    mapping = {"quick_start":"quick_start", "browsing":"getting_started", "organising":"copying_and_moving", "privacy":"licensing_and_privacy"}
    for chapter in old:
        if chapter["id"] in mapping:
            dest = next(c for c in chapters if c["id"] == mapping[chapter["id"]])
            dest["body"] += "\n\n" + chapter["body"]
        else:
            chapters.append(chapter)
    chapters.append({"id":"smart_collections", "title":"Smart Collections: Saved Searches", "body":SMART.strip()})
    # All historical content remains intact. Add corrections instead of silently
    # deleting historical build guidance or changing the recovered evidence file.
    corrections = {
        "build_and_rollback": "CURRENT BUILD WORKFLOW\n\nThe maintained project is F:\\Resolution File Manager project\\ResolutionFileManager-Project-v6. Desktop source links point there. Keep development source separate from dist and versioned release-output folders. Use tools/project_snapshot.py for a complete source snapshot or handoff, verify its SHA-256 manifest, and never reuse an older handoff as the development master. Windows uses build_windows.ps1; Linux uses build_linux.sh from the same source. A Linux binary must be built and tested on Linux; the Windows EXE is not a Linux executable. See DEVELOPMENT_WORKFLOW.md and LINUX_INSTALL.txt for current detailed instructions. Older numbered files are retained as rollback versions.",
        "support_the_project": "CURRENT REMINDER SETTINGS\n\nTools > Reminders controls the optional Microsoft Store rating and Buy Me a Coffee prompts independently. The rating prompt becomes eligible after five launches across three distinct days; the support prompt begins at launch eleven. Later postpones the corresponding prompt. Opening its link or choosing Never disables that automatic prompt. Re-enable it in Reminders if desired. Neither prompt is required for using the application.",
    }
    for chapter in chapters:
        if chapter["id"] in corrections: chapter["body"] += "\n\n" + corrections[chapter["id"]]
    index = {"id":"topic_index", "title":"Topic Index and Chapter Links", "body":"\n\n".join(f"{c['title']} — [chapter:{c['id']}]" for c in chapters)}
    chapters.append(index)
    for c in chapters:
        c["paragraphs"] = [{"id":f"{c['id']}.p{i:03d}", "text":p} for i,p in enumerate(re.split(r"\n\s*\n",c["body"]),1)]
    master = {"schema":2,"source_commit":RECOVERY_COMMIT,"source_guide_sha256":hashlib.sha256(guide.encode()).hexdigest(),"chapters":chapters}
    encoded = json.dumps(master, ensure_ascii=False, indent=2)+"\n"
    (target / "en.json").write_text(encoded,encoding="utf-8")
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    english["help"] = {**master,"master_sha256":digest,"direction":"ltr"}
    english_path.write_text(json.dumps(english,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (target / "ENGLISH_MANUAL.md").write_text("# Resolution File Manager — authoritative English manual\n\n"+"\n\n".join(f"## {c['title']}\n\n{c['body']}" for c in chapters)+"\n",encoding="utf-8")
    print(f"Recovered {len(chapters)} chapters / {sum(len(c['paragraphs']) for c in chapters)} paragraphs; master {digest}")

if __name__ == "__main__":
    recover()
