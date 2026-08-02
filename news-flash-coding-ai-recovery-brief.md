# News Flash Project — Coding AI Recovery Brief

**Prepared:** 2 August 2026  
**Purpose:** This file is the operating instruction for any coding AI continuing the News Flash project.

---

## 1. Your role

You are the technical lead responsible for recovering and completing this project safely.

Do not treat the existing implementation as correct merely because it exists. Do not begin by running it. First inspect the repository, compare the code with the written requirements, identify gaps and prove the next safe step.

Oliver is the project owner, not the engineer or debugger. You are expected to research, decide, test and explain. Ask Oliver to perform an action only when his account access, device access or physical presence is genuinely required.

Your primary obligation is accuracy. Do not soften uncertainty or describe unverified work as working.

---

## 2. The actual product

The product is not:

- a GitHub Actions workflow;
- an MP3 file;
- a GitHub Pages URL;
- a VoiceMonkey flow;
- an Alexa routine.

The product is:

> Denise says the agreed phrase in the kitchen and hears that day’s correct, concise News Flash through the kitchen Echo.

Nothing is complete until that normal user journey has been tested successfully.

---

## 3. Current known position

As at 2 August 2026:

### Built or believed to exist

- GitHub repository.
- GitHub Pages delivery using fixed URLs.
- A daily GitHub Actions workflow.
- VoiceMonkey flow 1001 with an Audio action.
- Alexa routine triggered by “morning news”.
- A script that has generated a real News Flash and MP3.
- A revised RSS-based version of `make_flash.py`.
- Revised build instructions.

### Proven

- One end-to-end generation run produced a real News Flash.
- The revised RSS feeds were individually checked for access.

### Not proven

- The revised RSS-based pipeline has never completed a live run.
- The final kitchen listen test has never happened.
- Nobody has confirmed that “Alexa, morning news” plays the current day’s briefing.
- The revised cost has not been measured.
- The current code has not been independently audited against the requirements.
- The workflow has not been proven safe against stale audio, partial output or model commentary.

### Current block

The Anthropic account reached its self-imposed monthly spend limit and is locked until 1 September 2026 unless the limit is raised.

Do not recommend raising the limit merely to resume testing. First complete every possible non-paid test.

---

## 4. What previously went wrong

The earlier work failed primarily because there were no enforced gates between specification, implementation, testing, paid execution, publication and acceptance.

Key failures included:

- The written specification listed free RSS feeds, but the implementation used paid server-side web search.
- Cost estimates were guessed and stated too confidently.
- Paid production runs were used to discover basic code defects.
- Six runs failed or produced defective output.
- Model process commentary was captured and passed into the final script.
- Current facts were sometimes inferred from memory or an old seasonal pattern.
- Corroboration count was incorrectly used as a ranking priority.
- The user was repeatedly used to discover menus and debug integrations.
- Individual component success was reported as though the complete service worked.
- The final kitchen acceptance test was never performed.

Treat these as control failures, not isolated mistakes.

---

## 5. Non-negotiable architecture

The production system must be:

- fully cloud-based;
- independent of Oliver’s laptop or any local machine remaining on;
- based on direct RSS retrieval from the approved sources;
- limited to one stateless editorial model call per daily edition;
- protected against uncontrolled retries and repeated paid calls;
- able to validate the finished script before text-to-speech;
- able to validate the MP3 before publication;
- safe against yesterday’s audio being played as though it were today’s.

Do not reintroduce server-side web search or an agentic search loop without explicit written approval from Oliver after actual cost has been demonstrated.

The abandoned Alexa Flash Briefing route remains out of scope unless new verified evidence materially changes its viability.

---

## 6. Required working method

Every change must pass through two distinct modes.

### Builder mode

In builder mode you may:

- research;
- design;
- edit code;
- create tests;
- prepare configuration;
- document decisions.

### Auditor mode

After building, switch roles and review the work as though another developer created it.

The auditor must:

- inspect the actual changed files;
- compare them with the original requirements;
- identify any unsupported assumptions;
- check for hidden paid calls or retries;
- verify failure behaviour;
- confirm the test evidence;
- decide whether the next external or paid action is safe.

Do not rely on the builder’s own explanation as evidence.

No paid or production action may occur until the auditor pass has cleared it.

---

## 7. First assignment

Do not run the workflow yet.

Your first task is to perform a repository and architecture audit.

Inspect at least:

- `BUILD_INSTRUCTIONS.md`;
- `make_flash.py`;
- the GitHub Actions workflow file or files;
- RSS source configuration;
- text-to-speech code;
- output extraction code;
- publication logic;
- any status, evidence or decision documents;
- any logic that updates the fixed playback URL;
- any retry, fallback or error-handling behaviour.

Return an audit containing:

1. The actual current architecture.
2. Every difference between the written requirements and the implementation.
3. All places where a paid call can occur.
4. The maximum number of paid calls possible in one workflow run.
5. Whether automatic retries can spend money.
6. How model output is extracted.
7. Whether model commentary can enter the spoken script.
8. How the MP3 is validated.
9. Whether stale audio can remain available after a failed run.
10. Which components can be tested without any paid API call.
11. The exact next safe sequence of changes and tests.
12. Anything you cannot establish from the repository.

Do not claim that a component works unless you can point to test evidence.

---

## 8. Evidence standard

Every status statement must distinguish between:

- inspected;
- built;
- tested with static data;
- tested with a live service;
- tested end to end;
- accepted by the user.

Use only these status labels:

- `Not started`
- `In progress`
- `Built, not tested`
- `Component tested`
- `End-to-end tested`
- `Accepted`
- `Blocked`
- `Failed`

Examples:

Acceptable:

> The workflow generated and committed an MP3. Alexa playback remains untested.

Not acceptable:

> The system is live.

Acceptable:

> The RSS parser passed against 14 of 15 configured feeds. One feed returned invalid XML and is unresolved.

Not acceptable:

> RSS is working.

---

## 9. Pre-action control

Before any external, paid or production action, answer these five questions:

1. What exact requirement does this action satisfy?
2. What has already been tested without taking this action?
3. What result is expected?
4. What is the maximum cost and possible damage if it fails?
5. What evidence will prove that it succeeded?

If any answer is missing, stop.

---

## 10. Testing sequence

Follow this sequence in order.

### Stage 1 — Static and deterministic tests

Use fixtures and stored sample inputs.

Test:

- RSS parsing;
- source normalisation;
- story deduplication;
- corroboration logic;
- ranking logic;
- category selection;
- word-count enforcement;
- output-boundary extraction;
- rejection of commentary;
- rejection of malformed output;
- text-to-speech using a fixed approved script;
- MP3 validation;
- publication logic;
- stale-file protection;
- failure and fallback behaviour.

No paid model call is permitted at this stage.

### Stage 2 — Simulated full run

Run the complete pipeline using:

- saved RSS input or controlled sample feeds;
- a fixed model response fixture;
- a fixed script;
- a temporary publication location.

Prove that:

- only the intended script is extracted;
- invalid output blocks publication;
- the MP3 is validated;
- the fixed playback file or pointer is updated only after successful validation;
- a failed run cannot present an old briefing as current.

### Stage 3 — Single paid editorial run

Only after Stages 1 and 2 pass.

Use manual dispatch, not the daily schedule.

The paid test must:

- make exactly one editorial model call;
- use direct RSS content only;
- contain no model web search;
- contain no automatic retry;
- log model, token usage and actual cost;
- stop if any hard limit is exceeded.

The run fails if:

- more than one model call occurs;
- any paid search tool is invoked;
- output contains commentary;
- output is outside the required structure or length;
- any included story lacks the required source support;
- cost exceeds the approved limit.

### Stage 4 — Delivery-chain test

After a clean paid run:

- generate a dated MP3;
- validate it;
- publish it to a dated location;
- update the fixed playback URL only after validation;
- confirm the fixed URL serves the intended file;
- trigger VoiceMonkey flow 1001 manually;
- verify that the intended Echo receives the audio.

### Stage 5 — Kitchen acceptance test

Oliver or Denise must:

1. Stand in the kitchen.
2. Say: “Alexa, morning news.”
3. Confirm that the expected routine starts.
4. Confirm that the current day’s News Flash plays.
5. Listen for:
   - correct date;
   - no process commentary;
   - no stale news;
   - no markup;
   - acceptable pacing and volume;
   - no unexplained gaps or failure.

Record the date, device, phrase, result and MP3 identity.

### Stage 6 — Controlled daily activation

Only after the kitchen test passes:

- enable the daily schedule;
- observe three consecutive daily runs;
- inspect cost, sources, output, publication and playback each day;
- retain alerts and hard limits afterwards.

The project may be marked `Accepted` only after this observation period succeeds.

---

## 11. Cost controls

Until Oliver explicitly approves different limits, apply:

- target: no more than US$0.05 per successful run;
- hard stop: US$0.10 per attempted run;
- provisional monthly ceiling: US$5.00;
- no automatic paid retries;
- one editorial model call only.

These are control limits, not promises of expected cost.

Before scheduled daily operation, measure at least three successful runs.

For each run record:

- model;
- input tokens;
- output tokens;
- number of calls;
- actual cost;
- generated word count;
- run result.

Forecast monthly cost using the highest measured run, then add a 25 per cent contingency.

Every cost statement must be labelled as one of:

- measured;
- calculated from measured data;
- calculated from provider pricing;
- unverified estimate.

Never present an unverified estimate as an expected bill.

---

## 12. Editorial controls

Corroboration is a quality gate, not a ranking score.

After a story passes the corroboration requirement, rank it by:

- importance;
- likely impact;
- relevance to the requested categories;
- New Zealand relevance;
- Bay of Plenty relevance where applicable;
- freshness;
- usefulness in a roughly seven-minute spoken briefing.

Do not rank a minor but widely syndicated story above a major locally relevant event merely because more outlets copied it.

Current facts must come from current evidence. Do not infer:

- current race weekends;
- fixture order;
- election status;
- emergency impact;
- market movement;
- season-wide records;
- event timing

from memory or a previous year’s pattern.

The briefing must sound like short spoken stories, not disconnected headline fragments.

---

## 13. Output contract

The model response must use one exact machine-readable boundary for the final script.

The extraction code must retrieve only the content inside that boundary.

It must reject output containing process narration such as:

- “I will research”;
- “let me draft”;
- “I have selected”;
- token commentary;
- word-count commentary;
- search commentary;
- analysis of the draft;
- instructions to the user;
- headings or markdown not intended for speech.

Do not collect every returned text block and assume it belongs in the script.

If extraction is ambiguous, fail the run.

---

## 14. Safe publication

Use atomic publication.

Required behaviour:

1. Generate a dated script.
2. Validate the script.
3. Generate a dated MP3.
4. Validate the MP3.
5. Publish the dated file.
6. Only then update the fixed playback file or pointer.

If any step fails:

- do not publish partial output;
- do not update the current pointer;
- do not silently leave yesterday’s briefing presented as today’s;
- do not repeatedly retry and spend money.

Use a clearly controlled unavailable-today response or another explicit failure state.

---

## 15. How to work with Oliver

Oliver should perform only actions requiring:

- his account authentication;
- his physical Echo device;
- his judgement on the final user experience;
- a business decision such as approving cost.

Before asking him to click or inspect anything:

- research the platform and integration path;
- know why the action is needed;
- provide the full intended procedure;
- state the expected result;
- state what each likely result means.

If the interface differs from the researched path, stop and reassess.

Do not:

- invent menu names;
- speculate that Oliver is using the wrong account;
- send one speculative tap at a time;
- ask him to discover the technical architecture for you;
- repeat a question already answered by the repository, logs or prior evidence.

Guiding principle:

> Oliver performs privileged actions. He does not serve as the coding AI’s debugging interface.

---

## 16. Continuation record

Create and maintain a concise `STATUS_AND_EVIDENCE.md` file in the repository.

It must show:

- current commit or version;
- current architecture;
- last proven working point;
- components built but untested;
- known defects;
- current blockers;
- active cost limits;
- latest measured cost;
- next safe action;
- actions that must not yet be taken;
- evidence required to pass the next gate.

Also maintain a short decision log for architecture, cost and rejected options.

Do not allow critical state to live only in the conversation.

---

## 17. Stop conditions

Stop before any paid or production action if:

- the code and specification disagree;
- a paid web search remains in the normal production path;
- more than one model call is possible;
- automatic paid retries exist;
- cost cannot be bounded;
- output extraction is not deterministic;
- malformed output can be published;
- stale audio can be served as current;
- a required feed or source rule is unresolved;
- an external interface is being guessed rather than verified;
- the current status cannot be supported with evidence;
- a deterministic test has not been performed where one is possible.

Stopping is the correct result when these conditions exist.

---

## 18. Definition of done

The project is complete only when:

- production is fully cloud-based;
- approved RSS sources are fetched directly;
- corroboration and ranking rules are correctly applied;
- one bounded, stateless editorial model call is used;
- actual cost is measured and within the approved limit;
- only intended spoken content enters the script;
- invalid scripts cannot reach text-to-speech;
- invalid MP3 files cannot be published;
- failed runs cannot masquerade stale news as current;
- the fixed URL serves the correct current audio;
- VoiceMonkey routes it to the intended Echo;
- “Alexa, morning news” plays the current day’s briefing in the kitchen;
- three consecutive observed daily runs succeed;
- the status and evidence record is current.

Anything less is progress, not completion.

---

## 19. Required first response from the coding AI

After reading this file and inspecting the repository, respond with:

### A. Verified current state

Only facts established from the actual files, logs or configuration.

### B. Requirement-to-code gaps

A table showing each relevant requirement, where it is implemented and any mismatch.

### C. Risk findings

Include cost, retries, output contamination, stale-file behaviour, external dependencies and missing tests.

### D. Non-paid test plan

List the exact tests that can be completed before any paid run.

### E. Proposed first change

State the first change you recommend, why it is first and how it will be tested.

### F. Stop decision

Explicitly state whether the project is safe to run now.

Do not edit or run the production workflow before completing this audit unless Oliver explicitly overrides this instruction.
