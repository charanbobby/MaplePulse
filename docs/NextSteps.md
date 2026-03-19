# MaplePulse — Next Steps

> Updated: 2026-03-19

---

## Completed

### Phase 1: Persona Generation (DONE)
- [x] Statistics Canada 2021 Census demographic distributions (13 categories)
- [x] Persona generator with stratified sampling (`scripts/generate_canada_personas.py`)
- [x] 25 fields per persona (21 deterministic + 4 LLM-enriched)
- [x] Additional signals: political leaning, religion, top concerns, commute mode
- [x] Income integration: `estimated_annual_income`, `income_bracket`, `income_source` — Job Bank 2025 wages + NOC mapping, age-adjusted estimates for non-employed (retirees, students, EI, etc.)
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

---

## Up Next

### Immediate: Regenerate Personas with Income
- [ ] Regenerate `data/personas_5000.json` with income fields baked in (current file predates income integration)
- [ ] Update notebook `build_persona_context()` to use actual income instead of "Income proxy via housing"

### Phase 2: Remaining Use Cases
- [ ] **Product concept** — implement `ProductReaction` flow in the LangGraph pipeline
- [ ] **A/B copy test** — implement `CopyReaction` flow
- [ ] **Survey pre-test** — implement `SurveyReaction` flow

### Phase 3: Dynamic Panel Generation
- [ ] Allow marketers to specify persona constraints (e.g. "$150K+ earners in Ontario aged 25-40")
- [ ] Generate targeted panels on-the-fly matching those constraints
- [ ] Support filtering by income bracket, province, age range, occupation, political leaning

### Phase 4: Backend — Query Engine
- [ ] Persona store — load personas, index by province/age/occupation/income/etc.
- [ ] Sampling engine with segment filters
- [ ] Prompt builder per use case
- [ ] LLM fan-out (concurrent, batched)
- [ ] Aggregation engine (sentiment, regional grouping, quote extraction, blind spots)
- [ ] API routes: `POST /api/pulse`, `GET /api/pulse/:id`

### Phase 5: Frontend (remaining)
- [x] Input panel + mode selector (localization mode implemented)
- [x] Segment picker (province, panel size)
- [x] Results dashboard (sentiment chart, tone distribution, cultural flags, representative quotes)
- [ ] Connect frontend to LangGraph backend (replace mock data with live API calls)
- [ ] A/B comparison view
- [ ] Export (PDF/CSV)

### Phase 6: Geography & Map
- [ ] Canadian GeoJSON boundaries (provinces + territories from Statistics Canada)
- [ ] Interactive map component colored by sentiment per region
- [ ] Area profiles (optional) — population, median income, key demographics

### Phase 7: Polish & Deploy
- [ ] Branding (MaplePulse logo, color scheme, landing page)
- [ ] Disclaimer system ("AI-generated perspectives" warnings)
- [ ] Rate limiting
- [ ] Deploy to Vercel
- [ ] Attribution (Ask Singapore / Aayush Mathur)
