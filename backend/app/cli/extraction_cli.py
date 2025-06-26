#!/usr/bin/env python3
"""
Command-line interface for managing game context extraction.

This CLI provides commands to extract game context, manage cache,
and configure extraction settings.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.data_aggregation_service import DataAggregationService
from app.services.game_context_extractor_service import GameContextExtractorService
from app.config.extraction_config import get_config_manager, get_env_vars_documentation


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def print_status(data_service: DataAggregationService) -> None:
    """Print extraction status information."""
    status = data_service.get_extraction_status()
    
    print("Game Context Extraction Status")
    print("=" * 40)
    print(f"Year: {status['year']}")
    print(f"Game: {status.get('game_name', 'Unknown')}")
    print(f"Extraction Mode: {'Enabled' if status['extraction_enabled'] else 'Disabled'}")
    print(f"Extractor Available: {'Yes' if status['extractor_available'] else 'No'}")
    print(f"Manual Available: {'Yes' if status['manual_available'] else 'No'}")
    print(f"Cached Extraction: {'Yes' if status.get('cached_extraction', False) else 'No'}")
    
    if status.get('manual_size'):
        print(f"Manual Size: {status['manual_size']:,} characters")
    
    if status.get('cache_validation_score'):
        print(f"Cache Validation Score: {status['cache_validation_score']:.2f}")
    
    if 'cache_info' in status:
        cache_info = status['cache_info']
        if 'cached_extractions' in cache_info:
            print(f"Cached Files: {cache_info['cached_extractions']}")


def print_config() -> None:
    """Print current extraction configuration."""
    config_manager = get_config_manager()
    config_dict = config_manager.get_config_dict()
    validation = config_manager.validate_config()
    
    print("Extraction Configuration")
    print("=" * 40)
    
    for key, value in config_dict.items():
        print(f"{key}: {value}")
    
    print("\nValidation Results:")
    print(f"Valid: {'Yes' if validation['is_valid'] else 'No'}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")


def extract_context(dataset_path: str, force: bool = False) -> None:
    """Extract game context from manual."""
    print("Extracting game context...")
    
    try:
        data_service = DataAggregationService(dataset_path, use_extracted_context=True)
        
        if force:
            print("Force refresh enabled - bypassing cache")
            result = data_service.force_extract_game_context()
        else:
            # Just load context (will extract if needed)
            context = data_service.load_game_context()
            if context:
                result = {"success": True, "message": "Context loaded successfully"}
            else:
                result = {"success": False, "message": "Failed to load context"}
        
        if result["success"]:
            print("✓ Extraction successful")
            if 'processing_time' in result:
                print(f"  Processing time: {result['processing_time']:.2f}s")
            if 'validation_score' in result:
                print(f"  Validation score: {result['validation_score']:.2f}")
            if 'token_usage' in result:
                tokens = result['token_usage']
                print(f"  Token usage: {tokens.get('total_tokens', 0)}")
        else:
            print(f"✗ Extraction failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during extraction: {e}")
        return False
    
    return True


def compare_contexts(dataset_path: str) -> None:
    """Compare full manual vs extracted context sizes."""
    print("Comparing context sizes...")
    
    try:
        data_service = DataAggregationService(dataset_path, use_extracted_context=False)
        
        # Get manual data
        manual_data = data_service._load_manual_data()
        if not manual_data:
            print("✗ Manual data not available")
            return
        
        # Get full context
        full_context = data_service._get_full_manual_context(manual_data)
        full_size = len(full_context)
        
        print(f"Full Manual Context: {full_size:,} characters")
        
        # Try to get extracted context
        if data_service.extractor_service is None:
            try:
                cache_dir = "/tmp/game_context_test"
                os.makedirs(cache_dir, exist_ok=True)
                data_service.extractor_service = GameContextExtractorService(cache_dir)
                data_service.use_extracted_context = True
            except Exception as e:
                print(f"Could not initialize extractor: {e}")
                return
        
        extracted_context = data_service._get_extracted_context(manual_data)
        if extracted_context:
            extracted_size = len(extracted_context)
            savings_pct = 100 * (1 - extracted_size / full_size)
            
            print(f"Extracted Context: {extracted_size:,} characters")
            print(f"Size Reduction: {full_size - extracted_size:,} characters ({savings_pct:.1f}%)")
            
            # Estimate token savings
            estimated_full_tokens = full_size // 4
            estimated_extracted_tokens = extracted_size // 4
            token_savings = estimated_full_tokens - estimated_extracted_tokens
            
            print(f"Estimated Token Savings: {token_savings:,} tokens")
        else:
            print("✗ Could not generate extracted context")
            
    except Exception as e:
        print(f"✗ Exception during comparison: {e}")


def manage_cache(action: str, dataset_path: str, version: str = None) -> None:
    """Manage extraction cache."""
    try:
        data_service = DataAggregationService(dataset_path, use_extracted_context=True)
        
        if not data_service.extractor_service:
            print("✗ Extraction service not available")
            return
        
        if action == "info":
            cache_info = data_service.extractor_service.get_cache_info()
            print("Cache Information")
            print("=" * 20)
            print(f"Cache Directory: {cache_info['cache_directory']}")
            print(f"Cached Extractions: {cache_info['cached_extractions']}")
            print(f"Extraction Version: {cache_info['extraction_version']}")
            
            if cache_info.get('files'):
                print("\nCached Files:")
                for file_info in cache_info['files']:
                    print(f"  {file_info['filename']} ({file_info['size_bytes']} bytes)")
        
        elif action == "clear":
            result = data_service.extractor_service.clear_cache(version)
            if 'error' in result:
                print(f"✗ Error clearing cache: {result['error']}")
            else:
                print(f"✓ Cleared {result['cleared_files']} cache files")
                if version:
                    print(f"  Version filter: {version}")
        
        else:
            print(f"✗ Unknown cache action: {action}")
            
    except Exception as e:
        print(f"✗ Exception managing cache: {e}")


def show_env_vars() -> None:
    """Show environment variable documentation."""
    env_vars = get_env_vars_documentation()
    
    print("Extraction Environment Variables")
    print("=" * 40)
    
    for var_name, var_info in env_vars.items():
        print(f"\n{var_name}")
        print(f"  Description: {var_info['description']}")
        print(f"  Type: {var_info['type']}")
        print(f"  Default: {var_info['default']}")
        print(f"  Range: {var_info['range']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Game Context Extraction CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  extraction_cli.py status /path/to/dataset.json
  extraction_cli.py extract /path/to/dataset.json --force
  extraction_cli.py compare /path/to/dataset.json
  extraction_cli.py cache info /path/to/dataset.json
  extraction_cli.py cache clear /path/to/dataset.json
  extraction_cli.py config
  extraction_cli.py env-vars
        """
    )
    
    parser.add_argument("command", choices=[
        "status", "extract", "compare", "cache", "config", "env-vars"
    ], help="Command to execute")
    
    parser.add_argument("dataset_path", nargs="?", 
                       help="Path to unified dataset JSON file (required for most commands)")
    
    parser.add_argument("cache_action", nargs="?", choices=["info", "clear"],
                       help="Cache action (for cache command)")
    
    parser.add_argument("--force", action="store_true",
                       help="Force refresh, bypass cache")
    
    parser.add_argument("--version", type=str,
                       help="Extraction version filter (for cache clear)")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Commands that don't require dataset path
    if args.command == "config":
        print_config()
        return
    
    if args.command == "env-vars":
        show_env_vars()
        return
    
    # Commands that require dataset path
    if not args.dataset_path:
        print("✗ Dataset path required for this command")
        parser.print_help()
        return 1
    
    if not os.path.exists(args.dataset_path):
        print(f"✗ Dataset file not found: {args.dataset_path}")
        return 1
    
    try:
        if args.command == "status":
            data_service = DataAggregationService(args.dataset_path, use_extracted_context=True)
            print_status(data_service)
        
        elif args.command == "extract":
            success = extract_context(args.dataset_path, force=args.force)
            return 0 if success else 1
        
        elif args.command == "compare":
            compare_contexts(args.dataset_path)
        
        elif args.command == "cache":
            if not args.cache_action:
                print("✗ Cache action required (info or clear)")
                return 1
            manage_cache(args.cache_action, args.dataset_path, args.version)
        
        else:
            print(f"✗ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())