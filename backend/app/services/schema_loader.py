# backend/app/services/schema_loader.py

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Global cache
SCHEMA_CACHE = {}


def load_schemas(year: int):
    """
    Loads scouting and superscouting schemas for the given season year.

    Args:
        year (int): FRC season year, e.g., 2025

    Populates:
        SCHEMA_CACHE dictionary with keys:
            - match_mapping
            - super_mapping
            - super_offsets
    """
    match_schema_path = os.path.join(DATA_DIR, f"schema_{year}.json")
    super_schema_path = os.path.join(DATA_DIR, f"schema_superscout_{year}.json")
    super_offsets_path = os.path.join(DATA_DIR, f"schema_superscout_offsets_{year}.json")

    try:
        with open(match_schema_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)

            # Check if the schema has the expected structure
            if "mappings" in schema_data and "match" in schema_data["mappings"]:
                # Use the nested structure
                SCHEMA_CACHE["match_mapping"] = schema_data["mappings"]["match"]
                print(
                    f"✅ Loaded match mapping in nested format with {len(schema_data['mappings']['match'])} entries"
                )
            elif isinstance(schema_data, dict) and all(
                isinstance(k, str) for k in schema_data.keys()
            ):
                # Schema is a direct mapping from header -> field
                SCHEMA_CACHE["match_mapping"] = schema_data
                print(f"✅ Loaded match mapping in flat format with {len(schema_data)} entries")
            else:
                # Unknown format, try to use as-is
                SCHEMA_CACHE["match_mapping"] = schema_data
                print("⚠️ Unknown match schema format, using as-is")
    except FileNotFoundError:
        raise Exception(f"❌ Match Scouting schema missing for {year}: {match_schema_path}")

    try:
        with open(super_schema_path, "r", encoding="utf-8") as f:
            SCHEMA_CACHE["super_mapping"] = json.load(f)
    except FileNotFoundError:
        print(f"⚠️ SuperScouting schema not found for {year}: {super_schema_path}")
        SCHEMA_CACHE["super_mapping"] = None

    try:
        with open(super_offsets_path, "r", encoding="utf-8") as f:
            SCHEMA_CACHE["super_offsets"] = json.load(f)
    except FileNotFoundError:
        print(f"⚠️ SuperScouting offsets not found for {year}: {super_offsets_path}")
        SCHEMA_CACHE["super_offsets"] = None

    print(f"✅ Schemas loaded for {year}")


def get_match_mapping():
    return SCHEMA_CACHE.get("match_mapping")


def get_super_mapping():
    return SCHEMA_CACHE.get("super_mapping")


def get_super_offsets():
    return SCHEMA_CACHE.get("super_offsets")
