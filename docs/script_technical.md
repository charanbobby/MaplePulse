# MaplePulse — Technical Deep Dive

**Audience:** Hiring managers evaluating decision-making, system thinking, and AI-augmented product development
**Length:** ~20 minutes (walkthrough with diagrams, code, and traces)
**Style:** Honest narrative. Claude Code wrote most of the code — what matters here is the sequence of decisions, the problems I spotted, the architecture I shaped, and the interventions that turned AI output into a working product.
**Diagrams:** Open `diagrams_technical.html` in a browser alongside this script. Each section references a diagram by name.

---

## TABLE OF CONTENTS

1. [The Spark — Finding the Reference Project](#1-the-spark)
2. [Day 1: Census Data & Persona Generation](#2-day-1-census-data--persona-generation)
3. [The Enrichment Problem — Flat Personas](#3-the-enrichment-problem)
4. [The Jupyter Prototype — LangGraph Pipeline](#4-the-jupyter-prototype)
5. [Meta Prompting — OpenAI Playground as a Design Tool](#5-meta-prompting)
6. [Fanning Out — From Notebook to Full-Stack App](#6-fanning-out)
7. [The Sycophancy Problem — When Every Persona Loves Everything](#7-the-sycophancy-problem)
8. [The Agentic Engine — From Static Pool to ReAct Agent](#8-the-agentic-engine)
9. [Observability — Langfuse + Langflow for Trace Understanding](#9-observability)
10. [Production Deployment](#10-production-deployment)
11. [Evaluation Framework — Measuring Quality Before Handoff](#11-evaluation-framework)
12. [Architecture Evolution — The Full Picture](#12-architecture-evolution)
13. [What I'd Do Differently](#13-what-id-do-differently)

---

## 1. THE SPARK

> **[SCREEN: Show Ask Singapore repo]**

I found Ask Singapore by Aayush Mathur — a project that uses synthetic personas grounded in Singapore's census data to test policy messaging. I spent a full session reading every file: the data pipeline, the LLM prompting strategy, the sentiment aggregation, the sampling logic.

**My decision:** Canada has richer, more fragmented demographics than Singapore — 13 provinces/territories, 200+ ethnic origins, official bilingualism, Indigenous populations, massive immigration. A direct port wouldn't work. I needed to rebuild the data layer from scratch and design for this complexity.

**What I did first:** Created `Learning.md` — a comprehensive architectural breakdown of how Ask Singapore works, file by file. This became my reference document for every design decision that followed.

---

## 2. DAY 1: CENSUS DATA & PERSONA GENERATION

> **[SCREEN: Show `canada_demographics_2021.py` — the 13 weight tables]**

**My intervention:** I manually researched and structured 13 categories of probability weights from the Statistics Canada 2021 Census:

| Category | Source | Example |
|----------|--------|---------|
| Province populations | Census 2021 | Ontario 38.5%, Quebec 22.9% |
| Age distribution | Census 2021 | 25-34: 13.7%, 35-44: 12.8% |
| Education levels | Census 2021 | Bachelor's: 23.3% |
| Occupation (NOC) | Census 2021 | 10 broad categories |
| Income brackets | Census 2021 | 11 brackets |
| Immigration status | Census 2021 | 23% immigrants |
| Visible minorities | Census 2021 | 13 categories |
| Indigenous identity | Census 2021 | First Nations, Métis, Inuit |
| Languages | Census 2021 | Official + mother tongue |
| Marital status | Census 2021 | 5 categories |
| Housing | Census 2021 | Tenure, dwelling type |
| Political leaning | CES + Angus Reid | Province-weighted, age-adjusted |
| Religion | Census 2021 | With visible minority correlations |

Claude Code wrote the Python module. **I directed the architecture**: stratified generation across all 13 provinces (not random sampling), province-aware language assignment (Quebec = French-dominant, New Brunswick = bilingual), and cultural background templates for 15+ ethnic groups including Indigenous populations.

**Key code review intervention:** The first version used sequential API calls and brittle JSON string parsing for LLM enrichment. I directed the refactor to:
- `AsyncAnthropic` + `asyncio.gather` (batches of 10 concurrent calls)
- Anthropic tool use schema instead of JSON parsing — guarantees valid structured output every time

Result: 5,000 personas generated with 22 deterministic fields each.

---

## 3. THE ENRICHMENT PROBLEM

> **[SCREEN: Show a raw persona — barista making $120K]**
> **[DIAGRAM: "Persona Enrichment Pipeline"]**

**Problem I spotted:** The personas had random income. A 22-year-old barista in Winnipeg was assigned $120K. This destroys credibility with anyone who knows Canadian demographics.

**My decision chain:**
1. Downloaded Job Bank Canada 2025 wage data (516 NOC occupation codes with provincial median salaries)
2. Built an occupation → NOC code mapping (100+ job titles)
3. Designed age-adjusted income estimation (young workers → Q1/low quartile, mid-career → median-Q3, senior → Q3/high)
4. Non-employed personas get realistic estimates (CPP pension, student income, EI, disability support)
5. Later discovered Census 2021 income data has reference year 2020 — added CPI inflation factor of 1.23 to adjust to 2026 dollars

**Architecture decision:** Initially built income enrichment as a separate post-processing script (`enrich_personas_income.py`). After validating it worked, I directed integration directly into the generator so income is assigned at creation time — not as an afterthought. Personas went from 22 to 25 fields.

---

## 4. THE JUPYTER PROTOTYPE

> **[SCREEN: Show `experiments/01_focus_group_test.ipynb`]**
> **[DIAGRAM: "LangGraph Pipeline Flow"]**

This is where the core pipeline was born. I built the first end-to-end LangGraph pipeline in a Jupyter notebook — intentionally. Notebooks let me run each node independently, inspect intermediate state, and iterate on prompts without restarting a server.

**Pipeline designed in notebook:**
```
classify_intent → select_panel → run_reactions → aggregate → optimize_message → run_reactions_v2 → aggregate_v2
```

**My design decisions in the notebook phase:**
- **Intent classification** routes to 4 use cases: localization, product concept, A/B copy test, survey pre-test
- **Optimization loop**: Round 1 reactions feed into an LLM rewriter, then the same panel re-evaluates the improved message
- **Before/after comparison** with sentiment delta — this is the core value proposition (show the system actually helps)
- **Langfuse v4 integration** from day one — I wanted observability before scaling, not after

**What the notebook taught me:** The pipeline worked, but running it interactively revealed that prompt quality was the bottleneck. The code was fine. The prompts needed work. This is what led me to meta prompting.

---

## 5. META PROMPTING — OpenAI Playground as a Design Tool

> **[SCREEN: Show OpenAI Playground with prompt iterations]**

**This was a parallel workstream** that doesn't show up in git history but shaped every prompt in the system.

I used the OpenAI Playground as a meta-prompting environment — not to write code, but to design and stress-test the prompts that Claude Code would then implement. The workflow:

1. **Draft a system prompt** (e.g., the persona reaction prompt)
2. **Run it against edge cases** in the Playground — vague messages, culturally sensitive topics, multilingual content, deliberately bad copy
3. **Identify failure modes** — sycophancy, hallucinated features, generic reactions that could apply to anyone
4. **Iterate on the prompt** until it handles edge cases
5. **Hand the refined prompt to Claude Code** for integration into the codebase

**Why this matters:** Claude Code is excellent at writing code around a prompt, but it can't evaluate whether a prompt produces realistic human-like reactions. That evaluation requires domain judgment — knowing what a skeptical 55-year-old Alberta oil worker would actually think about a federal carbon tax message. The Playground let me be the quality gate for prompt design while Claude Code handled the engineering.

**Key prompts I designed this way:**
- The persona reaction prompt (with anchored scoring)
- The optimization/rewriter prompt (pattern-based changes, preserve vivid language)
- The context projection prompt (which persona fields matter for which query)
- The audience brief parser (converting free-text to structured spec)

---

## 6. FANNING OUT — From Notebook to Full-Stack App

> **[DIAGRAM: "Project Evolution: Notebook → Full-Stack Application"]**

Once the notebook prototype validated the pipeline, I made the decision to fan out into a proper application. This wasn't incremental — it was a deliberate architectural expansion.

### The Fan-Out Decision

The notebook proved the pipeline works. But notebooks don't give you:
- Real-time streaming (reactions appearing one by one)
- A reviewable UI (hiring managers won't run Jupyter)
- Separation of concerns (backend API vs. frontend state)
- Deployment

**My architectural choices for the fan-out:**

| Decision | Choice | Why |
|----------|--------|-----|
| Backend framework | FastAPI | Async-native, SSE support, Pydantic validation |
| Frontend framework | Next.js 15 + React 19 | Server components, App Router, TypeScript |
| Design system | UI/UX Pro Max skill | Data-dense dashboard aesthetic (Fira Code/Sans, blue + amber) |
| Model routing | OpenRouter | Single API for 5+ models, cost tracking |
| Streaming | Server-Sent Events | Simpler than WebSockets for unidirectional updates |
| Containerization | Docker Compose | 3 services (backend, frontend, notebook) |

**Frontend-first approach:** I had Claude Code build the complete 8-step UI with mock data before connecting to the backend. This let me validate the workflow experience — input → panel → reactions → summary → optimize → round 2 → summary → comparison — before any real LLM calls. The mock data included deliberately negative reactions (avg sentiment 3.75, 0% resonance in R1) to test that the UI handles critical feedback, not just positive results.

---

## 7. THE SYCOPHANCY PROBLEM

> **[SCREEN: Show performance log — R1 resonance 95-100%, sentiment 6.5-7.2/10 regardless of input]**
> **[DIAGRAM: "Anti-Sycophancy Rubric Redesign"]**

**This was the biggest quality problem in the project.** After connecting the real backend, I ran multiple scenarios and checked the performance logs. Every single message got 95-100% resonance and sentiment scores of 6.5-7.2 out of 10. A mediocre ad got the same reaction as a brilliant one.

**Problem diagnosis (my analysis):**
1. LLMs default to being agreeable — it's in their training
2. A 1-10 scale with no anchors lets the model cluster at 7 (safe positive)
3. Boolean `resonates: true/false` defaults to `true`
4. Labels like "perfect" for tone fit bias toward positive selection

**My intervention — the anti-sycophancy rubric redesign:**

| Dimension | Before (v1) | After (v2) | Why |
|-----------|-------------|------------|-----|
| Sentiment | 1-10 (no anchors) | 1-5 with anchored descriptions (1=hostile, 2=skeptical, 3=neutral, 4=interested, 5=enthusiastic) | Narrower scale + anchors reduce tendency to cluster at 7+ |
| Resonance | boolean (true/false) | `relevance` enum: irrelevant / somewhat / directly_relevant | Binary forced "yes" default; three levels allow honest "meh" |
| Tone fit | perfect / acceptable / off / offensive | natural / acceptable / awkward / offensive | "Perfect" is aspirational and biases toward selection; "natural" is descriptive |
| Calibration | None | Explicit anti-sycophancy prompt section | "Score independently. Do not default to positive scores." |

**Result:** Went from 90% positive (regardless of input quality) to a realistic distribution where mediocre messages get mediocre scores.

**The multi-model rotation was my second lever.** Instead of relying on one model, each persona is assigned a different model from a pool of 5 (GPT-5.4-nano, GPT-5.4-mini, Mistral Small, Gemini 3 Flash, Grok 4 Beta) via round-robin. Different models have different biases. Spreading the panel across them produces a more honest aggregate signal than any single model alone.

**Why this matters for the product:** If every persona loves every message, the tool is useless. The entire value proposition is that MaplePulse tells you what's wrong with your messaging before you spend money on real research. Sycophantic reactions destroy that.

---

## 8. THE AGENTIC ENGINE

> **[SCREEN: Show `backend/panel_engine.py` — the ReAct agent]**
> **[DIAGRAM: "Agentic Panel Building (v3 Architecture)"]**

**Problem with v2:** The static persona pool (5,000 JSON records) could only be filtered by demographics. If a user typed "Costco shoppers in suburban Ontario" — there was no way to find them. You had to manually pick province = Ontario, income bracket = middle, and hope.

**My architecture decision for v3:** Replace the static filter with a ReAct agent that has tools.

The agent has three tools:
- **search_personas** — queries the SQLite DB with FTS5 full-text search
- **generate_personas** — creates new personas on-the-fly from census data
- **fetch_data** — pulls relevant Canadian domain data

It reasons about gaps, calls tools, evaluates results, and repeats until the panel is complete (12-20 personas).

**Key decisions I made in the agentic engine:**

1. **SQLite over PostgreSQL** — Simplicity. FTS5 full-text search is fast enough. Docker named volume for persistence. Can migrate later if needed.

2. **5,000 personas as seed, not ceiling** — The JSON pool becomes the starting point. The database grows with every run. Generated personas are persisted for reuse.

3. **Context projection** — Not every field matters for every query. A health question should weight health and lifestyle fields. A financial product should weight income and spending. I designed this as a separate LLM step before the agent runs, so the agent knows what to look for.

4. **Model cost optimization** — Switched from GPT-5.4 to GPT-5.4-mini for the agent (~10x cheaper). The agent doesn't need the best model — it needs to call tools correctly.

5. **CPI inflation adjustment** — Census 2021 income data uses 2020 reference year. I added a 1.23 inflation factor so a persona's income reflects 2026 purchasing power, not 2020.

---

## 9. OBSERVABILITY — Langfuse + Langflow

> **[SCREEN: Show Langfuse trace dashboard]**
> **[DIAGRAM: "Observability Stack"]**

With 12 personas reacting across rotating models in two rounds, plus the agentic panel builder and optimizer, that's ~30 LLM calls per run. You need to see what's happening.

### Langfuse — Production Tracing

**My integration decisions:**
- Every LLM call is traced — model, tokens, cost, latency
- Custom `OpenRouterLangfuseHandler` extracts cost from OpenRouter response metadata (OpenRouter returns cost per call, Langfuse doesn't know this natively)
- Session ID grouping — all calls within a focus group run share a session ID so I can see the full pipeline as one trace
- Named spans for each pipeline phase: `parse_audience_brief`, `context_projection`, `panel_builder_agent`, `round_1_reactions`, `optimizer`, `round_2_reactions`

### Langflow — Understanding Trace Topology

> **[SCREEN: Show Langflow trace visualization]**

**I used Langflow as a complementary tool** — not for building the pipeline (which is LangGraph code), but for visually inspecting how LLM calls chain together. When you have a multi-step pipeline with branching and parallel calls, seeing the topology as a visual graph helps you understand:
- Where time is being spent (which phase is the bottleneck?)
- Where calls are happening in parallel vs. sequentially
- Whether the agent is making too many tool calls (a sign of bad prompting)
- Cost distribution across pipeline phases

This visual understanding informed several optimizations — like realizing the agent was making 6-7 search calls when 2-3 were sufficient, which led me to tighten the agent's system prompt.

---

## 10. PRODUCTION DEPLOYMENT

> **[SCREEN: Show maplepulse.sshub.dev]**
> **[DIAGRAM: "3-Phase Split Workflow (Human-in-the-Loop)"]**

**Deployment decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cloud provider | Hetzner | Cost-effective for a demo/portfolio project |
| Reverse proxy | Nginx | Routes :80/:443 → backend :8000 + frontend :3000 |
| SSL | Let's Encrypt via Certbot | Free, automated renewal |
| DNS | Cloudflare → maplepulse.sshub.dev | Fast propagation, DDoS protection |
| Secrets | `.env` on server only | Never in git, never in Docker image |
| DB persistence | Docker named volume (`backend-db`) | SQLite survives container rebuilds |

**The 3-phase split workflow** was a deployment-stage decision. Instead of running the entire pipeline at once (which could take 2-3 minutes with no feedback), I split it:

- **Phase 1: Build Panel** — User provides audience brief → agent builds panel → user reviews 12-20 personas → user approves before proceeding
- **Phase 2: Run Reactions** — Panel reacts to message (1 call per persona, model rotated across pool of 5) → quality filtering → user reviews reactions → user can exclude bad ones before continuing
- **Phase 3: Optimize & Compare** — LLM rewrites message → same panel re-evaluates → before/after comparison with sentiment delta, relevance delta

**Why the split matters:** It gives users control. They can remove a persona that doesn't fit before wasting LLM calls on reactions. They can exclude a low-quality reaction before it pollutes the optimization. This is a trust-building design — the system shows its work.

---

## 11. EVALUATION FRAMEWORK — Measuring Quality Before Handoff

> **[DIAGRAM: "Evaluation Framework"]**

Before handing the project to the testing team, I needed to answer: how do we know the system is actually good? Langfuse tells you what the LLMs did. It doesn't tell you whether a 55-year-old Alberta rancher's reaction sounds authentic, or whether the optimizer hallucinated a claim that wasn't in the original.

**My design decision:** Build a 10-eval framework that combines automated checks (fire every run, no human needed) with human-in-the-loop judgments (testers vote thumbs up/down as they use the app). Store everything in SQLite alongside the persona DB, linked to Langfuse traces via `trace_id`.

### The 10 Evals

| #  | Eval                         | Type                  | What It Catches                                                  |
| -- | ---------------------------- | --------------------- | ---------------------------------------------------------------- |
| 01 | Brand Voice Consistency      | Human (thumbs up/down) | Optimizer strips personality, outputs generic corporate copy     |
| 02 | Optimization Length Drift    | Automated             | Optimizer inflates 14 words into 70 (first run caught 5x drift) |
| 03 | Panel Selection Stability    | In-app tracking       | Panel builder produces poor fits — tracked by removal rate       |
| 04 | Reaction Removal Rate        | In-app tracking       | Reactions are off-target — tracked by exclusion rate at R1 review |
| 05 | Sentiment-Reaction Alignment | Human (thumbs up/down) | Core sycophancy check: does the score match the text?            |
| 06 | Persona Faithfulness         | Human (thumbs up/down) | All personas sound the same regardless of demographics           |
| 07 | Optimization Faithfulness    | Human (thumbs up/down) | Optimizer hallucinates claims not in original                    |
| 08 | Metrics Improvement          | Automated             | R2 should beat R1 — if not, optimizer is broken                  |
| 09 | A/B Position Bias            | Automated             | LLMs prefer first/last option regardless of content              |
| 10 | Context Projection Relevance | Golden set test       | Context projection misses important attribute groups              |

### Architecture Decisions

**Why not just use Langfuse for evals?** Langfuse captures LLM traces — prompts, completions, cost, latency. But it can't capture human judgment. When a tester reads a reaction and thinks "this doesn't sound like a 65-year-old farmer," that signal needs to be logged somewhere. The eval SQLite DB captures these human signals. The two systems are linked by `trace_id` — you can find a bad eval vote and pull up the full Langfuse trace to understand why.

**Embedded, not bolted on:** The eval UI is woven into the existing workflow. Testers don't fill out a separate form. They see "Score match?" and "Authentic?" buttons right next to each reaction. They see "Brand voice preserved?" and "No hallucinated claims?" on the final comparison page. The act of testing the product IS the act of generating eval data.

**Automated evals fire silently.** Every focus group run logs length drift (word count ratio), metrics improvement (R1 vs R2 deltas), and A/B position bias automatically. The tester doesn't even know it's happening.

**Pass criteria are pre-defined:** Each eval has a threshold (e.g., >85% thumbs-up for sentiment alignment, <25% panel removal rate, word count ratio ≤ 1.3x). After enough runs, `GET /api/eval/summary` returns pass rates for all 10 evals.

---

## 12. ARCHITECTURE EVOLUTION — The Full Picture

> **[DIAGRAM: "MaplePulse — Current System Architecture"]**

The system today has three layers:

**Frontend (Next.js 15):** 13 React components, 8-step workflow state machine, SSE streaming client. React 19, TypeScript, Tailwind v4.

**Backend (FastAPI):** 12 API endpoints (8 core + 4 eval), LangGraph orchestration, agentic panel engine (2,131 lines), SSE streaming, Pydantic validation. Handles ~30 LLM calls per full run. Eval framework with SQLite storage, automated logging, and aggregation endpoints.

**Data & Infrastructure:** SQLite + FTS5 persona DB, SQLite eval DB (linked via trace_id to Langfuse), 5,000 seed personas, Census 2021 weights (13 tables), Job Bank 2025 wages (516 NOC codes), OpenRouter (5 LLM models), Langfuse tracing. Deployed on Hetzner behind Nginx with Let's Encrypt SSL.

---

## 13. WHAT I'D DO DIFFERENTLY

**If I started over:**

1. **Regenerate the 5K personas with income baked in** — The current `personas_5000.json` predates the income integration. It still works (income gets assigned at load), but a clean regeneration would be better.

2. **Start with the 3-phase split from day one** — The original monolithic pipeline was a detour. The split workflow is strictly better.

3. **Geography visualization** — Canadian GeoJSON with sentiment by region would make the results immediately compelling. This is on the roadmap.

---

## SUMMARY — My Role vs. AI's Role

> **[DIAGRAM: "What I Did vs. What Claude Code Did"]**

For hiring managers who want to know what I actually did vs. what Claude Code did:

**My Decisions & Interventions:**
- Found and analyzed the reference project (Ask Singapore)
- Researched and structured 13 Census data categories
- Researched 30+ Canadian data sources
- Designed stratified persona generation strategy
- Identified flat persona problem, designed income enrichment pipeline
- Discovered CPI inflation gap, added 1.23 adjustment factor
- Identified sycophancy from performance logs
- Designed anchored scoring rubric (1-5 with descriptions)
- Decided on multi-model rotation for bias reduction
- Designed all prompts via meta prompting in OpenAI Playground
- Chose the agentic architecture (ReAct + tools)
- Designed context projection as a separate phase
- Designed 3-phase split workflow with human checkpoints
- Designed 10-eval framework (automated + human-in-the-loop) with pass criteria
- Made all technology choices (FastAPI, LangGraph, Next.js, OpenRouter, etc.)
- Directed code reviews (async refactor, tool use over JSON parsing)
- Used Langflow for visual trace analysis and optimization
- Made deployment decisions (Hetzner, Nginx, Docker volumes)

**Claude Code's Implementation:**
- Wrote the Python demographics module (536 lines)
- Wrote the persona generator (902 lines)
- Wrote the income enrichment script (291 lines)
- Built the LangGraph pipeline in Jupyter
- Wrote the FastAPI backend (1,424 lines)
- Wrote the agentic panel engine (2,131 lines)
- Built all 13 React components (~10K lines TSX)
- Wrote the SSE streaming client
- Implemented scoring rubric changes across frontend + backend
- Built eval infrastructure (SQLite storage, 4 API endpoints, reusable EvalVote component)
- Built Docker Compose configs
- Wrote deployment scripts
- Implemented Langfuse integration
- Handled all refactoring (async, type safety, etc.)

**The pattern:** I identified problems, designed solutions, chose technologies, crafted prompts, and directed architecture. Claude Code turned those decisions into working code — fast and reliably. The skill is knowing *what* to build and *when* to intervene, not typing the code yourself.

---

## GIT HISTORY — The Commit Trail

For those who want to trace the evolution through commits:

| # | Commit | What Changed | My Key Decision |
|---|--------|-------------|-----------------|
| 1 | `2a762c8` | Initial commit — demographics module + persona generator | Adapt Ask Singapore for Canada using real Census data |
| 2 | `030e1c1` | LangGraph pipeline + Jupyter notebook | Build the pipeline as a notebook first for rapid iteration |
| 3 | `fa30c67` | Income enrichment + v2 architecture sketch | Ground income in real Job Bank wages, not random assignment |
| 4 | `0e8faf7` | Simplify v2 — defer Critic Agent | Cut scope: focus on Orchestrator + Subagents, defer complexity |
| 5 | `93491c0` | Full-stack app — FastAPI + Next.js + Docker | Fan out from notebook to production architecture |
| 6 | `0ecaed5` | Anti-sycophancy rubric rework | Redesign scoring to produce honest reactions, not polite ones |
| 7 | `46aaccb` | Favicon/manifest assets | (Housekeeping) |
| 8 | `3790335` | Agentic engine + production deployment + landing page | Replace static pool with ReAct agent; deploy to Hetzner |
| 9 | (pending) | 10-eval framework for testing handoff | Build automated + human-in-the-loop eval system before handing to testers |

---

## TECHNICAL STATS

| Metric | Value |
|--------|-------|
| Total Python code | ~18,000 lines |
| Total TypeScript/TSX | ~10,400 lines |
| Documentation | ~16,300 lines |
| Jupyter notebooks | ~4,900 lines |
| **Total codebase** | **~50,000 lines** |
| Seed personas | 5,000 (Census-grounded) |
| Persona fields | 25 (21 deterministic + 4 LLM-enriched) |
| Canadian data sources | 30+ |
| LLM models used | 5 (GPT-5.4-nano, GPT-5.4-mini, Mistral Small, Gemini 3 Flash, Grok 4 Beta) |
| API endpoints | 12 (8 core + 4 eval) |
| React components | 14 (13 core + EvalVote) |
| Eval framework | 10 evals (4 automated, 4 human, 2 hybrid) |
| LLM calls per full run | ~30 (12 R1 + 1 optimizer + 12 R2 + ~5 panel agent) |
| Development time | 9 sessions over 9 days (Mar 14-22, 2026) |
| Deployment | maplepulse.sshub.dev (Hetzner, Docker, Nginx, SSL) |

---

## NOTES FOR WALKTHROUGH

- **Open `diagrams_technical.html`** in a browser tab — switch to it when the script says `[DIAGRAM: ...]`
- **Show git log** to demonstrate the commit-by-commit evolution
- **Show a Langfuse trace** of a real run — point out cost, latency, model distribution
- **Show the performance log** before and after the sycophancy fix
- **Run a live demo** if time permits — type an audience brief and show the 3-phase flow
- **Don't apologize for using AI tools** — the value is in the decisions, not the keystrokes
- Assume the viewer knows Python and has basic LLM awareness
- Each section: show the problem, show your decision, show the result, move on
