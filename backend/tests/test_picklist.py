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


# Imports for the new test
import json
from unittest.mock import patch, MagicMock
from app.services.picklist_generator_service import PicklistGeneratorService
from app.services.progress_tracker import ProgressTracker


@pytest.mark.asyncio
@patch('app.services.picklist_generator_service.OpenAI') # Patch the OpenAI class where it's used
async def test_iterative_fallback_for_missing_teams(MockOpenAI):
    """
    Tests the iterative fallback mechanism when initial GPT calls miss some teams.
    """
    # 1. Setup
    mock_openai_instance = MockOpenAI.return_value # Get the mocked OpenAI instance
    mock_chat_completions_create = AsyncMock() # This will be the mock for client.chat.completions.create
    mock_openai_instance.chat.completions.create = mock_chat_completions_create

    service_instance = PicklistGeneratorService(unified_dataset_path="dummy_path.json")

    # Mock team data
    mock_teams_data_prepared = [
        {"team_number": 1, "nickname": "Team 1", "metrics": {"metric_a": 10}},
        {"team_number": 2, "nickname": "Team 2", "metrics": {"metric_a": 12}},
        {"team_number": 3, "nickname": "Team 3", "metrics": {"metric_a": 8}},
        {"team_number": 4, "nickname": "Team 4", "metrics": {"metric_a": 15}},
        {"team_number": 5, "nickname": "Team 5", "metrics": {"metric_a": 9}},
    ]
    your_team_number = 999 # Dummy team number for 'your_team_number'
    pick_position = "first"
    priorities = [{"id": "metric_a", "weight": 1.0}]
    team_index_map = {i + 1: team["team_number"] for i, team in enumerate(mock_teams_data_prepared)}

    # 2. Mocking
    service_instance._prepare_team_data_for_gpt = MagicMock(return_value=mock_teams_data_prepared)
    service_instance.token_encoder.encode = MagicMock(return_value=[1, 2, 3]) # Dummy encode

    # Mock ProgressTracker
    mock_tracker_instance = MagicMock()
    mock_tracker_instance.update = MagicMock()
    mock_tracker_instance.complete = MagicMock()
    mock_tracker_instance.fail = MagicMock()
    ProgressTracker.create_tracker = MagicMock(return_value=mock_tracker_instance)


    # --- Configure side effects for client.chat.completions.create ---
    # First call (main picklist generation) - returns teams 1 (index 1), 2 (index 2)
    mock_initial_response = AsyncMock()
    mock_initial_response.choices = [MagicMock()]
    mock_initial_response.choices[0].message = MagicMock()
    mock_initial_response.choices[0].message.content = json.dumps({
        "p": [
            [1, 9.0, "Reason Team 1"], # Index 1 (Team 1)
            [2, 8.5, "Reason Team 2"]  # Index 2 (Team 2)
        ], "s": "ok"
    })
    mock_initial_response.choices[0].finish_reason = "stop"
    mock_initial_response.model = "gpt-4.1-nano"


    # Second call (rank_missing_teams for teams 3, 4, 5) - returns team 3
    # Note: rank_missing_teams is NOT explicitly called in the one-shot path if initial call "succeeds"
    # The iterative fallback _rank_single_team_with_fallback will be called directly.
    # So, we need to prepare responses for _rank_single_team_with_fallback for teams 3, 4, 5.
    
    # Fallback call for Team 3 (first missing from initial call)
    mock_fallback_team3_response = AsyncMock()
    mock_fallback_team3_response.choices = [MagicMock()]
    mock_fallback_team3_response.choices[0].message = MagicMock()
    mock_fallback_team3_response.choices[0].message.content = json.dumps({"score": 8.0, "reasoning": "Fallback Reason T3"})
    mock_fallback_team3_response.choices[0].finish_reason = "stop"
    mock_fallback_team3_response.model = "gpt-4.1-nano"

    # Fallback call for Team 4 (second missing from initial call)
    mock_fallback_team4_response = AsyncMock()
    mock_fallback_team4_response.choices = [MagicMock()]
    mock_fallback_team4_response.choices[0].message = MagicMock()
    mock_fallback_team4_response.choices[0].message.content = json.dumps({"score": 7.5, "reasoning": "Fallback Reason T4"})
    mock_fallback_team4_response.choices[0].finish_reason = "stop"
    mock_fallback_team4_response.model = "gpt-4.1-nano"

    # Fallback call for Team 5 (third missing from initial call)
    mock_fallback_team5_response = AsyncMock()
    mock_fallback_team5_response.choices = [MagicMock()]
    mock_fallback_team5_response.choices[0].message = MagicMock()
    mock_fallback_team5_response.choices[0].message.content = json.dumps({"score": 7.0, "reasoning": "Fallback Reason T5"})
    mock_fallback_team5_response.choices[0].finish_reason = "stop"
    mock_fallback_team5_response.model = "gpt-4.1-nano"

    # Set the side_effect on the mock for client.chat.completions.create
    # The order is: Initial, Fallback T3, Fallback T4, Fallback T5
    mock_chat_completions_create.side_effect = [
        mock_initial_response,
        mock_fallback_team3_response,
        mock_fallback_team4_response,
        mock_fallback_team5_response
    ]

    # 3. Execution
    result = await service_instance.generate_picklist(
        your_team_number=your_team_number,
        pick_position=pick_position,
        priorities=priorities,
        exclude_teams=None,
        team_index_map=team_index_map, # Pass this directly as per one-shot logic
        teams_data=mock_teams_data_prepared, # Pass this directly as per one-shot logic
        use_batching=False # Force one-shot path
    )

    # 4. Assertions
    assert result["status"] == "success"
    picklist = result["picklist"]
    
    # Verify all 5 teams are present
    assert len(picklist) == 5, f"Expected 5 teams, got {len(picklist)}. Picklist: {picklist}"
    
    ranked_team_numbers = {entry["team_number"] for entry in picklist}
    assert ranked_team_numbers == {1, 2, 3, 4, 5}, "Not all teams were present in the final picklist."

    # Check reasons and fallback status
    team1_entry = next((t for t in picklist if t["team_number"] == 1), None)
    team2_entry = next((t for t in picklist if t["team_number"] == 2), None)
    team3_entry = next((t for t in picklist if t["team_number"] == 3), None)
    team4_entry = next((t for t in picklist if t["team_number"] == 4), None)
    team5_entry = next((t for t in picklist if t["team_number"] == 5), None)

    assert team1_entry is not None and team1_entry["reasoning"] == "Reason Team 1"
    assert team1_entry.get("is_fallback_ranked") is not True # Should not be fallback

    assert team2_entry is not None and team2_entry["reasoning"] == "Reason Team 2"
    assert team2_entry.get("is_fallback_ranked") is not True # Should not be fallback
    
    assert team3_entry is not None and team3_entry["reasoning"] == "Fallback Reason T3"
    assert team3_entry.get("is_fallback_ranked") is True

    assert team4_entry is not None and team4_entry["reasoning"] == "Fallback Reason T4"
    assert team4_entry.get("is_fallback_ranked") is True

    assert team5_entry is not None and team5_entry["reasoning"] == "Fallback Reason T5"
    assert team5_entry.get("is_fallback_ranked") is True
    
    assert result["missing_team_numbers"] == [], f"Expected missing_team_numbers to be empty, got {result['missing_team_numbers']}"

    # Verify number of calls to OpenAI
    assert mock_chat_completions_create.call_count == 4 # 1 initial + 3 fallback calls

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
