# Live Alliance Selection Feature Guide

This document provides a comprehensive guide to using the Live Alliance Selection feature in the FRC-GPT-Scouting-App. The Alliance Selection feature is designed to help teams manage and track the alliance selection process during FRC competitions.

## Overview

The Alliance Selection feature allows teams to:

1. Lock their picklists once they're satisfied with the rankings
2. Track the alliance selection process in real-time
3. Record which teams become alliance captains
4. Track team acceptances and declinations
5. Support the full 3-round selection process, including backup robots for World Championship events
6. Correctly follow FRC rules, such as allowing teams that declined to become captains later

## Database Models

The Alliance Selection feature uses SQLAlchemy models for data persistence:

1. **LockedPicklist** - Stores the final picklist data
2. **AllianceSelection** - Tracks the overall alliance selection process
3. **Alliance** - Represents each of the 8 alliances and their team members
4. **TeamSelectionStatus** - Tracks the status of each team during the selection

## Workflow

### Step 1: Locking a Picklist

Before starting the alliance selection process, you need to lock your picklist:

1. Generate your first and second pick rankings in the Picklist page
2. Click the "Lock Picklist" button when you're satisfied with your rankings
3. This saves the picklist data to the database and creates a persistent record

Once a picklist is locked:
- The picklist data is stored in the database
- The picklist can no longer be edited
- You can access the Alliance Selection page

### Step 2: Alliance Selection Page

After locking your picklist, you can access the Alliance Selection page:

1. Click the "Alliance Selection" button on the Picklist page
2. This takes you to the Alliance Selection interface
3. The teams are displayed in a grid sorted by your picklist rankings

The Alliance Selection interface has two main sections:
- **Team Grid** - Shows all teams, color-coded by status
- **Alliance Board** - Shows the 8 alliances and their members

### Step 3: Recording Team Actions

During the alliance selection process, you can record the following actions:

1. **Alliance Captain** - When a team becomes an alliance captain
2. **Accept Selection** - When a team accepts an invitation
3. **Decline Selection** - When a team declines an invitation

To record an action:
1. Click on a team in the grid
2. Select the appropriate action
3. For captains and accepts, select the alliance number
4. Click "Confirm"

### Step 4: Advancing Through Rounds

The alliance selection proceeds through multiple rounds:

1. **Round 1** - First picks
2. **Round 2** - Second picks
3. **Round 3** - Backup robots (for World Championship events)

To advance to the next round:
1. Click the "Advance to Round X" button at the top of the page
2. This will mark all captains and picked teams as eliminated for that round
3. You can now continue recording team actions for the next round

### Step 5: Completing the Selection

After Round 3 (or earlier for non-World events):
1. Click the "Complete After Backup Selections" button
2. This marks the alliance selection as completed
3. You can print the alliance selection results using the "Print Alliance Selection" button

## Key Features

### Team Status Tracking

Teams in the grid display their status:
- **Captain** - Blue background
- **Picked** - Green background
- **Declined** - Red background
- **Eliminated in Previous Round** - Gray background

### FRC Rules Compliance

The system follows official FRC rules:
- Teams that decline can still become captains later
- Teams are properly eliminated after each round
- The UI prevents selecting teams that are ineligible

### Round 3 Support

The system fully supports the backup robot round (Round 3):
- Backup slots appear in the Alliance Board during Round 3
- The system correctly handles backup picks
- The UI correctly disables selecting teams already picked in previous rounds

### Picklist Unlocking

If needed, you can unlock a picklist to make changes:
1. Click the "Unlock Picklist" button on the Picklist page
2. This will delete the locked picklist record
3. You can then make changes and lock it again

## API Endpoints

The following API endpoints support the Alliance Selection feature:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alliance/lock-picklist` | POST | Lock a picklist for alliance selection |
| `/api/alliance/picklist/{id}` | GET | Get a specific locked picklist |
| `/api/alliance/picklist/{id}` | DELETE | Unlock (delete) a locked picklist |
| `/api/alliance/picklists` | GET | Get all locked picklists |
| `/api/alliance/selection/create` | POST | Create a new alliance selection |
| `/api/alliance/selection/{id}` | GET | Get a specific alliance selection |
| `/api/alliance/selection/team-action` | POST | Record a team action |
| `/api/alliance/selection/{id}/next-round` | POST | Advance to the next round |

## Implementation Details

The Lock/Unlock functionality ensures data integrity by:
1. Preventing edits to the picklist once locked
2. Allowing users to unlock the picklist if needed
3. Maintaining proper connection between the picklist and alliance selection

The team grid sorting ensures optimal team selection by:
1. Sorting teams according to the picklist rankings
2. Providing visual indicators of team status
3. Using a fallback sorting mechanism when picklist data is unavailable

## Troubleshooting

Common issues and solutions:

1. **Picklist not locking**: Ensure you have both first and second pick rankings generated
2. **Teams not sorting by picklist rank**: Check that the picklist is correctly associated with the alliance selection
3. **Cannot advance to Round 3**: Make sure you've completed Round 2 selections first
4. **Teams that declined can't be captains**: This was fixed - declined teams can become captains

## Future Improvements

Potential future enhancements:
1. Team statistics display in the team selection grid
2. PDF export of alliance selections
3. Mobile-friendly interface
4. Real-time collaboration for multiple scouts
5. Historical alliance selection data comparison