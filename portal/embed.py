#!/usr/bin/env python3
"""Embeds the built portal (portal/dist) into server/classic_portal.py.

Replaces PORTAL_HTML_COMPRESSED (shell), PORTAL_CSS_COMPRESSED (empty —
MUI v9 injects styles at runtime, no external stylesheet) and
PORTAL_JS_COMPRESSED (bundle). Run from the repo root after `npm run build`
inside portal/.
"""

import base64
import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "portal" / "dist"
TARGET = ROOT / "src" / "fluxmedia" / "server" / "classic_portal.py"

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FluxMedia - LAN Share Portal</title>
</head>
<body>
<div id="root"></div>
<script type="module" src="/app.js"></script>
</body>
</html>
"""


def pack(text: str) -> str:
    # mtime=0 keeps blobs reproducible: same source always yields same blob,
    # so reviewers can verify embedded output matches portal/dist.
    return base64.b64encode(gzip.compress(text.encode("utf-8"), mtime=0)).decode("ascii")


def main() -> None:
    bundle = DIST / "app.js"
    if not bundle.is_file():
        sys.exit("dist/app.js missing — run `npm run build` in portal/ first")
    js = bundle.read_text(encoding="utf-8")

    src = TARGET.read_text(encoding="utf-8")
    for name, content in [
        ("PORTAL_HTML_COMPRESSED", SHELL),
        ("PORTAL_CSS_COMPRESSED", ""),
        ("PORTAL_JS_COMPRESSED", js),
    ]:
        pattern = re.compile(rf'^{name} = "[A-Za-z0-9+/=]*"$', re.M)
        replacement = f'{name} = "{pack(content)}"'
        src, n = pattern.subn(replacement, src)
        if n != 1:
            sys.exit(f"expected 1 match for {name}, found {n}")
    TARGET.write_text(src, encoding="utf-8")
    print(f"embedded: shell={len(SHELL)}B js={len(js)}B")


if __name__ == "__main__":
    main()
