"""MaplePulse v3 — Agentic Persona Engine

SQLite persona DB, audience brief parser, agent tools, context projection,
and panel-building agent. Used by the /api/build-panel endpoint.
"""

import json
import hashlib
import os
import sqlite3
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# ── Paths ────────────────────────────────────────────────────────────

DB_PATH = Path(os.environ.get("PERSONA_DB_PATH", "/app/db/personas.db"))
PERSONAS_JSON = Path("/app/data/personas_5000.json")

# Add parent so we can import canada_demographics_2021
sys.path.insert(0, str(Path("/app")))


# ╔══════════════════════════════════════════════════════════════════╗
# ║  SQLITE SCHEMA                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

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

    -- LLM-enriched fields
    personality     TEXT,
    skills_and_expertise TEXT,
    hobbies_and_interests TEXT,
    career_goals    TEXT,

    -- Extended attributes — JSON dict, selectively populated per query
    extended_attributes TEXT DEFAULT '{}',

    -- v3 metadata
    source          TEXT DEFAULT 'seed',
    audience_tags   TEXT DEFAULT '[]',
    domain_context  TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    raw_json        TEXT
);

CREATE INDEX IF NOT EXISTS idx_province ON personas(province);
CREATE INDEX IF NOT EXISTS idx_age ON personas(age);
CREATE INDEX IF NOT EXISTS idx_income ON personas(income_bracket);
CREATE INDEX IF NOT EXISTS idx_occupation ON personas(occupation);
CREATE INDEX IF NOT EXISTS idx_education ON personas(education_level);
CREATE INDEX IF NOT EXISTS idx_source ON personas(source);
CREATE INDEX IF NOT EXISTS idx_sex ON personas(sex);
CREATE INDEX IF NOT EXISTS idx_religion ON personas(religion);

CREATE VIRTUAL TABLE IF NOT EXISTS personas_fts USING fts5(
    id, occupation, top_concerns, domain_context, audience_tags,
    content='personas', content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key   TEXT PRIMARY KEY,
    cache_type  TEXT NOT NULL,       -- 'audience_spec', 'context_projection', 'panel'
    result_json TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now')),
    hit_count   INTEGER DEFAULT 0
);
"""


def init_db():
    """Create tables and indexes if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.close()
    print(f"[panel_engine] Initialized DB at {DB_PATH}")


# ── LLM Result Cache ──────────────────────────────────────────────

# Cache TTL in hours — results older than this are ignored
CACHE_TTL_HOURS = int(os.environ.get("CACHE_TTL_HOURS", "24"))


def _cache_key(cache_type: str, *parts: str) -> str:
    """Build a deterministic cache key from type + input parts."""
    raw = f"{cache_type}:" + "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(cache_type: str, *parts: str) -> dict | list | None:
    """Look up a cached LLM result. Returns None on miss."""
    if not DB_PATH.exists():
        return None
    key = _cache_key(cache_type, *parts)
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT result_json, created_at FROM llm_cache WHERE cache_key = ? AND cache_type = ?",
        (key, cache_type),
    ).fetchone()
    if row is None:
        conn.close()
        return None
    result_json, created_at = row
    # Check TTL
    try:
        created = datetime.fromisoformat(created_at)
        age_hours = (datetime.utcnow() - created).total_seconds() / 3600
        if age_hours > CACHE_TTL_HOURS:
            conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            print(f"[cache] EXPIRED {cache_type} (age={age_hours:.1f}h)")
            return None
    except (ValueError, TypeError):
        pass
    # Cache hit — bump counter
    conn.execute("UPDATE llm_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (key,))
    conn.commit()
    conn.close()
    result = json.loads(result_json)
    print(f"[cache] HIT {cache_type} key={key[:12]}...")
    return result


def _cache_set(cache_type: str, result: dict | list, *parts: str):
    """Store an LLM result in the cache."""
    if not DB_PATH.exists():
        return
    key = _cache_key(cache_type, *parts)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT OR REPLACE INTO llm_cache (cache_key, cache_type, result_json) VALUES (?, ?, ?)",
        (key, cache_type, json.dumps(result)),
    )
    conn.commit()
    conn.close()
    print(f"[cache] SET {cache_type} key={key[:12]}...")


def get_cache_stats() -> dict:
    """Return cache statistics."""
    if not DB_PATH.exists():
        return {"total_entries": 0, "by_type": {}}
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute(
            "SELECT cache_type, COUNT(*), SUM(hit_count) FROM llm_cache GROUP BY cache_type"
        ).fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return {"total_entries": 0, "by_type": {}}
    conn.close()
    by_type = {r[0]: {"entries": r[1], "total_hits": r[2] or 0} for r in rows}
    return {
        "total_entries": sum(v["entries"] for v in by_type.values()),
        "by_type": by_type,
    }


def get_db_stats() -> dict:
    """Return persona counts by source."""
    if not DB_PATH.exists():
        return {"total": 0, "seed": 0, "generated": 0}
    conn = sqlite3.connect(str(DB_PATH))
    total = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
    seed = conn.execute("SELECT COUNT(*) FROM personas WHERE source='seed'").fetchone()[0]
    generated = total - seed
    conn.close()
    return {"total": total, "seed": seed, "generated": generated}


def migrate_seed_personas():
    """One-time: load seed personas from JSON into SQLite."""
    if not PERSONAS_JSON.exists():
        print(f"[panel_engine] No seed file at {PERSONAS_JSON}")
        return

    init_db()
    conn = sqlite3.connect(str(DB_PATH))

    # Check if already migrated
    count = conn.execute("SELECT COUNT(*) FROM personas WHERE source='seed'").fetchone()[0]
    if count > 0:
        print(f"[panel_engine] Already have {count} seed personas, skipping migration")
        conn.close()
        return

    with open(PERSONAS_JSON, "r", encoding="utf-8") as f:
        personas = json.load(f)

    for p in personas:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO personas
                   (id, name, age, sex, province, city, occupation,
                    education_level, income_bracket, estimated_annual_income,
                    income_source, marital_status, immigration_status,
                    indigenous_identity, visible_minority, cultural_background,
                    languages_spoken, housing, political_leaning, religion,
                    commute_mode, top_concerns, personality, skills_and_expertise,
                    hobbies_and_interests, career_goals, source, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           ?, ?, ?, ?, ?, ?, ?, ?, ?, 'seed', ?)""",
                (
                    p.get("uuid", p.get("id", "")),
                    p.get("name", ""),
                    p.get("age", 0),
                    p.get("sex", ""),
                    p.get("province", ""),
                    p.get("planning_area", p.get("city", "")),
                    p.get("occupation", ""),
                    p.get("education_level", ""),
                    p.get("income_bracket"),
                    p.get("estimated_annual_income"),
                    p.get("income_source"),
                    p.get("marital_status", ""),
                    p.get("immigration_status", ""),
                    p.get("indigenous_identity", ""),
                    p.get("visible_minority", ""),
                    p.get("cultural_background", ""),
                    p.get("languages_spoken", ""),
                    p.get("housing", ""),
                    p.get("political_leaning"),
                    p.get("religion"),
                    p.get("commute_mode"),
                    json.dumps(p.get("top_concerns", [])),
                    p.get("personality"),
                    p.get("skills_and_expertise"),
                    p.get("hobbies_and_interests"),
                    p.get("career_goals"),
                    json.dumps(p),
                ),
            )
        except Exception as e:
            print(f"[panel_engine] Failed to insert: {e}")

    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
    conn.close()
    print(f"[panel_engine] Migrated {final} seed personas to SQLite")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  AUDIENCE BRIEF PARSER                                          ║
# ╚══════════════════════════════════════════════════════════════════╝

class IntRange(BaseModel):
    """A min/max integer range."""
    min: int
    max: int


class AudienceSpec(BaseModel):
    """Structured representation of a target audience."""
    age_range: IntRange | None = Field(None, description="e.g. {min: 25, max: 40}")
    sex: str | None = None
    provinces: list[str] | None = Field(None, description="e.g. ['Ontario', 'BC']")
    income_range: IntRange | None = Field(None, description="Annual income range e.g. {min: 60000, max: 100000}")
    education: list[str] | None = None
    occupation_keywords: list[str] | None = None
    immigration_status: str | None = None
    religion: list[str] | None = Field(None, description="e.g. ['Muslim'], ['Hindu', 'Sikh']")
    cultural_background: list[str] | None = Field(None, description="e.g. ['Chinese', 'Vietnamese', 'Korean']. Infer from cultural context clues like holidays, traditions, cuisines, etc.")
    values: list[str] | None = None
    concerns: list[str] | None = None
    lifestyle: list[str] | None = None
    interests: list[str] | None = None
    domain: str | None = None
    purchase_context: str | None = None
    behavioral_traits: list[str] | None = None
    holiday_or_festival: str | None = Field(
        None,
        description=(
            "The canonical holiday or festival name if one is mentioned or implied. "
            "Normalize to standard lowercase form: e.g. 'Ugadhi' → 'ugadi', "
            "'Chinese New Year' → 'lunar new year', 'Festival of Lights' → 'diwali', "
            "'Tamil harvest festival' → 'pongal'. "
            "Valid values: lunar new year, mid-autumn festival, chuseok, tet, "
            "diwali, navratri, vaisakhi, holi, ugadi, gudi padwa, pongal, onam, "
            "lohri, bihu, durga puja, ganesh chaturthi, eid, eid al-fitr, eid al-adha, "
            "ramadan, hanukkah, rosh hashanah, passover, simbang gabi, noche buena, "
            "national indigenous peoples day, pow wow, obon, caribana, carnival, "
            "black history month, canada day, thanksgiving, christmas, victoria day. "
            "Use null if no holiday/festival is referenced."
        ),
    )
    raw_brief: str = ""


BRIEF_PARSER_PROMPT = """You are parsing a target audience description into structured fields.
Extract as many fields as you can. Leave fields as null if not mentioned or implied.

IMPORTANT:
- occupation_keywords should contain SPECIFIC job titles or industries (e.g. "software developer",
  "nurse", "finance"). Do NOT put vague descriptors like "young professionals" or "working adults"
  here — those belong in lifestyle or behavioral_traits.
- When the brief involves a PURCHASE (buying, shopping, considering), infer a realistic income_range
  even if not explicitly stated. Condo buyers need $60K+, luxury car buyers need $100K+, etc.
- When the brief mentions SPENDING LEVEL or LIFESTYLE SIGNALS (e.g. "mid spenders", "luxury lovers",
  "budget-conscious", "high-income", "affluent"), ALWAYS map these to an income_range:
  - "budget-conscious" / "low income" / "cost-conscious" → {min: 0, max: 40000}
  - "mid spenders" / "middle class" / "moderate income" → {min: 40000, max: 80000}
  - "affluent" / "luxury" / "high spenders" / "premium" → {min: 80000, max: 200000}
  Adjust based on context (e.g. "luxury lovers" who are "mid spenders" → {min: 50000, max: 100000}).
- When a brief mentions a BRAND, RETAILER, or COMPANY, use your knowledge of that brand's typical
  customer to infer demographics. Think about who actually shops there:
  - Age range (e.g. IKEA skews 20-40, Costco skews 35-65)
  - Income level (e.g. Costco membership implies $80K+ household, Walmart is broad $30K-$100K)
  - Gender skew if any (e.g. grocery/household retailers skew 55-65% female primary shoppers)
  - Geographic presence (e.g. IKEA only in major cities, Walmart everywhere)
  - Lifestyle signals (e.g. Costco = suburban families who buy in bulk, IKEA = urban renters/first homes)

Examples:
- "Young professionals in Vancouver, $80-120K, environmentally conscious, considering EVs"
  → age_range: {min: 25, max: 35}, provinces: ["British Columbia"], income_range: {min: 80000, max: 120000},
    values: ["environmentally conscious"], domain: "electric vehicles",
    lifestyle: ["urban professional"], purchase_context: "considering EVs"

- "Young professionals interested in buying new condo developments in downtown Calgary"
  → age_range: {min: 25, max: 40}, provinces: ["Alberta"], income_range: {min: 60000, max: 150000},
    lifestyle: ["urban", "career-focused"], domain: "real estate",
    purchase_context: "buying new condo developments in downtown Calgary"

- "Parents of school-age kids worried about screen time"
  → age_range: {min: 30, max: 50}, concerns: ["screen time"], lifestyle: ["parent"], domain: "parenting/technology"

- "Budget-conscious students in Montreal"
  → age_range: {min: 18, max: 25}, provinces: ["Quebec"], income_range: {min: 0, max: 30000},
    occupation_keywords: ["student"], lifestyle: ["urban", "budget-conscious"]

- "Halal mortgage product for Muslim homebuyers in the GTA"
  → provinces: ["Ontario"], religion: ["Muslim"], income_range: {min: 60000, max: 150000},
    domain: "financial services / home financing",
    purchase_context: "halal mortgage product for Muslim homebuyers in the GTA"

- "South Asian families considering private school options in Brampton"
  → age_range: {min: 30, max: 55}, provinces: ["Ontario"], lifestyle: ["parent", "family-oriented"],
    domain: "education", values: ["education-focused"],
    purchase_context: "considering private school options"

- "Shopping for Lunar New Year"
  → income_range: {min: 0, max: 150000}, values: ["family-oriented", "tradition-oriented", "celebratory"],
    lifestyle: ["gift shopper", "seasonal shopper"], interests: ["Lunar New Year", "festive shopping"],
    cultural_background: ["Chinese", "Vietnamese", "Korean"],
    holiday_or_festival: "lunar new year",
    domain: "retail / seasonal shopping", purchase_context: "shopping for Lunar New Year",
    behavioral_traits: ["seasonal buyer", "occasion-driven"]

- "Diwali marketing campaign for a jewelry brand"
  → cultural_background: ["South Asian"], values: ["family-oriented", "celebratory"],
    lifestyle: ["jewelry buyer", "gift shopper"], domain: "retail / jewelry",
    holiday_or_festival: "diwali",
    purchase_context: "Diwali jewelry shopping"

- "Ugadhi celebrations"
  → cultural_background: ["South Asian"], holiday_or_festival: "ugadi",
    values: ["tradition-oriented", "celebratory"], interests: ["Ugadi", "festive shopping"]

- "Chinese New Year gift boxes"
  → cultural_background: ["Chinese"], holiday_or_festival: "lunar new year",
    lifestyle: ["gift shopper"], domain: "retail / gifting"

- "Costco shoppers in Canada"
  → age_range: {min: 30, max: 65}, income_range: {min: 80000, max: 200000},
    lifestyle: ["bulk shopper", "suburban family", "value-conscious", "homeowner"],
    domain: "retail / warehouse club", behavioral_traits: ["membership buyer", "stockpiler"]

- "IKEA shoppers in Canada"
  → age_range: {min: 20, max: 40}, income_range: {min: 30000, max: 100000},
    lifestyle: ["urban renter", "first-time homebuyer", "DIY", "design-conscious"],
    domain: "retail / home furnishings", behavioral_traits: ["budget-conscious", "self-assembly"]

- "Walmart shoppers in Canada"
  → age_range: {min: 18, max: 65}, income_range: {min: 25000, max: 100000},
    lifestyle: ["budget-conscious family", "value shopper"],
    domain: "retail / general merchandise + grocery",
    behavioral_traits: ["price-sensitive", "convenience-driven"]

- "French Canadians in Quebec and New Brunswick, culturally proud, mid spenders, luxury lovers"
  → provinces: ["Quebec", "New Brunswick"], income_range: {min: 50000, max: 100000},
    values: ["culturally proud", "French-Canadian identity"], lifestyle: ["luxury-oriented", "mid spender"],
    behavioral_traits: ["brand-conscious", "quality-over-quantity"]

IMPORTANT: When a brief references a cultural holiday, tradition, cuisine, or festival:
1. Set holiday_or_festival to the CANONICAL name from the valid values list (normalize alternate
   names, misspellings, and indirect references like "festival of lights" → "diwali").
2. Infer the cultural_background of the communities most associated with it (e.g. Lunar New Year
   → Chinese, Vietnamese, Korean; Diwali → South Asian; Eid → Muslim via religion field).
"""


def parse_audience_brief(brief: str, model: ChatOpenAI, config: dict | None = None) -> AudienceSpec:
    """Parse free-text audience description into structured spec (cached)."""
    # Check cache
    cached = _cache_get("audience_spec", brief)
    if cached is not None:
        spec = AudienceSpec(**cached)
        spec.raw_brief = brief
        return spec

    result = model.with_structured_output(AudienceSpec).invoke([
        SystemMessage(content=BRIEF_PARSER_PROMPT),
        HumanMessage(content=f"Parse this audience description:\n\n{brief}"),
    ], config=config)
    result.raw_brief = brief

    # Cache the result
    _cache_set("audience_spec", result.model_dump(), brief)
    return result


# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONTEXT PROJECTION                                             ║
# ╚══════════════════════════════════════════════════════════════════╝

ATTRIBUTE_GROUPS = {
    "core": [
        "age", "sex", "province", "city", "occupation",
        "education_level", "income_bracket", "languages_spoken",
    ],
    "identity": [
        "immigration_status", "indigenous_identity", "visible_minority",
        "cultural_background", "religion",
    ],
    "housing": ["housing", "commute_mode"],
    "political": ["political_leaning", "top_concerns"],
    "health": [],
    "digital": [],
    "financial": [],
    "civic": [],
    "lifestyle": ["hobbies_and_interests"],
    "values": [],
    "consumer": [],
}


class ContextProjection(BaseModel):
    """Determines which persona attributes to include in subagent prompts."""
    relevant_groups: list[str] = Field(description="Which attribute groups are relevant")
    relevant_extended_keys: list[str] = Field(description="Specific extended_attributes keys")
    reasoning: str = Field(description="Why these groups were selected")


def determine_relevant_attributes(
    use_case: str,
    audience_brief: str,
    content: str,
    model: ChatOpenAI,
    config: dict | None = None,
) -> ContextProjection:
    """LLM determines which persona attributes matter for this query (cached)."""
    content_prefix = content[:300]

    # Check cache
    cached = _cache_get("context_projection", use_case, audience_brief, content_prefix)
    if cached is not None:
        return ContextProjection(**cached)

    result = model.with_structured_output(ContextProjection).invoke([
        SystemMessage(content=f"""You decide which persona attributes are relevant for a focus group query.

Available attribute groups:
{json.dumps(ATTRIBUTE_GROUPS, indent=2)}

The "core" group is ALWAYS included. Select additional groups based on:
- The use case type
- What the audience brief emphasizes
- What the content being tested is about

Guidelines:
- "political" should only be included when the content is about policy, politics,
  government, social issues, or topics where political leaning materially affects
  reception. Do NOT include it for product, technology, or technical content.
- "identity" matters for content that touches on culture, immigration, diversity,
  or region-specific messaging.
- "housing" and "lifestyle" matter for consumer and lifestyle products.
- Be selective — typically 2-4 groups beyond core is right.

Also specify which extended_attributes keys should be populated."""),
        HumanMessage(content=f"""Use case: {use_case}
Audience brief: {audience_brief}
Content to test: {content_prefix}"""),
    ], config=config)

    # Cache the result
    _cache_set("context_projection", result.model_dump(), use_case, audience_brief, content_prefix)
    return result


def build_projected_context(persona: dict, projection: ContextProjection) -> str:
    """Build a lean persona context string using only relevant attributes."""
    lines = []

    lines.append(
        f"Age: {persona.get('age', '?')} | Sex: {persona.get('sex', '?')} | "
        f"Province: {persona.get('province', '?')}"
    )
    city = persona.get("city") or persona.get("planning_area", "")
    if city:
        lines.append(f"City/Region: {city}")
    lines.append(
        f"Occupation: {persona.get('occupation', '?')} | "
        f"Education: {persona.get('education_level', '?')}"
    )
    lines.append(f"Income: {persona.get('income_bracket', 'Unknown')}")
    lines.append(f"Languages: {persona.get('languages_spoken', '?')}")

    groups = set(projection.relevant_groups)

    if "identity" in groups:
        lines.append(
            f"Immigration: {persona.get('immigration_status', '?')} | "
            f"Indigenous: {persona.get('indigenous_identity', '?')}"
        )
        vm = persona.get("visible_minority", "")
        if vm and vm != "Not a visible minority":
            lines.append(f"Visible minority: {vm}")
        cb = persona.get("cultural_background", "")
        if cb:
            lines.append(f"Cultural background: {cb}")
        rel = persona.get("religion", "")
        if rel:
            lines.append(f"Religion: {rel}")

    if "housing" in groups:
        lines.append(f"Housing: {persona.get('housing', '?')}")
        cm = persona.get("commute_mode", "")
        if cm and cm != "not applicable":
            lines.append(f"Commute: {cm}")

    if "political" in groups:
        lines.append(f"Political leaning: {persona.get('political_leaning', 'Unknown')}")
        concerns = persona.get("top_concerns", [])
        if isinstance(concerns, str):
            try:
                concerns = json.loads(concerns)
            except (json.JSONDecodeError, TypeError):
                concerns = []
        if concerns:
            lines.append(f"Top concerns: {', '.join(concerns)}")

    if "lifestyle" in groups:
        hobbies = persona.get("hobbies_and_interests", "")
        if hobbies:
            lines.append(f"Hobbies/interests: {hobbies}")

    # Extended attributes
    ext = persona.get("extended_attributes", "{}")
    if isinstance(ext, str):
        try:
            ext = json.loads(ext) if ext else {}
        except (json.JSONDecodeError, TypeError):
            ext = {}

    for key in projection.relevant_extended_keys:
        if key in ext and ext[key] is not None:
            label = key.replace("_", " ").title()
            value = ext[key]
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(f"{label}: {value}")

    return "\n".join(lines)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  AGENT TOOLS                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

@tool
def search_personas(
    province: list[str] | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    sex: str | None = None,
    income_bracket: list[str] | None = None,
    income_min: int | None = None,
    income_max: int | None = None,
    education: list[str] | None = None,
    religion: list[str] | None = None,
    cultural_background: list[str] | None = None,
    occupation_keywords: list[str] | None = None,
    concerns_keywords: list[str] | None = None,
    limit: int = 50,
) -> dict:
    """Search the persona database for existing personas matching filters.

    Always call this BEFORE generate_personas — reuse existing personas first.

    Args:
        province: Filter by provinces, e.g. ["Ontario", "British Columbia"]
        age_min: Minimum age inclusive
        age_max: Maximum age inclusive
        sex: Filter by sex
        income_bracket: Filter by income bracket labels, e.g. ["$60K-$80K", "$80K-$100K"]
        income_min: Minimum annual income in dollars (e.g. 60000). Use this for
            purchase-related briefs to ensure personas can realistically afford the product.
        income_max: Maximum annual income in dollars (e.g. 150000)
        education: Filter by education levels
        religion: Filter by religion, e.g. ["Muslim"], ["Hindu", "Sikh"]
        cultural_background: Filter by cultural background, e.g. ["Chinese", "Vietnamese", "Korean"].
            Matches as substring in cultural_background field (e.g. "Chinese" matches "Chinese-Canadian").
        occupation_keywords: Keywords to match in occupation field
        concerns_keywords: Keywords to match in top_concerns
        limit: Max personas to return

    Returns:
        dict with 'personas' (list), 'total_matches' (int), 'coverage_score' (float 0-1)
    """
    conn = sqlite3.connect(str(DB_PATH))
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
    if income_min is not None:
        conditions.append("estimated_annual_income >= ?")
        params.append(income_min)
    if income_max is not None:
        conditions.append("estimated_annual_income <= ?")
        params.append(income_max)
    if education:
        placeholders = ",".join("?" * len(education))
        conditions.append(f"education_level IN ({placeholders})")
        params.extend(education)
    if religion:
        placeholders = ",".join("?" * len(religion))
        conditions.append(f"religion IN ({placeholders})")
        params.extend(religion)
    if cultural_background:
        # Substring match: "Chinese" matches "Chinese-Canadian, family from Beijing"
        cb_clauses = " OR ".join(["cultural_background LIKE ?" for _ in cultural_background])
        conditions.append(f"({cb_clauses})")
        params.extend([f"%{cb}%" for cb in cultural_background])

    where = " AND ".join(conditions) if conditions else "1=1"

    total = conn.execute(
        f"SELECT COUNT(*) FROM personas WHERE {where}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"SELECT raw_json FROM personas WHERE {where} ORDER BY RANDOM() LIMIT ?",
        params + [limit],
    ).fetchall()

    conn.close()

    personas = [json.loads(r["raw_json"]) for r in rows]

    # Post-filter by keywords
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

    filters_requested = sum(1 for x in [
        province, age_min, age_max, sex, income_bracket, income_min, income_max,
        education, religion, cultural_background, occupation_keywords, concerns_keywords,
    ] if x is not None)
    coverage = 1.0 if filters_requested == 0 else (
        min(1.0, len(personas) / max(limit, 1))
    )

    return {
        "personas": personas[:limit],
        "total_matches": total,
        "coverage_score": round(coverage, 2),
        "message": f"Found {total} matching, returned {len(personas[:limit])}",
    }


# Religion → cultural background correlations (Census 2021 + NHS 2011)
# When religion is constrained, bias visible_minority + cultural_background
# to match realistic Canadian demographics for that faith community.
_RELIGION_CULTURAL_WEIGHTS: dict[str, dict[str, float]] = {
    "Muslim": {
        "South Asian": 36,      # Pakistani, Bangladeshi, Indian
        "Arab": 20,
        "Black": 15,            # Somali, Nigerian, etc.
        "West Asian": 10,       # Iranian, Afghan, Turkish
        "Not a visible minority": 10,  # Bosnian, Albanian, converts
        "Southeast Asian": 4,
        "Multiple visible minorities": 3,
        "Visible minority n.i.e.": 2,
    },
    "Hindu": {
        "South Asian": 85,
        "Not a visible minority": 5,
        "Black": 3,             # Indo-Caribbean
        "Southeast Asian": 3,
        "Multiple visible minorities": 2,
        "Visible minority n.i.e.": 2,
    },
    "Sikh": {
        "South Asian": 95,
        "Not a visible minority": 3,
        "Multiple visible minorities": 2,
    },
    "Buddhist": {
        "Chinese": 35,
        "Southeast Asian": 25,
        "South Asian": 15,      # Sri Lankan
        "Korean": 5,
        "Japanese": 5,
        "Not a visible minority": 10,
        "Multiple visible minorities": 3,
        "Visible minority n.i.e.": 2,
    },
    "Jewish": {
        "Not a visible minority": 90,
        "Multiple visible minorities": 5,
        "Visible minority n.i.e.": 5,
    },
}

# Cultural background labels — more specific than visible_minority
# ── Cultural Holiday → Community Mapping ──────────────────────────
# Maps holiday/festival keywords to the visible_minority groups and
# cultural_background values most associated with them in Canada.
# Used by the brief parser prompt AND as a deterministic fallback
# when AudienceSpec.cultural_background is empty but the brief
# mentions a recognizable cultural event.

CULTURAL_HOLIDAY_MAP: dict[str, dict] = {
    # ── East Asian ──
    "lunar new year": {
        "aliases": ["chinese new year", "spring festival", "seollal", "tết nguyên đán"],
        "visible_minority": ["Chinese", "Vietnamese", "Korean"],
        "cultural_background": ["Chinese", "Vietnamese", "Korean"],
    },
    "mid-autumn festival": {
        "aliases": ["moon festival", "mooncake festival", "zhongqiu"],
        "visible_minority": ["Chinese", "Vietnamese"],
        "cultural_background": ["Chinese", "Vietnamese"],
    },
    "chuseok": {
        "aliases": ["korean thanksgiving"],
        "visible_minority": ["Korean"],
        "cultural_background": ["Korean"],
    },
    "tet": {
        "aliases": ["tet holiday", "vietnamese new year"],
        "visible_minority": ["Southeast Asian"],
        "cultural_background": ["Vietnamese"],
    },
    # ── South Asian ──
    "diwali": {
        "aliases": ["deepavali", "deepawali", "festival of lights"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Indian", "Nepali", "Sri Lankan"],
        "religion": ["Hindu", "Sikh"],
    },
    "navratri": {
        "aliases": ["navaratri", "navrathri"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Indian"],
        "religion": ["Hindu"],
    },
    "vaisakhi": {
        "aliases": ["baisakhi", "vasakhi"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Indian"],
        "religion": ["Sikh"],
    },
    "holi": {
        "aliases": ["festival of colors", "festival of colours"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Indian", "Nepali"],
        "religion": ["Hindu"],
    },
    "ugadi": {
        "aliases": ["ugadhi", "yugadi", "ugaadi"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Telugu", "Marathi"],
        "religion": ["Hindu"],
    },
    "gudi padwa": {
        "aliases": ["gudipadwa"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Marathi"],
        "religion": ["Hindu"],
    },
    "pongal": {
        "aliases": ["thai pongal", "tamil harvest festival"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Tamil"],
        "religion": ["Hindu"],
    },
    "onam": {
        "aliases": ["thiruvonam"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Malayalam"],
        "religion": ["Hindu"],
    },
    "lohri": {
        "aliases": [],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Punjabi"],
        "religion": ["Sikh", "Hindu"],
    },
    "bihu": {
        "aliases": ["rongali bihu", "bohag bihu"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Indian"],
        "religion": ["Hindu"],
    },
    "durga puja": {
        "aliases": ["durgapuja", "pujo"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Bengali"],
        "religion": ["Hindu"],
    },
    "ganesh chaturthi": {
        "aliases": ["vinayaka chaturthi", "ganpati"],
        "visible_minority": ["South Asian"],
        "cultural_background": ["Marathi", "Telugu"],
        "religion": ["Hindu"],
    },
    # ── Muslim ──
    "eid": {
        "aliases": ["eid mubarak"],
        "visible_minority": ["South Asian", "Arab", "Black", "West Asian"],
        "cultural_background": ["Pakistani", "Egyptian", "Somali", "Lebanese", "Iranian"],
        "religion": ["Muslim"],
    },
    "eid al-fitr": {
        "aliases": ["eid ul-fitr", "eid-ul-fitr"],
        "visible_minority": ["South Asian", "Arab", "Black", "West Asian"],
        "cultural_background": ["Pakistani", "Egyptian", "Somali", "Lebanese"],
        "religion": ["Muslim"],
    },
    "eid al-adha": {
        "aliases": ["eid ul-adha", "eid-ul-adha", "bakra eid", "bakrid"],
        "visible_minority": ["South Asian", "Arab", "Black", "West Asian"],
        "cultural_background": ["Pakistani", "Egyptian", "Somali", "Lebanese"],
        "religion": ["Muslim"],
    },
    "ramadan": {
        "aliases": ["ramazan", "ramzan"],
        "visible_minority": ["South Asian", "Arab", "Black", "West Asian"],
        "cultural_background": ["Pakistani", "Egyptian", "Somali", "Lebanese", "Iranian"],
        "religion": ["Muslim"],
    },
    # ── Jewish ──
    "hanukkah": {
        "aliases": ["chanukah", "hannukah", "festival of dedication"],
        "visible_minority": ["Not a visible minority"],
        "cultural_background": ["Canadian", "British", "Polish"],
        "religion": ["Jewish"],
    },
    "rosh hashanah": {
        "aliases": ["rosh hashana", "jewish new year"],
        "visible_minority": ["Not a visible minority"],
        "cultural_background": ["Canadian", "British"],
        "religion": ["Jewish"],
    },
    "passover": {
        "aliases": ["pesach"],
        "visible_minority": ["Not a visible minority"],
        "cultural_background": ["Canadian", "British"],
        "religion": ["Jewish"],
    },
    # ── Filipino ──
    "simbang gabi": {
        "aliases": [],
        "visible_minority": ["Filipino"],
        "cultural_background": ["Filipino"],
    },
    "noche buena": {
        "aliases": [],
        "visible_minority": ["Filipino"],
        "cultural_background": ["Filipino"],
    },
    # ── Indigenous ──
    "national indigenous peoples day": {
        "aliases": ["indigenous day"],
        "indigenous_identity": ["First Nations", "Métis", "Inuit"],
    },
    "national day for truth and reconciliation": {
        "aliases": ["orange shirt day", "truth and reconciliation"],
        "indigenous_identity": ["First Nations", "Métis", "Inuit"],
    },
    "pow wow": {
        "aliases": ["powwow"],
        "indigenous_identity": ["First Nations"],
    },
    # ── Japanese ──
    "obon": {
        "aliases": ["bon festival"],
        "visible_minority": ["Japanese"],
        "cultural_background": ["Japanese"],
    },
    # ── Caribbean / Black ──
    "caribana": {
        "aliases": ["toronto caribbean carnival"],
        "visible_minority": ["Black", "Latin American"],
        "cultural_background": ["Jamaican", "Haitian", "Colombian", "Nigerian"],
    },
    "carnival": {
        "aliases": ["carnaval"],
        "visible_minority": ["Black", "Latin American"],
        "cultural_background": ["Jamaican", "Haitian", "Colombian"],
    },
    "black history month": {
        "aliases": ["bhm"],
        "visible_minority": ["Black"],
        "cultural_background": ["Jamaican", "Nigerian", "Somali", "Ethiopian", "Haitian"],
    },
    # ── General Canadian ──
    "canada day": {"aliases": []},
    "thanksgiving": {"aliases": ["canadian thanksgiving"]},
    "christmas": {"aliases": ["xmas"]},
    "victoria day": {"aliases": ["may two-four", "may long weekend"]},
}

# Build flattened lookup: canonical keys + all aliases → mapping (without aliases field)
_HOLIDAY_LOOKUP: dict[str, dict] = {}
for _canonical, _entry in CULTURAL_HOLIDAY_MAP.items():
    _mapping = {k: v for k, v in _entry.items() if k != "aliases"}
    _HOLIDAY_LOOKUP[_canonical] = _mapping
    for _alias in _entry.get("aliases", []):
        _HOLIDAY_LOOKUP[_alias] = _mapping


# ── Life Event → Audience Constraints ─────────────────────────────
# Maps life event keywords to demographic constraints that should be
# applied when the AudienceSpec doesn't already cover them.
# These act as "safety nets" for the deterministic builder.

LIFE_EVENT_MAP: dict[str, dict] = {
    # Housing / Real estate
    "first-time homebuyer": {"age_min": 25, "age_max": 40, "income_min": 60000},
    "buying a house": {"age_min": 25, "age_max": 55, "income_min": 60000},
    "buying a home": {"age_min": 25, "age_max": 55, "income_min": 60000},
    "buying a condo": {"age_min": 25, "age_max": 45, "income_min": 50000},
    "mortgage": {"age_min": 25, "age_max": 55, "income_min": 50000},
    "downsizing": {"age_min": 55, "age_max": 75},
    "empty nester": {"age_min": 50, "age_max": 70},
    # Education / School
    "back to school": {"age_min": 25, "age_max": 50},  # parents shopping
    "going to university": {"age_min": 17, "age_max": 22, "occupation_keywords": ["student"]},
    "going to college": {"age_min": 17, "age_max": 25, "occupation_keywords": ["student"]},
    "sending kids to university": {"age_min": 45, "age_max": 60, "income_min": 60000},
    "student loan": {"age_min": 18, "age_max": 30, "occupation_keywords": ["student"]},
    # Career
    "new job": {"age_min": 22, "age_max": 45},
    "career change": {"age_min": 28, "age_max": 50},
    "job hunting": {"age_min": 22, "age_max": 55},
    "starting a business": {"age_min": 25, "age_max": 50},
    # Family
    "new baby": {"age_min": 25, "age_max": 40},
    "expecting a baby": {"age_min": 25, "age_max": 40},
    "new parent": {"age_min": 24, "age_max": 40},
    "daycare": {"age_min": 25, "age_max": 42},
    "wedding planning": {"age_min": 25, "age_max": 38},
    "getting married": {"age_min": 24, "age_max": 38},
    "divorce": {"age_min": 30, "age_max": 60},
    # Retirement
    "retirement": {"age_min": 50, "age_max": 70},
    "retirement planning": {"age_min": 50, "age_max": 65, "income_min": 50000},
    "pension": {"age_min": 55, "age_max": 75},
    # Health milestones
    "menopause": {"age_min": 45, "age_max": 60, "sex": "Female"},
    "senior care": {"age_min": 45, "age_max": 65},
    "aging parent": {"age_min": 40, "age_max": 60},
    # Big purchases
    "buying a car": {"age_min": 22, "age_max": 60, "income_min": 30000},
    "luxury car": {"age_min": 30, "age_max": 60, "income_min": 100000},
    "electric vehicle": {"age_min": 25, "age_max": 55, "income_min": 50000},
    "renovation": {"age_min": 30, "age_max": 60, "income_min": 60000},
}


def _infer_life_event_from_brief(brief: str) -> dict:
    """Check if the brief mentions a known life event and return matching constraints.

    Returns a dict with optional keys: age_min, age_max, income_min, income_max,
    sex, occupation_keywords. Empty dict if no match.
    """
    brief_lower = brief.lower()
    for event, constraints in LIFE_EVENT_MAP.items():
        if event in brief_lower:
            return constraints
    return {}


def _infer_cultural_from_brief(audience_spec: AudienceSpec) -> dict:
    """Resolve cultural holiday mapping from the parsed AudienceSpec.

    Uses a two-layer approach:
      1. PRIMARY: Look up audience_spec.holiday_or_festival (LLM-normalized canonical name)
      2. FALLBACK: Substring match raw_brief + interests against _HOLIDAY_LOOKUP keys

    The LLM handles fuzzy interpretation — typos, alternate names ("Chinese New Year" →
    "lunar new year"), indirect references ("festival of lights" → "diwali") — and outputs
    a canonical key. The substring fallback catches cases where the LLM leaves the field null.

    Returns a dict with optional keys: cultural_background, visible_minority, religion,
    indigenous_identity. Empty dict if no match.
    """
    # Layer 1: LLM-normalized holiday name (handles typos, alternate names, indirect refs)
    if audience_spec.holiday_or_festival:
        normalized = audience_spec.holiday_or_festival.lower().strip()
        if normalized in _HOLIDAY_LOOKUP:
            print(f"[deterministic] Holiday resolved via LLM: '{normalized}'")
            return _HOLIDAY_LOOKUP[normalized]

    # Layer 2: Substring fallback against all canonical names + aliases
    searchable = (audience_spec.raw_brief or "").lower()
    if audience_spec.interests:
        searchable += " " + " ".join(i.lower() for i in audience_spec.interests)
    for key, mapping in _HOLIDAY_LOOKUP.items():
        if key in searchable and mapping:
            print(f"[deterministic] Holiday resolved via substring fallback: '{key}'")
            return mapping
    return {}


_CULTURAL_BACKGROUND_BY_VM: dict[str, list[str]] = {
    "South Asian": [
        "Pakistani", "Indian", "Bangladeshi", "Sri Lankan", "Nepali", "Afghan",
        "Tamil", "Punjabi", "Gujarati", "Telugu", "Malayalam", "Bengali", "Marathi",
    ],
    "Arab": ["Lebanese", "Egyptian", "Syrian", "Iraqi", "Moroccan", "Palestinian", "Algerian"],
    "Black": ["Somali", "Nigerian", "Jamaican", "Ethiopian", "Haitian", "Ghanaian", "Congolese"],
    "West Asian": ["Iranian", "Turkish", "Kurdish", "Afghan"],
    "Chinese": ["Chinese"],
    "Filipino": ["Filipino"],
    "Southeast Asian": ["Vietnamese", "Cambodian", "Thai", "Indonesian", "Malaysian"],
    "Korean": ["Korean"],
    "Japanese": ["Japanese"],
    "Latin American": ["Mexican", "Colombian", "Brazilian", "Salvadoran", "Peruvian"],
    "Not a visible minority": [
        "Canadian", "British", "French", "Italian", "German", "Ukrainian", "Polish",
        "Bosnian", "Albanian", "Irish", "Scottish", "Dutch", "Swiss", "Austrian",
        "Portuguese", "Spanish", "Greek", "Serbian", "Croatian", "Romanian", "Hungarian",
        "Czech", "Slovak", "Swedish", "Norwegian", "Danish", "Finnish", "Russian",
        "Belgian", "Icelandic",
    ],
    "Multiple visible minorities": ["Mixed heritage"],
    "Visible minority n.i.e.": ["Other"],
}


_OCCUPATION_EXEMPLARS: dict[str, list[str]] = {
    "0 - Legislative and senior management": [
        "CEO", "Chief Financial Officer", "Director of Operations",
        "Municipal Councillor", "Vice President of Marketing",
        "Executive Director (Non-profit)", "Hospital Administrator", "General Manager",
    ],
    "1 - Business, finance and administration": [
        "Accountant", "Financial Analyst", "Human Resources Manager",
        "Administrative Assistant", "Bookkeeper", "Insurance Underwriter",
        "Office Manager", "Business Analyst", "Compliance Officer",
    ],
    "2 - Natural and applied sciences and related": [
        "Software Developer", "Civil Engineer", "Data Scientist",
        "Mechanical Engineer", "IT Project Manager", "Network Administrator",
        "Architect", "Cybersecurity Analyst", "UX Designer",
        "AI Researcher", "DevOps Engineer", "Product Manager (Tech)",
        "Machine Learning Engineer", "Cloud Solutions Architect",
    ],
    "3 - Health occupations": [
        "Registered Nurse", "Family Physician", "Pharmacist",
        "Dental Hygienist", "Physiotherapist", "Paramedic",
        "Personal Support Worker", "Veterinarian",
    ],
    "4 - Education, law and social, community and government": [
        "Elementary School Teacher", "High School Teacher", "Social Worker",
        "Lawyer", "Police Officer", "Professor", "Early Childhood Educator",
        "Firefighter", "Librarian",
    ],
    "5 - Art, culture, recreation and sport": [
        "Graphic Designer", "Journalist", "Photographer",
        "Fitness Instructor", "Film Editor", "Translator", "Musician",
    ],
    "6 - Sales and service": [
        "Retail Sales Associate", "Real Estate Agent", "Chef",
        "Customer Service Representative", "Hair Stylist", "Hotel Manager",
        "Restaurant Server", "Store Manager",
    ],
    "7 - Trades, transport and equipment operators": [
        "Electrician", "Plumber", "Carpenter", "Truck Driver",
        "Welder", "Heavy Equipment Operator", "Auto Mechanic",
        "HVAC Technician", "Bus Driver",
    ],
    "8 - Natural resources, agriculture and related production": [
        "Farm Manager", "Forestry Technician", "Fisher",
        "Mining Engineer", "Oil and Gas Driller", "Landscaper",
    ],
    "9 - Manufacturing and utilities": [
        "Machine Operator", "Quality Control Inspector",
        "Assembly Line Worker", "Power Plant Operator",
        "CNC Machinist", "Process Operator",
    ],
    "Not applicable / not in labour force": [
        "Retired", "University Student", "Stay-at-home Parent",
        "Unemployed (seeking work)", "College Student",
        "Graduate Student (Masters/PhD)", "Co-op Student",
    ],
}

# Income estimation by occupation category (median annual, approximate)
# Base data: Census 2021 (reflecting 2020 earnings)
# Inflation adjustment: ~23% cumulative CPI increase 2020→2026 (StatCan CPI)
_INCOME_INFLATION_FACTOR = 1.23

_OCCUPATION_INCOME_RANGES_2020: dict[str, tuple[int, int, int]] = {
    # (low, median, high) annual income — 2020 base values
    "0 - Legislative and senior management":                     (80000, 120000, 200000),
    "1 - Business, finance and administration":                  (35000, 55000, 95000),
    "2 - Natural and applied sciences and related":              (55000, 80000, 130000),
    "3 - Health occupations":                                    (40000, 70000, 150000),
    "4 - Education, law and social, community and government":   (45000, 65000, 110000),
    "5 - Art, culture, recreation and sport":                    (25000, 42000, 75000),
    "6 - Sales and service":                                     (22000, 35000, 60000),
    "7 - Trades, transport and equipment operators":             (35000, 55000, 90000),
    "8 - Natural resources, agriculture and related production": (30000, 50000, 85000),
    "9 - Manufacturing and utilities":                           (32000, 48000, 75000),
    "Not applicable / not in labour force":                      (0, 18000, 35000),
}

# Pre-compute inflation-adjusted ranges
_OCCUPATION_INCOME_RANGES: dict[str, tuple[int, int, int]] = {
    k: (
        int(lo * _INCOME_INFLATION_FACTOR),
        int(med * _INCOME_INFLATION_FACTOR),
        int(hi * _INCOME_INFLATION_FACTOR),
    )
    for k, (lo, med, hi) in _OCCUPATION_INCOME_RANGES_2020.items()
}


def _estimate_income(noc_category: str, occupation: str, age: int) -> dict:
    """Estimate income based on occupation category and age as career-stage proxy."""
    low, median, high = _OCCUPATION_INCOME_RANGES.get(
        noc_category, (25000, 45000, 80000)
    )

    # Special cases for non-employed (inflation-adjusted from 2020 base)
    f = _INCOME_INFLATION_FACTOR
    if occupation == "Retired":
        income = random.randint(int(18000 * f), int(45000 * f))
        return {"estimated_annual_income": income, "income_source": "estimated_pension"}
    if occupation in ("University Student", "College Student", "Graduate Student (Masters/PhD)", "Co-op Student"):
        income = random.randint(int(5000 * f), int(25000 * f))
        if occupation == "Graduate Student (Masters/PhD)":
            income = random.randint(int(15000 * f), int(35000 * f))  # TA/RA stipends
        elif occupation == "Co-op Student":
            income = random.randint(int(20000 * f), int(45000 * f))  # co-op earnings
        return {"estimated_annual_income": income, "income_source": "estimated_student"}
    if occupation == "Stay-at-home Parent":
        return {"estimated_annual_income": 0, "income_source": "not_employed"}
    if occupation == "Unemployed (seeking work)":
        income = random.randint(int(12000 * f), int(28000 * f))
        return {"estimated_annual_income": income, "income_source": "estimated_ei"}

    # Age-based career stage adjustment
    if age < 30:
        income = random.randint(low, median)
    elif age < 45:
        income = random.randint(median, high)
    elif age < 60:
        income = random.randint(int(median * 0.9), int(high * 1.1))
    else:
        income = random.randint(int(low * 0.8), median)

    noise = random.uniform(-0.05, 0.05)
    income = max(0, int(income * (1 + noise)))
    return {"estimated_annual_income": income, "income_source": "estimated_census"}


def _assign_income_bracket(annual_income: int | None) -> str:
    """Map annual income to a human-readable bracket."""
    if annual_income is None:
        return "Unknown"
    if annual_income < 20000:
        return "Under $20K"
    if annual_income < 40000:
        return "$20K-$40K"
    if annual_income < 60000:
        return "$40K-$60K"
    if annual_income < 80000:
        return "$60K-$80K"
    if annual_income < 100000:
        return "$80K-$100K"
    if annual_income < 150000:
        return "$100K-$150K"
    return "$150K+"


@tool
def generate_personas(
    count: int,
    province: list[str] | None = None,
    city: list[str] | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    sex: str | None = None,
    income_min: int | None = None,
    income_max: int | None = None,
    occupation_keywords: list[str] | None = None,
    religion: list[str] | None = None,
    cultural_background: list[str] | None = None,
    domain_context: str | None = None,
) -> list[dict]:
    """Generate new targeted personas using census-grounded distributions.

    Call this ONLY after search_personas shows insufficient coverage (<80%).
    Max 15 per call.

    Args:
        count: Number of personas to generate (max 15)
        province: Constrain to these provinces
        city: Constrain to these cities (e.g. ["Calgary", "Vancouver"])
        age_min: Minimum age
        age_max: Maximum age
        sex: Constrain to this sex
        income_min: Minimum annual income in dollars. Use for purchase-related briefs
            to ensure generated personas can realistically afford the product.
            Personas below this income will be re-rolled (up to 10 attempts).
        income_max: Maximum annual income in dollars
        occupation_keywords: Keywords to match when selecting occupations, e.g.
            ["software", "engineer", "data", "IT", "developer", "analyst"].
            When set, only NOC categories and exemplars matching these keywords
            will be used. Essential for technical/professional audiences.
        religion: Constrain to these religions, e.g. ["Muslim"]. When set,
            visible_minority and cultural_background are biased to match
            realistic Canadian demographics for that faith community.
        cultural_background: Constrain to these cultural backgrounds, e.g.
            ["Chinese", "Vietnamese", "Korean"]. When set, visible_minority is
            reverse-mapped from _CULTURAL_BACKGROUND_BY_VM to match.
        domain_context: Free-text domain context for tagging

    Returns:
        List of generated persona dicts (automatically persisted to DB)
    """
    count = min(count, 15)

    # Use the existing census-grounded generator
    try:
        from canada_demographics_2021 import (
            PROVINCE_TERRITORY_WEIGHTS, ADULT_AGE_WEIGHTS, SEX_AT_BIRTH_WEIGHTS,
            EDUCATION_WEIGHTS_25_64, OCCUPATION_WEIGHTS, MARITAL_STATUS_WEIGHTS,
            IMMIGRATION_STATUS_WEIGHTS, INDIGENOUS_IDENTITY_WEIGHTS,
            VISIBLE_MINORITY_WEIGHTS, HOUSING_TENURE_WEIGHTS,
            FIRST_OFFICIAL_LANGUAGE_WEIGHTS, PROVINCE_TO_CMAS, CMA_POPULATION,
        )
    except ImportError:
        return [{"error": "Could not import demographics module"}]

    import uuid as _uuid

    generated = []
    for _ in range(count):
        # Province
        if province:
            prov = random.choice(province)
        else:
            prov = random.choices(
                list(PROVINCE_TERRITORY_WEIGHTS.keys()),
                weights=list(PROVINCE_TERRITORY_WEIGHTS.values()),
            )[0]

        # Age — sample within requested range, avoid boundary clamping
        effective_min = age_min if age_min is not None else 18
        effective_max = age_max if age_max is not None else 85
        # Filter age brackets that overlap with the requested range
        eligible_brackets = []
        eligible_weights = []
        for bracket, weight in ADULT_AGE_WEIGHTS.items():
            if "-" in bracket:
                lo, hi = [int(x) for x in bracket.replace("+", "").split("-")]
            else:
                lo = int(bracket.replace("+", ""))
                hi = 90
            # Check if bracket overlaps with [effective_min, effective_max]
            if lo <= effective_max and hi >= effective_min:
                eligible_brackets.append((max(lo, effective_min), min(hi, effective_max)))
                eligible_weights.append(weight)

        if eligible_brackets:
            chosen = random.choices(eligible_brackets, weights=eligible_weights)[0]
            age = random.randint(chosen[0], chosen[1])
        else:
            age = random.randint(effective_min, effective_max)

        # Sex
        if sex:
            p_sex = sex
        else:
            p_sex = random.choices(
                list(SEX_AT_BIRTH_WEIGHTS.keys()),
                weights=list(SEX_AT_BIRTH_WEIGHTS.values()),
            )[0]

        # City — prefer specified cities, fall back to province CMA distribution
        if city:
            p_city = random.choice(city)
        else:
            cmas = PROVINCE_TO_CMAS.get(prov, [])
            if cmas:
                cma_pop = {name: pop for (_, name, _, pop) in CMA_POPULATION}
                cma_weights = [cma_pop.get(c, 1) for c in cmas]
                p_city = random.choices(cmas, weights=cma_weights)[0]
            else:
                p_city = prov

        # Other fields from distributions
        education = random.choices(
            list(EDUCATION_WEIGHTS_25_64.keys()),
            weights=list(EDUCATION_WEIGHTS_25_64.values()),
        )[0]

        # Filter NOC categories and exemplars by occupation_keywords if set
        if occupation_keywords:
            occ_kw = [k.lower() for k in occupation_keywords]
            # Build a filtered pool: exemplars whose title matches a keyword
            filtered_pool: list[tuple[str, str]] = []  # (noc_category, exemplar)
            seen_exemplars: set[str] = set()
            for noc_cat, exemplars_list in _OCCUPATION_EXEMPLARS.items():
                for ex in exemplars_list:
                    if any(k in ex.lower() for k in occ_kw):
                        filtered_pool.append((noc_cat, ex))
                        seen_exemplars.add(ex)
            # Also match NOC category names — include all their exemplars
            for noc_cat in _OCCUPATION_EXEMPLARS:
                if any(k in noc_cat.lower() for k in occ_kw):
                    for ex in _OCCUPATION_EXEMPLARS[noc_cat]:
                        if ex not in seen_exemplars:
                            filtered_pool.append((noc_cat, ex))
                            seen_exemplars.add(ex)
        else:
            filtered_pool = None

        # Sample occupation + income, re-rolling if outside requested income range
        for _attempt in range(10):
            if filtered_pool:
                noc_category, occupation = random.choice(filtered_pool)
            else:
                noc_category = random.choices(
                    list(OCCUPATION_WEIGHTS.keys()),
                    weights=list(OCCUPATION_WEIGHTS.values()),
                )[0]
                exemplars = _OCCUPATION_EXEMPLARS.get(noc_category, [])
                occupation = random.choice(exemplars) if exemplars else noc_category

            income_data = _estimate_income(noc_category, occupation, age)
            annual_income = income_data["estimated_annual_income"]

            # Check income constraints
            if income_min is not None and annual_income < income_min:
                continue
            if income_max is not None and annual_income > income_max:
                continue
            break  # income is within range
        else:
            # All attempts failed — clamp income to requested range
            if income_min is not None and annual_income < income_min:
                annual_income = income_min + random.randint(0, 5000)
            if income_max is not None and annual_income > income_max:
                annual_income = income_max - random.randint(0, 5000)
            income_data["estimated_annual_income"] = annual_income
        income_bracket = _assign_income_bracket(annual_income)

        marital = random.choices(
            list(MARITAL_STATUS_WEIGHTS.keys()),
            weights=list(MARITAL_STATUS_WEIGHTS.values()),
        )[0]
        immigration = random.choices(
            list(IMMIGRATION_STATUS_WEIGHTS.keys()),
            weights=list(IMMIGRATION_STATUS_WEIGHTS.values()),
        )[0]
        indigenous = random.choices(
            list(INDIGENOUS_IDENTITY_WEIGHTS.keys()),
            weights=list(INDIGENOUS_IDENTITY_WEIGHTS.values()),
        )[0]
        # Religion — constrain if specified, otherwise random from census distribution
        if religion:
            p_religion = random.choice(religion)
        else:
            p_religion = random.choice(["No religion", "Catholic", "Protestant", "Muslim", "Hindu", "Sikh", "Buddhist", "Jewish", "Other"])

        # Visible minority + cultural background
        # Priority: cultural_background constraint > religion correlation > census weights
        if cultural_background:
            # Pick a constrained cultural background, then reverse-map to visible minority
            p_cultural_bg = random.choice(cultural_background)
            # Reverse lookup: find which VM group contains this cultural background
            # Check both as a value in the lists AND as a key itself (e.g. "South Asian"
            # is both a VM key and a cultural_background value from the LLM)
            p_visible_minority = "Not a visible minority"
            if p_cultural_bg in _CULTURAL_BACKGROUND_BY_VM:
                # It's a VM group name itself (e.g. "South Asian", "Chinese", "Korean")
                p_visible_minority = p_cultural_bg
                # Pick a more specific cultural background from the group
                cb_options = _CULTURAL_BACKGROUND_BY_VM[p_cultural_bg]
                p_cultural_bg = random.choice(cb_options)
            else:
                for vm_group, cb_list in _CULTURAL_BACKGROUND_BY_VM.items():
                    if p_cultural_bg in cb_list:
                        p_visible_minority = vm_group
                        break
        else:
            cultural_weights = _RELIGION_CULTURAL_WEIGHTS.get(p_religion)
            if cultural_weights:
                vm_labels = list(cultural_weights.keys())
                vm_weights = list(cultural_weights.values())
                p_visible_minority = random.choices(vm_labels, weights=vm_weights)[0]
            else:
                p_visible_minority = random.choices(
                    list(VISIBLE_MINORITY_WEIGHTS.keys()),
                    weights=list(VISIBLE_MINORITY_WEIGHTS.values()),
                )[0]

            # Specific cultural background from visible minority group
            cb_options = _CULTURAL_BACKGROUND_BY_VM.get(p_visible_minority, ["Canadian"])
            p_cultural_bg = random.choice(cb_options)

        housing = random.choices(
            list(HOUSING_TENURE_WEIGHTS.keys()),
            weights=list(HOUSING_TENURE_WEIGHTS.values()),
        )[0]
        lang = random.choices(
            list(FIRST_OFFICIAL_LANGUAGE_WEIGHTS.keys()),
            weights=list(FIRST_OFFICIAL_LANGUAGE_WEIGHTS.values()),
        )[0]

        persona = {
            "uuid": str(_uuid.uuid4()),
            "id": str(_uuid.uuid4()),
            "name": f"Persona-{random.randint(10000, 99999)}",
            "age": age,
            "sex": p_sex,
            "province": prov,
            "planning_area": p_city,
            "city": p_city,
            "occupation": occupation,
            "education_level": education,
            "income_bracket": income_bracket,
            "estimated_annual_income": annual_income,
            "income_source": income_data["income_source"],
            "marital_status": marital,
            "immigration_status": immigration,
            "indigenous_identity": indigenous,
            "visible_minority": p_visible_minority,
            "cultural_background": p_cultural_bg,
            "languages_spoken": lang,
            "housing": housing,
            "political_leaning": random.choice(["Left", "Centre-left", "Centre", "Centre-right", "Right"]),
            "religion": p_religion,
            "commute_mode": random.choice(["Car", "Public transit", "Walk", "Bicycle", "Work from home"]),
            "top_concerns": random.sample(
                ["Cost of living", "Healthcare", "Housing", "Climate change", "Jobs",
                 "Immigration", "Education", "Taxes", "Crime", "Indigenous rights"],
                k=random.randint(2, 4),
            ),
            "source": "generated",
            "domain_context": domain_context or "",
            "audience_tags": [],
            "extended_attributes": {},
        }
        generated.append(persona)

    # Auto-persist to DB so the agent doesn't need a separate persist_personas call
    if generated:
        conn = sqlite3.connect(str(DB_PATH))
        saved = 0
        for p in generated:
            pid = p.get("uuid") or p.get("id", "")
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
                        pid, p.get("name", ""), p.get("age", 0), p.get("sex", ""),
                        p.get("province", ""),
                        p.get("planning_area", p.get("city", "")),
                        p.get("occupation", ""),
                        p.get("education_level", ""),
                        p.get("income_bracket"),
                        p.get("estimated_annual_income"),
                        p.get("income_source"),
                        p.get("marital_status", ""),
                        p.get("immigration_status", ""),
                        p.get("indigenous_identity", ""),
                        p.get("visible_minority", ""),
                        p.get("cultural_background", ""),
                        p.get("languages_spoken", ""),
                        p.get("housing", ""),
                        p.get("political_leaning"),
                        p.get("religion"),
                        p.get("commute_mode"),
                        json.dumps(p.get("top_concerns", [])),
                        p.get("source", "generated"),
                        json.dumps(p.get("audience_tags", [])),
                        p.get("domain_context", ""),
                        json.dumps(p),
                    ),
                )
                saved += 1
            except Exception as e:
                print(f"[panel_engine] Failed to save {pid}: {e}")
        conn.commit()
        conn.close()
        print(f"[panel_engine] Auto-persisted {saved}/{len(generated)} generated personas")

    return generated


@tool
def persist_personas(personas: list[dict]) -> dict:
    """Save newly generated personas to the SQLite database for future reuse.

    Args:
        personas: List of persona dicts to save

    Returns:
        dict with count of saved personas
    """
    conn = sqlite3.connect(str(DB_PATH))
    saved = 0

    for p in personas:
        pid = p.get("uuid") or p.get("id", "")
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
                    pid, p.get("name", ""), p.get("age", 0), p.get("sex", ""),
                    p.get("province", ""),
                    p.get("planning_area", p.get("city", "")),
                    p.get("occupation", ""),
                    p.get("education_level", ""),
                    p.get("income_bracket"),
                    p.get("estimated_annual_income"),
                    p.get("income_source"),
                    p.get("marital_status", ""),
                    p.get("immigration_status", ""),
                    p.get("indigenous_identity", ""),
                    p.get("visible_minority", ""),
                    p.get("cultural_background", ""),
                    p.get("languages_spoken", ""),
                    p.get("housing", ""),
                    p.get("political_leaning"),
                    p.get("religion"),
                    p.get("commute_mode"),
                    json.dumps(p.get("top_concerns", [])),
                    p.get("source", "generated"),
                    json.dumps(p.get("audience_tags", [])),
                    p.get("domain_context", ""),
                    json.dumps(p),
                ),
            )
            saved += 1
        except Exception as e:
            print(f"[panel_engine] Failed to save {pid}: {e}")

    conn.commit()
    conn.close()
    return {"saved": saved, "message": f"Persisted {saved} personas to DB"}


@tool
def fetch_data(
    source: str,
    query: str | None = None,
    province: str | None = None,
) -> dict:
    """Fetch data from pre-indexed Canadian data sources.

    Available sources:
    - "census_demographics" — age, province, education, occupation distributions
    - "jobbank_wages" — income by occupation and province
    - "ces_political" — political leaning by province/age

    Args:
        source: Source identifier
        query: Optional query to narrow results
        province: Optional province filter

    Returns:
        dict with source data
    """
    try:
        from canada_demographics_2021 import (
            PROVINCE_TERRITORY_WEIGHTS, ADULT_AGE_WEIGHTS,
            EDUCATION_WEIGHTS_25_64, OCCUPATION_WEIGHTS,
        )
    except ImportError:
        return {"error": "Could not import demographics module"}

    loaders = {
        "census_demographics": lambda: {
            "province_weights": PROVINCE_TERRITORY_WEIGHTS,
            "age_weights": ADULT_AGE_WEIGHTS,
            "education_weights": EDUCATION_WEIGHTS_25_64,
            "occupation_weights": OCCUPATION_WEIGHTS,
        },
    }

    if source not in loaders:
        return {"error": f"Unknown source: {source}. Available: {list(loaders.keys())}"}

    return {"source": source, "data": loaders[source]()}


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PANEL-BUILDING AGENT                                           ║
# ╚══════════════════════════════════════════════════════════════════╝

PANEL_AGENT_SYSTEM = """You are the MaplePulse Panel Builder — an agent that assembles
the optimal focus group panel for a given target audience.

## Your workflow:

1. UNDERSTAND the audience brief — demographics, psychographics, domain context.
   Infer implicit requirements:
   - If the brief is about buying condos, personas need sufficient income ($60K+).
   - If about luxury goods, filter for higher income. Budget products, include lower.
   - If the content is technical (AI, software, engineering), prioritize personas
     with relevant occupations (tech, IT, engineering, science, management) and
     higher education. A carpenter is not a realistic audience for an AI conference talk.
   - If the content is about healthcare, prioritize healthcare professionals.
   - If the content is educational (conference talks, courses, workshops, seminars),
     ALWAYS include 2-3 students (university, graduate, or co-op students).
     Students are a core audience for educational content. Use occupation_keywords
     like ["student", "software", "engineer", "data"] to get a mix.
   - Always think: "Would this person realistically be in this audience?"

2. SEARCH FIRST — always call search_personas before generating.
   Use occupation_keywords to filter by relevant job types when the content implies
   a specific professional audience. Use income_min/income_max when the brief
   implies a purchase or financial commitment.

3. ASSESS COVERAGE — if existing personas cover 80%+ of the spec, use them.

4. GENERATE to fill gaps — use generate_personas only for what's missing.
   Never generate more than 15 personas per query.
   Generated personas are automatically saved to the DB — no separate persist step needed.
   When generating for a technical/professional audience, specify occupation_keywords
   so the generated personas have relevant job titles.

5. COMPOSE the final panel — aim for the requested panel size.
   Review each persona: does their occupation and background make them a realistic
   member of the target audience for this specific content? Remove any that don't fit.

## Rules:
- Never generate personas that already exist in the DB
- The panel should have demographic diversity within the target spec
- Maximum 15 new personas per query — cost control
- For purchase-related briefs, ensure all panelists have realistic income for the product
- For technical/professional content, ensure panelists have relevant occupations
- After composing, output the word PANEL_COMPLETE followed by a JSON array of
  the persona UUIDs you selected for the final panel.
"""

AGENT_TOOLS = [
    search_personas,
    generate_personas,
    fetch_data,
]


def build_panel_agent(model_name: str | None = None, api_key: str | None = None):
    """Create the panel-building ReAct agent."""
    model_name = model_name or os.environ.get("PANEL_AGENT_MODEL", "openai/gpt-5.4-mini")
    model = ChatOpenAI(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0.3,
    )
    return create_react_agent(
        model=model,
        tools=AGENT_TOOLS,
        prompt=PANEL_AGENT_SYSTEM,
    )


# ── Deterministic Panel Builder (no LLM, no tool calls) ─────────

def _build_panel_deterministic(
    audience_spec: AudienceSpec,
    content: str,
    panel_size: int = 12,
    use_case: str = "localization",
) -> list[dict]:
    """Build a panel using structured AudienceSpec — zero LLM tokens.

    Replaces the ReAct agent for most cases. The parsed AudienceSpec already
    contains all the filters we need (age, province, income, occupation, etc.).

    Cultural background is resolved from:
      1. AudienceSpec.cultural_background (LLM-parsed)
      2. Fallback: _infer_cultural_from_brief() holiday keyword matching
    """
    # Resolve cultural background — LLM-parsed field, or holiday keyword fallback
    # Always compute holiday inference so we can fall back to it if LLM values don't match DB
    holiday_inferred: dict = {}
    if audience_spec.raw_brief:
        holiday_inferred = _infer_cultural_from_brief(audience_spec)

    cultural_bg = audience_spec.cultural_background
    # Normalize: move religion-like values from cultural_background to religion
    # (LLMs sometimes put "Jewish", "Muslim", "Hindu" in cultural_background)
    _RELIGION_NAMES = {"jewish", "muslim", "hindu", "sikh", "buddhist", "christian", "catholic", "protestant"}
    if cultural_bg:
        religions_found = [v for v in cultural_bg if v.lower() in _RELIGION_NAMES]
        if religions_found:
            cultural_bg = [v for v in cultural_bg if v.lower() not in _RELIGION_NAMES] or None
            if not audience_spec.religion:
                audience_spec.religion = religions_found
                print(f"[deterministic] Moved {religions_found} from cultural_background to religion")

    holiday_cb = holiday_inferred.get("cultural_background")
    if not cultural_bg and holiday_cb:
        cultural_bg = holiday_cb
        print(f"[deterministic] Holiday fallback inferred cultural_background={cultural_bg}")
    elif cultural_bg and holiday_cb:
        # If holiday map has MORE SPECIFIC values than LLM (e.g. LLM said "South Asian"
        # but holiday map says "Telugu" for Ugadi), prefer the holiday-specific values.
        # "Broad" = VM group keys like "South Asian", "Chinese", "Black"
        llm_has_broad = any(v in _CULTURAL_BACKGROUND_BY_VM for v in cultural_bg)
        holiday_is_specific = any(v not in _CULTURAL_BACKGROUND_BY_VM for v in holiday_cb)
        if llm_has_broad and holiday_is_specific:
            print(f"[deterministic] Holiday map more specific: {holiday_cb} beats LLM {cultural_bg}")
            cultural_bg = holiday_cb

    # Religion can also come from holiday inference (e.g. Diwali → Hindu/Sikh)
    religion = audience_spec.religion
    if not religion and holiday_inferred.get("religion"):
        religion = holiday_inferred["religion"]
        print(f"[deterministic] Holiday fallback inferred religion={religion}")

    # Life event inference — fill gaps in AudienceSpec from brief keywords
    life_event = _infer_life_event_from_brief(audience_spec.raw_brief) if audience_spec.raw_brief else {}
    if life_event:
        print(f"[deterministic] Life event inferred: {life_event}")
        if not audience_spec.age_range and ("age_min" in life_event or "age_max" in life_event):
            audience_spec.age_range = IntRange(
                min=life_event.get("age_min", 18),
                max=life_event.get("age_max", 85),
            )
            print(f"[deterministic] Applied life event age range: {audience_spec.age_range}")
        if not audience_spec.income_range and "income_min" in life_event:
            audience_spec.income_range = IntRange(
                min=life_event["income_min"],
                max=life_event.get("income_max", 250000),
            )
            print(f"[deterministic] Applied life event income range: {audience_spec.income_range}")
        if not audience_spec.sex and "sex" in life_event:
            audience_spec.sex = life_event["sex"]
        if not audience_spec.occupation_keywords and "occupation_keywords" in life_event:
            audience_spec.occupation_keywords = life_event["occupation_keywords"]

    # Step 1: Search existing personas
    search_kwargs: dict = {"limit": panel_size * 3}  # fetch extra for diversity sampling

    if audience_spec.provinces:
        search_kwargs["province"] = audience_spec.provinces
    if audience_spec.age_range:
        search_kwargs["age_min"] = audience_spec.age_range.min
        search_kwargs["age_max"] = audience_spec.age_range.max
    if audience_spec.sex:
        search_kwargs["sex"] = audience_spec.sex
    if audience_spec.income_range:
        search_kwargs["income_min"] = audience_spec.income_range.min
        search_kwargs["income_max"] = audience_spec.income_range.max
    if audience_spec.education:
        search_kwargs["education"] = audience_spec.education
    if religion:
        search_kwargs["religion"] = religion
    if audience_spec.occupation_keywords:
        search_kwargs["occupation_keywords"] = audience_spec.occupation_keywords
    if cultural_bg:
        search_kwargs["cultural_background"] = cultural_bg

    result = search_personas.invoke(search_kwargs)
    existing = result.get("personas", []) if isinstance(result, dict) else []
    print(f"[deterministic] Search found {len(existing)} matching personas")

    # If cultural filter was too restrictive (0 results), try holiday-inferred
    # values first, then fall back to no cultural filter
    if len(existing) == 0 and cultural_bg:
        # If LLM-parsed values failed but we have holiday-inferred values, try those
        holiday_cb = holiday_inferred.get("cultural_background")
        if holiday_cb and holiday_cb != cultural_bg:
            print(f"[deterministic] LLM cultural_bg={cultural_bg} returned 0, trying holiday fallback={holiday_cb}")
            cultural_bg = holiday_cb
            search_kwargs["cultural_background"] = cultural_bg
            result = search_personas.invoke(search_kwargs)
            existing = result.get("personas", []) if isinstance(result, dict) else []
            print(f"[deterministic] Holiday fallback search found {len(existing)} matching personas")

        if len(existing) == 0:
            print(f"[deterministic] No matches with cultural_background={cultural_bg}, retrying without it")
            relaxed_kwargs = {k: v for k, v in search_kwargs.items() if k != "cultural_background"}
            result = search_personas.invoke(relaxed_kwargs)
            existing = result.get("personas", []) if isinstance(result, dict) else []
            print(f"[deterministic] Relaxed search found {len(existing)} matching personas")
            # Cap relaxed results — reserve most slots for culturally-targeted generation
            max_relaxed = max(2, panel_size // 4)
            existing = existing[:max_relaxed]
            print(f"[deterministic] Capped relaxed results to {len(existing)} — reserving slots for culturally-targeted generation")

    # Step 2: If not enough, generate the gap
    panel = existing[:panel_size]
    gap = panel_size - len(panel)

    if gap > 0:
        gen_kwargs: dict = {"count": min(gap, 15)}
        if audience_spec.provinces:
            gen_kwargs["province"] = audience_spec.provinces
        if audience_spec.age_range:
            gen_kwargs["age_min"] = audience_spec.age_range.min
            gen_kwargs["age_max"] = audience_spec.age_range.max
        if audience_spec.sex:
            gen_kwargs["sex"] = audience_spec.sex
        if audience_spec.income_range:
            gen_kwargs["income_min"] = audience_spec.income_range.min
            gen_kwargs["income_max"] = audience_spec.income_range.max
        if audience_spec.occupation_keywords:
            gen_kwargs["occupation_keywords"] = audience_spec.occupation_keywords
        if religion:
            gen_kwargs["religion"] = religion
        if cultural_bg:
            gen_kwargs["cultural_background"] = cultural_bg
        gen_kwargs["domain_context"] = audience_spec.domain or content[:100] or use_case

        generated = generate_personas.invoke(gen_kwargs)
        if isinstance(generated, list):
            panel.extend(generated[:gap])
            print(f"[deterministic] Generated {len(generated)} personas to fill gap")

    # Step 3: Diversity sampling — if we have more than panel_size, sample diversely
    if len(panel) > panel_size:
        # Prefer diverse provinces and occupations
        panel = random.sample(panel, panel_size)

    print(f"[deterministic] Final panel: {len(panel)} personas")
    return panel


def _get_orchestrator(api_key: str | None = None) -> ChatOpenAI:
    """Create the orchestrator LLM for brief parsing and context projection."""
    import os
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("PANEL_ORCHESTRATOR_MODEL", "openai/gpt-5.4-mini")
    return ChatOpenAI(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0.2,
    )


async def run_panel_agent_phases(
    audience_brief: str,
    content: str,
    panel_size: int = 12,
    use_case: str = "localization",
    api_key: str | None = None,
    callbacks: list | None = None,
    metadata: dict | None = None,
):
    """Generator that yields (phase_name, data) tuples as each phase completes.

    Phases yielded:
      ("audience_spec", AudienceSpec dict)
      ("context_projection", ContextProjection dict)
      ("panel", list of persona dicts)
      ("panel_metadata", dict)
      ("agent_log", list of message dicts)
    """
    import os
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    config: dict | None = None
    if callbacks or metadata:
        config = {}
        if callbacks:
            config["callbacks"] = callbacks
        if metadata:
            config["metadata"] = metadata

    orchestrator = _get_orchestrator(api_key)

    # Phase 1: Parse audience brief
    print("[panel_agent] Phase 1: Parsing audience brief...")
    phase1_config = {**(config or {}), "run_name": "parse_audience_brief"}
    audience_spec = parse_audience_brief(audience_brief, orchestrator, config=phase1_config)
    print(f"[panel_agent] Parsed: {audience_spec.model_dump()}")
    yield ("audience_spec", audience_spec.model_dump())

    # Phase 2: Context projection
    print("[panel_agent] Phase 2: Context projection...")
    phase2_config = {**(config or {}), "run_name": "context_projection"}
    projection = determine_relevant_attributes(
        use_case=use_case,
        audience_brief=audience_brief,
        content=content,
        model=orchestrator,
        config=phase2_config,
    )
    print(f"[panel_agent] Projected groups: {projection.relevant_groups}")
    yield ("context_projection", projection.model_dump())

    # Phase 3: Build panel — fresh random draw each time (no panel cache)
    # Audience spec + context projection are cached (deterministic LLM),
    # but panel selection uses ORDER BY RANDOM() for variety across runs.
    panel_method = "unknown"

    # Use deterministic builder (zero LLM tokens) — the parsed AudienceSpec
    # already has all the structured filters we need.
    # Auto-escalate to agent when identity/cultural context is relevant but
    # the deterministic builder has no structured filters to handle it.
    use_agent = os.environ.get("PANEL_USE_AGENT", "false").lower() == "true"

    if not use_agent and "identity" in projection.relevant_groups:
        # Check if we have enough structured data for identity-sensitive briefs
        has_cultural = bool(audience_spec.cultural_background)
        has_religion = bool(audience_spec.religion)
        has_holiday_match = bool(_infer_cultural_from_brief(audience_spec))
        if not has_cultural and not has_religion and not has_holiday_match:
            print("[panel_agent] Auto-escalating to agent: identity group relevant but no structured cultural/religion filters")
            use_agent = True

    if not use_agent:
        print("[panel_agent] Phase 3: Deterministic panel build (no LLM)...")
        panel = _build_panel_deterministic(
            audience_spec=audience_spec,
            content=content,
            panel_size=panel_size,
            use_case=use_case,
        )
        panel_method = "deterministic"
    else:
        print("[panel_agent] Phase 3: Running panel-building agent (LLM)...")
        agent = build_panel_agent(api_key=api_key)
        agent_config = {**(config or {}), "run_name": "panel_builder_agent"}
        spec_lines = []
        if audience_spec.age_range:
            spec_lines.append(f"Age: {audience_spec.age_range.min}-{audience_spec.age_range.max}")
        if audience_spec.provinces:
            spec_lines.append(f"Provinces: {', '.join(audience_spec.provinces)}")
        if audience_spec.income_range:
            spec_lines.append(f"Income range: ${audience_spec.income_range.min:,}-${audience_spec.income_range.max:,}/year")
        if audience_spec.sex:
            spec_lines.append(f"Sex: {audience_spec.sex}")
        if audience_spec.education:
            spec_lines.append(f"Education: {', '.join(audience_spec.education)}")
        if audience_spec.occupation_keywords:
            spec_lines.append(f"Occupation keywords: {', '.join(audience_spec.occupation_keywords)}")
        if audience_spec.religion:
            spec_lines.append(f"Religion: {', '.join(audience_spec.religion)}")
        if audience_spec.cultural_background:
            spec_lines.append(f"Cultural background: {', '.join(audience_spec.cultural_background)}")
        if audience_spec.purchase_context:
            spec_lines.append(f"Purchase context: {audience_spec.purchase_context}")
        if audience_spec.domain:
            spec_lines.append(f"Domain: {audience_spec.domain}")
        parsed_spec = "\n".join(spec_lines) if spec_lines else "No structured filters extracted"

        result = await agent.ainvoke({
            "messages": [
                HumanMessage(content=f"""Build a focus group panel of {panel_size} personas
for this target audience:

{audience_brief}

Parsed audience spec:
{parsed_spec}

Content they'll evaluate: {content[:200]}...
Use case: {use_case}

Relevant attribute groups: {projection.relevant_groups}
Extended attributes to populate: {projection.relevant_extended_keys}
Reasoning: {projection.reasoning}

Search the DB first (use income_min/income_max if the brief involves a purchase),
then generate to fill gaps.""")
            ]
        }, config=agent_config)
        print(f"[panel_agent] Agent completed with {len(result.get('messages', []))} messages")

        panel = _extract_panel_from_messages(result.get("messages", []))
        print(f"[panel_agent] Extracted {len(panel)} personas from agent messages")

        if len(panel) > panel_size:
            panel = random.sample(panel, panel_size)
        panel_method = "agent"

    yield ("panel", panel)

    yield ("panel_metadata", {
        "total_in_panel": len(panel),
        "from_existing_db": sum(1 for p in panel if p.get("source") == "seed"),
        "newly_generated": sum(1 for p in panel if p.get("source") == "generated"),
        "audience_brief": audience_brief,
        "relevant_groups": projection.relevant_groups,
        "panel_method": panel_method,
    })

    if panel_method == "agent":
        yield ("agent_log", [
            {"role": getattr(m, "type", "unknown"), "content": getattr(m, "content", str(m))[:500]}
            for m in result.get("messages", [])[-10:]
        ])
    else:
        yield ("agent_log", [{"role": "system", "content": f"Panel built via {panel_method}"}])


def _extract_panel_from_messages(messages: list) -> list[dict]:
    """Extract persona lists from tool call results in agent messages."""
    personas = []
    seen_ids = set()

    def _add_personas(data):
        """Add personas from a parsed data structure."""
        if isinstance(data, dict):
            if "personas" in data:
                for p in data["personas"]:
                    if isinstance(p, dict):
                        pid = p.get("uuid") or p.get("id", "")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            personas.append(p)
            elif "uuid" in data or "id" in data:
                # Single persona dict
                pid = data.get("uuid") or data.get("id", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    personas.append(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    pid = item.get("uuid") or item.get("id", "")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        personas.append(item)

    for msg in messages:
        msg_type = getattr(msg, "type", type(msg).__name__)
        content = getattr(msg, "content", "")

        print(f"[_extract] msg type={msg_type}, content type={type(content).__name__}, preview={str(content)[:200]}")

        # Handle content that's already a Python object (dict/list)
        if isinstance(content, (dict, list)):
            _add_personas(content)
            continue

        # Handle JSON strings
        if isinstance(content, str) and content.strip():
            stripped = content.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    data = json.loads(stripped)
                    _add_personas(data)
                except (json.JSONDecodeError, TypeError):
                    pass

    print(f"[_extract] Total personas extracted: {len(personas)}")
    return personas
