#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$PROJECT_DIR"

command -v ffmpeg >/dev/null 2>&1 || { echo "Install FFmpeg first." >&2; exit 1; }
command -v ffprobe >/dev/null 2>&1 || { echo "Install ffprobe first." >&2; exit 1; }
command -v ffplay >/dev/null 2>&1 || { echo "Install ffplay first." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Install Python 3 first." >&2; exit 1; }

FFMPEG_PATH=$(command -v ffmpeg)
FFPROBE_PATH=$(command -v ffprobe)
FFPLAY_PATH=$(command -v ffplay)
VERSION=$(tr -d '[:space:]' < VERSION.txt)
ARCH=$(uname -m)
OUTPUT_NAME="ResolutionFileManager-v${VERSION}-linux-${ARCH}"
VENV_DIR="$PROJECT_DIR/.venv-build"

python3 verify_release_assets.py "$PROJECT_DIR"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creating isolated Python build environment..."
    python3 -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

echo "Installing build dependencies into isolated environment..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install pyinstaller -r requirements.txt

echo "Building $OUTPUT_NAME..."
"$VENV_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name "$OUTPUT_NAME" \
    --add-data "$PROJECT_DIR/app_icon.png:." \
    --add-data "$PROJECT_DIR/locales:locales" \
    --add-binary "$FFMPEG_PATH:." \
    --add-binary "$FFPROBE_PATH:." \
    --add-binary "$FFPLAY_PATH:." \
    media_sorter.py

OUTPUT_PATH="$PROJECT_DIR/dist/$OUTPUT_NAME"
test -f "$OUTPUT_PATH" || { echo "Build output was not created: $OUTPUT_PATH" >&2; exit 1; }
chmod +x "$OUTPUT_PATH"
echo "Portable Linux build complete: $OUTPUT_PATH"
echo "Copy this one file to compatible Linux Mint PCs, make it executable, and run it."
