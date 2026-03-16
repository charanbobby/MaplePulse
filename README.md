# MaplePulse

Synthetic focus group service for Canada. Ask a question or test a marketing message against thousands of AI personas grounded in real Statistics Canada 2021 Census demographics.

Inspired by [Ask Singapore](https://github.com/AayushMathur7/ask-singapore) by Aayush Mathur.

## How It Works

1. **5,000 synthetic personas** are generated from real Canadian census distributions (province, age, sex, occupation, education, income, immigration status, Indigenous identity, visible minority, religion, political leaning, and more)
2. **A LangGraph pipeline** classifies your input, selects a demographic panel, runs persona reactions concurrently via LLM, aggregates sentiment, then optimizes your message and re-tests it

```
                          MAPLEPULSE — END-TO-END FLOW
  ═══════════════════════════════════════════════════════════════

  MARKETER                         MAPLEPULSE ENGINE
  ────────                         ─────────────────

  ┌─────────────────────┐
  │  Paste marketing     │
  │  message, product    │
  │  concept, survey Q,  │
  │  or A/B copy         │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  1. CLASSIFY INTENT │────▶│  LLM (temp=0) classifies input   │
  │     (LangGraph)     │     │  into 1 of 4 use cases:          │
  └──────────┬──────────┘     │                                  │
             │                │  ● localization   (active)       │
             │                │  ● product_concept (wip)         │
             │                │  ● ab_copy_test    (wip)         │
             │                │  ● survey_pretest  (wip)         │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  2. SELECT PANEL    │────▶│  Sample N personas from 5,000    │
  │                     │     │  Filters: province, age range    │
  └──────────┬──────────┘     │  Deterministic seed for repro    │
             │                └──────────────────────────────────┘
             │
             │                ┌──────────────────────────────────┐
             │                │  PERSONA POOL (5,000)            │
             │                │  ┌────────────────────────────┐  │
             │                │  │ age: 42                    │  │
             │                │  │ province: British Columbia  │  │
             │                │  │ occupation: Elevator Mech.  │  │
             │                │  │ income_bracket: $60K-$80K   │  │
             │                │  │ cultural_bg: English-Cdn    │  │
             │                │  │ languages: French           │  │
             │                │  │ political: centre-left      │  │
             │                │  │ concerns: housing, transit  │  │
             │                │  │ ... 28 fields total         │  │
             │                │  └────────────────────────────┘  │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  3. RUN REACTIONS   │────▶│  For each persona (concurrent):  │
  │     ROUND 1         │     │                                  │
  │                     │     │  ┌────────────┐  ┌────────────┐  │
  └──────────┬──────────┘     │  │ Persona 1  │  │ Persona 2  │  │
             │                │  │   ┌─────┐  │  │   ┌─────┐  │  │
             │                │  │   │ LLM │  │  │   │ LLM │  │  │
             │                │  │   └──┬──┘  │  │   └──┬──┘  │  │
             │                │  │      ▼     │  │      ▼     │  │
             │                │  │ Structured │  │ Structured │  │
             │                │  │  Output    │  │  Output    │  │
             │                │  └────────────┘  └────────────┘  │
             │                │       ... x 20 concurrent ...    │
             │                │                                  │
             │                │  Each returns:                   │
             │                │   reaction: "Sounds handy but    │
             │                │     Metro aint in Van..."        │
             │                │   _meta:                         │
             │                │     sentiment_score: 6/10        │
             │                │     resonates: true              │
             │                │     tone_fit: acceptable         │
             │                │     cultural_flags: [...]        │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  4. AGGREGATE       │────▶│  DISPLAYED to marketer:          │
  │     ROUND 1         │     │   20 persona reactions (quotes)  │
  └──────────┬──────────┘     │                                  │
             │                │  HIDDEN metadata:                │
             │                │   avg sentiment: 6.8/10          │
             │                │   resonance: 95%                 │
             │                │   tone fit distribution          │
             │                │   top cultural flags             │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  5. OPTIMIZE        │────▶│  LLM receives:                   │
  │     MESSAGE         │     │   original message               │
  │                     │     │   + all 20 verbatim reactions     │
  └──────────┬──────────┘     │   + aggregated metadata          │
             │                │                                  │
             │                │  Outputs:                        │
             │                │   improved_message (rewritten)   │
             │                │   changes_made (list of fixes)   │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  6. RUN REACTIONS   │────▶│  SAME panel, SAME prompts        │
  │     ROUND 2         │     │  but with the OPTIMIZED message  │
  │                     │     │  20 concurrent LLM calls again   │
  └──────────┬──────────┘     └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │  7. AGGREGATE v2    │────▶│  BEFORE / AFTER COMPARISON       │
  │     + COMPARE       │     │                                  │
  └──────────┬──────────┘     │  Metric          R1    R2  Delta │
             │                │  ─────────────────────────────── │
             │                │  Avg Sentiment   6.8   7.5  +0.7 │
             │                │  Resonance %      95   100   +5% │
             │                │  Cultural Flags   12     3    -9 │
             │                │  Tone: perfect     7    14    +7 │
             │                └──────────────────────────────────┘
             ▼
  ┌─────────────────────┐
  │  MARKETER RECEIVES: │
  │                     │
  │  ● Original message │
  │  ● Optimized message│
  │  ● List of changes  │
  │  ● 40 reactions     │
  │    (20 per round)   │
  │  ● Before/after     │
  │    comparison table  │
  │  ● Cultural flags   │
  │    & regional issues │
  └─────────────────────┘


  DATA FOUNDATION
  ═══════════════

  Statistics Canada          Job Bank Canada         Other Sources
  2021 Census                2025 Wages CSV          ─────────────
  ─────────────              ──────────────          CES (political)
  province, age, sex         516 NOC codes           Angus Reid (concerns)
  education, housing         low/median/high wage    Environics (values)
  immigration, Indigenous    by province             Journey to Work
  visible minority, language
  marital status, religion
            │                      │                       │
            └──────────┬───────────┘───────────────────────┘
                       ▼
              ┌─────────────────┐
              │  5,000 PERSONAS │
              │  28 fields each │
              │  seed=42 repro  │
              └─────────────────┘
```

## Future State: Hierarchical Multi-Agent Architecture

```
                    MAPLEPULSE v2 — HIERARCHICAL MULTI-AGENT
  ═══════════════════════════════════════════════════════════════

  Key changes from v1:
    - Single LLM pretending to be 20 people  -->  20 independent subagents
    - One model (GPT-5-mini)                 -->  Multi-model (GPT-5-mini, Gemini 3 Flash, etc.)
    - Simple aggregation                     -->  Dedicated Critic Agent reviews for bias
    - Workflow (fixed pipeline)              -->  Orchestrator with agency + delegation


  MARKETER
  ────────
  ┌─────────────────────┐
  │  Paste marketing     │
  │  message / concept   │
  └──────────┬──────────┘
             │
             ▼
  ┌══════════════════════════════════════════════════════════════┐
  ║                   ORCHESTRATOR AGENT                        ║
  ║  (manages the overall goal, delegates, tracks progress)     ║
  ║                                                             ║
  ║  Responsibilities:                                          ║
  ║  - Classify intent (use case routing)                       ║
  ║  - Select panel composition strategy                        ║
  ║  - Spawn persona subagents with model assignments           ║
  ║  - Collect raw reactions                                    ║
  ║  - Hand off to Critic Agent for evaluation                  ║
  ║  - Decide: optimize & re-run, or finalize                   ║
  ║  - Compile final report for marketer                        ║
  ║                                                             ║
  ║  Model: GPT-5-mini (cheap, fast orchestration)              ║
  ║  Context: clean — delegates all persona work to subagents   ║
  ╚═══════════════╤════════════════════════════════╤════════════╝
                  │                                │
          ┌───────┘                                └───────┐
          │  spawn N stateless subagents                   │
          ▼                                                ▼

  ┌─────────────────────────────────────────────────────────────┐
  │              PERSONA SUBAGENTS (stateless)                  │
  │                                                             │
  │  Each subagent:                                             │
  │  - Receives ONE persona profile + the marketing message     │
  │  - Has NO memory of other personas (no context rot)         │
  │  - Returns structured reaction + metadata                   │
  │  - Dies after responding (stateless)                        │
  │                                                             │
  │  Multi-model assignment (round-robin or stratified):        │
  │                                                             │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
  │  │Persona 1 │ │Persona 2 │ │Persona 3 │ │Persona 4 │  ...  │
  │  │          │ │          │ │          │ │          │       │
  │  │GPT-5-mini│ │Gemini 3  │ │GPT-5-mini│ │Gemini 3  │       │
  │  │          │ │  Flash   │ │          │ │  Flash   │       │
  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
  │       │            │            │            │              │
  │       ▼            ▼            ▼            ▼              │
  │   reaction     reaction     reaction     reaction           │
  │   + _meta      + _meta      + _meta      + _meta            │
  │                                                             │
  │  Why multi-model?                                           │
  │  - Different LLMs have different "personalities" & biases   │
  │  - Reduces monoculture risk (all reactions sounding same)   │
  │  - Cheap models: ~$0.001/reaction, cost is negligible       │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             │  raw reactions collected
                             ▼
  ┌══════════════════════════════════════════════════════════════┐
  ║                     CRITIC AGENT                            ║
  ║  (dedicated evaluator — quality gate before final output)   ║
  ║                                                             ║
  ║  Receives:                                                  ║
  ║  - All raw reactions from subagents                         ║
  ║  - Original marketing message                               ║
  ║  - Panel demographics                                       ║
  ║                                                             ║
  ║  Checks for:                                                ║
  ║  ┌─────────────────────────────────────────────────┐        ║
  ║  │  BIAS DETECTION                                 │        ║
  ║  │  - Are reactions suspiciously uniform?           │        ║
  ║  │  - Positivity bias (all too nice)?              │        ║
  ║  │  - Sycophancy (agreeing with the ad too much)?  │        ║
  ║  │  - Model-specific patterns (GPT vs Gemini)?     │        ║
  ║  ├─────────────────────────────────────────────────┤        ║
  ║  │  CONSISTENCY CHECK                              │        ║
  ║  │  - Does a 19yo student sound like a 19yo?       │        ║
  ║  │  - Does a Quebec francophone mention French?    │        ║
  ║  │  - Are income-sensitive reactions realistic?     │        ║
  ║  ├─────────────────────────────────────────────────┤        ║
  ║  │  OUTLIER FLAGGING                               │        ║
  ║  │  - Flag reactions that contradict their persona  │        ║
  ║  │  - Flag identical/near-duplicate responses       │        ║
  ║  │  - Flag hallucinated store names / brands        │        ║
  ║  └─────────────────────────────────────────────────┘        ║
  ║                                                             ║
  ║  Outputs:                                                   ║
  ║  - Validated reactions (flagged or approved)                 ║
  ║  - Bias report (model-level & panel-level)                  ║
  ║  - Confidence score for the overall focus group run          ║
  ║  - Recommendations: re-run flagged personas? adjust panel?   ║
  ║                                                             ║
  ║  Model: GPT-5-mini (or stronger model for critical eval)    ║
  ╚═══════════════════════════╤═════════════════════════════════╝
                              │
                              │  validated reactions
                              ▼
  ┌══════════════════════════════════════════════════════════════┐
  ║                   ORCHESTRATOR AGENT                        ║
  ║                   (decision point)                          ║
  ║                                                             ║
  ║  IF critic flagged issues:                                  ║
  ║    -> Re-spawn flagged persona subagents (different model)  ║
  ║    -> Re-submit to Critic                                   ║
  ║                                                             ║
  ║  IF reactions are clean:                                    ║
  ║    -> Aggregate results                                     ║
  ║    -> Generate optimized message                            ║
  ║    -> Spawn Round 2 subagents with optimized message        ║
  ║    -> Critic validates Round 2                              ║
  ║    -> Compile before/after comparison                       ║
  ║    -> Return final report to marketer                       ║
  ╚═══════════════════════════╤═════════════════════════════════╝
                              │
                              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    MARKETER RECEIVES                        │
  │                                                             │
  │  Everything from v1, PLUS:                                  │
  │  - Bias report from Critic Agent                            │
  │  - Confidence score for the run                             │
  │  - Model diversity breakdown (which LLM said what)          │
  │  - Flagged/re-run reactions marked                          │
  │  - Richer before/after with critic commentary               │
  └─────────────────────────────────────────────────────────────┘


  ARCHITECTURE COMPARISON
  ═══════════════════════

  v1 (Current — Workflow)          v2 (Future — Hierarchical Multi-Agent)
  ─────────────────────────        ─────────────────────────────────────
  Single LangGraph pipeline        Orchestrator + Subagents + Critic
  1 model per run                  Multiple models (GPT-5, Gemini 3, etc.)
  1 LLM call = 1 persona           1 subagent = 1 persona (isolated)
  All personas share context       Each subagent: clean context window
  Simple aggregation               Critic validates before aggregation
  Fixed 2-round loop               Orchestrator decides: re-run or finalize
  No bias detection                Critic checks for sycophancy & uniformity
  ~20 concurrent calls             ~20 concurrent subagent spawns
  Same model = same blind spots    Model diversity = different perspectives
```

## Use Cases

| Use Case | Status | Description |
|----------|--------|-------------|
| Localization | Active | Test how a marketing message lands across Canadian regions |
| Product Concept | WIP | Get reactions to a product/service idea |
| A/B Copy Test | WIP | Compare two versions of ad copy |
| Survey Pre-Test | WIP | Test survey questions for clarity and bias |

## Project Structure

```
scripts/
  generate_canada_personas.py   # Generate personas from census data (skeleton + LLM enrichment)
  map_occupations_to_noc.py     # Map occupations to NOC 2021 codes via LLM
  enrich_personas_income.py     # Enrich personas with Job Bank 2025 wage data

canada_demographics_2021.py     # Statistics Canada 2021 Census data as probability weights

data/
  personas_5000.json            # Generated persona dataset
  occupation_noc_mapping.json   # Occupation → NOC code mappings
  raw/                          # Source CSVs (Job Bank wages, etc.)

experiments/
  01_focus_group_test.ipynb     # LangGraph focus group pipeline notebook
  run_test1.py                  # Standalone test script

docs/
  Plan.md                      # Research on Canadian persona data sources
  Learning.md                  # How Ask Singapore works (architecture deep dive)
  NextSteps.md                 # Phased implementation plan
  DataSources.md               # 30+ public Canadian data sources catalog
  Progress.md                  # Session-by-session progress log

ask-singapore/                  # Cloned reference project
```

## Persona Fields

Each persona includes 28 fields grounded in census distributions:

| Field | Source |
|-------|--------|
| age, sex, marital_status | Census 2021 |
| province, planning_area (CMA) | Census 2021 population weights |
| occupation | NOC broad categories + exemplar job titles |
| education_level | Census 2021 (25-64 working age) |
| immigration_status | Census 2021 |
| indigenous_identity | Census 2021 |
| visible_minority | Census 2021 |
| languages_spoken | Province-aware (QC=French-dominant, NB=bilingual) |
| housing | Census 2021 tenure + dwelling type |
| cultural_background | 15+ ethnic/cultural group templates |
| political_leaning | CES/Angus Reid, province-weighted, age-adjusted |
| religion | Census 2021, visible minority-correlated |
| top_concerns | Province-specific (Angus Reid, Environics, CoT surveys) |
| commute_mode | Census 2021 Journey to Work, urban/rural split |
| noc_code, noc_title | NOC 2021 (LLM-mapped from occupation) |
| estimated_annual_income | Job Bank 2025 wages by NOC + province, age-adjusted |
| income_bracket | Derived: Under $20K / $20K-$40K / ... / $150K+ |
| is_employed | Derived from occupation type |
| persona, skills_and_expertise, hobbies_and_interests, career_goals_and_ambitions | LLM-enriched |

## Tech Stack

- **LangGraph** - Pipeline orchestration with optimization loop
- **LangChain + OpenRouter** - LLM calls (Gemini, GPT-5 via OpenRouter)
- **Langfuse** - Observability and tracing
- **Pydantic** - Structured output schemas
- **Python + asyncio** - Concurrent persona reactions

## Quick Start

```bash
# Generate skeleton personas (no API key needed)
python scripts/generate_canada_personas.py --count 50 --skeleton-only

# Generate with LLM enrichment (requires ANTHROPIC_API_KEY)
python scripts/generate_canada_personas.py --count 5000

# Run the focus group pipeline (requires OPENROUTER_API_KEY + LANGFUSE keys)
# See experiments/01_focus_group_test.ipynb
```

## Attribution

- **Aayush Mathur** - Original [Ask Singapore](https://github.com/AayushMathur7/ask-singapore) project
- **Statistics Canada** - 2021 Census of Population demographic data
- **NVIDIA** - Nemotron-Personas methodology inspiration
- **Job Bank Canada** - 2025 wage data for income enrichment