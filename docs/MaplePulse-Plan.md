# MaplePulse — Product & Implementation Plan

> **Synthetic Focus Group as a Service for Canada**
> "Describe your target audience. We'll build a focus group of exactly those people and run your concept past them in 10 minutes."

---

## What is MaplePulse?

A web app where users describe their target audience and paste a product concept, ad copy, survey question, or policy proposal — and get instant feedback from a dynamically assembled panel of synthetic Canadians tailored to their specific market.

**Core value proposition**: Describe any target audience — the system dynamically generates or retrieves the right personas, grounded in Canadian census and market data, and runs your concept past them. Not a replacement for real research — a sharpening tool before you invest in it.

**Strategic direction (decided 2026-03-21)**: The system evolves from a static 5,000-persona pool to an **agentic persona engine** where an LLM orchestrator has tools to search existing personas, generate new targeted ones on-the-fly, fetch relevant data sources, and persist everything to a database for reuse. The 5,000 census personas become the seed corpus that grows with every query.

**Data sources powering personas**:
- **Statistics Canada 2021 Census** — demographics, population, income (inflation-adjusted from 2020 base to 2026 via CPI factor 1.23), education, occupation, immigration, visible minorities, Indigenous identity, language, housing, commute mode
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

### Legacy (v1) — Static Persona Pool (still available via filter-only mode)
```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│  (Next.js 15 + Tailwind CSS v4)             │
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Input   │  │ Segment  │  │ Results   │  │
│  │ Panel   │  │ Picker   │  │ Dashboard │  │
│  └─────────┘  └──────────┘  └───────────┘  │
└──────────────────┬──────────────────────────┘
                   │ SSE streaming
                   ▼
┌─────────────────────────────────────────────┐
│                  Backend                     │
│  (FastAPI + LangGraph)                       │
│                                             │
│  1. Classify intent                          │
│  2. Select panel (filter 15+ fields)         │
│  3. Fan out reactions (concurrent, multi-LLM)│
│  4. Aggregate results                        │
│  5. Optimize message                         │
│  6. Fan out round 2 reactions                │
│  7. Aggregate + compare                      │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│ Persona Pool │    │ OpenRouter      │
│ (5,000 JSON) │    │ (5 LLM models)  │
└──────────────┘    └─────────────────┘
```

### Current (v2) — Agentic Persona Engine (implemented)
```
┌─────────────────────────────────────────────────────┐
│                     Frontend                         │
│  User describes target audience + pastes content     │
│  "Young professionals in Vancouver, $80-120K,        │
│   environmentally conscious, considering EVs"        │
└──────────────────────┬──────────────────────────────┘
                       │ SSE streaming
                       ▼
┌─────────────────────────────────────────────────────┐
│              Agent Orchestrator                      │
│  (FastAPI + LangGraph with tool-calling)             │
│                                                     │
│  1. Parse audience brief                             │
│  2. TOOL: search_personas(spec) → check DB first     │
│  3. TOOL: generate_personas(spec) → fill gaps        │
│  4. TOOL: fetch_data(sources) → domain enrichment    │
│  5. Compose optimal panel (existing + new)           │
│  6. TOOL: persist_personas(new) → save to DB         │
│  7. Run focus group pipeline (react → optimize →     │
│     react v2 → compare) — same as v1                 │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌───────────┐ ┌─────────────────┐
│ Persona DB   │ │ Data      │ │ OpenRouter      │
│ (SQLite)     │ │ Sources   │ │ (5 LLM models)  │
│              │ │ (StatCan, │ │                 │
│ seed: 5,000  │ │ Job Bank, │ │                 │
│ grows with   │ │ domain    │ │                 │
│ each query   │ │ APIs)     │ │                 │
└──────────────┘ └───────────┘ └─────────────────┘
```

### Agent Tools (v2)

| Tool | Purpose | When used |
|------|---------|-----------|
| `search_personas` | Query persona DB by demographic/psychographic filters | Every query — always check existing pool first |
| `generate_personas` | Run Python persona generator with custom specs | When existing pool has insufficient coverage for the target audience |
| `fetch_data` | Pull from pre-indexed Canadian data sources (see data source registry below) | When generating personas — ground them in real statistical distributions |
| `persist_personas` | Save newly generated personas to SQLite DB with audience tags | After generation — every persona gets cached for future reuse |

### Data Source Registry (available to `fetch_data` tool)

The agent has access to 30+ Canadian data sources (full catalog: `docs/DataSources.md`). These are organized by what persona attribute they ground:

**Demographics & Economics (pre-indexed, always available)**
| Source | Grounds | Format |
|--------|---------|--------|
| Statistics Canada 2021 Census | Age, province, education, occupation, immigration, language, housing, commute. Income ranges inflation-adjusted from 2020 base to 2026 (CPI factor 1.23) | In-memory weights (`canada_demographics_2021.py`) + inflation-adjusted ranges in `backend/panel_engine.py` |
| Job Bank 2025 wages + NOC mapping | Income by occupation and province | CSV + JSON (`data/raw/`) |
| CMHC Housing Data | Rent levels, vacancy rates, housing affordability by city | API / tables |
| Bank of Canada CSCE | Financial stress, inflation expectations, spending confidence | Quarterly reports |
| Survey of Household Spending (SHS) | Spending patterns by category | PUMF |

**Values, Attitudes & Identity (pre-indexed)**
| Source | Grounds | Format |
|--------|---------|--------|
| Canadian Election Study (CES) | Political leaning, policy concerns, media habits | Harvard Dataverse |
| World Values Survey (Canada) | Moral values, religiosity, social tolerance | Downloadable dataset |
| Environics Institute | Social values, trust, diversity attitudes, regional identity | Reports |
| Angus Reid Institute | Current issue priorities, policy opinions | Reports |
| Confederation of Tomorrow | Provincial identity, regional grievances, federalism views | Reports |
| Pew Research (Canada) | Moral attitudes, international outlook | Reports |
| Census 2021 Religion | Religious affiliation by province + visible minority correlations | In-memory weights |

**Health & Wellbeing**
| Source | Grounds | Format |
|--------|---------|--------|
| CCHS | Self-rated health, chronic conditions, health behaviors, mental health | PUMF |
| CCHS Nutrition | Dietary preferences, food culture | PUMF |
| MHACS | Mental health status, help-seeking behavior | StatCan |
| Canadian Survey on Disability | Disability types, accessibility needs, employment barriers | StatCan |

**Digital Behavior & Media**
| Source | Grounds | Format |
|--------|---------|--------|
| CIRA Internet Trends | AI adoption, cybersecurity, e-commerce, social media trust | Annual report |
| Canadian Internet Use Survey (CIUS) | Digital literacy, online activities, privacy sensitivity | PUMF |
| DataReportal / Social Media Lab | Platform usage by age/gender (Facebook 66%, Instagram 45%, TikTok 18%) | Reports |
| Numeris | TV/radio audiences by market | Limited public data |
| CRTC Communications Monitoring | Broadcasting, telecom, internet trends | Annual reports |

**Civic & Community**
| Source | Grounds | Format |
|--------|---------|--------|
| Elections Canada Open Data | Voter turnout by age/gender/province | Open Gov Portal |
| GSS - Giving, Volunteering | Volunteer rates, charitable giving, community involvement | PUMF |
| Samara Centre for Democracy | Civic engagement barriers, online political abuse | Reports |
| Ipsos Canadian Public Affairs | 60+ surveys on elections, culture, politics | Borealis Dataverse |

**Lifestyle & Psychographics**
| Source | Grounds | Format |
|--------|---------|--------|
| Environics PRIZM | 67 geodemographic lifestyle segments by postal code | Free lookup tool |
| Canadian Financial Capability Survey | Financial literacy, saving habits, debt management | PUMF |
| GSS Time Use | Daily activity patterns — sleep, work, leisure | PUMF |
| Outdoor Activities (StatCan) | Recreation interests by income/age/region | Open Gov Portal |
| Reddit r/Canada dataset | Regional concerns, language patterns, issue salience | Kaggle |

> The `fetch_data` tool knows which sources are relevant for which persona attributes. When the agent parses an audience brief, it identifies which attributes need grounding and pulls from the right sources. For niche domains, the LLM's world knowledge + deterministic cultural/life-event maps provide sufficient context for persona selection without requiring live web search.

### Key Design Principles (v2)

1. **Search before generate** — never waste tokens creating personas that already exist in the DB
2. **The pool grows organically** — each query potentially adds specialized personas; the 5,000 census seed is the floor, not the ceiling
3. **Domain-agnostic** — the system doesn't know about furniture or EVs or healthcare ahead of time; the agent figures out what data it needs
4. **Persistent and queryable** — SQLite gives us indexed lookups without infrastructure overhead
5. **The persona generator becomes a tool** — the existing `generate_canada_personas.py` logic gets wrapped as an agent tool, not called as a standalone script
6. **Context projection** — the agent determines which persona attributes are relevant per query and builds lean, focused subagent prompts. A health product query gets health + financial fields; a social media campaign gets digital behavior + media fields. Core demographics always included. This keeps subagent context lean even as the persona schema grows.

---

## Phased Implementation Plan

### Phase 1: Persona Generation (DONE)

> Status: Code-complete, ready to run

- [x] Multi-source Canadian data as probability weights (census demographics, CES/Angus Reid political data, Environics/Confederation of Tomorrow concerns, Journey to Work commute data)
- [x] Persona generator script with stratified sampling across all provinces/territories
- [x] 25 fields per persona (21 deterministic + 4 LLM-enriched)
- [x] Async concurrent LLM enrichment with Anthropic tool calling
- [x] Additional signals: political leaning, religion, top concerns, commute mode
- [x] Income integration: estimated_annual_income, income_bracket, income_source — powered by Job Bank 2025 wage data + NOC occupation mapping, with age-adjusted estimates for non-employed personas (retirees, students, etc.)
- [ ] **Generate full 5,000 personas with LLM enrichment** (using Claude Code, not API key)

### Phase 2: Backend — Query Engine (DONE)

> The brain of MaplePulse: select personas, prompt them, aggregate results
> Implemented in `backend/main.py` (FastAPI + LangGraph)

- [x] **2a. Persona store** — loads 5,000 personas at startup, indexed by province/age/occupation/etc.
- [x] **2b. Sampling engine** — panel filtering by 15+ demographic fields (province, age, sex, income, education, marital status, immigration, Indigenous identity, visible minority, political leaning, religion, commute mode, housing, languages, top concerns)
- [x] **2c. Prompt builder** — per-persona evaluation prompt with anti-sycophancy scoring calibration
- [x] **2d. LLM fan-out** — concurrent reactions via 5-model pool through OpenRouter (gpt-5-nano, gpt-5-mini, mistral-small, gemini-3-flash, grok-3-mini)
- [x] **2e. Aggregation engine** — weighted relevance scoring, tone distribution, cultural flag collection, before/after comparison
- [x] **2f. API routes** — `POST /api/focus-group` (SSE streaming), `POST /api/build-panel` (agentic), `POST /api/select-panel` (filter-only), `POST /api/run-with-panel` (R1 only), `POST /api/continue-after-review` (R1→optimize→R2→done), `GET /api/panel-options`, `POST /api/panel-preview`, `POST /api/feedback` (Langfuse), `GET /health`
- [x] **2g. Reaction filtering** — auto-removes errors, empty/short text, irrelevant low-sentiment reactions (keeps minimum 3)
- [x] **2h. Langfuse cost tracking** — custom `OpenRouterLangfuseHandler` extracts cost from OpenRouter metadata, session ID grouping

### Phase 3: Frontend — User Interface (DONE)

> Clean, simple UI: paste your concept, pick segments, get results
> Refactored in Session 9 to 3-phase split architecture with human review checkpoint.

- [x] **3a. Input panel** — text area for message + audience brief field + panel filter controls (province, panel size)
- [x] **3b. Segment picker** — filter by province and panel size (6-20 personas), or describe audience in free text
- [x] **3c. Results dashboard** — sentiment, tone, cultural flags, per-persona cards, before/after comparison
- [x] **3d. 3-phase workflow** — Phase 1: Build panel (agentic or filter) → Phase 2: R1 reactions + human review → Phase 3: Optimize → R2 → Final
- [x] **3e. Connect to backend** — SSE streaming via 4 API functions (`runBuildPanel`, `selectPanel`, `runWithPanel`, `continueAfterReview`)
- [x] **3f. R1 review** — users can exclude individual persona reactions before optimization
- [x] **3g. Agentic metadata** — audience spec, context projection, agent log displayed when audience brief was used
- [ ] **3h. A/B comparison view** — side-by-side when testing multiple copies
- [ ] **3i. Export** — PDF report or CSV of raw responses

### Phase 4: Agentic Persona Engine (MOSTLY DONE)

> The core evolution: from static pool to dynamic, targeted persona generation via LLM tool use.
> Every subsequent feature (more use cases, geography, export) benefits from this foundation.
> Implemented in `backend/panel_engine.py` with frontend integration.

- [x] **4a. Persona DB (SQLite)** — 5,000 seed personas migrated from JSON to SQLite with indexed columns. Schema: all 25 fields + `source`, `created_at`, `audience_tags`, `extended_attributes` (JSON dict), `domain_context`. FTS5 full-text search. Persisted via Docker named volume `backend-db`.
- [x] **4b. Audience brief parser** — LLM parses free-text descriptions into `AudienceSpec` (demographics, psychographics, behavioral traits, domain context). Examples:
  - "Parents in suburban Ontario worried about screen time" → age 30-50, has_children, suburban, Ontario, concern: parenting/tech
  - "Retirees considering downsizing from houses to condos" → age 60+, homeowner, income from pension, housing concern
  - "Gen Z gamers in Vancouver" → age 18-27, Vancouver, digital_native, entertainment/gaming
- [x] **4c. search_personas tool** — query SQLite by structured spec via SQL WHERE clauses + FTS5 full-text search, return matching personas with coverage metadata
- [x] **4d. generate_personas tool** — generates targeted personas with NOC occupation lookup, income estimation via `_estimate_income()` + `_assign_income_bracket()`, CPI inflation adjustment (factor 1.23)
- [x] **4e. fetch_data tool** — agent pulls from pre-indexed Canadian data sources organized by persona attribute groups
- [x] ~~**4f. tavily_search tool**~~ — evaluated and deferred (2026-03-22). Web search results don't map to persona demographic filters; deterministic cultural holiday/life event maps + LLM brief parsing cover domain context without extra latency or API dependencies.
- [x] **4g. persist_personas tool** — saves newly generated personas to SQLite with audience_tags for future reuse
- [x] **4h. Panel composer** — ReAct agent assembles optimal panel: search existing DB → generate new personas to fill gaps → compose final panel
- [x] **4i. Context projection** — LLM determines relevant attribute groups per query (called once, not per persona). Groups: core (always), identity, housing, political, health, digital, financial, civic, lifestyle, values, consumer. Extended attributes stored as flexible JSON dict.
- [x] **4j. Backend integration** — `POST /api/build-panel` endpoint streams audience spec → context projection → agent log → panel via SSE. Panel engine init + seed migration at startup. `POST /api/select-panel` for quick filter-only mode.
- [ ] **4k. Cost controls** — generate max 10-15 new personas per query, cache aggressively, dedup similar specs
- [x] **LLM cache** — audience specs, context projections, and panel results cached in SQLite `llm_cache` table with hit counts

### Phase 5: Remaining Use Cases

> With the agentic persona engine in place, these become straightforward prompt/schema variations.

- [ ] **5a. Product concept** — implement `ProductReaction` flow
- [ ] **5b. A/B copy test** — implement `CopyReaction` flow
- [ ] **5c. Survey pre-test** — implement `SurveyReaction` flow

### Phase 6: Data & Geography

> Canadian map and regional context

- [ ] **6a. Canadian GeoJSON boundaries** — provinces + territories from Statistics Canada census boundaries
- [ ] **6b. Map component** — interactive Canada map colored by sentiment per region
- [ ] **6c. Area profiles** (optional) — population, median income, key demographics per region for context cards

### Phase 7: Polish & Deploy

> Make it real

- [ ] **7a. Branding** — MaplePulse logo, color scheme, landing page
- [ ] **7b. Disclaimer system** — clear "AI-generated perspectives" warnings on all outputs
- [ ] **7c. Rate limiting** — prevent abuse (each query fans out to 100+ LLM calls)
- [ ] **7d. Deploy to Vercel**
- [ ] **7e. Attribution** — credit Ask Singapore / Aayush Mathur as inspiration

---

## Key Technical Decisions

| Decision | Choice | Notes |
|----------|--------|-------|
| Frontend framework | **Next.js 15** | TypeScript + Tailwind CSS v4 + Lucide icons |
| Design system | **UI/UX Pro Max** | Data-Dense Dashboard style, Fira Code/Fira Sans, blue+amber palette |
| LLM for reactions | **OpenRouter (multi-model)** | gpt-5.4-nano, gpt-5.4-mini, mistral-small-2603, gemini-3-flash-preview, grok-4.20-beta |
| LLM for optimizer | **openai/gpt-5.4** | Best instruction following for goal-driven rewriting |
| LLM for agent orchestrator | **openai/gpt-5.4-mini** | Good tool-calling, cost-efficient. Configurable via `PANEL_AGENT_MODEL` env var |
| Persona DB | **SQLite** | Single file, zero infra, indexed queries + FTS5 full-text search. Docker named volume (`backend-db`) for persistence |
| Dynamic generation trigger | **Hybrid** | Search existing DB first; generate only when coverage < 80% of target spec |
| New personas per query | **Max 10-15** | Cost control — cache aggressively, dedup similar audience specs |
| Hosting | Vercel, Railway, self-hosted | Vercel is simplest for Next.js |
| Auth | None (public) vs. simple auth | Start public, add auth if needed |

---

## What We Already Have

| Asset | Status | Location |
|-------|--------|----------|
| Census demographic weights (13 categories) | Done | `canada_demographics_2021.py` |
| Persona generator (skeleton + LLM enrichment) | Done | `scripts/generate_canada_personas.py` |
| Income enrichment (Job Bank 2025 + NOC mapping) | Done | Integrated into generator — `estimated_annual_income`, `income_bracket`, `income_source`. Census 2020 income data inflation-adjusted to 2026 via CPI factor 1.23 in `backend/panel_engine.py` |
| Income enrichment data files | Done | `data/occupation_noc_mapping.json`, `data/raw/jobbank_wages_2025.csv` |
| 5,000 skeleton personas | Done | `data/personas_5000.json` (needs regeneration to include income fields) |
| LangGraph focus group pipeline | Done | `experiments/01_focus_group_test.ipynb` — classify → panel → react → optimize → react v2 → compare |
| 30+ data source catalog | Done | `docs/DataSources.md` |
| Ask Singapore reference codebase | Cloned | `ask-singapore/` |
| Architecture knowledge | Documented | `docs/Learning.md` |
| Agentic Persona Engine | Done | `backend/panel_engine.py` — SQLite DB, audience brief parser, ReAct agent with tools (search, generate, fetch_data, persist), context projection, LLM cache |
| Backend API (FastAPI + LangGraph) | Done | `backend/main.py` — SSE streaming, 9 endpoints, multi-model reactions, anti-sycophancy rubrics, reaction filtering, Langfuse cost tracking |
| Frontend backend client | Done | `frontend/src/lib/api.ts` — 4 API functions for split-phase workflow (build-panel, select-panel, run-with-panel, continue-after-review) |
| Frontend workflow UI | Done | `frontend/` — Next.js 15, 3-phase workflow with human review checkpoint, audience brief input, agentic metadata display |
| UI/UX design system | Done | `skills/ui-ux-pro-max/` — Data-Dense Dashboard style |
| Docker Compose (3 services) | Done | `docker-compose.yml` — frontend :3000, backend :8000, notebook :8888, `backend-db` named volume for SQLite |

---

## Immediate Next Steps (as of 2026-03-22)

1. **Regenerate personas** — `data/personas_5000.json` still lacks income fields; regenerate with income baked in
2. **Cost controls** — cap new persona generation at 10-15 per query, dedup similar audience specs
3. **Context projection → fan-out** — use `build_projected_context()` for lean subagent prompts in the reaction step (currently all fields still sent)
4. **Remaining use cases** — implement ProductReaction, CopyReaction, SurveyReaction flows
5. **A/B comparison view** — side-by-side UI when testing multiple copies
6. **Export** — PDF report or CSV of raw responses
7. **Validate anti-sycophancy rubrics** — run focus groups with new 1-5 scoring and confirm varied distributions
