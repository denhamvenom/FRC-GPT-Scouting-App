import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.picklist_service import build_picklist_from_unified_data

router = APIRouter()


class PicklistRequest(BaseModel):
    first_pick_priorities: List[str]
    second_pick_priorities: List[str]
    third_pick_priorities: List[str]


@router.post("/picklist/build")
def build_picklist(request: PicklistRequest):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    unified_dataset_path = os.path.join(base_dir, "..", "data", "unified_event_2025arc.json")
    unified_dataset_path = os.path.normpath(unified_dataset_path)

    picklist = build_picklist_from_unified_data(
        unified_dataset_path=unified_dataset_path,
        first_pick_priorities=request.first_pick_priorities,
        second_pick_priorities=request.second_pick_priorities,
        third_pick_priorities=request.third_pick_priorities
    )

    return {"picklist": picklist}
