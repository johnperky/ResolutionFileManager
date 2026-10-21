"""Package an already-built Linux candidate, preserving bytes and licence notices.

Run inside the Linux build tree with its build virtualenv. No compilation occurs.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

from PyInstaller.archive.readers import CArchiveReader


def main():
    root = Path(__file__).resolve().parents[1]
    version = (root / "VERSION.txt").read_text().strip()
    binary = root / "dist/linux" / f"ResolutionFileManager-v{version}-linux-x86_64"
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    package = output / f"ResolutionFileManager-{version}-Linux-x86_64-review"
    package.mkdir()
    shutil.copy2(binary, package / binary.name)
    (package / binary.name).chmod(0o755)
    for name in ("LICENSE", "PRIVACY.md", "THIRD_PARTY_NOTICES.md", "LINUX_INSTALL.txt", f"RELEASE_NOTES_{version}.md"):
        shutil.copy2(root / name, package / name)
    notices = package / "licenses"
    notices.mkdir()
    # Preserve the installed distributions' actual notices, including native TkDND.
    import importlib.metadata
    components = notices / "python-components"
    components.mkdir()
    for distribution in importlib.metadata.distributions():
        for file in distribution.files or ():
            if any(word in str(file).lower() for word in ("license", "licence", "copying", "copyright")):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    target = components / distribution.metadata["Name"] / str(file)
                    # Wheel RECORD paths can include ../../; flatten those safely.
                    if ".." in file.parts:
                        target = components / distribution.metadata["Name"] / source.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    archives = CArchiveReader(str(binary))
    native = notices / "ubuntu-packages"
    native.mkdir()
    packages = {}
    for name in archives.toc:
        basename = Path(name).name
        if ".so" not in basename and basename not in ("ffmpeg", "ffprobe", "ffplay"):
            continue
        candidates = [Path("/usr/bin") / basename, Path("/usr/lib/x86_64-linux-gnu") / basename,
                      Path("/usr/lib") / basename]
        for candidate in candidates:
            if not candidate.exists():
                continue
            result = subprocess.run(["dpkg-query", "-S", str(candidate)], capture_output=True, text=True)
            if result.returncode:
                continue
            for line in result.stdout.splitlines():
                package_name = line.split(": ", 1)[0]
                short = package_name.split(":")[0]
                copyright_file = Path("/usr/share/doc") / short / "copyright"
                if copyright_file.exists():
                    shutil.copy2(copyright_file, native / f"{short}.copyright")
                version_info = subprocess.run(["dpkg-query", "-W", "-f=${binary:Package} ${Version} ${source:Package} ${source:Version}\\n", package_name], capture_output=True, text=True)
                packages[package_name] = version_info.stdout.strip()
            break
    (native / "PACKAGES.json").write_text(json.dumps(packages, indent=2) + "\n")
    (native / "SOURCE.txt").write_text("Ubuntu 24.04 Noble packages. Exact binary/source package versions are in PACKAGES.json.\nCorresponding source: https://launchpad.net/ubuntu/+source/<source-package>/<source-version>\nUse apt-get source <source-package>=<source-version> with matching deb-src repositories.\nIndividual copyright files record upstream source URLs and licences.\n")
    (package / "FFMPEG-BUILD.txt").write_text(subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout)
    (package / "Run Resolution File Manager.sh").write_text('#!/bin/sh\ncd "$(dirname "$0")" || exit 1\nexec "./' + binary.name + '" "$@"\n')
    (package / "Run Resolution File Manager.sh").chmod(0o755)
    archive = output / (package.name + ".tar.gz")
    with tarfile.open(archive, "w:gz") as stream:
        stream.add(package, arcname=package.name)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{checksum}  {archive.name}\n" + hashlib.sha256(binary.read_bytes()).hexdigest() + f"  {package.name}/{binary.name}\n")
    print(json.dumps({"archive": str(archive), "sha256": checksum, "licence_packages": len(packages)}))


if __name__ == "__main__":
    main()
