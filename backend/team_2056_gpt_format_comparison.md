# Team 2056 GPT Data Format Comparison

This file shows exactly how Team 2056's data would be sent to GPT in both standard and optimized formats.

## Team 2056 Raw Data Summary
- **Team Number**: 2056
- **Nickname**: OP Robotics
- **Matches Played**: 6
- **Average Metrics** (calculated from scouting data):
  - Auto Total Points: 4.33
  - Teleop CORAL Scored in Branch (L2-L4): 8.83
  - teleop_coral_L1_scored: 3.67
  - teleop_algae_scored_barge_processor: 5.33
  - endgame_total_points: 8.33

---

## 1. STANDARD FORMAT (Pre-Sprint Optimization)

This is how the team data looks in the original verbose format:

```json
{
  "index": 15,
  "team_number": 2056,
  "nickname": "OP Robotics",
  "weighted_score": 7.2,
  "metrics": {
    "Auto Total Points": 4.33,
    "Teleop CORAL Scored in Branch (L2-L4)": 8.83,
    "teleop_coral_L1_scored": 3.67,
    "teleop_algae_scored_barge_processor": 5.33,
    "endgame_total_points": 8.33,
    "driver_skill_rating": 3.5,
    "statbotics_epa_total": 120.06,
    "teleop_total_points": 23.5,
    "consistency_score": 7.2,
    "defense_time_seconds": 0,
    "auto_algae_scored": 0,
    "auto_coral_L1_scored": 0,
    "auto_coral_L2_scored": 1.0,
    "auto_coral_L3_scored": 0.5,
    "auto_coral_L4_scored": 0.33,
    "teleop_pickups_from_field": 8.5,
    "teleop_pickups_from_coral_station": 4.2,
    "reliability_metric": 0.85,
    "tele_algae_bleed": 0,
    "climb_success_rate": 0.67,
    "auto_mobility": 1.0,
    "penalties_per_match": 0.2,
    "alliance_support_rating": 3.8,
    "strategic_flexibility": 4.0,
    "match_impact_score": 7.5
  },
  "text_data": {
    "scout_comments": "OP | Parked in barge | Climbed deep cage | Very consistent deep cage climbs",
    "auto_starting_position": "Mixed positions - Left/Non-Processor and Right/Processor",
    "strategy_notes": "Strong coral scorer with good algae capability. Reliable deep cage climber.",
    "defensive_capability": "Limited defensive play observed"
  }
}
```

**Character count**: ~1,300 characters for this single team

---

## 2. SPRINT 1-3 OPTIMIZED FORMAT (Compact Encoding)

### 2.1 What GPT Actually Sees - Compact Array

```json
[15, 2056, "OP Robotics", 7.2, [4.33, 8.83, 8.33, 3.67, 5.33, 23.5, 3.5, 120.06, 7.2, 0.85, "SC:OP|parked|climb cage|AP:mixed pos|SN:coral+algae reliable climb"]]
```

**Character count**: ~200 characters (85% reduction!)

### 2.2 Lookup Tables Provided in System Prompt

```
CODES: AP=Auto Total Points, TCB=Teleop CORAL Scored in Branch (L2-L4), EP=endgame_total_points, TC1=teleop_coral_L1_scored, TAB=teleop_algae_scored_barge_processor, TTP=teleop_total_points, DSR=driver_skill_rating, SET=statbotics_epa_total...+4 more
FORMAT: [index,team#,name,score,[metrics...]]
```

### 2.3 Metric Order (for GPT to understand array positions)
```
["AP", "TCB", "EP", "TC1", "TAB", "TTP", "DSR", "SET", "CS", "RM", "_compressed"]
```

---

## 3. WHAT GETS FILTERED OUT (Sprint 3 Strategy-Relevant Filtering)

With priorities set to:
- Auto Total Points (35% weight)
- Teleop CORAL Scored in Branch (L2-L4) (40% weight)
- endgame_total_points (25% weight)

These metrics are **excluded** to save tokens:
- defense_time_seconds
- auto_algae_scored
- teleop_pickups_from_field
- teleop_pickups_from_coral_station
- penalties_per_match
- alliance_support_rating
- strategic_flexibility
- match_impact_score
- (and 5-10 other low-relevance metrics)

---

## 4. TEXT COMPRESSION DETAILS

### Original Text Data:
```json
{
  "scout_comments": "OP | Parked in barge | Climbed deep cage | Very consistent deep cage climbs",
  "auto_starting_position": "Mixed positions - Left/Non-Processor and Right/Processor",
  "strategy_notes": "Strong coral scorer with good algae capability. Reliable deep cage climber.",
  "defensive_capability": "Limited defensive play observed"
}
```
**Original**: ~280 characters

### Compressed Format:
```
"SC:OP|parked|climb cage|AP:mixed pos|SN:coral+algae reliable climb"
```
**Compressed**: ~70 characters (75% reduction)

---

## 5. TOKEN ESTIMATION

### Standard Format:
- Team data: ~1,300 characters ≈ 325 tokens
- For 50 teams: ~16,250 tokens

### Optimized Format:
- Team data: ~200 characters ≈ 50 tokens
- For 50 teams: ~2,500 tokens
- Plus lookup tables: ~200 tokens
- **Total**: ~2,700 tokens (83% reduction per team!)

---

## 6. COMPLETE EXAMPLE IN CONTEXT

### What GPT receives for multiple teams (showing 3 teams):

```json
AVAILABLE_TEAMS = [
  [14, 1987, "Broncobots", 7.8, [5.2, 10.1, 9.5, 2.8, 4.2, 26.3, 4.1, 115.2, 7.5, 0.88, "SC:consistent|fast cycles"]],
  [15, 2056, "OP Robotics", 7.2, [4.33, 8.83, 8.33, 3.67, 5.33, 23.5, 3.5, 120.06, 7.2, 0.85, "SC:OP|parked|climb cage"]],
  [16, 2102, "Team Paradox", 8.5, [6.1, 12.5, 10.0, 4.2, 6.8, 30.2, 4.5, 125.3, 8.2, 0.92, "SC:elite|strategic|adaptive"]]
]
```

### With these codes defined earlier:
```
CODES: AP=Auto Total Points, TCB=Teleop CORAL Scored in Branch (L2-L4), EP=endgame_total_points...
```

---

## 7. KEY BENEFITS

1. **Token Savings**: ~83% reduction per team
2. **Preserved Information**: All critical metrics and insights retained
3. **GPT Understanding**: Lookup tables ensure GPT can interpret codes
4. **Ranking Precision**: Exact values maintained (no performance bands)
5. **Context Preservation**: Essential metrics and text insights included

---

## 8. RESPONSE PARSING ENHANCEMENT

When GPT references metrics in its reasoning like:
> "Team 2056 has better TCB than Team 1987..."

The Sprint 3 response parser automatically expands this to:
> "Team 2056 has better Teleop CORAL Scored in Branch (L2-L4) than Team 1987..."

This ensures human-readable output while maintaining compact input format.