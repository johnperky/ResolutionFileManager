param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDirectory

$Version = (Get-Content -LiteralPath (Join-Path $ProjectDirectory "VERSION.txt") -Raw).Trim()
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "VERSION.txt does not contain a valid release version." }

if (-not $SkipBuild) {
    & (Join-Path $ProjectDirectory "build_windows.ps1")
    if ($LASTEXITCODE -ne 0) { throw "The Windows application build failed." }
}

$BuiltExe = Join-Path $ProjectDirectory "dist\ResolutionFileManager.exe"
if (-not (Test-Path -LiteralPath $BuiltExe)) { throw "The built executable was not found: $BuiltExe" }
$ReleaseRoot = Join-Path $ProjectDirectory "release-output\$Version"
$PortableName = "ResolutionFileManager-$Version-Windows-x64"
$PortableDirectory = Join-Path $ReleaseRoot $PortableName

if (Test-Path -LiteralPath $ReleaseRoot) {
    $ResolvedProject = [System.IO.Path]::GetFullPath($ProjectDirectory)
    $ResolvedRelease = [System.IO.Path]::GetFullPath($ReleaseRoot)
    if (-not $ResolvedRelease.StartsWith($ResolvedProject, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to replace a release folder outside the project."
    }
    Remove-Item -LiteralPath $ReleaseRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $PortableDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PortableDirectory "licenses\ffmpeg") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PortableDirectory "licenses\python-components") -Force | Out-Null

$VersionedExe = Join-Path $PortableDirectory "ResolutionFileManager-$Version.exe"
Copy-Item -LiteralPath $BuiltExe -Destination $VersionedExe
Copy-Item -LiteralPath README.md, WINDOWS_RELEASE.md, RELEASE_NOTES_12.2.2.md, LICENSE, THIRD_PARTY_NOTICES.md, PRIVACY.md, CHANGELOG.md -Destination $PortableDirectory

$FfmpegPath = (Get-Command ffmpeg -ErrorAction Stop).Source
$FfmpegRoot = Split-Path (Split-Path $FfmpegPath -Parent) -Parent
Copy-Item -LiteralPath (Join-Path $FfmpegRoot "LICENSE") -Destination (Join-Path $PortableDirectory "licenses\ffmpeg\LICENSE")
Copy-Item -LiteralPath (Join-Path $FfmpegRoot "README.txt") -Destination (Join-Path $PortableDirectory "licenses\ffmpeg\README.txt")

$PythonLicenceMap = @{
    "tkinterdnd2" = "tkinterdnd2-0.6.2.dist-info/licenses/LICENSE"
    "Send2Trash" = "Send2Trash-1.8.3.dist-info/LICENSE"
    "Pillow" = "pillow-12.3.0.dist-info/licenses/LICENSE"
    "watchdog" = "watchdog-6.0.0.dist-info/LICENSE"
    "PyInstaller" = "pyinstaller-6.22.2.dist-info/licenses/COPYING.txt"
}
$SitePackages = python -c "import site; print(site.getusersitepackages())"
foreach ($Entry in $PythonLicenceMap.GetEnumerator()) {
    $Source = Join-Path $SitePackages $Entry.Value
    if (-not (Test-Path -LiteralPath $Source)) { throw "Missing third-party licence: $Source" }
    Copy-Item -LiteralPath $Source -Destination (Join-Path $PortableDirectory ("licenses\python-components\" + $Entry.Key + ".txt"))
}

$SourceDirectory = Join-Path $ReleaseRoot "ResolutionFileManager-$Version-Source"
New-Item -ItemType Directory -Path $SourceDirectory -Force | Out-Null
Copy-Item -LiteralPath media_sorter.py, app_icon.ico, app_icon.png, requirements.txt, build_windows.ps1, build_windows_release.ps1, run_windows.bat, VERSION.txt, README.md, PROJECT_CONTEXT.md, LICENSE, THIRD_PARTY_NOTICES.md, PRIVACY.md, CHANGELOG.md, WINDOWS_RELEASE.md, RELEASE_NOTES_12.2.2.md, .gitignore -Destination $SourceDirectory
Copy-Item -LiteralPath packaging -Destination $SourceDirectory -Recurse

$PortableZip = Join-Path $ReleaseRoot "$PortableName.zip"
$SourceZip = Join-Path $ReleaseRoot "ResolutionFileManager-$Version-Source.zip"
Compress-Archive -LiteralPath $PortableDirectory -DestinationPath $PortableZip -CompressionLevel Optimal
Compress-Archive -LiteralPath $SourceDirectory -DestinationPath $SourceZip -CompressionLevel Optimal
Copy-Item -LiteralPath $VersionedExe -Destination (Join-Path $ReleaseRoot "ResolutionFileManager-$Version.exe")

$ChecksumTargets = Get-ChildItem -LiteralPath $ReleaseRoot -File | Where-Object { $_.Extension -in '.exe', '.zip' } | Sort-Object Name
$ChecksumLines = foreach ($Target in $ChecksumTargets) {
    $Hash = (Get-FileHash -LiteralPath $Target.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$Hash  $($Target.Name)"
}
$ChecksumLines | Set-Content -LiteralPath (Join-Path $ReleaseRoot "SHA256SUMS.txt") -Encoding ascii

Write-Host "Windows release package complete: $ReleaseRoot"
