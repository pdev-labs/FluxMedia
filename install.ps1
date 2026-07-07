$ErrorActionPreference = 'Stop'

function Write-Color([String]$Text, [ConsoleColor]$Color) {
    Write-Host $Text -ForegroundColor $Color
}

Write-Color "=================================================" "Cyan"
Write-Color "         🌊 FluxMedia Installer (Windows)       " "White"
Write-Color "=================================================" "Cyan"
Write-Host ""
Write-Host "This script will interactively install:"
Write-Host "  - Python (via winget, if missing)"
Write-Host "  - FFmpeg (via winget, if missing)"
Write-Host "  - FluxMedia (via pip)"
Write-Host ""

$response = Read-Host "Do you want to proceed? (Y/n)"
if ($response -eq 'n' -or $response -eq 'N') {
    Write-Color "Installation aborted by user." "Yellow"
    exit
}

Write-Host ""
Write-Color "[1/4] Checking Python..." "Yellow"
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Color "  -> Python is already installed." "Green"
} else {
    Write-Host "  -> Python not found. Installing via winget..."
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

Write-Color "[2/4] Checking FFmpeg..." "Yellow"
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Color "  -> FFmpeg is already installed." "Green"
} else {
    Write-Host "  -> FFmpeg not found. Installing via winget..."
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

Write-Color "[3/4] Installing/Updating FluxMedia..." "Yellow"
python -m pip install --upgrade pip
python -m pip install -U fluxmedia

Write-Color "[4/4] Installation Complete!" "Green"
Write-Host ""
Write-Host "You can now run FluxMedia from your terminal by typing:"
Write-Color "  fluxmedia" "Cyan"
Write-Host ""

$launch = Read-Host "Do you want to launch FluxMedia now? (Y/n)"
if ($launch -ne 'n' -and $launch -ne 'N') {
    fluxmedia
}
