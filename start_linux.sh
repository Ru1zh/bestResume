#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

HOST="127.0.0.1"
PORT="8020"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3 was not found. Install Python 3.9+ and try again."
  exit 1
fi

PYTHON_VERSION="$(python3 --version 2>&1)"
echo "[OK] Using ${PYTHON_VERSION}"

if [ ! -x ".venv/bin/python" ]; then
  echo "[..] Creating virtual environment..."
  python3 -m venv .venv
fi

VENV_PYTHON=".venv/bin/python"

echo "[..] Installing dependencies..."
"${VENV_PYTHON}" -m pip install --quiet --upgrade pip
"${VENV_PYTHON}" -m pip install --quiet -r requirements.txt

URL="http://${HOST}:${PORT}"
echo "[OK] Starting bestResume at ${URL} ..."

if command -v xdg-open >/dev/null 2>&1; then
  (sleep 1; xdg-open "${URL}") >/dev/null 2>&1 &
fi

exec "${VENV_PYTHON}" -m uvicorn app:app --host "${HOST}" --port "${PORT}"
