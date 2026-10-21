"""Expand only the folder-rules English chapter; retain other Help and UI text."""
import json
import re
from pathlib import Path
from sync_help_master import main as sync

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "docs/help/en.json"
    master = json.loads(path.read_text(encoding="utf-8"))
    chapter = next(c for c in master["chapters"] if c["id"] == "folder_organization_rules")
    original = {p["id"]: p for p in chapter["paragraphs"]}
    additions = [
        ("purpose", """WHAT YOU CAN ACHIEVE

Use rules to copy favourite photos into a sharing folder, move videos with a project name into a project folder, separate videos by their existing codec, or collect files you have tagged for review. Each rule sends matching files to one fixed destination. The rule name is just a label for you; it is not a search condition. Copy leaves the source in place; Move relocates it. Neither action converts, renames or edits the media, assigns ratings/tags, or creates a live synchronised collection. Use Smart Collections instead when you only want a saved view without copying or moving files."""),
        ("conditions", """HOW CONDITIONS WORK TOGETHER

All filled conditions in one rule mean AND: a Videos rule with Filename contains set to holiday and Minimum rating set to 4 needs a video whose filename contains holiday AND whose assigned rating is 4 or 5. A matching name alone is insufficient. Leave text conditions blank, Extensions blank, Media kind at Any and Minimum rating at 0 for no restriction from those fields. A rule with no restrictions matches every file in the chosen preview scope, so place a general catch-all rule last. For alternative words or tags, make separate rules with the same destination; entering a comma-separated list in Filename contains or Required exact tag does not mean OR."""),
        ("extensions", """MEDIA KIND AND EXTENSIONS

Media kind limits a rule to Images, Videos, or either kind (Any); it does not include arbitrary documents outside the application's supported media. Extensions checks the final filename suffix: mp4 matches .mp4 and .MP4, and jpg, jpeg, png accepts any of those three extensions. A leading dot is optional. Extensions is a list field; the other text conditions are not. MP4 and MKV are containers, not codecs: use Extensions for a file format and Codec contains for the encoding shown in the pane."""),
        ("filename", """FILENAME CONTAINS: A PIECE OF THE ACTUAL NAME

Enter ordinary text without quotation marks. holiday matches Beach_Holiday_2026.mp4 and holiday-photo.jpg, ignoring letter case. It searches the whole filename, including its extension, but not parent folder names or the image/video content. A file called clip.mp4 inside a Holiday folder does not match holiday. Spaces and punctuation matter: summer holiday does not match summer_holiday. There are no wildcards, regular expressions or exclusion expressions here; *.mp4 is treated as literal text, so put mp4 in Extensions instead. To match holiday OR birthday, create two rules."""),
        ("codec", """CODEC CONTAINS: THE ENCODING ALREADY REPORTED

Look at the Codec column or Info first and enter part of that displayed codec label. HEVC matches H.265 / HEVC; H.264 matches H.264. Matching ignores letter case but keeps punctuation, so h264 without the dot does not match H.264. Do not use mp4 here when you mean an MP4 filename extension. This condition reads the item's Codec value, not every audio stream or embedded metadata tag. It neither converts a video nor changes its codec. If the codec is Unknown, an HEVC rule will not match; check that the scan completed and the file is readable."""),
        ("rating", """MINIMUM RATING: STARS YOU ASSIGN IN THIS APP

Select or tick your files, right-click and use Rating to assign one to five stars before previewing the rule. With ticks present, rating actions use the ticked group; clear unrelated ticks first. The application does not judge quality or automatically award stars. Unrated files have rating 0. Minimum rating 4 accepts both 4-star and 5-star files, not just exactly 4; 5 accepts only 5-star files; 0 includes unrated and rated files. This field cannot select only unrated files, a maximum rating or an exact middle rating. Ratings are local application annotations, not ratings read from or written into the media's embedded metadata."""),
        ("tag", """REQUIRED EXACT TAG: A LABEL YOU ASSIGN IN THIS APP

Select or tick files, right-click and choose Edit tags. Enter tags separated by commas, for example holiday, family, review. Saving replaces the tag list on every file in that action group; include tags you want to keep. These are local application labels, not embedded EXIF/video tags or words detected in a picture. In the rule, enter one whole tag, for example review, without quotes. Matching ignores letter case: Review matches review, but review does not match needs-review, and family does not match family holiday. The rule field accepts one required tag; review, family is not a request for either or both tags. Make separate rules for either tag. One rule cannot require two separate exact tags."""),
        ("examples", """MORE WORKED EXAMPLES

Project videos: choose Copy, destination Project copies, Media kind Videos and Filename contains wedding. Leave the other text fields blank and Minimum rating at 0. Wedding_ceremony.mp4 matches; clip.mp4 in a Wedding folder does not.

Favourite holiday photos: choose Copy, destination Holiday favourites, Media kind Images, Minimum rating 4 and Required exact tag holiday. First assign the holiday tag and 4 or 5 stars to the photos you want. A 5-star photo tagged work fails; a 3-star photo tagged holiday also fails. Nothing needs holiday in its filename.

HEVC review copies: choose Copy, destination HEVC review, Media kind Videos and Codec contains HEVC. Leave Extensions empty to accept supported containers such as MP4 and MKV; add mp4 only if you also want to require MP4. Outputs keep the original encoding.

Approved project videos: choose Copy, destination Approved project, Media kind Videos, Extensions mp4, Filename contains wedding, Codec contains H.264, Minimum rating 4 and Required exact tag approved. Every condition must match. Begin with fewer conditions and add them one at a time if this finds no files."""),
        ("precedence", """RULE ORDER: FIRST MATCH ONLY

Suppose the first rule copies 5-star Images to Best photos and the second copies all Images to Photo archive. A 5-star image uses only the first rule; it is not copied to both destinations. Other images reach the second rule. Reverse the order and the general Images rule catches every image before the favourites rule. Move specific rules above general ones with the arrow buttons. Disabled rules are skipped. An unsuitable destination on the first matching rule does not make the file fall through to another rule; fix the preview problem or change the order."""),
        ("folders", """DESTINATION FOLDERS AND PREVIEW SCOPE

With the active source folder Media and a file at Media/2026/Trip/clip.mp4, destination Review plus Preserve folders relative to the active pane produces Review/2026/Trip/clip.mp4. Without that option the target is Review/clip.mp4. Enable Include subfolders in the pane to scan nested files in the first place. Keeping folders can prevent two same-named files from different subfolders collapsing onto one target; without it the preview can report Duplicate target. Each rule has a fixed destination: it does not invent date/tag/codec folder names from templates. To route more groups to different folders, create more rules. Visible respects the active pane's current filters; All scanned considers its scanned set, not unscanned folders or every drive. Ticks do not supply a Selected scope for this tool."""),
        ("troubleshooting", """IF THE PREVIEW IS EMPTY OR UNEXPECTED

Check the active source pane, scanned files, Scope and pane filters first. Confirm the rule is enabled, then temporarily remove optional conditions and add them back one at a time. Compare the actual filename, Codec, Rating and Tags in Details/Info with what you typed. Check for a more general rule above yours. Click Refresh preview after changes. Unmatched files stay where they are; Already in destination needs no transfer. Target exists uses the normal conflict choices, while Duplicate target and other problem rows must be resolved before Apply becomes available. Review every destination before confirming Apply. Rules do not run automatically when new files arrive: preview and apply them again when wanted."""),
    ]
    # Literal example inputs must survive translation unchanged: translated search
    # words paired with unchanged example filenames would teach the wrong match.
    literals = ["Beach_Holiday_2026.mp4", "holiday-photo.jpg", "Wedding_ceremony.mp4",
        "clip.mp4", "summer holiday", "summer_holiday", "*.mp4", "holiday, family, review",
        "review, family", "family holiday", "needs-review", "holiday", "Holiday",
        "birthday", "review", "Review", "family", "wedding", "Wedding", "work", "approved"]
    pattern = re.compile(r"(?<![\w])(?:" + "|".join(re.escape(v) for v in sorted(literals, key=len, reverse=True)) + r")(?![\w])")
    additions = [(key, pattern.sub(lambda match: '"' + match.group(0) + '"', text)) for key, text in additions]
    # Keep the existing introduction, step-by-step editor/preview and MP4 example.
    chapter["paragraphs"] = [original["folder_organization_rules.p001"],
        {"id": "folder_organization_rules.purpose", "text": additions[0][1]},
        original["folder_organization_rules.p002"],
        *[{"id": "folder_organization_rules." + key, "text": text} for key, text in additions[1:7]],
        original["folder_organization_rules.p003"], original["folder_organization_rules.p004"],
        *[{"id": "folder_organization_rules." + key, "text": text} for key, text in additions[7:]]]
    path.write_text(json.dumps(master, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync()


if __name__ == "__main__":
    main()
