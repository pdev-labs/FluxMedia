# Contributing to FluxMedia

Thank you for your interest in contributing to FluxMedia! This document outlines code style, development environments, testing, and pull request workflows.

## Developer Setup

### 1. Clone the Repository
```bash
git clone https://github.com/pdev-labs/FluxMedia-py.git
cd FluxMedia-py
```

### 2. Set Up a Virtual Environment
```bash
python3 -m venv .venv
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies in Editable Mode
```bash
pip install --upgrade pip
pip install -e .
```

---

## Code Quality & Development Guidelines

### Code Style
- Follow PEP 8 style standards.
- Use explicit type hints for function signatures.
- Clean up unused modules or copy-pasted duplicate functions.

### Resource Repacking
If you modify static portal web files inside `index.html`, `style.css`, or `app.js`, you **must** repack them into `fluxmedia/main.py` before building or committing:
```bash
python repack.py
```
This base64-compresses the files and updates `PORTAL_HTML_COMPRESSED`, `PORTAL_CSS_COMPRESSED`, and `PORTAL_JS_COMPRESSED` variables.

---

## Release Guidelines

When prepping a release (adhering to project rules):
1. Document version changes in `CHANGELOG.md`.
2. Update the "Latest Release" section in `README.md`.
3. Increment the version number inside `pyproject.toml`.
4. Commit, push, and spawn a GitHub release tag using the GitHub CLI:
   ```bash
   gh release create v1.x.x -t "v1.x.x: Release Name" -n "Release notes..."
   ```
