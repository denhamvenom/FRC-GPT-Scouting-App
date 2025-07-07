#!/usr/bin/env python3
"""Detailed analysis of the metrics extraction issue."""

import json
import pprint
from app.services.data_aggregation_service import DataAggregationService
from app.services.metrics_extraction_service import MetricsExtractionService

def debug_detailed_metrics():
    """Debug the exact metrics extraction issue."""
    
    dataset_path = "app/data/unified_event_2025txhou1.json"
    
    print("=== DETAILED METRICS EXTRACTION DEBUG ===\n")
    
    # Get the teams data
    data_service = DataAggregationService(dataset_path)
    teams_data = data_service.get_teams_for_analysis()
    
    # Take first 3 teams for analysis
    test_teams = teams_data[:3]
    
    print("1. EXAMINING TEAM DATA STRUCTURE:")
    print("-" * 50)
    
    for i, team in enumerate(test_teams):
        print(f"\nTeam {i+1}: {team.get('team_number', 'Unknown')}")
        print(f"  Keys: {list(team.keys())}")
        
        # Show metrics structure
        metrics = team.get('metrics', {})
        print(f"  Metrics keys: {list(metrics.keys())}")
        print(f"  Metrics values: {metrics}")
        
        # Show what fields are numeric
        numeric_fields = {}
        text_fields = {}
        
        for key, value in metrics.items():
            try:
                float_val = float(value)
                numeric_fields[key] = float_val
            except (ValueError, TypeError):
                text_fields[key] = value
        
        print(f"  Numeric fields: {numeric_fields}")
        print(f"  Text fields: {text_fields}")
    
    print("\n2. TESTING METRICS EXTRACTION SERVICE:")
    print("-" * 50)
    
    metrics_service = MetricsExtractionService()
    
    # Test the discovery algorithm step by step
    print("Testing automatic discovery:")
    
    # Collect all numeric fields from all teams
    all_numeric_fields = set()
    
    for team in test_teams:
        for key, value in team.items():
            if key in ["team_number", "nickname", "reasoning"]:
                continue
            try:
                float(value)
                all_numeric_fields.add(key)
                print(f"  Added to numeric fields: {key} = {value}")
            except (ValueError, TypeError, AttributeError):
                print(f"  Skipped non-numeric: {key} = {value} (type: {type(value)})")
    
    print(f"\nAll numeric fields found: {all_numeric_fields}")
    
    # Test the priority metrics
    priority_metrics = [
        "auto_avg_points", "teleop_avg_points", "endgame_avg_points", "total_avg_points",
        "autonomous_score", "teleoperated_score", "endgame_score", "total_score",
        "epa_total", "epa_auto", "epa_teleop", "epa_endgame",
        "consistency_score", "defense_rating", "reliability_score"
    ]
    
    found_priority = []
    for metric in priority_metrics:
        if metric in all_numeric_fields:
            found_priority.append(metric)
    
    print(f"Priority metrics found: {found_priority}")
    
    # Test the actual extraction
    comparison_data = metrics_service.extract_comparison_stats(test_teams)
    print(f"\nActual extraction result:")
    print(f"  Metrics: {comparison_data['metrics']}")
    print(f"  Teams count: {len(comparison_data['teams'])}")
    
    for team in comparison_data['teams']:
        print(f"  Team {team['team_number']}: {len(team['stats'])} stats")
        print(f"    Stats: {team['stats']}")
    
    print("\n3. ANALYZING THE ISSUE:")
    print("-" * 50)
    
    # The issue is likely in the extract_comparison_stats method
    # Let's trace through its logic
    
    print("Tracing through extract_comparison_stats logic:")
    
    # Step 1: Check if suggested_metrics is None (it should be for discovery)
    print(f"suggested_metrics parameter: None (using discovery mode)")
    
    # Step 2: Check all_numeric_fields discovery
    print(f"Discovery found {len(all_numeric_fields)} numeric fields")
    
    # Step 3: Check if the logic correctly processes the team data
    print("Checking team data processing:")
    
    for team in test_teams:
        print(f"\nTeam {team.get('team_number')}:")
        print(f"  Full structure: {team}")
        
        # The issue might be that the algorithm is looking at top-level keys
        # but the actual metrics are nested under 'metrics'
        
        # Test what the algorithm actually sees
        algorithm_numeric_fields = set()
        for key, value in team.items():
            if key in ["team_number", "nickname", "reasoning"]:
                continue
            try:
                float(value)
                algorithm_numeric_fields.add(key)
            except (ValueError, TypeError, AttributeError):
                continue
        
        print(f"  Algorithm sees numeric fields: {algorithm_numeric_fields}")
        
        # Check metrics subkey
        if 'metrics' in team:
            metrics_numeric_fields = set()
            for key, value in team['metrics'].items():
                if key in ["team_number", "nickname", "reasoning"]:
                    continue
                try:
                    float(value)
                    metrics_numeric_fields.add(key)
                except (ValueError, TypeError, AttributeError):
                    continue
            print(f"  Metrics subkey has numeric fields: {metrics_numeric_fields}")
    
    print("\n=== ISSUE IDENTIFIED ===")
    print("The metrics extraction algorithm is looking at the wrong level!")
    print("It's checking team.items() but the actual metrics are in team['metrics']")

if __name__ == "__main__":
    debug_detailed_metrics()