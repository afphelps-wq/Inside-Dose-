"""Validate curated drug files in data/drugs/.

Usage (from the repo root):
    python -m backend.app.validate_data                 # check every data/drugs/*.json
    python -m backend.app.validate_data path/to/x.json  # check specific files
    python -m backend.app.validate_data --write-schema  # regenerate drug.schema.json
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from backend.app.models import Drug, drug_json_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DRUGS_DIR = DATA_DIR / "drugs"
SCHEMA_PATH = DATA_DIR / "schema" / "drug.schema.json"


def render_schema() -> str:
    return json.dumps(drug_json_schema(), indent=2) + "\n"


def _location(parts) -> str:
    path = ""
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else (f".{part}" if path else str(part))
    return path or "(top level)"


def validate_record(record: object, expected_id: str | None = None) -> list[str]:
    """Returns plain-language problems; an empty list means the record is valid."""
    errors: list[str] = []

    schema = json.loads(SCHEMA_PATH.read_text())
    for error in sorted(Draft202012Validator(schema).iter_errors(record), key=lambda e: list(e.path)):
        errors.append(f"schema: {_location(error.path)}: {error.message}")

    try:
        Drug.model_validate(record)
    except ValidationError as exc:
        for error in exc.errors():
            message = error["msg"].removeprefix("Value error, ")
            errors.append(f"model: {_location(error['loc'])}: {message}")

    if expected_id is not None and isinstance(record, dict) and record.get("id") != expected_id:
        errors.append(f'id: "{record.get("id")}" should match the file name "{expected_id}"')

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        record = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"]
    return validate_record(record, expected_id=path.stem)


def main(argv: list[str]) -> int:
    if argv == ["--write-schema"]:
        SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEMA_PATH.write_text(render_schema())
        print(f"Wrote {SCHEMA_PATH.relative_to(REPO_ROOT)}")
        return 0

    paths = [Path(arg) for arg in argv] or sorted(DRUGS_DIR.glob("*.json"))
    if not paths:
        print("No drug files found in data/drugs/.")
        return 0

    failed = 0
    for path in paths:
        errors = validate_file(path)
        if errors:
            failed += 1
            print(f"FAIL {path.name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"ok   {path.name}")

    print(f"\n{len(paths) - failed}/{len(paths)} files valid.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
