# backend/app/api/health.py

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from ..config.validators import get_config_validator, ConfigurationValidator
from ..core.dependencies import get_dependency_health, verify_configuration_health

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint"""
    return {"status": "ok"}


@router.get("/detailed", tags=["Health"])
async def detailed_health_check(
    validator: ConfigurationValidator = Depends(get_config_validator)
) -> Dict[str, Any]:
    """Detailed health check with configuration validation"""
    try:
        health_status = validator.quick_health_check()
        return {
            "basic_status": "ok",
            "configuration": health_status,
            "dependencies": get_dependency_health()
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "basic_status": "ok",
            "configuration": {"status": "error", "error": str(e)},
            "dependencies": {"status": "error", "error": str(e)}
        }


@router.get("/config", tags=["Health"])
async def configuration_health(
    health_check: Dict[str, Any] = Depends(verify_configuration_health)
) -> Dict[str, Any]:
    """Configuration-specific health check"""
    return health_check


@router.get("/full-report", tags=["Health"])
async def full_configuration_report(
    validator: ConfigurationValidator = Depends(get_config_validator)
) -> Dict[str, Any]:
    """Generate full configuration report"""
    try:
        return validator.generate_config_report()
    except Exception as e:
        logger.error(f"Full configuration report failed: {e}")
        return {"error": f"Failed to generate configuration report: {e}"}
