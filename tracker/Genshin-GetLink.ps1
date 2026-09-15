# Genshin-GetLink.ps1
# Extracts the Wish History URL from the Genshin Impact client cache.
# USAGE:
#   1. Open Genshin Impact and view your Wish History (Wishes > History) at least once.
#   2. Run:  powershell -ExecutionPolicy Bypass -File .\Genshin-GetLink.ps1
#      (or right-click > Run with PowerShell)
#   3. The URL is copied to your clipboard — paste it into /import <url> on Discord.
#
# For China-server installs run:  .\Genshin-GetLink.ps1 china

param(
    [string]$Region = "global"
)

$logLocation = "$env:USERPROFILE\AppData\LocalLow\miHoYo\Genshin Impact\output_log.txt"
$logLocationChina = "$env:USERPROFILE\AppData\LocalLow\miHoYo\$([char]0x539f)$([char]0x795e)\output_log.txt"

if ($Region -eq "china") {
    Write-Host "Using China client log location"
    $logLocation = $logLocationChina
}

$path = [System.Environment]::ExpandEnvironmentVariables($logLocation)

if (-Not [System.IO.File]::Exists($path)) {
    Write-Host "Cannot find the game log file! Make sure you opened the Wish History in-game at least once." -ForegroundColor Red
    Write-Host "Expected: $path"
    return
}

# Find the game install directory from the log
$logs = Get-Content -Path $path
$m = $logs -match "(?m).:/.+(GenshinImpact_Data|YuanShen_Data)"
if (-Not $m -or $m.Length -eq 0) {
    Write-Host "Cannot find the game directory in the log." -ForegroundColor Red
    return
}
$m[0] -match "(.:/.+(GenshinImpact_Data|YuanShen_Data))" >$null
$gamedir = $matches[1]

# webCaches may be directly under it (old clients) or under a version
# subfolder like webCaches\2.54.0.0\ (Luna/5.x+ clients) — pick the newest.
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
    Write-Host "Cannot find the web cache file! Open the Wish History in-game, then re-run this script." -ForegroundColor Red
    return
}
Write-Host "Using cache: $cachefile"

$tmpfile = "$env:TEMP\genshin_data_2"
Copy-Item $cachefile -Destination $tmpfile -Force
$content = Get-Content -Encoding UTF8 -Raw $tmpfile
Remove-Item $tmpfile

$splitted = $content -split "1/0/"
$found = $splitted -match "https.+?game_biz=hk4e.+?&"
if (-Not $found -or $found.Length -eq 0) {
    Write-Host "Cannot find the wish history URL! Open the Wish History in-game, then re-run this script." -ForegroundColor Red
    return
}

$found[$found.Length - 1] -match "(https.+?game_biz=hk4e.+?)&" >$null

if (-Not $matches[1]) {
    Write-Host "Cannot find the wish history URL! Open the Wish History in-game, then re-run this script." -ForegroundColor Red
    return
}

$wishUrl = $matches[1]
Write-Host ""
Write-Host "Wish History URL found:" -ForegroundColor Green
Write-Host $wishUrl
Set-Clipboard -Value $wishUrl
Write-Host ""
Write-Host "Copied to clipboard. Use  /import <url> game:Genshin Impact  in Discord." -ForegroundColor Green
