# Resolution File Manager 12.7.3 — multilingual review

Undo now coordinates with background metadata and thumbnail readers and releases
preview decoders before restoration. Recovery runs off the UI thread and retries
brief Windows sharing locks. Failed steps and replacement backups remain in the
session Undo history; pressing Undo again resumes without repeating completed
steps. Queued transfers wait until incomplete recovery is resolved. Existing
destination/source conflicts and modified files are not silently overwritten.

English safety instructions explain this behavior beside the existing Undo help.
All42 other languages were updated on21 October2026, including new controls,
dialogs, options, status/error messages and all134 detailed Help paragraphs.
All43 language Help and new-control automated checks passed. Native visual
capture was unavailable; RTL typography still requires visual review.
This review does not publish, submit to the Store, push GitHub or build Linux.
