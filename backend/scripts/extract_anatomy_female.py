"""Dev-time tool: build the frontend's female 3D body asset from the HuBMAP Human Reference Atlas.

Not run by the app. BodyParts3D (the male model, see extract_anatomy.py) has no female
dataset, so the female view uses the HRA "3D Reference Organ Set for Female"
(CC BY 4.0, built from the Visible Human Female -- see frontend/src/assets/CREDITS.md).
Every organ GLB shares one body coordinate space (metres, y up, +x = the body's left,
front = +z), so organs line up with the female skin without any manual placement.

For each of our body-map organs (spec §6.3) the matching GLBs are merged into one mesh,
decimated to a browser-friendly size, and packed in the same layout extract_anatomy.py
writes (float32 positions, int16 normals, uint32 indices + a JSON manifest), so
Body3D.jsx loads either sex the same way. The HRA set has no stomach or muscle mesh,
and (like BodyParts3D) no thyroid or fat, so those organs have no 3D visual in the female view.

Needs numpy, trimesh and fast-simplification (install them in a scratch venv, not the backend's).

Usage:
    python -m backend.scripts.extract_anatomy_female /path/to/dir/with/the/glb/files
"""

import gzip
import json
import sys
from pathlib import Path

import fast_simplification
import numpy as np
import trimesh

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "frontend" / "public" / "anatomy"

# organ key (spec §6.3) -> (GLB files to merge, target vertex count after decimation)
ORGANS = {
    "brain": (["3d-allen-f-brain.glb"], 40000),
    "heart": (["3d-vh-f-heart.glb"], 25000),
    "lungs": (["3d-vh-f-lung.glb"], 45000),
    "liver": (["3d-vh-f-liver.glb"], 25000),
    "intestines": (["3d-vh-f-small-intestine.glb", "3d-sbu-f-large-intestine.glb"], 40000),
    "kidneys": (["3d-vh-f-kidney-l.glb", "3d-vh-f-kidney-r.glb"], 14000),
    "pancreas": (["3d-vh-f-pancreas.glb"], 8000),
    "blood_vessels": (["3d-vh-f-blood-vasculature.glb"], 70000),
    "skin": (["3d-vh-f-skin.glb"], 45000),
    "spleen": (["3d-vh-f-spleen.glb"], 6000),
    "bladder": (["3d-vh-f-urinary-bladder.glb"], 6000),
}


def load_merged(path: Path) -> trimesh.Trimesh:
    scene = trimesh.load(path, force="scene")  # applies every node transform
    meshes = [g for g in scene.dump() if isinstance(g, trimesh.Trimesh) and len(g.faces)]
    return trimesh.util.concatenate(meshes)


def weld(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    # The GLBs ship unshared vertices; without welding, the simplifier sees every triangle as
    # its own island and shreds the mesh.
    mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def decimate(mesh: trimesh.Trimesh, target_verts: int) -> trimesh.Trimesh:
    if len(mesh.vertices) <= target_verts:
        return mesh
    faces_target = int(len(mesh.faces) * target_verts / len(mesh.vertices))
    verts, faces = fast_simplification.simplify(
        mesh.vertices.astype(np.float32), mesh.faces.astype(np.uint32), target_count=faces_target,
    )
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def main(src_dir: str) -> None:
    src = Path(src_dir)
    manifest = {"organs": {}}
    blob = bytearray()
    overall_min = np.full(3, np.inf)
    overall_max = np.full(3, -np.inf)

    for organ, (files, target) in ORGANS.items():
        parts = [load_merged(src / name) for name in files]
        merged = weld(trimesh.util.concatenate(parts))
        raw_verts = len(merged.vertices)
        merged = decimate(merged, target)

        positions = np.ascontiguousarray(merged.vertices, dtype="<f4")
        normals = np.clip(np.round(np.asarray(merged.vertex_normals) * 32767), -32767, 32767).astype("<i2")
        indices = np.ascontiguousarray(merged.faces.reshape(-1), dtype="<u4")
        lo, hi = positions.min(axis=0), positions.max(axis=0)
        overall_min, overall_max = np.minimum(overall_min, lo), np.maximum(overall_max, hi)

        pos_offset = len(blob)
        blob += positions.tobytes()
        nrm_offset = len(blob)
        blob += normals.tobytes()
        while len(blob) % 4:  # Uint32Array views need 4-byte-aligned offsets
            blob += b"\x00"
        idx_offset = len(blob)
        blob += indices.tobytes()

        manifest["organs"][organ] = {
            "positions": pos_offset, "normals": nrm_offset, "indices": idx_offset,
            "vertexCount": int(len(positions)), "indexCount": int(len(indices)),
            "bounds": [lo.tolist(), hi.tolist()],
        }
        print(f"{organ:14} {raw_verts:8} -> {len(positions):6} verts  {len(indices) // 3:7} tris")

    manifest["bounds"] = [overall_min.tolist(), overall_max.tolist()]
    manifest["source"] = (
        "HuBMAP Human Reference Atlas, 3D Reference Organ Set for Female (Visible Human Female), CC BY 4.0. "
        "Merged/decimated per organ via backend/scripts/extract_anatomy_female.py; see frontend/src/assets/CREDITS.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "organs-female.json").write_text(json.dumps(manifest))
    gz = gzip.compress(bytes(blob), compresslevel=9)
    (OUT_DIR / "organs-female.bin.gz").write_bytes(gz)
    print(f"\nTotal raw: {len(blob) / 1e6:.2f} MB -> gzipped: {len(gz) / 1e6:.2f} MB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
