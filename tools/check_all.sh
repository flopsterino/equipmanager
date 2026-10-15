#!/bin/sh
# Build, then prove the build only changed what the sources changed.
set -e
cd "$(dirname "$0")/.."
python3 tools/build_msapp.py
python3 tools/verify_roundtrip.py
