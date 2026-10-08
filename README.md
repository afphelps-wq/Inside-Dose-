# Inside Dose

User can type in a drug name and see what it actually does inside your body: what the molecule looks like, which proteins it binds to, which organs those proteins are present in, and (for a set of hand-checked drugs) how the drug moves through you over hours and days.

Drug modelling has always been something I've been interested in. I recently went to a conference where a PhD candidate was postering their research on a predictive model for drug/molecule binding affinity. This is where I got the idea to make a user friendly interface to allows the public to better understand the effects of medications they may be taking and how it actually works in their body. With the popularity of non-FDA approved medications/supplements on social media as of late, I wanted to be able to make a web service that educates people on the interactions that are taking place in their body. 

> This is all purely educational and not meant to be medical advice. 

## What it does

There are two tiers of drugs that I encorparted. 

**Any drug (live lookup).** Search by brand or generic name and you get:
- **Molecule:** a rotatable 3D structure with formula and molecular weight.
- **Targets:** the proteins the drug binds, with plain-language descriptions, plus a 3D view of the drug sitting in its target when a solved structure exists.
- **Body:** a rotatable 3D body with organs shaded by how much of the drug's target protein is found there.

**Curated drugs (20 for v1).** These also get:
- **Journey:** a concentration-over-time curve you can play with (dose, dosing interval, body weight) alongside a 3D body highlighting the organ the drug is passing through at each step.
- **Interaction checking:** save up to 5 drugs on the My Drugs page and see which pairs may interact, with severity colors (major / moderate / minor).

The curated 20 are acetaminophen, amlodipine, amphetamine, apixaban, atorvastatin, bupropion, escitalopram, fluoxetine, gabapentin, hydrochlorothiazide, ibuprofen, lisinopril, losartan, metformin, metoprolol, montelukast, omeprazole, pantoprazole, rosuvastatin, and sertraline.

I chose these curated 20 to be the most popular medications in the United States. 

## How to use it

1. Open the home page and search a drug, or click one from the curated gallery.
2. Flip through the tabs on the drug page. Drag to rotate any 3D view.
3. On curated drugs, open **Journey** and move the sliders. The weight slider only shows how body size changes the curve.
4. Hit the light/dark toggle in the corner, or switch the body model between male and female anatomy.
5. Save drugs to **My Drugs** (stored in your own browser's localStorage, never on a server) to check them against each other.


## Features I'm most proud of

- **The 3D body.** The male anatomy comes from BodyParts3D, and since that dataset has no female model, I created a script that merges the HuBMAP Human Reference Atlas female organs into the same format so the toggle works. Getting 15-ish organs to render smoothly in the browser (merged, decimated, gzipped) took a lot of fiddling.
- **The body map** I encorparated the data available in the Human Protein Atlas to showcase protein structure that the drugs bing to. Organ shading comes from Human Protein Atlas tissue expression, sorted into high / medium / low.
- **Curve map.** Curve math is standard pharmacokinetics running in the browser; everything else is published data.
- **data gathering.** Every curated value is from to a cited source (FDA label sections, PubChem, ChEMBL)
- **Interactions.** Adding drugs to My Drugs will flag any interactions that the drugs may have and give them a warning of low, medium, and high. 
## Running it locally

You'll need Python 3.13 and Node 22.

**Backend**

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env     # fill in values, see below
cd ..
uvicorn backend.app.main:app --reload
```

The API runs on `http://localhost:8000` (try `/health`). Curated drug JSON in `data/drugs/` is loaded into memory at startup.

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env     # set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

**Tests**

```bash
pytest backend
python -m backend.app.validate_data   # checks every curated drug against the JSON schema
cd frontend && npm test
```

## How secrets are handled

- Real values live only in gitignored `.env` files locally and in the Render dashboard in production. Only `backend/.env.example` (blank values) is committed.
- Backend variables: `DATABASE_URL` (Neon Postgres connection string, **secret**), `OPENFDA_API_KEY` (**secret**), `ALLOWED_ORIGINS` (CORS list), and `CACHE_TTL_DAYS` (default 30).
- The frontend is a static site on GitHub Pages, so it can't hold secrets. Its only variable, `VITE_API_BASE_URL`, is the public backend URL. Nothing secret ever goes in a `VITE_` variable.
- If `DATABASE_URL` is not set, the app still runs, it just skips the cache.
- The database holds only a cache of public API responses. There are no accounts and no health data on the server.

## Stack

React + Vite, three.js, 3Dmol.js, Mol\*, and D3 on the front end. FastAPI on the back end, with Postgres (Neon) as a cache. Data comes from RxNorm, PubChem, ChEMBL, RCSB PDB, the Human Protein Atlas, and DailyMed/FDA labels. Frontend deploys to GitHub Pages and the API to Render; CI runs the tests on every push.

## How I used AI

I built this with Claude Code (Claude Opus and Sonnet), working step by step from `SPEC.md` that I created in conjunction with Claude Opus in planning mode. Claude wrote most of the code, helped me curate the drug records from FDA labels, and handled debugging and a full codebase review against the spec. I made the design decisions, wrote the spec, brought in the UI mockups from Claude Design, and reviewed and redirected the output. 

Where AI was wrong: 
When making creating and designing the 3D body, it kept confidently delivering a 2D blob looking body. I would specify with images and it would still confidently deliver this. So, I searched through GitHub to see if other people have open source code for a 3D rendering of a body with anatomy. I then used this code to create the body rendering and then also create the female version with the help of AI. 

- Curated PK values were gathered with AI help and then re-checked by a second AI pass against the cited sources. That is **not** a clinical review.
- The 3D anatomy was extracted and processed with AI-written scripts (`backend/scripts/`).

## Credits and citations

- **BodyParts3D** (male anatomy), © The Database Center for Life Science, CC BY 4.0. Mitsuhashi et al. (2009), *BodyParts3D: 3D structure database for anatomical concepts*, Nucleic Acids Research. https://doi.org/10.1093/nar/gkn613
- **ashemag/human-atlas** (MIT), whose repackaged BodyParts3D geometry I extracted organs from. https://github.com/ashemag/human-atlas
- **HuBMAP Human Reference Atlas, 3D Reference Organ Set for Female** (Visible Human Female, NLM), CC BY 4.0. https://humanatlas.io/3d-reference-library
- **Mol\*** protein viewer (MIT). https://molstar.org
- **Human Protein Atlas** for tissue expression, **ChEMBL**, **PubChem**, **RxNorm**, **RCSB PDB**, **openFDA**, and **DailyMed** for the underlying drug data.

Full attribution details are in [`frontend/src/assets/CREDITS.md`](frontend/src/assets/CREDITS.md).
