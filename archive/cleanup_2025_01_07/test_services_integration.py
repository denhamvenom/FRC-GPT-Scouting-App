# backend/test_services_integration.py

import asyncio
import json
import os
import tempfile
import unittest
from typing import Dict, Any

# Import the new services
from app.services.data_aggregation_service import DataAggregationService
from app.services.team_analysis_service import TeamAnalysisService
from app.services.priority_calculation_service import PriorityCalculationService
from app.services.batch_processing_service import BatchProcessingService
from app.services.performance_optimization_service import PerformanceOptimizationService
from app.services.picklist_gpt_service import PicklistGPTService


class TestServicesIntegration(unittest.TestCase):
    """Integration tests for the refactored picklist generation services."""

    def setUp(self):
        """Set up test data and services."""
        # Create test dataset
        self.test_dataset = {
            "year": 2025,
            "event_key": "2025test",
            "teams": {
                "1": {
                    "team_number": 1,
                    "nickname": "The Juggernauts",
                    "scouting_data": [
                        {"autonomous": 15, "teleop": 25, "endgame": 10, "defense": 8},
                        {"autonomous": 18, "teleop": 22, "endgame": 12, "defense": 7},
                        {"autonomous": 16, "teleop": 28, "endgame": 8, "defense": 9}
                    ],
                    "statbotics": {"epa": 45.2, "auto_epa": 12.1, "teleop_epa": 28.5},
                    "ranking": {"rank": 1, "wins": 8, "losses": 2, "ties": 0}
                },
                "254": {
                    "team_number": 254,
                    "nickname": "The Cheesy Poofs",
                    "scouting_data": [
                        {"autonomous": 20, "teleop": 30, "endgame": 15, "defense": 5},
                        {"autonomous": 22, "teleop": 32, "endgame": 18, "defense": 4},
                        {"autonomous": 19, "teleop": 35, "endgame": 16, "defense": 6}
                    ],
                    "statbotics": {"epa": 52.8, "auto_epa": 15.2, "teleop_epa": 32.1},
                    "ranking": {"rank": 2, "wins": 9, "losses": 1, "ties": 0}
                },
                "973": {
                    "team_number": 973,
                    "nickname": "Greybots",
                    "scouting_data": [
                        {"autonomous": 12, "teleop": 20, "endgame": 8, "defense": 12},
                        {"autonomous": 14, "teleop": 18, "endgame": 10, "defense": 15},
                        {"autonomous": 11, "teleop": 22, "endgame": 6, "defense": 13}
                    ],
                    "statbotics": {"epa": 38.1, "auto_epa": 9.8, "teleop_epa": 22.3},
                    "ranking": {"rank": 5, "wins": 6, "losses": 4, "ties": 0}
                }
            }
        }

        # Create temporary dataset file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        json.dump(self.test_dataset, self.temp_file)
        self.temp_file.close()

        # Initialize services
        self.data_service = DataAggregationService(self.temp_file.name)
        self.team_analysis_service = TeamAnalysisService(self.test_dataset["teams"])
        self.priority_service = PriorityCalculationService()
        
        # Shared cache for performance and batch services
        self.shared_cache = {}
        self.performance_service = PerformanceOptimizationService(self.shared_cache)
        self.batch_service = BatchProcessingService(self.shared_cache)
        
        # GPT service (will mock API calls in tests)
        self.gpt_service = PicklistGPTService()

        # Test priorities
        self.test_priorities = {
            "autonomous": 0.25,
            "teleop": 0.35,
            "endgame": 0.20,
            "defense": 0.20
        }

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_data_aggregation_service(self):
        """Test the DataAggregationService functionality."""
        # Test dataset loading
        metadata = self.data_service.get_dataset_metadata()
        self.assertEqual(metadata["year"], 2025)
        self.assertEqual(metadata["teams_count"], 3)
        
        # Test data validation
        validation = self.data_service.validate_dataset()
        self.assertTrue(validation["valid"])
        self.assertEqual(len(validation["errors"]), 0)
        
        # Test team filtering
        filtered_teams = self.data_service.filter_teams_by_criteria(
            exclude_teams=[973],
            min_matches=2
        )
        self.assertEqual(len(filtered_teams), 2)  # Should exclude team 973
        
        # Test team aggregation
        teams_for_analysis = self.data_service.get_teams_for_analysis()
        self.assertEqual(len(teams_for_analysis), 3)
        
        # Verify aggregated metrics
        team_1_data = next(t for t in teams_for_analysis if t["team_number"] == 1)
        self.assertIn("metrics", team_1_data)
        self.assertAlmostEqual(team_1_data["metrics"]["autonomous"], 16.33, places=1)

    def test_team_analysis_service(self):
        """Test the TeamAnalysisService functionality."""
        # Test team data preparation
        formatted_teams = self.team_analysis_service.prepare_team_data_for_analysis()
        self.assertEqual(len(formatted_teams), 3)
        
        # Test weighted scoring
        team_data = formatted_teams[0]
        normalized_priorities = self.priority_service.normalize_priorities(self.test_priorities)
        score = self.team_analysis_service.calculate_weighted_score(team_data, normalized_priorities)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        
        # Test similarity scoring
        team1_metrics = formatted_teams[0]["metrics"]
        team2_metrics = formatted_teams[1]["metrics"]
        similarity = self.team_analysis_service.calculate_similarity_score(team1_metrics, team2_metrics)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        
        # Test team ranking
        ranked_teams = self.team_analysis_service.rank_teams_by_score(formatted_teams, normalized_priorities)
        self.assertEqual(len(ranked_teams), 3)
        
        # Verify ranking order (highest score first)
        for i in range(len(ranked_teams) - 1):
            self.assertGreaterEqual(
                ranked_teams[i]["calculated_score"],
                ranked_teams[i + 1]["calculated_score"]
            )

    def test_priority_calculation_service(self):
        """Test the PriorityCalculationService functionality."""
        # Test priority normalization
        normalized = self.priority_service.normalize_priorities(self.test_priorities)
        self.assertEqual(len(normalized), 4)
        
        # Check normalization (should sum to 1.0)
        total_weight = sum(p["weight"] for p in normalized)
        self.assertAlmostEqual(total_weight, 1.0, places=6)
        
        # Test multi-criteria scoring
        team_metrics = {"autonomous": 16, "teleop": 25, "endgame": 10, "defense": 8}
        score_result = self.priority_service.calculate_multi_criteria_score(
            team_metrics, normalized
        )
        self.assertIn("total_score", score_result)
        self.assertIn("breakdown", score_result)
        self.assertGreater(score_result["total_score"], 0)
        
        # Test priority validation
        validation = self.priority_service.validate_priorities(self.test_priorities)
        self.assertTrue(validation["valid"])
        
        # Test invalid priorities
        invalid_priorities = {"autonomous": -1, "teleop": 0}
        invalid_validation = self.priority_service.validate_priorities(invalid_priorities)
        self.assertFalse(invalid_validation["valid"])

    def test_performance_optimization_service(self):
        """Test the PerformanceOptimizationService functionality."""
        # Test cache key generation
        cache_key = self.performance_service.generate_cache_key(
            your_team_number=1678,
            pick_position="first",
            priorities=self.test_priorities,
            exclude_teams=[254]
        )
        self.assertIsInstance(cache_key, str)
        self.assertIn("1678", cache_key)
        self.assertIn("first", cache_key)
        
        # Test cache operations
        test_result = {"status": "success", "picklist": [], "score": 85.2}
        
        # Store result
        self.performance_service.store_cached_result(cache_key, test_result)
        self.assertIn(cache_key, self.shared_cache)
        
        # Retrieve result
        cached_result = self.performance_service.get_cached_result(cache_key)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result["status"], "success")
        
        # Test cache statistics
        stats = self.performance_service.get_cache_statistics()
        self.assertIn("cache_hits", stats)
        self.assertIn("hit_rate_percent", stats)
        self.assertGreater(stats["cache_hits"], 0)
        
        # Test cache cleanup
        cleaned = self.performance_service.cleanup_expired_cache(max_age_seconds=0)
        self.assertGreaterEqual(cleaned, 0)

    def test_batch_processing_service(self):
        """Test the BatchProcessingService functionality."""
        # Test batch calculation
        batch_info = self.batch_service.calculate_batch_info(teams_count=25, batch_size=10)
        self.assertEqual(batch_info["total_batches"], 3)
        self.assertEqual(batch_info["last_batch_size"], 5)
        
        # Test batch processing initialization
        cache_key = "test_batch_123"
        self.batch_service.initialize_batch_processing(cache_key, total_batches=3)
        
        # Verify initialization
        status = self.batch_service.get_batch_processing_status(cache_key)
        self.assertEqual(status["status"], "in_progress")
        self.assertEqual(status["batch_processing"]["total_batches"], 3)
        
        # Test progress updates
        batch_result = {"status": "success", "picklist": [{"team_number": 1, "score": 85}]}
        self.batch_service.update_batch_progress(cache_key, 0, batch_result)
        
        updated_status = self.batch_service.get_batch_processing_status(cache_key)
        self.assertEqual(updated_status["batch_processing"]["current_batch"], 1)
        
        # Test team batching
        teams_data = [{"team_number": i} for i in range(25)]
        batches = self.batch_service.create_team_batches(teams_data, batch_size=10)
        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 10)
        self.assertEqual(len(batches[2]), 5)  # Last batch smaller

    def test_gpt_service_prompt_generation(self):
        """Test the PicklistGPTService prompt generation (without API calls)."""
        # Test system prompt creation
        system_prompt = self.gpt_service.create_system_prompt(
            pick_position="first",
            team_count=10,
            game_context="Test game context"
        )
        self.assertIsInstance(system_prompt, str)
        self.assertIn("first", system_prompt)
        self.assertIn("Test game context", system_prompt)
        
        # Test user prompt creation
        normalized_priorities = self.priority_service.normalize_priorities(self.test_priorities)
        teams_data = self.team_analysis_service.prepare_team_data_for_analysis()
        
        user_prompt = self.gpt_service.create_user_prompt(
            your_team_number=1678,
            pick_position="first",
            priorities=normalized_priorities,
            teams_data=teams_data[:2]  # Use first 2 teams
        )
        self.assertIsInstance(user_prompt, str)
        self.assertIn("1678", user_prompt)
        self.assertIn("PRIORITIES", user_prompt)
        self.assertIn("TEAMS TO ANALYZE", user_prompt)
        
        # Test token counting
        try:
            self.gpt_service.check_token_count(system_prompt, user_prompt)
            # Should not raise exception for reasonable prompts
        except ValueError:
            self.fail("Token count check failed for reasonable prompt size")

    def test_response_parsing(self):
        """Test GPT response parsing functionality."""
        # Test response parsing
        mock_response = {
            "p": [
                [254, 95.5, "Excellent scorer with consistent performance"],
                [1, 87.2, "Strong autonomous and reliable"],
                [973, 78.1, "Good defense and teamwork"]
            ],
            "s": "ok"
        }
        
        teams_data = self.team_analysis_service.prepare_team_data_for_analysis()
        parsed_result = self.gpt_service.parse_response_with_index_mapping(
            mock_response, teams_data
        )
        
        self.assertEqual(len(parsed_result), 3)
        self.assertEqual(parsed_result[0]["team_number"], 254)
        self.assertEqual(parsed_result[0]["score"], 95.5)
        self.assertIn("reasoning", parsed_result[0])

    def test_end_to_end_integration(self):
        """Test end-to-end integration of all services."""
        # 1. Data Aggregation
        teams_for_analysis = self.data_service.get_teams_for_analysis(exclude_teams=[])
        self.assertGreater(len(teams_for_analysis), 0)
        
        # 2. Priority Processing
        normalized_priorities = self.priority_service.normalize_priorities(self.test_priorities)
        self.assertGreater(len(normalized_priorities), 0)
        
        # 3. Team Analysis
        ranked_teams = self.team_analysis_service.rank_teams_by_score(
            teams_for_analysis, normalized_priorities
        )
        self.assertEqual(len(ranked_teams), len(teams_for_analysis))
        
        # 4. Cache Management
        cache_key = self.performance_service.generate_cache_key(
            your_team_number=1678,
            pick_position="first",
            priorities=self.test_priorities
        )
        
        # 5. Batch Processing Setup
        should_batch = self.batch_service.should_use_batching(
            teams_count=len(teams_for_analysis),
            batch_size=2,
            use_batching=True
        )
        self.assertTrue(should_batch)  # 3 teams > batch_size of 2
        
        # 6. Performance Monitoring
        health_report = self.performance_service.get_cache_health_report()
        self.assertIn("health_score", health_report)
        self.assertIn("statistics", health_report)
        
        # Verify data flow integrity
        self.assertGreater(health_report["health_score"], 0)
        self.assertLessEqual(health_report["health_score"], 100)

    def test_error_handling_integration(self):
        """Test error handling across integrated services."""
        # Test invalid dataset path
        invalid_data_service = DataAggregationService("/nonexistent/path.json")
        metadata = invalid_data_service.get_dataset_metadata()
        self.assertEqual(metadata["teams_count"], 0)
        
        # Test empty priorities
        empty_score = self.priority_service.calculate_multi_criteria_score({}, [])
        self.assertEqual(empty_score["total_score"], 0.0)
        
        # Test cache miss
        nonexistent_result = self.performance_service.get_cached_result("nonexistent_key")
        self.assertIsNone(nonexistent_result)
        
        # Test invalid batch processing status
        invalid_status = self.batch_service.get_batch_processing_status("invalid_key")
        self.assertEqual(invalid_status["status"], "not_found")

    def test_service_coordination(self):
        """Test coordination between services in realistic scenarios."""
        # Scenario: Generate cache key and simulate full picklist generation
        
        # 1. Get teams data
        teams_data = self.data_service.get_teams_for_analysis()
        
        # 2. Generate cache key
        cache_key = self.performance_service.generate_cache_key(
            your_team_number=1678,
            pick_position="first", 
            priorities=self.test_priorities,
            team_count=len(teams_data)
        )
        
        # 3. Check cache (should be miss)
        cached_result = self.performance_service.get_cached_result(cache_key)
        self.assertIsNone(cached_result)
        
        # 4. Mark as processing
        self.performance_service.mark_cache_processing(cache_key)
        
        # 5. Check status (should show processing)
        processing_result = self.performance_service.get_cached_result(cache_key)
        self.assertEqual(processing_result["status"], "processing")
        
        # 6. Simulate analysis completion
        normalized_priorities = self.priority_service.normalize_priorities(self.test_priorities)
        ranked_teams = self.team_analysis_service.rank_teams_by_score(teams_data, normalized_priorities)
        
        # 7. Create final result
        final_result = {
            "status": "success",
            "picklist": ranked_teams[:2],  # Top 2 teams
            "total_teams": len(teams_data),
            "processing_time": 1.5
        }
        
        # 8. Store in cache
        self.performance_service.store_cached_result(cache_key, final_result)
        
        # 9. Verify retrieval
        retrieved_result = self.performance_service.get_cached_result(cache_key)
        self.assertEqual(retrieved_result["status"], "success")
        self.assertEqual(len(retrieved_result["picklist"]), 2)
        
        # 10. Verify cache statistics
        stats = self.performance_service.get_cache_statistics()
        self.assertGreater(stats["cache_hits"], 0)


if __name__ == "__main__":
    # Create test suite
    unittest.main(verbosity=2)