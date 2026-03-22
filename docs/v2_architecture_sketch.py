"""MaplePulse v2 — Hierarchical Multi-Agent Architecture Sketch

High-level code showing how the orchestrator spawns stateless persona
subagents using LangGraph's Send() pattern with multi-model assignment.

This is a DESIGN SKETCH, not runnable code. It shows the framework
pattern and key decisions before full implementation.

NOTE (2026-03-21): This sketch has been SUPERSEDED by:
- backend/main.py — the actual v2 implementation (FastAPI + LangGraph)
- docs/v3_architecture_sketch.py — the v3 agentic persona engine design
  that replaces static panel filtering with dynamic tool-calling agent
"""

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, Send
from pydantic import BaseModel, Field


# ╔══════════════════════════════════════════════════════════════════╗
# ║  MULTI-MODEL POOL                                               ║
# ║  Round-robin assignment — different LLMs = different biases      ║
# ╚══════════════════════════════════════════════════════════════════╝

# 5 models × 5 providers — maximize perspective diversity
# Cost: ~$0.01-0.03 per run (20 personas × 2 rounds = 40 calls)
#
# | Model                | Input/M | Output/M | Provider  | Training origin |
# |----------------------|---------|----------|-----------|-----------------|
# | gpt-5-nano           | $0.05   | $0.40    | OpenAI    | US              |
# | deepseek-v3.2        | $0.26   | $0.38    | DeepSeek  | China           |
# | mistral-small        | $0.20   | $0.60    | Mistral   | France/EU       |
# | gemini-3-flash       | $0.50   | $3.00    | Google    | US              |
# | grok-3-mini          | $0.30   | $0.50    | xAI       | US              |

MODEL_CONFIGS = [
    {"model": "openai/gpt-5-nano",          "label": "gpt5nano",   "provider": "OpenAI"},
    {"model": "deepseek/deepseek-v3.2",     "label": "dsv3.2",     "provider": "DeepSeek"},
    {"model": "mistralai/mistral-small",    "label": "mistral-sm", "provider": "Mistral"},
    {"model": "google/gemini-3-flash",      "label": "gem3flash",  "provider": "Google"},
    {"model": "xai/grok-3-mini",           "label": "grok3mini",  "provider": "xAI"},
]

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODELS = [
    ChatOpenAI(model=cfg["model"], base_url=OPENROUTER_BASE)  # api_key from env
    for cfg in MODEL_CONFIGS
]


# ╔══════════════════════════════════════════════════════════════════╗
# ║  SCHEMAS                                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

class PersonaReaction(BaseModel):
    """Structured output from each persona subagent."""
    overall_reaction: str = Field(description="2-3 sentence gut reaction")
    sentiment_score: float = Field(description="-1.0 (hostile) to 1.0 (love it)")
    would_engage: bool = Field(description="Would this persona click/buy/share?")
    cultural_flags: list[str] = Field(description="Regional/cultural issues spotted")
    suggested_tweak: str = Field(description="One specific improvement suggestion")
    tone_fit: str = Field(description="One of: perfect | acceptable | off-putting | offensive")


class OptimizedMessage(BaseModel):
    """Output from the optimize_message node."""
    improved_message: str = Field(description="Rewritten marketing message")
    changes_made: list[str] = Field(description="List of changes and why")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  ORCHESTRATOR STATE                                             ║
# ║                                                                  ║
# ║  Key: `reactions` uses operator.add reducer so parallel          ║
# ║  subagent outputs get merged automatically by LangGraph          ║
# ╚══════════════════════════════════════════════════════════════════╝

class OrchestratorState(TypedDict):
    # Input
    user_input: str
    use_case: str                                    # localization, product_concept, etc.

    # Panel
    panel: list[dict]                                # 20 selected personas (full profiles)

    # Round 1
    reactions: Annotated[list[dict], operator.add]   # reducer: merge from parallel subagents
    summary: dict

    # Optimization
    optimized_input: str
    optimization_changes: list[str]

    # Round 2
    reactions_v2: Annotated[list[dict], operator.add]
    summary_v2: dict


# ╔══════════════════════════════════════════════════════════════════╗
# ║  ORCHESTRATOR NODES (run on main graph)                         ║
# ╚══════════════════════════════════════════════════════════════════╝

def classify_intent(state: OrchestratorState) -> dict:
    """Classify the marketer's input into a use case."""
    # LLM call to classify: localization | product_concept | ab_copy_test | survey_pretest
    ...
    return {"use_case": "localization"}


def select_panel(state: OrchestratorState) -> dict:
    """Select 20 personas from the 5,000-persona pool.

    Strategy depends on use_case:
    - localization: geographic diversity (spread across provinces)
    - product_concept: demographic diversity (age, income, urban/rural)
    - ab_copy_test: matched pairs (same demographics, different messages)
    """
    ...
    return {"panel": selected_personas}


def aggregate_results(state: OrchestratorState) -> dict:
    """Aggregate Round 1 reactions into summary with metadata."""
    reactions = state["reactions"]
    summary = {
        "avg_sentiment": sum(r["reaction"]["sentiment_score"] for r in reactions) / len(reactions),
        "engagement_rate": sum(1 for r in reactions if r["reaction"]["would_engage"]) / len(reactions),
        "cultural_flags": _collect_flags(reactions),
        "tone_distribution": _count_tones(reactions),
        "model_breakdown": _group_by_model(reactions),
    }
    return {"summary": summary}


def optimize_message(state: OrchestratorState) -> dict:
    """Use Round 1 feedback to rewrite the marketing message."""
    # Feed: original message + all reactions + summary metadata → LLM
    # Output: OptimizedMessage (improved_message + changes_made)
    ...
    return {
        "optimized_input": result.improved_message,
        "optimization_changes": result.changes_made,
    }


def aggregate_v2(state: OrchestratorState) -> dict:
    """Aggregate Round 2 + build before/after comparison."""
    # Same aggregation as Round 1, plus delta comparison
    ...
    return {"summary_v2": summary_with_comparison}


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PERSONA SUBAGENT NODE (stateless, one persona per invocation)  ║
# ║                                                                  ║
# ║  This is the KEY difference from v1:                             ║
# ║  - v1: one LLM call pretends to be a persona (shared context)   ║
# ║  - v2: each persona is an isolated Send() with its own state    ║
# ╚══════════════════════════════════════════════════════════════════╝

def build_persona_prompt(persona: dict) -> str:
    """Build the system prompt that makes the LLM embody this persona."""
    return f"""You are {persona['name']}, a {persona['age']}-year-old {persona['occupation']}
living in {persona['city']}, {persona['province']}.

Background:
- Education: {persona['education']}
- Income bracket: {persona.get('income_bracket', 'Unknown')}
- Household: {persona['household_composition']}
- Languages: {', '.join(persona['languages'])}
- Values: {', '.join(persona['top_values'])}
- Media: {', '.join(persona['media_consumption'])}
- Concerns: {', '.join(persona['key_concerns'])}

React to the marketing message AS THIS PERSON. Use your background,
values, and regional perspective to form an authentic opinion.
Do NOT be artificially positive. If this message wouldn't resonate
with someone like you, say so honestly."""


def persona_subagent(state: dict) -> dict:
    """Stateless subagent: one persona + one message → one reaction.

    Each invocation:
    1. Receives ONE persona profile + the marketing message
    2. Has NO memory of other personas (clean context)
    3. Returns structured reaction + metadata
    4. State is discarded after return (stateless)
    """
    persona = state["persona"]
    message = state["message"]
    idx = state["model_index"] % len(MODELS)
    model = MODELS[idx]
    cfg = MODEL_CONFIGS[idx]

    result = model.with_structured_output(PersonaReaction).invoke([
        SystemMessage(content=build_persona_prompt(persona)),
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


def persona_subagent_v2(state: dict) -> dict:
    """Round 2: same logic, reads optimized message instead."""
    # Identical to persona_subagent — separate node so LangGraph
    # can route Round 1 vs Round 2 outputs to different state keys
    persona = state["persona"]
    message = state["message"]
    idx = state["model_index"] % len(MODELS)
    model = MODELS[idx]
    cfg = MODEL_CONFIGS[idx]

    result = model.with_structured_output(PersonaReaction).invoke([
        SystemMessage(content=build_persona_prompt(persona)),
        HumanMessage(content=f"React to this marketing message:\n\n{message}"),
    ])

    return {
        "reactions_v2": [{
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
# ║  FAN-OUT FUNCTIONS (LangGraph Send() pattern)                    ║
# ║                                                                  ║
# ║  These return list[Send()] — LangGraph spawns each as a          ║
# ║  parallel subgraph invocation with isolated state.               ║
# ╚══════════════════════════════════════════════════════════════════╝

def spawn_subagents(state: OrchestratorState) -> list[Send]:
    """Round 1: spawn one subagent per persona with round-robin model."""
    return [
        Send("persona_subagent", {
            "persona": persona,
            "message": state["user_input"],
            "model_index": i,
        })
        for i, persona in enumerate(state["panel"])
    ]


def spawn_subagents_v2(state: OrchestratorState) -> list[Send]:
    """Round 2: same panel + model assignments, optimized message."""
    return [
        Send("persona_subagent_v2", {
            "persona": persona,
            "message": state["optimized_input"],
            "model_index": i,
        })
        for i, persona in enumerate(state["panel"])
    ]


# ╔══════════════════════════════════════════════════════════════════╗
# ║  GRAPH ASSEMBLY                                                 ║
# ║                                                                  ║
# ║  Flow:                                                           ║
# ║  START → classify → select_panel                                 ║
# ║    → [Send() x20] persona_subagent → aggregate                  ║
# ║    → optimize_message                                            ║
# ║    → [Send() x20] persona_subagent_v2 → aggregate_v2            ║
# ║    → END                                                         ║
# ╚══════════════════════════════════════════════════════════════════╝

graph = StateGraph(OrchestratorState)

# Orchestrator nodes
graph.add_node("classify_intent", classify_intent)
graph.add_node("select_panel", select_panel)
graph.add_node("aggregate", aggregate_results)
graph.add_node("optimize_message", optimize_message)
graph.add_node("aggregate_v2", aggregate_v2)

# Subagent nodes (stateless workers)
graph.add_node("persona_subagent", persona_subagent)
graph.add_node("persona_subagent_v2", persona_subagent_v2)

# Edges: orchestrator flow
graph.set_entry_point("classify_intent")
graph.add_edge("classify_intent", "select_panel")

# Fan-out: select_panel → spawn N parallel persona_subagent via Send()
graph.add_conditional_edges("select_panel", spawn_subagents, ["persona_subagent"])
# Fan-in: all persona_subagent outputs merge into `reactions` via reducer
graph.add_edge("persona_subagent", "aggregate")

graph.add_edge("aggregate", "optimize_message")

# Fan-out: optimize_message → spawn N parallel persona_subagent_v2 via Send()
graph.add_conditional_edges("optimize_message", spawn_subagents_v2, ["persona_subagent_v2"])
graph.add_edge("persona_subagent_v2", "aggregate_v2")

graph.add_edge("aggregate_v2", END)

# Compile
focus_group = graph.compile()


# ╔══════════════════════════════════════════════════════════════════╗
# ║  USAGE                                                          ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    result = focus_group.invoke({
        "user_input": "Try our new Maple Crunch cereal — the taste of home!",
    })

    print(f"Round 1 sentiment: {result['summary']['avg_sentiment']:.2f}")
    print(f"Round 2 sentiment: {result['summary_v2']['avg_sentiment']:.2f}")
    print(f"Changes made: {result['optimization_changes']}")
