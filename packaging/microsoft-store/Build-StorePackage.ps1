param(
    [Parameter(Mandatory = $true)] [string] $IdentityName,
    [Parameter(Mandatory = $true)] [string] $Publisher,
    [Parameter(Mandatory = $true)] [string] $PublisherDisplayName,
    [string] $Version = "12.2.2.0"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$storeRoot = $PSScriptRoot
$stageRoot = Join-Path $storeRoot "stage"
$outputRoot = Join-Path $storeRoot "output"
$assetRoot = Join-Path $stageRoot "Assets"
$sourceExe = Join-Path $projectRoot "ResolutionFileManager.exe"
$sourceIcon = Join-Path $projectRoot "app_icon.png"
$makeAppx = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\makeappx.exe"

if (-not (Test-Path -LiteralPath $sourceExe)) { throw "Missing executable: $sourceExe" }
if (-not (Test-Path -LiteralPath $sourceIcon)) { throw "Missing icon: $sourceIcon" }
if (-not (Test-Path -LiteralPath $makeAppx)) { throw "MakeAppx.exe was not found. Install the Windows 10/11 SDK." }
if ($Version -notmatch '^([1-9][0-9]{0,4})\.([0-9]{1,5})\.([0-9]{1,5})\.0$') {
    throw "Store versions must use four numeric sections and end in .0, for example 12.2.2.0."
}

Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $assetRoot -Force | Out-Null
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

Copy-Item -LiteralPath $sourceExe -Destination (Join-Path $stageRoot "ResolutionFileManager.exe")
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination (Join-Path $stageRoot "LICENSE.txt")
Copy-Item -LiteralPath (Join-Path $projectRoot "PRIVACY.md") -Destination (Join-Path $stageRoot "PRIVACY.md")
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_NOTICES.md") -Destination (Join-Path $stageRoot "THIRD_PARTY_NOTICES.md")

Add-Type -AssemblyName System.Drawing
function New-StoreAsset {
    param([int] $Width, [int] $Height, [string] $Name, [switch] $Wide)
    $canvas = New-Object System.Drawing.Bitmap($Width, $Height)
    $graphics = [System.Drawing.Graphics]::FromImage($canvas)
    $graphics.Clear([System.Drawing.Color]::FromArgb(18, 30, 48))
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $icon = [System.Drawing.Image]::FromFile($sourceIcon)
    try {
        $side = [Math]::Min($Width, $Height)
        $target = if ($Wide) { [int]($side * 0.78) } else { [int]($side * 0.80) }
        $x = [int](($Width - $target) / 2)
        $y = [int](($Height - $target) / 2)
        $graphics.DrawImage($icon, $x, $y, $target, $target)
        $canvas.Save((Join-Path $assetRoot $Name), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $icon.Dispose()
        $graphics.Dispose()
        $canvas.Dispose()
    }
}

New-StoreAsset 50 50 "StoreLogo.png"
New-StoreAsset 44 44 "Square44x44Logo.png"
New-StoreAsset 150 150 "Square150x150Logo.png"
New-StoreAsset 310 310 "Square310x310Logo.png"
New-StoreAsset 310 150 "Wide310x150Logo.png" -Wide

$manifest = Get-Content -LiteralPath (Join-Path $storeRoot "AppxManifest.template.xml") -Raw
$manifest = $manifest.Replace("__IDENTITY_NAME__", $IdentityName)
$manifest = $manifest.Replace("__PUBLISHER__", $Publisher)
$manifest = $manifest.Replace("__PUBLISHER_DISPLAY_NAME__", $PublisherDisplayName)
$manifest = $manifest.Replace("__VERSION__", $Version)
[System.IO.File]::WriteAllText((Join-Path $stageRoot "AppxManifest.xml"), $manifest, [System.Text.UTF8Encoding]::new($false))

$outputPackage = Join-Path $outputRoot "ResolutionFileManager-$Version-x64.msix"
Remove-Item -LiteralPath $outputPackage -Force -ErrorAction SilentlyContinue
& $makeAppx pack /o /v /h SHA256 /d $stageRoot /p $outputPackage
if ($LASTEXITCODE -ne 0) { throw "MakeAppx failed with exit code $LASTEXITCODE" }
Get-FileHash -LiteralPath $outputPackage -Algorithm SHA256 | Format-List
Write-Host "Store package created: $outputPackage"
