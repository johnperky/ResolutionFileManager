param([string]$WindowsVersion)
$ErrorActionPreference = 'Stop'
$Project = Split-Path -Parent $PSScriptRoot
if (-not $WindowsVersion) {
    $record = Get-ChildItem (Join-Path $Project 'docs') -Filter 'RELEASE_PUBLICATION_*.json' | ForEach-Object {
        $data = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
        if ($data.assets | Where-Object name -Like '*.exe') { $data }
    } | Sort-Object { [version]$_.version } -Descending | Select-Object -First 1
} else {
    $record = Get-Content -LiteralPath (Join-Path $Project "docs/RELEASE_PUBLICATION_$WindowsVersion.json") -Raw | ConvertFrom-Json
}
if (-not $record) { throw 'No verified Windows publication record found.' }
$WindowsVersion = $record.version
$portable = Join-Path $Project "release-output/$WindowsVersion/ResolutionFileManager-$WindowsVersion-Windows-x64"
$exe = Join-Path $portable "ResolutionFileManager-$WindowsVersion.exe"
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $record.binarySha256) { throw 'Windows executable differs from published checksum.' }
$kit = Join-Path (Split-Path $Project) "Windows Clean Test $WindowsVersion"
if (Test-Path -LiteralPath $kit) { throw "Preserving existing test kit: $kit" }
New-Item -ItemType Directory -Path $kit,(Join-Path $kit 'Results'),(Join-Path $kit 'Samples') | Out-Null
$sample = 'E:/free to use videos/sample-10s.mp4'
if (Test-Path -LiteralPath $sample) { Copy-Item -LiteralPath $sample -Destination (Join-Path $kit 'Samples/sample.mp4') }
$start = @'
$ErrorActionPreference = 'Stop'
$tools = 'C:\Users\WDAGUtilityAccount\Desktop\RFM-Test-Tools'
$results = 'C:\Users\WDAGUtilityAccount\Desktop\RFM-Test-Results'
$root = 'C:\RFM-Clean-Test'
New-Item -ItemType Directory -Path "$root\Media","$root\Settings\ResolutionFileManager" -Force | Out-Null
Start-Transcript -LiteralPath "$results\Startup.txt"
$exe = 'C:\Users\WDAGUtilityAccount\Desktop\RFM-Portable\ResolutionFileManager-__VERSION__.exe'
if ((Get-FileHash -LiteralPath $exe).Hash.ToLowerInvariant() -ne '__SHA__') { throw 'Binary checksum mismatch' }
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' | Select-Object DisplayVersion,CurrentBuild,EditionID | Format-List
Write-Output ('Python on PATH: ' + [bool](Get-Command python -ErrorAction SilentlyContinue))
Write-Output ('FFmpeg on PATH: ' + [bool](Get-Command ffmpeg -ErrorAction SilentlyContinue))
Add-Type -AssemblyName System.Drawing
$image = New-Object System.Drawing.Bitmap 640,480
$graphics = [System.Drawing.Graphics]::FromImage($image)
$graphics.Clear([System.Drawing.Color]::ForestGreen)
$image.Save("$root\Media\normal.jpg",[System.Drawing.Imaging.ImageFormat]::Jpeg)
$graphics.Dispose(); $image.Dispose()
Copy-Item "$root\Media\normal.jpg" "$root\Media\hidden.jpg"
[System.IO.File]::SetAttributes("$root\Media\hidden.jpg",[System.IO.FileAttributes]::Hidden)
Copy-Item "$root\Media\normal.jpg" "$root\Media\.dot-hidden.jpg"
if (Test-Path "$tools\Samples\sample.mp4") { Copy-Item "$tools\Samples\sample.mp4" "$root\Media\sample.mp4" }
$env:LOCALAPPDATA = "$root\Settings"
$settings = @{language='en'; geometry='1500x900'; show_hidden_files=$false; left=@{path="$root\Media"}; right=@{path="$root\Media"}; reminders=@{rating_disabled=$true;support_disabled=$true}}
[System.IO.File]::WriteAllText("$root\Settings\ResolutionFileManager\settings.json", ($settings | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding $false))
Copy-Item "$tools\CHECKLIST.md" "$results\CHECKLIST.md" -Force
Write-Output 'Startup checks recorded. Test the app using CHECKLIST.md in the host Results folder.'
Start-Process -FilePath $exe
Stop-Transcript
'@
$start.Replace('__VERSION__',$WindowsVersion).Replace('__SHA__',$record.binarySha256) | Set-Content -LiteralPath (Join-Path $kit 'Start-Test.ps1') -Encoding UTF8
$escape = { param($value) [System.Security.SecurityElement]::Escape($value) }
$config = @"
<Configuration>
  <Networking>Disable</Networking>
  <MappedFolders>
    <MappedFolder><HostFolder>$(& $escape $portable)</HostFolder><SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\RFM-Portable</SandboxFolder><ReadOnly>true</ReadOnly></MappedFolder>
    <MappedFolder><HostFolder>$(& $escape $kit)</HostFolder><SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\RFM-Test-Tools</SandboxFolder><ReadOnly>true</ReadOnly></MappedFolder>
    <MappedFolder><HostFolder>$(& $escape (Join-Path $kit 'Results'))</HostFolder><SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\RFM-Test-Results</SandboxFolder><ReadOnly>false</ReadOnly></MappedFolder>
  </MappedFolders>
  <LogonCommand><Command>powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\WDAGUtilityAccount\Desktop\RFM-Test-Tools\Start-Test.ps1</Command></LogonCommand>
</Configuration>
"@
$config | Set-Content -LiteralPath (Join-Path $kit 'Run Clean Windows Test.wsb') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $Project 'docs/WINDOWS_CLEAN_TEST.md') -Destination (Join-Path $kit 'CHECKLIST.md')
Write-Output "Prepared: $kit"
Write-Output 'Enable Windows Sandbox in Windows Features first if unavailable; this script does not enable it or restart Windows.'
