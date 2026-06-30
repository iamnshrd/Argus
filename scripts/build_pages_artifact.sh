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

for old in [
    '      const API_BASE = "https://api.elections.kalshi.com/trade-api/v2";\n      const JINA_BASE = "https://r.jina.ai/http://";',
    '      const API_BASE = "https://external-api.kalshi.com/trade-api/v2";\n      const JINA_BASE = "https://r.jina.ai/http://";',
    '      const API_BASE = "https://kalshi-mentions-api.iloveyaphets.workers.dev/trade-api/v2";',
    '      const API_BASE = "https://kalshi-mentions-api.iloveyaphets.workers.dev";',
]:
    text = text.replace(old, f'      const API_BASE = "{api_base}";')

fetch_block = '''      async function fetchJson(path) {
        const response = await fetch(`${API_BASE}${path}`, {
          cache: "default",
          headers: { accept: "application/json" },
        });
        const body = await response.text();
        const payload = body ? JSON.parse(body) : null;
        if (!response.ok || payload?.error) {
          const detail = payload?.error?.message || payload?.error?.code || body.slice(0, 200) || "API error";
          const error = new Error(`${response.status} ${response.statusText}: ${detail}`);
          error.status = response.status;
          throw error;
        }
        state.source = "worker";
        return payload;
      }
'''
text, count = re.subn(
    r"      async function fetchJson\(path\) \{.*?\n      async function loadInput\(value\) \{",
    fetch_block.rstrip() + "\n\n      async function loadInput(value) {",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not patch fetchJson")

resolve_block = '''      async function resolveMarket(ticker) {
        if (looksLikeEventTicker(ticker)) {
          const historicalMarkets = await loadHistoricalMarkets(ticker);
          if (historicalMarkets.length) return buildHistoricalResolution(ticker, historicalMarkets);
        }

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
          if (marketError.status === 429) throw marketError;
          try {
            const eventPayload = await fetchJson(`/events/${encodeURIComponent(ticker)}`);
            const markets = eventPayload.markets || [];
            if (markets.length) return { market: pickDefaultMarket(markets), event: eventPayload.event || null, markets };
          } catch (eventError) {
            if (eventError.status === 429) throw eventError;
            console.warn("Event load failed; trying historical markets", eventError);
          }
          const historicalMarkets = await loadHistoricalMarkets(ticker);
          if (historicalMarkets.length) return buildHistoricalResolution(ticker, historicalMarkets);
          throw marketError;
        }
      }

      async function loadHistoricalMarkets(ticker) {
        const encoded = encodeURIComponent(ticker);
        const paths = looksLikeEventTicker(ticker)
          ? [`/historical/markets?event_ticker=${encoded}&limit=200`]
          : [`/historical/markets?event_ticker=${encoded}&limit=200`, `/historical/markets?tickers=${encoded}&limit=1`];
        for (const path of paths) {
          try {
            const payload = await fetchJson(path);
            const markets = payload.markets || [];
            if (markets.length) return markets;
          } catch (error) {
            if (error.status === 429) throw error;
            console.warn("Historical market lookup failed", path, error);
          }
        }
        return [];
      }

      function buildHistoricalResolution(ticker, markets) {
        const market = pickDefaultMarket(markets);
        const eventTicker = market?.event_ticker || ticker;
        return {
          market,
          event: { ticker: eventTicker, title: market?.event_title || market?.title || eventTicker, series_ticker: deriveSeriesFromTicker(eventTicker) },
          markets,
        };
      }

      function looksLikeEventTicker(ticker) {
        return /^KX[A-Z0-9]+-\d{2}[A-Z]{3}\d{2}$/.test(String(ticker || ""));
      }

      function deriveSeriesFromTicker(ticker) {
        const eventTicker = String(ticker || "");
        const datedPrefix = eventTicker.match(/^(.+?)-\d{2}[A-Z]{3}\d{2}/);
        if (datedPrefix) return datedPrefix[1];
        return eventTicker.split("-")[0];
      }
'''
text, count = re.subn(
    r"      async function resolveMarket\(ticker\) \{.*?\n      function pickDefaultMarket\(markets\) \{",
    resolve_block.rstrip() + "\n\n      function pickDefaultMarket(markets) {",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not patch resolveMarket")

candles_block = '''      async function loadCandles() {
        const market = state.market;
        if (!market?.ticker) throw new Error("No market selected");
        const { start, end, interval } = getRequestWindow(market);
        const series = deriveSeriesTicker(market);
        const params = new URLSearchParams({
          start_ts: String(Math.floor(start / 1000)),
          end_ts: String(Math.floor(end / 1000)),
          period_interval: String(interval),
        });
        const payload = await fetchJson(`/series/${encodeURIComponent(series)}/markets/${encodeURIComponent(market.ticker)}/candlesticks?${params}`);
        state.candles = (payload.candlesticks || []).map(normalizeCandle).filter(Boolean);
        state.plottedCandles = state.candles.map(applySide);
      }
'''
text, count = re.subn(
    r"      async function loadCandles\(\) \{.*?\n      function getTimeWindow\(market\) \{",
    candles_block.rstrip() + "\n\n      function getTimeWindow(market) {",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not patch loadCandles")

if "JINA_BASE" in text or "r.jina.ai" in text:
    raise SystemExit("Jina reference still present")
path.write_text(text, encoding="utf-8")
PY
fi

mkdir -p "$BUILD_DIR/Trump/Truth"
cp -R "$ROOT_DIR/truthsocial-forecast/pages/." "$BUILD_DIR/Trump/Truth/"

touch "$BUILD_DIR/.nojekyll"
