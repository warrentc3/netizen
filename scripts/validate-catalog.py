#!/usr/bin/env python3
"""Validate catalog.json: all entries must have a directory, all fields populated."""
import json
import os
import sys

REQUIRED = ["name", "description", "tags", "endpoints", "site"]
OPTIONAL_NULLABLE = ["upstream"]  # null is valid when no source repo exists

catalog = json.load(open("catalog.json"))
failed = 0

for key, entry in catalog.items():
    if not os.path.isdir(key):
        print(f"FAIL: catalog.json['{key}'] has no corresponding directory")
        failed = 1
    for field in REQUIRED:
        val = entry.get(field)
        if val is None or val == "" or val == []:
            print(f"FAIL: catalog.json['{key}'].{field} is missing or empty")
            failed = 1
        elif field == "endpoints" and (not isinstance(val, int) or val <= 0):
            print(f"FAIL: catalog.json['{key}'].endpoints must be an integer > 0 (got {val!r})")
            failed = 1

if not failed:
    print(f"OK:   catalog.json — {len(catalog)} entries, all fields populated")

sys.exit(failed)
