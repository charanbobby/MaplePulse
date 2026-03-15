#!/usr/bin/env python3
"""
Generate synthetic Canadian personas grounded in 2021 Census demographics.

Uses Statistics Canada demographic distributions as sampling weights,
then enriches each persona with LLM-generated personality details.

Usage:
  # Generate 50 personas (test run, no LLM needed - skeleton only)
  python scripts/generate_canada_personas.py --count 50 --skeleton-only

  # Generate 100 personas with LLM enrichment (requires ANTHROPIC_API_KEY)
  python scripts/generate_canada_personas.py --count 100

  # Full generation run
  python scripts/generate_canada_personas.py --count 5000 --output public/data/personas.canada.v1.json

Requirements:
  pip install anthropic

Attribution:
  - Demographic data: Statistics Canada, 2021 Census of Population
  - Original Ask Singapore project: Aayush Mathur (https://github.com/AayushMathur7/ask-singapore)
  - Persona generation approach inspired by NVIDIA Nemotron-Personas methodology
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import uuid
from pathlib import Path

# Add parent directory to path so we can import the demographics module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from canada_demographics_2021 import (
    ADULT_AGE_WEIGHTS,
    CMA_POPULATION,
    DWELLING_TYPE_WEIGHTS,
    EDUCATION_WEIGHTS_25_64,
    FIRST_OFFICIAL_LANGUAGE_WEIGHTS,
    HOUSING_TENURE_WEIGHTS,
    IMMIGRATION_STATUS_WEIGHTS,
    INDIGENOUS_IDENTITY_WEIGHTS,
    MARITAL_STATUS_WEIGHTS,
    OCCUPATION_WEIGHTS,
    PROVINCE_TERRITORY_WEIGHTS,
    PROVINCE_TO_CMAS,
    SEX_AT_BIRTH_WEIGHTS,
    VISIBLE_MINORITY_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Occupation exemplars — realistic job titles per NOC broad category
# ---------------------------------------------------------------------------
OCCUPATION_EXEMPLARS: dict[str, list[str]] = {
    "0 - Legislative and senior management": [
        "CEO", "Chief Financial Officer", "Director of Operations",
        "Municipal Councillor", "Vice President of Marketing",
        "Executive Director (Non-profit)", "School Board Superintendent",
        "Hospital Administrator", "General Manager", "Band Chief",
    ],
    "1 - Business, finance and administration": [
        "Accountant", "Financial Analyst", "Human Resources Manager",
        "Administrative Assistant", "Bookkeeper", "Insurance Underwriter",
        "Payroll Administrator", "Office Manager", "Purchasing Agent",
        "Business Analyst", "Tax Preparer", "Compliance Officer",
        "Executive Assistant", "Receptionist", "Data Entry Clerk",
    ],
    "2 - Natural and applied sciences and related": [
        "Software Developer", "Civil Engineer", "Data Scientist",
        "Environmental Scientist", "Mechanical Engineer", "IT Project Manager",
        "Network Administrator", "Geologist", "Architect",
        "Biomedical Researcher", "Cybersecurity Analyst", "UX Designer",
        "Systems Analyst", "Chemical Engineer", "Surveyor",
    ],
    "3 - Health occupations": [
        "Registered Nurse", "Family Physician", "Pharmacist",
        "Dental Hygienist", "Physiotherapist", "Paramedic",
        "Personal Support Worker", "Veterinarian", "Optometrist",
        "Medical Laboratory Technologist", "Occupational Therapist",
        "Psychologist", "Midwife", "Respiratory Therapist",
    ],
    "4 - Education, law and social, community and government": [
        "Elementary School Teacher", "High School Teacher", "Social Worker",
        "Lawyer", "Police Officer", "Paralegal", "Professor",
        "Early Childhood Educator", "Probation Officer", "Librarian",
        "Immigration Consultant", "Community Development Worker",
        "Firefighter", "Guidance Counsellor",
    ],
    "5 - Art, culture, recreation and sport": [
        "Graphic Designer", "Journalist", "Photographer",
        "Fitness Instructor", "Museum Curator", "Film Editor",
        "Translator", "Interior Designer", "Musician",
        "Recreation Program Coordinator", "Public Relations Specialist",
    ],
    "6 - Sales and service": [
        "Retail Sales Associate", "Real Estate Agent", "Chef",
        "Customer Service Representative", "Hair Stylist", "Hotel Manager",
        "Security Guard", "Restaurant Server", "Insurance Broker",
        "Travel Agent", "Cashier", "Bartender", "Store Manager",
        "Food Service Supervisor", "Call Centre Agent",
    ],
    "7 - Trades, transport and equipment operators": [
        "Electrician", "Plumber", "Carpenter", "Truck Driver",
        "Welder", "Heavy Equipment Operator", "Auto Mechanic",
        "Construction Labourer", "HVAC Technician", "Crane Operator",
        "Bus Driver", "Elevator Mechanic", "Millwright",
        "Delivery Driver", "Ironworker",
    ],
    "8 - Natural resources, agriculture and related production": [
        "Farm Manager", "Forestry Technician", "Fisher",
        "Mining Engineer", "Oil and Gas Driller", "Landscaper",
        "Agricultural Technician", "Park Ranger", "Greenhouse Worker",
    ],
    "9 - Manufacturing and utilities": [
        "Machine Operator", "Quality Control Inspector",
        "Assembly Line Worker", "Power Plant Operator",
        "Water Treatment Technician", "Industrial Mechanic",
        "CNC Machinist", "Process Operator", "Packaging Technician",
    ],
    "Not applicable / not in labour force": [
        "Retired", "University Student", "Stay-at-home Parent",
        "Unemployed (seeking work)", "College Student",
        "Person with disability (not working)", "Recent Immigrant (settling in)",
    ],
}

# ---------------------------------------------------------------------------
# Cultural background templates by visible minority / indigenous status
# ---------------------------------------------------------------------------
CULTURAL_TEMPLATES: dict[str, list[str]] = {
    "South Asian": [
        "Indian-Canadian heritage, family immigrated from {country}",
        "Punjabi-Canadian, raised in a Sikh household",
        "Sri Lankan Tamil background, active in the Tamil community",
        "Bangladeshi-Canadian, maintains close ties to South Asian culture",
        "Pakistani-Canadian, grew up bilingual (Urdu and English)",
    ],
    "Chinese": [
        "Chinese-Canadian, family from {region}, speaks Mandarin at home",
        "Cantonese-Canadian, grew up in a close-knit Chinese community",
        "Taiwanese-Canadian, bilingual in Mandarin and English",
        "Chinese heritage, second-generation Canadian",
    ],
    "Black": [
        "Caribbean-Canadian, family from Jamaica",
        "African-Canadian, parents immigrated from Nigeria",
        "Haitian-Canadian, grew up speaking French and Creole",
        "Somali-Canadian, active in the East African community",
        "Black Canadian, family has been in Canada for generations",
    ],
    "Filipino": [
        "Filipino-Canadian, speaks Tagalog at home",
        "Filipino heritage, family came to Canada through the caregiver program",
        "Filipino-Canadian, active in the Filipino community",
    ],
    "Arab": [
        "Lebanese-Canadian, grew up in a bilingual Arabic-English household",
        "Syrian refugee family, resettled in Canada in 2016",
        "Egyptian-Canadian, maintains strong ties to Arabic culture",
        "Moroccan-Canadian, trilingual in Arabic, French, and English",
    ],
    "Latin American": [
        "Colombian-Canadian, bilingual in Spanish and English",
        "Mexican-Canadian, grew up celebrating both cultures",
        "Chilean-Canadian, family came to Canada as political refugees",
        "Brazilian-Canadian, speaks Portuguese at home",
    ],
    "Southeast Asian": [
        "Vietnamese-Canadian, family came as boat people in the 1980s",
        "Thai-Canadian, grew up between two cultures",
        "Cambodian-Canadian, parents survived the Khmer Rouge era",
    ],
    "West Asian": [
        "Iranian-Canadian, speaks Farsi at home",
        "Afghan-Canadian, family resettled as refugees",
        "Kurdish-Canadian, maintains strong cultural traditions",
    ],
    "Korean": [
        "Korean-Canadian, grew up in a Korean church community",
        "Second-generation Korean-Canadian, bilingual",
    ],
    "Japanese": [
        "Japanese-Canadian, fourth-generation (Yonsei)",
        "Japanese heritage, moved to Canada for work",
    ],
    "First Nations": [
        "First Nations ({nation}), grew up on reserve",
        "First Nations ({nation}), urban Indigenous person",
        "First Nations heritage, reconnecting with cultural traditions",
    ],
    "Metis": [
        "Metis heritage, proud of Red River roots",
        "Metis, grew up learning jigging and Michif phrases",
        "Metis background, active in the Metis community",
    ],
    "Inuit": [
        "Inuit, grew up in {community} in Nunavut",
        "Inuit heritage, speaks Inuktitut",
    ],
    "Not a visible minority": [
        "English-Canadian background, family in Canada for generations",
        "French-Canadian (Quebecois), strong cultural identity",
        "Scottish-Canadian heritage, family came during early immigration waves",
        "Irish-Canadian background",
        "Ukrainian-Canadian heritage, active in cultural community",
        "Italian-Canadian, grew up in a close-knit Italian neighbourhood",
        "German-Canadian heritage",
        "Polish-Canadian background",
        "Portuguese-Canadian, grew up in a Portuguese community",
        "Dutch-Canadian heritage, family has farming roots",
        "Greek-Canadian background",
        "Acadian heritage (New Brunswick)",
    ],
}

# ---------------------------------------------------------------------------
# Regional signals — values, concerns, and identity (from CES, Environics,
# Confederation of Tomorrow surveys, World Values Survey Canada subset)
# ---------------------------------------------------------------------------
POLITICAL_LEANING_WEIGHTS: dict[str, dict[str, float]] = {
    # Approximate leanings derived from CES 2019/2021 + Angus Reid regional polling
    "British Columbia":       {"Progressive": 0.35, "Moderate": 0.30, "Conservative": 0.25, "Libertarian": 0.05, "Apolitical": 0.05},
    "Alberta":                {"Progressive": 0.15, "Moderate": 0.20, "Conservative": 0.50, "Libertarian": 0.10, "Apolitical": 0.05},
    "Saskatchewan":           {"Progressive": 0.15, "Moderate": 0.25, "Conservative": 0.45, "Libertarian": 0.08, "Apolitical": 0.07},
    "Manitoba":               {"Progressive": 0.25, "Moderate": 0.30, "Conservative": 0.30, "Libertarian": 0.05, "Apolitical": 0.10},
    "Ontario":                {"Progressive": 0.30, "Moderate": 0.30, "Conservative": 0.28, "Libertarian": 0.05, "Apolitical": 0.07},
    "Quebec":                 {"Progressive": 0.30, "Moderate": 0.25, "Conservative": 0.15, "Nationalist": 0.20, "Apolitical": 0.10},
    "New Brunswick":          {"Progressive": 0.25, "Moderate": 0.30, "Conservative": 0.30, "Libertarian": 0.05, "Apolitical": 0.10},
    "Nova Scotia":            {"Progressive": 0.30, "Moderate": 0.30, "Conservative": 0.28, "Libertarian": 0.04, "Apolitical": 0.08},
    "Prince Edward Island":   {"Progressive": 0.30, "Moderate": 0.35, "Conservative": 0.25, "Libertarian": 0.03, "Apolitical": 0.07},
    "Newfoundland and Labrador": {"Progressive": 0.30, "Moderate": 0.30, "Conservative": 0.25, "Libertarian": 0.05, "Apolitical": 0.10},
    "Yukon":                  {"Progressive": 0.35, "Moderate": 0.30, "Conservative": 0.20, "Libertarian": 0.05, "Apolitical": 0.10},
    "Northwest Territories":  {"Progressive": 0.35, "Moderate": 0.30, "Conservative": 0.15, "Libertarian": 0.05, "Apolitical": 0.15},
    "Nunavut":                {"Progressive": 0.25, "Moderate": 0.25, "Conservative": 0.10, "Libertarian": 0.05, "Apolitical": 0.35},
}

# Religion — from Census 2021 (53.3% Christian overall, 34.6% no religion, rising)
RELIGION_WEIGHTS: dict[str, dict[str, float]] = {
    "British Columbia":       {"No religion": 0.52, "Christian": 0.34, "Sikh": 0.05, "Buddhist": 0.03, "Muslim": 0.03, "Hindu": 0.02, "Other": 0.01},
    "Alberta":                {"No religion": 0.40, "Christian": 0.47, "Muslim": 0.04, "Sikh": 0.03, "Hindu": 0.02, "Buddhist": 0.02, "Other": 0.02},
    "Saskatchewan":           {"No religion": 0.37, "Christian": 0.55, "Muslim": 0.02, "Sikh": 0.02, "Indigenous spirituality": 0.02, "Other": 0.02},
    "Manitoba":               {"No religion": 0.35, "Christian": 0.53, "Muslim": 0.02, "Sikh": 0.02, "Hindu": 0.02, "Indigenous spirituality": 0.02, "Other": 0.02},
    "Ontario":                {"No religion": 0.35, "Christian": 0.48, "Muslim": 0.07, "Hindu": 0.04, "Sikh": 0.02, "Buddhist": 0.01, "Jewish": 0.02, "Other": 0.01},
    "Quebec":                 {"No religion": 0.37, "Christian": 0.53, "Muslim": 0.05, "Jewish": 0.02, "Buddhist": 0.01, "Hindu": 0.01, "Other": 0.01},
    "New Brunswick":          {"No religion": 0.33, "Christian": 0.63, "Muslim": 0.01, "Other": 0.03},
    "Nova Scotia":            {"No religion": 0.37, "Christian": 0.56, "Muslim": 0.03, "Other": 0.04},
    "Prince Edward Island":   {"No religion": 0.33, "Christian": 0.62, "Muslim": 0.02, "Other": 0.03},
    "Newfoundland and Labrador": {"No religion": 0.28, "Christian": 0.68, "Other": 0.04},
    "Yukon":                  {"No religion": 0.50, "Christian": 0.36, "Indigenous spirituality": 0.06, "Other": 0.08},
    "Northwest Territories":  {"No religion": 0.42, "Christian": 0.42, "Indigenous spirituality": 0.10, "Other": 0.06},
    "Nunavut":                {"No religion": 0.20, "Christian": 0.55, "Indigenous spirituality": 0.20, "Other": 0.05},
}

# Top concerns by region — from Angus Reid, Environics, CES, Confederation of Tomorrow
REGIONAL_CONCERNS: dict[str, list[str]] = {
    "British Columbia":       ["housing affordability", "climate change", "cost of living", "healthcare wait times", "opioid crisis", "transit infrastructure"],
    "Alberta":                ["oil and gas economy", "cost of living", "federal-provincial fairness", "healthcare", "housing affordability", "pipeline politics"],
    "Saskatchewan":           ["agricultural economy", "cost of living", "healthcare access", "natural resource development", "rural infrastructure"],
    "Manitoba":               ["healthcare wait times", "cost of living", "housing", "reconciliation with Indigenous peoples", "infrastructure"],
    "Ontario":                ["housing affordability", "cost of living", "healthcare", "immigration", "transit gridlock", "education funding"],
    "Quebec":                 ["language and culture", "cost of living", "healthcare", "immigration and integration", "climate change", "provincial autonomy"],
    "New Brunswick":          ["healthcare access", "cost of living", "aging population", "bilingual services", "economic development"],
    "Nova Scotia":            ["healthcare access", "cost of living", "housing", "population aging", "economic opportunity"],
    "Prince Edward Island":   ["healthcare", "housing affordability", "cost of living", "seasonal economy", "tourism sustainability"],
    "Newfoundland and Labrador": ["economic diversification", "healthcare", "outmigration", "cost of living", "fisheries sustainability"],
    "Yukon":                  ["housing", "reconciliation", "cost of living", "climate change and permafrost", "healthcare access"],
    "Northwest Territories":  ["reconciliation", "cost of living", "housing", "climate change", "healthcare and mental health"],
    "Nunavut":                ["housing crisis", "food security", "mental health", "reconciliation and self-governance", "cost of living", "education"],
}

# Commute mode — from Census 2021 Journey to Work data
COMMUTE_WEIGHTS_URBAN: dict[str, float] = {
    "drives": 0.65, "public transit": 0.22, "walks": 0.06, "cycles": 0.03, "works from home": 0.04,
}
COMMUTE_WEIGHTS_SUBURBAN: dict[str, float] = {
    "drives": 0.80, "public transit": 0.10, "walks": 0.02, "cycles": 0.01, "works from home": 0.07,
}
COMMUTE_WEIGHTS_RURAL: dict[str, float] = {
    "drives": 0.85, "walks": 0.04, "works from home": 0.09, "other": 0.02,
}

FIRST_NATIONS_EXAMPLES = [
    "Cree", "Ojibwe", "Mi'kmaq", "Mohawk", "Dene", "Blackfoot",
    "Salish", "Haida", "Tlingit", "Algonquin", "Innu", "Nuu-chah-nulth",
]

INUIT_COMMUNITIES = [
    "Iqaluit", "Rankin Inlet", "Arviat", "Cambridge Bay",
    "Pond Inlet", "Pangnirtung", "Baker Lake", "Kuujjuaq",
]


# ---------------------------------------------------------------------------
# Weighted random choice helper
# ---------------------------------------------------------------------------
def weighted_choice(weights: dict[str, float], rng: random.Random) -> str:
    """Pick a key from a dict of {label: weight} using weighted sampling."""
    labels = list(weights.keys())
    values = list(weights.values())
    return rng.choices(labels, weights=values, k=1)[0]


def pick_age_from_bracket(bracket: str, rng: random.Random) -> int:
    """Convert an age bracket like '25-34' into a specific age."""
    if bracket == "75+":
        return rng.randint(75, 95)
    parts = bracket.split("-")
    lo, hi = int(parts[0]), int(parts[1])
    return rng.randint(lo, hi)


def pick_region(province: str, rng: random.Random) -> str:
    """Pick a CMA within the province, or return 'Rural <Province>' if no CMA or randomly."""
    cmas = PROVINCE_TO_CMAS.get(province, [])
    if not cmas:
        # Territories or PEI — no CMA
        if province == "Nunavut":
            return rng.choice(["Iqaluit", "Rankin Inlet", "Arviat", "Cambridge Bay"])
        if province == "Northwest Territories":
            return rng.choice(["Yellowknife", "Hay River", "Inuvik"])
        if province == "Yukon":
            return rng.choice(["Whitehorse", "Dawson City"])
        if province == "Prince Edward Island":
            return rng.choice(["Charlottetown", "Summerside"])
        return f"Rural {province}"

    # ~30% chance of rural/small town for provinces with CMAs
    if rng.random() < 0.15:
        return f"Rural {province}"

    # Weight CMAs by population
    cma_pops = {}
    for rank, name, prov, pop in CMA_POPULATION:
        if name in cmas:
            cma_pops[name] = pop
    if not cma_pops:
        return f"Rural {province}"

    return weighted_choice({k: float(v) for k, v in cma_pops.items()}, rng)


def determine_cultural_background(
    visible_minority: str,
    indigenous: str,
    immigration_status: str,
    rng: random.Random,
) -> str:
    """Generate a cultural background string based on demographic attributes."""
    # Indigenous takes priority
    if indigenous == "First Nations":
        templates = CULTURAL_TEMPLATES["First Nations"]
        template = rng.choice(templates)
        return template.format(nation=rng.choice(FIRST_NATIONS_EXAMPLES))
    if indigenous == "Metis":
        return rng.choice(CULTURAL_TEMPLATES["Metis"])
    if indigenous == "Inuit":
        templates = CULTURAL_TEMPLATES["Inuit"]
        template = rng.choice(templates)
        return template.format(community=rng.choice(INUIT_COMMUNITIES))

    # Visible minority
    if visible_minority != "Not a visible minority":
        key = visible_minority
        # Handle combined/other categories
        if key in ("Multiple visible minorities", "Visible minority n.i.e."):
            key = rng.choice(["South Asian", "Chinese", "Black", "Filipino", "Arab", "Latin American"])
        templates = CULTURAL_TEMPLATES.get(key, CULTURAL_TEMPLATES["Not a visible minority"])
        template = rng.choice(templates)
        # Fill in placeholders
        if "{country}" in template:
            countries = {
                "South Asian": ["India", "Pakistan", "Sri Lanka", "Bangladesh", "Nepal"],
                "West Asian": ["Iran", "Afghanistan", "Turkey"],
            }
            template = template.format(country=rng.choice(countries.get(key, ["their homeland"])))
        if "{region}" in template:
            template = template.format(region=rng.choice(["Guangdong", "Fujian", "Hong Kong", "Beijing", "Shanghai"]))
        return template

    # Not a visible minority
    return rng.choice(CULTURAL_TEMPLATES["Not a visible minority"])


# ---------------------------------------------------------------------------
# Core persona generator (skeleton — demographics only, no LLM)
# ---------------------------------------------------------------------------
def assign_languages(
    province: str, immigration_status: str, visible_minority: str, rng: random.Random
) -> str:
    """Assign languages based on province, immigration status, and background."""
    if province == "Quebec":
        lang_roll = rng.random()
        if lang_roll < 0.50:
            languages = "French"
        elif lang_roll < 0.85:
            languages = "French, English"
        else:
            languages = "French, English, and another language"
    elif province == "New Brunswick":
        lang_roll = rng.random()
        if lang_roll < 0.65:
            languages = "English"
        elif lang_roll < 0.85:
            languages = "English, French"
        else:
            languages = "French, English"
    else:
        lang = weighted_choice(FIRST_OFFICIAL_LANGUAGE_WEIGHTS, rng)
        if lang == "English":
            languages = "English"
        elif lang == "French":
            languages = "French"
        elif lang == "English and French":
            languages = "English, French"
        else:
            languages = rng.choice([
                "Mandarin", "Punjabi", "Cantonese", "Spanish", "Arabic",
                "Tagalog", "Hindi", "Urdu", "Farsi", "Tamil",
            ])

    # Add heritage language for immigrants/visible minorities
    if immigration_status == "Immigrant" and visible_minority != "Not a visible minority" and rng.random() < 0.6:
        heritage_lang_map = {
            "South Asian": ["Hindi", "Punjabi", "Urdu", "Tamil", "Bengali", "Gujarati"],
            "Chinese": ["Mandarin", "Cantonese"],
            "Filipino": ["Tagalog"],
            "Arab": ["Arabic"],
            "Latin American": ["Spanish", "Portuguese"],
            "Korean": ["Korean"],
            "Japanese": ["Japanese"],
            "Southeast Asian": ["Vietnamese", "Thai", "Khmer"],
            "West Asian": ["Farsi", "Dari", "Turkish"],
        }
        heritage_options = heritage_lang_map.get(visible_minority, [])
        if heritage_options:
            heritage = rng.choice(heritage_options)
            if heritage not in languages:
                languages = f"{languages}, {heritage}"

    return languages


def generate_skeleton_persona(rng: random.Random, province_override: str | None = None) -> dict:
    """Generate a single persona's demographic skeleton from census distributions."""
    # Province
    province = province_override or weighted_choice(PROVINCE_TERRITORY_WEIGHTS, rng)

    # Region (CMA or rural)
    region = pick_region(province, rng)

    # Age
    age_bracket = weighted_choice(ADULT_AGE_WEIGHTS, rng)
    age = pick_age_from_bracket(age_bracket, rng)

    # Sex
    sex = weighted_choice(SEX_AT_BIRTH_WEIGHTS, rng)

    # Education
    education_level = weighted_choice(EDUCATION_WEIGHTS_25_64, rng)

    # Marital status
    marital_status = weighted_choice(MARITAL_STATUS_WEIGHTS, rng)

    # Occupation category → specific job
    occ_category = weighted_choice(OCCUPATION_WEIGHTS, rng)
    # Adjust for age: students more likely young, retired more likely old
    if age < 25 and rng.random() < 0.4:
        occ_category = "Not applicable / not in labour force"
    if age >= 65 and rng.random() < 0.6:
        occ_category = "Not applicable / not in labour force"

    exemplars = OCCUPATION_EXEMPLARS.get(occ_category, ["Worker"])
    occupation = rng.choice(exemplars)
    # Adjust "not in labour force" exemplars by age
    if occ_category == "Not applicable / not in labour force":
        if age >= 65:
            occupation = "Retired"
        elif age < 25:
            occupation = rng.choice(["University Student", "College Student"])

    # Immigration status
    immigration_status = weighted_choice(IMMIGRATION_STATUS_WEIGHTS, rng)

    # Indigenous identity
    indigenous = weighted_choice(INDIGENOUS_IDENTITY_WEIGHTS, rng)
    if indigenous == "Other Indigenous identity":
        indigenous = rng.choice(["First Nations", "Metis"])
    # If indigenous, force Canadian-born
    if indigenous != "Non-Indigenous":
        immigration_status = "Canadian-born (non-immigrant)"

    # Visible minority
    visible_minority = weighted_choice(VISIBLE_MINORITY_WEIGHTS, rng)
    # Indigenous people are not counted as visible minorities in the census
    if indigenous != "Non-Indigenous":
        visible_minority = "Not a visible minority"

    # Language
    languages = assign_languages(province, immigration_status, visible_minority, rng)

    # Cultural background
    cultural_background = determine_cultural_background(
        visible_minority, indigenous, immigration_status, rng
    )

    # Housing
    tenure = weighted_choice(HOUSING_TENURE_WEIGHTS, rng)
    dwelling = weighted_choice(DWELLING_TYPE_WEIGHTS, rng)
    housing = f"{tenure}, {dwelling}"

    # --- New signals: political leaning, religion, concerns, commute ---

    # Political leaning (province-weighted, age-adjusted)
    province_politics = POLITICAL_LEANING_WEIGHTS.get(province, POLITICAL_LEANING_WEIGHTS["Ontario"])
    political_leaning = weighted_choice(province_politics, rng)
    # Age adjustment: younger skews progressive, older skews conservative
    if age < 30 and political_leaning == "Conservative" and rng.random() < 0.3:
        political_leaning = "Progressive"
    elif age >= 60 and political_leaning == "Progressive" and rng.random() < 0.25:
        political_leaning = "Moderate"

    # Religion (province-weighted, adjusted for visible minority)
    province_religion = RELIGION_WEIGHTS.get(province, RELIGION_WEIGHTS["Ontario"])
    religion = weighted_choice(province_religion, rng)
    # Adjust religion for visible minority groups where there's a strong correlation
    if visible_minority == "South Asian" and rng.random() < 0.7:
        religion = rng.choice(["Hindu", "Sikh", "Muslim", "Christian"])
    elif visible_minority == "Arab" and rng.random() < 0.8:
        religion = "Muslim"
    elif visible_minority == "Filipino" and rng.random() < 0.7:
        religion = "Christian"
    elif indigenous != "Non-Indigenous" and rng.random() < 0.3:
        religion = "Indigenous spirituality"

    # Top concerns — pick 2-3 from the regional list
    regional_pool = REGIONAL_CONCERNS.get(province, REGIONAL_CONCERNS["Ontario"])
    num_concerns = rng.choice([2, 2, 3])
    top_concerns = rng.sample(regional_pool, min(num_concerns, len(regional_pool)))

    # Commute mode — based on urban/rural and occupation
    is_rural = region.startswith("Rural") or region in (
        "Rankin Inlet", "Arviat", "Cambridge Bay", "Pond Inlet",
        "Hay River", "Inuvik", "Dawson City", "Summerside",
    )
    big_cities = {"Toronto", "Montreal", "Vancouver", "Ottawa - Gatineau", "Calgary", "Edmonton"}
    if occ_category == "Not applicable / not in labour force":
        commute_mode = "not applicable"
    elif is_rural:
        commute_mode = weighted_choice(COMMUTE_WEIGHTS_RURAL, rng)
    elif region in big_cities:
        commute_mode = weighted_choice(COMMUTE_WEIGHTS_URBAN, rng)
    else:
        commute_mode = weighted_choice(COMMUTE_WEIGHTS_SUBURBAN, rng)

    return {
        "uuid": str(uuid.uuid4()),
        "age": age,
        "sex": sex,
        "occupation": occupation,
        "education_level": education_level,
        "marital_status": marital_status,
        "planning_area": region,  # keeping field name for compatibility with ask-singapore
        "province": province,
        "immigration_status": immigration_status,
        "indigenous_identity": indigenous,
        "visible_minority": visible_minority,
        "languages_spoken": languages,
        "housing": housing,
        "cultural_background": cultural_background,
        "political_leaning": political_leaning,
        "religion": religion,
        "top_concerns": top_concerns,
        "commute_mode": commute_mode,
        # These will be filled by LLM enrichment
        "persona": "",
        "skills_and_expertise": "",
        "hobbies_and_interests": "",
        "career_goals_and_ambitions": "",
    }


# ---------------------------------------------------------------------------
# LLM enrichment — generate personality details via Claude
# ---------------------------------------------------------------------------
PERSONA_TOOL = {
    "name": "generate_persona_details",
    "description": "Output the generated personality details for a synthetic Canadian persona.",
    "input_schema": {
        "type": "object",
        "properties": {
            "persona": {
                "type": "string",
                "description": "A 1-2 sentence summary of who this person is, their personality, and outlook on life. Max 180 characters.",
            },
            "skills_and_expertise": {
                "type": "string",
                "description": "Comma-separated list of 3-5 skills relevant to their occupation and background. Max 110 characters.",
            },
            "hobbies_and_interests": {
                "type": "string",
                "description": "Comma-separated list of 3-5 hobbies realistic for this person. Max 110 characters.",
            },
            "career_goals_and_ambitions": {
                "type": "string",
                "description": "1 sentence about their career/life goals. Max 110 characters.",
            },
        },
        "required": ["persona", "skills_and_expertise", "hobbies_and_interests", "career_goals_and_ambitions"],
    },
}


def build_enrichment_prompt(persona: dict) -> str:
    """Build the LLM prompt to enrich a skeleton persona with personality details."""
    concerns_str = ", ".join(persona.get("top_concerns", []))
    return f"""You are generating a realistic synthetic Canadian persona for a survey simulation app.
Given the demographic profile below, generate personality details that are authentic and grounded in the demographics.

Demographic Profile:
- Age: {persona['age']}
- Sex: {persona['sex']}
- Location: {persona['planning_area']}, {persona['province']}
- Occupation: {persona['occupation']}
- Education: {persona['education_level']}
- Marital status: {persona['marital_status']}
- Immigration status: {persona['immigration_status']}
- Indigenous identity: {persona['indigenous_identity']}
- Cultural background: {persona['cultural_background']}
- Languages: {persona['languages_spoken']}
- Housing: {persona['housing']}
- Political leaning: {persona['political_leaning']}
- Religion: {persona['religion']}
- Top concerns: {concerns_str}
- Commute: {persona['commute_mode']}

Rules:
- Be realistic and grounded in Canadian culture and the person's demographics
- Let their political leaning, religion, and regional concerns subtly inform their personality and goals — but don't make these the entire persona
- Avoid stereotypes while being culturally authentic
- Keep all fields concise — respect the character limits
- Use the generate_persona_details tool to return your response"""


async def enrich_single_persona(
    client,
    persona: dict,
    model: str,
    index: int,
    total: int,
    max_retries: int = 3,
) -> dict:
    """Enrich a single persona asynchronously using tool calling for guaranteed JSON."""
    prompt = build_enrichment_prompt(persona)

    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=300,
                temperature=0.7,
                tools=[PERSONA_TOOL],
                tool_choice={"type": "tool", "name": "generate_persona_details"},
                messages=[{"role": "user", "content": prompt}],
            )

            for block in response.content:
                if block.type == "tool_use":
                    result = block.input
                    persona["persona"] = result.get("persona", "")[:180]
                    persona["skills_and_expertise"] = result.get("skills_and_expertise", "")[:110]
                    persona["hobbies_and_interests"] = result.get("hobbies_and_interests", "")[:110]
                    persona["career_goals_and_ambitions"] = result.get("career_goals_and_ambitions", "")[:110]
                    return persona

            # No tool_use block found — treat as failure
            raise ValueError("No tool_use block in response")

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  WARNING: Failed for persona {index}/{total}: {e}")
            else:
                await asyncio.sleep(2 ** attempt)

    return persona  # Returns with empty fields if all retries fail


async def enrich_personas_async(
    personas: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-5-20250514",
    batch_size: int = 10,
    max_retries: int = 3,
) -> list[dict]:
    """Enrich skeleton personas concurrently using async tool calling."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        print("ERROR: anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = AsyncAnthropic(api_key=api_key)
    enriched: list[dict] = []
    total = len(personas)

    for i in range(0, total, batch_size):
        batch = personas[i : i + batch_size]
        tasks = [
            enrich_single_persona(client, p, model, i + j + 1, total, max_retries)
            for j, p in enumerate(batch)
        ]

        batch_results = await asyncio.gather(*tasks)
        enriched.extend(batch_results)
        print(f"  Enriched {len(enriched)}/{total} personas")

        # Brief pause between batches to respect rate limits
        if i + batch_size < total:
            await asyncio.sleep(0.5)

    return enriched


def enrich_personas_with_llm(
    personas: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-5-20250514",
    batch_size: int = 10,
    max_retries: int = 3,
) -> list[dict]:
    """Sync wrapper around the async enrichment pipeline."""
    return asyncio.run(
        enrich_personas_async(personas, api_key, model, batch_size, max_retries)
    )


# ---------------------------------------------------------------------------
# Stratified generation — ensure geographic coverage
# ---------------------------------------------------------------------------
def generate_stratified_personas(
    count: int,
    seed: int = 42,
) -> list[dict]:
    """Generate personas stratified across provinces and regions."""
    rng = random.Random(seed)

    # Calculate per-province targets based on population weights
    province_targets: dict[str, int] = {}
    total_weight = sum(PROVINCE_TERRITORY_WEIGHTS.values())
    for province, weight in PROVINCE_TERRITORY_WEIGHTS.items():
        target = max(1, round(count * weight / total_weight))
        province_targets[province] = target

    # Adjust to hit exact count
    current_total = sum(province_targets.values())
    if current_total > count:
        # Remove from largest provinces
        sorted_provs = sorted(province_targets, key=lambda p: province_targets[p], reverse=True)
        for prov in sorted_provs:
            if current_total <= count:
                break
            province_targets[prov] -= 1
            current_total -= 1
    elif current_total < count:
        sorted_provs = sorted(province_targets, key=lambda p: province_targets[p], reverse=True)
        for prov in sorted_provs:
            if current_total >= count:
                break
            province_targets[prov] += 1
            current_total += 1

    personas = []
    for province, target in province_targets.items():
        for _ in range(target):
            persona = generate_skeleton_persona(rng, province_override=province)
            # Special handling for Nunavut — predominantly Inuit
            if province == "Nunavut" and rng.random() < 0.85:
                persona["indigenous_identity"] = "Inuit"
                persona["immigration_status"] = "Canadian-born (non-immigrant)"
                persona["visible_minority"] = "Not a visible minority"
                persona["cultural_background"] = determine_cultural_background(
                    "Not a visible minority", "Inuit", "Canadian-born (non-immigrant)", rng
                )
            personas.append(persona)

    rng.shuffle(personas)
    return personas[:count]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Canadian personas from census demographics."
    )
    parser.add_argument(
        "--count", type=int, default=5000,
        help="Number of personas to generate (default: 5000)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output", default="public/data/personas.canada.v1.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--meta-output", default="public/data/personas.canada.v1.meta.json",
        help="Output metadata JSON file path",
    )
    parser.add_argument(
        "--skeleton-only", action="store_true",
        help="Generate demographic skeletons only (no LLM enrichment)",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-5-20250514",
        help="Anthropic model to use for enrichment",
    )
    parser.add_argument(
        "--batch-size", type=int, default=10,
        help="Number of concurrent LLM calls per batch (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    meta_output = Path(args.meta_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    meta_output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.count} Canadian personas (seed={args.seed})...")
    personas = generate_stratified_personas(args.count, args.seed)
    print(f"  Generated {len(personas)} demographic skeletons")

    # Show distribution summary
    province_counts: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    for p in personas:
        province_counts[p["province"]] = province_counts.get(p["province"], 0) + 1
        region_counts[p["planning_area"]] = region_counts.get(p["planning_area"], 0) + 1

    print(f"\n  Province distribution:")
    for prov, cnt in sorted(province_counts.items(), key=lambda x: -x[1]):
        print(f"    {prov}: {cnt} ({100*cnt/len(personas):.1f}%)")

    print(f"\n  Top 15 regions:")
    for region, cnt in sorted(region_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {region}: {cnt}")

    unique_regions = len(region_counts)
    print(f"\n  Total unique regions: {unique_regions}")

    if not args.skeleton_only:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("\nERROR: ANTHROPIC_API_KEY not set. Either set it or use --skeleton-only")
            sys.exit(1)
        print(f"\nEnriching personas with LLM ({args.model})...")
        personas = enrich_personas_with_llm(
            personas, api_key, model=args.model, batch_size=args.batch_size
        )
        print(f"  Enrichment complete")

    # Write output
    with output.open("w", encoding="utf-8") as fp:
        json.dump(personas, fp, ensure_ascii=True, separators=(",", ":"))

    # Write metadata
    meta = {
        "source": "Statistics Canada, 2021 Census of Population",
        "generator": "scripts/generate_canada_personas.py",
        "attribution": {
            "demographics": "Statistics Canada, 2021 Census",
            "original_project": "Aayush Mathur, Ask Singapore (https://github.com/AayushMathur7/ask-singapore)",
            "persona_methodology": "Inspired by NVIDIA Nemotron-Personas approach",
        },
        "count": len(personas),
        "unique_provinces": len(province_counts),
        "unique_regions": unique_regions,
        "seed": args.seed,
        "skeleton_only": args.skeleton_only,
        "model": None if args.skeleton_only else args.model,
        "province_distribution": province_counts,
    }
    with meta_output.open("w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=True, indent=2)

    print(f"\nWrote {len(personas)} personas to {output}")
    print(f"Wrote metadata to {meta_output}")


if __name__ == "__main__":
    main()
