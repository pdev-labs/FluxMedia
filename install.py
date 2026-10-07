#!/usr/bin/env python3
"""FluxMedia professional installer (cross-platform).

Interactive menu by default; scriptable with flags (same flags exist in
install.sh / install.ps1):

    python3 install.py                # interactive menu
    python3 install.py --yes          # default setup, no prompts
    python3 install.py --force        # reinstall everything, no prompts
    python3 install.py --check        # preflight report only (exit 0/1)
    python3 install.py --uninstall [--yes]
"""
import argparse
import os
import sys
import subprocess
import platform
import shutil

# --- UI Helpers ---
CYAN = '\033[0;36m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
GREEN = '\033[0;32m'
NC = '\033[0m'

def print_color(text, color, end='\n'):
    if sys.platform == 'win32':
        # Enable ANSI colors on Windows 10+
        os.system('')
    print(f"{color}{text}{NC}", end=end)

def print_logo():
    logo = """
    ______ __               __  ___          ___ 
   / ____// /_  __  __ _  //  |/  /___  ____/ (_)____
  / /_   / / / / / |/_/(_)/ /|_/ // _ \/ __  // / __ \ 
 / __/  / / /_/ />  < _  / /  / //  __/ /_/ // / /_/ / 
/_/    /_/\__,_/_/|_|(_)/_/  /_/ \___/\__,_//_/\__,_/  

          Welcome to the FluxMedia Toolkit!      
          Fast and Powerful.                     
"""
    print_color(logo, CYAN)

def run_command(cmd, shell=False, sudo=False):
    if sudo and sys.platform != 'win32' and 'com.termux' not in os.environ.get('PREFIX', ''):
        cmd = ['sudo'] + cmd

    print_color(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}", YELLOW)

    try:
        if shell:
            subprocess.run(cmd, shell=True, check=True)
        else:
            subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Command failed: {e}", RED)
        return False

MIN_PYTHON = (3, 8)


def check_network(timeout=3):
    import socket
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


def cmd_version(cmd, args=("--version",)):
    """First line of `<cmd> <args>` output, or None when missing/broken."""
    try:
        r = subprocess.run([cmd] + list(args), capture_output=True, text=True, timeout=15)
        lines = (r.stdout or r.stderr or "").strip().splitlines()
        return lines[0][:70] if r.returncode == 0 and lines else None
    except Exception:
        return None


def installed_fluxmedia_version():
    try:
        from importlib.metadata import version
        return version("fluxmedia")
    except Exception:
        return None


def preflight():
    """Returns [(component, ok, detail)] without changing anything."""
    rows = []
    v = sys.version_info
    ok = (v.major, v.minor) >= MIN_PYTHON
    rows.append(("Python", ok, f"{v.major}.{v.minor}.{v.micro}" + ("" if ok else " (requires >= 3.8)")))
    net = check_network()
    rows.append(("Network", net, "reachable" if net else "OFFLINE — downloads will fail"))
    try:
        free_gb = shutil.disk_usage(os.path.expanduser("~")).free / (1024 ** 3)
        rows.append(("Disk space", free_gb >= 1.0, f"{free_gb:.1f} GB free"))
    except Exception:
        rows.append(("Disk space", True, "unknown"))
    ff = cmd_version("ffmpeg", ("-version",))
    rows.append(("FFmpeg", ff is not None, ff or "not found"))
    nd = cmd_version("node", ("--version",))
    rows.append(("Node.js", nd is not None, nd or "not found (yt-dlp JS engine)"))
    fv = installed_fluxmedia_version()
    rows.append(("FluxMedia", fv is not None, f"v{fv}" if fv else "not installed"))
    return rows


def print_summary(rows, title="Preflight check"):
    print_color(f"\n=== {title} ===", CYAN)
    width = max(len(r[0]) for r in rows)
    for name, ok, detail in rows:
        mark = "OK  " if ok else "MISS"
        color = GREEN if ok else YELLOW
        print_color(f"  [{mark}] {name.ljust(width)}  {detail}", color)


def do_install(force=False):
    """Default setup: preflight, install what's missing, verify, summary."""
    print_logo()
    rows = preflight()
    print_summary(rows)
    by_name = {r[0]: r for r in rows}
    if not by_name["Python"][1]:
        print_color("Python >= 3.8 is required. Aborting.", RED)
        return False
    if not by_name["Network"][1]:
        print_color("No network connection. Aborting.", RED)
        return False
    install_system_dependencies(force=force)
    install_fluxmedia(force=force)
    final = preflight()
    ok = all(r[1] for r in final if r[0] in ("FFmpeg", "Node.js", "FluxMedia"))
    print_summary(final, title="Installation result")
    if ok:
        print_color("\nSuccess! FluxMedia is installed.", GREEN)
        print("Run 'fluxmedia' in your terminal to start.")
    else:
        print_color("\nSome components are still missing (see MISS rows above).", YELLOW)
    return ok


def do_uninstall(assume_yes=False):
    if not assume_yes:
        answer = input("Uninstall FluxMedia + FFmpeg? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return False
    uninstall_fluxmedia()
    uninstall_ffmpeg()
    print_summary(preflight(), title="After uninstall")
    return True

# --- OS Detection ---
def get_os_info():
    system = platform.system()
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    
    if is_termux:
        return 'Termux'
    return system

# --- Actions ---
def install_system_dependencies(force=False):
    os_name = get_os_info()
    if not force:
        ff, nd = cmd_version("ffmpeg", ("-version",)), cmd_version("node", ("--version",))
        if ff and nd:
            print_color("FFmpeg and Node.js already present — skipping system deps.", GREEN)
            return True
        elif ff or nd:
            print_color(f"Found {'FFmpeg' if ff else 'Node.js'}; installing the rest...", YELLOW)
    print_color("\nInstalling System Dependencies (FFmpeg & Node.js)...", CYAN)
    
    if os_name == 'Termux':
        # nodejs: yt-dlp JS runtime. clang/rust/libffi/openssl: fallback
        # toolchain so packages without Android wheels can build from source.
        run_command(['pkg', 'install', 'ffmpeg', 'nodejs', 'termux-api', 'clang',
                     'rust', 'binutils', 'libffi', 'openssl', 'python-pip', '-y'])
    elif os_name == 'Darwin':
        run_command(['brew', 'install', 'ffmpeg', 'node'])
    elif os_name == 'Windows':
        run_command(['winget', 'install', '-e', '--id', 'Gyan.FFmpeg', '--accept-package-agreements', '--accept-source-agreements'])
        run_command(['winget', 'install', '-e', '--id', 'OpenJS.NodeJS', '--accept-package-agreements', '--accept-source-agreements'])
    elif os_name == 'Linux':
        if shutil.which('apt'):
            run_command(['apt', 'update'], sudo=True)
            run_command(['apt', 'install', 'ffmpeg', 'nodejs', '-y'], sudo=True)
        elif shutil.which('pacman'):
            run_command(['pacman', '-Sy', 'ffmpeg', 'nodejs', '--noconfirm'], sudo=True)
        elif shutil.which('dnf'):
            run_command(['dnf', 'install', 'ffmpeg', 'nodejs', '-y'], sudo=True)
        elif shutil.which('zypper'):
            run_command(['zypper', 'install', '-y', 'ffmpeg', 'nodejs'], sudo=True)
        elif shutil.which('apk'):
            run_command(['apk', 'add', 'ffmpeg', 'nodejs'], sudo=True)
        elif shutil.which('xbps-install'):
            run_command(['xbps-install', '-Sy', 'ffmpeg', 'nodejs'], sudo=True)
        else:
            print_color("Unsupported package manager on Linux. Please install FFmpeg and Node.js manually.", RED)
    else:
        print_color("Unsupported OS. Please install FFmpeg and Node.js manually.", RED)

def uninstall_ffmpeg():
    os_name = get_os_info()
    print_color("\nUninstalling FFmpeg...", CYAN)
    
    if os_name == 'Termux':
        run_command(['pkg', 'uninstall', 'ffmpeg', '-y'])
    elif os_name == 'Darwin':
        run_command(['brew', 'uninstall', 'ffmpeg'])
    elif os_name == 'Windows':
        run_command(['winget', 'uninstall', '-e', '--id', 'Gyan.FFmpeg', '--silent', '--accept-source-agreements'])
    elif os_name == 'Linux':
        if shutil.which('apt'):
            run_command(['apt', 'remove', 'ffmpeg', '-y'], sudo=True)
        elif shutil.which('pacman'):
            run_command(['pacman', '-R', 'ffmpeg', '--noconfirm'], sudo=True)
        elif shutil.which('dnf'):
            run_command(['dnf', 'remove', 'ffmpeg', '-y'], sudo=True)
        elif shutil.which('zypper'):
            run_command(['zypper', 'remove', '-y', 'ffmpeg'], sudo=True)
        elif shutil.which('apk'):
            run_command(['apk', 'del', 'ffmpeg'], sudo=True)
        elif shutil.which('xbps-remove'):
            run_command(['xbps-remove', '-y', 'ffmpeg'], sudo=True)

def install_fluxmedia(force=False):
    if not force and installed_fluxmedia_version() is not None:
        print_color(f"FluxMedia {installed_fluxmedia_version()} already installed — skipping (use --force to reinstall).", GREEN)
        return True
    print_color("\nInstalling FluxMedia Core...", CYAN)
    
    os_name = get_os_info()
    pip_cmd = [sys.executable, "-m", "pip", "install", "-U", "fluxmedia"]
    
    if os_name == 'Termux':
        # Android has no official pydantic-core wheels; the community index
        # only covers certain versions per Python. Pin pydantic to a release
        # whose exact core has Android wheels, installed FIRST so fluxmedia
        # cannot float past it. Verified pairs:
        #   py3.11/3.12/3.13 -> pydantic==2.13.3 (core 2.46.3)
        #   py3.14           -> pydantic==2.12.4 (core 2.41.5)
        minor = sys.version_info[1]
        pin = None
        if minor in (11, 12, 13):
            pin = "pydantic==2.13.3"
        elif minor == 14:
            pin = "pydantic==2.12.4"
        extra = ["--extra-index-url", "https://termux-user-repository.github.io/pypi/",
                 "--extra-index-url", "https://eutalix.github.io/android-pydantic-core/"]
        if pin is not None:
            print_color(f"Termux Python 3.{minor}: pinning {pin} (Android wheels).", YELLOW)
            run_command([sys.executable, "-m", "pip", "install", pin] + extra)
        pip_cmd.extend(extra)
    
    # Attempt install normally, if fails, retry with --break-system-packages
    success = run_command(pip_cmd)
    if not success and os_name != 'Windows':
        print_color("Retrying with --break-system-packages...", YELLOW)
        pip_cmd.append("--break-system-packages")
        run_command(pip_cmd)

def uninstall_fluxmedia():
    print_color("\nUninstalling FluxMedia Core...", CYAN)
    pip_cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "fluxmedia", "rich", "requests", "yt-dlp", "textual", "markdown-it-py", "pygments"]
    
    success = run_command(pip_cmd)
    if not success and get_os_info() != 'Windows':
        pip_cmd.append("--break-system-packages")
        run_command(pip_cmd)

def show_menu(title, options):
    while True:
        print_color(f"\n=== {title} ===", CYAN)
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt}")
        
        choice = input(f"\nSelect an option (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        print_color("Invalid selection. Please try again.", RED)

def main():
    parser = argparse.ArgumentParser(description="FluxMedia professional installer")
    parser.add_argument("--yes", action="store_true", help="default setup without prompts")
    parser.add_argument("--force", action="store_true", help="reinstall everything without prompts")
    parser.add_argument("--check", action="store_true", help="preflight report only")
    parser.add_argument("--uninstall", action="store_true", help="uninstall FluxMedia + FFmpeg")
    args = parser.parse_args()

    if sys.platform == 'win32':
        os.system('')  # Enable ANSI colors

    if args.check:
        print_logo()
        rows = preflight()
        print_summary(rows)
        sys.exit(0 if all(r[1] for r in rows if r[0] in ("Python", "Network")) else 1)

    if args.uninstall:
        print_logo()
        sys.exit(0 if do_uninstall(assume_yes=args.yes or args.force) else 1)

    if args.force:
        sys.exit(0 if do_install(force=True) else 1)

    if args.yes:
        sys.exit(0 if do_install(force=False) else 1)

    print_logo()
    
    while True:
        choice = show_menu("Main Menu", [
            "Install FluxMedia (Default setup)",
            "Reinstall components",
            "Uninstall components",
            "Exit"
        ])
        
        if choice == 1:
            install_system_dependencies()
            install_fluxmedia()
            print_color("\nSuccess! FluxMedia is installed.", GREEN)
            print("Run 'fluxmedia' in your terminal to start.")
            input("\nPress Enter to return to menu...")
        elif choice == 2:
            sub = show_menu("Reinstall Menu", [
                "Reinstall FluxMedia Core Only",
                "Reinstall Everything (Deps + Core)",
                "Back to Main Menu"
            ])
            if sub == 1:
                uninstall_fluxmedia()
                install_fluxmedia()
                input("\nPress Enter to return to menu...")
            elif sub == 2:
                uninstall_fluxmedia()
                uninstall_ffmpeg()
                install_system_dependencies()
                install_fluxmedia()
                input("\nPress Enter to return to menu...")
            elif sub == 3:
                continue
        elif choice == 3:
            sub = show_menu("Uninstall Menu", [
                "Uninstall FluxMedia Core Only",
                "Uninstall FluxMedia + FFmpeg",
                "Back to Main Menu"
            ])
            if sub == 1:
                uninstall_fluxmedia()
                input("\nPress Enter to return to menu...")
            elif sub == 2:
                uninstall_fluxmedia()
                uninstall_ffmpeg()
                input("\nPress Enter to return to menu...")
            elif sub == 3:
                continue
        elif choice == 4:
            print("Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()
