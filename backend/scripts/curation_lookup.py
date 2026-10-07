"""Curation helper: look up a drug's IDs and pull its FDA label text.

Dev-time tool for writing data/drugs/*.json; the app never runs it.

    python -m backend.scripts.curation_lookup metoprolol --label 'openfda.brand_name:"Lopressor"'
    python -m backend.scripts.curation_lookup metoprolol --setid <dailymed setid>

--label searches openFDA and takes the newest match; the text itself always
comes from the DailyMed SPL, which keeps the numbered section titles (e.g.
"12.3 Pharmacokinetics") that the drug files cite.

Writes curation/<name>/ids.json and curation/<name>/label.md (gitignored).
label.md holds the label text verbatim so every value in the drug file can be
checked against the exact words it came from.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "curation"

HL7 = "{urn:hl7-org:v3}"


def fetch(url: str, body: dict | None = None) -> bytes:
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def get_json(url: str, body: dict | None = None) -> dict:
    return json.loads(fetch(url, body))


def rxnorm_ingredient(name: str) -> dict:
    ids = get_json(f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={urllib.parse.quote(name)}&search=0")
    for rxcui in ids["idGroup"].get("rxnormId", []):
        props = get_json(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json")["properties"]
        if props["tty"] == "IN":
            return {"rxcui": rxcui, "name": props["name"]}
    raise SystemExit(f'No RxNorm ingredient (tty IN) named "{name}"')


def pubchem_cid(name: str) -> int:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(name)}/cids/JSON"
    return get_json(url)["IdentifierList"]["CID"][0]


def chembl_id(name: str, cid: int) -> dict:
    """Asks ChEMBL directly; falls back to EBI UniChem's PubChem -> ChEMBL mapping."""
    try:
        url = f"https://www.ebi.ac.uk/chembl/api/data/molecule.json?pref_name__iexact={urllib.parse.quote(name)}"
        molecules = get_json(url)["molecules"]
        if molecules:
            return {"chembl": molecules[0]["molecule_chembl_id"], "via": "ChEMBL API"}
    except Exception as exc:  # ChEMBL's API is sometimes down
        print(f"  ChEMBL API failed ({exc}); trying UniChem", file=sys.stderr)
    found = get_json("https://www.ebi.ac.uk/unichem/api/v1/compounds",
                     {"type": "sourceID", "compound": str(cid), "sourceID": 22})
    ids = sorted({s["compoundId"] for c in found.get("compounds", []) for s in c["sources"]
                  if s["shortName"] == "chembl"})
    if len(ids) != 1:
        raise SystemExit(f"UniChem gave {ids or 'no'} ChEMBL IDs for CID {cid}; resolve by hand")
    return {"chembl": ids[0], "via": f"UniChem from PubChem CID {cid}"}


def find_setid(search: str) -> str:
    """Newest openFDA label matching the query; prints the top candidates."""
    url = f"https://api.fda.gov/drug/label.json?search={urllib.parse.quote(search, safe=':\"+()')}&limit=100"
    results = get_json(url)["results"]
    results.sort(key=lambda r: r.get("effective_time", ""), reverse=True)
    for r in results[:10]:
        o = r.get("openfda", {})
        print(f"  {r['set_id']}  {o.get('brand_name')}  {o.get('manufacturer_name')}  {r.get('effective_time')}",
              file=sys.stderr)
    return results[0]["set_id"]


def _text(element) -> str:
    return " ".join("".join(element.itertext()).split())


def _render(element, lines: list[str]) -> None:
    """Paragraphs as text, tables as one ' | '-joined line per row."""
    for child in element:
        tag = child.tag.removeprefix(HL7)
        if tag == "table":
            for row in child.iter(f"{HL7}tr"):
                cells = [_text(cell) for cell in row if cell.tag in (f"{HL7}td", f"{HL7}th")]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
        elif tag in ("paragraph", "list"):
            if tag == "list":
                for item in child.findall(f"{HL7}item"):
                    lines.append(f"- {_text(item)}")
            else:
                lines.append(_text(child))
            lines.append("")
        else:
            _render(child, lines)


def _sections(section, depth: int, lines: list[str]) -> None:
    title = section.find(f"{HL7}title")
    if title is not None and _text(title):
        lines += ["#" * min(depth, 6) + " " + _text(title), ""]
    text = section.find(f"{HL7}text")
    if text is not None:
        _render(text, lines)
    for sub in section.findall(f"{HL7}component/{HL7}section"):
        _sections(sub, depth + 1, lines)


def dailymed_label(setid: str) -> dict:
    root = ET.fromstring(fetch(f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.xml"))
    title = _text(root.find(f"{HL7}title"))
    lines = [
        f"# {title}", "",
        f"- DailyMed setid: `{setid}`",
        f"- https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}",
        f"- Label version date: {root.find(f'{HL7}effectiveTime').get('value')}", "",
    ]
    body = root.find(f"{HL7}component/{HL7}structuredBody")
    for section in body.findall(f"{HL7}component/{HL7}section"):
        _sections(section, 2, lines)
    return {"title": title, "markdown": "\n".join(lines)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", help="generic (ingredient) name, e.g. metoprolol")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--label", help="openFDA search query that picks the label")
    group.add_argument("--setid", help="exact DailyMed setid of the label to use")
    args = parser.parse_args()

    out = OUT_DIR / args.name
    out.mkdir(parents=True, exist_ok=True)

    ingredient = rxnorm_ingredient(args.name)
    cid = pubchem_cid(args.name)
    chembl = chembl_id(args.name, cid)
    setid = args.setid or find_setid(args.label)
    label = dailymed_label(setid)

    ids = {"rxcui": ingredient["rxcui"], "chembl": chembl["chembl"], "pubchem_cid": cid,
           "chembl_via": chembl["via"], "dailymed_setid": setid, "label_title": label["title"]}
    (out / "ids.json").write_text(json.dumps(ids, indent=2) + "\n")
    (out / "label.md").write_text(label["markdown"])
    print(json.dumps(ids, indent=2))
    print(f"Label text: {(out / 'label.md').relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
