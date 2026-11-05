#!/usr/bin/env bash
# Smoke test: boots the real server on a random port, checks the main endpoints
# with curl, shuts the server down, prints PASS/FAIL. No Docker, no fixtures.
set -u
cd "$(dirname "$0")/.."

PORT=$(( (RANDOM % 2000) + 8000 ))
BASE="http://127.0.0.1:${PORT}"
# python.exe is a native Windows binary — give it a Windows-style temp path
TMPD="$(mktemp -d)"
command -v cygpath >/dev/null && TMPD="$(cygpath -w "$TMPD")"
export RECIPE_DB="${TMPD}/smoke.db"

echo "smoke: starting uvicorn on :${PORT} (db: ${RECIPE_DB})"
python -m uvicorn app.main:app --port "${PORT}" --log-level warning &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" 2>/dev/null' EXIT

# wait for readiness (cold start on Windows can take a while)
up=0
for _ in $(seq 1 60); do
  # NB: mingw curl chokes on '-o /dev/null' (exit 23), use a shell redirect
  if curl -sf "${BASE}/" >/dev/null 2>&1; then up=1; break; fi
  sleep 0.5
done
if [ "${up}" -ne 1 ]; then
  echo "FAIL: server did not come up on :${PORT}"
  exit 1
fi

fail=0
check() { # name url grep-pattern
  local name="$1" url="$2" pattern="$3" body
  body="$(curl -sf "${url}")" || { echo "FAIL ${name}: request to ${url} failed"; fail=1; return; }
  if printf '%s' "${body}" | grep -q "${pattern}"; then
    echo "PASS ${name}"
  else
    echo "FAIL ${name}: '${pattern}' not found in ${url}"
    fail=1
  fi
}

check "index"        "${BASE}/"                          "Recipe Distiller"
check "bookmarklet"  "${BASE}/bookmarklet"               "javascript:"
check "manifest"     "${BASE}/manifest.webmanifest"      "Recipe Distiller"
check "sw"           "${BASE}/sw.js"                     "recipe-distiller-"
check "favicon"      "${BASE}/favicon.svg"               "svg"
check "recipes"      "${BASE}/api/recipes"               '"recipes"'
check "plan"         "${BASE}/api/plan"                  '"slots"'
check "export"       "${BASE}/api/recipes/export"        '"version"'

# POST checks
conv="$(curl -sf -X POST "${BASE}/api/convert" -H 'Content-Type: application/json' \
  -d '{"ingredients":["2 cups flour"]}')" \
  && printf '%s' "${conv}" | grep -q '480 ml' \
  && echo "PASS convert" || { echo "FAIL convert"; fail=1; }

kill "${SERVER_PID}" 2>/dev/null
wait "${SERVER_PID}" 2>/dev/null

if [ "${fail}" -eq 0 ]; then
  echo "SMOKE: PASS"
  exit 0
else
  echo "SMOKE: FAIL"
  exit 1
fi
