# backend/tests/test_health.py
from dotenv import load_dotenv
import sys
import os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force load .env from the project root manually
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=ENV_PATH)

import asyncio
from app.services.schema_loader import load_schemas
from app.services.tba_client import get_event_teams, get_event_matches, get_event_rankings
from app.services.statbotics_client import get_event_epas

async def run_tests():
    print("=== Unified Assistant Sanity Test ===\n")

    # 1. Test schema loading
    try:
        load_schemas(2025)
        print("[✅] Schemas loaded successfully.")
    except Exception as e:
        print(f"[❌] Schema loading failed: {e}")


    # 2. Test TBA event teams pull
    try:
        teams = await get_event_teams("2025arc")
        if teams:
            print(f"[✅] Pulled {len(teams)} teams from TBA.")
        else:
            print("[❌] No teams returned from TBA.")
    except Exception as e:
        print(f"[❌] TBA teams pull failed: {e}")

    # 3. Test TBA event matches pull
    try:
        matches = await get_event_matches("2025arc")
        if matches:
            print(f"[✅] Pulled {len(matches)} matches from TBA.")
        else:
            print("[❌] No matches returned from TBA.")
    except Exception as e:
        print(f"[❌] TBA matches pull failed: {e}")

    # 4. Test TBA event rankings pull
    try:
        rankings = await get_event_rankings("2025arc")
        if rankings:
            print(f"[✅] Pulled rankings from TBA.")
        else:
            print("[❌] No rankings data returned from TBA.")
    except Exception as e:
        print(f"[❌] TBA rankings pull failed: {e}")

    # 5. Test Statbotics event EPA pull
    try:
        epas = await get_event_epas("2025arc")
        if epas:
            print(f"[✅] Pulled {len(epas)} EPA entries from Statbotics.")
        else:
            print("[❌] No EPA data returned from Statbotics.")
    except Exception as e:
        print(f"[❌] Statbotics EPA pull failed: {e}")

    # Future Tests
    # - Superscout parsing on mock rows
    # - Virtual scouting sanity check
    # - Picklist builder quick compile

    print("\n=== Sanity Test Completed ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
