# Truth Social Forecast

Small forecasting app for Kalshi's weekly Trump Truth Social post-count market.

The target is the Roll Call / Factba.se count used by Kalshi resolution, not a native Truth Social scrape.

## Run

```bash
python3 truthsocial-forecast/truthsocial_forecast.py
```

## GitHub Pages

The dashboard in `truthsocial-forecast/pages/` is static. GitHub Actions rebuilds
`pages/data/forecast.json` every hour and deploys it to
`https://iamnshrd.github.io/Argus/Trump/Truth/`.

```bash
python3 truthsocial-forecast/build_pages_data.py
python3 -m http.server 8765 --directory truthsocial-forecast/pages
```

Use a fixed ET timestamp for reproducible checks:

```bash
python3 truthsocial-forecast/truthsocial_forecast.py --now 2026-05-24T10:00:00
```

Download a 3-month post-level base before forecasting:

```bash
python3 truthsocial-forecast/download_truths.py
python3 truthsocial-forecast/truthsocial_forecast.py --post-history truthsocial-forecast/data/truthsocial_posts_2026-02-22_2026-05-23.jsonl
```

Download explicit source-week ranges:

```bash
python3 truthsocial-forecast/download_truths.py --start 2026-01-04 --end 2026-05-23
```

Download holdout samples outside the training base:

```bash
python3 truthsocial-forecast/download_truths.py \
  --start 2025-08-31 \
  --end 2025-11-01 \
  --output truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl
```

Files in `truthsocial-forecast/data/sample/` are test-only holdouts. Training and calibration defaults should keep using post-history files from 2026+ in `truthsocial-forecast/data/`.

Backtest one historical cutoff:

```bash
python3 truthsocial-forecast/backtest_point.py --week first --weekday wednesday --time 12:00
```

Check the endorsement/election-week hypothesis:

```bash
python3 truthsocial-forecast/analyze_hypothesis.py \
  --post-history truthsocial-forecast/data/truthsocial_posts_2026-01-04_2026-05-23.jsonl
```

Compute weekly topic mix:

```bash
python3 truthsocial-forecast/topic_mix.py \
  --post-history truthsocial-forecast/data/truthsocial_posts_2026-01-04_2026-05-23.jsonl \
  --week first
```

Summarize current-week live features:

```bash
python3 truthsocial-forecast/live_features.py
```

Run random point backtests:

```bash
python3 truthsocial-forecast/random_backtest.py --n 10 --seed 11
```

Run full grid backtest:

```bash
python3 truthsocial-forecast/grid_backtest.py --samples 12000
```

Run the 2026-trained model on a separate holdout sample:

```bash
python3 truthsocial-forecast/holdout_backtest.py \
  --test-history truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl \
  --output truthsocial-forecast/data/sample/holdout_backtest_2025-08-31_2025-11-01_sun_sat_vs_2026.csv \
  --samples 12000
```

Run the late-week remaining model after five full days:

```bash
python3 truthsocial-forecast/holdout_backtest.py \
  --test-history truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl \
  --output truthsocial-forecast/data/sample/holdout_late_backtest_2025-08-31_2025-11-01_sun_sat_vs_2026.csv \
  --days 6,7 \
  --samples 12000
```

Export weekly topic feature tables:

```bash
python3 truthsocial-forecast/topic_mix.py \
  --post-history truthsocial-forecast/data/truthsocial_posts_2026-01-04_2026-05-23.jsonl \
  --export-csv truthsocial-forecast/data/weekly_topic_mix_2026-01-04_2026-05-23.csv \
  --export-json truthsocial-forecast/data/weekly_topic_mix_2026-01-04_2026-05-23.json
```

## What It Does

- Detects the current Sunday-Saturday week in New York time.
- Pulls the current week count through the Roll Call adapter.
- Pulls completed historical weekly counts.
- Can download post-level Truth Social history as JSONL.
- Fetches the matching Kalshi event bins when available.
- Simulates the final weekly count from weekly counts or post-level historical curves.
- Caches Roll Call weekly counts in `truthsocial-forecast/.cache/`.
- Always fetches the current-week observed count fresh; the cache is only for historical counts.

## Structure

- `truthsocial_forecast.py`: CLI, Kalshi bins, forecast simulation, report output.
- `rollcall_client.py`: Roll Call / Factba.se adapter, count API, local JSON cache.
- `download_truths.py`: post-level Roll Call downloader.
- `backtest_point.py`: leave-one-week-out point backtest for one historical cutoff.
- `analyze_hypothesis.py`: weekly endorsement/election feature check.
- `topic_mix.py`: weekly topic composition by primary topic.
- `live_features.py`: current-week velocity, burst, and topic summary.
- `random_backtest.py`: random leave-one-week-out point backtests.
- `grid_backtest.py`: all-weeks x cutoff grid calibration table.
- `remaining_model.py`: late-week remaining-post model for day 6-7 source tracking.
- `regime.py`: diagnostic regime classifier for high-tail / normal / fade-risk cuts.
- `topic_taxonomy.json`: editable keyword taxonomy for topic classification.

## Options

```bash
python3 truthsocial-forecast/truthsocial_forecast.py --lookback-weeks 52 --samples 30000
```

Post-history simulations add light residual noise by default so the output is not just a discrete replay of 13 historical weeks:

```bash
python3 truthsocial-forecast/truthsocial_forecast.py --post-history truthsocial-forecast/data/truthsocial_posts_2026-02-22_2026-05-23.jsonl --post-noise-sigma 0.12
```

Bypass the local cache:

```bash
python3 truthsocial-forecast/truthsocial_forecast.py --no-cache
```

## Notes

Early Sunday output is mostly a baseline forecast. As the week progresses, the model increasingly becomes a Roll Call source-count tracker.
