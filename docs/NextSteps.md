# MaplePulse — Next Steps

> Updated: 2026-03-22

---

## Completed

### Phase 1: Persona Generation (DONE)
- [x] Statistics Canada 2021 Census demographic distributions (13 categories)
- [x] Persona generator with stratified sampling (`scripts/generate_canada_personas.py`)
- [x] 25 fields per persona (21 deterministic + 4 LLM-enriched)
- [x] Additional signals: political leaning, religion, top concerns, commute mode
- [x] Income integration: `estimated_annual_income`, `income_bracket`, `income_source` — Job Bank 2025 wages + NOC mapping, age-adjusted estimates for non-employed (retirees, students, EI, etc.)
- [x] CPI inflation adjustment: Census 2020 income data adjusted to 2026 levels using factor 1.23 (~23% cumulative CPI increase). Applied to all occupation income ranges and special-case estimates in `backend/panel_engine.py`
- [x] Income enrichment pipeline (`scripts/enrich_personas_income.py`) — standalone script for batch enrichment
- [x] 5,000 skeleton personas generated (`data/personas_5000.json`)
- [x] 30+ Canadian data sources catalogued (`docs/DataSources.md`)

### Phase 1b: LangGraph Focus Group Pipeline (DONE)
- [x] LangGraph orchestration: classify → select_panel → react → aggregate → optimize → react_v2 → compare
- [x] Intent classifier (product_concept, ab_copy_test, survey_pretest, localization)
- [x] Localization use case fully implemented with structured output (LocalizationReaction schema)
- [x] Optimization loop: LLM rewrites message based on round 1 feedback, panel re-evaluates
- [x] Before/after comparison with sentiment delta, resonance, cultural flags
- [x] Langfuse observability integration
- [x] Performance logging to CSV

### Phase 5 (partial): Frontend — Focus Group Workflow UI (DONE)
- [x] UI/UX Pro Max design system generated (Data-Dense Dashboard style, Fira Code/Fira Sans, blue+amber palette)
- [x] Next.js 15 frontend with TypeScript, Tailwind CSS v4, Lucide icons
- [x] 8-step animated workflow: Input → Panel → Round 1 → Summary → Optimize → Round 2 → Summary → Final
- [x] Persona card grid with province color coding and demographic details
- [x] Animated response cards with sentiment scores, tone badges, cultural flag alerts, model attribution
- [x] Metrics dashboard: sentiment distribution, tone fit bars, cultural flags panel
- [x] Before/after optimization comparison with changes list
- [x] Final comparison dashboard with delta metrics and improvement summary
- [x] Docker service running on port 3000 (`docker-compose.yml` updated)
- [x] Mock data with 12 diverse personas and 24 reactions for demo

### Backend API — FastAPI + LangGraph (DONE)
- [x] FastAPI backend with LangGraph orchestration (`backend/main.py`)
- [x] Persona store — loads 5,000 personas at startup, indexed for filtering
- [x] Panel filtering by 15+ demographic fields (province, age, income, education, political leaning, religion, etc.)
- [x] LangGraph pipeline: classify → select_panel → react → aggregate → optimize → react_v2 → aggregate_v2
- [x] SSE streaming to frontend for real-time step progress
- [x] Multi-model reaction pool (gpt-5-nano, gpt-5-mini, mistral-small, gemini-3-flash, grok-3-mini)
- [x] API endpoints: `POST /api/focus-group`, `GET /api/panel-options`, `POST /api/panel-preview`, `POST /api/feedback`, `GET /health`
- [x] Frontend API client (`frontend/src/lib/api.ts`) wired to backend
- [x] Docker Compose: 3 services (notebook :8888, backend :8000, frontend :3000)

### Scoring Rubric Rework — Anti-Sycophancy (DONE)
- [x] Sentiment scale: 1-10 → 1-5 with anchored descriptions per level
- [x] Resonance: boolean → `relevance` enum (irrelevant / somewhat / directly_relevant)
- [x] Tone fit labels: "perfect"/"off" → "natural"/"awkward" (neutral wording)
- [x] Scoring Calibration section added to system prompt with anti-sycophancy guidance
- [x] Aggregation updated: weighted relevance scoring replaces binary resonance %
- [x] All frontend components aligned to new schema

### Phase 4 (partial): Agentic Persona Engine (DONE)
- [x] **4a. Persona DB (SQLite)** — seed personas migrated from JSON, with `source`, `created_at`, `audience_tags`, `extended_attributes` columns. FTS5 full-text search index. Persisted via Docker named volume (`backend-db`).
- [x] **4b. Audience brief parser** — LLM parses free-text audience descriptions into structured `AudienceSpec` (demographics + psychographics + domain context)
- [x] **4c. search_personas tool** — query DB by structured spec, return matches + coverage score
- [x] **4d. generate_personas tool** — wraps persona generation as an agent tool with NOC occupation lookup, income estimation, CPI inflation adjustment
- [x] **4e. fetch_data tool** — agent pulls from pre-indexed Canadian data sources organized by persona attribute
- [x] **4g. persist_personas tool** — save new personas to DB with audience tags for future reuse
- [x] **4h. Panel composer** — ReAct agent assembles optimal panel from existing + newly generated personas
- [x] **4i. Context projection** — LLM determines relevant attribute groups per query, subagents get lean prompts. Groups: core, identity, housing, political, health, digital, financial, civic, lifestyle, values, consumer.
- [x] **4j. Backend integration** — `POST /api/build-panel` endpoint streams audience spec → context projection → agent log → panel assembly via SSE. Panel engine initialized at startup.
- [x] **LLM cache** — audience specs, context projections, and panel results cached in SQLite `llm_cache` table with hit counts

### Backend: Split-Phase Workflow + Prompt Improvements (DONE)
- [x] New endpoints: `POST /api/select-panel` (quick filter, no LLM), `POST /api/run-with-panel` (R1 reactions only), `POST /api/continue-after-review` (R1 summary → optimize → R2 → done)
- [x] Reaction quality filtering — auto-removes errors, empty/short text, irrelevant low-sentiment reactions (keeps minimum 3)
- [x] Reaction prompt: personas don't invent details not in message, domain experts react with professional insight, scores must match reaction tone
- [x] Optimizer prompt: goal-driven (maximize R2 scores), preserves vivid language, pattern-based changes (3+ panelists), self-check before finalizing
- [x] Model upgrades: gpt-5.4-nano, gpt-5.4-mini, mistral-small-2603, gemini-3-flash-preview, grok-4.20-beta, optimizer gpt-5.4
- [x] Langfuse: custom OpenRouterLangfuseHandler for cost tracking, session ID grouping

### Frontend: 3-Phase Split Architecture (DONE)
- [x] Phase 1: Build panel (agentic via audience brief OR filter-based)
- [x] Phase 2: Run R1 reactions, pause for human review
- [x] Phase 3: User reviews/excludes R1 reactions, continues to optimize → R2 → final
- [x] Audience brief input field in InputStep
- [x] Agentic metadata display (audience spec, context projection, agent log)
- [x] R1 review with per-reaction exclusion toggles
- [x] Panel view shows source badges (seed vs generated)
- [x] API client rewrite: `runBuildPanel()`, `selectPanel()`, `runWithPanel()`, `continueAfterReview()`

---

## Up Next

### Prerequisite: Regenerate Personas with Income

- [ ] Regenerate `data/personas_5000.json` with income fields baked in (current file predates income integration)
- [ ] Update notebook `build_persona_context()` to use actual income instead of "Income proxy via housing"

### Phase 4 (remaining): Agentic Engine Polish

- [x] ~~**4f. tavily_search tool**~~ — evaluated and deferred. Web search results don't map to persona demographic filters; the deterministic cultural holiday/life event maps + LLM brief parsing cover domain context without extra latency or API dependencies.
- [ ] **4k. Cost controls** — max 10-15 new personas per query, cache aggressively, dedup similar specs
- [ ] Context projection → fan-out integration — use `build_projected_context()` for lean subagent prompts in the reaction step (currently all fields still sent)

### Phase 5: Remaining Use Cases

> With the agentic engine in place, these are prompt/schema variations — not major architecture work.

- [ ] **Product concept** — implement `ProductReaction` flow in the LangGraph pipeline
- [ ] **A/B copy test** — implement `CopyReaction` flow
- [ ] **Survey pre-test** — implement `SurveyReaction` flow

### Phase 6: Frontend (remaining)

- [ ] A/B comparison view
- [ ] Export (PDF/CSV)

### Phase 7: Geography & Map

- [ ] Canadian GeoJSON boundaries (provinces + territories from Statistics Canada)
- [ ] Interactive map component colored by sentiment per region
- [ ] Area profiles (optional) — population, median income, key demographics

### Phase 8: Polish & Deploy

- [ ] Branding (MaplePulse logo, color scheme, landing page)
- [ ] Disclaimer system ("AI-generated perspectives" warnings)
- [ ] Rate limiting
- [ ] Deploy to Vercel
- [ ] Attribution (Ask Singapore / Aayush Mathur)
