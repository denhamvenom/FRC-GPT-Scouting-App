"""Service for handling OpenAI GPT integration for team analysis."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class GPTAnalysisService:
    """Handles OpenAI GPT integration for team analysis."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def get_initial_analysis(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get initial structured analysis from GPT.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Parsed JSON response from GPT
        """
        response = self.client.chat.completions.create(
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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()