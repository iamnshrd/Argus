#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/pages-build"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

if [[ -d "$ROOT_DIR/site" ]]; then
  cp -R "$ROOT_DIR/site/." "$BUILD_DIR/"
fi

mkdir -p "$BUILD_DIR/Trump/Truth"
cp -R "$ROOT_DIR/truthsocial-forecast/pages/." "$BUILD_DIR/Trump/Truth/"

touch "$BUILD_DIR/.nojekyll"
