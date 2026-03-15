# MaplePulse — Product & Implementation Plan

> **Synthetic Focus Group as a Service for Canada**
> "Before you spend $50K on real focus groups, run your concept past 500 demographically targeted synthetic Canadians in 10 minutes."

---

## What is MaplePulse?

A web app where users paste a product concept, ad copy, survey question, or policy proposal — and get instant feedback from a demographically representative panel of synthetic Canadians.

**Core value proposition**: Fast, cheap, directional insight from 5,000 AI personas grounded in multiple Canadian data sources. Not a replacement for real research — a sharpening tool before you invest in it.

**Data sources powering personas**:
- **Statistics Canada 2021 Census** — demographics, population, income, education, occupation, immigration, visible minorities, Indigenous identity, language, housing, commute mode
- **Canadian Election Study (CES) 2019/2021 + Angus Reid regional polling** — political leaning by province/age
- **Census 2021 religion data** — religion by province with visible minority correlations
- **Angus Reid, Environics, Confederation of Tomorrow surveys** — regional top concerns
- **Census 2021 Journey to Work** — commute mode by urban/suburban/rural
- See `docs/DataSources.md` for the full catalog of 30+ sources investigated

### Use cases (validated with 5-persona demo)

| Use Case | What the user does | What they get back |
|----------|-------------------|-------------------|
| **Product concept test** | Describe a product/service | Sentiment breakdown, regional reactions, blind spots, who it resonates with |
| **Ad copy A/B test** | Paste 2+ taglines or messages | Which copy wins by segment, why, demographic splits |
| **Survey pre-test** | Paste a draft survey question | Ambiguity flags, regional interpretation differences, rewording suggestions |
| **Content localization** | Paste one message | Region-by-region reactions + suggested localizations |

### What MaplePulse is NOT (important disclaimers)

- Not real market research data — it's hypothesis generation
- Not a replacement for user testing (LLMs can't click through a UI)
- Not "5,000 Canadians said..." — it's "5,000 AI personas grounded in census data suggest..."
- Stated preferences only — no revealed behavior data

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│  (Next.js + shadcn/ui)                      │
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Input   │  │ Segment  │  │ Results   │  │
│  │ Panel   │  │ Picker   │  │ Dashboard │  │
│  └─────────┘  └──────────┘  └───────────┘  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│                  Backend                     │
│  (Next.js API routes)                        │
│                                             │
│  1. Select personas from pool (filter/sample)│
│  2. Build per-persona prompts               │
│  3. Fan out to LLM (concurrent)             │
│  4. Aggregate responses                     │
│  5. Return dashboard data                   │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│ Persona Pool │    │ LLM Provider    │
│ (5,000 JSON) │    │ (Claude / etc.) │
└──────────────┘    └─────────────────┘
```

---

## Phased Implementation Plan

### Phase 1: Persona Generation (DONE)
> Status: Code-complete, ready to run

- [x] Multi-source Canadian data as probability weights (census demographics, CES/Angus Reid political data, Environics/Confederation of Tomorrow concerns, Journey to Work commute data)
- [x] Persona generator script with stratified sampling across all provinces/territories
- [x] 22 fields per persona (18 deterministic + 4 LLM-enriched)
- [x] Async concurrent LLM enrichment with Anthropic tool calling
- [x] Additional signals: political leaning, religion, top concerns, commute mode
- [ ] **Generate full 5,000 personas with LLM enrichment** (using Claude Code, not API key)

### Phase 2: Backend — Query Engine
> The brain of MaplePulse: select personas, prompt them, aggregate results

- [ ] **2a. Persona store** — load 5,000 personas into memory, index by province/age/occupation/etc.
- [ ] **2b. Sampling engine** — given user's segment filters, select N representative personas (default: 100-500)
- [ ] **2c. Prompt builder** — take user's concept + persona profile → build per-persona evaluation prompt
- [ ] **2d. LLM fan-out** — send prompts concurrently (batches of 10-20), collect structured responses
- [ ] **2e. Aggregation engine** — sentiment scoring, regional grouping, quote extraction, blind spot detection
- [ ] **2f. API routes** — `POST /api/pulse` (submit concept), `GET /api/pulse/:id` (get results)

### Phase 3: Frontend — User Interface
> Clean, simple UI: paste your concept, pick segments, get results

- [ ] **3a. Input panel** — text area for concept/copy/question + mode selector (concept test / A/B test / survey pre-test / localization)
- [ ] **3b. Segment picker** — filter by province, age range, income, occupation, political leaning (optional, default = "Representative Canada")
- [ ] **3c. Results dashboard**:
  - Sentiment pie chart (positive / neutral / negative / irrelevant)
  - Regional heat map (Canada map showing where concept lands well vs. poorly)
  - Representative quotes (5-10 persona reactions with demographics shown)
  - Blind spots panel (demographics the concept misses or alienates)
  - Actionable recommendations (2-3 AI-generated bullets)
- [ ] **3d. A/B comparison view** — side-by-side when testing multiple copies
- [ ] **3e. Export** — PDF report or CSV of raw responses

### Phase 4: Data & Geography
> Canadian map and regional context

- [ ] **4a. Canadian GeoJSON boundaries** — provinces + territories from Statistics Canada census boundaries
- [ ] **4b. Map component** — interactive Canada map colored by sentiment per region
- [ ] **4c. Area profiles** (optional) — population, median income, key demographics per region for context cards

### Phase 5: Polish & Deploy
> Make it real

- [ ] **5a. Branding** — MaplePulse logo, color scheme, landing page
- [ ] **5b. Disclaimer system** — clear "AI-generated perspectives" warnings on all outputs
- [ ] **5c. Rate limiting** — prevent abuse (each query fans out to 100+ LLM calls)
- [ ] **5d. Deploy to Vercel**
- [ ] **5e. Attribution** — credit Ask Singapore / Aayush Mathur as inspiration

---

## Key Technical Decisions (to be made later)

| Decision | Options | Notes |
|----------|---------|-------|
| Frontend framework | Next.js (reuse ask-singapore patterns) vs. standalone | Next.js is the obvious choice |
| LLM for runtime queries | Claude via Claude Code / API, Gemini, OpenAI | User is on Claude Max — explore options |
| Database | None (static JSON) vs. Convex vs. Supabase | Start with static JSON, add persistence later |
| Personas per query | 50 / 100 / 500 | Trade-off: speed vs. representativeness |
| Hosting | Vercel, Railway, self-hosted | Vercel is simplest for Next.js |
| Auth | None (public) vs. simple auth | Start public, add auth if needed |

---

## What We Already Have

| Asset | Status | Location |
|-------|--------|----------|
| Census demographic weights (13 categories) | Done | `canada_demographics_2021.py` |
| Persona generator (skeleton + LLM enrichment) | Done | `scripts/generate_canada_personas.py` |
| 5 test enriched personas | Done | `scripts/test_enriched.json` |
| 30+ data source catalog | Done | `docs/DataSources.md` |
| Ask Singapore reference codebase | Cloned | `ask-singapore/` |
| Architecture knowledge | Documented | `docs/Learning.md` |

---

## Immediate Next Step

**Generate the full 5,000 personas.** Everything else depends on having the persona pool. This will be done through Claude Code (no API key needed — user is on Claude Max plan).
