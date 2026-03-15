# Ask Canada — Implementation Next Steps

Reference project: `ask-singapore/` (cloned)
Learning doc: `Learning.md`

---

## Phase 1: Canadian Persona Generation (Python)
> This is the critical path — everything else depends on having persona data

- [ ] **1a. Gather Statistics Canada demographic distributions**
  - Province/territory population proportions
  - Age distributions by province
  - Occupation categories (NOC codes) + distribution
  - Education level distributions
  - Income brackets by region
  - Immigration status proportions
  - Visible minority / Indigenous identity distributions
  - Language (English/French/bilingual) by province

- [ ] **1b. Design the Canadian persona schema**
  Adapt from Nemotron's 12 fields to Canadian context:
  ```
  uuid, age, sex, occupation, education_level, marital_status,
  region (province + city/CMA), persona (summary),
  cultural_background, skills_and_expertise,
  hobbies_and_interests, career_goals_and_ambitions,
  immigration_status, languages_spoken
  ```

- [ ] **1c. Build `scripts/generate_canada_personas.py`**
  - Use census distributions as sampling weights
  - Generate 5,000-10,000 personas via LLM (Claude API)
  - Stratified by province/region to ensure geographic coverage
  - Output: `public/data/personas.canada.v1.json`

---

## Phase 2: Canadian Geographic Data

- [ ] **2a. Get Canadian GeoJSON boundaries**
  - Statistics Canada Census boundaries (provinces, CMAs, or census subdivisions)
  - Choose granularity: provinces (13) vs CMAs (~35) vs census subdivisions (5,000+)
  - Recommended: Start with CMAs + provinces for non-CMA areas (~50 regions, similar to Singapore's 55)

- [ ] **2b. Build Canadian area profiles**
  - Create `scripts/prepare_canada_area_profiles.py`
  - Source: Statistics Canada census profiles, CMHC housing data, municipal open data
  - Fields: population, dominant age group, visible minority %, dwelling types, median income, median home price, transit mode, amenity counts

---

## Phase 3: Adapt the Codebase

- [ ] **3a. Fork/copy the ask-singapore codebase as ask-canada**
  - Rename project, update package.json, branding
  - Add attribution to Aayush Mathur in footer/about

- [ ] **3b. Replace data files**
  - `personas.compact.v1.json` -> `personas.canada.v1.json`
  - `area-profiles.json` -> Canadian area profiles
  - `singapore-subzone-no-sea.geojson` -> Canadian boundaries GeoJSON

- [ ] **3c. Update schemas and types**
  - `planning_area` -> `region` throughout codebase
  - Update `PersonaSchema` for Canadian fields
  - Update `AreaProfileSchema` for Canadian metrics

- [ ] **3d. Update map component**
  - Center: Canada (lat ~56, lng ~-106, zoom ~3) or specific province
  - GeoJSON property key for region matching
  - Adjust zoom/bounds for Canadian geography

- [ ] **3e. Update LLM prompt**
  - "persona from Canada" instead of "Singapore"
  - Canadian neighborhood context
  - Canadian-relevant suggested questions

- [ ] **3f. Update UI**
  - Branding: "Ask Canada"
  - Suggested questions (e.g., "Should Canada invest more in public transit?", "How do you feel about housing affordability?")
  - Attribution footer crediting Aayush Mathur's Ask Singapore

---

## Phase 4: Test & Deploy

- [ ] **4a. Test with small sample** (50 personas, 1 LLM provider)
- [ ] **4b. Validate geographic coverage** on map
- [ ] **4c. Deploy to Vercel**

---

## Decisions to Make

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Geographic granularity | Provinces (13), CMAs (~35), FSAs (1,600+) | CMAs + provincial remainders ~ 50 regions |
| Scope | All of Canada vs one province first | Start with all Canada at CMA level |
| LLM provider for personas | Claude, Gemini, OpenAI | Claude API (best for structured persona generation) |
| Persona count | 5K (fast/cheap) vs 10K+ (richer) | 5K to start, scale up later |
| LLM provider for runtime | Same multi-provider as Singapore | Keep multi-provider, same approach |

---

## What We Can Reuse As-Is from Ask Singapore

- Next.js project structure and build config
- LLM orchestration (`gemini.ts` — retries, fallbacks, structured output)
- Sampling strategy (`sampling.ts` — stratified sampling)
- Sentiment aggregation (`sentiment.ts`)
- Rate limiting, Zod validation patterns
- Convex persistence layer
- shadcn/ui components
- Model catalog pattern

## What Must Be Built New

1. **Canadian persona generator** (Python script using census data + LLM)
2. **Canadian GeoJSON** (download from Statistics Canada)
3. **Canadian area profiles** (Python script using StatCan/CMHC APIs)
4. All Singapore-specific strings, coordinates, and data references