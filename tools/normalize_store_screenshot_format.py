"""Preserve native captures and encode their exact decoded pixels as real PNGs."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

root = Path(r"F:\Resolution File Manager project\Store Preparation 12.6.2")
backup = root / "Original capture bytes"
results = []
for path in sorted(root.glob("*/*.png")):
    if path.parent == backup:
        continue
    with Image.open(path) as image:
        image.load()
        if image.format == "PNG":
            continue
        original = backup / path.parent.name / (path.stem + ".jpg")
        original.parent.mkdir(parents=True, exist_ok=True)
        if original.exists():
            assert original.read_bytes() == path.read_bytes(), original
        else:
            shutil.copy2(path, original)
        before = image.tobytes()
        size = image.size
        image.save(path, format="PNG")
    with Image.open(path) as encoded:
        assert encoded.format == "PNG" and encoded.size == size
        assert encoded.tobytes() == before, path
    results.append({"file": str(path), "original": str(original), "size": size,
                    "decodedPixelsIdentical": True,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
(root / "format-normalization.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Preserved {len(results)} originals; encoded true PNGs with identical decoded pixels.")
