# MaplePulse

Synthetic focus group as a service for Canada. Describe your target audience, paste your content — get instant reactions from dynamically assembled AI personas grounded in 30+ real Canadian data sources.

Inspired by [Ask Singapore](https://github.com/AayushMathur7/ask-singapore) by Aayush Mathur.

## How It Works

1. **Describe your target audience** in plain language — "homeowners aged 30-55, $80K-$150K income, Ontario/BC/Alberta, values quality over brand names"
2. **The agentic persona engine** searches a persistent database of personas, generates new ones to fill gaps using census data, and assembles the optimal focus group panel
3. **A LangGraph pipeline** runs persona reactions concurrently via multiple LLMs, aggregates sentiment, optimizes your message, and re-tests it

```
                     MAPLEPULSE — AGENTIC PERSONA ENGINE
  ═══════════════════════════════════════════════════════════════

  USER INPUT                        ENGINE
  ──────────                        ──────

  ┌───────────────────────┐
  │  1. Audience brief     │
  │     "Young parents in  │
  │      suburban Ontario,  │
  │      worried about     │
  │      screen time"      │
  │                        │
  │  2. Content to test    │
  │     "Screen-Free       │
  │      Sundays — a new   │
  │      family tradition" │
  └──────────┬────────────┘
             │
             ▼
  ┌══════════════════════════════════════════════════════════════┐
  ║              PANEL-BUILDING AGENT (ReAct)                   ║
  ║                                                             ║
  ║  LLM orchestrator with tools — decides HOW to assemble     ║
  ║  the optimal panel for each query                           ║
  ║                                                             ║
  ║  Tools available:                                           ║
  ║  ┌─────────────────────────────────────────────────────┐    ║
  ║  │ search_personas   → query SQLite DB for matches     │    ║
  ║  │ generate_personas → create new targeted personas    │    ║
  ║  │ fetch_data        → pull from 30+ Canadian sources  │    ║
  ║  │ persist_personas  → cache new personas to DB        │    ║
  ║  └─────────────────────────────────────────────────────┘    ║
  ║                                                             ║
  ║  Workflow:                                                  ║
  ║  1. Parse audience brief → structured spec                  ║
  ║  2. Search existing DB (5,000+ personas)                    ║
  ║  3. Assess coverage — enough matches? Generate to fill gaps ║
  ║  4. Fetch domain data (StatCan, Job Bank, 30+ sources)      ║
  ║  5. Persist new personas for future reuse                   ║
  ║  6. Compose final panel (existing + new)                    ║
  ╚═══════════════╤════════════════════════════════════════════╝
                  │  panel of 12-20 targeted personas
                  ▼
  ┌══════════════════════════════════════════════════════════════┐
  ║              CONTEXT PROJECTION (per query)                  ║
  ║                                                              ║
  ║  LLM determines which persona attributes matter for THIS     ║
  ║  query. Subagents get lean, focused prompts — not all 25+    ║
  ║  fields. Health query → health fields. Social media →        ║
  ║  digital behavior. Core demographics always included.        ║
  ╚═══════════════╤══════════════════════════════════════════════╝
                  │  projected persona contexts
                  ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  REACT — ROUND 1    │────▶│  For each persona (concurrent):  │
  │                     │     │  Multi-model fan-out:             │
  └──────────┬──────────┘     │  gpt-5-nano, gemini-3-flash,     │
             │                │  mistral-small, grok-3-mini ...   │
             │                │                                  │
             │                │  Each returns:                   │
             │                │   reaction: "gut feeling text"   │
             │                │   sentiment_score: 1-5           │
             │                │   relevance: irrelevant/somewhat/│
             │                │              directly_relevant   │
             │                │   tone_fit: natural/acceptable/  │
             │                │             awkward/offensive     │
             │                │   cultural_flags: [...]           │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  AGGREGATE + SHOW   │────▶│  Sentiment distribution          │
  └──────────┬──────────┘     │  Relevance breakdown             │
             │                │  Tone fit distribution            │
             │                │  Cultural flags                   │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  OPTIMIZE MESSAGE   │────▶│  LLM rewrites message based on   │
  └──────────┬──────────┘     │  panel feedback + metadata        │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐
  │  REACT — ROUND 2    │     Same panel, optimized message
  └──────────┬──────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  COMPARE            │────▶│  BEFORE / AFTER                  │
  └──────────┬──────────┘     │  Sentiment delta                 │
             │                │  Relevance improvement           │
             │                │  Cultural flags resolved          │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐
  │  MARKETER RECEIVES: │
  │  ● Original + opt.  │
  │  ● List of changes  │
  │  ● 40 reactions     │
  │  ● Before/after     │
  │  ● Cultural flags   │
  └─────────────────────┘


  DATA FOUNDATION
  ═══════════════

  ┌──────────────────────────────────────────────────────────────┐
  │                    PERSONA DB (SQLite)                       │
  │                                                              │
  │  Seed: 5,000 census-grounded personas                        │
  │  Grows organically with each query                           │
  │                                                              │
  │  Indexed by: province, age, income, education, occupation,   │
  │  political leaning, religion, concerns, domain context       │
  │  FTS5 search on: occupation, concerns, domain, audience tags │
  └──────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
  ┌──────┴────────┐   ┌──────┴──────┐   ┌────────┴──────────┐
  │ Statistics     │   │ Job Bank    │   │ 28+ Other Sources  │
  │ Canada 2021   │   │ 2025 Wages  │   │ CES, Angus Reid,   │
  │ Census        │   │ 516 NOC     │   │ Environics, CMHC,   │
  │               │   │ codes       │   │ CIRA, CCHS ...      │
  └───────────────┘   └─────────────┘   └────────────────────┘
```

## Use Cases

| Use Case | Status | Description |
|----------|--------|-------------|
| Content localization | Active | Test how a message lands across Canadian regions |
| Product concept test | Planned | Get reactions to a product/service idea |
| A/B copy test | Planned | Compare two versions of ad copy |
| Survey pre-test | Planned | Test survey questions for clarity and bias |

## Architecture

| Component | Tech | Status |
|-----------|------|--------|
| Frontend | Next.js 15 + Tailwind CSS v4 + TypeScript | Done |
| Backend API | FastAPI + LangGraph + SSE streaming | Done |
| Persona generation | Python + census data + LLM enrichment | Done |
| Multi-model reactions | OpenRouter (5 LLM providers) | Done |
| Anti-sycophancy scoring | 1-5 anchored scale + calibration prompts | Done |
| Observability | Langfuse tracing + cost tracking | Done |
| Agentic persona engine | LangGraph ReAct agent + tools | Planned (Phase 4) |
| Context projection | LLM selects relevant attributes per query | Planned (Phase 4) |
| Persona DB | SQLite with FTS5 + extended_attributes JSON | Planned (Phase 4) |
| Deterministic panel builder | Cultural holidays, life events, smart relaxation | Done |

## Project Structure

```
backend/
  main.py                         # FastAPI + LangGraph backend (SSE, 5 endpoints, multi-model)

frontend/
  src/app/page.tsx                # 8-step workflow state machine
  src/components/                 # UI components (panel, reactions, summary, comparison)
  src/lib/api.ts                  # SSE streaming client to backend
  src/lib/types.ts                # TypeScript types

scripts/
  generate_canada_personas.py     # Census-grounded persona generator (25 fields)
  enrich_personas_income.py       # Job Bank 2025 wage enrichment
  map_occupations_to_noc.py       # Occupation → NOC code mapping via LLM

canada_demographics_2021.py       # Statistics Canada 2021 Census probability weights

data/
  personas_5000.json              # 5,000 seed personas
  occupation_noc_mapping.json     # Occupation → NOC code mappings
  raw/                            # Source CSVs (Job Bank wages, etc.)

docs/
  MaplePulse-Plan.md              # Product plan + phased implementation
  NextSteps.md                    # Current priorities and roadmap
  DataSources.md                  # 30+ Canadian data sources catalog
  v3_architecture_sketch.py       # Agentic persona engine design sketch
  v2_architecture_sketch.py       # Multi-agent architecture (superseded)
  Progress.md                     # Session-by-session progress log
  Learning.md                     # How Ask Singapore works

docker-compose.yml                # 3 services: backend :8000, frontend :3000, notebook :8888
```

## Persona Fields

Each persona includes 25+ fields grounded in census distributions:

| Category | Fields | Source |
|----------|--------|--------|
| Core demographics | age, sex, marital_status, province, city | Census 2021 |
| Employment | occupation, noc_code, is_employed | Census 2021 + NOC |
| Income | estimated_annual_income, income_bracket, income_source | Job Bank 2025 wages |
| Education | education_level | Census 2021 |
| Identity | immigration_status, indigenous_identity, visible_minority, cultural_background | Census 2021 |
| Language | languages_spoken | Province-aware (QC=French, NB=bilingual) |
| Housing | housing, commute_mode | Census 2021 Journey to Work |
| Attitudes | political_leaning, religion, top_concerns | CES, Angus Reid, Environics |
| LLM-enriched | personality, skills, hobbies, career_goals | Claude / Anthropic |
| Extended (selective) | health, digital behavior, financial, civic, lifestyle, values, consumer | CCHS, CIRA, CFCS, GSS, Environics, etc. — populated per query via context projection |

## Quick Start

```bash
# Run all services with Docker
docker compose up

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Notebook: http://localhost:8888

# Generate skeleton personas (no API key needed)
python scripts/generate_canada_personas.py --count 50 --skeleton-only
```

**Environment variables needed:**
- `OPENROUTER_API_KEY` — for multi-model LLM reactions
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` — for observability

## Roadmap

See [docs/NextSteps.md](docs/NextSteps.md) for full details.

- **Phase 4 (current priority):** Agentic Persona Engine — SQLite DB, audience brief parser, dynamic persona generation with tool-calling agent, context projection (lean subagent prompts), deterministic panel builder with cultural/life-event maps, persistent caching
- **Phase 5:** Remaining use cases (product concept, A/B copy, survey pre-test)
- **Phase 6:** Frontend polish (A/B comparison view, PDF/CSV export, audience brief input)
- **Phase 7:** Geography & map (Canadian GeoJSON, sentiment by region)
- **Phase 8:** Deploy (branding, rate limiting, Vercel)

## Attribution

- **Aayush Mathur** — Original [Ask Singapore](https://github.com/AayushMathur7/ask-singapore) project
- **Statistics Canada** — 2021 Census of Population demographic data
- **NVIDIA** — Nemotron-Personas methodology inspiration
- **Job Bank Canada** — 2025 wage data for income enrichment
