#!/usr/bin/env python3
"""
Baseline Metrics Capture System
Captures and validates system performance and behavior metrics
"""

import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import sys
import argparse

class BaselineMetrics:
    def __init__(self, metrics_file="baseline_metrics.json"):
        self.metrics_file = Path(__file__).parent / metrics_file
        self.api_base_url = "http://localhost:8000"
        self.metrics = {
            "capture_time": None,
            "system_info": {},
            "api_endpoints": {},
            "performance_metrics": {},
            "database_state": {},
            "frontend_build": {}
        }
    
    def capture_system_info(self):
        """Capture system information"""
        print("Capturing system information...")
        self.metrics["system_info"] = {
            "python_version": sys.version,
            "capture_timestamp": datetime.now().isoformat(),
            "git_commit": self._get_git_commit(),
            "branch": self._get_git_branch()
        }
    
    def _get_git_commit(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _get_git_branch(self):
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    def capture_api_endpoints(self):
        """Capture all API endpoint responses"""
        print("Capturing API endpoint responses...")
        
        # Key endpoints to capture
        endpoints = [
            "/api/health",
            "/api/sheets/headers",
            "/api/schema",
            "/api/schema/selections",
            "/api/picklist/teams",
            "/api/team-comparison/compare",
            "/api/unified-dataset/events",
            "/api/progress/status"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                self.metrics["api_endpoints"][endpoint] = {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "headers": dict(response.headers),
                    "response_size": len(response.content)
                }
                
                # Store sample response for critical endpoints
                if endpoint in ["/api/health", "/api/schema"]:
                    try:
                        self.metrics["api_endpoints"][endpoint]["sample_response"] = response.json()
                    except:
                        self.metrics["api_endpoints"][endpoint]["sample_response"] = response.text[:200]
                        
            except Exception as e:
                self.metrics["api_endpoints"][endpoint] = {
                    "error": str(e),
                    "status": "unreachable"
                }
    
    def capture_performance_metrics(self):
        """Capture performance baselines"""
        print("Capturing performance metrics...")
        
        # Measure API response times
        performance_tests = [
            {
                "name": "health_check",
                "endpoint": "/api/health",
                "iterations": 10
            },
            {
                "name": "schema_load",
                "endpoint": "/api/schema",
                "iterations": 5
            }
        ]
        
        for test in performance_tests:
            times = []
            for _ in range(test["iterations"]):
                try:
                    start = time.time()
                    response = requests.get(f"{self.api_base_url}{test['endpoint']}", timeout=10)
                    end = time.time()
                    if response.status_code == 200:
                        times.append(end - start)
                except:
                    pass
            
            if times:
                self.metrics["performance_metrics"][test["name"]] = {
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                    "iterations": len(times)
                }
    
    def capture_database_state(self):
        """Capture database state information"""
        print("Capturing database state...")
        
        # Check if database file exists
        db_path = Path("backend/app/database/scouting.db")
        if db_path.exists():
            self.metrics["database_state"] = {
                "exists": True,
                "size_bytes": db_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
            }
        else:
            self.metrics["database_state"] = {
                "exists": False
            }
    
    def capture_frontend_build(self):
        """Capture frontend build information"""
        print("Capturing frontend build info...")
        
        # Check package.json
        package_json = Path("frontend/package.json")
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                    self.metrics["frontend_build"]["dependencies"] = package_data.get("dependencies", {})
                    self.metrics["frontend_build"]["scripts"] = package_data.get("scripts", {})
            except:
                self.metrics["frontend_build"]["error"] = "Failed to read package.json"
    
    def save_metrics(self):
        """Save captured metrics to file"""
        self.metrics["capture_time"] = datetime.now().isoformat()
        
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"Baseline metrics saved to {self.metrics_file}")
    
    def verify_baseline(self):
        """Verify current state against baseline"""
        if not self.metrics_file.exists():
            print("ERROR: No baseline metrics found. Run capture first.")
            return False
        
        with open(self.metrics_file) as f:
            baseline = json.load(f)
        
        # Capture current metrics
        current = BaselineMetrics("current_metrics.json")
        current.capture_all()
        
        # Compare metrics
        print("\n=== Baseline Verification ===")
        issues = []
        
        # Check API endpoints
        for endpoint, baseline_data in baseline.get("api_endpoints", {}).items():
            current_data = current.metrics.get("api_endpoints", {}).get(endpoint, {})
            
            if baseline_data.get("status_code") != current_data.get("status_code"):
                issues.append(f"API {endpoint}: Status code changed from {baseline_data.get('status_code')} to {current_data.get('status_code')}")
            
            # Check performance (within 50% tolerance for initial implementation)
            baseline_time = baseline_data.get("response_time", 0)
            current_time = current_data.get("response_time", 0)
            if baseline_time > 0 and current_time > baseline_time * 1.5:
                issues.append(f"API {endpoint}: Response time degraded from {baseline_time:.3f}s to {current_time:.3f}s")
        
        # Check performance metrics
        for metric, baseline_perf in baseline.get("performance_metrics", {}).items():
            current_perf = current.metrics.get("performance_metrics", {}).get(metric, {})
            
            baseline_avg = baseline_perf.get("avg", 0)
            current_avg = current_perf.get("avg", 0)
            
            if baseline_avg > 0 and current_avg > baseline_avg * 1.05:  # 5% tolerance
                issues.append(f"Performance {metric}: Average time increased from {baseline_avg:.3f}s to {current_avg:.3f}s")
        
        if issues:
            print("BASELINE VERIFICATION FAILED:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("BASELINE VERIFICATION PASSED")
            print(f"  - All API endpoints maintain status codes")
            print(f"  - Performance within acceptable range")
            return True
    
    def capture_all(self):
        """Capture all baseline metrics"""
        print("Starting baseline capture...")
        self.capture_system_info()
        self.capture_api_endpoints()
        self.capture_performance_metrics()
        self.capture_database_state()
        self.capture_frontend_build()
        self.save_metrics()
        print("Baseline capture complete!")


def main():
    parser = argparse.ArgumentParser(description="Baseline Metrics Capture and Verification")
    parser.add_argument("--verify", action="store_true", help="Verify against baseline")
    parser.add_argument("--capture", action="store_true", help="Capture new baseline")
    
    args = parser.parse_args()
    
    if args.verify:
        metrics = BaselineMetrics()
        success = metrics.verify_baseline()
        sys.exit(0 if success else 1)
    elif args.capture or not (args.verify):
        # Default to capture if no args
        metrics = BaselineMetrics()
        metrics.capture_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()