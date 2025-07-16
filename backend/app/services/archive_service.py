# backend/app/services/archive_service.py

import os
import json
import pickle
import logging
import datetime
import shutil
import glob
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect, and_, or_

from app.database.models import (
    ArchivedEvent,
    LockedPicklist,
    AllianceSelection,
    Alliance,
    TeamSelectionStatus,
    SheetConfiguration,
)
from app.services.unified_event_data_service import get_unified_dataset_path

# Configure logging
logger = logging.getLogger("archive_service")

# Tables to archive
TABLES_TO_ARCHIVE = [
    "LockedPicklist",
    "AllianceSelection",
    "Alliance",
    "TeamSelectionStatus",
    "SheetConfiguration",  # Added to ensure Google Sheet configurations are archived
]

# Data directories and file patterns to include in archives
DATA_PATHS = {
    "manual_data": "backend/app/data/",
    "event_data": "backend/app/data/",
    "cache_data": "backend/app/cache/",
    "config_data": "backend/app/config/",
    "database": "backend/data/",
    "logs": "backend/logs/",
    "manual_processing": "backend/data/manual_processing_data_2025/"
}

# Essential files that should always be included in archives
ESSENTIAL_FILES = [
    # Game configuration files
    "field_metadata_2025.json",
    "game_labels_2025.json", 
    "manual_text_2025.json",
    "critical_mappings_2025.json",
    "schema_2025.json",
    "schema_superscout_2025.json",
    "schema_superscout_insights_2025.json",
    "schema_superscout_offsets_2025.json",
    "robot_groups_2025.json",
    # Config files
    "extraction_config.py",
    "openai_config.py",
    "statbotics_field_map_DEFAULT.json",
    # Database
    "scouting_app.db"
]


def _get_file_content_safe(file_path: str, file_type: str = "json") -> Optional[Any]:
    """
    Safely read file content with error handling.
    
    Args:
        file_path: Path to the file to read
        file_type: Type of file (json, text, binary)
        
    Returns:
        File content or None if file doesn't exist or can't be read
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            if file_type == "json":
                return json.load(f)
            elif file_type == "text":
                return f.read()
            else:  # binary
                with open(file_path, "rb") as bf:
                    return bf.read()
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return None


def _collect_event_specific_files(event_key: str, year: int) -> Dict[str, Any]:
    """
    Collect all event-specific data files.
    
    Args:
        event_key: TBA event key
        year: FRC season year
        
    Returns:
        Dictionary of event-specific file contents
    """
    files = {}
    
    # Get current working directory and construct base path
    base_path = os.getcwd()
    
    # Event-specific files to look for
    event_patterns = [
        f"field_selections_{year}{event_key}.json",
        f"unified_event_{year}{event_key}.json",
        f"test_enhanced_{year}{event_key}.json",
        f"enhanced_dataset_{year}{event_key}.json"
    ]
    
    # Determine data directories based on environment
    if base_path.endswith('/app'):  # Docker environment
        data_dirs = ["app/data/", "backend/app/data/", "backend/data/"]
    else:  # Local environment
        data_dirs = ["backend/app/data/", "backend/data/"]
    
    # Search in data directories
    for pattern in event_patterns:
        for data_dir in data_dirs:
            file_path = os.path.join(base_path, data_dir, pattern)
            content = _get_file_content_safe(file_path, "json")
            if content is not None:
                files[pattern] = content
                logger.info(f"Included event-specific file: {pattern}")
    
    return files


def _collect_manual_data_files(year: int) -> Dict[str, Any]:
    """
    Collect all manual data files (game configuration, schemas, etc.).
    
    Args:
        year: FRC season year
        
    Returns:
        Dictionary of manual data file contents
    """
    files = {}
    base_path = os.getcwd()
    
    # Manual data files to collect
    manual_files = [
        f"field_metadata_{year}.json",
        f"field_metadata_{year}_backup.json",
        f"field_metadata_{year}_corrected.json",
        f"game_labels_{year}.json",
        f"manual_text_{year}.json",
        f"critical_mappings_{year}.json",
        f"schema_{year}.json",
        f"schema_superscout_{year}.json",
        f"schema_superscout_insights_{year}.json",
        f"schema_superscout_offsets_{year}.json",
        f"robot_groups_{year}.json",
        f"unified_dataset_{year}.json"
    ]
    
    # Determine data directories based on environment
    if base_path.endswith('/app'):  # Docker environment
        data_dirs = ["app/data/", "backend/app/data/", "backend/data/"]
    else:  # Local environment
        data_dirs = ["backend/app/data/", "backend/data/", "backend/backend/app/data/"]
    
    # Search in data directories
    for filename in manual_files:
        for data_dir in data_dirs:
            file_path = os.path.join(base_path, data_dir, filename)
            content = _get_file_content_safe(file_path, "json")
            if content is not None:
                files[filename] = content
                logger.info(f"Included manual data file: {filename}")
                break  # Only include the first found instance
    
    return files


def _collect_cache_files(limit: int = 50) -> Dict[str, Any]:
    """
    Collect cache files (limited to avoid huge archives).
    
    Args:
        limit: Maximum number of cache files to include
        
    Returns:
        Dictionary of cache file contents
    """
    files = {}
    base_path = os.getcwd()
    
    # Determine cache directory based on environment
    if base_path.endswith('/app'):  # Docker environment
        cache_dir = os.path.join(base_path, "app/cache/")
    else:  # Local environment
        cache_dir = os.path.join(base_path, "backend/app/cache/")
    
    if not os.path.exists(cache_dir):
        return files
    
    try:
        # Get all cache files, sorted by modification time (most recent first)
        cache_files = glob.glob(os.path.join(cache_dir, "*.json"))
        cache_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Include up to the limit
        for i, file_path in enumerate(cache_files[:limit]):
            if i >= limit:
                break
                
            filename = os.path.basename(file_path)
            content = _get_file_content_safe(file_path, "json")
            if content is not None:
                files[f"cache_{filename}"] = content
                
        logger.info(f"Included {len(files)} cache files (limit: {limit})")
    except Exception as e:
        logger.warning(f"Error collecting cache files: {e}")
    
    return files


def _collect_config_files() -> Dict[str, Any]:
    """
    Collect configuration files.
    
    Returns:
        Dictionary of configuration file contents
    """
    files = {}
    base_path = os.getcwd()
    
    # Determine configuration file paths based on environment
    if base_path.endswith('/app'):  # Docker environment
        config_files = [
            ("app/config/extraction_config.py", "text"),
            ("app/config/openai_config.py", "text"),
            ("app/config/statbotics_field_map_DEFAULT.json", "json"),
            (".env.example", "text")
        ]
    else:  # Local environment
        config_files = [
            ("backend/app/config/extraction_config.py", "text"),
            ("backend/app/config/openai_config.py", "text"),
            ("backend/app/config/statbotics_field_map_DEFAULT.json", "json"),
            ("backend/.env.example", "text")
        ]
    
    for file_path, file_type in config_files:
        full_path = os.path.join(base_path, file_path)
        content = _get_file_content_safe(full_path, file_type)
        if content is not None:
            filename = os.path.basename(file_path)
            files[f"config_{filename}"] = content
            logger.info(f"Included config file: {filename}")
    
    return files


def _collect_manual_processing_data(year: int) -> Dict[str, Any]:
    """
    Collect manual processing data (parsed game manual sections).
    
    Args:
        year: FRC season year
        
    Returns:
        Dictionary of manual processing data
    """
    files = {}
    base_path = os.getcwd()
    
    # Determine manual processing file paths based on environment
    if base_path.endswith('/app'):  # Docker environment
        processing_files = [
            f"data/manual_processing_data_{year}/parsed_sections/{year}GameManual_selected_sections.txt",
            f"data/manual_processing_data_{year}/toc/{year}GameManual_toc.json"
        ]
    else:  # Local environment
        processing_files = [
            f"backend/data/manual_processing_data_{year}/parsed_sections/{year}GameManual_selected_sections.txt",
            f"backend/data/manual_processing_data_{year}/toc/{year}GameManual_toc.json"
        ]
    
    for file_path in processing_files:
        full_path = os.path.join(base_path, file_path)
        file_type = "json" if file_path.endswith(".json") else "text"
        content = _get_file_content_safe(full_path, file_type)
        if content is not None:
            filename = os.path.basename(file_path)
            files[f"manual_processing_{filename}"] = content
            logger.info(f"Included manual processing file: {filename}")
    
    return files


async def archive_current_event(
    db: Session,
    name: str,
    event_key: str,
    year: int,
    notes: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Archives the current event data for later restoration.

    Args:
        db: Database session
        name: User-friendly name for the archive
        event_key: TBA event key for the event being archived
        year: FRC season year
        notes: Optional notes about the archive
        created_by: Optional username of who created the archive

    Returns:
        Dictionary with archive status and information
    """
    try:
        # Log start of archiving process
        logger.info(f"Starting archive for event {event_key} ({year}) with name: {name}")

        # Check if we have data for this event
        picklists = (
            db.query(LockedPicklist)
            .filter(LockedPicklist.event_key == event_key, LockedPicklist.year == year)
            .all()
        )

        selections = (
            db.query(AllianceSelection)
            .filter(AllianceSelection.event_key == event_key, AllianceSelection.year == year)
            .all()
        )

        # Log what we found
        logger.info(
            f"Found {len(picklists)} picklists and {len(selections)} selections for event {event_key} ({year})"
        )

        # Initialize archive data and metadata
        archive_data = {}
        archive_metadata = {
            "tables": {},
            "event_key": event_key,
            "year": year,
            "archived_at": datetime.datetime.now().isoformat(),
            "is_empty": not (picklists or selections),
            "files": [],
            "data_types": {
                "event_specific": 0,
                "manual_data": 0,
                "cache_files": 0,
                "config_files": 0,
                "manual_processing": 0
            }
        }

        # Try to include unified dataset if it exists
        unified_dataset_path = get_unified_dataset_path(event_key)
        if os.path.exists(unified_dataset_path):
            try:
                with open(unified_dataset_path, "r", encoding="utf-8") as f:
                    unified_dataset = json.load(f)
                archive_data["unified_dataset"] = unified_dataset
                archive_metadata["tables"]["unified_dataset"] = 1
                archive_metadata["files"].append(unified_dataset_path)
                logger.info(f"Included unified dataset in archive: {unified_dataset_path}")
            except Exception as e:
                logger.error(f"Error including unified dataset in archive: {e}")
                # Continue without including unified dataset

        # Collect all additional data types
        logger.info("Collecting comprehensive data for archive...")
        
        # Collect event-specific files
        event_files = _collect_event_specific_files(event_key, year)
        if event_files:
            archive_data["event_specific_files"] = event_files
            archive_metadata["data_types"]["event_specific"] = len(event_files)
            logger.info(f"Included {len(event_files)} event-specific files")
        
        # Collect manual data files
        manual_files = _collect_manual_data_files(year)
        if manual_files:
            archive_data["manual_data_files"] = manual_files
            archive_metadata["data_types"]["manual_data"] = len(manual_files)
            logger.info(f"Included {len(manual_files)} manual data files")
        
        # Collect cache files (limited to avoid huge archives)
        cache_files = _collect_cache_files(limit=50)
        if cache_files:
            archive_data["cache_files"] = cache_files
            archive_metadata["data_types"]["cache_files"] = len(cache_files)
            logger.info(f"Included {len(cache_files)} cache files")
        
        # Collect configuration files
        config_files = _collect_config_files()
        if config_files:
            archive_data["config_files"] = config_files
            archive_metadata["data_types"]["config_files"] = len(config_files)
            logger.info(f"Included {len(config_files)} configuration files")
        
        # Collect manual processing data
        processing_files = _collect_manual_processing_data(year)
        if processing_files:
            archive_data["manual_processing_files"] = processing_files
            archive_metadata["data_types"]["manual_processing"] = len(processing_files)
            logger.info(f"Included {len(processing_files)} manual processing files")
        
        # Calculate total data file count
        total_data_files = sum(archive_metadata["data_types"].values())
        logger.info(f"Total data files included in archive: {total_data_files}")
        
        # Update the emptiness detection to consider all data types
        has_data = (picklists or selections or 
                   event_files or manual_files or 
                   cache_files or config_files or processing_files)
        archive_metadata["is_empty"] = not has_data
        
        if has_data:
            logger.info(f"Archive contains substantial data: {total_data_files} data files")
        else:
            logger.warning(f"Archive appears to be empty or minimal")

        if not picklists and not selections:
            logger.warning(f"No data found for event {event_key} ({year}), creating empty archive")
            # Continue with empty archive rather than returning error

        # Store picklists if we have any
        if picklists:
            picklist_data = []
            for picklist in picklists:
                # Convert SQLAlchemy model to dict
                inspector = inspect(picklist)
                attrs = {}
                for column in inspector.mapper.column_attrs:
                    attrs[column.key] = getattr(picklist, column.key)
                picklist_data.append(attrs)

            archive_data["LockedPicklist"] = picklist_data
            archive_metadata["tables"]["LockedPicklist"] = len(picklist_data)

            # Get picklist IDs for related data
            picklist_ids = [p.id for p in picklists]
        else:
            picklist_ids = []

        # Get and store sheet configurations for this event
        sheet_configs = (
            db.query(SheetConfiguration)
            .filter(SheetConfiguration.event_key == event_key, SheetConfiguration.year == year)
            .all()
        )

        if sheet_configs:
            sheet_config_data = []
            for config in sheet_configs:
                # Convert SQLAlchemy model to dict
                inspector = inspect(config)
                attrs = {}
                for column in inspector.mapper.column_attrs:
                    attrs[column.key] = getattr(config, column.key)
                sheet_config_data.append(attrs)

            archive_data["SheetConfiguration"] = sheet_config_data
            archive_metadata["tables"]["SheetConfiguration"] = len(sheet_config_data)
            logger.info(f"Included {len(sheet_config_data)} sheet configurations in archive")
        else:
            logger.info(f"No sheet configurations found for event {event_key} ({year})")

        # Get alliance selections - try by both picklist_id and direct event/year query
        selection_data = []

        # Query by event_key and year to catch all selections, even those not linked to picklists
        # This ensures we catch alliance selections used for alliance selection board
        if not selections:
            selections = (
                db.query(AllianceSelection)
                .filter(AllianceSelection.event_key == event_key, AllianceSelection.year == year)
                .all()
            )

        for selection in selections:
            inspector = inspect(selection)
            attrs = {}
            for column in inspector.mapper.column_attrs:
                attrs[column.key] = getattr(selection, column.key)
            selection_data.append(attrs)

        if selection_data:
            archive_data["AllianceSelection"] = selection_data
            archive_metadata["tables"]["AllianceSelection"] = len(selection_data)

        # Get selection IDs for related data
        selection_ids = [s.id for s in selections]

        # Get alliances
        if selection_ids:
            alliance_data = []
            alliances = db.query(Alliance).filter(Alliance.selection_id.in_(selection_ids)).all()

            for alliance in alliances:
                inspector = inspect(alliance)
                attrs = {}
                for column in inspector.mapper.column_attrs:
                    attrs[column.key] = getattr(alliance, column.key)
                alliance_data.append(attrs)

            if alliance_data:
                archive_data["Alliance"] = alliance_data
                archive_metadata["tables"]["Alliance"] = len(alliance_data)

            # Get team selection statuses
            status_data = []
            statuses = (
                db.query(TeamSelectionStatus)
                .filter(TeamSelectionStatus.selection_id.in_(selection_ids))
                .all()
            )

            for status in statuses:
                inspector = inspect(status)
                attrs = {}
                for column in inspector.mapper.column_attrs:
                    attrs[column.key] = getattr(status, column.key)
                status_data.append(attrs)

            if status_data:
                archive_data["TeamSelectionStatus"] = status_data
                archive_metadata["tables"]["TeamSelectionStatus"] = len(status_data)

        # Serialize the archive data - use JSON instead of pickle for better compatibility
        try:
            logger.info("Serializing archive data")
            serialized_data = pickle.dumps(archive_data)
        except Exception as e:
            logger.error(f"Error serializing archive data with pickle: {e}")
            # Fallback to JSON serialization
            try:
                json_data = json.dumps(archive_data).encode("utf-8")
                serialized_data = json_data
                logger.info("Using JSON serialization instead of pickle")
            except Exception as json_err:
                logger.error(f"Error serializing with JSON too: {json_err}")
                raise

        # Create archive record
        logger.info("Creating archive record in database")
        archive = ArchivedEvent(
            name=name,
            event_key=event_key,
            year=year,
            archive_data=serialized_data,
            archive_metadata=archive_metadata,
            notes=notes,
            created_by=created_by,
        )

        db.add(archive)
        db.commit()
        db.refresh(archive)

        logger.info(f"Successfully created archive with ID {archive.id}")

        return {
            "status": "success",
            "message": f"Successfully archived event {event_key} ({year})",
            "archive_id": archive.id,
            "metadata": archive_metadata,
        }

    except Exception as e:
        logger.exception(f"Error archiving event: {str(e)}")
        return {"status": "error", "message": f"Error archiving event: {str(e)}"}


async def clear_event_data(db: Session, event_key: str, year: int) -> Dict[str, Any]:
    """
    Clears all data for a specific event from the active database tables.

    Args:
        db: Database session
        event_key: TBA event key for the event
        year: FRC season year

    Returns:
        Dictionary with status and information about cleared data
    """
    try:
        counts = {}

        # Get picklists for this event
        picklists = (
            db.query(LockedPicklist)
            .filter(LockedPicklist.event_key == event_key, LockedPicklist.year == year)
            .all()
        )

        # Get picklist IDs
        picklist_ids = [p.id for p in picklists]

        # Get alliance selections
        selections = (
            db.query(AllianceSelection)
            .filter(
                or_(
                    AllianceSelection.picklist_id.in_(picklist_ids),
                    and_(AllianceSelection.event_key == event_key, AllianceSelection.year == year),
                )
            )
            .all()
        )

        # Get selection IDs
        selection_ids = [s.id for s in selections]

        # Delete team selection statuses
        status_count = (
            db.query(TeamSelectionStatus)
            .filter(TeamSelectionStatus.selection_id.in_(selection_ids))
            .delete(synchronize_session=False)
        )
        counts["TeamSelectionStatus"] = status_count

        # Delete alliances
        alliance_count = (
            db.query(Alliance)
            .filter(Alliance.selection_id.in_(selection_ids))
            .delete(synchronize_session=False)
        )
        counts["Alliance"] = alliance_count

        # Delete alliance selections
        selection_count = (
            db.query(AllianceSelection)
            .filter(
                or_(
                    AllianceSelection.picklist_id.in_(picklist_ids),
                    and_(AllianceSelection.event_key == event_key, AllianceSelection.year == year),
                )
            )
            .delete(synchronize_session=False)
        )
        counts["AllianceSelection"] = selection_count

        # Delete locked picklists
        picklist_count = (
            db.query(LockedPicklist)
            .filter(LockedPicklist.event_key == event_key, LockedPicklist.year == year)
            .delete(synchronize_session=False)
        )
        counts["LockedPicklist"] = picklist_count

        # Delete sheet configurations (unless keep_configs is True)
        # Note: We're adding this but leaving it commented out by default
        # because deleting sheet configs might be disruptive to the user workflow
        # Users may want to keep their sheet configurations even when clearing event data
        """
        sheet_config_count = db.query(SheetConfiguration).filter(
            SheetConfiguration.event_key == event_key,
            SheetConfiguration.year == year
        ).delete(synchronize_session=False)
        counts["SheetConfiguration"] = sheet_config_count
        """

        db.commit()

        # Check for and delete unified dataset
        unified_dataset_path = get_unified_dataset_path(event_key)
        if os.path.exists(unified_dataset_path):
            try:
                # Create a backup before deletion
                backup_path = f"{unified_dataset_path}.bak"
                shutil.copy2(unified_dataset_path, backup_path)

                # Delete the file
                os.remove(unified_dataset_path)
                counts["unified_dataset"] = 1
                logger.info(
                    f"Removed unified dataset: {unified_dataset_path} (backup at {backup_path})"
                )
            except Exception as e:
                logger.error(f"Error removing unified dataset: {e}")

        return {
            "status": "success",
            "message": f"Successfully cleared event data for {event_key} ({year})",
            "deleted_counts": counts,
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"Error clearing event data: {str(e)}")
        return {"status": "error", "message": f"Error clearing event data: {str(e)}"}


async def get_archived_events(db: Session) -> List[Dict[str, Any]]:
    """
    Get a list of all archived events.

    Args:
        db: Database session

    Returns:
        List of archived events with their metadata
    """
    try:
        archives = db.query(ArchivedEvent).order_by(ArchivedEvent.created_at.desc()).all()

        result = []
        for archive in archives:
            # Don't include the binary data in the listing
            result.append(
                {
                    "id": archive.id,
                    "name": archive.name,
                    "event_key": archive.event_key,
                    "year": archive.year,
                    "created_at": archive.formatted_date,
                    "created_by": archive.created_by,
                    "notes": archive.notes,
                    "is_active": archive.is_active,
                    "metadata": archive.archive_metadata,
                }
            )

        return result
    except Exception as e:
        logger.exception(f"Error getting archived events: {str(e)}")
        return []


async def get_archived_event(db: Session, archive_id: int) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific archived event.

    Args:
        db: Database session
        archive_id: ID of the archived event

    Returns:
        Archived event details or None if not found
    """
    try:
        archive = db.query(ArchivedEvent).filter(ArchivedEvent.id == archive_id).first()

        if not archive:
            return None

        return {
            "id": archive.id,
            "name": archive.name,
            "event_key": archive.event_key,
            "year": archive.year,
            "created_at": archive.formatted_date,
            "created_by": archive.created_by,
            "notes": archive.notes,
            "is_active": archive.is_active,
            "metadata": archive.archive_metadata,
        }
    except Exception as e:
        logger.exception(f"Error getting archived event: {str(e)}")
        return None


async def restore_archived_event(db: Session, archive_id: int) -> Dict[str, Any]:
    """
    Restore an archived event to the active database.

    Args:
        db: Database session
        archive_id: ID of the archived event to restore

    Returns:
        Dictionary with restore status and information
    """
    try:
        # Get the archive
        archive = db.query(ArchivedEvent).filter(ArchivedEvent.id == archive_id).first()

        if not archive:
            return {"status": "error", "message": f"Archive with ID {archive_id} not found"}

        # Deserialize the archive data - handle both pickle and JSON formats
        try:
            archive_data = pickle.loads(archive.archive_data)
        except Exception as e:
            logger.warning(f"Error deserializing with pickle, trying JSON: {e}")
            try:
                # Try to deserialize from JSON if pickle fails
                archive_data = json.loads(archive.archive_data.decode("utf-8"))
                logger.info("Successfully deserialized using JSON")
            except Exception as json_err:
                logger.error(f"Failed to deserialize archive data: {json_err}")
                raise Exception(
                    f"Could not restore archive data. Original error: {e}, JSON error: {json_err}"
                )

        # Check if data already exists for this event
        existing_picklists = (
            db.query(LockedPicklist)
            .filter(
                LockedPicklist.event_key == archive.event_key, LockedPicklist.year == archive.year
            )
            .all()
        )

        if existing_picklists:
            return {
                "status": "error",
                "message": f"Data already exists for event {archive.event_key} ({archive.year}). Please clear it before restoring.",
            }

        # Begin restoration
        restored_counts = {}
        picklist_map = {}  # Map old IDs to new IDs

        # Restore LockedPicklists
        if "LockedPicklist" in archive_data:
            for data in archive_data["LockedPicklist"]:
                old_id = data.pop("id")

                # Create new record
                new_picklist = LockedPicklist(**data)
                db.add(new_picklist)
                db.flush()  # Get the new ID

                # Map old ID to new ID
                picklist_map[old_id] = new_picklist.id

            restored_counts["LockedPicklist"] = len(picklist_map)

        # Restore AllianceSelections - do this even if there are no picklists
        if "AllianceSelection" in archive_data:
            selection_map = {}  # Map old IDs to new IDs

            for data in archive_data["AllianceSelection"]:
                old_id = data.pop("id")

                # Remap picklist_id to new ID only if it's linked to a picklist
                if "picklist_id" in data and data["picklist_id"] is not None:
                    if data["picklist_id"] in picklist_map:
                        data["picklist_id"] = picklist_map[data["picklist_id"]]
                    else:
                        # If the old picklist ID isn't in the map, set picklist_id to None
                        # This ensures we don't have broken foreign keys
                        logger.warning(
                            f"Picklist ID {data['picklist_id']} not found in picklist map - setting to None"
                        )
                        data["picklist_id"] = None

                # Create new record
                try:
                    new_selection = AllianceSelection(**data)
                    db.add(new_selection)
                    db.flush()  # Get the new ID

                    # Map old ID to new ID
                    selection_map[old_id] = new_selection.id
                    logger.info(
                        f"Restored alliance selection: old_id={old_id}, new_id={new_selection.id}"
                    )
                except Exception as e:
                    logger.error(f"Error restoring alliance selection {old_id}: {str(e)}")
                    logger.error(f"Alliance selection data: {data}")
                    raise

            restored_counts["AllianceSelection"] = len(selection_map)
            logger.info(f"Restored {len(selection_map)} alliance selections")

            # Restore Alliances
            if "Alliance" in archive_data:
                alliance_count = 0

                for data in archive_data["Alliance"]:
                    data.pop("id")

                    # Remap selection_id to new ID
                    if data["selection_id"] in selection_map:
                        original_selection_id = data["selection_id"]
                        data["selection_id"] = selection_map[data["selection_id"]]

                        try:
                            # Create new record
                            new_alliance = Alliance(**data)
                            db.add(new_alliance)
                            db.flush()
                            logger.info(
                                f"Restored alliance: selection_id={original_selection_id}->{data['selection_id']}, alliance={new_alliance.alliance_number}"
                            )
                            alliance_count += 1
                        except Exception as e:
                            logger.error(f"Error restoring alliance: {str(e)}")
                            logger.error(f"Alliance data: {data}")
                            raise
                    else:
                        logger.warning(
                            f"Skipping alliance with unknown selection_id: {data['selection_id']}"
                        )

                restored_counts["Alliance"] = alliance_count
                logger.info(f"Restored {alliance_count} alliances")

            # Restore TeamSelectionStatuses
            if "TeamSelectionStatus" in archive_data:
                status_count = 0

                for data in archive_data["TeamSelectionStatus"]:
                    data.pop("id")

                    # Remap selection_id to new ID
                    if data["selection_id"] in selection_map:
                        original_selection_id = data["selection_id"]
                        data["selection_id"] = selection_map[data["selection_id"]]

                        try:
                            # Create new record
                            new_status = TeamSelectionStatus(**data)
                            db.add(new_status)
                            db.flush()
                            team_number = data.get("team_number", "unknown")
                            logger.info(
                                f"Restored team status: selection_id={original_selection_id}->{data['selection_id']}, team={team_number}"
                            )
                            status_count += 1
                        except Exception as e:
                            logger.error(f"Error restoring team status: {str(e)}")
                            logger.error(f"Team status data: {data}")
                            raise
                    else:
                        logger.warning(
                            f"Skipping team status with unknown selection_id: {data['selection_id']}"
                        )

                restored_counts["TeamSelectionStatus"] = status_count
                logger.info(f"Restored {status_count} team selection statuses")

        # Restore SheetConfigurations if they exist
        if "SheetConfiguration" in archive_data:
            sheet_config_count = 0

            for data in archive_data["SheetConfiguration"]:
                # Remove ID to create a new record
                data.pop("id")

                try:
                    # Check if a configuration with the same name already exists
                    existing_config = (
                        db.query(SheetConfiguration)
                        .filter(
                            SheetConfiguration.name == data["name"],
                            SheetConfiguration.event_key == data["event_key"],
                            SheetConfiguration.year == data["year"],
                        )
                        .first()
                    )

                    if existing_config:
                        logger.info(
                            f"Skipping sheet configuration '{data['name']}' as it already exists"
                        )
                        continue

                    # Create new record
                    new_config = SheetConfiguration(**data)
                    db.add(new_config)
                    db.flush()
                    logger.info(f"Restored sheet configuration: {data.get('name', 'unnamed')}")
                    sheet_config_count += 1
                except Exception as e:
                    logger.error(f"Error restoring sheet configuration: {str(e)}")
                    logger.error(f"Sheet configuration data: {data}")
                    raise

            restored_counts["SheetConfiguration"] = sheet_config_count
            logger.info(f"Restored {sheet_config_count} sheet configurations")

        # Commit all changes
        db.commit()

        # Restore unified dataset if it exists in the archive
        if "unified_dataset" in archive_data:
            try:
                unified_dataset = archive_data["unified_dataset"]
                unified_dataset_path = get_unified_dataset_path(archive.event_key)

                # Create the directory if needed
                os.makedirs(os.path.dirname(unified_dataset_path), exist_ok=True)

                # Write the unified dataset to disk
                with open(unified_dataset_path, "w", encoding="utf-8") as f:
                    json.dump(unified_dataset, f, indent=2)

                logger.info(f"Restored unified dataset to {unified_dataset_path}")
                restored_counts["unified_dataset"] = 1
            except Exception as e:
                logger.error(f"Error restoring unified dataset: {e}")
                # Continue even if unified dataset restoration fails

        # Restore event-specific files
        if "event_specific_files" in archive_data:
            try:
                event_files = archive_data["event_specific_files"]
                base_path = os.getcwd()
                event_file_count = 0
                
                for filename, content in event_files.items():
                    # Determine the appropriate directory
                    file_path = os.path.join(base_path, "backend/app/data/", filename)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        if isinstance(content, dict) or isinstance(content, list):
                            json.dump(content, f, indent=2)
                        else:
                            f.write(str(content))
                    
                    event_file_count += 1
                    logger.info(f"Restored event-specific file: {filename}")
                
                restored_counts["event_specific_files"] = event_file_count
                logger.info(f"Restored {event_file_count} event-specific files")
            except Exception as e:
                logger.error(f"Error restoring event-specific files: {e}")

        # Restore manual data files
        if "manual_data_files" in archive_data:
            try:
                manual_files = archive_data["manual_data_files"]
                base_path = os.getcwd()
                manual_file_count = 0
                
                for filename, content in manual_files.items():
                    # Determine the appropriate directory
                    file_path = os.path.join(base_path, "backend/app/data/", filename)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        if isinstance(content, dict) or isinstance(content, list):
                            json.dump(content, f, indent=2)
                        else:
                            f.write(str(content))
                    
                    manual_file_count += 1
                    logger.info(f"Restored manual data file: {filename}")
                
                restored_counts["manual_data_files"] = manual_file_count
                logger.info(f"Restored {manual_file_count} manual data files")
            except Exception as e:
                logger.error(f"Error restoring manual data files: {e}")

        # Restore cache files
        if "cache_files" in archive_data:
            try:
                cache_files = archive_data["cache_files"]
                base_path = os.getcwd()
                cache_dir = os.path.join(base_path, "backend/app/cache/")
                cache_file_count = 0
                
                # Create cache directory if needed
                os.makedirs(cache_dir, exist_ok=True)
                
                for filename, content in cache_files.items():
                    # Remove the "cache_" prefix
                    actual_filename = filename.replace("cache_", "")
                    file_path = os.path.join(cache_dir, actual_filename)
                    
                    # Write the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        if isinstance(content, dict) or isinstance(content, list):
                            json.dump(content, f, indent=2)
                        else:
                            f.write(str(content))
                    
                    cache_file_count += 1
                    logger.info(f"Restored cache file: {actual_filename}")
                
                restored_counts["cache_files"] = cache_file_count
                logger.info(f"Restored {cache_file_count} cache files")
            except Exception as e:
                logger.error(f"Error restoring cache files: {e}")

        # Restore configuration files
        if "config_files" in archive_data:
            try:
                config_files = archive_data["config_files"]
                base_path = os.getcwd()
                config_file_count = 0
                
                for filename, content in config_files.items():
                    # Remove the "config_" prefix and determine path
                    actual_filename = filename.replace("config_", "")
                    
                    if actual_filename.endswith('.py'):
                        file_path = os.path.join(base_path, "backend/app/config/", actual_filename)
                    elif actual_filename == '.env.example':
                        file_path = os.path.join(base_path, "backend/", actual_filename)
                    else:
                        file_path = os.path.join(base_path, "backend/app/config/", actual_filename)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        if isinstance(content, dict) or isinstance(content, list):
                            json.dump(content, f, indent=2)
                        else:
                            f.write(str(content))
                    
                    config_file_count += 1
                    logger.info(f"Restored config file: {actual_filename}")
                
                restored_counts["config_files"] = config_file_count
                logger.info(f"Restored {config_file_count} configuration files")
            except Exception as e:
                logger.error(f"Error restoring configuration files: {e}")

        # Restore manual processing files
        if "manual_processing_files" in archive_data:
            try:
                processing_files = archive_data["manual_processing_files"]
                base_path = os.getcwd()
                processing_file_count = 0
                
                for filename, content in processing_files.items():
                    # Remove the "manual_processing_" prefix
                    actual_filename = filename.replace("manual_processing_", "")
                    
                    # Determine the appropriate directory structure
                    if actual_filename.endswith('_toc.json'):
                        file_path = os.path.join(base_path, f"backend/data/manual_processing_data_{archive.year}/toc/", actual_filename)
                    else:
                        file_path = os.path.join(base_path, f"backend/data/manual_processing_data_{archive.year}/parsed_sections/", actual_filename)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        if isinstance(content, dict) or isinstance(content, list):
                            json.dump(content, f, indent=2)
                        else:
                            f.write(str(content))
                    
                    processing_file_count += 1
                    logger.info(f"Restored manual processing file: {actual_filename}")
                
                restored_counts["manual_processing_files"] = processing_file_count
                logger.info(f"Restored {processing_file_count} manual processing files")
            except Exception as e:
                logger.error(f"Error restoring manual processing files: {e}")

        return {
            "status": "success",
            "message": f"Successfully restored archive {archive.name} (ID: {archive_id})",
            "event_key": archive.event_key,
            "year": archive.year,
            "restored_counts": restored_counts,
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"Error restoring archived event: {str(e)}")
        return {"status": "error", "message": f"Error restoring archived event: {str(e)}"}


async def delete_archived_event(db: Session, archive_id: int) -> Dict[str, Any]:
    """
    Delete an archived event.

    Args:
        db: Database session
        archive_id: ID of the archived event to delete

    Returns:
        Dictionary with delete status and information
    """
    try:
        archive = db.query(ArchivedEvent).filter(ArchivedEvent.id == archive_id).first()

        if not archive:
            return {"status": "error", "message": f"Archive with ID {archive_id} not found"}

        # Get name for confirmation message
        name = archive.name
        event_key = archive.event_key
        year = archive.year

        # Delete the archive
        db.delete(archive)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully deleted archive {name}",
            "event_key": event_key,
            "year": year,
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting archived event: {str(e)}")
        return {"status": "error", "message": f"Error deleting archived event: {str(e)}"}
