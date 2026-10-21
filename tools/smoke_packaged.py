"""Launch a packaged executable with disposable settings, never user settings.

This proves startup/liveness only. Use the source GUI suite and visual review
for feature coverage; a live process alone is not a complete application test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--language", default="en")
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    binary = args.executable.resolve()
    with tempfile.TemporaryDirectory(prefix="rfm-binary-test-", ignore_cleanup_errors=True) as folder:
        root = Path(folder)
        media = root / "media"
        media.mkdir()
        settings = root / "ResolutionFileManager"
        settings.mkdir()
        (settings / "settings.json").write_text(json.dumps({
            "language": args.language, "geometry": "1400x900+30+30",
            "left": {"path": str(media)}, "right": {"path": str(media)},
            "reminders": {"rating_disabled": True, "support_disabled": True},
        }), encoding="utf-8")
        env = dict(os.environ, LOCALAPPDATA=str(root), XDG_CONFIG_HOME=str(root))
        with (root / "stdout.txt").open("wb") as out, (root / "stderr.txt").open("wb") as err:
            process = subprocess.Popen([str(binary)], env=env, stdout=out, stderr=err)
            print(f"Diagnostic packaged process: {process.pid}", flush=True)
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline and process.poll() is None:
                time.sleep(.2)
            alive = process.poll() is None
            if alive:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
                else:
                    process.terminate()
                process.wait(timeout=15)
        error = (root / "stderr.txt").read_text(encoding="utf-8", errors="replace")
        result = {"executable": str(binary), "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                  "language": args.language, "startup_liveness_passed": alive,
                  "observation_seconds": args.seconds, "stderr": error,
                  "scope": "Startup/liveness only; visual and feature checks reported separately."}
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result), flush=True)
        if not alive or "Traceback" in error:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
