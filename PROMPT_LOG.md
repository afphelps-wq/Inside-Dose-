# Prompt Log

A chronological log of the prompts given to Claude (Claude Code) across the development
of Inside Dose, for a single continuous working session (interrupted once by an
unplanned restart, noted below). Tool calls, file reads, and Claude's own responses are
omitted; this lists what the user actually asked for, in order.

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

7. "build M2 against the draft"
8. "is it pushed to github?"
9. "yes push"
10. "I can't figure out why its not working"
11. "ok render deployed, how do I view the web page"

## M3/M4 — Home, Drug page, Molecule tab, Journey tab

12. "yes, commit and start M4"
13. "fix the regression in M3 also change the UI of the body and journey models to look
    like the UI examples in the folder UI examples"
14. "is all the content still placeholder content or can it be verified?"
15. "https://github.com/ashemag/human-atlas use this github to make the body I want them
    to be 3D and similar detail"
16. (choice, two answers in one response) "Just omit them from the 3D view" / "Yes,
    proceed"
17. "I don't hink the 3D rendering is working"
18. "ok now what is the next step"

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
25. "why does all the lookups only have basic information?"

## M7 — Body map (Human Protein Atlas)

26. "ok time to incorparate the protein atlas, for m7"
27. (choice, HPA data adaptation) "Bin the numeric data into 3 levels myself"
28. "what does this mean A 3D view of the drug inside its target (Mol*) goes here when a
    structure exists."

## M8 — Targets tab (Mol* viewer)

29. "do M8"

*(Session interrupted here by a context-window compaction; resumed automatically with
full context preserved.)*

30. "ok what is the next step"

## M9 — All drugs verified, gating, polish

31. (choice, what "verified" should mean) "Redefine 'verified' as AI cross-checked"

## Full codebase review

32. "go through all the code and look for issues or deviations from the spec, make a
    list of concerns from critical, warning, med priority, low priority"

## Performance

33. "how do I make the lookups and data loading faster"
34. "commit and push"

## This log

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

48. "make a female version of the body thata you can toggle, since right now there is
    only male anatomy"

## This log (update)

49. "add these prompts to prompt log"
