# MaplePulse Eval Study

Tracking document for all evaluations before handoff to testing team.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| [ ] | Not started |
| [~] | In progress |
| [x] | Complete |

---

## EVAL-01: Brand Voice Consistency

**Status:** [x] Implemented

**What:** Does the optimized message preserve the original brand voice, tone, and personality?

**How:** In-app thumbs up/down on the optimized message. Tester reads the original, reads the optimized, and votes whether the brand voice was preserved.

**Tracking:**
- Log each vote (thumbs up/down) with: run ID, original message, optimized message, tester ID, timestamp
- Store in backend (same pattern as panel/reaction removal tracking)

**Pass criteria:** >80% thumbs-up rate across test runs

**Red flags to watch for:**
- Optimizer strips personality and outputs generic corporate copy
- Optimizer changes tone (e.g., playful original becomes formal optimized)
- Optimizer adds marketing jargon not in the original

---

## EVAL-02: Optimization Length Drift

**Status:** [x] Implemented

**What:** Is the optimized message significantly longer than the original?

**How:** Automated check — compare word count of original vs optimized message.

**Metrics:**
- Word count ratio: `optimized_words / original_words`
- Character count ratio: `optimized_chars / original_chars`
- Sentence count ratio: `optimized_sentences / original_sentences`

**Pass criteria (tiered by original length):**
- Under 30 words: ratio <= 2.0x (short copy needs room to add specificity)
- 30-75 words: ratio <= 1.5x
- 75+ words: ratio <= 1.3x

**Tracking:** Log per run: original word count, optimized word count, ratio, applicable threshold

---

## EVAL-03: Panel Selection Stability

**Status:** [x] Implemented

**What:** Track every time a panel member is removed/crossed off at the panel selection step. High removal rates mean panel selection is producing poor fits.

**How:** In-app tracking — every time a tester removes a persona from the panel, log it.

**What to log per removal:**
- Run ID
- Persona ID
- Persona summary (age, province, occupation)
- Audience brief used (if any)
- Filters used (province, age, income, etc.)
- Timestamp
- Tester ID

**Metrics:**
- Removal rate per run: `removed_count / panel_size`
- Removal rate by source: seed vs generated personas
- Most-removed persona archetypes (patterns)

**Pass criteria:** <25% removal rate per run on average

---

## EVAL-04: Reaction Removal Rate

**Status:** [x] Implemented

**What:** Track every time a reaction is excluded/checked off at the R1 review step. High exclusion rates mean reactions are off-target or low quality.

**How:** In-app tracking — every time a tester excludes a reaction at the R1 review step, log it.

**What to log per exclusion:**
- Run ID
- Persona ID
- Reaction text
- Sentiment score
- Tone fit value
- Relevance value
- Cultural flags (if any)
- Timestamp
- Tester ID

**Metrics:**
- Exclusion rate per run: `excluded_count / total_reactions`
- Exclusion rate by model (which reaction models produce the most excluded reactions?)
- Exclusion rate by persona source (seed vs generated)
- Common patterns in excluded reactions

**Pass criteria:** <30% exclusion rate per run on average

---

## EVAL-05: Sentiment-Reaction Alignment

**Status:** [x] Implemented

**What:** Does the sentiment score (1-5) actually match the tone of the reaction text? This is the core sycophancy check.

**How:** In-app thumbs up/down. Tester reads the reaction text, sees the sentiment score, and votes whether the score matches the text.

**Examples of misalignment:**
- Reaction says "I don't really care about this" but sentiment = 4 (should be 2-3)
- Reaction says "This is exactly what I need!" but sentiment = 3 (should be 4-5)
- Reaction is clearly negative but score is positive (sycophantic bias)

**Tracking:**
- Log each vote with: run ID, persona ID, reaction text, sentiment score, tester vote, tester ID
- Track misalignment rate by model (which models are most sycophantic?)

**Pass criteria:** >85% thumbs-up (score matches text) across all reactions

---

## EVAL-06: Persona Faithfulness

**Status:** [x] Implemented

**What:** Does each reaction sound like it actually comes from that specific persona? A 65-year-old retired farmer from rural Saskatchewan shouldn't sound like a 25-year-old urban marketer.

**How:** In-app thumbs up/down. Tester sees the persona profile alongside the reaction and votes whether the voice is authentic to that persona.

**What to watch for:**
- All personas sound the same regardless of demographics
- Vocabulary doesn't match education level or age
- Regional references are wrong (e.g., BC persona references Ontario-specific things)
- Cultural background is ignored in the reaction

**Tracking:**
- Log each vote with: run ID, persona ID, persona summary, reaction text, tester vote
- Track faithfulness rate by model
- Track faithfulness rate by persona demographics (are certain demographics harder to voice?)

**Pass criteria:** >75% thumbs-up rate

---

## EVAL-07: Optimization Faithfulness (No Hallucinated Claims)

**Status:** [x] Implemented

**What:** Does the optimized message introduce claims, features, or promises that were NOT in the original?

**How:** In-app thumbs up/down. Tester compares original and optimized, votes on whether the optimizer added anything that wasn't there.

**Examples of failures:**
- Original: "affordable" -> Optimized: "cheapest on the market"
- Original: no price mentioned -> Optimized: "starting at just $9.99"
- Original: "healthy snack" -> Optimized: "doctor-recommended"
- Brand names changed, misspelled, or removed

**Also check (automated):**
- Brand names preserved exactly
- Prices preserved exactly
- URLs preserved exactly
- Product names preserved exactly

**Pass criteria:** >95% thumbs-up (no hallucinated claims)

---

## EVAL-08: Optimization Improves Metrics

**Status:** [x] Implemented

**What:** Does the optimized message actually perform better than the original? If R2 metrics are frequently worse than R1, the optimizer is broken.

**How:** Automated — compare R1 aggregate metrics to R2 aggregate metrics.

**Metrics to compare (R1 vs R2):**
- Average sentiment score (should increase or stay same)
- Relevance percentage (should increase or stay same)
- Tone distribution: % natural (should increase)
- Tone distribution: % awkward + % offensive (should decrease)
- Cultural flags count (should decrease)

**Tracking per run:**
- R1 avg sentiment, R2 avg sentiment, delta
- R1 relevance %, R2 relevance %, delta
- R1 % natural, R2 % natural, delta
- Overall verdict: improved / no change / regressed

**Pass criteria:** >70% of runs show improvement in at least 2 of 3 core metrics (sentiment, relevance, tone)

---

## EVAL-09: A/B Preference Consistency (Position Bias)

**Status:** [x] Implemented

**What:** If you swap the order of A/B variants, does the preference change? LLMs have known position bias (tend to prefer the first or last option).

**How:** Run the same A/B test twice with variants in swapped order. Compare preferences.

**Test protocol:**
1. Run A/B test with variants [A, B]
2. Run same A/B test with variants [B, A] (same panel)
3. Compare: did the winner change?

**Metrics:**
- Preference flip rate: % of personas who changed their preference when order flipped
- Winner flip rate: % of test runs where the overall winner changed

**Pass criteria:**
- Persona preference flip rate < 20%
- Winner flip rate < 10%

---

## EVAL-10: Context Projection Relevance

**Status:** [x] Implemented

**What:** Does the context projection LLM correctly decide which persona attribute groups matter for a given audience brief?

**Output fields being tested** (the `ContextProjection` model):
- `relevant_groups`: list selected from `[core, identity, housing, political, health, digital, financial, civic, lifestyle, values, consumer]` (core is always included)
- `relevant_extended_keys`: specific extended_attributes keys to populate
- `reasoning`: explanation for selection

**Golden set examples:**

| Audience Brief | Expected Groups | Expected Extended Keys |
|---|---|---|
| "Muslim families shopping for halal groceries" | core, identity, lifestyle | religion, cultural_background, hobbies_and_interests |
| "First-time homebuyers in GTA, ages 25-35" | core, housing, financial | housing, commute_mode |
| "Conservative voters concerned about carbon tax" | core, political | political_leaning, top_concerns |
| "New immigrants from South Asia settling in BC" | core, identity, housing, lifestyle | immigration_status, cultural_background, religion, housing |
| "Tech workers interested in remote work tools" | core, digital, lifestyle | hobbies_and_interests |
| "Parents choosing after-school programs" | core, lifestyle, values | hobbies_and_interests |
| "Seniors on fixed income comparing pharmacy options" | core, health, financial | — |

**How:** Run each golden set brief through `determine_relevant_attributes()`, compare output to expected.

**Metrics:**
- Group precision: % of selected groups that are correct
- Group recall: % of expected groups that were selected
- Extended key precision/recall (same)

**Pass criteria:** >80% recall on groups (doesn't miss important ones), >70% precision (doesn't include irrelevant ones)

---

## API Endpoints for Testers

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/eval/log` | POST | Log any eval event (thumbs up/down, removals, exclusions) |
| `/api/eval/summary` | GET | Get aggregated pass rates for all eval types |
| `/api/eval/events` | GET | Get raw eval events (optional `?eval_type=X&limit=N`) |
| `/api/eval/context-projection` | POST | Run EVAL-10 golden set test (or custom test cases) |

## Summary Dashboard

| # | Eval | Type | Status |
|---|------|------|--------|
| 01 | Brand Voice Consistency | In-app (thumbs up/down) | [x] |
| 02 | Optimization Length Drift | Automated | [x] |
| 03 | Panel Selection Stability | In-app (removal tracking) | [x] |
| 04 | Reaction Removal Rate | In-app (exclusion tracking) | [x] |
| 05 | Sentiment-Reaction Alignment | In-app (thumbs up/down) | [x] |
| 06 | Persona Faithfulness | In-app (thumbs up/down) | [x] |
| 07 | Optimization Faithfulness | In-app (thumbs up/down) + automated | [x] |
| 08 | Optimization Improves Metrics | Automated | [x] |
| 09 | A/B Preference Consistency | Manual test protocol + auto logging | [x] |
| 10 | Context Projection Relevance | Golden set test | [x] |
