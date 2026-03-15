"""MaplePulse — Focus Group Test 1: Product Concept (SnowShare)
Run inside Docker with: python /project/experiments/run_test1.py
"""
import os, json, random, time, asyncio
from pydantic import BaseModel, Field
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler as LangfuseHandler
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# --- Init ---
lf = Langfuse()
print("Langfuse ready")

DEFAULT_MODEL = "google/gemini-3-flash-preview"


def build_model(model_name=DEFAULT_MODEL, temperature=0.7):
    return ChatOpenAI(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=temperature,
    )


# --- Load personas ---
os.chdir("/project")
with open("data/personas_5000.json", "r", encoding="utf-8") as f:
    ALL_PERSONAS = json.load(f)
print(f"Loaded {len(ALL_PERSONAS):,} personas")


# --- Pydantic model ---
class PersonaReaction(BaseModel):
    sentiment: str = Field(description="One of: positive, neutral, negative, mixed")
    interest_score: int = Field(description="1-10 how interested this persona would be")
    reaction: str = Field(description="2-3 sentence reaction in first person, in character")
    concerns: list[str] = Field(description="Key concerns or objections, if any")
    would_buy: bool = Field(description="Would this persona realistically purchase/use this?")


def build_persona_context(p):
    concerns = ", ".join(p.get("top_concerns", []))
    return (
        f"Age: {p['age']} | Sex: {p['sex']} | Province: {p['province']}\n"
        f"City/Region: {p['planning_area']}\n"
        f"Occupation: {p['occupation']} | Education: {p['education_level']}\n"
        f"Housing: {p['housing']}\n"
        f"Marital status: {p['marital_status']}\n"
        f"Immigration: {p['immigration_status']} | Indigenous: {p['indigenous_identity']}\n"
        f"Visible minority: {p['visible_minority']} | Background: {p['cultural_background']}\n"
        f"Languages: {p['languages_spoken']}\n"
        f"Political: {p['political_leaning']} | Religion: {p['religion']}\n"
        f"Top concerns: {concerns}\n"
        f"Commute: {p['commute_mode']}"
    )


SYSTEM_PROMPT = """You are simulating a Canadian consumer for a synthetic focus group.
You will receive a demographic profile and a product concept.
Respond AS this person — use their background, values, concerns, and life situation to inform your reaction.

Rules:
- Stay in character. A 67-year-old retiree in rural Nova Scotia reacts differently than a 25-year-old tech worker in Vancouver.
- Be realistic, not uniformly positive. Real focus groups have skeptics.
- Consider affordability relative to their likely income (infer from occupation + housing).
- Consider regional relevance (a snow tire service matters more in Winnipeg than Victoria).
- If the concept doesn't apply to this persona at all, say so honestly.
"""

CONCEPT = """SnowShare — A peer-to-peer snow removal marketplace app for Canadians.

Homeowners post snow removal jobs after a snowfall. Nearby workers (students, gig workers,
retirees) accept jobs and clear driveways/walkways within 2 hours. Payment is handled in-app.

Pricing: $25-45 per standard driveway clearing.
Available in: Major Canadian cities, launching winter 2026.
Revenue model: 15% service fee on each transaction."""

# --- Select panel ---
rng = random.Random(99)
panel = rng.sample(ALL_PERSONAS, 15)
print(f"\nPanel: {len(panel)} personas from {len(set(p['province'] for p in panel))} provinces")
for p in panel:
    print(f"  {p['age']:2d}  {p['province']:20s}  {p['occupation'][:40]}")


# --- Run focus group ---
async def run():
    # Create a Langfuse session for this focus group run
    session_id = f"focus-group-{uuid.uuid4().hex[:8]}"
    print(f"Langfuse session: {session_id}")

    model = build_model()
    structured_llm = model.with_structured_output(PersonaReaction)

    async def get_reaction(persona):
        ctx = build_persona_context(persona)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"## Your Profile\n{ctx}\n\n## Product Concept\n{CONCEPT}\n\nReact to this concept as this person."
            ),
        ]
        # Each persona gets its own trace, grouped under the session
        handler = LangfuseHandler(
            session_id=session_id,
            trace_name=f"persona-reaction",
            user_id=persona["uuid"],
            metadata={
                "test_type": "product_concept",
                "concept": "SnowShare",
                "model": DEFAULT_MODEL,
                "persona_age": persona["age"],
                "persona_province": persona["province"],
                "persona_city": persona["planning_area"],
                "persona_occupation": persona["occupation"],
            },
            tags=["focus-group", "product-concept", persona["province"]],
        )
        try:
            result = await structured_llm.ainvoke(
                messages, config={"callbacks": [handler]}
            )
            return {
                "age": persona["age"],
                "province": persona["province"],
                "city": persona["planning_area"],
                "occupation": persona["occupation"],
                **result.model_dump(),
            }
        except Exception as e:
            return {
                "age": persona["age"],
                "province": persona["province"],
                "error": str(e),
            }

    tasks = [get_reaction(p) for p in panel]
    return await asyncio.gather(*tasks)


print(f"\nRunning focus group with {DEFAULT_MODEL}...")
t0 = time.time()
results = asyncio.run(run())
elapsed = time.time() - t0

print(f"\n{'='*60}")
print(f"FOCUS GROUP RESULTS — SnowShare ({elapsed:.1f}s)")
print(f"Model: {DEFAULT_MODEL}")
print(f"{'='*60}\n")

for r in results:
    if "error" in r:
        print(f"  ERROR {r['age']} {r['province']}: {r['error'][:80]}")
        continue
    sym = {"positive": "+", "negative": "-", "neutral": "~", "mixed": "?"}.get(
        r["sentiment"], "?"
    )
    buy = "YES" if r["would_buy"] else "no"
    print(
        f"  [{sym}] {r['interest_score']:2d}/10  {r['age']:2d} {r['province']:15s} {r['occupation'][:30]:30s}  buy={buy}"
    )
    print(f'      "{r["reaction"]}"')
    if r["concerns"]:
        print(f"      Concerns: {'; '.join(r['concerns'])}")
    print()

# --- Summary ---
valid = [r for r in results if "error" not in r]
if valid:
    sentiments = {}
    for r in valid:
        sentiments[r["sentiment"]] = sentiments.get(r["sentiment"], 0) + 1
    avg_interest = sum(r["interest_score"] for r in valid) / len(valid)
    buyers = sum(1 for r in valid if r["would_buy"])

    print("=" * 60)
    print("SUMMARY")
    print(f"  Sentiment: {sentiments}")
    print(f"  Avg interest: {avg_interest:.1f}/10")
    print(f"  Would buy: {buyers}/{len(valid)} ({buyers/len(valid)*100:.0f}%)")

    # Top concerns
    all_concerns = [c for r in valid for c in r.get("concerns", [])]
    if all_concerns:
        from collections import Counter

        top = Counter(all_concerns).most_common(5)
        print(f"  Top concerns:")
        for concern, count in top:
            print(f"    {count}x  {concern}")
    print("=" * 60)

lf.flush()
print("\nLangfuse traces flushed — check dashboard!")
