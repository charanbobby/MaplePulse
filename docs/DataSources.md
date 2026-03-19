# Public Data Sources for Canadian Synthetic Personas

Beyond Statistics Canada 2021 Census data, the following sources can enrich persona generation with values, attitudes, behaviors, lifestyle, and psychographic signals.

---

## 1. Canadian Values & Attitudes Surveys

### Environics Institute for Survey Research
- **What**: Non-profit conducting in-depth public opinion research since 2006. Annual Social Values surveys (5,000+ Canadians/year since 1983). Focus Canada program tracks attitudes on trust, migration, multiculturalism. Confederation of Tomorrow surveys (5,000-6,000 respondents) cover identity, federalism, provincial belonging.
- **Signals**: Social values, trust in institutions, attitudes on immigration/diversity, regional identity, sense of belonging, views on federalism
- **Access**: Reports freely available; some raw data may require request
- **URLs**:
  - https://www.environicsinstitute.org/
  - https://www.environicsinstitute.org/projects/-in-type/type/canadian-public-opinion
- **Persona use**: Values orientation, attitudes on diversity/immigration, regional identity feelings

### Canadian Election Study (CES)
- **What**: Conducted every election year since 1965. The 2019 study gathered attitudes from 37,000+ respondents. Covers political attitudes, policy preferences, media consumption, trust, identity.
- **Signals**: Political ideology, party preference, policy positions, media habits, democratic engagement, trust in institutions
- **Access**: FREE - Public datasets on Harvard Dataverse and Borealis. R packages (cesR, ces) available on CRAN.
- **URLs**:
  - https://ces-eec.arts.ubc.ca/english-section/surveys/
  - https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XBZHKC (2021)
  - https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DUS88V (2019)
  - https://github.com/hodgettsp/cesR
- **Persona use**: Political leaning, policy concerns, democratic engagement level, media consumption habits

### World Values Survey (Canada Subset)
- **What**: Global survey with Canada data for 1982, 1990, 2000, 2006, 2020. Covers values on religion, gender, governance, social tolerance, life satisfaction, economic values.
- **Signals**: Moral values, religious importance, social tolerance, life satisfaction, economic attitudes, trust
- **Access**: FREE - Download from worldvaluessurvey.org
- **URLs**:
  - https://catalog.ihsn.org/catalog/study/CAN_2020_WVS-W7_v01_M
  - https://www.kaggle.com/datasets/fernandol/world-values-survey
- **Persona use**: Deep values/worldview, moral attitudes, religiosity, social tolerance levels

### Angus Reid Institute
- **What**: Non-partisan, non-profit polling foundation. Regular surveys on politics, society, policy. Uses Angus Reid Forum panel, weighted by demographics.
- **Signals**: Current issue opinions, trust in institutions, community belonging, policy preferences
- **Access**: Reports freely available online; raw data access varies
- **URL**: https://angusreid.org/
- **Persona use**: Current concern priorities, policy opinions, community engagement

### Confederation of Tomorrow Surveys
- **What**: Annual survey (5,000-6,000 adults) by consortium of policy organizations. Focuses on federalism, provincial identity, regional grievances.
- **Signals**: Provincial attachment, views on federal-provincial relations, regional identity, satisfaction with governance
- **Access**: Reports freely available
- **URLs**:
  - https://centre.irpp.org/data/confederation-of-tomorrow-surveys/
  - https://www.environicsinstitute.org/projects/project-details/confederation-of-tomorrow-2025-survey-of-canadians
- **Persona use**: Provincial identity strength, regional grievances, views on federalism

### Pew Research Center (Canada data)
- **What**: Global Attitudes Survey includes Canada regularly. Spring 2025 survey covered moral attitudes, views on US, social issues across 25 countries.
- **Signals**: Moral views (abortion, homosexuality), views on fellow citizens, international attitudes
- **Access**: FREE - Reports and datasets available
- **URL**: https://www.pewresearch.org/global/
- **Persona use**: Moral/social attitudes, international outlook

---

## 2. Consumer Behavior & Lifestyle Data

### Vividata (Study of the Canadian Consumer)
- **What**: Canada's most comprehensive consumer/media database. 40,000+ Canadians surveyed/year. 60,000+ variables, 1,500+ psychographic characteristics, 4,000+ brands.
- **Signals**: Media consumption (TV, streaming, print, radio, digital), brand preferences, product purchases, psychographics, opinions, activities
- **Access**: PAID - Subscription required. Some findings published in reports.
- **URLs**:
  - https://vividata.ca/
  - https://vividata.ca/our-data/study-of-the-canadian-consumer/
- **Persona use**: Media consumption patterns, brand affinities, lifestyle activities, psychographic profiles

### Environics Analytics PRIZM
- **What**: 67 geodemographic lifestyle segments classifying all Canadian neighbourhoods. Integrates demographic, psychographic, and geographic data from 40,000+ data points.
- **Signals**: Lifestyle type by postal code, consumer behavior patterns, media preferences, product affinities
- **Access**: PAID product, but FREE postal code lookup tool available. 67 segment descriptions publicly documented.
- **URLs**:
  - https://environicsanalytics.com/en-ca/data/segmentation/prizm
  - https://prizm.environicsanalytics.com/ (free lookup)
  - https://environicsanalytics.com/docs/default-source/can---glossaries-and-technical/prizm---technical-document.pdf
- **Persona use**: Map postal codes to lifestyle segments; use segment descriptions to infer consumer behavior, media preferences, values

### Numeris
- **What**: Canada's sole broadcast audience measurement organization. Measures radio and TV audiences via Personal People Meters in 5 markets (Vancouver, Edmonton, Calgary, Toronto, Montreal).
- **Signals**: TV show preferences, radio station choices, streaming vs. linear TV habits
- **Access**: Limited public data (top 30 TV shows, radio listenership). Full data requires membership.
- **URL**: https://en.numeris.ca/
- **Persona use**: Media consumption preferences by market/demographics

### Survey of Household Spending (SHS)
- **What**: Statistics Canada survey on household expenditures, dwelling characteristics, household equipment. PUMF available for multiple years.
- **Signals**: Spending patterns by category, dwelling type, household equipment ownership
- **Access**: FREE - PUMF on Open Government Portal
- **URLs**:
  - https://open.canada.ca/data/en/dataset/e77d97a0-cdd6-443e-9d68-b04818a95a6e
  - https://www150.statcan.gc.ca/n1/en/catalogue/62M0004X
- **Persona use**: Spending priorities, material lifestyle indicators

### Canadian Financial Capability Survey (CFCS)
- **What**: Sponsored by HRSDC/Finance Canada/FCAC. Covers financial literacy, money management, budgeting, saving, investment approaches.
- **Signals**: Financial literacy, saving habits, debt management, financial planning approach
- **Access**: FREE - PUMF available (2008, 2014 cycles)
- **URL**: https://www150.statcan.gc.ca/n1/en/catalogue/18-505-X
- **Persona use**: Financial behavior, financial stress levels, planning orientation

---

## 3. Health & Wellbeing

### Canadian Community Health Survey (CCHS)
- **What**: ~130,000 respondents aged 12+ across all provinces/territories over two-year cycles. Covers physical/mental health, chronic conditions, health behaviors.
- **Signals**: Self-rated health, chronic conditions, physical activity, smoking, alcohol, BMI, mental health, healthcare access
- **Access**: FREE - PUMF available
- **URLs**:
  - https://www150.statcan.gc.ca/n1/en/catalogue/82M0013X
  - https://www.canada.ca/en/health-canada/services/food-nutrition/food-nutrition-surveillance/health-nutrition-surveys/canadian-community-health-survey-cchs.html
- **Persona use**: Health status, health behaviors, chronic conditions, lifestyle risk factors

### CCHS - Nutrition Component
- **What**: Detailed dietary intake data using 24-hour recalls. Conducted 2004 and 2015.
- **Signals**: Food consumption patterns, dietary habits, nutrient intake
- **Access**: Available through Statistics Canada
- **URL**: https://www.canada.ca/en/health-canada/services/food-nutrition/food-nutrition-surveillance/health-nutrition-surveys/canadian-community-health-survey-cchs/2015-canadian-community-health-survey-nutrition-food-nutrition-surveillance.html
- **Persona use**: Dietary preferences, food culture signals

### Mental Health and Access to Care Survey (MHACS)
- **What**: Covers mental health status of Canadians 15+, access to services, need for formal/informal support.
- **Signals**: Mental health status, anxiety/depression prevalence, service usage, barriers to care
- **Access**: Available through Statistics Canada
- **URL**: https://www.statcan.gc.ca/en/survey/household/5015
- **Persona use**: Mental health indicators, help-seeking behavior

### Canadian Survey on Disability (CSD)
- **What**: Covers Canadians 15+ with activity limitations. Includes disability type/severity, assistive aids, employment, education, social isolation.
- **Signals**: Disability type, severity, accommodations needed, employment barriers, social isolation, internet use
- **Access**: Available through Statistics Canada
- **URL**: https://www.statcan.gc.ca/en/survey/household/3251
- **Persona use**: Disability representation, accessibility needs, employment barriers

---

## 4. Digital Behavior

### CIRA Canadian Internet Trends (formerly Internet Factbook)
- **What**: Annual survey of 2,000+ Canadian internet users. Covers internet habits, AI adoption, cybersecurity, e-commerce, social media trust.
- **Signals**: Social media platform usage, AI tool adoption, online shopping preferences, cybersecurity awareness, trust in platforms
- **Access**: FREE - Reports downloadable
- **URLs**:
  - https://www.cira.ca/en/resources/documents/state-of-internet/canadian-internet-trends-2025/
  - https://www.cira.ca/en/resources/documents/state-of-internet/
- **Persona use**: Digital sophistication, platform preferences, online trust levels, AI adoption

### Canadian Internet Use Survey (CIUS)
- **What**: Statistics Canada survey on digital technology adoption. 95% of Canadians 15+ used internet in 2022. Detailed demographic breakdowns.
- **Signals**: Internet access, intensity of use, online activities, e-government, digital skills, privacy concerns
- **Access**: FREE - PUMF available on Open Government Portal
- **URLs**:
  - https://www.statcan.gc.ca/en/survey/household/4432
  - https://open.canada.ca/data/en/dataset/7e9fe4e5-d311-43d9-a385-57603ef1de1b
- **Persona use**: Digital literacy level, online activity patterns, privacy sensitivity

### Social Media Usage Statistics (DataReportal / Social Media Lab)
- **What**: Multiple sources track platform-specific usage. Key stats: Facebook 66%, Instagram 45%, X/Twitter 19%, TikTok 18% of Canadians. Detailed age breakdowns available.
- **Signals**: Platform preference by age/gender, usage frequency, content engagement patterns
- **Access**: FREE - Reports available online
- **URLs**:
  - https://datareportal.com/reports/digital-2025-canada
  - https://canadiansinternet.com/2025-report-social-media-use-canada-statistics/
  - https://socialmedialab.ca/
- **Persona use**: Social media platform selection, digital engagement style

---

## 5. Political Views & Civic Engagement

### Elections Canada Open Data
- **What**: Voter turnout by age, gender, province for multiple election cycles (GE38-GE45). Administrative data combined with National Register of Electors.
- **Signals**: Voter turnout rates by demographics, electoral participation patterns
- **Access**: FREE - Open Government Portal
- **URLs**:
  - https://open.canada.ca/data/en/dataset/b545fe25-5cf5-4488-9923-b5c2ebeeb8cc
  - https://www.elections.ca/content.aspx?section=ele&dir=turn&document=index&lang=e
- **Persona use**: Likelihood of voting, political engagement level

### Samara Centre for Democracy
- **What**: Non-partisan charity producing research on civic engagement. MP Exit Interview Project (160+ former MPs), SAMbot (online abuse tracking), Democracy 360 report cards.
- **Signals**: Barriers to civic participation, online political abuse, democratic culture indicators
- **Access**: FREE - Reports and publications available
- **URL**: https://www.samaracentre.ca/
- **Persona use**: Civic engagement level, attitudes toward democracy, barriers to participation

### GSS - Giving, Volunteering and Participating
- **What**: Every 5 years, covers volunteering (32% in 2023, down from 41% in 2018), charitable giving (54% donate, down from 82%), civic participation.
- **Signals**: Volunteer rates, donation amounts, community involvement, reasons for (not) volunteering
- **Access**: FREE - PUMF available
- **URLs**:
  - https://www.statcan.gc.ca/en/survey/household/4430
  - https://givingandvolunteering.ca/gssgvp-insights/
- **Persona use**: Community engagement level, charitable behavior, volunteering patterns

---

## 6. Regional Culture & Identity Signals

### Key Regional Differences (from multiple surveys)
- **BC**: High environmental concern, high "no religion" (52.1%), progressive social values, high perceived provincial distinctiveness
- **Alberta**: Economic grievance (only 40% feel treated fairly by federal government), resource economy identity, lower trust in federal institutions, more conservative social values
- **Ontario**: Highest perceived fair treatment (75%), highest non-Christian religious diversity (16.3%), urban-suburban divide
- **Quebec**: Unique linguistic/cultural identity, highest gender equality agreement (87%), highest linguistic duality support (79%), distinct media ecosystem, 57 PRIZM QC segments
- **Prairies (SK/MB)**: Lowest gender equality agreement (76%), lowest linguistic duality support (43%), resource economy concerns
- **Atlantic Canada**: Lowest economic satisfaction (36%), aging population, outmigration concerns, strong community ties

### Sources for Regional Signals
- Confederation of Tomorrow surveys (see above)
- Environics Institute regional studies
- Angus Reid Canada Values project: https://angusreid.org/canada-values/
- Statistics Canada: https://www.statcan.gc.ca/o1/en/plus/8260-canadian-data-snapshot-through-multicultural-lens

---

## 7. Income & Wage Data (Actively Used)

### Job Bank Canada — 2025 Wage Data
- **What**: Wage data by NOC (National Occupational Classification) code and province. Includes median, low, high, Q1, Q3 wages. Both hourly and annual rates. Provincial and national level data.
- **Signals**: Occupation-specific income by province, wage ranges, annual vs hourly classification
- **Access**: FREE — downloaded as CSV
- **File**: `data/raw/jobbank_wages_2025.csv`
- **Status**: **ACTIVELY USED** — integrated into `scripts/generate_canada_personas.py` for income assignment
- **Persona use**: `estimated_annual_income`, `income_bracket`, `income_source` fields. Age-adjusted within wage quartiles. Non-employed personas (retirees, students, unemployed) get estimated income from pensions, EI, etc.

### Occupation → NOC Mapping
- **What**: Custom mapping of 100+ occupation exemplars to NOC 5-digit codes
- **File**: `data/occupation_noc_mapping.json`
- **Status**: **ACTIVELY USED** — links persona occupations to Job Bank wage data

---

## 8. Cost of Living & Economic Concerns

### CMHC Housing Data
- **What**: Comprehensive housing market data from neighbourhood to national level. Rental Market Survey with vacancy rates, average rents, turnover rates for all major centres.
- **Signals**: Rent levels by city, vacancy rates, housing affordability, homeownership rates
- **Access**: FREE - Data tables and HMIP portal
- **URLs**:
  - https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data
  - https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables
  - https://www03.cmhc-schl.gc.ca/hmip-pimh/en/TableMapChart
  - R package: https://mountainmath.github.io/canadian_data/intro/intro_cmhc.html
- **Persona use**: Housing cost burden, renter vs. owner concerns, housing affordability stress by city

### Bank of Canada - Canadian Survey of Consumer Expectations (CSCE)
- **What**: Quarterly survey measuring household views on inflation, labour market, household finances. Broken down by age, geography, income, education.
- **Signals**: Inflation expectations, spending plans, financial stress, job loss probability, debt payment risk
- **Access**: FREE - Survey data published quarterly
- **URLs**:
  - https://www.bankofcanada.ca/publications/canadian-survey-of-consumer-expectations/
  - https://www.bankofcanada.ca/publications/canadian-survey-of-consumer-expectations/canadian-survey-of-consumer-expectations-survey-data/
- **Persona use**: Economic anxiety level, financial outlook, spending confidence

---

## 8. Open Datasets on HuggingFace / Kaggle

### HuggingFace Synthetic Persona Datasets
- **SynthLabsAI/PERSONA**: 200k+ synthetic preferences over 1,000 personas grounded in US census (adaptable to Canadian census)
  - https://huggingface.co/datasets/SynthLabsAI/PERSONA
- **proj-persona/PersonaHub**: 1 billion diverse personas from web data
  - https://huggingface.co/datasets/proj-persona/PersonaHub
- **nvidia/Nemotron-Personas-USA**: Synthetically generated personas aligned to real-world US demographic distributions (methodology adaptable to Canada)
  - https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA
- **argilla/FinePersonas-v0.1**: 21M personas from PersonaHub pipeline
  - https://huggingface.co/datasets/argilla/FinePersonas-v0.1
- **google/Synthetic-Persona-Chat**: Persona-grounded chat dataset
  - https://huggingface.co/datasets/google/Synthetic-Persona-Chat

### GitHub Projects
- **MarketPersonas** (marketagents-ai): LLM + census data persona generator. Directly relevant - could be adapted for Canadian census.
  - https://github.com/marketagents-ai/MarketPersonas
- **Polypersona**: LLM with grounded persona profiles for synthetic survey generation. Open-source toolkit.
  - https://arxiv.org/html/2512.14562v1
- **Persona Hub** (Tencent AI Lab): 1B personas from web data
  - https://github.com/tencent-ailab/persona-hub

### Kaggle
- **Reddit r/Canada Subreddit Dataset**: Full dataset of r/Canada posts
  - https://www.kaggle.com/datasets/bwandowando/reddit-rcanada-subreddit-dataset
- **World Values Survey**: Includes Canada data
  - https://www.kaggle.com/datasets/fernandol/world-values-survey

---

## 9. Reddit / Social Media Analysis

### r/Canada Dataset on Kaggle
- **What**: Full dataset of r/Canada subreddit posts available for analysis
- **Access**: FREE on Kaggle
- **URL**: https://www.kaggle.com/datasets/bwandowando/reddit-rcanada-subreddit-dataset
- **Persona use**: Regional concerns, language patterns, issue salience

### Academic Studies on Canadian Subreddits
- **COVID vaccine sentiment**: Study comparing r/vancouver (49K comments), r/toronto (21K), r/calgary (21K) - shows regional variation in health attitudes
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8477909/
- **Samara Centre r/Canada analysis**: Power users dominate political discussion
  - https://www.samaracentre.ca/articles/federal-election-report-1-power-users-dominate-the-discussion-on-r-canada
- **Regional sentiment**: r/Calgary and r/Edmonton more positive; r/canada and r/saskatchewan more negative. Regional subreddits show distinct emotional tones.

### Regional Reddit User Distribution
- Ontario: 39% of Canadian Reddit traffic
- British Columbia: 17%
- Quebec: 15%
- r/Ontario grew 29% in one year (2023-2024)

---

## 10. Additional Statistics Canada Surveys (Free PUMFs)

### General Social Survey (GSS) - Multiple Cycles
- **Time Use** (2015, and earlier): 24-hour diary of activities - sleep, work, leisure, etc.
  - https://www150.statcan.gc.ca/n1/en/catalogue/89M0034X
- **Social Networks** (2008, 2013): Social connections, civic participation, trust, discrimination experiences
  - https://www150.statcan.gc.ca/n1/en/catalogue/12M0022X
- **Social Identity**: Shared values, confidence in institutions, pride, discrimination
  - https://www150.statcan.gc.ca/n1/en/catalogue/89M0032X
- All GSS PUMFs: https://www150.statcan.gc.ca/n1/pub/45-25-0001/index-eng.htm

### Labour Force Survey (LFS)
- **What**: Monthly survey on employment, occupation, industry, hours worked. PUMFs available back to 2006.
- **Access**: FREE
- **URL**: https://open.canada.ca/data/en/dataset/ebd35eda-e224-4bbb-ae9e-1e70d05c6e7d
- **Persona use**: Employment status, work patterns, industry alignment

### Participation in Outdoor Activities
- **What**: Statistics Canada data on outdoor recreation by income, age, region
- **Access**: FREE - Open Government Portal
- **URL**: https://open.canada.ca/data/en/dataset/662cf65a-5d81-43c4-a96b-bd16486bb9b8
- **Persona use**: Hobby/recreation interests

---

## 11. Other Notable Sources

### Ipsos Canadian Public Affairs Dataverse
- **What**: 60+ Ipsos Canada surveys on elections, culture, politics, society. All open access.
- **URL**: https://borealisdata.ca/dataverse/Ipsos
- **Persona use**: Political attitudes, cultural views, social opinions

### EKOS Research Associates
- **What**: Public opinion firm tracking economic confidence, trust in institutions, political polarization since 1980.
- **URL**: https://ekos.com/studies-products/reports/
- **Persona use**: Economic anxiety, institutional trust, polarization levels

### Abacus Data
- **What**: Ottawa-based polling firm with regular national omnibus surveys on politics, consumer behavior, social issues.
- **URL**: https://abacusdata.ca/
- **Persona use**: Current issue priorities, consumer attitudes

### Odesi (Canadian Social Science Data Repository)
- **What**: 5,700+ datasets curated by academic libraries. Includes Statistics Canada PUMFs, Gallup Canada, IPSOS Canada, CORA. Search by variable across thousands of datasets.
- **Access**: FREE and open
- **URLs**:
  - https://odesi.ca/
  - https://borealisdata.ca/dataverse/odesi
- **Persona use**: Master index for discovering additional survey data

### CRTC Communications Monitoring Reports
- **What**: Annual reports on Canadian broadcasting, telecom, internet trends
- **URL**: https://crtc.gc.ca/eng/publications/reports/PolicyMonitoring/aud.htm
- **Persona use**: Media consumption patterns, platform preferences

### Canadian Pet Population Survey (CAHI)
- **What**: 80% of Canadian households have pets. Data on pet types, spending, demographics of owners.
- **URL**: https://cahi-icsa.ca/canadian-pet-population-survey
- **Persona use**: Pet ownership (lifestyle signal)

### Religion Data (Census 2021)
- **What**: 100+ religious options tracked. 53.3% Christian (declining), regional variations significant.
- **URL**: https://www12.statcan.gc.ca/census-recensement/2021/ref/98-500/016/98-500-x2021016-eng.cfm
- **Persona use**: Religious affiliation, religiosity level

### Transportation / Commute Mode Data
- **What**: Census and LFS data on commuting. 80.9% drive, 11.9% transit, 4.8% walk, 1.4% cycle. Strong regional variation.
- **URLs**:
  - https://censusmapper.ca/maps/3720
  - https://www150.statcan.gc.ca/n1/daily-quotidien/250826/dq250826a-eng.htm
- **Persona use**: Commute mode, urban vs. suburban lifestyle

---

## Summary: Priority Data Sources for Persona Enrichment

| Persona Attribute | Best Source(s) | Free? |
|---|---|---|
| Political leaning | CES, Angus Reid, Ipsos Dataverse | Yes |
| Values/worldview | World Values Survey, Environics Institute | Yes |
| Provincial identity | Confederation of Tomorrow | Yes |
| Health status | CCHS | Yes |
| Mental health | MHACS, CCHS | Yes |
| Digital behavior | CIUS, CIRA Internet Trends | Yes |
| Social media platforms | DataReportal, Social Media Lab | Yes |
| Media consumption | Vividata (paid), CRTC reports (free) | Mixed |
| Consumer lifestyle | PRIZM (paid), SHS (free) | Mixed |
| Financial stress | CSCE (Bank of Canada), CFCS | Yes |
| Housing concerns | CMHC | Yes |
| Civic engagement | GSS-GVP, Elections Canada, Samara | Yes |
| Volunteering | GSS-GVP | Yes |
| Time use / hobbies | GSS Time Use, Outdoor Activities | Yes |
| Spending patterns | SHS | Yes |
| Commute / transport | Census, LFS | Yes |
| **Income (occupation-based)** | **Job Bank 2025 wages + NOC mapping** | **Yes — actively used** |
| Religious affiliation | Census 2021 | Yes |
| Dietary habits | CCHS Nutrition | Yes |
| Disability | CSD | Yes |
| Regional attitudes | Reddit r/Canada dataset, CES, Environics | Yes |
| Psychographic segments | PRIZM (paid), Environics Social Values (paid) | No |
