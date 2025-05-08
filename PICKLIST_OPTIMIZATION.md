# Picklist Generator Optimization

## Problem
The picklist generation feature was experiencing the following issues:
1. Incomplete or truncated JSON responses from GPT-4o
2. Duplicate teams in the generated picklist
3. JSON parsing errors due to truncation
4. Missing teams because of token limits

After analyzing the logs, we identified that the core issue was token usage. The GPT model was hitting token limits (indicated by `finish_reason=length`) and being cut off mid-response. This caused:
1. Incomplete JSON that failed to parse
2. The model trying to continue its list by restarting from earlier teams, resulting in duplicates
3. Missing teams because the model didn't have enough tokens to complete the full list

## Solution Overview
We implemented several optimizations to reduce token usage:

1. **Compact JSON Schema**
   - Changed from `{"team_number": 123, "nickname": "Team Name", "score": 45.6, "reasoning": "Explanation"}` 
   - To `{"team": 123, "score": 45.6, "reason": "Explanation"}`
   - Eliminated unnecessary fields like the analysis section

2. **Shorter Reasoning Text**
   - Limited reasoning to ≤12 words per team (previously it was ≤15 words)
   - Required more concise explanations to save tokens

3. **Overflow Detection**
   - Added logic to detect when the model thinks it will exceed token limits
   - Returns `{"status": "overflow"}` instead of a partial response
   - Prevents broken JSON and gives clear error messages to users

4. **Token Budget Optimization**
   - Specified minified JSON output with minimal whitespace
   - Increased `max_tokens` parameter from 3500 to 4000
   - Removed the analysis section which wasn't critical

5. **Backwards Compatibility Layer**
   - Added conversion logic to transform the compact schema back to the original format
   - Allows the frontend to continue working without changes

## Implementation Details

### System Prompt Changes
- Updated to specify the new compact schema
- Added explicit instructions for token optimization
- Required reasoning to be ≤12 words
- Added explicit overflow handling instructions

### Response Processing
- Added detection for the overflow status
- Added conversion from compact to standard format
- Preserved backward compatibility for the frontend

### Error Recovery
- Maintained existing regex-based error recovery
- Improved duplicate detection and handling

## Expected Results
- Successful generation of complete picklists with all teams
- No duplicate teams in responses
- No JSON parsing errors due to truncation
- Clear error messages when token limits are hit

## Future Improvements
- Split very large team sets into multiple API calls if needed
- Implement fallback modes with even more aggressive token saving
- Add caching for picklist generation results