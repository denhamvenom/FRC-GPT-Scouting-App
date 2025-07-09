# backend/app/services/game_context_synthesis_service.py

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

logger = logging.getLogger("game_context_synthesis")

GPT_MODEL = OPENAI_MODEL


class SynthesisResult:
    """Data class for synthesis results with validation."""
    
    def __init__(
        self,
        success: bool,
        synthesized_context: Optional[str] = None,
        error: Optional[str] = None,
        processing_time: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        character_count: int = 0,
        cache_key: Optional[str] = None
    ):
        self.success = success
        self.synthesized_context = synthesized_context
        self.error = error
        self.processing_time = processing_time
        self.token_usage = token_usage or {}
        self.character_count = character_count
        self.cache_key = cache_key
        self.timestamp = datetime.now().isoformat()


class GameContextSynthesisService:
    """
    Service for synthesizing game manual sections into strategic context for picklist generation.
    
    This service compresses lengthy game manual sections into concise strategic summaries
    (~300-400 characters) that provide essential context for alliance selection while
    dramatically reducing token usage in subsequent GPT calls.
    
    Key Features:
    - Game/year/event agnostic design works with any FRC manual structure
    - Content-hash based caching prevents redundant processing
    - Integrates with existing field_selections metadata
    - GPT-powered compression maintains strategic decision-making context
    
    Thread Safety: Thread-safe for read operations, synchronization required for cache writes
    Dependencies: OpenAI API, file system access for caching
    """
    
    def __init__(self, cache_dir: str = "backend/app/cache"):
        """
        Initialize the game context synthesis service.
        
        Args:
            cache_dir: Directory to store synthesized context cache files
            
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
        self.synthesis_version = "1.0"
        self.target_char_count = 350  # Target ~300-400 characters
        self.max_tokens = 150  # Max tokens for synthesis response
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Initialized GameContextSynthesisService with cache dir: {self.cache_dir}")

    def _generate_content_hash(self, manual_content: str, selected_sections: List[str]) -> str:
        """
        Generate deterministic hash from manual content and section selections.
        
        Args:
            manual_content: Full manual text content
            selected_sections: List of section identifiers that were selected
            
        Returns:
            SHA-256 hash string for cache key generation
        """
        # Create deterministic input by combining content and selections
        content_data = {
            "manual_content": manual_content,
            "selected_sections": sorted(selected_sections),  # Sort for determinism
            "synthesis_version": self.synthesis_version
        }
        
        content_str = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _extract_selected_sections(self, manual_data: Dict[str, Any], field_selections: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Extract relevant manual sections based on field_selections metadata.
        
        This method is game-agnostic and works by:
        1. Analyzing field_selections to find manual section references
        2. Extracting corresponding sections from manual_data
        3. Combining sections into synthesis-ready text
        
        Args:
            manual_data: Full manual data structure (e.g., from manual_text_2025.json)
            field_selections: Field selection metadata with manual section references
            
        Returns:
            Tuple of (combined_text, section_identifiers)
        """
        selected_text_sections = []
        section_identifiers = []
        
        # Method 1: Check if manual_data has individual_sections (preferred for synthesis)
        if "individual_sections" in manual_data and manual_data["individual_sections"]:
            individual_sections = manual_data["individual_sections"]
            
            # Select key sections for synthesis (prioritize core game elements)
            priority_sections = []
            core_keywords = ["reef", "scoring", "coral", "algae", "cage", "processor", "barge", "match", "game"]
            
            # First, add sections that match core keywords
            for section_name, section_content in individual_sections.items():
                section_lower = section_name.lower()
                if any(keyword in section_lower for keyword in core_keywords):
                    priority_sections.append((section_name, section_content))
            
            # If we don't have enough priority sections, add others (up to 5 total sections)
            remaining_sections = [(name, content) for name, content in individual_sections.items() 
                                if not any(keyword in name.lower() for keyword in core_keywords)]
            
            max_sections = 5  # Limit to prevent token overflow
            all_sections = priority_sections + remaining_sections[:max_sections - len(priority_sections)]
            
            for section_name, section_content in all_sections[:max_sections]:
                selected_text_sections.append(section_content)
                section_identifiers.append(section_name)
            
            logger.info(f"Using {len(all_sections)} individual sections from manual data: {section_identifiers}")
        
        # Method 1b: Fallback to relevant_sections if individual_sections not available
        elif "relevant_sections" in manual_data:
            relevant_sections = manual_data["relevant_sections"]
            
            # Try to split large relevant_sections into smaller chunks to avoid token limits
            if len(relevant_sections) > 10000:  # If too large, take first portion
                logger.warning(f"Large relevant_sections ({len(relevant_sections)} chars), using first 8000 chars")
                relevant_sections = relevant_sections[:8000] + "...\n[Section truncated for synthesis]"
            
            selected_text_sections.append(relevant_sections)
            section_identifiers.append("relevant_sections")
            logger.info("Using truncated 'relevant_sections' from manual data")
        
        # Method 2: Look for section references in field_selections
        manual_section_refs = set()
        for field_name, field_info in field_selections.items():
            if isinstance(field_info, dict):
                # Check for manual section references in field metadata
                if "manual_section" in field_info:
                    manual_section_refs.add(field_info["manual_section"])
                if "game_context" in field_info:
                    manual_section_refs.add(field_info["game_context"])
        
        # Extract referenced sections from manual_data
        for section_ref in manual_section_refs:
            if section_ref in manual_data:
                selected_text_sections.append(manual_data[section_ref])
                section_identifiers.append(section_ref)
        
        # Method 3: Fallback - use common FRC manual section names
        common_sections = [
            "scoring", "game_rules", "point_values", "scoring_elements", 
            "field_elements", "autonomous", "teleop", "endgame", "ranking"
        ]
        
        for section_name in common_sections:
            if section_name in manual_data and section_name not in section_identifiers:
                selected_text_sections.append(manual_data[section_name])
                section_identifiers.append(section_name)
        
        # Combine all selected sections
        combined_text = "\n\n".join(selected_text_sections)
        
        logger.info(f"Extracted {len(section_identifiers)} manual sections: {section_identifiers}")
        return combined_text, section_identifiers

    async def _synthesize_with_gpt(self, manual_sections: str, game_name: str) -> str:
        """
        Use GPT to synthesize manual sections into strategic context.
        
        Args:
            manual_sections: Combined text from selected manual sections
            game_name: Name of the game for context
            
        Returns:
            Synthesized strategic context string
            
        Raises:
            Exception: If GPT synthesis fails
        """
        prompt = f"""
You are an expert FRC alliance selection strategist. Compress the following game manual sections into a concise strategic context summary for picklist generation.

REQUIREMENTS:
- Target length: 300-400 characters MAXIMUM
- Focus on scoring values and strategic priorities
- Include autonomous and endgame point opportunities
- Mention key game pieces and scoring locations
- Use concise, tactical language
- Prioritize information that affects team selection

GAME: {game_name}

MANUAL SECTIONS:
{manual_sections}

Compress to strategic essentials only (300-400 chars max):"""

        try:
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=0.1  # Low temperature for consistent results
            )
            
            synthesized_context = response.choices[0].message.content.strip()
            
            # Validate character count
            char_count = len(synthesized_context)
            if char_count > 500:
                logger.warning(f"Synthesized context too long ({char_count} chars), truncating")
                synthesized_context = synthesized_context[:500] + "..."
            
            return synthesized_context
            
        except Exception as e:
            logger.error(f"GPT synthesis failed: {e}")
            raise

    def _get_cache_path(self, cache_key: str) -> str:
        """Generate cache file path from cache key."""
        return os.path.join(self.cache_dir, f"synthesis_{cache_key}.json")

    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Load synthesized context from cache.
        
        Args:
            cache_key: Content hash for cache lookup
            
        Returns:
            Cached synthesized context or None if not found
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                
                # Validate cache format and version
                if (cache_data.get("version") == self.synthesis_version and
                    "synthesized_context" in cache_data):
                    logger.info(f"Loaded synthesized context from cache: {cache_key[:16]}...")
                    return cache_data["synthesized_context"]
                else:
                    logger.warning(f"Cache version mismatch, ignoring: {cache_key[:16]}...")
            
        except Exception as e:
            logger.warning(f"Failed to load from cache {cache_key[:16]}...: {e}")
        
        return None

    def _save_to_cache(self, cache_key: str, synthesized_context: str, metadata: Dict[str, Any]) -> None:
        """
        Save synthesized context to cache.
        
        Args:
            cache_key: Content hash for cache storage
            synthesized_context: Synthesized strategic context
            metadata: Additional metadata for cache entry
        """
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            "version": self.synthesis_version,
            "synthesized_context": synthesized_context,
            "timestamp": datetime.now().isoformat(),
            "character_count": len(synthesized_context),
            "metadata": metadata
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved synthesized context to cache: {cache_key[:16]}...")
            
        except Exception as e:
            logger.error(f"Failed to save to cache {cache_key[:16]}...: {e}")

    async def synthesize_game_context(
        self,
        manual_data: Dict[str, Any],
        field_selections: Dict[str, Any]
    ) -> SynthesisResult:
        """
        Synthesize game manual sections into strategic context.
        
        This method is completely game/year/event agnostic and works by:
        1. Extracting relevant sections based on field_selections metadata
        2. Generating content hash for caching
        3. Using GPT to compress sections into strategic context
        4. Caching results for future use
        
        Args:
            manual_data: Game manual data (any structure with text sections)
            field_selections: Field selection metadata with section references
            
        Returns:
            SynthesisResult with synthesized context or error information
        """
        start_time = time.time()
        
        try:
            # Extract relevant sections from manual
            manual_sections, section_ids = self._extract_selected_sections(manual_data, field_selections)
            
            if not manual_sections.strip():
                return SynthesisResult(
                    success=False,
                    error="No relevant manual sections found for synthesis"
                )
            
            # Generate content hash for caching
            cache_key = self._generate_content_hash(manual_sections, section_ids)
            
            # Check cache first
            cached_context = self._load_from_cache(cache_key)
            if cached_context:
                return SynthesisResult(
                    success=True,
                    synthesized_context=cached_context,
                    processing_time=time.time() - start_time,
                    character_count=len(cached_context),
                    cache_key=cache_key
                )
            
            # Extract game name for context
            game_name = manual_data.get("game_name", "FRC Game")
            
            # Synthesize with GPT
            logger.info(f"Synthesizing context for {game_name} using {len(section_ids)} sections")
            synthesized_context = await self._synthesize_with_gpt(manual_sections, game_name)
            
            # Save to cache
            metadata = {
                "game_name": game_name,
                "sections_used": section_ids,
                "manual_char_count": len(manual_sections)
            }
            self._save_to_cache(cache_key, synthesized_context, metadata)
            
            return SynthesisResult(
                success=True,
                synthesized_context=synthesized_context,
                processing_time=time.time() - start_time,
                character_count=len(synthesized_context),
                cache_key=cache_key
            )
            
        except Exception as e:
            logger.error(f"Game context synthesis failed: {e}")
            return SynthesisResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )

    def get_synthesis_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cached synthesis results.
        
        Returns:
            Dictionary with cache statistics and metadata
        """
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith("synthesis_")]
            
            stats = {
                "total_cached_syntheses": len(cache_files),
                "cache_directory": self.cache_dir,
                "synthesis_version": self.synthesis_version,
                "target_character_count": self.target_char_count
            }
            
            if cache_files:
                # Get sample metadata from recent cache entries
                recent_files = sorted(cache_files)[-5:]  # Last 5 files
                sample_metadata = []
                
                for cache_file in recent_files:
                    try:
                        cache_path = os.path.join(self.cache_dir, cache_file)
                        with open(cache_path, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                        
                        sample_metadata.append({
                            "cache_key": cache_file.replace("synthesis_", "").replace(".json", "")[:16],
                            "character_count": cache_data.get("character_count", 0),
                            "timestamp": cache_data.get("timestamp", ""),
                            "game_name": cache_data.get("metadata", {}).get("game_name", "Unknown")
                        })
                    except Exception:
                        continue
                
                stats["recent_syntheses"] = sample_metadata
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get synthesis stats: {e}")
            return {"error": str(e)}