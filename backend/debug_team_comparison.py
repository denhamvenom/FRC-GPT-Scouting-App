#!/usr/bin/env python3
"""Debug script to understand Team Comparison data flow and identify the Statistical Comparison Panel issues."""

import json
import pprint
from app.services.team_comparison_service import TeamComparisonService
from app.services.data_aggregation_service import DataAggregationService

def debug_team_comparison():
    """Debug the team comparison data flow to identify issues."""
    
    # Use the existing dataset
    dataset_path = "app/data/unified_event_2025txhou1.json"
    
    print("=== DEBUGGING TEAM COMPARISON DATA FLOW ===\n")
    
    # 1. Check what data aggregation service provides
    print("1. Examining Data Aggregation Service output:")
    print("-" * 50)
    
    data_service = DataAggregationService(dataset_path)
    teams_data = data_service.get_teams_for_analysis()
    
    if teams_data:
        sample_team = teams_data[0]
        print(f"Sample team structure for team {sample_team.get('team_number', 'Unknown')}:")
        print(f"Top-level keys: {list(sample_team.keys())}")
        
        if 'metrics' in sample_team:
            print(f"Number of metrics: {len(sample_team['metrics'])}")
            print(f"Sample metrics (first 10):")
            metrics_sample = dict(list(sample_team['metrics'].items())[:10])
            pprint.pprint(metrics_sample, width=120)
        
        print()
    
    # 2. Test the metrics extraction service
    print("2. Testing Metrics Extraction Service:")
    print("-" * 50)
    
    # Use first 3 teams for testing
    test_teams = teams_data[:3]
    
    from app.services.metrics_extraction_service import MetricsExtractionService
    metrics_service = MetricsExtractionService()
    
    # Test without suggested metrics (discovery mode)
    print("Testing automatic metric discovery:")
    comparison_data = metrics_service.extract_comparison_stats(test_teams)
    print(f"Discovered {len(comparison_data['metrics'])} metrics")
    print(f"First 5 metrics: {comparison_data['metrics'][:5]}")
    
    # Check what's in the comparison data
    print(f"\nComparison data structure:")
    print(f"Teams: {len(comparison_data['teams'])}")
    for i, team in enumerate(comparison_data['teams']):
        print(f"  Team {i+1}: {team['team_number']} - {len(team['stats'])} stats available")
        if team['stats']:
            print(f"    Sample stats: {dict(list(team['stats'].items())[:3])}")
    
    print()
    
    # 3. Test with suggested metrics
    print("3. Testing with suggested metrics:")
    print("-" * 50)
    
    suggested_metrics = ["auto_coral_L1_scored", "teleop_coral_L1_scored", "statbotics_epa_total"]
    comparison_data_suggested = metrics_service.extract_comparison_stats(test_teams, suggested_metrics)
    print(f"With suggested metrics: {len(comparison_data_suggested['metrics'])} metrics")
    print(f"Suggested metrics result: {comparison_data_suggested['metrics']}")
    
    print()
    
    # 4. Test field mapping
    print("4. Testing field name mapping:")
    print("-" * 50)
    
    all_fields = set()
    for team in test_teams:
        if 'metrics' in team:
            all_fields.update(team['metrics'].keys())
    
    print(f"Total available fields: {len(all_fields)}")
    print(f"Sample fields: {list(all_fields)[:10]}")
    
    # Test some mappings
    test_mappings = ["epa", "auto", "teleop", "coral", "defense"]
    for test_metric in test_mappings:
        mapped = metrics_service.find_matching_field(test_metric, all_fields, test_teams)
        print(f"'{test_metric}' maps to: {mapped}")
    
    print()
    
    # 5. Test full team comparison service
    print("5. Testing Team Comparison Service:")
    print("-" * 50)
    
    try:
        comparison_service = TeamComparisonService(dataset_path)
        test_team_numbers = [team['team_number'] for team in test_teams]
        
        print(f"Testing with teams: {test_team_numbers}")
        
        # Mock priorities for testing
        priorities = [
            {"id": "auto_coral_L1_scored", "weight": 1.5},
            {"id": "teleop_coral_L1_scored", "weight": 1.2},
            {"id": "statbotics_epa_total", "weight": 1.0}
        ]
        
        # Note: This would normally call GPT, so we'll just test the data preparation
        teams_data_prepared, team_index_map = comparison_service.data_service.prepare_teams_data(test_team_numbers)
        
        print(f"Prepared {len(teams_data_prepared)} teams")
        print(f"Team index map: {team_index_map}")
        
        # Check the structure of prepared data
        if teams_data_prepared:
            sample_prepared = teams_data_prepared[0]
            print(f"Prepared team structure: {list(sample_prepared.keys())}")
            if 'metrics' in sample_prepared:
                print(f"Prepared metrics count: {len(sample_prepared['metrics'])}")
    
    except Exception as e:
        print(f"Error in team comparison service: {e}")
    
    print()
    
    # 6. Identify the issue
    print("6. ISSUE IDENTIFICATION:")
    print("=" * 50)
    
    issues = []
    
    # Check if teams have metrics
    if not teams_data:
        issues.append("No teams data available")
    else:
        teams_with_metrics = sum(1 for team in teams_data if team.get('metrics'))
        if teams_with_metrics == 0:
            issues.append("No teams have metrics data")
        else:
            print(f"✓ {teams_with_metrics} teams have metrics data")
    
    # Check if metrics extraction works
    if not comparison_data['metrics']:
        issues.append("Metrics extraction service returns no metrics")
    else:
        print(f"✓ Metrics extraction finds {len(comparison_data['metrics'])} metrics")
    
    # Check if teams have stats in comparison data
    teams_with_stats = sum(1 for team in comparison_data['teams'] if team.get('stats'))
    if teams_with_stats == 0:
        issues.append("No teams have stats in comparison data")
    else:
        print(f"✓ {teams_with_stats} teams have stats in comparison data")
    
    # Check data type issues
    for team in comparison_data['teams']:
        for metric, value in team.get('stats', {}).items():
            if not isinstance(value, (int, float)):
                issues.append(f"Non-numeric value found: {metric} = {value} (type: {type(value)})")
                break
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ No obvious issues found in data flow")
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_team_comparison()