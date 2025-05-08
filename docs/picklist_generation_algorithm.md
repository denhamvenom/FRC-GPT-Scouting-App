# FRC Picklist Generation Algorithm

This document explains the complete picklist generation approach with GPT-4o, including the two-phase strategy for handling teams that GPT might miss in the initial ranking.

## Complete Picklist Strategy

Our approach uses a one-shot generation followed by optional refinement:

1. **Initial Generation**: Generate complete picklist in a single API call
2. **Auto-Fallback**: Automatically add any missing teams with estimated scores
3. **User-Initiated Refinement**: Offer users the option to get more accurate rankings for auto-added teams
4. **Visual Clarity**: Clearly indicate which teams were auto-added vs. properly ranked by GPT

## Algorithm Overview

The algorithm uses these optimized steps:

1. **Data Preparation**: Prepare condensed team data with only essential metrics
2. **Team Verification**: Include complete list of team numbers to verify complete coverage
3. **Explicit Instructions**: Request ALL teams be ranked exactly once
4. **Enhanced Prompting**: Emphasize verification step to ensure no teams are missed
5. **Token Optimization**: Set max tokens to 3500 for complete response
6. **Fallback Mechanism**: Add any missing teams with a fallback score and visual indicators
7. **Two-Phase Ranking**: Offer users the option to re-rank just the auto-added teams

## Optimal Configuration

Based on performance testing, we've found the following optimal parameters:

- **Max tokens**: 3500 tokens for output
- **Team data condensing**: Limiting superscouting to most recent entry, removing unnecessary fields
- **Verification**: Explicit list of team numbers for GPT to check against
- **User feedback**: Progress tracking with estimated completion time based on 0.9s per team
- **Visual indicators**: Badges and explanatory text for auto-added teams

## Prompting Strategy

### Enhanced System Prompt

```
You are GPT-4.1, an elite FRC pick-list strategist.
Objective: Rank all {team_count} teams for the {pick_position} pick of Team {your_team_number}, producing valid JSON chunks until finished.
Invariant rules:
1. Every team exactly once - never repeat teams across chunks.
2. Pure JSON output—no commentary.
3. Each team's reasoning cites ≥ 1 distinct metric value.
4. Stop *before* hitting the token limit by chunking.
5. Signal continuation via "continue": true.
6. Teams you've already ranked in previous chunks will be listed in a follow-up prompt - never rank these again.

JSON SCHEMA (use precisely)
{
  "status": "success",
  "part": 1,
  "part_total": null,      // fill only in the final chunk
  "picklist": [
    {
      "team_number": 0,
      "nickname": "",
      "score": 0.0,
      "reasoning": ""
    }
  ],
  "analysis": {            // include ONLY in part 1 and last part
    "draft_reasoning": "",
    "evaluation": "",
    "final_recommendations": ""
  },
  "continue": false
}

Additional context: {position_context}
```

### User Prompt

```
YOUR_TEAM_PROFILE = {...} 
PRIORITY_METRICS  = {...}
GAME_CONTEXT      = {...}
AVAILABLE_TEAMS   = {...}

Instructions:
1. Draft metric‑weighted ranking.
2. Evaluate for alliance synergy with Team {your_team_number}.
3. Emit the picklist sorted best→worst.
4. Output ≤ 90% of remaining token budget per chunk.
5. Fill "continue": true if more teams remain; otherwise "continue": false and set part_total.
6. Include analysis only in part 1 and the final part.
```

### Targeted Continuation Prompt

The key improvement is this targeted continuation prompt that explicitly lists already processed teams and specifies exactly which teams to rank next:

```
You've already ranked these {len(processed_teams)} teams: {sorted(list(processed_teams))}. 
DO NOT rank any of these teams again. 
For this chunk, please rank ONLY these {len(next_chunk_teams)} teams: {next_chunk_teams}. 
Rank them in order from best to worst.
```

## One-Shot Python Implementation

```python
# Initialize variables for one-shot approach
start_time = time.time()
estimated_time = len(teams_data) * 0.9  # ~0.9 seconds per team estimate
logger.info(f"Estimated completion time: {estimated_time:.1f} seconds")

# Create prompts optimized for one-shot completion
system_prompt = self._create_system_prompt(pick_position, len(teams_data))

# Get sorted list of team numbers for verification
team_numbers = sorted([team["team_number"] for team in teams_data])
logger.info(f"Teams to rank: {len(team_numbers)}")
logger.info(f"Team numbers: {team_numbers[:10]}... (and {len(team_numbers) - 10} more)")

user_prompt = self._create_user_prompt(
    your_team_number, 
    pick_position, 
    priorities, 
    teams_data,
    team_numbers
)

# Initialize messages
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

# Make a single API call to rank all teams at once
logger.info(f"--- Requesting complete picklist for {len(team_numbers)} teams ---")
request_start_time = time.time()

# Call GPT with optimized settings for one-shot generation
logger.info("Starting API call...")
response = client.chat.completions.create(
    model="gpt-4o",  # Using a model that can handle the full team list
    messages=messages,
    temperature=0.2,  # Lower temperature for more consistent results
    response_format={"type": "json_object"},
    max_tokens=3500  # Optimized for one-shot generation
)

# Parse the response
response_content = response.choices[0].message.content
response_data = json.loads(response_content)

# Extract the picklist and analysis
picklist = response_data.get("picklist", [])
analysis = response_data.get("analysis", {
    "draft_reasoning": "Analysis not available",
    "evaluation": "Analysis not available",
    "final_recommendations": "Analysis not available"
})

# Check for duplicate teams (shouldn't happen with one-shot approach)
seen_teams = set()
deduplicated_picklist = []
duplicates = []

for team in picklist:
    team_number = team.get("team_number")
    if team_number and team_number not in seen_teams:
        seen_teams.add(team_number)
        deduplicated_picklist.append(team)
    elif team_number:
        duplicates.append(team_number)

# Check if we're missing teams
available_team_numbers = {team["team_number"] for team in teams_data}
ranked_team_numbers = {team["team_number"] for team in deduplicated_picklist}
missing_team_numbers = available_team_numbers - ranked_team_numbers

# If we're missing teams, add them to the end with is_fallback flag
if missing_team_numbers:
    logger.warning(f"Missing {len(missing_team_numbers)} teams from GPT response")
    
    # Get the lowest score from the existing picklist
    min_score = min([team["score"] for team in deduplicated_picklist]) if deduplicated_picklist else 0.0
    backup_score = max(0.1, min_score * 0.5)  # Use half of the minimum score
    
    # Add missing teams to the end of the picklist
    for team_number in missing_team_numbers:
        team_data = next((t for t in teams_data if t["team_number"] == team_number), None)
        if team_data:
            deduplicated_picklist.append({
                "team_number": team_number,
                "nickname": team_data.get("nickname", f"Team {team_number}"),
                "score": backup_score,
                "reasoning": "Added to complete the picklist - not enough data available for detailed analysis",
                "is_fallback": True  # Flag to indicate this team was added as a fallback
            })
```

## Frontend UI Enhancements

To improve the user experience, several enhancements were made to the frontend:

1. **Progress Indicator**:
   - Shows a progress bar during picklist generation
   - Displays estimated time based on team count (~0.9s per team)
   - Updates progress in real-time
   - Shows helpful status messages during generation

2. **Fallback Team Indicators**:
   - Clearly marks auto-added teams with "Auto-added" badge
   - Additional explanation text for fallback teams
   - Visual distinction for fallback team reasoning
   
3. **Performance Metrics**:
   - Shows performance statistics after generation completes
   - Includes total time, average time per team, missing team count
   - Helps users understand the quality of the response

## Performance Characteristics

For a typical event with 75 teams:

- **Execution time**: ~70 seconds in a single API call
- **API calls**: 1 (vs. 3+ with chunking)
- **Rate limit issues**: Eliminated (no rate limits with single call)
- **Duplicates**: Rare with one-shot approach
- **Coverage**: Complete with fallback mechanism
- **Client feedback**: Progress tracking with time estimation

## Debugging the Process

The process is extensively logged to `picklist_generator.log` and can be viewed in the Debug UI at `/debug/logs`.

## Benefits

- Eliminates rate limit/429 errors that chunking approach encountered
- Simplifies implementation with single API call
- Provides better user experience with progress tracking
- Ensures complete coverage with fallback mechanism
- Transparent performance metrics
- Visually indicates which teams were manually added