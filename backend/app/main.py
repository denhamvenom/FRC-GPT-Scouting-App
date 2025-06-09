# File: backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import traceback

# New configuration system imports
from app.config.settings import get_settings
from app.config.logging import setup_logging
from app.config.database import init_database
from app.core.dependencies import initialize_dependencies, cleanup_dependencies

# Initialize configuration and logging first
setup_logging()
logger = logging.getLogger(__name__)

# Initialize all dependencies
if not initialize_dependencies():
    logger.error("Failed to initialize dependencies")
    raise RuntimeError("Application initialization failed")

# Get application settings
settings = get_settings()

# Initialize database
init_database()

from app.api import health
from app.api import sheets
from app.api import sheets_headers  # Import the sheets headers API
from app.api import schema
from app.api import schema_save
from app.api import schema_superscout, schema_superscout_save
from app.api import validate
from app.api import setup
from app.api import prompt_builder_router
from app.api import unified_dataset  # Make sure this import is here
from app.api import field_selection  # Import the new field selection router
from app.api import picklist_analysis
from app.api import picklist_generator
from app.api import progress  # Import the progress tracking API
from app.api import debug_logs  # Import debug logs API
from app.api import alliance_selection  # Import alliance selection API
from app.api import archive  # Import event archiving API
from app.api import sheet_config  # Import sheet configuration API
from app.api import manuals as manuals_router  # Import the new manuals router
from app.api import team_comparison  # New team comparison API

app = FastAPI(
    title=settings.app.app_name,
    version=settings.app.app_version,
    debug=settings.app.debug
)

# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=settings.app.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to log all unhandled exceptions
    """
    error_msg = f"Unhandled exception: {str(exc)}"
    stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    # Log the full error with request details
    logger.error(f"{error_msg}\nRequest: {request.method} {request.url}\n{stack_trace}")

    # Return a JSON response
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )


# Include routers
app.include_router(health.router, prefix="/api/health")
app.include_router(sheets.router, prefix="/api/sheets")
app.include_router(sheets_headers.router)  # Already has prefix="/api/sheets" in its definition
app.include_router(schema.router)  # Router already has prefix="/api/schema"
app.include_router(schema_save.router, prefix="/api/schema")
app.include_router(schema_superscout.router, prefix="/api/schema/super")
app.include_router(schema_superscout_save.router, prefix="/api/schema/super")
app.include_router(validate.router)  # Router already has prefix="/api/validate"
app.include_router(setup.router)  # Router already has prefix="/api/setup"
app.include_router(prompt_builder_router.router, prefix="/api")
app.include_router(unified_dataset.router)  # Router already has prefix="/api/dataset"
app.include_router(field_selection.router)  # Add the field selection router
app.include_router(picklist_analysis.router, prefix="/api")
app.include_router(picklist_generator.router)
app.include_router(team_comparison.router)
app.include_router(progress.router, prefix="/api")  # Add the progress tracking API
app.include_router(debug_logs.router, prefix="/api/debug")  # Add the debug logs API
app.include_router(alliance_selection.router)  # Add the alliance selection API
app.include_router(archive.router)  # Add the event archiving API
app.include_router(sheet_config.router)  # Sheet configuration API already has prefix
app.include_router(manuals_router.router)  # Add the manuals router


# Legacy endpoints for backwards compatibility with frontend

@app.get("/api/unified/status")
async def legacy_unified_status(event_key: str, year: int = 2025):
    """
    Legacy endpoint for backward compatibility with frontend validation page.
    Maps to the new dataset status endpoint.
    """
    from app.services.unified_event_data_service import get_unified_dataset_path
    import os
    from datetime import datetime
    
    try:
        dataset_path = get_unified_dataset_path(event_key)
        
        if os.path.exists(dataset_path):
            return {
                "status": "exists",
                "path": dataset_path,
                "event_key": event_key,
                "year": year,
                "file_size": os.path.getsize(dataset_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(dataset_path)).isoformat()
            }
        else:
            return {
                "status": "not_found", 
                "path": None,
                "event_key": event_key,
                "year": year
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


@app.post("/api/unified/build")
async def legacy_unified_build(request: Request):
    """
    Legacy endpoint for backward compatibility with frontend field selection page.
    Maps to the new dataset build endpoint.
    """
    from app.api.schemas import BuildDatasetRequest
    import uuid
    from app.services.unified_event_data_service import build_unified_dataset
    import asyncio
    from datetime import datetime
    
    try:
        # Parse the request body
        body = await request.json()
        
        # Create a proper BuildDatasetRequest
        build_request = BuildDatasetRequest(
            event_key=body.get("event_key"),
            force_rebuild=body.get("force_rebuild", False),
            include_practice=body.get("include_practice", False),
            include_playoffs=body.get("include_playoffs", True),
            field_mappings=body.get("field_mappings", {}),
        )
        
        # Generate a unique operation ID
        operation_id = f"build_{build_request.event_key}_{uuid.uuid4().hex[:8]}"
        
        # Start the dataset build process in the background
        asyncio.create_task(
            build_unified_dataset(
                event_key=build_request.event_key,
                year=body.get("year", 2025),  # Use year from request body
                force_rebuild=build_request.force_rebuild,
                operation_id=operation_id,
            )
        )
        
        # Return legacy response format
        return {
            "status": "success",
            "message": "Dataset build initiated",
            "operation_id": operation_id,
            "event_key": build_request.event_key,
            "year": body.get("year", 2025)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info(f"Starting {settings.app.app_name} v{settings.app.app_version}")
    logger.info(f"Environment: {settings.app.environment}")
    logger.info(f"Debug mode: {settings.app.debug}")
    
    # Validate configuration on startup
    try:
        from app.config.validators import quick_health_check
        health_status = quick_health_check()
        if health_status["status"] == "healthy":
            logger.info("Configuration health check passed")
        else:
            logger.warning(f"Configuration health check issues: {health_status}")
    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down application...")
    cleanup_dependencies()
    logger.info("Application shutdown complete")


@app.get("/")
async def root():
    return {
        "message": "Backend is running!",
        "app_name": settings.app.app_name,
        "version": settings.app.app_version,
        "environment": settings.app.environment
    }
