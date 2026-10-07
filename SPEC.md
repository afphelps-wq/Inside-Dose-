# Inside Dose — Spec

> **For coding agents:** read §10 (Agent rules) first. Build one milestone (§9) at a time. If something isn't decided here, stop and ask; don't invent it.

## 1. Overview

**What it is:** A web service where a user enters a drug and sees how it interacts with the human body: its molecular structure, the proteins it targets, where those proteins are expressed across organs, and (for curated drugs) how the drug moves through and is cleared from the body.

**Context:** Class project for CMU 15-113. No course-imposed stack constraints.

**Audience:** General public. Plain-language explanations, minimal jargon.

**Timeline:** v1 due in under 4 weeks (before early November 2026).

**Core principles:**
- **Population average.** PK values are population averages from FDA labels. The only user-adjustable inputs are dose, dosing interval, and an illustrative body-weight slider (§6.2). No patient data is stored on the server; a user's saved drug list stays in their own browser.
- **No machine learning.** All content comes from published, measured data plus standard pharmacokinetic math.
- **Educational, not medical advice.** Clear disclaimer on every page.

**Drug coverage (hybrid model):**
- **Any drug (live lookup):** molecule, targets, and organ-level body map, pulled from structured public APIs.
- **Curated drugs (20 for v1, growing to 100 after the deadline):** additionally get the concentration curve, journey animation, and interaction checking, using hand-checked values from FDA labels.

**Risk:** Estimated ~60–65 h total for v1 (≈ 15–16 h/week under a 4-week deadline). Biggest items: curation (~25 h incl. effect categories), body map + journey animation (~12–15 h). The journey animation is the first thing to cut if time runs short.

## 2. Frontend

**Framework:** React + Vite, built to static files.
**Hosting:** GitHub Pages at `https://afphelps-wq.github.io/Inside-Dose-/` (repo `afphelps-wq/Inside-Dose-`; site base path `/Inside-Dose-/`). Static only; no secrets.

### 2.1 Design

- **Style:** Dark medical-scanner HUD, not a friendly illustrated look. Reference screenshots are in `UI examples/`. Near-black navy background; a translucent/wireframe human body is the central visual on Body/Molecule views, with a glowing highlight on whichever organ or system is active. Panels are thin hairline-bordered cards, optionally with corner brackets, over the dark background. Data is presented like instrumentation: small uppercase monospace labels, scale rulers, numeric readouts, circular gauges -- not flat icons. The chrome is sci-fi; the copy is not -- labels and explanations stay plain-language per the audience below (no military/alarming terms; use organ names and plain descriptions).
  - **Palette:** background `#05070f`/`#0a0e1a` (near-black navy); surface panels a lighter navy (`#10172a`-ish) with low-opacity borders; primary glow/accent cyan (`#22d3ee` range); secondary highlight warm amber (`#ff9d5c` range) used sparingly for emphasis against the cyan; body text off-white/pale blue-gray, not pure white.
  - **Severity colors** (interactions, §6.1) stay semantically distinct from the generic accent: major = red/orange, moderate = amber, minor = cyan/blue.
- **Devices:** Desktop only for v1.
- **Disclaimer:** "Educational, not medical advice" visible on every page.

### 2.2 Pages

| Page | Route | Contents |
|---|---|---|
| Home | `/` | Search bar with autocomplete + gallery of curated drugs |
| Drug | `/drug/:rxcui` | Tabs: **Molecule**, **Targets**, **Body**, **Journey** (Journey only for curated drugs) |
| My Drugs | `/my-drugs` | Saved list (up to 5 drugs) + interaction results |

Use hash routing (`/#/drug/...`) or a 404.html redirect so deep links work on GitHub Pages. _Agent: pick hash routing unless told otherwise._

### 2.3 Visualizations

| Tab | Visualization | Available for | Library |
|---|---|---|---|
| Molecule | Rotatable 3D structure + key properties (formula, weight) | Any drug | 3Dmol.js |
| Targets | Target list with plain-language function; 3D drug-in-target view when a PDB structure exists | Any drug | Mol* |
| Body | Rotatable 3D body with organs shaded by target expression level (§6.3) | Any drug | three.js |
| Journey | 3D body highlighting the active organ from the drug's `journey` steps + concentration-over-time curve (D3) | Curated only | three.js + D3 |

### 2.4 Inputs

- **Search:** autocomplete on brand and generic names (resolved via RxNorm). Results show both, e.g., "Lipitor (atorvastatin)."
- **My Drugs list:** add up to 5 drugs; stored in localStorage (wrap in try/catch; work without it).
- **Journey sliders:**
  - Dose: capped at the label's min/max for that drug.
  - Dosing interval: from the label's allowed intervals.
  - Body weight: 40–150 kg, default 70 kg. Labeled: "Shows how body size changes the curve. Not a dosing tool." Disabled (fixed) when the drug's Vd isn't given per kg.
  - Disclaimer shown next to the sliders.

## 3. Backend

### 3.1 Server

- **Framework:** Python 3.13 + FastAPI. Dependencies in `backend/requirements.txt`.
- **Hosting:** Render free web service.
  - Sleeps after 15 min idle; ~1 min to wake. Frontend shows a "Waking up the server…" state when a request takes >3 s.
  - Local filesystem resets on restart; never write persistent data to disk.
- **Database:** Postgres on Neon (free plan: no expiry, 1 GB). Used only for the API cache.
- **Curated data:** loaded into memory at startup from `data/drugs/*.json` (small; 100 files max). Not stored in Postgres.
- **No user accounts. No health data stored server-side.**

### 3.2 Environment variables

**Backend (Render dashboard; never committed):**

| Variable | Secret? | Value |
|---|---|---|
| `DATABASE_URL` | Yes | Neon connection string |
| `OPENFDA_API_KEY` | Yes | Free openFDA key |
| `ALLOWED_ORIGINS` | No | `https://afphelps-wq.github.io,http://localhost:5173` |
| `CACHE_TTL_DAYS` | No | `30` |

**Frontend (Vite build-time; public):**

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | Render backend URL, e.g. `https://inside-dose-api.onrender.com` |

- Nothing secret in any `VITE_` variable.
- Local dev: `.env` files (gitignored) + committed `.env.example` with blank values.

### 3.3 Database (Neon)

```sql
CREATE TABLE api_cache (
  source      TEXT NOT NULL,        -- 'rxnorm' | 'pubchem' | 'chembl' | 'pdb' | 'hpa' | 'openfda'
  cache_key   TEXT NOT NULL,        -- normalized request identifier
  response    JSONB NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (source, cache_key)
);
```

Entries older than `CACHE_TTL_DAYS` are refetched. If the refetch fails, serve the stale entry and mark the response `"stale": true`.

## 4. API contract

All responses are JSON. The canonical drug ID is the **RxNorm RxCUI** of the ingredient. Errors use:

```json
{ "error": { "code": "not_found", "message": "Plain-language message" } }
```

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{ "status": "ok" }` (used to wake the server) |
| GET | `/search?q=lip` | `[{ "rxcui", "generic", "brand", "curated": bool }]`, max 10 |
| GET | `/drugs/curated` | `[{ "rxcui", "id", "generic", "brands", "common_use" }]` for the gallery |
| GET | `/drugs/{rxcui}` | Drug bundle (below) |
| GET | `/drugs/{rxcui}/structure.sdf` | 3D SDF from PubChem (proxied) |
| GET | `/targets/{uniprot}/structures?rxcui=` | `[{ "pdb_id", "title", "has_this_drug": bool }]` |
| POST | `/interactions` | Body `{ "rxcuis": [..] }` (2–5) → interaction result (below) |

**Drug bundle:**

```json
{
  "rxcui": "…", "generic": "metoprolol", "brands": ["Lopressor"],
  "molecule": { "pubchem_cid": 0, "formula": "…", "weight": 0.0 },
  "targets": [{ "chembl_id": "…", "uniprot": "…", "gene": "ADRB1", "name": "…", "action": "antagonist", "plain_description": "…" }],
  "body_map": { "heart": { "level": "high", "basis": "protein", "targets": ["ADRB1"] } },
  "curated": null,
  "stale": false,
  "sources": [{ "name": "ChEMBL", "url": "…" }]
}
```

`curated` is the full curated drug record (§5.2) or `null`.

**Interaction result:**

```json
{
  "findings": [{
    "drugs": ["rxcuiA", "rxcuiB"],
    "type": "enzyme",
    "severity": "major",
    "mechanism": "Bupropion strongly inhibits CYP2D6, which clears metoprolol.",
    "plain_message": "Bupropion can raise metoprolol levels in the blood.",
    "sources": [{ "dailymed_setid": "…", "section": "7" }]
  }],
  "unchecked": ["rxcuiC"]
}
```

`unchecked` lists uncurated drugs, shown in the UI as "no data — not checked."

**Status codes:** 404 unknown drug, 422 bad input, 502 upstream API failed with no cache, 503 database unavailable.

## 5. Data

### 5.1 Live lookup (any drug, cached)

| Data | Source | Key needed? | Used in |
|---|---|---|---|
| Name resolution (brand ↔ generic, RxCUI) | RxNorm (NLM) | No | Search |
| 3D structure, formula, weight | PubChem PUG-REST (≤5 req/s) | No | Molecule |
| Targets, mechanism | ChEMBL | No | Targets, Body |
| Drug–target structures | RCSB PDB | No | Targets (Mol*) |
| Tissue protein + RNA expression | Human Protein Atlas (CC BY-SA; credit on site) | No | Body |
| Label dose range (fallback for uncurated) | openFDA (1,000/day without key; 120,000/day with) | **Yes, free** | Display only |

**Only one key to obtain:** openFDA, from open.fda.gov.

### 5.2 Curated drug records

- One JSON file per drug at `data/drugs/<id>.json`, validated against `data/schema/drug.schema.json` and a matching Pydantic model.
- Source: FDA labels via DailyMed. **Every value carries its unit and source.**
- **Formulation:** immediate release only for v1. Keep `formulations` as a list (one entry for now) so v2 can add more without a schema change.
- Store the label's **range** and the single **model** value used for the curve.

**Example (IDs are placeholders; values must be verified against the label):**

```json
{
  "id": "metoprolol",
  "names": { "generic": "metoprolol", "brands": ["Lopressor"] },
  "ids": { "rxcui": "<lookup>", "chembl": "<lookup>", "pubchem_cid": "<lookup>" },
  "common_use": "Blood pressure / heart rate",
  "formulations": [{
    "id": "tartrate_ir",
    "label": "Metoprolol tartrate (immediate release)",
    "route": "oral",
    "dose_mg": { "min": 25, "max": 450, "typical": 50, "intervals_h": [12],
                 "source": { "dailymed_setid": "<lookup>", "section": "2" } },
    "pk": {
      "bioavailability": { "range": [0.4, 0.5], "model": 0.5, "unit": "fraction", "source": {} },
      "half_life":       { "range": [3, 7],     "model": 5,   "unit": "h",        "source": {} },
      "vd":              { "range": [3.2, 5.6], "model": 4.2, "unit": "L/kg",     "source": {} },
      "tmax":            { "range": [1, 2],     "model": 1.5, "unit": "h",        "source": {} }
    }
  }],
  "enzymes": [{ "name": "CYP2D6", "role": "substrate", "importance": "major", "source": {} }],
  "transporters": [],
  "effects": [{ "category": "lowers_blood_pressure", "source": {} }],
  "elimination": { "routes": [{ "route": "kidney", "fraction": 0.95, "unchanged_fraction": 0.05 }], "source": {} },
  "journey": [
    { "step": "absorption",  "organ": "intestines", "text": "Absorbed quickly from the gut." },
    { "step": "metabolism",  "organ": "liver",      "text": "Broken down mainly by the CYP2D6 enzyme." },
    { "step": "action",      "organ": "heart",      "text": "Slows the heart and lowers its workload." },
    { "step": "elimination", "organ": "kidneys",    "text": "Leaves the body in urine, mostly as broken-down pieces." }
  ],
  "curation": { "reviewed_by": "Anabella Phelps", "reviewed_on": "YYYY-MM-DD", "status": "draft" }
}
```

**Vocabularies (closed lists; the validator rejects anything else):**

- `enzymes[].role`: `substrate` | `inhibitor` | `inducer`
- `enzymes[].strength` (required for inhibitor/inducer): `strong` | `moderate` | `weak`
- `enzymes[].importance` (required for substrate): `major` | `minor`
- `vd.unit`: `L/kg` | `L`
- `elimination.routes[].route`: `kidney` | `bile` | `other`
- `journey[].step`: `absorption` | `distribution` | `metabolism` | `action` | `elimination`
- `journey[].organ` and body-map keys: the 15 organs in §6.3
- `effects[].category`: `anticoagulant`, `bleeding_risk`, `serotonergic`, `lowers_blood_pressure`, `raises_potassium`, `nsaid`, `lowers_seizure_threshold`, `sedation`. Add new categories only by editing this list.

`curation.status`: `draft` | `verified`. Only `verified` drugs appear in the gallery and interaction checks.

### 5.3 v1 curated drug list

Selection: most-prescribed US drugs (ClinCalc DrugStats, 2024, from MEPS), with these changes:
- **Removed** (break the oral PK model): albuterol (#6, inhaled), semaglutide (#14, injection), levothyroxine (#2, replaces a hormone the body already makes).
- **Added** two over-the-counter drugs: acetaminophen, ibuprofen.
- **Swapped** trazodone (#20) for apixaban (#25), a blood thinner.

| # | Drug | US Rx rank | Common use |
|---|---|---|---|
| 1 | Atorvastatin | 1 | Cholesterol |
| 2 | Metformin | 3 | Type 2 diabetes |
| 3 | Amlodipine | 4 | Blood pressure |
| 4 | Lisinopril | 5 | Blood pressure |
| 5 | Losartan | 7 | Blood pressure |
| 6 | Metoprolol (tartrate IR) | 8 | Blood pressure / heart rate |
| 7 | Rosuvastatin | 9 | Cholesterol |
| 8 | Omeprazole | 10 | Acid reflux |
| 9 | Gabapentin | 11 | Nerve pain / seizures |
| 10 | Sertraline | 12 | Depression / anxiety |
| 11 | Escitalopram | 13 | Depression / anxiety |
| 12 | Amphetamine mixed salts (IR) | 15 | ADHD |
| 13 | Pantoprazole | 16 | Acid reflux |
| 14 | Bupropion (IR) | 17 | Depression / smoking cessation |
| 15 | Hydrochlorothiazide | 18 | Blood pressure (diuretic) |
| 16 | Fluoxetine | 19 | Depression |
| 17 | Apixaban | 25 | Blood thinner |
| 18 | Montelukast | 21 | Asthma / allergies |
| 19 | Acetaminophen | OTC | Pain / fever |
| 20 | Ibuprofen | OTC | Pain / inflammation |

**Interaction demo pairs** (verify against labels):
- Bupropion or fluoxetine + metoprolol: CYP2D6 inhibition (enzyme).
- Omeprazole + escitalopram: CYP2C19 inhibition (enzyme).
- Apixaban + ibuprofen or an SSRI: added bleeding risk (effect).

### 5.4 Phased expansion

- **v2 (after the deadline):** grow to 100 curated drugs (~80 h curation). Same schema; adding a drug means adding a file.
- Selection rules for drugs #21–100: _not decided._

### 5.5 Static assets

- **Body model:** a 3D model (BodyParts3D 4.0, CC BY 4.0, via DBCLS), trimmed from ashemag/human-atlas's packaged geometry (MIT) to one merged mesh per organ. 13 of the 15 organ keys are covered; BodyParts3D has no thyroid or fat/adipose mesh at all, so those two have no 3D visual (confirmed by exhaustive search, not a naming gap). Built by `backend/scripts/extract_anatomy.py` into `frontend/public/anatomy/organs.json` + `organs.bin.gz`; license and full adaptation notes in `frontend/src/assets/CREDITS.md`.
- **Tissue map:** `data/hpa_tissue_map.json` maps Human Protein Atlas tissue names → organ keys.

## 6. Logic

### 6.1 Interaction rules

Checked for every pair among the user's verified curated drugs. Uncurated or draft drugs go in `unchecked`.

**Enzyme/transporter rule:** if drug A is an `inhibitor` or `inducer` of enzyme E, and drug B is a `substrate` of E:

| A's strength | B importance = major | B importance = minor |
|---|---|---|
| strong | major | moderate |
| moderate | moderate | minor |
| weak | minor | minor |

Check both directions (A→B and B→A). Transporters use the same rule.

**Effect rule:** pair rules live in `data/rules/effect_pairs.json`. Proposed v1 rules (Anabella to confirm severities during curation):

| Category A | Category B | Severity | Plain message |
|---|---|---|---|
| anticoagulant | bleeding_risk | major | Together these can raise the risk of bleeding. |
| anticoagulant | nsaid | major | Together these can raise the risk of bleeding. |
| bleeding_risk | bleeding_risk | moderate | Both can make bleeding more likely. |
| serotonergic | serotonergic | moderate | Both raise serotonin; together this can cause side effects. |
| raises_potassium | raises_potassium | moderate | Both can raise potassium levels. |
| nsaid | lowers_blood_pressure | moderate | Ibuprofen-type drugs can weaken blood pressure medicines. |
| lowers_seizure_threshold | lowers_seizure_threshold | moderate | Both can make seizures more likely. |
| lowers_blood_pressure | lowers_blood_pressure | minor | Blood pressure can drop more than with either alone. |
| sedation | sedation | moderate | Both can cause drowsiness. |

If a pair matches several rules, report each finding separately. Sort findings by severity.

### 6.2 PK model (runs in the browser)

One-compartment model, first-order oral absorption, first-order elimination.

- `ke = ln(2) / half_life`
- `V = vd × weight_kg` if `vd.unit == "L/kg"`, else `V = vd` (weight slider disabled)
- `ka` is solved numerically from `tmax = ln(ka/ke) / (ka − ke)`, requiring `ka > ke`. If there's no solution, use `ka = 10 × ke` and log a warning.
- Single dose: `C(t) = (F·D·ka) / (V·(ka − ke)) · (e^(−ke·t) − e^(−ka·t))`, in mg/L
- Repeated dosing every τ hours: sum single-dose curves shifted by `n·τ` (superposition)
- Time window: `max(24 h, 5 × half_life)`, capped at 7 days; sample every 0.1 h
- Chart labels: "Estimated blood level (population average)", with units shown
- Unit tests compare output to hand-calculated values for 2 drugs.

### 6.3 Body map

**Organs (15 keys):** `brain`, `heart`, `lungs`, `liver`, `stomach`, `intestines`, `kidneys`, `pancreas`, `blood_vessels`, `muscle`, `skin`, `fat`, `thyroid`, `spleen`, `bladder`.

- For each target, take its Human Protein Atlas tissue data and map tissues → organs with `hpa_tissue_map.json`.
- If an organ has several tissues or targets, use the **highest** level.
- **Shading:** High = darkest, Medium = mid, Low = light, Not detected = none.
- **RNA fallback:** if a target has no protein data, use its RNA level, binned into the same 3 levels. RNA-based organs render at reduced opacity rather than a solid fill; the legend explains the difference.
- Clicking an organ lists which targets drove its shading and what each one does.

**Data-source caveat (discovered building M7, Oct 2026):** the spec above assumes HPA still publishes its old categorical "High / Medium / Low / Not detected" table per tissue. It doesn't anymore -- checked exhaustively against both the live search API and the full `proteinatlas.tsv` bulk download, neither has it. What HPA publishes now is a numeric "specific" value per tissue (`Protein tissue specific Intensity` / `RNA tissue specific nTPM`), and only for the handful of tissues where a gene is notably enriched -- not a full per-tissue readout. `backend/app/services/hpa.py` adapts: ranks a gene's own listed tissues against each other and bins the top/middle/bottom third into high/medium/low (single or paired values bin high/[high,medium] instead of thirds). Protein data wins when present; RNA is the fallback, exactly as originally specified. The real limitation this introduces: a tissue HPA doesn't list for a gene reads as "not detected" here, which conflates *truly absent* with *not one of that gene's standout tissues* -- an organ can go unshaded even where the target is genuinely present at an unremarkable baseline level. `data/hpa_tissue_map.json` only covers the HPA tissue names actually observed in their data; no tissue in HPA's "specific" columns maps to `spleen`, so that organ key never gets body_map data from this source.

## 7. Error and empty states

| Situation | Behavior |
|---|---|
| Server asleep | "Waking up the server…" with spinner after 3 s; retry `/health` until ready |
| Drug not found | "We couldn't find that drug." + suggestions from search |
| Upstream API down, cache available | Show cached data + "Data may be out of date" note |
| Upstream API down, no cache | That tab shows "Couldn't load this right now" + retry; other tabs still work |
| No 3D structure | Molecule tab shows 2D image instead |
| No PDB structure | Targets tab shows the list only, no 3D view |
| No targets in ChEMBL | Body and Targets tabs: "No known protein targets recorded." |
| Uncurated drug | Journey tab hidden; badge "Basic info only" |
| localStorage unavailable | My Drugs works for the session only; note shown |

## 8. Repo and deployment

```
inside-dose/
  SPEC.md
  frontend/                 React + Vite
  backend/
    app/                    FastAPI (main.py, routers/, services/, models.py)
    tests/
    requirements.txt
  data/
    schema/drug.schema.json
    drugs/*.json
    rules/effect_pairs.json
    hpa_tissue_map.json
  .github/workflows/
    deploy-frontend.yml     build frontend → GitHub Pages on push to main
    test.yml                pytest + validate data/ on every push
```

- **Frontend deploy:** GitHub Action builds with `VITE_API_BASE_URL` from a repo variable and publishes to Pages.
- **Backend deploy (Render):** root = repo root (so `data/` is available).
  - Build: `pip install -r backend/requirements.txt`
  - Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Tests:** pytest for the PK math, interaction rules, schema validation of every file in `data/drugs/`, and API endpoints (with mocked upstream calls).

## 9. Milestones

Build in order. Each is done only when its check passes.

| # | Milestone | Done when |
|---|---|---|
| M0 | Scaffold + deploy | Frontend live on Pages calls backend `/health` on Render successfully (CORS works) |
| M1 | Data schema + validator | Schema, Pydantic model, vocabularies, and tests exist; 3 hand-curated drugs pass (metoprolol, apixaban, ibuprofen) |
| M2 | Curated API + interactions | `/drugs/curated`, `/drugs/{rxcui}` (curated part), `/interactions` work; rule tests pass for the 3 demo pairs |
| M3 | Home + Drug page shell + Molecule tab | Gallery, tab layout, and 3D molecule render for curated drugs |
| M4 | Journey tab | PK curve matches hand calculations; sliders respect label limits; journey steps animate |
| M5 | My Drugs page | Add/remove up to 5 drugs, persisted in localStorage; interaction findings display by severity |
| M6 | Live lookup + cache | Search via RxNorm; any drug's bundle loads from PubChem/ChEMBL; cache hits on repeat |
| M7 | Body map | 15-organ SVG shaded per §6.3, RNA fallback hatched, organ click details |
| M8 | Targets tab | Target list + Mol* view where PDB structures exist |
| M9 | Remaining 17 drugs + polish | All 20 drugs `verified`; disclaimers, credits, and error states in place |

## 10. Agent rules

1. **Never invent drug data.** PK values, enzyme roles, effect categories, doses, and journey text come only from files Anabella curates. If a value is missing, leave it out and flag it; don't fill it in from memory.
2. Build one milestone at a time; stop for review after each.
3. If the spec doesn't decide something, ask. Don't guess.
4. No secrets in frontend code or any `VITE_` variable.
5. Every external API call goes through the backend cache.
6. Keep the closed vocabularies closed; adding a category means editing §5.2 first.

## 11. Open questions (non-blocking)

- Selection rules for v2 drugs #21–100.
- Final severities in the effect rules table (§6.1), confirmed during curation.
