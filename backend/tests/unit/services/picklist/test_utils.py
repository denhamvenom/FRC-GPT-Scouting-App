"""
Unit tests for picklist utils modules.
"""

import pytest

from app.services.picklist.utils.json_utils import (
    JSONCompressor,
    UltraCompactFormatter,
    JSONValidator,
    compact_json,
    format_ultra_compact,
    validate_json_structure,
    calculate_token_savings,
)
from app.services.picklist.utils.similarity_utils import (
    SimilarityCalculator,
    calculate_jaccard_similarity,
    calculate_response_similarity,
    detect_duplicate_patterns,
    normalize_response_for_comparison,
    analyze_response_diversity,
)
from app.services.picklist.utils.validation_utils import (
    PicklistValidator,
    validate_picklist_request,
    validate_team_numbers,
    validate_batch_parameters,
    is_valid_team_number,
    sanitize_team_numbers,
)
from app.services.picklist.exceptions import PicklistValidationError


class TestJSONUtils:
    """Test JSON utilities."""
    
    @pytest.fixture
    def compressor(self):
        """Create JSONCompressor instance."""
        return JSONCompressor()
    
    @pytest.fixture
    def formatter(self):
        """Create UltraCompactFormatter instance."""
        return UltraCompactFormatter()
    
    @pytest.fixture
    def validator(self):
        """Create JSONValidator instance."""
        return JSONValidator()
    
    @pytest.fixture
    def sample_team_data(self):
        """Sample team data for testing."""
        return {
            "team_number": 1001,
            "nickname": "Team Alpha",
            "score": 95.5,
            "reasoning": "Excellent autonomous performance",
            "metrics": {"auto": 10, "teleop": 20},
            "priority": None,  # Null value for testing
        }
    
    def test_json_compressor_abbreviate_fields(self, compressor, sample_team_data):
        """Test field abbreviation."""
        abbreviated = compressor._abbreviate_fields(sample_team_data)
        
        assert abbreviated["t"] == 1001  # team_number -> t
        assert abbreviated["n"] == "Team Alpha"  # nickname -> n
        assert abbreviated["s"] == 95.5  # score -> s
        assert abbreviated["r"] == "Excellent autonomous performance"  # reasoning -> r
        assert "priority" not in abbreviated  # Null values removed
    
    def test_json_compressor_expand_fields(self, compressor):
        """Test field expansion."""
        abbreviated_data = {"t": 1001, "n": "Team Alpha", "s": 95.5}
        expanded = compressor._expand_fields(abbreviated_data)
        
        assert expanded["team_number"] == 1001
        assert expanded["nickname"] == "Team Alpha"
        assert expanded["score"] == 95.5
    
    def test_json_compressor_remove_nulls(self, compressor):
        """Test null value removal."""
        data_with_nulls = {
            "team": 1001,
            "score": 95.5,
            "null_field": None,
            "empty_string": "",
            "empty_list": [],
            "valid_zero": 0,
            "nested": {"null_nested": None, "valid_nested": "value"}
        }
        
        cleaned = compressor._remove_nulls(data_with_nulls)
        
        assert "null_field" not in cleaned
        assert "empty_string" not in cleaned
        assert "empty_list" not in cleaned
        assert cleaned["valid_zero"] == 0  # Zero should be kept
        assert cleaned["nested"]["valid_nested"] == "value"
        assert "null_nested" not in cleaned["nested"]
    
    def test_json_compressor_compress_decompress(self, compressor, sample_team_data):
        """Test compression and decompression roundtrip."""
        compressed = compressor.compress_json(sample_team_data)
        decompressed = compressor.decompress_json(compressed)
        
        # Should preserve important data (nulls may be removed)
        assert decompressed["team_number"] == sample_team_data["team_number"]
        assert decompressed["nickname"] == sample_team_data["nickname"]
        assert decompressed["score"] == sample_team_data["score"]
    
    def test_ultra_compact_formatter_format_picklist(self, formatter):
        """Test ultra-compact formatting."""
        teams = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Great team"},
            {"team": 1002, "score": 90.0, "reason": "Good backup"},
        ]
        
        result = formatter.format_picklist(teams, status="ok")
        data = eval(result)  # Safe since we control the format
        
        assert data["s"] == "ok"
        assert len(data["p"]) == 2
        assert data["p"][0] == [1001, 95.0, "Great team"]
        assert data["p"][1] == [1002, 90.0, "Good backup"]
    
    def test_ultra_compact_formatter_parse(self, formatter):
        """Test ultra-compact parsing."""
        ultra_compact_str = '{"p": [[1001, 95.0, "Great"], [1002, 90.0, "Good"]], "s": "ok"}'
        teams, status = formatter.parse_ultra_compact(ultra_compact_str)
        
        assert status == "ok"
        assert len(teams) == 2
        assert teams[0] == (1001, 95.0, "Great")
        assert teams[1] == (1002, 90.0, "Good")
    
    def test_ultra_compact_formatter_with_index_mapping(self, formatter):
        """Test ultra-compact formatting with index mapping."""
        teams = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Great"},
            {"team_number": 1002, "score": 90.0, "reasoning": "Good"},
        ]
        
        json_str, index_map = formatter.create_with_index_mapping(teams, create_index_map=True)
        
        assert index_map == {0: 1001, 1: 1002}
        
        data = eval(json_str)
        assert data["p"][0][0] == 0  # Uses index instead of team number
        assert data["p"][1][0] == 1
    
    def test_json_validator_ultra_compact_valid(self, validator):
        """Test validation of valid ultra-compact format."""
        data = {
            "p": [
                [1001, 95.0, "Great team"],
                [1002, 90.0, "Good backup"],
            ],
            "s": "ok"
        }
        
        errors = validator.validate_picklist_response(data)
        assert len(errors) == 0
    
    def test_json_validator_ultra_compact_invalid(self, validator):
        """Test validation of invalid ultra-compact format."""
        data = {
            "p": [
                [1001],  # Too few elements
                ["invalid", 95.0, "Bad team number"],
                [1002, "invalid", "Bad score"],
                "not_a_list",  # Not a list
            ]
        }
        
        errors = validator.validate_picklist_response(data)
        assert len(errors) > 0
        assert any("must have at least 3 elements" in error for error in errors)
        assert any("team number must be integer" in error for error in errors)
        assert any("score must be numeric" in error for error in errors)
    
    def test_json_validator_standard_format(self, validator):
        """Test validation of standard format."""
        data = {
            "picklist": [
                {"team_number": 1001, "score": 95.0, "reasoning": "Great"},
                {"team_number": 1002, "score": 90.0},  # Missing reasoning is OK
            ]
        }
        
        errors = validator.validate_picklist_response(data)
        assert len(errors) == 0
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        data = {"team_number": 1001, "score": 95.0, "reasoning": None}
        
        # compact_json
        compressed = compact_json(data)
        assert len(compressed) < len(str(data))
        
        # format_ultra_compact
        teams = [{"team_number": 1001, "score": 95.0, "reasoning": "Great"}]
        ultra_compact = format_ultra_compact(teams)
        assert '"p":' in ultra_compact
        
        # validate_json_structure
        valid_data = {"p": [[1001, 95.0, "Great"]], "s": "ok"}
        errors = validate_json_structure(valid_data)
        assert len(errors) == 0
    
    def test_calculate_token_savings(self):
        """Test token savings calculation."""
        original = '{"team_number": 1001, "score": 95.0, "reasoning": "Great team"}'
        compressed = '{"t":1001,"s":95.0,"r":"Great team"}'
        
        savings = calculate_token_savings(original, compressed)
        
        assert savings["original_length"] == len(original)
        assert savings["compressed_length"] == len(compressed)
        assert savings["bytes_saved"] > 0
        assert savings["savings_percent"] > 0
        assert savings["compression_ratio"] < 1.0


class TestSimilarityUtils:
    """Test similarity utilities."""
    
    @pytest.fixture
    def calculator(self):
        """Create SimilarityCalculator instance."""
        return SimilarityCalculator()
    
    def test_calculate_jaccard_similarity(self):
        """Test Jaccard similarity calculation."""
        set1 = {1, 2, 3, 4}
        set2 = {3, 4, 5, 6}
        
        similarity = calculate_jaccard_similarity(set1, set2)
        expected = 2 / 6  # 2 intersection, 6 union
        assert similarity == expected
        
        # Empty sets
        assert calculate_jaccard_similarity(set(), set()) == 1.0
        assert calculate_jaccard_similarity({1, 2}, set()) == 0.0
    
    def test_calculate_ranking_similarity(self, calculator):
        """Test ranking similarity calculation."""
        ranking1 = [
            {"team_number": 1001, "score": 95.0},
            {"team_number": 1002, "score": 90.0},
            {"team_number": 1003, "score": 85.0},
        ]
        
        ranking2 = [
            {"team_number": 1001, "score": 94.0},  # Same team, different score
            {"team_number": 1003, "score": 86.0},  # Different order
            {"team_number": 1002, "score": 89.0},
        ]
        
        similarity = calculator.calculate_ranking_similarity(ranking1, ranking2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5  # Should have high similarity (same teams)
        
        # Different teams
        ranking3 = [
            {"team_number": 2001, "score": 95.0},
            {"team_number": 2002, "score": 90.0},
        ]
        
        similarity_low = calculator.calculate_ranking_similarity(ranking1, ranking3)
        assert similarity_low < similarity
    
    def test_calculate_score_similarity(self, calculator):
        """Test score-based similarity calculation."""
        ranking1 = [
            {"team_number": 1001, "score": 95.0},
            {"team_number": 1002, "score": 90.0},
        ]
        
        ranking2 = [
            {"team_number": 1001, "score": 94.0},  # Close score
            {"team_number": 1002, "score": 89.0},  # Close score
        ]
        
        similarity = calculator.calculate_score_similarity(ranking1, ranking2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.8  # Should be high due to close scores
    
    def test_normalize_response_for_comparison(self):
        """Test response normalization."""
        response = 'Team 1001 is "excellent" with score 95.5!'
        normalized = normalize_response_for_comparison(response)
        
        assert normalized.lower() == normalized
        assert "team" in normalized
        assert "excellent" in normalized
        assert "1001" not in normalized  # Numbers should be removed
        assert "95.5" not in normalized
        assert '"' not in normalized  # Quotes should be removed
        assert '!' not in normalized  # Punctuation should be removed
    
    def test_calculate_response_similarity(self):
        """Test response similarity calculation."""
        response1 = "Team 1001 is excellent for alliance captain role"
        response2 = "Team 1001 would be great as alliance captain"
        response3 = "Team 2002 is terrible and should be avoided"
        
        # Similar responses
        sim_high = calculate_response_similarity(response1, response2)
        assert 0.0 <= sim_high <= 1.0
        assert sim_high > 0.3
        
        # Different responses
        sim_low = calculate_response_similarity(response1, response3)
        assert sim_low < sim_high
    
    def test_detect_duplicate_patterns(self):
        """Test duplicate pattern detection."""
        responses = [
            "Team 1001 is excellent",
            "Team 1002 is good",
            "Team 1001 is excellent",  # Exact duplicate
            "Team 1003 is okay",
        ]
        
        duplicates = detect_duplicate_patterns(responses, min_similarity=0.9)
        
        assert len(duplicates) > 0
        # Should find duplicate between index 0 and 2
        assert any(pair[0] == 0 and pair[1] == 2 for pair in duplicates)
    
    def test_analyze_response_diversity(self):
        """Test response diversity analysis."""
        responses = [
            "Team 1001 is excellent",
            "Team 1002 is good",
            "Team 1001 is excellent",  # Duplicate
            "Team 1003 is okay",
        ]
        
        analysis = analyze_response_diversity(responses)
        
        assert analysis["total_responses"] == 4
        assert "average_similarity" in analysis
        assert "duplicate_pairs" in analysis
        assert analysis["duplicate_pairs"] > 0  # Should detect duplicates
        
        # Empty responses
        empty_analysis = analyze_response_diversity([])
        assert "error" in empty_analysis


class TestValidationUtils:
    """Test validation utilities."""
    
    @pytest.fixture
    def validator(self):
        """Create PicklistValidator instance."""
        return PicklistValidator()
    
    def test_validate_team_number_valid(self, validator):
        """Test valid team number validation."""
        errors = validator.validate_team_number(1001)
        assert len(errors) == 0
        
        # String that can be converted
        errors = validator.validate_team_number("1001")
        assert len(errors) == 0
    
    def test_validate_team_number_invalid(self, validator):
        """Test invalid team number validation."""
        # Non-numeric
        errors = validator.validate_team_number("abc")
        assert len(errors) > 0
        assert "must be an integer" in errors[0]
        
        # Out of range
        errors = validator.validate_team_number(-1)
        assert len(errors) > 0
        assert "below minimum" in errors[0]
        
        errors = validator.validate_team_number(999999)
        assert len(errors) > 0
        assert "exceeds maximum" in errors[0]
    
    def test_validate_team_numbers_valid(self, validator):
        """Test valid team numbers list validation."""
        team_numbers = [1001, 1002, 1003]
        errors = validator.validate_team_numbers(team_numbers)
        assert len(errors) == 0
    
    def test_validate_team_numbers_invalid(self, validator):
        """Test invalid team numbers list validation."""
        # Not a list
        errors = validator.validate_team_numbers("not_a_list")
        assert len(errors) > 0
        assert "must be a list" in errors[0]
        
        # Duplicates
        team_numbers = [1001, 1002, 1001]
        errors = validator.validate_team_numbers(team_numbers)
        assert len(errors) > 0
        assert any("Duplicate team number" in error for error in errors)
    
    def test_validate_priorities_valid(self, validator):
        """Test valid priorities validation."""
        priorities = [
            {"id": "auto", "name": "Autonomous", "weight": 0.4},
            {"id": "teleop", "name": "Teleoperated", "weight": 0.6},
        ]
        
        errors = validator.validate_priorities(priorities)
        assert len(errors) == 0
    
    def test_validate_priorities_invalid(self, validator):
        """Test invalid priorities validation."""
        # Empty priorities
        errors = validator.validate_priorities([])
        assert len(errors) > 0
        assert "At least one priority metric is required" in errors[0]
        
        # Missing fields
        priorities = [{"id": "auto"}]  # Missing name and weight
        errors = validator.validate_priorities(priorities)
        assert len(errors) > 0
        assert any("missing required field" in error for error in errors)
        
        # Invalid weights
        priorities = [
            {"id": "auto", "name": "Auto", "weight": -0.1},  # Negative
            {"id": "teleop", "name": "Teleop", "weight": 1.5},  # Too high
        ]
        errors = validator.validate_priorities(priorities)
        assert len(errors) > 0
        assert any("weight must be non-negative" in error for error in errors)
    
    def test_validate_batch_parameters_valid(self, validator):
        """Test valid batch parameters validation."""
        errors = validator.validate_batch_parameters(20, 5)
        assert len(errors) == 0
    
    def test_validate_batch_parameters_invalid(self, validator):
        """Test invalid batch parameters validation."""
        # Batch size too small
        errors = validator.validate_batch_parameters(3, 1)
        assert len(errors) > 0
        assert any("must be at least" in error for error in errors)
        
        # Reference teams too many
        errors = validator.validate_batch_parameters(10, 6)
        assert len(errors) > 0
        assert any("cannot exceed half" in error for error in errors)
    
    def test_validate_team_data_valid(self, validator):
        """Test valid team data validation."""
        teams_data = [
            {"team_number": 1001, "nickname": "Team Alpha"},
            {"team_number": 1002, "nickname": "Team Beta", "metrics": {"auto": 10}},
        ]
        
        errors = validator.validate_team_data(teams_data)
        assert len(errors) == 0
    
    def test_validate_team_data_invalid(self, validator):
        """Test invalid team data validation."""
        # Empty data
        errors = validator.validate_team_data([])
        assert len(errors) > 0
        assert "cannot be empty" in errors[0]
        
        # Missing team_number
        teams_data = [{"nickname": "Team Alpha"}]
        errors = validator.validate_team_data(teams_data)
        assert len(errors) > 0
        assert any("missing team_number" in error for error in errors)
    
    def test_convenience_functions_valid(self):
        """Test convenience functions with valid data."""
        # Should not raise exceptions
        validate_team_numbers([1001, 1002, 1003])
        validate_batch_parameters(20, 5)
        
        assert is_valid_team_number(1001) is True
        assert is_valid_team_number("abc") is False
    
    def test_convenience_functions_invalid(self):
        """Test convenience functions with invalid data."""
        # Should raise exceptions
        with pytest.raises(PicklistValidationError):
            validate_team_numbers([1001, "invalid"])
        
        with pytest.raises(PicklistValidationError):
            validate_batch_parameters(3, 1)
    
    def test_sanitize_team_numbers(self):
        """Test team number sanitization."""
        mixed_input = [1001, "1002", "invalid", -1, 1003, 999999]
        sanitized = sanitize_team_numbers(mixed_input)
        
        assert sanitized == [1001, 1002, 1003]  # Only valid teams
    
    def test_validate_picklist_request_complete(self):
        """Test complete picklist request validation."""
        valid_request = {
            "your_team_number": 1001,
            "priorities": [
                {"id": "auto", "name": "Autonomous", "weight": 0.5},
                {"id": "teleop", "name": "Teleoperated", "weight": 0.5},
            ],
            "exclude_teams": [1002, 1003],
            "use_batching": True,
            "batch_size": 20,
            "reference_teams_count": 5,
        }
        
        # Should not raise exception
        validate_picklist_request(valid_request)
        
        # Invalid request
        invalid_request = {"your_team_number": "invalid"}
        with pytest.raises(PicklistValidationError):
            validate_picklist_request(invalid_request)