# Source Map

## Mentions Flow

Status: internal software / AppSheet workspace.

Observed on: 2026-05-15.

Purpose:
- operational tracker for mention markets;
- intake queue for new markets;
- source-check and status workflow;
- store of completed markets and future postmortem data;
- guide/subcategory structure for recurring speakers, shows, and market types.

Main views observed:
- `Dashboard`: attention queue, markets due this week, due today, open markets.
- `Markets`: active/intake markets. Observed fields include `EventName`, `Date`, `MarketURL`, `Speaker`, `EventType`, `SourceStatus`, `Q&A`, related trades, related source checks, related strikes, related postmortems, `StatusBadge`.
- `Regular Markets`: recurring or scheduled market families, including MrBeast video, Trump monthly mentions, Trump Truth Social posts.
- `Analytics`: cumulative PnL, statistics, risk by market.
- `Guides`: top categories observed: politicians, TV, Trump.
- `Guides -> Subcategories`: observed politician subcategories include Marco Rubio, Gavin Newsom, JD Vance, Scott Bessent, Zohran Mamdani, Pete Hegseth; TV subcategories include Hannity, MeetThePress, FaceTheNation, 60minutes, Kudlow, The Ingram Angle, Jesse Watters Primetime.
- `Completed Markets`: resolved/history area. Observed completed examples include Trump maternal healthcare event and Kevin O'Leary Fox News interview.

Workflow signals observed:
- Status examples: `Intake`, `Watch`.
- Source-check fields observed: `SourceStatus`, `EDNQ Risk`, `Q&A`, `CheckedAt`, `Decision`, `Notes`.
- Related entities: `Trades`, `SourceChecks`, `Strikes`, `Postmortems`.

Argus usage rule:
- Treat Mentions Flow as Николай's internal operational map, not as proof by itself.
- Use it to identify market metadata, event type, source-check status, recurring categories, and postmortem hooks.
- For analytical conclusions, still require independent source discipline: official source, transcript/video/audio, direct quotes, or clearly labeled partial evidence.
- Completed markets should be mined for base rates and error logs when enough postmortems exist.
- Guides/subcategories should be used to route persona dossiers and show-format dossiers, but empty guide categories are not evidence of absence.

Current gaps:
- Several observed guide subcategories, including JD Vance and Hannity, had no visible guide items yet.
- No visible strike details in the sampled active market.
- No visible postmortems in sampled completed market.

## MentionsTerminal

Status: internal software / web app.

Observed on: 2026-05-15.

Purpose:
- transcript storage and management;
- speaker-level mention analysis;
- AI-assisted transcript and speech-structure analysis;
- market/calendar/terminal tooling around Kalshi and mention markets;
- admin and God Mode tools for deeper transcript, market, and usage workflows.

Public app shell observed:
- Site title: `MentionsTerminal`.
- Positioning: real-time tools for mentions traders.
- Landing-page promises: store transcripts, analyze mentions, track edge.

Main user-facing modules observed from app bundle:
- `Add Transcripts`: fetch and upload new transcripts.
- `Batch Upload`: bulk transcript upload flow.
- `Mentions Analysis` / `/analysis`: word frequency and speaker-pattern analysis.
- `Manage Transcripts` / `/admin`: organize, edit, and review transcripts.
- `Mentions Calendar`: Kalshi prediction-market calendar.
- `Live Market Terminal`: live strikes and order flow.
- `Transcript Editor`: AI speaker isolation and diff.
- `Speaker Notes`: user notes saved per speaker and shown when that speaker is selected.

God Mode / deeper analysis modules observed:
- `Transcript Analyzer`: AI-powered transcript analysis. Link: `https://mentionsterminal.com/transcript-analyzer`.
- `Speech Structures`: AI speech-structure breakdown by transcript. Link: `https://mentionsterminal.com/speech-structures`.
- `Transcribe`: real-time desktop audio transcription. Link: `https://mentionsterminal.com/live-transcribe`.
- `Speaker Socials`: social-account management for speakers. Link: `https://mentionsterminal.com/socials`.
- `Market Frequency`: weekly event frequency by speaker. Link: `https://mentionsterminal.com/market-frequency`.
- `Mesh API Explorer`: test Mesh API endpoints. Link: `https://mentionsterminal.com/mesh-api`.

Transcript/import sources observed:
- YouTube transcript tooling.
- NewsNation shorts.
- FOMC press conferences.
- Federal Reserve open board meetings.
- War.gov / Pete Hegseth press briefings.
- Leavitt Factbase / Karoline Leavitt briefings.
- Trump Mesh events.

Backend entities observed from client code:
- `transcripts`
- `full_transcripts_archive`
- `companies` as speakers
- `speaker_notes`
- `speaker_social_accounts`
- `speaker_social_posts`
- `speaker_social_analyses`
- `speech_structures`
- `kalshi_markets`
- `twitter_market_analyses`
- `live_transcripts`
- `transcribe_sessions`
- `batch_upload_sessions`
- `shared_collections`

Argus usage rule:
- Treat MentionsTerminal as the primary internal source for transcript history, speaker dossiers, and historical speech-pattern checks.
- When analyzing a mention market, first look for the speaker in MentionsTerminal before relying on broad web search.
- Prefer exact transcript hits and speaker-specific base rates over generic topic salience.
- Use `Speech Structures` and transcript sections to distinguish whether a word appears in opening framing, prompted answer, aside, repeated slogan, or closing remarks.
- Use `Speaker Notes` as internal analyst memory, not as independent factual evidence.
- Use `Completed`/historical transcript data for base rates and postmortems when available.

Access note:
- The public shell and client structure were inspected.
- Logged-in visual access through Chrome was confirmed on 2026-05-15.
- Actual user transcript rows were visible through the UI when the logged-in Chrome tab was claimed.
- Do not claim a transcript, speaker note, or AI analysis was checked unless the specific item was actually opened or retrieved.

Logged-in UI details observed:
- `Mentions Analysis` can load a Kalshi mention market and compare all strikes against a selected speaker's transcript set.
- For JD Vance, the UI showed 29 strikes and 16/16 transcripts included.
- The market list displays live strike metadata: yes/no price, volume, 24h volume, open interest, status, expiry, historical mention rate, mention count, and an automated label such as fair / underpriced YES / underpriced NO.
- The word matrix displays strike words across selected transcript dates, with hit rate and total count.
- The search function can expand a strike word into transcript-by-transcript context snippets.
- Full transcript view is available from search results, including transcript text, tags, and detected strike words.
- `Manage Transcripts` showed 321 transcripts and speaker-level transcript counts. Observed examples: Trump 73, Mamdani 28, JD Vance 16, Chair Powell 15, Karoline Leavitt 15, Hakeem Jeffries 12, Kathy Hochul 11, MrBeast 11, Starmer 10.
- On 2026-05-20, logged-in `Manage Transcripts` showed 336 transcripts and Trump 80 transcripts. Tags can be edited from the transcript row by pressing the `+` button in the `Tags` column, entering comma-separated tags, and pressing Enter.
- On 2026-05-20, for the Kalshi market `KXTRUMPMENTION-26MAY22` / `Donald Trump remarks in Suffern, New York`, the best Trump analog transcripts were tagged `Economy` in MentionsTerminal:
  - `President Trump Delivers Remarks on the Economy`
  - `President Trump Delivers Remarks on the Economy, Dec. 19, 2025`
  - `President Trump Delivers Remarks on the Economy, Feb. 19, 2026`
  - `WATCH: Trump delivers remarks at Verst Logistics`
  - `President Trump Participates in The Forum Club of the Palm Beaches Dinner`
  - `President Trump Participates in an Event with Seniors`
  - `President Trump and the First Lady Deliver Remarks at the Congressional Picnic`
  - `Trump participates in a Virginia Telerally`

Argus operational rule for logged-in visual use:
- For any mention market, first inspect `Mentions Analysis` if a relevant market/speaker is available.
- Record transcript coverage count before using base rates.
- Use search snippets to classify mentions by context, not just count.
- Treat automated mispricing labels as a sorting signal, not as analytical conclusion.
- If a word's historical hit rate is high but context is mismatched to the upcoming event format, downgrade its relevance.

## Recurring TV / Show Format Sources

Status: external public and community sources.

Purpose:
- verify whether a scheduled show is live, guest-hosted, prerecorded, replayed, or special programming;
- catch last-mile format changes that official schedule pages may not surface clearly;
- distinguish a normal recurring show from a non-qualifying or altered event under live-only market rules.

Primary source classes:
- Official network schedule and show pages: useful for baseline slot, timezone, show identity, and sometimes episode description.
- TV guide listings: useful for cross-checking schedule and description, but not always proof of live status.
- Official show/social accounts: useful for guest-host, clip, topic, and programming signals.
- Reddit/show communities and forums: C-level evidence, useful for early operational warnings such as "not live", "off tonight", "guest host", or "special programming".
- Bluesky/X/social search: C-level evidence unless from official or accountable accounts; useful for last-mile discovery.

Argus usage rule:
- Treat community/social signals as triggers to re-open rules and seek stronger confirmation, not as final proof by themselves.
- For live-only markets, a credible "not live" note can be more important than any topic analysis. If live eligibility is uncertain, cap confidence or refuse a number.

## Roll Call Factbase Trump Search

Status: external public source / Roll Call Factba.se transcript search.

Observed on: 2026-05-21 through the connected Chrome Codex extension.

Primary page:
- `https://rollcall.com/factbase/trump/search/`
- Page title: `Factbase search - Roll Call`.
- The page is a WordPress shell with an Alpine-style search component.
- `window.person = 'trump'`.
- The visible app is a search/browse UI for Donald Trump Factba.se records.

Visible UI structure:
- Top Factba.se navigation includes `Donald Trump`, `Donald Trump Tweets`, `White House Calendar`, `White House Releases`, `State of the Union`, `Press Seating Chart`, `Epstein Files`, `Blog`, `Joe Biden`, `Kamala Harris`.
- Main search screen shows a person selector area: `Joe Biden`, `Kamala Harris`, `Donald Trump`.
- Main heading for this page: `Donald Trump`.
- Left filter column on desktop; on smaller/mobile layout it is controlled by the filter icon.
- Main result column shows records with:
  - media marker such as `Video` or `Document` in the UI;
  - place, e.g. `New London, CT`;
  - date;
  - `View Transcript` link;
  - record title;
  - snippet text when a search query is active.

Observed filters:
- Search input: `input#search`, parameter name `q`, placeholder `Search...`.
- Event Type checkboxes are generated from the currently loaded result set, not from a fixed global list.
- Observed event types across searches/browse states: `Interview`, `Press Briefing`, `Press Gaggle`, `Remarks`, `Speech`, `Vlog`, `Op-Ed`.
- Media checkboxes are generated from the currently loaded result set.
- Observed media values for API use: `Video`, `Text`.
- UI may label text records as `Document`, but the API filter value that worked was `media=Text`; `media=Document` returned zero in testing.
- Sort dropdown:
  - `asc` = oldest first.
  - `desc` = newest first.
  - The dropdown can visually default to `Sort By: Oldest` even when the initial result order is newest/default. Treat the API response order as authoritative, not the initial visual select label.
- `Clear` resets selected filters/search state in the UI.

Search behavior:
- Typing in `input#search` triggers a debounced search after about 200 ms.
- The page resets to page 1 and scrolls back to the top after a new search.
- The browser URL did not reliably update during observed UI search/filter changes; do not depend on the visible URL as state.
- Query search returns paragraph-level hits:
  - result objects include `record_id`, `sequence`, `text`, transcript/video time fields when available, and `factbase_url` with `#sequence`.
  - snippets highlight exact query text in the UI.
- Browse/no-query results return document-level records:
  - result objects have `document_id` and `factbase_url` without a paragraph anchor;
  - no query text snippet is required.

Actual data API:
- The working data source observed was:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php`
- The Roll Call WordPress endpoint existed in page code:
  - `https://rollcall.com/wp-json/factbase/v1/search?...`
  - In testing, this endpoint returned zero usable results for the same basic Trump searches, so it should not be the first parser target unless revalidated.

Working API examples:
- Browse newest:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?page=1&sort=desc`
- Browse oldest:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?page=1&sort=asc`
- Search exact word:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?q=tariff&page=1&sort=desc`
- Filter event type:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?type=Speech&page=1`
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?type=Press%20Gaggle&page=1`
  - Multiple types work comma-separated, e.g. `type=Speech,Remarks`.
- Filter media:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?media=Video&page=1`
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?media=Text&page=1`
- Combine filters:
  - `https://api.factsquared.com/json/factba.se-trump-20240623.php?q=tariff&type=Interview&page=1&sort=desc`

API pagination:
- Response has `meta` and `data`.
- Observed `meta` fields:
  - `records_matched`
  - `records_total`
  - `page`
  - `total_pages`
  - `results_per_page`
  - `milliseconds`
- Observed default `results_per_page`: 40.
- Observed browse total on 2026-05-21:
  - `records_matched`: 5837
  - `total_pages`: 146
- Observed `q=tariff` total on 2026-05-21:
  - `records_matched`: 4646
  - `total_pages`: 117

Important response fields:
- Common fields:
  - `candidate`
  - `date`
  - `document_id`
  - `record_id` for paragraph/search hits
  - `sequence` for paragraph/search hits
  - `factbase_url`
  - `image_url`
  - `record_type`
  - `media_type`
  - `place`
  - `record_title`
  - `slug`
  - `source`
  - `speaker` / `speaker_id`
  - `type`
  - `url`
  - `version`
  - `version_number`
  - `video_url`
  - `location`
- Search-hit records can include:
  - `text`
  - `word_count`
  - `video.time_start`
  - `video.time_end`
  - `video.vimeo_start`
  - `transcript.text`
  - `transcript.time_start`
  - `transcript.time_end`
  - `transcript.duration_seconds`
- Browse records can include document-level metadata:
  - `document.speakers`
  - `document.entities`
  - `document.topics`
  - `document.duration`

Infinite scroll behavior:
- First page loads 40 result links.
- A `.sentinel` element sits after the results.
- The app uses `IntersectionObserver` on `.sentinel`.
- When the sentinel intersects and `hasMorePages` is true, the app increments `page` and appends another 40 records.
- Observed Chrome scroll test:
  - before bottom: 40 unique transcript links;
  - after reaching bottom/sentinel: 80 unique transcript links;
  - document height increased after the next page appended.

Parser discipline:
- Prefer API pagination over visual infinite scroll.
- Correct parser loop:
  - request page 1 with explicit `q`, `type`, `media`, and `sort`;
  - read `meta.total_pages`;
  - iterate `page=1..total_pages`;
  - dedupe by `record_id` when present, otherwise `document_id + factbase_url`;
  - persist each page before requesting the next page;
  - log `records_matched`, `total_pages`, and the last saved id/title/date per page.
- Do not send `media=all` or `type=all`; these produced zero results in the Roll Call WordPress endpoint and are not needed for the Factsquared API. Omit empty filters instead.
- If using browser scroll for manual capture, do not jump straight to very large scroll positions.
  - Scroll until near the bottom of the current page.
  - Wait until the count of transcript links grows by 40 or `document.documentElement.scrollHeight` increases.
  - Save the current batch before the next scroll.
  - Track the last visible `factbase_url` or `document_id`; if the count stops increasing before `total_pages`, switch to API pagination.
- UI filters are derived from loaded data, so scrolling/searching can change which filter checkboxes are visible. For comprehensive scraping, use API parameters rather than relying on visible filter options.

Argus usage rule:
- Treat Roll Call Factbase as a strong transcript/source map candidate, but still verify exact transcript context before using a hit as evidence in mention-market analysis.
- For mention-market base rates, record whether a hit is document-level browse metadata or paragraph-level query evidence.
- For exact wording markets, use `q=` search hits and inspect surrounding transcript context, not only `records_matched`.
