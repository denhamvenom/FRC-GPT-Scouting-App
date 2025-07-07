#!/usr/bin/env python3
"""
Visual Regression Testing Setup
Captures screenshots and detects visual changes in the UI
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib
import sys

class VisualRegressionTester:
    def __init__(self, screenshots_dir="visual_baselines"):
        self.screenshots_dir = Path(__file__).parent / screenshots_dir
        self.screenshots_dir.mkdir(exist_ok=True)
        self.frontend_url = "http://localhost:5173/"
        self.test_results = []
        
    def setup_playwright(self):
        """Install playwright if needed"""
        print("Checking Playwright installation...")
        try:
            import playwright
            print("Playwright already installed")
            return True
        except ImportError:
            print("Installing Playwright...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                print("Playwright installed successfully")
                return True
            except Exception as e:
                print(f"Failed to install Playwright: {e}")
                print("Manual screenshot comparison will be used instead")
                return False
    
    def capture_screenshot_playwright(self, route: str, filename: str):
        """Capture screenshot using Playwright"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                # Navigate to page
                page.goto(f"{self.frontend_url}{route}")
                
                # Wait for page to load
                page.wait_for_load_state('networkidle')
                time.sleep(2)  # Additional wait for dynamic content
                
                # Take screenshot
                screenshot_path = self.screenshots_dir / filename
                page.screenshot(path=str(screenshot_path), full_page=True)
                
                browser.close()
                
                print(f"Screenshot captured: {filename}")
                return True
                
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return False
    
    def capture_critical_routes(self):
        """Capture screenshots of critical UI routes"""
        print("\n=== Capturing Visual Baselines ===")
        
        routes = [
            ("/", "home.png"),
            ("/setup", "setup.png"),
            ("/event-manager", "event_manager.png"),
            ("/schema-mapping", "schema_mapping.png"),
            ("/validation", "validation.png"),
            ("/picklist", "picklist.png"),
            ("/alliance-selection", "alliance_selection.png"),
            ("/workflow", "workflow.png")
        ]
        
        has_playwright = self.setup_playwright()
        
        if has_playwright:
            for route, filename in routes:
                self.capture_screenshot_playwright(route, filename)
        else:
            self.create_manual_capture_script(routes)
    
    def create_manual_capture_script(self, routes):
        """Create script for manual screenshot capture"""
        script_content = """#!/bin/bash
# Manual Screenshot Capture Script
# Run this script and manually take screenshots as instructed

echo "=== Manual Visual Baseline Capture ==="
echo "Please take screenshots of the following pages:"
echo ""
"""
        
        for route, filename in routes:
            script_content += f'echo "1. Navigate to: http://localhost:5173{route}"\n'
            script_content += f'echo "   Save screenshot as: {self.screenshots_dir}/{filename}"\n'
            script_content += 'echo "   Press Enter when done..."\n'
            script_content += 'read\n'
            script_content += 'echo ""\n'
        
        script_content += """
echo "Visual baseline capture complete!"
"""
        
        script_path = self.screenshots_dir / "manual_capture.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        print(f"\nManual capture script created: {script_path}")
        print("Run this script to manually capture screenshots")
    
    def compute_image_hash(self, image_path: Path) -> str:
        """Compute hash of image file for comparison"""
        if not image_path.exists():
            return ""
            
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def load_screenshot_registry(self):
        """Load the screenshot registry to understand what we're comparing"""
        registry_path = Path(__file__).parent / "screenshot_registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                return json.load(f)
        return None
    
    def compare_screenshots(self, baseline_dir: str, current_dir: str):
        """Compare two sets of screenshots using registry information"""
        print("\n=== Visual Regression Comparison ===")
        
        baseline_path = Path(baseline_dir) if isinstance(baseline_dir, str) else Path(baseline_dir)
        current_path = Path(current_dir) if isinstance(current_dir, str) else Path(current_dir)
        
        if not baseline_path.exists():
            print(f"ERROR: Baseline directory not found: {baseline_dir}")
            return False
            
        if not current_path.exists():
            print(f"ERROR: Current directory not found: {current_dir}")
            return False
        
        # Load registry to understand screenshot importance
        registry = self.load_screenshot_registry()
        
        differences = []
        critical_differences = []
        
        # Get all baseline screenshots
        baseline_screenshots = list(baseline_path.glob("*.png"))
        if not baseline_screenshots:
            print("ERROR: No baseline screenshots found!")
            return False
        
        print(f"Comparing {len(baseline_screenshots)} baseline screenshots...")
        
        # Compare all baseline images
        for baseline_img in baseline_screenshots:
            current_img = current_path / baseline_img.name
            
            # Check if screenshot is critical (from registry)
            is_critical = True  # Default to critical
            screenshot_info = None
            if registry and "screenshots" in registry:
                screenshot_info = registry["screenshots"].get(baseline_img.name)
                if screenshot_info:
                    is_critical = screenshot_info.get("critical", True)
            
            if not current_img.exists():
                diff_msg = f"Missing screenshot: {baseline_img.name}"
                if is_critical:
                    critical_differences.append(diff_msg)
                else:
                    differences.append(diff_msg)
                continue
            
            # Compare file sizes first (quick check)
            baseline_size = baseline_img.stat().st_size
            current_size = current_img.stat().st_size
            
            size_difference = False
            if baseline_size != current_size:
                size_diff = abs(current_size - baseline_size)
                diff_percent = (size_diff / baseline_size) * 100
                
                # Allow small differences (< 2%) due to rendering variations, but only for non-critical
                tolerance = 1 if is_critical else 2
                if diff_percent > tolerance:
                    size_difference = True
                    diff_msg = (
                        f"{baseline_img.name}: Size difference {diff_percent:.1f}% "
                        f"(baseline: {baseline_size}, current: {current_size})"
                    )
                    
                    if is_critical:
                        critical_differences.append(diff_msg)
                    else:
                        differences.append(diff_msg)
            
            # Compare hashes for exact match
            baseline_hash = self.compute_image_hash(baseline_img)
            current_hash = self.compute_image_hash(current_img)
            
            if baseline_hash != current_hash:
                # Record the change
                self.test_results.append({
                    "file": baseline_img.name,
                    "status": "changed",
                    "baseline_hash": baseline_hash,
                    "current_hash": current_hash,
                    "critical": is_critical,
                    "description": screenshot_info.get("description", "Unknown") if screenshot_info else "Unknown",
                    "workflow": screenshot_info.get("workflow", "Unknown") if screenshot_info else "Unknown"
                })
                
                if not size_difference:  # If not already reported as size difference
                    diff_msg = f"{baseline_img.name}: Content changed (hash mismatch)"
                    if is_critical:
                        critical_differences.append(diff_msg)
                    else:
                        differences.append(diff_msg)
            else:
                # Record successful match
                self.test_results.append({
                    "file": baseline_img.name,
                    "status": "unchanged",
                    "baseline_hash": baseline_hash,
                    "current_hash": current_hash,
                    "critical": is_critical,
                    "description": screenshot_info.get("description", "Unknown") if screenshot_info else "Unknown",
                    "workflow": screenshot_info.get("workflow", "Unknown") if screenshot_info else "Unknown"
                })
        
        # Report results
        if critical_differences:
            print("🚨 CRITICAL visual differences detected:")
            for diff in critical_differences:
                print(f"  - {diff}")
        
        if differences:
            print("⚠️  Non-critical visual differences detected:")
            for diff in differences:
                print(f"  - {diff}")
        
        if not critical_differences and not differences:
            print("✅ No visual differences detected - all screenshots match!")
            return True
        elif critical_differences:
            print(f"\n❌ VALIDATION FAILED: {len(critical_differences)} critical differences found")
            return False
        else:
            print(f"\n⚠️  MINOR ISSUES: {len(differences)} non-critical differences found")
            # You might want to return True here if non-critical differences are acceptable
            return False
    
    def create_comparison_report(self):
        """Create HTML report for visual comparison"""
        report_content = """<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .comparison { margin-bottom: 30px; border: 1px solid #ccc; padding: 10px; }
        .images { display: flex; gap: 20px; }
        .image-container { flex: 1; }
        img { max-width: 100%; border: 1px solid #ddd; }
        h2 { color: #333; }
        .status-changed { color: red; }
        .status-unchanged { color: green; }
    </style>
</head>
<body>
    <h1>Visual Regression Test Report</h1>
    <p>Generated: {timestamp}</p>
    
    <div class="comparisons">
        {comparisons}
    </div>
</body>
</html>"""
        
        comparisons_html = ""
        for result in self.test_results:
            status_class = "status-changed" if result["status"] == "changed" else "status-unchanged"
            comparisons_html += f"""
        <div class="comparison">
            <h2>{result['file']} - <span class="{status_class}">{result['status'].upper()}</span></h2>
            <div class="images">
                <div class="image-container">
                    <h3>Baseline</h3>
                    <img src="visual_baselines/{result['file']}" alt="Baseline">
                </div>
                <div class="image-container">
                    <h3>Current</h3>
                    <img src="visual_current/{result['file']}" alt="Current">
                </div>
            </div>
        </div>"""
        
        report_path = self.screenshots_dir.parent / "visual_regression_report.html"
        with open(report_path, 'w') as f:
            f.write(report_content.format(
                timestamp=datetime.now().isoformat(),
                comparisons=comparisons_html
            ))
        
        print(f"\nVisual comparison report created: {report_path}")
    
    def save_baseline_metadata(self):
        """Save metadata about visual baselines"""
        metadata = {
            "capture_time": datetime.now().isoformat(),
            "screenshots": {}
        }
        
        for img_path in self.screenshots_dir.glob("*.png"):
            metadata["screenshots"][img_path.name] = {
                "size": img_path.stat().st_size,
                "hash": self.compute_image_hash(img_path),
                "modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat()
            }
        
        metadata_path = self.screenshots_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Baseline metadata saved: {metadata_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual Regression Testing")
    parser.add_argument("--capture", action="store_true", help="Capture baseline screenshots")
    parser.add_argument("--compare", type=str, help="Compare against baseline (provide current dir)")
    parser.add_argument("--report", action="store_true", help="Generate comparison report")
    
    args = parser.parse_args()
    
    tester = VisualRegressionTester()
    
    if args.capture:
        tester.capture_critical_routes()
        tester.save_baseline_metadata()
    elif args.compare:
        success = tester.compare_screenshots("safety/visual_baselines", args.compare)
        if args.report:
            tester.create_comparison_report()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()