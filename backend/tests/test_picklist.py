# backend/tests/test_picklist.py

import requests

def test_build_picklist():
    url = "http://localhost:8000/api/picklist/build"
    payload = {
        "first_pick_priorities": ["Fast cycle time", "Good autonomous", "Reliable climb"],
        "second_pick_priorities": ["Defense ability", "Drive consistency"],
        "third_pick_priorities": ["Floor pickup", "Backup climb"]
    }

    response = requests.post(url, json=payload)

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()

    assert "picklist" in data, "Response missing 'picklist' field"
    assert isinstance(data["picklist"], list), "'picklist' should be a list"
    assert len(data["picklist"]) > 0, "Picklist is empty"

    print("Picklist successfully generated!")
    for entry in data["picklist"]:
        print(f"Team {entry['team_number']}: {entry['reasoning']}")


if __name__ == "__main__":
    test_build_picklist()
