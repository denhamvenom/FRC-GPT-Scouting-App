# backend/tests/test_picklist.py

import requests
import pytest
from unittest.mock import AsyncMock
from collections import Counter
import re

# Predefined stop words for reason analysis
STOP_WORDS = {"a", "an", "the", "is", "was", "are", "were", "of", "to", "in", "it", "and", "for", "with", "on", "good", "strong", "excellent", "reliable", "consistent", "very", "high", "great"}

def analyze_reason_variety(picklist: list) -> bool:
    """
    Analyzes the variety of reasons in a picklist.

    Args:
        picklist: A list of team entries, where each entry is a dictionary
                  expected to have a "reasoning" key.

    Returns:
        True if reasons have good variety, False otherwise.
    """
    if not picklist:
        return True  # No reasons to analyze, so variety is vacuously good

    all_reason_words = []
    reason_count = len(picklist)

    for item in picklist:
        reasoning = item.get("reasoning", "")
        if not reasoning:
            continue
        # Simple word tokenization: lowercase and split by non-alphanumeric characters
        words = re.findall(r'\b\w+\b', reasoning.lower())
        all_reason_words.extend([word for word in words if word not in STOP_WORDS])

    if not all_reason_words:
        return True # No non-stop words found, consider it good variety

    word_counts = Counter(all_reason_words)
    
    # Check if any single non-stop word appears in more than 50% of the reasons
    # This is a simplified check. A more robust check might look at n-grams or semantic similarity.
    for word, count in word_counts.items():
        # We need to check how many *reasons* a word appears in, not its total frequency.
        # For this, we'll count distinct reasons containing the word.
        reasons_with_word = 0
        for p_item in picklist:
            p_reason = p_item.get("reasoning", "").lower()
            if word in re.findall(r'\b\w+\b', p_reason):
                 reasons_with_word +=1
        
        if reasons_with_word > reason_count / 2:
            # print(f"Low variety detected: Word '{word}' appears in {reasons_with_word}/{reason_count} reasons.")
            return False # Low variety

    return True # Good variety


@pytest.mark.asyncio
async def test_reason_variety_analysis():
    """
    Tests the analyze_reason_variety helper function with predefined good and bad picklists.
    """
    good_picklist_response = {
        "status": "success",
        "picklist": [
            {"team_number": 1, "nickname": "Team A", "score": 9.0, "reasoning": "Excellent shooter accuracy"},
            {"team_number": 2, "nickname": "Team B", "score": 8.5, "reasoning": "Fast cycle times"},
            {"team_number": 3, "nickname": "Team C", "score": 8.0, "reasoning": "Strong defensive play"},
            {"team_number": 4, "nickname": "Team D", "score": 7.5, "reasoning": "Reliable autonomous mode"}
        ],
        "analysis": {}, "missing_team_numbers": [], "performance": {}
    }

    bad_picklist_response_repetitive_auto = {
        "status": "success",
        "picklist": [
            {"team_number": 1, "nickname": "Team A", "score": 9.0, "reasoning": "Good auto capability"},
            {"team_number": 2, "nickname": "Team B", "score": 8.5, "reasoning": "Good auto performance"},
            {"team_number": 3, "nickname": "Team C", "score": 8.0, "reasoning": "Good auto scoring"},
            {"team_number": 4, "nickname": "Team D", "score": 7.5, "reasoning": "Good auto reliability"}
        ],
        "analysis": {}, "missing_team_numbers": [], "performance": {}
    }
    
    bad_picklist_response_repetitive_climber = {
        "status": "success",
        "picklist": [
            {"team_number": 1, "nickname": "Team A", "score": 9.0, "reasoning": "Consistent climber"},
            {"team_number": 2, "nickname": "Team B", "score": 8.5, "reasoning": "Very fast climber"},
            {"team_number": 3, "nickname": "Team C", "score": 8.0, "reasoning": "Reliable climber mechanism"},
            {"team_number": 4, "nickname": "Team D", "score": 7.5, "reasoning": "Good climber under pressure"}
        ],
        "analysis": {}, "missing_team_numbers": [], "performance": {}
    }

    # Test with good variety
    assert analyze_reason_variety(good_picklist_response["picklist"]) is True, "Expected good variety for the first picklist."

    # Test with bad variety (repetitive "auto")
    assert analyze_reason_variety(bad_picklist_response_repetitive_auto["picklist"]) is False, "Expected low variety for repetitive 'auto' reasons."

    # Test with bad variety (repetitive "climber")
    assert analyze_reason_variety(bad_picklist_response_repetitive_climber["picklist"]) is False, "Expected low variety for repetitive 'climber' reasons."

    # Test with an empty picklist (should be considered good variety)
    assert analyze_reason_variety([]) is True, "Expected good variety for an empty picklist."

    # Test with picklist having empty reasons (should be good)
    picklist_empty_reasons = {
        "picklist": [
            {"team_number": 1, "reasoning": ""},
            {"team_number": 2, "reasoning": ""},
        ]
    }
    assert analyze_reason_variety(picklist_empty_reasons["picklist"]) is True, "Expected good variety for picklist with empty reasons."

    # Test with picklist having only stop words in reasons (should be good)
    picklist_stop_words_reasons = {
        "picklist": [
            {"team_number": 1, "reasoning": "is a good"},
            {"team_number": 2, "reasoning": "the and for"},
        ]
    }
    assert analyze_reason_variety(picklist_stop_words_reasons["picklist"]) is True, "Expected good variety for picklist with only stop words in reasons."

    # Test with picklist where a non-stop word appears in exactly 50% of reasons (should be good)
    picklist_half_repetition = {
        "picklist": [
            {"team_number": 1, "reasoning": "Focus on shooting"},
            {"team_number": 2, "reasoning": "Focus on defense"},
            {"team_number": 3, "reasoning": "Good intake"},
            {"team_number": 4, "reasoning": "Strong drive"}
        ]
    }
    assert analyze_reason_variety(picklist_half_repetition["picklist"]) is True, "Expected good variety when a word appears in 50% of reasons."

    # Test with picklist where a non-stop word appears in >50% of reasons (should be bad)
    picklist_more_than_half_repetition = {
        "picklist": [
            {"team_number": 1, "reasoning": "Focus on shooting"},
            {"team_number": 2, "reasoning": "Focus on defense"},
            {"team_number": 3, "reasoning": "Focus on auto"},
            {"team_number": 4, "reasoning": "Good intake"}
        ]
    }
    assert analyze_reason_variety(picklist_more_than_half_repetition["picklist"]) is False, "Expected low variety when a word appears in >50% of reasons."

    # Test with picklist of 1, should be good
    picklist_single_team = {
        "picklist": [
            {"team_number": 1, "reasoning": "Focus on shooting"},
        ]
    }
    assert analyze_reason_variety(picklist_single_team["picklist"]) is True, "Expected good variety for single team picklist."
    
    # Test with a mix of stop words and a repetitive keyword
    picklist_mixed_repetition = {
        "picklist": [
            {"team_number": 1, "reasoning": "Good defense strategy"},
            {"team_number": 2, "reasoning": "Strong defense performance"},
            {"team_number": 3, "reasoning": "Excellent defense rating"},
            {"team_number": 4, "reasoning": "Reliable autonomous mode"}
        ]
    }
    assert analyze_reason_variety(picklist_mixed_repetition["picklist"]) is False, "Expected low variety for picklist with repetitive keyword among stop words."


# Keep existing test if needed, or remove/comment out if it's purely for manual execution.
# For automated testing with pytest, the `if __name__ == "__main__":` block is not typical.
# def test_build_picklist():
#     url = "http://localhost:8000/api/picklist/build"
#     payload = {
#         "first_pick_priorities": ["Fast cycle time", "Good autonomous", "Reliable climb"],
#         "second_pick_priorities": ["Defense ability", "Drive consistency"],
#         "third_pick_priorities": ["Floor pickup", "Backup climb"]
#     }
# 
#     response = requests.post(url, json=payload)
# 
#     assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
#     data = response.json()
# 
#     assert "picklist" in data, "Response missing 'picklist' field"
#     assert isinstance(data["picklist"], list), "'picklist' should be a list"
#     assert len(data["picklist"]) > 0, "Picklist is empty"
# 
#     print("Picklist successfully generated!")
#     for entry in data["picklist"]:
#         print(f"Team {entry['team_number']}: {entry['reasoning']}")
# 
# 
# if __name__ == "__main__":
#     test_build_picklist()
