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

Clear-Host
$logo = @"
    ______ __               __  ___          ___ 
   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____
  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \ 
 / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ / 
/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/  

"@

Write-Color $logo "Cyan"
Write-Color "          Welcome to the FluxMedia Installer!    " "White"
Write-Color "          Fast, Aesthetic, and Powerful.         " "DarkGray"
Write-Host ""

Write-Host "📦 " -NoNewline; Write-Host "What we will install today:" -ForegroundColor White
Write-Host "   🔹 " -NoNewline; Write-Host "Python 3.11" -ForegroundColor DarkCyan -NoNewline; Write-Host " (if missing)" -ForegroundColor DarkGray
Write-Host "   🔹 " -NoNewline; Write-Host "FFmpeg Engine" -ForegroundColor DarkCyan -NoNewline; Write-Host " (if missing)" -ForegroundColor DarkGray
Write-Host "   🔹 " -NoNewline; Write-Host "FluxMedia Core" -ForegroundColor DarkCyan
Write-Host ""

$response = Read-Host "🚀 Ready to begin? (Y/n)"
if ($response -eq 'n' -or $response -eq 'N') {
    Write-Color "`n❌ Installation gracefully aborted." "Red"
    exit
}

Write-Header "Step 1: Checking Python Environment"
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✅ " -NoNewline; Write-Host "Python is already installed and ready." -ForegroundColor Green
} else {
    Write-Host "⏳ " -NoNewline; Write-Host "Python not found. Fetching via Winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "✅ " -NoNewline; Write-Host "Python successfully installed." -ForegroundColor Green
}

Write-Header "Step 2: Checking Media Engine (FFmpeg)"
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "✅ " -NoNewline; Write-Host "FFmpeg is already installed and ready." -ForegroundColor Green
} else {
    Write-Host "⏳ " -NoNewline; Write-Host "FFmpeg not found. Fetching via Winget..." -ForegroundColor Yellow
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "✅ " -NoNewline; Write-Host "FFmpeg successfully installed." -ForegroundColor Green
}

Write-Header "Step 3: Installing FluxMedia Core"
Write-Host "⏳ " -NoNewline; Write-Host "Upgrading pip and fetching fluxmedia..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null
python -m pip install -U fluxmedia
Write-Host "✅ " -NoNewline; Write-Host "FluxMedia successfully installed." -ForegroundColor Green

Write-Host "`n🎉 " -NoNewline; Write-Host "SUCCESS! All components are fully installed." -ForegroundColor Green
Write-Host "------------------------------------------------" -ForegroundColor DarkGray
Write-Host "You can now run FluxMedia from anywhere by typing: " -NoNewline
Write-Host "fluxmedia" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

$launch = Read-Host "🎬 Would you like to launch FluxMedia right now? (Y/n)"
if ($launch -ne 'n' -and $launch -ne 'N') {
    Clear-Host
    fluxmedia
}
