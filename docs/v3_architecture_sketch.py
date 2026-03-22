"""MaplePulse v3 — Agentic Persona Engine Architecture Sketch

DESIGN SKETCH — not runnable code. Shows how the system evolves from
a static 5,000-persona pool (v2) to a dynamic, tool-calling agent that
searches, generates, and persists targeted personas per query.

Key differences from v2:
- v2: `select_panel` filters a static JSON pool by demographic fields
- v3: `build_panel` is an LLM agent with tools that searches a persistent
      DB, generates new personas to fill gaps, fetches domain data, and
      caches everything for future reuse

- v2: all 25 persona fields dumped into every subagent prompt
- v3: agent determines which attributes are RELEVANT for the use case,
      enriches personas with those specific attributes from data sources,
      and projects a lean, focused context per subagent. A health product
      query gets health + financial fields; a social media campaign gets
      digital behavior + media fields. Core demographics are always included.

The focus group pipeline (react → optimize → react v2 → compare) is
UNCHANGED from v2/backend. This sketch covers the new panel-building
layer AND the context projection layer.

Decided: 2026-03-21
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, Send
from langgraph.prebuilt import ToolNode, create_react_agent
from pydantic import BaseModel, Field
from tavily import TavilyClient


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PERSONA DB — SQLite                                            ║
# ║                                                                  ║
# ║  Replaces the static JSON file. Seed: 5,000 census personas.    ║
# ║  Grows with every query as the agent generates new ones.         ║
# ╚══════════════════════════════════════════════════════════════════╝

DB_PATH = Path("/app/data/personas.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS personas (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    age             INTEGER,
    sex             TEXT,
    province        TEXT,
    city            TEXT,
    occupation      TEXT,
    education_level TEXT,
    income_bracket  TEXT,
    estimated_annual_income REAL,
    income_source   TEXT,
    marital_status  TEXT,
    immigration_status TEXT,
    indigenous_identity TEXT,
    visible_minority TEXT,
    cultural_background TEXT,
    languages_spoken TEXT,
    housing         TEXT,
    political_leaning TEXT,
    religion        TEXT,
    commute_mode    TEXT,
    top_concerns    TEXT,       -- JSON array

    -- LLM-enriched fields (from original generator)
    personality     TEXT,
    skills_and_expertise TEXT,
    hobbies_and_interests TEXT,
    career_goals    TEXT,

    -- Extended attributes — JSON dict populated by the agent based on
    -- which data sources are relevant for a given audience brief.
    -- NOT all fields are populated for every persona. The agent decides
    -- which attributes to enrich based on the use case.
    --
    -- Possible keys (grounded in specific data sources):
    --
    -- Health (CCHS, MHACS, CSD):
    --   self_rated_health: "excellent" | "very_good" | "good" | "fair" | "poor"
    --   chronic_conditions: ["diabetes", "asthma", ...]
    --   physical_activity: "active" | "moderate" | "sedentary"
    --   mental_health: "excellent" | ... | "poor"
    --   disability: null | "mobility" | "vision" | ...
    --
    -- Digital (CIRA, CIUS, DataReportal):
    --   social_media_platforms: ["Instagram", "TikTok", "Facebook"]
    --   digital_literacy: "high" | "moderate" | "low"
    --   ai_adoption: "early_adopter" | "curious" | "skeptical" | "unaware"
    --   privacy_sensitivity: "high" | "moderate" | "low"
    --   screen_time_hours: 4.5
    --   online_shopping: "frequent" | "occasional" | "rare"
    --
    -- Financial (CFCS, CSCE, SHS):
    --   financial_stress: "high" | "moderate" | "low"
    --   saving_habits: "regular_saver" | "occasional" | "none"
    --   spending_confidence: "confident" | "cautious" | "anxious"
    --   housing_cost_burden: "affordable" | "stretched" | "unaffordable"
    --   debt_level: "none" | "manageable" | "heavy"
    --
    -- Civic (Elections Canada, GSS-GVP, Samara):
    --   voter_engagement: "always_votes" | "sometimes" | "never"
    --   volunteers: true | false
    --   charitable_giving: "regular" | "occasional" | "none"
    --   civic_participation: "active" | "passive" | "disengaged"
    --
    -- Lifestyle (PRIZM, GSS Time Use, Outdoor Activities):
    --   prizm_segment: "Urban Elite" | "Suburban Comfort" | ...
    --   daily_routine_type: "9-to-5" | "shift_work" | "flexible" | "stay_at_home"
    --   recreation_interests: ["hiking", "hockey", "gardening"]
    --   pet_owner: true | false
    --   dietary_preference: "omnivore" | "vegetarian" | "vegan" | ...
    --
    -- Values (WVS, Environics):
    --   social_tolerance: "high" | "moderate" | "low"
    --   institutional_trust: "high" | "moderate" | "low"
    --   environmental_concern: "high" | "moderate" | "low"
    --   provincial_identity: "strong" | "moderate" | "weak"
    --
    -- Domain-specific (from tavily_search or custom):
    --   (any key the agent deems relevant for the audience brief)
    --
    extended_attributes TEXT DEFAULT '{}',  -- JSON dict, selectively populated

    -- v3 metadata
    source          TEXT DEFAULT 'seed',      -- 'seed' | 'generated'
    audience_tags   TEXT DEFAULT '[]',        -- JSON array of brief hashes
    domain_context  TEXT,                     -- domain-specific traits added by agent
    created_at      TEXT DEFAULT (datetime('now')),
    -- Full JSON blob for fields not in columns
    raw_json        TEXT
);

-- Indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_province ON personas(province);
CREATE INDEX IF NOT EXISTS idx_age ON personas(age);
CREATE INDEX IF NOT EXISTS idx_income ON personas(income_bracket);
CREATE INDEX IF NOT EXISTS idx_occupation ON personas(occupation);
CREATE INDEX IF NOT EXISTS idx_education ON personas(education_level);
CREATE INDEX IF NOT EXISTS idx_source ON personas(source);
CREATE INDEX IF NOT EXISTS idx_sex ON personas(sex);

-- Full-text search on domain_context and audience_tags for semantic matching
CREATE VIRTUAL TABLE IF NOT EXISTS personas_fts USING fts5(
    id, occupation, top_concerns, domain_context, audience_tags,
    content='personas', content_rowid='rowid'
);
"""


def init_db():
    """Create tables and indexes if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.close()


def migrate_seed_personas(json_path: Path):
    """One-time: load 5,000 seed personas from JSON into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    with open(json_path) as f:
        personas = json.load(f)

    for p in personas:
        conn.execute(
            """INSERT OR IGNORE INTO personas
               (id, name, age, sex, province, city, occupation,
                education_level, income_bracket, estimated_annual_income,
                income_source, marital_status, immigration_status,
                indigenous_identity, visible_minority, cultural_background,
                languages_spoken, housing, political_leaning, religion,
                commute_mode, top_concerns, source, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, 'seed', ?)""",
            (
                p["id"], p["name"], p["age"], p["sex"], p["province"],
                p.get("planning_area", ""), p["occupation"],
                p["education_level"], p.get("income_bracket"),
                p.get("estimated_annual_income"), p.get("income_source"),
                p["marital_status"], p["immigration_status"],
                p["indigenous_identity"], p["visible_minority"],
                p["cultural_background"], p["languages_spoken"],
                p["housing"], p.get("political_leaning"),
                p.get("religion"), p.get("commute_mode"),
                json.dumps(p.get("top_concerns", [])),
                json.dumps(p),
            ),
        )
    conn.commit()
    conn.close()
    print(f"Migrated {len(personas)} seed personas to SQLite")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  AUDIENCE BRIEF PARSING                                         ║
# ║                                                                  ║
# ║  LLM parses free-text audience descriptions into structured      ║
# ║  specs that can be used for DB queries and persona generation.   ║
# ╚══════════════════════════════════════════════════════════════════╝

class AudienceSpec(BaseModel):
    """Structured representation of a target audience, parsed from free text."""

    # Demographics (hard filters for DB queries)
    age_range: tuple[int, int] | None = Field(None, description="e.g. (25, 40)")
    sex: str | None = None
    provinces: list[str] | None = Field(None, description="e.g. ['Ontario', 'BC']")
    income_range: tuple[int, int] | None = Field(None, description="Annual income range")
    education: list[str] | None = None
    occupation_keywords: list[str] | None = Field(None, description="e.g. ['tech', 'software', 'engineering']")
    immigration_status: str | None = None

    # Psychographics (soft matching + generation guidance)
    values: list[str] | None = Field(None, description="e.g. ['environmentally conscious', 'family-oriented']")
    concerns: list[str] | None = Field(None, description="e.g. ['housing affordability', 'childcare costs']")
    lifestyle: list[str] | None = Field(None, description="e.g. ['urban', 'active', 'tech-savvy']")
    interests: list[str] | None = Field(None, description="e.g. ['outdoor recreation', 'craft beer']")

    # Domain context (for enrichment)
    domain: str | None = Field(None, description="e.g. 'furniture retail', 'EV market', 'healthcare'")
    purchase_context: str | None = Field(None, description="What buying decision they're facing")
    behavioral_traits: list[str] | None = Field(None, description="e.g. ['comparison shopper', 'brand loyal']")

    # Original text for reference
    raw_brief: str = ""


BRIEF_PARSER_PROMPT = """You are parsing a target audience description into structured fields.

Extract as many fields as you can from the user's description. Leave fields as null
if not mentioned or clearly implied. Be precise — don't infer demographics that
aren't stated or strongly implied.

Examples:
- "Young professionals in Vancouver, $80-120K, environmentally conscious, considering EVs"
  → age_range: (25, 35), provinces: ["British Columbia"], income_range: (80000, 120000),
    values: ["environmentally conscious"], domain: "electric vehicles",
    purchase_context: "considering EV purchase"

- "Retired homeowners in Atlantic Canada thinking about downsizing"
  → age_range: (60, 80), provinces: ["Nova Scotia", "New Brunswick", "PEI", "Newfoundland and Labrador"],
    lifestyle: ["homeowner"], domain: "real estate",
    purchase_context: "downsizing from house to condo/apartment"

- "Parents of school-age kids worried about screen time"
  → age_range: (30, 50), concerns: ["screen time", "children's technology use"],
    lifestyle: ["parent"], domain: "parenting/technology"

- "Budget-conscious students in Montreal"
  → age_range: (18, 25), provinces: ["Quebec"], income_range: (0, 30000),
    occupation_keywords: ["student"], lifestyle: ["urban", "budget-conscious"]
"""


def parse_audience_brief(brief: str, model: ChatOpenAI) -> AudienceSpec:
    """Parse a free-text audience description into a structured AudienceSpec."""
    result = model.with_structured_output(AudienceSpec).invoke([
        SystemMessage(content=BRIEF_PARSER_PROMPT),
        HumanMessage(content=f"Parse this audience description:\n\n{brief}"),
    ])
    result.raw_brief = brief
    return result


# ╔══════════════════════════════════════════════════════════════════╗
# ║  AGENT TOOLS                                                    ║
# ║                                                                  ║
# ║  These are the tools the panel-building agent can call.          ║
# ║  LangGraph's create_react_agent wires them automatically.       ║
# ╚══════════════════════════════════════════════════════════════════╝

@tool
def search_personas(
    province: list[str] | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    sex: str | None = None,
    income_bracket: list[str] | None = None,
    education: list[str] | None = None,
    occupation_keywords: list[str] | None = None,
    concerns_keywords: list[str] | None = None,
    domain_keywords: list[str] | None = None,
    limit: int = 50,
) -> dict:
    """Search the persona database for existing personas matching demographic
    and psychographic criteria. Returns matching personas and a coverage score.

    Always call this BEFORE generate_personas — reuse existing personas first.

    Args:
        province: Filter by provinces, e.g. ["Ontario", "British Columbia"]
        age_min: Minimum age inclusive
        age_max: Maximum age inclusive
        sex: Filter by sex
        income_bracket: Filter by income brackets, e.g. ["$60,000-$79,999"]
        education: Filter by education levels
        occupation_keywords: Keywords to match in occupation field
        concerns_keywords: Keywords to match in top_concerns
        domain_keywords: Keywords to match in domain_context (from prior generations)
        limit: Max personas to return

    Returns:
        dict with 'personas' (list), 'total_matches' (int), 'coverage_score' (float 0-1)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conditions = []
    params = []

    if province:
        placeholders = ",".join("?" * len(province))
        conditions.append(f"province IN ({placeholders})")
        params.extend(province)

    if age_min is not None:
        conditions.append("age >= ?")
        params.append(age_min)

    if age_max is not None:
        conditions.append("age <= ?")
        params.append(age_max)

    if sex:
        conditions.append("sex = ?")
        params.append(sex)

    if income_bracket:
        placeholders = ",".join("?" * len(income_bracket))
        conditions.append(f"income_bracket IN ({placeholders})")
        params.extend(income_bracket)

    if education:
        placeholders = ",".join("?" * len(education))
        conditions.append(f"education_level IN ({placeholders})")
        params.extend(education)

    where = " AND ".join(conditions) if conditions else "1=1"

    # Count total matches
    total = conn.execute(
        f"SELECT COUNT(*) FROM personas WHERE {where}", params
    ).fetchone()[0]

    # Get sample
    rows = conn.execute(
        f"SELECT raw_json FROM personas WHERE {where} ORDER BY RANDOM() LIMIT ?",
        params + [limit],
    ).fetchall()

    conn.close()

    personas = [json.loads(r["raw_json"]) for r in rows]

    # If we have keyword filters, do post-filter (FTS would be better at scale)
    if occupation_keywords:
        kw = [k.lower() for k in occupation_keywords]
        personas = [p for p in personas if any(
            k in p.get("occupation", "").lower() for k in kw
        )]

    if concerns_keywords:
        kw = [k.lower() for k in concerns_keywords]
        personas = [p for p in personas if any(
            k in str(p.get("top_concerns", [])).lower() for k in kw
        )]

    if domain_keywords:
        kw = [k.lower() for k in domain_keywords]
        personas = [p for p in personas if any(
            k in str(p.get("domain_context", "")).lower() for k in kw
        )]

    # Coverage score: what fraction of the requested filters had matches?
    filters_requested = sum(1 for x in [
        province, age_min, age_max, sex, income_bracket, education,
        occupation_keywords, concerns_keywords, domain_keywords,
    ] if x is not None)
    filters_with_matches = filters_requested  # simplified — real impl checks each
    coverage = filters_with_matches / max(filters_requested, 1)

    return {
        "personas": personas[:limit],
        "total_matches": total,
        "coverage_score": coverage,
        "message": f"Found {total} personas matching filters, returned {len(personas[:limit])}",
    }


@tool
def generate_personas(
    count: int,
    spec: dict,
    domain_context: str | None = None,
) -> list[dict]:
    """Generate new targeted personas based on a specification.

    Uses the existing census-grounded persona generator but constrains it to
    match the target audience spec. Generated personas include domain-specific
    traits from the brief.

    Call this ONLY after search_personas shows insufficient coverage (<80%).
    Generate only what's needed to fill gaps — don't regenerate personas
    that already exist in the DB.

    Args:
        count: Number of personas to generate (max 15 per call)
        spec: Audience spec dict with keys like age_range, provinces,
              income_range, occupation_keywords, values, concerns, etc.
        domain_context: Free-text domain context for enrichment, e.g.
                       "furniture shopper, mid-range market, values quality
                        over brand name"

    Returns:
        List of generated persona dicts
    """
    count = min(count, 15)  # Cost control

    # Import the existing persona generator and constrain it
    # This wraps scripts/generate_canada_personas.py logic
    from scripts.generate_canada_personas import generate_skeleton_persona

    generated = []
    for _ in range(count):
        # Pass spec constraints to the generator
        persona = generate_skeleton_persona(
            force_province=spec.get("provinces"),
            force_age_range=spec.get("age_range"),
            force_income_range=spec.get("income_range"),
            force_education=spec.get("education"),
            force_occupation_keywords=spec.get("occupation_keywords"),
        )

        # Layer on domain-specific context
        if domain_context:
            persona["domain_context"] = domain_context

        # Tag with audience brief hash for future lookup
        brief_hash = hashlib.sha256(
            json.dumps(spec, sort_keys=True).encode()
        ).hexdigest()[:12]
        persona["audience_tags"] = [brief_hash]
        persona["source"] = "generated"

        generated.append(persona)

    return generated


@tool
def fetch_data(
    source: str,
    query: str | None = None,
    province: str | None = None,
) -> dict:
    """Fetch data from pre-indexed Canadian data sources to ground persona
    generation in real statistical distributions.

    Available sources and what they provide:

    Demographics & Economics:
    - "census_demographics" — age, province, education, occupation distributions
    - "jobbank_wages" — income by occupation (NOC code) and province
    - "cmhc_housing" — rent levels, vacancy rates by city
    - "household_spending" — spending patterns by category

    Values & Attitudes:
    - "ces_political" — political leaning by province/age from Canadian Election Study
    - "environics_values" — social values, trust, diversity attitudes
    - "angus_reid" — current issue priorities, policy opinions
    - "world_values" — moral values, religiosity, social tolerance
    - "confederation_tomorrow" — provincial identity, regional grievances

    Digital & Media:
    - "cira_internet" — AI adoption, e-commerce, social media trust
    - "cius_digital" — digital literacy, online activities, privacy
    - "social_media_stats" — platform usage by age/gender

    Health:
    - "cchs_health" — self-rated health, chronic conditions, health behaviors
    - "cchs_nutrition" — dietary preferences

    Civic:
    - "elections_turnout" — voter turnout by demographics
    - "gss_volunteering" — volunteer rates, charitable giving

    Args:
        source: Source identifier from the list above
        query: Optional query to narrow results (e.g., "Ontario" or "software developer")
        province: Optional province filter

    Returns:
        dict with source data relevant to the query
    """
    # This is a registry pattern — each source has a loader
    # that returns the relevant slice of data
    from canada_demographics_2021 import (
        PROVINCE_POP, AGE_DIST, EDUCATION_DIST, OCCUPATION_DIST,
        INCOME_BRACKETS, IMMIGRATION_STATUS,
    )

    loaders = {
        "census_demographics": lambda: {
            "province_populations": PROVINCE_POP,
            "age_distribution": AGE_DIST,
            "education_distribution": EDUCATION_DIST,
            "occupation_distribution": OCCUPATION_DIST,
            "income_brackets": INCOME_BRACKETS,
        },
        "jobbank_wages": lambda: _load_jobbank_wages(query, province),
        "ces_political": lambda: _load_political_data(province),
        # ... other loaders follow the same pattern
    }

    if source not in loaders:
        return {"error": f"Unknown source: {source}. Available: {list(loaders.keys())}"}

    return {"source": source, "data": loaders[source]()}


def _load_jobbank_wages(query: str | None, province: str | None) -> dict:
    """Load Job Bank wage data, optionally filtered by occupation/province."""
    import pandas as pd
    df = pd.read_csv("/app/data/raw/jobbank_wages_2025.csv")
    if province:
        df = df[df["province"] == province]
    if query:
        df = df[df["noc_title"].str.contains(query, case=False, na=False)]
    return df.head(20).to_dict(orient="records")


def _load_political_data(province: str | None) -> dict:
    """Load political leaning distributions from CES/Angus Reid data."""
    # From canada_demographics_2021.py political weights
    from canada_demographics_2021 import POLITICAL_LEANINGS
    if province:
        return {province: POLITICAL_LEANINGS.get(province, {})}
    return POLITICAL_LEANINGS


@tool
def tavily_search(query: str, max_results: int = 5) -> dict:
    """Search the internet for domain-specific context not covered by
    pre-indexed Canadian data sources.

    Use this when the audience brief involves:
    - Niche markets (e.g., "Canadian craft beer enthusiasts")
    - Emerging trends (e.g., "AI tutoring adoption in Canada")
    - Industry-specific consumer behavior
    - Current events affecting the target audience
    - Product categories not in census/survey data

    Always add "Canada" or "Canadian" to your query for relevance.

    Args:
        query: Search query — be specific. Include "Canada"/"Canadian".
        max_results: Number of results to return (max 10)

    Returns:
        dict with search results including titles, URLs, and content snippets
    """
    client = TavilyClient()  # API key from env: TAVILY_API_KEY
    results = client.search(
        query=query,
        max_results=min(max_results, 10),
        search_depth="basic",
        include_answer=True,
    )
    return {
        "answer": results.get("answer", ""),
        "results": [
            {
                "title": r["title"],
                "url": r["url"],
                "content": r["content"][:500],
            }
            for r in results.get("results", [])
        ],
    }


@tool
def persist_personas(personas: list[dict]) -> dict:
    """Save newly generated personas to the SQLite database for future reuse.

    Call this after generate_personas to cache the results. Every persisted
    persona becomes searchable by future queries via search_personas.

    Args:
        personas: List of persona dicts to save (must have 'id' field)

    Returns:
        dict with count of saved personas
    """
    conn = sqlite3.connect(DB_PATH)
    saved = 0

    for p in personas:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO personas
                   (id, name, age, sex, province, city, occupation,
                    education_level, income_bracket, estimated_annual_income,
                    income_source, marital_status, immigration_status,
                    indigenous_identity, visible_minority, cultural_background,
                    languages_spoken, housing, political_leaning, religion,
                    commute_mode, top_concerns, source, audience_tags,
                    domain_context, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["id"], p["name"], p["age"], p["sex"], p["province"],
                    p.get("planning_area", ""), p["occupation"],
                    p["education_level"], p.get("income_bracket"),
                    p.get("estimated_annual_income"), p.get("income_source"),
                    p["marital_status"], p["immigration_status"],
                    p["indigenous_identity"], p["visible_minority"],
                    p["cultural_background"], p["languages_spoken"],
                    p["housing"], p.get("political_leaning"),
                    p.get("religion"), p.get("commute_mode"),
                    json.dumps(p.get("top_concerns", [])),
                    p.get("source", "generated"),
                    json.dumps(p.get("audience_tags", [])),
                    p.get("domain_context", ""),
                    json.dumps(p),
                ),
            )
            saved += 1
        except Exception as e:
            print(f"Failed to save persona {p.get('id')}: {e}")

    conn.commit()
    conn.close()

    return {"saved": saved, "message": f"Persisted {saved} personas to DB"}


@tool
def run_python(code: str, description: str) -> dict:
    """Execute Python code for custom data processing.

    Use this when data sources need transformation before persona generation.
    For example: computing median income for a specific occupation+province
    combination, or parsing a downloaded CSV.

    The code runs in a sandboxed environment with access to:
    - pandas, numpy, json, csv (data processing)
    - pathlib (file access to /app/data/)
    - No network access, no file writes outside /app/data/tmp/

    Args:
        code: Python code to execute
        description: What this code does (for logging)

    Returns:
        dict with 'output' (stdout) and 'result' (last expression value)
    """
    import io
    import contextlib

    # Sandboxed execution with limited globals
    sandbox_globals = {
        "__builtins__": {
            "print": print, "len": len, "range": range, "int": int,
            "float": float, "str": str, "list": list, "dict": dict,
            "sum": sum, "min": min, "max": max, "sorted": sorted,
            "enumerate": enumerate, "zip": zip, "round": round,
        },
        "json": json,
        "Path": Path,
    }

    # Allow pandas/numpy imports
    try:
        import pandas as pd
        import numpy as np
        sandbox_globals["pd"] = pd
        sandbox_globals["np"] = np
    except ImportError:
        pass

    stdout = io.StringIO()
    result = None

    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, sandbox_globals)
            # Try to capture last expression
            result = sandbox_globals.get("result")
    except Exception as e:
        return {"error": str(e), "output": stdout.getvalue()}

    return {
        "output": stdout.getvalue()[:5000],
        "result": str(result)[:2000] if result else None,
        "description": description,
    }


# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONTEXT PROJECTION                                             ║
# ║                                                                  ║
# ║  The KEY v3 innovation beyond dynamic personas: the agent        ║
# ║  decides which persona attributes are RELEVANT for each query    ║
# ║  and builds a lean, focused context for each subagent.           ║
# ║                                                                  ║
# ║  v2: dump all 25 fields into every prompt                        ║
# ║  v3: select 8-15 fields based on use case + audience brief       ║
# ║                                                                  ║
# ║  This matters because:                                           ║
# ║  1. Fewer irrelevant fields = less noise = better reactions      ║
# ║  2. Extended attributes only populated when relevant = less cost ║
# ║  3. Subagent context stays lean even as the schema grows         ║
# ╚══════════════════════════════════════════════════════════════════╝

# Attribute groups — the agent picks which groups matter for a query
ATTRIBUTE_GROUPS = {
    # Always included for every query
    "core": [
        "age", "sex", "province", "city", "occupation",
        "education_level", "income_bracket", "languages_spoken",
    ],

    # Included based on use case / audience brief signals
    "identity": [
        "immigration_status", "indigenous_identity", "visible_minority",
        "cultural_background", "religion",
    ],
    "housing": [
        "housing", "commute_mode",
        # extended: housing_cost_burden
    ],
    "political": [
        "political_leaning", "top_concerns",
        # extended: voter_engagement, civic_participation
    ],
    "health": [
        # extended: self_rated_health, chronic_conditions,
        # physical_activity, mental_health, disability
    ],
    "digital": [
        # extended: social_media_platforms, digital_literacy,
        # ai_adoption, privacy_sensitivity, screen_time_hours
    ],
    "financial": [
        # extended: financial_stress, saving_habits,
        # spending_confidence, debt_level
    ],
    "civic": [
        # extended: voter_engagement, volunteers,
        # charitable_giving, civic_participation
    ],
    "lifestyle": [
        "hobbies_and_interests",
        # extended: prizm_segment, daily_routine_type,
        # recreation_interests, dietary_preference
    ],
    "values": [
        # extended: social_tolerance, institutional_trust,
        # environmental_concern, provincial_identity
    ],
    "consumer": [
        # extended: online_shopping, spending_confidence,
        # brand_sensitivity, price_sensitivity
    ],
}

# Maps use case keywords to which attribute groups matter
USE_CASE_RELEVANCE = {
    "localization": ["core", "identity", "political", "values"],
    "product_concept": ["core", "financial", "consumer", "lifestyle"],
    "ab_copy_test": ["core", "digital", "consumer", "values"],
    "survey_pretest": ["core", "identity", "political", "civic"],
    # Domain keywords from audience brief → additional groups
    "health": ["health"],
    "food": ["health", "lifestyle"],
    "tech": ["digital"],
    "finance": ["financial"],
    "housing": ["housing", "financial"],
    "environment": ["values", "political"],
    "social_media": ["digital", "lifestyle"],
    "government": ["political", "civic"],
    "fitness": ["health", "lifestyle"],
    "education": ["civic", "digital"],
    "retail": ["consumer", "financial"],
}


class ContextProjection(BaseModel):
    """Determines which persona attributes to include in subagent prompts."""
    relevant_groups: list[str] = Field(
        description="Which attribute groups are relevant for this query"
    )
    relevant_extended_keys: list[str] = Field(
        description="Specific extended_attributes keys to include"
    )
    reasoning: str = Field(
        description="Why these groups were selected"
    )


def determine_relevant_attributes(
    use_case: str,
    audience_brief: str,
    content: str,
    model: ChatOpenAI,
) -> ContextProjection:
    """LLM determines which persona attributes matter for this specific query.

    This is called ONCE per query, not per persona. The result drives:
    1. Which extended_attributes the agent enriches during persona generation
    2. Which fields are included in the subagent prompt context
    """
    result = model.with_structured_output(ContextProjection).invoke([
        SystemMessage(content=f"""You decide which persona attributes are relevant for a focus group query.

Available attribute groups:
{json.dumps(ATTRIBUTE_GROUPS, indent=2)}

The "core" group is ALWAYS included. Select additional groups based on:
- The use case type
- What the audience brief emphasizes
- What the content being tested is about

Also specify which extended_attributes keys should be populated.
For example:
- A health product → include "health" group, keys: self_rated_health, chronic_conditions, physical_activity
- A social media campaign → include "digital" group, keys: social_media_platforms, digital_literacy, ai_adoption
- A government policy → include "political" + "civic", keys: voter_engagement, institutional_trust
- A furniture ad → include "housing" + "financial" + "consumer", keys: housing_cost_burden, spending_confidence

Be selective — only include groups that would genuinely affect how a persona reacts to THIS specific content.
Typically 3-5 groups beyond core is right. Don't include everything."""),
        HumanMessage(content=f"""Use case: {use_case}
Audience brief: {audience_brief}
Content to test: {content[:300]}"""),
    ])
    return result


def build_projected_context(persona: dict, projection: ContextProjection) -> str:
    """Build a lean persona context string using only the relevant attributes.

    This replaces v2's build_persona_context() which dumped all 25 fields.
    """
    lines = []

    # Always include core identity line
    lines.append(
        f"Age: {persona['age']} | Sex: {persona['sex']} | "
        f"Province: {persona['province']}"
    )
    if persona.get("city"):
        lines.append(f"City/Region: {persona['city']}")
    lines.append(
        f"Occupation: {persona['occupation']} | "
        f"Education: {persona['education_level']}"
    )
    lines.append(f"Income: {persona.get('income_bracket', 'Unknown')}")
    lines.append(f"Languages: {persona['languages_spoken']}")

    # Conditionally include other groups
    groups = set(projection.relevant_groups)

    if "identity" in groups:
        lines.append(
            f"Immigration: {persona['immigration_status']} | "
            f"Indigenous: {persona['indigenous_identity']}"
        )
        if persona.get("visible_minority") != "Not a visible minority":
            lines.append(f"Visible minority: {persona['visible_minority']}")
        lines.append(f"Cultural background: {persona['cultural_background']}")
        if persona.get("religion"):
            lines.append(f"Religion: {persona['religion']}")

    if "housing" in groups:
        lines.append(f"Housing: {persona['housing']}")
        if persona.get("commute_mode") and persona["commute_mode"] != "not applicable":
            lines.append(f"Commute: {persona['commute_mode']}")

    if "political" in groups:
        lines.append(f"Political leaning: {persona.get('political_leaning', 'Unknown')}")
        concerns = persona.get("top_concerns", [])
        if concerns:
            lines.append(f"Top concerns: {', '.join(concerns)}")

    if "lifestyle" in groups:
        if persona.get("hobbies_and_interests"):
            lines.append(f"Hobbies/interests: {persona['hobbies_and_interests']}")

    # Include relevant extended attributes
    ext = persona.get("extended_attributes", {})
    if isinstance(ext, str):
        ext = json.loads(ext) if ext else {}

    for key in projection.relevant_extended_keys:
        if key in ext and ext[key] is not None:
            # Format the key nicely
            label = key.replace("_", " ").title()
            value = ext[key]
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(f"{label}: {value}")

    return "\n".join(lines)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PANEL-BUILDING AGENT                                           ║
# ║                                                                  ║
# ║  This is the core v3 innovation: an LLM agent with tools that   ║
# ║  decides HOW to assemble the optimal panel for each query.       ║
# ║                                                                  ║
# ║  Uses LangGraph's create_react_agent (ReAct pattern):            ║
# ║  - Agent reasons about the audience brief                        ║
# ║  - Calls tools in whatever order makes sense                     ║
# ║  - Decides when it has enough personas                           ║
# ╚══════════════════════════════════════════════════════════════════╝

PANEL_AGENT_SYSTEM = """You are the MaplePulse Panel Builder — an agent that assembles
the optimal focus group panel for a given target audience.

You have access to tools for searching existing personas, generating new ones,
fetching Canadian data sources, and searching the internet for domain context.

## Your workflow:

1. UNDERSTAND the audience brief — what demographics, psychographics, and
   domain context define this target audience?

2. DETERMINE RELEVANT ATTRIBUTES — based on the use case and content being
   tested, decide which persona attributes matter. You will be given a
   context projection that tells you which attribute groups are relevant.
   Only enrich personas with the attributes that matter for THIS query.

   Examples:
   - Health product → enrich with: self_rated_health, chronic_conditions,
     physical_activity, mental_health (from CCHS data)
   - Social media campaign → enrich with: social_media_platforms,
     digital_literacy, ai_adoption (from CIRA/CIUS data)
   - Government policy → enrich with: voter_engagement, institutional_trust,
     civic_participation (from Elections Canada/GSS data)
   - Furniture ad → enrich with: housing_cost_burden, spending_confidence,
     housing details (from CMHC/CFCS data)

3. SEARCH FIRST — always call search_personas before generating. Check what
   we already have in the database that matches. If existing personas already
   have the relevant extended_attributes populated, prefer them.

4. ASSESS COVERAGE — if existing personas cover 80%+ of the spec, use them.
   If not, identify the gaps.

5. ENRICH with data — use fetch_data to pull ONLY the relevant data sources
   for the attributes you need. Don't pull health data for a furniture query.
   For niche domains, use tavily_search.

6. GENERATE to fill gaps — use generate_personas only for what's missing.
   Never generate more than 15 personas per query. Include the relevant
   extended_attributes when generating.

7. PERSIST — save any newly generated personas to the DB for future reuse
   (including their extended_attributes).

8. COMPOSE the final panel — select the best mix of existing + new personas
   to represent the target audience. Aim for {panel_size} personas.

## Rules:
- Never generate personas that already exist in the DB
- Always ground new personas in real Canadian data (census, Job Bank, etc.)
- Only enrich attributes that are relevant — don't populate health data for
  a social media campaign or digital behavior for a health product query
- For unfamiliar domains, use tavily_search to understand the market first
- The panel should have demographic diversity within the target spec
  (don't make everyone the same age/city/background)
- Maximum 15 new personas per query — cost control
- Always persist new personas so they're available for future queries
"""


AGENT_TOOLS = [
    search_personas,
    generate_personas,
    fetch_data,
    tavily_search,
    persist_personas,
    run_python,
]


def build_panel_agent(model_name: str = "google/gemini-3-flash"):
    """Create the panel-building ReAct agent."""
    model = ChatOpenAI(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,  # Low temp for tool-calling decisions
    )

    agent = create_react_agent(
        model=model,
        tools=AGENT_TOOLS,
        prompt=PANEL_AGENT_SYSTEM,
    )

    return agent


# ╔══════════════════════════════════════════════════════════════════╗
# ║  INTEGRATION WITH EXISTING PIPELINE                             ║
# ║                                                                  ║
# ║  The panel-building agent replaces `select_panel` in the         ║
# ║  existing LangGraph focus group pipeline. Everything downstream  ║
# ║  (react → aggregate → optimize → react v2 → aggregate v2)       ║
# ║  stays exactly the same.                                         ║
# ╚══════════════════════════════════════════════════════════════════╝

# -- Updated orchestrator state (adds audience_brief and panel_metadata) --

import operator
from typing import Annotated, TypedDict


class OrchestratorStateV3(TypedDict):
    # Input
    user_input: str              # The marketing message / content to test
    audience_brief: str          # Free-text target audience description
    use_case: str                # localization, product_concept, etc.

    # Panel (NEW in v3 — built by agent instead of filtered)
    audience_spec: dict          # Parsed AudienceSpec
    panel: list[dict]            # Final assembled panel (full persona dicts)
    panel_metadata: dict         # Coverage score, new vs existing counts, data sources used

    # Context projection (NEW in v3 — determines what to pass to subagents)
    context_projection: dict     # ContextProjection — which attribute groups/keys matter

    # Round 1 (unchanged from v2)
    reactions: Annotated[list[dict], operator.add]
    summary: dict

    # Optimization (unchanged)
    optimized_input: str
    optimization_changes: list[str]

    # Round 2 (unchanged)
    reactions_v2: Annotated[list[dict], operator.add]
    summary_v2: dict


async def build_panel(state: OrchestratorStateV3) -> dict:
    """NEW node: replaces v2's select_panel.

    Two-phase process:
    Phase 1: Determine which persona attributes matter for this query
    Phase 2: Run the panel-building agent to assemble the right personas
             with those attributes enriched
    """
    orchestrator_model = ChatOpenAI(
        model="google/gemini-3-flash",
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2,
    )

    # Phase 1: Context projection — what attributes matter?
    projection = determine_relevant_attributes(
        use_case=state["use_case"],
        audience_brief=state["audience_brief"],
        content=state["user_input"],
        model=orchestrator_model,
    )

    # Phase 2: Build the panel with the right enrichment
    agent = build_panel_agent()

    result = await agent.ainvoke({
        "messages": [
            HumanMessage(content=f"""Build a focus group panel of {state.get('panel_size', 12)} personas
for this target audience:

{state['audience_brief']}

The content they'll be evaluating: {state['user_input'][:200]}...
Use case: {state['use_case']}

IMPORTANT — Relevant attribute groups for this query: {projection.relevant_groups}
Extended attributes to populate: {projection.relevant_extended_keys}
Reasoning: {projection.reasoning}

Only fetch data sources and enrich personas for these specific attributes.
Do NOT populate irrelevant attributes.""")
        ]
    })

    panel = _extract_panel_from_agent_result(result)

    return {
        "panel": panel,
        "context_projection": projection.model_dump(),
        "panel_metadata": {
            "total_in_panel": len(panel),
            "from_existing_db": sum(1 for p in panel if p.get("source") == "seed"),
            "newly_generated": sum(1 for p in panel if p.get("source") == "generated"),
            "audience_brief": state["audience_brief"],
            "relevant_groups": projection.relevant_groups,
            "relevant_extended_keys": projection.relevant_extended_keys,
        },
    }


def _extract_panel_from_agent_result(result: dict) -> list[dict]:
    """Extract persona list from the agent's conversation history.

    The agent will have called search_personas and/or generate_personas.
    We look through the tool call results to collect all personas.
    """
    personas = []
    for msg in result.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                if tc["name"] in ("search_personas", "generate_personas"):
                    output = tc.get("output", {})
                    if isinstance(output, dict) and "personas" in output:
                        personas.extend(output["personas"])
                    elif isinstance(output, list):
                        personas.extend(output)
    return personas


# ╔══════════════════════════════════════════════════════════════════╗
# ║  SUBAGENT PROMPTS WITH PROJECTED CONTEXT                        ║
# ║                                                                  ║
# ║  v2: build_persona_prompt() dumps all 25 fields                  ║
# ║  v3: build_projected_persona_prompt() uses the ContextProjection ║
# ║      to include only the relevant attributes per subagent        ║
# ╚══════════════════════════════════════════════════════════════════╝

def build_projected_persona_prompt(persona: dict, projection: ContextProjection) -> str:
    """Build a focused system prompt for a persona subagent.

    Uses build_projected_context() to include only attributes that matter
    for this specific query. A health product query gets health fields;
    a social media campaign gets digital behavior fields.
    """
    context = build_projected_context(persona, projection)

    return f"""You are {persona['name']}, a {persona['age']}-year-old {persona['occupation']}
living in {persona.get('city', 'Unknown')}, {persona['province']}.

{context}

React to the marketing message AS THIS PERSON. Use your background,
values, and regional perspective to form an authentic opinion.
Do NOT be artificially positive. If this message wouldn't resonate
with someone like you, say so honestly."""


# ╔══════════════════════════════════════════════════════════════════╗
# ║  FAN-OUT WITH CONTEXT PROJECTION                                ║
# ║                                                                  ║
# ║  v2: spawn_subagents passed full persona dict                    ║
# ║  v3: spawn_subagents reads context_projection from state and     ║
# ║      passes projected_prompt — lean, focused, per-query          ║
# ╚══════════════════════════════════════════════════════════════════╝

def spawn_subagents_v3(state: OrchestratorStateV3) -> list:
    """Round 1: spawn one subagent per persona with projected context.

    Each Send() carries:
    - persona: the full persona dict (for metadata in results)
    - message: the content to test
    - model_index: round-robin model assignment
    - projected_prompt: the LEAN system prompt built from context projection
    """
    projection = ContextProjection(**state["context_projection"])

    return [
        Send("persona_subagent", {
            "persona": persona,
            "message": state["user_input"],
            "model_index": i,
            "projected_prompt": build_projected_persona_prompt(persona, projection),
        })
        for i, persona in enumerate(state["panel"])
    ]


def spawn_subagents_v3_r2(state: OrchestratorStateV3) -> list:
    """Round 2: same panel + projections, optimized message."""
    projection = ContextProjection(**state["context_projection"])

    return [
        Send("persona_subagent_v2", {
            "persona": persona,
            "message": state["optimized_input"],
            "model_index": i,
            "projected_prompt": build_projected_persona_prompt(persona, projection),
        })
        for i, persona in enumerate(state["panel"])
    ]


# -- Updated subagent node: uses projected_prompt if available --
# NOTE: MODEL_CONFIGS, OPENROUTER_BASE, PersonaReaction are defined in
# v2_architecture_sketch.py / backend/main.py — shared with v3.

def persona_subagent_v3(state: dict) -> dict:
    """Stateless subagent: one persona + projected prompt → one reaction.

    v3 change: uses projected_prompt (lean, query-specific context)
    instead of building from all 25 fields.
    """
    persona = state["persona"]
    message = state["message"]
    idx = state["model_index"] % len(MODEL_CONFIGS)

    model = ChatOpenAI(
        model=MODEL_CONFIGS[idx]["model"],
        base_url=OPENROUTER_BASE,
    )
    cfg = MODEL_CONFIGS[idx]

    # v3: use projected prompt; v2 fallback for backwards compat
    system_prompt = state.get("projected_prompt") or build_full_persona_prompt(persona)

    result = model.with_structured_output(PersonaReaction).invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"React to this marketing message:\n\n{message}"),
    ])

    return {
        "reactions": [{
            "persona_id": persona["id"],
            "persona_name": persona["name"],
            "province": persona["province"],
            "reaction": result.dict(),
            "model_id": cfg["model"],
            "model_label": cfg["label"],
            "provider": cfg["provider"],
        }]
    }


# ╔══════════════════════════════════════════════════════════════════╗
# ║  GRAPH ASSEMBLY (v3)                                            ║
# ║                                                                  ║
# ║  Flow (★ = changed from v2):                                    ║
# ║                                                                  ║
# ║  START → classify_intent                                         ║
# ║    → ★ build_panel (agent + context projection)                  ║
# ║    → ★ [Send() x N] persona_subagent (projected prompt)          ║
# ║    → aggregate                                                   ║
# ║    → optimize_message                                            ║
# ║    → ★ [Send() x N] persona_subagent_v2 (projected prompt)       ║
# ║    → aggregate_v2                                                ║
# ║    → END                                                         ║
# ╚══════════════════════════════════════════════════════════════════╝

graph = StateGraph(OrchestratorStateV3)

# Orchestrator nodes
graph.add_node("classify_intent", classify_intent)   # unchanged from v2
graph.add_node("build_panel", build_panel)            # ★ replaces select_panel
graph.add_node("aggregate", aggregate_results)        # unchanged
graph.add_node("optimize_message", optimize_message)  # unchanged
graph.add_node("aggregate_v2", aggregate_v2)          # unchanged

# Subagent nodes (use projected prompts)
graph.add_node("persona_subagent", persona_subagent_v3)     # ★ projected context
graph.add_node("persona_subagent_v2", persona_subagent_v3)  # ★ same node, different state key

# Edges
graph.set_entry_point("classify_intent")
graph.add_edge("classify_intent", "build_panel")              # ★ new

# Fan-out Round 1: build_panel → spawn N subagents with projected prompts
graph.add_conditional_edges("build_panel", spawn_subagents_v3, ["persona_subagent"])
graph.add_edge("persona_subagent", "aggregate")

graph.add_edge("aggregate", "optimize_message")

# Fan-out Round 2: optimize → spawn N subagents with projected prompts
graph.add_conditional_edges("optimize_message", spawn_subagents_v3_r2, ["persona_subagent_v2"])
graph.add_edge("persona_subagent_v2", "aggregate_v2")

graph.add_edge("aggregate_v2", END)

focus_group = graph.compile()


# ╔══════════════════════════════════════════════════════════════════╗
# ║  FASTAPI INTEGRATION                                            ║
# ║                                                                  ║
# ║  The API endpoint changes to accept audience_brief alongside     ║
# ║  the existing message and filters.                               ║
# ╚══════════════════════════════════════════════════════════════════╝

class FocusGroupRequestV3(BaseModel):
    """Updated API request — adds audience_brief field."""
    message: str                                    # Content to test
    audience_brief: str = ""                        # NEW: free-text target audience
    panel_size: int = 12
    filters: dict | None = None                     # Legacy filters (still supported)
    seed: int | None = None

    # If audience_brief is provided, it takes priority over filters.
    # If only filters are provided, fall back to v2 behavior (filter static pool).
    # If neither is provided, use census-representative random sample.


class PanelMetadata(BaseModel):
    """Returned alongside results — tells the user about their panel."""
    total_in_panel: int
    from_existing_db: int
    newly_generated: int
    audience_brief: str
    coverage_score: float = 0.0
    data_sources_used: list[str] = []


# ╔══════════════════════════════════════════════════════════════════╗
# ║  USAGE EXAMPLE                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    # Example: furniture company targeting mid-range buyers
    result = focus_group.invoke({
        "user_input": "Discover handcrafted Canadian furniture — quality you can feel, prices you can live with.",
        "audience_brief": (
            "Homeowners aged 30-55, household income $80K-$150K, "
            "looking to furnish or upgrade their living space. "
            "Values quality and craftsmanship over brand names. "
            "Slightly above IKEA budget but not luxury. "
            "Mix of urban and suburban across Ontario, BC, and Alberta."
        ),
    })

    meta = result["panel_metadata"]
    print(f"Panel: {meta['total_in_panel']} personas "
          f"({meta['from_existing_db']} existing + {meta['newly_generated']} new)")
    print(f"Round 1 sentiment: {result['summary']['avg_sentiment']:.2f}")
    print(f"Round 2 sentiment: {result['summary_v2']['avg_sentiment']:.2f}")

    # Example: niche market — the agent uses tavily_search
    result2 = focus_group.invoke({
        "user_input": "Join BrewPass — your monthly passport to Canada's best craft breweries.",
        "audience_brief": "Canadian craft beer enthusiasts, 25-45, urban, willing to pay for experiences.",
    })

    # Example: policy testing — broad audience
    result3 = focus_group.invoke({
        "user_input": "Starting January 2027, all new vehicles sold in Canada must be zero-emission.",
        "audience_brief": "General Canadian population, representative sample across provinces and demographics.",
    })
