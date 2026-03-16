"""Map persona occupations to NOC 2021 codes using LLM.

Reads: unique persona occupations + NOC titles from Job Bank CSV
Outputs: data/occupation_noc_mapping.json
"""
import os, json, time
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent / ".env")

# --- Load NOC titles ---
import pandas as pd

df = pd.read_csv(
    Path(__file__).parent.parent / "data/raw/jobbank_wages_2025.csv", dtype=str
)
noc_nat = df[df["prov"] == "NAT"][["NOC_CNP", "NOC_Title_eng"]].drop_duplicates()
noc_list = "\n".join(
    f"{row['NOC_CNP']}  {row['NOC_Title_eng']}" for _, row in noc_nat.iterrows()
)

# --- Load persona occupations ---
with open(
    Path(__file__).parent.parent / "data/personas_5000.json", encoding="utf-8"
) as f:
    personas = json.load(f)

unique_occs = sorted(set(p["occupation"] for p in personas))
print(f"Unique occupations to map: {len(unique_occs)}")


# --- LLM mapping ---
class NOCMapping(BaseModel):
    occupation: str = Field(description="The input occupation title")
    noc_code: str = Field(description="Best matching NOC_CNP code (e.g., NOC_11100)")
    noc_title: str = Field(description="The NOC title that was matched")
    confidence: str = Field(description="high, medium, or low")
    is_employed: bool = Field(
        description="True if this is an employed occupation, False if student/retired/unemployed"
    )

class NOCMappingBatch(BaseModel):
    mappings: list[NOCMapping]


SYSTEM_PROMPT = f"""You are mapping Canadian occupation titles to NOC 2021 codes.

Given a list of occupation titles, find the BEST matching NOC code from the reference list below.

Rules:
- Match to the most specific NOC code available
- For "Retired" personas, set is_employed=False and use the closest NOC to their likely former career (default NOC_00010 if unclear)
- For "College Student" / "University Student", set is_employed=False, use NOC_41401 (College and other vocational instructors) as placeholder
- For "Unemployed (seeking work)", set is_employed=False, use NOC_00010 as placeholder
- For "Recent Immigrant (settling in)", set is_employed=False, use NOC_00010 as placeholder
- For "Stay-at-Home Parent", set is_employed=False, use NOC_00010 as placeholder

NOC Reference List:
{noc_list}
"""

model = ChatOpenAI(
    model="openai/gpt-5-mini",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    temperature=0,
)

# Process in batches of 20
BATCH_SIZE = 20
all_mappings = []
t0 = time.time()

for i in range(0, len(unique_occs), BATCH_SIZE):
    batch = unique_occs[i : i + BATCH_SIZE]
    batch_text = "\n".join(f"- {occ}" for occ in batch)

    structured = model.with_structured_output(NOCMappingBatch)
    batch_result = structured.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Map these occupations to NOC codes:\n\n{batch_text}"
            ),
        ]
    )
    result = batch_result.mappings

    for m in result:
        all_mappings.append(m.model_dump())
        print(
            f"  {m.occupation:40s} -> {m.noc_code}  {m.noc_title[:40]:40s}  [{m.confidence}]"
        )

    print(f"  Batch {i // BATCH_SIZE + 1} done ({len(result)} mapped)")

elapsed = time.time() - t0
print(f"\nMapped {len(all_mappings)} occupations in {elapsed:.1f}s")

# Save mapping
out_path = Path(__file__).parent.parent / "data/occupation_noc_mapping.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_mappings, f, indent=2, ensure_ascii=False)

print(f"Saved to {out_path}")

# Quick stats
high = sum(1 for m in all_mappings if m["confidence"] == "high")
med = sum(1 for m in all_mappings if m["confidence"] == "medium")
low = sum(1 for m in all_mappings if m["confidence"] == "low")
employed = sum(1 for m in all_mappings if m["is_employed"])
print(f"Confidence: {high} high, {med} medium, {low} low")
print(f"Employed: {employed}/{len(all_mappings)}")
