"""Dev-time tool: build the frontend's trimmed 3D body asset from BodyParts3D.

Not run by the app. Reads a local clone of ashemag/human-atlas (which packages
BodyParts3D 4.0, CC BY 4.0, via DBCLS) and keeps only the 13 of our 15 body-map
organs (spec §6.3) that have a clean whole-structure "concept" in that atlas --
thyroid and fat/adipose tissue aren't modeled in BodyParts3D at all and are
left out of the 3D view entirely (confirmed by exhaustive name search).

For each organ, every part belonging to its atlas concept(s) is merged into one
contiguous (positions, normals, indices) mesh -- our body-map granularity is
"one organ", not "one of its 2,234 sub-structures", so there is no reason to
ship per-part detail, and merging here (not in the browser) keeps the frontend
loader trivial.

Usage:
    python -m backend.scripts.extract_anatomy /path/to/human-atlas/clone
"""

import gzip
import json
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "frontend" / "public" / "anatomy"

# organ key (spec §6.3) -> atlas concept name(s) to merge
ORGAN_CONCEPTS = {
    "brain": ["brain"],
    "heart": ["heart"],
    "lungs": ["right lung", "left lung"],
    "liver": ["liver"],
    "stomach": ["stomach"],
    "intestines": ["small intestine", "large intestine"],
    "kidneys": ["kidney"],
    "pancreas": ["pancreas"],
    "blood_vessels": ["vascular tree"],
    "muscle": ["muscle organ"],
    "skin": ["skin"],
    "spleen": ["spleen"],
    "bladder": ["urinary bladder"],
    # thyroid, fat: not present anywhere in BodyParts3D -- omitted (confirmed,
    # not a naming mismatch; see the exploration notes in the M4+ conversation).
}


def main(atlas_root: str) -> None:
    atlas_root = Path(atlas_root)
    atlas = json.loads((atlas_root / "public" / "models" / "atlas.json").read_text())
    parts_by_id = {p["id"]: p for p in atlas["parts"]}
    concepts_by_name = {c["name"].lower(): c for c in atlas["concepts"]}

    chunk_cache: dict[int, bytes] = {}

    def chunk_bytes(index: int) -> bytes:
        if index not in chunk_cache:
            chunk_cache[index] = (atlas_root / "public" / "models" / f"body-{index}.bin").read_bytes()
        return chunk_cache[index]

    manifest = {"organs": {}}
    blob = bytearray()
    overall_min = [float("inf")] * 3
    overall_max = [float("-inf")] * 3

    for organ, concept_names in ORGAN_CONCEPTS.items():
        part_ids: list[str] = []
        seen = set()
        for name in concept_names:
            concept = concepts_by_name.get(name)
            if concept is None:
                raise SystemExit(f"Concept {name!r} not found in atlas (needed for organ {organ!r})")
            for pid in concept["elements"]:
                if pid not in seen:
                    seen.add(pid)
                    part_ids.append(pid)

        positions: list[float] = []
        normals: list[int] = []
        indices: list[int] = []
        vertex_base = 0
        organ_min = [float("inf")] * 3
        organ_max = [float("-inf")] * 3

        for pid in part_ids:
            p = parts_by_id[pid]
            buf = chunk_bytes(p["chunk"])
            vcount, icount = p["vertexCount"], p["indexCount"]

            pos = struct.unpack_from(f"<{vcount * 3}f", buf, p["positions"])
            positions.extend(pos)
            for axis in range(3):
                vals = pos[axis::3]
                organ_min[axis] = min(organ_min[axis], min(vals))
                organ_max[axis] = max(organ_max[axis], max(vals))

            nrm = struct.unpack_from(f"<{vcount * 3}h", buf, p["normals"])
            normals.extend(nrm)

            idx = struct.unpack_from(f"<{icount}I", buf, p["indices"])
            indices.extend(i + vertex_base for i in idx)
            vertex_base += vcount

        for axis in range(3):
            overall_min[axis] = min(overall_min[axis], organ_min[axis])
            overall_max[axis] = max(overall_max[axis], organ_max[axis])

        pos_offset = len(blob)
        blob += struct.pack(f"<{len(positions)}f", *positions)
        nrm_offset = len(blob)
        blob += struct.pack(f"<{len(normals)}h", *normals)
        while len(blob) % 4:  # Uint32Array views require 4-byte-aligned offsets
            blob += b"\x00"
        idx_offset = len(blob)
        blob += struct.pack(f"<{len(indices)}I", *indices)

        manifest["organs"][organ] = {
            "positions": pos_offset, "normals": nrm_offset, "indices": idx_offset,
            "vertexCount": vertex_base, "indexCount": len(indices),
            "bounds": [organ_min, organ_max],
        }
        print(f"{organ:15} {len(part_ids):4} parts  {vertex_base:7} verts  "
              f"{len(indices):8} indices  {(len(positions)*4 + len(normals)*2 + len(indices)*4)/1e6:6.2f} MB")

    manifest["bounds"] = [overall_min, overall_max]
    manifest["source"] = (
        "BodyParts3D 4.0 (c) The Database Center for Life Science, CC BY 4.0. "
        "Trimmed/merged per organ via backend/scripts/extract_anatomy.py; "
        "see frontend/src/assets/CREDITS.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "organs.json").write_text(json.dumps(manifest))
    (OUT_DIR / "organs.bin.gz").write_bytes(gzip.compress(bytes(blob), compresslevel=9))

    print(f"\nTotal raw: {len(blob)/1e6:.2f} MB -> gzipped: {(OUT_DIR / 'organs.bin.gz').stat().st_size/1e6:.2f} MB")
    print(f"Wrote {OUT_DIR / 'organs.json'} and {OUT_DIR / 'organs.bin.gz'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
