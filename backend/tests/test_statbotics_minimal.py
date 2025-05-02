# test_statbotics_minimal.py

import statbotics

def simple_pull():
    sb = statbotics.Statbotics()
    team_data = sb.get_team_year("8044", 2025)
    print("=== Slimmed EPA Data ===")
    print(team_data)
    input("\n✅ Pull complete. Press Enter to close.")

if __name__ == "__main__":
    simple_pull()
