<#
    WuWa Local Tracker
    
    This script runs entirely on your local machine.
    It does NOT send any data to external servers.
    It only fetches data from the official Kuro Games API.
    Pull history is saved as a JSON file in the same folder as this script.
    
    Usage:
    1. Launch Wuthering Waves and open Convene History in-game
    2. Run this script in PowerShell
    3. It will automatically find the URL from logs and fetch your gacha records
    
    License: MIT
#>

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = 'SilentlyContinue'
$SaveFolder = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($SaveFolder)) { $SaveFolder = (Get-Location).Path }

$BannerTypes = @{
    1 = "Featured Resonator"
    2 = "Featured Weapon"
    3 = "Standard Resonator"
    4 = "Standard Weapon"
    5 = "Beginner"
    6 = "Beginners Choice"
    7 = "Giveback"
}

function Get-RarityColor {
    param([int]$Rarity)
    switch ($Rarity) {
        5 { return "Yellow" }
        4 { return "Magenta" }
        3 { return "Cyan" }
        default { return "White" }
    }
}

# ============================================================
# Step 1: Find game path
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WuWa Local Tracker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/4] Searching for game path..." -ForegroundColor Yellow

$gamePath = $null
$gachaLogPathExists = $false

$64 = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
$32 = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"

try {
    $regResult = Get-ItemProperty -Path $32, $64 | Where-Object { $_.DisplayName -like "*wuthering*" } | Select-Object -First 1
    if ($regResult -and $regResult.InstallPath) {
        $gamePath = $regResult.InstallPath
        if ((Test-Path "$gamePath\Client\Saved\Logs\Client.log") -or
            (Test-Path "$gamePath\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
            $gachaLogPathExists = $true
        }
    }
} catch {}

if (!$gachaLogPathExists) {
    $muiCachePath = "Registry::HKEY_CURRENT_USER\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
    try {
        $filteredEntries = (Get-ItemProperty -Path $muiCachePath -ErrorAction SilentlyContinue).PSObject.Properties |
            Where-Object { $_.Value -like "*wuthering*" } |
            Where-Object { $_.Name -like "*client-win64-shipping.exe*" }
        if ($filteredEntries.Count -ne 0) {
            $gamePath = ($filteredEntries[0].Name -split '\\client\\')[0]
            if ((Test-Path "$gamePath\Client\Saved\Logs\Client.log") -or
                (Test-Path "$gamePath\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
                $gachaLogPathExists = $true
            }
        }
    } catch {}
}

if (!$gachaLogPathExists) {
    $firewallPath = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"
    try {
        $filteredEntries = (Get-ItemProperty -Path $firewallPath -ErrorAction SilentlyContinue).PSObject.Properties |
            Where-Object { $_.Value -like "*wuthering*" } |
            Where-Object { $_.Name -like "*client-win64-shipping*" }
        if ($filteredEntries.Count -ne 0) {
            $gamePath = (($filteredEntries[0].Value -split 'App=')[1] -split '\\client\\')[0]
            if ((Test-Path "$gamePath\Client\Saved\Logs\Client.log") -or
                (Test-Path "$gamePath\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
                $gachaLogPathExists = $true
            }
        }
    } catch {}
}

if (!$gachaLogPathExists) {
    $diskLetters = (Get-PSDrive -PSProvider FileSystem).Name
    foreach ($dl in $diskLetters) {
        if ($dl.Length -ne 1) { continue }
        $commonPaths = @(
            "${dl}:\Wuthering Waves Game",
            "${dl}:\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\Program Files\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\Program Files (x86)\Steam\steamapps\common\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\SteamLibrary\steamapps\common\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\Steam\steamapps\common\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\Program Files\Epic Games\WutheringWavesj3oFh\Wuthering Waves Game",
            "${dl}:\Games\Wuthering Waves\Wuthering Waves Game",
            "${dl}:\SteamLibrary\steamapps\common\Wuthering Waves",
            "${dl}:\Program Files (x86)\Steam\steamapps\common\Wuthering Waves",
            "${dl}:\Steam\steamapps\common\Wuthering Waves",
            "${dl}:\Program Files\Steam\steamapps\common\Wuthering Waves",
            "${dl}:\Games\Steam\steamapps\common\Wuthering Waves"
        )
        foreach ($p in $commonPaths) {
            if ((Test-Path "$p\Client\Saved\Logs\Client.log") -or
                (Test-Path "$p\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
                $gamePath = $p
                $gachaLogPathExists = $true
                break
            }
        }
        if ($gachaLogPathExists) { break }
    }
}

while (!$gachaLogPathExists) {
    Write-Host ""
    Write-Host "Could not find game path automatically." -ForegroundColor Red
    Write-Host "Please enter game install path (e.g. C:\Wuthering Waves\Wuthering Waves Game)" -ForegroundColor Yellow
    Write-Host "Type 'exit' to quit" -ForegroundColor DarkGray
    $manualPath = Read-Host "Path"
    if ($manualPath -eq "exit") { exit }
    if ($manualPath) {
        $gamePath = $manualPath
        if ((Test-Path "$gamePath\Client\Saved\Logs\Client.log") -or
            (Test-Path "$gamePath\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
            $gachaLogPathExists = $true
        } else {
            Write-Host "Log files not found. Please launch the game and open Convene History first." -ForegroundColor Red
        }
    }
}

Write-Host "  Found path: $gamePath" -ForegroundColor Green

# ============================================================
# Step 1.5: Collect ALL game installations
# ============================================================
$allGamePaths = @()
$allGamePaths += $gamePath

# Also scan all drives for additional installations
$diskLetters2 = (Get-PSDrive -PSProvider FileSystem).Name
foreach ($dl2 in $diskLetters2) {
    if ($dl2.Length -ne 1) { continue }
    $extraPaths = @(
        "${dl2}:\Wuthering Waves Game",
        "${dl2}:\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\Program Files\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\Program Files (x86)\Steam\steamapps\common\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\SteamLibrary\steamapps\common\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\Steam\steamapps\common\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\Program Files\Epic Games\WutheringWavesj3oFh\Wuthering Waves Game",
        "${dl2}:\Games\Wuthering Waves\Wuthering Waves Game",
        "${dl2}:\SteamLibrary\steamapps\common\Wuthering Waves",
        "${dl2}:\Program Files (x86)\Steam\steamapps\common\Wuthering Waves",
        "${dl2}:\Steam\steamapps\common\Wuthering Waves",
        "${dl2}:\Program Files\Steam\steamapps\common\Wuthering Waves",
        "${dl2}:\Games\Steam\steamapps\common\Wuthering Waves"
    )
    foreach ($ep in $extraPaths) {
        if ((Test-Path "$ep\Client\Saved\Logs\Client.log") -or
            (Test-Path "$ep\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log")) {
            if ($allGamePaths -notcontains $ep) {
                $allGamePaths += $ep
                Write-Host "  Found path: $ep" -ForegroundColor Green
            }
        }
    }
}

Write-Host "  Total installations found: $($allGamePaths.Count)" -ForegroundColor DarkGray

# ============================================================
# Step 2: Extract Convene URL from ALL logs (pick newest)
# ============================================================
Write-Host ""
Write-Host "[2/4] Extracting Convene URL from logs..." -ForegroundColor Yellow

$urlToCopy = $null
$newestLogTime = [datetime]::MinValue
$usedLogPath = ""

foreach ($gp in $allGamePaths) {
    $logCandidates = @(
        "$gp\Client\Saved\Logs\Client.log",
        "$gp\Client\Binaries\Win64\ThirdParty\KrPcSdk_Global\KRSDKRes\KRSDKWebView\debug.log"
    )

    foreach ($logPath in $logCandidates) {
        if (!(Test-Path $logPath)) { continue }

        $logInfo = Get-Item $logPath -ErrorAction SilentlyContinue
        if (!$logInfo) { continue }

        Write-Host "  Checking: $logPath (Modified: $($logInfo.LastWriteTime))" -ForegroundColor DarkGray

        $foundUrl = $null

        if ($logPath -like "*debug.log") {
            $entry = Select-String -Path $logPath -Pattern '"#url": "(https://aki-gm-resources(-oversea)?\.aki-game\.(net|com)/aki/gacha/index\.html#/record[^"]*)"' | Select-Object -Last 1
            if ($entry) {
                $foundUrl = $entry.Matches.Groups[1].Value
            }
        } else {
            $entry = Select-String -Path $logPath -Pattern "https://aki-gm-resources(-oversea)?\.aki-game\.(net|com)/aki/gacha/index\.html#/record" | Select-Object -Last 1
            if ($entry) {
                $foundUrl = $entry -replace '.*?(https://aki-gm-resources(-oversea)?\.aki-game\.(net|com)[^"]*)"?.*', '$1'
            }
        }

        if (![string]::IsNullOrWhiteSpace($foundUrl) -and $logInfo.LastWriteTime -gt $newestLogTime) {
            $urlToCopy = $foundUrl
            $newestLogTime = $logInfo.LastWriteTime
            $usedLogPath = $logPath
        }
    }
}

if ([string]::IsNullOrWhiteSpace($urlToCopy)) {
    Write-Host ""
    Write-Host "Could not find Convene URL!" -ForegroundColor Red
    Write-Host "Please launch the game and open Convene History first." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "  URL found in: $usedLogPath" -ForegroundColor Green

$urlParams = @{}
$urlParams["svr_id"] = [regex]::Match($urlToCopy, 'svr_id=([^&]+)').Groups[1].Value
$urlParams["player_id"] = [regex]::Match($urlToCopy, 'player_id=([^&]+)').Groups[1].Value
$urlParams["lang"] = [regex]::Match($urlToCopy, 'lang=([^&]+)').Groups[1].Value
$urlParams["gacha_id"] = [regex]::Match($urlToCopy, 'gacha_id=([^&]+)').Groups[1].Value
$urlParams["gacha_type"] = [regex]::Match($urlToCopy, 'gacha_type=([^&]+)').Groups[1].Value
$urlParams["svr_area"] = [regex]::Match($urlToCopy, 'svr_area=([^&]+)').Groups[1].Value
$urlParams["record_id"] = [regex]::Match($urlToCopy, 'record_id=([^&]+)').Groups[1].Value
$urlParams["resources_id"] = [regex]::Match($urlToCopy, 'resources_id=([^&]+)').Groups[1].Value

if ($urlToCopy -match "aki-game\.com") {
    $apiDomain = "https://gmserver-api.aki-game2.com"
} else {
    $apiDomain = "https://gmserver-api.aki-game2.net"
}

Write-Host "  Player ID: $($urlParams['player_id'])" -ForegroundColor DarkGray
Write-Host "  Server: $($urlParams['svr_area'])" -ForegroundColor DarkGray

# ============================================================
# Step 3: Fetch gacha records from API
# ============================================================
Write-Host ""
Write-Host "[3/4] Fetching gacha records from Kuro Games API..." -ForegroundColor Yellow

$ErrorActionPreference = "Stop"
$allPulls = @{}
$totalPulls = 0

foreach ($cardPoolType in 1..7) {
    $bannerName = if ($BannerTypes.ContainsKey($cardPoolType)) { $BannerTypes[$cardPoolType] } else { "Unknown ($cardPoolType)" }
    $bannerPulls = @()

    try {
        $apiUrl = "$apiDomain/gacha/record/query"
        $bodyObj = @{
            cardPoolId = $urlParams["record_id"]
            cardPoolType = $cardPoolType
            languageCode = $urlParams["lang"]
            playerId = $urlParams["player_id"]
            recordId = $urlParams["record_id"]
            serverId = $urlParams["svr_id"]
        }
        $body = $bodyObj | ConvertTo-Json -Compress
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop

        if ($response -and $response.data) {
            $bannerPulls = $response.data
        }
    } catch {
        try {
            $qs = "svr_id=$($urlParams['svr_id'])&player_id=$($urlParams['player_id'])&lang=$($urlParams['lang'])&gacha_type=$($urlParams['gacha_type'])&svr_area=$($urlParams['svr_area'])&record_id=$($urlParams['record_id'])&resources_id=$($urlParams['resources_id'])&cardPoolType=$cardPoolType"
            $apiUrl2 = "$apiDomain/gacha/record/query?$qs"
            $response2 = Invoke-RestMethod -Uri $apiUrl2 -Method Get -ErrorAction Stop
            if ($response2 -and $response2.data) {
                $bannerPulls = $response2.data
            }
        } catch {}
    }

    if ($bannerPulls.Count -gt 0) {
        $allPulls[$cardPoolType] = $bannerPulls
        $totalPulls += $bannerPulls.Count
        Write-Host "  ${bannerName}: $($bannerPulls.Count) pulls" -ForegroundColor Green
    }
}

if ($totalPulls -eq 0) {
    Write-Host ""
    Write-Host "Could not fetch gacha records." -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  - Convene URL may have expired (reopen Convene History in-game)" -ForegroundColor Yellow
    Write-Host "  - API endpoint may have changed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Copying URL to clipboard instead..." -ForegroundColor Cyan
    Set-Clipboard $urlToCopy
    Write-Host "URL copied: $urlToCopy" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "  Total: $totalPulls pulls fetched!" -ForegroundColor Green

# ============================================================
# Step 4: Save and display results
# ============================================================
Write-Host ""
Write-Host "[4/4] Saving and displaying results..." -ForegroundColor Yellow

$pullsStringKeys = @{}
foreach ($k in $allPulls.Keys) {
    $pullsStringKeys["$k"] = $allPulls[$k]
}

$savePath = Join-Path $SaveFolder "wuwa_pulls_$($urlParams['player_id']).json"

# ============================================================
# Merge with existing data (preserve old records beyond 6 months)
# ============================================================
if (Test-Path $savePath) {
    Write-Host "  Found existing data, merging..." -ForegroundColor DarkGray
    try {
        $existRaw = [System.IO.File]::ReadAllText($savePath, [System.Text.Encoding]::UTF8)
        $existRaw = $existRaw.TrimStart([char]0xFEFF)
        $existData = $existRaw | ConvertFrom-Json
        $existPulls = $existData.pulls

        foreach ($poolKey in $pullsStringKeys.Keys) {
            $newList = $pullsStringKeys[$poolKey]

            if ($existPulls.PSObject.Properties[$poolKey]) {
                $oldList = @($existPulls.$poolKey)

                # Build a set of unique keys from new data (time + name)
                $newKeys = @{}
                foreach ($item in $newList) {
                    $ukey = "$($item.time)|$($item.name)|$($item.qualityLevel)"
                    $newKeys[$ukey] = $true
                }

                # Add old items that are NOT in new data (these are expired from API)
                $merged = [System.Collections.ArrayList]@()
                foreach ($item in $newList) { [void]$merged.Add($item) }

                foreach ($oldItem in $oldList) {
                    $okey = "$($oldItem.time)|$($oldItem.name)|$($oldItem.qualityLevel)"
                    if (!$newKeys.ContainsKey($okey)) {
                        [void]$merged.Add($oldItem)
                    }
                }

                # Sort by time descending (newest first)
                $sorted = $merged | Sort-Object { [datetime]$_.time } -Descending
                $pullsStringKeys[$poolKey] = @($sorted)

                $addedCount = $merged.Count - $newList.Count
                if ($addedCount -gt 0) {
                    Write-Host "  Pool $poolKey : kept $addedCount old records" -ForegroundColor DarkGray
                }
            }
        }

        # Also keep pools that exist in old data but not in new fetch
        foreach ($prop in $existPulls.PSObject.Properties) {
            if (!$pullsStringKeys.ContainsKey($prop.Name)) {
                $pullsStringKeys[$prop.Name] = @($prop.Value)
                Write-Host "  Pool $($prop.Name): preserved from previous save" -ForegroundColor DarkGray
            }
        }
    }
    catch {
        Write-Host "  Warning: Could not merge old data, overwriting. Error: $_" -ForegroundColor DarkYellow
    }
}

$saveData = @{}
$saveData["player_id"] = $urlParams["player_id"]
$saveData["svr_area"] = $urlParams["svr_area"]
$saveData["fetched_at"] = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$saveData["pulls"] = $pullsStringKeys

$saveData | ConvertTo-Json -Depth 10 | Set-Content -Path $savePath -Encoding UTF8
Write-Host "  Saved to: $savePath" -ForegroundColor Green

# Count total
$totalMerged = 0
foreach ($k in $pullsStringKeys.Keys) { $totalMerged += $pullsStringKeys[$k].Count }
Write-Host "  Total records (after merge): $totalMerged" -ForegroundColor Green

# ============================================================
# Display summary with pity system
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done! Data saved." -ForegroundColor Green
Write-Host "  Location: $savePath" -ForegroundColor DarkGray
Write-Host "  Data sent to external servers: NONE" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open the viewer app (WuWa-Viewer.ps1) to see your stats." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"


