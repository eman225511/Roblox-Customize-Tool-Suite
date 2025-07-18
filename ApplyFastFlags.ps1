# PowerShell script to apply FastFlags to Roblox, Bloxstrap, or Fishstrap
param()

# Get script directory for safe path handling
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

# Set paths with proper escaping for spaces
$ROBLOX = Join-Path $env:LOCALAPPDATA "Roblox"
$BLOXSTRAP = Join-Path $env:LOCALAPPDATA "Bloxstrap"  
$FISHSTRAP = Join-Path $env:LOCALAPPDATA "Fishstrap"

$ROBLOXVERSIONS = Join-Path $ROBLOX "Versions"
$BLOXSTRAPVERSIONS = Join-Path $BLOXSTRAP "Versions"
$FISHSTRAPVERSIONS = Join-Path $FISHSTRAP "Versions"

$FASTFLAGPRESETS = Join-Path $ScriptDir "FastFlagPresets.json"

# Clear screen and set up console
Clear-Host
$Host.UI.RawUI.WindowTitle = "FastFlag Applier v2.0"

# Header
Write-Host ""
Write-Host "+============================================================+" -ForegroundColor DarkCyan
Write-Host "|                     FASTFLAG APPLIER v2.0                 |" -ForegroundColor Cyan
Write-Host "|                  Apply FastFlags with Style               |" -ForegroundColor DarkCyan
Write-Host "+============================================================+" -ForegroundColor DarkCyan
Write-Host ""

# Launcher selection with fancy formatting
Write-Host "+- SELECT LAUNCHER -------------------------------------+" -ForegroundColor Yellow
Write-Host "|  [R] Roblox                                       |" -ForegroundColor White
Write-Host "|  [B] Bloxstrap                                    |" -ForegroundColor White  
Write-Host "|  [F] Fishstrap                                    |" -ForegroundColor White
Write-Host "+-----------------------------------------------------+" -ForegroundColor Yellow

Write-Host ""

do {
    Write-Host -NoNewline "> " -ForegroundColor Cyan
    $CHOICE = Read-Host "Select launcher (R/B/F)"
    $CHOICE = $CHOICE.ToUpper()
    if ($CHOICE -notin @("R", "B", "F")) {
        Write-Host "[ERROR] Invalid choice. Please select R, B, or F." -ForegroundColor Red
    }
} while ($CHOICE -notin @("R", "B", "F"))

# Show selected launcher
$launcherName = switch ($CHOICE) {
    "R" { "[R] Roblox" }
    "B" { "[B] Bloxstrap" }
    "F" { "[F] Fishstrap" }
}
Write-Host "[SUCCESS] Selected: $launcherName" -ForegroundColor Green

# Set versions path based on choice
switch ($CHOICE) {
    "R" { $VERSIONSPATH = $ROBLOXVERSIONS }
    "B" { $VERSIONSPATH = $BLOXSTRAPVERSIONS }
    "F" { $VERSIONSPATH = $FISHSTRAPVERSIONS }
}

Write-Host ""

Write-Host ""
Write-Host ""

# Options selection with fancy formatting
Write-Host "+- SELECT ACTION -----------------------------------+" -ForegroundColor Magenta
Write-Host "|  [P] Apply Preset FastFlags                   |" -ForegroundColor White
Write-Host "|  [L] Apply Fleasion Flag                      |" -ForegroundColor White
Write-Host "+-------------------------------------------------+" -ForegroundColor Magenta
Write-Host ""

do {
    Write-Host -NoNewline "> " -ForegroundColor Magenta
    $PRESETCHOICE = Read-Host "Select action (P/L)"
    $PRESETCHOICE = $PRESETCHOICE.ToUpper()
    if ($PRESETCHOICE -notin @("P", "L")) {
        Write-Host "[ERROR] Invalid choice. Please select P or L." -ForegroundColor Red
    }
} while ($PRESETCHOICE -notin @("P", "L"))

Write-Host ""

Write-Host "DEBUG: PRESETCHOICE = '$PRESETCHOICE'" -ForegroundColor Magenta

if ($PRESETCHOICE -eq "P") {
    Write-Host "DEBUG: Entering Presets section" -ForegroundColor Magenta
    # Apply Presets
    Write-Host ""
    Write-Host "+- FASTFLAG PRESETS ------------------------------+" -ForegroundColor Green
    Write-Host "|  [1] Don's Fast Flags     - Performance      |" -ForegroundColor White
    Write-Host "|  [2] Ricky's Fast Flags   - High FPS         |" -ForegroundColor White
    Write-Host "|  [3] No Texture Fast Flags - Minimal textures|" -ForegroundColor White
    Write-Host "|  [4] Antwis Fast Flags    - Comprehensive    |" -ForegroundColor White
    Write-Host "|  [5] Eman's Fast Flags    - Custom optimized |" -ForegroundColor White
    Write-Host "+-------------------------------------------------+" -ForegroundColor Green
    Write-Host ""

    do {
        Write-Host -NoNewline "> " -ForegroundColor Green
        $PRESETNUM = Read-Host "Select preset number (1-5)"
        if ($PRESETNUM -notin @("1", "2", "3", "4", "5")) {
            Write-Host "[ERROR] Invalid choice. Please select 1-5." -ForegroundColor Red
        }
    } while ($PRESETNUM -notin @("1", "2", "3", "4", "5"))

    # Map preset numbers to names
    $presetNames = @{
        "1" = "Don's Fast Flags"
        "2" = "Ricky's Fast Flags"
        "3" = "No Texture Fast Flags"
        "4" = "Antwis Fast Flags"
        "5" = "Eman's Fast Flags"
    }

    $PRESETNAME = $presetNames[$PRESETNUM]
    
    # Show selected preset
    $presetEmoji = @{
        "1" = "[1]"
        "2" = "[2]"
        "3" = "[3]"
        "4" = "[4]"
        "5" = "[5]"
    }
    Write-Host "[SUCCESS] Selected: $($presetEmoji[$PRESETNUM]) $PRESETNAME" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[PROGRESS] Applying $PRESETNAME preset..." -ForegroundColor Yellow
    Write-Host "=======================================================" -ForegroundColor DarkYellow

    # Check if FastFlagPresets.json exists
    if (-not (Test-Path -LiteralPath $FASTFLAGPRESETS)) {
        Write-Host "[ERROR] Error: $FASTFLAGPRESETS not found!" -ForegroundColor Red
        Write-Host "   Please ensure the FastFlag presets file is in the same directory." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit
    }

    # Load JSON and get preset
    try {
        $json = Get-Content -LiteralPath $FASTFLAGPRESETS -Encoding UTF8 | ConvertFrom-Json
        $preset = $json.$PRESETNAME
        
        if (-not $preset) {
            Write-Host "[ERROR] Error: Preset '$PRESETNAME' not found in $FASTFLAGPRESETS!" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit
        }
    }
    catch {
        Write-Host "[ERROR] Error reading $FASTFLAGPRESETS`: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }

    # Apply to all version folders
    if (Test-Path -LiteralPath $VERSIONSPATH) {
        $versionFolders = Get-ChildItem -LiteralPath $VERSIONSPATH -Directory -ErrorAction SilentlyContinue
        $successCount = 0
        
        foreach ($folder in $versionFolders) {
            try {
                $clientSettingsDir = Join-Path -Path $folder.FullName -ChildPath "ClientSettings"
                
                # Create ClientSettings directory if it doesn't exist
                if (-not (Test-Path -LiteralPath $clientSettingsDir)) {
                    New-Item -ItemType Directory -Path $clientSettingsDir -Force | Out-Null
                }
                
                $flagFile = Join-Path -Path $clientSettingsDir -ChildPath "ClientAppSettings.json"
                
                Write-Host "[FOLDER] Processing: " -NoNewline -ForegroundColor Gray
                Write-Host "$($folder.Name)" -ForegroundColor Cyan
                
                # Clear existing flags by deleting the file if it exists
                if (Test-Path $flagFile) {
                    Write-Host "   [DELETE] Clearing existing flags..." -ForegroundColor DarkYellow
                    Remove-Item $flagFile -Force
                    Start-Sleep -Milliseconds 200  # Increased delay
                    
                    # Verify deletion
                    if (Test-Path $flagFile) {
                        Write-Host "   [WARNING] Warning: File still exists after deletion attempt" -ForegroundColor Yellow
                    } else {
                        Write-Host "   [SUCCESS] Old flags cleared" -ForegroundColor DarkGreen
                    }
                }
                
                # Write new preset flags
                try {
                    Write-Host "   [CREATE] Creating new FastFlag file..." -ForegroundColor DarkYellow
                    $jsonContent = $preset | ConvertTo-Json -Depth 10
                    
                    # Try multiple methods to ensure file is written with proper path handling
                    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
                    [System.IO.File]::WriteAllText($flagFile, $jsonContent, $utf8NoBom)
                    
                    # Force a file system refresh
                    Start-Sleep -Milliseconds 100
                    
                    # Verify file was written
                    if (Test-Path -LiteralPath $flagFile) {
                        $fileSize = (Get-Item -LiteralPath $flagFile).Length
                        Write-Host "   [SUCCESS] Success! " -NoNewline -ForegroundColor Green
                        Write-Host "($fileSize bytes)" -ForegroundColor DarkGreen
                        $successCount++
                    } else {
                        Write-Host "   [ERROR] Failed to create file" -ForegroundColor Red
                    }
                }
                catch {
                    Write-Host "   [ERROR] Error: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "   [ERROR] Failed to apply to $($folder.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "=======================================================" -ForegroundColor DarkGreen
        if ($successCount -gt 0) {
            Write-Host "[SUCCESS] SUCCESS! " -NoNewline -ForegroundColor Green
            Write-Host "FastFlags from '$PRESETNAME' applied to $successCount version folders!" -ForegroundColor White
        } else {
            Write-Host "[ERROR] No FastFlags were applied. Check the errors above." -ForegroundColor Red
        }
    }
    else {
        Write-Host "[ERROR] Error: Versions path not found: $VERSIONSPATH" -ForegroundColor Red
        Write-Host "   Make sure the selected launcher is installed." -ForegroundColor Yellow
    }
}
elseif ($PRESETCHOICE -eq "L") {
    Write-Host "DEBUG: Entering Fleasion section" -ForegroundColor Magenta
    # Apply Fleasion Flag
    Write-Host ""
    Write-Host "[PROGRESS] Applying Fleasion FastFlag..." -ForegroundColor Yellow
    Write-Host "=======================================================" -ForegroundColor DarkYellow

    $fleasionFlag = @{
        "FFlagHttpUseRbxStorage10" = $false
    }

    # Apply to all version folders
    if (Test-Path -LiteralPath $VERSIONSPATH) {
        $versionFolders = Get-ChildItem -LiteralPath $VERSIONSPATH -Directory -ErrorAction SilentlyContinue
        $successCount = 0
        
        foreach ($folder in $versionFolders) {
            try {
                $clientSettingsDir = Join-Path -Path $folder.FullName -ChildPath "ClientSettings"
                
                # Create ClientSettings directory if it doesn't exist
                if (-not (Test-Path -LiteralPath $clientSettingsDir)) {
                    New-Item -ItemType Directory -Path $clientSettingsDir -Force | Out-Null
                }
                
                $flagFile = Join-Path -Path $clientSettingsDir -ChildPath "ClientAppSettings.json"
                
                Write-Host "[FOLDER] Processing: " -NoNewline -ForegroundColor Gray
                Write-Host "$($folder.Name)" -ForegroundColor Cyan
                
                # Clear existing flags by deleting the file if it exists
                if (Test-Path -LiteralPath $flagFile) {
                    Write-Host "   [DELETE] Clearing existing flags..." -ForegroundColor DarkYellow
                    Remove-Item -LiteralPath $flagFile -Force
                    Start-Sleep -Milliseconds 200  # Increased delay
                    
                    # Verify deletion
                    if (Test-Path -LiteralPath $flagFile) {
                        Write-Host "   [WARNING] Warning: File still exists after deletion attempt" -ForegroundColor Yellow
                    } else {
                        Write-Host "   [SUCCESS] Old flags cleared" -ForegroundColor DarkGreen
                    }
                }
                
                # Write new Fleasion flag
                try {
                    Write-Host "   [CREATE] Creating Fleasion FastFlag file..." -ForegroundColor DarkYellow
                    $jsonContent = $fleasionFlag | ConvertTo-Json -Depth 10
                    
                    # Try multiple methods to ensure file is written
                    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
                    [System.IO.File]::WriteAllText($flagFile, $jsonContent, $utf8NoBom)
                    
                    # Force a file system refresh
                    Start-Sleep -Milliseconds 100
                    
                    # Verify file was written
                    if (Test-Path $flagFile) {
                        $fileSize = (Get-Item $flagFile).Length
                        Write-Host "   [SUCCESS] Success! " -NoNewline -ForegroundColor Green
                        Write-Host "($fileSize bytes)" -ForegroundColor DarkGreen
                        $successCount++
                    } else {
                        Write-Host "   [ERROR] Failed to create file" -ForegroundColor Red
                    }
                }
                catch {
                    Write-Host "   [ERROR] Error: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "   [ERROR] Failed to apply to $($folder.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "=======================================================" -ForegroundColor DarkGreen
        if ($successCount -gt 0) {
            Write-Host "[SUCCESS] SUCCESS! " -NoNewline -ForegroundColor Green
            Write-Host "Fleasion FastFlag applied to $successCount version folders!" -ForegroundColor White
        } else {
            Write-Host "[ERROR] No FastFlags were applied. Check the errors above." -ForegroundColor Red
        }
    }
    else {
        Write-Host "[ERROR] Error: Versions path not found: $VERSIONSPATH" -ForegroundColor Red
        Write-Host "   Make sure the selected launcher is installed." -ForegroundColor Yellow
    }
}
else {
    Write-Host "[ERROR] DEBUG: No valid choice made. PRESETCHOICE = '$PRESETCHOICE'" -ForegroundColor Red
}

# Footer
Write-Host ""
Write-Host "+============================================================+" -ForegroundColor DarkCyan
Write-Host "|                    OPERATION COMPLETED                    |" -ForegroundColor Cyan
Write-Host "|              Thanks for using FastFlag Applier!           |" -ForegroundColor DarkCyan
Write-Host "+============================================================+" -ForegroundColor DarkCyan
Write-Host ""
Write-Host -NoNewline "Press " -ForegroundColor Gray
Write-Host -NoNewline "Enter" -ForegroundColor Yellow
Write-Host " to exit..." -ForegroundColor Gray
Read-Host
