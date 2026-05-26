# Mention Market Operating Rules

Use this as the canonical order of operations for Argus mention-market work. Older lessons remain active, but this file defines priority when rules conflict.

## Prime Directive

Do not analyze what someone might say until the event is confirmed to qualify.

For live-only or speaker-specific markets, eligibility can dominate every strike. If the event fails the rules gate, the analysis is rules/eligibility, not speech pattern.

## Order Of Operations

### 0. Eligibility Gate

Check before topic, transcripts, or fair range:

- required speaker;
- required event/show;
- live versus prerecorded requirement;
- guest host or substitute speaker risk;
- replay, archival, clip-package, promo, or quote risk;
- holiday or special-programming risk;
- source that proves or challenges eligibility;
- what the rules say happens if eligibility fails.

Stop condition: if eligibility fails and rules imply NO/non-qualifying, do not continue into topical strike analysis.

### 1. Event Identity And Format

Fix the event before analyzing words:

- person/speaker;
- event name;
- date and timezone;
- format bucket: prepared remarks, interview, Q&A, debate, rally, ceremony, TV show, sports broadcast, earnings call, promo;
- expected duration;
- scriptedness;
- host/interviewer/moderator;
- audience and communicative purpose.

If the format is unclear, confidence is capped.

### 2. Source Discipline

Classify evidence before using it:

- A-level: full video/audio, official transcript, official source.
- B-level: reputable media with direct quotes and links.
- C-level: clips, social posts, Reddit/community notes, aggregators.
- D-level: rumors, anonymous claims, unsourced summaries.

C-level sources can trigger action, especially format/rules checks, but they do not become proof unless corroborated or directly tied to an accountable account.

### 3. Internal Tool Pass

For substantial analyses:

- use MentionsFlow for market metadata, event type, source-check status, related strikes, completed-market hooks;
- use MentionsTerminal for transcript coverage, word matrix, exact hits, context snippets, full transcript context, and speaker notes;
- record coverage count before relying on base rates;
- treat automated labels as sorting signals only.

Do not claim a tool, transcript, source check, or note was reviewed unless it was actually opened.

### 4. Wording Path

For each strike, build the path:

```text
event format -> speech phase -> communicative task -> topic -> natural formulation -> exact strike
```

If the path cannot be written clearly, there is no analysis yet, only association.

Classify the path:

- embedded;
- default speaker language;
- current agenda insert;
- prompt-dependent;
- aside/anecdote;
- residual salience.

### 5. Transcript And Base-Rate Discipline

Exact hits matter more than generic topic salience, but only if the sample matches:

- same speaker;
- same or adjacent format;
- same phase;
- comparable duration;
- comparable interviewer/channel/audience;
- fresh enough for current incentives.

Classify hits as prepared, unprompted, prompted, Q&A, aside, quote, replay, closing, or promo. Raw counts without context are not a conclusion.

### 6. Current Context And Consensus

Separate:

- fresh catalyst;
- official/promo framing;
- obvious consensus source;
- what the market likely already knows;
- where consensus overextends from topic to exact wording.

Question to ask: is this our edge, or just the public reason for the current price?

### 7. Fair Range

Use the practical formula:

```text
FV = Path Activation x Exact Wording Conditional x Countability
```

Keep components separate:

- path activation: topic/block appears in this format;
- exact wording conditional: the required word appears if the block appears;
- countability: the right speaker/content is counted under rules.

Prefer ranges over points. Refuse a number if eligibility, format, source freshness, speech pattern, or edge type is not defined well enough.

### 8. Price And Edge

Fair value is not a trade decision.

Always classify edge type:

- research;
- segmentation;
- rules;
- speed;
- flow;
- liquidity;
- tooling;
- temperament;
- none.

If price sits inside the honest uncertainty range, there is usually no analytical edge. A likely event can still be overpriced; an unlikely event can still be underpriced.

### 9. Last-Mile Checks

For recurring TV/show markets, run format checks close to air:

- 6-8h before: official schedule, holiday risk, show page, episode description;
- 2-4h before: Reddit/community notes, show forums, social search for "not live", "off tonight", "guest host", "special programming", "prerecorded";
- 30-60m before: updated TV guide, official socials, livestream status, guest-host clues.

For political events, check schedule conflicts, location, pool notes, official livestream pages, and whether Q&A is expected.

For sports announcer markets, check broadcaster, feed, announcer assignment, game state risks, and whether the relevant feed is the resolving source.

### 10. Live Update Plan

Before the event, define:

- what would move the range upward;
- what would move it downward;
- what invalidates the thesis;
- what content must not be counted;
- how to separate speaker, host, replay, quote, promo, and archival material.

Do not defend an old fair range after new live evidence changes the event mode.

### 11. Postmortem And Memory

After resolution, classify the miss or hit:

- eligibility/live-status;
- rules/countability;
- format/duration;
- speaker separation;
- exact wording/substitute;
- prompt/context;
- source freshness;
- historical sample mismatch;
- consensus/price;
- live update;
- variance inside a reasonable range.

Save only reusable lessons. A memory update should improve future decisions, not just archive a result.

## Fast Brief Minimum

When time is short, still cover these seven items:

1. Eligibility: qualifies / uncertain / fails.
2. Format: what kind of event this is.
3. Strike: exact word and required speaker.
4. Path: how the word naturally appears.
5. Main failure mode.
6. Edge type.
7. Fair range or no-number reason.

If any of items 1-4 is missing, do not give a confident number.
