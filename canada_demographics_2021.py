"""
Canada Demographics Data - 2021 Census of Population (Statistics Canada)
=========================================================================
All data sourced from Statistics Canada 2021 Census unless otherwise noted.
Designed as probability weights for synthetic Canadian persona generation.

Total population (2021 Census): 36,991,981
Reference year for income data: 2020 (calendar year prior to census)

Sources:
- Statistics Canada, 2021 Census of Population
  https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/index-eng.cfm
- Census Profile tables, Focus on Geography Series, The Daily releases
"""

# =============================================================================
# 1. PROVINCE / TERRITORY POPULATION DISTRIBUTION
# =============================================================================
# Source: Statistics Canada, Table 98-10-0001-01
# Total population: 36,991,981

PROVINCE_TERRITORY_POPULATION = {
    "Ontario":                     14_223_942,
    "Quebec":                       8_501_833,
    "British Columbia":             5_000_879,
    "Alberta":                      4_262_635,
    "Manitoba":                     1_342_153,
    "Saskatchewan":                 1_132_505,
    "Nova Scotia":                    969_383,
    "New Brunswick":                  775_610,
    "Newfoundland and Labrador":      510_550,
    "Prince Edward Island":           154_331,
    "Northwest Territories":           41_070,
    "Yukon":                           40_232,
    "Nunavut":                         36_858,
}

# As percentages (weights summing to 100.0)
PROVINCE_TERRITORY_WEIGHTS = {
    "Ontario":                     38.45,
    "Quebec":                      22.98,
    "British Columbia":            13.52,
    "Alberta":                     11.52,
    "Manitoba":                     3.63,
    "Saskatchewan":                 3.06,
    "Nova Scotia":                  2.62,
    "New Brunswick":                2.10,
    "Newfoundland and Labrador":    1.38,
    "Prince Edward Island":         0.42,
    "Northwest Territories":        0.11,
    "Yukon":                        0.11,
    "Nunavut":                      0.10,
}


# =============================================================================
# 2. CENSUS METROPOLITAN AREAS (CMAs) - TOP 41
# =============================================================================
# Source: Statistics Canada, Table 98-10-0005-01 and Table 98-10-0006-01
# Note: 2021 Census had 41 CMAs (6 new ones added since 2016).
# Some population figures below are from the census profile / highlight tables.
# Minor rounding differences may exist between data products.

CMA_POPULATION = [
    # (Rank, CMA Name, Province, 2021 Population)
    ( 1, "Toronto",                        "Ontario",                6_202_225),
    ( 2, "Montreal",                        "Quebec",                4_291_732),
    ( 3, "Vancouver",                       "British Columbia",      2_642_825),
    ( 4, "Ottawa-Gatineau",                 "Ontario/Quebec",        1_488_307),
    ( 5, "Calgary",                         "Alberta",               1_481_806),
    ( 6, "Edmonton",                        "Alberta",               1_418_118),
    ( 7, "Quebec City",                     "Quebec",                  839_311),
    ( 8, "Winnipeg",                        "Manitoba",                834_678),
    ( 9, "Hamilton",                        "Ontario",                 785_184),
    (10, "Kitchener-Cambridge-Waterloo",    "Ontario",                 575_847),
    (11, "London",                          "Ontario",                 543_551),
    (12, "St. Catharines-Niagara",          "Ontario",                 433_604),
    (13, "Halifax",                         "Nova Scotia",             465_703),
    (14, "Oshawa",                          "Ontario",                 415_311),
    (15, "Victoria",                        "British Columbia",        397_237),
    (16, "Windsor",                         "Ontario",                 422_630),
    (17, "Saskatoon",                       "Saskatchewan",            317_480),
    (18, "Regina",                          "Saskatchewan",            249_217),
    (19, "Sherbrooke",                      "Quebec",                  227_398),
    (20, "St. John's",                      "Newfoundland and Labrador", 212_579),
    (21, "Barrie",                          "Ontario",                 212_856),
    (22, "Kelowna",                         "British Columbia",        222_162),
    (23, "Abbotsford-Mission",              "British Columbia",        195_328),
    (24, "Greater Sudbury",                 "Ontario",                 166_004),
    (25, "Kingston",                        "Ontario",                 172_546),
    (26, "Saguenay",                        "Quebec",                  157_790),
    (27, "Trois-Rivieres",                  "Quebec",                  161_191),
    (28, "Guelph",                          "Ontario",                 165_588),
    (29, "Moncton",                         "New Brunswick",           157_717),
    (30, "Brantford",                       "Ontario",                 134_203),
    (31, "Saint John",                      "New Brunswick",           130_613),
    (32, "Peterborough",                    "Ontario",                 125_667),
    (33, "Thunder Bay",                     "Ontario",                 121_621),
    (34, "Lethbridge",                      "Alberta",                 117_394),
    (35, "Nanaimo",                         "British Columbia",        115_459),
    (36, "Kamloops",                        "British Columbia",        114_142),
    (37, "Chilliwack",                      "British Columbia",        113_767),
    (38, "Belleville-Quinte West",          "Ontario",                 111_491),
    (39, "Fredericton",                     "New Brunswick",           108_610),
    (40, "Red Deer",                        "Alberta",                 100_844),
    (41, "Drummondville",                   "Quebec",                  101_610),
]


# =============================================================================
# 3. AGE DISTRIBUTION
# =============================================================================
# Source: Census Profile, 2021 Census - Canada
# Total population: 36,991,981
# For persona generation (adults 18+), recompute weights excluding 0-17.

AGE_DISTRIBUTION_ALL = {
    # Age group: (count, percentage_of_total)
    "0-14":   (6_012_795, 16.25),
    "15-19":  (2_012_975,  5.44),
    "20-24":  (2_202_255,  5.95),
    "25-29":  (2_421_510,  6.55),
    "30-34":  (2_518_835,  6.81),
    "35-39":  (2_511_345,  6.79),
    "40-44":  (2_399_405,  6.49),
    "45-49":  (2_304_170,  6.23),
    "50-54":  (2_368_350,  6.40),
    "55-59":  (2_647_330,  7.16),
    "60-64":  (2_571_580,  6.95),
    "65-69":  (2_210_970,  5.98),
    "70-74":  (1_847_585,  4.99),
    "75-79":  (1_260_930,  3.41),
    "80-84":  (  840_545,  2.27),
    "85+":    (  861_395,  2.33),
}

# Adult-only age groups (18+), regrouped for persona generation
# Derived from 5-year groups above. 15-17 (~60% of 15-19) subtracted.
# Approximate adult population 18+: ~30,170,000
ADULT_AGE_WEIGHTS = {
    "18-24":  10.2,   # partial 15-19 (18-19) + 20-24
    "25-34":  16.4,   # 25-29 + 30-34
    "35-44":  16.3,   # 35-39 + 40-44
    "45-54":  15.5,   # 45-49 + 50-54
    "55-64":  17.3,   # 55-59 + 60-64
    "65-74":  13.4,   # 65-69 + 70-74
    "75+":    10.9,   # 75-79 + 80-84 + 85+
}


# =============================================================================
# 4. SEX / GENDER DISTRIBUTION
# =============================================================================
# Source: Census Profile, 2021 Census - Canada
# Sex at birth: Male 49.3%, Female 50.7%
# Gender identity (15+): Men 48.93%, Women 50.94%, Non-binary 0.14%

SEX_AT_BIRTH_WEIGHTS = {
    "Male":   49.3,
    "Female": 50.7,
}

GENDER_IDENTITY_WEIGHTS = {
    "Man":        48.93,
    "Woman":      50.94,
    "Non-binary":  0.14,
}


# =============================================================================
# 5. EDUCATION LEVELS
# =============================================================================
# Source: Table 98-10-0384-01, 2021 Census
# Population aged 15+ in private households
# For population aged 25-64, percentages shift (higher attainment).
# Both sets provided.

# Population 15+ (all ages)
EDUCATION_WEIGHTS_15PLUS = {
    "No certificate, diploma or degree":            16.2,
    "High school diploma or equivalent":            26.7,
    "Apprenticeship or trades certificate":           8.7,
    "College, CEGEP or other non-university":        18.8,
    "University certificate below bachelor":          3.0,
    "Bachelor's degree":                             17.4,
    "Graduate degree (Master's, Doctorate, Professional)": 9.3,
}

# Population 25-64 (working-age, more commonly used for persona generation)
# Source: The Daily, Nov 30 2022 release; Census Profile 25-64 age filter
EDUCATION_WEIGHTS_25_64 = {
    "No certificate, diploma or degree":             8.3,
    "High school diploma or equivalent":            21.3,
    "Apprenticeship or trades certificate":          10.0,
    "College, CEGEP or other non-university":        21.5,
    "University certificate below bachelor":          3.1,
    "Bachelor's degree":                             23.7,
    "Graduate degree (Master's, Doctorate, Professional)": 12.1,
}


# =============================================================================
# 6. OCCUPATION CATEGORIES (NOC 2021 Broad Categories)
# =============================================================================
# Source: 2021 Census, NOC 2021 Version 1.0 broad categories
# Employed labour force aged 15+ in private households
# Total employed: ~18.9 million
#
# Note: The interactive StatCan visualization groups these into 3 macro groups:
#   Management/Business/Science: 27.3%
#   Health/Education/Culture: 23.5%
#   Sales/Trades/Resources/Manufacturing: 49.2%
#
# Individual broad category estimates below derived from Labour Force Survey
# monthly data (Dec 2021) and census cross-tabulation products.
# These are approximate but suitable for weighted random generation.

OCCUPATION_WEIGHTS = {
    "0 - Legislative and senior management":                        4.0,
    "1 - Business, finance and administration":                    16.5,
    "2 - Natural and applied sciences and related":                 8.0,
    "3 - Health occupations":                                       7.5,
    "4 - Education, law and social, community and government":     11.0,
    "5 - Art, culture, recreation and sport":                       3.2,
    "6 - Sales and service":                                       22.0,
    "7 - Trades, transport and equipment operators":               14.5,
    "8 - Natural resources, agriculture and related production":    3.0,
    "9 - Manufacturing and utilities":                              5.3,
    "Not applicable / not in labour force":                         5.0,
}


# =============================================================================
# 7. INDIVIDUAL INCOME BRACKETS
# =============================================================================
# Source: Census Profile, 2021 Census - Canada
# Total income of individuals aged 15+ in 2020 (calendar year prior to census)
# Population with income: ~29.2 million
# Median total income: $41,200
# Average total income: $50,700 (approx)
# Median after-tax household income: $73,000

INCOME_BRACKET_COUNTS = {
    "Under $10,000":          2_434_730,
    "$10,000-$19,999":        3_448_185,
    "$20,000-$29,999":        4_635_650,
    "$30,000-$39,999":        3_723_680,
    "$40,000-$49,999":        3_290_715,
    "$50,000-$59,999":        2_677_465,
    "$60,000-$69,999":        2_100_000,   # estimated from distribution
    "$70,000-$79,999":        1_750_000,   # estimated from distribution
    "$80,000-$89,999":        1_400_000,   # estimated from distribution
    "$90,000-$99,999":        1_100_000,   # estimated from distribution
    "$100,000 and over":      3_160_245,
}

# As percentage weights (approx, summing to ~100)
INCOME_BRACKET_WEIGHTS = {
    "Under $10,000":           8.3,
    "$10,000-$19,999":        11.8,
    "$20,000-$29,999":        15.9,
    "$30,000-$39,999":        12.7,
    "$40,000-$49,999":        11.3,
    "$50,000-$59,999":         9.2,
    "$60,000-$69,999":         7.2,
    "$70,000-$79,999":         6.0,
    "$80,000-$89,999":         4.8,
    "$90,000-$99,999":         2.0,
    "$100,000 and over":      10.8,
}


# =============================================================================
# 8. IMMIGRATION STATUS
# =============================================================================
# Source: Focus on Geography Series, 2021 Census - Canada (Immigration topic)
# Total population: 36,328,480 (in private households)

IMMIGRATION_STATUS_WEIGHTS = {
    "Canadian-born (non-immigrant)": 74.4,
    "Immigrant":                     23.0,
    "Non-permanent resident":         2.5,
}

IMMIGRATION_STATUS_COUNTS = {
    "Canadian-born (non-immigrant)": 27_042_125,
    "Immigrant":                      8_361_505,
    "Non-permanent resident":           924_850,
}

# Top source countries for RECENT immigrants (2016-2021): 1,328,240 total
RECENT_IMMIGRANT_SOURCE_COUNTRIES = {
    "India":        (246_995, 18.6),
    "Philippines":  (151_490, 11.4),
    "China":        (118_035,  8.9),
    "Syria":        ( 63_135,  4.8),
    "Nigeria":      ( 40_355,  3.0),
    "Pakistan":     ( 36_000,  2.7),   # approximate
    "France":       ( 33_000,  2.5),   # approximate
    "Iran":         ( 31_000,  2.3),   # approximate
    "United States":( 28_000,  2.1),   # approximate
    "South Korea":  ( 25_000,  1.9),   # approximate
    "Other":        (555_230, 41.8),
}


# =============================================================================
# 9. VISIBLE MINORITY / RACIALIZED GROUPS
# =============================================================================
# Source: Focus on Geography Series, 2021 Census - Canada
# Note: "Visible minority" terminology replaced by "racialized population"
#       in 2021 Census products.
# Total racialized population: 9,639,205 (26.5% of total)
# Not a visible minority (incl. Indigenous): 73.5%

VISIBLE_MINORITY_WEIGHTS = {
    "Not a visible minority":    73.5,
    "South Asian":                7.1,
    "Chinese":                    4.7,
    "Black":                      4.3,
    "Filipino":                   2.6,
    "Arab":                       1.9,
    "Latin American":             1.6,
    "Southeast Asian":            1.1,
    "West Asian":                 1.0,
    "Korean":                     0.6,
    "Japanese":                   0.3,
    "Multiple visible minorities": 0.9,
    "Visible minority n.i.e.":    0.5,
}

VISIBLE_MINORITY_COUNTS = {
    "South Asian":                2_571_400,
    "Chinese":                    1_715_770,
    "Black":                      1_547_870,
    "Filipino":                     957_355,
    "Arab":                         694_020,
    "Latin American":               580_235,
    "Southeast Asian":              390_340,
    "West Asian":                   360_495,
    "Korean":                       218_140,
    "Japanese":                      98_890,
    "Multiple visible minorities":  331_805,
    "Visible minority n.i.e.":      172_885,
}


# =============================================================================
# 10. INDIGENOUS IDENTITY
# =============================================================================
# Source: The Daily, Sept 21 2022; Focus on Geography, 2021 Census
# Total Indigenous population: 1,807,250 (5.0% of total population)

INDIGENOUS_IDENTITY_WEIGHTS = {
    "Non-Indigenous":  95.0,
    "First Nations":    2.9,   # 1,048,405 = 58.0% of Indigenous
    "Metis":            1.7,   #   624,220 = 34.5% of Indigenous
    "Inuit":            0.2,   #    70,545 =  3.9% of Indigenous
    "Other Indigenous identity": 0.2,  # multiple or other responses
}

INDIGENOUS_COUNTS = {
    "First Nations":  1_048_405,
    "Metis":            624_220,
    "Inuit":             70_545,
    "Other Indigenous":  64_080,
    "Total Indigenous":1_807_250,
}


# =============================================================================
# 11. LANGUAGE
# =============================================================================
# Source: The Daily, Aug 17 2022; Census Profile, 2021 Census
# First Official Language Spoken (FOLS):
#   English: 75.5%, French: 21.4%, Both: 1.3%, Neither: 1.8%
# Knowledge of official languages:
#   English only: ~75%, French only: ~4%, Both: ~18%, Neither: ~2%
# English-French bilingualism rate: 18.0%

# First Official Language Spoken
FIRST_OFFICIAL_LANGUAGE_WEIGHTS = {
    "English":          75.5,
    "French":           21.4,
    "English and French": 1.3,
    "Neither":           1.8,
}

# Knowledge of Official Languages
OFFICIAL_LANGUAGE_KNOWLEDGE_WEIGHTS = {
    "English only":           74.7,
    "French only":             3.8,
    "English and French":     17.9,
    "Neither English nor French": 3.6,
}

# Mother Tongue (first language learned at home in childhood)
# English: 56.9%, French: 20.4%, Non-official language: 22.7%
MOTHER_TONGUE_WEIGHTS = {
    "English":              56.9,
    "French":               20.4,
    "Non-official language": 22.7,
}

# Top non-official mother tongues (approximate percentages of total pop)
TOP_NONOFFICIAL_LANGUAGES = {
    "Mandarin":    1.9,
    "Punjabi":     1.8,
    "Cantonese":   1.2,
    "Spanish":     1.2,
    "Arabic":      1.2,
    "Tagalog":     1.1,
    "Italian":     0.9,
    "Hindi":       0.7,
    "Urdu":        0.6,
    "Portuguese":  0.5,
    "Persian":     0.5,
    "Tamil":       0.5,
    "German":      0.5,
    "Vietnamese":  0.4,
    "Korean":      0.4,
    "Other":       8.3,
}


# =============================================================================
# 12. MARITAL STATUS
# =============================================================================
# Source: Focus on Geography Series, 2021 Census - Canada (Families topic)
# Population aged 15 and over in private households

MARITAL_STATUS_WEIGHTS = {
    "Married (not separated)":  44.3,
    "Living common-law":        12.6,
    "Never married (single)":   29.1,
    "Separated":                 2.4,
    "Divorced":                  6.2,
    "Widowed":                   5.4,
}


# =============================================================================
# 13. HOUSING
# =============================================================================
# Source: Census Profile, 2021 Census; Table 98-10-0047-01
# Total occupied private dwellings: 14,978,940

HOUSING_TENURE_WEIGHTS = {
    "Owner":                                   66.5,
    "Renter":                                  33.1,
    "Dwelling provided by local government/First Nation": 0.5,
}

DWELLING_TYPE_COUNTS = {
    "Single-detached house":                   7_872_305,
    "Semi-detached house":                       746_560,
    "Row house":                                 980_110,
    "Apartment or flat in a duplex":             821_495,
    "Apartment, building 5+ storeys":          1_596_155,
    "Apartment, building < 5 storeys":         2_738_020,
    "Other single-attached house":                34_880,
    "Movable dwelling":                          189_420,
}

DWELLING_TYPE_WEIGHTS = {
    "Single-detached house":                   52.6,
    "Semi-detached house":                      5.0,
    "Row house":                                6.5,
    "Apartment or flat in a duplex":            5.5,
    "Apartment, building 5+ storeys":          10.7,
    "Apartment, building < 5 storeys":         18.3,
    "Other single-attached house":              0.2,
    "Movable dwelling":                         1.3,
}

# Condominium status
CONDOMINIUM_WEIGHTS = {
    "Condominium":      15.0,
    "Not condominium":  85.0,
}


# =============================================================================
# HELPER: Province -> CMA mapping for weighted generation
# =============================================================================
# Maps each province to its CMAs for hierarchical persona generation

PROVINCE_TO_CMAS = {
    "Ontario": [
        "Toronto", "Ottawa-Gatineau", "Hamilton",
        "Kitchener-Cambridge-Waterloo", "London", "St. Catharines-Niagara",
        "Oshawa", "Windsor", "Barrie", "Greater Sudbury", "Kingston",
        "Guelph", "Brantford", "Peterborough", "Thunder Bay",
        "Belleville-Quinte West",
    ],
    "Quebec": [
        "Montreal", "Quebec City", "Sherbrooke", "Saguenay",
        "Trois-Rivieres", "Drummondville",
    ],
    "British Columbia": [
        "Vancouver", "Victoria", "Kelowna", "Abbotsford-Mission",
        "Nanaimo", "Kamloops", "Chilliwack",
    ],
    "Alberta": [
        "Calgary", "Edmonton", "Lethbridge", "Red Deer",
    ],
    "Manitoba": ["Winnipeg"],
    "Saskatchewan": ["Saskatoon", "Regina"],
    "Nova Scotia": ["Halifax"],
    "New Brunswick": ["Moncton", "Saint John", "Fredericton"],
    "Newfoundland and Labrador": ["St. John's"],
    "Prince Edward Island": [],
    "Northwest Territories": [],
    "Yukon": [],
    "Nunavut": [],
}


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================
SUMMARY = {
    "total_population_2021":      36_991_981,
    "total_private_households":   14_978_940,
    "median_individual_income":   41_200,
    "median_household_income_before_tax": 84_000,
    "median_household_income_after_tax":  73_000,
    "average_employment_income_fulltime": 77_200,
    "population_15_plus":         30_979_186,
    "employed_labour_force":      18_900_000,  # approximate
    "homeownership_rate":         66.5,
    "immigration_rate":           23.0,
    "indigenous_rate":             5.0,
    "bilingualism_rate_en_fr":    18.0,
    "visible_minority_rate":      26.5,
}
