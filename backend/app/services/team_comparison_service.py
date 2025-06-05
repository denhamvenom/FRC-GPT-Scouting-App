"""Service for comparing a small set of teams using GPT."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from app.services.picklist_generator_service import PicklistGeneratorService

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class TeamComparisonService:
    """Compare up to three teams and return a ranking and summary."""

    def __init__(self, unified_dataset_path: str) -> None:
        self.generator = PicklistGeneratorService(unified_dataset_path)

    async def compare_teams(
        self,
        team_numbers: List[int],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not team_numbers or len(team_numbers) < 2:
            raise ValueError("At least two teams must be provided")

        teams_data_all = self.generator._prepare_team_data_for_gpt()
        teams_data = [t for t in teams_data_all if t["team_number"] in team_numbers]
        if len(teams_data) != len(team_numbers):
            found = {t["team_number"] for t in teams_data}
            missing = [n for n in team_numbers if n not in found]
            raise ValueError(f"Teams not found in dataset: {missing}")

        teams_data.sort(key=lambda t: team_numbers.index(t["team_number"]))
        system_prompt = self.generator._create_system_prompt(pick_position, len(teams_data))
        team_index_map = {i + 1: t["team_number"] for i, t in enumerate(teams_data)}
        user_prompt = self.generator._create_user_prompt(
            your_team_number,
            pick_position,
            priorities,
            teams_data,
            team_numbers,
            team_index_map,
        )
        if question:
            user_prompt += f"\nQUESTION = {question}\nReturn answer in 'summary' field."

        self.generator._check_token_count(system_prompt, user_prompt)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        data = json.loads(response.choices[0].message.content)
        ordered = self.generator._parse_response_with_index_mapping(
            data, teams_data, team_index_map
        )
        return {
            "ordered_teams": ordered if ordered else teams_data,
            "summary": data.get("summary", ""),
        }
