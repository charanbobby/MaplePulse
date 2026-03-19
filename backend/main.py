"""MaplePulse Backend API — wraps the LangGraph focus group pipeline."""

import os
import json
import random
import time
import asyncio
from pathlib import Path
from typing import Literal
from collections import Counter

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler as _BaseLangfuseHandler

# ── Init ──────────────────────────────────────────────────────────────

load_dotenv(Path("/app/.env"))

app = FastAPI(title="MaplePulse API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_MODEL = "openai/gpt-5.4-nano"
OPTIMIZER_MODEL = "anthropic/claude-sonnet-4.6"
REACTION_MODELS = [
    "openai/gpt-5.4-nano",
    "openai/gpt-5.4-mini",
    "mistralai/mistral-small-2603",
    "google/gemini-3-flash-preview",
    "x-ai/grok-4.20-beta",
]

# ── Langfuse ──────────────────────────────────────────────────────────

lf = Langfuse()


class OpenRouterLangfuseHandler(_BaseLangfuseHandler):
    """Extends Langfuse handler to report OpenRouter cost to traces."""

    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        # Grab the observation ref before parent detaches it
        observation = self._runs.get(run_id)

        # Extract cost from OpenRouter's response metadata
        cost = None
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage") or {}
            cost = token_usage.get("cost")

        # Let parent do the normal processing (detach, update usage/model, end)
        super().on_llm_end(response, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

        # After parent has ended the observation, update with cost if available
        if cost is not None and observation is not None:
            try:
                observation.update(cost=cost)
            except Exception:
                pass  # observation already ended, cost update is best-effort


def make_langfuse_handler() -> OpenRouterLangfuseHandler:
    return OpenRouterLangfuseHandler()

# ── Persona Pool ──────────────────────────────────────────────────────

PERSONAS_PATH = Path("/app/data/personas_5000.json")
ALL_PERSONAS = []

def load_personas():
    global ALL_PERSONAS
    with open(PERSONAS_PATH, "r", encoding="utf-8") as f:
        ALL_PERSONAS = json.load(f)
    print(f"Loaded {len(ALL_PERSONAS):,} personas")

load_personas()

class PanelFilter(BaseModel):
    """All available filters for selecting a focus group panel."""
    province: list[str] | None = Field(None, description="Filter by one or more provinces/territories")
    age_range: tuple[int, int] | None = Field(None, description="Min and max age inclusive, e.g. [25, 44]")
    sex: list[str] | None = Field(None, description="Filter by sex, e.g. ['Female']")
    income_bracket: list[str] | None = Field(None, description="Filter by income brackets")
    education_level: list[str] | None = Field(None, description="Filter by education levels")
    marital_status: list[str] | None = Field(None, description="Filter by marital status")
    immigration_status: list[str] | None = Field(None, description="Filter by immigration status")
    indigenous_identity: list[str] | None = Field(None, description="Filter by indigenous identity")
    visible_minority: list[str] | None = Field(None, description="Filter by visible minority status")
    political_leaning: list[str] | None = Field(None, description="Filter by political leaning")
    religion: list[str] | None = Field(None, description="Filter by religion")
    commute_mode: list[str] | None = Field(None, description="Filter by commute mode")
    housing_type: list[str] | None = Field(None, description="Filter by housing tenure (Owner/Renter)")
    languages: list[str] | None = Field(None, description="Include personas who speak any of these languages")
    top_concerns: list[str] | None = Field(None, description="Include personas with any of these concerns")

class FocusGroupRequest(BaseModel):
    message: str
    panel_size: int = 12
    filters: PanelFilter = Field(default_factory=PanelFilter)
    seed: int | None = None

def select_panel(
    n: int = 12,
    filters: PanelFilter | None = None,
    seed: int | None = None,
) -> list[dict]:
    pool = ALL_PERSONAS

    if filters:
        if filters.province:
            pool = [p for p in pool if p["province"] in filters.province]
        if filters.age_range:
            lo, hi = filters.age_range
            pool = [p for p in pool if lo <= p["age"] <= hi]
        if filters.sex:
            pool = [p for p in pool if p["sex"] in filters.sex]
        if filters.income_bracket:
            pool = [p for p in pool if p.get("income_bracket") in filters.income_bracket]
        if filters.education_level:
            pool = [p for p in pool if p["education_level"] in filters.education_level]
        if filters.marital_status:
            pool = [p for p in pool if p["marital_status"] in filters.marital_status]
        if filters.immigration_status:
            pool = [p for p in pool if p["immigration_status"] in filters.immigration_status]
        if filters.indigenous_identity:
            pool = [p for p in pool if p["indigenous_identity"] in filters.indigenous_identity]
        if filters.visible_minority:
            pool = [p for p in pool if p["visible_minority"] in filters.visible_minority]
        if filters.political_leaning:
            pool = [p for p in pool if p.get("political_leaning") in filters.political_leaning]
        if filters.religion:
            pool = [p for p in pool if p.get("religion") in filters.religion]
        if filters.commute_mode:
            pool = [p for p in pool if p.get("commute_mode") in filters.commute_mode]
        if filters.housing_type:
            pool = [p for p in pool if any(ht in p.get("housing", "") for ht in filters.housing_type)]
        if filters.languages:
            lang_set = set(filters.languages)
            pool = [p for p in pool if lang_set & set(l.strip() for l in p["languages_spoken"].split(","))]
        if filters.top_concerns:
            concern_set = set(filters.top_concerns)
            pool = [p for p in pool if concern_set & set(p.get("top_concerns", []))]

    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))

def build_persona_context(persona: dict) -> str:
    concerns = ", ".join(persona.get("top_concerns", []))
    income = persona.get("estimated_annual_income")
    income_str = f"${income:,}/yr ({persona.get('income_bracket', 'Unknown')})" if income else persona.get("income_bracket", "Unknown")
    return (
        f"Age: {persona['age']} | Sex: {persona['sex']} | Province: {persona['province']}\n"
        f"City/Region: {persona['planning_area']}\n"
        f"Occupation: {persona['occupation']} | Education: {persona['education_level']}\n"
        f"Income: {income_str}\n"
        f"Housing: {persona['housing']}\n"
        f"Marital status: {persona['marital_status']}\n"
        f"Immigration: {persona['immigration_status']} | Indigenous: {persona['indigenous_identity']}\n"
        f"Visible minority: {persona['visible_minority']} | Cultural background: {persona['cultural_background']}\n"
        f"Languages: {persona['languages_spoken']}\n"
        f"Political leaning: {persona['political_leaning']} | Religion: {persona['religion']}\n"
        f"Top concerns: {concerns}\n"
        f"Commute: {persona['commute_mode']}"
    )

# ── LLM ───────────────────────────────────────────────────────────────

def build_model(model_name: str = DEFAULT_MODEL, temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=temperature,
        extra_body={"provider": {"allow_fallbacks": False}},
        default_headers={"HTTP-Referer": "https://maplepulse.app", "X-Title": "MaplePulse"},
    )

# ── Schemas ───────────────────────────────────────────────────────────

class LocalizationReaction(BaseModel):
    reaction: str = Field(description="Casual, informal 1-2 sentence gut reaction in character, under 50 words, like a text message")
    sentiment_score: int = Field(description="1-10 overall sentiment. 1=very negative, 5=neutral, 10=very positive")
    resonates: bool = Field(description="Does this message feel relevant to their life?")
    tone_fit: Literal["perfect", "acceptable", "off", "offensive"]
    cultural_flags: list[str] = Field(description="Anything culturally tone-deaf or regionally irrelevant, empty list if none")

class OptimizedMessageSchema(BaseModel):
    improved_message: str = Field(description="The rewritten marketing message")
    changes_made: list[str] = Field(description="List of specific changes and why")

class IntentClassification(BaseModel):
    use_case: Literal["product_concept", "ab_copy_test", "survey_pretest", "localization"] = Field(description="The detected use case type")
    confidence: float = Field(description="Confidence 0.0-1.0")
    reasoning: str = Field(description="Brief explanation")

# ── Prompts ───────────────────────────────────────────────────────────

LOCALIZATION_SYSTEM_PROMPT = """Respond as a typical Canadian consumer encountering the specific international marketing message provided in the \
user input. Share your authentic gut reaction based only on your own lived experience—not analysis or stepwise reasoning. Reply directly to the \
message given, ignoring anything unrelated (do NOT discuss jobs, localization, or countries unless it's in the marketing message itself).

Act casual and natural, using informal language, short forms, and include a few mild spelling mistakes or typos as if texting or chatting. Do not \
use emdashes (—) or formal wording. Stay under 50 words, in a single "messy" paragraph.

If the message doesn't feel "Canadian" or something seems off, react in your own words—not as a review or detailed critique, but briefly mention \
what feels strange or misses the mark to you personally.

Never reference background marketing strategies, statistics, or localization efforts. Always respond just to what's actually in the provided \
marketing message.

# Output Format

Provide one short paragraph (max 50 to 80 words), styled as an informal, slightly imperfect text message from a Canadian consumer. No lists, no emdashes, \
and no off-topic commentary. Only respond to the actual marketing message shown in the user input.

# Example

**User Input:**
"Why Genuine Egyptian Cotton Matters
At Silk & Snow, we strictly use 100% Egyptian Cotton, which has been certified by the Cotton Egypt Association. The Egyptian Cotton Association \
ensures the rigorous standards for quality, durability, and softness that we expect from genuine Egyptian Cotton."

**Persona Response Example:**
"Uh ok sounds fancy an all but dunno if that rlly means much to me here. Like I never rlly cared where cotton's from y'know? Not sure if it makes it \
more special 4 us tbh."

(Real example replies should always speak to what's actually in the message—nothing else.)

# Notes

- ONLY reply to the marketing message provided in the user input—never veer off-topic.
- Don't discuss local jobs, localization, or background details unless the ad itself mentions them.
- If something feels off or un-Canadian, say so briefly, but only as your personal, gut-level reaction.
- Always sound casual, authentic, and slightly imperfect, as if texting a friend."""

OPTIMIZE_PROMPT = """You are a Canadian marketing localization expert.

You will receive:
1. An original marketing message.
2. Verbatim reactions from a diverse panel of Canadian consumers.
3. Aggregated metadata: sentiment scores, cultural flags, and tone fit distribution.

Your job: Thoroughly analyze the panel feedback (including concerns, sentiment, and regional/cultural issues) and iteratively rewrite the \
marketing message until you are confident that all significant actionable concerns are fully addressed, keeping the core value proposition and \
authentic advertising style intact.

Continue the process internally (analyzing, reasoning, diagnosing, rewriting, and iterating), but DO NOT present or mention any chain-of-thought, \
reasoning steps, diagnosis, iteration notes, or feedback analysis in your output. **Only output your final, single revised ad message, \
fully ready for publication.**

**Rules:**
- Silently address the most common regional/cultural issues first (e.g., incorrect store names, references, tone, regional sensibilities).
- Update brand/term/references for regional fit or inclusivity.
- The message must still feel like an authentic ad, not a "committee draft".
- Keep the message roughly the same length and energy.
- Do not over-correct, and do not make the ad sound excessively corporate or "focus-grouped".
- No disclaimers or legalese.
- Ignore all French-language, French text, and bilingual conventions; only focus on the English message."""

CLASSIFICATION_PROMPT = """You are an intent classifier for MaplePulse, a synthetic focus group service.

Given a user's input, classify it into exactly ONE of these use cases:

1. **product_concept** — The user is describing a product, service, or business idea and wants reactions.
   Signals: describes features, pricing, target market, value proposition, "what do you think of..."

2. **ab_copy_test** — The user is presenting 2+ versions of text (ad copy, taglines, headlines) to compare.
   Signals: "Version A / Version B", "which is better", two distinct text blocks, "A/B test"

3. **survey_pretest** — The user is pasting a draft survey question to test for clarity and bias.
   Signals: "on a scale of...", "how likely...", "rate the following", question marks, survey language

4. **localization** — The user has a single marketing message and wants to know how it lands across regions.
   Signals: one short message/tagline, "how does this sound", ad copy without comparison, single message

If truly ambiguous, default to product_concept."""

# ── API Models ────────────────────────────────────────────────────────

# ── Core Pipeline (streaming via SSE) ────────────────────────────────

@app.post("/api/focus-group")
async def run_focus_group(req: FocusGroupRequest):
    """Run the full focus group pipeline, streaming results as Server-Sent Events."""

    async def event_stream():
        seed = req.seed if req.seed is not None else random.randint(1, 99999)

        # Langfuse trace (v4 API) — create trace ID, then start observation
        with lf.start_as_current_observation(
            name="focus-group-api",
            metadata={"pipeline": "v1_api", "panel_size": req.panel_size},
        ) as _span:
            trace_id = lf.get_current_trace_id()
            langfuse_handler = make_langfuse_handler()
            config: RunnableConfig = {"callbacks": [langfuse_handler]}

            # ── Step 1: Classify ──
            yield _sse("step", {"step": "classify", "status": "started"})
            t0 = time.time()

            classifier = build_model(temperature=0).with_structured_output(IntentClassification)
            classification = classifier.invoke(
                [
                    SystemMessage(content=CLASSIFICATION_PROMPT),
                    HumanMessage(content=f"Classify this user input:\n\n{req.message}"),
                ],
                config=config,
            )
            yield _sse("classify", {
                "use_case": classification.use_case,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
                "elapsed": round(time.time() - t0, 2),
            })

            # ── Step 2: Select Panel ──
            yield _sse("step", {"step": "panel_selection", "status": "started"})
            panel = select_panel(
                n=req.panel_size,
                filters=req.filters,
                seed=seed,
            )
            # Send full panel data
            panel_data = []
            for p in panel:
                panel_data.append({
                    "uuid": p["uuid"],
                    "age": p["age"],
                    "sex": p["sex"],
                    "occupation": p["occupation"],
                    "education_level": p["education_level"],
                    "marital_status": p["marital_status"],
                    "planning_area": p["planning_area"],
                    "province": p["province"],
                    "immigration_status": p["immigration_status"],
                    "indigenous_identity": p["indigenous_identity"],
                    "visible_minority": p["visible_minority"],
                    "languages_spoken": p["languages_spoken"],
                    "housing": p["housing"],
                    "cultural_background": p.get("cultural_background", ""),
                    "political_leaning": p.get("political_leaning", ""),
                    "religion": p.get("religion", ""),
                    "top_concerns": p.get("top_concerns", []),
                    "commute_mode": p.get("commute_mode", ""),
                    "estimated_annual_income": p.get("estimated_annual_income", 0),
                    "income_bracket": p.get("income_bracket", "Unknown"),
                })
            yield _sse("panel", {"panel": panel_data})

            # ── Step 3: Round 1 Reactions (stream each one) ──
            yield _sse("step", {"step": "round1_responding", "status": "started"})
            t0 = time.time()

            r1_reactions = await _run_reactions_streaming(
                panel, req.message, "reaction_r1"
            )
            async for event in r1_reactions["events"]:
                yield event

            r1_results = r1_reactions["results"]
            r1_elapsed = round(time.time() - t0, 2)

            # ── Step 4: Round 1 Summary ──
            yield _sse("step", {"step": "round1_summary", "status": "started"})
            r1_agg = _aggregate(r1_results)
            yield _sse("summary_r1", {**r1_agg, "elapsed": r1_elapsed})

            # ── Step 5: Optimize ──
            yield _sse("step", {"step": "optimization", "status": "started"})
            t0 = time.time()
            optimized = await _optimize(req.message, r1_results, r1_agg, config)
            yield _sse("optimized", {
                "improved_message": optimized["improved_message"],
                "changes_made": optimized["changes_made"],
                "elapsed": round(time.time() - t0, 2),
            })

            # ── Step 6: Round 2 Reactions (stream each one) ──
            yield _sse("step", {"step": "round2_responding", "status": "started"})
            t0 = time.time()

            r2_reactions = await _run_reactions_streaming(
                panel, optimized["improved_message"], "reaction_r2"
            )
            async for event in r2_reactions["events"]:
                yield event

            r2_results = r2_reactions["results"]
            r2_elapsed = round(time.time() - t0, 2)

            # ── Step 7: Round 2 Summary ──
            yield _sse("step", {"step": "round2_summary", "status": "started"})
            r2_agg = _aggregate(r2_results)
            yield _sse("summary_r2", {**r2_agg, "elapsed": r2_elapsed})

            # ── Step 8: Final ──
            yield _sse("step", {"step": "final_comparison", "status": "started"})
            yield _sse("done", {"trace_id": trace_id})

            lf.flush()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def _run_reactions_streaming(
    panel: list[dict],
    message: str,
    event_prefix: str,
):
    """Run reactions concurrently but yield SSE events as each completes."""
    results = []
    events = []

    async def get_reaction(persona: dict, index: int) -> dict:
        # Rotate model per persona
        model_name = REACTION_MODELS[index % len(REACTION_MODELS)]
        model = build_model(model_name=model_name)
        structured_llm = model.with_structured_output(LocalizationReaction)

        # Each task gets its own Langfuse handler to avoid OpenTelemetry context conflicts
        task_handler = make_langfuse_handler()
        task_config: RunnableConfig = {"callbacks": [task_handler]}

        ctx = build_persona_context(persona)
        messages = [
            SystemMessage(content=LOCALIZATION_SYSTEM_PROMPT),
            HumanMessage(
                content=f"## Your Profile\n{ctx}\n\n## Marketing Message\n{message}\n\nHow does this message land for you?"
            ),
        ]
        try:
            result = await structured_llm.ainvoke(messages, config=task_config)
            reaction_data = result.model_dump()
            return {
                "index": index,
                "persona_id": persona["uuid"],
                "age": persona["age"],
                "sex": persona["sex"],
                "province": persona["province"],
                "city": persona["planning_area"],
                "occupation": persona["occupation"],
                "income_bracket": persona.get("income_bracket", "Unknown"),
                "cultural_background": persona.get("cultural_background", ""),
                "languages": persona["languages_spoken"],
                "reaction": reaction_data["reaction"],
                "sentiment_score": reaction_data["sentiment_score"],
                "resonates": reaction_data["resonates"],
                "tone_fit": reaction_data["tone_fit"],
                "cultural_flags": reaction_data["cultural_flags"],
                "model_used": model_name,
            }
        except Exception as e:
            return {
                "index": index,
                "persona_id": persona["uuid"],
                "error": str(e),
            }

    # Run all concurrently, collect as they finish
    tasks = [asyncio.create_task(get_reaction(p, i)) for i, p in enumerate(panel)]

    async def generate_events():
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            yield _sse(event_prefix, result)

    return {"events": generate_events(), "results": results}


def _aggregate(results: list[dict]) -> dict:
    """Aggregate reaction results into summary metrics."""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"avg_sentiment": 0, "resonance_pct": 0, "tone_distribution": {}, "top_cultural_flags": []}

    sentiments = [r["sentiment_score"] for r in valid]
    resonance = sum(1 for r in valid if r["resonates"])
    tone_counts = Counter(r["tone_fit"] for r in valid)
    total = len(valid)

    all_flags = [f for r in valid for f in r.get("cultural_flags", [])]
    top_flags = [f for f, _ in Counter(all_flags).most_common(5)]

    return {
        "avg_sentiment": round(sum(sentiments) / len(sentiments), 2),
        "resonance_pct": round(resonance / total * 100),
        "tone_distribution": {
            "perfect": round(tone_counts.get("perfect", 0) / total * 100),
            "acceptable": round(tone_counts.get("acceptable", 0) / total * 100),
            "off": round(tone_counts.get("off", 0) / total * 100),
            "offensive": round(tone_counts.get("offensive", 0) / total * 100),
        },
        "top_cultural_flags": top_flags,
    }


async def _optimize(
    original: str,
    r1_results: list[dict],
    r1_agg: dict,
    config: RunnableConfig,
) -> dict:
    """Optimize the message based on round 1 feedback."""
    valid = [r for r in r1_results if "error" not in r]

    reaction_lines = []
    for r in valid:
        flags = ", ".join(r.get("cultural_flags", []))
        line = f"- {r['age']}yo {r['province']} ({r['city']}): \"{r['reaction']}\""
        if flags:
            line += f" [flags: {flags}]"
        reaction_lines.append(line)

    metadata_text = (
        f"Avg sentiment: {r1_agg.get('avg_sentiment', 'N/A')}/10\n"
        f"Resonance: {r1_agg.get('resonance_pct', 'N/A')}%\n"
        f"Tone fit: {r1_agg.get('tone_distribution', {})}\n"
        f"Top cultural flags: {r1_agg.get('top_cultural_flags', [])}"
    )

    user_msg = (
        f"## Original Message\n{original}\n\n"
        f"## Panel Reactions ({len(valid)} personas)\n" + "\n".join(reaction_lines) + "\n\n"
        f"## Aggregated Metadata\n{metadata_text}\n\n"
        f"Rewrite the original message to address these concerns. Keep the same core value proposition."
    )

    # Anthropic prompt caching: cache the system prompt via content-block format
    system_content = [{"type": "text", "text": OPTIMIZE_PROMPT, "cache_control": {"type": "ephemeral"}}]
    optimizer = build_model(model_name=OPTIMIZER_MODEL, temperature=0.4).with_structured_output(OptimizedMessageSchema)
    result = await optimizer.ainvoke(
        [SystemMessage(content=system_content), HumanMessage(content=user_msg)],
        config=config,
    )

    return {"improved_message": result.improved_message, "changes_made": result.changes_made}


# ── Panel Options (filter metadata) ──────────────────────────────

@app.get("/api/panel-options")
async def panel_options():
    """Return all unique values for each filterable field, so the frontend can populate dropdowns."""
    all_concerns: set[str] = set()
    all_languages: set[str] = set()
    ages = []

    fields: dict[str, set[str]] = {
        "province": set(),
        "sex": set(),
        "income_bracket": set(),
        "education_level": set(),
        "marital_status": set(),
        "immigration_status": set(),
        "indigenous_identity": set(),
        "visible_minority": set(),
        "political_leaning": set(),
        "religion": set(),
        "commute_mode": set(),
        "housing_type": set(),
    }

    for p in ALL_PERSONAS:
        ages.append(p["age"])
        for key in fields:
            if key == "housing_type":
                housing = p.get("housing", "")
                if housing.startswith("Owner"):
                    fields["housing_type"].add("Owner")
                elif housing.startswith("Renter"):
                    fields["housing_type"].add("Renter")
            else:
                val = p.get(key, "")
                if val:
                    fields[key].add(val)
        for lang in p.get("languages_spoken", "").split(","):
            lang = lang.strip()
            if lang:
                all_languages.add(lang)
        for concern in p.get("top_concerns", []):
            all_concerns.add(concern)

    return {
        "total_personas": len(ALL_PERSONAS),
        "age_range": {"min": min(ages), "max": max(ages)} if ages else None,
        **{k: sorted(v) for k, v in fields.items()},
        "languages": sorted(all_languages),
        "top_concerns": sorted(all_concerns),
    }


@app.post("/api/panel-preview")
async def panel_preview(filters: PanelFilter = None):
    """Return the count of personas matching the given filters (no LLM calls)."""
    if filters is None:
        filters = PanelFilter()
    matched = select_panel(n=len(ALL_PERSONAS), filters=filters, seed=0)
    return {"matching_personas": len(matched), "total_personas": len(ALL_PERSONAS)}


# ── Health Check ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    try:
        lf.auth_check()
        langfuse_ok = True
    except Exception:
        langfuse_ok = False

    return {
        "status": "ok",
        "personas": len(ALL_PERSONAS),
        "model": DEFAULT_MODEL,
        "reaction_models": REACTION_MODELS,
        "langfuse": langfuse_ok,
    }
