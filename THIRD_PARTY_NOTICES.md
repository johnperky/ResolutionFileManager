# Third-party software notices

Resolution File Manager includes or uses the following third-party software. The complete licence texts distributed with the Windows package are in `licenses/`.

## FFmpeg 8.0 full build

The Windows executable bundles `ffmpeg.exe`, `ffprobe.exe`, and `ffplay.exe` from the Gyan.dev FFmpeg 8.0 full build. That build was configured with GPL components, including x264 and x265, and is distributed under GNU GPL version 3 or later.

- Project: https://ffmpeg.org/
- Windows build provider: https://www.gyan.dev/ffmpeg/builds/
- Licence and compliance guidance: https://ffmpeg.org/legal.html
- Corresponding FFmpeg source: https://ffmpeg.org/releases/ffmpeg-8.0.tar.xz
- Build information: `licenses/ffmpeg/README.txt`
- Licence: `licenses/ffmpeg/LICENSE`

FFmpeg is a separate command-line program launched by Resolution File Manager. FFmpeg and its libraries are not owned by the Resolution File Manager project.

Linux builds bundle the Linux host's FFmpeg tools, which can have a different version and shared-library configuration from the Windows Gyan build above. Check `ffmpeg -version` and the build report. The distribution's FFmpeg copyright/licence information and corresponding source packages must accompany redistribution as applicable; test required system libraries on the destination platform.

## Python components

| Component | Version | Licence |
|---|---:|---|
| Python | Runtime used for the packaged application | Python Software Foundation Licence |
| Tcl/Tk | Runtime used for the graphical interface | BSD-style Tcl/Tk licence |
| Pillow | 12.3.0 | HPND licence |
| Send2Trash | 1.8.3 | BSD 3-Clause |
| tkinterdnd2 | 0.6.2 | MIT |
| watchdog | 6.0.0 | Apache License 2.0 |
| arabic-reshaper | 3.0.0 | MIT |
| python-bidi | 0.4.2 | GNU LGPL; COPYING and COPYING.LESSER included |
| six | 1.17.0 | MIT |
| PyInstaller | 6.22.2 | GPL-2.0-or-later with the PyInstaller bootloader exception |

PyInstaller's exception permits distribution of applications built with its bootloader. Copyright notices and full applicable licence texts are retained in the `licenses/python-components/` directory of the release package.

The small pure-Python shaping/bidi dependencies are used for Linux Tk 8.6 RTL display. Logical source translations are retained unchanged. Their source distributions are available from https://pypi.org/project/arabic-reshaper/3.0.0/, https://pypi.org/project/python-bidi/0.4.2/ and https://pypi.org/project/six/1.17.0/. The separate LGPL bidi component remains replaceable when building from the complete source distribution with requirements.txt.

## Standalone optional AI upscaling (English review 12.7.13)

Real-ESRGAN-ncnn-vulkan (MIT), the Real-ESRGAN models/project (BSD-3-Clause), ncnn (BSD-3-Clause), ONNX Runtime (MIT), numpy (BSD-3-Clause) and PyAV (BSD-3-Clause) provide local GPU/CPU inference and lossless timed-frame handling. Required model/engine/runtime files are supplied with the application; Shutter Encoder is neither included nor required. Hardware video encoding through FFmpeg/NVENC/Quick Sync/AMF is separate from AI inference.

`assets/ai/manifest.json` records exact upstream origins, hashes and model conversion verification. Full upstream notices, actual installed Python component licences and FFmpeg wheel configuration/licence records are retained in `assets/ai/LICENSES/` inside the packaged executable and copied beside packaged distributions. Development-only PyTorch export tools are not part of the runtime. See the retained runtime records for exact component versions and corresponding upstream source URLs; no upstream endorsement is implied.

## Trademarks

Windows is a trademark of Microsoft. FFmpeg and the names of other projects remain the property of their respective owners. Mention of a project does not imply endorsement.

If a notice appears incomplete, please report it through the official project page before redistributing the package.

## Native 2× animation model

The optional AI Animation 2× video enhancement uses **2xHFA2kAVCCompact** by
**Philip Hofmann (Helaman / Phhofm)**, licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
Original model: https://github.com/Phhofm/models/releases/tag/2xHFA2kAVCCompact .
The trained weights are converted to FP32 ONNX/NCNN, runtime I/O names adapted,
and the final NCNN clip expressed as equivalent scalar MAX(0), MIN(1).
Scale and trained parameters remain unchanged. No endorsement is implied.
Full attribution, licence and original model card are bundled under
`assets/ai/LICENSES/native-animation2/`; model source and hashes are recorded in
`assets/ai/manifest.json`. This model retains its CC BY 4.0 terms independently
of the application licence; no additional restrictions are imposed on the model.
The previous animation model remains available as the heavier quality option.
