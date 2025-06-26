"""Service for handling OpenAI GPT integration for team analysis."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI
from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL


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
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return json.loads(response.choices[0].message.content)

    async def get_followup_response(self, messages: List[Dict[str, str]]) -> str:
        """Get follow-up response from GPT.

        Args:
            messages: List of conversation messages

        Returns:
            GPT response text
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
