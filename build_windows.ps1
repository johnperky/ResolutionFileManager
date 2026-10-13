$ErrorActionPreference = "Stop"
$ProjectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDirectory

python -m pip install pyinstaller -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }
$FfprobePath = (Get-Command ffprobe -ErrorAction Stop).Source
$FfmpegPath = (Get-Command ffmpeg -ErrorAction Stop).Source
$FfplayPath = (Get-Command ffplay -ErrorAction Stop).Source
$IconPath = Join-Path $ProjectDirectory "app_icon.ico"
$IconPngPath = Join-Path $ProjectDirectory "app_icon.png"
if (-not (Test-Path -LiteralPath $IconPath)) { throw "Application icon was not found: $IconPath" }
if (-not (Test-Path -LiteralPath $IconPngPath)) { throw "Application icon PNG was not found: $IconPngPath" }
python verify_release_assets.py "$ProjectDirectory"
if ($LASTEXITCODE -ne 0) { throw "Language-pack validation failed with exit code $LASTEXITCODE" }

$BuildStarted = Get-Date
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name ResolutionFileManager `
    --icon "$IconPath" `
    --add-data "$IconPngPath;." `
    --add-data "$ProjectDirectory\locales;locales" `
    --add-binary "$FfprobePath;." `
    --add-binary "$FfmpegPath;." `
    --add-binary "$FfplayPath;." `
    media_sorter.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

$OutputPath = Join-Path $ProjectDirectory "dist\ResolutionFileManager.exe"
if (-not (Test-Path -LiteralPath $OutputPath)) { throw "Build output was not created: $OutputPath" }
if ((Get-Item -LiteralPath $OutputPath).LastWriteTime -lt $BuildStarted) { throw "Build output was not refreshed: $OutputPath" }
$Version = (Get-Content -LiteralPath (Join-Path $ProjectDirectory "VERSION.txt") -Raw).Trim()
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "VERSION.txt does not contain a valid release version." }
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopExe = Join-Path $DesktopPath "ResolutionFileManager-v$Version.exe"
Copy-Item -LiteralPath $OutputPath -Destination $DesktopExe -Force
Write-Host "Build complete: $OutputPath"
Write-Host "Desktop copy: $DesktopExe"
