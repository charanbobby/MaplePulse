# MaplePulse — Technical YouTube Script

**Target audience:** Developers, AI/ML practitioners, data engineers
**Tone:** Technical walkthrough, architecture-focused, show the evolution
**Length:** ~10-12 minutes

---

## INTRO (30s)

- Hook: "I'll walk you through how this project evolved from a weekend fork to a multi-model agentic pipeline — and the problems I hit along the way"
- Quick context: What MaplePulse does (one sentence), then into the story

## WHERE IT STARTED (1.5 min)

- Discovered Ask Singapore by Aayush Mathur — synthetic personas for Singapore policy testing
- Thought: what would this look like for Canada?
- First version was straightforward: fork the idea, swap Singapore data for Canadian data
- Started with Statistics Canada 2021 Census — built probability weight tables for demographics
- Generated 5,000 skeleton personas from census distributions
- [PLACEHOLDER: Show the original census weight tables in canada_demographics_2021.py]

## PROBLEM 1: PERSONAS FELT FLAT (1.5 min)

- Raw census-weighted personas had demographics but no depth — just age/province/income
- Needed realistic income tied to actual occupation, not random
- Solution: Job Bank Canada 2025 wage data — mapped 516 NOC occupation codes to median wages
- Built a pipeline: occupation → NOC code (via LLM mapping) → real wage lookup → income bracket
- Then LLM enrichment for personality, hobbies, career goals — but grounded in the demographic base
- Key lesson: the data foundation matters more than the AI layer on top
- [PLACEHOLDER: Walk through the enrichment pipeline scripts]

## PROBLEM 2: REACTIONS WERE TOO POSITIVE (1.5 min)

- First pass: every persona loved every message — classic LLM sycophancy
- Tried prompt engineering, didn't help enough
- Solution: anchored scoring rubrics — defined what a 1, 3, and 5 actually mean with concrete examples
- Also: multi-model fan-out — same persona reacts via GPT-5-nano, Gemini-3-Flash, Mistral, Grok
- Different models have different biases — aggregating across them gives a more balanced signal
- Before/after: went from 90% positive to a realistic distribution
- [PLACEHOLDER: Show the scoring rubrics and a side-by-side of sycophantic vs. calibrated output]

## PROBLEM 3: ORCHESTRATION (1.5 min)

- Needed to coordinate: build panel → react (concurrent) → aggregate → optimize → re-test → compare
- LangGraph was the right fit — graph-based orchestration with state management
- SSE streaming from FastAPI backend so the frontend shows progress in real time
- Docker Compose for the full stack: backend, Next.js frontend, Jupyter notebook
- [PLACEHOLDER: Show the LangGraph graph definition and SSE streaming flow]

## THE DATA FOUNDATION (1 min)

- 30+ Canadian data sources: StatCan Census, CES, Angus Reid, CMHC, CIRA, Environics
- How probability weights work: census says 38% of Ontarians are 25-44 → persona generation follows that distribution
- Not random — statistically representative within the limits of the source data
- [PLACEHOLDER: Quick walkthrough of DataSources.md and weight tables]

## OBSERVABILITY (1 min)

- Langfuse tracing: every LLM call tracked with cost, latency, tokens
- Critical when you're fanning out across 4+ models for 20 personas — that's 80+ LLM calls per run
- How we monitor cost and catch regressions via OpenRouter
- [PLACEHOLDER: Show a Langfuse trace screenshot]

## WHERE IT'S GOING — AGENTIC ENGINE (1.5 min)

- Current limitation: static pool of 5,000 personas, panel selected by filtering
- Next evolution: ReAct agent that decides HOW to build the panel
- Agent has tools: search_personas (SQLite + FTS5), generate_personas, fetch_data, persist
- Context projection: LLM picks which persona attributes matter for THIS query — health query gets health fields, not all 25+
- Tavily search for real-time domain context
- The 5,000 personas become a seed corpus that grows with every query
- [PLACEHOLDER: Walk through v3_architecture_sketch.py]

## OUTRO (30s)

- Recap the evolution: census data → enrichment → anti-sycophancy → multi-model → agentic
- Stack: Python, FastAPI, LangGraph, Next.js, Docker, OpenRouter, Langfuse
- Credit Aayush Mathur / Ask Singapore as the original inspiration
- [PLACEHOLDER: Links, repo, subscribe]

---

**Notes:**
- Frame as a project evolution story — each section is a problem encountered and solved
- Show code and traces, not just slides
- Assume viewer knows Python and has basic LLM/agent awareness
- Credit Aayush Mathur / Ask Singapore as inspiration
- Keep it "here's how I built it and what I learned" energy