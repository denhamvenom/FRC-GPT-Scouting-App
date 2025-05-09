# backend/app/database/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base

class LockedPicklist(Base):
    """Model for storing locked picklists"""
    __tablename__ = "locked_picklists"

    id = Column(Integer, primary_key=True, index=True)
    team_number = Column(Integer, index=True)
    event_key = Column(String, index=True)
    year = Column(Integer)
    
    # JSON fields to store picklist data
    first_pick_data = Column(JSON)
    second_pick_data = Column(JSON)
    third_pick_data = Column(JSON, nullable=True)  # Optional for games without third picks
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships to alliance selections
    alliance_selections = relationship("AllianceSelection", back_populates="picklist")

class AllianceSelection(Base):
    """Model for storing alliance selection events"""
    __tablename__ = "alliance_selections"

    id = Column(Integer, primary_key=True, index=True)
    picklist_id = Column(Integer, ForeignKey("locked_picklists.id"))
    event_key = Column(String, index=True)
    year = Column(Integer)
    
    # Status tracking
    is_completed = Column(Boolean, default=False)
    current_round = Column(Integer, default=1)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    picklist = relationship("LockedPicklist", back_populates="alliance_selections")
    alliances = relationship("Alliance", back_populates="selection")
    team_statuses = relationship("TeamSelectionStatus", back_populates="selection")

class Alliance(Base):
    """Model for storing alliances in a selection"""
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, index=True)
    selection_id = Column(Integer, ForeignKey("alliance_selections.id"))
    alliance_number = Column(Integer)  # 1-8 for the 8 alliances
    
    # Team numbers (0 means empty slot)
    captain_team_number = Column(Integer, default=0)
    first_pick_team_number = Column(Integer, default=0)
    second_pick_team_number = Column(Integer, default=0)
    backup_team_number = Column(Integer, default=0, nullable=True)  # Optional backup
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    selection = relationship("AllianceSelection", back_populates="alliances")

class TeamSelectionStatus(Base):
    """Model for tracking team status during selection"""
    __tablename__ = "team_selection_statuses"

    id = Column(Integer, primary_key=True, index=True)
    selection_id = Column(Integer, ForeignKey("alliance_selections.id"))
    team_number = Column(Integer)
    
    # Status flags
    is_captain = Column(Boolean, default=False)
    is_picked = Column(Boolean, default=False)
    has_declined = Column(Boolean, default=False)
    round_eliminated = Column(Integer, nullable=True)  # Round in which team was eliminated
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    selection = relationship("AllianceSelection", back_populates="team_statuses")