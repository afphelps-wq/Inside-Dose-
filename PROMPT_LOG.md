# Prompt Log

A chronological log of the prompts given to Claude (Claude Code) across the development
of Inside Dose

## Planning Prompt
A. "I'm trying to brainstorm a webservice that uses front end and backend and apis and data visualization. My initial Idea is to train a model on the open source patient transcriptome and proteasome data and drug compounds to train it to understand and predict how a drug will interact with the proteasome. Then I want to create a consumer web service that allows you to input the drugs you are taking, visualize it as a chemical compound/ molecule, visualize how it interacts and metabolizes through your body using the predictive model"

B. "I do mean proteome, I don't want it to be personalized I just want to show the population average but make a web service that is easy to navigate and showcase visually how the drug is interacting with your body."

C. Planning — writing SPEC.md
"create a spec.md with information about this project from our brainstorming. Create a frontend(design, visualization, inputs), backend(server, environment variables, etc), API keys needed, data needed sections. Ask me questions as you create. Don't assume anything! Ask before filling in any section."
(choices, overview) Audience: "General public" · Purpose: "Class project" · v1 scope: "Any drug (live lookup)" · Name: "Not yet, placeholder"
(choices, scope) Live lookup gaps: "Hybrid (Recommended)" · Class: "15-113" · Deadline: "< 4 weeks" · Course constraints: "No constraints"
(choices, frontend) Curated set: "~20" · Framework: "should work on github pages" · Style: "Friendly illustrated" · Devices: "Desktop only"
(choices, hosting) Backend: "Separate backend" · Framework: "React + Vite"
(choices, features) Visuals: "3D molecule viewer, Target proteins, Body map, Journey + PK curve" · Interactions: "Yes, up to ~5" · Input: "Search + browse" · Dose input: "Yes, sliders"
(choices, feature details) Interaction scope: "Show 'no data' for others" · Slider limits: "Labeled range only" · Layout: "Single drug page, tabs" · Protein 3D: "Yes, when PDB structure exists"
(choices, backend) Host: "Render (free tier)" · Server: "Python + FastAPI" · Duties: all four selected + "allow a user to log in and save their drug list or add to their list" · Storage: "Postgres (hosted)"
(choices, backend risks) Login: "Save in browser only" · Render limits: "Different Postgres host"
(choices, backend details) Postgres: "Neon (Recommended)" · PK compute: "Browser" · Cold start: "Loading message"
(choices, data) Sources: "ChEMBL + PubChem, Human Protein Atlas, RCSB PDB, RxNorm + openFDA" · openFDA key: "Yes" · Curation: "FDA labels (DailyMed)" · Repo: "Not decided"
Planning — name and curated drug list
"project name brainstorm"
"use Inside Dose in the spec"
"make the 20 curated list, a list of the most commonly used drugs"
(choices, drug list) Non-oral drugs: "Swap them (Recommended)" · OTC: "Yes, add 2 OTC"
"bring apixaban back"
"I want to make it so that the curated drug list is 100 actully"
"20 drugs for the class deadline, then grow to 100 afterward. The data format stays the same, so nothing has to be rebuilt."
"how should I format the data best?"
Planning — making the spec agent-ready
"before I move to using vs code. is the spec ready for a coding agent to understand what to do?"
"work through these now"
(choices, blocking decisions) Repo: "inside-dose" · Effect-based interactions: "Yes, both" · Formulation: "Immediate release only" · Checker location: "Own page"
(choices, visuals and data) Body SVG: "Openly licensed SVG" · Body weight: "Weight slider" · Expression: "Shaded by level" · Cache TTL: "30 days"
(choices, final details) Weight slider: "Keep, labeled illustrative" · Organs: "Core 8, + Blood vessels, + Muscle, skin, fat, + Thyroid, spleen, bladder" · Severity: "3 levels" · Protein fallback: "Fall back to RNA"
"should i add any connectors or extensions to claude or vs before this"

## Session start / recovery

1. "read SPEC.md, also read all the files and find out where I left off and what errors
   there are, I had to restart unexpectedly"

## Curation (M1 data)

2. "fill metoprolol.json using same sources as the other durg jsons"
3. [pasted a table of 5 drug files mid-curation, missing required PK fields] "try and fix
   these prblems by searching in the sources"
4. (choice, bupropion bioavailability) "Use animal data, heavily caveated"
5. (choice, amphetamine bioavailability) "Use the ~90% tertiary figure, caveated"
6. "commit. Then read spec.md and figure out what the next step is"

## M2 — Curated API + interactions

7. "build M2 against the draft
8. "yes push"
9. Render deployed-- made sure everything synched correctly

## M3/M4 — Home, Drug page, Molecule tab, Journey tab

12. "yes, commit and start M4"
13. "fix the regression in M3 also change the UI of the body and journey models to look
    like the UI examples in the folder UI examples"
14. "All the content should be a placeholder. The drug content has not been verified yet."
15. "https://github.com/ashemag/human-atlas use this github to make the body I want them
    to be 3D and similar detail. Omit muscles and skin from the 3D view.
17. Help me debug this 3D rendering
18. Resize rendering for front end deployment so it is the main focus of the front page. 

## M5/M6 — My Drugs page, live lookup + cache

19. "Complete M5 and do M6"
20. "how do I set up the Neon database"
21. [explicit Neon CLI setup instructions, run verbatim]:
    ```
    1. npm i -g neon@latest && neon login
    2. neon skills -y
    3. neon mcp -y
    4. neon link --project-id small-glitter-06265713 --branch production -y
    5. neon config init
    6. Update neon.ts:
       import { defineConfig } from "@neon/config/v1";
       export default defineConfig({});
    ```
22. "Fetch the Neon skill from https://neon.com/.well-known/agent-skills/neon/SKILL.md
    and follow its instructions. Check whether Neon agent skills and the Neon MCP server
    are already installed for this project, install anything missing, preserve my
    existing configuration, and summarize every change you make."
23. (choice, Neon tooling artifacts) "git ignored"
24. "yes, commit and start M6"
25. "fix the synch to the chemPUB lookup. All the lookups only have basic information?"

## M7 — Body map (Human Protein Atlas)

26. "ok time to incorparate the protein atlas, for m7"
27. (choice, HPA data adaptation) "Bin the numeric data into 3 levels myself"

## M8 — Targets tab (Mol* viewer)

29. "start on M8, ask me any clarifying questions first"

## M9 — All drugs verified, gating, polish

31. (choice, what "verified" should mean) "Redefine 'verified' as AI cross-checked"

## Full codebase review

32. "go through all the code and look for issues or deviations from the spec, make a
    list of concerns from critical, warning, med priority, low priority"

## Performance

33. "how do I make the lookups and data loading faster. Check the pooling in the render"
34. "commit and push"

## Prompt log

35. "create a prompt log of this chat"

## Front-end redesign session

36. `source /Users/anabellaphelps/Documents/GitHub/Inside-Dose-/backend/.venv/bin/activate`
37. "I want to work on front end design, I designed how I want the webpage to look in
    claude design mode l the journey tab for each drug like this file in the folder UI
    examples, the html file. Inspect it and use that as a model"
38. "start the dev server"
39. "- extend so that it takes up the entire width of the screen right (do this for all
    pages),- make the body model 3x bigger."
40. "it says the site can't be reached"
41. "- the body is now cut off, take a screen shot of this so you understnad and then fix
    it so you minimize the empty space as much as possible"
42. "fix the body tab as well"
43. "combine the targest and body onto the same page so they are side by side"
44. "make it so the full screen button on the protein models allows you to actually full
    scfreen the proteins and not the site"

## Home page redesign, light/dark theme

45. "inspect and look at the new folder inside UI examples there is an html file and
    other files that are the new design, update the home page to that in light mode and
    then also create a dark mode version of that design. Create a toggel button."
46. "extend the toggle so it effects all other pages and also match the theme and fonts
    of the home page to the other pages"
47. "whenever I add to my drugs, the 0/5 doesn't update"

## Female body model

48. "debug my code for a female version of the body that you can toggle, since right now there is
    only male anatomy deployed"

I brainstormed with Claude Opus in planning mode and we wrote SPEC.md together, which then became the roadmap I used to build everything step by step in Claude Code (Opus and Sonnet). Claude Code wrote most of the front end (React, Vite, and three.js for the 3D body) and the FastAPI backend, and I set up the Neon MCP server and skills in it so it could help with the Postgres cache. For the look of the site, I designed the Journey tab and the new home page in Claude Design and then had Claude Code rebuild those mockups in the actual app, in both light and dark mode. The data side was mostly public sources: DailyMed/FDA labels for the curated drug values, RxNorm and PubChem for lookups, ChEMBL for targets, RCSB PDB and Mol* for the protein structures, 3Dmol.js for the molecules, and the Human Protein Atlas for the body map. For the 3D anatomy, AI kept giving me a flat blob, so I went and found open-source anatomy on GitHub (BodyParts3D by way of human-atlas) and the HuBMAP Human Reference Atlas for the female body, and used AI-written scripts to merge and shrink them for the browser. To check things, I had Claude look at the running site in Chrome and take screenshots so we could fix cut-off and overlapping layouts, and a second AI pass re-checked the drug values against their cited sources (which is not a clinical review). Everything is hosted for free: GitHub Pages and Actions for the front end, Render for the API, and Neon for the database.

For the 3x body, AI set the viewer to 1260px tall and said it was done without looking at it. In the browser it was a 181px-wide strip running off the bottom of the screen. I had to tell it the body was cut off. After that I had to make it fit the window, then fixed the empty space around it, then made it fill its panel. The female model was first reported working, but the skin was rendering as scattered specks. The mesh vertices weren't welded, so the simplifier shredded the mesh. I debugged with AI to fix it. When the body looked small in a screenshot that I sent AI, it spent a lot of time on camera framing. The cause was that the skin and legs were too faint in dark mode. A bug AI introduced was the 0/5 count not updating. It added a  header count with its own separate copy of the saved list.

