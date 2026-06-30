#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/pages-build"
BERNIE_WORKER_API_BASE="https://kalshi-mentions-api.iloveyaphets.workers.dev/trade-api/v2"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

if [[ -d "$ROOT_DIR/site" ]]; then
  cp -R "$ROOT_DIR/site/." "$BUILD_DIR/"
fi

BERNIE_INDEX="$BUILD_DIR/Bernie/index.html"
if [[ -f "$BERNIE_INDEX" ]]; then
  BERNIE_INDEX="$BERNIE_INDEX" BERNIE_WORKER_API_BASE="$BERNIE_WORKER_API_BASE" python - <<'PY'
from pathlib import Path
import os
import re

path = Path(os.environ["BERNIE_INDEX"])
text = path.read_text(encoding="utf-8")
api_base = os.environ["BERNIE_WORKER_API_BASE"]

text = text.replace(
    '      const API_BASE = "https://api.elections.kalshi.com/trade-api/v2";\n      const JINA_BASE = "https://r.jina.ai/http://";',
    f'      const API_BASE = "{api_base}";',
)
text = text.replace(
    '      const API_BASE = "https://external-api.kalshi.com/trade-api/v2";\n      const JINA_BASE = "https://r.jina.ai/http://";',
    f'      const API_BASE = "{api_base}";',
)

fetch_block = '''      async function fetchJson(path) {
        const url = appendCacheBust(`${API_BASE}${path}`);

        const response = await fetch(url, {
          cache: "no-store",
          headers: {
            accept: "application/json",
          },
        });

        if (!response.ok) {
          const body = await response.text().catch(() => "");
          throw new Error(
            `${response.status} ${response.statusText}${body ? `: ${body.slice(0, 200)}` : ""}`
          );
        }

        const payload = await response.json();

        if (payload?.error) {
          throw new Error(payload.error.message || payload.error.code || "Kalshi API error");
        }

        state.source = "worker";
        return payload;
      }
'''
pattern = re.compile(
    r"      async function fetchJson\(path\) \{.*?\n      async function loadInput\(value\) \{",
    re.S,
)
text, count = pattern.subn(fetch_block.rstrip() + "\n\n      async function loadInput(value) {", text, count=1)
if count != 1:
    raise SystemExit("Could not patch Bernie fetchJson block")
if "JINA_BASE" in text or "r.jina.ai" in text:
    raise SystemExit("Jina reference still present after Bernie patch")
if api_base not in text:
    raise SystemExit("Worker API base missing after Bernie patch")
path.write_text(text, encoding="utf-8")
PY
fi

mkdir -p "$BUILD_DIR/Trump/Truth"
cp -R "$ROOT_DIR/truthsocial-forecast/pages/." "$BUILD_DIR/Trump/Truth/"

touch "$BUILD_DIR/.nojekyll"
