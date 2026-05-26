# Session Handoff — 2026-05-26 — Mention Rules And Alerts

## 1. Current Operating State

- Argus mode: Russian, concise, risk-officer analytical partner for Kalshi mention markets. No trading decisions, no buy/sell/size instructions.
- Workspace: `C:\Users\Professional\Documents\Argus`.
- Telegram mention alert bot exists in `telegram-mention-alert-bot/`.
  - Built as a local Node.js project.
  - Sends Telegram notifications for new Kalshi mention markets.
  - Default polling interval: `MENTION_ALERT_INTERVAL_MS=120000` (2 minutes).
  - Current Kalshi scan is intentionally capped at recent mention series (`MENTION_ALERT_MAX_SERIES=50`) to avoid 429s.
  - Local `.env` contains Telegram bot token and private chat id; do not echo the token. Token was pasted in chat, so rotation via BotFather is recommended before VPS deployment.
  - `npm test` previously passed 14/14 after terminal logging was added.
  - Store seeded in `data/mention-alert-seen.json`, so first real run should not spam old backlog.
- Discord/Chrome investigation was abandoned; user wants Telegram alerts locally first, VPS later.
- Git tree has many unrelated dirty/untracked files. Do not revert or stage unrelated changes. Current Argus-memory edits are uncommitted unless explicitly committed later.

## 2. Important Memory Updates

- Created canonical operating rules:
  - `argus-memory/market-case-files/mention-market-operating-rules.md`
  - Core rule: do not analyze what someone might say until the event is confirmed to qualify.
  - Order: eligibility gate -> event/format -> source discipline -> internal tools -> wording path -> transcript/base rate -> consensus/price -> live plan -> postmortem.
- Updated `AGENTS.md`:
  - Operating principle now begins with rules/eligibility and live status.
  - `mention-market-operating-rules.md` is the canonical order when memory files conflict.
  - Full rules section is still omitted unless asked, except when eligibility/live/speaker/countability controls the analysis.
- Updated templates:
  - `mention-market-brief-template.md` now has `Eligibility Gate` and `Fast Brief Minimum`.
  - `mention-market-wording-fv-protocols.md` now has `Step 0: Verify Event Eligibility`.
  - `mention-market-postmortem-template.md` now tracks event eligibility/live status and missed eligibility.
  - `trader-interviews-2026-05.md` operational checklist now starts with event qualification/live/special-programming risk.
- Reorganized `argus-memory/error-log.md` into categories:
  - rules/eligibility errors;
  - wording errors;
  - format/sample errors;
  - source errors;
  - price/edge errors.
- Added Rachel Maddow dossier:
  - `argus-memory/persona-dossiers/rachel-maddow.md`
  - Main lesson: regular Monday 9pm ET slot is not proof of live Rachel Maddow participation.
- Filled watchlist:
  - `argus-memory/watchlist.md`
  - Includes Maddow Mondays, guest-host TV shows, Sunday political shows, Trump event ambiguity, sports announcer segmentation.
- Updated source map:
  - `argus-memory/source-map.md`
  - Added recurring TV/show format sources: official schedule, TV guides, official socials, Reddit/show communities, Bluesky/X/social search.
- Updated `шаблоны.md`:
  - Added copy-paste prompts for full market analysis, quick analysis, and TV/live-only markets.

## 3. Open Hypotheses

- Live-only mention markets can have rules/eligibility edge that dominates every strike. If the speaker is not live, topical content may be irrelevant.
- Last-mile community signals 2-4 hours before TV airtime can be actionable as triggers, even if not final proof.
- Official TV schedules are often necessary but insufficient: they confirm slot/show identity, not live status or speaker participation.
- C-level sources such as subreddit programming notes should trigger rules re-checks, not high-confidence factual conclusions by themselves.
- For recurring markets, edge migrates from transcript access to correct segmentation, rules awareness, and last-mile format checks.
- Broad transcript hit rates may be actively harmful if event format, speaker role, phase, or broadcaster does not match.

## 4. Active Watchlist

- Rachel Maddow Mondays:
  - Before topic analysis, check live eligibility.
  - Check holidays, special programming, guest host, prerecorded/replay risk.
  - Last-mile sources: official schedule, MS NOW/show page, `r/msnow`, `r/RachelMaddow`, Bluesky/X searches.
- TV shows with named speakers:
  - A show title does not prove the named person appears or speaks.
  - Verify required speaker and content that counts.
- Sunday political shows:
  - Guest list, transcript source, and speaker separation matter more than broad topic salience.
- Trump events:
  - Check live remarks vs prepared text vs pool spray vs replay/quote.
  - Do not transfer rally wording into ceremonial/prepared remarks without phase mapping.
- VP/White House interviews:
  - Long topic segment does not imply all second-layer words.
  - Names, meme details, and case-specific terms usually require a direct prompt.
- Sports announcer markets:
  - Confirm broadcaster, feed, announcer assignment, game state, and resolving source.
  - Broad sport transcript rates need broadcaster/game-state segmentation.

## 5. Current Analytical Standards

- Start every market with eligibility:
  - Does the event qualify?
  - If live participation is required, is the speaker actually live?
  - Is there guest-host, prerecorded, replay, archival, clip-package, or holiday/special-programming risk?
- Then establish:
  - exact strike;
  - required speaker;
  - event/show identity;
  - timezone;
  - source quality;
  - format bucket;
  - phase map.
- Use internal tools when available:
  - MentionsFlow for market metadata and workflow state.
  - MentionsTerminal for transcript coverage, word matrix, hit context, and full transcripts.
- Do not claim sources/tools/transcripts were checked unless actually opened.
- Use wording path:
  - `event format -> speech phase -> communicative task -> topic -> natural formulation -> exact strike`.
- Keep probability components separate:
  - path activation;
  - exact wording conditional;
  - countability.
- Always classify edge type:
  - research, segmentation, rules, speed, flow, liquidity, tooling, temperament, or none.
- Refuse a number when eligibility, format, source freshness, speech pattern, or edge type is too unclear.
- No trading decisions. Fair range can be compared to market price if price is provided, but no buy/sell/hold/size.

## 6. Pending Tasks

- Commit or intentionally leave uncommitted the Argus-memory rule revision. If committing, stage only relevant files.
- Consider rotating Telegram bot token via BotFather before VPS deployment because token was pasted into chat.
- Add timestamps to Telegram bot terminal logs if user wants better operational observability.
- Add VPS deployment notes for Telegram bot when ready:
  - process manager;
  - `.env` handling;
  - log rotation;
  - restart policy;
  - safe token storage.
- Build a recurring Maddow pre-air checklist automation only if user asks for recurring monitoring.
- For next real market analysis, use the new copy-paste prompt in `шаблоны.md` and verify that the operating rules are not too heavy in live use.
- Create more show/person dossiers as recurring traps appear:
  - Sunday shows;
  - major Fox/MSNBC hosts;
  - sports broadcaster families.
