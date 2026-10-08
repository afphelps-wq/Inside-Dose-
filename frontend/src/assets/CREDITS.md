# Body model attribution (spec §5.5)

## Anatomy data

BodyParts3D, © The Database Center for Life Science, licensed under **CC BY 4.0**.

- License: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Dataset: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- License terms: https://creativecommons.org/licenses/by/4.0/
- Publication: Mitsuhashi et al. (2009), *BodyParts3D: 3D structure database for
  anatomical concepts*. https://doi.org/10.1093/nar/gkn613

BodyParts3D represents an adult male reference anatomy. It does not model every
human structure or variation; notably for this app, it has no thyroid gland or
adipose (fat) tissue mesh, so `frontend/public/anatomy/organs.json` has no
entry for those two of the app's 15 body-map organs (spec §6.3) -- they simply
have no 3D visual. This is an educational reference, not a clinical tool.

## Female anatomy data

The female body view uses the **HuBMAP Human Reference Atlas, 3D Reference Organ Set for Female**
(built from the Visible Human Female, National Library of Medicine), licensed under **CC BY 4.0**.

- Library: https://humanatlas.io/3d-reference-library
- Files: `https://cdn.humanatlas.io/digital-objects/ref-organ/<organ>-female/…/assets/*.glb`
- License terms: https://creativecommons.org/licenses/by/4.0/

BodyParts3D has no female dataset. `backend/scripts/extract_anatomy_female.py` merges the HRA
organ GLBs (skin, brain, heart, lungs, liver, small + large intestine, kidneys, pancreas, blood
vasculature, spleen, bladder) into one mesh per organ, welds and decimates them, and writes
`frontend/public/anatomy/organs-female.json` + `organs-female.bin.gz` (~7.7 MB), in the same
layout as the male asset. The HRA set has no stomach or muscle mesh, so those two have no 3D
visual in the female view (the viewer says so). Both sexes are rendered by `Body3D.jsx`.

## Adaptation

The 13 organs this app does render (brain, heart, lungs, liver, stomach,
intestines, kidneys, pancreas, blood vessels, muscle, skin, spleen, bladder)
were extracted from the packaged geometry of **ashemag/human-atlas**
(https://github.com/ashemag/human-atlas, MIT License) -- a separate project
that itself repackages BodyParts3D 4.0 for the browser (geometry simplified,
normals quantized to signed 16-bit, packed into binary chunks). We did not
reuse its application code; `backend/scripts/extract_anatomy.py` reads that
project's `atlas.json` + binary chunks and, for each of our 13 organs, merges
every part belonging to its named BodyParts3D "concept" into one mesh --
our body-map model only needs organ-level granularity, not the full 2,234
individually selectable sub-structures the original project exposes. Output:
`frontend/public/anatomy/organs.json` (manifest) and `organs.bin.gz` (merged,
gzip-compressed position/normal/index buffers), ~14.7 MB total.

Rendered in `frontend/src/components/Body3D.jsx` via three.js.

## Protein structure viewer

**Mol\*** (`https://molstar.org`), licensed under the **MIT License**
(© 2018-2026 mol* contributors). `frontend/public/vendor/molstar/molstar.js`
and `molstar.css` are the prebuilt viewer bundle from the `molstar` npm
package (v5.13.0), copied in rather than imported as an npm dependency since
only the standalone viewer build is used -- see its embedding docs at
https://molstar.org/viewer-docs/. Loaded on demand in
`frontend/src/components/StructureViewer.jsx` for the Targets tab (spec §4,
§6.3's "Mol\* view"), rendering PDB entries from RCSB.
