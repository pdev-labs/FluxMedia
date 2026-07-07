#!/usr/bin/env bash
set -e

# Colors
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
RED='\033[1;31m'
GRAY='\033[0;90m'
NC='\033[0m'

# Helper Functions
print_header() {
    echo ""
    echo -e "${CYAN}✨ $1 ✨${NC}"
    echo -e "${GRAY}----------------------------------------${NC}"
}

pause_and_return() {
    echo ""
    echo -e "${GREEN}Operation completed successfully!${NC}"
    read -p "Press Enter to return to main menu..."
}

install_python() {
    echo -e "${YELLOW}⏳ Fetching Python via package manager...${NC}"
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        brew install python > /dev/null 2>&1 || true
    elif [ "$OS" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -yqq python3 python3-pip > /dev/null 2>&1 || true
        elif command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm python python-pip > /dev/null 2>&1 || true
        elif command -v dnf &> /dev/null; then
            sudo dnf install -yq python3 python3-pip > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ Python installed.${NC}"
}

install_ffmpeg() {
    echo -e "${YELLOW}⏳ Fetching FFmpeg via package manager...${NC}"
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        brew install ffmpeg > /dev/null 2>&1 || true
    elif [ "$OS" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -yqq ffmpeg > /dev/null 2>&1 || true
        elif command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm ffmpeg > /dev/null 2>&1 || true
        elif command -v dnf &> /dev/null; then
            sudo dnf install -yq ffmpeg > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ FFmpeg installed.${NC}"
}

install_fluxmedia() {
    echo -e "${YELLOW}⏳ Fetching FluxMedia Core...${NC}"
    if command -v pipx &> /dev/null; then
        pipx install fluxmedia > /dev/null 2>&1 || true
    else
        if pip3 install -U fluxmedia --break-system-packages > /dev/null 2>&1; then
            :
        else
            pip3 install -U fluxmedia > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ FluxMedia Core installed.${NC}"
}

uninstall_fluxmedia() {
    echo -e "${YELLOW}⏳ Removing FluxMedia Core...${NC}"
    if command -v pipx &> /dev/null; then
        pipx uninstall fluxmedia > /dev/null 2>&1 || true
    else
        if pip3 uninstall -y fluxmedia --break-system-packages > /dev/null 2>&1; then
            :
        else
            pip3 uninstall -y fluxmedia > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ FluxMedia Core removed.${NC}"
}

uninstall_ffmpeg() {
    echo -e "${YELLOW}⏳ Removing FFmpeg...${NC}"
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        brew uninstall ffmpeg > /dev/null 2>&1 || true
    elif [ "$OS" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get remove -yqq ffmpeg > /dev/null 2>&1 || true
        elif command -v pacman &> /dev/null; then
            sudo pacman -Rns --noconfirm ffmpeg > /dev/null 2>&1 || true
        elif command -v dnf &> /dev/null; then
            sudo dnf remove -yq ffmpeg > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ FFmpeg removed.${NC}"
}

uninstall_python() {
    echo -e "${YELLOW}⏳ Removing Python...${NC}"
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        brew uninstall python > /dev/null 2>&1 || true
    elif [ "$OS" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get remove -yqq python3 python3-pip > /dev/null 2>&1 || true
        elif command -v pacman &> /dev/null; then
            sudo pacman -Rns --noconfirm python python-pip > /dev/null 2>&1 || true
        elif command -v dnf &> /dev/null; then
            sudo dnf remove -yq python3 python3-pip > /dev/null 2>&1 || true
        fi
    fi
    echo -e "${GREEN}✅ Python removed.${NC}"
}

do_install() {
    print_header "Step 1: Checking Python Environment"
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✅ Python is already installed and ready.${NC}"
    else
        install_python
    fi

    print_header "Step 2: Checking Media Engine (FFmpeg)"
    if command -v ffmpeg &> /dev/null; then
        echo -e "${GREEN}✅ FFmpeg is already installed and ready.${NC}"
    else
        install_ffmpeg
    fi

    print_header "Step 3: Installing FluxMedia Core"
    install_fluxmedia

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
}

show_uninstall_menu() {
    while true; do
        clear
        print_header "Uninstall Menu"
        echo -e "${RED}  [1] Uninstall FluxMedia Core Only${NC}"
        echo -e "${RED}  [2] Uninstall FluxMedia + FFmpeg${NC}"
        echo -e "${RED}  [3] Uninstall Everything (FluxMedia, FFmpeg, and Python)${NC}"
        echo -e "${GRAY}  [0] Back to Main Menu${NC}"
        echo ""
        
        read -p "Choice: " choice
        case $choice in
            1)
                uninstall_fluxmedia
                pause_and_return
                return
                ;;
            2)
                uninstall_fluxmedia
                uninstall_ffmpeg
                pause_and_return
                return
                ;;
            3)
                echo ""
                echo -e "${RED}⚠️  CRITICAL WARNING ⚠️${NC}"
                echo -e "${YELLOW}Removing Python completely from Unix environments (macOS/Linux) can severely break system tools, package managers, and essential OS scripts that rely on it.${NC}"
                read -p "Are you absolutely sure you want to forcibly remove Python? (y/N) " confirm
                if [[ "$confirm" =~ ^[yY]$ ]]; then
                    uninstall_fluxmedia
                    uninstall_ffmpeg
                    uninstall_python
                    pause_and_return
                    return
                else
                    echo -e "${GREEN}Python removal aborted.${NC}"
                    sleep 2
                fi
                ;;
            0) return ;;
        esac
    done
}

show_reinstall_menu() {
    while true; do
        clear
        print_header "Reinstall Menu"
        echo -e "${YELLOW}  [1] Reinstall FluxMedia Core Only${NC}"
        echo -e "${YELLOW}  [2] Reinstall FFmpeg Only${NC}"
        echo -e "${YELLOW}  [3] Reinstall Python Only${NC}"
        echo -e "${YELLOW}  [4] Reinstall Everything${NC}"
        echo -e "${GRAY}  [0] Back to Main Menu${NC}"
        echo ""
        
        read -p "Choice: " choice
        case $choice in
            1)
                uninstall_fluxmedia; install_fluxmedia
                pause_and_return
                return
                ;;
            2)
                uninstall_ffmpeg; install_ffmpeg
                pause_and_return
                return
                ;;
            3)
                uninstall_python; install_python
                pause_and_return
                return
                ;;
            4)
                uninstall_fluxmedia; uninstall_ffmpeg; uninstall_python
                install_python; install_ffmpeg; install_fluxmedia
                pause_and_return
                return
                ;;
            0) return ;;
        esac
    done
}

show_main_menu() {
    while true; do
        clear
        echo -e "${CYAN}    ______ __               __  ___          ___ ${NC}"
        echo -e "${CYAN}   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____${NC}"
        echo -e "${CYAN}  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \\${NC}"
        echo -e "${CYAN} / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ /${NC}"
        echo -e "${CYAN}/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/ ${NC}"
        echo ""
        echo -e "${WHITE}          Welcome to the FluxMedia Toolkit!      ${NC}"
        echo -e "${GRAY}          Fast, Aesthetic, and Powerful.         ${NC}"
        echo ""
        echo -e "${WHITE}Please select an action:${NC}"
        echo -e "${CYAN}  [1] Install FluxMedia (Default setup)${NC}"
        echo -e "${YELLOW}  [2] Reinstall components${NC}"
        echo -e "${RED}  [3] Uninstall components${NC}"
        echo -e "${GRAY}  [0] Exit${NC}"
        echo ""
        
        read -p "Choice: " choice
        case $choice in
            1) do_install; return ;;
            2) show_reinstall_menu ;;
            3) show_uninstall_menu ;;
            0)
                echo -e "\n${CYAN}Goodbye!${NC}"
                exit 0
                ;;
        esac
    done
}

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}⏳ Homebrew not found. Installing Homebrew for package management...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
fi

show_main_menu
