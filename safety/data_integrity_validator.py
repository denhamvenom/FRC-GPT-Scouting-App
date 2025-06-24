#!/usr/bin/env python3
"""
Data Integrity Validator
Ensures data consistency and integrity across refactoring changes
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Any, Optional
import sys

class DataIntegrityValidator:
    def __init__(self, db_path="backend/app/database/scouting.db"):
        self.db_path = Path(db_path)
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "errors": []
        }
    
    def check_database_schema(self) -> bool:
        """Validate database schema integrity"""
        print("Checking database schema...")
        
        if not self.db_path.exists():
            self.validation_results["errors"].append("Database file not found")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema_info = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema_info[table_name] = {
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "nullable": not col[3],
                            "default": col[4],
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ]
                }
            
            self.validation_results["checks"]["database_schema"] = schema_info
            conn.close()
            
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Database schema check failed: {str(e)}")
            return False
    
    def check_data_consistency(self) -> bool:
        """Check for data consistency issues"""
        print("Checking data consistency...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            consistency_checks = {
                "orphaned_records": [],
                "duplicate_keys": [],
                "null_violations": []
            }
            
            # Example: Check for orphaned picklist entries
            cursor.execute("""
                SELECT COUNT(*) FROM picklist_entries 
                WHERE picklist_id NOT IN (SELECT id FROM picklists)
            """)
            orphaned_count = cursor.fetchone()[0]
            if orphaned_count > 0:
                consistency_checks["orphaned_records"].append({
                    "table": "picklist_entries",
                    "count": orphaned_count,
                    "description": "Entries with non-existent picklist_id"
                })
            
            self.validation_results["checks"]["data_consistency"] = consistency_checks
            conn.close()
            
            return len(consistency_checks["orphaned_records"]) == 0
            
        except Exception as e:
            self.validation_results["errors"].append(f"Data consistency check failed: {str(e)}")
            return False
    
    def create_data_snapshot(self, snapshot_name: str = "data_snapshot.json"):
        """Create a snapshot of critical data for comparison"""
        print("Creating data snapshot...")
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "database": {},
            "files": {}
        }
        
        # Snapshot database row counts
        if self.db_path.exists():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    # Get sample data hash for integrity check
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                    rows = cursor.fetchall()
                    data_hash = hashlib.md5(str(rows).encode()).hexdigest()
                    
                    snapshot["database"][table_name] = {
                        "row_count": count,
                        "sample_hash": data_hash
                    }
                
                conn.close()
            except Exception as e:
                snapshot["errors"] = [f"Database snapshot failed: {str(e)}"]
        
        # Snapshot critical configuration files
        config_files = [
            "backend/app/config/statbotics_field_map_DEFAULT.json",
            "frontend/package.json",
            "backend/requirements.txt"
        ]
        
        for file_path in config_files:
            path = Path(file_path)
            if path.exists():
                with open(path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    
                snapshot["files"][file_path] = {
                    "exists": True,
                    "hash": file_hash,
                    "size": path.stat().st_size
                }
            else:
                snapshot["files"][file_path] = {"exists": False}
        
        # Save snapshot
        snapshot_path = Path("safety") / snapshot_name
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"Data snapshot saved: {snapshot_path}")
        return snapshot
    
    def compare_snapshots(self, baseline_path: str, current_path: str) -> bool:
        """Compare two data snapshots"""
        print("\n=== Data Integrity Comparison ===")
        
        with open(baseline_path) as f:
            baseline = json.load(f)
        
        with open(current_path) as f:
            current = json.load(f)
        
        differences = []
        
        # Compare database tables
        for table, baseline_info in baseline.get("database", {}).items():
            current_info = current.get("database", {}).get(table, {})
            
            if not current_info:
                differences.append(f"Table '{table}' missing in current snapshot")
                continue
            
            if baseline_info["row_count"] != current_info["row_count"]:
                differences.append(
                    f"Table '{table}' row count changed: "
                    f"{baseline_info['row_count']} → {current_info['row_count']}"
                )
            
            if baseline_info["sample_hash"] != current_info["sample_hash"]:
                differences.append(f"Table '{table}' data changed (hash mismatch)")
        
        # Compare files
        for file_path, baseline_file in baseline.get("files", {}).items():
            current_file = current.get("files", {}).get(file_path, {})
            
            if baseline_file["exists"] != current_file.get("exists", False):
                differences.append(f"File '{file_path}' existence changed")
            elif baseline_file["exists"] and baseline_file["hash"] != current_file.get("hash"):
                differences.append(f"File '{file_path}' content changed")
        
        if differences:
            print("Data integrity differences found:")
            for diff in differences:
                print(f"  - {diff}")
            return False
        else:
            print("Data integrity validated - no unexpected changes")
            return True
    
    def validate_api_data_consistency(self):
        """Validate that API responses contain consistent data"""
        print("Validating API data consistency...")
        
        import requests
        
        api_tests = [
            {
                "name": "Team data consistency",
                "endpoints": [
                    "/api/picklist/teams",
                    "/api/team-comparison/teams"
                ],
                "compare_field": "team_number"
            }
        ]
        
        for test in api_tests:
            try:
                data_sets = []
                for endpoint in test["endpoints"]:
                    response = requests.get(f"http://localhost:8000{endpoint}")
                    if response.status_code == 200:
                        data_sets.append(set(
                            item.get(test["compare_field"]) 
                            for item in response.json() 
                            if isinstance(response.json(), list)
                        ))
                
                # Check if all endpoints return same data
                if len(data_sets) > 1:
                    if not all(ds == data_sets[0] for ds in data_sets):
                        self.validation_results["errors"].append(
                            f"Inconsistent data across endpoints for {test['name']}"
                        )
                        
            except Exception as e:
                self.validation_results["errors"].append(
                    f"API consistency check failed for {test['name']}: {str(e)}"
                )
    
    def save_validation_report(self, filename="data_validation_report.json"):
        """Save validation results"""
        report_path = Path("safety") / filename
        
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\nValidation report saved: {report_path}")
        
        # Print summary
        if self.validation_results["errors"]:
            print("\nValidation Errors:")
            for error in self.validation_results["errors"]:
                print(f"  - {error}")
            return False
        else:
            print("\nAll data integrity checks passed!")
            return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Integrity Validation")
    parser.add_argument("--snapshot", action="store_true", help="Create data snapshot")
    parser.add_argument("--validate", action="store_true", help="Run validation checks")
    parser.add_argument("--compare", nargs=2, metavar=('baseline', 'current'), 
                       help="Compare two snapshots")
    
    args = parser.parse_args()
    
    validator = DataIntegrityValidator()
    
    if args.snapshot:
        validator.create_data_snapshot()
    elif args.validate:
        # Run all validation checks
        schema_ok = validator.check_database_schema()
        consistency_ok = validator.check_data_consistency()
        validator.validate_api_data_consistency()
        
        success = validator.save_validation_report()
        sys.exit(0 if success else 1)
    elif args.compare:
        success = validator.compare_snapshots(args.compare[0], args.compare[1])
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()