# Ask Canada — Progress Log

## Session 1 (2026-03-14)

### What was done

**1. Project setup and research**
- Cloned the ASK Singapore reference project (`ask-singapore/`) from https://github.com/AayushMathur7/ask-singapore
- Reviewed the entire codebase: architecture, data pipeline, LLM prompting, sampling, sentiment aggregation
- Created `Learning.md` — a comprehensive breakdown of how ASK Singapore works (architecture, file-by-file guide, data flow, prompt engineering, tech stack)
- Created `NextSteps.md` — phased implementation plan for adapting to Canada
- Created `Plan.md` (user-authored) — research on Canadian persona data sources

**2. Canadian demographics data module**
- Created `canada_demographics_2021.py` — 13 categories of real 2021 Census data from Statistics Canada, structured as probability weights:
  - Province/territory populations (13 entries)
  - Census Metropolitan Areas (41 CMAs with populations)
  - Age distribution (adult groups)
  - Sex at birth
  - Education levels (15+ and 25-64 working age)
  - Occupation categories (NOC broad groups)
  - Income brackets (11 brackets)
  - Immigration status + top source countries
  - Visible minority groups (13 categories)
  - Indigenous identity (First Nations, Metis, Inuit)
  - Language (official, mother tongue, non-official)
  - Marital status
  - Housing (tenure, dwelling types, condo status)
- Includes helper mappings: Province-to-CMA, summary statistics

**3. Persona generation script**
- Created `scripts/generate_canada_personas.py` — generates synthetic Canadian personas grounded in census demographics
- Features:
  - Stratified generation across all 13 provinces/territories
  - Realistic occupation exemplars (10 NOC categories, 100+ job titles)
  - Cultural background templates for 15+ ethnic/cultural groups (including Indigenous)
  - Province-aware language assignment (Quebec = French-dominant, New Brunswick = bilingual, etc.)
  - Heritage language layering for immigrants
  - Two modes: `--skeleton-only` (instant, no API) and full LLM enrichment
- Refactored based on code review:
  - **Async concurrency**: replaced sequential calls with `AsyncAnthropic` + `asyncio.gather` (batch of 10 concurrent calls)
  - **Tool calling**: replaced brittle JSON string parsing with Anthropic tool use schema — guarantees valid structured output every time
  - Cleaned up unused imports
- Tested with 50 and 100 persona runs — distributions match real census proportions

### Files created

| File | Purpose |
|------|---------|
| `Plan.md` | Research on Canadian persona data sources (user-authored) |
| `Learning.md` | How ASK Singapore works — architecture deep dive |
| `NextSteps.md` | Phased implementation plan |
| `Progress.md` | This file — progress log |
| `canada_demographics_2021.py` | Statistics Canada 2021 Census data as probability weights |
| `scripts/generate_canada_personas.py` | Canadian persona generator (skeleton + LLM enrichment) |
| `ask-singapore/` | Cloned reference project |

### Current state

- Phase 1 (Persona Generation) is **code-complete**, ready to run against the Claude API
- No personas have been generated with LLM enrichment yet (requires `ANTHROPIC_API_KEY`)
- Skeleton-only generation works and produces demographically realistic output

### What's next (Phase 2+)

- Run full persona generation (5,000 personas with LLM enrichment)
- Get Canadian GeoJSON boundaries (Statistics Canada census boundaries)
- Build Canadian area profiles script (StatCan/CMHC data)
- Fork ask-singapore codebase and adapt for Canada
- Update map, schemas, prompts, UI for Canadian context
- Test and deploy

---

## Session 2 (2026-03-15)

### What was done

**1. Research: additional data sources beyond Statistics Canada**
- Investigated 30+ public data sources to enrich persona realism
- Created `docs/DataSources.md` — comprehensive catalog of free/paid Canadian data sources covering:
  - Values & attitudes (CES, World Values Survey, Environics, Angus Reid, Confederation of Tomorrow)
  - Consumer behavior & lifestyle (Vividata, PRIZM, Numeris, SHS)
  - Health & wellbeing (CCHS, MHACS, CSD)
  - Digital behavior (CIRA, CIUS, DataReportal, Social Media Lab)
  - Political views & civic engagement (Elections Canada, Samara Centre, GSS-GVP)
  - Regional culture & identity signals (per-province breakdowns)
  - Economic concerns (CMHC, Bank of Canada CSCE)
  - Open datasets (HuggingFace, Kaggle, GitHub)
  - Additional StatCan surveys (GSS cycles, LFS, outdoor activities)

**2. Enhanced persona generation with new signals**
- Added 4 new deterministic skeleton fields to `scripts/generate_canada_personas.py`:
  - **Political leaning** — province-weighted from CES/Angus Reid data, age-adjusted (younger skews progressive, older skews moderate/conservative). Quebec includes "Nationalist" category.
  - **Religion** — province-weighted from Census 2021, with visible minority correlations (South Asian → Hindu/Sikh/Muslim, Arab → Muslim, Filipino → Christian, Indigenous → Indigenous spirituality)
  - **Top concerns** — 2-3 issues sampled from province-specific concern pools (from Angus Reid, Environics, Confederation of Tomorrow surveys)
  - **Commute mode** — urban/suburban/rural weighted (Census 2021 Journey to Work), with big-city vs suburban vs rural splits
- Updated LLM enrichment prompt to include all new fields so generated personality details are regionally grounded
- Smoke tested with 20 personas — all new fields generating correctly

**3. Project reorganization**
- Created `docs/` folder and moved all markdown files there:
  - `docs/Plan.md`, `docs/Learning.md`, `docs/NextSteps.md`, `docs/Progress.md`, `docs/DataSources.md`

### Files created/modified

| File | Change |
|------|--------|
| `docs/DataSources.md` | NEW — 30+ public Canadian data sources for persona enrichment |
| `scripts/generate_canada_personas.py` | MODIFIED — added political leaning, religion, top concerns, commute mode fields + updated enrichment prompt |
| `docs/` folder | NEW — all markdown docs moved here |

### Current state

- Phase 1 (Persona Generation) is **enhanced and code-complete**
- Personas now include 4 additional fields: political_leaning, religion, top_concerns, commute_mode
- LLM enrichment prompt updated to use these signals for more grounded personality generation
- All docs organized under `docs/`

---

## Session 3 (2026-03-15, continued)

### What was done

**1. Income enrichment pipeline**
- Created `scripts/enrich_personas_income.py` — standalone script to enrich personas with income data from Job Bank 2025 wages
- Created `data/occupation_noc_mapping.json` — maps 100+ occupation exemplars to NOC codes
- Downloaded `data/raw/jobbank_wages_2025.csv` — Job Bank 2025 wage data by NOC code and province
- Income fields added: `noc_code`, `noc_title`, `is_employed`, `estimated_annual_income`, `income_bracket`, `income_source`, `wage_data`
- Age-adjusted income estimation (young → Q1/low, mid-career → median-Q3, senior → Q3/high)
- Non-employed personas get estimated income (pension, student income, EI, disability, newcomer)
- Generated enriched file: `data/personas_5000_enriched.json`

**2. Generated 5,000 skeleton personas**
- Ran full generation: `data/personas_5000.json` with 22 fields per persona
- Stratified across all 13 provinces/territories

**3. LangGraph focus group pipeline**
- Created `experiments/01_focus_group_test.ipynb` — full LangGraph pipeline
- Architecture: `classify_intent → select_panel → run_reactions → aggregate → optimize_message → run_reactions_v2 → aggregate_v2`
- Intent classifier routes to 4 use cases (localization is fully active, other 3 are WIP)
- Optimization loop: round 1 reactions feed into LLM rewriter, panel re-evaluates improved message
- Before/after comparison with sentiment delta, resonance %, cultural flags
- Langfuse v4 observability integration
- Performance logging to CSV (`data/experiments/performance_log.csv`)
- Tested with localization use case — working end-to-end

**4. v2 architecture sketch**
- Created `docs/v2_architecture_sketch.py` — design for Orchestrator + Subagent architecture

### Files created/modified

| File | Change |
|------|--------|
| `scripts/enrich_personas_income.py` | NEW — income enrichment pipeline |
| `data/occupation_noc_mapping.json` | NEW — occupation → NOC code mapping |
| `data/raw/jobbank_wages_2025.csv` | NEW — Job Bank 2025 wage data |
| `data/personas_5000.json` | NEW — 5,000 skeleton personas |
| `data/personas_5000_enriched.json` | NEW — enriched with income data |
| `experiments/01_focus_group_test.ipynb` | NEW — LangGraph focus group pipeline |
| `docs/v2_architecture_sketch.py` | NEW — v2 architecture design |
| `docs/MaplePulse-Plan.md` | NEW — comprehensive product & implementation plan |

---

## Session 4 (2026-03-18)

### What was done

**1. Income integration into persona generator**
- Integrated income assignment directly into `generate_skeleton_persona()` in `scripts/generate_canada_personas.py`
- Moved logic from the standalone `enrich_personas_income.py` into the generator so income is included from the start
- Three new fields per persona: `estimated_annual_income`, `income_bracket`, `income_source`
- Loads NOC mapping + Job Bank wages at module level; gracefully degrades if data files missing
- LLM enrichment prompt now includes `income_bracket` for persona-aware narrative generation
- Personas now have 25 fields (21 deterministic + 4 LLM-enriched)
- Tested with 50-persona skeleton generation — all income fields populating correctly

**2. Documentation updates**
- Updated `docs/MaplePulse-Plan.md` — field count (25), income integration status, dynamic panel generation as future feature, updated asset table
- Rewrote `docs/NextSteps.md` — renamed from "Ask Canada" to "MaplePulse", reorganized into completed vs. upcoming, added dynamic panel generation phase
- Updated `docs/Progress.md` — added Session 3 and Session 4 entries
- Updated `docs/DataSources.md` — added Job Bank 2025 wages as an actively used source
- Updated notebook `build_persona_context()` to use actual income bracket instead of "Income proxy via housing"

### Files modified

| File | Change |
|------|--------|
| `scripts/generate_canada_personas.py` | MODIFIED — integrated income assignment (NOC mapping + Job Bank wages) directly into `generate_skeleton_persona()` |
| `docs/MaplePulse-Plan.md` | MODIFIED — updated field count, income status, asset table, next steps |
| `docs/NextSteps.md` | REWRITTEN — renamed to MaplePulse, reorganized with completed/upcoming sections |
| `docs/Progress.md` | MODIFIED — added Session 3 and Session 4 |
| `docs/DataSources.md` | MODIFIED — added Job Bank wages as used source |
| `experiments/01_focus_group_test.ipynb` | MODIFIED — income in persona context |

### Current state

- Persona generator now produces 25-field personas with income baked in
- Existing `data/personas_5000.json` needs regeneration to include income fields
- LangGraph pipeline works end-to-end for localization use case
- 3 remaining use cases (product concept, A/B copy, survey pre-test) are WIP

---

## Session 5 (2026-03-19)

### What was done

**1. Frontend scaffolding with UI/UX Pro Max design system**
- Cloned `nextlevelbuilder/ui-ux-pro-max-skill` into `skills/ui-ux-pro-max/` for design intelligence
- Generated MaplePulse design system: Data-Dense Dashboard style, Fira Code/Fira Sans typography, blue data + amber highlights color palette
- Scaffolded Next.js 15 frontend app in `frontend/` with TypeScript, Tailwind CSS v4, Lucide icons

**2. Built complete focus group workflow UI (8 steps)**
- **Step 1: Input** — textarea for marketing statement, panel filter controls (province, panel size), example prompts
- **Step 2: Panel Selection** — grid of persona cards showing age, province, occupation, income, education, languages, concerns, cultural background, political leaning, visible minority, Indigenous identity
- **Step 3: Round 1 Responses** — animated persona response cards appearing one by one (600ms intervals), with sentiment scores, resonance indicators, tone fit badges, cultural flag alerts, model attribution
- **Step 4: Round 1 Summary** — metric cards (avg sentiment, resonance %, tone distribution), sentiment distribution bar, cultural flags panel
- **Step 5: Optimization** — side-by-side original vs improved message, list of changes made by AI
- **Step 6: Round 2 Responses** — same panel re-evaluating the optimized message, same animated card system
- **Step 7: Round 2 Summary** — same metrics view for round 2
- **Step 8: Final Comparison** — before/after delta cards for sentiment, resonance, tone; messages side-by-side with metrics; improvement summary; key optimizations applied

**3. UI components built**
- `WorkflowStepper` — 8-step progress bar with icons and active/done/pending states
- `InputStep` — message input with filter panel and example prompts
- `PanelView` — persona card grid with province color coding
- `ReactionCard` — per-persona response with typing animation, sentiment badge, tone badge, cultural flags
- `ReactionsView` — grid of reaction cards with progress bar and sequential reveal
- `SummaryView` — metrics dashboard with sentiment distribution and tone bars
- `OptimizationView` — before/after message comparison with changes list
- `FinalComparison` — full comparison dashboard with delta metrics and improvement summary

**4. Mock data for demo**
- 12 diverse mock personas spanning Quebec, Ontario, BC, Alberta, Saskatchewan, Manitoba, Nova Scotia, Newfoundland
- 12 Round 1 reactions (negative/critical, avg sentiment 3.75, 0% resonance)
- 12 Round 2 reactions (positive, avg sentiment 7.08, 100% resonance)
- Mock optimization with 7 specific changes

**5. Docker setup**
- Created `frontend/Dockerfile` (Node 22 Alpine)
- Updated `docker-compose.yml` with frontend service on port 3000
- Frontend running at http://localhost:3000

**6. Housekeeping**
- Updated `.gitignore` — added `skills/`, `frontend/node_modules/`, `frontend/.next/`, `frontend/out/`

### Files created

| File | Purpose |
|------|---------|
| `frontend/package.json` | Next.js 15 project config |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/next.config.ts` | Next.js config (standalone output) |
| `frontend/postcss.config.mjs` | Tailwind CSS v4 via PostCSS |
| `frontend/Dockerfile` | Node 22 Alpine dev container |
| `frontend/src/app/globals.css` | Design system tokens (colors, fonts from UI/UX Pro Max) |
| `frontend/src/app/layout.tsx` | Root layout with Google Fonts |
| `frontend/src/app/page.tsx` | Main orchestrator — 8-step workflow state machine |
| `frontend/src/app/api/focus-group/route.ts` | API route stub (mock mode, ready for backend proxy) |
| `frontend/src/lib/types.ts` | TypeScript types for personas, reactions, aggregation, workflow |
| `frontend/src/lib/cn.ts` | Tailwind merge utility |
| `frontend/src/lib/mock-data.ts` | 12 personas, 24 reactions, aggregation, optimization mock data |
| `frontend/src/components/workflow-stepper.tsx` | 8-step progress indicator |
| `frontend/src/components/input-step.tsx` | Message input + filter panel |
| `frontend/src/components/panel-view.tsx` | Persona card grid |
| `frontend/src/components/reaction-card.tsx` | Individual persona response card |
| `frontend/src/components/reactions-view.tsx` | Reaction grid with animated reveal |
| `frontend/src/components/summary-view.tsx` | Metrics dashboard |
| `frontend/src/components/optimization-view.tsx` | Before/after optimization |
| `frontend/src/components/final-comparison.tsx` | Full comparison dashboard |
| `skills/ui-ux-pro-max/` | Cloned UI/UX design intelligence toolkit |

### Current state

- Frontend is running at http://localhost:3000 with full workflow demo using mock data
- 8-step workflow: Input → Panel → Round 1 → Summary → Optimize → Round 2 → Summary → Final
- API route stubbed, ready to connect to Python LangGraph backend
- Docker Compose now runs both notebook (port 8888) and frontend (port 3000)

---

## Session 6 (2026-03-19, continued)

### What was done

**1. Backend API — FastAPI + LangGraph (`backend/main.py`)**
- Built the full MaplePulse backend as a FastAPI app with LangGraph orchestration
- Loads 5,000 personas at startup, indexed for filtering
- Panel filtering by: province, age range, sex, income bracket, education, marital status, immigration status, Indigenous identity, visible minority, political leaning, religion, commute mode, housing type, languages, top concerns
- LangGraph pipeline: classify_intent → select_panel → run_reactions (concurrent) → aggregate → optimize_message → run_reactions_v2 → aggregate_v2
- SSE streaming — frontend receives progress events for each of the 8 workflow steps
- Multi-model reaction pool: `openai/gpt-5-nano`, `openai/gpt-5-mini`, `mistralai/mistral-small`, `google/gemini-3-flash`, `xai/grok-3-mini`
- Default model: `openai/gpt-5-nano`, optimizer model: `openai/gpt-5.1`
- Endpoints: `POST /api/focus-group`, `GET /api/panel-options`, `POST /api/panel-preview`, `POST /api/feedback` (Langfuse), `GET /health`

**2. Frontend backend client (`frontend/src/lib/api.ts`)**
- Added API client to connect frontend to the FastAPI backend via SSE
- Frontend API route (`api/focus-group/route.ts`) proxies to backend

**3. Docker Compose updated**
- Added `backend` service on port 8000 (FastAPI)
- Docker Compose now runs 3 services: notebook (:8888), backend (:8000), frontend (:3000)
- Frontend depends_on backend

### Files created/modified

| File | Change |
|------|--------|
| `backend/main.py` | NEW — FastAPI + LangGraph backend (696 lines) |
| `frontend/src/lib/api.ts` | NEW — Backend API client |
| `docker-compose.yml` | MODIFIED — added backend service |

### Current state

- Backend API is functional with full LangGraph pipeline
- Frontend wired to backend via SSE streaming
- 3-service Docker Compose (notebook + backend + frontend)

---

## Session 7 (2026-03-20)

### What was done

**1. Scoring rubric rework — reduce sycophantic bias**

Problem: Performance log showed R1 resonance always 95-100% and sentiment scores 6.5-7.2/10 regardless of input quality. Personas were being too positive (sycophantic LLM behavior).

Changes:
- **Sentiment scale**: 1-10 → **1-5** with anchored descriptions per level (1=hostile, 2=skeptical, 3=neutral, 4=interested, 5=enthusiastic). Explicit instruction: "A mediocre message deserves mediocre scores."
- **Resonance**: boolean `resonates` → **`relevance`** enum (`irrelevant` / `somewhat` / `directly_relevant`). Three levels instead of binary removes the "default to yes" bias.
- **Tone fit labels**: "perfect"/"off-putting" → **"natural"/"awkward"**. Neutral labels avoid implying a positive default — "acceptable" replaces "perfect" as the middle ground for generic ads.
- **Scoring Calibration section** added to system prompt: explicit anti-sycophancy guidance ("Score structured fields independently from reaction text. Do not default to positive scores.")
- **Aggregation updated**: weighted relevance scoring replaces binary resonance percentage
- **All frontend components updated**: types, mock data, summary-view, reaction-card, final-comparison, input-step — all aligned to new schema

**2. Favicon and manifest assets**
- Added `favicon-96x96.png`, `favicon.svg`, `site.webmanifest`, PWA icons (192x192, 512x512)
- Updated `.gitignore` for favicon source files and `tsconfig.tsbuildinfo`

### Files modified

| File | Change |
|------|--------|
| `backend/main.py` | MODIFIED — new scoring schema, calibration prompt, weighted aggregation |
| `frontend/src/lib/types.ts` | MODIFIED — `resonates` → `relevance`, sentiment 1-5, tone fit labels |
| `frontend/src/lib/mock-data.ts` | MODIFIED — mock data aligned to new schema |
| `frontend/src/components/summary-view.tsx` | MODIFIED — relevance distribution, new tone labels |
| `frontend/src/components/reaction-card.tsx` | MODIFIED — 1-5 sentiment display, relevance badge |
| `frontend/src/components/final-comparison.tsx` | MODIFIED — delta metrics for new schema |
| `frontend/src/components/reactions-view.tsx` | MODIFIED — new schema support |
| `frontend/src/components/input-step.tsx` | MODIFIED — updated for new flow |
| `frontend/src/app/page.tsx` | MODIFIED — aligned to new types |
| `frontend/src/app/layout.tsx` | MODIFIED — favicon/manifest references |
| `frontend/public/` | NEW — favicon assets and webmanifest |
| `.gitignore` | MODIFIED — favicon sources, tsbuildinfo |

### Anti-sycophancy rubric design decisions

| Before (v1) | After (v2) | Rationale |
|-------------|-----------|-----------|
| Sentiment 1-10 | Sentiment 1-5 with anchors | Narrower scale + anchored descriptions reduce tendency to cluster at 7+ |
| `resonates: bool` | `relevance: irrelevant/somewhat/directly_relevant` | Binary forced "yes" default; three levels allow honest "meh" |
| `tone_fit: perfect/acceptable/off/offensive` | `tone_fit: natural/acceptable/awkward/offensive` | "Perfect" is aspirational and biases toward selection; "natural" is descriptive |
| No scoring guidance | Scoring Calibration section in system prompt | Explicit instruction to score independently and avoid positive defaults |

### Current state

- Scoring rubrics are tighter and calibrated against sycophantic bias
- Frontend fully aligned to new schema
- Performance log (`data/experiments/performance_log.csv`) predates this change — future runs should show more varied score distributions

---

## Session 8 (2026-03-21)

### What was done

**1. Agentic Persona Engine — panel_engine.py**
- Built `backend/panel_engine.py` — the agentic persona engine for dynamic panel assembly
- Three-phase pipeline: parse audience brief → context projection → ReAct agent with tools
- Tools: `search_personas`, `generate_personas`, `fetch_data`
- SQLite persona database replaces static JSON pool
- Langfuse tracing with named spans (`parse_audience_brief`, `context_projection`, `panel_builder_agent`)

**2. Model optimization**
- Switched from GPT-5.4 to `openai/gpt-5.4-mini` (~10x cheaper) for both orchestrator and agent
- Model configurable via `PANEL_AGENT_MODEL` and `PANEL_ORCHESTRATOR_MODEL` env vars

**3. generate_personas tool improvements**
- NOC codes resolved to specific job titles via `_OCCUPATION_EXEMPLARS` lookup
- Income estimation via `_estimate_income()` + `_assign_income_bracket()` — no more "Unknown" income
- Age distribution: filters census brackets to overlap with requested range instead of clamping
- City constraint: respects specified cities instead of random CMA selection

**4. CPI inflation adjustment**
- Census 2021 income data has reference year 2020 — incomes have risen ~23% since then
- Added `_INCOME_INFLATION_FACTOR = 1.23` constant applied to all 2020 base income ranges
- Applied to `_OCCUPATION_INCOME_RANGES` pre-computed dict and special-case estimates (Retired, Student, Unemployed)
- Updated all documentation (DataSources.md, MaplePulse-Plan.md, NextSteps.md) to note the adjustment

**5. Cleanup**
- Removed stale "persist" step from agent system prompt (persist_personas was removed from tools)
- Cleaned 115 low-quality generated personas from SQLite DB

### Files modified

| File | Change |
|------|--------|
| `backend/panel_engine.py` | MODIFIED — model switch, run_name spans, occupation exemplars, income estimation, inflation adjustment, system prompt cleanup, city parameter |
| `docs/DataSources.md` | MODIFIED — added Census 2020 income inflation adjustment note |
| `docs/MaplePulse-Plan.md` | MODIFIED — inflation adjustment references in data sources and asset table |
| `docs/NextSteps.md` | MODIFIED — inflation adjustment as completed item |
| `docs/Progress.md` | MODIFIED — added Session 8 |

### Current state

- Agentic persona engine generates targeted personas with realistic income, job titles, and age distribution
- All income figures inflation-adjusted from 2020 Census base to 2026 (CPI factor 1.23)
- Agent model is gpt-5.4-mini for cost efficiency
- Documentation updated across all docs to reflect inflation adjustment

---

## Session 9 (2026-03-22)

### What was done

**1. Full backend integration of agentic persona engine**
- Wired `panel_engine.py` into `backend/main.py` — DB init + seed migration runs at startup
- Added SQLite persona DB as a Docker named volume (`backend-db`) for persistence across rebuilds
- Health endpoint now reports `persona_db` stats (total personas, seed count, generated count) and `llm_cache` stats

**2. New API endpoints for split-phase workflow**
- `POST /api/build-panel` — runs the agentic panel builder via SSE, streaming audience spec → context projection → agent log → panel assembly. Stops after panel — does NOT run reactions. Used when user provides an audience brief.
- `POST /api/select-panel` — quick filter-based panel selection from the static pool (no LLM calls). Used when user provides demographic filters only.
- `POST /api/run-with-panel` — runs Round 1 reactions only with a pre-built panel, then pauses for human review. Auto-filters low-quality reactions before returning.
- `POST /api/continue-after-review` — continues pipeline after human review: R1 summary → optimize → R2 reactions → R2 summary → done. Accepts the user's curated R1 reactions (after manual exclusions).

**3. Reaction quality filtering**
- Added `_filter_reactions()` — auto-removes reactions that are errors, have empty text, very short text (<15 chars), or "irrelevant" relevance with sentiment ≤2
- Safety floor: always keeps at least 3 reactions even if filter removes many
- Frontend receives `reactions_filtered` SSE event showing kept/removed counts and per-persona removal reasons

**4. Reaction prompt improvements**
- Added: "Do NOT invent or assume details not in the message" — prevents personas from reacting to features/prices not mentioned
- Added: "If the message is about your professional field, react with domain knowledge" — AI researchers now sound like experts on AI products
- Changed scoring calibration: scores MUST be consistent with reaction text (positive text = 4-5, critical text = 1-2). Previous guidance said to "score independently" which caused mismatches.

**5. Optimizer prompt rewrite**
- Reframed from defensive ("don't add info") to goal-driven ("make Round 2 score HIGHER on all three metrics")
- Key shift: preserve vivid/emotional language unless a MAJORITY of panelists flagged it. Previous version was overly cautious and stripped persuasive language.
- Added self-check section: optimizer must verify it hasn't degraded sentiment, natural tone, or relevance before finalizing
- Fixed symbol preservation: ampersands (&) and special characters no longer get replaced
- Removed XML `<FINAL_RESPONSE>` tag requirement from prompt (added regex strip as fallback)
- Pattern-based changes only: requires 3+ panelists to flag something before acting, not individual outliers

**6. Model upgrades**
- Optimizer: `openai/gpt-5.1` → `openai/gpt-5.4` (better instruction following)
- Reaction models updated: `openai/gpt-5-nano` → `gpt-5.4-nano`, `gpt-5-mini` → `gpt-5.4-mini`, `mistral-small` → `mistral-small-2603`, `gemini-3-flash` → `gemini-3-flash-preview`, `grok-3-mini` → `grok-4.20-beta`

**7. Langfuse improvements**
- Custom `OpenRouterLangfuseHandler` — extracts cost from OpenRouter response metadata and attaches it to Langfuse observations
- Session ID tracking: all LLM calls within a focus group run share a `langfuse_session_id`

**8. Frontend refactor — 3-phase split architecture**
- Replaced single `runFocusGroup()` flow with 3 independent phases:
  - Phase 1: `handleStart()` — builds panel (agentic via `/api/build-panel` or filter-based via `/api/select-panel`)
  - Phase 2: `handleRunReactions()` — runs R1 reactions via `/api/run-with-panel`, pauses for review
  - Phase 3: `handleContinue()` — user reviews R1, excludes bad reactions, continues via `/api/continue-after-review`
- Audience brief input field added to InputStep component (free-text field alongside demographic filters)
- Agentic metadata display: audience spec, context projection, panel metadata, agent log shown when audience brief was used
- R1 review: users can manually exclude individual persona reactions before continuing to optimization
- Panel view shows `source` badge (seed vs generated) for agentic panels

**9. Frontend API client rewrite (`frontend/src/lib/api.ts`)**
- New functions: `runBuildPanel()`, `selectPanel()`, `runWithPanel()`, `continueAfterReview()`
- Each handles SSE streaming with typed callbacks
- Old `runFocusGroup()` kept for backwards compatibility but no longer the primary path

**10. Docker Compose**
- Added `backend-db` named volume for SQLite persona database persistence
- DB mounted at `/app/db` in the backend container

### Files created/modified

| File | Change |
|------|--------|
| `backend/main.py` | MODIFIED — panel_engine integration, 4 new endpoints, reaction filtering, prompt improvements, model upgrades, Langfuse cost tracking |
| `backend/panel_engine.py` | NEW (Session 8) — agentic persona engine with SQLite, tools, context projection |
| `backend/db/personas.db` | NEW — SQLite persona database (auto-created at startup) |
| `docker-compose.yml` | MODIFIED — added `backend-db` named volume |
| `frontend/src/app/page.tsx` | MODIFIED — 3-phase architecture, audience brief, R1 review, agentic metadata |
| `frontend/src/lib/api.ts` | MODIFIED — 4 new API client functions for split-phase workflow |
| `frontend/src/lib/types.ts` | MODIFIED — added source field to Persona type |
| `frontend/src/components/input-step.tsx` | MODIFIED — audience brief input field |
| `frontend/src/components/panel-view.tsx` | MODIFIED — source badges, expanded persona details |
| `frontend/src/components/reactions-view.tsx` | MODIFIED — exclusion support for R1 review |
| `frontend/src/components/summary-view.tsx` | MODIFIED — minor alignment fixes |
| `frontend/src/components/final-comparison.tsx` | MODIFIED — expanded delta metrics display |
| `frontend/src/components/workflow-stepper.tsx` | MODIFIED — new step support |
| `README.md` | REWRITTEN — updated to reflect agentic engine, new architecture, current stack |

### Current state

- Full agentic pipeline working: audience brief → parse → context projection → agent builds panel → reactions → review → optimize → R2
- Also supports filter-only mode (no LLM for panel building) for quick runs
- 3-phase frontend with human review checkpoint between R1 and optimization
- All models upgraded to latest versions (gpt-5.4 family, grok-4.20, gemini-3-flash-preview)
- SQLite persona DB persisting across Docker rebuilds via named volume
- Reaction filtering removes low-quality responses before aggregation
- Langfuse traces include OpenRouter cost data and session grouping
