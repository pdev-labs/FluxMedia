"""
FluxMedia - A powerful, cross-platform media processing toolkit.
"""

import sys

def main():
    try:
        from fluxmedia.cli.main import main as cli_main
        cli_main()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
