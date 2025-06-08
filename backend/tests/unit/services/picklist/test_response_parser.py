"""
Unit tests for ResponseParser.
"""

import json
import pytest

from app.services.picklist.response_parser import ResponseParser
from app.services.picklist.exceptions import GPTResponseError
from app.services.picklist.models import RankedTeam


class TestResponseParser:
    """Test ResponseParser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create ResponseParser instance for testing."""
        return ResponseParser()
    
    @pytest.fixture
    def sample_teams_data(self):
        """Sample teams data for testing."""
        return [
            {"team_number": 1001, "nickname": "Team Alpha", "metrics": {"auto": 10}},
            {"team_number": 1002, "nickname": "Team Beta", "metrics": {"auto": 8}},
            {"team_number": 1003, "nickname": "Team Gamma", "metrics": {"auto": 12}},
        ]
    
    def test_parser_initialization(self, parser):
        """Test ResponseParser initialization."""
        assert parser is not None
        assert hasattr(parser, 'ULTRA_COMPACT_PATTERN')
        assert hasattr(parser, 'COMPACT_PATTERN')
        assert hasattr(parser, 'STANDARD_PATTERN')
    
    def test_clean_response_text_basic(self, parser):
        """Test basic response text cleaning."""
        # Clean text
        clean_text = '{"p": [[1001, 95.0, "Great team"]]}'
        result = parser._clean_response_text(clean_text)
        assert result == clean_text
        
        # Text with markdown
        markdown_text = '```json\n{"p": [[1001, 95.0, "Great team"]]}\n```'
        result = parser._clean_response_text(markdown_text)
        assert result == '{"p": [[1001, 95.0, "Great team"]]}'
        
        # Text with just ```
        simple_markdown = '```\n{"p": [[1001, 95.0, "Great team"]]}\n```'
        result = parser._clean_response_text(simple_markdown)
        assert result == '{"p": [[1001, 95.0, "Great team"]]}'
    
    def test_clean_response_text_empty(self, parser):
        """Test cleaning empty response."""
        with pytest.raises(GPTResponseError, match="Empty response from GPT"):
            parser._clean_response_text("")
        
        with pytest.raises(GPTResponseError, match="Empty response from GPT"):
            parser._clean_response_text(None)
    
    def test_parse_ultra_compact_format_valid(self, parser, sample_teams_data):
        """Test parsing valid ultra-compact format."""
        response_data = {
            "p": [
                [1001, 95.0, "Excellent autonomous"],
                [1002, 90.0, "Strong teleop"],
                [1003, 85.0, "Good all-around"],
            ],
            "s": "ok"
        }
        
        result = parser._parse_ultra_compact_format(response_data, sample_teams_data)
        
        assert len(result) == 3
        assert isinstance(result[0], RankedTeam)
        assert result[0].team_number == 1001
        assert result[0].score == 95.0
        assert result[0].reasoning == "Excellent autonomous"
        assert result[0].nickname == "Team Alpha"
    
    def test_parse_ultra_compact_format_with_index_mapping(self, parser, sample_teams_data):
        """Test parsing ultra-compact format with index mapping."""
        response_data = {
            "p": [
                [0, 95.0, "Excellent autonomous"],  # Index 0 -> Team 1001
                [1, 90.0, "Strong teleop"],        # Index 1 -> Team 1002
            ],
            "s": "ok"
        }
        
        team_index_map = {0: 1001, 1: 1002, 2: 1003}
        
        result = parser._parse_ultra_compact_format(
            response_data, sample_teams_data, team_index_map
        )
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_parse_ultra_compact_format_missing_p_field(self, parser, sample_teams_data):
        """Test parsing ultra-compact format without 'p' field."""
        response_data = {"s": "ok"}
        
        with pytest.raises(GPTResponseError, match="Response missing 'p' field"):
            parser._parse_ultra_compact_format(response_data, sample_teams_data)
    
    def test_parse_ultra_compact_format_invalid_entries(self, parser, sample_teams_data):
        """Test parsing ultra-compact format with invalid entries."""
        response_data = {
            "p": [
                [1001, 95.0, "Valid entry"],
                [1002],  # Too few elements
                ["invalid", 90.0, "Invalid team number"],
                [1003, "invalid", "Invalid score"],
            ],
            "s": "ok"
        }
        
        result = parser._parse_ultra_compact_format(response_data, sample_teams_data)
        
        # Should only return valid entry
        assert len(result) == 1
        assert result[0].team_number == 1001
    
    def test_parse_ultra_compact_format_duplicates(self, parser, sample_teams_data):
        """Test parsing ultra-compact format with duplicate teams."""
        response_data = {
            "p": [
                [1001, 95.0, "First entry"],
                [1002, 90.0, "Valid entry"],
                [1001, 85.0, "Duplicate entry"],
            ],
            "s": "ok"
        }
        
        result = parser._parse_ultra_compact_format(response_data, sample_teams_data)
        
        # Should skip duplicate
        assert len(result) == 2
        team_numbers = [t.team_number for t in result]
        assert 1001 in team_numbers
        assert 1002 in team_numbers
        assert team_numbers.count(1001) == 1
    
    def test_parse_standard_format(self, parser, sample_teams_data):
        """Test parsing standard picklist format."""
        picklist_data = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Great team"},
            {"team": 1002, "score": 90.0, "reason": "Good backup"},  # Alternative field names
        ]
        
        result = parser._parse_standard_format(picklist_data, sample_teams_data)
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_parse_list_format_arrays(self, parser, sample_teams_data):
        """Test parsing direct list format with arrays."""
        response_list = [
            [1001, 95.0, "Great team"],
            [1002, 90.0, "Good backup"],
        ]
        
        result = parser._parse_list_format(response_list, sample_teams_data)
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_parse_list_format_dicts(self, parser, sample_teams_data):
        """Test parsing direct list format with dictionaries."""
        response_list = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Great team"},
            {"team": 1002, "score": 90.0, "reason": "Good backup"},
        ]
        
        result = parser._parse_list_format(response_list, sample_teams_data)
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_parse_json_response_ultra_compact(self, parser, sample_teams_data):
        """Test main JSON parsing with ultra-compact format."""
        response_data = {
            "p": [[1001, 95.0, "Great team"]],
            "s": "ok"
        }
        
        result = parser._parse_json_response(response_data, sample_teams_data)
        
        assert len(result) == 1
        assert result[0].team_number == 1001
    
    def test_parse_json_response_standard(self, parser, sample_teams_data):
        """Test main JSON parsing with standard format."""
        response_data = {
            "picklist": [
                {"team_number": 1001, "score": 95.0, "reasoning": "Great team"}
            ]
        }
        
        result = parser._parse_json_response(response_data, sample_teams_data)
        
        assert len(result) == 1
        assert result[0].team_number == 1001
    
    def test_parse_json_response_unknown_format(self, parser, sample_teams_data):
        """Test main JSON parsing with unknown format."""
        response_data = {"unknown_field": "value"}
        
        with pytest.raises(GPTResponseError, match="Unknown response format"):
            parser._parse_json_response(response_data, sample_teams_data)
    
    def test_parse_gpt_response_valid_json(self, parser, sample_teams_data):
        """Test full GPT response parsing with valid JSON."""
        response_text = '{"p": [[1001, 95.0, "Great team"]], "s": "ok"}'
        
        result = parser.parse_gpt_response(response_text, sample_teams_data)
        
        assert len(result) == 1
        assert result[0].team_number == 1001
    
    def test_parse_gpt_response_with_markdown(self, parser, sample_teams_data):
        """Test GPT response parsing with markdown formatting."""
        response_text = '''```json
        {"p": [[1001, 95.0, "Great team"]], "s": "ok"}
        ```'''
        
        result = parser.parse_gpt_response(response_text, sample_teams_data)
        
        assert len(result) == 1
        assert result[0].team_number == 1001
    
    def test_parse_gpt_response_invalid_json_with_recovery(self, parser, sample_teams_data):
        """Test GPT response parsing with invalid JSON and error recovery."""
        # Malformed JSON that should be recoverable with regex
        response_text = 'Some preamble [1001, 95.0, "Great team"] and [1002, 90.0, "Good backup"] postamble'
        
        result = parser.parse_gpt_response(response_text, sample_teams_data)
        
        assert len(result) >= 1  # Should recover at least one team
    
    def test_repair_json_basic(self, parser):
        """Test basic JSON repair functionality."""
        # Unescaped quotes
        malformed = '{"reason": "It"s great"}'
        repaired = parser._repair_json(malformed)
        # Note: Simple repair might not fix all cases, but should attempt fixes
        assert repaired != malformed
        
        # Trailing commas
        malformed_comma = '{"team": 1001, "score": 95.0,}'
        repaired_comma = parser._repair_json(malformed_comma)
        assert repaired_comma == '{"team": 1001, "score": 95.0}'
    
    def test_extract_ultra_compact_teams(self, parser, sample_teams_data):
        """Test regex extraction of ultra-compact teams."""
        response_text = '''
        Some text before [1001, 95.0, "Great team"] and
        more text [1002, 90.0, "Good backup"] and some after
        '''
        
        result = parser._extract_ultra_compact_teams(
            response_text, sample_teams_data, parser.ULTRA_COMPACT_PATTERN
        )
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_extract_compact_teams(self, parser, sample_teams_data):
        """Test regex extraction of compact teams."""
        response_text = '''
        {"team":1001,"score":95.0,"reason":"Great team"}
        {"team":1002,"score":90.0,"reason":"Good backup"}
        '''
        
        result = parser._extract_compact_teams(
            response_text, sample_teams_data, parser.COMPACT_PATTERN
        )
        
        assert len(result) == 2
        assert result[0].team_number == 1001
        assert result[1].team_number == 1002
    
    def test_create_ranked_team_valid(self, parser, sample_teams_data):
        """Test creating ranked team with valid data."""
        result = parser._create_ranked_team(1001, 95.0, "Great team", sample_teams_data)
        
        assert result is not None
        assert isinstance(result, RankedTeam)
        assert result.team_number == 1001
        assert result.score == 95.0
        assert result.reasoning == "Great team"
        assert result.nickname == "Team Alpha"
        assert result.metrics == {"auto": 10}
    
    def test_create_ranked_team_not_found(self, parser, sample_teams_data):
        """Test creating ranked team with team not in data."""
        result = parser._create_ranked_team(9999, 95.0, "Unknown team", sample_teams_data)
        
        assert result is None
    
    def test_resolve_duplicate_teams(self, parser):
        """Test duplicate team resolution."""
        ranked_teams = [
            RankedTeam(team_number=1001, nickname="Team Alpha", score=95.0, reasoning="First"),
            RankedTeam(team_number=1002, nickname="Team Beta", score=90.0, reasoning="Unique"),
            RankedTeam(team_number=1001, nickname="Team Alpha", score=85.0, reasoning="Second"),
        ]
        
        result = parser.resolve_duplicate_teams(ranked_teams)
        
        assert len(result) == 2
        team_numbers = [t.team_number for t in result]
        assert 1001 in team_numbers
        assert 1002 in team_numbers
        assert team_numbers.count(1001) == 1
        
        # Should keep the one with higher score (95.0)
        team_1001 = next(t for t in result if t.team_number == 1001)
        assert team_1001.score == 95.0
        assert team_1001.reasoning == "First"
    
    def test_detect_response_patterns(self, parser):
        """Test response pattern detection."""
        # Ultra-compact format
        ultra_compact_text = '{"p": [[1001, 95.0, "Great"]], "s": "ok"}'
        analysis = parser.detect_response_patterns(ultra_compact_text)
        
        assert analysis["format"] == "ultra_compact"
        assert analysis["has_json"] is True
        assert analysis["ultra_compact_matches"] > 0
        
        # Standard format
        standard_text = '{"picklist": [{"team_number": 1001, "score": 95.0}]}'
        analysis = parser.detect_response_patterns(standard_text)
        
        assert analysis["format"] == "standard"
        assert analysis["has_json"] is True
        
        # Markdown format
        markdown_text = '```json\n{"p": [[1001, 95.0, "Great"]]}\n```'
        analysis = parser.detect_response_patterns(markdown_text)
        
        assert analysis["has_markdown"] is True
    
    def test_parse_with_error_recovery_complete_failure(self, parser, sample_teams_data):
        """Test error recovery when all methods fail."""
        # Completely unparseable text
        response_text = "This is completely unparseable text with no team data whatsoever"
        
        with pytest.raises(GPTResponseError, match="All parsing and recovery attempts failed"):
            parser._parse_with_error_recovery(response_text, sample_teams_data)
    
    def test_edge_cases_empty_data(self, parser):
        """Test edge cases with empty data."""
        # Empty teams data
        response_text = '{"p": [[1001, 95.0, "Great team"]], "s": "ok"}'
        result = parser.parse_gpt_response(response_text, [])
        
        assert len(result) == 0  # No teams found in empty data
    
    def test_edge_cases_malformed_entries(self, parser, sample_teams_data):
        """Test edge cases with various malformed entries."""
        response_data = {
            "p": [
                [],  # Empty array
                [1001],  # Missing elements
                [1001, 95.0],  # Missing reasoning
                [1001, 95.0, "Valid", "extra"],  # Extra elements (should still work)
                ["not_a_number", 95.0, "Invalid team"],
                [1001, "not_a_number", "Invalid score"],
            ],
            "s": "ok"
        }
        
        result = parser._parse_ultra_compact_format(response_data, sample_teams_data)
        
        # Should extract the valid entry (with extra elements)
        assert len(result) == 1
        assert result[0].team_number == 1001