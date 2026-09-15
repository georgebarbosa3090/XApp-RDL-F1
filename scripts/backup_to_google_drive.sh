#!/usr/bin/env bash
# Bash wrapper for automated Google Drive backup of XApp-RDL-F2
set -e

echo "=== Iniciando processo de backup automatizado para o Google Drive ==="

if command -v uv &> /dev/null; then
    uv run --with google-api-python-client --with google-auth-httplib2 --with google-auth-oauthlib python3 scripts/backup_to_google_drive.py
else
    python3 scripts/backup_to_google_drive.py
fi
