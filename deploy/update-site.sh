#!/usr/bin/env bash
set -euo pipefail

readonly REPO_DIR=/opt/nepp
readonly VENV_DIR="${REPO_DIR}/venv"
readonly SITE_DIR=/srv/nepp-site

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this command with sudo." >&2
    exit 1
fi

if [[ ! -d "${REPO_DIR}/.git" ]]; then
    echo "NEPP repository not found at ${REPO_DIR}." >&2
    exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Python virtual environment not found at ${VENV_DIR}." >&2
    exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
    apt-get update
    apt-get install --yes rsync
fi

echo "Updating NEPP from GitHub..."
git -C "${REPO_DIR}" pull --ff-only

echo "Updating documentation dependencies..."
"${VENV_DIR}/bin/python" -m pip install "${REPO_DIR}[docs]"

echo "Building the Japanese and English site..."
cd "${REPO_DIR}"
"${VENV_DIR}/bin/mkdocs" build --clean --strict

echo "Publishing to ${SITE_DIR}..."
install -d -m 0755 "${SITE_DIR}"
rsync -a --delete "${REPO_DIR}/site/" "${SITE_DIR}/"

echo "Published: https://nepp.kenic.jp/"
