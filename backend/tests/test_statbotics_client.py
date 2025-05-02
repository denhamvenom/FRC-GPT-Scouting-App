# backend/tests/test_statbotics_client.py

from backend.app.services.statbotics_client import get_team_epa

def test_pull_statbotics_slim_data():
    team_key = 254  # Statbotics expects just the number, not "frc8044"
    year = 2025

    team_data = get_team_epa(team_key, year)

    print("=== Slimmed Statbotics EPA Data ===")
    for key, value in team_data.items():
        print(f"{key}: {value}")

    input("\n✅ Test complete. Press Enter to close this window.")

if __name__ == "__main__":
    test_pull_statbotics_slim_data()
