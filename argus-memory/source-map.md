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
- `Transcript Analyzer`: AI-powered transcript analysis.
- `Speech Structures`: AI speech-structure breakdown by transcript.
- `Transcribe`: real-time desktop audio transcription.
- `Speaker Socials`: social-account management for speakers.
- `Market Frequency`: weekly event frequency by speaker.
- `Mesh API Explorer`: test Mesh API endpoints.

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

Argus operational rule for logged-in visual use:
- For any mention market, first inspect `Mentions Analysis` if a relevant market/speaker is available.
- Record transcript coverage count before using base rates.
- Use search snippets to classify mentions by context, not just count.
- Treat automated mispricing labels as a sorting signal, not as analytical conclusion.
- If a word's historical hit rate is high but context is mismatched to the upcoming event format, downgrade its relevance.
