# backend/app/services/game_context_extractor_service.py

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
import tiktoken

from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger("game_context_extractor")

GPT_MODEL = OPENAI_MODEL


class ExtractionResult:
    """Data class for extraction results with validation."""
    
    def __init__(
        self,
        success: bool,
        extracted_context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        processing_time: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        validation_score: float = 0.0
    ):
        self.success = success
        self.extracted_context = extracted_context
        self.error = error
        self.processing_time = processing_time
        self.token_usage = token_usage or {}
        self.validation_score = validation_score
        self.timestamp = datetime.now().isoformat()


class ValidationResult:
    """Data class for extraction validation results."""
    
    def __init__(
        self,
        is_valid: bool,
        completeness_score: float,
        accuracy_score: float,
        issues: List[str],
        recommendations: List[str]
    ):
        self.is_valid = is_valid
        self.completeness_score = completeness_score
        self.accuracy_score = accuracy_score
        self.overall_score = (completeness_score + accuracy_score) / 2
        self.issues = issues
        self.recommendations = recommendations


class GameContextExtractorService:
    """
    Service for extracting essential game information from FRC game manuals.
    
    This service processes large game manual texts once to extract only the information
    needed for alliance selection and team evaluation, significantly reducing token usage
    in subsequent GPT API calls.
    
    Thread Safety: Thread-safe for read operations, synchronization required for cache writes
    Dependencies: OpenAI API, file system access for caching
    """
    
    def __init__(self, cache_dir: str = "backend/app/cache/game_context"):
        """
        Initialize the game context extractor.
        
        Args:
            cache_dir: Directory to store extracted context cache files
            
        Raises:
            ValueError: If OpenAI API key is not configured
            OSError: If cache directory cannot be created
        """
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
            
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Handle tiktoken encoding with fallback for unsupported models
        try:
            self.token_encoder = tiktoken.encoding_for_model(GPT_MODEL)
        except KeyError:
            self.token_encoder = tiktoken.get_encoding("cl100k_base")
            logger.info(f"Using fallback encoding 'cl100k_base' for model {GPT_MODEL}")
        
        self.cache_dir = cache_dir
        self.max_tokens = 4000  # Max tokens for extraction response
        self.extraction_version = "1.0"
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Initialized GameContextExtractorService with cache dir: {cache_dir}")

    async def extract_game_context(
        self,
        manual_data: Dict[str, Any],
        force_refresh: bool = False
    ) -> ExtractionResult:
        """
        Extract relevant context from game manual data.
        
        Args:
            manual_data: Dictionary containing game manual information
            force_refresh: If True, bypass cache and re-extract
            
        Returns:
            ExtractionResult containing extracted context or error information
            
        Raises:
            ValueError: If manual_data is invalid
            Exception: If extraction process fails critically
        """
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_manual_data(manual_data)
            
            # Generate cache key based on manual content
            cache_key = self._generate_cache_key(manual_data)
            
            # Check cache first unless force refresh
            if not force_refresh:
                cached_result = self._load_cached_extraction(cache_key)
                if cached_result:
                    logger.info(f"Returning cached extraction for key: {cache_key[:16]}...")
                    return cached_result
                    
            # Perform extraction
            logger.info("Starting game context extraction")
            extraction_result = await self._perform_extraction(manual_data)
            
            if extraction_result.success:
                # Validate extraction quality
                validation = self.validate_extraction(
                    extraction_result.extracted_context,
                    manual_data
                )
                extraction_result.validation_score = validation.overall_score
                
                # Cache result if validation passes
                if validation.is_valid:
                    self._cache_extraction(cache_key, extraction_result)
                    logger.info(f"Extraction completed successfully (score: {validation.overall_score:.2f})")
                else:
                    logger.warning(f"Extraction validation failed (score: {validation.overall_score:.2f})")
                    logger.warning(f"Issues: {', '.join(validation.issues)}")
                    
            extraction_result.processing_time = time.time() - start_time
            return extraction_result
            
        except Exception as e:
            logger.error(f"Critical error in extract_game_context: {str(e)}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                processing_time=time.time() - start_time
            )

    def validate_extraction(
        self,
        extracted_context: Dict[str, Any],
        original_manual: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate extraction completeness and accuracy.
        
        Args:
            extracted_context: The extracted context to validate
            original_manual: Original manual data for comparison
            
        Returns:
            ValidationResult with validation scores and recommendations
        """
        issues = []
        recommendations = []
        
        # Check required fields
        required_fields = [
            'game_year', 'game_name', 'scoring_summary',
            'strategic_elements', 'key_metrics'
        ]
        
        completeness_score = 0.0
        for field in required_fields:
            if field in extracted_context and extracted_context[field]:
                completeness_score += 1.0
            else:
                issues.append(f"Missing or empty required field: {field}")
                
        completeness_score = completeness_score / len(required_fields)
        
        # Check for content quality
        accuracy_score = 1.0  # Start optimistic
        
        # Validate scoring summary structure
        if 'scoring_summary' in extracted_context:
            scoring = extracted_context['scoring_summary']
            if not isinstance(scoring, dict):
                issues.append("scoring_summary should be a dictionary")
                accuracy_score -= 0.2
            else:
                expected_phases = ['autonomous', 'teleop', 'endgame']
                for phase in expected_phases:
                    if phase not in scoring:
                        recommendations.append(f"Consider adding {phase} to scoring_summary")
                        
        # Check strategic elements
        if 'strategic_elements' in extracted_context:
            elements = extracted_context['strategic_elements']
            if not isinstance(elements, list) or len(elements) == 0:
                issues.append("strategic_elements should be a non-empty list")
                accuracy_score -= 0.2
                
        # Check extraction metadata
        if 'extraction_version' not in extracted_context:
            recommendations.append("Add extraction_version for tracking")
            
        # Determine overall validity
        is_valid = len(issues) == 0 and completeness_score >= 0.8 and accuracy_score >= 0.8
        
        return ValidationResult(
            is_valid=is_valid,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            issues=issues,
            recommendations=recommendations
        )

    def get_extraction_prompt(self) -> Tuple[str, str]:
        """
        Get optimized prompts for game context extraction.
        
        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        system_prompt = """You are an expert FRC (FIRST Robotics Competition) game analyst and strategist. Your task is to extract ONLY the essential information needed for alliance selection and team evaluation from the provided game manual.

CRITICAL FOCUS AREAS:
1. Scoring mechanisms and point values for all game phases
2. Game piece types, interactions, and strategic value
3. Autonomous period objectives and scoring opportunities
4. Teleop period strategies and optimization points
5. Endgame/climbing requirements and point values
6. Strategic robot capabilities that matter for alliance selection
7. Alliance cooperation elements and synergies

EXCLUDE (do not extract):
- Safety rules and regulations
- Field setup and maintenance procedures
- Competition scheduling and logistics
- Referee signals and administrative rules
- Detailed technical specifications not relevant to strategy
- Historical information or rule changes

OUTPUT FORMAT:
Return a structured JSON object with this exact schema:

{
  "game_year": <year as integer>,
  "game_name": "<official game name>",
  "extraction_version": "1.0",
  "extraction_date": "<current date>",
  "scoring_summary": {
    "autonomous": {
      "duration_seconds": <number>,
      "key_objectives": ["<objective 1>", "<objective 2>"],
      "point_values": {"<action>": <points>, ...},
      "strategic_notes": "<key strategic insights>"
    },
    "teleop": {
      "duration_seconds": <number>,
      "key_objectives": ["<objective 1>", "<objective 2>"],
      "point_values": {"<action>": <points>, ...},
      "strategic_notes": "<key strategic insights>"
    },
    "endgame": {
      "duration_seconds": <number>,
      "key_objectives": ["<objective 1>", "<objective 2>"],
      "point_values": {"<action>": <points>, ...},
      "strategic_notes": "<key strategic insights>"
    }
  },
  "strategic_elements": [
    {
      "name": "<element name>",
      "description": "<brief description>",
      "strategic_value": "<high|medium|low>",
      "alliance_impact": "<how this affects alliance selection>"
    }
  ],
  "alliance_considerations": [
    "<key consideration 1>",
    "<key consideration 2>"
  ],
  "key_metrics": [
    {
      "metric_name": "<metric name>",
      "description": "<what this measures>",
      "importance": "<high|medium|low>",
      "calculation_hint": "<how to evaluate this>"
    }
  ],
  "game_pieces": [
    {
      "name": "<piece name>",
      "scoring_locations": ["<location 1>", "<location 2>"],
      "point_values": {"<location>": <points>, ...},
      "strategic_notes": "<usage strategy>"
    }
  ]
}

Be concise but comprehensive. Focus on information that directly impacts team evaluation and alliance selection decisions."""

        user_prompt_template = """Extract the essential alliance selection information from this FRC game manual:

GAME MANUAL DATA:
{manual_content}

Please analyze this manual and extract only the information needed for effective alliance selection and team evaluation. Focus on scoring, strategy, and competitive advantages that would help in ranking teams for picklist generation.

Return the structured JSON as specified in the system prompt."""

        return system_prompt, user_prompt_template

    def _validate_manual_data(self, manual_data: Dict[str, Any]) -> None:
        """
        Validate that manual data has required structure.
        
        Args:
            manual_data: Manual data to validate
            
        Raises:
            ValueError: If manual data is invalid
        """
        if not isinstance(manual_data, dict):
            raise ValueError("manual_data must be a dictionary")
            
        if 'relevant_sections' not in manual_data:
            raise ValueError("manual_data must contain 'relevant_sections' field")
            
        if not manual_data['relevant_sections']:
            raise ValueError("manual_data 'relevant_sections' cannot be empty")
            
        if 'game_name' not in manual_data:
            raise ValueError("manual_data must contain 'game_name' field")

    def _generate_cache_key(self, manual_data: Dict[str, Any]) -> str:
        """
        Generate a cache key based on manual content.
        
        Args:
            manual_data: Manual data to generate key for
            
        Returns:
            SHA-256 hash of manual content and extraction version
        """
        content = f"{manual_data.get('relevant_sections', '')}{self.extraction_version}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _load_cached_extraction(self, cache_key: str) -> Optional[ExtractionResult]:
        """
        Load cached extraction result if available.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            ExtractionResult if cached, None otherwise
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validate cache format
                if 'extracted_context' in data and 'timestamp' in data:
                    return ExtractionResult(
                        success=True,
                        extracted_context=data['extracted_context'],
                        processing_time=data.get('processing_time', 0.0),
                        token_usage=data.get('token_usage', {}),
                        validation_score=data.get('validation_score', 0.0)
                    )
        except Exception as e:
            logger.warning(f"Failed to load cached extraction: {str(e)}")
            
        return None

    def _cache_extraction(self, cache_key: str, result: ExtractionResult) -> None:
        """
        Cache extraction result for future use.
        
        Args:
            cache_key: Cache key for storage
            result: ExtractionResult to cache
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            cache_data = {
                'extracted_context': result.extracted_context,
                'processing_time': result.processing_time,
                'token_usage': result.token_usage,
                'validation_score': result.validation_score,
                'timestamp': result.timestamp,
                'extraction_version': self.extraction_version
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cached extraction result: {cache_key[:16]}...")
            
        except Exception as e:
            logger.error(f"Failed to cache extraction: {str(e)}")

    async def _perform_extraction(self, manual_data: Dict[str, Any]) -> ExtractionResult:
        """
        Perform the actual GPT-powered extraction.
        
        Args:
            manual_data: Manual data to extract from
            
        Returns:
            ExtractionResult with extraction outcome
        """
        try:
            system_prompt, user_prompt_template = self.get_extraction_prompt()
            user_prompt = user_prompt_template.format(
                manual_content=json.dumps(manual_data, ensure_ascii=False)
            )
            
            # Check token count
            total_tokens = (
                len(self.token_encoder.encode(system_prompt)) +
                len(self.token_encoder.encode(user_prompt))
            )
            
            logger.info(f"Extraction prompt token count: {total_tokens}")
            
            # Perform extraction
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "length":
                return ExtractionResult(
                    success=False,
                    error="Extraction response was truncated due to length limit"
                )
                
            # Parse JSON response
            try:
                extracted_context = json.loads(content)
            except json.JSONDecodeError as e:
                return ExtractionResult(
                    success=False,
                    error=f"Failed to parse extraction JSON: {str(e)}"
                )
                
            # Add metadata
            extracted_context['extraction_version'] = self.extraction_version
            extracted_context['extraction_date'] = datetime.now().isoformat()
            extracted_context['original_manual_hash'] = self._generate_cache_key(manual_data)
            
            return ExtractionResult(
                success=True,
                extracted_context=extracted_context,
                token_usage={
                    'prompt_tokens': total_tokens,
                    'completion_tokens': len(self.token_encoder.encode(content)),
                    'total_tokens': total_tokens + len(self.token_encoder.encode(content))
                }
            )
            
        except Exception as e:
            logger.error(f"Extraction API call failed: {str(e)}")
            return ExtractionResult(
                success=False,
                error=f"Extraction API call failed: {str(e)}"
            )

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached extractions.
        
        Returns:
            Dictionary with cache statistics and file information
        """
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            
            cache_info = {
                'cache_directory': self.cache_dir,
                'cached_extractions': len(cache_files),
                'extraction_version': self.extraction_version,
                'files': []
            }
            
            for cache_file in cache_files[:10]:  # Limit to first 10 for readability
                file_path = os.path.join(self.cache_dir, cache_file)
                stat = os.stat(file_path)
                
                cache_info['files'].append({
                    'filename': cache_file,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                
            return cache_info
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return {'error': str(e)}

    def clear_cache(self, extraction_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cached extractions, optionally filtered by version.
        
        Args:
            extraction_version: If provided, only clear this version
            
        Returns:
            Dictionary with clearing results
        """
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            cleared_count = 0
            
            for cache_file in cache_files:
                file_path = os.path.join(self.cache_dir, cache_file)
                
                # If version filter specified, check file content
                if extraction_version:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('extraction_version') != extraction_version:
                                continue
                    except:
                        continue
                
                os.remove(file_path)
                cleared_count += 1
                
            logger.info(f"Cleared {cleared_count} cached extractions")
            return {
                'cleared_files': cleared_count,
                'version_filter': extraction_version
            }
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return {'error': str(e)}