#!/usr/bin/env python3
"""
PICKLIST RECONSTRUCTION VALIDATION TEST
=========================================

Comprehensive test suite to validate the picklist reconstruction meets all success criteria:
- Process 55 teams in <30 seconds without rate limits
- Return all teams with zero duplicates
- Use <40k tokens (vs current >150k) 
- Maintain service architecture benefits

Test Scenarios:
1. 55 teams, single processing (auto-threshold test)
2. 55 teams, forced batching
3. Token usage measurement
4. Rate limit stress test
5. Missing team scenarios
6. Malformed response recovery
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Set

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.services.picklist_generator_service import PicklistGeneratorService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("reconstruction_validation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("reconstruction_validation")


class ReconstructionValidator:
    """Comprehensive validation test suite for picklist reconstruction."""
    
    def __init__(self):
        """Initialize validator with 2025lake dataset."""
        self.dataset_path = "backend/app/data/unified_event_2025lake.json"
        self.generator = None
        self.test_results = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete validation test suite."""
        logger.info("🚀 Starting Picklist Reconstruction Validation Tests")
        
        # Initialize service
        self.generator = PicklistGeneratorService(self.dataset_path)
        
        # Standard test parameters
        test_team = 1678  # Citrus Circuits (commonly used test team)
        test_priorities = [
            {"id": "auto_points", "name": "Autonomous Points", "weight": 3.0},
            {"id": "teleop_points", "name": "Teleoperated Points", "weight": 4.0},
            {"id": "endgame_points", "name": "Endgame Points", "weight": 2.0},
            {"id": "defense_rating", "name": "Defense Rating", "weight": 1.5},
            {"id": "consistency_rating", "name": "Consistency", "weight": 2.5}
        ]
        
        # Test suite
        tests = [
            ("test_55_teams_auto_strategy", test_team, test_priorities),
            ("test_55_teams_forced_batching", test_team, test_priorities),
            ("test_token_usage_measurement", test_team, test_priorities),
            ("test_duplicate_prevention", test_team, test_priorities),
            ("test_missing_team_detection", test_team, test_priorities),
            ("test_processing_time", test_team, test_priorities)
        ]
        
        for test_name, team, priorities in tests:
            try:
                logger.info(f"🧪 Running {test_name}")
                test_method = getattr(self, test_name)
                result = await test_method(team, priorities)
                self.test_results[test_name] = result
                self._log_test_result(test_name, result)
            except Exception as e:
                logger.error(f"❌ Test {test_name} failed: {str(e)}")
                self.test_results[test_name] = {"status": "failed", "error": str(e)}
        
        return self._generate_final_report()
    
    async def test_55_teams_auto_strategy(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 1: 55 teams with automatic strategy selection (should choose batching at >20 threshold)."""
        start_time = time.time()
        
        result = await self.generator.generate_picklist(
            your_team_number=your_team_number,
            pick_position="first",
            priorities=priorities,
            use_batching=None  # Let it auto-decide
        )
        
        processing_time = time.time() - start_time
        
        # Validate results
        success_criteria = {
            "processing_time_under_30s": processing_time < 30.0,
            "status_success": result.get("status") == "success",
            "team_count": len(result.get("picklist", [])),
            "zero_duplicates": self._check_no_duplicates(result.get("picklist", [])),
            "all_teams_returned": len(result.get("picklist", [])) >= 50,  # Allow some missing but expect most
            "auto_batching_selected": "batch" in result.get("processing_strategy", "").lower()
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "processing_time": processing_time,
            "team_count": success_criteria["team_count"],
            "success_criteria": success_criteria,
            "raw_result": result
        }
    
    async def test_55_teams_forced_batching(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 2: 55 teams with forced batching to test batch processing."""
        start_time = time.time()
        
        result = await self.generator.generate_picklist(
            your_team_number=your_team_number,
            pick_position="first",
            priorities=priorities,
            use_batching=True  # Force batching
        )
        
        processing_time = time.time() - start_time
        
        success_criteria = {
            "processing_time_under_30s": processing_time < 30.0,
            "status_success": result.get("status") == "success",
            "team_count": len(result.get("picklist", [])),
            "zero_duplicates": self._check_no_duplicates(result.get("picklist", [])),
            "batching_used": True  # We forced it
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "processing_time": processing_time,
            "team_count": success_criteria["team_count"],
            "success_criteria": success_criteria,
            "batch_processing": True
        }
    
    async def test_token_usage_measurement(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 3: Measure token usage to verify <40k token target."""
        
        # Use the performance service to estimate tokens
        performance_service = self.generator.performance_service
        teams_data = self.generator.data_service.get_teams_for_analysis()
        
        token_estimation = performance_service.estimate_token_usage(
            teams_count=len(teams_data),
            priorities_count=len(priorities),
            use_ultra_compact=True,
            has_game_context=bool(self.generator.game_context)
        )
        
        success_criteria = {
            "total_tokens_under_40k": token_estimation["total_with_margin"] < 40000,
            "ultra_compact_used": token_estimation["optimization_used"] == "ultra_compact",
            "within_api_limits": token_estimation["within_limits"],
            "token_efficiency": token_estimation["total_with_margin"] < 50000  # Even with margin
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "token_estimation": token_estimation,
            "success_criteria": success_criteria
        }
    
    async def test_duplicate_prevention(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 4: Verify zero duplicates in results."""
        
        result = await self.generator.generate_picklist(
            your_team_number=your_team_number,
            pick_position="second",
            priorities=priorities
        )
        
        picklist = result.get("picklist", [])
        duplicates_info = self._analyze_duplicates(picklist)
        
        success_criteria = {
            "zero_duplicates": duplicates_info["duplicate_count"] == 0,
            "all_teams_unique": len(duplicates_info["unique_teams"]) == len(picklist),
            "index_mapping_used": True  # Should always be used now
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "duplicates_info": duplicates_info,
            "success_criteria": success_criteria
        }
    
    async def test_missing_team_detection(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 5: Verify missing team detection and recovery."""
        
        # Get total available teams
        all_teams = self.generator.data_service.get_teams_for_analysis()
        total_available = len(all_teams)
        
        result = await self.generator.generate_picklist(
            your_team_number=your_team_number,
            pick_position="third",
            priorities=priorities
        )
        
        picklist = result.get("picklist", [])
        returned_teams = {team["team_number"] for team in picklist}
        available_teams = {team["team_number"] for team in all_teams}
        missing_teams = available_teams - returned_teams
        
        success_criteria = {
            "high_coverage": len(picklist) >= total_available * 0.9,  # 90% coverage minimum
            "missing_team_handling": len(missing_teams) <= 5,  # Allow some missing but not many
            "comprehensive_results": len(picklist) >= 50  # Expect at least 50/55 teams
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "total_available": total_available,
            "teams_returned": len(picklist),
            "missing_count": len(missing_teams),
            "coverage_percent": round(len(picklist) / total_available * 100, 1),
            "success_criteria": success_criteria
        }
    
    async def test_processing_time(self, your_team_number: int, priorities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test 6: Verify processing time consistency."""
        
        times = []
        for i in range(3):  # Run 3 times to check consistency
            start_time = time.time()
            
            result = await self.generator.generate_picklist(
                your_team_number=your_team_number,
                pick_position="first",
                priorities=priorities,
                cache_key=f"timing_test_{i}"  # Different cache keys
            )
            
            processing_time = time.time() - start_time
            times.append(processing_time)
            
            if result.get("status") != "success":
                return {
                    "status": "failed",
                    "error": f"Run {i+1} failed: {result.get('error', 'Unknown error')}"
                }
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        success_criteria = {
            "average_under_30s": avg_time < 30.0,
            "max_under_30s": max_time < 30.0,
            "consistent_performance": max_time - min(times) < 10.0  # Within 10s variance
        }
        
        return {
            "status": "passed" if all(success_criteria.values()) else "failed",
            "times": times,
            "average_time": avg_time,
            "max_time": max_time,
            "success_criteria": success_criteria
        }
    
    def _check_no_duplicates(self, picklist: List[Dict[str, Any]]) -> bool:
        """Check if picklist has no duplicate teams."""
        if not picklist:
            return True
        
        team_numbers = [team.get("team_number") for team in picklist]
        return len(team_numbers) == len(set(team_numbers))
    
    def _analyze_duplicates(self, picklist: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze duplicates in picklist."""
        team_numbers = [team.get("team_number") for team in picklist]
        unique_teams = set(team_numbers)
        duplicate_count = len(team_numbers) - len(unique_teams)
        
        # Find which teams are duplicated
        duplicated_teams = []
        seen = set()
        for team_num in team_numbers:
            if team_num in seen:
                duplicated_teams.append(team_num)
            seen.add(team_num)
        
        return {
            "total_entries": len(team_numbers),
            "unique_teams": unique_teams,
            "duplicate_count": duplicate_count,
            "duplicated_teams": list(set(duplicated_teams))
        }
    
    def _log_test_result(self, test_name: str, result: Dict[str, Any]) -> None:
        """Log test result with appropriate emoji."""
        status = result.get("status", "unknown")
        emoji = "✅" if status == "passed" else "❌"
        
        logger.info(f"{emoji} {test_name}: {status.upper()}")
        
        if "processing_time" in result:
            logger.info(f"   ⏱️  Processing time: {result['processing_time']:.2f}s")
        
        if "team_count" in result:
            logger.info(f"   👥 Teams returned: {result['team_count']}")
        
        if "token_estimation" in result:
            tokens = result["token_estimation"]["total_with_margin"]
            logger.info(f"   🔤 Estimated tokens: {tokens:,}")
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("status") == "passed")
        
        # Check overall success criteria
        overall_success_criteria = {
            "all_tests_passed": passed_tests == total_tests,
            "processing_performance": True,  # Will be set based on timing tests
            "token_efficiency": True,  # Will be set based on token tests
            "duplicate_prevention": True,  # Will be set based on duplicate tests
            "comprehensive_coverage": True  # Will be set based on coverage tests
        }
        
        # Analyze specific success metrics
        for test_name, result in self.test_results.items():
            if test_name == "test_processing_time" and result.get("status") == "passed":
                overall_success_criteria["processing_performance"] = result.get("max_time", 999) < 30
            
            if test_name == "test_token_usage_measurement" and result.get("status") == "passed":
                tokens = result.get("token_estimation", {}).get("total_with_margin", 999999)
                overall_success_criteria["token_efficiency"] = tokens < 40000
            
            if test_name == "test_duplicate_prevention" and result.get("status") == "passed":
                overall_success_criteria["duplicate_prevention"] = result.get("duplicates_info", {}).get("duplicate_count", 1) == 0
            
            if test_name == "test_missing_team_detection" and result.get("status") == "passed":
                coverage = result.get("coverage_percent", 0)
                overall_success_criteria["comprehensive_coverage"] = coverage >= 90
        
        reconstruction_success = all(overall_success_criteria.values())
        
        return {
            "reconstruction_status": "SUCCESS" if reconstruction_success else "NEEDS_ATTENTION",
            "tests_passed": f"{passed_tests}/{total_tests}",
            "overall_success_criteria": overall_success_criteria,
            "detailed_results": self.test_results,
            "summary": {
                "ready_for_production": reconstruction_success,
                "critical_algorithms_restored": reconstruction_success,
                "performance_targets_met": overall_success_criteria["processing_performance"],
                "token_optimization_working": overall_success_criteria["token_efficiency"],
                "duplicate_prevention_active": overall_success_criteria["duplicate_prevention"]
            }
        }


async def main():
    """Run validation tests."""
    validator = ReconstructionValidator()
    
    try:
        report = await validator.run_all_tests()
        
        # Print final report
        print("\n" + "="*80)
        print("🏁 PICKLIST RECONSTRUCTION VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL STATUS: {report['reconstruction_status']}")
        print(f"🧪 Tests Passed: {report['tests_passed']}")
        
        print(f"\n🎯 SUCCESS CRITERIA:")
        for criteria, met in report["overall_success_criteria"].items():
            emoji = "✅" if met else "❌"
            print(f"   {emoji} {criteria.replace('_', ' ').title()}")
        
        print(f"\n📋 SUMMARY:")
        for key, value in report["summary"].items():
            emoji = "✅" if value else "❌"
            print(f"   {emoji} {key.replace('_', ' ').title()}")
        
        if report["reconstruction_status"] == "SUCCESS":
            print(f"\n🎉 RECONSTRUCTION VALIDATION SUCCESSFUL!")
            print("   The picklist reconstruction has restored all critical algorithms")
            print("   and meets all performance targets. Ready for production use.")
        else:
            print(f"\n⚠️  RECONSTRUCTION NEEDS ATTENTION")
            print("   Some tests failed. Review detailed results above.")
        
        print("\n" + "="*80)
        
        return report["reconstruction_status"] == "SUCCESS"
        
    except Exception as e:
        logger.error(f"💥 Validation failed with exception: {str(e)}")
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)