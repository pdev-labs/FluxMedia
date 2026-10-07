#!/usr/bin/env bash
# FluxMedia automated device test — built for Termux, runs anywhere.
# Usage: bash scripts/test-termux.sh [--full]
#   (default) quick: environment, pins, imports, config, plugin scan — no downloads
#   --full:   + real small download + --web boot probe (isolated HOME, network needed)
#
# Exit code: 0 = all passed, 1 = anything failed. No manual steps.
set -u

FULL=0
[[ "${1:-}" == "--full" ]] && FULL=1

PASS=0
FAIL=0
RESULTS=()

pass() { PASS=$((PASS + 1)); RESULTS+=("PASS: $1"); echo "  [OK] $1"; }
fail() { FAIL=$((FAIL + 1)); RESULTS+=("FAIL: $1 -- $2"); echo "  [MISS] $1 -- $2"; }

step() { echo "==> $1"; }

IS_TERMUX=0
[[ "${PREFIX:-}" == *com.termux* ]] && IS_TERMUX=1

# --- 1. environment -------------------------------------------------------
step "1/7 environment"
PYV=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || echo "none")
if [[ "$PYV" =~ ^3\.(11|12|13|14)$ ]]; then pass "python $PYV supported"; else fail "python version" "$PYV"; fi
command -v pip >/dev/null 2>&1 || python3 -m pip --version >/dev/null 2>&1
if [ $? -eq 0 ]; then pass "pip present"; else fail "pip present" "missing"; fi
if [ "$IS_TERMUX" = 1 ]; then
  for c in ffmpeg node; do
    command -v "$c" >/dev/null 2>&1 && pass "$c present" || fail "$c present" "pkg install $c"
  done
else
  echo "  (not Termux: skipping pkg checks, testing generic paths)"
fi
if (echo > /dev/tcp/8.8.8.8/53) 2>/dev/null; then pass "network reachable"; else fail "network reachable" "offline?"; fi
FREE_KB=$(df -k "$HOME" 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "$FREE_KB" ] && [ "$FREE_KB" -gt 500000 ]; then pass "disk space ${FREE_KB}K"; else fail "disk space" "${FREE_KB:-unknown}K"; fi

# --- 2. pydantic pin table --------------------------------------------------
step "2/7 pydantic pin table"
case "$PYV" in
  3.11|3.12|3.13) WANT_PIN="pydantic==2.13.3"; WANT_CORE="2.46.3" ;;
  3.14)           WANT_PIN="pydantic==2.12.4"; WANT_CORE="2.41.5" ;;
  *)              WANT_PIN=""; WANT_CORE="" ;;
esac
if [ "$IS_TERMUX" -ne 1 ]; then
  echo "  (not Termux: pins don't apply, core imports are enough)"
  python3 -c "import pydantic_core; print('  core imports, version', pydantic_core.__version__)" 2>/dev/null \
    && pass "pydantic_core imports" || fail "pydantic_core imports" "broken install?"
elif [ -z "$WANT_PIN" ]; then
  echo "  (python $PYV outside pin table: skipping pin checks)"
else
  HAVE_PYD=$(python3 -c "import importlib.metadata as m; print(m.version('pydantic'))" 2>/dev/null || echo "missing")
  HAVE_CORE=$(python3 -c "import importlib.metadata as m; print(m.version('pydantic-core'))" 2>&1 | grep -v Warning | tail -1)
  WANT_VER="${WANT_PIN##*==}"
  if [ "$HAVE_PYD" = "$WANT_VER" ]; then pass "pydantic==$WANT_VER pinned"; else fail "pydantic pin" "have $HAVE_PYD, want $WANT_VER"; fi
  if [ "$HAVE_CORE" = "$WANT_CORE" ]; then pass "pydantic-core==$WANT_CORE"; else fail "pydantic-core" "have $HAVE_CORE, want $WANT_CORE"; fi
  python3 -c "import pydantic_core; print('  core imports, version', pydantic_core.__version__)" 2>/dev/null \
    && pass "pydantic_core imports" || fail "pydantic_core imports" "No module named 'pydantic_core'?"
fi

# --- 3. fluxmedia install ---------------------------------------------------
step "3/7 fluxmedia package"
if python3 -c "import fluxmedia" 2>/dev/null; then
  FV=$(python3 -c "import importlib.metadata as m; print(m.version('fluxmedia'))" 2>/dev/null || echo "unknown")
  pass "fluxmedia importable ($FV)"
else
  fail "fluxmedia importable" "pip install fluxmedia"
fi

# --- 4. core logic (no network) ----------------------------------------------
step "4/7 core logic"
python3 - <<'EOF' 2>&1 | tail -4
import sys
try:
    import fluxmedia
except ImportError as e:
    print("SKIP-NO-FLUXMEDIA"); raise SystemExit(0)
from fluxmedia.core import normalize_url, should_check_for_updates, is_version_ignored
assert normalize_url("https://youtu.be/AAA?t=5") == "https://www.youtube.com/watch?v=AAA"
assert should_check_for_updates({"auto_update": True, "update_interval": "weekly", "last_update_check": 0})
assert not should_check_for_updates({"auto_update": True, "update_interval": "never", "last_update_check": 0})
assert is_version_ignored("1.0", {"ignored_versions": ["1.0"]})
from fluxmedia.plugins import PluginManager
m = PluginManager({}).discover()
print("CORE-OK plugins-found:", len(m))
EOF
if [ "${PIPESTATUS[0]}" -eq 0 ]; then
  if python3 -c "import fluxmedia" 2>/dev/null; then pass "core logic + plugin scan"; else pass "core logic (skipped, no package)"; fi
else
  fail "core logic" "see output above"
fi

# --- 5. install.py --check ----------------------------------------------------
step "5/7 installer preflight"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/install.py" ]; then
  python3 "$ROOT/install.py" --check >/dev/null 2>&1 && pass "install.py --check" || fail "install.py --check" "non-zero exit"
else
  echo "  (repo checkout not found: skipping)"
fi

if [ "$FULL" -ne 1 ]; then
  echo; echo "QUICK DONE: $PASS passed, $FAIL failed (rerun with --full for download+web probes)"
  [ "$FAIL" -eq 0 ]
  exit $?
fi

# --- 6. real download (isolated HOME) ------------------------------------------
step "6/7 real download"
export TESTHOME=/tmp/fluxtest-home
rm -rf "$TESTHOME"; mkdir -p "$TESTHOME"
# Isolated HOME hides ~/.local site-packages: carry it explicitly so the
# dev tree (or any --user install) stays importable under the test HOME.
USERSITE=$(python3 -c "import site; print(site.getusersitepackages())" 2>/dev/null || echo "")
export PYTHONPATH="${PYTHONPATH:-}:${USERSITE}"
U="https://download.samplelib.com/mp4/sample-5s.mp4"
printf "n\n" | HOME="$TESTHOME" timeout 120 python3 -m fluxmedia "$U" >/tmp/fluxtest-dl.log 2>&1
if ls "$TESTHOME"/*/FluxMediaDownloads/*.mp4 "$TESTHOME"/FluxMediaDownloads/*.mp4 2>/dev/null | head -1 | grep -q mp4; then
  pass "real download landed on disk"
else
  # fall back: any mp4 anywhere under TESTHOME
  if find "$TESTHOME" -name "*.mp4" 2>/dev/null | grep -q .; then pass "real download landed on disk"; else fail "real download" "see /tmp/fluxtest-dl.log"; fi
fi

# --- 7. --web boot probe ---------------------------------------------------------
step "7/7 web boot probe"
printf "n\n" | HOME="$TESTHOME" nohup python3 -m fluxmedia --web >/tmp/fluxtest-web.log 2>&1 &
SRV=$!
ok=0
for _ in $(seq 1 20); do
  curl -sf -o /dev/null --max-time 3 http://127.0.0.1:8000/ && { ok=1; break; }
  sleep 3
done
if [ "$ok" = 1 ]; then
  curl -sf http://127.0.0.1:8000/api/diagnostics >/dev/null && pass "web boot + diagnostics" || fail "web boot + diagnostics" "endpoint error"
else
  fail "web boot + diagnostics" "no response on :8000"
fi
kill $SRV 2>/dev/null

echo; echo "FULL DONE: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
