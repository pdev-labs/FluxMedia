#!/usr/bin/env bash
set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================${NC}"
echo -e "${WHITE}         🌊 FluxMedia Installer (Unix)           ${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""
echo "This script will interactively install:"
echo "  - Python (if not installed)"
echo "  - FFmpeg (if not installed)"
echo "  - FluxMedia (via pip)"
echo ""

read -p "Do you want to proceed? (Y/n) " response
if [[ "$response" =~ ^[nN]$ ]]; then
    echo -e "${YELLOW}Installation aborted by user.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/3] Checking system dependencies (Python & FFmpeg)...${NC}"

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo "  -> Ensuring Python and FFmpeg via brew..."
    brew install python ffmpeg
elif [ "$OS" = "Linux" ]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        echo "  -> Ensuring Python and FFmpeg via apt..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip ffmpeg
    elif command -v pacman &> /dev/null; then
        echo "  -> Ensuring Python and FFmpeg via pacman..."
        sudo pacman -Sy --noconfirm python python-pip ffmpeg
    elif command -v dnf &> /dev/null; then
        echo "  -> Ensuring Python and FFmpeg via dnf..."
        sudo dnf install -y python3 python3-pip ffmpeg
    else
        echo -e "${YELLOW}Could not determine package manager. Please install python3, python3-pip, and ffmpeg manually.${NC}"
    fi
else
    echo -e "${YELLOW}Unknown OS. Please install python and ffmpeg manually.${NC}"
fi

echo -e "${YELLOW}[2/3] Installing/Updating FluxMedia...${NC}"
# Use pipx if available, otherwise pip3 with break-system-packages (needed for newer Debian/Ubuntu)
if command -v pipx &> /dev/null; then
    pipx install fluxmedia
else
    # Try standard pip3
    if pip3 install -U fluxmedia --break-system-packages 2>/dev/null; then
        echo "  -> Installed with --break-system-packages"
    else
        pip3 install -U fluxmedia
    fi
fi

echo -e "${GREEN}[3/3] Installation Complete!${NC}"
echo ""
echo "You can now run FluxMedia from your terminal by typing:"
echo -e "${CYAN}  fluxmedia${NC}"
echo ""

read -p "Do you want to launch FluxMedia now? (Y/n) " launch
if [[ ! "$launch" =~ ^[nN]$ ]]; then
    if command -v fluxmedia &> /dev/null; then
        fluxmedia
    else
        python3 -m fluxmedia
    fi
fi
