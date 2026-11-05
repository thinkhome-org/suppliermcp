"""Encode protected JSON values for Portainer's line-based .env upload and dotenv backend."""

import argparse
import json
import os
import re
from pathlib import Path


def write_portainer_env(path, values):
    if not isinstance(values, dict) or any(
        not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key) or not isinstance(value, str)
        for key, value in values.items()
    ):
        raise ValueError("Expected an object of uppercase environment names and string values")
    # UI preserves these quotes; dotenv decodes them and $$ prevents variable expansion.
    content = "".join(
        key + "=" + json.dumps(value, ensure_ascii=False).replace("$", "$$") + "\n"
        for key, value in values.items()
    )
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_env", type=Path)
    args = parser.parse_args()
    write_portainer_env(args.output_env, json.loads(args.input_json.read_text()))
    print("Prepared protected Portainer environment file; values suppressed.")


if __name__ == "__main__":
    main()
