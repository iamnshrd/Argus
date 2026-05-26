# Mention Market Wording Path and FV Protocols

Use this as active methodology for pre-event mention-market analysis. The goal is to prevent topic salience from being mistaken for exact-word probability.

## 1. Wording Path Protocol

Purpose: understand the concrete route by which a specific word or phrase can appear in a specific speaker's speech at a specific event.

### Step 0: Verify Event Eligibility

Before analyzing wording paths, verify that the event itself qualifies under the market rules:

- required speaker;
- live versus prerecorded requirement;
- show/event identity;
- guest host risk;
- holiday or special-programming risk;
- replay / archival / clip package risk;
- content that counts and content that does not count.

If the market is live-only and the event is not live, topic analysis stops. The edge is rules/eligibility, not speech pattern.

Core formula:

```text
event format -> speech phase -> communicative task -> topic -> natural formulation -> exact strike
```

If the route cannot be written clearly, there is no analysis yet. There is only association.

### Step 1: Fix The Event Format

Before analyzing strikes, record:

- speaker;
- event;
- format: speech, interview, press gaggle, rally, debate, ceremony, signing, policy event, town hall;
- whether Q&A is expected;
- expected duration;
- audience;
- scriptedness;
- main communicative purpose.

Main question:

```text
Does the event itself push the speaker toward this topic, or does the topic need an outside trigger?
```

### Step 2: Split The Event Into Phases

Do not analyze the event as one block. Map likely phases:

- opening;
- thanks / acknowledgements;
- prepared remarks;
- policy pitch;
- self-congratulation;
- attack block;
- audience riff;
- interview answer;
- Q&A / prompted response;
- closing;
- archival / replayed / quoted material, if applicable.

For each strike, ask:

```text
In which phase can this word naturally appear?
```

If there is no natural phase, the strike is weak even if the broad topic is salient.

### Step 3: Build The Wording Path

For each strike, write the path:

```text
format -> phase -> speech task -> topic -> natural wording -> exact strike
```

Example:

```text
Congressional ceremony -> thanks / unity -> both parties -> "Republicans and Democrats" -> Democrat
```

Short paths are stronger. Long paths requiring several transitions, a question, or a random aside should be discounted.

### Step 4: Classify The Path

Use five levels:

| Level | Type | Meaning |
|---|---|---|
| 1 | Embedded | The word is built into the event, audience, role, or room. |
| 2 | Default speaker language | The word is part of the speaker's normal brag, attack, or stump vocabulary. |
| 3 | Current agenda insert | The topic is live, but not forced by the format. |
| 4 | Prompt-dependent | The word likely needs a question, conflict, interviewer, or media trigger. |
| 5 | Aside / anecdote | The word requires a joke, personal story, guest, or digression. |

Common market error: treating Level 3 as Level 1, or Level 5 as Level 2.

### Step 5: Separate Topic From Exact Wording

For every strike, answer separately:

- Is the topic likely?
- Is the exact wording natural?
- What substitutes could the speaker use instead?
- Does the speaker habitually use this exact word?
- Does the word appear unprompted, or mostly when prompted?

Rule:

```text
topic YES != wording YES
```

### Step 6: Check Transcript Evidence

Search exact wording first. Then search adjacent variants:

- synonyms;
- related entities;
- common speaker phrasings;
- alternate wording paths.

Classify every meaningful transcript hit:

- prepared remarks;
- opening statement;
- interview answer;
- prompted response;
- Q&A;
- rally repetition;
- aside;
- closing;
- archival / replayed / quoted material.

Raw counts without context are not a conclusion.

### Step 7: Segment By Format

Broad transcript hit rate is background only. Prioritize:

- same or similar format;
- similar audience;
- similar duration;
- similar speech phase;
- similar scriptedness;
- same interviewer / venue / broadcaster, if relevant.

A rally hit does not automatically transfer to a ceremony. A prompted interview answer does not automatically transfer to prepared remarks.

### Step 8: Build A Trigger Map

For each strike, identify the trigger:

- audience;
- fresh news;
- interviewer question;
- hostile press;
- policy rollout;
- personal story;
- guest in the room;
- scripted talking point;
- standard stump riff;
- closing applause line.

If the trigger is absent, downgrade the path.

### Step 9: Write Bull And Bear Paths

For each important strike:

Bull path:

```text
What concrete sequence leads to the exact wording?
```

Bear path:

```text
How can the topic appear without the exact wording?
```

This protects against turning topic salience into exact-word probability.

### Step 10: Evaluate Current Agenda

Separately from transcript history, ask:

- Is the topic currently active?
- Is the speaker raising it unprompted recently?
- Is there a 24-72 hour catalyst?
- Does the event format allow that catalyst to enter?

Current agenda can strengthen Level 3. It does not turn Level 3 into Level 1 by itself.

### Step 11: Market Steelman

Before concluding, ask:

- What obvious source is the market likely using?
- Is the price just broad frequency or headline salience?
- Where could the market be right?
- Where could it be overextending: format, exact wording, prompt-dependence, stale transcripts, or residual salience?

### Step 12: Final Strike Classification

Use this template:

```text
Strike:
Path level:
Primary path:
Likely phase:
Trigger:
Exact wording naturalness:
Substitutes:
Transcript support:
Format match:
Bull path:
Bear path:
Main failure mode:
Status: alive / semi-alive / stale / not ready
```

## 2. FV Protocol For Mention Strikes

Purpose: estimate fair value for the exact strike, not the broad topic and not the desire to find edge.

FV answers:

```text
How often should this wording path actually resolve YES in this format?
```

### Step 1: Refuse A Number Until The Setup Exists

Do not give FV until these are defined:

- exact strike;
- required speaker;
- event format;
- Q&A / no Q&A;
- expected duration;
- wording path;
- transcript support;
- current agenda catalyst;
- main failure mode.

If these are missing, a number is false precision.

### Step 2: Start With The Strike Bucket

Start from the strike type, not intuition:

| Type | Base logic |
|---|---|
| Embedded | Word is built into event, audience, or role. |
| Default speaker language | Word is part of normal speaker vocabulary. |
| Current agenda | Topic is live, but not required by format. |
| Prompt-dependent | Needs question, conflict, or media trigger. |
| Aside / anecdote | Needs digression, joke, personal story, or guest. |
| Residual salience | Recent word, but current format does not naturally pull it in. |

### Step 3: Use The Clean Base Formula

Preferred practical formula:

```text
FV = Path Activation x Exact Wording Conditional x Countability
```

Where:

```text
Path Activation = format fit + event phase + current agenda + speaker incentive + duration
```

This avoids double-counting format risk.

More detailed version, only if factors are not already included:

```text
FV =
P(topic/block appears before format)
x Format Fit Modifier
x P(exact wording | topic/block)
x Countability Modifier
```

Do not mix the two versions casually. If format is already inside Path Activation, do not also apply a heavy separate format discount.

### Step 4: Separate The Components

For every strike, estimate:

Topic / path activation:

- How likely is the speaker to enter this topic or block?
- Does the format itself create the path?
- Does the speech have a natural phase for it?

Exact wording conditional:

- If the topic appears, how likely is this exact word?
- Is it a stable speaker phrase?
- Are substitutes more natural?

Countability:

- Will the required speaker say it?
- Is the content likely to be counted?
- Is there replay / quoted / intro ambiguity?

### Step 5: Use Transcripts As Calibration, Not Automation

Classify evidence:

- exact hits;
- adjacent hits;
- same-format hits;
- recent hits;
- prompted versus unprompted;
- prepared versus riff;
- one-off versus recurring.

Strongest evidence:

```text
recent + exact + same format + unprompted
```

Weakest evidence:

```text
old + adjacent + different format + prompted
```

### Step 6: Prefer Ranges Over Points

Default probability bands:

| Range | Meaning |
|---|---|
| 0-5% | Almost no path; only accident / rules tail. |
| 5-15% | Weak aside, stale topic, or unusual trigger required. |
| 15-30% | Semi-live, but detour or exact-word risk is high. |
| 30-45% | Live path, but serious format or substitute risk. |
| 45-60% | Strong path and reasonable format, but not embedded. |
| 60-75% | Very strong recurring or default path. |
| 75%+ | Embedded or nearly forced; still check rules and format. |

For mention markets, 70%+ should be rare. It requires a near-forced path.

### Step 7: Keep Topic Probability And Exact Probability Separate

Use this structure:

```text
Topic probability:
Exact wording conditional:
Final FV:
```

Example logic:

```text
Economy appears: 60%
"stock market" if economy appears: 40-50%
Final FV before other adjustments: about 24-30%
```

Do not price the exact strike at the broad topic probability.

### Step 8: Apply Modifiers

Increase FV for:

- same-format exact hit;
- recent unprompted exact use;
- word in prepared talking point;
- topic-native event;
- Q&A or interviewer likely to prompt;
- audience / location directly pulls the word;
- fresh catalyst the speaker is already raising.

Decrease FV for:

- word appears mostly when prompted;
- recent hits were asides;
- short or scripted format;
- topic is not event-native;
- many substitutes;
- market wording is unnatural for speaker;
- evidence comes from rally/interview while current event is ceremony/prepared remarks.

### Step 9: List Failure Modes

Before final FV, write:

- topic does not appear;
- topic appears, but different wording;
- word is said by another person;
- word appears in replay / intro / quote but does not count;
- event is shorter than expected;
- speaker stays scripted;
- fresh agenda is displaced by event ceremony.

If failure modes are numerous and realistic, lower FV.

### Step 10: Final FV Template

```text
Strike:
Path level:
Path activation:
Exact wording conditional:
Countability:
Transcript support:
Same-format support:
Main substitutes:
Main failure mode:
FV range:
Center, if justified:
Confidence:
Why not higher:
Why not lower:
```

### Step 11: Price Discipline

FV is not an entry price. It is the center of an uncertainty estimate.

Do not treat market price near FV as edge. Compare price to the honest FV range, not only the center.

Analytical rule:

```text
Market price near FV = watch / no edge, unless another edge type exists.
```

Another edge type can be:

- flow;
- speed;
- rules;
- liquidity;
- tooling;
- superior source work;
- better format segmentation.

For a price below FV center, ask:

```text
Is the market below the lower bound of the honest FV range after costs, spread, uncertainty, and model error?
```

If not, the difference may be noise rather than edge.

Exit logic should be analytical, not automatic:

- thesis invalidates;
- new information changes FV;
- market reaches fair range;
- event format changes;
- better source appears;
- live evidence opens or closes the wording path.

No buy / sell / hold recommendation follows from FV alone.
