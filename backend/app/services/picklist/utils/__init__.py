"""
Utilities package for picklist service.

Contains JSON utilities, similarity calculations, and validation helpers.
"""

from .json_utils import (
    JSONCompressor,
    JSONValidator,
    UltraCompactFormatter,
    compact_json,
    format_ultra_compact,
    validate_json_structure,
)
from .similarity_utils import (
    SimilarityCalculator,
    calculate_jaccard_similarity,
    calculate_response_similarity,
    detect_duplicate_patterns,
    normalize_response_for_comparison,
)
from .validation_utils import (
    PicklistValidator,
    validate_batch_parameters,
    validate_picklist_request,
    validate_team_data,
    validate_team_numbers,
)

__all__ = [
    # JSON utilities
    "JSONCompressor",
    "JSONValidator", 
    "UltraCompactFormatter",
    "compact_json",
    "format_ultra_compact",
    "validate_json_structure",
    # Similarity utilities
    "SimilarityCalculator",
    "calculate_jaccard_similarity",
    "calculate_response_similarity",
    "detect_duplicate_patterns",
    "normalize_response_for_comparison",
    # Validation utilities
    "PicklistValidator",
    "validate_batch_parameters",
    "validate_picklist_request",
    "validate_team_data",
    "validate_team_numbers",
]