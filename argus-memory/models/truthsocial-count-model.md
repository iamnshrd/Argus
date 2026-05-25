# Trump Truth Social Weekly Count Model

Purpose: forecast Kalshi's weekly `KXTRUTHSOCIAL` basket from the same Roll Call / Factba.se count used for resolution.

Core discipline:
- Target the Roll Call count, not a native Truth Social scrape.
- Use Sunday 00:00 ET through Saturday 23:59 ET.
- Treat Truths, ReTruths, and Quote Truths as included, matching Kalshi's market text.
- Treat replies and deletions as source-mechanics risk unless Roll Call makes them visible in the count.

MVP implementation:
- App folder: `truthsocial-forecast/`
- Script: `truthsocial-forecast/truthsocial_forecast.py`
- Roll Call adapter: `truthsocial-forecast/rollcall_client.py`
- Post-level downloader: `truthsocial-forecast/download_truths.py`
- Point backtest: `truthsocial-forecast/backtest_point.py`
- Hypothesis check: `truthsocial-forecast/analyze_hypothesis.py`
- Topic mix: `truthsocial-forecast/topic_mix.py`
- Live features: `truthsocial-forecast/live_features.py`
- Data source: `https://rollcall.com/wp-json/factbase/v1/twitter`
- Kalshi event source: `https://api.elections.kalshi.com/trade-api/v2/events/{event_ticker}`
- No external Python dependencies.

Run:

```bash
python3 truthsocial-forecast/truthsocial_forecast.py
```

Download post-level history for the last 13 completed weeks:

```bash
python3 truthsocial-forecast/download_truths.py
python3 truthsocial-forecast/truthsocial_forecast.py --post-history truthsocial-forecast/data/truthsocial_posts_2026-02-22_2026-05-23.jsonl
```

Holdout sample, not training data:

```bash
python3 truthsocial-forecast/download_truths.py \
  --start 2025-08-31 \
  --end 2025-11-01 \
  --output truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl
```

Rule: use `truthsocial-forecast/data/sample/` only for out-of-sample tests. Default training/calibration should use 2026+ post-history files from `truthsocial-forecast/data/`.

Run the fixed-train holdout test:

```bash
python3 truthsocial-forecast/holdout_backtest.py \
  --test-history truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl \
  --output truthsocial-forecast/data/sample/holdout_backtest_2025-08-31_2025-11-01_sun_sat_vs_2026.csv \
  --samples 12000
```

Late-week discipline:
- After five full days, forecast remaining posts instead of replaying whole-week similarity.
- `truthsocial-forecast/remaining_model.py` classifies late remaining regimes: `burst_exhaustion`, `quiet_taper`, `late_continuation`, `active_taper`, and `normal_taper`.
- The late-week forecast is `observed + calibrated remaining`, where remaining quantiles are learned from 2026 train weeks for the same cutoff.
- On the Sunday-Saturday 2025-08-31..2025-11-01 sample, `--days 6,7` produced median absolute error 4.0, mean absolute error 5.2, and max p50 error 15.

Run the late-week holdout test:

```bash
python3 truthsocial-forecast/holdout_backtest.py \
  --test-history truthsocial-forecast/data/sample/truthsocial_posts_2025-08-31_2025-11-01_sun_sat.jsonl \
  --output truthsocial-forecast/data/sample/holdout_late_backtest_2025-08-31_2025-11-01_sun_sat_vs_2026.csv \
  --days 6,7 \
  --samples 12000
```

Run one cutoff backtest:

```bash
python3 truthsocial-forecast/backtest_point.py --week first --weekday wednesday --time 12:00
```

Check endorsement/election-week hypothesis:

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

Export weekly topic features:

```bash
python3 truthsocial-forecast/topic_mix.py \
  --post-history truthsocial-forecast/data/truthsocial_posts_2026-01-04_2026-05-23.jsonl \
  --export-csv truthsocial-forecast/data/weekly_topic_mix_2026-01-04_2026-05-23.csv \
  --export-json truthsocial-forecast/data/weekly_topic_mix_2026-01-04_2026-05-23.json
```

For a fixed timestamp:

```bash
python3 truthsocial-forecast/truthsocial_forecast.py --now 2026-05-24T10:00:00
```

Model shape:
- Pull the current week count through the Roll Call adapter.
- Pull completed Sunday-Saturday weekly counts for the lookback window through the same adapter.
- Build a recency-weighted empirical weekly distribution.
- Shrink the live count into the baseline according to elapsed week fraction.
- Simulate final weekly totals and map them into Kalshi bins.

Post-history simulation shape:
- Download post-level rows for the last 13 completed Sunday-Saturday weeks.
- Drop incomplete weeks from the local history.
- For the current elapsed point in the week, sample a historical week and add its remaining posts after that same point to the observed current-week count.
- Add light residual noise so 13 historical weeks do not create artificial zero-probability bins.
- Map simulated totals into Kalshi bins.

Point backtest:
- Choose a target source week and cutoff point.
- Count observed posts before cutoff.
- Exclude the target week from the simulation history.
- Forecast final count, then compare the distribution with the actual final source-week count.

Topic mix:
- Classify each post into one primary topic using an editable keyword taxonomy.
- Aggregate topic counts by source week.
- Use percentages as model features and diagnostic context, not as final truth.

Source adapter boundary:
- `rollcall_client.py` owns Roll Call URL parameters, `MM/DD/YYYY` date formatting, `meta.total_hits` parsing, cache TTL, and request errors.
- Forecast code should not know Roll Call's raw JSON structure.
- Future source quirks, pagination, post-level rows, lag checks, and deleted/reply handling should be added to the adapter first.

Interpretation:
- Early Sunday output is mostly baseline, because little of the week has elapsed.
- Late-week output increasingly becomes a source-counting problem.
- If Kalshi event fetch fails, the script falls back to the observed May 2026 bin set: `<80`, `80-99`, `100-119`, `120-139`, `140-159`, `160-179`, `180-199`, `200-220`, `>220`.

Known weaknesses:
- The MVP is weekly-count first; it does not yet model day/hour posting bursts directly.
- It does not classify post type clusters such as repost streaks, endorsement dumps, image-only bursts, or crisis/news catalysts.
- Roll Call lag is not modeled separately yet.
- The 2026-01-18 week finished at 291 and should be treated as a stress-case, not as a central training target. Do not overfit regime settings to make that single outlier look well-calibrated. Keep rare explosion signals as a separate `extreme_outlier_risk` diagnostic unless repeated cases prove they improve broad backtest quality.

Next model upgrades:
- Add daily/hourly profile from paginated Roll Call rows.
- Add burst-state detection from recent post velocity.
- Add catalyst features from Trump's public calendar and major news clusters.
- Add rolling backtest with log loss and calibration by Kalshi bin.
