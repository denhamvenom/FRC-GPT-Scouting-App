# backend/app/services/data_aggregation_service.py

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from app.services.game_context_extractor_service import GameContextExtractorService
    EXTRACTION_AVAILABLE = True
except ImportError:
    EXTRACTION_AVAILABLE = False
    GameContextExtractorService = None

try:
    from app.services.game_context_synthesis_service import GameContextSynthesisService
    SYNTHESIS_AVAILABLE = True
except ImportError:
    SYNTHESIS_AVAILABLE = False
    GameContextSynthesisService = None

try:
    from app.config.extraction_config import get_extraction_config
except ImportError:
    def get_extraction_config():
        return {}

logger = logging.getLogger("data_aggregation_service")


class DataAggregationService:
    """
    Service for collecting, transforming, and validating data from multiple sources.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    
    Enhanced with GameContextSynthesisService for strategic manual compression.
    """

    def __init__(self, unified_dataset_path: str, use_extracted_context: bool = True, use_synthesis: bool = True):
        """
        Initialize the data aggregation service.
        
        Args:
            unified_dataset_path: Path to the unified dataset JSON file
            use_extracted_context: Whether to use extracted context (True) or full manual (False)
            use_synthesis: Whether to use context synthesis (True) for strategic compression
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self._determine_year()
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")
        self.use_extracted_context = use_extracted_context
        self.use_synthesis = use_synthesis
        self.label_mappings = self._load_label_mappings()  # Load field-to-label mappings
        
        # Initialize extraction service if using extracted context
        if self.use_extracted_context and EXTRACTION_AVAILABLE:
            try:
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "cache", "game_context"
                )
                self.extractor_service = GameContextExtractorService(cache_dir=cache_dir)
                logger.info("Initialized game context extractor service")
            except Exception as e:
                logger.warning(f"Failed to initialize extractor service: {e}")
                logger.warning("Falling back to full manual context")
                self.use_extracted_context = False
                self.extractor_service = None
        else:
            if self.use_extracted_context and not EXTRACTION_AVAILABLE:
                logger.warning("Extraction service not available, falling back to full manual context")
                self.use_extracted_context = False
            self.extractor_service = None
        
        # Initialize synthesis service if using synthesis
        if self.use_synthesis and SYNTHESIS_AVAILABLE:
            try:
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "cache"
                )
                self.synthesis_service = GameContextSynthesisService(cache_dir=cache_dir)
                logger.info("Initialized game context synthesis service")
            except Exception as e:
                logger.warning(f"Failed to initialize synthesis service: {e}")
                logger.warning("Falling back to full manual context")
                self.use_synthesis = False
                self.synthesis_service = None
        else:
            if self.use_synthesis and not SYNTHESIS_AVAILABLE:
                logger.warning("Synthesis service not available, falling back to full manual context")
                self.use_synthesis = False
            self.synthesis_service = None

    def _get_current_year(self) -> int:
        """
        Get current FRC season year as fallback when no year is specified.
        
        This should only be used as a last resort fallback when:
        - No year is provided in the dataset
        - No year is provided by user input
        - No year can be determined from other sources
        
        FRC seasons run from roughly September to April, so:
        - September-December: Use current calendar year + 1
        - January-August: Use current calendar year
        
        Returns:
            Current FRC season year (fallback only)
        """
        now = datetime.now()
        if now.month >= 9:  # September or later
            return now.year + 1
        else:  # January through August
            return now.year

    def _determine_year(self) -> int:
        """
        Determine the FRC season year using proper priority order.
        
        Priority order:
        1. Year from dataset (user input via setup process)
        2. Year from global cache (active user session)
        3. Dynamic calculation as last resort fallback
        
        Returns:
            FRC season year from the most authoritative source available
        """
        # PRIORITY 1: Use year from dataset (comes from user input in setup)
        if "year" in self.dataset and isinstance(self.dataset["year"], int):
            return self.dataset["year"]
        
        # PRIORITY 2: Try to get year from global cache (active user session)
        try:
            from app.services.global_cache import cache
            if "active_event_year" in cache and isinstance(cache["active_event_year"], int):
                return cache["active_event_year"]
        except Exception:
            # Global cache may not be available in all contexts
            pass
        
        # PRIORITY 3: Fall back to dynamic calculation (last resort)
        return self._get_current_year()

    def _load_label_mappings(self) -> Dict[str, Any]:
        """
        Load field-to-label mappings using unified field selection structure.
        Priority: field_selections.label_mapping → game_labels → fallback
        
        Returns:
            Dictionary mapping original field names to enhanced label data and metadata
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            
            label_mappings = {}
            
            # PRIORITY 1: Load from field_selections with enhanced label_mapping
            field_selections_path = os.path.join(data_dir, f"field_selections_{self.year}{self.event_key.replace(str(self.year), '')}.json")
            if os.path.exists(field_selections_path):
                with open(field_selections_path, "r", encoding="utf-8") as f:
                    field_selections_data = json.load(f)
                
                # Extract enhanced label mappings from field_selections
                field_selections = field_selections_data.get("field_selections", {})
                for field_name, field_info in field_selections.items():
                    if isinstance(field_info, dict) and "label_mapping" in field_info:
                        label_mapping = field_info["label_mapping"]
                        if "label" in label_mapping:
                            # Store full label mapping with metadata
                            label_mappings[field_name] = {
                                "label": label_mapping["label"],
                                "category": label_mapping.get("category", "unknown"),
                                "description": label_mapping.get("description", ""),
                                "data_type": label_mapping.get("data_type", "count"),
                                "typical_range": label_mapping.get("typical_range", ""),
                                "usage_context": label_mapping.get("usage_context", ""),
                                "source": "field_selections"
                            }
                
                logger.info(f"Loaded {len(label_mappings)} enhanced field-to-label mappings from field_selections")
            
            # PRIORITY 2: Load from game_labels as fallback for unmapped fields
            game_labels_path = os.path.join(data_dir, f"game_labels_{self.year}.json")
            if os.path.exists(game_labels_path):
                with open(game_labels_path, "r", encoding="utf-8") as f:
                    game_labels_data = json.load(f)
                
                # Create a lookup for game labels
                game_labels_lookup = {}
                for label_info in game_labels_data.get("labels", []):
                    label_name = label_info.get("label", "")
                    if label_name:
                        game_labels_lookup[label_name] = label_info
                
                # Fill in missing mappings from game_labels
                game_labels_added = 0
                for label_name, label_info in game_labels_lookup.items():
                    # Check if this label isn't already mapped from field_selections
                    found_in_field_selections = any(
                        mapping.get("label") == label_name 
                        for mapping in label_mappings.values()
                    )
                    
                    if not found_in_field_selections:
                        # Add as direct mapping (label name = field name)
                        label_mappings[label_name] = {
                            "label": label_name,
                            "category": label_info.get("category", "unknown"),
                            "description": label_info.get("description", ""),
                            "data_type": label_info.get("data_type", "count"),
                            "typical_range": label_info.get("typical_range", ""),
                            "usage_context": label_info.get("usage_context", ""),
                            "source": "game_labels"
                        }
                        game_labels_added += 1
                
                logger.info(f"Added {game_labels_added} fallback mappings from game_labels")
            
            # PRIORITY 3: Legacy support for field_metadata files (Sprint 3 compatibility)
            metadata_path = os.path.join(data_dir, f"field_metadata_{self.year}.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    field_metadata = json.load(f)
                
                # Add any mappings not already present
                legacy_added = 0
                for field_name, field_info in field_metadata.items():
                    if field_name not in label_mappings and isinstance(field_info, dict) and "label_mapping" in field_info:
                        label_mapping = field_info["label_mapping"]
                        if "label" in label_mapping:
                            label_mappings[field_name] = {
                                "label": label_mapping["label"],
                                "category": label_mapping.get("category", "unknown"),
                                "description": label_mapping.get("description", ""),
                                "data_type": label_mapping.get("data_type", "count"),
                                "typical_range": label_mapping.get("typical_range", ""),
                                "usage_context": label_mapping.get("usage_context", ""),
                                "source": "field_metadata"
                            }
                            legacy_added += 1
                
                if legacy_added > 0:
                    logger.info(f"Added {legacy_added} legacy mappings from field_metadata")
            
            logger.info(f"Total enhanced label mappings loaded: {len(label_mappings)}")
            return label_mappings
            
        except Exception as e:
            logger.error(f"Error loading enhanced label mappings: {e}")
            return {}

    def _load_dataset(self) -> Dict[str, Any]:
        """
        Load the unified dataset from the JSON file.
        
        Returns:
            Loaded dataset dictionary
        """
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                logger.info(f"Loaded dataset from {self.dataset_path}")
                return dataset
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {self.dataset_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in dataset file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading unified dataset: {e}")
            return {}

    def load_game_context(self) -> Optional[str]:
        """
        Load the game context for picklist generation.
        
        Priority order:
        1. Synthesis (compressed strategic context) if enabled
        2. Extraction (optimized context) if enabled 
        3. Full manual text (fallback)
        
        Returns:
            Game context text or None if not available
        """
        try:
            manual_data = self._load_manual_data()
            if not manual_data:
                return None
            
            # PRIORITY 1: Use synthesis if available and enabled
            if self.use_synthesis and self.synthesis_service:
                synthesized_context = self._get_synthesized_context(manual_data)
                if synthesized_context:
                    return synthesized_context
                else:
                    logger.warning("Synthesis failed, falling back to extraction/full context")
            
            # PRIORITY 2: Use extracted context if available and enabled
            if self.use_extracted_context and self.extractor_service:
                return self._get_extracted_context(manual_data)
            
            # PRIORITY 3: Fall back to full manual context
            return self._get_full_manual_context(manual_data)
                
        except Exception as e:
            logger.error(f"Error loading game context: {e}")
            return None

    def _load_manual_data(self) -> Optional[Dict[str, Any]]:
        """
        Load the raw manual data from JSON file.
        
        Returns:
            Manual data dictionary or None if not available
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            manual_text_path = os.path.join(data_dir, f"manual_text_{self.year}.json")

            if os.path.exists(manual_text_path):
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)
                    logger.debug(f"Loaded manual data for {self.year}")
                    return manual_data
            else:
                logger.warning(f"Game manual not found: {manual_text_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading manual data: {e}")
            return None

    def _load_field_selections(self) -> Optional[Dict[str, Any]]:
        """
        Load field selections metadata for the current year/event.
        
        Returns:
            Field selections dictionary or None if not available
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            field_selections_path = os.path.join(data_dir, f"field_selections_{self.year}{self.event_key.replace(str(self.year), '')}.json")

            if os.path.exists(field_selections_path):
                with open(field_selections_path, "r", encoding="utf-8") as f:
                    field_selections_data = json.load(f)
                    logger.debug(f"Loaded field selections for {self.year}{self.event_key.replace(str(self.year), '')}")
                    return field_selections_data.get("field_selections", {})
            else:
                logger.warning(f"Field selections not found: {field_selections_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading field selections: {e}")
            return None

    def _get_synthesized_context(self, manual_data: Dict[str, Any]) -> Optional[str]:
        """
        Get synthesized game context using the synthesis service.
        
        Args:
            manual_data: Raw manual data dictionary
            
        Returns:
            Synthesized context string or None if synthesis fails
        """
        try:
            # Load field selections for synthesis
            field_selections = self._load_field_selections()
            if not field_selections:
                logger.warning("No field selections available for synthesis")
                return None
            
            import asyncio
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_synthesis_sync, manual_data, field_selections)
                        synthesis_result = future.result()
                else:
                    # Safe to run directly
                    synthesis_result = loop.run_until_complete(
                        self.synthesis_service.synthesize_game_context(manual_data, field_selections)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    synthesis_result = loop.run_until_complete(
                        self.synthesis_service.synthesize_game_context(manual_data, field_selections)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if synthesis_result.success and synthesis_result.synthesized_context:
                synthesized_context = synthesis_result.synthesized_context
                
                # Log token savings
                original_size = len(manual_data.get('relevant_sections', ''))
                synthesized_size = len(synthesized_context)
                savings = 100 * (1 - synthesized_size / original_size) if original_size > 0 else 0
                
                logger.info(f"Using synthesized context for {self.year} (Size reduction: {savings:.1f}%)")
                logger.info(f"Context size: {original_size} -> {synthesized_size} characters")
                logger.info(f"Processing time: {synthesis_result.processing_time:.2f}s")
                
                return synthesized_context
            else:
                logger.warning(f"Synthesis failed: {synthesis_result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error in synthesized context: {e}")
            return None

    def _run_synthesis_sync(self, manual_data: Dict[str, Any], field_selections: Dict[str, Any]) -> Any:
        """
        Helper method to run synthesis in a new event loop.
        
        Args:
            manual_data: Manual data to synthesize from
            field_selections: Field selections metadata
            
        Returns:
            SynthesisResult from the synthesis process
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.synthesis_service.synthesize_game_context(manual_data, field_selections)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def _get_extracted_context(self, manual_data: Dict[str, Any]) -> Optional[str]:
        """
        Get extracted game context using the extraction service.
        
        Args:
            manual_data: Raw manual data dictionary
            
        Returns:
            Extracted context string or None if extraction fails
        """
        try:
            import asyncio
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_extraction_sync, manual_data)
                        extraction_result = future.result()
                else:
                    # Safe to run directly
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if extraction_result.success and extraction_result.extracted_context:
                # Convert extracted context to string format for compatibility
                extracted_data = extraction_result.extracted_context
                
                # Format extracted context for GPT consumption
                context_parts = []
                
                # Game information
                context_parts.append(f"Game: {extracted_data.get('game_name', '')} ({extracted_data.get('game_year', self.year)})")
                
                # Scoring summary
                if 'scoring_summary' in extracted_data:
                    context_parts.append("\nSCORING SUMMARY:")
                    scoring = extracted_data['scoring_summary']
                    
                    for phase in ['autonomous', 'teleop', 'endgame']:
                        if phase in scoring:
                            phase_data = scoring[phase]
                            context_parts.append(f"\n{phase.upper()} ({phase_data.get('duration_seconds', 0)}s):")
                            context_parts.append(f"  Objectives: {', '.join(phase_data.get('key_objectives', []))}")
                            context_parts.append(f"  Point Values: {phase_data.get('point_values', {})}")
                            if phase_data.get('strategic_notes'):
                                context_parts.append(f"  Strategy: {phase_data['strategic_notes']}")
                
                # Strategic elements
                if 'strategic_elements' in extracted_data and extracted_data['strategic_elements']:
                    context_parts.append("\nSTRATEGIC ELEMENTS:")
                    for element in extracted_data['strategic_elements']:
                        context_parts.append(f"- {element.get('name', '')}: {element.get('description', '')} (Impact: {element.get('alliance_impact', '')})")
                
                # Alliance considerations
                if 'alliance_considerations' in extracted_data and extracted_data['alliance_considerations']:
                    context_parts.append("\nALLIANCE CONSIDERATIONS:")
                    for consideration in extracted_data['alliance_considerations']:
                        context_parts.append(f"- {consideration}")
                
                # Key metrics
                if 'key_metrics' in extracted_data and extracted_data['key_metrics']:
                    context_parts.append("\nKEY METRICS:")
                    for metric in extracted_data['key_metrics']:
                        context_parts.append(f"- {metric.get('metric_name', '')}: {metric.get('description', '')} (Importance: {metric.get('importance', '')})")
                
                formatted_context = '\n'.join(context_parts)
                
                # Log token savings
                original_size = len(manual_data.get('relevant_sections', ''))
                extracted_size = len(formatted_context)
                savings = 100 * (1 - extracted_size / original_size) if original_size > 0 else 0
                
                logger.info(f"Using extracted context for {self.year} (Size reduction: {savings:.1f}%)")
                logger.info(f"Context size: {original_size} -> {extracted_size} characters")
                
                return formatted_context
            else:
                logger.warning(f"Extraction failed: {extraction_result.error}")
                logger.warning("Falling back to full manual context")
                return self._get_full_manual_context(manual_data)
                
        except Exception as e:
            logger.error(f"Error in extracted context: {e}")
            logger.warning("Falling back to full manual context")
            return self._get_full_manual_context(manual_data)

    def _get_full_manual_context(self, manual_data: Dict[str, Any]) -> str:
        """
        Get full manual context (original behavior).
        
        Args:
            manual_data: Raw manual data dictionary
            
        Returns:
            Full manual context string
        """
        game_context = f"Game: {manual_data.get('game_name', '')}\n\n{manual_data.get('relevant_sections', '')}"
        logger.info(f"Using full manual context for {self.year}")
        return game_context

    def _run_extraction_sync(self, manual_data: Dict[str, Any]) -> Any:
        """
        Helper method to run extraction in a new event loop.
        
        Args:
            manual_data: Manual data to extract from
            
        Returns:
            ExtractionResult from the extraction process
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.extractor_service.extract_game_context(manual_data)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def _run_force_extraction_sync(self, manual_data: Dict[str, Any]) -> Any:
        """
        Helper method to run force extraction in a new event loop.
        
        Args:
            manual_data: Manual data to extract from
            
        Returns:
            ExtractionResult from the force extraction process
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.extractor_service.extract_game_context(manual_data, force_refresh=True)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def force_extract_game_context(self) -> Dict[str, Any]:
        """
        Force extraction of game context, bypassing cache.
        
        Returns:
            Dictionary with extraction results and status
        """
        if not self.extractor_service:
            return {
                "success": False,
                "error": "Extraction service not available",
                "message": "Enable extracted context mode to use this feature"
            }
        
        try:
            manual_data = self._load_manual_data()
            if not manual_data:
                return {
                    "success": False,
                    "error": "Manual data not available",
                    "message": f"Could not load manual data for year {self.year}"
                }
            
            import asyncio
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_force_extraction_sync, manual_data)
                        extraction_result = future.result()
                else:
                    # Safe to run directly
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data, force_refresh=True)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data, force_refresh=True)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if extraction_result.success:
                return {
                    "success": True,
                    "extraction_result": extraction_result.extracted_context,
                    "processing_time": extraction_result.processing_time,
                    "validation_score": extraction_result.validation_score,
                    "token_usage": extraction_result.token_usage,
                    "message": f"Successfully extracted context for {self.year}"
                }
            else:
                return {
                    "success": False,
                    "error": extraction_result.error,
                    "processing_time": extraction_result.processing_time,
                    "message": "Extraction failed"
                }
                
        except Exception as e:
            logger.error(f"Error in force extraction: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during extraction"
            }

    def get_extraction_status(self) -> Dict[str, Any]:
        """
        Get status of game context extraction for current year.
        
        Returns:
            Dictionary with extraction status information
        """
        status = {
            "year": self.year,
            "extraction_enabled": self.use_extracted_context,
            "extractor_available": self.extractor_service is not None,
            "manual_available": False,
            "cached_extraction": False,
            "cache_info": {}
        }
        
        # Check manual availability
        manual_data = self._load_manual_data()
        status["manual_available"] = manual_data is not None
        
        if manual_data:
            status["manual_size"] = len(manual_data.get('relevant_sections', ''))
            status["game_name"] = manual_data.get('game_name', 'Unknown')
        
        # Check cache status if extractor available
        if self.extractor_service:
            try:
                status["cache_info"] = self.extractor_service.get_cache_info()
                
                # Check if we have a cached extraction for current manual
                if manual_data:
                    cache_key = self.extractor_service._generate_cache_key(manual_data)
                    cached_result = self.extractor_service._load_cached_extraction(cache_key)
                    status["cached_extraction"] = cached_result is not None
                    if cached_result:
                        status["cache_validation_score"] = cached_result.validation_score
                        
            except Exception as e:
                logger.warning(f"Error getting cache status: {e}")
                status["cache_error"] = str(e)
        
        return status

    def set_extraction_mode(self, use_extracted_context: bool) -> Dict[str, Any]:
        """
        Enable or disable extracted context mode.
        
        Args:
            use_extracted_context: Whether to use extracted context
            
        Returns:
            Dictionary with operation results
        """
        previous_mode = self.use_extracted_context
        
        try:
            if use_extracted_context and not self.extractor_service:
                # Initialize extraction service
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "cache", "game_context"
                )
                self.extractor_service = GameContextExtractorService(cache_dir=cache_dir)
                logger.info("Initialized game context extractor service")
            
            self.use_extracted_context = use_extracted_context
            
            return {
                "success": True,
                "previous_mode": "extracted" if previous_mode else "full",
                "current_mode": "extracted" if use_extracted_context else "full",
                "message": f"Switched to {'extracted' if use_extracted_context else 'full'} context mode"
            }
            
        except Exception as e:
            # Revert on error
            self.use_extracted_context = previous_mode
            logger.error(f"Error setting extraction mode: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "current_mode": "extracted" if previous_mode else "full",
                "message": "Failed to change extraction mode"
            }

    def get_teams_data(self) -> Dict[str, Any]:
        """
        Get the teams data from the dataset.
        
        Returns:
            Dictionary of team data
        """
        return self.teams_data

    def get_dataset_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the dataset.
        
        Returns:
            Dataset metadata
        """
        metadata = {
            "year": self.year,
            "event_key": self.event_key,
            "teams_count": len(self.teams_data),
            "dataset_path": self.dataset_path,
            "has_game_context": self.load_game_context() is not None,
            "extraction_mode": "extracted" if self.use_extracted_context else "full",
            "extraction_available": self.extractor_service is not None
        }

        # Analyze available data types
        data_types = {
            "scouting_data": 0,
            "statbotics": 0,
            "ranking": 0,
            "superscouting": 0
        }

        for team_data in self.teams_data.values():
            if isinstance(team_data, dict):
                for data_type in data_types:
                    if data_type in team_data:
                        data_types[data_type] += 1

        metadata["data_availability"] = data_types
        
        return metadata

    def validate_dataset(self) -> Dict[str, Any]:
        """
        Validate the dataset for completeness and consistency.
        
        Returns:
            Validation report
        """
        validation_report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "team_issues": {},
            "summary": {}
        }

        if not self.dataset:
            validation_report["valid"] = False
            validation_report["errors"].append("Dataset is empty or failed to load")
            return validation_report

        # Check required fields
        required_fields = ["teams", "year", "event_key"]
        for field in required_fields:
            if field not in self.dataset:
                validation_report["valid"] = False
                validation_report["errors"].append(f"Missing required field: {field}")

        # Validate teams data
        if "teams" not in self.dataset:
            validation_report["valid"] = False
            validation_report["errors"].append("No teams data found")
        else:
            teams_validation = self._validate_teams_data(self.teams_data)
            validation_report["team_issues"] = teams_validation["issues"]
            validation_report["warnings"].extend(teams_validation["warnings"])
            validation_report["summary"]["teams_with_issues"] = len(teams_validation["issues"])

        # Summary statistics
        validation_report["summary"].update({
            "total_teams": len(self.teams_data),
            "year": self.year,
            "event_key": self.event_key,
            "has_errors": len(validation_report["errors"]) > 0,
            "has_warnings": len(validation_report["warnings"]) > 0
        })

        return validation_report

    def _validate_teams_data(self, teams_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual teams data.
        
        Args:
            teams_data: Dictionary of team data
            
        Returns:
            Teams validation report
        """
        issues = {}
        warnings = []

        for team_key, team_data in teams_data.items():
            team_issues = []
            
            if not isinstance(team_data, dict):
                team_issues.append("Team data is not a dictionary")
                continue

            # Check required team fields
            if "team_number" not in team_data:
                team_issues.append("Missing team_number")
            elif not isinstance(team_data["team_number"], int):
                team_issues.append("team_number is not an integer")

            if "nickname" not in team_data:
                team_issues.append("Missing nickname")

            # Validate scouting data if present
            if "scouting_data" in team_data:
                if not isinstance(team_data["scouting_data"], list):
                    team_issues.append("scouting_data is not a list")
                elif len(team_data["scouting_data"]) == 0:
                    warnings.append(f"Team {team_data.get('team_number', team_key)} has no scouting data")

            # Validate statbotics data if present
            if "statbotics" in team_data:
                if not isinstance(team_data["statbotics"], dict):
                    team_issues.append("statbotics data is not a dictionary")

            if team_issues:
                issues[str(team_data.get("team_number", team_key))] = team_issues

        return {"issues": issues, "warnings": warnings}

    def filter_teams_by_criteria(
        self,
        exclude_teams: Optional[List[int]] = None,
        min_matches: int = 0,
        require_statbotics: bool = False,
        require_scouting_data: bool = False
    ) -> Dict[str, Any]:
        """
        Filter teams based on specified criteria.
        
        Args:
            exclude_teams: List of team numbers to exclude
            min_matches: Minimum number of matches required
            require_statbotics: Whether to require Statbotics data
            require_scouting_data: Whether to require scouting data
            
        Returns:
            Filtered teams data
        """
        filtered_teams = {}
        exclude_set = set(exclude_teams or [])

        for team_key, team_data in self.teams_data.items():
            if not isinstance(team_data, dict):
                continue

            team_number = team_data.get("team_number")
            if team_number in exclude_set:
                continue

            # Check scouting data requirements
            if require_scouting_data:
                scouting_data = team_data.get("scouting_data", [])
                if not isinstance(scouting_data, list) or len(scouting_data) == 0:
                    continue

                if len(scouting_data) < min_matches:
                    continue

            # Check Statbotics requirements
            if require_statbotics:
                if "statbotics" not in team_data or not isinstance(team_data["statbotics"], dict):
                    continue

            filtered_teams[team_key] = team_data

        logger.info(f"Filtered teams: {len(self.teams_data)} -> {len(filtered_teams)}")
        return filtered_teams

    def aggregate_team_metrics(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate metrics for a single team from all available data sources.
        
        Args:
            team_data: Individual team data
            
        Returns:
            Aggregated team metrics
        """
        aggregated = {
            "team_number": team_data.get("team_number"),
            "nickname": team_data.get("nickname", f"Team {team_data.get('team_number', 'Unknown')}"),
            "metrics": {},
            "data_sources": []
        }

        # Aggregate scouting data with label enhancement
        if "scouting_data" in team_data and isinstance(team_data["scouting_data"], list):
            scouting_metrics = self._aggregate_scouting_metrics(team_data["scouting_data"])
            
            # Apply label mappings to enhance field names
            enhanced_scouting_metrics = self._apply_label_mappings(scouting_metrics)
            aggregated["metrics"].update(enhanced_scouting_metrics)
            aggregated["data_sources"].append("scouting")
            aggregated["match_count"] = len(team_data["scouting_data"])

        # Add Statbotics data (check both 'statbotics' and 'statbotics_info' for compatibility)
        statbotics_data = team_data.get("statbotics") or team_data.get("statbotics_info", {})
        if statbotics_data and isinstance(statbotics_data, dict):
            for metric, value in statbotics_data.items():
                if isinstance(value, (int, float)):
                    aggregated["metrics"][f"statbotics_{metric}"] = value
            aggregated["data_sources"].append("statbotics")

        # Add ranking data (check both 'ranking' and 'ranking_info' for compatibility)
        ranking_data = team_data.get("ranking") or team_data.get("ranking_info", {})
        if ranking_data and isinstance(ranking_data, dict):
            aggregated["rank"] = ranking_data.get("rank")
            aggregated["record"] = {
                "wins": ranking_data.get("wins", 0),
                "losses": ranking_data.get("losses", 0),
                "ties": ranking_data.get("ties", 0)
            }
            
            # Calculate win percentage
            total_matches = aggregated["record"]["wins"] + aggregated["record"]["losses"] + aggregated["record"]["ties"]
            if total_matches > 0:
                aggregated["metrics"]["win_percentage"] = aggregated["record"]["wins"] / total_matches
            
            aggregated["data_sources"].append("ranking")

        # Add superscouting notes (limited for token efficiency)
        if "superscouting" in team_data and isinstance(team_data["superscouting"], list):
            if team_data["superscouting"]:
                aggregated["superscouting_notes"] = [team_data["superscouting"][0]]
                aggregated["data_sources"].append("superscouting")

        return aggregated

    def _aggregate_scouting_metrics(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate average metrics from scouting data with text field support.
        
        Args:
            scouting_data: List of match scouting data
            
        Returns:
            Dictionary of averaged metrics and collected text data
        """
        metrics_sum = {}
        metrics_count = {}
        text_data = {}

        # Accumulate metrics from all matches
        for match_data in scouting_data:
            if not isinstance(match_data, dict):
                continue

            for key, value in match_data.items():
                # Skip standard non-metric fields
                if key in ["team_number", "match_number", "qual_number", "alliance_color", "notes", "timestamp"]:
                    continue

                if isinstance(value, (int, float)):
                    # Handle numeric fields
                    if key not in metrics_sum:
                        metrics_sum[key] = 0
                        metrics_count[key] = 0
                    metrics_sum[key] += value
                    metrics_count[key] += 1
                elif isinstance(value, str) and value.strip():
                    # Handle text fields - collect all non-empty values
                    if key not in text_data:
                        text_data[key] = []
                    text_data[key].append(value.strip())

        # Calculate averages for numeric fields
        averaged_metrics = {}
        for metric in metrics_sum:
            if metrics_count[metric] > 0:
                averaged_metrics[metric] = round(metrics_sum[metric] / metrics_count[metric], 2)

        # Add text data with consolidation
        for field, values in text_data.items():
            # Remove duplicates while preserving order
            unique_values = []
            seen = set()
            for value in values:
                if value not in seen:
                    unique_values.append(value)
                    seen.add(value)
            
            # Store as concatenated string if multiple unique values
            if len(unique_values) == 1:
                averaged_metrics[field] = unique_values[0]
            elif len(unique_values) > 1:
                averaged_metrics[field] = " | ".join(unique_values)

        return averaged_metrics

    def _apply_label_mappings(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply enhanced label mappings to transform field names and add text field support.
        
        Args:
            metrics: Original metrics with generic field names
            
        Returns:
            Enhanced metrics with label-enhanced field names and text data support
        """
        if not isinstance(metrics, dict):
            logger.warning(f"Expected dict for metrics, got {type(metrics)}")
            return {}
            
        enhanced_metrics = {}
        text_fields = {}
        
        try:
            # Keep all original metrics for compatibility
            enhanced_metrics.update(metrics)
            
            # Add enhanced metrics using unified label mappings
            if self.label_mappings:
                enhanced_count = 0
                text_fields_count = 0
                
                for original_field, value in metrics.items():
                    if not isinstance(original_field, str):
                        continue
                        
                    if original_field in self.label_mappings:
                        try:
                            label_info = self.label_mappings[original_field]
                            enhanced_field = label_info.get("label", "")
                            data_type = label_info.get("data_type", "count")
                            
                            # Validate enhanced field name
                            if isinstance(enhanced_field, str) and enhanced_field.strip():
                                if data_type == "text":
                                    # Handle text fields separately
                                    text_fields[enhanced_field] = {
                                        "value": value,
                                        "description": label_info.get("description", ""),
                                        "category": label_info.get("category", "unknown"),
                                        "usage_context": label_info.get("usage_context", "")
                                    }
                                    text_fields_count += 1
                                else:
                                    # Handle numeric fields
                                    enhanced_metrics[enhanced_field] = value
                                    enhanced_count += 1
                                
                                logger.debug(f"Enhanced field: {original_field} -> {enhanced_field} ({data_type})")
                        except Exception as e:
                            logger.warning(f"Error applying label mapping for {original_field}: {e}")
                
                # Add text fields to enhanced metrics with special prefix
                if text_fields:
                    enhanced_metrics["text_fields"] = text_fields
                
                if enhanced_count > 0:
                    logger.info(f"Enhanced {enhanced_count} numeric and {text_fields_count} text field names with scouting labels")
            else:
                logger.debug("No label mappings available")
        
        except Exception as e:
            logger.error(f"Error applying enhanced label mappings: {e}")
            # Return original metrics if enhancement fails
            return metrics
        
        return enhanced_metrics

    def get_teams_for_analysis(
        self,
        exclude_teams: Optional[List[int]] = None,
        team_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get teams prepared for analysis with all aggregated data.
        
        Args:
            exclude_teams: List of team numbers to exclude
            team_numbers: Specific team numbers to include (if provided, only these teams)
            
        Returns:
            List of teams ready for analysis
        """
        # Filter teams based on criteria
        filtered_teams = self.filter_teams_by_criteria(exclude_teams=exclude_teams)

        # If specific team numbers provided, filter to only those
        if team_numbers:
            team_numbers_set = set(team_numbers)
            filtered_teams = {
                key: data for key, data in filtered_teams.items()
                if data.get("team_number") in team_numbers_set
            }

        # Aggregate metrics for each team
        teams_for_analysis = []
        for team_data in filtered_teams.values():
            aggregated_team = self.aggregate_team_metrics(team_data)
            teams_for_analysis.append(aggregated_team)

        # Sort by team number for consistency
        teams_for_analysis.sort(key=lambda x: x.get("team_number", 0))

        logger.info(f"Prepared {len(teams_for_analysis)} teams for analysis")
        return teams_for_analysis

    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the available data.
        
        Returns:
            Dictionary with data statistics
        """
        stats = {
            "total_teams": len(self.teams_data),
            "teams_with_scouting": 0,
            "teams_with_statbotics": 0,
            "teams_with_ranking": 0,
            "teams_with_superscouting": 0,
            "total_matches": 0,
            "average_matches_per_team": 0.0,
            "metrics_available": set()
        }

        total_matches = 0
        teams_with_matches = 0

        for team_data in self.teams_data.values():
            if not isinstance(team_data, dict):
                continue

            # Count data source availability
            if "scouting_data" in team_data and isinstance(team_data["scouting_data"], list):
                stats["teams_with_scouting"] += 1
                match_count = len(team_data["scouting_data"])
                total_matches += match_count
                if match_count > 0:
                    teams_with_matches += 1

                # Collect available metrics
                for match in team_data["scouting_data"]:
                    if isinstance(match, dict):
                        for key in match.keys():
                            if key not in ["team_number", "match_number", "alliance_color", "notes"]:
                                stats["metrics_available"].add(key)

            if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
                stats["teams_with_statbotics"] += 1
                for key in team_data["statbotics"].keys():
                    stats["metrics_available"].add(f"statbotics_{key}")

            if "ranking" in team_data and isinstance(team_data["ranking"], dict):
                stats["teams_with_ranking"] += 1

            if "superscouting" in team_data and isinstance(team_data["superscouting"], list):
                if team_data["superscouting"]:
                    stats["teams_with_superscouting"] += 1

        stats["total_matches"] = total_matches
        stats["average_matches_per_team"] = (
            total_matches / teams_with_matches if teams_with_matches > 0 else 0.0
        )
        stats["metrics_available"] = list(stats["metrics_available"])

        return stats

    def refresh_dataset(self) -> bool:
        """
        Reload the dataset from file.
        
        Returns:
            True if reload was successful
        """
        try:
            new_dataset = self._load_dataset()
            if new_dataset:
                self.dataset = new_dataset
                self.teams_data = self.dataset.get("teams", {})
                self.year = self._determine_year()
                self.event_key = self.dataset.get("event_key", f"{self.year}arc")
                logger.info("Dataset refreshed successfully")
                return True
            else:
                logger.error("Failed to refresh dataset")
                return False
        except Exception as e:
            logger.error(f"Error refreshing dataset: {e}")
            return False

    def get_label_mapping_source(self) -> str:
        """
        Get information about the source of label mappings being used.
        
        Returns:
            String indicating the primary source of label mappings
        """
        if hasattr(self, 'field_selections') and self.field_selections:
            # Check if we have enhanced field selections with label mappings
            has_label_mappings = any(
                isinstance(field_info, dict) and field_info.get('label')
                for field_info in self.field_selections.values()
            )
            if has_label_mappings:
                return "enhanced_field_selections"
        
        if hasattr(self, 'label_mappings') and self.label_mappings:
            return "game_labels_fallback"
        
        return "minimal_fallback"
    
    def generate_performance_signatures(self, output_filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate performance signatures for all teams in the dataset.
        
        This method is triggered after data validation is complete to create
        strategic intelligence signatures for each team's metrics.
        
        Args:
            output_filepath: Optional path to save performance signatures.
                           If None, generates filename based on event_key.
        
        Returns:
            Dictionary with signature generation results and metadata
        """
        try:
            from app.services.performance_signature_service import PerformanceSignatureService
            
            # Initialize performance signature service
            signature_service = PerformanceSignatureService(self.dataset_path)
            
            logger.info(f"Generating performance signatures for {self.event_key}...")
            
            # Generate profiles for all teams
            team_profiles = signature_service.generate_all_team_profiles()
            
            if not team_profiles:
                return {
                    "success": False,
                    "error": "No valid team profiles generated",
                    "teams_analyzed": 0
                }
            
            # Get metrics summary for reporting
            metrics_summary = signature_service.get_metric_summary()
            
            # Determine output filepath
            if output_filepath is None:
                data_dir = os.path.dirname(self.dataset_path)
                filename = f"performance_signatures_{self.event_key}.json"
                output_filepath = os.path.join(data_dir, filename)
            
            # Export team profiles
            signature_service.export_team_profiles(team_profiles, output_filepath)
            
            # Also export baselines for reference
            baseline_filepath = output_filepath.replace('.json', '_baselines.json')
            event_baselines = signature_service.get_event_baselines()
            signature_service.stats_service.export_baselines(baseline_filepath, event_baselines)
            
            logger.info(f"Performance signatures generated successfully:")
            logger.info(f"  Teams analyzed: {len(team_profiles)}")
            logger.info(f"  Metrics processed: {metrics_summary['metrics_analyzed']}")
            logger.info(f"  Signatures saved: {output_filepath}")
            logger.info(f"  Baselines saved: {baseline_filepath}")
            
            return {
                "success": True,
                "teams_analyzed": len(team_profiles),
                "metrics_processed": metrics_summary['metrics_analyzed'],
                "signatures_filepath": output_filepath,
                "baselines_filepath": baseline_filepath,
                "event_info": metrics_summary['event_info'],
                "processing_summary": {
                    "total_teams": metrics_summary['event_info']['total_teams'],
                    "teams_with_signatures": len(team_profiles),
                    "avg_matches_per_team": metrics_summary['event_info']['avg_matches_per_team'],
                    "event_level": metrics_summary['event_info']['event_level']
                },
                "message": f"Generated performance signatures for {len(team_profiles)} teams with {metrics_summary['metrics_analyzed']} metrics"
            }
            
        except ImportError as e:
            logger.error(f"Performance signature service not available: {e}")
            return {
                "success": False,
                "error": "Performance signature service not available",
                "message": "Performance signature generation requires PerformanceSignatureService"
            }
        except Exception as e:
            logger.error(f"Error generating performance signatures: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate performance signatures: {e}"
            }
    
    async def generate_strategic_intelligence_file(self, output_filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate strategic intelligence file for all teams using StrategicAnalysisService.
        
        This method is called after performance signature generation to create strategic
        intelligence files ready for Sprint 4 picklist enhancement.
        
        Args:
            output_filepath: Optional path to save strategic intelligence.
                           If None, generates filename based on event_key.
        
        Returns:
            Dictionary with strategic intelligence generation results and metadata
        """
        try:
            from app.services.strategic_analysis_service import StrategicAnalysisService
            import json
            from datetime import datetime
            
            # Initialize strategic analysis service
            strategic_service = StrategicAnalysisService()
            
            logger.info(f"Generating strategic intelligence for {self.event_key}...")
            
            # Get teams data for analysis (reuse existing method)
            teams_data = self.get_teams_for_analysis()
            
            if len(teams_data) < 5:
                return {
                    "success": False,
                    "error": f"Insufficient teams for strategic analysis: {len(teams_data)} < 5",
                    "teams_analyzed": len(teams_data)
                }
            
            # Generate strategic intelligence using batched processing
            intelligence_result = await strategic_service.generate_strategic_intelligence(teams_data)
            
            if intelligence_result.get("status") != "success":
                return {
                    "success": False,
                    "error": intelligence_result.get("error", "Strategic analysis failed"),
                    "teams_analyzed": len(teams_data)
                }
            
            # Determine output filepath
            if output_filepath is None:
                data_dir = os.path.dirname(self.dataset_path)
                filename = f"strategic_intelligence_{self.event_key}.json"
                output_filepath = os.path.join(data_dir, filename)
            
            # Get original teams data for metric averages calculation (before aggregation)
            original_teams_data = list(self.teams_data.values())
            
            # Enhance strategic signatures with metric averages for user priority weighting
            enhanced_strategic_signatures = self._add_metric_averages_to_signatures(
                intelligence_result.get("strategic_signatures", {}), 
                original_teams_data
            )
            
            # Create complete strategic intelligence file
            strategic_intelligence_file = {
                "event_key": self.event_key,
                "analysis_timestamp": datetime.now().isoformat(),
                "strategic_signatures": enhanced_strategic_signatures,
                "event_baselines": intelligence_result.get("event_baselines", {}),
                "processing_summary": {
                    "total_teams": len(teams_data),
                    "teams_processed": len(intelligence_result.get("strategic_signatures", {})),
                    "batches_processed": intelligence_result.get("batches_processed", 0),
                    "total_processing_time": intelligence_result.get("total_processing_time", 0),
                    "token_usage": intelligence_result.get("token_usage", {})
                }
            }
            
            # Export strategic intelligence file
            with open(output_filepath, 'w') as f:
                json.dump(strategic_intelligence_file, f, indent=2)
            
            logger.info(f"Strategic intelligence generated successfully:")
            logger.info(f"  Teams analyzed: {len(teams_data)}")
            logger.info(f"  Teams with signatures: {len(intelligence_result.get('strategic_signatures', {}))}")
            logger.info(f"  Batches processed: {intelligence_result.get('batches_processed', 0)}")
            logger.info(f"  File saved: {output_filepath}")
            
            return {
                "success": True,
                "teams_analyzed": len(teams_data),
                "teams_with_signatures": len(intelligence_result.get("strategic_signatures", {})),
                "batches_processed": intelligence_result.get("batches_processed", 0),
                "filepath": output_filepath,
                "processing_time": intelligence_result.get("total_processing_time", 0),
                "message": f"Generated strategic intelligence for {len(intelligence_result.get('strategic_signatures', {}))} teams"
            }
            
        except ImportError as e:
            logger.error(f"Strategic analysis service not available: {e}")
            return {
                "success": False,
                "error": "Strategic analysis service not available",
                "message": "Strategic intelligence generation requires StrategicAnalysisService"
            }
        except Exception as e:
            logger.error(f"Error generating strategic intelligence: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate strategic intelligence: {e}"
            }
    
    def _add_metric_averages_to_signatures(
        self, 
        strategic_signatures: Dict[str, Any], 
        teams_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add metric averages to strategic signatures for user priority weighting support.
        
        This method enhances strategic signatures with raw metric averages that can be
        used for user-defined priority weighting in picklist generation while maintaining
        the strategic intelligence benefits.
        
        Args:
            strategic_signatures: Strategic signatures from StrategicAnalysisService
            teams_data: Original teams data for metric calculation
            
        Returns:
            Enhanced strategic signatures with metric_averages added
        """
        try:
            # Create lookup map for teams data by team number
            teams_lookup = {team.get("team_number", 0): team for team in teams_data}
            
            # Enhance each strategic signature with metric averages
            enhanced_signatures = {}
            for team_key, signature in strategic_signatures.items():
                team_number = signature.get("team_number", 0)
                
                # Find corresponding team data
                team_data = teams_lookup.get(team_number)
                if not team_data:
                    logger.warning(f"No team data found for team {team_number} in strategic signatures")
                    enhanced_signatures[team_key] = signature
                    continue
                
                # Calculate metric averages for this team
                metric_averages = self._calculate_team_metric_averages(team_data)
                
                # Create enhanced signature with metric averages
                enhanced_signature = signature.copy()
                enhanced_signature["metric_averages"] = metric_averages
                enhanced_signatures[team_key] = enhanced_signature
                
            logger.info(f"Enhanced {len(enhanced_signatures)} strategic signatures with metric averages")
            return enhanced_signatures
            
        except Exception as e:
            logger.error(f"Error adding metric averages to signatures: {e}")
            return strategic_signatures  # Return original signatures on error
    
    def _calculate_team_metric_averages(self, team_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate metric averages for a single team.
        
        This method extracts all numerical metrics from team data and calculates
        averages for use in user priority weighting system.
        
        Args:
            team_data: Team data dictionary from unified dataset
            
        Returns:
            Dictionary of metric names to average values
        """
        try:
            metric_averages = {}
            
            # Get aggregated metrics if available (these are already averages)
            aggregated_metrics = team_data.get("aggregated_metrics", {})
            for metric_name, metric_value in aggregated_metrics.items():
                if isinstance(metric_value, (int, float)) and metric_value is not None:
                    metric_averages[metric_name] = round(float(metric_value), 2)
            
            # Calculate averages from scouting_data (match-by-match data)
            scouting_data = team_data.get("scouting_data", [])
            if scouting_data:
                match_metrics = {}
                
                # Collect all metric values across matches
                for match_data in scouting_data:
                    for metric_name, metric_value in match_data.items():
                        # Skip non-numeric fields like match_number, team_number, strategy_field
                        if (isinstance(metric_value, (int, float)) and 
                            metric_value is not None and 
                            metric_name not in ['match_number', 'qual_number', 'team_number']):
                            
                            if metric_name not in match_metrics:
                                match_metrics[metric_name] = []
                            match_metrics[metric_name].append(float(metric_value))
                
                # Calculate averages for match-level metrics
                for metric_name, values in match_metrics.items():
                    if values and metric_name not in metric_averages:  # Don't override aggregated metrics
                        average_value = sum(values) / len(values)
                        metric_averages[metric_name] = round(average_value, 2)
            
            # Also check for 'matches' structure (alternative data format)
            matches = team_data.get("matches", [])
            if matches and not scouting_data:  # Only if scouting_data not available
                match_metrics = {}
                
                for match in matches:
                    match_data = match.get("data", {})
                    for metric_name, metric_value in match_data.items():
                        if isinstance(metric_value, (int, float)) and metric_value is not None:
                            if metric_name not in match_metrics:
                                match_metrics[metric_name] = []
                            match_metrics[metric_name].append(float(metric_value))
                
                # Calculate averages for match-level metrics
                for metric_name, values in match_metrics.items():
                    if values and metric_name not in metric_averages:
                        average_value = sum(values) / len(values)
                        metric_averages[metric_name] = round(average_value, 2)
            
            logger.debug(f"Calculated {len(metric_averages)} metric averages for team {team_data.get('team_number', 'unknown')}")
            return metric_averages
            
        except Exception as e:
            logger.error(f"Error calculating metric averages for team {team_data.get('team_number', 'unknown')}: {e}")
            return {}