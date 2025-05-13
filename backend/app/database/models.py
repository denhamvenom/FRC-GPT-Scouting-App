# backend/app/database/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Table, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

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

class ArchivedEvent(Base):
    """Model for storing archived event data"""
    __tablename__ = "archived_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # User-friendly name for the archive
    event_key = Column(String, index=True)
    year = Column(Integer)

    # Archive data
    archive_data = Column(LargeBinary)  # SQLite BLOB to store serialized event data
    archive_metadata = Column(JSON)  # JSON metadata about the archive (tables, counts, etc.)

    # Archive status
    is_active = Column(Boolean, default=False)  # Whether this is the currently active archive

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, nullable=True)  # User who created the archive
    notes = Column(String, nullable=True)  # Optional notes about the archive

    @property
    def formatted_date(self):
        """Return a formatted date string for display"""
        if self.created_at:
            return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown date"


class SheetConfiguration(Base):
    """Model for storing Google Sheets configuration"""
    __tablename__ = "sheet_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # User-friendly name for this configuration
    spreadsheet_id = Column(String, index=True)  # Google Sheets ID

    # Sheet names for different data types (tab names in the spreadsheet)
    match_scouting_sheet = Column(String)
    pit_scouting_sheet = Column(String, nullable=True)
    super_scouting_sheet = Column(String, nullable=True)

    # Event association
    event_key = Column(String, index=True)
    year = Column(Integer)

    # Metadata
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Cache for sheet headers (to avoid repeated API calls)
    match_scouting_headers = Column(JSON, nullable=True)
    pit_scouting_headers = Column(JSON, nullable=True)
    super_scouting_headers = Column(JSON, nullable=True)

    @property
    def formatted_date(self):
        """Return a formatted date string for display"""
        if self.created_at:
            return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown date"