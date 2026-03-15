# How ASK Singapore Was Built — Learning Guide

> Original project by **Aayush Mathur** ([GitHub](https://github.com/AayushMathur7/ask-singapore))
> Dataset: NVIDIA Nemotron-Personas-Singapore (CC BY 4.0)

---

## 1. What the App Does

ASK Singapore is an interactive web app where you type a question and thousands of synthetic Singaporean personas answer it. Responses are plotted on a Mapbox map of Singapore's 55 planning areas, color-coded by sentiment (green = positive, yellow = neutral, red = negative).

Think of it as: **an instant AI focus group of an entire country**.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                      FRONTEND                             │
│  Next.js 16 + React 19 + Tailwind CSS + shadcn/ui        │
│  react-map-gl (Mapbox) for geographic visualization       │
│                                                           │
│  User types question → selects filters → hits "Ask"       │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /api/ask
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    API ROUTE (Next.js)                     │
│                                                           │
│  1. Validate request (Zod schemas)                        │
│  2. Rate-limit by IP (20 req / 10 min)                    │
│  3. Load personas from JSON + area profiles               │
│  4. Filter personas by user criteria                      │
│  5. Stratified sample across planning areas               │
│  6. Send each persona + question to LLM in parallel       │
│  7. Collect structured JSON responses                     │
│  8. Aggregate sentiment per area                          │
│  9. Persist result to Convex DB                           │
│ 10. Return JSON response to frontend                      │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    LLM PROVIDERS                          │
│                                                           │
│  Google Gemini (primary, fastest)                         │
│  Anthropic Claude (with prompt caching)                   │
│  OpenAI GPT (with reasoning control)                      │
│                                                           │
│  Each call: persona profile → structured JSON reply       │
│  { answer, reasoning, stance (-2 to +2), confidence }     │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Data Pipeline (How Personas Are Prepared)

This is the most important part to understand for our Canada adaptation.

### Step 1: Source Data
- NVIDIA released a dataset of 888K synthetic personas for Singapore on HuggingFace
- Each persona has ~38 fields: age, sex, occupation, education, planning area, cultural background, skills, hobbies, career goals, etc.
- Data is stored as Parquet files

### Step 2: Python Processing (`scripts/prepare_personas.py`)
```
Input: 2 Parquet files from HuggingFace (888K records)
        ↓
Clean: Drop nulls, normalize planning areas, compact text fields
        ↓
Filter: Keep ages 18-120
        ↓
Sample: Stratified sample of ~5,000 across all 55 planning areas
        ↓
Output: personas.compact.v1.json (~4.9 MB)
```

Key design decisions:
- **Stratified sampling**: ensures every planning area gets represented (not just dense ones)
- **Text compaction**: persona summaries capped at 180 chars, other fields at 110-120 chars (keeps JSON small and LLM prompts short)
- **12 fields kept** per persona: uuid, age, sex, occupation, education_level, marital_status, planning_area, persona, cultural_background, skills_and_expertise, hobbies_and_interests, career_goals_and_ambitions

### Step 3: Area Profiles (`scripts/prepare_area_profiles.py`)
- Fetches real government data from Singapore's OneMap API + data.gov.sg
- Population demographics, ethnic groups, income, dwelling types, transport modes
- Amenity counts: hawker centres, supermarkets, schools, clinics
- HDB resale prices
- Generates a natural-language summary per area that gets injected into LLM prompts

---

## 4. How the LLM Prompting Works

This is the core intelligence of the app. Each persona gets a carefully constructed prompt:

```
System prompt structure:
1. Role instruction: "You are role-playing a synthetic persona from Singapore"
2. Behavior rules: Be natural, don't mention you're AI
3. Stance rubric: -2 (definitely not) to +2 (definitely yes)
4. Confidence instruction: 0 to 1 based on how clearly the profile supports the stance

5. The user's question

6. Persona Profile:
   - Age, Sex, Occupation, Education, Marital status
   - Planning area
   - Cultural background, Skills, Hobbies, Career goals
   - General persona summary

7. (Optional) Neighborhood context — real demographic data about their area

8. Output format: strict JSON { answer, reasoning, stance, confidence }
```

### Key Design Patterns:
- **Structured output via Vercel AI SDK's `generateObject()`** — forces the LLM to return valid JSON matching a Zod schema
- **Fallback chain**: if primary model fails, tries a fallback model (e.g., Gemini Flash → Gemini Flash, Claude 4.6 → Claude 4.5)
- **3 retries per model** with provider-specific delays (900ms Anthropic, 500ms OpenAI, 220ms Google)
- **Timeouts**: 22s Anthropic, 26s OpenAI, 10s Google
- **Concurrency limiting**: 3 parallel calls for Anthropic, 6 for others (respecting rate limits)
- **Temperature 0.6** — balanced between creative/diverse and consistent responses

---

## 5. Sampling Strategy

When a user asks a question with filters:

1. **Filter**: narrow down the 5,000 personas by age range, sex, occupation, planning area
2. **Stratified sample**: pick one persona from each planning area first (ensures geographic spread)
3. **Backfill**: if sample size > number of areas, randomly pick more from remaining candidates
4. **Sample sizes**: 5 to 200 personas per question (user-configurable)

This ensures responses aren't dominated by high-population areas.

---

## 6. Sentiment Aggregation

Each persona response includes:
- **stance**: integer from -2 to +2
- **confidence**: float from 0 to 1
- **score**: stance × confidence (e.g., stance=2, confidence=0.8 → score=1.6)

Aggregation:
- Per-area: average score of all personas in that area
- Overall: mean score across all responses
- Score → sentiment mapping: positive (>0.3), negative (<-0.3), neutral (in between)
- Map coloring: green → yellow → red based on area sentiment

---

## 7. Tech Stack Breakdown

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | Next.js 16 (App Router) | Server-side API routes + React frontend in one project |
| UI | Tailwind CSS + shadcn/ui | Fast, accessible component library |
| Map | react-map-gl + Mapbox GL JS | Interactive map with polygon rendering |
| Validation | Zod 4 | Runtime type safety for API requests/responses |
| LLM | Vercel AI SDK (`ai` package) | Unified interface for multiple LLM providers |
| Database | Convex | Real-time persistence for ask results and cohorts |
| Data prep | Python + Polars | Fast parquet processing |
| Deployment | Vercel | Seamless Next.js hosting |

---

## 8. File-by-File Guide

### Data & Scripts
| File | Purpose |
|------|---------|
| `scripts/prepare_personas.py` | Downloads NVIDIA parquet, stratified samples 5K personas, exports JSON |
| `scripts/prepare_area_profiles.py` | Fetches Singapore gov APIs, builds area demographic profiles |
| `public/data/personas.compact.v1.json` | The 5K persona records used at runtime |
| `public/data/area-profiles.json` | Per-area demographic summaries |
| `public/data/singapore-subzone-no-sea.geojson` | Singapore 55 planning area boundaries |

### Core Library (`src/lib/`)
| File | Purpose |
|------|---------|
| `schemas.ts` | All Zod schemas: Persona, AreaProfile, AskRequest, AskResponse, PersonaReply |
| `persona-store.ts` | Loads personas JSON, indexes by planning area |
| `area-profiles.ts` | Loads area profiles JSON, indexes by planning area |
| `gemini.ts` | LLM orchestration: prompt building, `generateObject()`, retries, fallbacks |
| `model-catalog.ts` | Model registry with provider config and fallback chains |
| `sampling.ts` | `filterPersonas()` and stratified `sampleFromCandidates()` |
| `sentiment.ts` | `aggregateSentiment()` — computes per-area and overall sentiment |
| `rate-limit.ts` | IP-based rate limiting (20 requests per 10 min) |
| `utils.ts` | Helper functions: normalizePlanningArea, shuffle, stanceToSentiment, scoreToSentiment |

### API Routes (`src/app/api/`)
| File | Purpose |
|------|---------|
| `api/ask/route.ts` | Main endpoint: filter → sample → LLM calls → aggregate → persist → respond |
| `api/chat/route.ts` | Chat endpoint for follow-up conversations |
| `api/cohort/create/route.ts` | Create reusable persona cohorts |
| `api/options/route.ts` | Returns available models and filter options |

### Frontend (`src/components/`)
| File | Purpose |
|------|---------|
| `ask-singapore-app.tsx` | Main UI: question bar, filters, results panel, model selector |
| `singapore-map.tsx` | Mapbox map with planning area polygons, sentiment coloring |
| `ui/*.tsx` | shadcn/ui primitives (button, card, dialog, etc.) |

---

## 9. Key Lessons for Building "Ask Canada"

### What we can reuse as-is:
- The entire Next.js framework and project structure
- LLM orchestration logic (`gemini.ts` — model fallbacks, retries, structured output)
- Sampling strategy (`sampling.ts` — stratified sampling works for any geography)
- Sentiment aggregation (`sentiment.ts`)
- Rate limiting, Zod schemas pattern, Convex persistence
- shadcn/ui components

### What must be replaced:
1. **Persona dataset** — Canada has no Nemotron equivalent; we need to generate synthetic personas from Statistics Canada census data
2. **GeoJSON boundaries** — Singapore planning areas → Canadian regions (provinces, CMAs, census subdivisions, or FSAs)
3. **Area profiles** — Singapore gov APIs → Statistics Canada APIs / Canadian open data
4. **Map configuration** — Center coordinates, zoom level, polygon property keys
5. **UI text and branding** — "Ask Singapore" → "Ask Canada", suggested questions, attribution

### What needs adaptation:
- `planning_area` field → `region` or `geographic_area` (used throughout schemas, sampling, aggregation)
- Persona schema fields → add Canadian-relevant fields (province, immigration_status, languages_spoken, indigenous_identity)
- Area profile schema → Canadian metrics (median home price vs HDB resale, community centres vs hawker centres)
- LLM prompt → "persona from Canada" with Canadian neighborhood context

---

## 10. Attribution Requirements

When building Ask Canada, we must credit:
- **Aayush Mathur** — original Ask Singapore creator and codebase
- **NVIDIA** — Nemotron-Personas-Singapore dataset (CC BY 4.0) if any derived data is used
- **Statistics Canada** — for census data used in persona generation
- **Mapbox** — for map rendering
- **Any Canadian open data sources** we use for area profiles