#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/pages-build"
BERNIE_WORKER_API_BASE="https://kalshi-mentions-api.iloveyaphets.workers.dev"

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
text = text.replace(
    '      const API_BASE = "https://kalshi-mentions-api.iloveyaphets.workers.dev/trade-api/v2";',
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

resolve_block = '''      async function resolveMarket(ticker) {
        try {
          const marketPayload = await fetchJson(`/markets/${encodeURIComponent(ticker)}`);
          const market = marketPayload.market;
          let event = null;
          let markets = [market];
          if (market?.event_ticker) {
            try {
              const eventPayload = await fetchJson(`/events/${encodeURIComponent(market.event_ticker)}`);
              event = eventPayload.event || null;
              markets = eventPayload.markets?.length ? eventPayload.markets : markets;
            } catch (error) {
              console.warn("Related event load failed", error);
            }
          }
          return { market, event, markets };
        } catch (marketError) {
          try {
            const eventPayload = await fetchJson(`/events/${encodeURIComponent(ticker)}`);
            const markets = eventPayload.markets || [];
            if (markets.length) {
              return {
                market: pickDefaultMarket(markets),
                event: eventPayload.event || null,
                markets,
              };
            }
          } catch (eventError) {
            console.warn("Event load failed; trying historical markets", eventError);
          }

          const historicalMarkets = await loadHistoricalMarkets(ticker);
          if (historicalMarkets.length) {
            const market = pickDefaultMarket(historicalMarkets);
            const eventTicker = market?.event_ticker || ticker;
            return {
              market,
              event: {
                ticker: eventTicker,
                title: market?.event_title || market?.title || eventTicker,
                series_ticker: deriveSeriesFromTicker(eventTicker),
              },
              markets: historicalMarkets,
            };
          }

          throw marketError;
        }
      }

      async function loadHistoricalMarkets(ticker) {
        const encoded = encodeURIComponent(ticker);
        const paths = [
          `/historical/markets?event_ticker=${encoded}&limit=200`,
          `/historical/markets?tickers=${encoded}&limit=1`,
        ];

        for (const path of paths) {
          try {
            const payload = await fetchJson(path);
            const markets = payload.markets || [];
            if (markets.length) return markets;
          } catch (error) {
            console.warn("Historical market lookup failed", path, error);
          }
        }
        return [];
      }

      function deriveSeriesFromTicker(ticker) {
        const eventTicker = String(ticker || "");
        const datedPrefix = eventTicker.match(/^(.+?)-\d{2}[A-Z]{3}\d{2}/);
        if (datedPrefix) return datedPrefix[1];
        return eventTicker.split("-")[0];
      }
'''
resolve_pattern = re.compile(
    r"      async function resolveMarket\(ticker\) \{.*?\n      function pickDefaultMarket\(markets\) \{",
    re.S,
)
text, count = resolve_pattern.subn(resolve_block.rstrip() + "\n\n      function pickDefaultMarket(markets) {", text, count=1)
if count != 1:
    raise SystemExit("Could not patch Bernie resolveMarket block")

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
