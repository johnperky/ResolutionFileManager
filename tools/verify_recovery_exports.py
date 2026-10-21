"""Verify recovery exports and record reproducible artifact hashes.

Does not mutate releases, snapshots, Git or application settings. The report
is generated after exports and therefore is separate from their manifests.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.project_snapshot import sha, verify


def main():
    version = (ROOT / "VERSION.txt").read_text().strip()
    release = ROOT / "release-output" / version
    backups = ROOT.parent / "Recovery Backups"
    sources = [release / f"ResolutionFileManager-{version}-Source",
               Path(f"F:/ResolutionFileManager-Linux-Handoff-{version}"),
               backups / f"2026-10-19-final-source-{version}",
               backups / f"2026-10-19-completed-source-{version}"]
    results = []
    for source in sources:
        manifest = verify(source)
        assert manifest["version"] == version
        for name in ["media_sorter.py", "localization.py", "rtl_display.py", "docs/help/en.json", "build_linux.sh", "build_windows.ps1"]:
            assert manifest["files"][name] == sha(ROOT / name), f"Export stale: {source}: {name}"
        for locale in (ROOT / "locales").glob("*.json"):
            assert manifest["files"][f"locales/{locale.name}"] == sha(locale), f"Locale stale: {source}: {locale.name}"
        results.append({"path": str(source), "verified_files": len(manifest["files"]),
                        "manifest_sha256": sha(source / "SOURCE_MANIFEST.json")})
    artifacts = [ROOT / "dist/ResolutionFileManager.exe",
                 ROOT / f"dist/linux/ResolutionFileManager-v{version}-linux-x86_64",
                 Path(f"C:/Users/johnp/Desktop/ResolutionFileManager-v{version}.exe"),
                 release / f"ResolutionFileManager-{version}-Windows-x64.zip",
                 release / f"ResolutionFileManager-{version}-Source.zip",
                 backups / "2026-10-19-current-git-history.bundle"]
    hashes = {str(path): sha(path) for path in artifacts}
    assert hashes[str(artifacts[0])] == hashes[str(artifacts[2])]
    # Inspect real independent backup copies, not a junction to the F: files.
    independent = Path(f"C:/Users/johnp/Desktop/project backup/RFM-recovery-2026-10-19-v{version}")
    for original in [Path(str(sources[-1]) + ".zip"), artifacts[-1]]:
        target = independent / original.name
        assert sha(original) == sha(target), f"Independent backup mismatch: {target}"
        hashes[str(target)] = sha(target)
    report = {"version": version, "authoritative_project": str(ROOT), "source_exports": results,
              "artifact_sha256": hashes, "independent_backup": str(independent),
              "history_bundle": "git bundle verify completed separately; includes committed history only",
              "scope": "Every source-manifest entry verified. Current application/locales/builders matched explicitly. This later verification report is not part of the earlier export manifests."}
    (ROOT / "docs/RECOVERY_EXPORT_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
