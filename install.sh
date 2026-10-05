#!/usr/bin/env bash

set -e

# --- Request sudo upfront if available (not needed for read-only --check) ---
if [ "${1:-}" != "--check" ] && [ "${1:-}" != "--help" ] && [ "${1:-}" != "-h" ] && [ "$EUID" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    echo "This script may require administrative privileges to install dependencies."
    sudo -v || { echo "Failed to get sudo privileges. Exiting."; exit 1; }
fi

# --- UI Colors and Styles ---
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
DARKGRAY='\033[1;30m'
WHITE='\033[1;37m'
BG_CYAN='\033[46;1m'
FG_BLACK='\033[30;1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n  ${CYAN}✨ $1 ✨${NC}"
    echo -e "  ${DARKGRAY}------------------------------------------------${NC}"
}

print_logo() {
    echo -e "${CYAN}    ______ __               __  ___          ___ "
    echo -e "   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____"
    echo -e "  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \ "
    echo -e " / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ / "
    echo -e "/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/  ${NC}\n"
    echo -e "${WHITE}          Welcome to the FluxMedia Toolkit!      ${NC}"
    echo -e "${DARKGRAY}          Fast and Powerful.                     ${NC}\n"
}

pause_and_return() {
    echo ""
    echo -e "${GREEN}Operation completed successfully!${NC}"
    read -p "Press Enter to return to main menu..." < /dev/tty
}

# --- Real-Time Progress Spinner ---
run_with_spinner() {
    local msg="$1"
    shift
    
    tput civis 2>/dev/null || true
    
    "$@" >/dev/null 2>&1 &
    local pid=$!
    
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    
    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr#?}
        printf "\r⏳ ${YELLOW}%s...${NC} ${CYAN}%c${NC} " "$msg" "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    
    set +e
    wait $pid
    local exit_code=$?
    set -e
    
    tput cnorm 2>/dev/null || true
    
    if [ $exit_code -eq 0 ]; then
        printf "\r✅ ${GREEN}%s complete.                           ${NC}\n" "$msg"
    else
        printf "\r❌ ${RED}%s failed.                               ${NC}\n" "$msg"
    fi
    return $exit_code
}

# --- Interactive Arrow Key Menu ---
show_menu() {
    local prompt="$1"
    shift
    local options=("$@")
    local selected=0
    local key

    # Hide cursor
    tput civis 2>/dev/null || true
    
    while true; do
        clear
        print_logo
        print_header "$prompt"
        
        for i in "${!options[@]}"; do
            if [ "$i" -eq "$selected" ]; then
                # Highlighted row
                echo -e "  ${BG_CYAN}${FG_BLACK} ❯ ${options[$i]} ${NC}"
            else
                # Normal row
                echo -e "     ${options[$i]}"
            fi
        done
        
        # Read 1 char. If it's escape, read two more for arrow sequences.
        read -rsn1 key < /dev/tty || true
        if [[ $key == $'\e' ]]; then
            read -rsn2 key < /dev/tty || true
            if [[ $key == "[A" ]]; then # Up arrow
                selected=$((selected - 1))
                if [ $selected -lt 0 ]; then selected=$((${#options[@]} - 1)); fi
            elif [[ $key == "[B" ]]; then # Down arrow
                selected=$((selected + 1))
                if [ $selected -ge ${#options[@]} ]; then selected=0; fi
            fi
        elif [[ $key == "" ]]; then # Enter key
            break
        fi
    done
    
    # Show cursor
    tput cnorm 2>/dev/null || true
    MENU_CHOICE=$selected
    return 0
}

# --- OS Detection ---
OS="$(uname -s)"
DISTRO=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
fi

is_termux() {
    if [[ "$PREFIX" == *com.termux* ]]; then
        return 0
    else
        return 1
    fi
}

# --- Installation Logic ---
install_dependencies() {
    if [ "${FORCE_MODE:-0}" != "1" ] && command -v ffmpeg &> /dev/null && command -v node &> /dev/null; then
        echo -e "${GREEN}FFmpeg and Node.js already present — skipping system deps.${NC}"
        return 0
    fi
    local cmd=""
    if is_termux; then
        # nodejs: yt-dlp JS runtime (quickjs has no Android wheels).
        # clang/rust/binutils/libffi/openssl: fallback C/Rust toolchain so
        # any package without an Android wheel can still build from source.
        cmd="pkg install python python-pip ffmpeg termux-api nodejs clang rust binutils libffi openssl -y"
    elif [ "$OS" = "Darwin" ]; then
        if ! command -v brew &> /dev/null; then
            echo -e "\n${RED}Homebrew is required on macOS. Please install it first.${NC}"
            exit 1
        fi
        cmd="brew install python ffmpeg"
    elif [ "$OS" = "Linux" ]; then
        if command -v apt &> /dev/null; then
            sudo apt update >/dev/null 2>&1
            cmd="sudo apt install python3-pip python3-venv pipx ffmpeg -y"
        elif command -v pacman &> /dev/null; then
            cmd="sudo pacman -Sy python-pip python-pipx ffmpeg --noconfirm"
        elif command -v dnf &> /dev/null; then
            cmd="sudo dnf install python3-pip pipx ffmpeg -y"
        elif command -v zypper &> /dev/null; then
            cmd="sudo zypper install -y python3-pip pipx ffmpeg"
        elif command -v apk &> /dev/null; then
            cmd="sudo apk add python3 py3-pip pipx ffmpeg"
        elif command -v xbps-install &> /dev/null; then
            cmd="sudo xbps-install -Sy python3-pip pipx ffmpeg"
        else
            echo -e "\n${YELLOW}Unsupported package manager. Please install Python and FFmpeg manually.${NC}"
        fi
    fi
    
    if [ -n "$cmd" ]; then
        run_with_spinner "Checking/Installing Dependencies (Python & FFmpeg)" bash -c "$cmd"
    fi
}

install_fluxmedia() {
    if [ "${FORCE_MODE:-0}" != "1" ] && python3 -c "import importlib.metadata as m; m.version('fluxmedia')" 2>/dev/null; then
        echo -e "${GREEN}FluxMedia already installed — skipping (use --force to reinstall).${NC}"
        return 0
    fi
    local cmd=""
    if is_termux; then
        # Termux: PyPI has no Android wheels for pydantic-core, and the
        # community index only covers certain versions per Python. Pin
        # pydantic to a release whose exact core has Android wheels, install
        # it FIRST so the fluxmedia install below cannot float past it.
        # Verified pairs (pydantic -> core with Android wheels):
        #   py3.11/3.12 -> pydantic==2.11.7 (core 2.33.2)
        #   py3.13/3.14 -> pydantic==2.12.4 (core 2.41.5)
        local py_minor
        py_minor=$(python3 -c 'import sys; print(sys.version_info[1])' 2>/dev/null || echo 0)
        local pyd_pin=""
        if [ "$py_minor" -eq 11 ] || [ "$py_minor" -eq 12 ]; then
            pyd_pin="pydantic==2.11.7"
        elif [ "$py_minor" -eq 13 ] || [ "$py_minor" -eq 14 ]; then
            pyd_pin="pydantic==2.12.4"
        fi
        local extra="--extra-index-url https://termux-user-repository.github.io/pypi/ --extra-index-url https://eutalix.github.io/android-pydantic-core/"
        local pindl=""
        if [ -n "$pyd_pin" ]; then
            # shellcheck disable=SC2086
            pindl="pip install $pyd_pin $extra -q &&"
        fi
        # shellcheck disable=SC2086
        cmd="pip install --upgrade pip -q && $pindl pip install -U fluxmedia -q"
    elif [ "$OS" = "Darwin" ]; then
        cmd="pip install --upgrade pip -q && pip install -U fluxmedia -q"
    else
        if command -v pipx &> /dev/null; then
            cmd="pipx install fluxmedia --force && pipx ensurepath"
        else
            cmd="pip3 install --upgrade pip -q && pip3 install -U fluxmedia -q || pip3 install -U fluxmedia --break-system-packages -q"
        fi
    fi
    run_with_spinner "Fetching fluxmedia" bash -c "$cmd"
}

uninstall_fluxmedia() {
    local cmd="pip uninstall -y fluxmedia rich requests yt-dlp textual markdown-it-py pygments -q || true; pip3 uninstall -y fluxmedia rich requests yt-dlp textual markdown-it-py pygments -q || true"
    if command -v pipx &> /dev/null; then
        cmd="pipx uninstall fluxmedia || true; $cmd"
    fi
    run_with_spinner "Removing fluxmedia" bash -c "$cmd"
}

uninstall_ffmpeg() {
    local cmd=""
    if is_termux; then
        cmd="pkg uninstall ffmpeg -y || true"
    elif [ "$OS" = "Darwin" ]; then
        cmd="brew uninstall ffmpeg || true"
    elif [ "$OS" = "Linux" ]; then
        if command -v apt &> /dev/null; then
            cmd="sudo apt remove ffmpeg -y || true"
        elif command -v pacman &> /dev/null; then
            cmd="sudo pacman -R ffmpeg --noconfirm || true"
        elif command -v dnf &> /dev/null; then
            cmd="sudo dnf remove ffmpeg -y || true"
        elif command -v zypper &> /dev/null; then
            cmd="sudo zypper remove -y ffmpeg || true"
        elif command -v apk &> /dev/null; then
            cmd="sudo apk del ffmpeg || true"
        elif command -v xbps-remove &> /dev/null; then
            cmd="sudo xbps-remove -y ffmpeg || true"
        fi
    fi
    
    if [ -n "$cmd" ]; then
        run_with_spinner "Removing FFmpeg" bash -c "$cmd"
    fi
}

uninstall_python() {
    local cmd=""
    if is_termux; then
        cmd="pkg uninstall python python-pip -y || true"
    elif [ "$OS" = "Darwin" ]; then
        cmd="brew uninstall python || true"
    fi
    
    if [ -n "$cmd" ]; then
        run_with_spinner "Removing Python" bash -c "$cmd"
    elif [ "$OS" = "Linux" ]; then
        echo -e "\n⚠️  ${RED}Skipped: Uninstalling Python on Linux can break the OS.${NC}"
    fi
}

# --- Preflight (read-only; same report shape as install.py --check) ---
cmd_version() { "$1" --version 2>&1 | head -n1 | cut -c1-70; }

preflight() {
    local py="MISSING" net="OFFLINE" disk="unknown" ff="MISSING" nd="MISSING" fm="MISSING"
    if command -v python3 &> /dev/null; then py=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")' 2>/dev/null || echo "present"); fi
    if (echo > /dev/tcp/8.8.8.8/53) 2>/dev/null; then net="reachable"; fi
    if command -v ffmpeg &> /dev/null; then ff=$(cmd_version ffmpeg); fi
    if command -v node &> /dev/null; then nd=$(cmd_version node); fi
    if python3 -c "import importlib.metadata as m; print(m.version('fluxmedia'))" 2>/dev/null; then fm=$(python3 -c "import importlib.metadata as m; print('v'+m.version('fluxmedia'))" 2>/dev/null); fi
    if command -v df &> /dev/null; then disk="$(df -h "$HOME" 2>/dev/null | awk 'NR==2{print $4" free"}')"; fi
    echo -e "\n  ✨ ${CYAN}Preflight check ✨${NC}"
    echo -e "  [Python]     $py"
    echo -e "  [Network]    $net"
    echo -e "  [Disk]       $disk"
    echo -e "  [FFmpeg]     $ff"
    echo -e "  [Node.js]    $nd"
    echo -e "  [FluxMedia]  $fm"
    [[ "$net" == "OFFLINE" ]] && return 1
    [[ "$py" == MISSING* ]] && return 1
    return 0
}

do_install() {
    FORCE_MODE="${FORCE_MODE:-0}"
    clear
    print_logo
    if ! preflight; then
        echo -e "\n${RED}Preflight failed (Python or network missing). Aborting.${NC}"
        return 1
    fi
    print_header "Step 1 & 2: Environment Setup"
    install_dependencies
    
    print_header "Step 3: Installing FluxMedia Core"
    install_fluxmedia
    
    echo -e "\n🎉 ${GREEN}SUCCESS! All components are fully installed.${NC}"
    echo -e "${DARKGRAY}------------------------------------------------${NC}"
    echo -ne "You can now run FluxMedia from anywhere by typing: "
    echo -e "${CYAN}fluxmedia${NC}"
    echo -e "${DARKGRAY}------------------------------------------------${NC}\n"
    
    # Interactive launch prompt only for menu-driven installs.
    if [ -n "$NONINTERACTIVE" ]; then
        return 0
    fi
    # Quick Yes/No menu for launching
    local launch_opts=("Yes, launch it now" "No, exit")
    show_menu "Would you like to launch FluxMedia right now?" "${launch_opts[@]}"
    local choice=$MENU_CHOICE
    
    if [ "$choice" -eq 0 ]; then
        clear
        if command -v fluxmedia &> /dev/null; then
            fluxmedia
        else
            python3 -m fluxmedia || python -m fluxmedia
        fi
    fi
    exit 0
}

show_uninstall_menu() {
    local opts=(
        "Uninstall FluxMedia Core Only"
        "Uninstall FluxMedia + FFmpeg"
        "Uninstall Everything (FluxMedia, FFmpeg, Python)"
        "Back to Main Menu"
    )
    while true; do
        show_menu "Uninstall Menu" "${opts[@]}"
        local choice=$MENU_CHOICE
        case $choice in
            0) uninstall_fluxmedia; pause_and_return; return ;;
            1) uninstall_fluxmedia; uninstall_ffmpeg; pause_and_return; return ;;
            2) 
                clear
                print_logo
                echo -e "\n⚠️  ${RED}CRITICAL WARNING${NC} ⚠️"
                echo -e "${YELLOW}Removing Python completely may break other scripts or tools.${NC}"
                read -p "Are you absolutely sure you want to remove Python? (y/N) " confirm < /dev/tty
                if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
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
            3) return ;;
        esac
    done
}

show_reinstall_menu() {
    local opts=(
        "Reinstall FluxMedia Core Only"
        "Reinstall Everything (Deps + Core)"
        "Back to Main Menu"
    )
    while true; do
        show_menu "Reinstall Menu" "${opts[@]}"
        local choice=$MENU_CHOICE
        case $choice in
            0) uninstall_fluxmedia; install_fluxmedia; pause_and_return; return ;;
            1) uninstall_fluxmedia; do_install; pause_and_return; return ;;
            2) return ;;
        esac
    done
}

show_main_menu() {
    local opts=(
        "Install FluxMedia (Default setup)"
        "Reinstall components"
        "Uninstall components"
        "Exit"
    )
    while true; do
        show_menu "Please select an action:" "${opts[@]}"
        local choice=$MENU_CHOICE
        case $choice in
            0) do_install; return ;;
            1) show_reinstall_menu ;;
            2) show_uninstall_menu ;;
            3) tput cnorm 2>/dev/null || true; echo -e "\n${CYAN}Goodbye!${NC}"; exit 0 ;;
        esac
    done
}

# Entry point: same flags as install.py (--yes/--force/--check/--uninstall).
FORCE_MODE=0
case "${1:-}" in
    --check)
        print_logo
        if preflight; then exit 0; else exit 1; fi
        ;;
    --yes)
        NONINTERACTIVE=1
        do_install
        ;;
    --force)
        NONINTERACTIVE=1
        FORCE_MODE=1
        do_install
        ;;
    --uninstall)
        if [ "${2:-}" != "--yes" ]; then
            read -p "Uninstall FluxMedia + FFmpeg? [y/N] " confirm < /dev/tty
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then echo "Aborted."; exit 1; fi
        fi
        uninstall_fluxmedia
        uninstall_ffmpeg
        preflight
        ;;
    -h|--help)
        echo "Usage: install.sh [--yes|--force|--check|--uninstall [--yes]]"
        echo "  (no flags)  interactive menu"
        ;;
    *)
        show_main_menu
        ;;
esac
