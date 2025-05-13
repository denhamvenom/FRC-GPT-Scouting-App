# backend/app/services/sheet_config_service.py

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.database.models import SheetConfiguration

# Configure logging
logger = logging.getLogger("sheet_config_service")

async def create_sheet_config(
    db: Session,
    name: str,
    spreadsheet_id: str,
    match_scouting_sheet: str,
    event_key: str,
    year: int,
    pit_scouting_sheet: Optional[str] = None,
    super_scouting_sheet: Optional[str] = None,
    set_active: bool = True
) -> Dict[str, Any]:
    """
    Create a new sheet configuration.
    
    Args:
        db: Database session
        name: User-friendly name for this configuration
        spreadsheet_id: Google Sheets ID
        match_scouting_sheet: Name of the match scouting sheet tab
        event_key: TBA event key (e.g., "2024txirv")
        year: Event year
        pit_scouting_sheet: Optional name of the pit scouting sheet tab
        super_scouting_sheet: Optional name of the super scouting sheet tab
        set_active: Whether to set this as the active configuration
        
    Returns:
        Dictionary with status and configuration details
    """
    try:
        # Check if a configuration with the same name and event already exists
        existing_config = db.query(SheetConfiguration).filter(
            and_(
                SheetConfiguration.name == name,
                SheetConfiguration.event_key == event_key,
                SheetConfiguration.year == year
            )
        ).first()
        
        if existing_config:
            # Update existing configuration
            existing_config.spreadsheet_id = spreadsheet_id
            existing_config.match_scouting_sheet = match_scouting_sheet
            existing_config.pit_scouting_sheet = pit_scouting_sheet
            existing_config.super_scouting_sheet = super_scouting_sheet
            
            if set_active:
                await set_active_configuration(db, existing_config.id, event_key, year)
                
            db.commit()
            db.refresh(existing_config)
            
            return {
                "status": "success",
                "message": f"Updated sheet configuration '{name}' for event {event_key}",
                "config_id": existing_config.id,
                "is_new": False
            }
        else:
            # Create new configuration
            new_config = SheetConfiguration(
                name=name,
                spreadsheet_id=spreadsheet_id,
                match_scouting_sheet=match_scouting_sheet,
                pit_scouting_sheet=pit_scouting_sheet,
                super_scouting_sheet=super_scouting_sheet,
                event_key=event_key,
                year=year,
                is_active=set_active
            )
            
            db.add(new_config)
            
            # If this is set as active, deactivate other configurations for this event
            if set_active:
                await deactivate_other_configurations(db, event_key, year)
                
            db.commit()
            db.refresh(new_config)
            
            return {
                "status": "success",
                "message": f"Created new sheet configuration '{name}' for event {event_key}",
                "config_id": new_config.id,
                "is_new": True
            }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error creating sheet configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Error creating sheet configuration: {str(e)}"
        }

async def get_sheet_configurations(
    db: Session,
    event_key: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get a list of sheet configurations, optionally filtered by event and year.
    
    Args:
        db: Database session
        event_key: Optional TBA event key to filter by
        year: Optional event year to filter by
        
    Returns:
        Dictionary with status and configurations
    """
    try:
        query = db.query(SheetConfiguration)
        
        if event_key:
            query = query.filter(SheetConfiguration.event_key == event_key)
            
        if year:
            query = query.filter(SheetConfiguration.year == year)
            
        configs = query.order_by(SheetConfiguration.created_at.desc()).all()
        
        return {
            "status": "success",
            "configurations": [
                {
                    "id": config.id,
                    "name": config.name,
                    "spreadsheet_id": config.spreadsheet_id,
                    "match_scouting_sheet": config.match_scouting_sheet,
                    "pit_scouting_sheet": config.pit_scouting_sheet,
                    "super_scouting_sheet": config.super_scouting_sheet,
                    "event_key": config.event_key,
                    "year": config.year,
                    "is_active": config.is_active,
                    "created_at": config.formatted_date
                }
                for config in configs
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting sheet configurations: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting sheet configurations: {str(e)}"
        }

async def get_sheet_configuration(
    db: Session,
    config_id: int
) -> Dict[str, Any]:
    """
    Get a specific sheet configuration by ID.
    
    Args:
        db: Database session
        config_id: Configuration ID
        
    Returns:
        Dictionary with status and configuration details
    """
    try:
        config = db.query(SheetConfiguration).filter(SheetConfiguration.id == config_id).first()
        
        if not config:
            return {
                "status": "error",
                "message": f"Configuration with ID {config_id} not found"
            }
            
        return {
            "status": "success",
            "configuration": {
                "id": config.id,
                "name": config.name,
                "spreadsheet_id": config.spreadsheet_id,
                "match_scouting_sheet": config.match_scouting_sheet,
                "pit_scouting_sheet": config.pit_scouting_sheet,
                "super_scouting_sheet": config.super_scouting_sheet,
                "event_key": config.event_key,
                "year": config.year,
                "is_active": config.is_active,
                "created_at": config.formatted_date,
                "match_scouting_headers": config.match_scouting_headers,
                "pit_scouting_headers": config.pit_scouting_headers,
                "super_scouting_headers": config.super_scouting_headers
            }
        }
    except Exception as e:
        logger.exception(f"Error getting sheet configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting sheet configuration: {str(e)}"
        }

async def get_active_configuration(
    db: Session,
    event_key: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """First try with event_key and year filters, but if that returns nothing,
       fall back to just finding any active configuration."""
    """
    Get the active sheet configuration for an event.
    
    Args:
        db: Database session
        event_key: Optional TBA event key to filter by
        year: Optional event year to filter by
        
    Returns:
        Dictionary with status and configuration details
    """
    try:
        # First try with all filters
        filtered_query = db.query(SheetConfiguration).filter(SheetConfiguration.is_active == True)

        logger.info(f"Looking for active configuration with event_key={event_key}, year={year}")

        if event_key:
            filtered_query = filtered_query.filter(SheetConfiguration.event_key == event_key)
            logger.info(f"Added event_key filter: {event_key}")

        if year:
            filtered_query = filtered_query.filter(SheetConfiguration.year == year)
            logger.info(f"Added year filter: {year}")

        config = filtered_query.first()
        logger.info(f"Found configuration with filters: {config is not None}")

        # If no config found with filters, try without event_key filter
        if not config and event_key and year:
            logger.info(f"No config found with event_key filter, trying just with year={year}")
            year_query = db.query(SheetConfiguration).filter(
                SheetConfiguration.is_active == True,
                SheetConfiguration.year == year
            )
            config = year_query.first()
            logger.info(f"Found configuration with just year filter: {config is not None}")

        # If still no config, try any active config
        if not config:
            logger.info(f"No config found with filters, trying any active config")
            any_query = db.query(SheetConfiguration).filter(SheetConfiguration.is_active == True)
            config = any_query.first()
            logger.info(f"Found any active configuration: {config is not None}")

        if not config:
            return {
                "status": "error",
                "message": "No active configuration found"
            }
            
        return {
            "status": "success",
            "configuration": {
                "id": config.id,
                "name": config.name,
                "spreadsheet_id": config.spreadsheet_id,
                "match_scouting_sheet": config.match_scouting_sheet,
                "pit_scouting_sheet": config.pit_scouting_sheet,
                "super_scouting_sheet": config.super_scouting_sheet,
                "event_key": config.event_key,
                "year": config.year,
                "is_active": config.is_active,
                "created_at": config.formatted_date,
                "match_scouting_headers": config.match_scouting_headers,
                "pit_scouting_headers": config.pit_scouting_headers,
                "super_scouting_headers": config.super_scouting_headers
            }
        }
    except Exception as e:
        logger.exception(f"Error getting active configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting active configuration: {str(e)}"
        }

async def set_active_configuration(
    db: Session,
    config_id: int,
    event_key: Optional[str] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Set a configuration as active and deactivate others for the same event.
    
    Args:
        db: Database session
        config_id: Configuration ID to set as active
        event_key: Optional TBA event key for deactivating other configurations
        year: Optional event year for deactivating other configurations
        
    Returns:
        Dictionary with status and result
    """
    try:
        config = db.query(SheetConfiguration).filter(SheetConfiguration.id == config_id).first()
        
        if not config:
            return {
                "status": "error",
                "message": f"Configuration with ID {config_id} not found"
            }
            
        # Use the configuration's event_key and year if not provided
        event_key = event_key or config.event_key
        year = year or config.year
        
        # Deactivate other configurations for this event
        await deactivate_other_configurations(db, event_key, year)
        
        # Set this configuration as active
        config.is_active = True
        db.commit()
        
        return {
            "status": "success",
            "message": f"Configuration '{config.name}' set as active for event {event_key}"
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error setting active configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Error setting active configuration: {str(e)}"
        }

async def deactivate_other_configurations(
    db: Session,
    event_key: str,
    year: int
) -> None:
    """
    Deactivate all configurations for an event except the specified one.
    
    Args:
        db: Database session
        event_key: TBA event key
        year: Event year
    """
    try:
        db.query(SheetConfiguration).filter(
            and_(
                SheetConfiguration.event_key == event_key,
                SheetConfiguration.year == year
            )
        ).update({"is_active": False})
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deactivating configurations: {str(e)}")
        raise

async def delete_configuration(
    db: Session,
    config_id: int
) -> Dict[str, Any]:
    """
    Delete a sheet configuration.
    
    Args:
        db: Database session
        config_id: Configuration ID to delete
        
    Returns:
        Dictionary with status and result
    """
    try:
        config = db.query(SheetConfiguration).filter(SheetConfiguration.id == config_id).first()
        
        if not config:
            return {
                "status": "error",
                "message": f"Configuration with ID {config_id} not found"
            }
            
        db.delete(config)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Configuration '{config.name}' deleted successfully"
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting configuration: {str(e)}")
        return {
            "status": "error",
            "message": f"Error deleting configuration: {str(e)}"
        }

async def update_sheet_headers(
    db: Session,
    config_id: int,
    sheet_type: str,
    headers: List[str]
) -> Dict[str, Any]:
    """
    Update the cached headers for a sheet configuration.
    
    Args:
        db: Database session
        config_id: Configuration ID
        sheet_type: Type of sheet ('match', 'pit', or 'super')
        headers: List of headers from the sheet
        
    Returns:
        Dictionary with status and result
    """
    try:
        config = db.query(SheetConfiguration).filter(SheetConfiguration.id == config_id).first()
        
        if not config:
            return {
                "status": "error",
                "message": f"Configuration with ID {config_id} not found"
            }
            
        # Update the appropriate headers field
        if sheet_type == 'match':
            config.match_scouting_headers = headers
        elif sheet_type == 'pit':
            config.pit_scouting_headers = headers
        elif sheet_type == 'super':
            config.super_scouting_headers = headers
        else:
            return {
                "status": "error",
                "message": f"Invalid sheet type: {sheet_type}"
            }
            
        db.commit()
        
        return {
            "status": "success",
            "message": f"Updated {sheet_type} headers for configuration '{config.name}'",
            "headers": headers
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating sheet headers: {str(e)}")
        return {
            "status": "error",
            "message": f"Error updating sheet headers: {str(e)}"
        }