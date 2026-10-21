"""Small isolated Linux visual pilot; writes evidence, never user media."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageGrab, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import media_sorter as m
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    pictures = []
    with tempfile.TemporaryDirectory(prefix="rfm-linux-visual-") as folder:
        base = Path(folder)
        media = base / "Media"
        media.mkdir()
        for name, color in (("Landscape.jpg", "seagreen"), ("Portrait.jpg", "steelblue")):
            Image.new("RGB", (1280, 720), color).save(media / name)
        for language in (os.environ.get("RFM_PROBE_LANGUAGE", "en"),):
            data = base / language
            data.mkdir()
            (data / "settings.json").write_text(json.dumps({"language": language,
                "geometry": "1300x1000+0+0", "left": {"path": str(media)},
                "right": {"path": str(media)}, "reminders": {
                    "rating_disabled": True, "support_disabled": True}}), encoding="utf-8")
            m.application_data_directory = lambda: data
            app = m.MediaSorterApp()
            try:
                for scale in (100, max(m.interface_scales())):
                    app.apply_appearance("System", scale)
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        app.update()
                        time.sleep(.03)
                    for widget in app.toolbar_actions:
                        assert widget.winfo_width() >= widget.winfo_reqwidth() - 2
                        assert widget.winfo_x() + widget.winfo_width() <= app.toolbar.winfo_width()
                    path = output / f"source-{language}-{scale}.png"
                    ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).crop((0, 0, 1300, 1000)).save(path)
                    pictures.append(path)
            finally:
                app.close_app()
        # Separate actual packaged process, with its own settings and populated fixture.
        env = dict(os.environ, XDG_CONFIG_HOME=str(base / "binary"))
        settings = Path(env["XDG_CONFIG_HOME"]) / "ResolutionFileManager"
        settings.mkdir(parents=True)
        (settings / "settings.json").write_text(json.dumps({"language": "ar",
            "geometry": "1300x1000+0+0", "left": {"path": str(media)},
            "right": {"path": str(media)}, "reminders": {
                "rating_disabled": True, "support_disabled": True}}), encoding="utf-8")
        process = subprocess.Popen([sys.argv[2]], env=env)
        try:
            time.sleep(12)
            assert process.poll() is None
            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).crop((0, 0, 1300, 1000)).save(output / "packaged-ar.png")
        finally:
            process.terminate()
            process.wait(timeout=20)
    gallery = Image.new("RGB", (1300, 500), "white")
    for i, path in enumerate(pictures):
        picture = Image.open(path).resize((650, 500))
        ImageDraw.Draw(picture).text((4, 4), path.stem, fill="red")
        gallery.paste(picture, ((i % 2) * 650, (i // 2) * 1000))
    gallery.save(output / ("gallery-" + os.environ.get("RFM_PROBE_LANGUAGE", "en") + ".png"))


if __name__ == "__main__":
    main()
