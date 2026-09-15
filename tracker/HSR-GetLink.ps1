# HSR-GetLink.ps1
# Extracts the Warp History URL from the Honkai: Star Rail client cache.
# USAGE:
#   1. Open Honkai: Star Rail and view your Warp History (Warp > Records) at least once.
#   2. Run:  powershell -ExecutionPolicy Bypass -File .\HSR-GetLink.ps1
#   3. The URL is copied to your clipboard — paste it into /import <url> on Discord.

# The log lives under AppData\LocalLow\miHoYo\Star Rail (global) or
# miHoYo\崩坏：星穹铁道 (China). Search for it if the default is missing.
$candidates = @(
    "$env:USERPROFILE\AppData\LocalLow\miHoYo\Star Rail\output_log.txt",
    "$env:USERPROFILE\AppData\LocalLow\miHoYo\$([char]0x5d29)$([char]0x574f)$([char]0xff1a)$([char]0x661f)$([char]0x7a79)$([char]0x94c1\)\output_log.txt"
)
$logLocation = $null
foreach ($c in $candidates) {
    if ([System.IO.File]::Exists($c)) { $logLocation = $c; break }
}
if (-Not $logLocation) {
    $found = Get-ChildItem "$env:USERPROFILE\AppData\LocalLow\miHoYo" -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path "$($_.FullName)\output_log.txt" }
    if ($found) { $logLocation = "$($found[0].FullName)\output_log.txt" }
}

if (-Not $logLocation) {
    Write-Host "Cannot find the game log file! Make sure you opened the Warp History in-game at least once." -ForegroundColor Red
    Write-Host "Expected one of:"; $candidates | ForEach-Object { Write-Host "  $_" }
    return
}
Write-Host "Using log: $logLocation"

$path = $logLocation
$logs = Get-Content -Path $path
$m = $logs -match "(?m).:/.+(StarRail_Data|YuanShen_Data)"
if (-Not $m -or $m.Length -eq 0) {
    Write-Host "Cannot find the game directory in the log." -ForegroundColor Red
    return
}
$m[0] -match "(.:/.+(StarRail_Data))" >$null
$gamedir = $matches[1]

$webCachesRoot = "$gamedir/webCaches"
$cachefile = $null
if ([System.IO.File]::Exists("$webCachesRoot/Cache/Cache_Data/data_2")) {
    $cachefile = "$webCachesRoot/Cache/Cache_Data/data_2"
} else {
    $versionDirs = Get-ChildItem -Path $webCachesRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending
    foreach ($vd in $versionDirs) {
        $candidate = "$webCachesRoot/$($vd.Name)/Cache/Cache_Data/data_2"
        if ([System.IO.File]::Exists($candidate)) { $cachefile = $candidate; break }
    }
}

if (-Not $cachefile) {
    Write-Host "Cannot find the web cache file! Open the Warp History in-game, then re-run this script." -ForegroundColor Red
    return
}
Write-Host "Using cache: $cachefile"

$tmpfile = "$env:TEMP\hsr_data_2"
Copy-Item $cachefile -Destination $tmpfile -Force
$content = Get-Content -Encoding UTF8 -Raw $tmpfile
Remove-Item $tmpfile

$splitted = $content -split "1/0/"
$found = $splitted -match "https.+?game_biz=hkrpg.+?&"
if (-Not $found -or $found.Length -eq 0) {
    Write-Host "Cannot find the warp history URL! Open the Warp History in-game, then re-run this script." -ForegroundColor Red
    return
}

$found[$found.Length - 1] -match "(https.+?game_biz=hkrpg.+?)&" >$null

if (-Not $matches[1]) {
    Write-Host "Cannot find the warp history URL! Open the Warp History in-game, then re-run this script." -ForegroundColor Red
    return
}

$warpUrl = $matches[1]
Write-Host ""
Write-Host "Warp History URL found:" -ForegroundColor Green
Write-Host $warpUrl
Set-Clipboard -Value $warpUrl
Write-Host ""
Write-Host "Copied to clipboard. Use  /import <url> game:Honkai: Star Rail  in Discord." -ForegroundColor Green
