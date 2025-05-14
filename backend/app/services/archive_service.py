# backend/app/services/archive_service.py

import os
import json
import pickle
import logging
import datetime
import shutil
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect, and_, or_

from app.database.models import ArchivedEvent, LockedPicklist, AllianceSelection, Alliance, TeamSelectionStatus, SheetConfiguration
from app.services.unified_event_data_service import get_unified_dataset_path

# Configure logging
logger = logging.getLogger("archive_service")

# Tables to archive
TABLES_TO_ARCHIVE = [
    "LockedPicklist",
    "AllianceSelection", 
    "Alliance", 
    "TeamSelectionStatus",
    "SheetConfiguration"  # Added to ensure Google Sheet configurations are archived
]

async def archive_current_event(
    db: Session, 
    name: str, 
    event_key: str, 
    year: int, 
    notes: Optional[str] = None,
    created_by: Optional[str] = None
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
        picklists = db.query(LockedPicklist).filter(
            LockedPicklist.event_key == event_key,
            LockedPicklist.year == year
        ).all()
        
        selections = db.query(AllianceSelection).filter(
            AllianceSelection.event_key == event_key,
            AllianceSelection.year == year
        ).all()
        
        # Log what we found
        logger.info(f"Found {len(picklists)} picklists and {len(selections)} selections for event {event_key} ({year})")
        
        # Initialize archive data and metadata
        archive_data = {}
        archive_metadata = {
            "tables": {},
            "event_key": event_key,
            "year": year,
            "archived_at": datetime.datetime.now().isoformat(),
            "is_empty": not (picklists or selections),
            "files": []
        }

        # Try to include unified dataset if it exists
        unified_dataset_path = get_unified_dataset_path(event_key)
        if os.path.exists(unified_dataset_path):
            try:
                with open(unified_dataset_path, 'r', encoding='utf-8') as f:
                    unified_dataset = json.load(f)
                archive_data['unified_dataset'] = unified_dataset
                archive_metadata['tables']['unified_dataset'] = 1
                archive_metadata['files'].append(unified_dataset_path)
                logger.info(f"Included unified dataset in archive: {unified_dataset_path}")
            except Exception as e:
                logger.error(f"Error including unified dataset in archive: {e}")
                # Continue without including unified dataset
        
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
        sheet_configs = db.query(SheetConfiguration).filter(
            SheetConfiguration.event_key == event_key,
            SheetConfiguration.year == year
        ).all()
        
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
            selections = db.query(AllianceSelection).filter(
                AllianceSelection.event_key == event_key,
                AllianceSelection.year == year
            ).all()

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
            alliances = db.query(Alliance).filter(
                Alliance.selection_id.in_(selection_ids)
            ).all()

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
            statuses = db.query(TeamSelectionStatus).filter(
                TeamSelectionStatus.selection_id.in_(selection_ids)
            ).all()

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
                json_data = json.dumps(archive_data).encode('utf-8')
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
            created_by=created_by
        )
        
        db.add(archive)
        db.commit()
        db.refresh(archive)
        
        logger.info(f"Successfully created archive with ID {archive.id}")
        
        return {
            "status": "success",
            "message": f"Successfully archived event {event_key} ({year})",
            "archive_id": archive.id,
            "metadata": archive_metadata
        }
        
    except Exception as e:
        logger.exception(f"Error archiving event: {str(e)}")
        return {
            "status": "error",
            "message": f"Error archiving event: {str(e)}"
        }

async def clear_event_data(
    db: Session, 
    event_key: str,
    year: int
) -> Dict[str, Any]:
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
        picklists = db.query(LockedPicklist).filter(
            LockedPicklist.event_key == event_key,
            LockedPicklist.year == year
        ).all()
        
        # Get picklist IDs
        picklist_ids = [p.id for p in picklists]
        
        # Get alliance selections
        selections = db.query(AllianceSelection).filter(
            or_(
                AllianceSelection.picklist_id.in_(picklist_ids),
                and_(
                    AllianceSelection.event_key == event_key,
                    AllianceSelection.year == year
                )
            )
        ).all()
        
        # Get selection IDs
        selection_ids = [s.id for s in selections]
        
        # Delete team selection statuses
        status_count = db.query(TeamSelectionStatus).filter(
            TeamSelectionStatus.selection_id.in_(selection_ids)
        ).delete(synchronize_session=False)
        counts["TeamSelectionStatus"] = status_count
        
        # Delete alliances
        alliance_count = db.query(Alliance).filter(
            Alliance.selection_id.in_(selection_ids)
        ).delete(synchronize_session=False)
        counts["Alliance"] = alliance_count
        
        # Delete alliance selections
        selection_count = db.query(AllianceSelection).filter(
            or_(
                AllianceSelection.picklist_id.in_(picklist_ids),
                and_(
                    AllianceSelection.event_key == event_key,
                    AllianceSelection.year == year
                )
            )
        ).delete(synchronize_session=False)
        counts["AllianceSelection"] = selection_count
        
        # Delete locked picklists
        picklist_count = db.query(LockedPicklist).filter(
            LockedPicklist.event_key == event_key,
            LockedPicklist.year == year
        ).delete(synchronize_session=False)
        counts["LockedPicklist"] = picklist_count
        
        # Delete sheet configurations (unless keep_configs is True)
        # Note: We're adding this but leaving it commented out by default
        # because deleting sheet configs might be disruptive to the user workflow
        # Users may want to keep their sheet configurations even when clearing event data
        '''
        sheet_config_count = db.query(SheetConfiguration).filter(
            SheetConfiguration.event_key == event_key,
            SheetConfiguration.year == year
        ).delete(synchronize_session=False)
        counts["SheetConfiguration"] = sheet_config_count
        '''

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
                logger.info(f"Removed unified dataset: {unified_dataset_path} (backup at {backup_path})")
            except Exception as e:
                logger.error(f"Error removing unified dataset: {e}")

        return {
            "status": "success",
            "message": f"Successfully cleared event data for {event_key} ({year})",
            "deleted_counts": counts
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error clearing event data: {str(e)}")
        return {
            "status": "error",
            "message": f"Error clearing event data: {str(e)}"
        }

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
            result.append({
                "id": archive.id,
                "name": archive.name,
                "event_key": archive.event_key,
                "year": archive.year,
                "created_at": archive.formatted_date,
                "created_by": archive.created_by,
                "notes": archive.notes,
                "is_active": archive.is_active,
                "metadata": archive.archive_metadata
            })
            
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
            "metadata": archive.archive_metadata
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
            return {
                "status": "error",
                "message": f"Archive with ID {archive_id} not found"
            }
            
        # Deserialize the archive data - handle both pickle and JSON formats
        try:
            archive_data = pickle.loads(archive.archive_data)
        except Exception as e:
            logger.warning(f"Error deserializing with pickle, trying JSON: {e}")
            try:
                # Try to deserialize from JSON if pickle fails
                archive_data = json.loads(archive.archive_data.decode('utf-8'))
                logger.info("Successfully deserialized using JSON")
            except Exception as json_err:
                logger.error(f"Failed to deserialize archive data: {json_err}")
                raise Exception(f"Could not restore archive data. Original error: {e}, JSON error: {json_err}")
        
        # Check if data already exists for this event
        existing_picklists = db.query(LockedPicklist).filter(
            LockedPicklist.event_key == archive.event_key,
            LockedPicklist.year == archive.year
        ).all()
        
        if existing_picklists:
            return {
                "status": "error",
                "message": f"Data already exists for event {archive.event_key} ({archive.year}). Please clear it before restoring."
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
                        logger.warning(f"Picklist ID {data['picklist_id']} not found in picklist map - setting to None")
                        data["picklist_id"] = None

                # Create new record
                try:
                    new_selection = AllianceSelection(**data)
                    db.add(new_selection)
                    db.flush()  # Get the new ID

                    # Map old ID to new ID
                    selection_map[old_id] = new_selection.id
                    logger.info(f"Restored alliance selection: old_id={old_id}, new_id={new_selection.id}")
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
                            logger.info(f"Restored alliance: selection_id={original_selection_id}->{data['selection_id']}, alliance={new_alliance.alliance_number}")
                            alliance_count += 1
                        except Exception as e:
                            logger.error(f"Error restoring alliance: {str(e)}")
                            logger.error(f"Alliance data: {data}")
                            raise
                    else:
                        logger.warning(f"Skipping alliance with unknown selection_id: {data['selection_id']}")

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
                            logger.info(f"Restored team status: selection_id={original_selection_id}->{data['selection_id']}, team={team_number}")
                            status_count += 1
                        except Exception as e:
                            logger.error(f"Error restoring team status: {str(e)}")
                            logger.error(f"Team status data: {data}")
                            raise
                    else:
                        logger.warning(f"Skipping team status with unknown selection_id: {data['selection_id']}")

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
                    existing_config = db.query(SheetConfiguration).filter(
                        SheetConfiguration.name == data["name"],
                        SheetConfiguration.event_key == data["event_key"],
                        SheetConfiguration.year == data["year"]
                    ).first()
                    
                    if existing_config:
                        logger.info(f"Skipping sheet configuration '{data['name']}' as it already exists")
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
                with open(unified_dataset_path, 'w', encoding='utf-8') as f:
                    json.dump(unified_dataset, f, indent=2)

                logger.info(f"Restored unified dataset to {unified_dataset_path}")
                restored_counts["unified_dataset"] = 1
            except Exception as e:
                logger.error(f"Error restoring unified dataset: {e}")
                # Continue even if unified dataset restoration fails

        return {
            "status": "success",
            "message": f"Successfully restored archive {archive.name} (ID: {archive_id})",
            "event_key": archive.event_key,
            "year": archive.year,
            "restored_counts": restored_counts
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error restoring archived event: {str(e)}")
        return {
            "status": "error",
            "message": f"Error restoring archived event: {str(e)}"
        }

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
            return {
                "status": "error",
                "message": f"Archive with ID {archive_id} not found"
            }
            
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
            "year": year
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting archived event: {str(e)}")
        return {
            "status": "error",
            "message": f"Error deleting archived event: {str(e)}"
        }