"""
Similarity calculations for picklist responses.

Provides utilities for detecting duplicate responses, calculating
similarity between rankings, and normalizing responses for comparison.
"""

import logging
import re
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """
    Calculates various similarity metrics between picklist responses.
    """
    
    def __init__(self):
        """Initialize similarity calculator."""
        pass
    
    def calculate_ranking_similarity(
        self, 
        ranking1: List[Dict[str, Any]], 
        ranking2: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate similarity between two team rankings.
        
        Uses a combination of Jaccard similarity and rank correlation.
        
        Args:
            ranking1: First team ranking
            ranking2: Second team ranking
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not ranking1 or not ranking2:
            return 0.0
        
        # Extract team numbers from rankings
        teams1 = {team.get("team_number", team.get("team")) for team in ranking1}
        teams2 = {team.get("team_number", team.get("team")) for team in ranking2}
        
        # Calculate Jaccard similarity for team overlap
        intersection = len(teams1 & teams2)
        union = len(teams1 | teams2)
        jaccard = intersection / union if union > 0 else 0.0
        
        # Calculate rank correlation for common teams
        rank_correlation = self._calculate_rank_correlation(ranking1, ranking2)
        
        # Weighted combination
        return 0.6 * jaccard + 0.4 * rank_correlation
    
    def calculate_score_similarity(
        self, 
        ranking1: List[Dict[str, Any]], 
        ranking2: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate similarity based on team scores.
        
        Args:
            ranking1: First team ranking
            ranking2: Second team ranking
            
        Returns:
            Score similarity (0.0 to 1.0)
        """
        if not ranking1 or not ranking2:
            return 0.0
        
        # Create score maps
        scores1 = {
            team.get("team_number", team.get("team")): team.get("score", 0.0)
            for team in ranking1
        }
        scores2 = {
            team.get("team_number", team.get("team")): team.get("score", 0.0)
            for team in ranking2
        }
        
        # Find common teams
        common_teams = set(scores1.keys()) & set(scores2.keys())
        if not common_teams:
            return 0.0
        
        # Calculate score differences
        total_diff = 0.0
        max_possible_diff = 0.0
        
        for team in common_teams:
            score1 = scores1[team]
            score2 = scores2[team]
            diff = abs(score1 - score2)
            total_diff += diff
            max_possible_diff += max(abs(score1), abs(score2), 1.0)
        
        # Normalize to 0-1 scale
        if max_possible_diff > 0:
            return 1.0 - (total_diff / max_possible_diff)
        else:
            return 1.0
    
    def _calculate_rank_correlation(
        self, 
        ranking1: List[Dict[str, Any]], 
        ranking2: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate Spearman rank correlation for common teams.
        
        Args:
            ranking1: First ranking
            ranking2: Second ranking
            
        Returns:
            Rank correlation coefficient (0.0 to 1.0)
        """
        # Create rank maps
        ranks1 = {
            team.get("team_number", team.get("team")): idx + 1
            for idx, team in enumerate(ranking1)
        }
        ranks2 = {
            team.get("team_number", team.get("team")): idx + 1
            for idx, team in enumerate(ranking2)
        }
        
        # Find common teams
        common_teams = set(ranks1.keys()) & set(ranks2.keys())
        if len(common_teams) < 2:
            return 0.0
        
        # Calculate rank differences
        rank_diffs = []
        for team in common_teams:
            diff = ranks1[team] - ranks2[team]
            rank_diffs.append(diff ** 2)
        
        n = len(common_teams)
        sum_diff_squared = sum(rank_diffs)
        
        # Spearman correlation coefficient
        if n > 1:
            rho = 1 - (6 * sum_diff_squared) / (n * (n ** 2 - 1))
            # Convert to 0-1 scale
            return (rho + 1) / 2
        else:
            return 0.0


def calculate_jaccard_similarity(set1: Set[Any], set2: Set[Any]) -> float:
    """
    Calculate Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Jaccard similarity coefficient (0.0 to 1.0)
    """
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def calculate_response_similarity(response1: str, response2: str) -> float:
    """
    Calculate similarity between two response strings.
    
    Uses normalized edit distance and token overlap.
    
    Args:
        response1: First response string
        response2: Second response string
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not response1 or not response2:
        return 0.0
    
    # Normalize responses for comparison
    norm1 = normalize_response_for_comparison(response1)
    norm2 = normalize_response_for_comparison(response2)
    
    # Calculate token-based similarity
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    token_similarity = calculate_jaccard_similarity(tokens1, tokens2)
    
    # Calculate character-based similarity using edit distance
    char_similarity = _calculate_edit_distance_similarity(norm1, norm2)
    
    # Weighted combination
    return 0.7 * token_similarity + 0.3 * char_similarity


def normalize_response_for_comparison(response: str) -> str:
    """
    Normalize response text for similarity comparison.
    
    Args:
        response: Raw response text
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    normalized = response.lower()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common formatting
    normalized = re.sub(r'[{}[\]"]', '', normalized)
    
    # Remove numbers (team numbers, scores) for reasoning comparison
    normalized = re.sub(r'\b\d+\.?\d*\b', '', normalized)
    
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    return normalized.strip()


def detect_duplicate_patterns(
    responses: List[str], 
    min_similarity: float = 0.8
) -> List[Tuple[int, int, float]]:
    """
    Detect duplicate or highly similar patterns in responses.
    
    Args:
        responses: List of response strings
        min_similarity: Minimum similarity threshold for duplicates
        
    Returns:
        List of (index1, index2, similarity) tuples for duplicates
    """
    duplicates = []
    
    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            similarity = calculate_response_similarity(responses[i], responses[j])
            if similarity >= min_similarity:
                duplicates.append((i, j, similarity))
    
    return duplicates


def find_repeated_substrings(
    text: str, 
    min_length: int = 10, 
    min_occurrences: int = 3
) -> List[Tuple[str, int]]:
    """
    Find repeated substrings in text that may indicate response loops.
    
    Args:
        text: Text to analyze
        min_length: Minimum substring length
        min_occurrences: Minimum number of occurrences
        
    Returns:
        List of (substring, count) tuples
    """
    repeated = []
    text_lower = text.lower()
    
    # Look for repeated patterns
    for length in range(min_length, len(text) // min_occurrences):
        pattern_counts = {}
        
        for start in range(len(text) - length + 1):
            pattern = text_lower[start:start + length]
            
            # Skip patterns that are mostly whitespace or numbers
            if re.match(r'^[\s\d,.\[\]{}":]+$', pattern):
                continue
            
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Find patterns with sufficient occurrences
        for pattern, count in pattern_counts.items():
            if count >= min_occurrences:
                # Get original case version
                original_pattern = None
                for start in range(len(text) - length + 1):
                    if text[start:start + length].lower() == pattern:
                        original_pattern = text[start:start + length]
                        break
                
                if original_pattern:
                    repeated.append((original_pattern, count))
    
    # Sort by count descending
    repeated.sort(key=lambda x: x[1], reverse=True)
    
    return repeated


def analyze_response_diversity(responses: List[str]) -> Dict[str, Any]:
    """
    Analyze diversity in a set of responses.
    
    Args:
        responses: List of response strings
        
    Returns:
        Dictionary with diversity metrics
    """
    if not responses:
        return {"error": "No responses provided"}
    
    n = len(responses)
    similarities = []
    
    # Calculate pairwise similarities
    for i in range(n):
        for j in range(i + 1, n):
            sim = calculate_response_similarity(responses[i], responses[j])
            similarities.append(sim)
    
    if not similarities:
        return {"single_response": True}
    
    avg_similarity = sum(similarities) / len(similarities)
    max_similarity = max(similarities)
    min_similarity = min(similarities)
    
    # Find duplicates
    duplicates = detect_duplicate_patterns(responses)
    
    # Find repeated patterns
    all_text = " ".join(responses)
    repeated_patterns = find_repeated_substrings(all_text)
    
    return {
        "total_responses": n,
        "average_similarity": round(avg_similarity, 3),
        "max_similarity": round(max_similarity, 3),
        "min_similarity": round(min_similarity, 3),
        "duplicate_pairs": len(duplicates),
        "repeated_patterns": len(repeated_patterns),
        "diversity_score": round(1 - avg_similarity, 3),
        "top_repeated_patterns": repeated_patterns[:3],
    }


def _calculate_edit_distance_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity based on edit distance.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not str1 and not str2:
        return 1.0
    
    if not str1 or not str2:
        return 0.0
    
    # Simple edit distance calculation
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    
    edit_distance = dp[m][n]
    max_length = max(m, n)
    
    # Convert to similarity score
    return 1 - (edit_distance / max_length) if max_length > 0 else 1.0