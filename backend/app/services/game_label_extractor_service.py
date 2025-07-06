# backend/app/services/game_label_extractor_service.py

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
import tiktoken

from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger("game_label_extractor")

GPT_MODEL = OPENAI_MODEL


class LabelExtractionResult:
    """Data class for label extraction results with validation."""
    
    def __init__(
        self,
        success: bool,
        extracted_labels: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
        processing_time: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        labels_count: int = 0
    ):
        self.success = success
        self.extracted_labels = extracted_labels or []
        self.error = error
        self.processing_time = processing_time
        self.token_usage = token_usage or {}
        self.labels_count = labels_count
        self.timestamp = datetime.now().isoformat()


class GameLabelExtractorService:
    """
    Service for extracting game-specific labels from FRC game manuals.
    
    This service identifies specific game elements with short labels (like L4, L3, L2, L1)
    that correspond to scoring locations, game pieces, or strategic elements.
    
    Thread Safety: Thread-safe for read operations
    Dependencies: OpenAI API, file system access for storage
    """
    
    def __init__(self, data_dir: str = "backend/app/data"):
        """
        Initialize the game label extractor service.
        
        Args:
            data_dir: Directory to store extracted labels
            
        Raises:
            ValueError: If OpenAI API key is not configured
            OSError: If data directory cannot be created
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
        
        self.data_dir = data_dir
        self.max_tokens = 4000
        self.extraction_version = "1.0"
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Initialized GameLabelExtractorService with data dir: {data_dir}")

    async def extract_game_labels(
        self,
        manual_data: Dict[str, Any],
        year: int,
        force_refresh: bool = False
    ) -> LabelExtractionResult:
        """
        Extract game labels from manual data.
        
        Args:
            manual_data: Dictionary containing game manual information
            year: Game year for file naming
            force_refresh: If True, bypass cache and re-extract
            
        Returns:
            LabelExtractionResult containing extracted labels or error information
        """
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_manual_data(manual_data)
            
            # Check for existing labels unless force refresh
            if not force_refresh:
                existing_labels = self._load_existing_labels(year)
                if existing_labels:
                    logger.info(f"Using existing labels for year {year}")
                    return LabelExtractionResult(
                        success=True,
                        extracted_labels=existing_labels,
                        processing_time=time.time() - start_time,
                        labels_count=len(existing_labels)
                    )
            
            # Perform extraction
            logger.info(f"Starting game label extraction for year {year}")
            extraction_result = await self._perform_extraction(manual_data, year)
            
            if extraction_result.success:
                # Save labels to file
                self._save_labels(year, extraction_result.extracted_labels)
                logger.info(f"Successfully extracted {extraction_result.labels_count} labels for year {year}")
            
            extraction_result.processing_time = time.time() - start_time
            return extraction_result
            
        except Exception as e:
            logger.error(f"Critical error in extract_game_labels: {str(e)}")
            return LabelExtractionResult(
                success=False,
                error=f"Label extraction failed: {str(e)}",
                processing_time=time.time() - start_time
            )

    def get_extraction_prompt(self) -> tuple[str, str]:
        """
        Get optimized prompts for game label extraction.
        
        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        system_prompt = """You are an expert FRC (FIRST Robotics Competition) scouting data analyst specializing in identifying trackable robot performance metrics.

Your task is to extract SCOUTING DATA FIELD LABELS from the provided manual - these are specific metrics that teams would track about robot performance during matches.

Focus on extracting potential scouting data fields in these categories:

1. **Autonomous Metrics**: Specific scoring actions during autonomous period
   - Example: "auto_coral_L1_scored", "auto_mobility_successful", "auto_starting_position"

2. **Teleop Scoring Metrics**: Scoring actions during teleoperated period
   - Example: "teleop_coral_L4_count", "teleop_algae_processor_scored", "teleop_cycles_completed"

3. **Endgame Metrics**: End-of-match activities and achievements
   - Example: "endgame_climb_attempted", "endgame_climb_successful", "endgame_park_achieved"

4. **Defensive Metrics**: Defensive and counter-defensive actions
   - Example: "defense_time_spent", "defense_effectiveness_rating", "was_defended_against"

5. **Reliability Metrics**: Robot performance and consistency measures
   - Example: "mechanical_failures", "brownouts_occurred", "overall_reliability_rating"

6. **Strategic Metrics**: Game-specific strategic elements and text observations
   - Example: "cooperation_with_alliance", "field_positioning_effectiveness", "strategy_notes", "performance_comments"

CRITICAL REQUIREMENTS:
- Extract SCOUTING METRICS that teams would actually track, not just game elements
- Use descriptive field names that indicate what is being measured
- Include metrics for autonomous, teleop, endgame, defense, and reliability
- Focus on quantifiable or rateable performance indicators
- Consider counting metrics (how many X), rating metrics (effectiveness 1-5), and text observations (strategy notes, comments)

OUTPUT FORMAT:
Return a structured JSON object with this exact schema:

{
  "extraction_version": "1.0",
  "extraction_date": "<current date>",
  "game_year": <year as integer>,
  "game_name": "<official game name>",
  "labels": [
    {
      "label": "<scouting field name like auto_coral_L1_scored>",
      "category": "<autonomous|teleop|endgame|defense|reliability|strategic>",
      "description": "<what this metric measures about robot performance>",
      "data_type": "<count|rating|boolean|time|text>",
      "typical_range": "<expected range like 0-10, 1-5, true/false, or 'text' for text fields>",
      "usage_context": "<when this would be tracked during a match>"
    }
  ]
}

Think like a scouting team: what specific robot performance metrics would you want to track to evaluate teams for alliance selection?"""

        user_prompt_template = """Extract scouting data field labels from this FRC game manual:

GAME MANUAL DATA:
{manual_content}

Please analyze this manual and extract specific SCOUTING METRICS that teams would track about robot performance during matches. Focus on:

1. **Quantifiable actions**: How many times robots score in different locations, pick up game pieces, etc.
2. **Performance ratings**: Effectiveness measures for defense, reliability, cooperation, etc.
3. **Success/failure tracking**: Whether specific actions were attempted and completed
4. **Time-based metrics**: How long robots spend on certain activities
5. **Text observations**: Strategic notes, comments, or descriptive observations about robot performance

Think from a scouting perspective: if you were watching a robot during a match, what specific performance metrics would you want to record to help with alliance selection?

Return the structured JSON as specified in the system prompt."""

        return system_prompt, user_prompt_template

    def get_labels_by_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Get stored labels for a specific year.
        
        Args:
            year: Game year
            
        Returns:
            List of label dictionaries, empty if not found
        """
        return self._load_existing_labels(year) or []

    def save_labels(self, year: int, labels: List[Dict[str, Any]]) -> bool:
        """
        Save labels for a specific year.
        
        Args:
            year: Game year
            labels: List of label dictionaries
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._save_labels(year, labels)
            return True
        except Exception as e:
            logger.error(f"Failed to save labels for year {year}: {str(e)}")
            return False

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

    def _load_existing_labels(self, year: int) -> Optional[List[Dict[str, Any]]]:
        """
        Load existing labels from file if available.
        
        Args:
            year: Game year
            
        Returns:
            List of labels if found, None otherwise
        """
        try:
            labels_file = os.path.join(self.data_dir, f"game_labels_{year}.json")
            if os.path.exists(labels_file):
                with open(labels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('labels', [])
        except Exception as e:
            logger.warning(f"Failed to load existing labels for year {year}: {str(e)}")
        return None

    def _save_labels(self, year: int, labels: List[Dict[str, Any]]) -> None:
        """
        Save labels to file.
        
        Args:
            year: Game year
            labels: List of label dictionaries
        """
        try:
            labels_file = os.path.join(self.data_dir, f"game_labels_{year}.json")
            labels_data = {
                'extraction_version': self.extraction_version,
                'extraction_date': datetime.now().isoformat(),
                'game_year': year,
                'labels_count': len(labels),
                'labels': labels
            }
            
            with open(labels_file, 'w', encoding='utf-8') as f:
                json.dump(labels_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(labels)} labels to {labels_file}")
            
        except Exception as e:
            logger.error(f"Failed to save labels for year {year}: {str(e)}")
            raise

    async def _perform_extraction(self, manual_data: Dict[str, Any], year: int) -> LabelExtractionResult:
        """
        Perform the actual GPT-powered label extraction.
        
        Args:
            manual_data: Manual data to extract from
            year: Game year
            
        Returns:
            LabelExtractionResult with extraction outcome
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
            
            logger.info(f"Label extraction prompt token count: {total_tokens}")
            
            # Perform extraction
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "length":
                return LabelExtractionResult(
                    success=False,
                    error="Label extraction response was truncated due to length limit"
                )
            
            # Parse JSON response
            try:
                extraction_data = json.loads(content)
            except json.JSONDecodeError as e:
                return LabelExtractionResult(
                    success=False,
                    error=f"Failed to parse extraction JSON: {str(e)}"
                )
            
            # Extract labels from response
            labels = extraction_data.get('labels', [])
            
            # Add metadata to each label
            for label in labels:
                label['extraction_version'] = self.extraction_version
                label['extraction_date'] = datetime.now().isoformat()
                label['game_year'] = year
            
            return LabelExtractionResult(
                success=True,
                extracted_labels=labels,
                labels_count=len(labels),
                token_usage={
                    'prompt_tokens': total_tokens,
                    'completion_tokens': len(self.token_encoder.encode(content)),
                    'total_tokens': total_tokens + len(self.token_encoder.encode(content))
                }
            )
            
        except Exception as e:
            logger.error(f"Label extraction API call failed: {str(e)}")
            return LabelExtractionResult(
                success=False,
                error=f"Label extraction API call failed: {str(e)}"
            )

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the label extraction service.
        
        Returns:
            Dictionary with service statistics and configuration
        """
        try:
            # Count existing label files
            label_files = [f for f in os.listdir(self.data_dir) if f.startswith('game_labels_') and f.endswith('.json')]
            
            service_info = {
                'data_directory': self.data_dir,
                'extraction_version': self.extraction_version,
                'available_years': [],
                'total_label_files': len(label_files),
                'model_used': GPT_MODEL
            }
            
            # Extract years from filenames
            for filename in label_files:
                try:
                    year = int(filename.replace('game_labels_', '').replace('.json', ''))
                    service_info['available_years'].append(year)
                except ValueError:
                    continue
            
            service_info['available_years'].sort(reverse=True)
            
            return service_info
            
        except Exception as e:
            logger.error(f"Failed to get service info: {str(e)}")
            return {'error': str(e)}

    async def call_gpt_for_description(self, prompt: str) -> Dict[str, Any]:
        """
        Call GPT to generate description for a custom label.
        
        Args:
            prompt: The prompt to send to GPT
            
        Returns:
            Dictionary with generation results
        """
        try:
            if not self.client:
                return {'success': False, 'error': 'OpenAI client not initialized'}
            
            logger.info("Calling GPT for label description generation")
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"GPT response received: {len(content)} characters")
            
            # Try to parse as JSON (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                json_content = content
                if content.strip().startswith('```json'):
                    json_content = content.split('```json')[1].split('```')[0].strip()
                elif content.strip().startswith('```'):
                    json_content = content.split('```')[1].split('```')[0].strip()
                
                result = json.loads(json_content)
                result['success'] = True
                return result
            except (json.JSONDecodeError, IndexError) as e:
                # If not JSON, try to extract key information
                logger.warning(f"GPT response was not valid JSON, attempting to parse: {e}")
                return {
                    'success': True,
                    'description': content,
                    'typical_range': 'varies',
                    'usage_context': 'custom tracking',
                    'suggested_label': None
                }
                
        except Exception as e:
            logger.error(f"GPT description generation failed: {str(e)}")
            return {
                'success': False,
                'error': f"GPT description generation failed: {str(e)}"
            }