#!/usr/bin/env python3
"""Test script for the updated Statistical Comparison functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.team_comparison_service import TeamComparisonService
from app.services.metrics_extraction_service import MetricsExtractionService

def test_metrics_extraction():
    """Test the updated metrics extraction functionality."""
    print("🧪 Testing Statistical Comparison with Dynamic Field Detection")
    print("=" * 70)
    
    # Use the lake dataset which has field selections
    dataset_path = "app/data/unified_event_2025lake.json"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    try:
        # Initialize the team comparison service
        comparison_service = TeamComparisonService(dataset_path)
        
        # Get some teams from the dataset
        teams_data = comparison_service.generator.data_service.get_teams_for_analysis()
        
        if not teams_data:
            print("❌ No team data found")
            return
            
        print(f"✅ Loaded {len(teams_data)} teams from dataset")
        
        # Take first 3 teams for comparison
        test_teams = teams_data[:3]
        team_numbers = [team['team_number'] for team in test_teams]
        
        print(f"🎯 Testing with teams: {team_numbers}")
        
        # Test the metrics extraction directly
        print("\n📊 Testing Metrics Extraction:")
        print("-" * 40)
        
        metrics_service = comparison_service.metrics_service
        
        # Test automatic discovery mode
        comparison_data = metrics_service.extract_comparison_stats(test_teams)
        
        print(f"Found {len(comparison_data['metrics'])} metrics:")
        for i, metric in enumerate(comparison_data['metrics'][:10]):  # Show first 10
            print(f"  {i+1}. {metric}")
        
        if len(comparison_data['metrics']) > 10:
            print(f"  ... and {len(comparison_data['metrics']) - 10} more")
        
        # Show sample data for first team
        if comparison_data['teams']:
            first_team = comparison_data['teams'][0]
            print(f"\n🔍 Sample data for Team {first_team['team_number']}:")
            print(f"  Stats found: {len(first_team['stats'])}")
            sample_stats = list(first_team['stats'].items())[:5]
            for metric, value in sample_stats:
                print(f"    {metric}: {value}")
        
        print("\n✅ Metrics extraction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metrics_extraction()