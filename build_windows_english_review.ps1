$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot
$version = (Get-Content -LiteralPath 'VERSION.txt' -Raw).Trim()
$name = "ResolutionFileManager-v$version-English-Review"
python -c "from tools.validate_help import validate; r=validate(languages=['en']); assert not r['errors'], r['errors']; print('English help validated; other languages intentionally await review approval.')"
if ($LASTEXITCODE -ne 0) { throw 'English help validation failed' }
$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
$ffplay = (Get-Command ffplay -ErrorAction Stop).Source
python -m PyInstaller --noconfirm --clean --onefile --windowed --name $name --distpath "dist/english-review-$version" --workpath "build/windows-english-review-$version" --icon app_icon.ico --add-data 'app_icon.png;.' --add-data 'locales;locales' --add-binary "$ffmpeg;." --add-binary "$ffprobe;." --add-binary "$ffplay;." media_sorter.py
if ($LASTEXITCODE -ne 0) { throw 'English review build failed' }
$output = Join-Path $projectRoot "dist/english-review-$version/$name.exe"
$desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) "$name.exe"
if (Test-Path -LiteralPath $desktop) { $desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) "$name-$(Get-Date -Format 'yyyyMMdd-HHmmss').exe" }
Copy-Item -LiteralPath $output -Destination $desktop
Get-FileHash -LiteralPath $output, $desktop
Write-Output "Desktop review executable: $desktop"
