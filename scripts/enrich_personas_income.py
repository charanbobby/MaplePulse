"""Step 1: Enrich 5,000 personas with income data from Job Bank 2025 wages.

Reads:
  - data/personas_5000.json
  - data/occupation_noc_mapping.json
  - data/raw/jobbank_wages_2025.csv

Outputs:
  - data/personas_5000_enriched.json (full enriched file)
  - scripts/test_enriched.json (sample of 10 for quick inspection)
"""
import json, random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent

# --- Load inputs ---
with open(ROOT / "data/personas_5000.json", encoding="utf-8") as f:
    personas = json.load(f)
print(f"Loaded {len(personas):,} personas")

with open(ROOT / "data/occupation_noc_mapping.json", encoding="utf-8") as f:
    noc_mapping_list = json.load(f)
# Build lookup: occupation -> mapping
noc_map = {m["occupation"]: m for m in noc_mapping_list}
print(f"Loaded {len(noc_map)} occupation->NOC mappings")

df_wages = pd.read_csv(ROOT / "data/raw/jobbank_wages_2025.csv", dtype=str)
print(f"Loaded {len(df_wages):,} wage rows")

# --- Province abbreviation mapping ---
PROVINCE_ABBREV = {
    "Ontario": "ON",
    "Quebec": "QC",
    "British Columbia": "BC",
    "Alberta": "AB",
    "Manitoba": "MB",
    "Saskatchewan": "SK",
    "Nova Scotia": "NS",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Prince Edward Island": "PEI",
    "Northwest Territories": "NWT",
    "Yukon": "YK",
    "Nunavut": "NU",
}

# --- Build wage lookup: (noc_code, prov_abbrev) -> wage data ---
# Use provincial-level rows (ER_Code matching province codes, not sub-regions)
# Provincial rows have ER codes like ER10, ER20, etc. (2-digit after ER)
# National rows have ER00
prov_er_codes = {
    "NL": "ER10", "PEI": "ER11", "NS": "ER12", "NB": "ER13",
    "QC": "ER24", "ON": "ER35", "MB": "ER46", "SK": "ER47",
    "AB": "ER48", "BC": "ER59", "YK": "ER60", "NWT": "ER61", "NU": "ER62",
}

def get_wage(noc_code: str, province: str) -> dict | None:
    """Look up wage data for a NOC code + province. Falls back to national."""
    prov_abbrev = PROVINCE_ABBREV.get(province, "")

    # Try province-level first
    mask = (df_wages["NOC_CNP"] == noc_code) & (df_wages["prov"] == prov_abbrev)
    # Filter to rows that have actual wage data (not sub-regions with no data)
    prov_rows = df_wages[mask].dropna(subset=["Median_Wage_Salaire_Median"])
    if not prov_rows.empty:
        row = prov_rows.iloc[0]
    else:
        # Fall back to national
        mask_nat = (df_wages["NOC_CNP"] == noc_code) & (df_wages["prov"] == "NAT")
        nat_rows = df_wages[mask_nat].dropna(subset=["Median_Wage_Salaire_Median"])
        if nat_rows.empty:
            return None
        row = nat_rows.iloc[0]

    is_annual = str(row.get("Annual_Wage_Flag_Salaire_annuel", "0")) == "1"

    def to_float(val):
        try:
            v = float(val)
            if pd.isna(v):
                return None
            return v
        except (ValueError, TypeError):
            return None

    median = to_float(row["Median_Wage_Salaire_Median"])
    low = to_float(row["Low_Wage_Salaire_Minium"])
    high = to_float(row["High_Wage_Salaire_Maximal"])
    q1 = to_float(row["Quartile1_Wage_Salaire_Quartile1"])
    q3 = to_float(row["Quartile3_Wage_Salaire_Quartile3"])

    if median is None:
        return None

    # Convert hourly to annual (assume 2,000 hours/year = 40hrs * 50 weeks)
    if not is_annual:
        median = round(median * 2000)
        low = round(low * 2000) if low else None
        high = round(high * 2000) if high else None
        q1 = round(q1 * 2000) if q1 else None
        q3 = round(q3 * 2000) if q3 else None

    return {
        "median_annual": int(median),
        "low_annual": int(low) if low else None,
        "high_annual": int(high) if high else None,
        "q1_annual": int(q1) if q1 else None,
        "q3_annual": int(q3) if q3 else None,
        "source": "jobbank_2025",
        "is_annual_original": is_annual,
    }


def assign_income_bracket(annual_income: int) -> str:
    """Assign to a bracket for segmentation."""
    if annual_income < 20000:
        return "Under $20K"
    elif annual_income < 40000:
        return "$20K-$40K"
    elif annual_income < 60000:
        return "$40K-$60K"
    elif annual_income < 80000:
        return "$60K-$80K"
    elif annual_income < 100000:
        return "$80K-$100K"
    elif annual_income < 150000:
        return "$100K-$150K"
    else:
        return "$150K+"


def estimate_persona_income(wage_data: dict, persona: dict, rng: random.Random) -> int:
    """Estimate a specific annual income for this persona within the wage range.

    Uses age as a proxy for career stage:
    - Young (18-29): tends toward Q1/low
    - Mid-career (30-49): tends toward median-Q3
    - Senior (50-64): tends toward Q3/high
    - Retired (65+): pension estimate
    """
    age = persona["age"]
    median = wage_data["median_annual"]
    low = wage_data.get("low_annual") or int(median * 0.6)
    high = wage_data.get("high_annual") or int(median * 1.8)
    q1 = wage_data.get("q1_annual") or int((low + median) / 2)
    q3 = wage_data.get("q3_annual") or int((median + high) / 2)

    def safe_randint(a, b):
        a, b = int(a), int(b)
        if a > b:
            a, b = b, a
        if a == b:
            return a
        return rng.randint(a, b)

    if age < 25:
        base = safe_randint(low, q1)
    elif age < 35:
        base = safe_randint(q1, median)
    elif age < 50:
        base = safe_randint(median, q3)
    elif age < 65:
        base = safe_randint(int(median * 0.9), q3)
    else:
        base = safe_randint(q1, median)

    # Add some noise (+/- 5%)
    noise = rng.uniform(-0.05, 0.05)
    return max(0, int(base * (1 + noise)))


# --- Enrich personas ---
rng = random.Random(42)
matched = 0
unmatched = 0
not_employed = 0

for p in personas:
    occ = p["occupation"]
    mapping = noc_map.get(occ)

    if not mapping:
        p["noc_code"] = None
        p["noc_title"] = None
        p["is_employed"] = True
        p["estimated_annual_income"] = None
        p["income_bracket"] = "Unknown"
        p["income_source"] = "no_noc_mapping"
        unmatched += 1
        continue

    p["noc_code"] = mapping["noc_code"]
    p["noc_title"] = mapping["noc_title"]
    p["is_employed"] = mapping["is_employed"]

    if not mapping["is_employed"]:
        # Students, retired, unemployed, etc.
        not_employed += 1
        if occ == "Retired":
            # Estimate pension: 40-70% of median working income for their province
            # Use national median of ~$45K as base
            pension = rng.randint(18000, 45000)
            p["estimated_annual_income"] = pension
            p["income_bracket"] = assign_income_bracket(pension)
            p["income_source"] = "estimated_pension"
        elif occ in ("College Student", "University Student"):
            student_income = rng.randint(5000, 25000)
            p["estimated_annual_income"] = student_income
            p["income_bracket"] = assign_income_bracket(student_income)
            p["income_source"] = "estimated_student"
        elif occ == "Unemployed (seeking work)":
            ei_income = rng.randint(12000, 28000)  # EI benefits range
            p["estimated_annual_income"] = ei_income
            p["income_bracket"] = assign_income_bracket(ei_income)
            p["income_source"] = "estimated_ei"
        elif occ == "Stay-at-home Parent":
            p["estimated_annual_income"] = 0
            p["income_bracket"] = "Under $20K"
            p["income_source"] = "not_employed"
        elif occ == "Person with disability (not working)":
            disability_income = rng.randint(10000, 22000)
            p["estimated_annual_income"] = disability_income
            p["income_bracket"] = assign_income_bracket(disability_income)
            p["income_source"] = "estimated_disability"
        elif occ == "Recent Immigrant (settling in)":
            newcomer_income = rng.randint(8000, 30000)
            p["estimated_annual_income"] = newcomer_income
            p["income_bracket"] = assign_income_bracket(newcomer_income)
            p["income_source"] = "estimated_newcomer"
        else:
            p["estimated_annual_income"] = None
            p["income_bracket"] = "Unknown"
            p["income_source"] = "not_employed"
        continue

    # Employed — look up wage
    wage_data = get_wage(mapping["noc_code"], p["province"])
    if wage_data:
        income = estimate_persona_income(wage_data, p, rng)
        p["estimated_annual_income"] = income
        p["income_bracket"] = assign_income_bracket(income)
        p["income_source"] = wage_data["source"]
        p["wage_data"] = {
            "median_annual": wage_data["median_annual"],
            "low_annual": wage_data["low_annual"],
            "high_annual": wage_data["high_annual"],
        }
        matched += 1
    else:
        p["estimated_annual_income"] = None
        p["income_bracket"] = "Unknown"
        p["income_source"] = "no_wage_data"
        unmatched += 1

print(f"\nResults:")
print(f"  Matched with wage data: {matched}")
print(f"  Not employed (estimated): {not_employed}")
print(f"  Unmatched: {unmatched}")

# --- Save enriched personas ---
out_path = ROOT / "data/personas_5000_enriched.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(personas, f, indent=2, ensure_ascii=False, default=str)
print(f"\nSaved enriched personas to {out_path}")
print(f"  Fields per persona: {len(personas[0])}")

# --- Save test sample ---
sample = rng.sample(personas, 10)
test_path = ROOT / "scripts/test_enriched.json"
with open(test_path, "w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2, ensure_ascii=False, default=str)
print(f"Saved 10-persona test sample to {test_path}")

# --- Quick stats ---
incomes = [p["estimated_annual_income"] for p in personas if p["estimated_annual_income"]]
if incomes:
    print(f"\nIncome stats ({len(incomes)} personas with income):")
    print(f"  Median: ${sorted(incomes)[len(incomes)//2]:,}")
    print(f"  Min:    ${min(incomes):,}")
    print(f"  Max:    ${max(incomes):,}")
    print(f"  Mean:   ${sum(incomes)//len(incomes):,}")

# Bracket distribution
from collections import Counter
brackets = Counter(p["income_bracket"] for p in personas)
print(f"\nIncome bracket distribution:")
for bracket, count in sorted(brackets.items()):
    print(f"  {bracket:15s}  {count:5d}  ({count/len(personas)*100:.1f}%)")
