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

## Trademarks

Windows is a trademark of Microsoft. FFmpeg and the names of other projects remain the property of their respective owners. Mention of a project does not imply endorsement.

If a notice appears incomplete, please report it through the official project page before redistributing the package.
