"""Write the API's OpenAPI schema to a file so the TypeScript client can be generated from it."""

import json
import sys
from pathlib import Path

from app.main import app


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m scripts.export_openapi <output.json>")
    out = Path(sys.argv[1])
    out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
