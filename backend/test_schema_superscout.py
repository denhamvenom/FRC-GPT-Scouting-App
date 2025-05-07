import asyncio
import os
import json
from app.services.schema_superscout_service import map_superscout_headers
from app.services.sheets_service import get_sheet_values
from app.services.unified_event_data_service import build_unified_dataset

async def test_enhanced_schema_mapping():
    print("Fetching headers...")
    headers_data = await get_sheet_values('SuperScouting!A1:Z1')
    headers = headers_data[0] if headers_data else []
    
    print("Fetching sample data...")
    sample_data = await get_sheet_values('SuperScouting!A2:Z6')
    
    print("Running enhanced schema mapping...")
    mapping, offsets, insights = await map_superscout_headers(headers, sample_data)
    
    # Save the results for inspection
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "app", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Save mapping
    mapping_path = os.path.join(data_dir, "schema_superscout_2025.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"Schema mapping saved to {mapping_path}")
    
    # Save offsets
    offsets_path = os.path.join(data_dir, "schema_superscout_offsets_2025.json")
    with open(offsets_path, "w", encoding="utf-8") as f:
        json.dump(offsets, f, indent=2)
    print(f"Robot groups saved to {offsets_path}")
    
    # Save insights
    insights_path = os.path.join(data_dir, "schema_superscout_insights_2025.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2)
    print(f"Insights saved to {insights_path}")
    
    # Print summary of the results
    print("\nMapping Summary:")
    for header, tag in mapping.items():
        print(f"- {header}: {tag}")
    
    print("\nInsights Summary:")
    if "content_insights" in insights:
        print("Content insights found for:")
        for insight in insights.get("content_insights", []):
            print(f"- {insight.get('header')}: {insight.get('tag')} ({', '.join(str(v) for v in insight.get('values', []))})")
    
    print("\nStrategic Insights:")
    print(insights.get("strategic_insights", "No strategic insights available"))
    
    # Now rebuild the unified dataset with our enhanced schema
    print("\nRebuilding unified dataset with enhanced schema...")
    unified_path = await build_unified_dataset(
        event_key="2025arc",
        year=2025,
        force_rebuild=True
    )
    print(f"Unified dataset rebuilt at: {unified_path}")
    
    # Verify superscouting data in unified dataset
    print("\nVerifying superscout data in unified dataset...")
    with open(unified_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)
    
    # Check for a team with superscouting data
    found_superscout = False
    for team_num, team_data in unified_data.get("teams", {}).items():
        superscout_data = team_data.get("superscouting_data", [])
        if superscout_data:
            print(f"\nFound superscouting data for team {team_num}:")
            superscout_entry = superscout_data[0]
            
            # Print selected fields from superscout data
            for field, value in superscout_entry.items():
                if "pickup" in field.lower() or "climb" in field.lower() or "skill" in field.lower():
                    print(f"  - {field}: {value}")
            
            found_superscout = True
            break
    
    if not found_superscout:
        print("No superscouting data found in unified dataset!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_schema_mapping())