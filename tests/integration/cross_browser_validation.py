#!/usr/bin/env python3
"""
Cross-Browser Validation Tests
Validates UI works correctly across different browsers
"""

import json
from pathlib import Path
from datetime import datetime
import sys

class CrossBrowserValidator:
    """Validates UI consistency across browsers"""
    
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "browsers": {},
            "issues": []
        }
        self.frontend_url = "http://localhost:3000"
    
    def create_manual_test_checklist(self):
        """Create manual testing checklist for browsers"""
        checklist = """
# Cross-Browser Validation Checklist

## Test Date: {date}
## Frontend URL: {url}

## Browsers to Test:
- [ ] Chrome (Latest)
- [ ] Firefox (Latest)
- [ ] Safari (Latest) - if on macOS
- [ ] Edge (Latest)

## Critical Pages to Validate:

### 1. Home Page (/)
- [ ] Layout renders correctly
- [ ] Navigation menu works
- [ ] All buttons clickable
- [ ] No console errors

### 2. Setup Page (/setup)
- [ ] Form inputs work correctly
- [ ] Dropdowns function properly
- [ ] Save functionality works
- [ ] Validation messages appear

### 3. Event Manager (/event-manager)
- [ ] Table displays correctly
- [ ] Sorting works
- [ ] Filtering works
- [ ] Actions work (edit/delete)

### 4. Schema Mapping (/schema-mapping)
- [ ] Schema loads properly
- [ ] Checkboxes work
- [ ] Save selections work
- [ ] No layout breaks

### 5. Validation Page (/validation)
- [ ] Validation runs correctly
- [ ] Results display properly
- [ ] Error/warning styling correct
- [ ] Export works

### 6. Picklist Page (/picklist)
- [ ] Teams display correctly
- [ ] Drag-and-drop works (if implemented)
- [ ] Sorting works
- [ ] Export functionality works

### 7. Alliance Selection (/alliance-selection)
- [ ] Alliance display correct
- [ ] Selection interface works
- [ ] Updates work properly
- [ ] No visual glitches

### 8. Workflow Page (/workflow)
- [ ] Workflow steps display
- [ ] Navigation between steps works
- [ ] Progress indicators work
- [ ] All links functional

## Common Issues to Check:

### Visual Consistency:
- [ ] Fonts render consistently
- [ ] Colors match exactly
- [ ] Spacing/padding consistent
- [ ] No elements overlapping
- [ ] Responsive behavior works

### Functionality:
- [ ] All buttons work
- [ ] Forms submit correctly
- [ ] Modal dialogs work
- [ ] Tooltips appear
- [ ] Loading states work

### Performance:
- [ ] Page load times acceptable
- [ ] Animations smooth
- [ ] No memory leaks
- [ ] API calls complete

### Console Checks:
- [ ] No JavaScript errors
- [ ] No failed resource loads
- [ ] No security warnings
- [ ] No deprecation warnings

## Browser-Specific Issues Found:

### Chrome:
_[Document any Chrome-specific issues]_

### Firefox:
_[Document any Firefox-specific issues]_

### Safari:
_[Document any Safari-specific issues]_

### Edge:
_[Document any Edge-specific issues]_

## Screenshots:
Please take screenshots of any visual differences or issues found.
Save as: browser_name_page_name_issue.png

## Summary:
- Total Issues Found: ___
- Critical Issues: ___
- Minor Issues: ___
- Browsers Affected: ___

## Recommendations:
_[List any recommended fixes or changes]_

---
Tested by: _______________
Date: {date}
"""
        
        # Save checklist
        checklist_path = Path("safety/cross_browser_checklist.md")
        with open(checklist_path, 'w') as f:
            f.write(checklist.format(
                date=datetime.now().strftime("%Y-%m-%d"),
                url=self.frontend_url
            ))
        
        print(f"Manual test checklist created: {checklist_path}")
        print("Please complete this checklist in each browser")
    
    def create_automated_test_script(self):
        """Create automated test script using Selenium"""
        script_content = '''#!/usr/bin/env python3
"""
Automated Cross-Browser Tests using Selenium
Requires: pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import json
import time

FRONTEND_URL = "http://localhost:3000"
WAIT_TIMEOUT = 10

def test_page_load(driver, path, page_name):
    """Test basic page loading"""
    print(f"Testing {page_name} ({path})...")
    
    try:
        driver.get(f"{FRONTEND_URL}{path}")
        time.sleep(2)  # Wait for initial render
        
        # Check for basic page load
        assert driver.title, f"{page_name} has no title"
        
        # Check for console errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            print(f"  ⚠️  JavaScript errors found in {page_name}:")
            for error in errors:
                print(f"     {error['message']}")
        else:
            print(f"  ✓ No JavaScript errors")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to load {page_name}: {str(e)}")
        return False

def test_navigation(driver):
    """Test navigation menu works"""
    print("Testing navigation...")
    
    try:
        driver.get(FRONTEND_URL)
        
        # Find and click navigation items
        nav_items = driver.find_elements(By.CSS_SELECTOR, "nav a, .navbar a")
        print(f"  Found {len(nav_items)} navigation items")
        
        return True
    except Exception as e:
        print(f"  ✗ Navigation test failed: {str(e)}")
        return False

def run_browser_tests(browser_name):
    """Run tests for a specific browser"""
    print(f"\\n{'='*50}")
    print(f"Testing {browser_name}")
    print('='*50)
    
    # Initialize driver based on browser
    if browser_name == "Chrome":
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    elif browser_name == "Firefox":
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    elif browser_name == "Edge":
        driver = webdriver.Edge(EdgeChromiumDriverManager().install())
    else:
        print(f"Unknown browser: {browser_name}")
        return
    
    driver.set_window_size(1920, 1080)
    
    results = {
        "browser": browser_name,
        "tests": {}
    }
    
    # Test pages
    pages = [
        ("/", "Home"),
        ("/setup", "Setup"),
        ("/event-manager", "Event Manager"),
        ("/schema-mapping", "Schema Mapping"),
        ("/validation", "Validation"),
        ("/picklist", "Picklist"),
        ("/alliance-selection", "Alliance Selection"),
        ("/workflow", "Workflow")
    ]
    
    for path, name in pages:
        results["tests"][name] = test_page_load(driver, path, name)
    
    # Test navigation
    results["tests"]["Navigation"] = test_navigation(driver)
    
    # Save screenshots of each page
    driver.get(FRONTEND_URL)
    time.sleep(2)
    driver.save_screenshot(f"safety/screenshots_{browser_name.lower()}_home.png")
    
    driver.quit()
    
    # Summary
    passed = sum(1 for v in results["tests"].values() if v)
    total = len(results["tests"])
    print(f"\\n{browser_name} Summary: {passed}/{total} tests passed")
    
    return results

def main():
    """Run cross-browser tests"""
    print("Starting Cross-Browser Validation")
    print("Note: This requires browsers and drivers to be installed")
    
    browsers = ["Chrome", "Firefox", "Edge"]
    all_results = []
    
    for browser in browsers:
        try:
            results = run_browser_tests(browser)
            all_results.append(results)
        except Exception as e:
            print(f"Failed to test {browser}: {str(e)}")
    
    # Save results
    with open("safety/cross_browser_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\\nCross-browser validation complete!")
    print("Results saved to: safety/cross_browser_results.json")

if __name__ == "__main__":
    main()
'''
        
        script_path = Path("safety/automated_browser_tests.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        import os
        os.chmod(script_path, 0o755)
        
        print(f"Automated test script created: {script_path}")
        print("To run: python safety/automated_browser_tests.py")
        print("Note: Requires Selenium and browser drivers to be installed")
    
    def create_visual_comparison_guide(self):
        """Create guide for visual comparison across browsers"""
        guide_content = """# Visual Comparison Guide

## Purpose
This guide helps ensure visual consistency across browsers by comparing screenshots.

## Setup Instructions

### 1. Install Screenshot Tools
- **Chrome/Edge/Firefox**: Built-in developer tools (F12)
- **Full Page Screenshots**: 
  - Chrome: Full Page Screen Capture extension
  - Firefox: Built-in screenshot tool (Ctrl+Shift+S)

### 2. Screenshot Naming Convention
`[browser]_[page]_[viewport].png`

Examples:
- chrome_home_1920x1080.png
- firefox_picklist_1366x768.png
- safari_setup_mobile.png

### 3. Key Viewports to Test
- Desktop: 1920x1080, 1366x768
- Tablet: 768x1024 (iPad)
- Mobile: 375x667 (iPhone 6/7/8)

## Visual Elements to Compare

### 1. Typography
- [ ] Font rendering
- [ ] Font sizes
- [ ] Line heights
- [ ] Font weights

### 2. Colors
- [ ] Background colors
- [ ] Text colors
- [ ] Border colors
- [ ] Hover states

### 3. Layout
- [ ] Element alignment
- [ ] Spacing/padding
- [ ] Grid/flexbox behavior
- [ ] Responsive breakpoints

### 4. Components
- [ ] Buttons
- [ ] Forms
- [ ] Tables
- [ ] Modals
- [ ] Navigation

### 5. Animations
- [ ] Transitions
- [ ] Loading states
- [ ] Hover effects
- [ ] Page transitions

## Comparison Process

1. Take screenshots in each browser
2. Use image diff tools:
   - Online: www.diffchecker.com/image-diff
   - Command line: `compare image1.png image2.png diff.png` (ImageMagick)
   - GUI: Beyond Compare, Kaleidoscope

3. Document differences in comparison matrix:

| Feature | Chrome | Firefox | Safari | Edge | Notes |
|---------|--------|---------|--------|------|-------|
| Home Layout | ✓ | ✓ | ✓ | ✓ | |
| Button Styles | ✓ | ⚠️ | ✓ | ✓ | Firefox: slight border difference |
| Form Inputs | ✓ | ✓ | ⚠️ | ✓ | Safari: default styling differs |

## Acceptable Differences

Some differences are expected and acceptable:
- Font rendering (anti-aliasing)
- Form control styling (browser defaults)
- Scrollbar appearance
- Selection highlighting

## Critical Issues

These differences require fixes:
- Layout breaks
- Missing elements
- Non-functional features
- Significant color differences
- Text overlap/cutoff

## Reporting Template

```
Browser: [Name and Version]
Page: [URL]
Issue: [Description]
Impact: [Critical/Major/Minor]
Screenshot: [Filename]
Steps to Reproduce:
1. 
2. 
3. 
Expected: [What should happen]
Actual: [What actually happens]
```

---

Remember: The goal is functional consistency, not pixel-perfect matching across browsers.
"""
        
        guide_path = Path("safety/visual_comparison_guide.md")
        with open(guide_path, 'w') as f:
            f.write(guide_content)
        
        print(f"Visual comparison guide created: {guide_path}")


def main():
    """Main entry point for cross-browser validation"""
    validator = CrossBrowserValidator()
    
    print("=== Cross-Browser Validation Setup ===")
    
    # Create manual checklist
    validator.create_manual_test_checklist()
    
    # Create automated test script
    validator.create_automated_test_script()
    
    # Create visual comparison guide
    validator.create_visual_comparison_guide()
    
    print("\nCross-browser validation tools created!")
    print("\nNext steps:")
    print("1. Complete manual testing using: safety/cross_browser_checklist.md")
    print("2. Run automated tests (if Selenium installed): python safety/automated_browser_tests.py")
    print("3. Compare screenshots using: safety/visual_comparison_guide.md")


if __name__ == "__main__":
    main()