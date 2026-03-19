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
