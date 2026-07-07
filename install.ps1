$ErrorActionPreference = 'Stop'

function Write-Color([String]$Text, [ConsoleColor]$Color) {
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header([String]$Text) {
    Write-Host "`n✨ " -NoNewline
    Write-Host $Text -ForegroundColor Cyan -NoNewline
    Write-Host " ✨"
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
}

$logo = @"
    ______ __               __  ___          ___ 
   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____
  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \ 
 / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ / 
/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/  

"@

# Helper to swallow output and errors silently
function Run-Silent([scriptblock]$Script) {
    $oldError = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        & $Script 2>&1 | Out-Null
    } catch {}
    $ErrorActionPreference = $oldError
}

function Install-Python {
    Write-Host "⏳ " -NoNewline; Write-Host "Fetching Python via Winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements | Out-Null
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "✅ " -NoNewline; Write-Host "Python installed." -ForegroundColor Green
}

function Install-FFmpeg {
    Write-Host "⏳ " -NoNewline; Write-Host "Fetching FFmpeg via Winget..." -ForegroundColor Yellow
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements | Out-Null
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "✅ " -NoNewline; Write-Host "FFmpeg installed." -ForegroundColor Green
}

function Install-FluxMedia {
    Write-Host "⏳ " -NoNewline; Write-Host "Fetching fluxmedia..." -ForegroundColor Yellow
    Run-Silent { python -m pip install --upgrade pip -q }
    Run-Silent { python -m pip install -U fluxmedia -q }
    Write-Host "✅ " -NoNewline; Write-Host "FluxMedia Core installed." -ForegroundColor Green
}

function Uninstall-FluxMedia {
    Write-Host "⏳ " -NoNewline; Write-Host "Removing fluxmedia and all dependencies..." -ForegroundColor Yellow
    $oldError = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    python -m pip uninstall -y fluxmedia rich requests yt-dlp textual markdown-it-py pygments -q 2>&1 | Out-Null
    $ErrorActionPreference = $oldError
    Write-Host "✅ " -NoNewline; Write-Host "FluxMedia Core and dependencies removed." -ForegroundColor Green
}

function Uninstall-FFmpeg {
    Write-Host "⏳ " -NoNewline; Write-Host "Removing FFmpeg..." -ForegroundColor Yellow
    winget uninstall -e --id Gyan.FFmpeg --silent --accept-source-agreements | Out-Null
    Write-Host "✅ " -NoNewline; Write-Host "FFmpeg removed." -ForegroundColor Green
}

function Uninstall-Python {
    Write-Host "⏳ " -NoNewline; Write-Host "Removing Python..." -ForegroundColor Yellow
    
    # 1. Attempt winget ID uninstalls
    for ($i = 8; $i -le 16; $i++) {
        winget uninstall -e --id Python.Python.3.$i --silent --accept-source-agreements 2>&1 | Out-Null
    }
    
    # 2. Attempt native PackageManagement (catches manual python.org installs)
    Get-Package -Name "Python 3.*" -ErrorAction SilentlyContinue | Uninstall-Package -AllVersions -Force -ErrorAction SilentlyContinue | Out-Null
    Get-Package -Name "Python Launcher" -ErrorAction SilentlyContinue | Uninstall-Package -AllVersions -Force -ErrorAction SilentlyContinue | Out-Null
    
    # 3. Attempt to remove Windows Store versions of Python
    Get-AppxPackage *PythonSoftwareFoundation* 2>&1 | Remove-AppxPackage 2>&1 | Out-Null
    
    # 4. Ultimate Brute Force Cleanup (Bypasses Admin/User scope conflict locks)
    $pythonLocalPath = "$env:LOCALAPPDATA\Programs\Python"
    if (Test-Path $pythonLocalPath) { Remove-Item -Path $pythonLocalPath -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path "$env:ProgramFiles\Python*") { Remove-Item -Path "$env:ProgramFiles\Python*" -Recurse -Force -ErrorAction SilentlyContinue }
    
    # 5. Clean PATH variable of any Python references
    $mPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $uPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $newMPath = ($mPath -split ';' | Where-Object { $_ -notmatch 'Python' }) -join ';'
    $newUPath = ($uPath -split ';' | Where-Object { $_ -notmatch 'Python' }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newMPath, "Machine")
    [Environment]::SetEnvironmentVariable("Path", $newUPath, "User")
    $env:Path = $newMPath + ";" + $newUPath

    Write-Host "✅ " -NoNewline; Write-Host "Python removed." -ForegroundColor Green
}

function Show-MainMenu {
    while ($true) {
        Clear-Host
        Write-Color $logo "Cyan"
        Write-Color "          Welcome to the FluxMedia Toolkit!      " "White"
        Write-Color "          Fast, Aesthetic, and Powerful.         " "DarkGray"
        Write-Host ""
        Write-Color "Please select an action:" "White"
        Write-Color "  [1] Install FluxMedia (Default setup)" "Cyan"
        Write-Color "  [2] Reinstall components" "Yellow"
        Write-Color "  [3] Uninstall components" "Red"
        Write-Color "  [0] Exit" "DarkGray"
        Write-Host ""
        
        $choice = Read-Host "Choice"
        switch ($choice) {
            '1' { Do-Install; return }
            '2' { Show-ReinstallMenu }
            '3' { Show-UninstallMenu }
            '0' { Write-Color "`nGoodbye!" "Cyan"; exit }
        }
    }
}

function Show-UninstallMenu {
    while ($true) {
        Clear-Host
        Write-Header "Uninstall Menu"
        Write-Color "  [1] Uninstall FluxMedia Core Only" "Red"
        Write-Color "  [2] Uninstall FluxMedia + FFmpeg" "Red"
        Write-Color "  [3] Uninstall Everything (FluxMedia, FFmpeg, and Python)" "Red"
        Write-Color "  [0] Back to Main Menu" "DarkGray"
        Write-Host ""
        
        $choice = Read-Host "Choice"
        switch ($choice) {
            '1' {
                Uninstall-FluxMedia
                PauseAndReturn
                return
            }
            '2' {
                Uninstall-FluxMedia
                Uninstall-FFmpeg
                PauseAndReturn
                return
            }
            '3' {
                Write-Host ""
                Write-Color "⚠️  CRITICAL WARNING ⚠️" "Red"
                Write-Color "Removing Python completely from your system may break other tools or scripts that depend on it." "Yellow"
                $confirm = Read-Host "Are you absolutely sure you want to remove Python? (y/N)"
                if ($confirm -eq 'y' -or $confirm -eq 'Y') {
                    Uninstall-FluxMedia
                    Uninstall-FFmpeg
                    Uninstall-Python
                    PauseAndReturn
                    return
                } else {
                    Write-Color "Python removal aborted." "Green"
                    Start-Sleep 2
                }
            }
            '0' { return }
        }
    }
}

function Show-ReinstallMenu {
    while ($true) {
        Clear-Host
        Write-Header "Reinstall Menu"
        Write-Color "  [1] Reinstall FluxMedia Core Only" "Yellow"
        Write-Color "  [2] Reinstall FFmpeg Only" "Yellow"
        Write-Color "  [3] Reinstall Python Only" "Yellow"
        Write-Color "  [4] Reinstall Everything" "Yellow"
        Write-Color "  [0] Back to Main Menu" "DarkGray"
        Write-Host ""
        
        $choice = Read-Host "Choice"
        switch ($choice) {
            '1' {
                Uninstall-FluxMedia; Install-FluxMedia
                PauseAndReturn
                return
            }
            '2' {
                Uninstall-FFmpeg; Install-FFmpeg
                PauseAndReturn
                return
            }
            '3' {
                Uninstall-Python; Install-Python
                PauseAndReturn
                return
            }
            '4' {
                Uninstall-FluxMedia; Uninstall-FFmpeg; Uninstall-Python
                Install-Python; Install-FFmpeg; Install-FluxMedia
                PauseAndReturn
                return
            }
            '0' { return }
        }
    }
}

function PauseAndReturn {
    Write-Host ""
    Write-Color "Operation completed successfully!" "Green"
    Read-Host "Press Enter to return to main menu..."
}

function Do-Install {
    Write-Header "Step 1: Checking Python Environment"
    $pythonExists = $false
    try {
        $pyVersion = & python --version 2>&1
        if ($pyVersion -match "Python 3") { $pythonExists = $true }
    } catch {}

    if ($pythonExists) {
        Write-Host "✅ " -NoNewline; Write-Host "Python is already installed and ready." -ForegroundColor Green
    } else {
        Install-Python
    }

    Write-Header "Step 2: Checking Media Engine (FFmpeg)"
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Host "✅ " -NoNewline; Write-Host "FFmpeg is already installed and ready." -ForegroundColor Green
    } else {
        Install-FFmpeg
    }

    Write-Header "Step 3: Installing FluxMedia Core"
    Install-FluxMedia
    
    Write-Host "`n🎉 " -NoNewline; Write-Host "SUCCESS! All components are fully installed." -ForegroundColor Green
    Write-Host "------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "You can now run FluxMedia from anywhere by typing: " -NoNewline
    Write-Host "fluxmedia" -ForegroundColor Cyan
    Write-Host "------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ""

    $launch = Read-Host "🎬 Would you like to launch FluxMedia right now? (Y/n)"
    if ($launch -ne 'n' -and $launch -ne 'N') {
        Clear-Host
        if (Get-Command fluxmedia -ErrorAction SilentlyContinue) {
            fluxmedia
        } else {
            python -m fluxmedia
        }
    }
}

# Start the application
Show-MainMenu
