param(
    [string]$Language = 'it',
    [ValidateSet('Details','Thumbnails')][string]$View = 'Details',
    [string]$Search = '',
    [ValidateSet('name','duration','resolution','codec','size')][string]$Sort = 'resolution',
    [string]$MediaPath = 'E:\free to use videos',
    [switch]$Info
)
$ErrorActionPreference='Stop'
if (-not(Test-Path -LiteralPath $MediaPath -PathType Container)) { throw "Sample folder is missing: $MediaPath" }
if ((Split-Path -Qualifier $MediaPath) -ne 'E:') { throw 'Store capture sessions must use the E: sample drive.' }
$projectRoot=Split-Path -Parent $PSScriptRoot
$version=(Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'VERSION.txt')).Trim()
$exePath=Join-Path $projectRoot "dist/multilingual-review-$version/ResolutionFileManager-v$version-Multilingual-Review.exe"
if (-not(Test-Path -LiteralPath $exePath)) { throw "Current multilingual review build is missing: $exePath" }
$reviewRoot=Join-Path (Split-Path -Parent $projectRoot) "Store Preparation $version"
$reviewData=Join-Path $reviewRoot 'Review Settings'
$settingsFolder=Join-Path $reviewData 'ResolutionFileManager'
if (Get-Process | Where-Object { $_.Path -eq $exePath }) { throw 'Close the isolated dist review app before changing its review settings.' }
New-Item -ItemType Directory -Force -Path $settingsFolder | Out-Null
$previousData=Join-Path (Split-Path -Parent $projectRoot) 'Store Preparation 12.7.4/Review Settings/ResolutionFileManager'
$settingsPath=Join-Path $settingsFolder 'settings.json'
$template=if(Test-Path -LiteralPath $settingsPath) {$settingsPath} else {Join-Path $previousData 'settings.json'}
$prefs=Get-Content -Raw -LiteralPath $template | ConvertFrom-Json -AsHashtable
$prefs.language=$Language
$prefs.geometry='1900x900+0+0'
$prefs.browser_split=960
$prefs.preview_split=480
$prefs.performance_profile='Quiet'
$prefs.reminders.rating_disabled=$true
$prefs.reminders.support_disabled=$true
foreach($side in @('left','right')) {
    $prefs[$side].path=$MediaPath
    $prefs[$side].recursive=$true
    $prefs[$side].inspector_enabled=($Info -and $side -eq 'right')
    $prefs[$side].inspector_width=290
    $prefs[$side].folder_width=200
    $prefs[$side].thumbnail_pixels=160
    $prefs[$side].view_mode=if($side -eq 'left') {$View} else {'Details'}
    $prefs[$side].show_images=$false
    $prefs[$side].show_videos=$true
    $prefs[$side].search=if($side -eq 'left') {$Search} else {''}
    $prefs[$side].sort_column=if($side -eq 'left') {$Sort} else {'resolution'}
    $prefs[$side].sort_reverse=($side -eq 'right' -or $Sort -eq 'duration')
    $prefs[$side].column_order=@('name','codec','resolution','duration','size','rate','fps','modified','type','bitrate','audio','hdr','pixels','color','tags','rating')
    $prefs[$side].column_widths.name=270
    $prefs[$side].Remove('column_width_language')
}
$prefs | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding utf8
# Reuse only the closed, isolated review instance's metadata cache. Never use
# or overwrite the user's personal settings or database.
$cachePath=Join-Path $settingsFolder 'metadata-cache.sqlite3'
if (-not(Test-Path -LiteralPath $cachePath)) {
    $previousCache=Join-Path $previousData 'metadata-cache.sqlite3'
    if(Test-Path -LiteralPath $previousCache) {Copy-Item -LiteralPath $previousCache -Destination $cachePath}
}
$start=[System.Diagnostics.ProcessStartInfo]::new()
$start.FileName=$exePath
$start.UseShellExecute=$false
$start.Environment['LOCALAPPDATA']=$reviewData
$process=[System.Diagnostics.Process]::Start($start)
$deadline=[DateTime]::UtcNow.AddSeconds(30)
do {
    $ready=Get-Process | Where-Object { $_.Path -eq $exePath -and $_.MainWindowHandle -ne 0 }
    if ($ready) {break}
    Start-Sleep -Milliseconds 200
} while ([DateTime]::UtcNow -lt $deadline)
if (-not $ready) {throw 'The isolated review app did not expose its window within 30 seconds.'}
Write-Output "Isolated $Language review PID $($process.Id); settings: $settingsPath"
