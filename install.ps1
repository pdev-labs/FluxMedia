$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Unicode definitions (immune to file encoding corruption)
$e_sparkle = [char]::ConvertFromUtf32(0x2728)
$e_hour = [char]::ConvertFromUtf32(0x23F3)
$e_check = [char]::ConvertFromUtf32(0x2705)
$e_cross = [char]::ConvertFromUtf32(0x274C)
$e_warn = [char]::ConvertFromUtf32(0x26A0)
$e_arrow = [char]::ConvertFromUtf32(0x276F)

function Write-Color([String]$Text, [ConsoleColor]$Color) {
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header([String]$Text) {
    Write-Host "`n  $e_sparkle " -NoNewline -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan -NoNewline
    Write-Host " $e_sparkle" -ForegroundColor Cyan
    Write-Host "  ------------------------------------------------" -ForegroundColor DarkGray
}

$logo = @"
    ______ __               __  ___          ___ 
   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____
  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \ 
 / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ / 
/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/  

"@

# Helper to swallow output and errors silently
function Run-Silent([scriptblock]$ScriptBlock) {
    $oldError = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try { & $ScriptBlock 2>&1 | Out-Null } catch {}
    $ErrorActionPreference = $oldError
}

# --- Real-Time Progress Spinner ---
function Run-WithSpinner {
    param (
        [string]$Message,
        [string]$FilePath,
        [string[]]$ArgumentList
    )
    
    Write-Host "$e_hour " -NoNewline
    Write-Host "$Message... " -ForegroundColor Yellow -NoNewline
    
    try { [Console]::CursorVisible = $false } catch {}
    
    $proc = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -PassThru -WindowStyle Hidden
    
    $spinChars = @('⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏')
    $i = 0
    while (-not $proc.HasExited) {
        Write-Host "`b$($spinChars[$i % 10])" -NoNewline -ForegroundColor Cyan
        $i++
        Start-Sleep -Milliseconds 100
    }
    
    try { [Console]::CursorVisible = $true } catch {}
    Write-Host "`r                                                                        `r" -NoNewline
    
    if ($proc.ExitCode -eq 0 -or $proc.ExitCode -eq $null) {
        Write-Host "$e_check " -NoNewline; Write-Host "$Message complete." -ForegroundColor Green
    } else {
        Write-Host "$e_cross " -NoNewline; Write-Host "$Message failed (Exit Code: $($proc.ExitCode))." -ForegroundColor Red
    }
}

# --- Interactive Arrow Key Menu ---
function Show-Menu {
    param (
        [string]$Prompt,
        [string[]]$Options,
        [ConsoleColor[]]$Colors
    )
    $selected = 0

    # Ensure we have default colors for each option
    if (-not $Colors) {
        $Colors = @('White') * $Options.Length
    }

    # Hide cursor
    try { [Console]::CursorVisible = $false } catch {}

    while ($true) {
        Clear-Host
        Write-Color $logo "Cyan"
        Write-Color "          Welcome to the FluxMedia Toolkit!      " "White"
        Write-Color "          Fast and Powerful.                     " "DarkGray"
        Write-Host ""
        Write-Header $Prompt
        
        for ($i = 0; $i -lt $Options.Length; $i++) {
            if ($i -eq $selected) {
                Write-Host "   $e_arrow $($Options[$i]) " -BackgroundColor Cyan -ForegroundColor Black
            } else {
                Write-Host "     $($Options[$i])" -ForegroundColor $Colors[$i]
            }
        }
        
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        if ($key.VirtualKeyCode -eq 38) { # Up arrow
            $selected--
            if ($selected -lt 0) { $selected = $Options.Length - 1 }
        } elseif ($key.VirtualKeyCode -eq 40) { # Down arrow
            $selected++
            if ($selected -ge $Options.Length) { $selected = 0 }
        } elseif ($key.VirtualKeyCode -eq 13) { # Enter
            break
        }
    }

    # Show cursor
    try { [Console]::CursorVisible = $true } catch {}
    return $selected
}

function Install-Python {
    # We leave Invoke-WebRequest as is so it natively displays its own progress bar at the top!
    Write-Host "$e_hour " -NoNewline; Write-Host "Downloading Python..." -ForegroundColor Yellow
    $installer = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe" -OutFile $installer -UseBasicParsing
    
    # Cleanup ghost state silently first
    Start-Process -FilePath $installer -ArgumentList "/uninstall", "/quiet" -Wait -NoNewWindow
    
    # Install with animated spinner
    Run-WithSpinner -Message "Installing Python" -FilePath $installer -ArgumentList @("/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "Include_doc=0")
}

function Install-FFmpeg {
    Run-WithSpinner -Message "Installing FFmpeg via Winget" -FilePath "winget" -ArgumentList @("install", "-e", "--id", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements")
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

function Install-FluxMedia {
    $pyCmd = Get-RealPython
    Run-WithSpinner -Message "Upgrading Pip" -FilePath $pyCmd -ArgumentList @("-m", "pip", "install", "--upgrade", "pip", "-q")
    Run-WithSpinner -Message "Installing FluxMedia Core" -FilePath $pyCmd -ArgumentList @("-m", "pip", "install", "-U", "fluxmedia", "-q")
}

function Uninstall-FluxMedia {
    $pyCmd = Get-RealPython
    Run-WithSpinner -Message "Removing FluxMedia and dependencies" -FilePath $pyCmd -ArgumentList @("-m", "pip", "uninstall", "-y", "fluxmedia", "rich", "requests", "yt-dlp", "textual", "markdown-it-py", "pygments", "-q")
}

function Uninstall-FFmpeg {
    Run-WithSpinner -Message "Removing FFmpeg" -FilePath "winget" -ArgumentList @("uninstall", "-e", "--id", "Gyan.FFmpeg", "--silent", "--accept-source-agreements")
}

function Uninstall-Python {
    Write-Host "⏳ " -NoNewline; Write-Host "Removing Python..." -ForegroundColor Yellow
    
    # 1. Uninstall via Registry (Catches all Python 3.x installations cleanly without freezing)
    $uninstallKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    
    $pythonUninstalls = Get-ItemProperty $uninstallKeys -ErrorAction SilentlyContinue | 
        Where-Object { $_.DisplayName -match 'Python 3\.\d+' }

    foreach ($app in $pythonUninstalls) {
        if ($app.UninstallString) {
            $uninstallString = $app.UninstallString
            if ($uninstallString -match 'MsiExec.exe') {
                $uninstallString = $uninstallString -replace '/I', '/X'
                $uninstallString += ' /qn /norestart'
                Run-Silent { cmd.exe /c $uninstallString }
            } else {
                # Python.org installer
                $exe = ($uninstallString -split '"')[1]
                if ($exe -and (Test-Path $exe)) {
                    Start-Process -FilePath $exe -ArgumentList "/uninstall", "/quiet" -Wait -NoNewWindow
                }
            }
        }
    }
    
    # 2. Attempt to remove Windows Store versions of Python
    Run-Silent { Get-AppxPackage *PythonSoftwareFoundation* | Remove-AppxPackage -Confirm:$false }
    
    # 3. Ultimate Brute Force Cleanup (Bypasses Admin/User scope conflict locks)
    $pythonLocalPath = "$env:LOCALAPPDATA\Programs\Python"
    if (Test-Path $pythonLocalPath) { Remove-Item -Path $pythonLocalPath -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path "$env:ProgramFiles\Python*") { Remove-Item -Path "$env:ProgramFiles\Python*" -Recurse -Force -ErrorAction SilentlyContinue }
    
    # 4. Clean PATH variable of any Python references
    $mPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $uPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($mPath) {
        $newMPath = ($mPath -split ';' | Where-Object { $_ -notmatch 'Python' }) -join ';'
        Run-Silent { [Environment]::SetEnvironmentVariable("Path", $newMPath, "Machine") }
    }
    if ($uPath) {
        $newUPath = ($uPath -split ';' | Where-Object { $_ -notmatch 'Python' }) -join ';'
        Run-Silent { [Environment]::SetEnvironmentVariable("Path", $newUPath, "User") }
    }

    Write-Host "✅ " -NoNewline; Write-Host "Python removed." -ForegroundColor Green
}

function Show-MainMenu {
    $opts = @("Install FluxMedia (Default setup)", "Reinstall components", "Uninstall components", "Exit")
    $colors = @("Cyan", "Yellow", "Red", "DarkGray")
    
    while ($true) {
        $choice = Show-Menu -Prompt "Please select an action:" -Options $opts -Colors $colors
        switch ($choice) {
            0 { Do-Install; return }
            1 { Show-ReinstallMenu }
            2 { Show-UninstallMenu }
            3 { Write-Color "`nGoodbye!" "Cyan"; exit }
        }
    }
}

function Show-UninstallMenu {
    $opts = @(
        "Uninstall FluxMedia Core Only",
        "Uninstall FluxMedia + FFmpeg",
        "Uninstall Everything (FluxMedia, FFmpeg, and Python)",
        "Back to Main Menu"
    )
    $colors = @("Red", "Red", "Red", "DarkGray")
    
    while ($true) {
        $choice = Show-Menu -Prompt "Uninstall Menu" -Options $opts -Colors $colors
        switch ($choice) {
            0 { Uninstall-FluxMedia; PauseAndReturn; return }
            1 { Uninstall-FluxMedia; Uninstall-FFmpeg; PauseAndReturn; return }
            2 {
                Write-Host ""
                Write-Color "$e_warn  CRITICAL WARNING $e_warn" "Red"
                Write-Color "Removing Python completely from your system may break other tools or scripts that depend on it." "Yellow"
                
                $confirmOpts = @("Yes, remove Python", "Cancel")
                $confirmColors = @("Red", "Green")
                $confirm = Show-Menu -Prompt "Are you absolutely sure you want to remove Python?" -Options $confirmOpts -Colors $confirmColors
                
                if ($confirm -eq 0) {
                    Uninstall-FluxMedia; Uninstall-FFmpeg; Uninstall-Python
                    PauseAndReturn
                    return
                } else {
                    Write-Color "Python removal aborted." "Green"
                    Start-Sleep -Seconds 2
                }
            }
            3 { return }
        }
    }
}

function Show-ReinstallMenu {
    $opts = @(
        "Reinstall FluxMedia Core Only",
        "Reinstall FFmpeg Only",
        "Reinstall Python Only",
        "Reinstall Everything",
        "Back to Main Menu"
    )
    $colors = @("Yellow", "Yellow", "Yellow", "Yellow", "DarkGray")
    
    while ($true) {
        $choice = Show-Menu -Prompt "Reinstall Menu" -Options $opts -Colors $colors
        switch ($choice) {
            0 { Uninstall-FluxMedia; Install-FluxMedia; PauseAndReturn; return }
            1 { Uninstall-FFmpeg; Install-FFmpeg; PauseAndReturn; return }
            2 { Uninstall-Python; Install-Python; PauseAndReturn; return }
            3 {
                Uninstall-FluxMedia; Uninstall-FFmpeg; Uninstall-Python
                Install-Python; Install-FFmpeg; Install-FluxMedia
                PauseAndReturn
                return
            }
            4 { return }
        }
    }
}

function PauseAndReturn {
    Write-Host ""
    Write-Color "Operation completed successfully!" "Green"
    try { [Console]::CursorVisible = $true } catch {}
    Read-Host "Press Enter to return to main menu..."
}

function Get-RealPython {
    # Dynamically find the real python.exe on disk to bypass PATH caching and MS Store Aliases
    $realPath = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles\Python*" -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if ($realPath) { return $realPath }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    return "python"
}

function Do-Install {
    Clear-Host
    Write-Color $logo "Cyan"
    Write-Color "          Welcome to the FluxMedia Toolkit!      " "White"
    Write-Color "          Fast and Powerful.                     " "DarkGray"
    
    Write-Header "Step 1: Checking Python Environment"
    $pythonExists = $false
    try {
        $pyCmd = Get-RealPython
        $pyVersion = & $pyCmd --version 2>&1
        if ($pyVersion -match "Python 3") { $pythonExists = $true }
    } catch {}

    if ($pythonExists) {
        Write-Host "$e_check " -NoNewline; Write-Host "Python is already installed and ready." -ForegroundColor Green
    } else {
        Install-Python
    }

    Write-Header "Step 2: Checking Media Engine (FFmpeg)"
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Host "$e_check " -NoNewline; Write-Host "FFmpeg is already installed and ready." -ForegroundColor Green
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
    
    $launchOpts = @("Yes, launch it now", "No, exit")
    $launchChoice = Show-Menu -Prompt "🎬 Would you like to launch FluxMedia right now?" -Options $launchOpts
    
    if ($launchChoice -eq 0) {
        Clear-Host
        $pyCmd = Get-RealPython
        if (Get-Command fluxmedia -ErrorAction SilentlyContinue) {
            fluxmedia
        } else {
            & $pyCmd -m fluxmedia
        }
    }
}

# Start the application
Show-MainMenu
