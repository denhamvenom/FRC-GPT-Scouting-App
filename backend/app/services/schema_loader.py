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
            SCHEMA_CACHE["match_mapping"] = json.load(f)
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
