#!/usr/bin/env bash
set -e

# Colors
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
RED='\033[1;31m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

clear

# ASCII Logo
echo -e "${CYAN}    ______ __               __  ___          ___ ${NC}"
echo -e "${CYAN}   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____${NC}"
echo -e "${CYAN}  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \\${NC}"
echo -e "${CYAN} / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ /${NC}"
echo -e "${CYAN}/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/ ${NC}"
echo ""
echo -e "${WHITE}          Welcome to the FluxMedia Installer!    ${NC}"
echo -e "${GRAY}          Fast, Aesthetic, and Powerful.         ${NC}"
echo ""

echo -e "${WHITE}📦 What we will install today:${NC}"
echo -e "${GRAY}   🔹 ${CYAN}Python 3${GRAY} (if missing)${NC}"
echo -e "${GRAY}   🔹 ${CYAN}FFmpeg Engine${GRAY} (if missing)${NC}"
echo -e "${GRAY}   🔹 ${CYAN}FluxMedia Core${NC}"
echo ""

read -p "🚀 Ready to begin? (Y/n) " response
if [[ "$response" =~ ^[nN]$ ]]; then
    echo -e "\n${RED}❌ Installation gracefully aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}✨ Step 1: Checking System Dependencies ✨${NC}"
echo -e "${GRAY}----------------------------------------${NC}"

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}⏳ Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo -e "${YELLOW}⏳ Ensuring Python and FFmpeg via brew...${NC}"
    brew install python ffmpeg > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ Dependencies verified.${NC}"
elif [ "$OS" = "Linux" ]; then
    if command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}⏳ Ensuring Python and FFmpeg via apt...${NC}"
        sudo apt-get update -qq
        sudo apt-get install -yqq python3 python3-pip ffmpeg > /dev/null 2>&1 || true
        echo -e "${GREEN}✅ Dependencies verified.${NC}"
    elif command -v pacman &> /dev/null; then
        echo -e "${YELLOW}⏳ Ensuring Python and FFmpeg via pacman...${NC}"
        sudo pacman -Sy --noconfirm python python-pip ffmpeg > /dev/null 2>&1 || true
        echo -e "${GREEN}✅ Dependencies verified.${NC}"
    elif command -v dnf &> /dev/null; then
        echo -e "${YELLOW}⏳ Ensuring Python and FFmpeg via dnf...${NC}"
        sudo dnf install -yq python3 python3-pip ffmpeg > /dev/null 2>&1 || true
        echo -e "${GREEN}✅ Dependencies verified.${NC}"
    else
        echo -e "${YELLOW}⚠️ Could not determine package manager. Assuming manual installation.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Unknown OS. Assuming manual installation.${NC}"
fi

echo ""
echo -e "${CYAN}✨ Step 2: Installing FluxMedia Core ✨${NC}"
echo -e "${GRAY}----------------------------------------${NC}"
echo -e "${YELLOW}⏳ Fetching latest version via pip...${NC}"

if command -v pipx &> /dev/null; then
    pipx install fluxmedia > /dev/null 2>&1 || true
else
    if pip3 install -U fluxmedia --break-system-packages > /dev/null 2>&1; then
        :
    else
        pip3 install -U fluxmedia > /dev/null 2>&1 || true
    fi
fi
echo -e "${GREEN}✅ FluxMedia successfully installed.${NC}"

echo ""
echo -e "${GREEN}🎉 SUCCESS! All components are fully installed.${NC}"
echo -e "${GRAY}------------------------------------------------${NC}"
echo -e "You can now run FluxMedia from anywhere by typing:"
echo -e "${CYAN}fluxmedia${NC}"
echo -e "${GRAY}------------------------------------------------${NC}"
echo ""

read -p "🎬 Would you like to launch FluxMedia right now? (Y/n) " launch
if [[ ! "$launch" =~ ^[nN]$ ]]; then
    clear
    if command -v fluxmedia &> /dev/null; then
        fluxmedia
    else
        python3 -m fluxmedia
    fi
fi
