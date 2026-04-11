#!/usr/bin/env python3
"""Enrich catalog.json with derived spec metadata from the directory structure.

For each catalog entry, finds the *-api_openapi-v*.json file in the corresponding
directory and writes spec_file and spec_version back into the catalog entry.
"""
import json
import os
import re
import sys

catalog_path = "catalog.json"
catalog = json.load(open(catalog_path))
failed = 0

for key in catalog:
    if not os.path.isdir(key):
        print(f"SKIP: {key}/ — directory not found")
        continue

    spec_files = [
        f for f in os.listdir(key)
        if f.endswith(".json") and re.search(r"-api_openapi-v[\d.]+.*\.json$", f, re.IGNORECASE)
    ]

    if not spec_files:
        print(f"FAIL: {key}/ — no *-api_openapi-v*.json file found")
        failed = 1
        continue

    if len(spec_files) > 1:
        print(f"FAIL: {key}/ — multiple spec files found: {spec_files}")
        failed = 1
        continue

    spec_file = spec_files[0]
    m = re.search(r"-api_openapi-v([\d.]+(?:\.[^.]+)?)\.json$", spec_file, re.IGNORECASE)
    spec_version = m.group(1) if m else None

    catalog[key]["spec_file"] = spec_file
    catalog[key]["spec_version"] = spec_version
    print(f"OK:   {key}/ → {spec_file} (v{spec_version})")

with open(catalog_path, "w") as f:
    json.dump(catalog, f, indent=4)
    f.write("\n")

sys.exit(failed)
