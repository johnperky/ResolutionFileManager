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
VENV_DIR="${RFM_BUILD_VENV:-$PROJECT_DIR/.venv-linux-build}"

python3 verify_release_assets.py "$PROJECT_DIR"
if [ "${RFM_REVIEW_LANGUAGE:-}" = "en" ]; then
    python3 -c "from tools.validate_help import validate; r=validate(languages=['en']); assert not r['errors'], r['errors']; print('English review Help validated; translations pending.')"
else
    python3 tools/validate_help.py
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creating isolated Python build environment..."
    python3 -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

if [ "${RFM_REUSE_BUILD_ENV:-0}" = "1" ]; then
    "$VENV_PYTHON" -c 'import PyInstaller, PIL, tkinterdnd2, send2trash, watchdog, onnxruntime, numpy, av'
else
    echo "Installing build dependencies into isolated environment..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install pyinstaller -r requirements.txt -r requirements-ai.txt
fi

echo "Building $OUTPUT_NAME..."
"$VENV_PYTHON" -c 'from ai_backends import validate_assets; validate_assets("assets/ai")'
"$VENV_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --workpath "${RFM_BUILD_WORK_DIR:-$PROJECT_DIR/build/linux}" \
    --distpath "$PROJECT_DIR/dist/linux" \
    --onefile \
    --windowed \
    --name "$OUTPUT_NAME" \
    --add-data "$PROJECT_DIR/app_icon.png:." \
    --add-data "$PROJECT_DIR/locales:locales" \
    --add-data "$PROJECT_DIR/assets/ai:assets/ai" \
    --collect-binaries onnxruntime \
    --collect-data onnxruntime \
    --collect-all av \
    --add-binary "$FFMPEG_PATH:." \
    --add-binary "$FFPROBE_PATH:." \
    --add-binary "$FFPLAY_PATH:." \
    media_sorter.py

OUTPUT_PATH="$PROJECT_DIR/dist/linux/$OUTPUT_NAME"
test -f "$OUTPUT_PATH" || { echo "Build output was not created: $OUTPUT_PATH" >&2; exit 1; }
chmod +x "$OUTPUT_PATH"
echo "Portable Linux build complete: $OUTPUT_PATH"
echo "See LINUX_INSTALL.txt for target system libraries, fonts and desktop validation requirements."
