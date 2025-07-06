"""Service for handling OpenAI GPT integration for team analysis."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from openai import AsyncOpenAI
from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger("gpt_analysis_service")


class GPTAnalysisService:
    """Handles OpenAI GPT integration for team analysis."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    async def get_initial_analysis(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get initial structured analysis from GPT.

        Args:
            messages: List of conversation messages

        Returns:
            Parsed JSON response from GPT
        """
        # Log the strategy analysis request
        logger.info("=" * 80)
        logger.info("GPT STRATEGY ANALYSIS REQUEST")
        logger.info("=" * 80)
        for i, message in enumerate(messages):
            logger.info(f"MESSAGE {i+1} ({message.get('role', 'unknown')}):")
            logger.info(message.get('content', ''))
            logger.info("-" * 40)
        logger.info("=" * 80)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        
        response_content = response.choices[0].message.content
        
        # Log the strategy analysis response
        logger.info("=" * 80)
        logger.info("GPT STRATEGY ANALYSIS RESPONSE")
        logger.info("=" * 80)
        logger.info("RAW RESPONSE:")
        logger.info(response_content)
        logger.info("=" * 80)
        
        return json.loads(response_content)

    async def get_followup_response(self, messages: List[Dict[str, str]]) -> str:
        """Get follow-up response from GPT.

        Args:
            messages: List of conversation messages

        Returns:
            GPT response text
        """
        # Log the follow-up request
        logger.info("=" * 80)
        logger.info("GPT FOLLOW-UP REQUEST")
        logger.info("=" * 80)
        for i, message in enumerate(messages):
            logger.info(f"MESSAGE {i+1} ({message.get('role', 'unknown')}):")
            logger.info(message.get('content', ''))
            logger.info("-" * 40)
        logger.info("=" * 80)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        
        response_content = response.choices[0].message.content
        
        # Log the follow-up response
        logger.info("=" * 80)
        logger.info("GPT FOLLOW-UP RESPONSE")
        logger.info("=" * 80)
        logger.info("RAW RESPONSE:")
        logger.info(response_content)
        logger.info("=" * 80)
        
        return response_content
