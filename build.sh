#!/usr/bin/env bash
# Build-Script für Render
# Wird vor dem Start ausgeführt
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
